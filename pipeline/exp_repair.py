"""Sửa lỗi "số mũ nuốt biểu thức" (swallowed exponent).

BỐI CẢNH
--------
Giáo viên soạn MathType: gõ ``6x``, bấm Ctrl+H vào ô số mũ, gõ ``2``, rồi QUÊN
bấm mũi tên (→) để thoát ô số mũ, nên gõ luôn ``-7x+1=0`` ngay trong ô số mũ.

MTEF nhị phân vì thế lưu ĐÚNG một template SUP có nội dung ``2-7x+1=0``.
Nghĩa là decoder KHÔNG sai — đây là **lỗi dữ liệu nguồn**, thuộc lớp
*semantic repair*, không phải *syntactic normalization*.

Hệ quả: KaTeX render **THÀNH CÔNG** (cú pháp hợp lệ) nhưng sai toán học —
cả đoạn ``-7x+1=0`` bị co nhỏ và đẩy lên cao. Đây là lỗi IM LẶNG, không có
lỗi đỏ nào để bắt, nên bắt buộc phải xử lý bằng heuristic có kiểm soát.

TRIẾT LÝ
--------
Bài toán này về bản chất là **suy diễn ý định tác giả** — không thể đúng 100%.
Vì vậy nguyên tắc là **bất đối xứng về rủi ro**:

    Để nguyên một số mũ hỏng  ->  render xấu, người dùng NHÌN THẤY ngay.
    Phá một số mũ hợp lệ      ->  công thức SAI toán học, trông vẫn bình thường.

Sai loại thứ hai tệ hơn nhiều. Nên khi không chắc: KHÔNG SỬA, đưa vào quarantine.

TÍN HIỆU NHẬN BIẾT (trigger)
---------------------------
Chỉ sửa khi có tín hiệu rõ ràng. Hai tín hiệu, cần ít nhất một:

1. **Quan hệ ở cấp ngoài cùng** của ô số mũ (``=``, ``<``, ``>``, ``\\le``,
   ``\\Leftrightarrow``, ...). Số mũ hợp lệ trong toán phổ thông gần như không
   bao giờ chứa toán tử quan hệ.

2. **Biến của atom cơ sở lặp lại trong số mũ.** Ví dụ ``6x^{2-7x+1}``: atom cơ
   sở là ``x`` và ``x`` xuất hiện lại trong số mũ -> gần như chắc chắn bị nuốt.
   Ngược lại ``x^{n-1}`` không lặp ``x`` -> hợp lệ.

   CỰC KỲ QUAN TRỌNG: phải lấy atom LIỀN KỀ dấu ``^``, không phải cả tiền tố.
   Với ``nx^{n-1}`` (đạo hàm ``(x^n)' = nx^{n-1}``) atom là ``x``, không phải
   ``{n, x}``. Nếu lấy cả tiền tố thì ``n`` sẽ khớp và PHÁ công thức hợp lệ.

CHẶN AN TOÀN
------------
Ngoài trigger, chỉ tự động sửa khi số mũ giữ lại là **literal SỐ** (``2``, ``3``,
``10``). Số mũ ký hiệu (``n``, ``k``, ``\\alpha``) quá dễ là số mũ hợp lệ nên
được đẩy vào quarantine cho người xem, không tự sửa.

ĐO TRÊN CORPUS THẬT (4.584 công thức, 11 file .docx Toán 10/11/12)
-----------------------------------------------------------------
    kích hoạt sửa            : 76 công thức (50 do biến lặp, 28 do quan hệ)
    KaTeX lỗi cứng trước/sau : 62 / 62   (đúng như dự đoán: đây là lỗi IM LẶNG)
    THOÁI TRIỂN              : 0         (không công thức nào từ đúng thành sai)

Test: xem ``tests/test_exp_repair.py`` — 8 ca phải sửa, 29 ca tuyệt đối không
được động tới (gồm ``nx^{n-1}``, ``e^{-x}``, ``2^{x-1}=8``, ``u_1 q^{n-1}``).
"""

from __future__ import annotations

import re

__all__ = ["repair_swallowed_exponent", "RepairNote"]


# Toán tử quan hệ — gần như không bao giờ có trong một số mũ hợp lệ.
_RELATIONS = [
    r"\\Leftrightarrow", r"\\Rightarrow", r"\\leftrightarrow", r"\\rightarrow",
    r"\\geqslant", r"\\leqslant", r"\\approx", r"\\equiv", r"\\neq",
    r"\\ne\b", r"\\geq", r"\\leq", r"\\ge\b", r"\\le\b", r"\\to\b",
    "=", "<", ">", "≤", "≥", "≠",
]
_RELATION_RE = re.compile("|".join(_RELATIONS))

# Số mũ "tối thiểu" hợp lệ: literal số, macro, hoặc một ký tự đơn (có thể có dấu).
_MINIMAL_EXP_RE = re.compile(r"^\s*([+-]?\s*(?:\d+|\\[a-zA-Z]+|[a-zA-Z]))")

_SUP_OPEN_RE = re.compile(r"\^\s*\{")


class RepairNote(str):
    """Ghi chú một quyết định. Dạng ``action:reason:detail``.

    action ∈ {repaired, quarantine}. Dùng cho telemetry và cổng CI.
    """


def _tokenize_depth(s: str) -> list[tuple[str, int]]:
    """Trả về [(token, depth)] với depth = độ sâu ngoặc ``{}``.

    Escape (``\\{``, ``\\}``, ``\\alpha``) được coi là một token và KHÔNG đổi
    depth — nhờ vậy ``\\{`` không bị tính là mở ngoặc nhóm.
    """
    out: list[tuple[str, int]] = []
    depth = 0
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            out.append((s[i:i + 2], depth))
            i += 2
            continue
        if c == "{":
            out.append((c, depth))
            depth += 1
        elif c == "}":
            depth -= 1
            out.append((c, depth))
        else:
            out.append((c, depth))
        i += 1
    return out


def _top_level_text(sup: str) -> str:
    """Chỉ các ký tự ở depth 0 — để dò quan hệ ở cấp ngoài cùng của số mũ."""
    return "".join(t for t, d in _tokenize_depth(sup) if d == 0)


def _has_top_level_relation(sup: str) -> bool:
    return _RELATION_RE.search(_top_level_text(sup)) is not None


def _first_top_level_additive(sup: str) -> int:
    """Vị trí ``+``/``-`` đầu tiên ở depth 0. Bỏ qua dấu ở đầu chuỗi (``e^{-x}``)."""
    idx = 0
    for tok, d in _tokenize_depth(sup):
        if idx > 0 and d == 0 and tok in ("+", "-", "–"):
            return idx
        idx += len(tok)
    return -1


def _immediate_base_atom(base: str) -> str:
    """Atom cơ sở LIỀN KỀ dấu ``^`` — chứ không phải cả tiền tố.

    ``nx^{n-1}``  -> ``x``   (nên ``n`` trong số mũ KHÔNG bị coi là lặp)
    ``6x^{...}``  -> ``x``
    ``\\sin^{...}`` -> ``\\sin`` (macro, không mang biến)
    ``(a+b)^{...}`` -> ``)``   (group, không mang biến)
    """
    b = base.rstrip()
    if not b:
        return ""
    if b[-1] in ")]}":
        return b[-1]
    m = re.search(r"(\\[a-zA-Z]+|[a-zA-Z0-9])$", b)
    return m.group(1) if m else ""


def _vars_of(expr: str) -> set[str]:
    """Tập biến (chữ cái đơn), sau khi bỏ tên macro."""
    return set(re.findall(r"[a-zA-Z]", re.sub(r"\\[a-zA-Z]+", " ", expr)))


def _base_atom_vars(base: str) -> set[str]:
    atom = _immediate_base_atom(base)
    if atom.startswith("\\"):
        return set()
    return _vars_of(atom)


def _match_closing_brace(s: str, start: int) -> int:
    """Từ vị trí ngay sau ``{``, trả về index NGAY SAU ``}`` khớp; -1 nếu hở."""
    depth, j = 1, start
    while j < len(s):
        if s[j] == "\\":
            j += 2
            continue
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return -1


def repair_swallowed_exponent(latex: str) -> tuple[str, list[RepairNote]]:
    """Sửa các ô số mũ đã "nuốt" phần còn lại của biểu thức.

    Trả về ``(latex_đã_sửa, notes)``. Nếu không có gì đáng sửa thì trả về
    nguyên bản và ``notes`` rỗng — hàm này an toàn để gọi trên mọi công thức.

    Idempotent: gọi lại trên kết quả không làm thay đổi thêm.
    """
    notes: list[RepairNote] = []
    out: list[str] = []
    i = 0

    while i < len(latex):
        m = _SUP_OPEN_RE.match(latex, i)
        if not m:
            out.append(latex[i])
            i += 1
            continue

        end = _match_closing_brace(latex, m.end())
        if end < 0:                                  # ngoặc hở -> để tầng khác lo
            out.append(latex[i])
            i += 1
            continue

        sup = latex[m.end():end - 1]
        base = "".join(out)

        has_rel = _has_top_level_relation(sup)
        add_at = _first_top_level_additive(sup)
        recurs = bool(_base_atom_vars(base) & _vars_of(sup)) if base else False

        # ---- trigger: cần tín hiệu rõ ràng, và cần có chỗ để cắt ----
        if not ((has_rel and add_at > 0) or (add_at > 0 and recurs)):
            out.append(latex[i:end])
            i = end
            continue

        me = _MINIMAL_EXP_RE.match(sup)
        if not me:
            notes.append(RepairNote(f"quarantine:no_minimal_exp:{sup[:48]}"))
            out.append(latex[i:end])
            i = end
            continue

        exp = me.group(1).strip()
        rest = sup[me.end():].strip()

        if not rest:
            out.append(latex[i:end])
            i = end
            continue

        # ---- chặn an toàn: chỉ tự sửa khi số mũ là literal SỐ ----
        if not exp.lstrip("+-").strip().isdigit():
            notes.append(RepairNote(f"quarantine:symbolic_exp:{exp}|{sup[:48]}"))
            out.append(latex[i:end])
            i = end
            continue

        reason = "relation" if has_rel else "base_var_recurrence"
        notes.append(RepairNote(f"repaired:{reason}:exp={exp}|{sup[:48]}"))
        out.append("^{" + exp + "} " + rest + " ")
        i = end

    return "".join(out), notes
