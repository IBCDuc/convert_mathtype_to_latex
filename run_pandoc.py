#!/usr/bin/env python3
import os
import re
import subprocess
import unicodedata
import zipfile
from pathlib import Path

PANDOC_BIN = Path(__file__).parent / "bin" / "pandoc"
LUA_FILTER = Path(__file__).parent / "crop_theory.lua"

TARGETS = [
    ("Kiến thức trọng tâm và tài tập/Văn 12", "out-pandoc-van12"),
    ("Kiến thức trọng tâm và tài tập/ĐỊA 11", "out-pandoc-dia11"),
    ("Kiến thức trọng tâm và tài tập/GDKTPL 12", "out-pandoc-gdktpl12"),
    ("Kiến thức trọng tâm và tài tập/bai-1-cach-mang-tu-san.docx", "out-pandoc-su12"),
]

def fix_vietnamese_nfd(html_content: str) -> str:
    """Khắc phục lỗi Pandoc tách dấu thanh tiếng Việt (NFD -> NFC & gộp thẻ định dạng bị đứt đoạn)."""
    html_content = re.sub(r"</em>(\s*)<em>", r"\1", html_content)
    html_content = re.sub(r"</strong>(\s*)<strong>", r"\1", html_content)
    # Bỏ dấu gạch đầu dòng trùng lặp trong thẻ <li><p>- ...</p></li> -> <li><p>...</p></li>
    html_content = re.sub(r"(<li>\s*<p>)\s*[\-\+\*\•\–\—]\s*", r"\1", html_content)
    # Loại bỏ thẻ blockquote theo yêu cầu
    html_content = html_content.replace("<blockquote>", "").replace("</blockquote>", "")
    return unicodedata.normalize("NFC", html_content)

def process_item(src_path_str, out_dir_str):
    src_path = Path(src_path_str)
    out_dir = Path(out_dir_str)
    out_dir.mkdir(parents=True, exist_ok=True)

    if src_path.is_dir():
        docx_files = sorted(src_path.rglob("*.docx"))
    else:
        docx_files = [src_path]
    docx_files = [f for f in docx_files if not f.name.startswith("~$") and not f.name.startswith("._")]

    print(f"\n📂 Processing {len(docx_files)} files from '{src_path_str}' -> '{out_dir_str}' using Pandoc 3.6.3...")

    for f in docx_files:
        slug = f.stem.lower().replace(" ", "-")
        out_file = out_dir / f"{slug}.html"
        cmd = [
            str(PANDOC_BIN),
            str(f),
            "--lua-filter", str(LUA_FILTER),
            "-s",
            "-o", str(out_file)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            raw_html = out_file.read_text(encoding="utf-8")
            fixed_html = fix_vietnamese_nfd(raw_html)
            out_file.write_text(fixed_html, encoding="utf-8")

            size_kb = out_file.stat().st_size / 1024
            print(f"  [OK - Pandoc 3.6.3] {f.name} -> {out_file.name} ({size_kb:.1f} KB)")
        else:
            print(f"  [ERROR] {f.name}: {res.stderr.strip()}")

def create_zip():
    zip_name = "output_dia_van_gdktpl_su12.zip"
    output_dirs = ["out-pandoc-van12", "out-pandoc-dia11", "out-pandoc-gdktpl12", "out-pandoc-su12"]
    
    print(f"\n📦 Creating zip archive '{zip_name}'...")
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for d_str in output_dirs:
            d = Path(d_str)
            if d.exists():
                for f in d.glob("*.html"):
                    arcname = f"{d.name}/{f.name}"
                    zipf.write(f, arcname)
                    print(f"  + Added: {arcname}")
    
    zip_path = Path(zip_name)
    print(f"✨ Zip created successfully: {zip_path.name} ({zip_path.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    for src, out in TARGETS:
        process_item(src, out)
    create_zip()
