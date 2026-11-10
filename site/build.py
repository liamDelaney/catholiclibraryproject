#!/usr/bin/env python3
"""Build the static site from the book repositories.

Usage: python3 site/build.py [--preview]

--preview writes links that end in index.html, for viewing the output
straight from disk or from a host that does not resolve directory URLs.
"""
import copy
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
XHTML = "http://www.w3.org/1999/xhtml"
EPUB = "http://www.idpf.org/2007/ops"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/", "h": XHTML}
TYPE = f"{{{EPUB}}}type"
HEADINGS = {f"{{{XHTML}}}h{n}" for n in range(1, 7)}

# Sections that are apparatus of the ebook file, not part of the work.
# Endnotes are not a page of their own: each note is shown under the section that calls it.
APPARATUS = {"titlepage", "imprint", "halftitlepage", "colophon", "copyright-page", "endnotes"}
SECTION_LABELS = {"chapter": "Chapter", "part": "Part", "division": "Book", "volume": "Volume"}

PREVIEW = "--preview" in sys.argv


def link(path):
    """A site-relative URL, without a leading slash, for a directory page."""
    path = path.strip("/")
    tail = "index.html" if PREVIEW else ""
    return f"{path}/{tail}" if path else tail


def types(el):
    return (el.get(TYPE) or "").split()


def flat(el):
    return " ".join("".join(el.itertext()).split())


def to_html(element, inner=True):
    """Turn a namespaced XHTML element into plain HTML5 markup."""
    element = copy.deepcopy(element)
    element.tail = None
    for el in element.iter():
        if not isinstance(el.tag, str):
            continue
        el.tag = etree.QName(el).localname
        for name, value in list(el.attrib.items()):
            q = etree.QName(name)
            if q.namespace == EPUB:
                del el.attrib[name]
                el.set("data-type", value)
            elif q.namespace == XML:
                del el.attrib[name]
                el.set(q.localname, value)
    etree.cleanup_namespaces(element)
    if not inner:
        return etree.tostring(element, method="html", encoding="unicode")
    return "".join(etree.tostring(child, method="html", encoding="unicode") for child in element)


def read_heading(section, kind):
    """Take the section's own heading out of its body and return (label, ordinal, title, subtitle, long)."""
    for wrapper in [section.find("h:hgroup", NS), section.find("h:header", NS), section]:
        if wrapper is None:
            continue
        heading = next((el for el in wrapper if el.tag in HEADINGS), None)
        if heading is None:
            continue
        label, ordinal, title, subtitle, bridgehead = None, None, None, None, None
        for el in [heading, *heading]:
            if "z3998:ordinal" in types(el):
                ordinal = flat(el)
            if "se:label" in types(el):
                label = flat(el)
            if el is heading and "title" in types(el):
                title = flat(el)
        if not ordinal and not title and not types(heading):
            title = flat(heading)
        for el in wrapper:
            if el is heading:
                continue
            if "title" in types(el):
                title = flat(el)
            if "subtitle" in types(el):
                subtitle = flat(el)
            if "se:bridgehead" in types(el):
                bridgehead = flat(el)
        if wrapper is section:
            section.remove(heading)
        else:
            section.remove(wrapper)
        long = False
        if bridgehead and not title:
            title, long = bridgehead, True
        elif bridgehead:
            subtitle = subtitle or bridgehead
        if ordinal:
            word = label or SECTION_LABELS.get(kind)
            label = f"{word} {ordinal}" if word else ordinal
        else:
            label = None
        return label, ordinal, title, subtitle, long
    return None, None, None, None, False


def read_file(path, notes):
    """Read one text file of a book. Each top-level section or article in it is a page."""
    tree = etree.parse(str(path))
    body = tree.find(".//h:body", NS)
    tops = [el for el in body if el.tag in (f"{{{XHTML}}}section", f"{{{XHTML}}}article")]
    doc_title = tree.findtext(".//h:head/h:title", namespaces=NS)
    lang = tree.getroot().get(f"{{{XML}}}lang")
    return [read_section(el, notes, doc_title if len(tops) == 1 else None, lang) for el in tops]


def read_section(section, notes, doc_title, lang):
    """Read one section: its kind, heading, body and the notes it calls."""
    kind = (types(section) or [""])[0]
    slug = section.get("id")
    label, ordinal, title, subtitle, long = read_heading(section, kind)
    title = title or label or doc_title or slug

    def retarget(scope):
        """Links between files of the book become links between pages of the site."""
        for a in scope.iter(f"{{{XHTML}}}a"):
            m = re.fullmatch(r"([\w-]+)\.xhtml(#[\w-]+)?", a.get("href") or "")
            if m and not {"noteref", "backlink"} & set(types(a)):
                a.set("href", f"../{link(m.group(1))}{m.group(2) or ''}")

    retarget(section)
    called = []
    for ref in section.iter(f"{{{XHTML}}}a"):
        if "noteref" in types(ref):
            note_id = ref.get("href").split("#")[1]
            ref.set("href", f"#{note_id}")
            if note_id in notes:
                note = copy.deepcopy(notes[note_id])
                retarget(note)
                for back in note.iter(f"{{{XHTML}}}a"):
                    if "backlink" in types(back):
                        back.set("href", f"#{ref.get('id')}")
                note.set("data-number", flat(ref))
                called.append({"number": flat(ref), "element": note})

    plain = copy.deepcopy(section)
    for ref in plain.iter(f"{{{XHTML}}}a"):
        if "noteref" in types(ref):
            ref.text = f"[{ref.text}]"
    def para(p):
        # A stanza is a paragraph of line spans separated by breaks.
        if p.find("h:br", NS) is not None and p.find("h:span", NS) is not None:
            return "\n".join(flat(span) for span in p.findall("h:span", NS))
        return flat(p)

    text = "\n\n".join(para(p) for p in plain.iter(f"{{{XHTML}}}p"))
    if called:
        text += "\n\n" + "\n".join(f"[{n['number']}] {flat(n['element']).rstrip('↩ ')}" for n in called)

    return {
        "slug": slug,
        "css": kind.split(":")[-1],
        "subtitle": subtitle,
        "kind": kind,
        "parent": section.get("data-parent"),
        "ordinal": ordinal,
        "label": label,
        "title": title,
        "long_title": long,
        "lang": lang,
        "html": to_html(section),
        "notes": [{"number": n["number"], "html": to_html(n["element"], inner=False)} for n in called],
        "text": text,
    }


def read_book(book_dir, authors):
    meta = yaml.safe_load((book_dir / "book.yaml").read_text())
    opf_path = book_dir / "src/epub/content.opf"
    opf = etree.parse(str(opf_path))
    manifest = {i.get("id"): i.get("href") for i in opf.findall(".//opf:manifest/opf:item", NS)}

    notes = {}
    endnotes = opf_path.parent / "text/endnotes.xhtml"
    if endnotes.exists():
        for li in etree.parse(str(endnotes)).iter(f"{{{XHTML}}}li"):
            if li.get("id"):
                notes[li.get("id")] = li

    # Divisions (books, parts) are headings in the contents, not pages.
    sections, divisions = [], {}
    for ref in opf.findall(".//opf:spine/opf:itemref", NS):
        for section in read_file(opf_path.parent / manifest[ref.get("idref")], notes):
            if section["kind"] in APPARATUS:
                continue
            if section["kind"] in ("division", "part", "volume") and not section["text"]:
                divisions[section["slug"]] = section
                continue
            section["division"] = divisions.get(section["parent"])
            sections.append(section)

    contents = []
    for section in sections:
        if not contents or contents[-1]["division"] is not section["division"]:
            contents.append({"division": section["division"], "sections": []})
        contents[-1]["sections"].append(section)

    author = authors[meta["author"]]
    words = opf.findtext(".//opf:meta[@property='schema:wordCount']", namespaces=NS)
    url = f"{author['slug']}/{meta['slug']}"
    if meta.get("translator"):
        url += f"/{meta['translator']}"
    return {
        "dir": book_dir,
        "meta": meta,
        "title": opf.findtext(".//dc:title", namespaces=NS),
        "author": author,
        "words": int(words) if words and words.isdigit() else None,
        "sections": sections,
        "contents": contents,
        "url": url,
        "root": "../" * len(url.split("/")),
    }


def build_downloads(book, out):
    """Build every format the toolchain here can make; return those that exist."""
    downloads = out / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    slug = book["meta"]["slug"]
    formats = []

    # EPUB: the source tree zipped, mimetype first and uncompressed.
    # For release, build with the Standard Ebooks tools instead, which also give AZW3 and KEPUB.
    src = book["dir"] / "src"
    epub = downloads / f"{slug}.epub"
    with zipfile.ZipFile(epub, "w") as z:
        z.write(src / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for f in sorted(src.rglob("*")):
            if f.is_file() and f.name != "mimetype":
                z.write(f, f.relative_to(src).as_posix(), compress_type=zipfile.ZIP_DEFLATED)
    formats.append({"label": "EPUB", "file": epub.name})

    # Plain text.
    parts = [book["title"].upper(), book["author"]["name"], ""]
    division = None
    for s in book["sections"]:
        if s["division"] is not division:
            division = s["division"]
            if division:
                parts += ["", "", f"{division['label']}: {division['title']}".upper()]
        heading = f"{s['label']}: {s['title']}" if s["label"] and s["label"] != s["title"] else s["title"]
        parts += ["", heading if s["long_title"] else heading.upper(), "", s["text"]]
    txt = downloads / f"{slug}.txt"
    txt.write_text("\n".join(parts) + "\n", encoding="utf-8")
    formats.append({"label": "Plain text", "file": txt.name})

    # Other formats appear only when a tool for them is installed.
    if shutil.which("ebook-convert"):
        azw3 = downloads / f"{slug}.azw3"
        subprocess.run(["ebook-convert", str(epub), str(azw3)], check=True, capture_output=True)
        formats.append({"label": "Kindle (AZW3)", "file": azw3.name})
    return formats


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    site = yaml.safe_load((ROOT / "site/site.yaml").read_text())
    authors = {p.stem: yaml.safe_load(p.read_text()) for p in (ROOT / "authors").glob("*.yaml")}
    books = [read_book(p.parent, authors) for p in sorted((ROOT / "books").glob("*/*/book.yaml"))]
    books.sort(key=lambda b: (list(site["paths"]).index(b["meta"]["path"]), b["meta"]["order"]))
    env = Environment(loader=FileSystemLoader(ROOT / "site/templates"), autoescape=True)
    env.globals.update(site=site, link=link)
    shutil.copy(ROOT / "site/style.css", DIST / "style.css")

    for book in books:
        out = DIST / book["url"]
        out.mkdir(parents=True)
        meta = book["meta"]
        if meta["cover"].get("file"):
            shutil.copy(book["dir"] / meta["cover"]["file"], out / "cover.jpg")
        # Images used inside the text and notes; the source refers to them as ../images/.
        used = {src.split("/")[-1] for s_ in book["sections"] for part in [s_["html"], *[n["html"] for n in s_["notes"]]]
                for src in re.findall(r'src="\.\./images/([^"]+)"', part)}
        if used:
            (out / "images").mkdir()
            for name in used:
                shutil.copy(book["dir"] / "src/epub/images" / name, out / "images" / name)
        formats = build_downloads(book, out)
        siblings = [b for b in books if b["meta"]["path"] == meta["path"] and b is not book]
        (out / "index.html").write_text(
            env.get_template("book.html").render(
                book=book, meta=meta, formats=formats, siblings=siblings, root=book["root"],
                path_name=site["paths"][meta["path"]],
            ),
            encoding="utf-8",
        )
        sections = book["sections"]
        for i, section in enumerate(sections):
            sdir = out / section["slug"]
            sdir.mkdir()
            (sdir / "index.html").write_text(
                env.get_template("section.html").render(
                    book=book, section=section, root=book["root"] + "../",
                    previous=sections[i - 1] if i else None,
                    next=sections[i + 1] if i + 1 < len(sections) else None,
                ),
                encoding="utf-8",
            )
        noted = sum(len(s["notes"]) for s in sections)
        print(f"{book['url']}: {len(sections)} sections, {noted} notes, formats: {', '.join(f['label'] for f in formats)}")

    (DIST / "index.html").write_text(
        env.get_template("home.html").render(books=books, root=""), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
