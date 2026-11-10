#!/usr/bin/env python3
"""Assign permanent paragraph and line identifiers to a book, once, at publication.

Usage: python3 tools/assign_ids.py books/<author>/<book>

Each top-level section or article of a text file is one page of the site, and
is numbered on its own.

  Prose: every paragraph and block quotation directly inside the section gets
  id="p-N", by position.

  Verse (a section marked z3998:poem): every line gets id="l-N", counted
  through the whole poem, whatever stanza or part it stands in.

Elements that already carry such an id are left alone and numbering continues
after the highest one, so the tool is safe to run again but never renumbers. A
paragraph or line added by a later correction is given a suffixed id by hand
(p-14a), as the technical spec says.

Run it when a book's status changes to published, not before: the ids freeze
the paragraph and line boundaries.
"""
import re
import sys
from pathlib import Path

from lxml import etree

XHTML = "http://www.w3.org/1999/xhtml"
TYPE = "{http://www.idpf.org/2007/ops}type"
TOPS = {f"{{{XHTML}}}section", f"{{{XHTML}}}article"}
BLOCKS = {f"{{{XHTML}}}p", f"{{{XHTML}}}blockquote"}
APPARATUS = {"titlepage", "imprint", "halftitlepage", "colophon", "copyright-page", "endnotes"}


def number(elements, prefix):
    pattern = re.compile(rf"{prefix}-(\d+)[a-z]?")
    used = [int(m.group(1)) for el in elements if (m := pattern.fullmatch(el.get("id", "")))]
    n, added = max(used, default=0), 0
    for el in elements:
        if not el.get("id"):
            n += 1
            el.set("id", f"{prefix}-{n}")
            added += 1
    return added


def lines(section):
    """Line spans of a poem: spans that are direct children of a paragraph and are followed or preceded by a break."""
    found = []
    for p in section.iter(f"{{{XHTML}}}p"):
        if p.find(f"{{{XHTML}}}br") is not None or len(p.findall(f"{{{XHTML}}}span")) == 1:
            found += [s for s in p.findall(f"{{{XHTML}}}span")]
    return found


def main(book_dir):
    for path in sorted(Path(book_dir, "src/epub/text").glob("*.xhtml")):
        tree = etree.parse(str(path))
        body = tree.find(f".//{{{XHTML}}}body")
        added = kept = 0
        for section in [el for el in body if el.tag in TOPS]:
            kinds = (section.get(TYPE) or "").split()
            if kinds and kinds[0] in APPARATUS:
                continue
            if "z3998:poem" in kinds:
                elements, prefix = lines(section), "l"
            else:
                elements, prefix = [el for el in section if el.tag in BLOCKS], "p"
            a = number(elements, prefix)
            added += a
            kept += len(elements) - a
        if added:
            tree.write(str(path), encoding="utf-8", xml_declaration=True)
        if added or kept:
            print(f"{path.name}: {added} assigned, {kept} kept")


if __name__ == "__main__":
    main(sys.argv[1])
