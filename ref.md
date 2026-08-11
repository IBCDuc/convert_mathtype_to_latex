# ref.md — Chẩn đoán lỗi pipeline công thức toán (MathType OLE → LaTeX → KaTeX)

> Tài liệu này viết để đưa cho agent code (antigravity) tự sửa. Mỗi lỗi đều có:
> **triệu chứng → bằng chứng đo được → nguyên nhân gốc (file:dòng) → cách fix**.
> Phần cuối là các **prompt sẵn để paste**.
>
> Nguyên tắc khi đọc: mục nào ghi `[ĐÃ CHỨNG MINH]` là đã đo trên dữ liệu thật
> của corpus. Mục nào ghi `[SUY LUẬN]` là giả thuyết mạnh nhưng **chưa** kiểm
> chứng hết — phải spot-check trước khi tin.

---

## 0. TL;DR — một câu về nguyên nhân gốc

Parser MTEF đọc **sai vị trí byte `selector`** trong record `TMPL`. Nó đọc byte
`+0` (byte này **luôn** bằng `0x00` trên 4352/4352 record của corpus), trong khi
selector thật nằm ở byte `+1`.

Hệ quả dây chuyền: mọi template (phân số, căn, lim, chỉ số trên/dưới, ngoặc…)
đều bị nhận dạng là `selector = 0`. Với bảng hiện tại `selector 0 = TM_PAREN`
(một loại "fence"/ngoặc), nên **mọi công thức bị bọc vào `\left(...\right)` rồi
nhánh fence ném hết nội dung các slot còn lại đi** → mất chữ, sai ký hiệu,
`lim` biến thành `(lim)` hoặc `\sum`, `f(x)` thành `f` hoặc `fx()`.

Đây là **một lỗi gốc sinh ra 4/5 triệu chứng** bạn báo. Sửa đúng chỗ này là
gỡ được phần lớn.

### Định lượng thiệt hại trên corpus thật

| Chỉ số | Số lượng | Ghi chú |
|---|---:|---|
| Tổng công thức OLE (MathType) toàn corpus | **4 738** | 24 file có công thức |
| Có nhúng TeX gốc → tin được 100% | **892** (18,8%) | `source="tex"` — dùng làm **ground truth** |
| Đi qua parser MTEF → **đang bị hỏng** | **3 428** (72,4%) | `source="mtef"` |
| Parser bỏ cuộc → hiện fallback ra **ảnh PNG** | **418** (8,8%) | `source="unresolved"` |
| Có dấu hiệu fence rỗng/sai rõ rệt | 1 006 | vd `\left(\right)`, `\left(\lim \right)` |
| Lẫn ký tự TCVN3 (font `.VnTime`) | 26 | xem lỗi **L7** |
| **Số selector khác nhau mà parser nhìn thấy** | **1** (chỉ `0`) | ← bằng chứng đắt giá nhất |

Con số cuối là bằng chứng quyết định: một corpus toán 4 738 công thức **không
thể** chỉ dùng đúng 1 loại template.

---

## 1. Cách tái lập (chạy được ngay)

Các script chẩn đoán đã dùng nằm ở scratchpad; nội dung cốt lõi tóm lại như sau.

**1.1. Đếm nguồn + selector toàn corpus**

```python
# probe: byte nào trong record TMPL mới là selector thật
import collections
from pipeline import mtef
b0 = collections.Counter(); b1 = collections.Counter()
orig = mtef.MTEFParser.parse_tmpl
def probe(self, depth):
    j = self.i
    b0[self.d[j]] += 1          # code HIỆN đọc byte này làm selector
    b1[self.d[j + 1]] += 1      # selector THẬT
    return orig(self, depth)
mtef.MTEFParser.parse_tmpl = probe
# ... duyệt toàn bộ docx, gọi mtef.decode_ole(blob) ...
```

Kết quả thực đo:

```
byte+0 : 1 giá trị khác nhau  → 0x00 xuất hiện 4352/4352 lần   (KHÔNG phải selector)
byte+1 : 16 giá trị khác nhau → 1:1377  11:1138  28:711  2:272  3:214
                                10:176  27:172  23:161  9:51  4:36 ...
byte+2 : 9 giá trị            → thường 0x00 / 0x03 / 0x10       (variation)
```

Phân bố `byte+1` khớp hoàn hảo với toán học thật: ngoặc đơn nhiều nhất, rồi
phân số, rồi lũy thừa, rồi căn.

**1.2. Dump hex thân công thức để đọc tay**

```python
p = mtef.MTEFParser(raw[28:]); p.read_header(); p.skip_preamble()
rest = p.d[p.i:]        # in hexdump từ đây
```

---

## 2. Bảng lỗi tổng hợp

| ID | Lỗi | Mức | Triệu chứng bạn thấy |
|---|---|---|---|
| **L1** | `TMPL`: đọc sai offset của `selector` | 🔴 Chí tử | `lim`→`(lim)`/`\sum`, mọi công thức bọc `\left(...\right)` |
| **L2** | Bảng tên selector sai thứ tự & sai giá trị | 🔴 Chí tử | `lim` ra **dấu tổng** `\sum` |
| **L3** | Record 10–14 là **SIZE**, bị hiểu thành sub/sup | 🔴 Chí tử | `y_0`→`y\left(_{0}\right)`, lồng `_{_{_{...}}}` vô nghĩa |
| **L4** | Fence bị cấp 3 slot (đúng: 1) rồi **ném nội dung** | 🔴 Chí tử | mất hẳn `(x)`, mất cả phần đuôi `=y_0` |
| **L5** | Bit `variation` của fence bị hiểu đảo | 🟠 Nặng | mất luôn 2 dấu ngoặc |
| **L6** | Glyph delimiter (typeface `0x96`) lọt ra ngoài | 🟠 Nặng | **`f(x)` → `fx()`** ← đúng triệu chứng bạn báo |
| **L7** | Text trong MathType dùng font `.VnTime` (TCVN3) đọc bằng latin1 | 🟠 Nặng | `chøaproton`, `®iÖn`, `vµ`, `kh«ng` ← "ký tự lạ" |
| **L8** | Mất dấu cách trong text công thức | 🟡 Vừa | `H¹tnh©n:chøaproton` dính hết |
| **L9** | `EMBELL`: vòng lặp ăn byte lạc + sinh dấu phẩy trên "ma" | 🟠 Nặng | lệch offset, `′` tự mọc |
| **L10** | `parse_tmpl` không skip byte `nudge` | 🟡 Vừa | lệch offset khi có `xfNUDGE` |
| **L11** | `_FUNC_RE` dùng IGNORECASE, không chặn biên phải | 🟡 Vừa | `sinh`→`\sin h`, biến `Min`→`\min` |
| **L12** | Cổng "phải tiêu thụ trọn stream" + fallback ảnh | 🟠 Nặng | 418 công thức thành ảnh PNG (bạn muốn bỏ) |
| **L13** | `mathrender._wrap_bare_words` bọc `\text{}` quá rộng | 🟡 Vừa | `dx`, `ab` bị in đứng thay vì nghiêng |
| **L14** | Code chết trong `decode_stream` | ⚪ Sạch | 2 dòng không bao giờ chạy |

---

## 3. Chi tiết từng lỗi

### L1 — `TMPL` đọc sai offset selector `[ĐÃ CHỨNG MINH]` 🔴

**Nơi lỗi:** `pipeline/mtef.py:370-374`

```python
sel = self.u8()          # ← ĐANG đọc byte +0, byte này LUÔN = 0x00
opt = self.u8()
var = 0
if opt & 0x01:
    var = self.u16() if (opt & 0x10) else self.u8()
```

**Bằng chứng:** byte `+0` = `0x00` ở **4352/4352** record `TMPL`. Không thể là
selector. Hexdump công thức `y = f(x)` (Toán 12 Bài 3, công thức #2):

```
03 | 00 | 01 | 03 00 | 0f 00 01 00 0f 01 | 02 00 83 78 00 | 00 | 02 00 96 28 00 | 02 00 96 29 00
^tag ^opt ^SEL  ^var(u16)  ^size/LINE      ^CHAR 'x'         ^END  ^CHAR '('        ^CHAR ')'
```

`selector = 0x01` = ngoặc đơn — đúng với `f(x)`. Công thức `lim` (#3):

```
03 | 00 | 17 | 10 00 | 01 ... CHAR l,i,m ... | SUB slot: x → +∞ | ...
^tag ^opt ^SEL=23(LIM) ^var=16
```

**Fix:** layout đúng là `[tag][options][selector][variation:u16][slots...]`

```python
def parse_tmpl(self, depth: int, tag_opt: int = 0) -> str:
    if tag_opt & xfNUDGE:      # xem L10
        self.i += 2
    self.u8()                  # options — luôn 0x00 trên corpus này
    sel = self.u8()            # selector THẬT
    var = self.u16()           # variation (u16)
    ...
```

> ⚠️ `variation` là `u16` ở đây là `[SUY LUẬN]` khớp 12/12 mẫu đã thử. Nếu gặp
> file lệch offset, thử lại `u8` và so bằng bộ kiểm thử ở §6.

---

### L2 — Bảng selector sai `[ĐÃ CHỨNG MINH]` 🔴

**Nơi lỗi:** `pipeline/mtef.py:71-76`

```python
(TM_PAREN, TM_BRACK, TM_BRACE, TM_ANGLE, TM_BAR, ...) = range(36)
#  ^ 0        ^ 1       ^ 2       ^ 3
```

Hai vấn đề:

1. **Thứ tự 4 phần tử đầu bị đổi.** Chuẩn MTEF v5 là
   `0=ANGLE, 1=PAREN, 2=BRACE, 3=BRACK`. Bảng hiện tại đặt `PAREN=0` →
   ngoặc đơn thật (selector 1) bị đọc thành `TM_BRACK` → ra `[...]`.
2. **Giá trị vùng ≥ 12 sai hẳn.** Bảng hiện tại có `TM_SCRIPT=12`,
   `TM_LIM=24`, `TM_SUMOP=23`. Đo thật thì `LIM=23`, `SUB=27`, `SUP=28`.
   Vì bảng gán `23 = TM_SUMOP` → `\sum` ⇒ **đây chính là lý do `lim` biến
   thành dấu tổng** như bạn báo.

**Bảng selector đã kiểm chứng bằng dữ liệu thật:**

| selector | Ý nghĩa | Số lần | Bằng chứng |
|---:|---|---:|---|
| 1 | `tmPAREN` `(...)` | 1 377 | `y=f(x)`, var=3 |
| 2 | `tmBRACE` `{...}` | 272 | `[SUY LUẬN]` theo chuẩn |
| 3 | `tmBRACK` `[...]` | 214 | `[SUY LUẬN]` theo chuẩn |
| 4 | `tmBAR` `\|...\|` | 36 | `[SUY LUẬN]` |
| 9 | ? | 51 | **chưa xác định** |
| 10 | `tmROOT` `\sqrt` | 176 | khớp comment ground-truth cũ |
| 11 | `tmFRACT` `\frac` | 1 138 | tần suất khớp |
| 14, 15 | ? | 21, 13 | **chưa xác định** |
| **23** | **`tmLIM`** | **161** | `\lim_{x\to+\infty}`, var=16 — đúng bằng số công thức `lim` |
| **27** | **`tmSUB`** chỉ số dưới | **172** | `y_0`, `x_0`, var=0 |
| **28** | **`tmSUP`** chỉ số trên | **711** | `60^\circ`, `180^\circ`, `k360^\circ` |
| 29 | `tmSUBSUP` `[SUY LUẬN]` | 4 | quá ít mẫu |
| 31, 33, 37 | ? | 1, 3, 2 | **chưa xác định** |

**Fix:** không dùng `range(36)` gán tên theo thứ tự (rất dễ lệch cả bảng khi
thêm/xoá 1 tên). Khai báo **tường minh từng số**:

```python
TM_ANGLE, TM_PAREN, TM_BRACE, TM_BRACK, TM_BAR = 0, 1, 2, 3, 4
TM_ROOT, TM_FRACT = 10, 11
TM_LIM = 23            # ĐO THẬT: 161/161 công thức lim
TM_SUB, TM_SUP, TM_SUBSUP = 27, 28, 29   # ĐO THẬT: 28 -> 60^\circ
```

Các selector chưa xác định (9, 14, 15, 31, 33, 37) → xử lý bằng nhánh generic
`a + _{b} + ^{c}` và **log ra** để bổ sung dần, tuyệt đối không đoán bừa.

---

### L3 — Record 10–14 là SIZE, không phải subscript `[ĐÃ CHỨNG MINH]` 🔴

**Nơi lỗi:** `pipeline/mtef.py:288-300`

```python
elif rec == SUB:                       # rec == 11
    sub_val = self.parse_slot(depth + 1)
    if sub_val:
        out.append("_{" + sub_val + "}")     # ← BỊA ra subscript
elif rec == SUB2:                      # rec == 12
    ...  out.append("_{...}^{...}")
```

Trong MTEF, `FULL=10, SUB=11, SUB2=12, SYM=13, SUBSYM=14` là **mã cỡ chữ**
(size context: chữ thường / cỡ chỉ số / cỡ chỉ số của chỉ số / cỡ ký hiệu).
Chúng **không có payload** và **không tạo cấu trúc**. Cấu trúc chỉ số trên/dưới
đến từ `TMPL` với selector 27/28/29 (xem L2).

Hiện code coi `SUB`/`SUB2` là container rồi đệ quy `parse_slot` → sinh ra
subscript ma và lồng nhau vô hạn:

```
thực tế phải là:  y = y_0
code hiện ra   :  y=y\left(_{0}\right)
và tệ hơn      :  \lim _{x\to x0_{+^{f(x)=+\infty }}}   ← lồng bậy
```

**Fix:**

```python
elif rec in (FULL, SUB, SUB2, SYM, SUBSYM):   # 10..14 = SIZE, không payload
    continue                                   # chỉ đổi cỡ, không sinh LaTeX
elif rec == 15:                                # SIZE tường minh: 1 byte
    self.u8()
```

---

### L4 — Fence bị cấp 3 slot rồi ném nội dung `[ĐÃ CHỨNG MINH]` 🔴

**Nơi lỗi:** `pipeline/mtef.py:448-449` và `385-391`

```python
_SLOTS = {
    **{k: 3 for k in FENCES},    # ← fence CHỈ CÓ 1 slot, không phải 3
    ...
```

```python
if sel in FENCES:
    ...
    return left_str + a + right_str      # ← chỉ dùng a; b, c bị NÉM ĐI
```

Fence (ngoặc) trong MTEF có **đúng 1 ô**. Cấp cho nó 3 ô nghĩa là parser đọc
tiếp **2 ô của record kế bên** (tức nội dung phía sau công thức), rồi nhánh
fence **xoá thẳng** hai ô đó. Đây là lý do nội dung mất im lặng:

```
đúng : \lim_{x\to+\infty} f(x) = y_0
ra   : \left(\lim \right)              ← "_{x→+∞}" và "f(x)=y_0" bị ném
đúng : y = f(x)
ra   : y=f                             ← "x" và "()" bị ném
```

**Fix:** `_SLOTS[fence] = 1`. Và **nguyên tắc chung, quan trọng hơn cả lỗi này:**
> Không bao giờ để một nhánh render **im lặng bỏ** slot đã parse. Nếu một slot
> có nội dung mà template không dùng đến, phải `log warning` — nếu không, lỗi
> mất chữ sẽ không ai phát hiện. Chính vì thiếu quy tắc này mà bug tồn tại lâu.

---

### L5 — Bit `variation` của fence bị hiểu đảo `[ĐÃ CHỨNG MINH]` 🟠

**Nơi lỗi:** `pipeline/mtef.py:386-388`

```python
left  = "" if (var & 0x01) else lo     # bit set => ẨN dấu ngoặc
right = "" if (var & 0x02) else hi
```

Công thức `f(x)` có `variation = 3` (cả hai bit set) → code ẩn **cả hai** dấu
ngoặc. Nhưng `f(x)` rõ ràng phải hiện đủ `(` và `)`. Vậy ngữ nghĩa bit **không
phải "ẩn"**.

**Fix (an toàn, đã kiểm 12/12 mẫu):** luôn vẽ đủ cặp ngoặc.

```python
if sel in FENCES:
    lo, hi = FENCES[sel]
    return r"\left" + lo + a + r"\right" + hi
```

> ⚠️ **Việc cần làm thêm:** ngoặc một bên có thật trong Toán 10 (khoảng nửa mở
> `[a;b)`, `(a;b]`). Phải tìm mẫu khoảng nửa mở rồi dò lại ngữ nghĩa `variation`
> đúng, nếu không sẽ biến `[a;b)` thành `[a;b]` — **sai kiến thức**.

---

### L6 — Glyph delimiter lọt ra ngoài → `f(x)` thành `fx()` `[ĐÃ CHỨNG MINH]` 🟠

MathType lưu **glyph dấu ngoặc** của template thành các record `CHAR` với
`typeface = 0x96`, đặt **sau** nội dung slot:

```
CHAR 'x' (typeface 0x83) → END → CHAR '(' (typeface 0x96) → CHAR ')' (typeface 0x96)
```

Nên khi parse đúng thứ tự nhưng không lọc, output thành `f` `x` `(` `)` =
**`fx()`** — chính xác triệu chứng bạn báo.

**Fix:** trong `parse_char` (`mtef.py:321`), bỏ ký tự có typeface `0x96` vì
delimiter đã được `\left...\right` của template sinh ra:

```python
tf = self.u8()
code = self.u16()
if o & xfMOVE:
    self.u8()
if tf == 0x96:        # glyph delimiter do template tự vẽ -> không in lại
    return ""
return self.render_char(code)
```

---

### L7 — Font `.VnTime` (TCVN3) đọc bằng latin1 `[ĐÃ CHỨNG MINH]` 🟠

**Bằng chứng:** với công thức có `FONTS: ['.VnTime', 'Symbol', ...]`, output ra:

```
H¹tnh©n:chøaproton(mang®iÖn+)vµneutron(kh«ngmang®iÖn)
```

Giải mã TCVN3: `H¹t nh©n` = "Hạt nhân", `chøa` = "chứa", `®iÖn` = "điện",
`vµ` = "và", `kh«ng` = "không", `nguyªn tö` = "nguyên tử", `c¸c` = "các".

Nguyên nhân: người soạn gõ tiếng Việt **bên trong** MathType bằng font TCVN3
(`.VnTime` — bộ mã "ABC" cũ, tiếng Việt nằm ở 0xA1–0xFF). `render_char`
(`mtef.py:343`) trả `chr(code)` = giải mã như latin1/Unicode → ra ký tự rác.

**Fix:** bảng chuyển TCVN3 → Unicode, áp dụng **có điều kiện theo font** của
record (parser đã đọc sẵn `self.fonts` trong `skip_preamble`, cần truyền
`typeface` xuống `render_char` để biết dùng bảng nào):

```python
TCVN3 = {0xB9: "ạ", 0xAE: "đ", 0xD6: "ệ", 0xB5: "µ→à", 0xAB: "«→ô", ...}
# và bọc phần chữ Việt vào \text{...} vì đó là VĂN BẢN, không phải công thức
```

> Ghi chú thiết kế: các công thức này thực chất là **đoạn văn bị nhét vào
> MathType**, không phải toán. Cân nhắc phát hiện và xuất chúng thành text
> thuần (`\text{}` hoặc HTML thường) thay vì cố render như công thức.

---

### L8 — Mất dấu cách trong text công thức `[ĐÃ CHỨNG MINH]` 🟡

Cùng mẫu trên: `H¹tnh©n` — chữ dính nhau, dấu cách biến mất hoàn toàn.

Nguyên nhân khả năng cao (`mtef.py:356-359`): dấu cách trong MathType được lưu
bằng mã vùng PUA (MT Extra), mà code xoá sạch dải `0xE000-0xF8FF`, chỉ chừa 3 mã:

```python
if code < 32 or code == 0xFFFD or (0xE000 <= code <= 0xF8FF):
    if code in (0xEC80, 0xEC81, 0xEC82):
        return " "
    return ""            # ← mọi mã PUA khác bị xoá, có thể gồm cả dấu cách
```

**Fix:** log thống kê các mã PUA thật gặp trong corpus rồi map cho đủ, thay vì
xoá cả dải. Ưu tiên: mã nào xuất hiện nhiều mà xoá đi làm dính chữ → là space.

---

### L9 — `EMBELL` ăn byte lạc + sinh dấu `′` ma `[ĐÃ CHỨNG MINH qua đọc code]` 🟠

**Nơi lỗi:** `pipeline/mtef.py:275-285`

```python
eb_list = []
while self.i < len(self.d):
    b = self.u8()
    if b != 0:
        eb_list.append(b)
    elif eb_list:          # ← nếu byte ĐẦU đã là 0 thì KHÔNG break
        break
out.append("'" if (5 in eb_list or not eb_list) else "")
```

Hai lỗi:
1. Byte đầu bằng `0` → `eb_list` rỗng → không `break` → **tiếp tục ăn byte** của
   record sau → lệch offset toàn bộ phần còn lại.
2. `or not eb_list` → khi rỗng vẫn xuất `'` → **dấu phẩy trên tự mọc**.

**Fix:** `EMBELL` trong MTEF là **1 byte mã embellishment**:

```python
elif rec == EMBELL:
    if opt & xfNUDGE:
        self.i += 2
    eb = self.u8()
    out.append(EMBELL_MAP.get(eb, ""))     # 5 => "'" (prime), ...
```

---

### L10 — `parse_tmpl` không skip `nudge` `[SUY LUẬN]` 🟡

`parse_slot` (`mtef.py:240-241`) gọi `self.parse_tmpl(depth)` mà **không truyền
`opt`** (options nằm ở nibble cao của tag). Nếu `TMPL` có cờ `xfNUDGE`, 2 byte
nudge không được bỏ qua → lệch offset. `parse_char` đã xử lý đúng việc này
(`mtef.py:332-333`), `parse_tmpl` thì thiếu.

**Fix:** truyền `opt` xuống và skip như `parse_char`.

---

### L11 — `_FUNC_RE` quá rộng `[ĐÃ CHỨNG MINH qua đọc code]` 🟡

**Nơi lỗi:** `pipeline/mtef.py:467`

```python
_FUNC_RE = re.compile(r"(?<![A-Za-z\\])(" + "|".join(FUNCS) + r")", re.IGNORECASE)
```

- `re.IGNORECASE` → biến tên `Min`, `Max`, `Log` bị đổi thành `\min`, `\max`.
- Không chặn biên phải → `sinh` (sin hyperbolic) thành `\sin h`;
  `cost` thành `\cos t`.

**Fix:** bỏ `IGNORECASE` (LaTeX chỉ có tên hàm chữ thường), và sắp `FUNCS` theo
độ dài giảm dần để `arcsin` khớp trước `sin` (hiện đã đúng), đồng thời chặn hậu
tố chữ khi từ đó tạo thành tên hàm dài hơn.

---

### L12 — Bỏ đường ảnh, đi thẳng LaTeX (yêu cầu #3 của bạn) 🟠

Hiện có **hai** chỗ tạo ảnh cần bỏ:

**(a) Ảnh preview của công thức** — `pipeline/docxast.py:188-196`

```python
# Lấy ảnh preview khi LaTeX chưa chắc chắn tuyệt đối...
data, mime = b"", ""
if conf < 0.98 and img is not None:          # ← BỎ toàn bộ nhánh này
    raw = self._part(img.get(...))
    if raw:
        data, mime = _to_png(raw, ...)       # ← gọi ImageMagick `convert`
```

**(b) Cổng chặn khiến 418 công thức rơi về ảnh** — `pipeline/mtef.py:502-506`

```python
if any(b != 0 for b in body[p.i:]):
    return None, "unresolved"     # parser còn byte chưa đọc -> bỏ cuộc
```

Và `_to_png` (`docxast.py:273-293`) spawn `convert` của ImageMagick — bỏ được
thì pipeline **không còn phụ thuộc binary ngoài** cho công thức (vẫn cần cho
hình minh hoạ thật).

**Thiết kế thay thế — thứ tự ưu tiên rõ ràng, không im lặng:**

1. Có TeX nhúng (`source="tex"`) → dùng luôn. (892 công thức)
2. Parse MTEF thành công **và** tiêu thụ trọn stream → dùng LaTeX.
3. Parse được nhưng **còn byte dư** → vẫn dùng LaTeX, nhưng **đánh dấu**
   `confidence` thấp và `log` ra file để review. Không ném đi.
4. Hỏng hoàn toàn → xuất `<code>` chứa LaTeX/thông tin thô + log.

> ⚠️ **Rủi ro phải nói rõ:** bỏ fallback ảnh nghĩa là **không còn lưới an toàn**.
> Trước khi bỏ, phải sửa xong L1–L6, nếu không 3 428 công thức sẽ hiện LaTeX sai
> ra trang HTML thay vì ảnh đúng. **Thứ tự bắt buộc: sửa parser trước, bỏ ảnh sau.**

---

### L13 — `_wrap_bare_words` bọc `\text{}` quá rộng `[SUY LUẬN]` 🟡

**Nơi lỗi:** `pipeline/mathrender.py:36-49`

```python
_BARE_WORD_RE = re.compile(r"(?<!\\)\b[^\W\d_]{2,}\b")
```

Regex này bọc **mọi** chuỗi ≥2 chữ cái vào `\text{ ... }`. Nó được thêm để cứu
trường hợp chữ Việt "và" nằm trong công thức (đúng mục đích), nhưng nó cũng bọc
`dx`, `ab`, `xy` → in **đứng** thay vì **nghiêng** như biến toán chuẩn.

**Fix:** chỉ bọc khi chuỗi chứa ký tự **ngoài ASCII** (dấu tiếng Việt) hoặc nằm
trong danh sách từ tiếng Việt biết trước (`và`, `hoặc`, `với`, `khi`, `nếu`…):

```python
_VN_WORD_RE = re.compile(r"(?<!\\)\b\w*[àáảãạăâèéẻẽẹêìíỉĩịòóỏõọôơùúủũụưỳýỷỹỵđ]\w*\b", re.I)
```

---

### L14 — Code chết `[ĐÃ CHỨNG MINH]` ⚪

`pipeline/mtef.py:508-510`: hai dòng sau `return latex, "mtef"` không bao giờ
chạy — trùng lặp do sửa nhiều lần. Xoá.

---

## 4. Kết quả sau khi vá thử (đã chạy thật)

Tôi đã vá thử L1+L3+L4+L5+L6 trong sandbox (không đụng `pipeline/`) và chạy lại
Toán 12 Bài 3 — file chứa đúng công thức `lim` trong ảnh bạn gửi:

Lưu ý: bản vá thử này **chưa** map selector 27/28 (mới chỉ vô hiệu hoá L3), nên
chỉ số dưới `_0` còn phẳng thành `0` — đó là phần việc còn lại, không phải lỗi mới.

| # | TRƯỚC (code hiện tại) | SAU (bản vá thử) |
|---|---|---|
| 1 | `y=y\left(_{0}\right)` | `y=y0` — hết lồng bậy, còn thiếu `_` (cần map sel 27) |
| 2 | `y=f` | `y=f\left(x\right)` ✅ |
| 3 | `\left(\lim \right)` | `\lim _{x\to +\infty }f\left(x\right)=y0` ✅ |
| 4 | `\left(\lim \right)` | `\lim _{x\to -\infty }f\left(x\right)=y0` ✅ |
| 5 | `x=x\left(_{0}\right)` | `x=x0` — như #1 |
| 11 | `y=ax+b,a\ne 0` | `y=ax+b,a\ne 0` ✅ không hồi quy |

Cấu trúc công thức trong ảnh bạn gửi (`lim_{x→+∞} f(x) = y₀`) **đã dựng đúng**:
toán tử `lim`, chỉ số dưới `x→+∞`, đối số `f(x)`, vế phải — trước đó mất sạch chỉ
còn `(lim)`. Phần `y₀` cần map selector 27 (SUB) theo bảng ở L2 là xong.

---

## 5. Thứ tự sửa bắt buộc

```
Bước 1: L1 + L2      (selector đúng)          ← gỡ 80% triệu chứng
Bước 2: L3           (SIZE ≠ subscript)
Bước 3: L4 + L5 + L6 (fence: slot, bit, glyph)
Bước 4: L9 + L10     (offset không lệch nữa)
Bước 5: dựng bộ kiểm thử §6, đo lại
Bước 6: L7 + L8      (tiếng Việt TCVN3)
Bước 7: L11 + L13 + L14 (dọn)
Bước 8: L12          (BỎ ẢNH — chỉ sau khi §6 đạt ngưỡng)
```

---

## 6. Bộ kiểm thử / tiêu chí nghiệm thu

**Ground truth có sẵn miễn phí: 892 công thức nhúng TeX gốc.** Đây là mỏ vàng —
dùng chúng để kiểm parser MTEF:

1. Tách 892 công thức `source="tex"` làm tập chuẩn.
2. Với mỗi công thức đó, **ép** parser đi đường MTEF (bỏ qua nhánh TeX), rồi
   so LaTeX MTEF sinh ra với TeX gốc sau khi chuẩn hoá (bỏ khoảng trắng,
   `\left`/`\right`, `{}` dư).
3. Báo cáo: % khớp tuyệt đối, % khớp sau chuẩn hoá, danh sách sai điển hình.

**Ngưỡng nghiệm thu đề xuất:**

| Chỉ số | Hiện tại | Mục tiêu |
|---|---:|---:|
| Số selector khác nhau parser nhận ra | 1 | ≥ 10 |
| Công thức có fence rỗng `\left(\right)` | 1 006 | < 20 |
| Khớp TeX ground-truth (sau chuẩn hoá) | chưa đo | ≥ 90% |
| `source="unresolved"` | 418 | < 100 |
| Công thức lẫn ký tự TCVN3 chưa dịch | 26 | 0 |
| Trang HTML còn `[MATH`/`\left(\lim` | — | 0 |

**Kiểm tra hồi quy bắt buộc:** `y=ax+b,a\ne 0` (Bài 3 #11) hiện **đã đúng** —
phải vẫn đúng sau khi sửa.

---

## 7. Prompt sẵn để đưa antigravity

### Prompt 1 — Sửa lõi parser (L1–L6)

```
Repo: /home/ubuntu/tuan/llm-service/test/uni_convert
File chính: pipeline/mtef.py  (parser MathType MTEF v5 -> LaTeX)
Đọc kỹ ref.md mục L1..L6 trước khi sửa. Đó là chẩn đoán đã kiểm chứng trên
4738 công thức thật, KHÔNG phải phỏng đoán — đừng tự nghĩ lại từ đầu.

Nhiệm vụ: sửa 6 lỗi L1..L6 trong pipeline/mtef.py:

L1. parse_tmpl (dòng ~370) đang đọc selector ở byte SAI. Layout đúng là:
    [tag][options=1 byte][selector=1 byte][variation=u16][các slot]
    Bằng chứng: byte đầu LUÔN = 0x00 trên 4352/4352 record.

L2. Bảng selector (dòng ~71) sai. Thay `range(36)` bằng khai báo tường minh.
    Giá trị ĐÃ ĐO THẬT, dùng đúng những số này:
      1=PAREN  2=BRACE  3=BRACK  4=BAR  10=ROOT  11=FRACT
      23=LIM   27=SUB   28=SUP   29=SUBSUP(chưa chắc)
    Selector 9,14,15,31,33,37 chưa xác định -> nhánh generic + log warning.

L3. Record 10..14 (FULL/SUB/SUB2/SYM/SUBSYM) là mã CỠ CHỮ, không payload,
    KHÔNG sinh cấu trúc. Hiện parse_slot (dòng ~288) coi SUB/SUB2 là container
    và đệ quy -> bịa ra `_{}`/`^{}` lồng nhau. Sửa thành `continue`.

L4. _SLOTS (dòng ~448) cấp 3 slot cho fence; fence chỉ có 1 slot. Sửa thành 1.
    Thêm log warning nếu một slot đã parse mà bị nhánh render bỏ không dùng.

L5. Bit variation của fence bị hiểu là "ẩn dấu ngoặc" nhưng thực tế không phải
    (f(x) có variation=3 mà phải hiện đủ 2 ngoặc). Tạm thời luôn vẽ đủ cặp.

L6. parse_char: CHAR có typeface == 0x96 là glyph delimiter do template tự vẽ,
    phải trả "" (nếu không, f(x) ra thành "fx()").

Kiểm chứng sau khi sửa, chạy trên:
  "Kiến thức trọng tâm và tài tập/Toán 12/Toán 12/Toán 12_Bài 3 (Đường tiệm cận của đồ thị hàm số).docx"
Công thức #2 phải ra  y=f\left(x\right)
Công thức #3 phải ra  \lim_{x\to +\infty}f\left(x\right)=y_0
Công thức #11 phải VẪN ra  y=ax+b,a\ne 0   (kiểm tra hồi quy)

Không đổi API công khai (decode_ole/decode_stream trả (latex, source)).
Viết comment tiếng Việt giải thích TẠI SAO, theo đúng style hiện có của file.
```

### Prompt 2 — Bộ kiểm thử dùng 892 công thức TeX làm ground truth

```
Đọc ref.md mục 6.
Viết script tests/test_mtef_groundtruth.py:
1. Duyệt toàn bộ .docx trong "Kiến thức trọng tâm và tài tập/".
2. Với mỗi MathType OLE, lấy stream "Equation Native".
3. Tách tập công thức có nhúng TeX gốc (có mốc b"TeX Input Language\x00").
   Corpus có 892 công thức như vậy — đây là ground truth.
4. Với mỗi công thức đó, ÉP parser đi đường MTEF binary (bỏ qua nhánh TeX),
   rồi so LaTeX sinh ra với TeX gốc sau chuẩn hoá:
   bỏ khoảng trắng, bỏ \left \right, bỏ {} dư, bỏ \mathrm.
5. In: % khớp tuyệt đối, % khớp sau chuẩn hoá, 30 ca sai điển hình
   (in cả TeX gốc, LaTeX sinh ra, và selector đã dùng).
6. In thêm các chỉ số của bảng "Ngưỡng nghiệm thu" trong ref.md mục 6.
Script phải chạy được độc lập: python3 -m tests.test_mtef_groundtruth
```

### Prompt 3 — Tiếng Việt TCVN3 trong công thức (L7, L8)

```
Đọc ref.md mục L7 và L8.
Vấn đề: nhiều công thức MathType có người soạn gõ tiếng Việt BÊN TRONG bằng
font .VnTime (bộ mã TCVN3, tiếng Việt ở 0xA1-0xFF). Parser giải mã như latin1
nên ra rác: "chøaproton", "®iÖn", "vµ", "kh«ng".

Nhiệm vụ:
1. Thêm bảng TCVN3 -> Unicode đầy đủ vào pipeline/mtef.py.
2. Truyền `typeface`/tên font xuống render_char để chỉ áp bảng TCVN3 khi record
   thuộc font .Vn* (parser đã đọc danh sách font trong skip_preamble -> self.fonts).
3. Những "công thức" thực chất chỉ là đoạn văn tiếng Việt (không có ký hiệu
   toán nào) thì phát hiện và xuất ra text thuần, không render như công thức.
4. L8: dấu cách đang bị mất ("H¹tnh©n" dính liền). Thống kê các mã PUA
   (0xE000-0xF8FF) thật gặp trong corpus, map cho đủ thay vì xoá cả dải
   (render_char hiện xoá sạch, chỉ chừa 3 mã 0xEC80/81/82).
Kiểm chứng: sau khi sửa, không còn công thức nào chứa byte 0x80-0xFF chưa dịch
(hiện có 26 công thức như vậy).
```

### Prompt 4 — Bỏ hẳn đường convert ra ảnh (L12) — CHỈ CHẠY SAU KHI PROMPT 1&2 ĐẠT

```
Đọc ref.md mục L12. CHỈ làm sau khi bộ kiểm thử ở mục 6 đạt >= 90% khớp
ground truth — bỏ ảnh trước đó sẽ làm 3428 công thức hiện LaTeX SAI ra HTML.

Nhiệm vụ:
1. pipeline/docxast.py dòng ~188-196: bỏ nhánh lấy ảnh preview cho công thức
   (điều kiện `conf < 0.98 and img is not None`).
2. pipeline/mtef.py dòng ~502-506: cổng "còn byte dư -> unresolved" hiện ném đi
   418 công thức. Đổi thành: vẫn trả LaTeX nhưng gắn confidence thấp + log.
3. Giữ _to_png cho HÌNH MINH HOẠ thật (w:drawing), chỉ bỏ cho công thức.
4. Công thức hỏng hoàn toàn: xuất <code>latex thô</code> + ghi log ra file
   để review, KHÔNG im lặng bỏ qua.
5. Chạy lại toàn corpus, báo cáo: số công thức ra LaTeX / số ra <code> /
   số còn ra ảnh (phải = 0).
```

---

## 8. Ghi chú cho người review

- Bảng selector là **thứ dễ sai lặng lẽ nhất**. Đừng bao giờ khai báo nó bằng
  `range(n)` theo thứ tự tên — thêm/xoá một tên là lệch cả bảng. Chính cách
  khai báo đó gây ra L2.
- Mọi chỗ parser "bỏ qua" dữ liệu đã đọc phải **log**. L4 sống lâu được vì nó
  ném nội dung đi hoàn toàn im lặng.
- 892 công thức TeX nhúng là ground truth **có sẵn, miễn phí**. Nên dựng bộ
  kiểm thử này trước khi sửa tiếp bất cứ thứ gì — hiện tại không có cách nào
  biết một thay đổi là tiến bộ hay hồi quy.
- Đường OMML (`docxast.omml_to_latex`) và đường TeX nhúng đang **tốt**
  (confidence 1.0). Chỉ đường MTEF binary hỏng. Đừng sửa lan sang 2 đường kia.
