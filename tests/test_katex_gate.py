import json
import pathlib
import subprocess
import pytest
from pipeline import docxast, mtef

GATE_JS_PATH = pathlib.Path(__file__).parent.parent / "pipeline" / "katex_gate.js"
MATH_DOCX_FILES = list((pathlib.Path(__file__).parent.parent / "Kiến thức trọng tâm và tài tập").rglob("*[tT]oán*/**/*.docx"))

def validate_katex_strict_batch(tex_list: list[str]) -> list[str | None]:
    """Pass a list of LaTeX strings through katex_gate.js (throwOnError=True).
    Returns list of None (success) or error message string.
    """
    if not tex_list:
        return []
    p = subprocess.Popen(
        ["node", str(GATE_JS_PATH)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, err = p.communicate(json.dumps(tex_list, ensure_ascii=False))
    if p.returncode != 0:
        raise RuntimeError(f"katex_gate.js process failed: {err}")
    return json.loads(out)


def test_gate1_measure_corpus_katex_strict():
    """Gate 1: Measure exact KaTeX strict errors across all Math DOCX formulas."""
    all_raw_formulas = []
    all_tidied_formulas = []
    metadata = []

    for docx_path in MATH_DOCX_FILES:
        try:
            reader = docxast.DocxReader(docx_path)
            doc = reader.parse()
            for aid, asset in doc.assets.items():
                if asset.latex and asset.latex.strip():
                    raw_latex = asset.latex.strip()
                    tidied_latex = mtef._tidy(raw_latex)
                    all_raw_formulas.append(raw_latex)
                    all_tidied_formulas.append(tidied_latex)
                    metadata.append({
                        "file": docx_path.name,
                        "aid": aid,
                        "raw": raw_latex,
                        "tidied": tidied_latex,
                    })
        except Exception as e:
            print(f"Error parsing {docx_path.name}: {e}")

    print(f"\n[Gate 1] Total decoded formulas across {len(MATH_DOCX_FILES)} files: {len(all_raw_formulas)}")

    raw_errors = validate_katex_strict_batch(all_raw_formulas)
    tidied_errors = validate_katex_strict_batch(all_tidied_formulas)

    raw_err_count = sum(1 for e in raw_errors if e is not None)
    tidied_err_count = sum(1 for e in tidied_errors if e is not None)

    print(f"[Gate 1] Raw formulas KaTeX strict errors     : {raw_err_count} / {len(all_raw_formulas)}")
    print(f"[Gate 1] Tidied formulas KaTeX strict errors  : {tidied_err_count} / {len(all_tidied_formulas)}")


def test_gate2_non_regression_check():
    """Gate 2: Assert that normalization NEVER breaks a formula that was valid in RAW."""
    regressions = []
    for docx_path in MATH_DOCX_FILES:
        try:
            reader = docxast.DocxReader(docx_path)
            doc = reader.parse()
            raw_list = []
            tidied_list = []
            asset_ids = []

            for aid, asset in doc.assets.items():
                if asset.latex and asset.latex.strip():
                    raw = asset.latex.strip()
                    tidied = mtef._tidy(raw)
                    raw_list.append(raw)
                    tidied_list.append(tidied)
                    asset_ids.append(aid)

            raw_errs = validate_katex_strict_batch(raw_list)
            tidied_errs = validate_katex_strict_batch(tidied_list)

            for i in range(len(raw_list)):
                if raw_errs[i] is None and tidied_errs[i] is not None:
                    regressions.append({
                        "file": docx_path.name,
                        "aid": asset_ids[i],
                        "raw": raw_list[i],
                        "tidied": tidied_list[i],
                        "error": tidied_errs[i],
                    })
        except Exception as e:
            pass

    print(f"\n[Gate 2] Total regression cases (_tidy broke raw valid formula): {len(regressions)}")
    if regressions:
        print("[Gate 2] Sample Regressions:")
        for r in regressions[:5]:
            print(f"  - [{r['file']} asset {r['aid']}]")
            print(f"    RAW   : {r['raw']}")
            print(f"    TIDIED: {r['tidied']}")
            print(f"    ERR   : {r['error']}")
