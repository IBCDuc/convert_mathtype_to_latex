"""Dựng output HTML: chỉ nội dung docx, không có bookkeeping/pipeline metadata.

Mỗi mức (doc/lesson/section) map thẳng sang thẻ HTML tương ứng (không dùng
data-* thay cho field JSON cũ): <dl> cho metadata bài học, <section>+<h2..h6>
cho cấp mục, <p>/<ul><li>/<table> cho nội dung, <img> cho ảnh/công thức không
giải được (nhúng base64 thẳng trong thẻ, không CSS/class). HTML được ghi có
thụt lề theo cấp lồng (2 space/cấp) để đọc trực tiếp bằng mắt cho dễ, không
dồn hết vào 1 dòng.
"""
from __future__ import annotations

import base64
import re
from html import escape as _esc
from pathlib import Path

from . import mathrender, mtef
from .docxast import Asset, Block, DocxReader
from .segment import Node, build_tree, find_theory, fold

DEFAULT_BOOK_NAME = "Kết nối tri thức với cuộc sống"
DEFAULT_BOOK_CODE = "KNTT"

SUBJECTS = {
    "toan": ("MATH", "Toán"), "hoa": ("CHEM", "Hóa học"), "van": ("LIT", "Ngữ văn"),
    "dia": ("GEO", "Địa lí"), "gdktpl": ("ECOL", "Giáo dục kinh tế và pháp luật"),
    "su": ("HIST", "Lịch sử"),
}


# ------------------------------------------------------------------ metadata
def _parse_meta(path: Path, head: list[str]) -> dict:
    folded = [fold(p) for p in path.parts]
    subject_dir = next((f for f in folded
                        if re.search(r"(toan|hoa|van|dia|gdktpl)\s*\d", f)), fold(path.stem))
    code, name = next(((c, n) for k, (c, n) in SUBJECTS.items() if k in subject_dir),
                      ("UNK", "?"))
    gm = re.search(r"\b(1[0-2])\b", subject_dir)
    grade = int(gm.group(1)) if gm else 0

    # Ngữ văn: "BÀI n: ..." là tên chương (không lấy làm tên bài),
    # "VĂN BẢN k: ..." mới là tên bài thật.
    vb = next((h for h in head if re.match(r"(?i)^(v[aă]n b[ảa]n|đọc)\s*\d*\s*[:.\-–]", h)), None)

    stem, number, title = path.stem, None, ""
    for cand in [stem, *head]:
        lm = re.search(r"(?i)b[àa]i\s*(\d{1,2})", cand)
        if lm:
            number = int(lm.group(1))
            title = re.sub(r"(?i)^.*?b[àa]i\s*\d{1,2}\s*[.:\-–_)]*\s*", "", cand).strip()
            break
    if vb:
        title = re.sub(r"(?i)^(v[aă]n b[ảa]n|đọc)\s*\d*\s*[:.\-–]\s*", "", vb).strip()
    if not title:
        title = re.sub(r"^\s*\d+\s*[.)]\s*", "", stem)
    title = title.strip()
    if title.startswith("(") and title.endswith(")"):
        title = title[1:-1].strip()
    title = re.sub(r"^\(.+?\)\s*[-–]\s*", "", title).strip() or stem

    return {"subject_code": code, "subject": name, "grade": grade,
            "book": DEFAULT_BOOK_NAME, "book_code": DEFAULT_BOOK_CODE,
            "lesson_number": number, "lesson_title": title}


def _doc_id(m: dict) -> str:
    head = fold(f"{m['subject_code']}-{m['grade']}-{m['book_code']}").replace(" ", "-")
    head += f"-bai-{m['lesson_number']:02d}" if m["lesson_number"] else "-bai-x"
    slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", fold(m["lesson_title"]))).strip("-")
    return f"{head}-{slug[:48].rstrip('-')}" if slug else head


# -------------------------------------------------------------------- render
_QUOTE_RE = re.compile(r"\s*[“\"].{4,}[”\"]\s*", re.S)
_CALLOUT_RE = re.compile(
    r"^\s*(Chú ý|Lưu ý|Nhận xét|Ví dụ|Quy ước|Cảnh báo)\s*[.:]?\s*(?=\S)", re.I)
# Đoạn kiểu "1. Về nội dung, ý nghĩa lịch sử:Các cuộc..." — docx không có dấu
# cách sau ":" (lỗi soạn thảo gốc) nên dính liền câu sau, đọc không theo quy
# chuẩn. Chỉ khớp khi KHÔNG có khoảng trắng sau ":" ((?=\S)) — nếu có cách thì
# đó là văn bản bình thường, không đụng tới.
_NUMHEAD_RE = re.compile(r"^\s*(\d{1,2}[.)]\s*[^:\n]{2,80}):(?=\S)")


def _pad(depth: int) -> str:
    return "  " * depth


def _b64img(a: Asset | None) -> str:
    if a is None or not a.data:
        return ""
    b64 = base64.b64encode(a.data).decode()
    mime = a.mime or "image/png"
    if "emf" in mime.lower() or "wmf" in mime.lower():
        mime = "image/png"
    return f'<img src="data:{mime};base64,{b64}">'


def _needs_gap(prev: tuple, cur: tuple) -> bool:
    """True nếu cần tự chèn 1 dấu cách giữa 2 inline liền nhau.

    Docx gốc nhiều chỗ gõ thiếu dấu cách giữa công thức và chữ theo sau/trước
    (VD: "S" rồi "và" dính thành "Svà"). Chỉ xét khi 1 bên là formula/image
    (không đụng ranh giới 2 đoạn text thường — đó có thể là ranh giới định
    dạng có chủ đích) và cạnh text kề đó là chữ/số dính liền, không có
    khoảng trắng hay dấu câu ngăn cách (công thức áp sát dấu câu là bình
    thường, VD "(S)", không cần chèn cách)."""
    p_kind, p_plain, _ = prev
    c_kind, c_plain, _ = cur
    if p_kind == "text" and c_kind == "text":
        return False
    edge = p_plain[-1] if p_kind == "text" and p_plain else None
    cedge = c_plain[0] if c_kind == "text" and c_plain else None
    return any(e and e.isalnum() for e in (edge, cedge))


# LaTeX cho các tên tia/vectơ hay gặp: Om Ou Ov Ox Oy Oz
# (các biến in nghiêng dạng toán học — render bằng KaTeX để nhất quán font)
_RAY_NAMES_LATEX: dict[str, str] = {}  # được populate lazy


def _get_ray_html(name: str, math: dict[str, str]) -> str:
    """Lấy KaTeX HTML cho tên tia (Om, Ou, Ov...). Cache vào _RAY_NAMES_LATEX."""
    if name not in _RAY_NAMES_LATEX:
        # Ví dụ: "Om" -> "Om" (KaTeX sẽ tự render nghiêng như biến toán)
        try:
            result = mathrender.render_many([name])
            _RAY_NAMES_LATEX[name] = result.get(name, f'<em>{name}</em>')
        except Exception:
            _RAY_NAMES_LATEX[name] = f'<em>{name}</em>'
    return _RAY_NAMES_LATEX[name]


# Regex để detect tên tia dạng Om Ou Ov Ox Oy Oz trong plain text
_RAY_NAME_RE = re.compile(r'\b(O[uvmxyz])\b')


def _render_inline(items, assets: dict[str, Asset], math: dict[str, str]) -> str:
    """Nối text/formula/image thành MỘT chuỗi — công thức/ảnh nhúng thẳng tại chỗ."""
    parts: list[tuple[str, str | None, str]] = []
    for i in items:
        if i.kind == "text":
            parts.append(("text", i.text, _esc(i.text)))
        elif i.kind == "formula":
            a = assets.get(i.ref)
            html = math[a.latex] if a and a.latex else _b64img(a)
            parts.append(("formula", None, html))
        elif i.kind == "image":
            parts.append(("image", None, _b64img(assets.get(i.ref))))

    out = []
    for idx, part in enumerate(parts):
        prev = parts[idx - 1] if idx else None

        # Fix: MTEF đôi khi decode \mathrm{O} thành formula nhưng tách O ra
        # khỏi chữ u/v/m/x/y/z theo sau → "O u" có dấu cách xấu.
        # Nếu formula trước render chứa ">O</span>" ở cuối (tên tia O chỉ có mọt ký tự)
        # và text sau bắt đầu bằng u/v/m/x/y/z → không chèn space, render bằng KaTeX.
        if prev and prev[0] == "formula" and part[0] == "text" and part[1]:
            prev_ends_O = (prev[2].rstrip().endswith('>O</span>') or
                          bool(re.search(r'>O</span>(?:</span>)*$', prev[2].rstrip())))
            if prev_ends_O and part[1] and part[1][0] in 'uvmxyz':
                # Pop trailing spaces rồi pop O-katex span đã append ở iteration trước.
                # Nếu không pop, out sẽ chứa cả [O-span][Ou-span] → hiển thị "OOu".
                while out and out[-1].strip() == '':
                    out.pop()
                if out:  # xóa O-katex span
                    out.pop()
                letter = part[1][0]
                ray_name = 'O' + letter  # VD: "Ou", "Ov", "Om"
                ray_html = _get_ray_html(ray_name, math)
                rest = part[1][1:]
                out.append(ray_html + _esc(rest))
                if part[0] == "image":
                    out.append("<br>")
                continue
            elif idx and _needs_gap(parts[idx - 1], part):
                out.append(" ")
        elif idx and _needs_gap(parts[idx - 1], part):
            out.append(" ")

        out.append(part[2])
        if part[0] == "image":
            # Ảnh (hình vẽ/sơ đồ thật, khác công thức render dạng ảnh) luôn
            # xuống dòng riêng, tránh dính vào chữ chú thích ngay sau (VD
            # "Hình 1a Hình 1b" nối liền 2 ảnh cạnh nhau).
            out.append("<br>")

    result = "".join(out)
    # Wrap tên tia/vectơ như Ou, Ov, Om trong text thuần thành KaTeX HTML
    # (không dùng <em> — font browser italic khác font KaTeX math italic).
    # Chỉ áp dụng cho các ký hiệu nằm NGOÀI các thẻ HTML (đặc biệt không
    # replace bên trong span katex đã có).
    def replace_ray(m):
        return _get_ray_html(m.group(1), math)
    result = re.sub(r'(?<![<\/\w=])\b(O[uvmxyz])\b(?![^<]*>)', replace_ray, result)
    return result


_MANUAL_BULLET_RE = re.compile(r"^\s*([+\-–•*])\s+(?=\S)")

def _render_para(b: Block, assets: dict[str, Asset], math: dict[str, str]) -> tuple[str | None, str]:
    """Render 1 paragraph (không phải table) thành nội dung <p>/<li>, KHÔNG kèm thẻ bọc.

    Trả (label, body): `label` khác None khi đoạn nên tách thành 1 heading
    riêng (xem _NUMHEAD_RE) — caller (_content_html) tự quyết định thẻ <hN>."""
    plain = "".join(i.text for i in b.inlines if i.kind == "text")
    # QUAN TRỌNG: giữ s CHƯA strip khi còn cần cắt theo chỉ số của `plain`.
    # strip() sớm từng làm lệch 1 ký tự (mất chữ "T" của "Tập") vì `plain` có
    # khoảng trắng đầu dòng mà s (sau strip) đã mất — hai chỉ số không còn khớp.
    s = _render_inline(b.inlines, assets, math)
    if not s.strip():
        return None, ""

    # Trích dẫn/thơ trong ngoặc kép cong (Văn 12 dùng nhiều) -> in nghiêng,
    # mỗi dòng thơ ngăn bằng <br> (là HTML thật, browser hiển thị trực tiếp,
    # không phải ký tự \n để đọc như text thuần nữa).
    if _QUOTE_RE.fullmatch(plain.strip()):
        lines = [ln.strip() for ln in plain.strip("“”\" \n").split("\n") if ln.strip()]
        s = "<i>" + "<br>".join(_esc(ln) for ln in lines) + "</i>"
        return None, s.strip()

    m = _CALLOUT_RE.match(plain)
    if m:
        # Nhãn (Chú ý/Nhận xét/...) chỉ chứa ASCII+dấu, không bị escape khác
        # đi giữa text và s -> cắt theo cùng vị trí (chưa strip) là an toàn.
        s = f"<b>{m.group(1).strip()}:</b> {s[m.end():].strip()}"
        return None, s.strip()

    if b.ilvl is None and not any(i.kind == "image" for i in b.inlines):
        m = _NUMHEAD_RE.match(plain)
        if m:
            # Cùng lý do an toàn cắt-theo-vị-trí như _CALLOUT_RE ở trên.
            return s[:m.end()].strip(), s[m.end():].strip()
        if b.inlines and b.inlines[0].kind == "text":
            mb = _MANUAL_BULLET_RE.match(b.inlines[0].text)
            if mb:
                from pipeline.docxast import Inline as _Inline
                clean_inlines = [_Inline("text", b.inlines[0].text[mb.end():],
                                        bold=b.inlines[0].bold, color=b.inlines[0].color,
                                        underline=b.inlines[0].underline)] + list(b.inlines[1:])
                s_clean = _render_inline(clean_inlines, assets, math)
                return "__bullet__", s_clean.strip()

    # KHÔNG bọc <b> theo `b.bold` (majority-vote toàn đoạn) — thiếu chính xác
    # trên các đoạn dài/nhiều run khác định dạng, ra <b> tràn lan không đều.
    return None, s.strip()


def _render_table(b: Block, assets: dict[str, Asset], math: dict[str, str], depth: int) -> str:
    pad = _pad(depth)
    rows = []
    for row in b.rows:
        cells = []
        for c in row:
            rendered = _render_inline(c, assets, math)
            if re.search(r"(?:^\s*|\s+)[+\-–•*]\s+", rendered):
                items = [item.strip() for item in re.split(r"(?:^\s*|\s+)[+\-–•*]\s+", rendered) if item.strip()]
                if len(items) > 1 or (len(items) == 1 and rendered.strip().startswith(("-", "+", "•", "*"))):
                    lis = "".join(f"<li>{item}</li>" for item in items)
                    rendered = f"<ul>{lis}</ul>"
            cells.append(f"<td>{rendered}</td>")
        rows.append(f"{pad}  <tr>{''.join(cells)}</tr>")
    return "\n".join([f"{pad}<table>", *rows, f"{pad}</table>"])


def _content_html(n: Node, assets: dict[str, Asset], math: dict[str, str], depth: int) -> str:
    """Ghép các block trong 1 mục thành HTML: nội dung thường -> <p>, các block
    liên tiếp có ilvl (gạch đầu dòng) -> gộp vào 1 <ul><li>, bảng giữ <table>.
    Mỗi thẻ ở đúng dòng riêng, thụt lề theo `depth`."""
    pad = _pad(depth)
    parts: list[str] = []
    bullet_buf: list[str] = []

    def flush_bullets():
        if bullet_buf:
            items = "\n".join(f"{pad}  <li>{x}</li>" for x in bullet_buf)
            parts.append(f"{pad}<ul>\n{items}\n{pad}</ul>")
            bullet_buf.clear()

    for b in n.blocks:
        if b.kind == "table":
            flush_bullets()
            parts.append(_render_table(b, assets, math, depth))
            parts.append(f"{pad}<br>")
            continue
        label, s = _render_para(b, assets, math)
        if not s and not label:
            continue
        if label == "__bullet__":
            bullet_buf.append(s)
        elif label:
            flush_bullets()
            tag = f"h{min(depth + 1, 6)}"
            parts.append(f"{pad}<{tag}>{label}</{tag}>")
            if s:
                parts.append(f"{pad}<p>{s}</p>")
        elif b.ilvl is not None:
            bullet_buf.append(s)
        else:
            flush_bullets()
            parts.append(f"{pad}<p>{s}</p>")
    flush_bullets()
    return "\n".join(parts)


_ROMAN_RE = re.compile(r"^(?:X{0,2}(?:IX|IV|V?I{0,3}))[.)\s]", re.I)
_ALPHA_UPPER_RE = re.compile(r"^[A-Z][.)\s]")


def _use_h_tag(n: Node, depth: int) -> bool:
    """Tất cả các mục đã phân cấp trong cây cấu trúc (Node) đều dùng thẻ <h2..h6>."""
    return True


def _section_html(n: Node, assets: dict[str, Asset], math: dict[str, str], depth: int) -> str:
    pad = _pad(depth)
    lines = []

    if isinstance(n.header_block, Block):
        title_html = _render_inline(n.header_block.inlines, assets, math).strip()
    elif isinstance(n.header_block, list) and n.header_block and hasattr(n.header_block[0], "inlines"):
        title_html = "".join(_render_inline(b.inlines, assets, math) for b in n.header_block).strip()
    else:
        title_html = _esc(f"{n.numbering} {n.title}".strip()) if n.numbering else _esc(n.title.strip())

    use_h = _use_h_tag(n, depth)
    if use_h and title_html:
        tag = f"h{min(depth + 1, 6)}"
        lines.append(f"{pad}<{tag}>{title_html}</{tag}>")
    elif title_html:
        lines.append(f"{pad}<p><strong>{title_html}</strong></p>")

    content = _content_html(n, assets, math, depth + 1)
    if content:
        lines.append(content)
    for c in n.children:
        lines.append(_section_html(c, assets, math, depth + 1 if use_h else depth))
    return "\n".join(lines)


# ---------------------------------------------------------------------- main
def convert(path: str | Path) -> tuple[str, str]:
    """Trả về (doc_id, html) — html là 1 trang hoàn chỉnh cho 1 bài học."""
    path = Path(path)
    doc = DocxReader(path).parse()
    head = [b.text for b in doc.blocks[:6] if b.kind == "para" and b.text]
    meta = _parse_meta(path, head)
    start, end, _flags, _heading = find_theory(doc.blocks)

    for a in doc.assets.values():
        if a.kind == "formula" and a.latex:
            a.latex = mtef._tidy(a.latex)

    latex_list = [a.latex for a in doc.assets.values() if a.kind == "formula" and a.latex]
    math = mathrender.render_many(latex_list)

    sections_html = ""
    if start >= 0:
        tree = build_tree(doc.blocks, start, end)
        sections_html = "\n".join(_section_html(n, doc.assets, math, depth=1) for n in tree)

    doc_id = _doc_id(meta)
    lesson_title = meta["lesson_title"]
    html = "\n".join(x for x in [
        "<!doctype html>",
        "<html>",
        "<head>",
        '  <meta charset="utf-8">',
        f"  <title>{_esc(lesson_title)}</title>",
        f"  <style>{mathrender.katex_css()} p {{ line-height: 1.6; overflow-x: auto; }} .katex, .katex-html, .katex-base {{ display: inline-block !important; white-space: nowrap !important; }}</style>" if latex_list else "",
        "</head>",
        "<body>",
        f"  <h1>{_esc(lesson_title)}</h1>",
        sections_html,
        "</body>",
        "</html>",
    ] if x)
    return doc_id, html
