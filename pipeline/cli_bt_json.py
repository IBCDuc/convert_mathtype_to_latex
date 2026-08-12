"""CLI riêng cho pipeline BÀI TẬP -> JSON: python3 -m pipeline.cli_bt_json <file.docx> [-o out-bt-json]

Mỗi câu hỏi tương ứng 1 file .json theo chuẩn baitap_ref.
"""
from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

from . import mathrender
from .exercises import convert_json


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--out", default="out-bt-json")
    ap.add_argument("--structured", action="store_true", help="Ghi file câu hỏi vào thư mục con theo cấu trúc SGK/Bài học")
    ap.add_argument("--fail-on-katex-error", action="store_true",
                    help="Exit code 1 nếu còn công thức KaTeX không render được (dùng cho CI)")
    ap.add_argument("--katex-report", type=Path,
                    help="Ghi danh sách công thức lỗi KaTeX ra file JSON")
    a = ap.parse_args()

    mathrender.clear_cache()   # reset bộ đếm lỗi KaTeX cho lần chạy này

    files: list[Path] = []
    base_dir: Path | None = None
    for i in a.inputs:
        p = Path(i)
        if p.is_dir():
            base_dir = p
            files.extend(sorted(p.rglob("*.docx")))
        else:
            files.append(p)
    files = [f for f in files
             if not f.name.startswith("~$") and not f.name.startswith("._")]

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    is_structured = a.structured or "structured" in out.name
    rc = 0
    total_questions = 0

    for f in files:
        try:
            questions, debug = convert_json(f)
        except Exception as e:                       # noqa: BLE001
            print(f"[ERROR] {f.name}: {type(e).__name__}: {e}", file=sys.stderr)
            rc = 1
            continue

        matched_base = None
        for i in a.inputs:
            p_in = Path(i)
            if p_in.is_dir() and f.is_relative_to(p_in):
                matched_base = p_in
                break

        if is_structured and matched_base:
            rel = f.relative_to(matched_base)
            parts = []
            for part in rel.parent.parts:
                p_clean = part.strip()
                if p_clean in ("__MACOSX",) or p_clean.startswith("."):
                    continue
                if "đã sửa" in p_clean or "Kiến thức trọng tâm" in p_clean:
                    continue
                if not parts or parts[-1].lower() != p_clean.lower():
                    parts.append(p_clean)
            target_dir = out.joinpath(*parts, f.stem)
        else:
            target_dir = out

        target_dir.mkdir(parents=True, exist_ok=True)
        slug = f.stem.lower().replace(" ", "-")
        for q in questions:
            order = q["order"]
            images = q.pop("_images", {})
            for img_rel_path, img_data in images.items():
                img_file = target_dir / img_rel_path
                img_file.parent.mkdir(parents=True, exist_ok=True)
                img_file.write_bytes(img_data)

            dst = target_dir / (f"q{order:03d}.json" if is_structured else f"{slug}_q{order:03d}.json")
            dst.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")

        total_questions += len(questions)
        print(f"[OK] {f.name} -> {len(questions)} file JSON câu hỏi")

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

    print(f"\n✅ Hoàn thành! Tổng số {total_questions} file JSON câu hỏi đã tạo trong '{out}'")

    # --- Cổng KaTeX: báo cáo công thức không render được -------------------
    # Trước đây thông tin này bị mất sạch (throwOnError:false), lỗi đỏ đi thẳng
    # ra sản phẩm. Nay nó hiện ra, và tuỳ chọn --fail-on-katex-error làm fail CI.
    seen: set[tuple[str, str]] = set()
    bad: list[dict[str, str]] = []
    for fail in mathrender.failures():
        key = (fail["source"], fail["error"])
        if key not in seen:
            seen.add(key)
            bad.append(fail)

    if bad:
        print(f"\n⚠️  {len(bad)} công thức KaTeX KHÔNG render được:")
        for fail in bad[:10]:
            print(f"    {fail['error'][:90]}")
            print(f"      TEX: {fail['source'][:90]}")
        if len(bad) > 10:
            print(f"    ... và {len(bad) - 10} công thức nữa")
        if a.katex_report:
            a.katex_report.write_text(
                json.dumps(bad, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"    Báo cáo đầy đủ: {a.katex_report}")
        if a.fail_on_katex_error:
            print("\n❌ FAIL — còn lỗi KaTeX (--fail-on-katex-error)")
            rc = 1
    else:
        print("✅ Cổng KaTeX: mọi công thức đều render được")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
