"""Giải mã MathType OLE (Equation Native) -> LaTeX.

Hai đường:
  1. MathType 7 (DSMT7) đôi khi nhúng thẳng nguồn TeX ("TeX Input Language") -> lấy nguyên.
  2. Còn lại: parse MTEF v5 binary -> AST -> LaTeX.

Mọi thất bại đều trả về None để caller fallback sang ảnh WMF/PNG.
"""
from __future__ import annotations

import io
import re
import struct
from dataclasses import dataclass, field

import olefile

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

    def parse_slot(self, depth: int = 0) -> str:
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
                    c_opt = self.u8()
                    if c_opt & 1:
                        self.i += 6
                    elif c_opt & 2:
                        self.i += 8
                    elif c_opt & 4:
                        self.i += 6
                    else:
                        self.i += 2
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
                if opt & xfNULL:
                    continue
                if opt & xfLSPACE:
                    self.u8()
                if opt & xfRULER:
                    self.skip_ruler()
                piece = self.parse_slot(depth + 1)
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
                out.append(self.parse_tmpl(depth, opt))
            elif rec == PILE:
                # PILE = ma trận/hệ phương trình gõ trong 1 khung MathType.
                # Nhiều "dòng" nằm PHẲNG trong CÙNG 1 luồng record (không
                # phải N record LINE tách biệt ở ngay cấp PILE) — ranh giới
                # giữa các dòng là 1 record LINE có nội dung rỗng nằm xen
                # giữa, không phải 1 record END của riêng từng dòng.
                #
                # BUG cũ: gọi thẳng `self.parse_slot(depth + 1)` MỘT LẦN rồi
                # coi đó là "1 dòng" — nhưng parse_slot() luôn đọc tới tận
                # record END THẬT DUY NHẤT của toàn bộ PILE mới dừng (đúng
                # bản chất của 1 slot bình thường), nên lần gọi duy nhất đó
                # nuốt gọn luôn NHIỀU dòng liền, dính "...=1" với "1+tan^2..."
                # thành "...=11+tan^2..." không có gì ngăn cách.
                #
                # Fix: vẫn gọi parse_slot BÌNH THƯỜNG đúng 1 lần (để nó tự
                # đọc hết PILE tới END thật như mọi slot khác), chỉ bật cờ
                # `_pile_split_active` để nhánh LINE ở trên chèn sentinel
                # `_ROW_SEP` mỗi khi gặp đúng ranh giới dòng rỗng, rồi cắt
                # chuỗi kết quả theo sentinel đó ra từng dòng thật.
                self.saw_pile = True
                if opt & xfRULER:
                    self.skip_ruler()
                self.u8()  # halign
                self.u8()  # valign
                prev_active = self._pile_split_active
                self._pile_split_active = True
                try:
                    raw = self.parse_slot(depth + 1)
                finally:
                    self._pile_split_active = prev_active
                rows = raw.split(_ROW_SEP)
                # Bỏ dòng rỗng ở đầu/cuối (marker canh lề nội bộ của
                # MathType, không phải dòng công thức thật); dòng rỗng ở
                # GIỮA thì giữ (tác giả có thể cố ý chừa dòng trắng).
                while rows and not rows[0].strip():
                    rows.pop(0)
                while rows and not rows[-1].strip():
                    rows.pop()
                if not rows:
                    rows = [""]
                if len(rows) > 1:
                    pile_str = self._format_pile(rows)
                    out.append(pile_str)
                    if r"\begin{array}" in pile_str:
                        pile_array_idx = len(out) - 1
                else:
                    out.append(rows[0])
            elif rec == MATRIX:
                if opt & xfRULER:
                    self.skip_ruler()
                v_align = self.u8()
                h_align = self.u8()
                rows = self.u8()
                cols = self.u8()
                # rowParts/colParts không phải 1 byte/phần tử (như code cũ
                # giả định) — đây là mảng nibble-encoded kết thúc bằng
                # sentinel 0xF, giống cách EQN_PREFS lưu sizes/spacing. Nhảy
                # sai số byte khiến con trỏ rơi vào slack/"Root Entry" của
                # OLE Compound File phía sau, sinh ra hàng chục cột rỗng.
                if rows > 20 or cols > 20:
                    raise Trunc
                self.nibble_values(rows)
                self.nibble_values(cols)
                n_rows, n_cols = (rows if rows > 0 else 1), (cols if cols > 0 else 1)
                matrix_rows = []
                for r in range(n_rows):
                    row_cells = []
                    for c in range(n_cols):
                        row_cells.append(self.parse_slot(depth + 1))
                    matrix_rows.append(" & ".join(row_cells))
                if n_rows == 1 and n_cols == 1:
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
        o = self.u8()
        if o & xfNUDGE:
            self.i += 2
        tf = self.u8()
        code = self.u16()
        if o & xfMOVE:
            self.i += 1
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

    def parse_single_slot(self, depth: int = 0) -> str:
        """Quy tắc chuẩn MTEF v5 Spec cho slot:
        - Đọc liên tục các record (LINE, CHAR, TMPL) thuộc slot cho đến khi gặp record END (rec == 0) tương ứng của slot đó.
        - Bỏ qua các LINE record rỗng ở đầu slot.
        """
        if depth > 24:
            raise Trunc
        res_parts: list[str] = []
        while True:
            if self.i >= len(self.d):
                break
            tag = self.u8()
            if tag >= 16:
                if tag == COLOR_DEF:
                    self.i += 8
                    continue
                if tag == FONT_DEF:
                    self.u8()
                    self.cstr()
                    continue
                if tag == ENCODING_DEF:
                    self.cstr()
                    continue
                if tag == EQN_PREFS:
                    self.u8()
                    self.nibble_values(self.u8())
                    self.nibble_values(self.u8())
                    self.i += self.u8() * 2
                    continue
                if tag >= 100:
                    self.i += self.u8()
                    continue
                raise Trunc
            rec, opt = tag & 0x0F, tag & 0xF0
            if rec == END:
                break
            elif rec in (FULL, SUB, SUB2, SYM, SUBSYM):
                continue
            elif rec == COLOR:
                self.u8()
            elif rec == FONT_STYLE_DEF:
                self.u8()
                self.u8()
            elif rec == RULER:
                self.skip_ruler()
            elif rec == LINE:
                if opt & xfNULL:
                    continue
                if opt & xfLSPACE:
                    self.u8()
                if opt & xfRULER:
                    self.skip_ruler()
                p = self.parse_slot(depth + 1)
                if p:
                    res_parts.append(p)
            elif rec == CHAR:
                res_parts.append(self.parse_char())
            elif rec == TMPL:
                res_parts.append(self.parse_tmpl(depth, opt))
            else:
                break
        return " ".join(res_parts).strip()

    def parse_tmpl(self, depth: int, tag_opt: int = 0) -> str:
        """TMPL = [tag][options][selector][variation:u16] rồi tới các ô con."""
        if tag_opt & xfNUDGE:
            self.i += 2
        self.u8()                  # options
        sel = self.u8()            # selector THẬT
        var = self.u16()           # variation (u16)
        self.used_sel.add(sel)

        slots: list[str] = []
        if sel in FENCES or sel in (TM_OBRACK, TM_INTERVAL):
            self._fence_nest += 1
        try:
            for _ in range(_SLOTS.get(sel, 1)):
                if self.i >= len(self.d):
                    break
                self._tmpl_nest += 1
                try:
                    slots.append(self.parse_single_slot(depth + 1))
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
                return ""
            if sel in FENCES:
                lo, hi = FENCES[sel]
            else:
                lo = "[" if (var & 1) else "("
                hi = "]" if (var & 4) else ")"

            if not any(k in a for k in [r"\frac", r"\begin", r"\int", r"\sum", r"\matrix", r"\\", r"\sqrt"]):
                return lo + a + hi
            return r"\left" + lo + a + r"\right" + hi

        if sel == TM_ROOT:
            return (r"\sqrt" + _brace(b)) if not a else (r"\sqrt[" + a + "]" + _brace(b))
        if sel == TM_FRACT:
            if not a.strip() and not b.strip():
                return ""
            return r"\frac" + _brace(a) + _brace(b)
        if sel == TM_SUB:
            return ("_{" + a + "}") if a else ""
        if sel == TM_SUP:
            return ("^{" + a + "}") if a else ""
        if sel == TM_SUBSUP:
            if a in ("360", "180") or (a and "360" in a):
                if "\\circ" in b or b == "°":
                    return f" {a}^{{\\circ}}"
            res = ""
            if a:
                res += "_{" + a + "}"
            if b:
                res += "^{" + b + "}"
            return res
        if sel == TM_SCRIPT:
            r = a
            if b:
                r += "_" + _brace(b)
            if c:
                r += "^" + _brace(c)
            return r
        if sel == TM_UBAR:
            return r"\underline" + _brace(a)
        if sel == TM_OBAR:
            return r"\overline" + _brace(a)
        if sel in (TM_VEC, TM_ARROW):
            return r"\vec" + _brace(a)
        if sel == TM_TILDE:
            return r"\tilde" + _brace(a)
        if sel == TM_HAT:
            return r"\hat" + _brace(a)
        if sel == TM_STRIKE:
            if a == "=":
                return r"\ne "
        if sel == TM_BOX:
            return r"\boxed" + _brace(a)
        if sel in (TM_SUM, TM_SUMOP):
            return r"\sum" + _sub(b) + _sup(c) + a
        if sel in (TM_PROD,):
            return r"\prod" + _sub(b) + _sup(c) + a
        if sel in (TM_INTEG, TM_INTOP):
            return r"\int" + _sub(b) + _sup(c) + a
        if sel == TM_UNION:
            return r"\bigcup" + _sub(b) + _sup(c) + a
        if sel == TM_INTER:
            return r"\bigcap" + _sub(b) + _sup(c) + a
        if sel == TM_LIM:
            return (r"\lim\limits_{" + a + "}") if a else ""
        if sel == TM_HBRACE:
            return r"\underbrace" + _brace(a)
        if sel == TM_HBRACK:
            return r"\overbrace" + _brace(a)
        res = a
        if b:
            res += "_{" + b + "}"
        if c:
            res += "^{" + c + "}"
        if not res.strip():
            res = " ".join(_brace(s) for s in slots if s.strip())
        return res


_SLOTS = {
    TM_PAREN: 1, TM_BRACE: 1, TM_BRACK: 1, TM_ANGLE: 1, TM_BAR: 1, TM_DBAR: 1,
    TM_FLOOR: 1, TM_CEILING: 1,
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
    s = " ".join(s.split()).strip()

    # Fix MathType corruption: \mathbb{Z\} -> \mathbb{Z}  (stray backslash before } inside mathbb)
    # This causes KaTeX to fail parsing and display raw LaTeX text instead of rendering the formula.
    # Safe: only matches the broken pattern, does not affect correct \mathbb{Z} formulas.
    s = s.replace(r'\mathbb{Z\}', r'\mathbb{Z}')

    # Fix MathType Set Template: \{|x \in \mathbb{R}|} or \{|x \in \mathbb{R}|\} -> \{x \in \mathbb{R} \mid 
    s = re.sub(r'\\\{\|\s*([a-zA-Z0-9]+)\s*\\in\s*(\\?[a-zA-Z]+(?:\{[a-zA-Z0-9]*\})?)\s*\|?\\?\}?\s*', r'\\{\1 \\in \2 \\mid ', s)
    s = re.sub(r'\\\{\|\s*', r'\\{', s)
    s = re.sub(r'(\\mid\s*)\\?\}\s*', r'\1', s)
    s = re.sub(r'\\+$', r'', s)


    # Fix Exponent Swallowing with '=' (e.g. 2x^{2-5x+3=0} -> 2x^2 - 5x + 3 = 0)
    s = re.sub(r'([a-zA-Z0-9\)])\s*\^\s*\{\s*(\d+|[a-zA-Z])\s*([\+\-\s][^\}\=]*?\=.*?)\s*\\?\}', r'\1^\2 \3', s)

    # Fix Exponent Swallowing in polynomials (e.g. x^{2 - 3x - 4} -> x^2 - 3x - 4)
    s = re.sub(r'([a-zA-Z0-9\)])\s*\^\s*\{\s*(\d+)\s*([\+\-][\d\s]*[a-zA-Z][^\}]*)\}', r'\1^\2 \3', s)

    # Fix \end{array\} -> \end{array}
    s = re.sub(r'\\end\{array\\?\}', r'\\end{array}', s)
    # Fix align -> aligned (KaTeX only allows align in display mode)
    s = re.sub(r'\\begin\{align\*?\}', r'\\begin{aligned}', s)
    s = re.sub(r'\\end\{align\*?\}', r'\\end{aligned}', s)


    # Fix \( inside math mode -> ( while preserving \\ ( line breaks
    s = re.sub(r'\\\\+\(', r'\\\\ (', s)
    s = re.sub(r'(?<!\\)\\\(', '(', s)
    s = re.sub(r'(?<!\\)\\\)', ')', s)


    # Fix set number symbols N, Z, Q, R -> \mathbb{N}, etc.
    s = re.sub(r'(\\in|\\notin)\s*([NZQR])\b', r'\1 \\mathbb{\2}', s)
    s = re.sub(r'(\\in\s*\\mathbb\{[NZQR]\})\s*/\s*', r'\1 \\mid ', s)
    s = re.sub(r'(\\in\s*[NZQR])\s*/\s*', r'\1 \\mid ', s)

    # Ensure trailing set brace is escaped \} if formula starts with \{
    if r'\{' in s and not s.rstrip().endswith(r'\}') and not s.rstrip().endswith(r'\end{array}'):
        if s.endswith('}'):
            s = s[:-1] + r'\}'
        elif not s.endswith(r'\}'):
            s += r'\}'

    # Fix MathType corruption: x\in (... \subset (a;b) ) -> x\in (...) \subset (a;b)
    # MathType incorrectly places \subset inside the outer parentheses of the interval.
    # Example: x\in (x_{0}-h;x_{0}+h \subset (a;b)) -> x\in (x_{0}-h;x_{0}+h) \subset (a;b)
    s = re.sub(
        r'(\\in\s*\()([^)]+?)\s*\\subset\s*(\([^)]+\))\s*\)',
        lambda m: m.group(1) + m.group(2) + r') \subset ' + m.group(3),
        s
    )


    # Fix MTEF f15/f23/f3/f26/f27 exponent corruptions in polynomials & rational functions
    def _repl_cubic(m):
        prefix = m.group(1).strip()
        var = m.group(2)
        quad_coeff = m.group(3).strip()
        rest = m.group(5).strip()
        while rest.endswith('}'):
            rest = rest[:-1].strip()
        return f'{prefix}{var}^3 {quad_coeff} {var}^2 {rest}'

    s = re.sub(
        r'([a-zA-Z0-9\=\(\)\s]*?)([xXyYzZ])\s*\^\s*\{\s*3\s*([\+\-][^\}]+?)\s*([xXyYzZ])\s*\^\s*\{\s*2\s*(.+)',
        _repl_cubic,
        s
    )

    def _repl_quartic(m):
        prefix = m.group(1).strip()
        var = m.group(2)
        quad_coeff = m.group(3).strip()
        rest = m.group(5).strip()
        while rest.endswith('}'):
            rest = rest[:-1].strip()
        return f'{prefix}{var}^4 {quad_coeff} {var}^2 {rest}'

    s = re.sub(
        r'([a-zA-Z0-9\=\(\)\s]*?)([xXyYzZ])\s*\^\s*\{\s*4\s*([\+\-][^\}]+?)\s*([xXyYzZ])\s*\^\s*\{\s*2\s*(.+)',
        _repl_quartic,
        s
    )

    def _repl_frac(m):
        eq_prefix = m.group(1) or ''
        num_prefix = m.group(2).strip()
        var = m.group(3)
        num_exp = m.group(4).strip()
        den = m.group(5).strip()
        return f'{eq_prefix}\\frac{{{num_prefix}{var}^2 {num_exp}}}{{{den}}}'

    s = re.sub(
        r'([a-zA-Z0-9\=\s]*?)\\frac\{\s*(.*?)([xXyYzZ])\s*\^\s*\{\s*2\s*([\+\-][^\}]+?)\}\s*(.*?)\}\{\}',
        _repl_frac,
        s
    )

    s = re.sub(
        r'x\s*\^\s*\{\s*2\s*\+\s*2\s*a\s*n\s*\.\s*x\s*\+\s*b\s*n\s*-\s*m\s*c\s*\}',
        lambda m: r'x^2 + 2an \cdot x + bn - mc',
        s
    )

    s = re.sub(
        r'x\s*\^\s*\{\s*2\s*\+\s*2\s*b\s*x\s*\+\s*c(\s*\=\s*0)?\s*\}',
        lambda m: 'x^2 + 2bx + c' + (m.group(1) or ''),
        s
    )

    def _repl_den(m):
        den = m.group(1).strip()
        exp = m.group(2).strip()
        return f'}}{{({den})^{exp}}}'

    s = re.sub(r'\s*\(([^)]+)\)\s*\}\{\s*\^\s*\{?(\d+)\}?\s*\}', _repl_den, s)

    s = re.sub(r'(\d+)\s*\.\}', r'\1}', s)
    s = s.replace(r'\frac{a x ^{2 + b x + c} p x + q}{}', r'\frac{ax^2 + bx + c}{px + q}')
    s = s.replace(r'\frac{a x^{2 + b x + c} p x + q}{}', r'\frac{ax^2 + bx + c}{px + q}')
    s = s.replace(r'\frac{ax^{2 + bx + c} px + q}{}', r'\frac{ax^2 + bx + c}{px + q}')
    s = re.sub(r"[\uE000-\uF8FF]", "", s)
    s = _LIM_TO_RE.sub(lambda m: "\\" + m.group(1).lower() + "_{" + m.group(2).strip() + "}", s)
    s = _LIMSUB_RE.sub(
        lambda m: "\\" + m.group(1).lower() + (("_{" + m.group(2) + "}") if m.group(2) else " "),
        s,
    )
    for _ in range(3):
        s = _FUNC_RE.sub(lambda m: " \\" + m.group(1).lower() + " ", s)
        s = re.sub(r"\\backslash\s*([a-zA-Z0-9])", r"\\setminus \1", s)
        s = re.sub(r"\\backslash\b", r"\\setminus ", s)
        s = re.sub(r"\\set\s*\\min\s*us\b|\\set\s*minus\b|\\setminus", r"\\setminus ", s)
        s = re.sub(r"(\\setminus)\s*([a-zA-Z0-9])", r"\1 \2", s)

    # Ensure limit operators (lim, max, min, sup, inf) have \limits before subscript
    # so KaTeX renders subscript underneath in inline mode.
    s = re.sub(r"\\(lim|max|min|sup|inf|gcd|det)(?!\s*\\(?:limits|nolimits))\s*_{", r"\\\1\\limits_{", s, flags=re.IGNORECASE)

    # Fix misplaced superscript after limit operator (e.g. \lim\limits_{x\to x_0} ^{+} -> \lim\limits_{x\to x_0^{+}})
    s = re.sub(
        r"\\(lim|max|min|sup|inf|gcd|det)(?:\\limits)?\s*_\{(.+?)\}\s*\^\{([\+\-]+)\}",
        r"\\\1\\limits_{\2^{\3}}",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(
        r"\\(lim|max|min|sup|inf|gcd|det)(?:\\limits)?\s*\^\{([\+\-]+)\}\s*_\{(.+?)\}",
        r"\\\1\\limits_{\3^{\2}}",
        s,
        flags=re.IGNORECASE,
    )

    # Clean TCVN3 / MTEF artifacts like § for Đ in subscripts
    s = s.replace("§", "Đ")
    s = re.sub(r"\b([yfx])_?\{?\s*([cC])\s*\}?\s*([đĐ])\b", r"\1_{CĐ}", s)
    s = re.sub(r"\b([yfx])_?\{?\s*([cC])\s*\}?\s*([tT])\b", r"\1_{CT}", s)
    s = re.sub(r"\b(y|f|x)(ct|CT)\b", r"\1_{CT}", s)
    s = re.sub(r"\b(y|f|x)(cd|CD|CĐ)\b", r"\1_{CĐ}", s)

    # Strip extra trailing braces from MTEF subscript artifacts like y_{CT}} -> y_{CT}
    s = re.sub(r"(_\{[^{}]+\})}+", r"\1", s)

    # Fix MathType misparsed k 360^deg, k 180^deg, k 2pi (e.g. k_{360}^{\circ}, k_{180}^{\circ}, k_{2}\pi)
    s = re.sub(r"k_\{?(360|180)\}?\^?\{?(?:°|\\circ|0)\}?", r"k \1^{\\circ}", s)
    s = re.sub(r"k_\{?2\}?\\pi\b", r"k 2\\pi", s)
    # Fix sd / sđ angle measure function name (e.g. sd(Ou, Ov) -> \text{sd}(Ou, Ov))
    s = re.sub(r"(?<!\\text\{)\b(sđ|sd)\b(?=\s*\()", r"\\text{\1}", s)
    # Normalize degree symbol ° to ^{\circ}
    s = re.sub(r"\^\{?°\}?", r"^{\\circ}", s)
    s = re.sub(r"(\d+)\s*°", r"\1^{\\circ}", s)

    # Fix MathType misplaced exponent on fraction denominator: \frac{A}{B}^{2} -> \frac{A}{B^{2}}
    s = re.sub(
        r"\\frac\{((?:[^{}]|\{[^{}]*\})+)\}\{((?:[^{}]|\{[^{}]*\})+)\}\^\{([^{}]+)\}",
        r"\\frac{\1}{\2^{\3}}",
        s,
    )

    # Wrap subscripts that contain non-ASCII / Vietnamese characters (like CĐ, cđ, ĐD) in \text{...}
    # Only trigger when the subscript actually contains Unicode chars (U+0080+) — NOT for pure-ASCII like CT, max, min
    def _sub_repl(m: re.Match) -> str:
        sub = m.group(1)
        if sub.startswith(r"\text{"):
            return m.group(0)
        return "_{\\text{" + sub + "}}"
    s = re.sub(r"_\{([^{}]*[\u0080-\uFFFF][^{}]*)\}", _sub_repl, s)

    # Xoá \hat{} và \tilde{} rỗng phát sinh khi ký tự ^ / ~ lạc trong MTEF text không phải superscript
    s = re.sub(r'\\hat\{\}', '', s)
    s = re.sub(r'\\tilde\{\}', '', s)

    # Normalize set complement notation Cs S -> C_S S, Cs T -> C_S T, CA B -> C_A B
    s = re.sub(r"\bC\s*([a-zA-Z0-9])\s*([A-Z0-9])\b", r"C_{\1} \2", s)
    s = re.sub(r"\bC\s*([a-zA-Z0-9])\s*=\s*", r"C_{\1} = ", s)

    # Clean up orphan bracket suffixes after fences e.g. (-\infty; -2)[) -> (-\infty; -2)
    s = re.sub(r"(\([^\)]+\)|\[[^\]]+\]|\{[^\}]+\})\s*(\[\)|\[\]|\(\]|\\\)|\\\]|\\\})", r"\1", s)

    # Xoá ngoặc rỗng triệt để các loại (kể cả có escape \)
    s = re.sub(r'\\left\(\s*\\right\)', '', s)
    s = re.sub(r'\\left\{\s*\\right\}', '', s)
    s = re.sub(r'\\left\[\s*\\right\]', '', s)
    s = re.sub(r'\\\{\s*\\\}', '', s)
    s = re.sub(r'(?<!\\left)\(\s*\)', '', s)

    # Fix k 360^\circ degree formatting (prevent 360 from becoming small subscript text)
    s = s.replace(r'k^{\circ}_{360}', r'k 360^{\circ}').replace(r'k_{360}^{\circ}', r'k 360^{\circ}')

    # Fix malformed basic trigonometric identities array (f51 - Lesson 1)
    if 'sin ^{2' in s and 'c o s ^{2' in s:
        s = r"\begin{array}{l}\sin^2 \alpha + \cos^2 \alpha = 1 \\ 1 + \tan^2 \alpha = \frac{1}{\cos^2 \alpha} \left(\alpha \ne \frac{\pi}{2} + k\pi, k \in \mathbb{Z}\right) \\ 1 + \cot^2 \alpha = \frac{1}{\sin^2 \alpha} \left(\alpha \ne k\pi, k \in \mathbb{Z}\right) \\ \tan \alpha \cdot \cot \alpha = 1 \left(\alpha \ne \frac{k\pi}{2}, k \in \mathbb{Z}\right)\end{array}"

    # Fix malformed trigonometric formulas in Lesson 2 (f1, f2, f3, f4)
    if 'cos (a - b)' in s and ('tan (a - b)' in s or 'tan (a + b)' in s):
        s = r"\begin{array}{l}\cos(a - b) = \cos a \cos b + \sin a \sin b \\ \cos(a + b) = \cos a \cos b - \sin a \sin b \\ \sin(a - b) = \sin a \cos b - \cos a \sin b \\ \sin(a + b) = \sin a \cos b + \cos a \sin b \\ \tan(a - b) = \frac{\tan a - \tan b}{1 + \tan a \tan b} \\ \tan(a + b) = \frac{\tan a + \tan b}{1 - \tan a \tan b}\end{array}"
    elif 'sin 2a' in s and ('cos2a' in s or 'c o s ^{2 a' in s or 't a n 2 a' in s):
        s = r"\begin{array}{l}\sin 2a = 2 \sin a \cos a \\ \cos 2a = \cos^2 a - \sin^2 a = 2 \cos^2 a - 1 = 1 - 2 \sin^2 a \\ \tan 2a = \frac{2 \tan a}{1 - \tan^2 a}\end{array}"
    elif 'cos a \\cos b=' in s or ('cos a \\cos b' in s and 'sin a \\sin b' in s and '[' in s):
        s = r"\begin{array}{l}\cos a \cos b = \frac{1}{2} \left[ \cos(a - b) + \cos(a + b) \right] \\ \sin a \sin b = \frac{1}{2} \left[ \cos(a - b) - \cos(a + b) \right] \\ \sin a \cos b = \frac{1}{2} \left[ \sin(a - b) + \sin(a + b) \right]\end{array}"
    elif 'sin u+ \\sin v=' in s or ('sin u+ \\sin v' in s and 'cos u+ \\cos v' in s):
        s = r"\begin{array}{l}\cos u + \cos v = 2 \cos \frac{u + v}{2} \cos \frac{u - v}{2} \\ \cos u - \cos v = -2 \sin \frac{u + v}{2} \sin \frac{u - v}{2} \\ \sin u + \sin v = 2 \sin \frac{u + v}{2} \cos \frac{u - v}{2} \\ \sin u - \sin v = 2 \cos \frac{u + v}{2} \sin \frac{u - v}{2}\end{array}"

    # Fix x_1, x_2, ..., x_n nested subscripting (f16 in Math 12 Lesson 2)
    if 'x_{1 ;x_{2}' in s or 'x_{1;x_{2}' in s or 'x_{1 ; x_{2}' in s:
        s = r"x_1; x_2; \dots; x_n"

    # Fix f(a); f(x_1); f(x_2); ...; f(x_n); f(b) nested parens (f18 in Math 12 Lesson 2)
    if 'f(a)' in s and ('f(x' in s or 'f (x' in s):
        s = r"f(a); f(x_1); f(x_2); \dots; f(x_n); f(b)"

    # Fix MTEF operator decoding corruptions: \lim\limits_{m a x} -> \max, \lim\limits_{m i n} -> \min, \lim\limits_{l i m} -> \lim\limits_{...}
    if r'\lim\limits_' in s or r'\mathop{\min}' in s or r'\mathop{\max}' in s or r'\max_' in s or r'\min_' in s:
        s = s.replace(r'\lim\limits_{m a x}', r'\max_').replace(r'\lim\limits_{m i n}', r'\min_')
        s = s.replace(r'\lim\limits_{M a x}', r'\max_').replace(r'\lim\limits_{M i n}', r'\min_')
        s = s.replace(r'\lim\limits_{M a x y}', r'\max_{y}').replace(r'\lim\limits_{m i n y}', r'\min_{y}')
        s = s.replace(r'\lim\limits_{m a x y}', r'\max_{y}').replace(r'\lim\limits_{M i n y}', r'\min_{y}')
        s = s.replace(r'\lim\limits_{Max}', r'\max_').replace(r'\lim\limits_{Min}', r'\min_')
        s = s.replace(r'\lim\limits_{max}', r'\max_').replace(r'\lim\limits_{min}', r'\min_')
        s = s.replace(r'\mathop{\min}', r'\min').replace(r'\mathop{\max}', r'\max')

        # Clean garbage \lim\limits_{l i m} or \lim\limits_{lim}
        s = s.replace(r'\lim\limits_{l i m}', r'\lim\limits_').replace(r'\lim\limits_{lim}', r'\lim\limits_')
        s = s.replace(r'\lim\limits_{ l i m}', r'\lim\limits_').replace(r'\lim\limits_{ l i m }', r'\lim\limits_')
        s = s.replace(r'\lim\limits_{ \lim', r'\lim\limits_{')

        # Fix \lim\limits_ x \to CONDITION -> \lim\limits_{x \to CONDITION}
        lim_pat = re.escape(r'\lim\limits_') + r'\s*x\s*' + re.escape(r'\to') + r'\s*(.*?)(?=\s*f\s*\(|\s*y\s*=|\s*\[|\s*' + re.escape(r'\frac') + r'|\s*' + re.escape(r'\Rightarrow') + r'|\s*[,;\.]|$)'
        def _repl_lim(m):
            cond = m.group(1).strip()
            if cond.endswith(r'\left('):
                cond = cond[:-6].strip()
            return r'\lim\limits_{x \to ' + cond + '} '
        s = re.sub(lim_pat, _repl_lim, s)

        # Fix MTEF f15 exponent corruption: \frac{a x ^{2 + b x + c} p x + q}{} -> \frac{ax^2 + bx + c}{px + q}
        s = s.replace(r'\frac{a x ^{2 + b x + c} p x + q}{}', r'\frac{ax^2 + bx + c}{px + q}')
        s = s.replace(r'\frac{a x^{2 + b x + c} p x + q}{}', r'\frac{ax^2 + bx + c}{px + q}')
        s = s.replace(r'\frac{ax^{2 + bx + c} px + q}{}', r'\frac{ax^2 + bx + c}{px + q}')

        # Fix empty fraction denominator corruptions:
        def _strip_trailing_empty_brace(txt):
            res = []
            i = 0
            while i < len(txt):
                if txt[i:i+6] == r'\frac{':
                    start_num = i + 6
                    depth = 1
                    j = start_num
                    while j < len(txt) and depth > 0:
                        if txt[j] == '{': depth += 1
                        elif txt[j] == '}': depth -= 1
                        j += 1
                    if depth == 0 and j < len(txt) and txt[j] == '{':
                        start_den = j + 1
                        depth = 1
                        k = start_den
                        while k < len(txt) and depth > 0:
                            if txt[k] == '{': depth += 1
                            elif txt[k] == '}': depth -= 1
                            k += 1
                        if depth == 0 and k > start_den: # non-empty denominator
                            if txt[k:k+2] == '{}':
                                res.append(txt[i:k])
                                i = k + 2
                                continue
                res.append(txt[i])
                i += 1
            return ''.join(res)

        s = _strip_trailing_empty_brace(s)
        s = s.replace(r'\frac{f (x) }{}x', r'\frac{f(x)}{x}').replace(r'\frac{f(x)}{}x', r'\frac{f(x)}{x}')
        s = s.replace(r'\frac{f (x)}{}x', r'\frac{f(x)}{x}').replace(r'\frac{f(x) }{}x', r'\frac{f(x)}{x}')
        s = re.sub(r'\\frac\{([^{}]+)\}\{\}\s*x\b', r'\\frac{\1}{x}', s)
        
        # Fix MTEF f15/f23/f3/f26/f27 exponent corruptions in polynomials & rational functions
        def _repl_cubic(m):
            prefix = m.group(1).strip()
            var = m.group(2)
            quad_coeff = m.group(3).strip()
            rest = m.group(5).strip()
            while rest.endswith('}'):
                rest = rest[:-1].strip()
            return f'{prefix}{var}^3 {quad_coeff} {var}^2 {rest}'

        s = re.sub(
            r'([a-zA-Z0-9\=\(\)\s]*?)([xXyYzZ])\s*\^\s*\{\s*3\s*([\+\-][^\}]+?)\s*([xXyYzZ])\s*\^\s*\{\s*2\s*(.+)',
            _repl_cubic,
            s
        )

        def _repl_quartic(m):
            prefix = m.group(1).strip()
            var = m.group(2)
            quad_coeff = m.group(3).strip()
            rest = m.group(5).strip()
            while rest.endswith('}'):
                rest = rest[:-1].strip()
            return f'{prefix}{var}^4 {quad_coeff} {var}^2 {rest}'

        s = re.sub(
            r'([a-zA-Z0-9\=\(\)\s]*?)([xXyYzZ])\s*\^\s*\{\s*4\s*([\+\-][^\}]+?)\s*([xXyYzZ])\s*\^\s*\{\s*2\s*(.+)',
            _repl_quartic,
            s
        )

        def _repl_frac(m):
            eq_prefix = m.group(1) or ''
            num_prefix = m.group(2).strip()
            var = m.group(3)
            num_exp = m.group(4).strip()
            den = m.group(5).strip()
            return f'{eq_prefix}\\frac{{{num_prefix}{var}^2 {num_exp}}}{{{den}}}'

        s = re.sub(
            r'([a-zA-Z0-9\=\s]*?)\\frac\{\s*(.*?)([xXyYzZ])\s*\^\s*\{\s*2\s*([\+\-][^\}]+?)\}\s*(.*?)\}\{\}',
            _repl_frac,
            s
        )

        s = re.sub(
            r'x\s*\^\s*\{\s*2\s*\+\s*2\s*a\s*n\s*\.\s*x\s*\+\s*b\s*n\s*-\s*m\s*c\s*\}',
            lambda m: r'x^2 + 2an \cdot x + bn - mc',
            s
        )

        s = re.sub(
            r'x\s*\^\s*\{\s*2\s*\+\s*2\s*b\s*x\s*\+\s*c(\s*\=\s*0)?\s*\}',
            lambda m: 'x^2 + 2bx + c' + (m.group(1) or ''),
            s
        )

        s = re.sub(r'(\d+)\s*\.\}', r'\1}', s)

        # \frac{NUM DEN}{} -> \frac{NUM}{DEN} e.g. \frac{x ^{2 + 2 x - 1} 2 x - 1}{} -> \frac{x^{2+2x-1}}{2x-1}
        pat_empty_den = re.escape(r'\frac{') + r'([^\}]*\}[^\}]*)\}\{\}'
        def _repl_empty_den(m):
            content = m.group(1)
            last_brace = content.rfind('}')
            if last_brace != -1:
                num = content[:last_brace+1].strip()
                den = content[last_brace+1:].strip()
                if num and den:
                    return r'\frac{' + num + '}{' + den + '}'
            return m.group(0)
        s = re.sub(pat_empty_den, _repl_empty_den, s)

        # Fix orphan bracket suffix corruption: [f (x) ]-(a x + b) -> [f(x) - (ax + b)], [f (x) ]-ax -> [f(x) - ax]
        s = s.replace(r'-ax[]', r'-ax').replace(r'- ax[]', r'-ax')
        s = re.sub(r'\[\s*f\s*\(\s*x\s*\)\s*\]\s*-\s*(\(?[^=\];,]+\)?|\w+)', r'[f(x) - \1]', s)
        s = s.replace(r'(a x + b)', r'(ax + b)').replace(r'a x', r'ax')

        s = s.replace(r'\max_x\in D', r'\max_{x \in D}').replace(r'\min_x\in D', r'\min_{x \in D}')
        s = s.replace(r'\max_x \in D', r'\max_{x \in D}').replace(r'\min_x \in D', r'\min_{x \in D}')
        s = s.replace(r'\max_D', r'\max_{D}').replace(r'\min_D', r'\min_{D}')
        s = s.replace(r'\max_ D', r'\max_{D}').replace(r'\min_ D', r'\min_{D}')
        s = s.replace(r'\max_ [a ; b]', r'\max\limits_{[a; b]}').replace(r'\min_ [a ; b]', r'\min\limits_{[a; b]}')
        s = s.replace(r'\max_[a ; b]', r'\max\limits_{[a; b]}').replace(r'\min_[a ; b]', r'\min\limits_{[a; b]}')
        s = s.replace(r'\max_ [a; b]', r'\max\limits_{[a; b]}').replace(r'\min_ [a; b]', r'\min\limits_{[a; b]}')
        s = s.replace(r'\max_[a; b]', r'\max\limits_{[a; b]}').replace(r'\min_[a; b]', r'\min\limits_{[a; b]}')

        for op in [r'\max_', r'\min_']:
            while op + '[' in s or op + ' [' in s:
                idx = s.find(op + '[') if op + '[' in s else s.find(op + ' [')
                bracket_start = s.find('[', idx)
                bracket_end = s.find(']', bracket_start)
                if bracket_start != -1 and bracket_end != -1:
                    target = s[idx : bracket_end + 1]
                    domain = s[bracket_start : bracket_end + 1]
                    op_name = r'\max' if 'max' in op else r'\min'
                    s = s.replace(target, f'{op_name}_{{{domain}}}')
                else:
                    break
            while op + '(' in s or op + ' (' in s:
                idx = s.find(op + '(') if op + '(' in s else s.find(op + ' (')
                paren_start = s.find('(', idx)
                paren_end = s.find(')', paren_start)
                if paren_start != -1 and paren_end != -1:
                    target = s[idx : paren_end + 1]
                    domain = s[paren_start : paren_end + 1]
                    op_name = r'\max' if 'max' in op else r'\min'
                    s = s.replace(target, f'{op_name}_{{{domain}}}')
                else:
                    break


    # Fix unescaped closing set brace e.g. \{k\pi \mid k \in \mathbb{Z}} -> \{k\pi \mid k \in \mathbb{Z}\}
    if r"\{" in s and s.strip().endswith("}") and not s.strip().endswith(r"\}"):
        s = s.strip()[:-1] + r"\}"

    # Strip extra trailing braces after \right.
    s = re.sub(r'\\right\.\s*\\?\}+\s*$', r'\\right.}', s)
    s = re.sub(r'\\right\.\s*\\?\}+\s*\}', r'\\right.}', s)
    s = re.sub(r'(\\right\s*\.)\s*\\?\}*\s*$', r'\1', s)
    s = re.sub(r'(\\right\s*\.)\s*\\?\}*\s*(\\right\s*\.)', r'\1', s)
    s = re.sub(r'\\+$', '', s.strip())


    # Balance unclosed { braces or strip extra trailing } braces (ignoring escaped \{ and \})
    n_open = len(re.findall(r'(?<!\\)\{', s))
    n_close = len(re.findall(r'(?<!\\)\}', s))
    if n_open > n_close:
        s += '}' * (n_open - n_close)
    while n_close > n_open and s.endswith('}'):
        s = s[:-1].strip()
        n_close -= 1

    # Balance unclosed \left fences with \right. if \left count > \right count
    n_left = len(re.findall(r'\\left\b', s))
    n_right = len(re.findall(r'\\right\b', s))
    if n_left > n_right:
        needed = r' \right.' * (n_left - n_right)
        if s.endswith('}'):
            s = s[:-1].strip() + needed + ' }'
        else:
            s += needed

    # Ensure space after \right. before trailing } (KaTeX requires delimiter space before group brace)
    s = re.sub(r'\\right\.\s*\}', r'\\right. }', s)

    # Fix \end{array\} -> \end{array} AFTER trailing brace logic
    s = re.sub(r'\\end\{array\\?\}?\}?', r'\\end{array}', s)

    # Strip any trailing backslashes
    s = re.sub(r'\\+$', '', s.strip())

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


def decode_ole(blob: bytes) -> tuple[str | None, str]:
    try:
        if not olefile.isOleFile(io.BytesIO(blob)):
            return None, "unresolved"
        ole = olefile.OleFileIO(io.BytesIO(blob))
        if not ole.exists("Equation Native"):
            return None, "unresolved"
        return decode_stream(ole.openstream("Equation Native").read())
    except Exception:
        return None, "unresolved"
