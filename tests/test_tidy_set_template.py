"""Test luật dọn dải phân cách của MathType Set Template trong mtef._tidy.

Template tập hợp của MathType có HAI dải phân cách quanh phần điều kiện. Khi số
slot bị lệch (RC2), chúng rò ra thành ký tự ``|`` thường::

    \\{|x \\in \\mathbb{R}|\\}          <- cả hai dải rò
    \\{k\\pi |k \\in \\mathbb{Z} |\\}    <- dải đóng rò

Điều kiện phân biệt sống còn là **khoảng trắng phía trước**:

    "\\mathbb{Z} |\\}"   dải phân cách rò ra   -> BỎ
    "|x|\\}"            giá trị tuyệt đối     -> GIỮ

Không có điều kiện đó, luật sẽ ăn mất dấu giá trị tuyệt đối — một lỗi *im lặng*
vì ``|x` vẫn render được, chỉ là sai nghĩa.
"""

import re

import pytest

from pipeline import mtef


# (đầu vào, chuỗi KHÔNG được còn trong kết quả)
LEAK_CASES = [
    r"S=\{k2\pi ;\pi +k2\pi |k\in \mathbb{Z} |\}",
    r"X=\{x\in \mathbb{R}|2x^{2} -5x+3=0 |\}",
    r"D=\mathbb{R} \setminus \{k\pi |k\in \mathbb{Z} |\}",
]


@pytest.mark.parametrize("src", LEAK_CASES)
def test_closing_divider_removed(src):
    """Chỉ dải ĐÓNG (| ngay trước \\}) phải mất.

    Thanh set-builder MỞ (``\\{k\\pi |k\\in ...``) là hợp lệ và vẫn còn — đổi nó
    sang ``\\mid`` là việc trình bày, không thuộc luật này.
    """
    out = mtef._tidy(src)
    assert re.search(r"\|\s*\\?\}", out) is None, f"dải đóng còn sót: {out!r}"


@pytest.mark.parametrize("src", LEAK_CASES)
def test_set_closer_preserved(src):
    r"""Không được ăn mất ``\}`` đóng tập hợp khi dọn dải phân cách."""
    out = mtef._tidy(src)
    assert out.rstrip().endswith(r"\}"), f"mất dấu đóng tập hợp: {out!r}"


@pytest.mark.parametrize("src", [
    r"D=\mathbb{R} \setminus \{k\pi |k\in \mathbb{Z}\}",
    r"\mathbb{R} \setminus \{k \pi \mid k \in \mathbb{Z}}",
    r"\{k\pi \mid k \in \mathbb{Z}\}",
])
def test_mathbb_group_not_escaped(src):
    r"""``\mathbb{Z}\}`` không được biến thành ``\mathbb{Z\}}`` (render ra "Z}").

    Đây là hai bug che nhau: luật escape ngoặc cuối biến ``\mathbb{Z}`` thành
    ``\mathbb{Z\}``, còn luật dọn ngoặc mồ côi lại xoá ``\}`` hợp lệ. Sửa một
    cái sẽ làm lộ cái kia, nên phải khoá cả hai bằng test.
    """
    out = mtef._tidy(src)
    assert r"\mathbb{Z\}" not in out, out
    assert r"\mathbb{Z}" in out, out
    assert out.rstrip().endswith(r"\}"), out


# Dấu giá trị tuyệt đối TUYỆT ĐỐI không được mất
ABS_CASES = [
    r"\{x : |x| < 1\}",
    r"\frac{|x|}{2}",
    r"|x|",
    r"\{ |x| \}",
    r"|x-1|+|x+1|=4",
    r"\left| x \right|",
    r"A=\{x\in \mathbb{N} |x<20\}",   # set-builder hợp lệ, | không có space trước
]


@pytest.mark.parametrize("src", ABS_CASES)
def test_absolute_value_bars_preserved(src):
    out = mtef._tidy(src)
    assert out.count("|") == src.count("|"), (
        f"mất dấu |: {src!r} -> {out!r}"
    )


def test_opening_divider_removed():
    """Dải MỞ: \\{|x ... -> \\{x ..."""
    out = mtef._tidy(r"D=\{|x \in \mathbb{R}|\}")
    assert r"\{|" not in out, out


@pytest.mark.parametrize("src", LEAK_CASES + ABS_CASES)
def test_idempotent(src):
    once = mtef._tidy(src)
    assert mtef._tidy(once) == once, f"không idempotent: {src!r}"
