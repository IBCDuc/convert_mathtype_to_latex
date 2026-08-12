#!/usr/bin/env python3
"""Cổng 1 — quét output JSON/HTML và FAIL nếu còn công thức KaTeX không render được.

Đây là cổng mà pipeline hiện tại KHÔNG có: pipeline/katex_render.js dùng
throwOnError:false nên KaTeX âm thầm trả HTML lỗi đỏ và pipeline coi là thành
công. Script này dùng throwOnError:true để một công thức sai LÀM FAIL BUILD.

Dùng:
    python tools/check_katex.py out-bt-json-new/            # quét cây thư mục
    python tools/check_katex.py out/ --json report.json     # xuất báo cáo
    python tools/check_katex.py out/ --max-fail 5           # cho phép ngưỡng tạm

Exit code:  0 = sạch, 1 = còn lỗi, 2 = lỗi hạ tầng (thiếu node/katex).

LƯU Ý: không bắt được lỗi "số mũ nuốt biểu thức" (6x^{2-7x+1=0}) vì chuỗi đó
HỢP LỆ về cú pháp — KaTeX render thành công. Lớp lỗi im lặng đó do
tests/test_exp_repair.py phụ trách, không phải cổng này.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

GATE = pathlib.Path(__file__).with_name("katex_gate.js")

# [MATH: ...] trong JSON/text, và nội dung annotation của KaTeX HTML đã render
RE_MATH_TAG = re.compile(r"\[MATH:\s*(.+?)\]", re.DOTALL)
RE_KATEX_ANNO = re.compile(
    r'<annotation encoding="application/x-tex">(.*?)</annotation>', re.DOTALL
)
RE_KATEX_ERROR = re.compile(r'class="[^"]*katex-error', re.I)

HTML_UNESCAPE = [("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"), ("&amp;", "&")]


def _unescape(s: str) -> str:
    for a, b in HTML_UNESCAPE:
        s = s.replace(a, b)
    return s


def collect(root: pathlib.Path) -> tuple[list[str], list[tuple[str, str]], int]:
    """Trả về (danh sách latex, danh sách (file, latex), số thẻ katex-error sẵn có)."""
    items: list[tuple[str, str]] = []
    prerendered_errors = 0
    paths = [root] if root.is_file() else sorted(
        p for p in root.rglob("*") if p.suffix.lower() in (".json", ".html", ".htm", ".txt")
    )
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        prerendered_errors += len(RE_KATEX_ERROR.findall(text))
        for m in RE_MATH_TAG.finditer(text):
            items.append((str(p), m.group(1).strip()))
        for m in RE_KATEX_ANNO.finditer(text):
            items.append((str(p), _unescape(m.group(1)).strip()))
    return [t for _, t in items], items, prerendered_errors


def run_gate(latex: list[str], strict: bool = False) -> list[str | None]:
    if not latex:
        return []
    env = {"KATEX_STRICT": "1"} if strict else {}
    import os

    try:
        proc = subprocess.run(
            ["node", str(GATE)],
            input=json.dumps(latex),
            capture_output=True,
            text=True,
            env={**os.environ, **env},
            cwd=str(GATE.parent.parent),
        )
    except FileNotFoundError:
        print("LỖI: không tìm thấy 'node'. Cần Node.js để chạy cổng KaTeX.", file=sys.stderr)
        sys.exit(2)
    if proc.returncode != 0 or not proc.stdout:
        print(f"LỖI hạ tầng khi chạy katex_gate.js:\n{proc.stderr[:600]}", file=sys.stderr)
        sys.exit(2)
    return json.loads(proc.stdout)


def main() -> int:
    ap = argparse.ArgumentParser(description="Cổng kiểm định KaTeX cho output pipeline")
    ap.add_argument("root", type=pathlib.Path, help="file hoặc thư mục output")
    ap.add_argument("--strict", action="store_true", help="bật strict:'error' (nghiêm hơn)")
    ap.add_argument("--max-fail", type=int, default=0, help="ngưỡng lỗi cho phép (mặc định 0)")
    ap.add_argument("--json", type=pathlib.Path, help="ghi báo cáo JSON")
    ap.add_argument("--show", type=int, default=15, help="số lỗi in ra")
    args = ap.parse_args()

    if not args.root.exists():
        print(f"Không tồn tại: {args.root}", file=sys.stderr)
        return 2

    latex, items, prerendered = collect(args.root)
    if not latex:
        print(f"Không tìm thấy công thức nào trong {args.root}")
        return 0

    errs = run_gate(latex, args.strict)
    fails = [
        {"file": items[i][0], "latex": latex[i], "error": e}
        for i, e in enumerate(errs)
        if e
    ]

    uniq = len(set(latex))
    print(f"Đã quét   : {args.root}")
    print(f"Công thức : {len(latex)}  ({uniq} duy nhất)")
    if prerendered:
        print(f"⚠️  Thẻ katex-error có sẵn trong output: {prerendered}")
    print(f"Lỗi cứng  : {len(fails)}  ({100*len(fails)/len(latex):.2f}%)")

    if fails:
        print(f"\n--- {min(args.show, len(fails))} lỗi đầu ---")
        for f in fails[: args.show]:
            print(f"  {pathlib.Path(f['file']).name}")
            print(f"    {f['error'][:110]}")
            print(f"    TEX: {f['latex'][:110]}")

    if args.json:
        args.json.write_text(
            json.dumps(fails, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"\nBáo cáo: {args.json}")

    total_bad = len(fails) + prerendered
    if total_bad > args.max_fail:
        print(f"\n❌ FAIL — {total_bad} vấn đề (ngưỡng {args.max_fail})")
        return 1
    print("\n✅ ĐẠT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
