"""Test: dọn ngoặc thừa sau chỉ số dưới KHÔNG được phá group bao ngoài.

Bug đã sửa
----------
``_tidy`` từng có luật::

    re.sub(r"(_\\{[^{}]+\\})}+", r"\\1", s)      # y_{CT}} -> y_{CT}

Nó xoá dấu ``}`` sau MỌI chỉ số dưới, không kiểm xem group bao ngoài có cần dấu
đó hay không. Nên mọi phân số có tử số mang chỉ số dưới đều bị phá::

    \\frac{M_{polymer}}{n}  ->  \\frac{M_{polymer}{n}  ->  \\frac{M_{polymer}{n}}

Đây là 3 lỗi KaTeX cuối cùng còn sót trong production, và chúng đi qua đường
**OMML** (docxast.py:170 chạy _tidy cho cả OMML) chứ không phải MTEF — nên
scan riêng MTEF không thấy.

``balance_braces()`` làm việc này đúng và đúng vị trí, nên luật kia đã được xoá.
"""

import pytest

from pipeline import mtef

# Ngoặc thừa THẬT sự mồ côi -> phải bỏ
ORPHAN = [
    (r"y_{CT}}", r"y_{CT}"),
    (r"x_{1}}", r"x_{1}"),
]

# Ngoặc đóng group bao ngoài -> phải GIỮ
KEEP = [
    r"\frac{M_{polymer}}{n}",
    r"\frac{A_{1}.x_{1} + A_{2}.x_{2}}{100}",
    r"\frac{x_{0}}{y_{0}}",
    r"\sqrt{a_{n}}",
    r"\overline{x_{1}}",
    r"\frac{M_{polymer}}{n_{1}}",
]


@pytest.mark.parametrize("src,want", ORPHAN)
def test_orphan_brace_after_subscript_removed(src, want):
    assert mtef._tidy(src) == want


@pytest.mark.parametrize("src", KEEP)
def test_enclosing_group_brace_preserved(src):
    out = mtef._tidy(src)
    # \frac phải còn ĐÚNG hai đối số; sau khi hỏng nó thành \frac{A{B}}
    assert out == src or out.replace(" ", "") == src.replace(" ", ""), (
        f"phá group bao ngoài: {src!r} -> {out!r}"
    )


@pytest.mark.parametrize("src", KEEP)
def test_stays_katex_parsable_shape(src):
    r"""Không được sinh ra dạng ``\frac{A{B}}`` (tử số chưa đóng)."""
    import re

    out = mtef._tidy(src)
    assert re.search(r"\\d?frac\{[^{}]*\{[^{}]*\}\}(?!\{)", out) is None, out
