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

# Công thức không parse được ở chế độ nghiêm — dữ liệu cho Cổng 1. Xem failures().
_failures: list[dict[str, str]] = []

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
    # RAW MODE: Disabled _wrap_bare_words
    return tex



def clear_cache():
    _cache.clear()
    _failures.clear()


def failures() -> list[dict[str, str]]:
    """Các công thức KaTeX KHÔNG parse được ở chế độ nghiêm, tích luỹ từ lần
    clear_cache() gần nhất.

    Mỗi phần tử: {"latex": <latex sau _wrap_bare_words>, "source": <latex gốc>,
    "error": <thông báo KaTeX>}.

    Đây là dữ liệu để Cổng 1 (xem tools/check_katex.py) làm fail build. Trước
    đây thông tin này bị mất hoàn toàn vì katex_render.js chỉ dùng
    throwOnError:false — lỗi đỏ đi thẳng ra sản phẩm mà không ai biết.
    """
    return list(_failures)


def render_many(latex_list: list[str]) -> dict[str, str]:
    """Trả {latex: html}. Latex nào KaTeX không parse được thì rơi lại thành
    `<code>latex gốc</code>` (không mất thông tin, không giả vờ đã dựng đúng).

    Song song, mọi công thức không đạt chế độ nghiêm được ghi vào failures().
    """
    from html import escape as _esc

    _cache.clear()  # Clear cache on every run so updated _tidy rules take effect!
    uniq = sorted(set(latex_list))
    todo = [s for s in uniq if s not in _cache]
    if todo:
        prepared = [_wrap_bare_words(s) for s in todo]
        proc = subprocess.run(
            ["node", str(_NODE_SCRIPT)], input=json.dumps(prepared),
            capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            raise RuntimeError(f"katex_render.js lỗi: {proc.stderr}")
        for src, prep, item in zip(todo, prepared, json.loads(proc.stdout)):
            # Tương thích cả contract cũ (chuỗi html) và mới ({html, error})
            if isinstance(item, dict):
                _cache[src] = item.get("html")
                if item.get("error"):
                    _failures.append({"latex": prep, "source": src, "error": item["error"]})
            else:
                _cache[src] = item

    return {s: (_cache[s] or f"<code>{_esc(s)}</code>") for s in uniq}


def katex_css() -> str:
    return _KATEX_CSS.read_text(encoding="utf-8")
