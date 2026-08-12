"""Test cho pipeline.latex_balance — cân bằng ngoặc bằng ngăn xếp.

Test quan trọng nhất ở đây là ``test_never_breaks_frac``: nó khoá lại đúng cái
bug mà cách cũ (đếm tổng rồi cắt đuôi) gây ra — xoá dấu ``}`` của ``\\frac``.
"""

import pytest

from pipeline.latex_balance import balance_braces, brace_defects


def _balanced(s: str) -> bool:
    d = brace_defects(s)
    return d["orphan_close"] == 0 and d["unclosed_open"] == 0


# ---------------------------------------------------------------------------
# } mồ côi phải bị bỏ ĐÚNG CHỖ, không được cắt dấu khác
# ---------------------------------------------------------------------------
ORPHAN_CASES = [
    (r"-495^{\circ}=-\frac{13\pi }{4}}",        r"-495^{\circ}=-\frac{13\pi }{4}"),
    (r"132^{\circ}=\frac{12\pi }{15}}",         r"132^{\circ}=\frac{12\pi }{15}"),
    (r"30^{\circ}=\frac{\pi }{6}}",             r"30^{\circ}=\frac{\pi }{6}"),
    (r"x^{2}}",                                 r"x^{2}"),
    (r"a}b",                                    r"ab"),
    (r"}x",                                     r"x"),
]


@pytest.mark.parametrize("src,want", ORPHAN_CASES)
def test_drops_orphan_close(src, want):
    got, notes = balance_braces(src)
    assert got == want, f"{src!r} -> {got!r}, mong đợi {want!r}"
    assert any(n.startswith("dropped_orphan_close") for n in notes)


# ---------------------------------------------------------------------------
# { còn hở phải được đóng
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("src,want", [
    (r"\frac{1", r"\frac{1}"),
    (r"x^{2", r"x^{2}"),
    (r"\sqrt{a+b", r"\sqrt{a+b}"),
])
def test_closes_unclosed_open(src, want):
    got, _ = balance_braces(src)
    assert got == want


# ---------------------------------------------------------------------------
# HỒI QUY: KHÔNG BAO GIỜ được phá \frac — đây là bug của cách làm cũ
# ---------------------------------------------------------------------------
FRAC_CASES = [
    r"\frac{1}{\cos^2 \alpha}",
    r"\frac{1}{c o s}",
    r"\begin{array}{l}1 + \tan^2 \alpha = \frac{1}{\cos^2 \alpha}\end{array}",
    r"\frac{a}{b} + \frac{c}{d}",
    r"\frac{\frac{1}{2}}{3}",
]


@pytest.mark.parametrize("src", FRAC_CASES)
def test_never_breaks_frac(src):
    got, notes = balance_braces(src)
    assert got == src, f"PHÁ \\frac: {src!r} -> {got!r}  {notes}"
    assert notes == []


# ---------------------------------------------------------------------------
# \{ \} là ngoặc LITERAL, không phải ngoặc nhóm
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("src", [
    r"\{x \in \mathbb{R} \mid x > 0\}",
    r"A=\{1;2;3\}",
    r"\left\{ \begin{aligned} & x=1 \\ \end{aligned} \right.",
])
def test_escaped_braces_are_literal(src):
    got, notes = balance_braces(src)
    assert got == src, f"{src!r} -> {got!r}  {notes}"


def test_escaped_brace_not_counted():
    """``\\{`` không mở group, nên ``\\{a}`` có một ``}`` mồ côi."""
    got, notes = balance_braces(r"\{a}")
    assert got == r"\{a"
    assert any("orphan" in n for n in notes)


# ---------------------------------------------------------------------------
# Bất biến chung
# ---------------------------------------------------------------------------
ALL = [s for s, _ in ORPHAN_CASES] + FRAC_CASES + [
    r"", r"{", r"}", r"{}", r"}{", r"\\", r"\{", r"\}",
    r"\frac{1{2}", r"x^{a^{b^{c}}}", r"{{{}}}",
]


@pytest.mark.parametrize("src", ALL)
def test_output_always_balanced(src):
    got, _ = balance_braces(src)
    assert _balanced(got), f"kết quả vẫn lệch: {src!r} -> {got!r}"


@pytest.mark.parametrize("src", ALL)
def test_idempotent(src):
    once, _ = balance_braces(src)
    twice, notes = balance_braces(once)
    assert twice == once, f"không idempotent: {src!r}"
    assert notes == [], f"lần 2 vẫn phải sửa: {notes}"


@pytest.mark.parametrize("src", ALL)
def test_preserves_non_brace_chars(src):
    """Chỉ được thêm/bớt ngoặc nhóm, không được đụng ký tự khác."""
    got, _ = balance_braces(src)
    strip = lambda s: s.replace("{", "").replace("}", "")
    assert strip(got) == strip(src), f"{src!r} -> {got!r}"
