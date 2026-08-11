"""Cắt vùng lý thuyết và dựng cây mục con nhiều cấp.

Không dùng Heading style vì đa số file trong corpus dùng Normal + bold thủ công
(Toán 12 / Địa 11 / Toán 10 có 0 heading style).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .docxast import Block, Inline


def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.replace("đ", "d").replace("Đ", "D")).strip().lower()


# Marker mở/đóng vùng lý thuyết — gom từ toàn bộ 46 file.
RE_START = re.compile(
    r"^(?:phan\s+)?[ab]\s*[.\-–:)]?\s*"
    r"(kien thuc trong tam|ly thuyet|tom tat ly thuyet|tom tat kien thuc"
    r"|phan li thuyet|phan ly thuyet)|^kien thuc trong tam\b")
# Bắt buộc chứa cụm "bai tap": tránh cắt nhầm ở mục 'B. PEPTIDE' (Hóa 12 bài 9).
RE_END = re.compile(r"^(?:[ab]\s*[.\-–:)]?\s*)?(phan\s+)?bai tap\b")

# Thứ tự phải khớp: roman đứng trước alpha để "I." không bị bắt thành chữ cái.
NUMBERING = [
    ("roman", re.compile(r"^((?:X{0,2}(?:IX|IV|V?I{0,3}))\s*[.)\-–:])\s+(.*)$")),
    ("arabic", re.compile(r"^(\d{1,2}\s*[.)\-–:])\s+(.*)$")),
    ("alpha_upper", re.compile(r"^([A-Z]\s*[.)\-–:])\s+(.*)$")),
    ("alpha_lower", re.compile(r"^([a-z]\s*[.)])\s+(.*)$")),
    ("star", re.compile(r"^([*+❖])\s*(.*)$")),
    ("dash", re.compile(r"^([\-–—•])\s+(.*)$")),
]
# Quy ước SGK: A/B  >  I/II  >  1/2  >  a/b  >  *  >  -
# Gộp A. và a. vào cùng một bậc là nguyên nhân khiến "A. TÓM TẮT KIẾN THỨC"
# nhận level 2 rồi nằm ngang hàng với các mục 1./2./3. đáng lẽ là con của nó.
RANK = {"alpha_upper": 0, "roman": 1, "arabic": 2, "alpha_lower": 3,
        "star": 4, "dash": 5}

KIND_HINT = [
    ("dinh nghia", "definition"), ("dinh li", "theorem"), ("dinh ly", "theorem"),
    ("tinh chat", "property"), ("chu y", "note"), ("luu y", "note"),
    ("nhan xet", "remark"), ("vi du", "example"), ("ket luan", "summary"),
    ("quy uoc", "note"), ("he qua", "property"),
]


@dataclass
class Node:
    level: int
    numbering: str
    title: str
    kind: str = "concept"
    para_index: int = -1
    header_block: Block | None = None
    blocks: list[Block] = field(default_factory=list)
    children: list["Node"] = field(default_factory=list)


def find_theory(blocks: list[Block]) -> tuple[int, int, list[str], str]:
    """Trả (start, end, flags, heading).

    `heading` là nguyên văn tiêu đề mục A — corpus có 7 biến thể
    ("A – LÝ THUYẾT (KIẾN THỨC TRỌNG TÂM)", "A. TÓM TẮT LÝ THUYẾT", ...) và
    trước đây bị bỏ hẳn nên UniLearn không hiển thị lại được tiêu đề gốc.
    """
    flags, starts, end = [], [], len(blocks)
    for i, b in enumerate(blocks):
        if b.kind != "para":
            continue
        t = fold(b.text)
        if not t or len(t) > 80:
            continue
        if RE_START.match(t):
            starts.append(i)
        elif RE_END.match(t) and starts:
            end = i
            break
    if not starts:
        return -1, -1, ["THEORY_START_NOT_FOUND"], ""
    if len(starts) > 1:
        flags.append(f"MULTIPLE_THEORY_HEADERS:{len(starts)}")
    if end == len(blocks):
        flags.append("THEORY_END_NOT_FOUND")
    return starts[0] + 1, end, flags, blocks[starts[0]].text


def _match_num(text: str):
    for name, rx in NUMBERING:
        m = rx.match(text)
        if m and m.group(1).strip(".)-–: ") != "":
            return name, m.group(1).strip(), m.group(2).strip()
        if m and name == "star":
            return name, m.group(1).strip(), m.group(2).strip()
    return None


def is_heading(b: Block) -> bool:
    if b.kind != "para":
        return False
    t = b.text.strip()
    if not t or len(t) > 140:
        return False
    if b.style.startswith("Heading"):
        return True
    m = _match_num(t)
    if m:
        num_type = m[0]
        # Tiêu đề lớn (La Mã I., Số 1., Chữ hoa A.) có thể là heading nếu ngắn hoặc in đậm
        if num_type in ("roman", "arabic", "alpha_upper"):
            if b.bold or len(t) <= 100:
                return True
        # Tiêu đề con a), b), c) là các ý/mục nhỏ trong đoạn, không phải tiêu đề phân cấp lớn
        elif num_type in ("alpha_lower", "dash", "star"):
            return False
    if b.bold:
        if t.isupper():
            return True
        # Tiêu đề từ khóa đặc biệt (Chú ý, Lưu ý, Định lý, Định nghĩa, ...) dù có dấu ':' hay không
        if fold(t) in ("chu y", "luu y", "dinh ly", "dinh li", "dinh nghia", "tinh chat", "nhan xet"):
            return True
        # Không phân loại nhầm các mục danh sách/bước thực hiện in đậm ngắn làm heading
        if len(t) <= 80 and t.endswith(":") and not re.match(r"^\(\d+\)", t):
            return True
    return False


def _split_soft_breaks(body: list[Block]) -> list[Block]:
    """Vá lỗi soạn thảo: có file gõ cả mục lục lý thuyết bằng soft-break
    (Shift+Enter) thay vì xuống đoạn thật (Enter). Khi đó nhiều dòng tiêu đề
    in đậm ("I. Tìm hiểu chung", "2. Tác giả:...") nằm chung 1 paragraph, nên
    `Block.bold` (trung bình cả đoạn) ra False và is_heading() không thấy gì
    -> toàn bộ lý thuyết rơi vào 1 mục "Nội dung" duy nhất, không phân cấp.

    Chỉ tách khi paragraph chứa >=2 dòng thật sự giống heading (in đậm + đúng
    số thứ tự) sau khi tách theo "\\n" — tránh phá đoạn thơ/trích dẫn xuống
    dòng hợp lệ (thơ không có nhiều dòng in đậm bắt đầu bằng số thứ tự).
    """
    out: list[Block] = []
    for b in body:
        if b.kind != "para" or "\n" not in b.text:
            out.append(b)
            continue
        # QUAN TRỌNG: `_merge_text` (docxast.py) đã gộp "\n" vào chung 1 chuỗi
        # với đoạn text cùng format đứng cạnh (ví dụ toàn bộ các dòng gạch đầu
        # dòng không in đậm bị nối thành 1 inline dài chứa nhiều "\n" bên
        # trong). Nếu chỉ tìm inline nào ĐÚNG BẰNG "\n" thì bỏ lọt gần hết —
        # phải tách theo ký tự "\n" nằm trong text của TỪNG inline.
        groups: list[list] = [[]]
        for i in b.inlines:
            if i.kind != "text" or "\n" not in i.text:
                groups[-1].append(i)
                continue
            pieces = i.text.split("\n")
            for k, piece in enumerate(pieces):
                if piece:
                    groups[-1].append(Inline("text", piece, bold=i.bold,
                                              color=i.color, underline=i.underline))
                if k != len(pieces) - 1:
                    groups.append([])
        subs = []
        for g in groups:
            if not g:
                continue
            # Bỏ inline chỉ chứa khoảng trắng khi đếm — có file để lại 1 dấu
            # cách được bật in đậm ngẫu nhiên (do gõ xong rồi bấm Bold rồi mới
            # gõ tiếp), khiến dòng nội dung thường bị tính nhầm thành in đậm.
            texts = [i for i in g if i.kind == "text" and i.text.strip()]
            nt = len(texts)
            nb = sum(1 for i in texts if i.bold)
            bold = nb >= max(1, nt // 2) if nt else False
            subs.append(Block("para", inlines=g, ilvl=b.ilvl, style=b.style,
                              bold=bold, para_index=b.para_index))
        if sum(1 for s in subs if is_heading(s)) >= 2:
            out.extend(subs)
        else:
            out.append(b)
    return out


def guess_kind(title: str) -> str:
    f = fold(title)
    for key, kind in KIND_HINT:
        if f.startswith(key):
            return kind
    return "concept"


def _keep_media(b: Block, n: Node) -> None:
    """Word hay neo ảnh nổi vào paragraph tiêu đề gần nhất.

    Tiêu đề chỉ dùng làm `title`, nên nếu bỏ luôn `inlines` thì ảnh biến mất
    không dấu vết. Giữ lại media (ảnh) thành một block riêng của node.
    """
    media = [i for i in b.inlines if i.kind == "image"]
    if not media:
        return
    n.blocks.append(Block("para", inlines=media, style=b.style,
                          para_index=b.para_index))


def build_tree(blocks: list[Block], start: int, end: int) -> list[Node]:
    body = _split_soft_breaks(blocks[start:end])
    # Xác định các bậc đánh số thực sự xuất hiện -> ánh xạ về level 1..n liên tục.
    used = {_match_num(b.text)[0] for b in body if is_heading(b) and _match_num(b.text)}
    ladder = sorted(used, key=lambda k: RANK[k])
    lvl_of = {name: i + 1 for i, name in enumerate(ladder)}

    root = Node(0, "", "__root__")
    stack = [root]
    for b in body:
        if is_heading(b) and _match_num(b.text):
            name, num, title = _match_num(b.text)
            lvl = lvl_of.get(name, len(ladder) + 1)
            while len(stack) > 1 and stack[-1].level >= lvl:
                stack.pop()
            n = Node(lvl, num, title or b.text, guess_kind(title or b.text), b.para_index, header_block=b)
            stack[-1].children.append(n)
            stack.append(n)
            _keep_media(b, n)
        elif is_heading(b):
            while len(stack) > 1:
                stack.pop()
            n = Node(1, "", b.text, guess_kind(b.text), b.para_index, header_block=b)
            stack[-1].children.append(n)
            stack.append(n)
            _keep_media(b, n)
        else:
            if b.kind == "para" and not b.text and not any(
                    i.kind in ("formula", "image") for i in b.inlines):
                continue
            stack[-1].blocks.append(b)

    # Bảo vệ dữ liệu: nếu có nội dung trước heading đầu tiên, không bao giờ vứt bỏ
    if root.blocks:
        non_empty = [b for b in root.blocks if b.kind != "para" or b.text or any(
            i.kind in ("formula", "image") for i in b.inlines)]
        if non_empty:
            intro_node = Node(1, "", "", "concept", start, non_empty)
            root.children.insert(0, intro_node)

    return root.children or ([Node(1, "", "Nội dung", "concept", start,
                                   [b for b in body])] if body else [])
