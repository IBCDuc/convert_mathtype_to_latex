"""CLI: python3 -m pipeline.cli <file.docx|thư mục> [-o out] [-j jobs]

Output là HTML (1 file .html / bài học), không còn JSON.
Hỗ trợ xử lý đa nhân (Multiprocessing) tận dụng tối đa sức mạnh CPU.
"""
from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from . import mathrender
from .emit import convert


def _process_file(f: Path) -> tuple[Path, str | None, str | None, Exception | None]:
    try:
        mathrender.clear_cache()
        doc_id, html = convert(f)
        return f, doc_id, html, None
    except Exception as e:
        return f, None, None, e


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--out", default="out")
    ap.add_argument("-j", "--jobs", type=int, default=min(32, os.cpu_count() or 4),
                    help="Số luồng CPU chạy song song")
    a = ap.parse_args()

    files: list[Path] = []
    for i in a.inputs:
        p = Path(i)
        files.extend(sorted(p.rglob("*.docx")) if p.is_dir() else [p])
    # "~$" = file tạm của Word; "._" = AppleDouble resource fork của macOS.
    files = [f for f in files
             if not f.name.startswith("~$") and not f.name.startswith("._")]

    if not files:
        print("Không tìm thấy file .docx nào.")
        return 0

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rc = 0
    seen: dict[str, str] = {}   # doc_id -> file đã ghi, chặn ghi đè âm thầm

    print(f"🚀 Bắt đầu chuyển đổi {len(files)} file .docx trên {a.jobs} tiến trình CPU song song...")

    if len(files) == 1 or a.jobs <= 1:
        results = [_process_file(f) for f in files]
    else:
        with ProcessPoolExecutor(max_workers=a.jobs) as executor:
            results = list(executor.map(_process_file, files))

    for f, doc_id, html, exc in results:
        if exc is not None:
            print(f"[ERROR] {f.name}: {type(exc).__name__}: {exc}", file=sys.stderr)
            rc = 1
            continue
        if not doc_id or not html:
            continue
        if doc_id in seen:
            print(f"[COLLISION] {doc_id}: {f.name} trùng doc_id với {seen[doc_id]} "
                  f"-> BỎ QUA, không ghi đè", file=sys.stderr)
            rc = 1
            continue
        seen[doc_id] = f.name
        dst = out / f"{doc_id}.html"
        dst.write_text(html, encoding="utf-8")
        empty = "<body>\n</body>" in html or "<body></body>" in html
        status = "EMPTY" if empty else "OK"
        print(f"[{status:5}] {doc_id:40} -> {dst.name} "
              f"({dst.stat().st_size / 1024:.0f} KB)")
        if empty:
            rc = max(rc, 1)

    print(f"✨ Hoàn tất chuyển đổi {len(seen)} bài học sang HTML!")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
