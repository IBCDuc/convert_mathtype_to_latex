#!/usr/bin/env python3
"""Cổng bất biến — bắt LỖI IM LẶNG mà cổng KaTeX không thể thấy.

VÌ SAO CẦN CỔNG THỨ HAI
-----------------------
tools/check_katex.py chỉ bắt lỗi CÚ PHÁP. Sau khi cú pháp đã sạch (99,85%), toàn
bộ lỗi còn lại đều **im lặng** — KaTeX render thành công nhưng ra công thức sai:

    c o s \\alpha      -> tích các biến italic c·o·s, không phải hàm cos
    1 8 0              -> ba chữ số rời, không phải số 180
    Cho tập hợp A      -> chữ tiếng Việt thành chuỗi biến nghiêng
    \\{|x \\in R|\\}     -> dấu | rò từ dải phân cách slot MTEF

Không có lỗi đỏ nào để bắt. Không kiểm tra bằng mắt nào bắt hết được. Nên cách
duy nhất là **bất biến có số đếm, chốt theo kiểu ratchet**: số ca không được phép
tăng so với baseline đã commit.

Bất biến chạy trên chuỗi LaTeX ĐI VÀO KaTeX, thu qua mathrender.render_many, nên
bao trùm CẢ HAI đường: công thức MTEF (docxast kind="formula") và toán suy ra từ
Text Run (exercises._format_inline_text).

DÙNG
----
    python tools/check_invariants.py "Kiến thức trọng tâm và tài tập" --baseline tests/invariants_baseline.json
    python tools/check_invariants.py <dir> --update-baseline     # chốt baseline mới
    python tools/check_invariants.py <dir> --show viet_outside_text --limit 20

Exit code: 0 = không xấu hơn baseline, 1 = có bất biến tăng số ca.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

VIET = re.compile(
    r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]",
    re.I,
)
_TEXT_GROUP = re.compile(r"\\(?:text|mathrm|operatorname|textrm|mbox)\s*\{[^{}]*\}")
_FUNCS = ("sin", "cos", "tan", "cot", "log", "ln", "lim", "max", "min", "exp")


def _strip_text_groups(tex: str) -> str:
    """Bỏ nội dung \\text{...} — chữ tiếng Việt trong đó là HỢP LỆ."""
    prev = None
    while prev != tex:
        prev = tex
        tex = _TEXT_GROUP.sub(" ", tex)
    return tex


# --- các bất biến ----------------------------------------------------------
# Mỗi hàm trả True nếu công thức VI PHẠM bất biến.

def viet_outside_text(tex: str) -> bool:
    """RC4 — chữ tiếng Việt ngoài \\text{} sẽ render thành biến nghiêng sai."""
    return VIET.search(_strip_text_groups(tex)) is not None


def spaced_function_name(tex: str) -> bool:
    """RC1 — tên hàm bị tách bởi space-join CHAR record: 'c o s'."""
    for f in _FUNCS:
        if re.search(r"(?<![a-zA-Z\\])" + r"\s+".join(f) + r"(?![a-zA-Z])", tex):
            return True
    return False


def spaced_digits(tex: str) -> bool:
    """RC1 — chữ số bị tách: '1 8 0' vốn là 180."""
    return re.search(r"(?<![\d.])\d\s+\d\s+\d(?!\d)", tex) is not None


def stray_pipe(tex: str) -> bool:
    r"""RC2 — dấu | RÒ RA từ dải phân cách slot template MTEF.

    Chỉ tính dấu | dính ngay ngoặc tập hợp: ``\{|x ...`` hoặc ``... x|\}``.

    KHÔNG tính ``A=\{x \in \mathbb{N} |x<20\}`` — dấu | ở giữa là ký hiệu
    set-builder HỢP LỆ, KaTeX render bình thường (chỉ nên đổi sang \mid cho
    giãn cách đẹp hơn, đó là vấn đề trình bày chứ không phải lỗi).
    """
    return re.search(r"\\\{\s*\||\|\s*\\\}", tex) is not None


def spurious_pipe_style(tex: str) -> bool:
    r"""Trình bày — nên dùng ``\mid`` thay ``|`` trong set-builder (không phải lỗi)."""
    return re.search(r"\\in[^|]{0,24}\|", tex) is not None


# ĐÃ BỎ: right_dot_brace.
#
# Bất biến này từng báo 38 ca và bị tôi xếp ưu tiên 1. Kiểm chứng bằng KaTeX cho
# thấy nó là DƯƠNG TÍNH GIẢ HOÀN TOÀN — cả 5 biến thể đều render ĐẠT:
#
#     {...\right.}     ĐẠT      {...\right. }   ĐẠT      \left\{...\right.   ĐẠT
#     {...\right..\}}  ĐẠT      {...\right.\}}  ĐẠT
#
# Các công thức bị gắn cờ đều dạng `{ \left\{ ... \right. }` — một group bọc ngoài
# chứa cặp \left...\right hoàn chỉnh, tức LaTeX hợp lệ.
#
# Kéo theo: chú thích trong _tidy ghi "KaTeX requires delimiter space before group
# brace" dựa trên TIỀN ĐỀ SAI. KaTeX không đòi khoảng trắng đó.


def empty_macro_arg(tex: str) -> bool:
    """\\sqrt / \\frac với đối số rỗng — luôn là hỏng."""
    return re.search(r"\\(?:sqrt|frac|overline|underline)(?:\[[^\]]*\])?\{\}", tex) is not None


def escaped_brace_in_macro(tex: str) -> bool:
    r"""``\mathbb{Z\}}`` — dấu ``\}`` lọt vào trong đối số macro, render ra "Z}".

    Sinh ra khi luật escape ngoặc cuối biến ``\mathbb{Z}`` thành ``\mathbb{Z\}``
    rồi bộ cân bằng thêm ``}`` để bù. Đo được 6 ca; nay phải luôn bằng 0.
    """
    return re.search(r"\\(?:mathbb|mathrm|text|mathcal|operatorname)\{[^{}]*\\\}", tex) is not None


def brace_imbalance(tex: str) -> bool:
    """Ngoặc nhóm lệch — phải LUÔN bằng 0 sau latex_balance."""
    from pipeline.latex_balance import brace_defects

    d = brace_defects(tex)
    return d["orphan_close"] != 0 or d["unclosed_open"] != 0


def pua_chars(tex: str) -> bool:
    """Ký tự Private Use Area còn sót từ MTEF."""
    return re.search(r"[\uE000-\uF8FF]", tex) is not None


INVARIANTS = {
    "viet_outside_text": viet_outside_text,
    "spaced_function_name": spaced_function_name,
    "spaced_digits": spaced_digits,
    "stray_pipe": stray_pipe,
    "spurious_pipe_style": spurious_pipe_style,
    "empty_macro_arg": empty_macro_arg,
    "escaped_brace_in_macro": escaped_brace_in_macro,
    "brace_imbalance": brace_imbalance,
    "pua_chars": pua_chars,
}

# Bất biến PHẢI bằng 0 — tăng dù chỉ 1 ca cũng là fail, không cần baseline.
MUST_BE_ZERO = {"brace_imbalance", "pua_chars", "escaped_brace_in_macro"}


def collect_latex(root: pathlib.Path) -> tuple[list[str], int, list[str]]:
    """Chạy pipeline thật, thu ĐÚNG chuỗi mà KaTeX nhận (cả 2 đường).

    QUAN TRỌNG: phải áp `_wrap_bare_words` như `render_many` làm bên trong. Nếu
    chỉ bắt `latex_list` ở đầu vào thì ta đo chuỗi TRƯỚC tầng chuẩn hoá cuối, và
    sẽ báo sai — ví dụ 'và' bị tính là tiếng Việt trong math mode dù ngay sau đó
    nó đã được bọc thành `\\text{ và }`.
    """
    from pipeline import exercises, mathrender

    seen: list[str] = []
    original = mathrender.render_many

    def spy(latex_list):
        seen.extend(mathrender._wrap_bare_words(s) for s in latex_list)
        return original(latex_list)

    mathrender.render_many = spy
    try:
        files = (
            [root]
            if root.is_file()
            else sorted(
                f
                for f in root.rglob("*.docx")
                if not f.name.startswith(("~$", "._"))
            )
        )
        errors: list[str] = []
        for f in files:
            try:
                exercises.convert_json(f)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{f.name}: {type(e).__name__}: {e}")
        return seen, len(files), errors
    finally:
        mathrender.render_many = original


def main() -> int:
    ap = argparse.ArgumentParser(description="Cổng bất biến cho lỗi im lặng")
    ap.add_argument("root", type=pathlib.Path)
    ap.add_argument("--baseline", type=pathlib.Path,
                    default=pathlib.Path(__file__).parent.parent / "tests" / "invariants_baseline.json")
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--show", help="in các ca vi phạm của một bất biến")
    ap.add_argument("--limit", type=int, default=10)
    a = ap.parse_args()

    if not a.root.exists():
        print(f"Không tồn tại: {a.root}", file=sys.stderr)
        return 2

    latex, n_files, errors = collect_latex(a.root)
    uniq = sorted(set(latex))
    if errors:
        print(f"⚠️  {len(errors)} file lỗi khi xử lý:")
        for e in errors[:5]:
            print(f"    {e}")

    counts: dict[str, int] = {}
    samples: dict[str, list[str]] = {}
    for name, fn in INVARIANTS.items():
        hits = [t for t in uniq if fn(t)]
        counts[name] = len(hits)
        samples[name] = hits

    print(f"\nfile .docx        : {n_files}")
    print(f"công thức duy nhất: {len(uniq)}  (tổng lượt {len(latex)})")

    if a.show:
        if a.show not in INVARIANTS:
            print(f"Bất biến không tồn tại: {a.show}. Có: {', '.join(INVARIANTS)}", file=sys.stderr)
            return 2
        print(f"\n--- {a.show}: {counts[a.show]} ca ---")
        for t in samples[a.show][: a.limit]:
            print(f"   {t[:120]}")
        return 0

    base = {}
    if a.baseline.exists() and not a.update_baseline:
        base = json.loads(a.baseline.read_text(encoding="utf-8")).get("counts", {})

    print(f"\n{'bất biến':22s}{'ca':>7s}{'baseline':>10s}{'':>4s}")
    worse: list[str] = []
    for name in INVARIANTS:
        now = counts[name]
        was = base.get(name)
        limit = 0 if name in MUST_BE_ZERO else was
        if limit is not None and now > limit:
            mark, flag = "✗ TĂNG", True
        elif was is not None and now < was:
            mark, flag = "↓ tốt hơn", False
        else:
            mark, flag = "ok", False
        if flag:
            worse.append(f"{name}: {was if was is not None else 0} -> {now}")
        shown = "-" if was is None else str(was)
        print(f"  {name:22s}{now:5d}{shown:>10s}   {mark}")

    if a.update_baseline:
        a.baseline.parent.mkdir(parents=True, exist_ok=True)
        a.baseline.write_text(
            json.dumps({"corpus": str(a.root), "n_files": n_files,
                        "n_unique_formulas": len(uniq), "counts": counts},
                       ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"\n✅ Đã chốt baseline: {a.baseline}")
        return 0

    if worse:
        print("\n❌ FAIL — bất biến xấu đi:")
        for w in worse:
            print(f"    {w}")
        print("\nXem chi tiết:  python tools/check_invariants.py <dir> --show <tên_bất_biến>")
        return 1

    print("\n✅ ĐẠT — không bất biến nào xấu hơn baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
