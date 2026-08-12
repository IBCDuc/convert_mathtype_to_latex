#!/usr/bin/env python3
"""Xuất báo cáo công thức hỏng NGAY TRONG FILE WORD, để đội nội dung sửa tại nguồn.

VÌ SAO CẦN
----------
Phần lớn lỗi còn lại không phải lỗi decode — chúng hỏng sẵn trong file `.docx`.
Ví dụ điển hình: giáo viên gõ ``6x``, bấm Ctrl+H vào ô số mũ, gõ ``2``, rồi quên
bấm ``→`` để thoát, nên gõ tiếp ``-7x+1=0`` ngay trong ô số mũ. Mở file bằng
MathType cũng thấy sai.

Sửa tại nguồn là **chính xác**. Heuristic ở pipeline mãi mãi chỉ là **phỏng đoán**
— xem pipeline/exp_repair.py. Nên với các ca không suy diễn được đáng tin, việc
đúng là trả về cho người soạn, không phải viết thêm luật.

BÁO CÁO GỒM
-----------
* ``defects.md``       — cho người: nhóm theo file, kèm ngữ cảnh đoạn văn
* ``defects.json``     — cho tooling
* ``overrides.skel.json`` — khung sẵn để dán vào pipeline/overrides.json cho các
  ca KaTeX lỗi cứng (đã điền sha1 + latex hiện tại, chỉ cần sửa `latex`)

DÙNG
----
    python tools/report_source_defects.py "Kiến thức trọng tâm và tài tập" -o report/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

GATE = pathlib.Path(__file__).with_name("katex_gate.js")


def _katex_errors(latex: list[str]) -> list[str | None]:
    if not latex:
        return []
    proc = subprocess.run(
        ["node", str(GATE)], input=json.dumps(latex),
        capture_output=True, text=True, cwd=str(GATE.parent.parent),
    )
    if proc.returncode != 0 or not proc.stdout:
        print(f"katex_gate.js lỗi: {proc.stderr[:300]}", file=sys.stderr)
        sys.exit(2)
    return json.loads(proc.stdout)


def _scan_file(path: pathlib.Path) -> list[dict]:
    """Trả về [{sha1, latex, context, para}] theo đúng thứ tự trong tài liệu."""
    from pipeline import docxast, mtef

    # Chặn decode_ole để lấy sha1 của blob — Asset.data chỉ chứa ảnh preview,
    # không phải OLE blob, nên không lấy được sha1 từ asset.
    sha_of: dict[str, str] = {}
    original = mtef.decode_ole

    def spy(blob: bytes):
        latex, source = original(blob)
        if latex:
            sha_of.setdefault(latex, hashlib.sha1(blob).hexdigest())
        return latex, source

    mtef.decode_ole = spy
    try:
        reader = docxast.DocxReader(str(path)).parse()
    finally:
        mtef.decode_ole = original

    out: list[dict] = []
    for block in reader.blocks:
        if block.kind != "para":
            continue
        context = block.text
        for inline in block.inlines:
            if inline.kind != "formula":
                continue
            asset = reader.assets.get(inline.ref or "")
            if asset is None or not asset.latex:
                continue
            out.append({
                # Rỗng khi công thức đến từ OMML (Equation Editor mới) chứ không
                # phải MTEF OLE — khi đó không có blob nào để băm, và cơ chế
                # override theo sha1 KHÔNG áp dụng được.
                "sha1": sha_of.get(asset.latex, ""),
                "source": asset.source,
                "latex": asset.latex,
                "context": context,
                "para": block.para_index,
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Báo cáo công thức hỏng trong file Word")
    ap.add_argument("root", type=pathlib.Path)
    ap.add_argument("-o", "--out", type=pathlib.Path, default=pathlib.Path("report"))
    a = ap.parse_args()

    if not a.root.exists():
        print(f"Không tồn tại: {a.root}", file=sys.stderr)
        return 2

    from tools.check_invariants import INVARIANTS

    files = (
        [a.root] if a.root.is_file()
        else sorted(f for f in a.root.rglob("*.docx")
                    if not f.name.startswith(("~$", "._")))
    )

    records: list[dict] = []
    for f in files:
        try:
            items = _scan_file(f)
        except Exception as e:  # noqa: BLE001
            print(f"[BỎ QUA] {f.name}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        for it in items:
            it["file"] = str(f.relative_to(a.root) if f != a.root else f.name)
            records.append(it)

    errs = _katex_errors([r["latex"] for r in records])
    for rec, err in zip(records, errs):
        defects = [name for name, fn in INVARIANTS.items()
                   if name != "spurious_pipe_style" and fn(rec["latex"])]
        rec["katex_error"] = err
        rec["defects"] = defects
        # Số mũ nuốt biểu thức: dấu hiệu là quan hệ nằm trong ô số mũ
        if re.search(r"\^\s*\{[^{}]*[=<>][^{}]*\}", rec["latex"]):
            rec["defects"].append("swallowed_exponent")

    bad = [r for r in records if r["katex_error"] or r["defects"]]
    a.out.mkdir(parents=True, exist_ok=True)

    (a.out / "defects.json").write_text(
        json.dumps(bad, ensure_ascii=False, indent=1), encoding="utf-8")

    # --- báo cáo cho người ---
    by_file: dict[str, list[dict]] = {}
    for r in bad:
        by_file.setdefault(r["file"], []).append(r)

    lines = [
        "# Công thức cần sửa trong file Word",
        "",
        f"Quét **{len(files)}** file `.docx`, **{len(records)}** công thức MathType.",
        f"Cần sửa: **{len(bad)}** công thức trong **{len(by_file)}** file.",
        "",
        "Các công thức dưới đây hỏng **ngay trong file Word** — mở bằng MathType cũng thấy sai.",
        "Sửa tại nguồn là chính xác; pipeline chỉ có thể phỏng đoán.",
        "",
        "> **Lưu ý cách đọc.** Báo cáo này đo LaTeX ngay sau khi đọc file, **trước** tầng",
        "> chuẩn hoá cuối (`mathrender._wrap_bare_words`) và trước `overrides.json`. Vì vậy",
        "> một số ca ghi \"không hiển thị được\" ở đây **vẫn hiển thị đúng trên web** nhờ các",
        "> tầng đó. Con số chính thức của sản phẩm là output của",
        "> `python -m pipeline.cli_bt_json ... --fail-on-katex-error`.",
        ">",
        "> Mục đích của báo cáo là chỉ ra chỗ **dữ liệu nguồn sai**, để sửa dứt điểm trong",
        "> file Word thay vì để pipeline phỏng đoán mãi.",
        "",
        "## Nguyên nhân thường gặp nhất",
        "",
        "Khi gõ số mũ bằng `Ctrl+H`, phải bấm **mũi tên phải (→)** để thoát khỏi ô số mũ",
        "trước khi gõ tiếp. Nếu quên, cả phần còn lại của phương trình bị đưa vào ô số mũ:",
        "",
        "| Gõ | Kết quả |",
        "|---|---|",
        "| `6x` `Ctrl+H` `2` `→` `-7x+1=0` | 6x² − 7x + 1 = 0  ✅ |",
        "| `6x` `Ctrl+H` `2` `-7x+1=0` | 6x^(2−7x+1=0)  ❌ |",
        "",
    ]
    for fname in sorted(by_file):
        items = by_file[fname]
        lines += [f"## {fname}", "", f"{len(items)} công thức:", ""]
        for r in items:
            ctx = re.sub(r"\s+", " ", r["context"])[:150]
            lines.append(f"- **Đoạn:** …{ctx}…" if ctx else "- **Đoạn:** _(không có chữ)_")
            lines.append(f"  - Công thức đọc được: `{r['latex'][:180]}`")
            if r["katex_error"]:
                lines.append(f"  - ❌ Không hiển thị được: {r['katex_error'][:120]}")
            if r["defects"]:
                lines.append(f"  - Dấu hiệu: {', '.join(sorted(set(r['defects'])))}")
            if r["sha1"]:
                lines.append(f"  - `sha1={r['sha1'][:12]}` (nguồn: {r['source']})")
            else:
                lines.append(
                    f"  - nguồn: **{r['source']}** — không phải MathType OLE,"
                    " nên không override được theo sha1; phải sửa trong file Word"
                )
            lines.append("")
    (a.out / "defects.md").write_text("\n".join(lines), encoding="utf-8")

    # --- khung overrides cho các ca KaTeX lỗi cứng ---
    skel = {
        "_comment": "Khung sinh tự động. Sửa trường 'latex' cho đúng rồi dán vào pipeline/overrides.json.",
    }
    for r in bad:
        if r["katex_error"] and r["sha1"]:
            skel[r["sha1"]] = {
                "latex": r["latex"],
                "note": f"{r['file']} — {r['katex_error'][:80]}",
                "_context": re.sub(r"\s+", " ", r["context"])[:120],
            }
    (a.out / "overrides.skel.json").write_text(
        json.dumps(skel, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"file quét            : {len(files)}")
    print(f"công thức MathType   : {len(records)}")
    print(f"cần sửa tại nguồn    : {len(bad)}  (trong {len(by_file)} file)")
    print(f"  - KaTeX lỗi cứng   : {sum(1 for r in bad if r['katex_error'])}")
    print(f"  - số mũ nuốt bt    : {sum(1 for r in bad if 'swallowed_exponent' in r['defects'])}")
    print(f"\nĐã ghi: {a.out}/defects.md, defects.json, overrides.skel.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
