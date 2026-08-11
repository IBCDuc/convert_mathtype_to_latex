"""CLI riêng cho pipeline BÀI TẬP: python3 -m pipeline.cli_bt <file.docx> [-o out-bt]

Output là HTML (1 file .html / docx, mỗi câu hỏi là 1 <section>), không còn
JSON array. Tách khỏi cli.py (lý thuyết) vì logic tách câu hỏi khác hẳn.
"""
from __future__ import annotations

import sys
import argparse
from pathlib import Path

from .exercises import convert


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--out", default="out-bt")
    a = ap.parse_args()

    files: list[Path] = []
    for i in a.inputs:
        p = Path(i)
        files.extend(sorted(p.rglob("*.docx")) if p.is_dir() else [p])
    files = [f for f in files
             if not f.name.startswith("~$") and not f.name.startswith("._")]

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rc = 0
    for f in files:
        try:
            html, debug = convert(f)
        except Exception as e:                       # noqa: BLE001
            print(f"[ERROR] {f.name}: {type(e).__name__}: {e}", file=sys.stderr)
            rc = 1
            continue
        slug = f.stem.lower().replace(" ", "-")
        dst = out / f"{slug}.html"
        dst.write_text(html, encoding="utf-8")
        print(f"[OK] {f.name} -> {dst.name}: {len(debug)} câu "
              f"({dst.stat().st_size / 1024:.0f} KB)")
        for d in debug:
            flags = []
            if not d["answer"] and d["n_choices"]:
                flags.append("CHƯA XÁC ĐỊNH ĐÁP ÁN")
            if d.get("inferred_A"):
                flags.append("ĐÃ SUY LUẬN OPTION A (docx thiếu nhãn 'A.')")
            tail = "  <-- " + "; ".join(flags) if flags else ""
            ans_str = str(d['answer']) if d['answer'] is not None else '?'
            print(f"    Câu {d['order']:3}: đáp_án={ans_str:10}  "
                  f"nguồn={d['answer_source']:24} n_lựa_chọn={d['n_choices']}{tail}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
