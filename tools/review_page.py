#!/usr/bin/env python3
"""Dựng 1 trang HTML để SOÁT BẰNG MẮT các công thức pipeline đã tự đoán.

BỐI CẢNH
--------
Khi không có ai sửa được file Word gốc, mọi công thức hỏng buộc phải do pipeline
đoán. Đoán đúng hay sai thì đều **hiển thị sạch sẽ**, nên không thể phát hiện
bằng cách đọc output. Cách khả thi duy nhất cho một người là **nhìn**: đặt bản
trong Word cạnh bản trên web, render cả hai, rồi lướt.

Trang này xếp theo RỦI RO GIẢM DẦN, nên soát từ trên xuống và dừng khi thấy phần
còn lại đã hiển nhiên đúng:

  1. still_broken   — số mũ vẫn nuốt biểu thức, ĐANG hiện sai trên web
  2. katex_error    — không render được
  3. ambiguous      — pipeline đoán, nhưng cấu trúc còn đáng ngờ
  4. canonical      — dạng đa thức chuẩn ``ax^{n} + bx + c = 0``, gần như chắc đúng

DÙNG
----
    python tools/review_page.py "Kiến thức trọng tâm và tài tập" -o SOAT_CONG_THUC.html
    # rồi mở file đó bằng trình duyệt (mở TỪ THƯ MỤC DỰ ÁN để lấy được CSS KaTeX)
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

ROOT = pathlib.Path(__file__).resolve().parent.parent
RENDER_JS = ROOT / "pipeline" / "katex_render.js"

# Dạng đa thức chuẩn sau khi sửa: hệ số + biến ^{chữ số} rồi các hạng tử +/- và một dấu =
_CANONICAL = re.compile(r"\^\{\d\}\s*[-+]")
_REL = re.compile(r"=|<|>|\\le|\\ge|\\ne|\\Leftrightarrow|\\to")
_STILL_SWALLOWED = re.compile(r"\^\s*\{[^{}]*[=<>][^{}]*\}")
_FUNC_MULTI = re.compile(r"\\(?:sin|cos|tan|cot)\s*\^\s*\{\s*\d\d")


def classify(rec: dict) -> tuple[int, str]:
    """(thứ tự ưu tiên, nhãn). Số nhỏ = cần soát trước."""
    tex = rec["latex"]
    if rec.get("katex_error"):
        return 0, "không render được"
    if _STILL_SWALLOWED.search(tex):
        return 1, "VẪN ĐANG HIỆN SAI"
    if _FUNC_MULTI.search(tex):
        return 2, "số mũ hàm 2 chữ số"
    if not rec.get("raw"):
        return 5, "khác"
    # hệ nhiều quan hệ mà không có dấu xuống dòng -> nhiều khả năng mất cấu trúc hệ
    if len(_REL.findall(tex)) >= 2 and r"\\" not in tex and "array" not in tex:
        return 3, "nhiều quan hệ, không có xuống dòng"
    if _CANONICAL.search(tex):
        return 4, "dạng đa thức chuẩn"
    return 3, "cần soát"


def render(latex: list[str]) -> list[str]:
    proc = subprocess.run(
        ["node", str(RENDER_JS)], input=json.dumps(latex),
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if proc.returncode != 0 or not proc.stdout:
        print(f"katex_render.js lỗi: {proc.stderr[:300]}", file=sys.stderr)
        sys.exit(2)
    out = []
    for item in json.loads(proc.stdout):
        h = item.get("html") if isinstance(item, dict) else item
        out.append(h or "")
    return out


CSS = """
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;
     background:#f6f7f9;color:#16191d;line-height:1.5}
header{background:#fff;border-bottom:2px solid #16191d;padding:22px 28px;position:sticky;top:0;z-index:9}
h1{margin:0 0 6px;font-size:20px}
.sub{color:#5a6472;font-size:14px}
.legend{display:flex;gap:14px;flex-wrap:wrap;margin-top:12px;font-size:13px}
.legend b{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:5px;vertical-align:-1px}
main{max-width:1100px;margin:0 auto;padding:22px 28px 90px}
.item{background:#fff;border:1px solid #dde2e9;border-left-width:5px;margin-bottom:14px;padding:14px 16px}
.p0{border-left-color:#a63a2e}.p1{border-left-color:#a63a2e}
.p2{border-left-color:#c9741d}.p3{border-left-color:#c9741d}
.p4{border-left-color:#1f6b5e}.p5{border-left-color:#98a1ad}
.tag{display:inline-block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;
     font-weight:700;padding:2px 7px;border-radius:3px;background:#eef1f5;color:#39424f}
.p0 .tag,.p1 .tag{background:#f7e7e4;color:#a63a2e}
.p2 .tag,.p3 .tag{background:#fbf0e2;color:#8a4f10}
.p4 .tag{background:#e2f0ec;color:#1f6b5e}
.file{font-size:12px;color:#5a6472;margin-left:8px}
.ctx{margin:9px 0;font-size:14px;color:#39424f;font-style:italic}
.row{display:grid;grid-template-columns:110px 1fr;gap:10px;align-items:start;
     padding:8px 0;border-top:1px dashed #e6eaef}
.lbl{font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:#5a6472;padding-top:6px;font-weight:700}
.math{overflow-x:auto;padding:4px 0}
.tex{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11.5px;color:#6b7480;
     word-break:break-all;margin-top:4px}
.katex-error{color:#a63a2e!important}
@media (max-width:640px){.row{grid-template-columns:1fr}}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Trang soát công thức bằng mắt")
    ap.add_argument("root", type=pathlib.Path)
    ap.add_argument("-o", "--out", type=pathlib.Path, default=pathlib.Path("SOAT_CONG_THUC.html"))
    ap.add_argument("--defects", type=pathlib.Path, default=pathlib.Path("report/defects.json"),
                    help="dùng lại kết quả của report_source_defects.py nếu đã có")
    a = ap.parse_args()

    if a.defects.exists():
        recs = json.loads(a.defects.read_text(encoding="utf-8"))
        print(f"Dùng lại {a.defects} ({len(recs)} bản ghi)")
    else:
        print(f"Chưa có {a.defects}. Chạy trước:\n"
              f"  python tools/report_source_defects.py {a.root} -o report/", file=sys.stderr)
        return 2

    # gộp trùng theo (raw, latex)
    seen: set[tuple[str, str]] = set()
    uniq = []
    for r in recs:
        key = (r.get("raw", ""), r["latex"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)

    for r in uniq:
        r["_prio"], r["_label"] = classify(r)
    uniq.sort(key=lambda r: (r["_prio"], r["file"]))

    html_now = render([r["latex"] for r in uniq])
    html_raw = render([r.get("raw") or r["latex"] for r in uniq])

    counts: dict[str, int] = {}
    for r in uniq:
        counts[r["_label"]] = counts.get(r["_label"], 0) + 1

    parts = [
        "<!doctype html><html lang='vi'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>Soát công thức</title>",
        "<link rel='stylesheet' href='node_modules/katex/dist/katex.min.css'>",
        f"<style>{CSS}</style></head><body>",
        "<header><h1>Soát công thức pipeline đã tự đoán</h1>",
        f"<div class='sub'>{len(uniq)} công thức, xếp theo rủi ro giảm dần. "
        "Soát từ trên xuống, dừng khi phần còn lại đã hiển nhiên đúng.</div>",
        "<div class='legend'>",
    ]
    for label, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        parts.append(f"<span>{html.escape(label)}: <b style='background:#ccc'></b>{n}</span>")
    parts.append("</div></header><main>")

    for r, now, raw in zip(uniq, html_now, html_raw):
        ctx = re.sub(r"\s+", " ", r.get("context", ""))[:160]
        parts.append(f"<div class='item p{r['_prio']}'>")
        parts.append(f"<span class='tag'>{html.escape(r['_label'])}</span>"
                     f"<span class='file'>{html.escape(r['file'])}</span>")
        if ctx:
            parts.append(f"<div class='ctx'>“…{html.escape(ctx)}…”</div>")
        if r.get("raw"):
            parts.append("<div class='row'><div class='lbl'>Trong Word</div>"
                         f"<div><div class='math'>{raw}</div>"
                         f"<div class='tex'>{html.escape(r['raw'][:220])}</div></div></div>")
        parts.append("<div class='row'><div class='lbl'>Web đang hiện</div>"
                     f"<div><div class='math'>{now}</div>"
                     f"<div class='tex'>{html.escape(r['latex'][:220])}</div></div></div>")
        if r.get("katex_error"):
            parts.append(f"<div class='row'><div class='lbl'>Lỗi</div>"
                         f"<div style='color:#a63a2e'>{html.escape(r['katex_error'][:160])}</div></div>")
        parts.append("</div>")

    parts.append("</main></body></html>")
    a.out.write_text("\n".join(parts), encoding="utf-8")

    print(f"\n{'nhãn':38s}{'số ca':>7s}")
    for label, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {label:36s}{n:5d}")
    print(f"\nĐã ghi: {a.out}")
    print("Mở bằng trình duyệt TỪ THƯ MỤC DỰ ÁN để lấy được CSS của KaTeX.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
