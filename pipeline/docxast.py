"""DOCX -> AST tuyến tính, giữ đúng thứ tự tài liệu.

Không hiểu ngữ nghĩa bài học ở tầng này; chỉ chuẩn hoá OOXML thành block/inline
và phân loại media (formula / figure).
"""
from __future__ import annotations

import base64
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
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
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
    style: str | None = None   # w:rStyle/@w:val — character style của run


@dataclass
class Block:
    kind: str                 # para | table
    inlines: list[Inline] = field(default_factory=list)
    ilvl: int | None = None
    num_id: str | None = None   # w:numPr/w:numId — Word TỰ SINH số thứ tự câu
    style: str = "Normal"
    bold: bool = False
    rows: list = field(default_factory=list)
    para_index: int = -1

    @property
    def text(self) -> str:
        if self.kind == "table":
            parts = []
            for r in self.rows:
                for cell in r:
                    parts.extend(b.text for b in cell if b.text)
            return " ".join(parts).strip()
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
             latex: str | None = None, source: str = "",
             width: int = 0, height: int = 0) -> str:
        sha = hashlib.sha256(data or (latex or "").encode()).hexdigest()
        if sha in self._by_sha:
            existing_aid = self._by_sha[sha]
            if width and height and not self.assets[existing_aid].width:
                self.assets[existing_aid].width = width
                self.assets[existing_aid].height = height
            return existing_aid
        self._n += 1
        aid = f"{'f' if kind == 'formula' else 'img'}{self._n}"
        # Truyền theo tên: thứ tự field của Asset đã đổi và gán vị trí từng làm
        # sha256 rơi vào confidence, khiến 20 file sai schema.
        a = Asset(aid=aid, kind=kind, mime=mime, data=data, latex=latex,
                  source=source, sha256=sha, width=width, height=height)
        if kind == "formula":
            a.confidence = mtef.confidence_of(source, set(mtef._LAST_SEL)) if latex else 0.0
        if not a.width or not a.height:
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
                # numId cho biết đoạn thuộc danh sách ĐÁNH SỐ TỰ ĐỘNG nào. Nhiều
                # file đánh số câu hỏi bằng cách này, nên chuỗi "Câu 1." KHÔNG
                # nằm trong <w:t> — bỏ qua numPr thì tầng bài tập không thấy mốc
                # câu và gộp hàng chục câu làm một.
                nid = npr.find(W("numId"))
                b.num_id = nid.get(W("val")) if nid is not None else None
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
                    ext = el.find(f".//{{{NS['wp']}}}extent")
                    w_px, h_px = 0, 0
                    if ext is not None:
                        cx, cy = int(ext.get("cx", 0)), int(ext.get("cy", 0))
                        w_px, h_px = round(cx / 9525), round(cy / 9525)
                    ref = self._figure(rid, width=w_px, height=h_px)
                    if ref:
                        out.append(Inline("image", ref=ref))
            elif tag == "pict" and ns == NS["w"]:
                groups = el.findall(f".//{{{NS['v']}}}group")
                top_groups = [g for g in groups if g.getparent().tag != f"{{{NS['v']}}}group"]
                if top_groups:
                    for g in top_groups:
                        img_bytes, mime, w_px, h_px = _vml_group_to_img(g, self)
                        if img_bytes:
                            ref = self._add("figure", data=img_bytes, mime=mime, width=w_px, height=h_px)
                            if ref:
                                out.append(Inline("image", ref=ref))
                else:
                    for img_data in el.findall(f".//{{{NS['v']}}}imagedata"):
                        rid = img_data.get(f"{{{NS['r']}}}id") or img_data.get("id")
                        if rid and not rid.endswith("_OLE"):
                            shape = img_data.getparent()
                            w_px, h_px = 0, 0
                            if shape is not None:
                                w_px, h_px = _parse_vml_style_dims(shape.get("style"))
                            ref = self._figure(rid, width=w_px, height=h_px)
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

        if latex and latex.strip() in ("''", '""', "'", '"', '“', '”', "\\prime", "\\prime\\prime"):
            return Inline("text", '"')

        # Fallback image preview if formula is unresolved
        data, mime = b"", ""
        w_px, h_px = 0, 0
        if not latex:
            img_data = el.find(f".//{{{NS['v']}}}imagedata")
            blip = el.find(f".//{{{NS['a']}}}blip")
            img_rid = None
            if img_data is not None:
                img_rid = img_data.get(f"{{{NS['r']}}}id") or img_data.get("id")
                shape = img_data.getparent()
                if shape is not None:
                    w_px, h_px = _parse_vml_style_dims(shape.get("style"))
            elif blip is not None:
                img_rid = blip.get(f"{{{NS['r']}}}embed")
                ext = el.find(f".//{{{NS['wp']}}}extent")
                if ext is not None:
                    cx, cy = int(ext.get("cx", 0)), int(ext.get("cy", 0))
                    w_px, h_px = round(cx / 9525), round(cy / 9525)

            if img_rid:
                raw_img = self._part(img_rid)
                if raw_img:
                    target = self.rels.get(img_rid, "")
                    data, mime = _to_png(raw_img, target)

        return Inline("formula", ref=self._add(
            "formula", data=data, mime=mime, latex=latex, source=source, width=w_px, height=h_px))



    def _figure(self, rid: str | None, width: int = 0, height: int = 0) -> str | None:
        raw = self._part(rid) if rid else None
        if not raw:
            return None
        target = self.rels.get(rid, "")
        data, mime = _to_png(raw, target)
        return self._add("figure", data=data, mime=mime, width=width, height=height)

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
    # rStyle = character style của run. Word dùng nó để đánh dấu nhãn phương án
    # ("A.", "B.") KHÁC với văn bản thường, ngay cả khi cỡ chữ và màu y hệt:
    #     run3 'Trong các đẳng thức sau...'  rPr = sz, szCs
    #     run5 'A.'                          rPr = rStyle, sz, szCs
    # Bỏ qua rStyle thì hai run trông giống nhau và _merge_text gộp mất ranh
    # giới, khiến phương án dính vào đề và đáp án trỏ sai ô.
    style_el = rpr.find(W("rStyle"))
    return {"bold": rpr.find(W("b")) is not None,
            "underline": rpr.find(W("u")) is not None,
            "color": color,
            "style": style_el.get(W("val")) if style_el is not None else None}


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
                and prev.underline == i.underline and prev.style == i.style):
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


def _parse_vml_style_dims(style_str: str | None) -> tuple[int, int]:
    if not style_str:
        return 0, 0
    w, h = 0, 0
    m_w = re.search(r"width:\s*([\d.]+)\s*(pt|px|in|cm|mm)?", style_str)
    if m_w:
        val = float(m_w.group(1))
        unit = m_w.group(2) or "pt"
        if unit == "pt": w = round(val * 96 / 72)
        elif unit == "in": w = round(val * 96)
        elif unit == "cm": w = round(val * 96 / 2.54)
        elif unit == "mm": w = round(val * 96 / 25.4)
        else: w = round(val)
    m_h = re.search(r"height:\s*([\d.]+)\s*(pt|px|in|cm|mm)?", style_str)
    if m_h:
        val = float(m_h.group(1))
        unit = m_h.group(2) or "pt"
        if unit == "pt": h = round(val * 96 / 72)
        elif unit == "in": h = round(val * 96)
        elif unit == "cm": h = round(val * 96 / 2.54)
        elif unit == "mm": h = round(val * 96 / 25.4)
        else: h = round(val)
    return w, h


def _parse_style_dict(s: str | None) -> dict[str, str]:
    res: dict[str, str] = {}
    if not s:
        return res
    for item in s.split(";"):
        if ":" in item:
            k, v = item.split(":", 1)
            res[k.strip()] = v.strip()
    return res



def _vml_path_to_svg(path_str: str, left: float, top: float, scale_x: float = 1.0, scale_y: float = 1.0) -> str:
    parts = re.split(r'([a-zA-Z]+)', path_str)
    curr_cmd = None
    cur_x, cur_y = 0.0, 0.0
    svg_cmd = []

    for p in parts:
        p = p.strip()
        if not p:
            continue
        if re.match(r'^[a-zA-Z]+$', p):
            curr_cmd = p.lower()
            if curr_cmd == 'x':
                svg_cmd.append('Z')
            elif curr_cmd == 'e':
                break
        else:
            raw_nums = p.split(',')
            nums = []
            for item in raw_nums:
                item = item.strip()
                if item == '':
                    nums.append(0.0)
                else:
                    for sub in item.split():
                        try:
                            nums.append(float(sub))
                        except ValueError:
                            pass

            if curr_cmd == 'm' and len(nums) >= 2:
                x = left + nums[0] * scale_x
                y = top + nums[1] * scale_y
                cur_x, cur_y = x, y
                svg_cmd.append(f'M {x:.1f} {y:.1f}')
            elif curr_cmd == 'l':
                for i in range(0, len(nums) - 1, 2):
                    x = left + nums[i] * scale_x
                    y = top + nums[i + 1] * scale_y
                    cur_x, cur_y = x, y
                    svg_cmd.append(f'L {x:.1f} {y:.1f}')
            elif curr_cmd == 'r':
                for i in range(0, len(nums) - 1, 2):
                    dx = nums[i] * scale_x
                    dy = nums[i + 1] * scale_y
                    x = cur_x + dx
                    y = cur_y + dy
                    cur_x, cur_y = x, y
                    svg_cmd.append(f'L {x:.1f} {y:.1f}')
            elif curr_cmd == 'c':
                for i in range(0, len(nums) - 5, 6):
                    x1 = left + nums[i] * scale_x
                    y1 = top + nums[i + 1] * scale_y
                    x2 = left + nums[i + 2] * scale_x
                    y2 = top + nums[i + 3] * scale_y
                    x = left + nums[i + 4] * scale_x
                    y = top + nums[i + 5] * scale_y
                    cur_x, cur_y = x, y
                    svg_cmd.append(f'C {x1:.1f} {y1:.1f}, {x2:.1f} {y2:.1f}, {x:.1f} {y:.1f}')

    return ' '.join(svg_cmd)


def _render_vml_element(el, reader: "DocxReader") -> str:
    tag = etree.QName(el).localname
    st = _parse_style_dict(el.get("style"))
    left = float(st.get("left", 0))
    top = float(st.get("top", 0))
    width = float(st.get("width", 0))
    height = float(st.get("height", 0))
    flip = st.get("flip", "")

    if tag == "group":
        co = (el.get("coordorigin") or "0,0").split(",")
        ox = float(co[0])
        oy = float(co[1]) if len(co) > 1 else 0.0
        cs = (el.get("coordsize") or "1000,1000").split(",")
        cw = float(cs[0])
        ch = float(cs[1]) if len(cs) > 1 else 1000.0

        scale_x = width / cw if cw > 0 else 1.0
        scale_y = height / ch if ch > 0 else 1.0

        tf_parts = [f"translate({left:.1f}, {top:.1f})"]
        if "x" in flip and "y" in flip:
            tf_parts.append(f"translate({width:.1f}, {height:.1f}) scale(-1, -1)")
        elif "x" in flip:
            tf_parts.append(f"translate({width:.1f}, 0) scale(-1, 1)")
        elif "y" in flip:
            tf_parts.append(f"translate(0, {height:.1f}) scale(1, -1)")

        tf_parts.append(f"scale({scale_x:.4f}, {scale_y:.4f})")
        tf_parts.append(f"translate({-ox:.1f}, {-oy:.1f})")
        transform_attr = f' transform="{" ".join(tf_parts)}"'

        inner = []
        for child in el:
            inner.append(_render_vml_element(child, reader))
        return f'<g{transform_attr}>\n  ' + "\n  ".join(filter(None, inner)) + "\n</g>"

    elif tag == "shape":
        img_data = el.find(f".//{{{NS['v']}}}imagedata")
        if img_data is not None:
            rid = img_data.get(f"{{{NS['r']}}}id") or img_data.get("id")
            if rid:
                raw = reader._part(rid)
                target = reader.rels.get(rid, "")
                if raw:
                    png_bytes, mime = _to_png(raw, target)
                    b64 = base64.b64encode(png_bytes).decode()
                    return (
                        f'<image href="data:{mime};base64,{b64}" x="{left:.1f}" y="{top:.1f}" '
                        f'width="{width:.1f}" height="{height:.1f}"/>'
                    )
        elif el.get("path"):
            path_raw = el.get("path", "")
            local_cs = (el.get("coordsize") or "").split(",")
            scale_x = width / float(local_cs[0]) if len(local_cs) > 1 and float(local_cs[0]) > 0 else 1.0
            scale_y = height / float(local_cs[1]) if len(local_cs) > 1 and float(local_cs[1]) > 0 else 1.0
            d = _vml_path_to_svg(path_raw, left, top, scale_x, scale_y)
            fill_el = el.find(f".//{{{NS['v']}}}fill")
            if fill_el is not None:
                title = fill_el.get("o:title") or fill_el.get("{urn:schemas-microsoft-com:office:office}title") or ""
                fill = "url(#diagUp)" if "Upward" in title else "url(#diagDown)"
            else:
                fill = el.get("fillcolor") or "rgba(0,0,0,0.15)"
            
            stroked = el.get("stroked")
            if stroked == "f" or stroked == "false":
                stroke = "none"
                stroke_w = 0
            else:
                stroke = el.get("strokecolor") or "none"
                stroke_w = 20.0 if stroke != "none" else 0
            return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w:.1f}"/>'
        else:
            stroke_color = el.get("strokecolor") or "#000000"
            stroke_weight = el.get("strokeweight", "")
            stroke_w = 1.5 if "1.5pt" in stroke_weight else 1.0
            has_arrow = el.find(f".//{{{NS['v']}}}stroke[@endarrow='classic']") is not None
            marker = ' marker-end="url(#arrow)"' if has_arrow else ""

            x1, y1 = left, top
            if "y" in flip and height > 0:
                y1 = top + height
                y2 = top
            else:
                y2 = top + height

            if "x" in flip and width > 0:
                x1 = left + width
                x2 = left
            else:
                x2 = left + width

            return (
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{stroke_color}" stroke-width="{stroke_w * 20:.1f}"{marker}/>'
            )
    elif tag == "oval":
        rx = width / 2.0 if width > 0 else 50.0
        ry = height / 2.0 if height > 0 else 50.0
        cx = left + rx
        cy = top + ry
        
        filled = el.get("filled")
        fill_color = el.get("fillcolor")
        if filled == "f" or filled == "false" or not fill_color:
            fill = "none"
        else:
            fill = fill_color
            
        stroked = el.get("stroked")
        if stroked == "f" or stroked == "false":
            stroke = "none"
            stroke_w = 0
        else:
            stroke = el.get("strokecolor") or "#000000"
            sw_str = el.get("strokeweight", "")
            sw_val = 1.0
            if "pt" in sw_str:
                try:
                    sw_val = float(sw_str.replace("pt", ""))
                except Exception:
                    sw_val = 1.0
            stroke_w = max(sw_val * 20.0, 1.5)

        # Render oval using standard SVG path arc to avoid ImageMagick MVG memory bug with ellipse/circle
        d = f"M {cx - rx:.1f} {cy:.1f} A {rx:.1f} {ry:.1f} 0 1 0 {cx + rx:.1f} {cy:.1f} A {rx:.1f} {ry:.1f} 0 1 0 {cx - rx:.1f} {cy:.1f}"
        return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w:.1f}"/>'

    return ""


def _vml_group_to_img(group, reader: "DocxReader") -> tuple[bytes, str, int, int]:
    w_px, h_px = _parse_vml_style_dims(group.get("style"))
    co = (group.get("coordorigin") or "0,0").split(",")
    ox = float(co[0])
    oy = float(co[1]) if len(co) > 1 else 0.0
    cs = (group.get("coordsize") or "1000,1000").split(",")
    cw = float(cs[0])
    ch = float(cs[1]) if len(cs) > 1 else 1000.0

    p_size = cw / 120.0
    p_stroke = p_size / 6.0

    defs = f"""<defs>
<pattern id="diagDown" width="{p_size:.1f}" height="{p_size:.1f}" patternUnits="userSpaceOnUse">
  <path d="M {-p_size*0.25:.1f},{p_size*0.25:.1f} l {p_size*0.5:.1f},{-p_size*0.5:.1f} M 0,{p_size:.1f} l {p_size:.1f},{-p_size:.1f} M {p_size*0.75:.1f},{p_size*1.25:.1f} l {p_size*0.5:.1f},{-p_size*0.5:.1f}" stroke="#444" stroke-width="{p_stroke:.1f}" />
</pattern>
<pattern id="diagUp" width="{p_size:.1f}" height="{p_size:.1f}" patternUnits="userSpaceOnUse">
  <path d="M {-p_size*0.25:.1f},{p_size*0.75:.1f} l {p_size*0.5:.1f},{p_size*0.5:.1f} M 0,0 l {p_size:.1f},{p_size:.1f} M {p_size*0.75:.1f},{-p_size*0.25:.1f} l {p_size*0.5:.1f},{p_size*0.5:.1f}" stroke="#444" stroke-width="{p_stroke:.1f}" />
</pattern>
<marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
  <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000"/>
</marker>
</defs>"""

    body = []
    for child in group:
        body.append(_render_vml_element(child, reader))
    body_str = "\n  ".join(filter(None, body))

    target_w = max(w_px * 2, 400)
    target_h = max(h_px * 2, 400)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="{ox:.1f} {oy:.1f} {cw:.1f} {ch:.1f}" width="{target_w}" height="{target_h}" style="background: #fff;">
{defs}
  {body_str}
</svg>"""

    in_path = None
    out_path = None
    temp_dir = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f_svg:
            f_svg.write(svg.encode("utf-8"))
            in_path = f_svg.name
        out_path = in_path + ".png"
        res = subprocess.run(["convert", in_path, out_path], capture_output=True, timeout=15)
        if res.returncode == 0 and Path(out_path).exists() and Path(out_path).stat().st_size > 0:
            png_bytes = Path(out_path).read_bytes()
            return png_bytes, "image/png", w_px, h_px
        
        # Fallback to LibreOffice if ImageMagick fails on complex SVG
        temp_dir = tempfile.mkdtemp()
        subprocess.run(["soffice", "--headless", "--convert-to", "png", in_path, "--outdir", temp_dir],
                       capture_output=True, timeout=15)
        so_out = Path(temp_dir) / (Path(in_path).stem + ".png")
        if so_out.exists() and so_out.stat().st_size > 0:
            png_bytes = so_out.read_bytes()
            return png_bytes, "image/png", w_px, h_px
    except Exception:
        pass
    finally:
        if in_path:
            Path(in_path).unlink(missing_ok=True)
        if out_path:
            Path(out_path).unlink(missing_ok=True)
        if temp_dir and Path(temp_dir).exists():
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    return svg.encode("utf-8"), "image/svg+xml", w_px, h_px


_PNG_CACHE: dict[str, tuple[bytes, str]] = {}


def _to_png(raw: bytes, target: str) -> tuple[bytes, str]:
    ext = Path(target).suffix.lower()
    if ext in (".wmf", ".emf", ".wdp"):
        key = hashlib.sha256(raw).hexdigest()
        if key in _PNG_CACHE:
            return _PNG_CACHE[key]
        in_path = None
        out_path = None
        temp_dir = None
        try:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f_in:
                f_in.write(raw)
                in_path = f_in.name
            out_path = in_path + ".png"
            res = subprocess.run(
                ["convert", "-density", "300", in_path, out_path],
                capture_output=True, timeout=15
            )
            if res.returncode == 0 and Path(out_path).exists() and Path(out_path).stat().st_size > 0:
                png_bytes = Path(out_path).read_bytes()
                _PNG_CACHE[key] = (png_bytes, "image/png")
                return _PNG_CACHE[key]

            # Fallback to LibreOffice if ImageMagick fails (e.g. improper placable header)
            temp_dir = tempfile.mkdtemp()
            subprocess.run(
                ["soffice", "--headless", "--convert-to", "png", in_path, "--outdir", temp_dir],
                capture_output=True, timeout=15
            )
            so_out = Path(temp_dir) / (Path(in_path).stem + ".png")
            if so_out.exists() and so_out.stat().st_size > 0:
                png_bytes = so_out.read_bytes()
                _PNG_CACHE[key] = (png_bytes, "image/png")
                return _PNG_CACHE[key]
        except Exception:
            pass
        finally:
            if in_path:
                try:
                    Path(in_path).unlink(missing_ok=True)
                except Exception:
                    pass
            if out_path:
                try:
                    Path(out_path).unlink(missing_ok=True)
                except Exception:
                    pass
            if temp_dir and Path(temp_dir).exists():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
        return raw, "image/x-wmf" if ext == ".wmf" else "image/x-emf"
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
    tx = re.sub(r"(?<!\\)\\(?=[A-Z]\b)", r"\\setminus ", tx)
    tx = re.sub(r"(?<!\\)\b(và|hoặc|với|khi|nếu|thì|là|thuộc)\b", r"\\text{ \1 }", tx)
    for k, v in mtef.SYMBOLS.items():
        if chr(k) in tx:
            tx = tx.replace(chr(k), v + " ")
    return " ".join(tx.split()).strip()


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", re.sub(r"[ \t ]+", " ", s)).strip()
