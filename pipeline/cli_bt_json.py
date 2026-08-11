"""CLI riêng cho pipeline BÀI TẬP -> JSON: python3 -m pipeline.cli_bt_json <file.docx> [-o out-bt-json]

Mỗi câu hỏi tương ứng 1 file .json theo chuẩn baitap_ref.
"""
from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

from .exercises import convert_json


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--out", default="out-bt-json")
    ap.add_argument("--structured", action="store_true", help="Ghi file câu hỏi vào thư mục con theo cấu trúc SGK/Bài học")
    a = ap.parse_args()

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
            rel = f.relative_to(matched_base.parent if matched_base.parent != matched_base else matched_base)
            target_dir = out / rel.parent / f.stem
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
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
