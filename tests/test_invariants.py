"""Test cho các bất biến trong tools/check_invariants.py.

VÌ SAO PHẢI TEST CHÍNH BỘ ĐO
----------------------------
Bản đầu của ``stray_pipe`` đếm MỌI dấu ``|``, nên nó báo 50 ca trong khi phần lớn
là ``A=\\{x \\in \\mathbb{N} |x<20\\}`` — ký hiệu set-builder HỢP LỆ. Một bộ đo
sai còn tệ hơn không đo: nó tạo ra việc phải làm không tồn tại, và che mất việc
thật (``\\overline{}``, 23 ca).

Nên mỗi bất biến có test dương (phải bắt) và test âm (không được bắt).
"""

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tools.check_invariants import (  # noqa: E402
    INVARIANTS,
    MUST_BE_ZERO,
    brace_imbalance,
    empty_macro_arg,
    pua_chars,
    right_dot_brace,
    spaced_digits,
    spaced_function_name,
    stray_pipe,
    viet_outside_text,
)

# (hàm, các ca PHẢI bắt, các ca KHÔNG được bắt)
CASES = [
    (
        viet_outside_text,
        [r"Cho tập hợp A", r"x \in S và x \in T", r"\frac{độ}{2}"],
        [
            r"\text{Cho tập hợp} A",
            r"x^2 + 3x = 0",
            r"\text{sđ}(Ou, Ov)",
            r"y_{\text{CĐ}}",
            r"\mathrm{Độ}",
        ],
    ),
    (
        spaced_function_name,
        [r"c o s \alpha", r"1 + t a n^2 \alpha", r"s i n x"],
        [r"\cos \alpha", r"\sin x + \tan y", r"a b c", r"cos x"],
    ),
    (
        spaced_digits,
        [r"\frac{3 0 \pi}{1 8 0}", r"1 8 0"],
        [r"180", r"\frac{30\pi}{180}", r"1 8", r"x_1 x_2 x_3"],
    ),
    (
        stray_pipe,
        [r"\{|x \in \mathbb{R}|\}", r"A=\{|x<3\}", r"B=\{x<3|\}"],
        [
            r"A=\{x\in \mathbb{N} |x<20\}",   # set-builder HỢP LỆ
            r"\{x \in \mathbb{R} \mid x > 0\}",
            r"|x|",
            r"\left| x \right|",
        ],
    ),
    (
        right_dot_brace,
        [r"\left\{ x \right.}", r"\right. }"],
        [r"\left\{ x \right.", r"\left( a \right)", r"\right.\\"],
    ),
    (
        empty_macro_arg,
        [r"\overline{}", r"\sqrt{}", r"\frac{}", r"\sqrt[2]{}", r"\underline{}"],
        [r"\overline{AB}", r"\sqrt{2}", r"\frac{1}{2}", r"\sqrt[3]{8}"],
    ),
    (
        brace_imbalance,
        [r"x^{2", r"x^{2}}", r"\frac{1{2}"],
        [r"x^{2}", r"\frac{1}{2}", r"\{x\}", r"\{a \mid b\}"],
    ),
    (
        pua_chars,
        ["x \ue001 y", "\uf8ff"],
        [r"x \ne y", "≠", r"\mathbb{R}"],
    ),
]


@pytest.mark.parametrize(
    "fn,src",
    [(fn, s) for fn, pos, _ in CASES for s in pos],
    ids=lambda v: v if isinstance(v, str) else getattr(v, "__name__", ""),
)
def test_invariant_catches(fn, src):
    assert fn(src) is True, f"{fn.__name__} KHÔNG bắt được: {src!r}"


@pytest.mark.parametrize(
    "fn,src",
    [(fn, s) for fn, _, neg in CASES for s in neg],
    ids=lambda v: v if isinstance(v, str) else getattr(v, "__name__", ""),
)
def test_invariant_no_false_positive(fn, src):
    assert fn(src) is False, f"{fn.__name__} BÁO SAI (dương tính giả): {src!r}"


def test_all_invariants_have_tests():
    """Thêm bất biến mới thì phải thêm test — nếu không test này fail."""
    tested = {fn.__name__ for fn, _, _ in CASES}
    declared = set(INVARIANTS)
    missing = declared - tested - {"spurious_pipe_style"}
    assert not missing, f"bất biến chưa có test: {sorted(missing)}"


def test_must_be_zero_are_declared():
    assert MUST_BE_ZERO <= set(INVARIANTS)


def test_baseline_file_is_valid():
    """Baseline đã commit phải đọc được và khớp tên bất biến hiện tại."""
    import json

    p = pathlib.Path(__file__).parent / "invariants_baseline.json"
    if not p.exists():
        pytest.skip("chưa chốt baseline")
    data = json.loads(p.read_text(encoding="utf-8"))
    unknown = set(data.get("counts", {})) - set(INVARIANTS)
    assert not unknown, f"baseline có bất biến không còn tồn tại: {sorted(unknown)}"
