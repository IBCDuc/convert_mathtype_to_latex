"""Render LaTeX công thức thành HTML thật (KaTeX) thay cho text "[MATH: ...]".

Gọi node (package `katex`, xem package.json) qua subprocess theo lô — 1 lần
gọi node cho toàn bộ công thức của 1 file docx, không phải 1 lần/công thức,
để đỡ tốn thời gian khởi động Node lặp lại. Kết quả cache theo chuỗi LaTeX vì
nhiều công thức lặp lại y hệt nhau giữa các câu hỏi trắc nghiệm.

HTML do KaTeX renderToString() sinh ra cần CSS riêng (`katex_css()`) để canh
vị trí subscript/superscript/phân số — không có CSS này công thức vẫn đọc
được (KaTeX vẫn in ký tự Unicode thật) nhưng bị lệch canh.
"""
from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from pathlib import Path

_NODE_SCRIPT = Path(__file__).parent / "katex_render.js"
_KATEX_CSS = Path(__file__).parent.parent / "node_modules" / "katex" / "dist" / "katex.min.css"

_cache: dict[str, str | None] = {}

# Equation Editor trong docx gốc nhiều chỗ gõ lẫn chữ tiếng Việt vào NGAY
# TRONG vùng công thức (VD: "x ∈ S và x ∉ T" — "và" là chữ thường, không phải
# biến toán), nên omml_to_latex() lấy ra latex kiểu 'S\T={x|x\in S và x\in T}'.
# KaTeX coi "và" là 2 biến toán rời ("v", "a") + dấu, ra "v a ˋ" sai lệch.
# Bọc các "từ" trần (chữ liền nhau >=2 ký tự, KHÔNG đứng sau "\") vào \text{}
# để KaTeX in nguyên chữ, không tách ký tự có dấu ra như biến toán.
_VIET_WORD_RE = re.compile(
    r"(?<!\\)\b([a-zA-ZàáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ]{2,})\b"
)
_VIET_DIACRITICS = re.compile(r"[àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ]")
_VIET_WORDS_ASCII = {
    "va", "hoac", "voi", "khi", "neu", "thi", "la", "thuoc", "tai", "tren", "duoi",
    "thoa", "man", "ke", "bo", "trong", "do", "nhung", "dong", "thoi", "bang", "an",
    "so", "cap", "mient", "nghiem", "cua", "bat", "phuong", "trinh", "bac", "nhat", "hai"
}

_NEQ_RE = re.compile(r"\\not\s*=|\\cancel\s*\{\s*=\s*\}|≠|[\u0338]=|=[\u0338]|̸=")


def _wrap_bare_words(tex: str) -> str:
    tex = unicodedata.normalize("NFC", tex)
    tex = _NEQ_RE.sub(r" \\ne ", tex)
    tex = re.sub(r"[\uE000-\uF8FF]", "", tex)
    # Fix manual backslash set difference (e.g. S\T, A\B -> S \setminus T) causing red KaTeX error
    tex = re.sub(r"\\([A-Za-z])(?![a-zA-Z])", r" \\setminus \1", tex)
    # Clean TCVN3 / MTEF artifacts like § for Đ
    tex = tex.replace("§", "Đ")
    # Convert bare subscript patterns: x0 -> x_0, y0 -> y_0, A1 -> A_1, fct -> f_{CT}, ycd -> y_{CĐ}
    def _subscript_repl(m):
        var, num = m.group(1), m.group(2)
        if var in ('k', 'K') and num in ('360', '180', '720', '90', '2'):
            return m.group(0)
        return f"{var}_{{{num}}}"
    tex = re.sub(r"(?<!\\)\b([a-zA-Z])([0-9]+)\b", _subscript_repl, tex)
    tex = re.sub(r"(?<![\\a-zA-Z])(y|f|x)(ct|CT)\b", r"\1_{CT}", tex)
    tex = re.sub(r"(?<![\\a-zA-Z])(y|f|x)(cd|CD|CĐ)\b", r"\1_{CĐ}", tex)
    # Fix setminus corruptions like \set \min us, \set minus, \setminus
    tex = re.sub(r"\\set\s*\\min\s*us\b|\\set\s*minus\b", r" \\setminus ", tex)
    # Clean ray / vector notation like \mathrm{Om}, \mathrm{Ou}, \mathrm{Ov} -> Om, Ou, Ov
    tex = re.sub(r"\\mathrm\{O([uvmxyz])\}", r"O\1", tex)
    tex = re.sub(r"\\mathrm\{O\}\s*([uvmxyz])", r"O\1", tex)
    tex = re.sub(r"\bO\s+([uvmxyz])\b", r"O\1", tex)
    # Upgrade \frac to \dfrac for balanced fraction rendering
    tex = re.sub(r"(?<!\\)\bfrac\b", "dfrac", tex)
    # Force subscript of lim/max/min/sup/inf to appear BELOW the operator (not to the side)
    # even in inline math mode. \limits modifier achieves this in KaTeX.
    # Pattern: \lim_ or \max_ etc. (without \limits already present)
    tex = re.sub(r"\\(lim|max|min|sup|inf|limsup|liminf)(?!\\limits)\s*_",
                 r"\\\1\\limits_", tex)
    # Fix misplaced superscripts after limit subscripts (e.g. \lim\limits_{x\to x_0} ^{+} -> \lim\limits_{x\to x_0^{+}})
    tex = re.sub(r"\\(lim|max|min|sup|inf)(?:\\limits)?\s*_\{(.+?)\}\s*\^\{([\+\-]+)\}",
                 r"\\\1\\limits_{\2^{\3}}", tex, flags=re.IGNORECASE)
    tex = re.sub(r"\\(lim|max|min|sup|inf)(?:\\limits)?\s*\^\{([\+\-]+)\}\s*_\{(.+?)\}",
                 r"\\\1\\limits_{\3^{\2}}", tex, flags=re.IGNORECASE)
    def repl(m):
        w = m.group(1)
        if _VIET_DIACRITICS.search(w) or w.lower() in _VIET_WORDS_ASCII:
            return r"\text{ %s }" % w
        return w
    return _VIET_WORD_RE.sub(repl, tex)


def clear_cache():
    _cache.clear()


def render_many(latex_list: list[str]) -> dict[str, str]:
    """Trả {latex: html}. Latex nào KaTeX không parse được thì rơi lại thành
    `<code>latex gốc</code>` (không mất thông tin, không giả vờ đã dựng đúng)."""
    from html import escape as _esc

    _cache.clear()  # Clear cache on every run so updated _tidy rules take effect!
    uniq = sorted(set(latex_list))
    todo = [s for s in uniq if s not in _cache]
    if todo:
        proc = subprocess.run(
            ["node", str(_NODE_SCRIPT)], input=json.dumps([_wrap_bare_words(s) for s in todo]),
            capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            raise RuntimeError(f"katex_render.js lỗi: {proc.stderr}")
        for src, html in zip(todo, json.loads(proc.stdout)):
            _cache[src] = html

    return {s: (_cache[s] or f"<code>{_esc(s)}</code>") for s in uniq}


def katex_css() -> str:
    return _KATEX_CSS.read_text(encoding="utf-8")
