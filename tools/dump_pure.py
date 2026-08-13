#!/usr/bin/env python3
"""Xuất HTML một câu hỏi bằng CONVERT THUẦN — tắt mọi tầng sửa đổi.

Mục đích: xem parser MTEF một mình đọc ra gì, không có bất kỳ lớp vá nào.

Bị TẮT:
  * mtef._tidy                      (~450 dòng regex chuẩn hoá)
  * mtef.repair_swallowed_exponent  (sửa số mũ nuốt biểu thức)
  * mtef.balance_braces             (cân bằng ngoặc)
  * overrides.json                  (bảng sửa tay theo sha1)
  * mathrender._wrap_bare_words     (bọc \\text, đổi cos -> \\cos, ...)

Chỉ còn: đọc docx -> parser MTEF -> KaTeX.

DÙNG
    python tools/dump_pure.py <file.docx> --block 33 --n 8 -o ra.html
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("docx", type=pathlib.Path)
    ap.add_argument("--block", type=int, required=True, help="chỉ số block bắt đầu")
    ap.add_argument("--n", type=int, default=8, help="số block lấy tiếp")
    ap.add_argument("-o", "--out", type=pathlib.Path, default=pathlib.Path("pure.html"))
    a = ap.parse_args()

    from pipeline import docxast, mathrender, mtef

    # ---- TẮT TOÀN BỘ TẦNG SỬA ĐỔI ----
    mtef._tidy = lambda s: " ".join(s.split()).strip()
    mtef.repair_swallowed_exponent = lambda s: (s, [])
    mtef.balance_braces = lambda s: (s, [])
    mtef._load_overrides = lambda: {}
    mathrender._wrap_bare_words = lambda t: t

    reader = docxast.DocxReader(str(a.docx)).parse()
    blocks = reader.blocks[a.block:a.block + a.n]

    latex: list[str] = []
    rows: list[list[tuple[str, str]]] = []
    for b in blocks:
        parts: list[tuple[str, str]] = []
        for inl in b.inlines:
            if inl.kind == "text" and inl.text.strip():
                parts.append(("text", inl.text))
            elif inl.kind == "formula":
                asset = reader.assets.get(inl.ref or "")
                tex = (asset.latex if asset else None) or ""
                parts.append(("math", tex))
                if tex:
                    latex.append(tex)
        if parts:
            rows.append(parts)

    rendered = mathrender.render_many(latex) if latex else {}

    css = (ROOT / "node_modules" / "katex" / "dist" / "katex.min.css").read_text(encoding="utf-8")
    out = [
        "<!doctype html><html lang='vi'><head><meta charset='utf-8'>",
        "<title>Convert thuần — không qua bất kỳ hàm sửa đổi nào</title>",
        f"<style>{css}</style>",
        "<style>body{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;"
        "padding:28px;line-height:1.7;color:#16191d}"
        "h1{font-size:19px;border-bottom:2px solid #16191d;padding-bottom:10px}"
        ".note{background:#fbf0e2;border-left:4px solid #c9741d;padding:12px 15px;"
        "font-size:14px;margin:16px 0}"
        "p{margin:14px 0}.tex{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;"
        "color:#6b7480;background:#f4f6f8;padding:2px 5px;border-radius:3px;"
        "display:inline-block;margin-left:6px}"
        ".katex-error{color:#a63a2e!important}</style></head><body>",
        "<h1>Convert thuần — Câu 4, Toán 11 Bài 2</h1>",
        "<div class='note'><b>Đã tắt hết:</b> <code>_tidy</code>, "
        "<code>exp_repair</code>, <code>balance_braces</code>, "
        "<code>overrides.json</code>, <code>_wrap_bare_words</code>.<br>"
        "Chỉ còn: đọc docx → parser MTEF → KaTeX.</div>",
    ]
    for parts in rows:
        out.append("<p>")
        for kind, val in parts:
            if kind == "text":
                out.append(html.escape(val))
            else:
                out.append(rendered.get(val, f"<code>{html.escape(val)}</code>"))
                out.append(f"<span class='tex'>{html.escape(val)}</span>")
        out.append("</p>")
    out.append("</body></html>")
    a.out.write_text("\n".join(out), encoding="utf-8")

    print(f"công thức: {len(latex)}")
    for t in latex:
        print("   ", t)
    print(f"\nĐã ghi {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
