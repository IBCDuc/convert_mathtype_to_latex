"""DOCX -> AST tuyến tính, giữ đúng thứ tự tài liệu.

Không hiểu ngữ nghĩa bài học ở tầng này; chỉ chuẩn hoá OOXML thành block/inline
và phân loại media (formula / figure).
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from . import mtef

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "v": "urn:schemas-microsoft-com:vml",
    "o": "urn:schemas-microsoft-com:office:office",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
W = lambda t: f"{{{NS['w']}}}{t}"          # noqa: E731
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".emf": "image/emf", ".wmf": "image/wmf",
        ".wdp": "image/vnd.ms-photo"}


@dataclass
class Inline:
    kind: str                 # text | formula | image | break
    text: str = ""
    ref: str | None = None
    bold: bool = False
    color: str | None = None   # w:color/@w:val của run, dùng để phát hiện đáp án bôi màu
    underline: bool = False    # w:u present, dùng để phát hiện đáp án gạch chân


@dataclass
class Block:
    kind: str                 # para | table
    inlines: list[Inline] = field(default_factory=list)
    ilvl: int | None = None
    style: str = "Normal"
    bold: bool = False
    rows: list = field(default_factory=list)
    para_index: int = -1

    @property
    def text(self) -> str:
        return "".join(i.text for i in self.inlines if i.kind == "text").strip()


@dataclass
class Asset:
    aid: str
    kind: str                 # formula | figure
    mime: str = ""
    data: bytes = b""
    latex: str | None = None
    source: str = ""          # tex | mtef | omml | unresolved
    confidence: float = 0.0
    sha256: str = ""
    width: int = 0
    height: int = 0


class DocxReader:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.zf = zipfile.ZipFile(self.path)
        self.rels = self._rels()
        self.assets: dict[str, Asset] = {}
        self._by_sha: dict[str, str] = {}
        self.blocks: list[Block] = []
        self._n = 0

    def _rels(self) -> dict[str, str]:
        x = etree.fromstring(self.zf.read("word/_rels/document.xml.rels"))
        return {r.get("Id"): r.get("Target") for r in x}

    # ---------------------------------------------------------------- assets
    def _part(self, rid: str) -> bytes | None:
        t = self.rels.get(rid)
        if not t:
            return None
        name = "word/" + t.lstrip("/") if not t.startswith("word/") else t
        try:
            return self.zf.read(name)
        except KeyError:
            return None

    def _add(self, kind: str, *, data: bytes = b"", mime: str = "",
             latex: str | None = None, source: str = "") -> str:
        sha = hashlib.sha256(data or (latex or "").encode()).hexdigest()
        if sha in self._by_sha:
            return self._by_sha[sha]
        self._n += 1
        aid = f"{'f' if kind == 'formula' else 'img'}{self._n}"
        # Truyền theo tên: thứ tự field của Asset đã đổi và gán vị trí từng làm
        # sha256 rơi vào confidence, khiến 20 file sai schema.
        a = Asset(aid=aid, kind=kind, mime=mime, data=data, latex=latex,
                  source=source, sha256=sha)
        if kind == "formula":
            a.confidence = mtef.confidence_of(source, set(mtef._LAST_SEL)) if latex else 0.0
        if kind == "figure" and data:
            a.width, a.height = _dims(data, mime)
        self.assets[aid] = a
        self._by_sha[sha] = aid
        return aid

    # --------------------------------------------------------------- parsing
    def parse(self) -> "DocxReader":
        root = etree.fromstring(self.zf.read("word/document.xml"))
        body = root.find(W("body"))
        idx = 0
        for el in body:
            if el.tag == W("p"):
                self.blocks.append(self._para(el, idx))
                idx += 1
            elif el.tag == W("tbl"):
                self.blocks.append(self._table(el, idx))
                idx += 1
        return self

    def _para(self, p, idx: int) -> Block:
        b = Block("para", para_index=idx)
        ppr = p.find(W("pPr"))
        if ppr is not None:
            st = ppr.find(W("pStyle"))
            if st is not None:
                b.style = st.get(W("val")) or "Normal"
            npr = ppr.find(W("numPr"))
            if npr is not None:
                lv = npr.find(W("ilvl"))
                b.ilvl = int(lv.get(W("val"))) if lv is not None else 0
        b.inlines = self._walk(p)
        runs = p.findall(f".//{W('r')}")
        if runs:
            nb = sum(1 for r in runs if r.find(f"{W('rPr')}/{W('b')}") is not None)
            b.bold = nb >= max(1, len(runs) // 2)
        return b

    def _walk(self, node) -> list[Inline]:
        """Duyệt cây theo thứ tự tài liệu để text và công thức không bị đảo."""
        out: list[Inline] = []
        for el in node.iter():
            tag = etree.QName(el).localname
            ns = etree.QName(el).namespace
            if tag == "t" and ns == NS["w"]:
                txt = el.text or ""
                txt = re.sub(r"[\uf000-\uf8ff]\s*", "", txt)
                out.append(Inline("text", txt, **_run_fmt(el)))
            elif tag == "tab" and ns == NS["w"]:
                out.append(Inline("text", "\t"))
            elif tag == "br" and ns == NS["w"]:
                out.append(Inline("text", "\n"))
            elif tag == "object" and ns == NS["w"]:
                out.append(self._ole(el))
            elif tag == "oMath" and ns == NS["m"]:
                latex = omml_to_latex(el)
                if latex:
                    latex = mtef._tidy(latex)
                out.append(Inline("formula", ref=self._add(
                    "formula", latex=latex, source="omml")))
            elif tag == "drawing" and ns == NS["w"]:
                blip = el.find(f".//{{{NS['a']}}}blip")
                if blip is not None:
                    rid = blip.get(f"{{{NS['r']}}}embed")
                    ref = self._figure(rid)
                    if ref:
                        out.append(Inline("image", ref=ref))
            elif tag == "pict" and ns == NS["w"]:
                for img_data in el.findall(f".//{{{NS['v']}}}imagedata"):
                    rid = img_data.get(f"{{{NS['r']}}}id") or img_data.get("id")
                    if rid and not rid.endswith("_OLE"):
                        ref = self._figure(rid)
                        if ref:
                            out.append(Inline("image", ref=ref))
        return _merge_text(out)

    def _ole(self, el) -> Inline:
        """<w:object> = công thức MathType. Đi trực tiếp LaTeX. Nếu unresolved, lấy ảnh preview fallback."""
        obj = el.find(f".//{{{NS['o']}}}OLEObject")
        latex, source = None, "unresolved"
        if obj is not None:
            blob = self._part(obj.get(f"{{{NS['r']}}}id"))
            if blob:
                latex, source = mtef.decode_ole(blob)

        # Fallback image preview if formula is unresolved
        data, mime = b"", ""
        if not latex:
            img_data = el.find(f".//{{{NS['v']}}}imagedata")
            blip = el.find(f".//{{{NS['a']}}}blip")
            img_rid = None
            if img_data is not None:
                img_rid = img_data.get(f"{{{NS['r']}}}id") or img_data.get("id")
            elif blip is not None:
                img_rid = blip.get(f"{{{NS['r']}}}embed")

            if img_rid:
                raw_img = self._part(img_rid)
                if raw_img:
                    target = self.rels.get(img_rid, "")
                    data, mime = _to_png(raw_img, target)

        return Inline("formula", ref=self._add(
            "formula", data=data, mime=mime, latex=latex, source=source))



    def _figure(self, rid: str | None) -> str | None:
        raw = self._part(rid) if rid else None
        if not raw:
            return None
        target = self.rels.get(rid, "")
        data, mime = _to_png(raw, target)
        return self._add("figure", data=data, mime=mime)

    def _table(self, tbl, idx: int) -> Block:
        b = Block("table", para_index=idx)
        for tr in tbl.findall(W("tr")):
            row = []
            for tc in tr.findall(W("tc")):
                row.append(self._walk(tc))
            b.rows.append(row)
        return b


# --------------------------------------------------------------------- utils
_WS = re.compile(r"[ \t ]+")


def _run_fmt(t_el) -> dict:
    """Đọc màu chữ / gạch chân / đậm của run chứa <w:t> này.

    Cần cho pipeline bài tập: đáp án đúng thường được đánh dấu bằng bôi màu
    hoặc gạch chân trên riêng option đó, không có chữ "Đáp án:" nào cả.
    """
    r = t_el.getparent()
    rpr = r.find(W("rPr")) if r is not None else None
    if rpr is None:
        return {}
    color_el = rpr.find(W("color"))
    color = color_el.get(W("val")) if color_el is not None else None
    if color in ("auto", "000000", None):
        color = None
    return {"bold": rpr.find(W("b")) is not None,
            "underline": rpr.find(W("u")) is not None,
            "color": color}


def _merge_text(items: list[Inline]) -> list[Inline]:
    """Gộp các token text liền nhau CÙNG định dạng thành một.

    OOXML tách text theo run, nên một đoạn thụt lề ra 5 token `{t:text,v:"\\t"}`
    rời rạc. Gộp lại rồi thu gọn khoảng trắng (giữ `\\n` cho thơ), và bỏ token
    chỉ toàn khoảng trắng ở đầu/cuối.

    QUAN TRỌNG: chỉ gộp khi (bold, color, underline) giống nhau — nếu gộp vô
    điều kiện sẽ xoá mất ranh giới định dạng, và pipeline bài tập cần đúng
    ranh giới đó để biết run nào là đáp án được bôi màu/gạch chân.
    """
    out: list[Inline] = []
    for i in items:
        prev = out[-1] if out else None
        if (i.kind == "text" and prev is not None and prev.kind == "text"
                and prev.bold == i.bold and prev.color == i.color
                and prev.underline == i.underline):
            out[-1] = Inline("text", prev.text + i.text, bold=i.bold,
                              color=i.color, underline=i.underline)
        else:
            out.append(i)
    for i in out:
        if i.kind == "text":
            i.text = _WS.sub(" ", i.text)
    while out and out[0].kind == "text" and not out[0].text.strip():
        out.pop(0)
    while out and out[-1].kind == "text" and not out[-1].text.strip():
        out.pop()
    return [i for i in out if i.kind != "text" or i.text]


_PNG_CACHE: dict[str, tuple[bytes, str]] = {}


def _to_png(raw: bytes, target: str) -> tuple[bytes, str]:
    ext = Path(target).suffix.lower()
    if ext in (".wmf", ".emf", ".wdp"):
        mime = "image/x-wmf" if ext == ".wmf" else ("image/x-emf" if ext == ".emf" else "image/png")
        return raw, mime



        # Ép mime sang image/png để tránh lọt image/emf hay image/wmf lên HTML/JSON
        _PNG_CACHE[key] = (raw, "image/png")
        return _PNG_CACHE[key]
    return raw, MIME.get(ext, "image/png")


def _dims(data: bytes, mime: str) -> tuple[int, int]:
    try:
        from PIL import Image
        import io as _io
        with Image.open(_io.BytesIO(data)) as im:
            return im.size
    except Exception:
        return 0, 0


# ------------------------------------------------------------- OMML -> LaTeX
def omml_to_latex(node) -> str:
    m = lambda t: f"{{{NS['m']}}}{t}"                     # noqa: E731
    def conv(el) -> str:
        tag = etree.QName(el).localname
        if tag == "t":
            return el.text or ""
        if tag == "r":
            return "".join(conv(c) for c in el)
        if tag == "f":
            num = el.find(m("num")); den = el.find(m("den"))
            return r"\frac{%s}{%s}" % (kids(num), kids(den))
        if tag == "rad":
            deg, e = el.find(m("deg")), el.find(m("e"))
            dg = kids(deg)
            return (r"\sqrt[%s]{%s}" % (dg, kids(e))) if dg else r"\sqrt{%s}" % kids(e)
        if tag in ("sSub", "sSup", "sSubSup"):
            base = kids(el.find(m("e")))
            sub = kids(el.find(m("sub"))); sup = kids(el.find(m("sup")))
            s = base
            if sub:
                s += "_{%s}" % sub
            if sup:
                s += "^{%s}" % sup
            return s
        if tag == "d":
            pr = el.find(m("dPr"))
            beg, end = "(", ")"
            if pr is not None:
                b = pr.find(m("begChr")); e2 = pr.find(m("endChr"))
                if b is not None:
                    beg = b.get(m("val")) or "("
                if e2 is not None:
                    end = e2.get(m("val")) or ")"
            beg = {"{": r"\{", "[": "[", "|": "|"}.get(beg, beg)
            end = {"}": r"\}", "]": "]", "|": "|"}.get(end, end)
            return r"\left%s%s\right%s" % (beg, kids(el), end)
        if tag == "nary":
            return r"\sum" + kids(el)
        return "".join(conv(c) for c in el)

    def kids(el) -> str:
        return "".join(conv(c) for c in el) if el is not None else ""

    tx = "".join(conv(c) for c in node)
    tx = unicodedata.normalize("NFC", tx)
    tx = re.sub(r"\\not\s*=|\\cancel\s*\{\s*=\s*\}|≠|[\u0338]=|=[\u0338]|̸=", r" \ne ", tx)
    for k, v in mtef.SYMBOLS.items():
        if chr(k) in tx:
            tx = tx.replace(chr(k), v + " ")
    return " ".join(tx.split()).strip()


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", re.sub(r"[ \t ]+", " ", s)).strip()
