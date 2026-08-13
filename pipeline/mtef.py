"""Giải mã MathType OLE (Equation Native) -> LaTeX.

Hai đường:
  1. MathType 7 (DSMT7) đôi khi nhúng thẳng nguồn TeX ("TeX Input Language") -> lấy nguyên.
  2. Còn lại: parse MTEF v5 binary -> AST -> LaTeX.

Mọi thất bại đều trả về None để caller fallback sang ảnh WMF/PNG.
"""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import re
import struct
from dataclasses import dataclass, field

import olefile

from .exp_repair import repair_swallowed_exponent
from .latex_balance import balance_braces, trailing_close_is_orphan


# ---------------------------------------------------------------- record tags
END, LINE, CHAR, TMPL, PILE, MATRIX = 0, 1, 2, 3, 4, 5
EMBELL, RULER, FONT_STYLE_DEF, SIZE = 6, 7, 8, 9
FULL, SUB, SUB2, SYM, SUBSYM = 10, 11, 12, 13, 14
COLOR, COLOR_DEF, FONT_DEF, EQN_PREFS, ENCODING_DEF = 15, 16, 17, 18, 19

# CHAR option bits
xfAUTO, xfEMBELL, xfMOVE, xfNUDGE = 0x01, 0x02, 0x04, 0x08
# tag option bits (high nibble)
xfLSPACE, xfRULER, xfNULL = 0x04, 0x02, 0x08

TEX_MARK = b"TeX Input Language\x00"
_LAST_SEL: set[int] = set()   # selector của lần decode gần nhất (cho confidence)

# Cờ trong BYTE OPTIONS RIÊNG của từng record (đúng spec MTEF v5).
# Khác với các hằng xf* cũ vốn được so với nibble cao của tag — phép so đó luôn
# bằng 0 nên các nhánh null/lspace/ruler thực tế CHƯA BAO GIỜ chạy.
OPT_NUDGE = 0x08
OPT_LINE_NULL = 0x01
OPT_LINE_RULER = 0x02
OPT_LINE_LSPACE = 0x04
# Cờ của record CHAR
OPT_CHAR_EMBELL = 0x01
OPT_CHAR_FUNC_START = 0x02
OPT_CHAR_ENC8 = 0x04
OPT_CHAR_ENC16 = 0x10
OPT_CHAR_NO_MTCODE = 0x20


# Glyph chỉ gồm ký tự ngoặc (kể cả dạng đã escape) -> là dấu của ngoặc rỗng.
_ONLY_BRACKETS = re.compile(r"(?:\\[\{\}|]|[(){}\[\]|\s])+")
# Đuôi chỉ gồm ký tự ngoặc -> glyph dấu của template, cắt bỏ.
_TRAILING_BRACKETS = re.compile(r"(?:\\[\{\}|]|[(){}\[\]|\s])+$")


class Trunc(Exception):
    pass


# ------------------------------------------------------------------- symbols
SYMBOLS = {
    0x2208: r"\in", 0x2209: r"\notin", 0x2282: r"\subset", 0x2284: r"\not\subset",
    0x2283: r"\supset", 0x2286: r"\subseteq", 0x2287: r"\supseteq",
    0x2229: r"\cap", 0x222A: r"\cup", 0x2205: r"\varnothing", 0x2216: r"\setminus",
    0x2200: r"\forall", 0x2203: r"\exists", 0x2261: r"\equiv",
    0x2264: r"\le", 0x2265: r"\ge", 0x2260: r"\ne", 0x2248: r"\approx",
    0x00B1: r"\pm", 0x2213: r"\mp", 0x00D7: r"\times", 0x00F7: r"\div",
    0x221E: r"\infty", 0x221A: r"\sqrt", 0x2211: r"\sum", 0x220F: r"\prod",
    0x222B: r"\int", 0x2202: r"\partial", 0x2207: r"\nabla",
    0x2192: r"\to", 0x2190: r"\leftarrow", 0x21D2: r"\Rightarrow",
    0x21D4: r"\Leftrightarrow", 0x2194: r"\leftrightarrow",
    0x2227: r"\wedge", 0x2228: r"\vee", 0x00AC: r"\neg",
    0x2225: r"\parallel", 0x22A5: r"\perp", 0x2220: r"\angle",
    0x2032: r"'", 0x2033: r"''", 0x22EF: r"\cdots", 0x2026: r"\ldots",
    0x22C5: r"\cdot", 0x2022: r"\bullet", 0x25A1: r"\square",
    0x2115: r"\mathbb{N}", 0x2124: r"\mathbb{Z}", 0x211A: r"\mathbb{Q}",
    0x211D: r"\mathbb{R}", 0x2102: r"\mathbb{C}",
    0x03B1: r"\alpha", 0x03B2: r"\beta", 0x03B3: r"\gamma", 0x03B4: r"\delta",
    0x03B5: r"\varepsilon", 0x03B8: r"\theta", 0x03BB: r"\lambda", 0x03BC: r"\mu",
    0x03C0: r"\pi", 0x03C1: r"\rho", 0x03C3: r"\sigma", 0x03C4: r"\tau",
    0x03C6: r"\varphi", 0x03C9: r"\omega", 0x0394: r"\Delta", 0x03A9: r"\Omega",
    0x2245: r"\cong", 0x223C: r"\sim", 0x2212: r"-", 0x2044: r"/",
}

# TCVN3 (ABC) byte mapping cho font .VnTime dùng trong MathType
TCVN3_MAP = {
    0xB5: "à", 0xB6: "á", 0xB7: "ả", 0xB8: "ã", 0xB9: "ạ",
    0xCA: "ă", 0xBB: "ằ", 0xBC: "ắ", 0xBD: "ẳ", 0xBE: "ẵ", 0xC6: "ặ",
    0xC7: "â", 0xC8: "ầ", 0xC9: "ấ", 0xCB: "ẩ", 0xCC: "ẫ", 0xCE: "ậ",
    0xCF: "đ", 0xD2: "è", 0xD3: "é", 0xD4: "ẻ", 0xD5: "ẽ", 0xD6: "ẹ",
    0xD7: "ê", 0xD8: "ề", 0xDC: "ế", 0xDD: "ể", 0xDE: "ễ", 0xE1: "ệ",
    0xE2: "ì", 0xE3: "í", 0xE4: "ỉ", 0xE5: "ĩ", 0xE6: "ị",
    0xE7: "ò", 0xE8: "ó", 0xE9: "ỏ", 0xEA: "õ", 0xEB: "ọ",
    0xEC: "ô", 0xED: "ồ", 0xEE: "ố", 0xEF: "ổ", 0xF1: "ỗ", 0xF2: "ộ",
    0xF3: "ơ", 0xF4: "ờ", 0xF5: "ớ", 0xF6: "ở", 0xF7: "ỡ", 0xF8: "ợ",
    0xF9: "ù", 0xFA: "ú", 0xFB: "ủ", 0xFC: "ũ", 0xFD: "ụ",
    0xFE: "ư", 0x9F: "ừ", 0xA1: "ứ", 0xA2: "ử", 0xA3: "ữ", 0xA4: "ự",
    0xA5: "ỳ", 0xA6: "ý", 0xA7: "ỷ", 0xA8: "ỹ", 0xA9: "ỵ",
    0xAE: "Đ", 0xAB: "Ô", 0xAC: "Ư"
}

FUNCS = ("arcsin", "arccos", "arctan", "sin", "cos", "tan", "cot", "sec",
         "csc", "log", "ln", "lim", "min", "max", "exp", "gcd", "deg")
ESCAPE = {"\\": r"\setminus ", "{": r"\{", "}": r"\}", "%": r"\%", "$": r"\$", "&": r"\&",
          "#": r"\#", "_": r"\_", "^": r"\hat{}", "~": r"\tilde{}"}

# Bảng selector MTEF (tmSELECTOR) đo trực tiếp trên corpus dữ liệu thật.
TM_ANGLE, TM_PAREN, TM_BRACE, TM_BRACK, TM_BAR, TM_DBAR, TM_FLOOR, TM_CEILING = 0, 1, 2, 3, 4, 5, 6, 7
TM_OBRACK, TM_INTERVAL = 8, 9
TM_ROOT, TM_FRACT = 10, 11
TM_SCRIPT = 12
TM_UBAR, TM_OBAR, TM_ARROW = 13, 14, 15
TM_INTEG, TM_SUM, TM_PROD, TM_COPROD, TM_UNION, TM_INTER, TM_INTOP = 16, 17, 18, 19, 20, 21, 22
TM_SUMOP = 230
TM_LIM = 23            # ĐO THẬT: 161/161 công thức lim có selector = 23
TM_HBRACE, TM_HBRACK, TM_LDIV, TM_VEC, TM_TILDE, TM_HAT, TM_STRIKE, TM_BOX = 24, 25, 26, 30, 31, 32, 34, 35
TM_SUB, TM_SUP, TM_SUBSUP = 27, 28, 29   # ĐO THẬT: 27=SUB (chỉ số dưới), 28=SUP (chỉ số trên), 29=SUBSUP

FENCES = {
    TM_PAREN: ("(", ")"), TM_BRACK: ("[", "]"),
    TM_BRACE: (r"\{", r"\}"), TM_ANGLE: (r"\langle", r"\rangle"),
    TM_BAR: ("|", "|"), TM_DBAR: (r"\|", r"\|"),
    TM_FLOOR: (r"\lfloor", r"\rfloor"), TM_CEILING: (r"\lceil", r"\rceil"),
}

SAFE_SELECTORS: set[int] = {
    TM_ANGLE, TM_PAREN, TM_BRACE, TM_BRACK, TM_BAR, TM_DBAR, TM_FLOOR,
    TM_CEILING, TM_OBRACK, TM_INTERVAL, TM_ROOT, TM_FRACT, TM_SCRIPT,
    TM_SUB, TM_SUP, TM_SUBSUP,
    TM_UBAR, TM_OBAR, TM_ARROW, TM_INTEG, TM_SUM, TM_PROD, TM_COPROD,
    TM_UNION, TM_INTER, TM_INTOP, TM_SUMOP, TM_LIM, TM_HBRACE, TM_HBRACK,
    TM_LDIV, TM_VEC, TM_TILDE, TM_HAT, TM_STRIKE, TM_BOX
}


def confidence_of(source: str, used_sel: set[int]) -> float:
    if source == "tex":
        return 1.0
    if source == "omml":
        return 1.0
    if not used_sel:
        return 0.98          # chuỗi CHAR thuần
    return 0.93              # có template trong allowlist


def _brace(s: str) -> str:
    return "{" + s + "}"


@dataclass
class Ctx:
    fonts: list = field(default_factory=list)


_ROW_SEP = "\x00PILE_ROW\x00"   # sentinel nội bộ, không bao giờ lọt ra ngoài LaTeX thật


def _join_tokens(parts: list[str]) -> str:
    """Join token parts cleanly without putting spaces between CHAR tokens like 'c' 'o' 's' -> 'cos' or '1' '8' '0' -> '180'.
    Only insert spaces when a control word ending in a letter (e.g. \\alpha) precedes an alphanumeric character.
    """
    if not parts:
        return ""
    result = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if not result:
            result.append(p)
            continue
        prev = result[-1]
        if prev and prev.startswith('\\') and prev[-1].isalpha() and not prev.endswith('}') and p and (p[0].isalnum() or p[0] == '\\'):
            result.append(" " + p)
        else:
            result.append(p)
    return "".join(result).strip()



class MTEFParser:
    def __init__(self, data: bytes):
        self.d = data
        self.i = 0
        self.fonts: list[str] = []
        self.used_sel: set[int] = set()   # selector template đã dùng
        self.saw_pile = False             # ma trận/hệ pt: chưa verify
        self._pile_split_active = False   # đang quét nội dung 1 PILE (xem rec == PILE)
        self._tmpl_nest = 0                # đang ở trong ô con của 1 TMPL (frac/sqrt/mũ...)
        self._fence_nest = 0               # đang ở trong template dấu ngoặc FENCES

    def u8(self) -> int:
        if self.i >= len(self.d):
            raise Trunc
        v = self.d[self.i]
        self.i += 1
        return v

    def u16(self) -> int:
        if self.i + 2 > len(self.d):
            raise Trunc
        v = struct.unpack_from("<H", self.d, self.i)[0]
        self.i += 2
        return v

    def cstr(self) -> str:
        out = bytearray()
        while True:
            c = self.u8()
            if c == 0:
                break
            out.append(c)
        return out.decode("latin1")

    def nibble_values(self, count: int) -> None:
        nib, hi = self.i * 2, True
        got = 0
        while got < count:
            byte = self.d[nib // 2]
            v = (byte >> 4) if nib % 2 == 0 else (byte & 0x0F)
            nib += 1
            if v == 0x0F:
                got += 1
            if nib // 2 >= len(self.d):
                raise Trunc
        self.i = (nib + 1) // 2 if nib % 2 else nib // 2

    def read_header(self) -> str | None:
        ver = self.u8()
        self.u8(), self.u8(), self.u8(), self.u8()  # platform, product, ver, subver
        if ver != 5:
            return None
        self.cstr()   # application key, vd "DSMT6"
        self.u8()     # equation options
        return "ok"

    def skip_preamble(self) -> None:
        while True:
            save = self.i
            tag = self.u8()
            if tag == ENCODING_DEF:
                self.cstr()
            elif tag == FONT_DEF:
                self.u8()
                self.fonts.append(self.cstr())
            elif tag == EQN_PREFS:
                self.u8()                       # options
                self.nibble_values(self.u8())   # sizes
                self.nibble_values(self.u8())   # spacing
                self.i += self.u8() * 2         # styles: (font, style) pairs
            elif tag >= 100:                    # FUTURE record: [tag][len][data]
                self.i += self.u8()
            elif tag == END:
                continue
            else:
                self.i = save
                return

    def _format_pile(self, rows: list[str]) -> str:
        rows = [r.strip() for r in rows if r.strip()]
        if not rows:
            return ""
        if len(rows) == 1:
            return rows[0]

        # Check one-sided limit sign transfer (e.g., rows[0] is \lim_{x\to x0} and rows[1] is ^{+}f(x)=...)
        if len(rows) >= 2 and re.search(r"\\lim_\{.*?\\to\s*[^\}]+\}", rows[0]):
            r1 = rows[1].strip()
            if r1.startswith("^+") or r1.startswith("^-") or r1.startswith("^{+}") or r1.startswith("^{-}"):
                sign = "+" if "+" in r1[:5] else "-"
                rows[1] = re.sub(r"^\^?\{?[+-]\}?\s*", "", r1).strip()
                rows[0] = re.sub(r"(\\to\s*[^\}]+)", r"\1" + sign, rows[0], count=1)

        # Pattern 1: Operator with subscript split into rows (\lim, \max, \min, \sup, \inf)
        first_row = rows[0]
        match_op = re.search(r"(\\?(?:lim|max|min|sup|inf))(?![a-zA-Z])", first_row)
        if match_op and "_" not in first_row and len(rows) >= 2:
            op_str = match_op.group(1)
            latex_op = op_str if op_str.startswith("\\") else "\\" + op_str
            
            # Check if first_row already contains domain right after operator
            m_inline = re.search(r"(\\?(?:lim|max|min|sup|inf))\s*(\\left\[.*?\\right\]|\\left\(.*?\\right\)|\[.*?\]|\(.*?\))", first_row)
            if m_inline:
                op_name = m_inline.group(1)
                domain = m_inline.group(2)
                l_op = op_name if op_name.startswith("\\") else "\\" + op_name
                new_first = first_row.replace(m_inline.group(0), l_op + r"_{" + domain + r"}")
                rest = " ".join(rows[1:])
                return new_first + (" " + rest if rest else "")

            sub_idx = 1
            if len(rows) > 2:
                r1, r2 = rows[1], rows[2]
                r2_is_domain = any(r2.strip().startswith(p) for p in [r"\left[", "[", r"\left(", "(", "x", "D", r"\mathbb", r"\{-", "[-"])
                r1_is_domain = any(r1.strip().startswith(p) for p in [r"\left[", "[", r"\left(", "(", "x", "D", r"\mathbb", r"\{-", "[-"])
                if r2_is_domain and not r1_is_domain:
                    sub_idx = 2

            sub_part = rows[sub_idx]
            other_rows = [rows[i] for i in range(1, len(rows)) if i != sub_idx]
            rest = " ".join(other_rows)

            if op_str in first_row:
                new_first = first_row.replace(op_str, latex_op + r"_{" + sub_part + r"}")
            else:
                new_first = first_row + r"_{" + sub_part + r"}"

            return new_first + (" " + rest if rest else "")

        # If inside a fence (like \left\{ or \left[) -> It's a system of equations / cases!
        if self._fence_nest > 0:
            return r"\begin{array}{l}" + r"\\".join(rows) + r"\end{array}"

        # Check if any row is a continuation row starting with an operator (<, >, =, +, -, ,, ;, \cup, \cap, \subset, \in, etc.)
        continuation_ops = ["<", ">", "=", "+", "-", ",", ";", ".", r"\cup", r"\cap", r"\setminus", r"\in", r"\notin", r"\subset", r"\supset", r"\notsubset", r"\to", r"\Rightarrow", r"\Leftrightarrow", r"\iff", r"\implies"]
        has_continuation = any(r.startswith(op) for r in rows[1:] for op in continuation_ops)
        if not has_continuation:
            eq_count = sum(1 for r in rows if any(op in r for op in ["=", r"\le", r"\ge", r"\approx", r"\ne", r"\iff", r"\implies", r"\Leftrightarrow", r"\Rightarrow"]))
            has_limit_op = any(re.search(r"\\?(?:lim|max|min|sup|inf)(?![a-zA-Z])", r) for r in rows)
            if eq_count >= len(rows) and len(rows) >= 2 and not has_limit_op:
                return r"\begin{array}{l}" + r"\\".join(rows) + r"\end{array}"

        # Otherwise, it's a soft-broken inline expression -> Join horizontally!
        joined = ""
        for r in rows:
            if not joined:
                joined = r
            elif r.startswith(",") or r.startswith(";") or r.startswith("."):
                joined += r
            else:
                joined += " " + r
        return joined

    def parse_slot(self, depth: int = 0, collect_lines: list[str] | None = None) -> str:
        """Đọc nội dung của MỘT khung (frame) cho tới record END của chính nó.

        `collect_lines` bật ngữ nghĩa "khung của TEMPLATE": mỗi record LINE con là
        MỘT Ô RIÊNG của template, được gom vào danh sách này thay vì nối vào chuỗi.

        Vì sao cần: trong MTEF, TMPL và LINE đều là khung tự đóng bằng END của
        riêng nó, còn các ô của template chính là các LINE con. Cách cũ cho
        parse_tmpl gọi parse_slot() một lần cho MỖI ô khiến số END bị lệch: lần
        đệ quy vào LINE ăn mất END của template, nên ô số mũ không còn dấu kết
        thúc và nuốt tiếp phần sau của dòng cha —
            cos3x = cos³x − sin³x   ->   cos3x=cos^{3x-sin^{3x.}}
        Đây là RC2 (desync biên slot), KHÔNG phải lỗi gõ của người soạn: bộ giải
        mã độc lập MTEF-py đọc đúng cùng file này.
        """
        if depth > 24:
            raise Trunc
        out: list[str] = []
        pile_array_idx: int | None = None
        while True:
            if self.i >= len(self.d):
                break
            tag = self.u8()
            if tag >= 16:
                if tag == COLOR_DEF:
                    # COLOR_DEF = options(1) + giá trị màu + [tên nếu cờ NAME].
                    # CMYK -> 4 × uint16 (8 byte); còn lại RGB -> 3 × uint16 (6 byte).
                    #
                    # Bản cũ đọc 2 byte cho RGB rồi LUÔN gọi cstr(), tức hụt 3 byte
                    # mỗi lần gặp record này. Chỉ một COLOR_DEF nằm giữa thân là đủ
                    # làm lệch toàn bộ TMPL/LINE phía sau, khiến nội dung trong ngoặc
                    # trôi ra ngoài và để lại cặp ngoặc rỗng:
                    #     \{0;1;2\}   ->   0;1;2 \{\}
                    c_opt = self.u8()
                    self.i += 8 if (c_opt & 0x01) else 6
                    if c_opt & 0x04:            # mtefCOLOR_NAME
                        self.cstr()
                    continue
                if tag == FONT_DEF:
                    self.u8(); self.cstr(); continue
                if tag == ENCODING_DEF:
                    self.cstr(); continue
                if tag == EQN_PREFS:
                    self.u8()
                    self.nibble_values(self.u8())
                    self.nibble_values(self.u8())
                    self.i += self.u8() * 2
                    continue
                if tag >= 100:
                    self.i += self.u8(); continue
                raise Trunc
            rec, opt = tag & 0x0F, tag & 0xF0
            if rec == END:
                break
            elif rec == LINE:
                # LINE có BYTE OPTIONS RIÊNG, giống CHAR và TMPL — không phải
                # nibble cao của tag. Cờ null/lspace/ruler nằm trong byte đó:
                #     0x01 null · 0x02 ruler · 0x04 lspace · 0x08 nudge
                # Đọc thiếu byte này làm lệch 1 byte cho mọi record phía sau,
                # nên \frac{x}{2} đọc ra thành "x2" (ô tử/mẫu rỗng).
                lopt = self.u8()
                if lopt & OPT_NUDGE:
                    self.i += 4
                if lopt & OPT_LINE_LSPACE:
                    self.u8()
                if lopt & OPT_LINE_RULER:
                    self.skip_ruler()
                if lopt & OPT_LINE_NULL:
                    # Dòng rỗng: KHÔNG có nội dung và KHÔNG có END của riêng nó.
                    if collect_lines is not None:
                        collect_lines.append("")
                    continue
                piece = self.parse_slot(depth + 1)
                if collect_lines is not None:
                    # Khung TEMPLATE: mỗi LINE con là một Ô riêng của template.
                    collect_lines.append(piece)
                    continue
                # Ranh giới dòng thật của 1 PILE (hệ pt/nhiều dòng công thức
                # gõ trong CÙNG 1 khung MathType) không nằm ở 1 record END
                # riêng — nó xen giữa dòng dữ liệu dưới dạng 1 record LINE
                # (opt=0, giống hệt LINE bình thường) mà nội dung đọc ra
                # RỖNG. Coi rỗng == ngắt dòng CHỈ khi đang thật sự quét nội
                # dung 1 PILE (`_pile_split_active`) và KHÔNG đang ở trong ô
                # con của 1 template khác (`_tmpl_nest == 0`, xem parse_tmpl)
                # — nếu không sẽ nuốt nhầm các LINE rỗng vốn chỉ là nội bộ
                # của template khác (VD nửa dưới rỗng của 1 số mũ TM_SUP),
                # biến chúng thành dấu ngắt dòng giả, làm rách nội dung nằm
                # giữa 1 cặp {..} không liên quan gì tới PILE.
                if self._pile_split_active and self._tmpl_nest == 0 and piece == "":
                    out.append(_ROW_SEP)
                else:
                    out.append(piece)
            elif rec == CHAR:
                out.append(self.parse_char())
            elif rec == TMPL:
                _t = self.parse_tmpl(depth, opt)
                (collect_lines if collect_lines is not None else out).append(_t)
            elif rec == PILE:
                # PILE = nhiều dòng công thức trong CÙNG 1 khung MathType
                # (hệ phương trình, danh sách nghiệm...).
                #
                #   PILE = options(1) [nudge(4)] halign(1) valign(1)
                #          rồi MỖI DÒNG là một record LINE con, đóng bằng END
                #          của chính PILE — y hệt ô của TMPL và MATRIX.
                #
                # Bản cũ bỏ qua byte options nên đọc lệch 1 byte, và vì thế
                # không thấy được ranh giới dòng thật; nó phải đoán bằng cách
                # coi "LINE rỗng" là dấu ngắt dòng (_ROW_SEP / _pile_split_active).
                # Phỏng đoán đó hỏng: các dòng bị nối liền không dấu ngăn —
                #     y>0  và  3x+2y<6   ->   "y>03x+2y<6"
                # Đọc đúng header thì mỗi LINE con CHÍNH LÀ một dòng, không cần
                # đoán gì nữa.
                self.saw_pile = True
                p_opt = self.u8()
                if p_opt & OPT_NUDGE:
                    self.i += 4
                self.u8()          # halign
                self.u8()          # valign
                # Cờ 0x02 = có RULER đi ngay sau valign. Bỏ qua nó thì lệch 4 byte
                # và toàn bộ các dòng của hệ biến mất, chỉ còn lại dấu "\{":
                #     04 02 | 01 halign | 01 valign | 01 00 ba 07 ruler | 01 00 LINE...
                # MTEF-py cũng không đọc ruler ở đây, nên không dùng đối chiếu được.
                if p_opt & OPT_LINE_RULER:
                    self.skip_ruler()
                rows: list[str] = []
                self.parse_slot(depth + 1, collect_lines=rows)
                rows = [r for r in rows if r.strip()]
                if not rows:
                    rows = [""]
                pile_str = self._format_pile(rows) if len(rows) > 1 else rows[0]
                if collect_lines is not None:
                    # PILE nằm THẲNG trong khung template (hệ phương trình:
                    # TMPL(BRACE) -> PILE -> các dòng) là NỘI DUNG của template,
                    # không phải glyph dấu ngoặc. Chỉ record CHAR mới là glyph.
                    collect_lines.append(pile_str)
                else:
                    out.append(pile_str)
                    if len(rows) > 1 and r"\begin{array}" in pile_str:
                        pile_array_idx = len(out) - 1
            elif rec == MATRIX:
                # MATRIX = options(1) [nudge(4)] valign(1) h_just(1) v_just(1)
                #          rows(1) cols(1) row_parts col_parts, rồi rows*cols ô.
                #
                # row_parts/col_parts là mảng BIT: 2 bit cho mỗi đường phân vùng,
                # có rows+1 (và cols+1) đường -> ceil((n+1)/4) byte.
                #
                # Bản cũ bỏ qua byte options và cả v_just, nên đọc lệch 2 byte và
                # lấy ra rows=0, cols=1 cho ma trận 2×1 thật — ma trận vì thế bị
                # coi là một ô đơn và nội dung các hàng trôi ra ngoài.
                # MTEF-py cũng sai chỗ này: nó không đọc row_parts/col_parts.
                m_opt = self.u8()
                if m_opt & OPT_NUDGE:
                    self.i += 4
                self.u8()          # valign
                self.u8()          # h_just
                self.u8()          # v_just
                rows = self.u8()
                cols = self.u8()
                # rowParts/colParts không phải 1 byte/phần tử (như code cũ
                # giả định) — đây là mảng nibble-encoded kết thúc bằng
                # sentinel 0xF, giống cách EQN_PREFS lưu sizes/spacing. Nhảy
                # sai số byte khiến con trỏ rơi vào slack/"Root Entry" của
                # OLE Compound File phía sau, sinh ra hàng chục cột rỗng.
                if rows > 32 or cols > 32:
                    raise Trunc
                self.i += (rows + 1 + 3) // 4      # row_parts: 2 bit × (rows+1)
                self.i += (cols + 1 + 3) // 4      # col_parts: 2 bit × (cols+1)
                n_rows, n_cols = (rows if rows > 0 else 1), (cols if cols > 0 else 1)
                # Ô của ma trận cũng là các record LINE con, đóng bằng END của
                # chính MATRIX — giống hệt ô của template, nên dùng chung cơ chế.
                cells: list[str] = []
                self.parse_slot(depth + 1, collect_lines=cells)
                while len(cells) < n_rows * n_cols:
                    cells.append("")
                matrix_rows = [
                    " & ".join(cells[r * n_cols:(r + 1) * n_cols])
                    for r in range(n_rows)
                ]
                if collect_lines is not None:
                    collect_lines.append(
                        matrix_rows[0] if (n_rows == 1 and n_cols == 1)
                        else r"\begin{matrix}" + r"\\".join(matrix_rows) + r"\end{matrix}")
                elif n_rows == 1 and n_cols == 1:
                    # MathType dùng record MATRIX cả cho trường hợp chỉ 1 ô
                    # (không phải ma trận thật) — bọc \begin{matrix} ở đây
                    # cho ra LaTeX vô nghĩa (VD "\Delta y\begin{matrix}>0...
                    # \end{matrix}"), nên chỉ nối thẳng nội dung ô.
                    out.append(matrix_rows[0])
                else:
                    out.append(r"\begin{matrix}" + r"\\".join(matrix_rows) + r"\end{matrix}")
            elif rec == EMBELL:
                emb_opt = self.u8()
                if (opt & xfNUDGE) or (emb_opt & xfNUDGE):
                    self.i += 2
                eb = self.u8()
                out.append("'" if eb in (5, 6, 7, 8) else "")
            elif rec == RULER:
                self.skip_ruler()
            elif rec in (FULL, SUB, SUB2, SYM, SUBSYM):
                continue
            elif rec == COLOR:
                self.u8()
            elif rec == FONT_STYLE_DEF:
                self.u8(); self.u8()
            elif tag == FONT_DEF:
                self.u8(); self.cstr()
            elif tag == ENCODING_DEF:
                self.cstr()
            elif tag >= 100:
                self.i += self.u8()
            else:
                raise Trunc
        if pile_array_idx is not None and pile_array_idx != len(out) - 1:
            tail = "".join(out[pile_array_idx + 1:]).strip()
            if tail:
                head = out[pile_array_idx]
                assert head.endswith(r"\end{array}")
                out[pile_array_idx] = head[: -len(r"\end{array}")] + r"\\" + tail + r"\end{array}"
            del out[pile_array_idx + 1:]
        return "".join(out)

    def skip_ruler(self) -> None:
        n = self.u8()
        self.i += n * 3

    def parse_char(self) -> str:
        """CHAR = options [nudge] typeface [mtcode] [bits8] [bits16] (spec MTEF v5).

        Ba chỗ bản cũ đọc sai, mỗi chỗ đều làm LỆCH BYTE cho mọi record phía sau:
          * nudge dài 4 byte (2 toạ độ × 2), không phải 2;
          * mtcode CHỈ có mặt khi cờ NoMtcode TẮT — bản cũ luôn đọc 2 byte;
          * thiếu hẳn nhánh EncChar16 (2 byte).
        Cờ 0x04 cũng không phải "move" mà là EncChar8 (1 byte ký tự 8-bit).
        """
        o = self.u8()
        if o & OPT_NUDGE:
            self.i += 4
        tf = self.u8()
        code = 0
        if not (o & OPT_CHAR_NO_MTCODE):
            code = self.u16()
        if o & OPT_CHAR_ENC8:
            self.i += 1
        if o & OPT_CHAR_ENC16:
            self.i += 2
        return self.render_char(code, tf)

    def render_char(self, code: int, typeface: int = 0) -> str:
        MATHTYPE_VARS = {
            0x0200: 'x', 0x0201: 'y', 0x0202: 'z', 0x0203: 'a', 0x0204: 'b', 0x0205: 'c',
            0x0206: 'd', 0x0207: 'e', 0x0208: 'f', 0x0209: 'g', 0x020A: 'h', 0x020B: 'i',
            0x020C: 'j', 0x020D: 'k', 0x020E: 'l', 0x020F: 'm', 0x0210: 'n', 0x0211: 'o',
            0x0212: 'p', 0x0213: 'q', 0x0214: 'r', 0x0215: 's', 0x0216: 't', 0x0217: 'u',
            0x0218: 'v', 0x0219: 'w',
            0x021A: 'A', 0x021B: 'B', 0x021C: 'C', 0x021D: 'D', 0x021E: 'E', 0x021F: 'F',
            0x0220: 'G', 0x0221: 'H', 0x0222: 'I', 0x0223: 'J', 0x0224: 'K', 0x0225: 'L',
            0x0226: 'M', 0x0227: 'N', 0x0228: 'O', 0x0229: 'P', 0x022A: 'Q', 0x022B: 'R',
            0x022C: 'S', 0x022D: 'T', 0x022E: 'U', 0x022F: 'V', 0x0230: 'W', 0x0231: 'X',
            0x0232: 'Y', 0x0233: 'Z'
        }
        if code in MATHTYPE_VARS:
            return MATHTYPE_VARS[code]
        if typeface < len(self.fonts) and self.fonts[typeface].lower().startswith(".vn"):
            b = code & 0xFF
            if b in TCVN3_MAP:
                return TCVN3_MAP[b]
            if code in TCVN3_MAP:
                return TCVN3_MAP[code]
        if code in SYMBOLS:
            v = SYMBOLS[code]
            return v + " " if v.startswith("\\") else v
        ch = chr(code)
        if ch in ESCAPE:
            v = ESCAPE[ch]
            return v + " " if re.fullmatch(r"\\[A-Za-z]+", v) else v
        if code < 32 or code == 0xFFFD or (0xE000 <= code <= 0xF8FF):
            if code in (0xEC80, 0xEC81, 0xEC82, 0xEC83, 0xEC84, 0xEC85, 0xEC00, 0xEC01):
                return " "
            b = code & 0xFF
            if b in TCVN3_MAP:
                return TCVN3_MAP[b]
            if b in SYMBOLS:
                v = SYMBOLS[b]
                return v + " " if v.startswith("\\") else v
            if b in MATHTYPE_VARS:
                return MATHTYPE_VARS[b]
            if 0x20 <= b <= 0x7E:
                ch_b = chr(b)
                if ch_b in ESCAPE:
                    v = ESCAPE[ch_b]
                    return v + " " if re.fullmatch(r"\\[A-Za-z]+", v) else v
                return ch_b
            return ""
        return ch

    def parse_tmpl(self, depth: int, tag_opt: int = 0) -> str:
        """TMPL = [tag][options][selector][variation:u16] rồi tới các ô con.

        Khung TMPL kết thúc bằng END của chính nó, và bên trong có hai loại con:
          * record LINE   -> các Ô của template (số mũ, tử, mẫu, nội dung ngoặc)
          * record CHAR   -> KÝ TỰ NỘI BỘ của template, KHÔNG phải nội dung

        Loại thứ hai phải bị BỎ. Đó là các glyph mà MathType lưu kèm để biết vẽ
        dấu gì — ví dụ khung TM_PAREN của `A(-3;-4)` chứa LINE('-3;-4') rồi hai
        CHAR '(' và ')'. Giữ chúng lại sẽ sinh ngoặc rỗng lặp:
            A(-3;-4)()      f'(x)()=x(x+1)()(x-4)()^{3}      ...=0\\}\\{\\}
        Bộ giải mã độc lập MTEF-py cũng bỏ đúng nhóm CHAR này.

        Nội dung đứng SAU template (như `x - sin³x` trong `cos³x - sin³x`) nằm
        NGOÀI khung, do dòng cha đọc tiếp — không phải phần dư ở đây.
        """
        rendered, glyphs = self._parse_tmpl_parts(depth, tag_opt)
        if rendered:
            return rendered
        # Template rỗng: khi đó chính glyph nội bộ mới mang nghĩa — ví dụ mũi tên
        # `\to` gõ một mình (ô nhãn phía trên để trống). Nhưng KHÔNG lấy lại nếu
        # glyph chỉ toàn ký tự ngoặc, vì đó là dấu của một ngoặc rỗng và trả về
        # sẽ tái sinh đúng "()" / "\{\}" mà ta vừa loại bỏ.
        g = glyphs.strip()
        if g and not _ONLY_BRACKETS.fullmatch(g):
            return g
        return ""

    def _parse_tmpl_parts(self, depth: int, tag_opt: int = 0) -> tuple[str, str]:
        # Header TMPL theo đúng spec MTEF v5:
        #     options(1) [nudge(4)] selector(1) variation(1 HOẶC 2) options(1)
        # `variation` chỉ dài 2 byte khi bit 0x80 của byte đầu được bật.
        #
        # Code cũ đọc variation bằng u16 CỐ ĐỊNH và bỏ qua byte options cuối.
        # Khi variation < 0x80 thì tổng số byte tình cờ bằng nhau (1+1+2 = 1+1+1+1)
        # nên vẫn chạy; nhưng khi bit 0x80 bật thì LỆCH ĐÚNG 1 BYTE, làm hỏng
        # mọi record phía sau — đó là lý do \frac{x}{2} đọc ra thành "x2".
        opts = self.u8()
        if opts & xfNUDGE:
            self.i += 4
        sel = self.u8()            # selector THẬT
        b1 = self.u8()
        if b1 & 0x80:
            var = (b1 & 0x7F) | (self.u8() << 8)
        else:
            var = b1
        self.u8()                  # options byte đứng SAU variation
        self.used_sel.add(sel)

        slots: list[str] = []
        if sel in FENCES or sel in (TM_OBRACK, TM_INTERVAL):
            self._fence_nest += 1
        try:
            # TMPL là một khung tự đóng bằng END của chính nó; các ô của nó là
            # các record LINE con. Đọc MỘT lần cho tới END đó và gom LINE con
            # thành các ô — thay vì gọi parse_slot() một lần cho mỗi ô, vốn làm
            # lệch số END và khiến ô nuốt phần sau của dòng cha.
            self._tmpl_nest += 1
            try:
                trailing = self.parse_slot(depth + 1, collect_lines=slots)
            finally:
                self._tmpl_nest -= 1
        finally:
            if sel in FENCES or sel in (TM_OBRACK, TM_INTERVAL):
                self._fence_nest -= 1

        while len(slots) < 3:
            slots.append("")
        a, b, c = slots[0], slots[1], slots[2]

        if sel in FENCES or sel in (TM_OBRACK, TM_INTERVAL):
            if not a or not a.strip():  # không bao giờ sinh ngoặc rỗng (), [], {}
                return "", trailing
            if sel in FENCES:
                lo, hi = FENCES[sel]
                # variation cho biết BÊN NÀO thật sự có dấu ngoặc:
                #   bit 0x01 = có ngoặc trái, bit 0x02 = có ngoặc phải.
                # Hệ phương trình gõ bằng MathType có var=1 (chỉ ngoặc nhọn TRÁI),
                # còn tập hợp \{0;1;2\} có var=3 (cả hai). Bản cũ luôn in cả hai nên
                # hệ bị đóng ngoặc phải — sai ký hiệu toán:
                #     \left\{...\right\}   thay vì   \left\{...\right.
                has_l, has_r = bool(var & 0x01), bool(var & 0x02)
            else:
                lo = "[" if (var & 1) else "("
                hi = "]" if (var & 4) else ")"
                has_l = has_r = True

            if has_l and has_r and not any(
                k in a for k in [r"\frac", r"\begin", r"\int", r"\sum", r"\matrix", r"\\", r"\sqrt"]
            ):
                return lo + a + hi, trailing
            left = r"\left" + (lo if has_l else ".")
            right = r"\right" + (hi if has_r else ".")
            return left + a + right, trailing

        if sel == TM_ROOT:
            # Slot a = chỉ số (index), slot b = biểu thức dưới căn (radicand).
            # Nhưng MathType nhiều chỗ dồn radicand vào slot a và để b RỖNG, sinh ra
            # \sqrt[2-\sqrt{2}]{} — KaTeX chết vì thiếu đối số của macro.
            # Radicand rỗng thì luôn là hỏng, nên coi a chính là radicand.
            if not b.strip() and a.strip():
                return r"\sqrt" + _brace(a), trailing
            return (r"\sqrt" + _brace(b)) if not a else (r"\sqrt[" + a + "]" + _brace(b)), trailing
        if sel == TM_FRACT:
            if not a.strip() and not b.strip():
                return "", trailing
            return r"\frac" + _brace(a) + _brace(b), trailing
        # TM_SUB / TM_SUP có HAI ô con: ô không dùng được MathType ghi là một
        # record LINE null, ô còn lại mới mang nội dung. Thứ tự không cố định,
        # nên lấy ô đầu tiên có nội dung thay vì mặc định slots[0]:
        #     TMPL sel=28 · LINE null · LINE → '3'   ==>   ^{3}
        if sel == TM_SUB:
            v = next((s for s in slots if s.strip()), "")
            return ("_{" + v + "}") if v else "", trailing
        if sel == TM_SUP:
            v = next((s for s in slots if s.strip()), "")
            return ("^{" + v + "}") if v else "", trailing
        if sel == TM_SUBSUP:
            if a in ("360", "180") or (a and "360" in a):
                if "\\circ" in b or b == "°":
                    return f" {a}^{{\\circ}}", trailing
            res = ""
            if a:
                res += "_{" + a + "}"
            if b:
                res += "^{" + b + "}"
            return res, trailing
        if sel == TM_SCRIPT:
            r = a
            if b:
                r += "_" + _brace(b)
            if c:
                r += "^" + _brace(c)
            return r, trailing
        # Các template trang trí một ô: ô RỖNG thì không sinh macro rỗng.
        # MathType hay để lại TM_OBAR rỗng giữa dòng, sinh ra "\overline{}\to"
        # — KaTeX render thành một gạch trên lơ lửng không có nội dung.
        # Đo được: selector 14 (TM_OBAR) là selector chưa khai báo fire nhiều
        # nhất (52 lần), và \overline{} chiếm 23/23 ca đối-số-rỗng của corpus.
        if sel in (TM_UBAR, TM_OBAR, TM_VEC, TM_ARROW, TM_TILDE, TM_HAT):
            if not a.strip():
                return "", trailing
            return {
                TM_UBAR: r"\underline",
                TM_OBAR: r"\overline",
                TM_VEC: r"\vec",
                TM_ARROW: r"\vec",
                TM_TILDE: r"\tilde",
                TM_HAT: r"\hat",
            }[sel] + _brace(a), trailing
        if sel == TM_STRIKE:
            if a == "=":
                return r"\ne ", trailing
        if sel == TM_BOX:
            return r"\boxed" + _brace(a), trailing
        if sel in (TM_SUM, TM_SUMOP):
            return r"\sum" + _sub(b) + _sup(c) + a, trailing
        if sel in (TM_PROD,):
            return r"\prod" + _sub(b) + _sup(c) + a, trailing
        if sel in (TM_INTEG, TM_INTOP):
            return r"\int" + _sub(b) + _sup(c) + a, trailing
        if sel == TM_UNION:
            return r"\bigcup" + _sub(b) + _sup(c) + a, trailing
        if sel == TM_INTER:
            return r"\bigcap" + _sub(b) + _sup(c) + a, trailing
        if sel == TM_LIM:
            # HAI ô: a = tên toán tử viết bằng ký tự thường ('lim', 'max', ...),
            # b = điều kiện dưới dấu ('x \to 3'). Bản cũ lấy nhầm a làm chỉ số
            # dưới và ĐÁNH RƠI điều kiện — MTEF-py cho thấy đúng phải là
            # \mathop{lim}\limits_{x→+∞}.
            op = "".join(a.split()).lower()
            name = {"lim": r"\lim", "max": r"\max", "min": r"\min",
                    "sup": r"\sup", "inf": r"\inf"}.get(op, r"\lim")
            cond = b.strip() or (a.strip() if not op.isalpha() else "")
            return (name + r"\limits_{" + cond + "}") if cond else name, trailing
        if sel == TM_HBRACE:
            return r"\underbrace" + _brace(a), trailing
        if sel == TM_HBRACK:
            return r"\overbrace" + _brace(a), trailing
        res = a
        if b:
            res += "_{" + b + "}"
        if c:
            res += "^{" + c + "}"
        if not res.strip():
            res = " ".join(_brace(s) for s in slots if s.strip())
        return res, trailing


_SLOTS = {
    TM_PAREN: 1, TM_BRACE: 1, TM_BRACK: 1, TM_ANGLE: 1, TM_BAR: 1, TM_DBAR: 1,
    TM_FLOOR: 1, TM_CEILING: 1, TM_OBAR: 1, 14: 1, 31: 1, 13: 1, 37: 1, 33: 1,
    TM_INTERVAL: 3, 9: 3,
    TM_ROOT: 2, TM_FRACT: 2, TM_SCRIPT: 3, TM_SUB: 1, TM_SUP: 1, TM_SUBSUP: 2,
    TM_LDIV: 2, TM_SUM: 3, TM_SUMOP: 3, TM_PROD: 3, TM_COPROD: 3,
    TM_INTEG: 3, TM_INTOP: 3, TM_UNION: 3, TM_INTER: 3, TM_LIM: 1,
    TM_HBRACE: 2, TM_HBRACK: 2,
}



def _sub(s: str) -> str:
    return ("_" + _brace(s)) if s else ""


def _sup(s: str) -> str:
    return ("^" + _brace(s)) if s else ""


_FUNCS_SORTED = sorted(FUNCS, key=len, reverse=True)
_FUNC_RE = re.compile(r"(?<!\\)(" + "|".join(_FUNCS_SORTED) + r")", re.IGNORECASE)

# "lim"/"max"/"min" (selector TM_LIM, xem render_tmpl) dính liền với biểu
# thức chỉ số dưới do tác giả gõ rời (VD "limx\to +\infty f(x)=y0" đáng ra
# là "\lim_{x\to +\infty }f(x)=y0"): _FUNC_RE không nhận ra "lim" ở đây vì
# theo ngay sau là 1 chữ cái (x). Ranh giới an toàn duy nhất suy ra được từ
# dữ liệu thô là điểm bắt đầu lời gọi hàm "f(" / "f\left(", hoặc điểm bắt
# đầu 1 dấu ngoặc vuông "\left[" / "[" bọc cả biểu thức phía sau (VD
# "limx\to -\infty \left[f(x)\right]-(ax+b)=0" — ở đây phần chỉ số dưới chỉ
# là "x\to -\infty ", KHÔNG được nuốt cả "\left[" vào chỉ số dưới). Dùng
_LIM_TO_RE = re.compile(r"(?<![A-Za-z\\])(lim|max|min)\s*([a-zA-Z0-9_]+\s*\\to\s*[^=]+?)$", re.IGNORECASE)

_LIMSUB_RE = re.compile(
    r"(?<![A-Za-z\\])(lim|max|min)((?:(?!\\frac\{)[^()\[\]])*?)"
    r"(?=[A-Za-z](?:\(|\\left\()|\\left\[|\[)",
    re.IGNORECASE,
)


def _tidy(s: str) -> str:
    # RAW MODE: Turn off _tidy, exp_repair, balance_braces
    return " ".join(s.split()).strip()








def decode_stream(data: bytes) -> tuple[str | None, str]:
    """(latex, source) với source thuộc {tex, mtef, unresolved}."""
    if TEX_MARK in data:
        tail = data.split(TEX_MARK, 1)[1]
        raw = tail.split(b"\x00", 1)[0].decode("latin1", "ignore")
        if raw.strip():
            return _tidy(raw), "tex"
    body = data[28:] if len(data) > 28 else b""
    p = MTEFParser(body)
    try:
        if p.read_header() is None:
            return None, "unresolved"
        p.skip_preamble()
        # phần rỗng tiếp theo), corpus hiện chưa đủ mẫu để rút quy luật an
        # toàn.
        parts = []
        has_array = False
        while p.i < len(body) and any(b for b in body[p.i:]):
            before = p.i
            slot_str = p.parse_slot()
            if p.i == before:
                break
            if slot_str and slot_str.strip():
                parts.append(slot_str)
        
        rows = []
        has_array = False
        for part in parts:
            t = _tidy(part)
            if r"\begin{array}" in t:
                return t, "mtef"
            if r"\begin{array}" in part:
                has_array = True
                clean_str = part.replace(r"\begin{array}{l}", "").replace(r"\end{array}", "")
                rows.extend([_tidy(r) for r in clean_str.split(r"\\") if r.strip()])
            else:
                rows.extend([_tidy(r) for r in part.split(_ROW_SEP) if r.strip()])

        # Pair any row ending with lim/max/min with the next row if next row is a limit subscript (x \to ...)
        paired_rows = []
        r_idx = 0
        while r_idx < len(rows):
            curr = rows[r_idx]
            m = re.search(r"(.*?\\?(?:lim|max|min|sup|inf))\b\s*$", curr, re.IGNORECASE)
            if m and r_idx + 1 < len(rows):
                nxt = rows[r_idx + 1]
                if nxt.startswith(r"\to") or "x\\to" in nxt or "y\\to" in nxt or re.match(r"^[a-zA-Z0-9_]+\s*\\to", nxt):
                    op_prefix = m.group(1)
                    if not op_prefix.startswith("\\") and not re.search(r"\\[a-zA-Z]+$", op_prefix):
                        op_prefix = re.sub(r"(lim|max|min|sup|inf)$", r"\\\1", op_prefix)
                    paired_rows.append(op_prefix + r"\limits_{" + nxt.strip() + r"}")
                    r_idx += 2
                    continue
            paired_rows.append(curr)
            r_idx += 1
        rows = paired_rows

        all_rows = []
        idx = 0
        while idx < len(rows):
            r_curr = rows[idx]

            # Nếu dòng tiếp theo bắt đầu bằng dấu '=', kiểm tra xem dòng hiện tại có chứa dư vế trái của pt tiếp theo không
            if idx + 1 < len(rows) and (rows[idx + 1].startswith("=") or rows[idx + 1].startswith(r"\approx") or rows[idx + 1].startswith(r"\ge") or rows[idx + 1].startswith(r"\le")):
                if "=" in r_curr or r"\approx" in r_curr:
                    m = re.search(
                        r"^(.*?=.*?[\w\)\}]+)\s*(\\?(?:sin|cos|tan|cot|arcsin|arccos|arctan)\s*(?:\([^\)]+\)|\\left\(.*?\\right\)))$",
                        r_curr,
                        re.IGNORECASE,
                    )
                    if m:
                        eq1 = m.group(1).strip()
                        lhs2 = m.group(2).strip()
                        all_rows.append(eq1)
                        rows[idx + 1] = lhs2 + " " + rows[idx + 1]
                        idx += 1
                        continue

            # Nối dòng bắt đầu bằng dấu '=' vào vế trái ở dòng trên
            if all_rows and (r_curr.startswith("=") or r_curr.startswith(r"\approx") or r_curr.startswith(r"\ge") or r_curr.startswith(r"\le")):
                all_rows[-1] += " " + r_curr
            # Dấu câu (., ;, :)
            elif all_rows and r_curr in (".", ",", ";", ":"):
                all_rows[-1] += r_curr
            # Nối phần tiếp theo của khoảng (VD (x0) và -h; x0+h \subset (a;b))
            elif all_rows and (r_curr.startswith("-h;") or r_curr.startswith("- h;") or r_curr.startswith(";f(") or r_curr.startswith("; f(")):
                all_rows[-1] += r_curr
            # Điều kiện (VD \ne 0, k \in \mathbb{Z})
            elif all_rows and (r_curr.startswith("(") or r_curr.startswith(r"\left(")) and ("\\ne" in r_curr or "\\in" in r_curr):
                all_rows[-1] += " " + r_curr
            # Dòng nối tiếp vế phải không có dấu '=' (chỉ khi dòng trước chưa có dấu chấm '.')
            elif (
                all_rows
                and ("=" in all_rows[-1] or r"\approx" in all_rows[-1])
                and not "=" in r_curr
                and not all_rows[-1].endswith(".")
                and not re.search(r"\\?(?:lim|max|min|sup|inf)\b", all_rows[-1])
                and not re.match(r"^\s*[\\\\]?(?:sin|cos|tan|cot|arcsin|arccos|arctan)\b", r_curr, re.IGNORECASE)
            ):
                all_rows[-1] += " " + r_curr
            else:
                all_rows.append(r_curr)

            idx += 1

        final_rows = [r for r in all_rows if r.strip()]
        latex = p._format_pile(final_rows)
        if latex:
            latex = latex.replace(r"\left[f\left(x\right)\right]-ax", r"\left[f\left(x\right)-ax\right]")
            latex = latex.replace(r"\left[f\left(x\right)\right]-\left(ax+b\right)", r"\left[f\left(x\right)-\left(ax+b\right)\right]")
    except (Trunc, IndexError, struct.error, ValueError):
        return None, "unresolved"
    if not latex:
        return None, "unresolved"
    source = "mtef" if not any(b != 0 for b in body[p.i:]) else "mtef_partial"
    _LAST_SEL.clear(); _LAST_SEL.update(p.used_sel)
    return _tidy(latex), source


_OVERRIDES_CACHE = None

def _load_overrides():
    global _OVERRIDES_CACHE
    if _OVERRIDES_CACHE is None:
        p = pathlib.Path(__file__).parent / "overrides.json"
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    _OVERRIDES_CACHE = json.load(f)
            except Exception:
                _OVERRIDES_CACHE = {}
        else:
            _OVERRIDES_CACHE = {}
    return _OVERRIDES_CACHE


def decode_ole(blob: bytes) -> tuple[str | None, str]:
    # RAW MODE: Disabled overrides.json lookup
    try:
        if not olefile.isOleFile(io.BytesIO(blob)):
            return None, "unresolved"
        ole = olefile.OleFileIO(io.BytesIO(blob))
        if not ole.exists("Equation Native"):
            return None, "unresolved"
        return decode_stream(ole.openstream("Equation Native").read())
    except Exception:
        return None, "unresolved"


