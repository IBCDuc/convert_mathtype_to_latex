# Công thức cần sửa trong file Word

Quét **43** file `.docx`, **4708** công thức MathType.
Cần sửa: **265** công thức trong **12** file.

Các công thức dưới đây hỏng **ngay trong file Word** — mở bằng MathType cũng thấy sai.
Sửa tại nguồn là chính xác; pipeline chỉ có thể phỏng đoán.

> **Lưu ý cách đọc.** Báo cáo này đo LaTeX ngay sau khi đọc file, **trước** tầng
> chuẩn hoá cuối (`mathrender._wrap_bare_words`) và trước `overrides.json`. Vì vậy
> một số ca ghi "không hiển thị được" ở đây **vẫn hiển thị đúng trên web** nhờ các
> tầng đó. Con số chính thức của sản phẩm là output của
> `python -m pipeline.cli_bt_json ... --fail-on-katex-error`.
>
> Mục đích của báo cáo là chỉ ra chỗ **dữ liệu nguồn sai**, để sửa dứt điểm trong
> file Word thay vì để pipeline phỏng đoán mãi.

## Nguyên nhân thường gặp nhất

Khi gõ số mũ bằng `Ctrl+H`, phải bấm **mũi tên phải (→)** để thoát khỏi ô số mũ
trước khi gõ tiếp. Nếu quên, cả phần còn lại của phương trình bị đưa vào ô số mũ:

| Gõ | Kết quả |
|---|---|
| `6x` `Ctrl+H` `2` `→` `-7x+1=0` | 6x² − 7x + 1 = 0  ✅ |
| `6x` `Ctrl+H` `2` `-7x+1=0` | 6x^(2−7x+1=0)  ❌ |

## Hóa 10/Hóa 10/Bài 2. Nguyên tố hóa học.docx

5 công thức:

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `_{5}^{11} B và _{6}^{12} C`
  - Dấu hiệu: viet_outside_text
  - `sha1=a08027d6a130` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `_{3}^{7} Li và _{4}^{9} Be`
  - Dấu hiệu: viet_outside_text
  - `sha1=3102ad999246` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `_{12}^{24} Mg và _{14}^{28} Si`
  - Dấu hiệu: viet_outside_text
  - `sha1=72dde3c0b27d` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `_{7}^{14} N và _{8}^{16} O`
  - Dấu hiệu: viet_outside_text
  - `sha1=de6b98a3ee21` (nguồn: mtef)

- **Đoạn:** …Câu 4. Trong tự nhiên, carbon có hai đồng vị bền là và oxygen có ba đồng vị bền là Số lượng tối đa loại phân tử CO2 có thể tạo ra từ các đồng vị này l…
  - Công thức đọc được: `^{16O, ^{17O và ^{18O.}}}`
  - Dấu hiệu: viet_outside_text
  - `sha1=1ef95c54be33` (nguồn: mtef)

## TOÁN 11/Toán 11-Bài 1. GIÁ TRỊ LƯỢNG GIÁC CỦA GÓC LƯỢNG GIÁC.docx

4 công thức:

- **Đoạn:** _(không có chữ)_
  - Công thức đọc được: `\begin{array}{l}\sin ^{2} \alpha + \cos ^{2} \alpha =1 1+ \tan ^{2} \alpha =\frac{1}{ \cos ^{2\alpha }}\left(\alpha \ne \frac{\pi }{2}\right)+k\pi ,k\in \mathbb{Z}\\1+ \cot ^{2} \a`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\begin{array}{l}\sin ^{2\alpha + \cos ^{2\alpha =1}1+ \tan ^{2\alpha =\frac{1}{ \cos ^{2\alpha }}\left(\alpha \ne \frac{\pi }{2}\right)+k\pi ,k\in \ma`
    - web đang hiện : `\begin{array}{l}\sin ^{2} \alpha + \cos ^{2} \alpha =1 1+ \tan ^{2} \alpha =\frac{1}{ \cos ^{2\alpha }}\left(\alpha \ne \frac{\pi }{2}\right)+k\pi ,k\`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f17d7de3d215` (nguồn: mtef)

- **Đoạn:** …Ta có…
  - Công thức đọc được: `\begin{array}{l}a=\left(\frac{\alpha .180}{\pi }\right)\\^{0} =\left(\frac{-\frac{3\pi }{16}}{.180}\pi \right)\\^{0} =\left(-\frac{135}{4}\right)\\^{0} =-33^{045'.}\end{array}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\begin{array}{l}a=\left(\frac{\alpha .180}{\pi }\right)\\^{0=\left(\frac{-\frac{3\pi }{16}}{.180}\pi \right)}\\^{0=\left(-\frac{135}{4}\right)}\\^{0=-`
    - web đang hiện : `\begin{array}{l}a=\left(\frac{\alpha .180}{\pi }\right)\\^{0} =\left(\frac{-\frac{3\pi }{16}}{.180}\pi \right)\\^{0} =\left(-\frac{135}{4}\right)\\^{0`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=988a438040b8` (nguồn: mtef)

- **Đoạn:** …Theo đề…
  - Công thức đọc được: `Ox,Oy =1822^{030'\to 22^{030'+k.360^{0=1822^{030'\to k=5}}}}`
  - Dấu hiệu: swallowed_exponent
  - `sha1=1c72eb066963` (nguồn: mtef)

- **Đoạn:** …a) b) ;…
  - Công thức đọc được: `B= \sin ^{2} 60^{\circ}+ \tan ^{2} 30^{\circ}-2=-\frac{11}{12}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `B= \sin ^{260^{\circ}+ \tan ^{230^{\circ}-2=-\frac{11}{12}}}`
    - web đang hiện : `B= \sin ^{2} 60^{\circ}+ \tan ^{2} 30^{\circ}-2=-\frac{11}{12}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=3882ec8c8d6e` (nguồn: mtef)

## TOÁN 11/Toán 11-Bài 2. CÔNG THỨC LƯỢNG GIÁC.docx

38 công thức:

- **Đoạn:** …A. B.…
  - Công thức đọc được: `\cos 6a= \cos ^{2} 3 a- \sin ^{2} 3a.`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos 6a= \cos ^{23a- \sin ^{23a.}}`
    - web đang hiện : `\cos 6a= \cos ^{2} 3 a- \sin ^{2} 3a.`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=3786f6add23b` (nguồn: mtef)

- **Đoạn:** …A. B.…
  - Công thức đọc được: `\cos 6a=1-2 \sin ^{2} 3a.`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos 6a=1-2 \sin ^{23a.}`
    - web đang hiện : `\cos 6a=1-2 \sin ^{2} 3a.`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=cd8bed099910` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\cos 6a=2 \cos ^{2} 3a-1`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos 6a=2 \cos ^{23a-1}`
    - web đang hiện : `\cos 6a=2 \cos ^{2} 3a-1`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f58f8804848e` (nguồn: mtef)

- **Đoạn:** …Áp dụng công thức , ta được…
  - Công thức đọc được: `\cos 2\alpha = \cos ^{2} \alpha - \sin ^{2} \alpha =2 \cos ^{2} \alpha -1=1-2 \sin ^{2\alpha }`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos 2\alpha = \cos ^{2\alpha - \sin ^{2\alpha =2 \cos ^{2\alpha -1=1-2 \sin ^{2\alpha }}}}`
    - web đang hiện : `\cos 2\alpha = \cos ^{2} \alpha - \sin ^{2} \alpha =2 \cos ^{2} \alpha -1=1-2 \sin ^{2\alpha }`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=3e5ee1bbf460` (nguồn: mtef)

- **Đoạn:** ….…
  - Công thức đọc được: `\cos 6a= \cos ^{2} 3 a- \sin ^{2} 3 a=2 \cos ^{2} 3 a-1=1-2 \sin ^{2} 3a`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos 6a= \cos ^{23a- \sin ^{23a=2 \cos ^{23a-1=1-2 \sin ^{23a}}}}`
    - web đang hiện : `\cos 6a= \cos ^{2} 3 a- \sin ^{2} 3 a=2 \cos ^{2} 3 a-1=1-2 \sin ^{2} 3a`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=3f4d6c84a73c` (nguồn: mtef)

- **Đoạn:** …A. B.…
  - Công thức đọc được: `\sin ^{2} x=\frac{1- \cos 2x}{2} .`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\sin ^{2x=\frac{1- \cos 2x}{2}}.`
    - web đang hiện : `\sin ^{2} x=\frac{1- \cos 2x}{2} .`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ece1d97f6dc1` (nguồn: mtef)

- **Đoạn:** …A. B.…
  - Công thức đọc được: `\cos ^{2} x=\frac{1+ \cos 2x}{2} .`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos ^{2x=\frac{1+ \cos 2x}{2}}.`
    - web đang hiện : `\cos ^{2} x=\frac{1+ \cos 2x}{2} .`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=6b3eb8f52552` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\cos 3x= \cos ^{3} x- \sin ^{3x.}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos 3x= \cos ^{3x- \sin ^{3x.}}`
    - web đang hiện : `\cos 3x= \cos ^{3} x- \sin ^{3x.}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=7ade08712eec` (nguồn: mtef)

- **Đoạn:** …Ta có .…
  - Công thức đọc được: `\cos 3x=4 \cos ^{3} x-3 \cos x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos 3x=4 \cos ^{3x-3 \cos x}`
    - web đang hiện : `\cos 3x=4 \cos ^{3} x-3 \cos x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=e0f1632f76ea` (nguồn: mtef)

- **Đoạn:** …A. B.…
  - Công thức đọc được: `\cos 3a=4 \cos ^{3} a-3 \cos a.`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos 3a=4 \cos ^{3a-3 \cos a.}`
    - web đang hiện : `\cos 3a=4 \cos ^{3} a-3 \cos a.`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=4f2303aa710f` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\cos 3a=3 \cos ^{3} a-4 \cos a.`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos 3a=3 \cos ^{3a-4 \cos a.}`
    - web đang hiện : `\cos 3a=3 \cos ^{3} a-4 \cos a.`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=fcb3f83922c2` (nguồn: mtef)

- **Đoạn:** …A. B.…
  - Công thức đọc được: `\sin 3a=4 \sin ^{3} a-3 \sin a.`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\sin 3a=4 \sin ^{3a-3 \sin a.}`
    - web đang hiện : `\sin 3a=4 \sin ^{3} a-3 \sin a.`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=cddf63043e3d` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\sin 3a=3 \sin ^{3} a-4 \sin a.`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\sin 3a=3 \sin ^{3a-4 \sin a.}`
    - web đang hiện : `\sin 3a=3 \sin ^{3} a-4 \sin a.`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=4e746fc507e5` (nguồn: mtef)

- **Đoạn:** …A. . B. .…
  - Công thức đọc được: `\cos ^{2} a=\frac{1+ \cos 2a}{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos ^{2a=\frac{1+ \cos 2a}{2}}`
    - web đang hiện : `\cos ^{2} a=\frac{1+ \cos 2a}{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f6acd4697c15` (nguồn: mtef)

- **Đoạn:** …A. . B. .…
  - Công thức đọc được: `\cos ^{2} a=\frac{1- \cos 2a}{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos ^{2a=\frac{1- \cos 2a}{2}}`
    - web đang hiện : `\cos ^{2} a=\frac{1- \cos 2a}{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=058203f84012` (nguồn: mtef)

- **Đoạn:** …C. . D.…
  - Công thức đọc được: `\cos ^{2} a=\frac{1+ \sin 2a}{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos ^{2a=\frac{1+ \sin 2a}{2}}`
    - web đang hiện : `\cos ^{2} a=\frac{1+ \sin 2a}{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=d60fa1070fe4` (nguồn: mtef)

- **Đoạn:** …C. . D.…
  - Công thức đọc được: `\cos ^{2} a=\frac{1- \sin 2a}{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos ^{2a=\frac{1- \sin 2a}{2}}`
    - web đang hiện : `\cos ^{2} a=\frac{1- \sin 2a}{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=18dc731b3373` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D.…
  - Công thức đọc được: `\sin ^{2} a=\frac{1+ \cos 2a}{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\sin ^{2a=\frac{1+ \cos 2a}{2}}`
    - web đang hiện : `\sin ^{2} a=\frac{1+ \cos 2a}{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=6b5e9733f94a` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D.…
  - Công thức đọc được: `\sin ^{2} a=\frac{1- \cos 2a}{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\sin ^{2a=\frac{1- \cos 2a}{2}}`
    - web đang hiện : `\sin ^{2} a=\frac{1- \cos 2a}{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f8696fad80bb` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D.…
  - Công thức đọc được: `\sin ^{2} a=\frac{1+ \tan 2a}{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\sin ^{2a=\frac{1+ \tan 2a}{2}}`
    - web đang hiện : `\sin ^{2} a=\frac{1+ \tan 2a}{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=49c6b893adde` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D.…
  - Công thức đọc được: `\sin ^{2} a=\frac{1- \cot 2a}{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\sin ^{2a=\frac{1- \cot 2a}{2}}`
    - web đang hiện : `\sin ^{2} a=\frac{1- \cot 2a}{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c53ba45dcfd2` (nguồn: mtef)

- **Đoạn:** …A. B.…
  - Công thức đọc được: `\cos 2a= \cos ^{2} a- \sin ^{2a}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos 2a= \cos ^{2a- \sin ^{2a}}`
    - web đang hiện : `\cos 2a= \cos ^{2} a- \sin ^{2a}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=467bce8ebbc6` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\cos 2a= \cos ^{2} a+ \sin ^{2a}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos 2a= \cos ^{2a+ \sin ^{2a}}`
    - web đang hiện : `\cos 2a= \cos ^{2} a+ \sin ^{2a}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ed58b464a53d` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\cos 2a=2 \cos ^{2} a- \sin ^{2a}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos 2a=2 \cos ^{2a- \sin ^{2a}}`
    - web đang hiện : `\cos 2a=2 \cos ^{2} a- \sin ^{2a}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=06de3b06f19e` (nguồn: mtef)

- **Đoạn:** …Câu 21. Rút gọn biểu thức…
  - Công thức đọc được: `M= \cos ^{4} 15^{o- \sin ^{415^{o.}}}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `M= \cos ^{415^{o- \sin ^{415^{o.}}}}`
    - web đang hiện : `M= \cos ^{4} 15^{o- \sin ^{415^{o.}}}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=77b42502af76` (nguồn: mtef)

- **Đoạn:** _(không có chữ)_
  - Công thức đọc được: `=( \cos ^{2} 15^{o- \sin ^{215^{o}}( \cos ^{215^{o+ \sin ^{215^{o}}}})} )`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `=( \cos ^{215^{o- \sin ^{215^{o}}( \cos ^{215^{o+ \sin ^{215^{o}}}})}})`
    - web đang hiện : `=( \cos ^{2} 15^{o- \sin ^{215^{o}}( \cos ^{215^{o+ \sin ^{215^{o}}}})} )`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=1a388ae55d8b` (nguồn: mtef)

- **Đoạn:** _(không có chữ)_
  - Công thức đọc được: `= \cos ^{2} 15^{o- \sin ^{215^{o= \cos (2.15^{o})= \cos 30^{o=\frac{\sqrt[3]{2}}{.}}}}}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `= \cos ^{215^{o- \sin ^{215^{o= \cos (2.15^{o})= \cos 30^{o=\frac{\sqrt[3]{2}}{.}}}}}}`
    - web đang hiện : `= \cos ^{2} 15^{o- \sin ^{215^{o= \cos (2.15^{o})= \cos 30^{o=\frac{\sqrt[3]{2}}{.}}}}}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f90f11d8b8df` (nguồn: mtef)

- **Đoạn:** …Vì nên suy ra…
  - Công thức đọc được: `\sin 10^{0} \ne 0`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\sin 10^{0\ne 0}`
    - web đang hiện : `\sin 10^{0} \ne 0`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=93688b1ed6c7` (nguồn: mtef)

- **Đoạn:** …c)…
  - Công thức đọc được: `\begin{array}{l}\cos 2\alpha =1-2 \sin ^{2} \alpha =1-2\left(\frac{1}{3}\right)\\^{2} =\frac{7}{9}\end{array}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\begin{array}{l}\cos 2\alpha =1-2 \sin ^{2\alpha =1-2\left(\frac{1}{3}\right)}\\^{2=\frac{7}{9}}\end{array}`
    - web đang hiện : `\begin{array}{l}\cos 2\alpha =1-2 \sin ^{2} \alpha =1-2\left(\frac{1}{3}\right)\\^{2} =\frac{7}{9}\end{array}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b5e829b5c99f` (nguồn: mtef)

- **Đoạn:** …a)…
  - Công thức đọc được: `Vì \frac{\pi }{2} <\alpha <\pi \Rightarrow \cos \alpha <0.`
  - Dấu hiệu: viet_outside_text
  - `sha1=b735dead8bd2` (nguồn: mtef)

- **Đoạn:** …b)…
  - Công thức đọc được: `Ta có \cos \alpha =-\sqrt{1- \sin ^{2\alpha }=-\frac{4}{5}}`
  - Dấu hiệu: viet_outside_text
  - `sha1=8b118398d166` (nguồn: mtef)

- **Đoạn:** …Câu 37. Tính giá trị của biểu thức…
  - Công thức đọc được: `M= \cos ^{4} 15^{0- \sin ^{415^{0+ \cos ^{215^{0- \sin ^{215^{0}}}}}}}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `M= \cos ^{415^{0- \sin ^{415^{0+ \cos ^{215^{0- \sin ^{215^{0}}}}}}}}`
    - web đang hiện : `M= \cos ^{4} 15^{0- \sin ^{415^{0+ \cos ^{215^{0- \sin ^{215^{0}}}}}}}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=72bce1f1db62` (nguồn: mtef)

- **Đoạn:** …Áp dụng công thức nhân đôi .…
  - Công thức đọc được: `\cos ^{2} a- \sin ^{2} a= \cos 2a`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos ^{2a- \sin ^{2a= \cos 2a}}`
    - web đang hiện : `\cos ^{2} a- \sin ^{2} a= \cos 2a`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c4c81fe4b8d1` (nguồn: mtef)

- **Đoạn:** …Ta có .…
  - Công thức đọc được: `M=( \cos ^{4} 15^{o- \sin ^{415^{o}}+( \cos ^{215^{o- \sin ^{215^{o}}}})} )`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `M=( \cos ^{415^{o- \sin ^{415^{o}}+( \cos ^{215^{o- \sin ^{215^{o}}}})}})`
    - web đang hiện : `M=( \cos ^{4} 15^{o- \sin ^{415^{o}}+( \cos ^{215^{o- \sin ^{215^{o}}}})} )`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=af3b70b9d9b9` (nguồn: mtef)

- **Đoạn:** ….…
  - Công thức đọc được: `=( \cos ^{2} 15^{o- \sin ^{215^{o}}( \cos ^{215^{o+ \sin ^{215^{o}}+( \cos ^{215^{o- \sin ^{215^{o}}}})}})} )`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `=( \cos ^{215^{o- \sin ^{215^{o}}( \cos ^{215^{o+ \sin ^{215^{o}}+( \cos ^{215^{o- \sin ^{215^{o}}}})}})}})`
    - web đang hiện : `=( \cos ^{2} 15^{o- \sin ^{215^{o}}( \cos ^{215^{o+ \sin ^{215^{o}}+( \cos ^{215^{o- \sin ^{215^{o}}}})}})} )`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=8348feb91cc0` (nguồn: mtef)

- **Đoạn:** _(không có chữ)_
  - Công thức đọc được: `=\left( \cos ^{2} 15^{o- \sin ^{215^{o}}+\left( \cos ^{215^{o- \sin ^{215^{o}}= \cos 30^{o+ \cos 30^{o=\sqrt[3]{.}}}}}\right)} \right)`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `=\left( \cos ^{215^{o- \sin ^{215^{o}}+\left( \cos ^{215^{o- \sin ^{215^{o}}= \cos 30^{o+ \cos 30^{o=\sqrt[3]{.}}}}}\right)}}\right)`
    - web đang hiện : `=\left( \cos ^{2} 15^{o- \sin ^{215^{o}}+\left( \cos ^{215^{o- \sin ^{215^{o}}= \cos 30^{o+ \cos 30^{o=\sqrt[3]{.}}}}}\right)} \right)`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=7566a1f6b759` (nguồn: mtef)

- **Đoạn:** _(không có chữ)_
  - Công thức đọc được: `=\frac{1- \tan 9^{0} . \tan 21^{0} \tan 9^{0+ \tan 21^{0}}=\frac{1}{ \tan (9^{0+21^{0}})}=\frac{1}{ \tan 30^{0}}=\sqrt[3]{.} }{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `=\frac{1- \tan 9^{0. \tan 21^{0} \tan 9^{0+ \tan 21^{0}}=\frac{1}{ \tan (9^{0+21^{0}})}=\frac{1}{ \tan 30^{0}}=\sqrt[3]{.}}}{}`
    - web đang hiện : `=\frac{1- \tan 9^{0} . \tan 21^{0} \tan 9^{0+ \tan 21^{0}}=\frac{1}{ \tan (9^{0+21^{0}})}=\frac{1}{ \tan 30^{0}}=\sqrt[3]{.} }{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=1de9945d8d89` (nguồn: mtef)

- **Đoạn:** …Từ hệ thức , suy ra .…
  - Công thức đọc được: `\sin ^{2\alpha + \cos ^{2\alpha =1}}`
  - Dấu hiệu: swallowed_exponent
  - `sha1=fb30c959e54d` (nguồn: mtef)

## TOÁN 11/Toán 11-Bài 3. HÀM SỐ LƯỢNG GIÁC.docx

5 công thức:

- **Đoạn:** …Hàm số xác định khi và chỉ khi và xác định…
  - Công thức đọc được: `1- \sin ^{2} x\ne 0`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `1- \sin ^{2x\ne 0}`
    - web đang hiện : `1- \sin ^{2} x\ne 0`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=98865d707703` (nguồn: mtef)

- **Đoạn:** _(không có chữ)_
  - Công thức đọc được: `\Leftrightarrow \{ \sin ^{2} x\ne 1 \cos x\ne 0\Leftrightarrow \cos x\ne 0\Leftrightarrow x\ne \frac{\pi }{2} +k\pi ,k\in \mathbb{Z} .\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\Leftrightarrow \{ \sin ^{2x\ne 1} \cos x\ne 0\Leftrightarrow \cos x\ne 0\Leftrightarrow x\ne \frac{\pi }{2} +k\pi ,k\in \mathbb{Z} .\}`
    - web đang hiện : `\Leftrightarrow \{ \sin ^{2} x\ne 1 \cos x\ne 0\Leftrightarrow \cos x\ne 0\Leftrightarrow x\ne \frac{\pi }{2} +k\pi ,k\in \mathbb{Z} .\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=572d5a722c7d` (nguồn: mtef)

- **Đoạn:** …Câu 53. Tìm giá trị lớn nhất M của hàm số…
  - Công thức đọc được: `y=4 \sin ^{2} x+\sqrt[2]{ \sin \left(2x+\frac{\pi }{4}\right)}.`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=4 \sin ^{2x+\sqrt[2]{ \sin \left(2x+\frac{\pi }{4}\right)}.}`
    - web đang hiện : `y=4 \sin ^{2} x+\sqrt[2]{ \sin \left(2x+\frac{\pi }{4}\right)}.`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=303146351bc5` (nguồn: mtef)

- **Đoạn:** …Ta có…
  - Công thức đọc được: `y=4 \sin ^{2} x+\sqrt[2]{ \sin \left(2x+\frac{\pi }{4}\right)}=4\left(\frac{1- \cos 2x}{2}\right) + \sin 2x+ \cos 2x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=4 \sin ^{2x+\sqrt[2]{ \sin \left(2x+\frac{\pi }{4}\right)}=4\left(\frac{1- \cos 2x}{2}\right)} + \sin 2x+ \cos 2x`
    - web đang hiện : `y=4 \sin ^{2} x+\sqrt[2]{ \sin \left(2x+\frac{\pi }{4}\right)}=4\left(\frac{1- \cos 2x}{2}\right) + \sin 2x+ \cos 2x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f36f7e81f85d` (nguồn: mtef)

- **Đoạn:** …Do…
  - Công thức đọc được: `0\le \cos ^{2} x\le 1\to 0\le y\le 2\to M=2.`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `0\le \cos ^{2x\le 1\to 0\le y\le 2\to M=2}`
    - web đang hiện : `0\le \cos ^{2} x\le 1\to 0\le y\le 2\to M=2.`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=0ca9bd9f517e` (nguồn: mtef)

## TOÁN 11/Toán 11-Bài 4. PHƯƠNG TRÌNH LƯỢNG GIÁC CƠ BẢN.docx

4 công thức:

- **Đoạn:** …Câu 22. Nghiệm của phương trình là:…
  - Công thức đọc được: `\cos ^{2} x=0`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos ^{2x=0}`
    - web đang hiện : `\cos ^{2} x=0`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=0a8e7bc45c81` (nguồn: mtef)

- **Đoạn:** ….…
  - Công thức đọc được: `\cos ^{2} x=0\Leftrightarrow \cos x=0\Leftrightarrow x=\frac{\pi }{2} +k\pi (k\in \mathbb{Z} )`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\cos ^{2x=0\Leftrightarrow \cos x=0\Leftrightarrow x=\frac{\pi }{2}}+k\pi (k\in \mathbb{Z} )`
    - web đang hiện : `\cos ^{2} x=0\Leftrightarrow \cos x=0\Leftrightarrow x=\frac{\pi }{2} +k\pi (k\in \mathbb{Z} )`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=cdb94335b738` (nguồn: mtef)

- **Đoạn:** …A. . B. .…
  - Công thức đọc được: `S=\left\{k2\pi ;\frac{\pi }{3}\right\}+\frac{k2\pi }{3} |k\in \mathbb{Z} |\}`
  - Dấu hiệu: stray_pipe
  - `sha1=d035a218b2bd` (nguồn: mtef)

- **Đoạn:** …b)…
  - Công thức đọc được: `Vì x\in (0;\pi ) nên x\in \left\{\frac{\pi }{6}\right\};\frac{5\pi }{6}`
  - Dấu hiệu: viet_outside_text
  - `sha1=209efa86c5fa` (nguồn: mtef)

## Toán 10/Toán 10/BÀI 2 Tập hợp và các phép toán trên tập hợp.docx

13 công thức:

- **Đoạn:** _(không có chữ)_
  - Công thức đọc được: `S\cap T=\left\{x|x\in S và x\in T\right\}`
  - Dấu hiệu: viet_outside_text
  - nguồn: **omml** — không phải MathType OLE, nên không override được theo sha1; phải sửa trong file Word

- **Đoạn:** ….…
  - Công thức đọc được: `S\cup T=\left\{x|x\in S hoặc x\in T\right\}`
  - Dấu hiệu: viet_outside_text
  - nguồn: **omml** — không phải MathType OLE, nên không override được theo sha1; phải sửa trong file Word

- **Đoạn:** _(không có chữ)_
  - Công thức đọc được: `S\T=\left\{x|x\in S và x\notin T\right\}`
  - ❌ Không hiển thị được: KaTeX parse error: Undefined control sequence: \T at position 2: S\̲T̲=\left\{x|x\in …
  - Dấu hiệu: viet_outside_text
  - nguồn: **omml** — không phải MathType OLE, nên không override được theo sha1; phải sửa trong file Word

- **Đoạn:** …Câu 4. Liệt kê phần tử của tập hợp .…
  - Công thức đọc được: `B=\{x\in \mathbb{N} |(2x^{2} -x)(x^{2} -3x-4)=0 \}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `B=\{x\in \mathbb{N} |(2x^{2-x)(x^{2-3x-4)=0}}\}`
    - web đang hiện : `B=\{x\in \mathbb{N} |(2x^{2} -x)(x^{2} -3x-4)=0 \}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=fbe0f3c7600a` (nguồn: mtef)

- **Đoạn:** …Câu 5. Cho , khẳng định nào sau đây đúng?…
  - Công thức đọc được: `X=\{x\in \mathbb{R}|2x^{2} -5x+3=0\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `X=\{x\in \mathbb{R}|2x^{2-5x+3=0}|\}`
    - web đang hiện : `X=\{x\in \mathbb{R}|2x^{2} -5x+3=0\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=2f75e195c641` (nguồn: mtef)

- **Đoạn:** …A. . B. .…
  - Công thức đọc được: `\{x\in \mathbb{N} \mid |x|\}<1\}`
  - Dấu hiệu: stray_pipe
  - `sha1=40e0a97274f6` (nguồn: mtef)

- **Đoạn:** …A. . B. .…
  - Công thức đọc được: `\{x\in \mathbb{Z} \mid 6x^{2} -7x+1=0 \}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\{x\in \mathbb{Z} \mid 6x^{2-7x+1=0}\}`
    - web đang hiện : `\{x\in \mathbb{Z} \mid 6x^{2} -7x+1=0 \}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=19944eba6e30` (nguồn: mtef)

- **Đoạn:** …C. . D. .…
  - Công thức đọc được: `\{x\in \mathbb{Q} \mid x^{2} -4x+2=0 \}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\{x\in \mathbb{Q} \mid x^{2-4x+2=0}\}`
    - web đang hiện : `\{x\in \mathbb{Q} \mid x^{2} -4x+2=0 \}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=da6bbbd6cb7f` (nguồn: mtef)

- **Đoạn:** …C. . D. .…
  - Công thức đọc được: `\{x\in \mathbb{R} \mid x^{2} -4x+3=0 \}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\{x\in \mathbb{R} \mid x^{2-4x+3=0}\}`
    - web đang hiện : `\{x\in \mathbb{R} \mid x^{2} -4x+3=0 \}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=d113c49faff0` (nguồn: mtef)

- **Đoạn:** …Câu 4. Cho các tập hợp sau và . Khi đó:…
  - Công thức đọc được: `A=\{x \in \mathbb{R} \mid (2x-x^{2})(2x^{2} -3x-2 )=0\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `A=\{x \in \mathbb{R} \mid (2x-x^{2})(2x^{2-3x-2})=0\}`
    - web đang hiện : `A=\{x \in \mathbb{R} \mid (2x-x^{2})(2x^{2} -3x-2 )=0\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=5dbd998e9828` (nguồn: mtef)

- **Đoạn:** …Câu 4. Cho các tập hợp sau và . Khi đó:…
  - Công thức đọc được: `B=\{x \in \mathbb{N} \mid ^{*}|3<x^{2} <30 \}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `B=\{x \in \mathbb{N} \mid ^{*}|3<x^{2<30}\}`
    - web đang hiện : `B=\{x \in \mathbb{N} \mid ^{*}|3<x^{2} <30 \}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=3e00ad26ba68` (nguồn: mtef)

- **Đoạn:** …Câu 10. Cho các tập hợp và . Xác định số phần tử để .…
  - Công thức đọc được: `A=\{-2;1;2\};B=\{x \in \mathbb{Z} \mid ^{*}|(x^{2-4})(x^{3} -4x^{2} +3x =0)\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `A=\{-2;1;2\};B=\{x \in \mathbb{Z} \mid ^{*}|(x^{2-4})(x^3 -4 x^2 +3x=0)\}`
    - web đang hiện : `A=\{-2;1;2\};B=\{x \in \mathbb{Z} \mid ^{*}|(x^{2-4})(x^{3} -4x^{2} +3x =0)\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ed58e12cc51d` (nguồn: mtef)

- **Đoạn:** …Câu 10. Cho các tập hợp và . Xác định số phần tử để .…
  - Công thức đọc được: `C=\{x \in \mathbb{R} \mid x^{2} -(2m+1)x+m^{2} +m=0\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `C=\{x \in \mathbb{R} \mid x^{2-(2m+1)x+m^{2+m=0}}`
    - web đang hiện : `C=\{x \in \mathbb{R} \mid x^{2} -(2m+1)x+m^{2} +m=0\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=bf8f4f7b9a16` (nguồn: mtef)

## Toán 10/Toán 10/BÀI 3 Bất phương trình bậc nhất hai ẩn.docx

4 công thức:

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `2x-3y^{3} >0`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `2x-3y^{3>0}`
    - web đang hiện : `2x-3y^{3} >0`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b5fb00b9f68f` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `2x^{2} +y<-3`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `2x^{2+y<-3}`
    - web đang hiện : `2x^{2} +y<-3`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f20d9f155106` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `2x-y^{2} \le 2`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `2x-y^{2\le 2}`
    - web đang hiện : `2x-y^{2} \le 2`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=8ee4ef3c3318` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `2x^{2} +y<-3`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `2x^{2+y<-3}`
    - web đang hiện : `2x^{2} +y<-3`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f20d9f155106` (nguồn: mtef)

## Toán 10/Toán 10/BÀI 4.Hệ bất phương trình bậc nhất hai ẩn.docx

13 công thức:

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\{2x^{2} -y>-3 2x+5y^{2} \le 6\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\{2x^{2-y>-3}2x+5y^{2\le 6}`
    - web đang hiện : `\{2x^{2} -y>-3 2x+5y^{2} \le 6\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c74b99a7d362` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\{x^{2} -y=-3 2x+5^{2} y>6\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\{x^{2-y=-3}2x+5^{2y>6}`
    - web đang hiện : `\{x^{2} -y=-3 2x+5^{2} y>6\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c70726f8c8e9` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\{2^{2} x-y<4 2x+5y=1\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\{2^{2x-y<4}2x+5y=1\}`
    - web đang hiện : `\{2^{2} x-y<4 2x+5y=1\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b37d89055bb7` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\{2x^{2} -y>-3 2x+5y^{2} \le 6\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\{2x^{2-y>-3}2x+5y^{2\le 6}`
    - web đang hiện : `\{2x^{2} -y>-3 2x+5y^{2} \le 6\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c74b99a7d362` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\left\{\frac{x}{2}-y\le -32x+3^{2} y>1 \right\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\left\{\frac{x}{2}-y\le -32x+3^{2y>1}\right\}`
    - web đang hiện : `\left\{\frac{x}{2}-y\le -32x+3^{2} y>1 \right\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=fce3d08b60aa` (nguồn: mtef)

- **Đoạn:** …A. B.…
  - Công thức đọc được: `\{2x-y>3^{2}5^{3} x-y\le 0\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\{2x-y>3^{2}5^{3x-y\le 0}`
    - web đang hiện : `\{2x-y>3^{2}5^{3} x-y\le 0\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=29e765628866` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\left\{\frac{x}{2}-y\le -32x+3^{2} y>1 \right\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\left\{\frac{x}{2}-y\le -32x+3^{2y>1}\right\}`
    - web đang hiện : `\left\{\frac{x}{2}-y\le -32x+3^{2} y>1 \right\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=fce3d08b60aa` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\{2^{2} x-y>-3 2x+5^{2} y\le 6\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\{2^{2x-y>-3}2x+5^{2y\le 6}`
    - web đang hiện : `\{2^{2} x-y>-3 2x+5^{2} y\le 6\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b4c90bab38a3` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\left\{\frac{2}{x}-y\le -32x+3^{2} y>\sqrt{5} \{\right\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\left\{\frac{2}{x}-y\le -32x+3^{2y>\sqrt{5}}\{\right\}`
    - web đang hiện : `\left\{\frac{2}{x}-y\le -32x+3^{2} y>\sqrt{5} \{\right\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ce4612ce8f8c` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\{2x^{2} -y>-3 2x+5y^{2} \le 6\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\{2x^{2-y>-3}2x+5y^{2\le 6}`
    - web đang hiện : `\{2x^{2} -y>-3 2x+5y^{2} \le 6\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c74b99a7d362` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\left\{\frac{x}{2}-y\le x-12x+3^{2} y>2-x \right\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\left\{\frac{x}{2}-y\le x-12x+3^{2y>2-x}\right\}`
    - web đang hiện : `\left\{\frac{x}{2}-y\le x-12x+3^{2} y>2-x \right\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=222f4a6a0927` (nguồn: mtef)

- **Đoạn:** …A. B.…
  - Công thức đọc được: `\{x+y^{2} <0 y-x\le 1\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\{x+y^{2<0}y-x\le 1\}`
    - web đang hiện : `\{x+y^{2} <0 y-x\le 1\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=87c26c73e99b` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `\{2x-y>3^{2}4^{2} x+5y<1\}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\{2x-y>3^{2}4^{2x+5y<1}`
    - web đang hiện : `\{2x-y>3^{2}4^{2} x+5y<1\}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=9669896ef2fd` (nguồn: mtef)

## Toán 12/Toán 12/Toán 12_Bài 1 (Tính đơn điệu và cực trị của hàm số).docx

30 công thức:

- **Đoạn:** …Câu 11. Cho hàm số có đồ thị như hình vẽ bên. Số điểm cực trị của hàm số này là…
  - Công thức đọc được: `y=ax^{3} +bx^{2} +cx+d`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^3 +b x^2 +cx+d`
    - web đang hiện : `y=ax^{3} +bx^{2} +cx+d`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=04d92261ffb6` (nguồn: mtef)

- **Đoạn:** …Câu 16. Cho hàm số (, , ) có đồ thị như hình vẽ bên.…
  - Công thức đọc được: `y=ax^{4} +bx^{2+c}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^4 +b x^2 +c`
    - web đang hiện : `y=ax^{4} +bx^{2+c}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=deec54f638d5` (nguồn: mtef)

- **Đoạn:** …Câu 20. Cho hàm số có đồ thị là đường cong hình bên dưới…
  - Công thức đọc được: `y=ax^{4} +bx^{2+c}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^4 +b x^2 +c`
    - web đang hiện : `y=ax^{4} +bx^{2+c}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=deec54f638d5` (nguồn: mtef)

- **Đoạn:** ….…
  - Công thức đọc được: `f' (x) =x(x+1) (x-4) ^{3} =0\Leftrightarrow [x=0x=-1x=4] [`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f' (x) =x(x+1) (x-4) ^{3=0\Leftrightarrow [x=0x=-1x=4]}[`
    - web đang hiện : `f' (x) =x(x+1) (x-4) ^{3} =0\Leftrightarrow [x=0x=-1x=4] [`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=13d84004f4be` (nguồn: mtef)

- **Đoạn:** …Câu 5. Tìm giá trị cực tiểu của hàm số.…
  - Công thức đọc được: `y=-x^{3} +3x-4`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^{3+3x-4}`
    - web đang hiện : `y=-x^{3} +3x-4`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ea7814360b8f` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `y=x^{3} +x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{3+x}`
    - web đang hiện : `y=x^{3} +x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=09b516e4fa8d` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `y=-x^{3} -3x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^{3-3x}`
    - web đang hiện : `y=-x^{3} -3x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=75f1e16da0b1` (nguồn: mtef)

- **Đoạn:** …Vì .…
  - Công thức đọc được: `y=x^{3} +x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{3+x}`
    - web đang hiện : `y=x^{3} +x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=09b516e4fa8d` (nguồn: mtef)

- **Đoạn:** …Vì .…
  - Công thức đọc được: `\Rightarrow y' =3x^{2} +1>0,\forall x\in \mathbb{R}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\Rightarrow y' =3x^{2+1>0,\forall x\in \mathbb{R} }`
    - web đang hiện : `\Rightarrow y' =3x^{2} +1>0,\forall x\in \mathbb{R}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=6909fa7e7fc1` (nguồn: mtef)

- **Đoạn:** …Câu 7. Cho hàm số . Mệnh đề nào dưới đây đúng?…
  - Công thức đọc được: `y=x^{3} -3x^{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 -3 x^2`
    - web đang hiện : `y=x^{3} -3x^{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=4f60669f0f80` (nguồn: mtef)

- **Đoạn:** …Ta có ; .…
  - Công thức đọc được: `y' =3x^{2} -6x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =3x^{2-6x}`
    - web đang hiện : `y' =3x^{2} -6x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=60741c5693e3` (nguồn: mtef)

- **Đoạn:** …Câu 9. Hàm số đồng biến trên khoảng…
  - Công thức đọc được: `y=x^{4} -4x^{3}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{4-4x^{3}}`
    - web đang hiện : `y=x^{4} -4x^{3}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=fb454f40bb32` (nguồn: mtef)

- **Đoạn:** …Ta có…
  - Công thức đọc được: `y' =4x^{3} -12x^{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =4x^3 -12 x^2`
    - web đang hiện : `y' =4x^{3} -12x^{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=4a11d1d51967` (nguồn: mtef)

- **Đoạn:** …Cho…
  - Công thức đọc được: `y' =0\Leftrightarrow 4x^{3} -12x^{2} =0`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =0\Leftrightarrow 4x^3 -12 x^2 =0`
    - web đang hiện : `y' =0\Leftrightarrow 4x^{3} -12x^{2} =0`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=762b7ab35647` (nguồn: mtef)

- **Đoạn:** …Câu 15. Cho hàm số có đồ thị .…
  - Công thức đọc được: `y=\frac{x^{3}3}{}-2x^{2} +3x+\frac{2}{3}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^{3}3}{}-2x^{2+3x+\frac{2}{3}}`
    - web đang hiện : `y=\frac{x^{3}3}{}-2x^{2} +3x+\frac{2}{3}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=3dd4922bf76d` (nguồn: mtef)

- **Đoạn:** …Ta có .…
  - Công thức đọc được: `y' =x^{2} -4x+3\Rightarrow y' =0\Leftrightarrow [x=1x=3][`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =x^{2-4x+3\Rightarrow y'}=0\Leftrightarrow [x=1x=3][`
    - web đang hiện : `y' =x^{2} -4x+3\Rightarrow y' =0\Leftrightarrow [x=1x=3][`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f78262253bc1` (nguồn: mtef)

- **Đoạn:** …Câu 1. Cho hàm số có đồ thị . Gọi lần lượt là điểm cực tiểu và điểm cực đại của .…
  - Công thức đọc được: `y=\frac{x^{2} +2x+2 x+1}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^2 +2x+2}{x+1}`
    - web đang hiện : `y=\frac{x^{2} +2x+2 x+1}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=1228f055d7e3` (nguồn: mtef)

- **Đoạn:** …b) .…
  - Công thức đọc được: `y' =\frac{x^{2} +2x}{(x+1)^2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =\frac{x^{2+2x}}{(x+1)^2}`
    - web đang hiện : `y' =\frac{x^{2} +2x}{(x+1)^2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=0a91b97b5a85` (nguồn: mtef)

- **Đoạn:** …Câu 2. Cho hàm số có đồ thị (C). Gọi là điểm cực đại và là điểm cực tiểu của .…
  - Công thức đọc được: `y=x^{3} -3x^{2+4}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 -3 x^2 +4`
    - web đang hiện : `y=x^{3} -3x^{2+4}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=354b90f4e7a3` (nguồn: mtef)

- **Đoạn:** …b) Ta có và hoặc…
  - Công thức đọc được: `y'=3x^{2} -6x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y'=3x^{2-6x}`
    - web đang hiện : `y'=3x^{2} -6x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=0c0ed10c9f39` (nguồn: mtef)

- **Đoạn:** …c) Ta có…
  - Công thức đọc được: `g' (x) =[f(x)]+1 [] ^{'=f'}(x)`
  - Dấu hiệu: swallowed_exponent
  - `sha1=7ea5bfd9f412` (nguồn: mtef)

- **Đoạn:** …Câu 5. Một hộ làm nghề dệt vải lụa tơ tằm sản xuất mỗi ngày được mét vải lụa . Tổng chi phí sản xuất mét vải lụa, tính bằng nghìn đồng, cho bởi hàm ch…
  - Công thức đọc được: `C(x) =x^{3} -3x^{2} -20x+500`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `C(x) =x^3 -3 x^2 -20x+500`
    - web đang hiện : `C(x) =x^{3} -3x^{2} -20x+500`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b215a6f97e29` (nguồn: mtef)

- **Đoạn:** …Lợi nhuận = doanh thu chi phí, khi đó ta có lợi nhuận nghìn đồng.…
  - Công thức đọc được: `L(x) =220x-(x^{3} -3x^{2} -20x+500 =-x^{3} +3x^{2} +240x-500 )`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `L(x) =220x-(x^3 -3 x^2 -20x+500=-x^3 +3 x^2 +240x-500)`
    - web đang hiện : `L(x) =220x-(x^{3} -3x^{2} -20x+500 =-x^{3} +3x^{2} +240x-500 )`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=94b60b133b50` (nguồn: mtef)

- **Đoạn:** …Ta có…
  - Công thức đọc được: `L' (x) =-3x^{2} +6x+240`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `L' (x) =-3x^{2+6x+240}`
    - web đang hiện : `L' (x) =-3x^{2} +6x+240`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=38b897825ce1` (nguồn: mtef)

- **Đoạn:** …Câu 7. Giả sử sự lây lan của một loại virus ở một địa phương có thể được mô hình hoá bằng hàm số , , trong đó là số người bị nhiễm bệnh (đơn vị là tră…
  - Công thức đọc được: `N(t) =-t^{3} +12t^{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `N(t) =-t^{3+12t^{2}}`
    - web đang hiện : `N(t) =-t^{3} +12t^{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c4abcb3d0119` (nguồn: mtef)

- **Đoạn:** …Ta có . Bảng biến thiên như sau:…
  - Công thức đọc được: `N'(t)=-3t^{2} +24t=0\Rightarrow t=0;t=8`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `N'(t)=-3t^{2+24t=0\Rightarrow t=0;t=8}`
    - web đang hiện : `N'(t)=-3t^{2} +24t=0\Rightarrow t=0;t=8`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=d2e6e1965c8a` (nguồn: mtef)

- **Đoạn:** …Vậy .…
  - Công thức đọc được: `P=2\cdot 0^{2-8^{2=-64}}`
  - Dấu hiệu: swallowed_exponent
  - `sha1=d81f1d0babff` (nguồn: mtef)

- **Đoạn:** …Ta có (vì ).…
  - Công thức đọc được: `N' (t) =\frac{100(100-t^{2})}{(100+t^{2})^{2}}=0\Leftrightarrow 100-t^{2} =0\Leftrightarrow t=10`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `N' (t) =\frac{100(100-t^{2})}{(100+t^{2})^{2}}=0\Leftrightarrow 100-t^{2=0\Leftrightarrow t=10}`
    - web đang hiện : `N' (t) =\frac{100(100-t^{2})}{(100+t^{2})^{2}}=0\Leftrightarrow 100-t^{2} =0\Leftrightarrow t=10`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=33b60fb76952` (nguồn: mtef)

- **Đoạn:** …Câu 10. Thể tích nước của một bể bơi sau phút bơm được tính theo công thức với . Tốc độ bơm nước ở thời đi được tính theo công thức . Tìm vận tốc bơm …
  - Công thức đọc được: `V(t) =\frac{1}{100} \left(30t^{3} -\frac{t^{4}4}{} \right)`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `V(t) =\frac{1}{100} \left(30t^{3-\frac{t^{4}4}{}}\right)`
    - web đang hiện : `V(t) =\frac{1}{100} \left(30t^{3} -\frac{t^{4}4}{} \right)`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=2279564612ed` (nguồn: mtef)

- **Đoạn:** …Ta có .…
  - Công thức đọc được: `v(t) =V' (t) =\frac{1}{100} (90t^{2} -t^{3} )`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `v(t) =V' (t) =\frac{1}{100} (90t^{2-t^{3}})`
    - web đang hiện : `v(t) =V' (t) =\frac{1}{100} (90t^{2} -t^{3} )`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=2afe46617f50` (nguồn: mtef)

## Toán 12/Toán 12/Toán 12_Bài 2 (Giá trị lớn nhất-giá trị nhỏ nhất).docx

27 công thức:

- **Đoạn:** …Câu 3. Giá trị lớn nhất của hàm số trên đoạn bằng:…
  - Công thức đọc được: `f(x)=-x^{4} +12x^{2+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f(x)=-x^4 +12 x^2 +1`
    - web đang hiện : `f(x)=-x^{4} +12x^{2+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=fb1aa08bf8bc` (nguồn: mtef)

- **Đoạn:** …liên tục trên và…
  - Công thức đọc được: `f(x)=-x^{4} +12x^{2+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f(x)=-x^4 +12 x^2 +1`
    - web đang hiện : `f(x)=-x^{4} +12x^{2+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=fb1aa08bf8bc` (nguồn: mtef)

- **Đoạn:** …liên tục trên và…
  - Công thức đọc được: `f'(x)=-4x^{3} +24x^{2} =0\Leftrightarrow \left[x=\sqrt[6]{(L)x=-\sqrt[6]{(L)}}[\right]`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f'(x)=-4x^3 +24 x^2 =0\Leftrightarrow \left[x=\sqrt[6]{(L)x=-\sqrt[6]{(L)}}[\right]`
    - web đang hiện : `f'(x)=-4x^{3} +24x^{2} =0\Leftrightarrow \left[x=\sqrt[6]{(L)x=-\sqrt[6]{(L)}}[\right]`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=4ed9c84510ca` (nguồn: mtef)

- **Đoạn:** …Vậy, giá trị lớn nhất của hàm số trên đoạn bằng 33 tại…
  - Công thức đọc được: `f(x)=-x^{4} +12x^{2+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f(x)=-x^4 +12 x^2 +1`
    - web đang hiện : `f(x)=-x^{4} +12x^{2+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=fb1aa08bf8bc` (nguồn: mtef)

- **Đoạn:** …Câu 4. Giá trị nhỏ nhất của hàm số trên đoạn bằng…
  - Công thức đọc được: `f(x) =x^{3} -24x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f(x) =x^{3-24x}`
    - web đang hiện : `f(x) =x^{3} -24x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=58fd93e21429` (nguồn: mtef)

- **Đoạn:** …Ta có…
  - Công thức đọc được: `f' (x) =3x^{2} -24=0\Leftrightarrow \left[x=2\sqrt[2]{\in [2;19]}x=-2\sqrt[2]{\notin [2;19]}[.\right]`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f' (x) =3x^{2-24=0\Leftrightarrow \left[x=2\sqrt[2]{\in [2;19]}x=-2\sqrt[2]{\notin [2;19]}[.\right]}`
    - web đang hiện : `f' (x) =3x^{2} -24=0\Leftrightarrow \left[x=2\sqrt[2]{\in [2;19]}x=-2\sqrt[2]{\notin [2;19]}[.\right]`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=1f6dd4871859` (nguồn: mtef)

- **Đoạn:** …;; .…
  - Công thức đọc được: `f(2) =2^{3} -24.2=-40`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f(2) =2^{3-24.2=-40}`
    - web đang hiện : `f(2) =2^{3} -24.2=-40`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=0c1ef935614e` (nguồn: mtef)

- **Đoạn:** …;; .…
  - Công thức đọc được: `f\left(2\sqrt[2]{}=\left(2\sqrt[2]{}^{3-24.2\sqrt[2]{=-32\sqrt{2}}}\right)\right)`
  - Dấu hiệu: empty_macro_arg
  - `sha1=12997be55c12` (nguồn: mtef)

- **Đoạn:** …;; .…
  - Công thức đọc được: `f(19) =19^{3} -24.19=6403`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f(19) =19^{3-24.19=6403}`
    - web đang hiện : `f(19) =19^{3} -24.19=6403`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=a2d459e09aad` (nguồn: mtef)

- **Đoạn:** …Vậy giá trị nhỏ nhất của hàm số trên đoạn bằng .…
  - Công thức đọc được: `f(x) =x^{3} -24x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f(x) =x^{3-24x}`
    - web đang hiện : `f(x) =x^{3} -24x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=58fd93e21429` (nguồn: mtef)

- **Đoạn:** …Câu 6. Giá trị lớn nhất của hàm số trên đoạn bằng…
  - Công thức đọc được: `f(x) =x^{3} -3x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f(x) =x^{3-3x}`
    - web đang hiện : `f(x) =x^{3} -3x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ff8c04182016` (nguồn: mtef)

- **Đoạn:** …Ta có…
  - Công thức đọc được: `y' =3x^{2} -3=0\Leftrightarrow x=\pm 1`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =3x^{2-3=0\Leftrightarrow x=\pm 1}`
    - web đang hiện : `y' =3x^{2} -3=0\Leftrightarrow x=\pm 1`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=41f1f7b30144` (nguồn: mtef)

- **Đoạn:** …Câu 9. Giá trị lớn nhất của hàm số bằng…
  - Công thức đọc được: `y=-3x^{4} +4x^{3+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-3x^{4+4x^{3+1}}`
    - web đang hiện : `y=-3x^{4} +4x^{3+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=01e54a2533d2` (nguồn: mtef)

- **Đoạn:** …Ta có . Khi đó ta có bảng biến thiên…
  - Công thức đọc được: `y' =-12x^{3} +12x^{2} \Rightarrow y' =0\Leftrightarrow [x=0x=1][`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =-12x^3 +12 x^2 \Rightarrow y'=0\Leftrightarrow [x=0x=1][`
    - web đang hiện : `y' =-12x^{3} +12x^{2} \Rightarrow y' =0\Leftrightarrow [x=0x=1][`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=799eebd4c3ad` (nguồn: mtef)

- **Đoạn:** …Câu 12. Cho hàm số . Xét tính đúng sai của mệnh đề sau.…
  - Công thức đọc được: `y=x^{3} -3x+2`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{3-3x+2}`
    - web đang hiện : `y=x^{3} -3x+2`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ddece317a84a` (nguồn: mtef)

- **Đoạn:** …Ta có ; ; .…
  - Công thức đọc được: `g(x) =\frac{1}{y} =\frac{1}{x^{3} -3x+2 }`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `g(x) =\frac{1}{y} =\frac{1}{x^{3-3x+2}}`
    - web đang hiện : `g(x) =\frac{1}{y} =\frac{1}{x^{3} -3x+2 }`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=a6b5d55536cd` (nguồn: mtef)

- **Đoạn:** …Ta có ; ; .…
  - Công thức đọc được: `g' (x) =\frac{3x^2 -3}{(x^{3} -3x+2 )^{2}}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `g' (x) =\frac{3x^2 -3}{(x^{3-3x+2})^{2}}`
    - web đang hiện : `g' (x) =\frac{3x^2 -3}{(x^{3} -3x+2 )^{2}}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c28b39942aa7` (nguồn: mtef)

- **Đoạn:** …Câu 13. Cho hàm số…
  - Công thức đọc được: `y=x^{3} -3x+1`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{3-3x+1}`
    - web đang hiện : `y=x^{3} -3x+1`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=4de73fe0e974` (nguồn: mtef)

- **Đoạn:** …Diện tích bề mặt của hình hộp là nên…
  - Công thức đọc được: `x^{2} +4xh=108\Rightarrow h=\frac{108-x^{2}4x}{}( cm)`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `x^{2+4xh=108\Rightarrow h=\frac{108-x^{2}4x}{}( cm)}`
    - web đang hiện : `x^{2} +4xh=108\Rightarrow h=\frac{108-x^{2}4x}{}( cm)`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=6921198cc4f1` (nguồn: mtef)

- **Đoạn:** …Thể tích của hình hộp là: .…
  - Công thức đọc được: `V=x^{2} \cdot h=x^{2} \cdot \frac{108-x^{2}4x}{}=\frac{108x-x^{3}4}{}( cm^{3})`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `V=x^{2\cdot h=x^{2\cdot \frac{108-x^{2}4x}{}=\frac{108x-x^{3}4}{}( cm^{3})}}`
    - web đang hiện : `V=x^{2} \cdot h=x^{2} \cdot \frac{108-x^{2}4x}{}=\frac{108x-x^{3}4}{}( cm^{3})`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=38076ddd644d` (nguồn: mtef)

- **Đoạn:** …Bán kính hình tròn là diện tích của hình tròn bằng .…
  - Công thức đọc được: `\begin{array}{l}\pi \left(\frac{x}{2\pi }\right)\\^{2} =\frac{x^{2}4\pi }{}\end{array}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\begin{array}{l}\pi \left(\frac{x}{2\pi }\right)\\^{2=\frac{x^{2}4\pi }{}}\end{array}`
    - web đang hiện : `\begin{array}{l}\pi \left(\frac{x}{2\pi }\right)\\^{2} =\frac{x^{2}4\pi }{}\end{array}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=1c09d0df0e49` (nguồn: mtef)

- **Đoạn:** …, .…
  - Công thức đọc được: `\begin{array}{l}S(x) =\left(\frac{120-x}{4}\right)\\^{2} +\frac{x^{2}4\pi }{}=\left(\frac{1}{4\pi }\right)+\frac{1}{16} x^{2} -15x+900\end{array}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\begin{array}{l}S(x) =\left(\frac{120-x}{4}\right)\\^{2+\frac{x^{2}4\pi }{}=\left(\frac{1}{4\pi }\right)+\frac{1}{16}} x^{2-15x+900}\end{array}`
    - web đang hiện : `\begin{array}{l}S(x) =\left(\frac{120-x}{4}\right)\\^{2} +\frac{x^{2}4\pi }{}=\left(\frac{1}{4\pi }\right)+\frac{1}{16} x^{2} -15x+900\end{array}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ede6dab71a27` (nguồn: mtef)

- **Đoạn:** …Đặt , với…
  - Công thức đọc được: `\begin{array}{l}HE=x\\vàFK=y\end{array}`
  - Dấu hiệu: viet_outside_text
  - `sha1=59f0ceb68cfd` (nguồn: mtef)

- **Đoạn:** ….…
  - Công thức đọc được: `f' (x) =\frac{x}{\sqrt[x^{2+25}]{+\frac{x-24}{\sqrt[x^{2} -48x+625 ]{,\forall x\in (0;24)}}}}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f' (x) =\frac{x}{\sqrt[x^{2+25}]{+\frac{x-24}{\sqrt[x^{2-48x+625}]{,\forall x\in (0;24)}}}}`
    - web đang hiện : `f' (x) =\frac{x}{\sqrt[x^{2+25}]{+\frac{x-24}{\sqrt[x^{2} -48x+625 ]{,\forall x\in (0;24)}}}}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=80b269bda4b7` (nguồn: mtef)

- **Đoạn:** …Câu 6. Một loại vi khuẩn được tiêm một loại thuốc kích thích sự sinh sản. Sau t phút, số vi khuẩn được xác định theo công thức . Hỏi sau bao phút thì …
  - Công thức đọc được: `N(t) =1000+30t^{2} -t^{3} (0\le t\le 30)`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `N(t) =1000+30t^{2-t^{3(0\le t\le 30)}}`
    - web đang hiện : `N(t) =1000+30t^{2} -t^{3} (0\le t\le 30)`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ba399ee1439f` (nguồn: mtef)

- **Đoạn:** …Xét hàm số .…
  - Công thức đọc được: `N(t) =1000+30t^{2} -t^{3} (0\le t\le 30)`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `N(t) =1000+30t^{2-t^{3(0\le t\le 30)}}`
    - web đang hiện : `N(t) =1000+30t^{2} -t^{3} (0\le t\le 30)`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ba399ee1439f` (nguồn: mtef)

- **Đoạn:** …Ta có:…
  - Công thức đọc được: `N' (t) =60t-3t^{2} =0\Leftrightarrow [t=0t=20] [`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `N' (t) =60t-3t^{2=0\Leftrightarrow [t=0t=20]}[`
    - web đang hiện : `N' (t) =60t-3t^{2} =0\Leftrightarrow [t=0t=20] [`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=92a1f7e8a5a8` (nguồn: mtef)

## Toán 12/Toán 12/Toán 12_Bài 3 (Đường tiệm cận của đồ thị hàm số).docx

10 công thức:

- **Đoạn:** …Trong thực hành, để tìm tiệm cận xiên của đồ thị hàm số trong đó , đa thức tử không chia hết cho đa thức mẫu, ta thực hiện chia tử số cho mẫu số để đư…
  - Công thức đọc được: `f(x) =\frac{ax^{2} +bx+c px+q}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f(x) =\frac{ax^2 +bx+c}{px+q}`
    - web đang hiện : `f(x) =\frac{ax^{2} +bx+c px+q}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ed16644b9c80` (nguồn: mtef)

- **Đoạn:** …Câu 18. Cho hàm số có đồ thị như sau:…
  - Công thức đọc được: `y=\frac{x^{2} +2x-1 2x-1}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^2 +2x-1}{2x-1}`
    - web đang hiện : `y=\frac{x^{2} +2x-1 2x-1}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=0fdbe4c5ab5c` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `y=\frac{x^{2} -3x+2 x-1}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^2 -3x+2}{x-1}`
    - web đang hiện : `y=\frac{x^{2} -3x+2 x-1}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=389e46bf1ca5` (nguồn: mtef)

- **Đoạn:** …Câu 14. Cho hàm số có đồ thị là .…
  - Công thức đọc được: `y=f(x)=\frac{x^{2} +3x+5 x+2}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=f(x)=\frac{x^2 +3x+5}{x+2}`
    - web đang hiện : `y=f(x)=\frac{x^{2} +3x+5 x+2}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=653c55bed141` (nguồn: mtef)

- **Đoạn:** …Câu 1. Cho hàm số . Các mệnh đề sau đúng hay sai?…
  - Công thức đọc được: `y=\frac{x^{2} -2x+2 x+2}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^2 -2x+2}{x+2}`
    - web đang hiện : `y=\frac{x^{2} -2x+2 x+2}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=fd7373eefb46` (nguồn: mtef)

- **Đoạn:** …Câu 2. Cho hàm số .…
  - Công thức đọc được: `y=f(x)=\frac{x+1}{x^{2} +2x+1 }`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=f(x)=\frac{x+1}{x^{2+2x+1}}`
    - web đang hiện : `y=f(x)=\frac{x+1}{x^{2} +2x+1 }`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=d6450b490183` (nguồn: mtef)

- **Đoạn:** …Câu 3. Cho hàm số có đồ thị . Đường tiệm cận xiên của đồ thị là đường thẳng . Tính .…
  - Công thức đọc được: `y=f(x) =\frac{x^{2} -5x+7 x-3}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=f(x) =\frac{x^2 -5x+7}{x-3}`
    - web đang hiện : `y=f(x) =\frac{x^{2} -5x+7 x-3}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=4e6f9fffb1ea` (nguồn: mtef)

- **Đoạn:** …Ta có .…
  - Công thức đọc được: `f(x) =\frac{x^{2} -5x+7 x-3}{}=x-2+\frac{1}{x-3}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f(x) =\frac{x^2 -5x+7}{x-3}=x-2+\frac{1}{x-3}`
    - web đang hiện : `f(x) =\frac{x^{2} -5x+7 x-3}{}=x-2+\frac{1}{x-3}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=505c25b5d890` (nguồn: mtef)

- **Đoạn:** …Do đó .…
  - Công thức đọc được: `\lim\limits_{ }x\to +\infty [f(x) - (x-2) ]=\lim\limits_{ }x\to +\infty \left[\frac{x^{2}}{-5x+7 x-3}-(x-2)\right]`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\lim\limits_{ }x\to +\infty [f(x) - (x-2) ]=\lim\limits_{ }x\to +\infty \left[\frac{x^2 -5x+7}{x-3}-(x-2)\right]`
    - web đang hiện : `\lim\limits_{ }x\to +\infty [f(x) - (x-2) ]=\lim\limits_{ }x\to +\infty \left[\frac{x^{2}}{-5x+7 x-3}-(x-2)\right]`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=510e3f109856` (nguồn: mtef)

- **Đoạn:** …Ta thấy và nên đồ thị hàm số có đường tiệm cận đứng .…
  - Công thức đọc được: `-2^{2} +4.2+3\ne 0`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `-2^{2+4.2+3\ne 0}`
    - web đang hiện : `-2^{2} +4.2+3\ne 0`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b8715f556d85` (nguồn: mtef)

## Toán 12/Toán 12/Toán 12_Bài 4 (Khảo sát sự biến thiên và vẽ đồ thị của hàm số).docx

112 công thức:

- **Đoạn:** …a) Đồ thị hàm số…
  - Công thức đọc được: `y=ax^{3} +bx^{2} +cx+d(a\ne 0)`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^3 +b x^2 +cx+d(a\ne 0)`
    - web đang hiện : `y=ax^{3} +bx^{2} +cx+d(a\ne 0)`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b4e1f0cb330f` (nguồn: mtef)

- **Đoạn:** …c) Đồ thị của hàm số phân thức (, đa thức tử không chia hết cho đa thức mẫu):…
  - Công thức đọc được: `y=\frac{ax^{2} +bx+c px+q}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{ax^2 +bx+c}{px+q}`
    - web đang hiện : `y=\frac{ax^{2} +bx+c px+q}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=660716295568` (nguồn: mtef)

- **Đoạn:** …Hàm số bậc ba…
  - Công thức đọc được: `y=ax^{3} +bx^{2} +cx+d(a\ne 0)`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^3 +b x^2 +cx+d(a\ne 0)`
    - web đang hiện : `y=ax^{3} +bx^{2} +cx+d(a\ne 0)`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b4e1f0cb330f` (nguồn: mtef)

- **Đoạn:** …Hàm số phân thức (, đa thức tử không chia hết cho đa thức mẫu)…
  - Công thức đọc được: `y=\frac{ax^{2} +bx+c mx+n}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{ax^2 +bx+c}{mx+n}`
    - web đang hiện : `y=\frac{ax^{2} +bx+c mx+n}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=17a98d03e106` (nguồn: mtef)

- **Đoạn:** …Đạo hàm . Đặt .…
  - Công thức đọc được: `y' =\frac{am.x^{2} +2an.x+bn-mc}{(mx+n)^2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =\frac{am.x^2 + 2an \cdot x + bn - mc}{(mx+n)^2}`
    - web đang hiện : `y' =\frac{am.x^{2} +2an.x+bn-mc}{(mx+n)^2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=eff072800aa8` (nguồn: mtef)

- **Đoạn:** …Đạo hàm . Đặt .…
  - Công thức đọc được: `g(x) =am.x^{2} +2an.x+bn-mc`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `g(x) =am.x^2 + 2an \cdot x + bn - mc`
    - web đang hiện : `g(x) =am.x^{2} +2an.x+bn-mc`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ac104226a300` (nguồn: mtef)

- **Đoạn:** …Dấu của là dấu của .…
  - Công thức đọc được: `g(x) =am.x^{2} +2an.x+bn-mc`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `g(x) =am.x^2 + 2an \cdot x + bn - mc`
    - web đang hiện : `g(x) =am.x^{2} +2an.x+bn-mc`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ac104226a300` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{3} -3x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{3-3x}`
    - web đang hiện : `y=x^{3} -3x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=372dd985f5d4` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=-x^{3} +3x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^{3+3x}`
    - web đang hiện : `y=-x^{3} +3x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=263b038753a1` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{3} -3x^{2+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 -3 x^2 +1`
    - web đang hiện : `y=x^{3} -3x^{2+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=80ff60f05db9` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=-x^{3} +3x^{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^3 +3 x^2`
    - web đang hiện : `y=-x^{3} +3x^{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=0351eea00241` (nguồn: mtef)

- **Đoạn:** …Đường cong có dạng của đồ thị hàm số bậc với hệ số nên chỉ có hàm số thỏa yêu cầu bài toán.…
  - Công thức đọc được: `y=x^{3} -3x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{3-3x}`
    - web đang hiện : `y=x^{3} -3x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=372dd985f5d4` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `y=-x^{3} -3x^{2-2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^3 -3 x^2 -2.`
    - web đang hiện : `y=-x^{3} -3x^{2-2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=a2e82afff3d4` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `y=x^{3} +3x^{2-2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 +3 x^2 -2.`
    - web đang hiện : `y=x^{3} +3x^{2-2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=783d5ce3edd8` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `y=-x^{3} +3x^{2-2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^3 +3 x^2 -2`
    - web đang hiện : `y=-x^{3} +3x^{2-2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=45d70dc58eaa` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `y=x^{3} -3x^{2-2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 -3 x^2 -2`
    - web đang hiện : `y=x^{3} -3x^{2-2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ec8b008f0a5b` (nguồn: mtef)

- **Đoạn:** …Câu 4. Hình nào dưới đây là dạng đồ thị của hàm số ?…
  - Công thức đọc được: `y=-x^{3} +3x^{2-2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^3 +3 x^2 -2`
    - web đang hiện : `y=-x^{3} +3x^{2-2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=45d70dc58eaa` (nguồn: mtef)

- **Đoạn:** …Vì hàm số có nên nhánh cuối đồ thị đi xuống, suy ra loại (II).…
  - Công thức đọc được: `y=-x^{3} +3x^{2-2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^3 +3 x^2 -2`
    - web đang hiện : `y=-x^{3} +3x^{2-2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=45d70dc58eaa` (nguồn: mtef)

- **Đoạn:** …Đồ thị cắt trục tung tại điểm có tung độ bằng nên chọn (I).…
  - Công thức đọc được: `y=-x^{3} +3x^{2-2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^3 +3 x^2 -2`
    - web đang hiện : `y=-x^{3} +3x^{2-2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=45d70dc58eaa` (nguồn: mtef)

- **Đoạn:** …Câu 6. Cho hàm số có đồ thị như hình bên. Mệnh đề nào dưới đây đúng?…
  - Công thức đọc được: `y=ax^{3} +3x+d(a;d\in \mathbb{R} )`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^{3+3x+d(a;d\in \mathbb{R} )}`
    - web đang hiện : `y=ax^{3} +3x+d(a;d\in \mathbb{R} )`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c6ee8708270d` (nguồn: mtef)

- **Đoạn:** …A. B.…
  - Công thức đọc được: `y=x^{4} -2x^{2-2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^4 -2 x^2 -2`
    - web đang hiện : `y=x^{4} -2x^{2-2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=024bec29432a` (nguồn: mtef)

- **Đoạn:** …A. B.…
  - Công thức đọc được: `y=-x^{3} +2x^{2-2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^3 +2 x^2 -2`
    - web đang hiện : `y=-x^{3} +2x^{2-2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=98d148150f25` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `y=x^{3} -3x^{2-2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 -3 x^2 -2`
    - web đang hiện : `y=x^{3} -3x^{2-2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ec8b008f0a5b` (nguồn: mtef)

- **Đoạn:** …C. D.…
  - Công thức đọc được: `y=-x^{4} +2x^{2-2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^4 +2 x^2 -2`
    - web đang hiện : `y=-x^{4} +2x^{2-2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=5ce57c4fcbe5` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=-x^{4} +2x^{2-1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^4 +2 x^2 -1`
    - web đang hiện : `y=-x^{4} +2x^{2-1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c0842d82fb0f` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{4} -2x^{2-1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^4 -2 x^2 -1`
    - web đang hiện : `y=x^{4} -2x^{2-1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=626b830b8e62` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{3} -3x^{2-1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 -3 x^2 -1`
    - web đang hiện : `y=x^{3} -3x^{2-1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=fc83b2b3a596` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=-x^{3} +3x^{2-1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^3 +3 x^2 -1`
    - web đang hiện : `y=-x^{3} +3x^{2-1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=81de1865a9a6` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `y=x^{4} +x^{2+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{4+x^{2+1}}`
    - web đang hiện : `y=x^{4} +x^{2+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=bd2e8031b67f` (nguồn: mtef)

- **Đoạn:** …A. B. C. D.…
  - Công thức đọc được: `y=x^{3} -3x-1`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{3-3x-1}`
    - web đang hiện : `y=x^{3} -3x-1`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f60e4739746b` (nguồn: mtef)

- **Đoạn:** …A. B. C. D. .…
  - Công thức đọc được: `y=-x^{3} +3x^{2+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^3 +3 x^2 +1`
    - web đang hiện : `y=-x^{3} +3x^{2+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=bf791ac64c99` (nguồn: mtef)

- **Đoạn:** …A. B. C. D. .…
  - Công thức đọc được: `y=x^{3} -3x^{2+3}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 -3 x^2 +3`
    - web đang hiện : `y=x^{3} -3x^{2+3}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=e269779f8bc2` (nguồn: mtef)

- **Đoạn:** …A. B. C. D. .…
  - Công thức đọc được: `y=-x^{4} +2x^{2+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^4 +2 x^2 +1`
    - web đang hiện : `y=-x^{4} +2x^{2+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=441d72b9fef6` (nguồn: mtef)

- **Đoạn:** …A. B. C. D. .…
  - Công thức đọc được: `y=x^{4} -2x^{2+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^4 -2 x^2 +1`
    - web đang hiện : `y=x^{4} -2x^{2+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=7040e82f421d` (nguồn: mtef)

- **Đoạn:** …Dựa vào đồ thị ta thấy đây là hình ảnh đồ thị của hàm số bậc ba nên loại đáp án C, D; Mặt khác dựa vào đồ thị ta có nên hệ số của dương nên ta chọn đá…
  - Công thức đọc được: `y=x^{3} -3x^{2+3}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 -3 x^2 +3`
    - web đang hiện : `y=x^{3} -3x^{2+3}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=e269779f8bc2` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{3} +2x+1`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{3+2x+1}`
    - web đang hiện : `y=x^{3} +2x+1`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=7f134a2ca4fb` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{3} -2x^{2+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 -2 x^2 +1`
    - web đang hiện : `y=x^{3} -2x^{2+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=8f2eed91ead8` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{3} -2x+1`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{3-2x+1}`
    - web đang hiện : `y=x^{3} -2x+1`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c29095982456` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=-x^{3} +2x+1`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^{3+2x+1}`
    - web đang hiện : `y=-x^{3} +2x+1`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=15e29aa2c9c4` (nguồn: mtef)

- **Đoạn:** …Xét phương án có , hàm số không có cực tri, loại phương án .…
  - Công thức đọc được: `y' =3x^{2} +2>0,\forall x\in \mathbb{R}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =3x^{2+2>0,\forall x\in \mathbb{R} }`
    - web đang hiện : `y' =3x^{2} +2>0,\forall x\in \mathbb{R}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=97e04170c883` (nguồn: mtef)

- **Đoạn:** …Xét phương án có và đổi dấu khi đi qua các điểm nên hàm số đạt cực tri tại và , loại phương án .…
  - Công thức đọc được: `y' =3x^{2} -6x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =3x^{2-6x}`
    - web đang hiện : `y' =3x^{2} -6x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=6ad35b69a735` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{4} -3x^{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^4 -3 x^2`
    - web đang hiện : `y=x^{4} -3x^{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=de6100e06bbf` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{3} -3x^{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 -3 x^2`
    - web đang hiện : `y=x^{3} -3x^{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=dc82ae1e1a20` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=-x^{3} -2x+\frac{1}{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^{3-2x+\frac{1}{2}}`
    - web đang hiện : `y=-x^{3} -2x+\frac{1}{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c387a3fb663c` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{3} -2x+\frac{1}{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{3-2x+\frac{1}{2}}`
    - web đang hiện : `y=x^{3} -2x+\frac{1}{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=310e320e600d` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=-x^{4} +2x^{2+\frac{1}{2}}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^4 +2 x^2 +\frac{1}{2}`
    - web đang hiện : `y=-x^{4} +2x^{2+\frac{1}{2}}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=948126f14c53` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{4} +2x^{2+\frac{1}{2}}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^4 +2 x^2 +\frac{1}{2}`
    - web đang hiện : `y=x^{4} +2x^{2+\frac{1}{2}}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=2d75dee71fe6` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{4} -2x^{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^4 -2 x^2`
    - web đang hiện : `y=x^{4} -2x^{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b872214712d6` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=-x^{3} +3x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^{3+3x}`
    - web đang hiện : `y=-x^{3} +3x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=263b038753a1` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=-x^{4} +2x^{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^4 +2 x^2`
    - web đang hiện : `y=-x^{4} +2x^{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c3aed7b7e0e7` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{3} -3x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{3-3x}`
    - web đang hiện : `y=x^{3} -3x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=372dd985f5d4` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{x^{2} -3x+4 -x-4}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^2 -3x+4}{-x-4}`
    - web đang hiện : `y=\frac{x^{2} -3x+4 -x-4}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ccfb5b3b7255` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{x^{2} -4x+4 -x-4}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^2 -4x+4}{-x-4}`
    - web đang hiện : `y=\frac{x^{2} -4x+4 -x-4}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b2ab728a646c` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{x^{2} -5x+4 x+4}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^2 -5x+4}{x+4}`
    - web đang hiện : `y=\frac{x^{2} -5x+4 x+4}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ab73b2152572` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{x^{2} -4x+4 x+4}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^2 -4x+4}{x+4}`
    - web đang hiện : `y=\frac{x^{2} -4x+4 x+4}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=2af0e3381f3d` (nguồn: mtef)

- **Đoạn:** …Điểm cực đại và điểm cực tiểu . Do đó hàm số cần tìm là…
  - Công thức đọc được: `y=\frac{x^{2} -4x+4 -x-4}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^2 -4x+4}{-x-4}`
    - web đang hiện : `y=\frac{x^{2} -4x+4 -x-4}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b2ab728a646c` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{3} -3x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{3-3x}`
    - web đang hiện : `y=x^{3} -3x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=372dd985f5d4` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=x^{2} -2x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^{2-2x}`
    - web đang hiện : `y=x^{2} -2x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=833e03238c4f` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=-x^{3} +3x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^{3+3x}`
    - web đang hiện : `y=-x^{3} +3x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=263b038753a1` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=-x^{2} +2x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^{2+2x}`
    - web đang hiện : `y=-x^{2} +2x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b9a0fee50467` (nguồn: mtef)

- **Đoạn:** …Dựa vào bảng biến thiên trên, ta nhận thấy đây là hàm số bậc ba có dạng với .…
  - Công thức đọc được: `y=ax^{3} +bx^{2} +cx+d`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^3 +b x^2 +cx+d`
    - web đang hiện : `y=ax^{3} +bx^{2} +cx+d`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f3246ef70850` (nguồn: mtef)

- **Đoạn:** …Mà .…
  - Công thức đọc được: `\lim\limits_{ }x\to +\infty (ax^{3} +bx^{2} +cx+d =-\infty )`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\lim\limits_{ }x\to +\infty (ax^3 +b x^2 +cx+d=-\infty )`
    - web đang hiện : `\lim\limits_{ }x\to +\infty (ax^{3} +bx^{2} +cx+d =-\infty )`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=a775fb739326` (nguồn: mtef)

- **Đoạn:** …Do đó có duy nhất hàm số thoả mãn.…
  - Công thức đọc được: `y=-x^{3} +3x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^{3+3x}`
    - web đang hiện : `y=-x^{3} +3x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=263b038753a1` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{2x^{2} -6x+2 x-3}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{2x^2 -6x+2}{x-3}`
    - web đang hiện : `y=\frac{2x^{2} -6x+2 x-3}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=70b88e0f34bf` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{2x^{2} -6x+2 x+3}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{2x^2 -6x+2}{x+3}`
    - web đang hiện : `y=\frac{2x^{2} -6x+2 x+3}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=dd2d9b15200f` (nguồn: mtef)

- **Đoạn:** …Câu 1. Cho hàm số có bảng biến thiên như sau:…
  - Công thức đọc được: `f(x) =ax^{3} +bx^{2} +cx+d(a,b,c,d\in \mathbb{R} )`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `f(x) =ax^3 +b x^2 +cx+d(a,b,c,d\in \mathbb{R} )`
    - web đang hiện : `f(x) =ax^{3} +bx^{2} +cx+d(a,b,c,d\in \mathbb{R} )`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=2ebf76f36b6b` (nguồn: mtef)

- **Đoạn:** …Câu 2. Cho hàm số có đồ thị như hình vẽ dưới đây. Chọn khẳng định đúng về dấu của , , , ?…
  - Công thức đọc được: `y=ax^{3} +bx^{2} +cx+d(a\ne 0)`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^3 +b x^2 +cx+d(a\ne 0)`
    - web đang hiện : `y=ax^{3} +bx^{2} +cx+d(a\ne 0)`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=b4e1f0cb330f` (nguồn: mtef)

- **Đoạn:** …B. .…
  - Công thức đọc được: `y=-2x^{3} +x^{2}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-2x^{3+x^{2}}`
    - web đang hiện : `y=-2x^{3} +x^{2}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=cc0b556de976` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{2x^{2} +3x+1 x+1}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{2x^2 +3x+1}{x+1}`
    - web đang hiện : `y=\frac{2x^{2} +3x+1 x+1}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=936b274c471f` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{x^{2} +x+4 x+1}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^2 +x+4}{x+1}`
    - web đang hiện : `y=\frac{x^{2} +x+4 x+1}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=6c53a8128c9a` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{-x^{2} -3x+10 x+1}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{-x^2 -3x+10}{x+1}`
    - web đang hiện : `y=\frac{-x^{2} -3x+10 x+1}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=a72439b4fede` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{3x^{2} +5x-2 x+1}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{3x^2 +5x-2}{x+1}`
    - web đang hiện : `y=\frac{3x^{2} +5x-2 x+1}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=8c2a1ab5c56d` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{2x^{2} -9x+10 -x+2}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{2x^2 -9x+10}{-x+2}`
    - web đang hiện : `y=\frac{2x^{2} -9x+10 -x+2}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=d51f7f3e1704` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{2x^{2} -9x+10 x+2}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{2x^2 -9x+10}{x+2}`
    - web đang hiện : `y=\frac{2x^{2} -9x+10 x+2}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=8f0ed1334932` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{x^{2} -5x+7 x+2}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^2 -5x+7}{x+2}`
    - web đang hiện : `y=\frac{x^{2} -5x+7 x+2}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=2d5de2e3badc` (nguồn: mtef)

- **Đoạn:** …A. . B. . C. . D. .…
  - Công thức đọc được: `y=\frac{x^{2} -5x+7 -x+2}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{x^2 -5x+7}{-x+2}`
    - web đang hiện : `y=\frac{x^{2} -5x+7 -x+2}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=cd90b187431d` (nguồn: mtef)

- **Đoạn:** …Câu 12. Cho hàm số có đồ thị…
  - Công thức đọc được: `y=\frac{-x^{2} +x+1 x+1}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{-x^2 +x+1}{x+1}`
    - web đang hiện : `y=\frac{-x^{2} +x+1 x+1}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=2a50e7c3c081` (nguồn: mtef)

- **Đoạn:** …Ta có…
  - Công thức đọc được: `y=\frac{-x^{2} +x+1 x+1}{}=-x+2-\frac{1}{x+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{-x^2 +x+1}{x+1}=-x+2-\frac{1}{x+1}`
    - web đang hiện : `y=\frac{-x^{2} +x+1 x+1}{}=-x+2-\frac{1}{x+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=67cc04485521` (nguồn: mtef)

- **Đoạn:** …Mặt khác,…
  - Công thức đọc được: `y=0\Leftrightarrow -x^{2} +x+1=0(∗)`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=0\Leftrightarrow -x^{2+x+1=0(∗)}`
    - web đang hiện : `y=0\Leftrightarrow -x^{2} +x+1=0(∗)`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=21fe0c4c910d` (nguồn: mtef)

- **Đoạn:** …a) Hình 1 là đồ thị hàm số bậc ba có hệ số và…
  - Công thức đọc được: `y=ax^{3} +bx^{2} +cx+d`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^3 +b x^2 +cx+d`
    - web đang hiện : `y=ax^{3} +bx^{2} +cx+d`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f3246ef70850` (nguồn: mtef)

- **Đoạn:** …c) Hình 3 là đồ thị hàm số có dạng với và có điểm cực đại của đồ thị hàm số là…
  - Công thức đọc được: `y=\frac{ax^{2} +bx+c mx+n}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{ax^2 +bx+c}{mx+n}`
    - web đang hiện : `y=\frac{ax^{2} +bx+c mx+n}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=17a98d03e106` (nguồn: mtef)

- **Đoạn:** …(a) Hình 1 là đồ thị hàm số bậc ba có hệ số và…
  - Công thức đọc được: `y=ax^{3} +bx^{2} +cx+d`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^3 +b x^2 +cx+d`
    - web đang hiện : `y=ax^{3} +bx^{2} +cx+d`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f3246ef70850` (nguồn: mtef)

- **Đoạn:** …(c) Hình 3 là đồ thị hàm số có dạng với và có điểm cực đại của đồ thị hàm số là…
  - Công thức đọc được: `y=\frac{ax^{2} +bx+c mx+n}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{ax^2 +bx+c}{mx+n}`
    - web đang hiện : `y=\frac{ax^{2} +bx+c mx+n}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=17a98d03e106` (nguồn: mtef)

- **Đoạn:** …Dễ thấy bảng biến thiên của Hình 3 là dạng đồ thị hàm số với và có điểm đại của đồ thị hàm số là…
  - Công thức đọc được: `y=\frac{ax^{2} +bx+c mx+n}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{ax^2 +bx+c}{mx+n}`
    - web đang hiện : `y=\frac{ax^{2} +bx+c mx+n}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=17a98d03e106` (nguồn: mtef)

- **Đoạn:** …Câu 14. Cho hai đồ thị hàm số hình 1 là: và hình 2 là:…
  - Công thức đọc được: `y=ax^{3} +bx^{2} +cx+d`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^3 +b x^2 +cx+d`
    - web đang hiện : `y=ax^{3} +bx^{2} +cx+d`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f3246ef70850` (nguồn: mtef)

- **Đoạn:** …c) Hình 2 có đồ thị hàm số có dạng là:…
  - Công thức đọc được: `y=-x^{3} +3x^{2-1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^3 +3 x^2 -1`
    - web đang hiện : `y=-x^{3} +3x^{2-1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=81de1865a9a6` (nguồn: mtef)

- **Đoạn:** …(c) Hình 2 có đồ thị hàm số có dạng là:…
  - Công thức đọc được: `y=-x^{3} +3x^{2-1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^3 +3 x^2 -1`
    - web đang hiện : `y=-x^{3} +3x^{2-1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=81de1865a9a6` (nguồn: mtef)

- **Đoạn:** …Độ thị hàm số có hai điểm cực trị ;…
  - Công thức đọc được: `y=ax^{3} +bx^{2} +cx+d`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^3 +b x^2 +cx+d`
    - web đang hiện : `y=ax^{3} +bx^{2} +cx+d`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f3246ef70850` (nguồn: mtef)

- **Đoạn:** …Suy ra ta có: , với…
  - Công thức đọc được: `y' =3ax^{2} +2bx+c`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =3ax^2 + 2bx + c`
    - web đang hiện : `y' =3ax^{2} +2bx+c`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ecaee68191d5` (nguồn: mtef)

- **Đoạn:** _(không có chữ)_
  - Công thức đọc được: `\Rightarrow y=-x^{3} +3x^{2-1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\Rightarrow y=-x^3 +3 x^2 -1`
    - web đang hiện : `\Rightarrow y=-x^{3} +3x^{2-1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=db3875984ca9` (nguồn: mtef)

- **Đoạn:** …Ta có đồ thị hàm số bậc là có các hệ số…
  - Công thức đọc được: `y=-x^{3} +3x^{2-1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=-x^3 +3 x^2 -1`
    - web đang hiện : `y=-x^{3} +3x^{2-1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=81de1865a9a6` (nguồn: mtef)

- **Đoạn:** …Câu 15. . Cho hàm số , có đồ thị (C). Khi đó:…
  - Công thức đọc được: `y=f(x) =x^{3} -3x^{2+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=f(x) =x^3 -3 x^2 +1`
    - web đang hiện : `y=f(x) =x^{3} -3x^{2+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=5dbcf15d24d9` (nguồn: mtef)

- **Đoạn:** …Xét hàm số có tập xác định .…
  - Công thức đọc được: `y=x^{3} -3x^{2+1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 -3 x^2 +1`
    - web đang hiện : `y=x^{3} -3x^{2+1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=80ff60f05db9` (nguồn: mtef)

- **Đoạn:** …Có : ;…
  - Công thức đọc được: `y' =3x^{2} -6x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =3x^{2-6x}`
    - web đang hiện : `y' =3x^{2} -6x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=6ad35b69a735` (nguồn: mtef)

- **Đoạn:** …Câu 1. Cho hàm số có đồ thị là .…
  - Công thức đọc được: `y=\frac{-x^{2} -3x+4 x-3}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=\frac{-x^2 -3x+4}{x-3}`
    - web đang hiện : `y=\frac{-x^{2} -3x+4 x-3}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f5a6cd82b65e` (nguồn: mtef)

- **Đoạn:** …Mặt khác, (*)…
  - Công thức đọc được: `y' =\frac{-x+6x+5}{(x-3)^{2}} =0\Leftrightarrow x^{2} -6x-5=0`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =\frac{-x+6x+5}{(x-3)^{2}} =0\Leftrightarrow x^{2-6x-5=0}`
    - web đang hiện : `y' =\frac{-x+6x+5}{(x-3)^{2}} =0\Leftrightarrow x^{2} -6x-5=0`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ce949d4c2782` (nguồn: mtef)

- **Đoạn:** …Hơn nữa, .…
  - Công thức đọc được: `y=0\Leftrightarrow -x^{2} -3x+4=0`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=0\Leftrightarrow -x^{2-3x+4=0}`
    - web đang hiện : `y=0\Leftrightarrow -x^{2} -3x+4=0`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=45c4302cd0f3` (nguồn: mtef)

- **Đoạn:** …Câu 2. Cho hàm số , có đồ thị (C). Khi đó:…
  - Công thức đọc được: `y=f(x) =x^{3} -3x^{2-1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=f(x) =x^3 -3 x^2 -1`
    - web đang hiện : `y=f(x) =x^{3} -3x^{2-1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=e6877a1847ea` (nguồn: mtef)

- **Đoạn:** …Xét hàm số có tập xác định .…
  - Công thức đọc được: `y=f(x) =x^{3} -3x^{2-1}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=f(x) =x^3 -3 x^2 -1`
    - web đang hiện : `y=f(x) =x^{3} -3x^{2-1}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=e6877a1847ea` (nguồn: mtef)

- **Đoạn:** …Có : ;…
  - Công thức đọc được: `y' =3x^{2} -6x`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =3x^{2-6x}`
    - web đang hiện : `y' =3x^{2} -6x`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=6ad35b69a735` (nguồn: mtef)

- **Đoạn:** …Câu 3. Cho hàm số . Khi đó…
  - Công thức đọc được: `y=f(x) =\frac{x^{2} -x-1 x-2}{}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=f(x) =\frac{x^2 -x-1}{x-2}`
    - web đang hiện : `y=f(x) =\frac{x^{2} -x-1 x-2}{}`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=2e1c817db00b` (nguồn: mtef)

- **Đoạn:** …a) Ta có và ; nên đồ thị của hàm số không có tiệm cận ngang.…
  - Công thức đọc được: `\lim\limits_{ }x\to +\infty y=\lim\limits_{ }x\to +\infty \frac{x^{2}}{-x-1 x-2}=+\infty`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\lim\limits_{ }x\to +\infty y=\lim\limits_{ }x\to +\infty \frac{x^2 -x-1}{x-2}=+\infty`
    - web đang hiện : `\lim\limits_{ }x\to +\infty y=\lim\limits_{ }x\to +\infty \frac{x^{2}}{-x-1 x-2}=+\infty`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f724af9b5038` (nguồn: mtef)

- **Đoạn:** …a) Ta có và ; nên đồ thị của hàm số không có tiệm cận ngang.…
  - Công thức đọc được: `\lim\limits_{ }x\to -\infty y=\lim\limits_{ }x\to -\infty \frac{x^{2}}{-x-1 x-2}=-\infty`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\lim\limits_{ }x\to -\infty y=\lim\limits_{ }x\to -\infty \frac{x^2 -x-1}{x-2}=-\infty`
    - web đang hiện : `\lim\limits_{ }x\to -\infty y=\lim\limits_{ }x\to -\infty \frac{x^{2}}{-x-1 x-2}=-\infty`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=c2877e9ada18` (nguồn: mtef)

- **Đoạn:** …c) Ta có…
  - Công thức đọc được: `y=0\Leftrightarrow \frac{x^{2} -x-1 x-2}{}=0\Leftrightarrow \left[x=\frac{1-\sqrt[5]{2}}{}x=\frac{1+\sqrt[5]{2}}{}[\right]`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=0\Leftrightarrow \frac{x^2 -x-1}{x-2}=0\Leftrightarrow \left[x=\frac{1-\sqrt[5]{2}}{}x=\frac{1+\sqrt[5]{2}}{}[\right]`
    - web đang hiện : `y=0\Leftrightarrow \frac{x^{2} -x-1 x-2}{}=0\Leftrightarrow \left[x=\frac{1-\sqrt[5]{2}}{}x=\frac{1+\sqrt[5]{2}}{}[\right]`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=0a1b38840126` (nguồn: mtef)

- **Đoạn:** …d) Ta có:…
  - Công thức đọc được: `y'=\frac{x^{2} -4x+3}{(x-2)^2}\Rightarrow y'=0\Leftrightarrow [x=1\Rightarrow x=3\Rightarrow ][`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y'=\frac{x^{2-4x+3}}{(x-2)^2}\Rightarrow y'=0\Leftrightarrow [x=1\Rightarrow x=3\Rightarrow ][`
    - web đang hiện : `y'=\frac{x^{2} -4x+3}{(x-2)^2}\Rightarrow y'=0\Leftrightarrow [x=1\Rightarrow x=3\Rightarrow ][`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=d77aec5d07c8` (nguồn: mtef)

- **Đoạn:** …Câu 5. Cho hàm số có đồ thị là đường cong trong hình bên.…
  - Công thức đọc được: `y=ax^{3} +bx^{2} +cx+d`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^3 +b x^2 +cx+d`
    - web đang hiện : `y=ax^{3} +bx^{2} +cx+d`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f3246ef70850` (nguồn: mtef)

- **Đoạn:** …Gọi , là hoành độ hai điểm cực trị của hàm số suy ra , nghiệm phương trình nên theo định lý Viet:…
  - Công thức đọc được: `y' =3ax^{2} +2bx+c=0`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y' =3ax^2 + 2bx + c=0`
    - web đang hiện : `y' =3ax^{2} +2bx+c=0`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=ad8af6374d22` (nguồn: mtef)

- **Đoạn:** …Câu 6. Biết đồ thị hàm số đi qua điểm và có điểm cực trị . Tính giá trị biểu thức .…
  - Công thức đọc được: `y=x^{3} +ax^{2} +bx+c`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 +a x^2 +bx+c`
    - web đang hiện : `y=x^{3} +ax^{2} +bx+c`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=6d0cff4c3a4b` (nguồn: mtef)

- **Đoạn:** …Ta có .…
  - Công thức đọc được: `y=x^{3} +ax^{2} +bx+c\Rightarrow y' =3x^{2} +2ax+b`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=x^3 +a x^2 +bx+c\Rightarrow y'=3x^{2+2ax+b}`
    - web đang hiện : `y=x^{3} +ax^{2} +bx+c\Rightarrow y' =3x^{2} +2ax+b`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=21dab8a905a7` (nguồn: mtef)

- **Đoạn:** …Dấu “=” xảy ra .…
  - Công thức đọc được: `\begin{array}{l}\Leftrightarrow |m+1| =\frac{1}{|m+1|} \Leftrightarrow |m+1|\\^{2} =1\Leftrightarrow [m=0\Rightarrow M(0;1)m=-2\Rightarrow M(-2;3)] [\end{array}`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `\begin{array}{l}\Leftrightarrow |m+1| =\frac{1}{|m+1|} \Leftrightarrow |m+1|\\^{2=1\Leftrightarrow [m=0\Rightarrow M(0;1)m=-2\Rightarrow M(-2;3)]} [\e`
    - web đang hiện : `\begin{array}{l}\Leftrightarrow |m+1| =\frac{1}{|m+1|} \Leftrightarrow |m+1|\\^{2} =1\Leftrightarrow [m=0\Rightarrow M(0;1)m=-2\Rightarrow M(-2;3)] [\`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=de0440346784` (nguồn: mtef)

- **Đoạn:** …Câu 8. Cho hàm số có bảng biến thiên như sau:…
  - Công thức đọc được: `y=ax^{3} +bx^{2} +cx+d`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y=ax^3 +b x^2 +cx+d`
    - web đang hiện : `y=ax^{3} +bx^{2} +cx+d`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=f3246ef70850` (nguồn: mtef)

- **Đoạn:** …Ta có:…
  - Công thức đọc được: `y'=3ax^{2} +2bx+c`
  - ⚠️ **Pipeline đã tự đoán** — hiển thị sạch nhưng có thể SAI:
    - trong file Word: `y'=3ax^2 + 2bx + c`
    - web đang hiện : `y'=3ax^{2} +2bx+c`
  - Dấu hiệu: auto_repaired_exponent
  - `sha1=6e6773acc293` (nguồn: mtef)
