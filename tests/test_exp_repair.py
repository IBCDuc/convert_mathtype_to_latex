"""Test cho pipeline.exp_repair — sửa lỗi số mũ nuốt biểu thức.

Bộ test này có hai nửa, và nửa thứ hai QUAN TRỌNG HƠN:

  MUST_REPAIR      — các ca giáo viên quên bấm -> thoát ô số mũ.
  MUST_NOT_TOUCH   — các số mũ HỢP LỆ. Phá một trong số này là lỗi nghiêm trọng
                     hơn nhiều so với việc sót một ca ở MUST_REPAIR, vì công
                     thức sai vẫn render bình thường (lỗi im lặng).

Chạy:  python -m pytest tests/test_exp_repair.py -v
"""

import pytest

from pipeline.exp_repair import repair_swallowed_exponent as repair

# --------------------------------------------------------------------------
# Phải sửa: số mũ đã nuốt phần còn lại của biểu thức
# --------------------------------------------------------------------------
MUST_REPAIR = [
    # (đầu vào,                        chuỗi phải xuất hiện trong kết quả)
    (r"6x^{2-7x+1=0}",                 "^{2}"),
    (r"2x^{2-5x+3=0}",                 "^{2}"),
    (r"x^{2-3x-4}",                    "^{2}"),   # không có '=', bắt bằng biến lặp
    (r"x^{2+2bx+c=0}",                 "^{2}"),
    (r"x^{2+2an.x+bn-mc}",             "^{2}"),
    (r"t^{2-5t+6=0}",                  "^{2}"),
    (r"y=x^{3-3x^{2}+2}",              "^{3}"),
    (r"\sin^{2\alpha+\cos^2\alpha=1}", "^{2}"),
    (r"2x^{2+y<-3}",                   "^{2}"),
]

# --------------------------------------------------------------------------
# TUYỆT ĐỐI không được động tới: số mũ hợp lệ
# --------------------------------------------------------------------------
MUST_NOT_TOUCH = [
    # luỹ thừa ký hiệu thông thường
    r"x^{n-1}", r"a^{m-n}", r"2^{n+1}", r"x^{2n}", r"x^{2}", r"x^{-1}",
    r"e^{-x}", r"e^{x+y}", r"e^{2x}", r"10^{-3}", r"a^{i+j}", r"2^{k-1}",
    r"x^{\frac{1}{2}}", r"C^{k}_{n}",
    # ĐẠO HÀM — atom cơ sở là x, không phải n. Nếu lấy cả tiền tố sẽ PHÁ.
    r"nx^{n-1}", r"n x^{n-1}", r"k a^{k-1}", r"(x^n)'=nx^{n-1}",
    # cấp số nhân
    r"u_1 q^{n-1}", r"q^{n-1}",
    # nhị thức
    r"(a+b)^{n-k}", r"\frac{x^{n+1}}{n+1}", r"a^{n-1}+a^{n-2}",
    # phương trình mũ: dấu '=' nằm NGOÀI ô số mũ
    r"2^{x-1}=8", r"3^{x+1}=9", r"e^{x-1}>0",
    # số mũ đã đúng, phần còn lại nằm ngoài
    r"x^{2}+3x+2=0", r"6x^{2}-7x+1=0",
    # tổng/tích
    r"\sum_{i=1}^{n} x_i", r"\prod_{k=1}^{n} a_k",
]


@pytest.mark.parametrize("src,expect", MUST_REPAIR)
def test_must_repair(src, expect):
    got, notes = repair(src)
    assert got != src, f"SÓT: không sửa {src!r}"
    assert expect in got, f"số mũ sai: {src!r} -> {got!r}, mong đợi {expect!r}"
    assert any(n.startswith("repaired:") for n in notes), notes


@pytest.mark.parametrize("src", MUST_NOT_TOUCH)
def test_must_not_touch(src):
    got, _ = repair(src)
    assert got == src, f"PHÁ SỐ MŨ HỢP LỆ: {src!r} -> {got!r}"


@pytest.mark.parametrize("src", [s for s, _ in MUST_REPAIR] + MUST_NOT_TOUCH)
def test_idempotent(src):
    """f(f(x)) == f(x) — chạy lại pipeline phải hội tụ."""
    once, _ = repair(src)
    twice, _ = repair(once)
    assert twice == once, f"KHÔNG idempotent: {src!r}\n  1: {once!r}\n  2: {twice!r}"


@pytest.mark.parametrize("src", [
    r"", r"x", r"x^", r"x^{", r"x^{}", r"^{2}", r"\frac{1}{2}",
    r"x^{{2}-3x}", r"\{x^{2}\}", r"x^{a^{b^{c}}}",
])
def test_no_crash_on_edge_cases(src):
    """Không được ném exception với đầu vào méo/rỗng."""
    got, _ = repair(src)
    assert isinstance(got, str)


def test_nested_braces_respected():
    """Ngoặc lồng: '-' bên trong \\frac KHÔNG phải điểm cắt cấp ngoài."""
    src = r"x^{\frac{a-b}{c}}"
    got, _ = repair(src)
    assert got == src, got


def test_escaped_braces_not_counted_as_depth():
    r"""``\{`` và ``\}`` không được tính là ngoặc nhóm."""
    src = r"A=\{x \in \mathbb{R} \mid (2x-x^{2})(2x^{2-3x-2})=0\}"
    got, notes = repair(src)
    assert "^{2} -3x-2" in got, got
    assert r"\mid" in got and got.endswith(r"\}"), "phá cấu trúc tập hợp"
