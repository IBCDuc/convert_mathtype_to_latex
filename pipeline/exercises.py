"""Trích xuất phần B – BÀI TẬP từ docx thành HTML: 1 <section> / câu hỏi.

Mỗi field JSON (baitap_ref) cũ nay map sang 1 thẻ HTML tương ứng: metadata vô
hướng (subject/grade/cognitive_level/answer/score/kc_id...) vào <dl>, nội dung
đề vào <p>, lựa chọn vào <ol type="A"><li>, giải thích vào <div>. Field nào
docx không cho biết thì bỏ hẳn <dt>/<dd> đó (không suy đoán, không hiện rỗng).
Ảnh/công thức không giải được nhúng thẳng <img> base64 (không còn placeholder
text, vì giờ là HTML thật hiển thị được).

Corpus có 4 kiểu đánh dấu đáp án khác nhau, không kiểu nào giống kiểu kia:
  1. "Đáp án: B. giải thích..."               (Hóa 10, Hóa 12 — text rõ)
  2. "Lời giải" -> "Chọn B" -> giải thích      (Toán 11, một số Toán khác)
  3. Option đúng được TÔ MÀU riêng (FF0000)    (GDKTPL — màu chỉ trên 1 option)
  4. Option đúng được GẠCH CHÂN                (Toán 10, Địa 11 — có thể tất
     cả option cùng chung 1 màu trang trí, gạch chân mới là tín hiệu thật)
Độ ưu tiên: text rõ ràng > định dạng (màu/gạch chân) — vì text là tường minh,
định dạng là suy luận. Không tìm được gì thì answer=None và gắn cờ để review,
KHÔNG đoán bừa.
"""
from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import dataclass, field
from html import escape as _esc
from pathlib import Path

from . import mathrender, mtef
from .docxast import Asset, Block, DocxReader, Inline

from .segment import find_theory, fold

SUBJECTS = {
    "toan": ("toan", "Toán"), "hoa": ("hoa", "Hóa học"), "van": ("van", "Ngữ văn"),
    "dia": ("dia", "Địa lí"), "gdktpl": ("gdktpl", "Giáo dục kinh tế và pháp luật"),
    "su": ("su", "Lịch sử"),
}

RE_QUESTION = re.compile(r"(?i)^câu\s*(\d+)\s*[.:)]?\s*")
RE_LEVEL = re.compile(r"(?i)^level\s*([123])\b")
RE_BLOOM = re.compile(r"(?i)^(?:[ivx]+\.?\s*)?(nhận biết|thông hiểu|vận dụng cao|vận dụng)\b")
BLOOM_MAP = {"nhận biết": ("knowledge", 1), "thông hiểu": ("comprehension", 2),
             "vận dụng": ("application", 3), "vận dụng cao": ("application", 4)}
LEVEL_MAP = {1: ("knowledge", 1), 2: ("comprehension", 2), 3: ("application", 3)}

# `Block.text` bị .strip() ở cuối, nên 1 paragraph chỉ có "B." (không gì khác
# sau) sẽ KHÔNG khớp nếu bắt buộc có \s theo sau dấu câu -> phải chấp nhận cả
# cuối chuỗi ($), không chỉ \s.
RE_OPTION_ANY = re.compile(r"(?<![a-zA-Z])[A-D][.)](?:\s|$)")   # dò xem đoạn có phải dòng option
RE_OPTION_MARK = re.compile(r"^\s*([A-D])[.)]\s*")        # cắt marker A./B./C./D. đầu run
# Khi đáp án bị gạch chân, Word tách "D" và "." thành 2 run riêng (gạch chân
# chỉ áp cho chữ cái) -> marker "D" đứng lẻ không khớp RE_OPTION_MARK ở trên.
RE_BARE_LETTER = re.compile(r"^\s*([A-D])[.)]?\s*$")
RE_PUNCT_ONLY = re.compile(r"^[.)\s]+$")
# Một số file (Ngữ văn) đánh dấu đáp án bằng mũi tên đứng trước, ví dụ
# "=> Đáp án: A" -> phải bỏ qua tiền tố "=>"/"->"/"→" trước khi so khớp.
_ARROW = r"(?i)^\s*(?:=>|->|→)?\s*"
RE_ANSWER_HEAD = re.compile(_ARROW + r"(đáp\s*án|lời\s*giải|chọn)\b")
RE_DAPAN = re.compile(_ARROW + r"đáp\s*án\s*[:.\-]?\s*([A-D])\b\s*[.:)]?\s*")
RE_LOIGIAI = re.compile(r"(?i)^\s*lời\s*giải\s*$")
RE_CHON = re.compile(r"(?i)^\s*chọn\s+([A-D])\b\s*[.:)]?\s*")


@dataclass
class Choice:
    letter: str
    items: list[Inline] = field(default_factory=list)
    bold: bool = False
    color: str | None = None
    underline: bool = False
    inferred: bool = False   # suy ra do thiếu nhãn "A." trong docx gốc, không phải marker thật


def _b64img(a: Asset | None) -> str:
    if a is None or not a.data:
        return ""
    b64 = base64.b64encode(a.data).decode()
    mime = a.mime or "image/png"
    if "emf" in mime.lower() or "wmf" in mime.lower():
        mime = "image/png"
    return f'<img src="data:{mime};base64,{b64}">'


def _flat(paras: list[Block]) -> list[list[Inline]]:
    """Trả list-of-paragraph (mỗi paragraph là list Inline) để giữ ranh giới
    đoạn — mỗi paragraph render thành 1 <p> riêng."""
    return [b.inlines for b in paras]


def _flat_all(paras: list[Block]) -> list[Inline]:
    """Flatten toàn bộ inline xuyên paragraph, KHÔNG chèn separator — dùng khi
    ranh giới đoạn không quan trọng (tách lựa chọn A/B/C/D)."""
    out: list[Inline] = []
    for b in paras:
        out.extend(b.inlines)
    return out


def _needs_gap(prev: tuple, cur: tuple) -> bool:
    """True nếu cần tự chèn 1 dấu cách giữa 2 inline liền nhau (docx gốc nhiều
    chỗ gõ thiếu dấu cách giữa công thức và chữ theo sau/trước, VD: "S" rồi
    "và" dính thành "Svà"). Chỉ xét khi 1 bên là formula/image và cạnh text kề
    đó là chữ/số dính liền, không có khoảng trắng/dấu câu ngăn cách."""
    p_kind, p_plain, _ = prev
    c_kind, c_plain, _ = cur
    if p_kind == "text" and c_kind == "text":
        return False
    edge = p_plain[-1] if p_kind == "text" and p_plain else None
    cedge = c_plain[0] if c_kind == "text" and c_plain else None
    return any(e and e.isalnum() for e in (edge, cedge))


def _render_para(inlines: list[Inline], assets, math: dict[str, str]) -> str:
    """Render 1 paragraph thành HTML: KaTeX HTML cho công thức có LaTeX,
    <img> base64 cho ảnh/công thức không giải được."""
    parts: list[tuple[str, str | None, str]] = []
    for i in inlines:
        if i.kind == "text":
            formatted = _format_inline_text(i.text)
            def _math_sub(match):
                raw_tex = match.group(1).strip()
                return math.get(raw_tex) or math.get(mtef._tidy(raw_tex)) or f"[MATH: {raw_tex}]"
            html_text = re.sub(r'\[MATH:\s*(.*?)\]', _math_sub, _esc(formatted))
            parts.append(("text", i.text, html_text))
        elif i.kind == "formula":
            a = assets.get(i.ref)
            if a:
                raw_latex = a.latex.strip() if (a.latex and a.latex.strip()) else ""
                latex = mtef._tidy(raw_latex) if raw_latex else ""
                html = None
                if latex:
                    html = math.get(latex) or math.get(raw_latex) or f"[MATH: {latex}]"
                elif a.data:
                    html = _b64img(a)
                if html:
                    parts.append(("formula", None, html))
        elif i.kind == "image":
            img_html = _b64img(assets.get(i.ref))
            if img_html:
                parts.append(("image", None, img_html))

    out = []
    for idx, part in enumerate(parts):
        if idx and _needs_gap(parts[idx - 1], part):
            out.append(" ")
        out.append(part[2])
    return re.sub(r"[ \t]+", " ", "".join(out)).strip()




def _render(paras: list[Block], assets, math: dict[str, str], depth: int = 0) -> str | None:
    """Mỗi paragraph -> 1 <p> riêng, mỗi thẻ 1 dòng, thụt lề theo `depth`."""
    pad = "  " * depth
    lines = [_render_para(inl, assets, math) for inl in _flat(paras)]
    lines = [f"{pad}<p>{x}</p>" for x in lines if x]
    return "\n".join(lines) or None


def _wrap_math(latex: str) -> str:
    latex = latex.strip()
    if not latex:
        return ""
    punct = ""
    while latex and latex[-1] in ".,;":
        punct = latex[-1] + punct
        latex = latex[:-1].strip()
    if not latex:
        return punct
    return f"[MATH: {latex}]{punct}"


RE_MATH_EXPR = re.compile(
    r'(\\[a-zA-Z]+|[=<>≤≥±≠∈∉⊂⊃∪∩]|[-–]?\d+;|\([-?\d\w\\;]+;|\[-?\d\w\\;]+;|[A-Za-z]\s*=\s*[\{\[\(])'
)


RE_VIETNAMESE = re.compile(
    r'[àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ'
    r'ÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ]',
    re.IGNORECASE
)


RE_INLINE_MATH = re.compile(
    r'('
    r'\\[a-zA-Z]+\{[^\}]*\}|'                    # Macro with brace arg like \mathbb{R}
    r'\\[a-zA-Z]+|'                             # LaTeX macro like \cap, \in, \alpha
    r'[A-Z]\s*=\s*[\{\[\(][^\}\]\)]*[\}\]\)]|'  # Set notation like A={a;b;c;d}
    r'\{[^\}]+\}|'                              # Brace content like {1; 2; 3}
    r'\b[a-zA-Z]\s*[\=\<\>≤≥±≠∈∉⊂⊃∪∩]\s*[^,;.\s]+' # Equations/inequalities like x \in A
    r')'
)



def _format_inline_text(text: str) -> str:
    text_strip = text.strip()
    if not text_strip or text_strip.startswith("[MATH:") or text_strip.startswith("[IMAGE:"):
        return text

    # Strict promotion: ONLY promote if string has NO Vietnamese and contains explicit LaTeX macros
    if not RE_VIETNAMESE.search(text_strip):
        has_explicit_macro = bool(re.search(r'(\\[a-zA-Z]+|\{.*?\}|[A-Z]\s*=\s*[\{\[\(])', text_strip))
        if has_explicit_macro:
            m = re.match(r'^(.*?)([.,;]*)$', text_strip)
            if m:
                math_part = m.group(1).strip()
                punct_part = m.group(2)
                if math_part:
                    tidied = mtef._tidy(math_part)
                    return f"[MATH: {tidied}]{punct_part}"
    return text




def _render_para_text(inlines: list[Inline], assets, q_order: int = 1, img_collector: dict | None = None) -> str:
    """Render 1 paragraph thành plain text + [MATH: latex] + [IMAGE: assets/...] markers."""
    parts: list[tuple[str, str | None, str]] = []
    for i in inlines:
        if i.kind == "text":
            parts.append(("text", i.text, _format_inline_text(i.text)))
        elif i.kind == "formula":
            a = assets.get(i.ref)
            raw_latex = a.latex.strip() if (a and a.latex and a.latex.strip()) else ""
            latex = mtef._tidy(raw_latex) if raw_latex else ""
            if latex:
                math_str = _wrap_math(latex)

            elif a and a.data:
                ext = ".png" if "png" in (a.mime or "") else ".wmf"
                img_name = f"assets/q{q_order:03d}_f{a.aid}{ext}"
                if img_collector is not None:
                    img_collector[img_name] = a.data
                math_str = f"[IMAGE: {img_name}]"

            else:
                math_str = ""
            if math_str:
                parts.append(("formula", None, math_str))
        elif i.kind == "image":
            a = assets.get(i.ref)
            if a and a.data and img_collector is not None:
                ext = ".png" if "png" in (a.mime or "") else ".jpg"
                img_name = f"assets/q{q_order:03d}_{a.aid}{ext}"
                img_collector[img_name] = a.data
                parts.append(("image", None, f"[IMAGE: {img_name}]"))
            else:
                parts.append(("image", None, "[IMAGE]"))

    out = []
    for idx, part in enumerate(parts):
        if idx and _needs_gap(parts[idx - 1], part):
            out.append(" ")
        out.append(part[2])
    return re.sub(r"[ \t]+", " ", "".join(out)).strip()


def _render_text(paras: list[Block], assets, q_order: int = 1, img_collector: dict | None = None) -> str | None:
    """Ghép các paragraph thành chuỗi plain text phân cách bởi \\n\\n."""
    lines = [_render_para_text(inl, assets, q_order, img_collector) for inl in _flat(paras)]
    lines = [x for x in lines if x]
    return "\n\n".join(lines) or None


def _split_choices(paras: list[Block]) -> list[Choice]:
    choices: list[Choice] = []
    leading: list[Inline] = []   # nội dung đứng trước marker đầu tiên (nếu có)
    cur: Choice | None = None
    skip_punct = False   # sau marker gạch chân đứng lẻ, bỏ qua "." đứng lẻ theo ngay sau
    for inl in _flat_all(paras):
        if inl.kind == "text":
            m = RE_OPTION_MARK.match(inl.text)
            if m:
                cur = Choice(letter=m.group(1), bold=inl.bold, color=inl.color,
                             underline=inl.underline)
                choices.append(cur)
                skip_punct = False
                rest = inl.text[m.end():]
                if rest:
                    cur.items.append(Inline("text", rest, bold=inl.bold,
                                             color=inl.color, underline=inl.underline))
                continue
            m2 = RE_BARE_LETTER.match(inl.text) if inl.bold else None
            if m2:
                cur = Choice(letter=m2.group(1), bold=inl.bold, color=inl.color,
                             underline=inl.underline)
                choices.append(cur)
                skip_punct = True
                continue
            if skip_punct:
                skip_punct = False
                if RE_PUNCT_ONLY.match(inl.text):
                    continue
        if cur is not None:
            cur.items.append(inl)
        elif inl.kind != "text" or inl.text.strip():
            leading.append(inl)
    # Lỗi có thật trong nguồn: vài câu thiếu hẳn nhãn "A." (option bắt đầu
    # thẳng bằng công thức, không có chữ "A." nào) -> nếu không suy luận thì
    # nội dung option A bị vứt hoàn toàn và câu chỉ còn 3 lựa chọn.
    if leading and choices and choices[0].letter != "A":
        choices.insert(0, Choice(letter="A", items=leading, inferred=True))
    return choices


def _formatting_answer(choices: list[Choice]) -> tuple[str | None, str]:
    """Suy đáp án từ định dạng khi không có text tường minh. Trả (letter, cách_dò)."""
    underlined = [c for c in choices if c.underline or
                  any(i.kind == "text" and i.underline for i in c.items)]
    if len(underlined) == 1:
        return underlined[0].letter, "underline"
    colors = [c.color for c in choices]
    distinct = set(colors)
    if len(distinct) == 2:
        # màu xuất hiện đúng 1 lần trong 4 option -> option đó là đáp án
        counts = {c: colors.count(c) for c in distinct}
        odd = [c for c in distinct if counts[c] == 1]
        if len(odd) == 1:
            hit = [c for c, col in zip(choices, colors) if col == odd[0]]
            if len(hit) == 1:
                return hit[0].letter, "color"
    return None, "unresolved"


def _cognitive(text: str) -> tuple[str | None, int | None]:
    t = fold(text)
    m = RE_LEVEL.match(t)
    if m:
        return LEVEL_MAP.get(int(m.group(1)), (None, None))
    m = RE_BLOOM.match(text.strip())
    if m:
        # BLOOM_MAP dùng key CÓ dấu (giống văn bản gốc) -> chỉ lower(), không
        # fold() (fold bỏ dấu, làm mất khớp với key "nhận biết"/"thông hiểu"...).
        return BLOOM_MAP.get(m.group(1).strip().lower(), (None, None))
    return None, None


def _extract_meta(path: Path, head: list[str]) -> dict:
    folded = [fold(p) for p in path.parts]
    subject_dir = next((f for f in folded
                        if re.search(r"(toan|hoa|van|dia|gdktpl)\s*\d", f)), fold(path.stem))
    code, name = next(((c, n) for k, (c, n) in SUBJECTS.items() if k in subject_dir),
                      ("unk", "?"))
    gm = re.search(r"\b(1[0-2])\b", subject_dir)
    grade = int(gm.group(1)) if gm else None

    stem, number, title = path.stem, None, ""
    for cand in [stem, *head]:
        lm = re.search(r"(?i)b[àa]i\s*(\d{1,2})", cand)
        if lm:
            number = int(lm.group(1))
            title = re.sub(r"(?i)^.*?b[àa]i\s*\d{1,2}\s*[.:\-–_)]*\s*", "", cand).strip()
            break
    vb = next((h for h in head if re.match(r"(?i)^(v[aă]n b[ảa]n|đọc)\s*\d*\s*[:.\-–]", h)), None)
    if vb:
        title = re.sub(r"(?i)^(v[aă]n b[ảa]n|đọc)\s*\d*\s*[:.\-–]\s*", "", vb).strip()
    if not title:
        title = re.sub(r"^\s*\d+\s*[.)]\s*", "", stem)
    if title.startswith("(") and title.endswith(")"):
        title = title[1:-1].strip()
    lesson_name = f"Bài {number}. {title}" if number else title
    chapter_name = None
    for part in path.parts[:-1]:
        if re.search(r"(?i)\bchương\b", part):
            chapter_name = part.strip()
            break
    if not chapter_name:
        for h in head:
            if re.search(r"(?i)^\s*chương\b", h):
                chapter_name = h.strip()
                break

    return {"subject": code, "subject_vi": name, "grade": grade, "lesson_name": lesson_name, "chapter_name": chapter_name}


def convert(path: str | Path) -> tuple[str, list[dict]]:
    """Trả (html, debug) — debug chỉ để review, KHÔNG đưa vào file output.
    html là 1 trang hoàn chỉnh, mỗi câu hỏi là 1 <section>."""
    path = Path(path)
    doc = DocxReader(path).parse()
    head = [b.text for b in doc.blocks[:6] if b.kind == "para" and b.text]
    meta = _extract_meta(path, head)
    _t_start, t_end, _flags, _heading = find_theory(doc.blocks)
    if t_end < 0:
        return "<!doctype html>\n<html><body></body></html>", []

    latex_list = [a.latex for a in doc.assets.values() if a.kind == "formula" and a.latex]
    math = mathrender.render_many(latex_list)

    body = doc.blocks[t_end + 1:]
    sections: list[str] = []
    debug: list[dict] = []
    order = 0
    cog_level, cog_num = None, None

    # Cắt thành từng khối [q_start, q_end) theo "Câu n." — paragraph không nằm
    # trong khối nào (ví dụ heading "Level 1:") được xét riêng cho cognitive level.
    #
    # Có câu KHÔNG đánh số (thường là câu đầu tiên ngay sau heading "Level n:")
    # -> nếu bỏ qua từng paragraph lạc một cách im lặng sẽ MẤT nguyên câu đó mà
    # không có dấu vết. Dồn các paragraph "lạc" (chưa thuộc câu nào) vào
    # `pending`; khi chạm mốc kế tiếp (Câu N. hoặc Level mới), nếu `pending`
    # trông như một câu hỏi thật (có "Lời giải"/"Đáp án" hoặc có option) thì
    # vẫn tạo thành 1 câu không số, không âm thầm bỏ.
    idx = 0
    pending_start = 0

    def flush_pending(upto: int):
        nonlocal order
        if pending_start >= upto:
            return
        stray = body[pending_start:upto]
        if _looks_like_question(stray):
            order += 1
            html, dbg = _build_question([], "", stray, doc.assets, math, meta, order,
                                        cog_level, cog_num)
            sections.append(html)
            debug.append(dbg)

    while idx < len(body):
        b = body[idx]
        if b.kind == "para":
            lv, lvn = _cognitive(b.text)
            if lv:
                flush_pending(idx)
                cog_level, cog_num = lv, lvn
                idx += 1
                pending_start = idx
                continue
            m = RE_QUESTION.match(b.text)
            if m:
                flush_pending(idx)
                q_start = idx
                idx += 1
                # Dừng ở "Câu n." KẾ TIẾP hoặc heading Level/Bloom kế tiếp — nếu
                # chỉ dừng ở "Câu n." thì heading Level sẽ bị nuốt luôn vào thân
                # câu hỏi hiện tại, và câu không đánh số ngay sau heading đó bị
                # gán nhầm vào explanation của câu TRƯỚC (đã xảy ra với "Level 3:").
                while idx < len(body) and not (
                        body[idx].kind == "para" and
                        (RE_QUESTION.match(body[idx].text) or _cognitive(body[idx].text)[0])):
                    idx += 1
                q_body = body[q_start + 1:idx]   # bỏ paragraph "Câu n." (giữ lại phần đề)
                stem_first = [b]                  # nội dung đề còn nằm luôn trên dòng "Câu n."
                stem_rest_text = RE_QUESTION.sub("", b.text, count=1)
                order += 1
                html, dbg = _build_question(stem_first, stem_rest_text, q_body, doc.assets,
                                            math, meta, order, cog_level, cog_num)
                sections.append(html)
                debug.append(dbg)
                pending_start = idx
                continue
        idx += 1
    flush_pending(idx)

    page = "\n".join(x for x in [
        "<!doctype html>",
        "<html>",
        "<head>",
        '  <meta charset="utf-8">',
        f"  <title>{_esc(meta['lesson_name'])}</title>",
        f"  <style>{mathrender.katex_css()}</style>" if latex_list else "",
        "</head>",
        "<body>",
        f"  <h1>{_esc(meta['lesson_name'])}</h1>",
        *sections,
        "</body>",
        "</html>",
    ] if x)
    return page, debug


def _looks_like_question(paras: list[Block]) -> bool:
    if any(b.kind == "para" and (RE_ANSWER_HEAD.match(b.text) or RE_OPTION_ANY.search(b.text))
           for b in paras):
        return True
    return sum(len(b.text) for b in paras if b.kind == "para") > 30


def _dl(pairs: list[tuple[str, str | int | float | None]], depth: int) -> str:
    """<dl> chỉ chứa các field có giá trị — field None bị bỏ hẳn, không suy đoán."""
    pad = "  " * depth
    rows = [f"{pad}  <dt>{_esc(k)}</dt><dd>{_esc(str(v))}</dd>"
            for k, v in pairs if v is not None and v != ""]
    if not rows:
        return ""
    return "\n".join([f"{pad}<dl>", *rows, f"{pad}</dl>"])


def _trim_question_prefix(b: Block) -> list[Inline]:
    out = list(b.inlines)
    if not out:
        return []
    for idx, inl in enumerate(out):
        if inl.kind == "text":
            m = RE_QUESTION.match(inl.text)
            if m:
                new_text = inl.text[m.end():]
                if new_text:
                    out[idx] = Inline("text", new_text, bold=inl.bold, color=inl.color, underline=inl.underline)
                else:
                    out.pop(idx)
                break
    return out


def _build_question(stem_first: list[Block], stem_rest_text: str, body: list[Block],
                     assets, math: dict[str, str], meta: dict, order: int,
                     cog_level, cog_num) -> tuple[str, dict]:
    opt_start = next((i for i, b in enumerate(body)
                      if b.kind == "para" and RE_OPTION_ANY.search(b.text)), None)
    ans_start = next((i for i, b in enumerate(body)
                      if b.kind == "para" and RE_ANSWER_HEAD.match(b.text)), None)

    stem_paras = body[:opt_start] if opt_start is not None else (
        body[:ans_start] if ans_start is not None else body)
    opt_paras = body[opt_start:ans_start] if opt_start is not None else []
    tail_paras = body[ans_start:] if ans_start is not None else []

    # Nội dung đề: phần chữ ngay sau "Câu n." (nếu có) + các paragraph đề tiếp theo.
    head_inlines = _trim_question_prefix(stem_first[0]) if stem_first else []
    head_html = f"    <p>{_render_para(head_inlines, assets, math)}</p>" if head_inlines else ""
    stem_html = _render(stem_paras, assets, math, depth=2) or ""
    content_html = "\n".join(x for x in [head_html, stem_html] if x)

    choices = _split_choices(opt_paras) if opt_start is not None else []
    choices_html = ""
    if choices:
        items = "\n".join(f'      <li>{_render_para(c.items, assets, math)}</li>' for c in choices)
        choices_html = "\n".join(['    <ol type="A">', items, "    </ol>"])

    letter, ans_source, explanation_html = None, "none", ""
    if tail_paras:
        first_text = tail_paras[0].text
        m = RE_DAPAN.match(first_text)
        if m:
            letter, ans_source = m.group(1), "text:đáp_án"
            rest = RE_DAPAN.sub("", first_text, count=1)
            rest_paras = [Block("para", inlines=[Inline("text", rest)])] + tail_paras[1:]
            explanation_html = _render(rest_paras, assets, math, depth=2) or ""
        elif RE_LOIGIAI.match(first_text.strip()):
            if len(tail_paras) >= 2 and RE_CHON.match(tail_paras[1].text):
                m2 = RE_CHON.match(tail_paras[1].text)
                letter, ans_source = m2.group(1), "text:chọn"
                rest = RE_CHON.sub("", tail_paras[1].text, count=1)
                rest_paras = ([Block("para", inlines=[Inline("text", rest)])]
                              if rest.strip() else []) + tail_paras[2:]
                explanation_html = _render(rest_paras, assets, math, depth=2) or ""
            else:
                explanation_html = _render(tail_paras[1:], assets, math, depth=2) or ""
                ans_source = "essay_no_answer_letter"
        elif RE_CHON.match(first_text):
            m2 = RE_CHON.match(first_text)
            letter, ans_source = m2.group(1), "text:chọn"
            rest = RE_CHON.sub("", first_text, count=1)
            rest_paras = ([Block("para", inlines=[Inline("text", rest)])]
                          if rest.strip() else []) + tail_paras[1:]
            explanation_html = _render(rest_paras, assets, math, depth=2) or ""
        else:
            explanation_html = _render(tail_paras, assets, math, depth=2) or ""
            ans_source = "unrecognized_tail_format"

    if letter is None and choices:
        letter, fmt_source = _formatting_answer(choices)
        if letter:
            ans_source = f"format:{fmt_source}"

    q_type = "single-choice" if choices else "essay"
    dl = _dl([
        ("Loại", q_type), ("Môn", meta["subject_vi"]), ("Khối", meta["grade"]),
        ("Bài", meta["lesson_name"]), ("Mức độ nhận thức", cog_level),
        ("Mã mức độ", cog_num), ("Đáp án", letter),
    ], depth=2)
    explanation_block = "\n".join(["    <div>", explanation_html, "    </div>"]) \
        if explanation_html else ""
    html = "\n".join(x for x in [
        "  <section>",
        f"    <h2>Câu {order}</h2>",
        dl,
        content_html,
        choices_html,
        explanation_block,
        "  </section>",
    ] if x)
    dbg = {"order": order, "answer": letter, "answer_source": ans_source,
           "n_choices": len(choices), "inferred_A": any(c.inferred for c in choices)}
    return html, dbg


LETTER_MAP = {"A": 1, "B": 2, "C": 3, "D": 4}


def _build_question_json(stem_first: list[Block], stem_rest_text: str, body: list[Block],
                         assets, meta: dict, order: int,
                         cog_level: str | None, cog_num: int | None, doc_stem: str = "",
                         math_dict: dict[str, str] | None = None) -> tuple[dict, dict]:
    opt_start = next((i for i, b in enumerate(body)
                      if b.kind == "para" and RE_OPTION_ANY.search(b.text)), None)
    ans_start = next((i for i, b in enumerate(body)
                      if b.kind == "para" and RE_ANSWER_HEAD.match(b.text)), None)

    stem_paras = body[:opt_start] if opt_start is not None else (
        body[:ans_start] if ans_start is not None else body)
    opt_paras = body[opt_start:ans_start] if opt_start is not None else []
    tail_paras = body[ans_start:] if ans_start is not None else []

    math_dict = math_dict or {}

    head_inlines = _trim_question_prefix(stem_first[0]) if stem_first else []
    head_html = f"<p>{_render_para(head_inlines, assets, math_dict)}</p>" if head_inlines else ""
    stem_html = _render(stem_paras, assets, math_dict) or ""
    content_html = "\n".join(x for x in [head_html, stem_html] if x)

    choices = _split_choices(opt_paras) if opt_start is not None else []
    choices_list = None
    if choices:
        choices_list = []
        for i, c in enumerate(choices):
            c_html = _render_para(c.items, assets, math_dict).strip()
            if c_html:
                c_html = f"<p>{c_html}</p>"
            choices_list.append({"id": i + 1, "content": c_html})



    letter, ans_source, explanation_html = None, "none", ""
    if tail_paras:
        first_text = tail_paras[0].text
        m = RE_DAPAN.match(first_text)
        if m:
            letter, ans_source = m.group(1), "text:đáp_án"
            rest = RE_DAPAN.sub("", first_text, count=1)
            rest_paras = [Block("para", inlines=[Inline("text", rest)])] + tail_paras[1:]
            explanation_html = _render(rest_paras, assets, math_dict) or ""
        elif RE_LOIGIAI.match(first_text.strip()):
            if len(tail_paras) >= 2 and RE_CHON.match(tail_paras[1].text):
                m2 = RE_CHON.match(tail_paras[1].text)
                letter, ans_source = m2.group(1), "text:chọn"
                rest = RE_CHON.sub("", tail_paras[1].text, count=1)
                rest_paras = ([Block("para", inlines=[Inline("text", rest)])]
                              if rest.strip() else []) + tail_paras[2:]
                explanation_html = _render(rest_paras, assets, math_dict) or ""
            else:
                explanation_html = _render(tail_paras[1:], assets, math_dict) or ""
                ans_source = "essay_no_answer_letter"
        elif RE_CHON.match(first_text):
            m2 = RE_CHON.match(first_text)
            letter, ans_source = m2.group(1), "text:chọn"
            rest = RE_CHON.sub("", first_text, count=1)
            rest_paras = ([Block("para", inlines=[Inline("text", rest)])]
                          if rest.strip() else []) + tail_paras[1:]
            explanation_html = _render(rest_paras, assets, math_dict) or ""
        else:
            explanation_html = _render(tail_paras, assets, math_dict) or ""
            ans_source = "unrecognized_tail_format"

    if letter is None and choices:
        letter, fmt_source = _formatting_answer(choices)
        if letter:
            ans_source = f"format:{fmt_source}"

    # Determine q_type, choices, answer format, fillMatchMode, essayGuideline
    raw_letters = [l.upper() for l in re.findall(r"[A-D]", letter.upper())] if letter else []

    fill_match_mode = None
    essay_guideline = None
    answer_val = None

    # True-False Group detection
    is_tf_group = False
    if choices_list and len(choices_list) >= 2:
        is_tf_group = all(re.search(r"(?i)^\s*<p>\s*[a-d1-4][.)]", c.get("content", "")) for c in choices_list)

    if is_tf_group:
        q_type = "true-false-group"
        tail_text = " ".join(b.text for b in tail_paras) if tail_paras else ""
        tf_ans = []
        for c in choices_list:
            cid = c["id"]
            l_code = chr(96 + cid)
            m_tf = re.search(fr"(?i)\b{l_code}[.)]?\s*(đúng|sai|true|false)\b", tail_text)
            val = "true"
            if m_tf:
                val = "true" if m_tf.group(1).lower() in ("đúng", "true") else "false"
            tf_ans.append({"id": cid, "value": val})
        answer_val = tf_ans

    elif not choices_list:
        plain_stem = content_html
        if "___" in plain_stem or "[___]" in plain_stem or "[...]" in plain_stem:

            q_type = "fill-answer"
            choices_list = None
            fill_match_mode = "case_insensitive"
            tail_text = " ".join(b.text for b in tail_paras).strip() if tail_paras else ""
            if tail_text:
                items = [t.strip() for t in re.split(r"[,;]\s*", tail_text) if t.strip()]
                answer_val = [items] if items else [[""]]
            else:
                answer_val = [[""]]
        else:
            q_type = "essay"
            choices_list = None
            answer_val = None
            if explanation_html:
                m_g = re.search(r"(?i)(chấm theo[^.<]*|hướng dẫn chấm[^.<]*)", explanation_html)
                if m_g:
                    essay_guideline = m_g.group(0).strip()

    elif len(raw_letters) > 1:
        q_type = "multiple-choice"
        answer_val = [LETTER_MAP[l] for l in raw_letters if l in LETTER_MAP]

    else:
        q_type = "single-choice"
        if raw_letters and raw_letters[0] in LETTER_MAP:
            answer_val = [LETTER_MAP[raw_letters[0]]]
        elif letter and letter.upper() in LETTER_MAP:
            answer_val = [LETTER_MAP[letter.upper()]]
        else:
            answer_val = None

    seed = f"{doc_stem}_{order}"
    oid_hex = hashlib.md5(seed.encode()).hexdigest()[:24]

    q_data = {
        "_id": {"$oid": oid_hex},
        "examId": None,
        "type": q_type,
        "content": content_html,
        "choices": choices_list,
        "answer": answer_val,
        "fillMatchMode": fill_match_mode,
        "essayGuideline": essay_guideline,
        "explanation": explanation_html or None,
        "imageUrl": None,
        "score": None,
        "order": order,
        "isDeleted": 0,
        "createdAt": None,
        "updatedAt": None,
        "subject": meta["subject"],
        "subject_vi": meta["subject_vi"],
        "grade": meta["grade"],
        "cognitive_level": cog_level,
        "difficulty": meta.get("difficulty"),
        "is_synthesis": meta.get("is_synthesis", False),
        "estimated_time_sec": meta.get("estimated_time_sec"),
        "chapter_name": meta.get("chapter_name"),
        "lesson_name": meta["lesson_name"],
        "kc_id": meta.get("kc_id"),
        "kc_ids": meta.get("kc_ids"),
        "cognitive_level_num": cog_num,
        "elo_difficulty": meta.get("elo_difficulty"),
        "time_fast_ms": meta.get("time_fast_ms"),
        "time_slow_ms": meta.get("time_slow_ms"),
    }

    dbg = {"order": order, "answer": answer_val, "answer_source": ans_source,
           "n_choices": len(choices) if choices else 0, "inferred_A": any(c.inferred for c in choices) if choices else False}
    return q_data, dbg


def convert_json(path: str | Path) -> tuple[list[dict], list[dict]]:
    """Trả (questions_json, debug) — questions_json là list các dict theo baitap_ref schema."""
    path = Path(path)
    doc = DocxReader(path).parse()
    head = [b.text for b in doc.blocks[:6] if b.kind == "para" and b.text]
    meta = _extract_meta(path, head)
    _t_start, t_end, _flags, _heading = find_theory(doc.blocks)
    if t_end < 0:
        return [], []

    latex_list = [a.latex for a in doc.assets.values() if a and a.latex]
    for b in doc.blocks:
        for inl in b.inlines:
            if inl.kind == "text":
                formatted = _format_inline_text(inl.text)
                for m in re.finditer(r'\[MATH:\s*(.*?)\]', formatted):
                    latex_list.append(m.group(1))

    math_dict = mathrender.render_many(latex_list) if latex_list else {}


    body = doc.blocks[t_end + 1:]
    questions: list[dict] = []
    debug: list[dict] = []
    order = 0
    cog_level, cog_num = None, None

    idx = 0
    pending_start = 0

    def flush_pending(upto: int):
        nonlocal order
        if pending_start >= upto:
            return
        stray = body[pending_start:upto]
        if _looks_like_question(stray):
            order += 1
            q_data, dbg = _build_question_json([], "", stray, doc.assets, meta, order,
                                                cog_level, cog_num, doc_stem=path.stem,
                                                math_dict=math_dict)
            questions.append(q_data)
            debug.append(dbg)

    while idx < len(body):
        b = body[idx]
        if b.kind == "para":
            lv, lvn = _cognitive(b.text)
            if lv:
                flush_pending(idx)
                cog_level, cog_num = lv, lvn
                idx += 1
                pending_start = idx
                continue
            m = RE_QUESTION.match(b.text)
            if m:
                flush_pending(idx)
                q_start = idx
                idx += 1
                while idx < len(body) and not (
                        body[idx].kind == "para" and
                        (RE_QUESTION.match(body[idx].text) or _cognitive(body[idx].text)[0])):
                    idx += 1
                q_body = body[q_start + 1:idx]
                stem_first = [b]
                stem_rest_text = RE_QUESTION.sub("", b.text, count=1)
                order += 1
                q_data, dbg = _build_question_json(stem_first, stem_rest_text, q_body, doc.assets,
                                                    meta, order, cog_level, cog_num, doc_stem=path.stem,
                                                    math_dict=math_dict)
                questions.append(q_data)
                debug.append(dbg)
                pending_start = idx
                continue
        idx += 1
    flush_pending(idx)

    return questions, debug
