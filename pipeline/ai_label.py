"""AI Cognitive Level Labeler — su dung Gemini proxy de phan loai muc do nhan thuc.

Su dung: python3 -m pipeline.ai_label <folder_or_file.json> [--out <out_dir>] [--inplace]

Muc do nhan thuc theo thang Bloom (Viet Nam):
  - Nhan biet    -> cognitive_level: "knowledge",        cognitive_level_num: 1
  - Thong hieu   -> cognitive_level: "comprehension",    cognitive_level_num: 2
  - Van dung     -> cognitive_level: "application",      cognitive_level_num: 3
  - Van dung cao -> cognitive_level: "application_high", cognitive_level_num: 4
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import argparse
from pathlib import Path
import urllib.request
import urllib.error

# Auto-load .env neu chua set trong env
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.is_file():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# --- Config ---
PROXY_URL = os.getenv("AI_PROXY_URL", "http://107.155.65.2:4321")
API_KEY   = os.getenv("API_KEY_PROXY", "")
MODEL     = os.getenv("AI_MODEL", "gemini-2.5-flash")
MAX_RETRY = 3
RETRY_DELAY = 2  # giay

# --- Mapping ket qua AI -> schema ---
LABEL_MAP = {
    "nhan_biet":    ("knowledge",        1),
    "thong_hieu":   ("comprehension",    2),
    "van_dung":     ("application",      3),
    "van_dung_cao": ("application_high", 4),
}

# --- System prompt ---
SYSTEM_PROMPT = (
    "You are a Vietnamese education expert. Classify the cognitive level of a question."
    " Reply with ONLY one of these exact labels (no explanation):\n"
    "nhan_biet | thong_hieu | van_dung | van_dung_cao\n\n"
    "nhan_biet: recall/memorize knowledge (list, define, name, recognize)\n"
    "thong_hieu: explain/compare/interpret knowledge (explain why, compare, describe)\n"
    "van_dung: apply formula/rule to solve a specific problem (calculate, solve equation)\n"
    "van_dung_cao: analyze/synthesize/evaluate/create (prove, design, multi-step complex reasoning)"
)


# --- API call ---
def _call_api(prompt_text: str) -> str | None:
    payload = json.dumps({
        "model": MODEL,
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "prompt": prompt_text,
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 128,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{PROXY_URL}/api/generate",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
        },
        method="POST",
    )

    for attempt in range(MAX_RETRY):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("text", "").strip().lower()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            print(f"    [HTTP {e.code}] {body[:120]}", file=sys.stderr)
            if e.code == 429:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return None
        except Exception as exc:
            print(f"    [ERROR] {exc}", file=sys.stderr)
            if attempt < MAX_RETRY - 1:
                time.sleep(RETRY_DELAY)
            else:
                return None

    return None


# --- Strip HTML ---
def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()[:800]


# --- Build prompt ---
def _build_prompt(q: dict) -> str:
    content_txt = _strip_html(q.get("content") or "")
    choices_txt = ""
    if q.get("choices"):
        parts = []
        for c in q["choices"]:
            letter = chr(64 + c["id"])   # A, B, C, D
            c_text = _strip_html(c.get("content") or "")
            parts.append(f"{letter}. {c_text}")
        choices_txt = "\n".join(parts)

    prompt = f"Cau hoi:\n{content_txt}"
    if choices_txt:
        prompt += f"\n\nLua chon:\n{choices_txt}"
    prompt += "\n\nPhan loai muc do nhan thuc:"
    return prompt


# --- Parse label ---
def _parse_label(raw: str | None) -> tuple[str | None, int | None]:
    if not raw:
        return None, None
    # Normalize: lowercase, trim
    s = raw.strip().lower()
    # Priority: van_dung_cao before van_dung (to avoid substring match)
    if "van_dung_cao" in s or "van dung cao" in s or s in ("van_dung_cao", "application_high"):
        return LABEL_MAP["van_dung_cao"]
    if "van_dung" in s or "van dung" in s or s in ("van_dung", "van", "application"):
        return LABEL_MAP["van_dung"]
    if "thong_hieu" in s or "thong hieu" in s or s in ("thong_hieu", "thong", "comprehension"):
        return LABEL_MAP["thong_hieu"]
    if "nhan_biet" in s or "nhan biet" in s or s in ("nhan_biet", "nhan", "knowledge"):
        return LABEL_MAP["nhan_biet"]
    return None, None


# --- Label 1 file ---
def label_file(src: Path, dst: Path) -> bool:
    try:
        with open(src, encoding="utf-8") as f:
            q = json.load(f)
    except Exception as e:
        print(f"  [SKIP] doc loi: {e}", file=sys.stderr)
        return False

    prompt = _build_prompt(q)
    raw_label = _call_api(prompt)
    cog_level, cog_num = _parse_label(raw_label)

    print(f"  -> AI: '{raw_label}' -> {cog_level} ({cog_num})")

    if cog_level is None:
        print(f"  [WARN] Khong parse duoc nhan tu '{raw_label}', giu nguyen.", file=sys.stderr)
        cog_level = q.get("cognitive_level")
        cog_num   = q.get("cognitive_level_num")

    q["cognitive_level"]     = cog_level
    q["cognitive_level_num"] = cog_num

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


# --- CLI ---
def main() -> int:
    ap = argparse.ArgumentParser(description="Gan nhan muc do nhan thuc bang AI")
    ap.add_argument("inputs", nargs="+", help="File .json hoac thu muc chua .json")
    ap.add_argument("--out",     default="", help="Thu muc dau ra (mac dinh: out-bt-json-labeled)")
    ap.add_argument("--inplace", action="store_true", help="Ghi de truc tiep len file goc")
    ap.add_argument("--limit",   type=int, default=0, help="Gioi han so cau hoi (0=tat ca)")
    a = ap.parse_args()

    if not API_KEY:
        print("[ERROR] Chua set API_KEY_PROXY trong .env!", file=sys.stderr)
        return 1

    files: list[Path] = []
    for i in a.inputs:
        p = Path(i)
        if p.is_dir():
            files.extend(sorted(p.rglob("*.json")))
        elif p.is_file():
            files.append(p)
        else:
            print(f"[WARN] Khong tim thay: {i}", file=sys.stderr)

    if a.limit > 0:
        files = files[:a.limit]

    print(f"Total: {len(files)} questions to label")
    print(f"Model: {MODEL} | Proxy: {PROXY_URL}\n")

    out_dir = Path(a.out) if a.out else None
    ok = 0
    for idx, src in enumerate(files, 1):
        print(f"[{idx:4d}/{len(files)}] {src.name}")

        if out_dir:
            dst = out_dir / src.name
        elif a.inplace:
            dst = src
        else:
            # Default: mirror structure into out-bt-json-labeled
            try:
                base = next(p for p in src.parents if p.name == "out-bt-json-html")
                rel = src.relative_to(base)
                dst = base.parent / "out-bt-json-labeled" / rel
            except (StopIteration, ValueError):
                dst = Path("out-bt-json-labeled") / src.name

        success = label_file(src, dst)
        if success:
            ok += 1

        time.sleep(0.5)  # tranh rate limit

    print(f"\nDone! {ok}/{len(files)} questions labeled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
