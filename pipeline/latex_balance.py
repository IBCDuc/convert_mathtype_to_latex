"""Cân bằng ngoặc LaTeX bằng NGĂN XẾP, thay cho cách đếm-rồi-cắt-đuôi.

VÌ SAO KHÔNG DÙNG REGEX / ĐẾM TỔNG
----------------------------------
Cân bằng ngoặc lồng nhau là bài toán **context-free** — cần ngăn xếp không giới
hạn. Regex (automat hữu hạn) không biểu diễn nổi. Cách cũ trong ``_tidy``::

    n_open  = số '{'
    n_close = số '}'
    while n_close > n_open and s.endswith('}'):
        s = s[:-1]                      # <-- CẮT Ở CUỐI CHUỖI

đếm **tổng số** rồi cắt **ở cuối**, nên khi dấu ``}`` thừa nằm ở GIỮA, nó cắt
mất dấu ``}`` hợp lệ của ``\\frac`` ở cuối::

    \\frac{1}{c o s}   ->   \\frac{1{c o s}      (mất dấu } của tử số)

Đo được: cách cũ tự tạo ra 30 công thức lệch ngoặc mà bản raw không hề có.

CÁCH ĐÚNG
---------
Ghép cặp thật bằng ngăn xếp:

* ``}`` **mồ côi** (không có ``{`` tương ứng đang mở) -> BỎ ĐI, tại đúng vị trí
  của nó. Không đẩy sang cuối, không cắt nhầm dấu khác.
* ``{`` còn hở ở cuối -> thêm ``}`` để đóng.

``\\{``, ``\\}`` là ngoặc LITERAL (phần tử tập hợp) chứ không phải ngoặc nhóm,
nên không được tính vào ngăn xếp — đây là chỗ cách đếm bằng ``(?<!\\\\)`` cũng
làm đúng, nhưng ngăn xếp thì làm đúng cả vị trí.
"""

from __future__ import annotations

__all__ = ["balance_braces", "brace_defects"]


def _scan(s: str):
    """Sinh (kind, text, index) với kind ∈ {'open','close','other'}.

    Escape hai ký tự (``\\{``, ``\\}``, ``\\\\``, ``\\alpha``...) luôn là 'other'.
    """
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            yield "other", s[i:i + 2], i
            i += 2
            continue
        if c == "{":
            yield "open", c, i
        elif c == "}":
            yield "close", c, i
        else:
            yield "other", c, i
        i += 1


def brace_defects(s: str) -> dict[str, int]:
    """Đếm khuyết tật ngoặc mà KHÔNG sửa — dùng cho assert/telemetry."""
    stack = 0
    orphan_close = 0
    for kind, _t, _i in _scan(s):
        if kind == "open":
            stack += 1
        elif kind == "close":
            if stack:
                stack -= 1
            else:
                orphan_close += 1
    return {"orphan_close": orphan_close, "unclosed_open": stack}


def balance_braces(s: str) -> tuple[str, list[str]]:
    """Cân bằng ``{}`` bằng ngăn xếp. Trả ``(kết quả, ghi chú)``.

    Idempotent: kết quả luôn cân bằng nên gọi lại không đổi gì.
    """
    notes: list[str] = []
    out: list[str] = []
    depth = 0

    for kind, text, idx in _scan(s):
        if kind == "open":
            depth += 1
            out.append(text)
        elif kind == "close":
            if depth > 0:
                depth -= 1
                out.append(text)
            else:
                # } mồ côi: bỏ tại chỗ, KHÔNG cắt ở cuối chuỗi
                notes.append(f"dropped_orphan_close@{idx}")
        else:
            out.append(text)

    if depth:
        out.append("}" * depth)
        notes.append(f"closed_unclosed_open:{depth}")

    return "".join(out), notes
