# DOCX → JSON Pipeline (Lý thuyết / Kiến thức trọng tâm) → UniLearn

> Bản kế hoạch v1.0 — mục tiêu: chốt **schema JSON output chuẩn** + **kiến trúc pipeline** trước khi code.
> Phạm vi v1: **chỉ trích xuất phần Lý thuyết / Kiến thức trọng tâm**. Phần Bài tập để v2 (schema đã chừa chỗ).

---

## 1. Khảo sát thực tế corpus (số liệu đo được, không phải phỏng đoán)

**46 file .docx / 8 môn.** Lưu ý: **không có Văn 10**, chỉ có Văn 12. Tương tự chỉ có Toán 10/11/12, Hóa 10/12, Địa 11, GDKTPL 12.

| Nhóm | Files | Ảnh (media) | OLE MathType | Đặc điểm |
|---|---|---|---|---|
| Văn 12, Địa 11, GDKTPL 12 | 18 | **0** | 0 | Text thuần → tier dễ |
| Hóa 12 | 10 | 154 | 18 | Ảnh PNG thật (sơ đồ, CTCT) |
| Hóa 10 | 3 | 193 | 178 | Trộn: WMF công thức + ảnh |
| Toán 10/11/12 | 11 | **4.432** | 4.601 | 95%+ là WMF công thức |
| **Tổng** | **46** | **4.779 (16.6 MB)** | **4.797** | |

### 1.1. Phát hiện quan trọng #1 — "Ảnh" phần lớn KHÔNG phải hình minh hoạ

Ví dụ `Toán 10 / BÀI 2 Tập hợp`: **382 `<w:object>` với `ProgID="Equation.DSMT4"`** (MathType) so với chỉ **15 `<w:drawing>`** là hình thật (biểu đồ Ven, trục số).

Hệ quả: nếu base64 tất cả ảnh như nhau, JSON gửi UniLearn sẽ là **rừng WMF blob** — không search được, không render được trên web (WMF là format Windows metafile, browser không đọc), và phồng dung lượng vô ích.
→ **Bắt buộc phân loại `formula` vs `figure` ngay từ đầu.** Đây là quyết định kiến trúc số 1.

Bằng chứng text bị mất khi bỏ qua formula (trích thẳng từ python-docx):

```
"Nếu mọi phần tử của tập hợp  đều là phần tử của tập hợp  thì ta nói  là một tập con của ..."
                             ^A                              ^B              ^A
```
Các ký hiệu A, B, ⊂ nằm trong OLE → text trần **vô nghĩa**. Không xử lý formula = output rác.

### 1.2. Phát hiện quan trọng #2 — MathType không tự giải mã được

- OLE binary chứa **MTEF (MathType Equation Format) nhị phân**, chuỗi ASCII duy nhất đọc được là `MathType 6.0 Equation / DSMT6` — **không có LaTeX bên trong**.
- **Đã test LibreOffice** (`--convert-to docx` và `--convert-to odt`): giữ nguyên 382 OLE, **không** chuyển sang OMML/StarMath. Đường LibreOffice → pandoc **thất bại**.
- Chỉ một số ít công thức đã là OMML native (`<m:oMath>`, 3–7 cái/file) — cái này pandoc xử lý ngon.

→ Chiến lược formula phải tự build (mục 4.3).

### 1.3. Phát hiện quan trọng #3 — Không thể dựa vào Heading style

| File | Heading styles |
|---|---|
| Toán 10 Bài 2 | **0** |
| Toán 12 (cả 4 bài) | **0** |
| Địa 11 (cả 7 bài) | **0** |
| Văn 12 | 5–7 |
| Hóa 10 Bài 1 | 16 (nhưng dùng lộn xộn) |

Đa số file dùng `Normal` + **bold** thủ công. → Segmentation phải dựa **marker text + regex + bold**, không dựa `style.name`.

### 1.4. Biến thể marker thực tế (đã gom đủ từ 46 file)

**Mở đầu lý thuyết** (7 biến thể):
`A – LÝ THUYẾT (KIẾN THỨC TRỌNG TÂM)` · `A. KIẾN THỨC TRỌNG TÂM` · `A: KIẾN THỨC TRỌNG TÂM` · `a. kiến thức trọng tâm` (thường) · `A. TÓM TẮT LÝ THUYẾT` · `A. PHẦN LÍ THUYẾT` · `Kiến thức trọng tâm` (không tiền tố)

**Kết thúc lý thuyết** (8 biến thể):
`B – BÀI TẬP` · `B. BÀI TẬP` · `B. Bài tập` · `B. Phần bài tập` · `B. PHẦN BÀI TẬP` · `Bài tập` · `B. BÀI TẬP VẬN DỤNG SAU BÀI HỌC` · `b. BÀI TẬP`

**Cạm bẫy đã phát hiện:**
- `Hóa 12 – bài 9 amino acid`: trong **thân lý thuyết** có mục `A. AMINO ACID` và **`B. PEPTIDE`** → regex `^B\.` sẽ **cắt nhầm giữa bài**. Phải match cả cụm từ khoá `BÀI TẬP`, không chỉ chữ cái.
- `Toán 11 – Bài 4`: có **hai** header lý thuyết lồng nhau (`A – LÝ THUYẾT` rồi `A. TÓM TẮT KIẾN THỨC CƠ BẢN CẦN NẮM`).
- `Hóa 12 – BÀI 4`: cũng có 2 (`A. PHẦN LÍ THUYẾT` + `A. TÓM TẮT LÝ THUYẾT`).
- Sai chính tả có hệ thống: `Lever 1` / `Lever I` thay vì `Level` (Hóa 12).

### 1.5. Phát hiện quan trọng #4 — Có file lý thuyết RỖNG

`Hóa 10 / Bài 1. Thành phần của nguyên tử`: giữa `A. KIẾN THỨC TRỌNG TÂM` và `B. Bài tập` chỉ có **2 paragraph ảnh + 1 ký tự `❖`**, còn lại là paragraph trống. Một trong 2 ảnh là **ảnh stock hồng cầu** (trang trí, không phải nội dung).

→ Pipeline **bắt buộc** có QA gate chặn file kiểu này, không được im lặng đẩy JSON rỗng sang UniLearn.

---

## 2. Nguyên tắc thiết kế schema

1. **1 file .docx = 1 document JSON** (1 bài học). Không gộp.
2. **Cây đệ quy có level đầy đủ** — `sections[].children[]`, mỗi node có `level`, `numbering`, `path` (`"1.2.a"`) để UniLearn render mục lục / deep-link mà không phải parse lại.
3. **Tách bạch nội dung và trình bày.** Mỗi block có `text` (plain, để search/index) và `html` (để render). Không nhét markup vào `text`.
4. **Formula là công dân hạng nhất**, không phải ảnh. Node `formula` có `latex` + `image_fallback` + `confidence`.
5. **Ảnh dedupe qua asset registry.** Base64 lưu **một lần** ở `assets`, block chỉ tham chiếu `asset_id`. Có chế độ `inline` để bung base64 trực tiếp khi bàn giao.
6. **Lossless provenance.** Mọi node giữ `src` (index paragraph gốc) → truy vết ngược về docx khi có khiếu nại nội dung.
7. **Deterministic ID.** `doc_id` = slug(subject-grade-lesson); `node_id` ổn định giữa các lần chạy → UniLearn upsert idempotent, không tạo bản ghi trùng.

---

## 3. JSON Schema output (đề xuất chốt)

### 3.1. Envelope

```jsonc
{
  "schema_version": "1.0.0",
  "doc_id": "toan-10-ket-noi-tri-thuc-bai-02",
  "content_hash": "sha256:9f2c…",          // hash của phần content, để UniLearn skip nếu không đổi

  "meta": {
    "subject":       { "code": "MATH", "name": "Toán" },
    "grade":         10,
    "book":          { "name": "Kết nối tri thức với cuộc sống", "code": "KNTT", "confidence": "default" },
    "curriculum":    "GDPT-2018",
    "lesson": {
      "number": 2,
      "code":   "BAI_02",
      "title":  "Tập hợp và các phép toán trên tập hợp",
      "chapter": { "number": 1, "title": "Mệnh đề và tập hợp" }   // null nếu docx không nêu
    },
    "part": "THEORY",                       // THEORY | EXERCISE  (v1 luôn = THEORY)
    "language": "vi"
  },

  "source": {
    "file_name": "BÀI 2 Tập hợp và các phép toán trên tập hợp.docx",
    "file_sha256": "…",
    "relative_path": "Toán 10/Toán 10/BÀI 2 …docx",
    "paragraph_range": [1, 47],
    "extracted_at": "2026-08-03T10:00:00+07:00",
    "pipeline_version": "1.0.0"
  },

  "stats": {
    "sections": 3, "blocks": 41, "words": 812,
    "formulas": { "total": 388, "resolved_latex": 371, "fallback_image": 17 },
    "figures": 15, "tables": 9
  },

  "quality": {
    "status": "PASS",                       // PASS | WARN | FAIL
    "score": 0.94,
    "flags": ["FORMULA_LOW_CONFIDENCE:4"]   // xem mục 5.2
  },

  "sections": [ /* §3.2 */ ],
  "assets":   { /* §3.4 */ }
}
```

### 3.2. Section node (đệ quy — "level đầy đủ")

```jsonc
{
  "node_id":   "s1-2-a",
  "level":     3,                    // 1 = A/I ; 2 = 1./I. ; 3 = a./b. ; 4 = bullet
  "order":     7,                    // thứ tự tuyệt đối trong document
  "path":      "1.2.a",
  "numbering": "a.",                 // ký hiệu gốc trong docx, giữ nguyên
  "title":     "Giao của hai tập hợp",
  "title_html":"Giao của hai tập hợp",
  "kind":      "concept",            // concept | definition | theorem | property | note | example | remark | summary
  "src":       { "paragraph": 42 },
  "blocks":    [ /* §3.3 */ ],
  "children":  [ /* section node lồng nhau */ ]
}
```

`kind` suy ra từ marker tiếng Việt: `Định nghĩa` → `definition`, `Chú ý` / `Lưu ý` → `note`, `Nhận xét` → `remark`, `Ví dụ` → `example`, `Định lí` → `theorem`, `Tính chất` → `property`. Cho UniLearn style callout box khác nhau mà không cần NLP.

### 3.3. Block types

Mọi block đều có: `{ "type", "block_id", "order", "src" }`.

```jsonc
// (a) paragraph — đơn vị phổ biến nhất
{
  "type": "paragraph",
  "text": "Tập hợp gồm các phần tử thuộc cả hai tập hợp A và B gọi là giao của A và B, kí hiệu A ∩ B.",
  "html": "Tập hợp gồm các phần tử thuộc cả hai tập hợp <span data-formula=\"f12\">\\(A\\)</span> và …",
  "inlines": [                                  // token hoá — nguồn chân lý, html render từ đây
    { "t": "text",    "v": "Tập hợp gồm các phần tử thuộc cả hai tập hợp " },
    { "t": "formula", "ref": "f12" },
    { "t": "text",    "v": " và " },
    { "t": "formula", "ref": "f13" }
  ],
  "marks": ["bold"]                             // định dạng cấp paragraph
}

// (b) list
{ "type": "list", "ordered": false, "items": [ { "level": 0, "inlines": [...], "text": "…" } ] }

// (c) formula — block-level (công thức đứng riêng dòng)
{
  "type": "formula", "ref": "f88",
  "latex": "A \\cap B = \\{ x \\mid x \\in A \\text{ và } x \\in B \\}",
  "display": "block"
}

// (d) figure — HÌNH THẬT (đây là chỗ base64 nằm)
{
  "type": "figure",
  "asset_id": "img_8",
  "caption": "Hình 1.2. Biểu đồ Ven",
  "alt": "Biểu đồ Ven minh hoạ tập hợp con",
  "html": "<img src=\"data:image/png;base64,iVBORw0KG…\" alt=\"Biểu đồ Ven\" />"
}

// (e) table
{ "type": "table", "has_header": true,
  "rows": [ { "cells": [ { "inlines": [...], "text": "…", "colspan": 1, "rowspan": 1 } ] } ] }

// (f) quote — thơ / trích dẫn văn bản (Văn 12 dùng nhiều)
{ "type": "quote", "lines": ["Sông Mã xa rồi Tây Tiến ơi", "Nhớ về rừng núi nhớ chơi vơi"], "attribution": null }

// (g) callout — Chú ý / Nhận xét
{ "type": "callout", "variant": "note", "title": "Chú ý", "blocks": [ /* nested */ ] }
```

### 3.4. Assets registry (base64 nằm ở đây)

```jsonc
"assets": {
  "img_8": {
    "kind": "figure",                 // figure | formula_fallback | decorative
    "mime": "image/png",
    "width": 480, "height": 320,
    "sha256": "…",                    // dedupe: 2 block dùng chung 1 ảnh → 1 entry
    "bytes": 65614,
    "data": "iVBORw0KGgoAAAANSUhEUg…" // base64 THUẦN, không kèm prefix
  },
  "f12": {
    "kind": "formula",
    "latex": "A \\cap B",
    "mathml": "<math>…</math>",       // optional
    "confidence": 0.97,
    "source": "mtef",                 // mtef | omml | vlm_ocr | manual
    "fallback": { "mime": "image/png", "data": "iVBOR…" }  // PNG render, chỉ khi confidence thấp
  }
}
```

### 3.5. Về yêu cầu `<img>base64</img>` — đề xuất điều chỉnh

Anh yêu cầu nhúng `<img>base64<img>`. Em **giữ đúng tinh thần** (base64 inline trong HTML để bên kia revert) nhưng đề xuất **2 chỉnh sửa nhỏ, quan trọng**:

| Anh đề xuất | Em đề xuất | Lý do |
|---|---|---|
| `<img>BASE64</img>` | `<img src="data:image/png;base64,BASE64" alt="…" />` | Đúng chuẩn HTML → UniLearn **không cần viết parser riêng**, mọi renderer/WYSIWYG hiển thị được ngay. Vẫn là "1 chuỗi base64 nhúng inline". |
| Mọi ảnh đều base64 | **Chỉ `figure`** base64. `formula` → LaTeX. | 95% ảnh là WMF công thức. Base64 chúng = JSON phồng, không search được, browser không render WMF. |

Thêm cờ cấu hình cho phía bàn giao:

- `asset_mode: "inline"` → bung base64 thẳng vào `html` của từng figure (đúng ý anh, file to nhưng self-contained).
- `asset_mode: "reference"` → `html` chỉ có `<img data-asset-id="img_8">`, base64 nằm ở `assets` (dedupe, nhỏ hơn ~30–40%).

**Khuyến nghị:** thống nhất với UniLearn dùng `reference`. Nếu họ chưa sẵn sàng, chạy `inline` cho v1 — cùng một pipeline, chỉ khác flag lúc serialize.

---

## 4. Kiến trúc pipeline

```
[0] Ingest        →  [1] Parse DOCX     →  [2] Media triage   →  [3] Formula resolve
 unrar/unzip          OOXML → DocAST        formula vs figure     MTEF→LaTeX (+OCR)
 sha256, dedupe       (chưa hiểu ngữ nghĩa)  vs decorative         confidence score
        │                                                                │
        └──────────────────────────────────────────────────────────────┘
                                     ↓
[4] Segment       →  [5] Theory slice   →  [6] Emit JSON      →  [7] QA gate    →  [8] Deliver
 marker/regex/bold    cắt A…đến trước B     schema v1.0           validate+score    UniLearn API
 dựng cây level                             assets registry       PASS/WARN/FAIL    idempotent upsert
                                                                        │
                                                                  FAIL → hàng đợi review thủ công
```

Mỗi stage **ghi artifact ra đĩa** (`work/<doc_id>/stage-N.json`) → resume được, debug được, không phải chạy lại từ đầu khi tune stage 4.

### 4.1. Stage 1 — Parse DOCX → DocAST

- Duyệt `document.xml` theo **thứ tự tài liệu** (`w:p` xen kẽ `w:tbl` — python-docx `.paragraphs` **bỏ sót table**, phải tự iterate `body.iterchildren()`; code khảo sát đã làm đúng).
- Giữ nguyên: `w:numPr/w:ilvl` (bậc bullet), bold/italic, `w:tab`, ngắt dòng mềm.
- Mỗi run được gắn nhãn: `text` | `ole_equation` | `omml` | `drawing` | `pict`.
- Chuẩn hoá Unicode **NFC**, thu gọn khoảng trắng, loại paragraph rỗng (nhưng **đếm và log**).

### 4.2. Stage 2 — Media triage (quyết định phân loại)

| Tín hiệu | Kết luận |
|---|---|
| `<w:object>` có `ProgID="Equation.*"` | `formula` |
| `<m:oMath>` | `formula` (OMML native) |
| `.wmf`/`.emf` kích thước < ~2KB, cao < 20pt, nằm inline giữa dòng | `formula` (heuristic) |
| `<w:drawing>` PNG/JPEG, rộng > 200px | `figure` |
| Ảnh không nằm trong section lý thuyết, hoặc là ảnh stock | `decorative` → **loại bỏ** |

Ảnh trang trí (ví dụ ảnh hồng cầu ở Hóa 10 Bài 1) bị drop nhưng **ghi vào `quality.flags`**, không xoá âm thầm.

### 4.3. Stage 3 — Formula resolution (**decode binary, KHÔNG phải OCR**)

**Kết luận đo được: không cần OCR cho công thức.** Hai bằng chứng:

**(a) Không có ảnh công thức nào mất nguồn.** Kiểm 3 file nặng nhất:

| File | `<w:object>` | có OLE | **thiếu OLE** |
|---|---|---|---|
| Toán 10 Bài 2 | 382 | 382 | **0** |
| Toán 12 Bài 4 | 639 | 639 | **0** |
| Hóa 10 Bài 2 | 150 | 150 | **0** |

Mọi công thức đều còn MTEF gốc. Ảnh WMF chỉ là **bản render preview** của OLE, không phải nguồn duy nhất.

**(b) MTEF v5 decode được — đã chạy thử trên `oleObject5.bin`:**

```
offset 28:  05 01 00 06 09        → MTEF v5, platform 1, MathType 6.9
            "DSMT6"               → application key
0x13 ENCODING_DEF   → "WinAllBasicCodePages"
0x11 FONT_DEF   ×4  → Times New Roman / Symbol / Courier New / MT Extra
0x08 FONT_STYLE_DEF, 0x12 EQN_PREFS
0x02 CHAR: opt=0x00, typeface=0x83, char=0x61   → 'a'
```

Format **tự mô tả**: có bảng font, record type cố định, chiều dài suy ra được. Đây là bài toán **parse binary deterministic**, không phải nhận dạng ảnh.

**Chiến lược 2 tầng:**

| Tầng | Cách làm | Bao phủ | Accuracy | Chi phí |
|---|---|---|---|---|
| **T0** | MathType 7 nhúng sẵn nguồn TeX → lấy nguyên văn | 18.6% (892/4797) | 100% | 0 |
| **T1** | OMML → LaTeX | ~2% | 100% | ~0 |
| **T2** | **MTEF v5 decoder** → AST → LaTeX | 51.7% (2482) | ~91% | offline |

**Tổng: 70.3% có LaTeX, 29.7% fallback ảnh PNG.** (v1.0 chỉ đạt 32.7%.)

#### 4.3.1. Đo độ chính xác — và vì sao ước lượng "~98%" ban đầu là SAI

892 công thức chứa **cả** nguồn TeX **lẫn** thân MTEF → dùng làm **validation set có ground truth miễn phí**: decode đường MTEF rồi đối chiếu với TeX.

| Vòng | Coverage | Đúng | **Sai** | Nhận xét |
|---|---|---|---|---|
| Decoder v1 (không cổng) | 84.5% | 0 | 6 | 99.3% cụt; `B=\left\{x\in\mathbb{R}\|x^2-5x=0\right\}` ra `B` |
| + cổng "tiêu thụ trọn stream" | 32.8% | 0 | 0 | An toàn nhưng ít dùng được |
| + từ chối mọi template | 32.7% | 220 | 0 | Bản v1.0 đã ship |
| + `CHAR` dùng **u16** thay vì u8 | 83.0% | 503 | 240 | Lỗi gốc: byte cao của mã ký tự bị đọc thành `END` |
| + lặp record ở tầng ngoài cùng | — | — | — | `parse_slot` dừng ở `END` lồng bên trong |
| + bảng selector đúng, ngoặc lấy từ ô 3 | — | — | — | `\sqrt` là selector 10, không phải 3 |
| + bit `0x02` là cờ tên hàm, không phải embellishment | — | — | — | `\sin` từng ra `sn` — mất record kế tiếp |
| **+ allowlist selector** | **70.3%** | **649** | **62** | **Đang dùng — accuracy 91.3%** |

Bài học: **coverage không phải là accuracy.** Con số 84.5% ban đầu chỉ đo "có sinh ra output", và gần như toàn bộ là chuỗi cụt. Nếu không có validation set này thì pipeline đã âm thầm đẩy LaTeX sai sang UniLearn — **nguy hiểm hơn hẳn việc không có LaTeX**, vì nội dung sai trông vẫn như đúng.

Nguyên tắc đã cài vào code: **thà từ chối còn hơn đoán.** Bốn lớp chặn trong `pipeline/mtef.py`:
1. Parser phải tiêu thụ trọn stream (còn byte thừa = lạc nhịp → loại).
2. Gặp `PILE` (ma trận / hệ phương trình) → loại.
3. `SAFE_SELECTORS` allowlist — chỉ nhận template đã đo đạt chuẩn.
4. Còn 8.7% sai nên **mọi công thức có `confidence < 0.98` đều kèm PNG** → luôn có đường đối chiếu.

Accuracy đo riêng từng selector (chỉ trên công thức dùng **đúng một** selector — cách quy lỗi cho *mọi* selector mà công thức chạm tới làm sai lệch số liệu):

| selector | đúng | sai | accuracy | trong allowlist |
|---|---|---|---|---|
| (không template) | 547 | 12 | 97.9% | – |
| `ROOT` (10) | 6 | 0 | 100% | ✔ |
| `FRACT` (11) | 75 | 6 | 92.6% | ✔ |
| `PAREN` (1) | 12 | 1 | 92.3% | ✔ |
| `BRACK` (3) | 2 | 2 | 50.0% | ✘ |
| `BRACE` (2) | 1 | 4 | 20.0% | ✘ |

`confidence` trong output phản ánh đúng số đo: `1.0` (TeX/OMML) · `0.98` (CHAR thuần) · `0.93` (có template) · `0.0` (fallback ảnh).

Đường tăng coverage tiếp theo (ước lượng, **chưa** verify): giải đúng ngữ pháp `TMPL` sẽ mở khoá phần lớn 67.3% còn lại. Mỗi selector template nên được bật **từng cái một**, có validation set gác.

Công thức trong corpus khá đơn giản (∈, ⊂, ∩, ∪, ℕ/ℤ/ℚ/ℝ, phân số, chỉ số, căn, giới hạn) → phần lớn là record `CHAR` + vài `TMPL`. Rủi ro tập trung ở template hiếm (ma trận, bảng biến thiên dạng `PILE`/`MATRIX`) — xử lý bằng cách **fallback về ảnh PNG** cho riêng những record đó, không kéo cả pipeline xuống.

**OCR chỉ còn 2 chỗ, đều KHÔNG trên đường găng:**
1. `Hóa 10 Bài 1` — lý thuyết là ảnh chụp, không có text lẫn MTEF. **Ưu tiên xin lại file gốc** thay vì OCR.
2. **QA spot-check** — đối chiếu ngẫu nhiên ~2% công thức để bắt bug parser. Vài chục call, không phải vài nghìn.

Mọi công thức đều **luôn** kèm `fallback` PNG (render từ WMF) → UniLearn không bao giờ mất nội dung kể cả khi LaTeX sai.

> Ghi chú sửa đổi (v1.1): bản v1.0 xếp VLM OCR thành tầng T3 với ~600–700 call. Sau khi xác minh tỉ lệ OLE đầy đủ = 100% và decode thử MTEF thành công, **T3 bị loại khỏi đường găng**. Ngân sách OCR không còn là ràng buộc của dự án.

### 4.4. Stage 4 — Segmentation

Rule-based, **không dùng LLM ở đường chính** (deterministic, rẻ, debug được):

1. Chuẩn hoá dòng: bỏ dấu, lowercase, gộp space.
2. Match `THEORY_START` = `^[ab][\.\-–:)\s]*\s*(kien thuc trong tam|ly thuyet|tom tat ly thuyet|phan li thuyet)`
3. Match `THEORY_END` = `\b(bai tap|phan bai tap|bai tap van dung)\b` (**bắt buộc có cụm "bài tập"** — tránh bẫy `B. PEPTIDE`).
4. Bên trong: nhận bậc theo thứ tự ưu tiên `I./II.` → `1./2.` → `a./b.` → `-` → `•`, kết hợp bold + `w:ilvl`.
5. **Nhiều header lý thuyết** (Toán 11 Bài 4, Hóa 12 Bài 4): lấy từ header **đầu tiên**, header thứ hai trở thành section con level 1.
6. Không match được → `quality.status = FAIL`, đẩy sang hàng đợi review, **không đoán bừa**.

LLM chỉ dùng ở **fallback lane** cho các file FAIL, và cho việc suy `chapter` khi docx không ghi.

### 4.5. Stage 8 — Delivery

- Format: **NDJSON** 1 document/dòng, hoặc `POST /v1/lessons/bulk-upsert`.
- Khoá idempotent: `doc_id` + `content_hash` → chạy lại không tạo trùng.
- Contract test: UniLearn cung cấp 1 endpoint `dry-run` để validate schema trước khi ghi thật.

---

## 5. Chất lượng & vận hành

### 5.1. JSON Schema chính thức
Publish `schema/lesson.v1.json` (Draft 2020-12), validate **mọi** output trong CI (`jsonschema` đã có sẵn trong env). Schema là **hợp đồng** với UniLearn — đổi phải bump `schema_version` (semver).

### 5.2. QA gates (fail-closed)

| Gate | Điều kiện FAIL | Điều kiện WARN |
|---|---|---|
| Theory không rỗng | < 50 từ **và** < 2 figure | < 150 từ |
| Formula resolved | < 70% có LaTeX | < 90% |
| Text coverage | ký tự output < 80% ký tự vùng lý thuyết trong docx | < 95% |
| Cây section | không có section nào | chỉ có level 1 |
| Marker | không tìm thấy `THEORY_START` | tìm thấy > 1 |
| Base64 | ảnh hỏng / decode fail | ảnh > 2 MB |

`Hóa 10 / Bài 1` sẽ **FAIL** ở gate đầu — đúng như mong muốn.

### 5.3. Golden set
Chốt **6 file mẫu** phủ hết các tier, snapshot JSON làm baseline regression:
Toán 10 Bài 2 (formula nặng) · Toán 12 Bài 4 (ảnh nhiều nhất, 647) · Hóa 10 Bài 2 (155 WMF) · Hóa 12 Bài 13 (PNG thật) · Văn 12 Tây Tiến (text + thơ) · Địa 11 Bài 2 (text + table).

### 5.4. Observability
Log/metric mỗi run: `docs_ok / warn / fail`, `formula_resolve_rate`, `ocr_calls`, `cache_hit_rate`, `p95_latency`, `output_bytes`. Dashboard đơn giản là đủ, nhưng phải có — 46 file hôm nay, vài nghìn file khi scale.

---

## 6. Lộ trình đề xuất

| Tuần | Hạng mục | Điều kiện hoàn thành (DoD) |
|---|---|---|
| **W1** | Stage 0–2 + schema v1.0 + JSON Schema file | Chốt schema với UniLearn; Văn 12 + Địa 11 + GDKTPL (18 file, không ảnh) ra JSON PASS |
| **W2** | Stage 4–7: segmentation + emit + QA gate | 18 file text-only đạt 100% PASS; golden set khoá |
| **W3** | Formula T1 + T2 (OMML + **MTEF v5 decoder**) | Toán 10 Bài 2 resolve ≥ 95%; figure base64 chạy đúng |
| **W4** | Hoàn thiện template hiếm + fallback PNG | Toàn bộ 46 file có báo cáo QA; spot-check 2% đạt ≥ 98% khớp |
| **W5** | Delivery + contract test + backfill | Đẩy trọn 46 file lên UniLearn, idempotent, có rollback |

**Milestone quan trọng nhất là cuối W1**: có JSON thật của 1 bài Văn 12 để bắn cho UniLearn ký duyệt schema. Chốt hợp đồng schema sớm, mọi thứ sau đó chỉ là lấp nội dung.

---

## 7. Việc cần anh quyết trước khi code

1. **`asset_mode`**: `inline` (đúng ý ban đầu, file to) hay `reference` (dedupe, khuyến nghị)?
2. **Định dạng `<img>`**: chấp nhận đổi sang `<img src="data:...">` chuẩn HTML?
3. **`book`**: mặc định "Kết nối tri thức" cho **tất cả** môn, hay Địa 11 / GDKTPL 12 dùng bộ khác? (docx không ghi bộ sách)
4. **Văn 10 / Hóa 10 đủ bài**: corpus hiện chỉ có Hóa 10 3 bài, Toán 10 3 bài (thiếu Bài 1), không có Văn 10 — anh có nguồn bổ sung không?
5. ~~Ngân sách OCR~~ — **đã gỡ bỏ**, xem §4.3. Formula giải bằng MTEF decoder, offline, không tốn call.
6. **`Hóa 10 Bài 1`** (lý thuyết là ảnh chụp): xin lại file gốc từ bên soạn (khuyến nghị), hay OCR để dựng tạm?

---

## 8. Hiện trạng code (v1.1)

```
pipeline/
  mtef.py      MathType OLE -> LaTeX: TeX fast-path + MTEF v5 decoder + 4 lớp chặn
  docxast.py   DOCX -> AST tuyến tính; phân loại formula/figure; WMF->PNG (cache); OMML->LaTeX
  segment.py   Cắt vùng lý thuyết theo marker; dựng cây mục con nhiều cấp
  emit.py      Dựng JSON schema v1.0; block quote/callout; QA gate
  cli.py       CLI + validate JSON Schema
schema/
  lesson.v1.json   JSON Schema Draft 2020-12 — hợp đồng với UniLearn
```

Chạy:

```bash
python3 -m pipeline.cli "<file.docx hoặc thư mục>" -o out [--asset-mode inline|reference]
```

Exit code: `0` sạch · `1` có file lỗi hoặc sai schema · `2` có file FAIL ở QA gate.

### Đã làm trong v1.1

| # | Hạng mục | Kết quả |
|---|---|---|
| 1 | **Công thức** | 32.7% → **70.3%** có LaTeX, accuracy 91.3% (§4.3.1) |
| 2 | **`schema/lesson.v1.json`** | Draft 2020-12, `additionalProperties: false`; CLI validate mọi output |
| 3 | **Block `quote` / `callout`** | Thơ trong ngoặc kép → `quote` + `lines[]`; `Chú ý`/`Nhận xét`/`Ví dụ` → `callout` + `variant` |
| 4 | **`chapter`** | Nhận `CHƯƠNG n`; với Ngữ văn suy `BÀI n:` là chương và `VĂN BẢN k:` là bài |
| – | **Bug mất ảnh** | Ảnh neo vào paragraph tiêu đề không còn bị vứt (`_keep_media`) |
| – | **Bug đếm figure** | `stats.figures` đã tính cả ảnh nằm inline trong paragraph |

### Kết quả chạy toàn bộ corpus

**42 file** (không phải 46 — 4 file `._*` là rác AppleDouble của macOS, đã lọc).

```
== tổng 42 file: PASS=31  WARN=10  FAIL=1     ERROR=0  INVALID=0
```

| Chỉ số | Giá trị |
|---|---|
| Sai schema | **0 / 42** |
| `doc_id` trùng | **0** |
| Công thức có LaTeX (trong output) | 230 / 333 = **69.1%** |
| Block sinh ra | paragraph 944 · figure 49 · callout 47 · table 21 · **quote 14** |
| `chapter` nhận được | 4 / 42 (docx phần lớn không ghi chương) |
| Thời gian | ~9 phút toàn bộ |

`FAIL` duy nhất là `chem-10-bai-01` — lý thuyết là ảnh chụp, không có text lẫn MTEF. Đây là **đúng ý muốn**: gate chặn lại thay vì đẩy JSON rỗng sang UniLearn.

10 `WARN` đều là `FORMULA_RESOLVE_*`, tập trung ở Toán 12 (34–50%) vì các bài đó dùng nhiều bảng biến thiên dạng `PILE` — bị từ chối đúng thiết kế và có PNG kèm.

### Bug bắt được nhờ gate tự động (không phải nhờ đọc code)

| Bug | Hậu quả | Ai bắt |
|---|---|---|
| `Asset` gán tham số theo vị trí sau khi chèn field `confidence` | `sha256` rỗng ở **20/42 file** | JSON Schema (mục 2) |
| `doc_id` chỉ gồm môn+lớp+số bài | **9 file bị ghi đè, mất hẳn** | Đếm file output |
| Logic `chapter` lấy tên chương làm tên bài (Ngữ văn) | 3 file Văn dùng chung `doc_id` | Collision guard |
| Ảnh neo vào paragraph tiêu đề bị vứt cùng `inlines` | Mất ảnh âm thầm | Đối chiếu docx ↔ output |

Hai bug giữa do chính việc làm mục 2–4 sinh ra. Đó là lý do gate tự động đáng giá hơn review thủ công.

### Hạn chế đã biết (chưa làm, không giấu)

1. **30.9% công thức còn là ảnh PNG.** `text` chèn `[công thức]` → search kém; `html` vẫn hiển thị đủ. Đường đi tiếp: bật thêm selector `BRACE`/`BRACK` và xử lý `PILE` (bảng biến thiên), mỗi lần bật **một** selector có validation set gác.
2. **Accuracy 91.3%, còn 8.7% LaTeX sai.** Đã giảm thiểu bằng cách kèm PNG cho mọi `confidence < 0.98`, nhưng chưa loại hẳn.
3. **Layout ảnh nổi bị mất** (`wrapTight`, vị trí bên phải). Khuyến nghị **không** tái tạo layout Word; nên thêm gợi ý `placement` để UniLearn tự quyết (schema đã chừa field).
4. **Caption ảnh không trích được** — "Hình 1.2" nằm trong pixel, không phải text.
5. **`chapter` chỉ nhận được 4/42** vì docx không ghi chương. Cần bảng tra ngoài (chương ↔ số bài) theo từng môn.
6. **Bài tập chưa xử lý** — v1 chỉ làm lý thuyết như phạm vi đã chốt.
7. **Tốc độ ~9 phút/42 file**, nghẽn ở spawn ImageMagick cho từng WMF.
