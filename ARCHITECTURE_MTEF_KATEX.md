# MTEF → KaTeX: Chẩn đoán gốc rễ và Kiến trúc lại

> **Post-mortem kỹ thuật · pipeline `uni_convert` · 11 Aug 2026**
>
> Đo trên **4.584 công thức MathType thật** từ 11 file `.docx` Toán 10/11/12.
> Kết luận trung tâm: `_tidy()` không phải lớp sửa lỗi — nó là một lớp **gây** lỗi mới,
> và lỗi thật nằm ở tầng parser byte-stream phía trên nó.

| Chỉ số | Giá trị |
|---|---|
| Công thức đã decode | **4.584** |
| KaTeX lỗi cứng (`throwOnError:true`) | **77 — 1,7%** |
| Lệch ngoặc **do `_tidy` tạo ra** | **0 → 30** |
| Công thức bị `_tidy` sửa | **44,2%** (2.024) |
| Số dòng regex trong `_tidy` | **~450** |

Mọi con số đều tái lập được bằng harness ở [§4](#4-cổng-kiểm-thử-tự-động).

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

Hệ quả trên KaTeX là **lớp lỗi lớn nhất toàn corpus** — `Expected 'EOF', got '}'`, khoảng **28/77 ca (~36% tổng lỗi cứng)** đều truy về đúng cơ chế này.

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

Trong MTEF, ô con được phân định bởi record `END`. Nếu bảng khai 1 slot nhưng template thật có 3, thì slot thứ 2–3 cùng các `END` của chúng bị **cha** đọc mất → slot cha kết thúc sớm → phần dư trôi lên ông nội. Đây là **desync lan truyền**, và nó chính là cơ chế sinh ra hai triệu chứng bạn mô tả:

- **Số mũ nuốt biểu thức** — slot của `TM_SUP` mất `END` nên tiếp tục ăn record tới `END` xa hơn: `2x^{2-5x+3=0}`.
- **Ký tự `|` rò ra** — dải phân cách slot của template tập hợp/khoảng bị render thành ký tự thường: `\{|x \in \mathbb{R}|\}`. Đo được **60 công thức raw**, `_tidy` chỉ khử được 4 (còn **56**).

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

## Phụ lục B — Phân lớp 77 lỗi cứng KaTeX

| Số ca | Lớp lỗi | Truy về |
|---:|---|---|
| 20 | `Unexpected end of input in a macro argument` | `\sqrt[` hở — RC1 + RC2 |
| ~28 | `Expected 'EOF', got '}'` (nhiều vị trí) | **RC3 — `_tidy` xoá `}` của `\frac`** |
| 7 | `Got function '\left' with no arguments as subscript` | RC2 desync |
| 6 | `{align} can be used only in display mode` | Cấu hình — sửa thành `aligned` |
| 2 | `Undefined control sequence` | RC1 |
| 1 | `Can't use function '\tan' in text mode` | RC4 — trộn text/math |
| 13 | các lớp còn lại (đuôi phân bố) | — |

---

**Tóm lại:** lỗi không nằm ở LaTeX mà ở **hai chỗ mất thông tin trong decoder** (RC1, RC2), **một lớp regex khuếch đại lỗi** (RC3), **một chỗ đoán lại thứ đã biết** (RC4), và **một cổng kiểm định bị tắt** (RC5).

*Đo trên 4.584 công thức MathType · 11 file `.docx` môn Toán · KaTeX `throwOnError:true` · 11 Aug 2026*
