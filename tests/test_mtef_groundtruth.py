"""Bộ kiểm thử MTEF parser đối chiếu với 892 công thức TeX Ground-Truth trong corpus.

Chạy độc lập: python3 -m tests.test_mtef_groundtruth
"""
from __future__ import annotations

import collections
import io
import re
from pathlib import Path

import olefile

from pipeline import mtef


def normalize_tex(s: str) -> str:
    """Chuẩn hoá chuỗi TeX/LaTeX để so sánh cấu trúc thực tế."""
    if not s:
        return ""
    s = s.replace(r"\left", "").replace(r"\right", "")
    s = s.replace(r"\mathrm", "").replace(r"\text", "")
    s = s.replace(r"\neq", r"\ne").replace("°", r"\circ")
    s = s.replace(r"\rightarrow", r"\to").replace(r"\Rightarrow", r"\to")
    s = s.replace(r"\cdot", ".").replace("~", "")
    s = re.sub(r"\s+", "", s)
    s = s.replace("{", "").replace("}", "")
    return s


def run_groundtruth_test(corpus_dir: Path):
    files = sorted(corpus_dir.rglob("*.docx"))
    files = [f for f in files if not f.name.startswith("~$") and not f.name.startswith("._")]

    total_ole = 0
    tex_groundtruth_count = 0
    exact_matches = 0
    norm_matches = 0
    mismatches = []
    selectors_seen = collections.Counter()
    sources_count = collections.Counter()

    for f in files:
        import zipfile
        try:
            zf = zipfile.ZipFile(f)
        except Exception:
            continue
        
        # Đọc document.xml.rels để tìm các OLE object
        try:
            rels_xml = zf.read("word/_rels/document.xml.rels")
        except KeyError:
            continue

        from lxml import etree
        rels_tree = etree.fromstring(rels_xml)
        rels = {r.get("Id"): r.get("Target") for r in rels_tree}

        for rid, target in rels.items():
            if "embeddings/" not in target and not target.endswith(".bin"):
                continue
            name = "word/" + target.lstrip("/") if not target.startswith("word/") else target
            try:
                blob = zf.read(name)
            except KeyError:
                continue

            if not olefile.isOleFile(io.BytesIO(blob)):
                continue
            try:
                ole = olefile.OleFileIO(io.BytesIO(blob))
                if not ole.exists("Equation Native"):
                    continue
                data = ole.openstream("Equation Native").read()
            except Exception:
                continue

            total_ole += 1

            # Kiểm tra xem có TeX Ground Truth không
            if mtef.TEX_MARK in data:
                tex_groundtruth_count += 1
                tail = data.split(mtef.TEX_MARK, 1)[1]
                gt_tex = tail.split(b"\x00", 1)[0].decode("latin1", "ignore").strip()

                # Ép MTEF Parser đi đường MTEF Binary (bỏ qua TeX check)
                body = data[28:] if len(data) > 28 else b""
                p = mtef.MTEFParser(body)
                mtef_latex = None
                try:
                    if p.read_header() is not None:
                        p.skip_preamble()
                        parts = []
                        while p.i < len(body) and any(b for b in body[p.i:]):
                            before = p.i
                            parts.append(p.parse_slot())
                            if p.i == before:
                                break
                        mtef_latex = mtef._tidy("".join(parts))
                        for sel in p.used_sel:
                            selectors_seen[sel] += 1
                except Exception:
                    pass

                if mtef_latex is None:
                    misfit = True
                    mtef_latex = "<ERROR/UNRESOLVED>"
                else:
                    misfit = False

                gt_norm = normalize_tex(gt_tex)
                mtef_norm = normalize_tex(mtef_latex)

                if mtef_latex == gt_tex:
                    exact_matches += 1
                if gt_norm == mtef_norm and gt_norm != "":
                    norm_matches += 1
                else:
                    if len(mismatches) < 30:
                        mismatches.append((f.name, gt_tex, mtef_latex, list(p.used_sel) if 'p' in locals() else []))

            # Đo thống kê source bình thường
            latex, src = mtef.decode_stream(data)
            sources_count[src] += 1

    print("=" * 70)
    print("📊 BÁO CÁO KIỂM THỬ MTEF PARSER TRÊN CORPUS GROUND-TRUTH")
    print("=" * 70)
    print(f"Tổng số công thức OLE tìm thấy: {total_ole}")
    print(f"Số công thức có TeX Ground-Truth: {tex_groundtruth_count}")
    if tex_groundtruth_count > 0:
        print(f"Khớp tuyệt đối (Exact Match): {exact_matches} ({exact_matches / tex_groundtruth_count * 100:.1f}%)")
        print(f"Khớp sau chuẩn hoá (Norm Match): {norm_matches} ({norm_matches / tex_groundtruth_count * 100:.1f}%)")
    print(f"Số selector khác nhau parser nhận ra: {len(selectors_seen)} loại -> {dict(selectors_seen)}")
    print(f"Phân bố nguồn decode: {dict(sources_count)}")

    if mismatches:
        print("\n--- 30 MẪU LỆCH TIÊU BIỂU (Ground-Truth vs MTEF Generated) ---")
        for idx, (fname, gt, gen, sels) in enumerate(mismatches, 1):
            print(f"[{idx:02d}] File: {fname} | Selectors: {sels}")
            print(f"     GT  : {gt}")
            print(f"     MTEF: {gen}")
            print("-" * 50)


def main():
    workspace = Path(__file__).parent.parent
    corpus = workspace / "Kiến thức trọng tâm và tài tập"
    if not corpus.exists():
        corpus = workspace
    run_groundtruth_test(corpus)


if __name__ == "__main__":
    main()
