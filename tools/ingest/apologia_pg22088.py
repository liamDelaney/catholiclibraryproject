#!/usr/bin/env python3
"""Convert Project Gutenberg #22088 (Newman, Apologia Pro Vita Sua, Longmans 1890)
into text files in the Standard Ebooks layout.

Usage: python3 apologia_pg22088.py <pg22088-images.html> <draft>/epub/text

This is a one-off: it encodes what was learned by reading this particular file.
It is kept so the conversion can be audited and repeated. It changes no wording
except the corrections listed in CORRECTIONS. Typography, spelling and semantics
are left to the Standard Ebooks tools, which are run afterwards.

After those tools have run, three things were done by hand and are not in this
script: se modernize-spelling rewrote the id of note-d as "noted", which was put
back; headings in the appendices were moved down one level, because they sit
under a division; and the spine order was set by hand.
"""
import re
import sys
from pathlib import Path

from lxml import etree, html
import se.formatting

XHTML = "http://www.w3.org/1999/xhtml"
EPUB = "http://www.idpf.org/2007/ops"
TYPE = f"{{{EPUB}}}type"
NSMAP = {None: XHTML, "epub": EPUB}

# Errors in the transcription, corrected here. Each is (wrong, right, reason).
CORRECTIONS = [
    ("LETTER PROM THE REV. E. SMEDLEY", "LETTER FROM THE REV. E. SMEDLEY",
     "heading typo; the book's own table of contents reads 'from'"),
]

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}


def E(tag, text=None, **attrs):
    el = etree.Element(f"{{{XHTML}}}{tag}", nsmap=NSMAP)
    for k, v in attrs.items():
        el.set(TYPE if k == "type" else k.replace("_", "-"), v)
    el.text = text
    return el


def squash(text):
    return re.sub(r"\s+", " ", text) if text else text


def title(text):
    text = " ".join(text.split()).rstrip(".")
    return se.formatting.titlecase(text.lower())


class Converter:
    def __init__(self):
        self.files = []          # (slug, section element)
        self.pages = {}          # page label -> slug
        self.notes = {}          # PG footnote id -> list of converted blocks
        self.refs = []           # (PG footnote id, slug) in order of appearance
        self.current = None
        self.unlinked = 0

    # ----- inline and block conversion -----
    def add(self, out, child):
        out.append(child)
        return child

    def append_text(self, out, text):
        text = squash(text)
        if not text:
            return
        if len(out):
            out[-1].tail = (out[-1].tail or "") + text
        else:
            out.text = (out.text or "") + text

    def convert_children(self, src, out):
        self.append_text(out, src.text)
        for child in src:
            if isinstance(child.tag, str):
                self.convert(child, out)
            self.append_text(out, child.tail)

    def convert(self, src, out):
        tag, cls = src.tag, src.get("class") or ""
        if tag == "span" and cls == "pagenum":
            label = src.find("a").get("id").replace("Page_", "")
            self.pages[label] = self.current
            self.add(out, E("span", id=f"page-{label}", type="pagebreak", title=label))
        elif tag == "a" and "fnanchor" in cls:
            pg_id = src.get("href").lstrip("#")
            self.refs.append((pg_id, self.current))
            n = len(self.refs)
            self.add(out, E("a", str(n), href=f"endnotes.xhtml#note-{n}", id=f"noteref-{n}", type="noteref"))
        elif tag == "a":
            href = src.get("href") or ""
            if href.startswith("http"):
                self.convert_children(src, self.add(out, E("a", href=href)))
            else:
                # Anchors and links internal to the Gutenberg file: keep the words only.
                if href:
                    self.unlinked += 1
                self.convert_children(src, out)
        elif tag in ("i", "em", "sup", "sub", "table", "tbody", "tr", "td", "ul", "ol", "li", "blockquote"):
            self.convert_children(src, self.add(out, E(tag)))
        elif tag in ("b", "strong"):
            self.convert_children(src, self.add(out, E("b")))
        elif tag == "br":
            self.add(out, E("br"))
        elif tag == "hr":
            self.add(out, E("hr"))
        elif tag == "p":
            p = self.add(out, E("p"))
            self.convert_children(src, p)
            if p.text:
                p.text = p.text.lstrip()
            # A trailing break before the end of a paragraph carries nothing.
            while len(p) and p[-1].tag == f"{{{XHTML}}}br" and not (p[-1].tail or "").strip():
                p.remove(p[-1])
        elif tag == "div" and cls == "footnote":
            # Footnotes are gathered here and written out as endnotes.
            holder = E("div")
            self.convert_children(src, holder)
            first = holder[0]
            first.text = re.sub(r"^\s*\[\d+\]\s*", "", first.text or "")
            self.notes[src.find(".//a[@id]").get("id")] = list(holder)
        elif tag == "div" and cls == "blockquot":
            self.convert_children(src, self.add(out, E("blockquote")))
        elif tag == "div" and cls == "poem":
            quote = self.add(out, E("blockquote", type="z3998:verse"))
            for stanza in src.findall("div"):
                p = self.add(quote, E("p"))
                lines = stanza.findall("span")
                for i, line in enumerate(lines):
                    span = E("span")
                    indent = line.get("class", "i0")
                    if indent != "i0":
                        span.set("class", indent)
                    for br in line.findall("br"):
                        line.remove(br)
                    self.convert_children(line, span)
                    if span.text:
                        span.text = span.text.strip() if not len(span) else span.text.lstrip()
                    p.append(span)
                    if i < len(lines) - 1:
                        p.append(E("br"))
        else:
            # span.smcap, other spans, bare divs: keep the content, drop the wrapper.
            self.convert_children(src, out)

    # ----- structure -----
    def open_file(self, slug, kind, parent=None):
        section = E("section", id=slug, type=kind)
        if parent:
            section.set("data-parent", parent)
        self.files.append((slug, section))
        self.current = slug
        self.target = section
        self.sub = 0
        return section

    def open_sub(self, heading):
        self.sub += 1
        top = dict(self.files)[self.current]
        self.target = self.add(top, E("section", id=f"{self.current}-{self.sub}"))
        self.target.append(heading)

    def run(self, source):
        raw = Path(source).read_text(encoding="utf-8")
        for wrong, right, _ in CORRECTIONS:
            assert raw.count(wrong) == 1 or re.search(re.escape(wrong).replace(r"\ ", r"\s+"), raw), wrong
            raw = re.sub(re.escape(wrong).replace(r"\ ", r"\s+"), right, raw)
        body = html.fromstring(raw).body
        els = [c for c in body if isinstance(c.tag, str) and c.tag not in ("header", "footer")]

        mode, pending, division, count = "skip", None, None, 0
        for i, el in enumerate(els):
            text = " ".join(el.text_content().split())
            nxt = els[i + 1] if i + 1 < len(els) else None

            if el.tag == "h2":
                pending = None
                if text == "PREFACE.":
                    self.open_file("preface", "preface").append(E("h2", "Preface", type="title"))
                    mode = "body"
                elif text.startswith("CHAPTER "):
                    numeral = text.split()[1].rstrip(".")
                    section = self.open_file(f"chapter-{ROMAN[numeral]}", "chapter")
                    hgroup = self.add(section, E("hgroup"))
                    hgroup.append(E("h2", numeral, type="z3998:ordinal z3998:roman"))
                    mode, pending = "body", hgroup
                elif text in ("NOTES.", "SUPPLEMENTAL MATTER.", "ADDITIONAL NOTES."):
                    division = se.formatting.make_url_safe(text.rstrip("."))
                    self.open_file(division, "division").append(E("h2", title(text), type="title"))
                    mode, count = division, 0
                else:
                    mode = "skip"       # title page, contents, half title
                continue
            if mode == "skip":
                continue

            if el.tag == "h3" and pending is not None:
                pending.append(E("p", title(text), type="title"))
                pending = None
                continue

            if el.tag == "h3" and mode == "body" and text.startswith("§"):
                self.open_sub(E("h3", text.rstrip("."), type="title"))
                continue

            if el.tag == "h3" and mode == "notes":
                letter, page = re.fullmatch(r"NOTE ([A-G])\. ON PAGE (\d+)\.", text).groups()
                section = self.open_file(f"note-{letter.lower()}", "appendix", "notes")
                hgroup = self.add(section, E("hgroup"))
                h2 = self.add(hgroup, E("h2"))
                h2.append(E("span", "Note", type="se:label"))
                h2[-1].tail = " "
                h2.append(E("span", letter, type="z3998:ordinal"))
                self.page_ref(section, [page])
                pending = hgroup
                continue

            if el.tag == "h3" and mode == "supplemental-matter":
                count += 1
                section = self.open_file(f"supplemental-matter-{count}", "appendix", "supplemental-matter")
                hgroup = self.add(section, E("hgroup"))
                hgroup.append(E("h2", text.rstrip("."), type="z3998:ordinal z3998:roman"))
                pending = hgroup
                continue

            if el.tag == "h3" and mode == "additional-notes":
                m = re.fullmatch(r"NOTE ON PAGES? ([\d-]+)\.", text)
                if m:
                    count += 1
                    section = self.open_file(f"additional-note-{count}", "appendix", "additional-notes")
                    pages = m.group(1).split("-")
                    if nxt is not None and nxt.tag == "h3":
                        self.heading_slot = section
                    else:
                        word = "Pages" if len(pages) > 1 else "Page"
                        section.append(E("h2", f"Note on {word} {'–'.join(pages)}", type="title"))
                        self.heading_slot = None
                    self.pending_pages = pages
                    if self.heading_slot is None:
                        self.page_ref(section, pages)
                else:
                    self.heading_slot.append(E("h2", title(text), type="title"))
                    self.page_ref(self.heading_slot, self.pending_pages)
                continue

            if el.tag == "h4":
                if re.fullmatch(r"\d+\.", text):
                    self.open_sub(E("h3", text.rstrip("."), type="z3998:ordinal"))
                else:
                    # "II.—THE ACADEMIA ..." keeps its numeral; only the words are title-cased.
                    m = re.fullmatch(r"([IVX]+(?:\. AND [IVX]+)?)\.?—?\s*(.*)", text)
                    numeral = m.group(1).replace(". AND ", " and ")
                    self.open_sub(E("h3", f"{numeral}. {title(m.group(2))}", type="title"))
                continue

            if el.tag == "hr":
                # Rules next to headings are decoration; rules between paragraphs are breaks.
                prev = els[i - 1]
                if (nxt is not None and nxt.tag in ("h2", "h3", "h4")) or prev.tag in ("h2", "h3", "h4"):
                    continue
            if el.tag == "div" and not el.get("class") and not len(el) and not (el.text or "").strip():
                continue
            self.convert(el, self.target)

    def page_ref(self, section, pages):
        p = self.add(section, E("p", "On "))
        word = "pages " if len(pages) > 1 else "page "
        for i, page in enumerate(pages):
            a = E("a", (word if i == 0 else "") + page, href=f"PAGE:{page}")
            if i:
                p[-1].tail = "–"
            p.append(a)
        p[-1].tail = "."

    # ----- output -----
    def write(self, outdir):
        outdir = Path(outdir)
        for slug, section in self.files:
            for a in section.iter(f"{{{XHTML}}}a"):
                href = a.get("href", "")
                if href.startswith("PAGE:"):
                    page = href[5:]
                    a.set("href", f"{self.pages[page]}.xhtml#page-{page}")
            kind = section.get(TYPE)
            matter = "frontmatter" if kind == "preface" else "backmatter" if kind == "appendix" else "bodymatter"
            self.save(outdir / f"{slug}.xhtml", section, f"{matter} z3998:non-fiction", self.doc_title(section, slug))

        endnotes = E("section", id="endnotes", type="endnotes")
        endnotes.append(E("h2", "Endnotes", type="title"))
        ol = self.add(endnotes, E("ol"))
        for n, (pg_id, slug) in enumerate(self.refs, 1):
            li = self.add(ol, E("li", id=f"note-{n}"))
            for block in self.notes[pg_id]:
                li.append(block)
            last = li[-1]
            back = E("a", "↩", href=f"{slug}.xhtml#noteref-{n}", type="backlink")
            if len(last):
                last[-1].tail = (last[-1].tail or "").rstrip() + " "
            else:
                last.text = (last.text or "").rstrip() + " "
            last.append(back)
        self.save(outdir / "endnotes.xhtml", endnotes, "backmatter", "Endnotes")

    def doc_title(self, section, slug):
        hgroup = section.find(f"{{{XHTML}}}hgroup")
        if hgroup is not None:
            parts = [" ".join("".join(el.itertext()).split()) for el in hgroup]
            return ": ".join(parts)
        h2 = section.find(f"{{{XHTML}}}h2")
        return "".join(h2.itertext()) if h2 is not None else slug

    def save(self, path, section, body_type, doc_title):
        root = E("html")
        root.set("{http://www.w3.org/XML/1998/namespace}lang", "en-GB")
        root.set(f"{{{EPUB}}}prefix", "z3998: http://www.daisy.org/z3998/2012/vocab/structure/, se: https://standardebooks.org/vocab/1.0")
        head = self.add(root, E("head"))
        head.append(E("title", doc_title))
        head.append(E("link", href="../css/core.css", rel="stylesheet", type_="text/css"))
        head.append(E("link", href="../css/local.css", rel="stylesheet", type_="text/css"))
        for link in head.findall(f"{{{XHTML}}}link"):
            link.set("type", link.attrib.pop("type-"))
        body = self.add(root, E("body", type=body_type))
        body.append(section)
        path.write_bytes(etree.tostring(root, encoding="utf-8", xml_declaration=True, pretty_print=True))


if __name__ == "__main__":
    c = Converter()
    c.run(sys.argv[1])
    c.write(sys.argv[2])
    print(f"{len(c.files)} files, {len(c.refs)} notes of {len(c.notes)} footnotes, {len(c.pages)} page anchors, "
          f"{c.unlinked} internal links reduced to text")
    for slug, section in c.files:
        print(f"  {slug}: {len(section.findall('.//{%s}p' % XHTML))} paragraphs")
