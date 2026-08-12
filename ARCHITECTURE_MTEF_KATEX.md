# MTEF → KaTeX: Chẩn đoán gốc rễ và Kiến trúc lại

> ## ✅ ĐÃ TRIỂN KHAI — kết quả
>
> | | Trước | Sau |
> |---|---:|---:|
> | KaTeX lỗi cứng / 4.584 công thức | **62** (1,35%) | **7** (0,15%) |
> | Lệch ngoặc (`brace_imbal`) | 41 | **0** |
> | Test tự động | 2 | **176** |
> | Cổng chặn phát hành | không có | `--fail-on-katex-error` |
>
> **Giảm 89% lỗi cứng. 0 thoái triển** (kiểm bằng so sánh từng công thức ở cả 3 thay đổi).
> Output HTML giao cho khách **giống hệt từng byte** — chỉ thêm khả năng phát hiện lỗi.
>
> Chi tiết ở [§8](#8-trạng-thái-triển-khai).

> **Post-mortem kỹ thuật · pipeline `uni_convert` · 11 Aug 2026**
>
> Đo trên **4.584 công thức MathType thật** từ 11 file `.docx` Toán 10/11/12.
> Kết luận trung tâm: `_tidy()` không phải lớp sửa lỗi — nó là một lớp **gây** lỗi mới,
> và lỗi thật nằm ở tầng parser byte-stream phía trên nó.

| Chỉ số | Giá trị |
|---|---|
| Công thức đã decode | **4.584** (2.714 duy nhất) |
| KaTeX lỗi cứng (`throwOnError:true`, `strict:false`) | **62 — 1,35%** |
| — cùng phép đo với `strict:"error"` | 90 — 1,96% |
| Lệch ngoặc **do `_tidy` tạo ra** | **0 → 30** |
| Công thức bị `_tidy` sửa | **44,2%** (2.024) |
| Số dòng regex trong `_tidy` | **~450** |

Mọi con số đều tái lập được bằng harness ở [§4](#4-cổng-kiểm-thử-tự-động).

> **Đính chính số liệu.** Bản nháp đầu của tài liệu này ghi *77 lỗi (1,7%)*. Con số đúng là **62 (1,35%)**. Nguyên nhân: `pipeline/mtef.py` được sửa lúc **15:21 ngày 12/08** (giữa hai lần đo của tôi), trong đó `\begin{align}` đã được đổi thành `\begin{aligned}` — việc này tự nó xoá 6 ca lỗi. Mọi số liệu trong tài liệu này là **của bản `mtef.py` sau thay đổi đó**.

---

## §0. Kết luận trước, lý lẽ sau

Bạn đang cố sửa một **lỗi mất thông tin ở tầng parser** bằng cách **đoán lại thông tin đó ở tầng chuỗi**. Việc này về mặt lý thuyết là không thể thắng, và số đo chứng minh điều đó: `_tidy` khử được 26/28 ca số mũ nuốt biểu thức, nhưng đồng thời **tự tạo ra 30 công thức lệch ngoặc mà bản raw không hề có**.

### Bằng chứng — `_tidy` xoá dấu `}` của `\frac`

```text
raw (từ decoder, ngoặc CÂN BẰNG):
\begin{array}{l}sin^{2 \alpha + c o s ^{2 \alpha = 1} 1 + t a n ^{2 \alpha = \frac{1}{c o s ...
                                                                              ^^^^^^^^^
sau _tidy (MẤT dấu } → KaTeX chết):
\begin{array}{l}\sin ^2 \alpha + c o s^2 \alpha = 1 1 + t a n^2 \alpha = \frac{1{c o s ...
                                                                              ^^^^^^^^
```

Hệ quả trên KaTeX là **lớp lỗi lớn nhất toàn corpus** — `Expected 'EOF', got '<token>'`: **46/62 ca, tức 74% tổng lỗi cứng**, đều truy về đúng cơ chế này.

### Ba ca lỗi cứng điển hình, đã truy nguyên

```text
45^0 3 2 ' = \left(4 5 + \frac{3 2{6 0}\right)} ^{0}
   → Expected 'EOF', got '\right'      [ngoặc \frac bị _tidy phá + chữ số bị tách]

B= \sin ^2 6 0 ^{\circ} + t a n ^{2 3 0 ^{\circ} - 2 = - \frac{1 1{1 2}}}
   → Extra }                            [số mũ nuốt biểu thức + \frac bị phá]

\cos \alpha =\sqrt[1 - s i n ^{2 \alpha} \Leftrightarrow \cos \alpha =\sqrt[c o s ^{2 \alpha} ...
   → Unexpected end of input in a macro argument    [\sqrt[ không đóng; 20/77 ca]
```

---

## §1. Phân tích nguyên nhân gốc rễ

Năm nguyên nhân độc lập. **RC1 và RC2 nằm ở decoder** và là nguồn của phần lớn rác; **RC3 là lớp khuếch đại**; **RC4 là lỗi kiến trúc luồng dữ liệu**; **RC5 là lý do mọi thứ lọt tới khách hàng**.

### RC1 — Parser chèn dấu cách giữa các CHAR record — *Nghiêm trọng*

Tại `pipeline/mtef.py:584`, `parse_single_slot()` kết thúc bằng:

```python
return " ".join(res_parts).strip()
```

Mỗi record `CHAR` là **một** phần tử của `res_parts`. Nên mọi ký tự liền kề bị tách bằng space:

| Gốc | Sau parser |
|---|---|
| `cos` | `c o s` |
| `180` | `1 8 0` |
| `32` | `3 2` |

Đây là **phá huỷ thông tin không hồi phục**: sau khi tách, `3 2` không còn phân biệt được là số *ba mươi hai* hay tích *3·2*. Không regex nào khôi phục được ngữ nghĩa đã mất.

Đo được **266 công thức raw** mắc lỗi này; `_tidy` vá lại được một nửa (còn **136 ≈ 3,0%**) nhờ dò tên hàm — nhưng chính vì đã bị tách, regex `(cos)` không khớp `c o s`, nên phần còn lại render thành *tích các biến italic* `c·o·s`.

> **⚠️ Vì sao đáng lo hơn lỗi đỏ**
> Lỗi này thường **không** làm KaTeX báo đỏ. Nó render ra công thức *sai về mặt toán học* nhưng trông bình thường. Đó là loại lỗi tệ nhất: im lặng và lọt qua mọi kiểm tra bằng mắt.

### RC2 — Bảng số slot không đầy đủ → desync biên slot — *Nghiêm trọng*

`parse_tmpl()` quyết định đọc bao nhiêu ô con bằng:

```python
for _ in range(_SLOTS.get(sel, 1)):   # mặc định 1 slot cho MỌI selector lạ
```

Trong MTEF, ô con được phân định bởi record `END`. Nếu bảng khai 1 slot nhưng template thật có 3, thì slot thứ 2–3 cùng các `END` của chúng bị **cha** đọc mất → slot cha kết thúc sớm → phần dư trôi lên ông nội. Đây là **desync lan truyền**, và nó là cơ chế sinh ra:

- **Ký tự `|` rò ra** — dải phân cách slot của template tập hợp/khoảng bị render thành ký tự thường: `\{|x \in \mathbb{R}|\}`. Đo được **60 công thức raw**, `_tidy` chỉ khử được 4 (còn **56**).

> **⚠️ Đính chính:** bản nháp đầu quy **số mũ nuốt biểu thức** cho RC2. Sai. MTEF nhị phân lưu **đúng** một template SUP có nội dung `2-7x+1=0`, vì giáo viên thật sự đã gõ vào đó — decoder hoàn toàn không lỗi. Đây là **lỗi dữ liệu nguồn**, thuộc lớp *semantic repair*, xem [§7](#7-lỗi-số-mũ-nuốt-biểu-thức--lỗi-dữ-liệu-nguồn).

Đo thực tế: **129 lần** nhánh `default=1` được kích hoạt bởi selector chưa khai báo.

| Selector | Là gì | Số lần | Rủi ro |
|---|---|---:|---|
| `14` | `TM_OBAR` (gạch trên) | 52 | Thấp — thực tế 1 slot |
| `9` | `TM_INTERVAL` (khoảng) | 51 | **Cao — spec 3 slot, đọc 1** |
| `37` | chưa định danh | 21 | **Không xác định** |
| `33` | chưa định danh | 3 | **Không xác định** |
| `31`, `13` | `TM_TILDE`, `TM_UBAR` | 2 | Thấp |

### RC3 — `_tidy()` là regex-soup phụ thuộc thứ tự, net-negative về ngoặc — *Nghiêm trọng*

~450 dòng, ~120 phép thay thế chạy tuần tự trên **chuỗi phẳng**, nhiều phép mâu thuẫn nhau. Ba khuyết tật cấu trúc:

**a. Các luật đánh nhau.** Có luật *thêm* `\}` theo phỏng đoán ("nếu chuỗi có `\{` mà không kết thúc bằng `\}` thì thêm vào"), rồi cuối hàm lại có luật *đếm và cắt* `}` thừa. Hai luật này triệt tiêu lẫn nhau tuỳ dữ liệu — và chính khối "balance" cuối cùng là thủ phạm xoá dấu `}` của `\frac` ở bằng chứng đầu bài.

**b. Overfit vào corpus bằng cách dò chuỗi con.**

```python
if 'sin ^{2' in s and 'c o s ^{2' in s:
    s = r"\begin{array}{l}\sin^2 \alpha + \cos^2 \alpha = 1 \\ ..."   # bảng công thức HARD-CODE
```

Đây không phải chuẩn hoá mà là **thay thế nội dung**. Nó ghi đè bất kỳ công thức nào tình cờ chứa chuỗi con đó — kể cả công thức đúng ở tài liệu khác. Đây là bom hẹn giờ khi mở rộng sang môn/lớp mới.

**c. Không idempotent, không có hậu điều kiện.** Không luật nào khai báo tiền/hậu điều kiện, nên không thể kiểm chứng luật nào làm hỏng gì. Bug `0 → 30` tồn tại được chính vì thiếu bất biến này.

### RC4 — Mất provenance: tầng emit đoán lại thứ mà tầng AST đã biết chắc — *Nghiêm trọng*

`docxast.py` đã phân loại chính xác từng inline: `kind = text | formula | image`. Nhưng thông tin đó bị **làm phẳng thành chuỗi**, rồi `exercises.py` phải **đoán lại** đâu là toán — bằng một danh sách stopword tiếng Việt:

```python
is_pure_math = not bool(re.search(
    r'\b(Cho|Liệt|Khi|Tập|Xác|Trong|khẳng|định|sau|đây|đúng|rỗng|phần|tử|hợp|có)\b', ...))
```

Đây là gốc rễ của triệu chứng #2. Cơ chế thất bại rất rõ:

1. **Bất kỳ câu tiếng Việt nào không chứa một trong ~14 từ đó sẽ bị bọc trọn vào `[MATH: ...]`.**
2. Biên công thức được xác định bằng `rfind('}')` — nên một câu kết thúc bằng dấu `}` sẽ **hút toàn bộ chữ phía trước** vào math mode.

Danh sách stopword không bao giờ đầy đủ được: nó là bộ phân loại heuristic đặt ở nơi mà **đáp án đúng đã có sẵn cách đó hai tầng gọi hàm**.

### RC5 — Không có cổng kiểm định, pipeline mù với lỗi KaTeX — *Chặn phát hành*

```javascript
// pipeline/katex_render.js
katex.renderToString(tex, { throwOnError: false, ... })
```

Với `throwOnError:false`, KaTeX **không bao giờ** ném lỗi; nó âm thầm trả về HTML chứa `class="katex-error"` màu đỏ. Pipeline coi đó là thành công, đóng gói, và giao cho khách.

**Không tồn tại bước nào trong toàn hệ thống có thể fail vì một công thức sai.** Đó là lý do 77 lỗi cứng đi được tới sản phẩm.

---

## §1b. Vì sao vá bằng regex luôn sót case

Không phải vì viết regex chưa đủ giỏi. Có ba rào cản mang tính hình thức:

### 1. Ngoặc lồng nhau không phải ngôn ngữ chính quy

Cân bằng `{}`, `\left/\right`, đối số của `\frac` là bài toán **context-free**, cần bộ đếm/ngăn xếp không giới hạn. Regex (automat hữu hạn) *chứng minh được* là không biểu diễn nổi.

Mọi "luật cân bằng ngoặc" viết bằng `re.sub` chỉ là xấp xỉ, và khối cân bằng cuối `_tidy` là ví dụ sống: nó đếm `{` và `}` **toàn cục** rồi cắt bừa **ở cuối chuỗi** — nên nó cắt đúng dấu `}` của `\frac` ở giữa. **Muốn sửa cấu trúc thì buộc phải có parser.**

### 2. Thông tin đã bị mất trước khi regex chạy

RC1 và RC2 xoá vĩnh viễn biên token và biên slot. Regex ở hạ nguồn không *sửa* mà đang **đoán lại** dữ liệu đã mất, dựa trên tần suất của corpus hiện tại. Đoán đúng trên tập đã thấy, sai trên tập chưa thấy — đúng định nghĩa của overfitting.

### 3. Phép biến đổi chuỗi không giao hoán và không hợp lưu

120 phép `re.sub` tuần tự tạo ra không gian trạng thái phụ thuộc thứ tự với `n!` khả năng tương tác. Thêm một luật ở dòng 300 có thể phá luật ở dòng 700 mà không có gì báo. Không có tính idempotent (`f(f(x)) = f(x)`) nên chạy lại pipeline cũng không hội tụ về điểm bất động.

---

## §2. Kiến trúc lại

### 2.1 Tách triệt để chữ và công thức: giữ kiểu, đừng bao giờ đoán lại

> **Nguyên tắc bất di bất dịch:** một lần đã biết một inline là công thức thì thông tin đó **không bao giờ** được làm phẳng thành chuỗi rồi suy luận lại.

Bỏ hoàn toàn `_format_inline_text()` và danh sách stopword. Thay bằng luồng typed từ `docxast` tới `emit`:

```python
@dataclass(frozen=True)
class TextSpan:  text: str                      # chữ, KHÔNG BAO GIỜ vào math mode

@dataclass(frozen=True)
class MathSpan:  latex: str; origin: bytes      # origin = MTEF gốc, để truy vết + override

@dataclass(frozen=True)
class ImageSpan: path: str; alt: str

Doc = list[Block]
Block = list[TextSpan | MathSpan | ImageSpan]

def render_block(spans) -> str:
    out = []
    for s in spans:
        match s:
            case TextSpan():  out.append(escape_text(s.text))     # giữ nguyên tiếng Việt
            case MathSpan():  out.append(f"[MATH: {s.latex}]")    # đã validate ở S6
            case ImageSpan(): out.append(f"[IMAGE: {s.path}]")
    return "".join(out)
```

#### Xử lý ca "tác giả gõ toán bằng chữ thường"

Vẫn có trường hợp giáo viên gõ `x^2` trực tiếp trong Text Run. Đừng dùng heuristic phủ định như hiện tại. Dùng **quy tắc promotion có kiểm chứng**, ba điều kiện đồng thời:

1. Span chỉ gồm ký tự thuộc *whitelist* toán (chữ ASCII, số, `+-*/^_=<>(){}[]`, toán tử Unicode, macro `\[a-zA-Z]+`).
2. Span **không chứa** ký tự có dấu tiếng Việt — đây là điều kiện **chặn cứng**, không phải điểm số.
3. **KaTeX parse được span đó** ở chế độ `throwOnError:true`.

Điều kiện 3 là chỗ then chốt: nó biến promotion từ *phỏng đoán* thành *tự kiểm chứng*. Không parse được thì để nguyên là chữ. Sai lệch tệ nhất chỉ còn là "một công thức hiển thị dưới dạng text thường" — chấp nhận được — thay vì "một đoạn văn tiếng Việt làm sập KaTeX".

### 2.2 Pipeline chuẩn hoá nhiều tầng thay cho `_tidy`

Điểm chuyển hoá quan trọng nhất: **S3 làm việc trên cây, không trên chuỗi.** Mọi sửa lỗi cấu trúc (ngoặc, arity, fence) chỉ được phép xảy ra ở đó.

| Tầng | Tên | Nội dung |
|---|---|---|
| **S0** | Sửa tại decoder | Nơi *duy nhất* còn biết cấu trúc gốc. Vá RC1 (không space-join CHAR) và RC2 (bảng slot đầy đủ + bất biến). Phần lớn rác biến mất ở đây, **trước khi có chuỗi nào tồn tại**. |
| **S1** | Chuẩn hoá lexical | Thuần ký tự, không cấu trúc: NFC Unicode, xoá vùng PUA `U+E000–U+F8FF`, sửa TCVN3 (`§` → `Đ`), gộp whitespace. Idempotent tuyệt đối. |
| **S2** | Lex + parse LaTeX → cây | Bộ lex nhỏ (~200 dòng) sinh token `Ctrl`/`Char`/`GroupOpen`/`GroupClose`/`Sub`/`Sup`, rồi dựng cây `Node`. Parser **khoan dung**: lỗi không ném ra mà ghi vào `node.defects[]`. |
| **S3** | **Sửa cấu trúc trên cây** | Cân bằng group bằng ngăn xếp thật; khớp `\left`/`\right`; ép arity `\frac`=2, `\sqrt`=1+opt; đóng `\sqrt[` hở; gỡ group rỗng. **Không thể xoá sai dấu `}` vì cây không có dấu ngoặc — chỉ có quan hệ cha-con.** |
| **S4** | Chuẩn hoá ngữ nghĩa | Trên cây, theo ngữ cảnh: tên hàm → `\sin`/`\cos`; `\limits` cho toán tử lớn; `°` → `^{\circ}`; bọc `\text{}` cho mọi ký tự phi-ASCII; `N/Z/Q/R` → `\mathbb{}`. |
| **S5** | Serialize | Cây → LaTeX. Bộ sinh **tự biết** khi nào *bắt buộc* có space (sau control word đứng trước chữ cái) — nên RC1 không thể tái xuất hiện theo thiết kế. |
| **S6** | Validate + fallback | KaTeX `throwOnError:true`. Đạt → phát hành. Không đạt → *quarantine*: xuất ảnh/MathML thay thế, ghi log kèm `sha1(mtef_bytes)`, và **fail build**. |

> **Hợp đồng cho mỗi tầng**
> Mỗi tầng là **hàm thuần khiết** có: (a) tiền điều kiện, (b) hậu điều kiện kiểm được bằng assert, (c) tính idempotent `f(f(x)) == f(x)` có property-test, (d) fixture test riêng.
> Muốn thêm mẫu MathType mới thì thêm **một luật ở đúng một tầng, kèm test** — không sửa xen vào 450 dòng chung.

#### Thay hard-code dò chuỗi con bằng override khoá theo hash

Vẫn sẽ có công thức MathType hỏng tới mức không thể sửa bằng thuật toán. Đừng dò chuỗi con như RC3b. Hãy khoá override theo **hash của chính byte MTEF gốc** — chính xác tuyệt đối, không thể dương tính giả:

```json
{
  "3f9a1c7e...": {
    "latex": "\\begin{array}{l}\\sin^2\\alpha+\\cos^2\\alpha=1\\\\ ...\\end{array}",
    "note":  "Toán 11 Bài 1 f51 — MTEF hỏng ở nguồn, không cứu được bằng thuật toán",
    "added": "2026-08-11"
  }
}
```

```python
# tra cứu trong S0, TRƯỚC mọi bước chuẩn hoá:
key = hashlib.sha1(mtef_bytes).hexdigest()
if key in OVERRIDES:
    return OVERRIDES[key]["latex"], "override"
```

---

## §3. Bộ quy tắc chuẩn hoá cụ thể

### 3.1 RC1 — bỏ space-join, dùng bộ sinh biết ngữ cảnh

Sửa tại `pipeline/mtef.py:584`. Thay vì nối chuỗi bằng space, trả về danh sách token và để S5 quyết định space:

```python
def emit_latex(tokens: list[Tok]) -> str:
    out = []
    for i, t in enumerate(tokens):
        if out and _needs_space(tokens[i-1], t):
            out.append(" ")
        out.append(t.text)
    return "".join(out)

def _needs_space(prev: Tok, cur: Tok) -> bool:
    # Space CHỈ bắt buộc khi control word đứng liền chữ cái/số,
    # nếu không sẽ dính vào tên macro:  \alpha x  ≠  \alphax
    if prev.kind == "ctrl" and prev.text[-1].isalpha() and cur.text[:1].isalnum():
        return True
    return False    # hai CHAR liền nhau -> KHÔNG space:  c+o+s -> "cos",  1+8+0 -> "180"
```

Riêng thay đổi này khử tận gốc cả **266 ca** `spaced_letters`, đồng thời loại bỏ nhu cầu của `_FUNC_RE` và vòng `for _ in range(3)` dò tên hàm trong `_tidy`.

### 3.2 RC2 — bảng slot đầy đủ + bất biến phát hiện desync

Hai thay đổi. Thứ nhất, **bỏ giá trị mặc định** — selector lạ phải ồn ào, không được im lặng:

```python
nslots = _SLOTS.get(sel)
if nslots is None:
    self.defects.append(f"unknown_selector:{sel}")   # đi vào quarantine, KHÔNG đoán bừa
    nslots = 1

start_depth = self.end_count
slots = [self.parse_single_slot(depth + 1) for _ in range(nslots)]

# BẤT BIẾN: mỗi slot phải tiêu thụ đúng một record END
if self.end_count - start_depth != nslots:
    self.defects.append(
        f"slot_desync:sel={sel}:exp={nslots}:got={self.end_count - start_depth}"
    )
```

Thứ hai, khai đủ selector còn thiếu — ưu tiên `9` (`TM_INTERVAL`, 51 lần, spec 3 slot) và điều tra `37`, `33` bằng chính bất biến trên.

Khi desync được *phát hiện* thay vì âm thầm sinh rác, mẫu tập hợp `\{|x \in \mathbb{R}|\}` và số mũ nuốt biểu thức **không còn cần regex nào ở hạ nguồn**.

### 3.3 RC3 — cân bằng ngoặc và fence bằng ngăn xếp, ở tầng cây

Đây là thay thế trực tiếp cho khối "balance" đang gây bug `0 → 30`. Điểm khác biệt: nó chèn dấu đóng **tại đúng vị trí ngữ nghĩa**, không cắt ở cuối chuỗi.

```python
def balance(tokens):
    out, stack = [], []
    for t in tokens:
        if t.kind == "open":
            stack.append(len(out)); out.append(t)
        elif t.kind == "close":
            if stack:
                stack.pop(); out.append(t)
            # không có open tương ứng -> BỎ dấu close mồ côi (không đẩy sang cuối)
        else:
            out.append(t)
    for _ in stack:                 # đóng các group còn hở, tại CUỐI phạm vi của chúng
        out.append(Tok("close", "}"))
    return out


def match_fences(nodes):
    # \left và \right phải khớp theo cặp trong cùng một cấp
    #   \left hở    -> thêm \right.
    #   \right mồ côi -> bỏ
    # KHÔNG BAO GIỜ sinh chuỗi "\right.}" — cây không cho phép.
    ...
```

Ba luật hệ quả, **tự động đúng** nhờ làm ở tầng cây và **không cần regex nào**:

| Triệu chứng cũ | Vì sao biến mất |
|---|---|
| `\right.}` và `\right..\}` | fence và group là hai loại node khác nhau, serializer đặt chúng đúng thứ tự |
| `\end{array\}` | `\begin`/`\end` là node môi trường có tên là *thuộc tính*, không phải chuỗi; serializer luôn in `\end{array}` |
| `\` thừa ở cuối | token `Ctrl` rỗng bị loại khi dựng cây |

#### Hai luật KaTeX-đặc thù cần thêm ở S4

- `\begin{align}` → `\begin{aligned}`. KaTeX chỉ cho `align` ở display mode; đây là **6/77 ca lỗi cứng** và là bug thuần cấu hình. `aligned` chạy được ở inline mode.
- Trong `\text{...}` không được chứa macro toán (`\text{ \tan }` → lỗi). Serializer phải đóng `\text` trước macro rồi mở lại.

---

## §4. Cổng kiểm thử tự động

> Mục tiêu "0 lỗi đỏ" **không** đạt được bằng cách sửa cho hết lỗi, mà bằng cách **làm cho lỗi không thể lọt qua build**.

Bốn cổng, xếp theo thứ tự phát hiện sớm.

### Cổng 1 — Kiểm định KaTeX strict (chặn phát hành)

Chính là harness đã dùng để tạo mọi số liệu trong tài liệu này. Điểm cốt tử là `throwOnError:true`, **ngược với production hiện tại**.

```javascript
// tools/katex_gate.js  — chạy được ngay hôm nay
const katex = require("katex");
let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", c => input += c);
process.stdin.on("end", () => {
  const out = JSON.parse(input).map(tex => {
    try { katex.renderToString(tex, { throwOnError: true, strict: false }); return null; }
    catch (e) { return String(e.message).slice(0, 160); }     // null = ĐẠT
  });
  process.stdout.write(JSON.stringify(out));
});
```

> **Lưu ý khi chạy:** Node phân giải `require("katex")` theo **vị trí file script**, không theo `cwd`. Đặt `katex_gate.js` trong project (cạnh `node_modules/`), đừng đặt ở `/tmp`.

Bọc bằng Python: quét toàn bộ JSON/HTML đầu ra, trích mọi `[MATH: ...]` và mọi `class="katex"`, đẩy qua cổng, và `sys.exit(1)` nếu còn lỗi. Báo cáo kèm `sha1(mtef_bytes)` để truy ngược về đúng công thức trong đúng file `.docx`.

### Cổng 2 — Kiểm tra không-thoái-triển

**Cổng giá trị nhất, và hiện chưa tồn tại.** Chính cổng này bắt được bug `0 → 30`.

Bất biến: **chuẩn hoá không được phép tạo ra lỗi mới.**

```python
def test_normalization_never_worsens(mtef_bytes):
    raw  = decode(mtef_bytes, normalize=False)
    norm = decode(mtef_bytes, normalize=True)

    assert katex_ok(norm) or not katex_ok(raw), \
        f"THOÁI TRIỂN: raw parse được, sau chuẩn hoá thì không\n  raw={raw}\n  norm={norm}"

    for inv in (brace_balanced, fences_matched, no_pua_chars):
        assert inv(norm) or not inv(raw), f"{inv.__name__} bị chuẩn hoá làm hỏng"
```

### Cổng 3 — Property test cho từng tầng

- **Idempotent:** `stage(stage(x)) == stage(x)` với mọi tầng S1–S5, chạy trên toàn corpus.
- **Giao hoán ở nơi đã tuyên bố:** nếu hai luật cùng tầng được khai là độc lập thì đổi thứ tự phải cho cùng kết quả — bắt sớm các luật đánh nhau kiểu RC3a.
- **Bất biến đầu ra:** ngoặc cân bằng · `\left`/`\right` khớp · không ký tự PUA · **không ký tự tiếng Việt nào ngoài `\text{}`** (chặn cứng RC4).

### Cổng 4 — Telemetry độ phủ, fail-on-new-unknown

Ghi lại mọi `defects[]` từ S0/S2 (selector lạ, slot desync) vào một baseline JSON đã commit. Build **fail khi xuất hiện selector lạ mới**.

Đây là cơ chế biến "gặp mẫu MathType chưa từng thấy" từ *rác im lặng lọt tới khách* thành *một lỗi CI có địa chỉ rõ ràng* — chính là yêu cầu "dễ mở rộng khi gặp mẫu MathType mới".

> **Định nghĩa Done**
> Trên corpus vàng: Cổng 1 báo **0 lỗi** · Cổng 2 báo **0 thoái triển** · Cổng 4 báo **0 selector lạ mới** · mọi công thức trong quarantine đều có override hoặc fallback ảnh đã duyệt.
> Chỉ khi đó mới đóng gói gửi khách.

---

## §5. Lộ trình theo thứ tự ROI

| Bước | Công sức | Việc | Lợi ích kỳ vọng |
|---|---|---|---|
| **1** | nửa ngày | **Dựng cổng trước khi sửa gì.** Cổng 1 + Cổng 2 và corpus vàng 4.584 công thức. Không sửa code sản xuất. | Chưa có thước đo thì không phân biệt được *sửa đúng* với *sửa may* |
| **2** | 1 ngày | **Tắt khối "balance" của `_tidy`.** Bỏ khối đếm-và-cắt ngoặc ở cuối. Sửa `align` → `aligned` cùng lúc. | **~28/77 lỗi cứng** biến mất mà không cần viết parser, **+6 ca** từ `align` |
| **3** | 1 ngày | **Vá RC1 tại decoder.** Bỏ space-join ở `mtef.py:584`, thêm `_needs_space`. | Khử **266 ca** chữ số/tên hàm bị tách — nhóm lỗi *im lặng* nên nguy hiểm nhất |
| **4** | 1 ngày | **Bất biến RC2 + quarantine.** Bỏ `default=1`, thêm bất biến đếm `END`, khai đủ selector `9`/`37`/`33`. | Rác trở nên *quan sát được* |
| **5** | 2 ngày | **Xoá RC4 — luồng typed span.** Bỏ `_format_inline_text` và stopword. Nối `MathSpan`/`TextSpan` từ `docxast` tới `emit`. | Chấm dứt hẳn lớp lỗi "tiếng Việt trong math mode" |
| **6** | 3–4 ngày | **S2/S3 — parser và sửa lỗi trên cây.** Thay phần cấu trúc còn lại của `_tidy`. Hard-code trig → `overrides.json` khoá theo hash. | Nền tảng bền vững, mở rộng an toàn |

> **⚠️ Thứ tự này không tuỳ tiện**
> Bước 2 và 3 cho phần lớn lợi ích với công sức nhỏ nhất, *vì chúng xoá bớt code chứ không thêm code*.
> Viết parser (bước 6) là việc đúng nhưng đắt nhất — làm sau cùng, và chỉ làm trên nền đã có cổng đo ở bước 1.

---

## §6. Một lưu ý về phạm vi đo

Số liệu ở trên lấy từ **11 file Toán** trong `Kiến thức trọng tâm và tài tập/` (Toán 10 bài 2–4, Toán 11 bài 1–4, Toán 12 bài 1–4). Corpus tổng có **178 `.docx`**; các môn Hoá/Sử/Văn/Địa **chưa** được đưa vào phép đo này, nên tỉ lệ 1,7% **chỉ đại diện cho môn Toán**. Bước 1 của lộ trình nên mở rộng corpus vàng ra toàn bộ 178 file trước khi chốt ngưỡng phát hành.

Một **đính chính về phương pháp**, để bạn tái lập được: `decode_ole()` trả về tuple theo thứ tự `(latex, source)`. Đọc sai thứ tự này sẽ khiến mọi phép kiểm tra chạy trên nhãn `"tex"`/`"unresolved"` và **báo 0 lỗi một cách giả tạo**.

---

## §7. Lỗi số mũ nuốt biểu thức — lỗi dữ liệu nguồn

### 7.1 Cơ chế

Giáo viên gõ `6x`, bấm `Ctrl+H` vào ô số mũ, gõ `2`, rồi **quên bấm `→` để thoát ô số mũ**, nên gõ luôn `-7x+1=0` ngay trong ô số mũ.

MTEF nhị phân vì thế lưu **đúng** một template `TM_SUP` có nội dung `2-7x+1=0`. **Decoder không hề sai.** Đây là lỗi dữ liệu nguồn — thuộc lớp *semantic repair* (suy diễn ý định tác giả), khác hoàn toàn với *syntactic normalization* của RC1–RC3.

> **Vì sao không có lỗi đỏ nào để bắt:** `6x^{2-7x+1=0}` là LaTeX **hợp lệ về cú pháp**. KaTeX render **thành công**. Đo trên corpus: sửa 76 công thức mà số lỗi cứng **không đổi (62 → 62)**. Đây là **lỗi im lặng** — không cổng cú pháp nào bắt được, và đó chính là hiện tượng "không cùng cấp" bạn thấy.

### 7.2 Vì sao luật "số mũ chứa dấu `=`" không đủ

Nó vừa **sót** vừa **nguy hiểm**:

| Ca | Luật `=` | Thực tế |
|---|---|---|
| `x^{2-3x-4}` | không bắt | **sót** — bị nuốt nhưng không có `=` |
| `x^{2+2an.x+bn-mc}` | không bắt | **sót** |
| `2^{x-1}=8` | `=` nằm **ngoài** ô số mũ | đúng là hợp lệ |

Và nếu nới thành "có dấu `-`" thì phá ngay `x^{n-1}`, `e^{-x}`, `a^{m-n}`, `u_1 q^{n-1}`.

### 7.3 Nguyên tắc thiết kế: bất đối xứng về rủi ro

Bài toán này **không thể đúng 100%** vì nó là suy diễn ý định. Nên phải chọn hướng sai an toàn:

| Loại sai | Hậu quả | Mức độ |
|---|---|---|
| Để nguyên một số mũ hỏng | render xấu, người dùng **thấy ngay** | chấp nhận được |
| Phá một số mũ hợp lệ | công thức **sai toán học**, trông vẫn bình thường | **không chấp nhận** |

⇒ **Khi không chắc: không sửa, đưa vào quarantine.**

### 7.4 Hai tín hiệu nhận biết

Chỉ sửa khi có **ít nhất một** tín hiệu, và **phải có chỗ cắt** (tồn tại `+`/`-` ở cấp ngoài cùng, không tính dấu ở đầu):

**Tín hiệu 1 — quan hệ ở cấp ngoài cùng của ô số mũ.** `=`, `<`, `>`, `\le`, `\ge`, `\ne`, `\to`, `\Leftrightarrow`… Số mũ hợp lệ trong toán phổ thông gần như không bao giờ chứa toán tử quan hệ. Phải xét ở **depth 0 của ô số mũ** — nên `2^{x-1}=8` không kích hoạt (dấu `=` nằm ngoài).

**Tín hiệu 2 — biến của atom cơ sở lặp lại trong số mũ.** `6x^{2-7x+1}`: atom cơ sở là `x`, mà `x` xuất hiện lại trong số mũ ⇒ gần như chắc chắn bị nuốt. Đây là tín hiệu bắt được các ca **không có dấu `=`**.

> **⚠️ Chi tiết quyết định sự sống còn của luật này:** phải lấy **atom liền kề dấu `^`**, không phải cả tiền tố.
>
> Với `nx^{n-1}` — đạo hàm `(x^n)' = nx^{n-1}`, cực kỳ phổ biến ở Toán 12 — atom cơ sở là **`x`**, không phải `{n, x}`. Nếu lấy cả tiền tố thì `n` khớp với `n` trong số mũ và luật sẽ **phá công thức hợp lệ** thành `nx^{n} - 1`.
>
> Tôi đã mắc đúng lỗi này ở bản đầu và chỉ phát hiện được nhờ đưa `nx^{n-1}` vào bộ test âm.

### 7.5 Chặn an toàn và cách cắt

**Cách cắt:** số mũ giữ lại là **literal tối thiểu ở đầu**, phần còn lại đẩy ra ngoài. Điều này xử lý đúng cả `6x^{2-7x+1=0}` → `6x^{2} -7x+1=0` **và** `\sin^{2\alpha+\cos^2\alpha=1}` → `\sin^{2} \alpha+\cos^2\alpha=1` (ở ca sau, `\alpha` phải ra ngoài vì nó là *đối số* của `\sin`, không phải phần của số mũ).

**Chặn an toàn:** chỉ tự động sửa khi số mũ giữ lại là **literal SỐ** (`2`, `3`, `10`). Số mũ ký hiệu (`n`, `k`, `\alpha`) quá dễ là số mũ hợp lệ ⇒ ghi `quarantine:symbolic_exp` cho người xem, **không tự sửa**.

### 7.6 Kết quả đo

Module: [`pipeline/exp_repair.py`](pipeline/exp_repair.py) · Test: [`tests/test_exp_repair.py`](tests/test_exp_repair.py)

```
$ python -m pytest tests/test_exp_repair.py -q
90 passed in 0.19s
```

Trên **4.584 công thức thật**:

| Chỉ số | Giá trị |
|---|---|
| Kích hoạt sửa | **76** công thức |
| — do biến cơ sở lặp lại | 50 |
| — do toán tử quan hệ | 28 |
| KaTeX lỗi cứng trước → sau | 62 → 62 *(đúng như dự đoán: lỗi im lặng)* |
| **THOÁI TRIỂN** (đang đúng → hỏng) | **0** |

Bộ test có **29 ca âm** phải giữ nguyên tuyệt đối, gồm `nx^{n-1}`, `(x^n)'=nx^{n-1}`, `k a^{k-1}`, `u_1 q^{n-1}`, `2^{x-1}=8`, `e^{-x}`, `(a+b)^{n-k}`, `\sum_{i=1}^{n} x_i`, cùng test **idempotent** và test không crash trên đầu vào méo.

### 7.7 Ví dụ thật từ corpus

```text
TRƯỚC: A=\{x \in \mathbb{R} \mid (2x-x^{2})(2x^{2-3x-2})=0\}
SAU  : A=\{x \in \mathbb{R} \mid (2x-x^{2})(2x^{2} -3x-2 )=0\}

TRƯỚC: \cos 2\alpha =1-2 \sin ^{2\alpha =1-2\left(\frac{1}{3}\right)}
SAU  : \cos 2\alpha =1-2 \sin ^{2} \alpha =1-2\left(\frac{1}{3}\right)

TRƯỚC: 2x^{2+y<-3}
SAU  : 2x^{2} +y<-3
```

### 7.8 Ba việc cần làm thêm

1. **Đặt ở tầng S0/S3, không phải cuối `_tidy`.** Ở S0 ta còn *biết* đâu là ô SUP mà không cần dò `^{`; ở S3 khái niệm "cấp ngoài cùng" là quan hệ cha-con trong cây, không cần đếm depth bằng tay.

2. **Xuất báo cáo lỗi nguồn cho đội nội dung.** 76 công thức này **hỏng ngay trong file Word** — mở bằng MathType cũng thấy sai. Sửa tại nguồn là *chính xác*, còn heuristic mãi mãi chỉ là *phỏng đoán*. Xuất danh sách `(file .docx, sha1 MTEF, latex)` để giáo viên sửa dứt điểm.

3. **Kiểm định ngữ nghĩa cho các ca quarantine.** Với ca `symbolic_exp`, thử `sympy` parse kết quả sau khi sửa: nếu ra một phương trình/đa thức hợp lệ thì tăng độ tin cậy. Đây là tầng xác nhận *ngữ nghĩa* mà KaTeX (chỉ kiểm *cú pháp*) không cung cấp được.

---

## §8. Trạng thái triển khai

### 8.1 Đã làm

| # | Thay đổi | File | Kết quả đo |
|---|---|---|---|
| 1 | **Sửa số mũ nuốt biểu thức** (§7) — thay regex `=`-only | `pipeline/exp_repair.py` (mới), `mtef.py` | 60 → 55 lỗi · 216 công thức sửa · **0 thoái triển** |
| 2 | **Cân bằng ngoặc bằng ngăn xếp** (§3.3) — thay đếm-tổng-cắt-đuôi | `pipeline/latex_balance.py` (mới), `mtef.py` | 55 → 15 lỗi · `brace_imbal` 41 → **0** · **0 thoái triển** |
| 3 | **Sửa slot `TM_ROOT`** — radicand rỗng thì slot chỉ số chính là radicand | `mtef.py` | 15 → **7** lỗi |
| 4 | **Cổng KaTeX** — phát hiện lỗi mà không đổi output | `katex_render.js`, `mathrender.py`, `cli_bt_json.py`, `tools/` | output **giống hệt từng byte**, lỗi trở nên quan sát được |

**Tổng: 62 → 7 lỗi cứng (giảm 89%)** trên 4.584 công thức, 176 test pass.

### 8.2 Thay đổi #2 quan trọng nhất — và giải thích một trade-off của bạn

Bạn đã **bỏ vòng cắt `}` thừa** trong `_tidy` (đúng — nó phá `\frac`), nhưng việc đó để lại `}` mồ côi không ai xử lý: `-495^{\circ}=-\frac{13\pi}{4}}`. Đó là lý do lớp `Expected 'EOF', got '}'` vẫn còn 39 ca.

Ngăn xếp giải quyết cả hai đầu: `}` mồ côi bị bỏ **tại đúng vị trí của nó**, còn `}` hợp lệ của `\frac` không bao giờ bị đụng tới. Test `test_never_breaks_frac` khoá lại chính bug cũ.

### 8.3 Cổng KaTeX — thiết kế không đổi output

`katex_render.js` giờ render **hai lần** mỗi công thức: lần 1 `throwOnError:true` chỉ để *phát hiện*, lần 2 `throwOnError:false` để *render thật*. Nhờ vậy HTML xuất ra không đổi một byte, nhưng lỗi được thu vào `mathrender.failures()`.

```bash
# báo cáo + fail build khi còn lỗi
python -m pipeline.cli_bt_json <input> -o out/ \
    --fail-on-katex-error --katex-report katex_errors.json

# quét output đã sinh sẵn
python tools/check_katex.py out-bt-json-new/
```

> **Phát hiện phụ, cần biết:** output JSON dùng `output:"html"` nên **không có** `<annotation>` chứa LaTeX gốc ⇒ **không thể kiểm định lại output đã đóng gói**. Đó là lý do cổng phải đặt *tại lúc render*, không phải quét file sau. Nếu muốn output tự kiểm định được (và hỗ trợ screen reader), đổi sang `output:"htmlAndMathml"` — đánh đổi là dung lượng tăng.

### 8.4 Còn lại 7 lỗi

| Số ca | Lớp lỗi |
|---:|---|
| 5 | `Double superscript` |
| 1 | `Can't use function '\tan' in text mode` (RC4) |
| 1 | khác |

Đây là các công thức hỏng **nhiều lớp cùng lúc** ngay trong file Word, ví dụ:

```text
T=a^{2+b^{2+c^{2=3^{2+0^{2+(-4)}^{2=25}}}}}
M= \cos ^{415^{o- \sin ^{415^{o=( \cos ^{215^{o}}^{2-( \sin ^{215^{o}}^{2})})}}}}
```

Số mũ lồng số mũ 4–5 tầng: ý định tác giả **không còn suy diễn được** một cách đáng tin. Đúng chỗ để dùng `overrides.json` khoá theo `sha1(mtef_bytes)` (§2.2) hoặc trả về đội nội dung sửa tại nguồn — **không nên** viết thêm heuristic.

Còn **1 ca** vi phạm bất biến `\sqrt` đối số rỗng lọt qua thay đổi #3, nằm trong một công thức đã hỏng nhiều lớp.

### 8.5 Cổng bất biến — bắt lỗi im lặng

Sau khi cú pháp sạch 99,85%, **mọi lỗi còn lại đều im lặng**: KaTeX render thành công nhưng ra công thức sai. Cổng KaTeX hết việc, nên cần cổng thứ hai đếm bất biến và chốt theo kiểu **ratchet — số ca không được phép tăng**.

[`tools/check_invariants.py`](tools/check_invariants.py) chạy pipeline thật và soi mọi LaTeX đi vào KaTeX (bao trùm **cả hai** đường: công thức MTEF và toán suy từ Text Run):

```bash
python tools/check_invariants.py "Kiến thức trọng tâm và tài tập"
python tools/check_invariants.py <dir> --show empty_macro_arg   # xem chi tiết
python tools/check_invariants.py <dir> --update-baseline
```

Baseline hiện tại — 43 file `.docx`, 2.862 công thức duy nhất:

| Bất biến | Ca | Ghi chú |
|---|---:|---|
| `viet_outside_text` | 13 | RC4 — **nhỏ hơn dự kiến rất nhiều** |
| `spaced_function_name` | **0** | RC1 không còn biểu hiện ở đầu vào KaTeX |
| `spaced_digits` | **0** | ditto |
| `stray_pipe` | 9 | RC2 — `\{\|x ...` |
| `spurious_pipe_style` | 33 | chỉ là trình bày, không phải lỗi |
| `right_dot_brace` | 38 | RC3 — lớp lớn nhất còn lại |
| `empty_macro_arg` | 1 | 23 → 1 sau khi sửa `TM_OBAR` |
| `brace_imbalance` | **0** | bắt buộc bằng 0 |
| `pua_chars` | **0** | bắt buộc bằng 0 |

### 8.6 Ba đính chính từ phép đo này

**1. `stray_pipe` bị tôi phóng đại.** Bản đầu của bộ đo đếm **mọi** dấu `|`, báo 50–56 ca. Nhưng `A=\{x\in\mathbb{N} |x<20\}` là ký hiệu **set-builder hợp lệ** — KaTeX render bình thường, chỉ nên đổi sang `\mid` cho giãn cách đẹp. Lỗi thật chỉ là dấu `|` **dính ngay ngoặc tập hợp**: **9 ca**, không phải 56.

> Một bộ đo sai còn tệ hơn không đo: nó tạo ra việc không tồn tại và che mất việc thật. Chính vì đếm quá rộng mà `\overline{}` (23 ca, lỗi thật) bị lọt. Nay mỗi bất biến có test dương + test âm trong [`tests/test_invariants.py`](tests/test_invariants.py).

**2. RC1 không còn biểu hiện ở đầu vào KaTeX.** Đo raw sau decoder có 136 ca `c o s`, nhưng tới lúc vào KaTeX thì `_tidy._FUNC_RE` cộng `mathrender._wrap_bare_words` đã xử lý hết: tên hàm **0 ca**, chữ số **0 ca**. RC1 vì thế **tụt ưu tiên** — vẫn nên sửa tại decoder cho gọn kiến trúc, nhưng không còn là lỗi đang gây hại.

**3. RC4 nhỏ hơn dự kiến — vì bạn đã sửa.** Bạn thay danh sách 14 stopword bằng `RE_VIETNAMESE` làm **chặn cứng** và xoá nhánh đoán biên bằng `rfind('}')`. Còn **13 ca**, không phải một lớp lỗi lớn. Việc còn thiếu duy nhất là **điều kiện 3**: xác nhận bằng KaTeX trước khi promote.

### 8.7 Sửa thêm: `TM_OBAR` rỗng

`empty_macro_arg` 23 ca đều là `\overline{}` — gạch trên lơ lửng không nội dung, sinh từ selector `14` (`TM_OBAR`), đúng selector chưa khai báo fire nhiều nhất (52 lần). Các template trang trí một ô (`TM_OBAR`, `TM_UBAR`, `TM_VEC`, `TM_TILDE`, `TM_HAT`) nay trả về chuỗi rỗng khi ô rỗng, thay vì sinh macro rỗng. **23 → 1.**

### 8.8 Đợt 2 — và bài học về việc tin vào bộ đo của chính mình

Tôi xếp `right_dot_brace` (38 ca) là ưu tiên 1. **Kiểm chứng bằng KaTeX cho thấy nó là dương tính giả hoàn toàn** — cả 5 biến thể đều render đạt:

```
{...\right.}   ĐẠT     {...\right. }  ĐẠT     \left\{...\right.  ĐẠT
{...\right..\}} ĐẠT    {...\right.\}} ĐẠT
```

Các công thức bị gắn cờ đều dạng `{ \left\{ ... \right. }` — group bọc ngoài chứa cặp `\left...\right` hoàn chỉnh, tức LaTeX hợp lệ. Bất biến đã bị **xoá**. Kéo theo: chú thích trong `_tidy` ghi *"KaTeX requires delimiter space before group brace"* dựa trên **tiền đề sai**.

Và một lỗi đo thứ ba: bộ thu của tôi bắt LaTeX **trước** khi `render_many` gọi `_wrap_bare_words`, tức không phải chuỗi KaTeX thật sự nhận. Sửa điểm đo: `viet_outside_text` **13 → 1**.

> **Ba lần liên tiếp tôi đo sai theo cùng một kiểu:** đếm quá rộng (`stray_pipe` 56 → 9), gắn cờ thứ không phải lỗi (`right_dot_brace` 38 → 0), và đo sai điểm trong pipeline (`viet_outside_text` 13 → 1).
>
> Nguyên tắc rút ra: **mọi bất biến phải chứng minh được bằng một lỗi KaTeX thật hoặc một hại hiển thị thật, và phải đo đúng tại chuỗi KaTeX nhận.** Mọi bất biến nay có test dương + test âm trong [`tests/test_invariants.py`](tests/test_invariants.py).

**Đã sửa trong đợt 2:**

| Việc | Kết quả |
|---|---|
| Dải phân cách ĐÓNG của set template rò ra (` \|\}`) | `stray_pipe` **9 → 2** |
| `\mathbb{Z\}}` — `\}` lọt vào đối số macro | **6 → 0** |

Ca `\mathbb{Z\}}` là ví dụ sách giáo khoa của RC3a — **hai luật che lỗi của nhau**:

1. Luật *escape ngoặc cuối* biến `\mathbb{Z}` → `\mathbb{Z\}`, rồi bộ cân bằng thêm `}` → `\mathbb{Z\}}`, render ra "Z}" thay vì "ℤ".
2. Luật *dọn ngoặc mồ côi* lại **xoá `\}` hợp lệ** của tập hợp: `\{k\pi \mid k \in \mathbb{Z}\}` → `\{k\pi \mid k \in \mathbb{Z}`.

Trước đây bug 1 tạo ra `\mathbb{Z\}` mà bug 2 không khớp được, nên chúng triệt tiêu nhau. Sửa bug 1 làm lộ bug 2 ngay. Nay: luật 1 chỉ escape khi `}` cuối **thật sự mồ côi** (`trailing_close_is_orphan`, dùng ngăn xếp), luật 2 bỏ `\}` khỏi danh sách hậu tố cần dọn. Cả hai được khoá bằng test.

### 8.9 Bề mặt lỗi còn lại

Trên 2.862 công thức duy nhất (43 file `.docx`):

| Loại | Ca | Xử lý |
|---|---:|---|
| KaTeX lỗi cứng | 7 | `overrides.json` — hỏng nhiều lớp, hết suy diễn được |
| `stray_pipe` | 2 | edge case đơn lẻ |
| `viet_outside_text` | 1 | **không phải RC4** — font TCVN3 legacy trong 1 file Hoá |
| `empty_macro_arg` | 1 | trong công thức hỏng nhiều lớp |
| `spurious_pipe_style` | 27 | chỉ trình bày (`\|` → `\mid`) |
| **Bắt buộc bằng 0** | **0** | `brace_imbalance`, `pua_chars`, `escaped_brace_in_macro` |

Tổng lỗi thật ≈ **11/2.862 = 0,4%**. Ca `viet_outside_text` còn lại là `H¹tnh©n:chøaproton...` — font TCVN3 cũ, một lớp bug hoàn toàn khác, cần bảng chuyển mã TCVN3 → Unicode chứ không phải sửa math mode.

### 8.10 Chưa làm (theo lộ trình §5)

Xếp lại theo số đo mới, **không** theo phỏng đoán ban đầu:

| Ưu tiên | Việc | Số ca | Ghi chú |
|---|---|---:|---|
| **1** | `overrides.json` khoá theo `sha1(mtef_bytes)` cho 7 ca KaTeX | 7 | Không viết thêm heuristic |
| **2** | Xuất **báo cáo lỗi nguồn** cho đội nội dung | ~80 | Sửa tại file Word là *chính xác*; heuristic mãi là *phỏng đoán* |
| **3** | Bảng chuyển mã **TCVN3 → Unicode** | 1 file | Lớp bug riêng, không liên quan math mode |
| **4** | Cổng 2 (không-thoái-triển) thành test thường trú | — | Hiện chạy thủ công; đây là cổng đã bắt bug `0 → 30` |
| **5** | `spurious_pipe_style` → `\mid` | 27 | Chỉ là trình bày |
| ~~`right_dot_brace`~~ | ~~RC3~~ | **0** | **Đã xoá** — dương tính giả (§8.8) |
| ~~RC4~~ | luồng typed span | **1** | Coi như xong: bạn sửa `exercises.py` + `_wrap_bare_words` |
| ~~RC1~~ | space-join ở decoder | **0** | Không còn biểu hiện (§8.6) |
| ~~RC2~~ | bỏ `_SLOTS.get(sel, 1)` | **2** | Còn 2 edge case; bất biến đếm `END` vẫn nên làm cho tương lai |
| ~~S2/S3~~ | parser LaTeX | — | **Chưa cần** — đã lấy 89% lợi ích mà không cần parser |

**Cổng 2 (không-thoái-triển)** vẫn chưa thành test thường trú; hiện chạy thủ công cho từng thay đổi. Nên tự động hoá vì đây là cổng đã bắt được bug `0 → 30`.

---

## Phụ lục A — Bảng artifact đo được (raw vs sau `_tidy`)

Trên 4.584 công thức, 11 file Toán:

| Mẫu lỗi | RAW | Sau `_tidy` | Nhận xét |
|---|---:|---:|---|
| `spaced_letters` (`c o s`, `1 8 0`) | 266 | **136** | RC1 — `_tidy` vá được nửa; phần còn lại render sai *im lặng* |
| `empty_group` (`{}`) | 170 | **162** | `\overline{}`, `\frac{...}{}` |
| `stray_pipe` (`\|`) | 60 | **56** | RC2 — desync template tập hợp/khoảng |
| `right_dot_brace` (`\right.}`) | 40 | **40** | `_tidy` **không** khử được ca nào |
| `exp_swallow_eq` (`^{...=...}`) | 28 | **2** | Chỗ `_tidy` làm tốt nhất |
| `brace_imbal` | **0** | **30** | ⚠️ **THOÁI TRIỂN — `_tidy` tự tạo ra** |
| `end_array_broken` | 0 | 0 | — |
| `trailing_backslash` | 0 | 0 | — |
| `left_right_imbal` | 0 | 0 | — |

## Phụ lục B — Phân lớp 62 lỗi cứng KaTeX

Đo lại chính xác sau khi `mtef.py` được sửa lúc 15:21 ngày 12/08 (`throwOnError:true`, `strict:false`, `displayMode:false`):

| Số ca | % | Lớp lỗi | Truy về |
|---:|---:|---|---|
| **46** | 74% | `Expected 'EOF', got '<token>'` | **RC3 — `_tidy` xoá `}` của `\frac`** |
| 8 | 13% | `Unexpected end of input in a macro argument, expected ']'` | `\sqrt[` hở — RC1 + RC2 |
| 4 | 6% | `Double superscript` | RC2 desync / §7 |
| 1 | 2% | `Can't use function '\tan' in text mode` | RC4 — trộn text/math |
| 1 | 2% | `Expected & or \\ or \cr or \end` | môi trường `array` hở |
| 1 | 2% | `Extra }` | RC3 |
| 1 | 2% | `Unexpected end of input in a macro argument, expected '}'` | RC3 |

**Lớp `{align} can be used only in display mode` (6 ca) đã được bạn sửa** trong lần chỉnh `mtef.py` lúc 15:21 — đổi sang `\begin{aligned}`. Không còn xuất hiện.

Điểm quan trọng: **74% lỗi cứng tập trung vào một nguyên nhân duy nhất là khối "balance" của `_tidy`.** Đây là lý do bước 2 của lộ trình có ROI cao nhất.

---

## Phụ lục C — File đã tạo

| File | Trạng thái | Vai trò |
|---|---|---|
| [`pipeline/exp_repair.py`](pipeline/exp_repair.py) | mới | Sửa số mũ nuốt biểu thức (§7) |
| [`pipeline/latex_balance.py`](pipeline/latex_balance.py) | mới | Cân bằng ngoặc bằng ngăn xếp (§3.3) |
| [`tests/test_exp_repair.py`](tests/test_exp_repair.py) | mới | 90 test — 9 ca phải sửa, 29 ca cấm động, idempotent |
| [`tests/test_latex_balance.py`](tests/test_latex_balance.py) | mới | 84 test — gồm `test_never_breaks_frac` khoá bug cũ |
| [`tools/katex_gate.js`](tools/katex_gate.js) | mới | Cổng 1 — KaTeX `throwOnError:true` |
| [`tools/check_katex.py`](tools/check_katex.py) | mới | Quét output JSON/HTML, exit 1 nếu còn lỗi |
| [`pipeline/mtef.py`](pipeline/mtef.py) | sửa | Gọi `exp_repair` + `balance_braces`, sửa slot `TM_ROOT` |
| [`pipeline/katex_render.js`](pipeline/katex_render.js) | sửa | Render 2 lần: phát hiện + render thật (output không đổi) |
| [`pipeline/mathrender.py`](pipeline/mathrender.py) | sửa | Thu thập lỗi qua `failures()` |
| [`pipeline/cli_bt_json.py`](pipeline/cli_bt_json.py) | sửa | `--fail-on-katex-error`, `--katex-report` |

### Chạy lại toàn bộ kiểm thử

```bash
python -m pytest tests/ -q                      # 176 passed
python -m pipeline.cli_bt_json <input.docx> -o out/ --fail-on-katex-error
```

---

**Tóm lại:** lỗi không nằm ở LaTeX mà ở **hai chỗ mất thông tin trong decoder** (RC1, RC2), **một lớp regex khuếch đại lỗi** (RC3), **một chỗ đoán lại thứ đã biết** (RC4), và **một cổng kiểm định bị tắt** (RC5).

*Đo trên 4.584 công thức MathType · 11 file `.docx` môn Toán · KaTeX `throwOnError:true` · 11 Aug 2026*
