# Library prototype

Four books, Orthodoxy, The Imitation of Christ, Newman's Verses on Various Occasions and his Apologia, taken end to end: source, metadata, site pages, downloads.

    books/<author>/<book>/src        XHTML source in the Standard Ebooks layout
    books/<author>/<book>/book.yaml  sidecar metadata (see the technical spec)
    authors/<author>.yaml            author records
    site/build.py                    builds dist/ from every book found
    site/templates, site/style.css   the reading page, book page and library list
    tools/assign_ids.py              assigns permanent paragraph ids at publication

Build (needs Python with lxml, PyYAML and Jinja2):

    python3 site/build.py            # directory URLs, for a web server
    python3 site/build.py --preview  # index.html links, for opening dist/ from disk

Formats are derived: the book page lists only what the build produced. EPUB here
is the source tree zipped; for release, build with the Standard Ebooks tools.
AZW3 is added when Calibre's ebook-convert is installed. PDF and KEPUB are not
built yet.

All four books are white-label in the Standard Ebooks sense: no imprint, Uncopyright
page, logo or se.css, and an identifier of the form author/work[/translator]. The
Standard Ebooks tools (se lint, se build-toc, se clean) treat them accordingly. Each
book's description lives in its content.opf; book.yaml records who drafted and reviewed it.

Known linter errors that are accepted for now: the cover size (cover art is not chosen),
the author-link rule for descriptions, the Apologia's page anchors (s-010, x-018, x-019,
s-050) and its placeholder metadata.

Paragraph and line ids are not assigned, because every book's status is draft.

Endnotes are shown at the foot of the section that calls them, keeping the book-wide
numbers of the source. Divisions (the four books of the Imitation) are headings in the
contents, not pages. A translated work carries its translator in its address.

A text file may hold several top-level sections or articles (a collection of poems);
each is a page, addressed by its id. For single-section files the id is the filename.
Verse is set line by line, and assign_ids.py numbers lines (l-N) through each poem.

The Apologia was converted from Project Gutenberg HTML, not taken from Standard Ebooks:

    tools/ingest/apologia_pg22088.py   the conversion, kept so it can be audited and rerun
    se create-draft -o -w              white-label skeleton (no Standard Ebooks branding)
    se typogrify, modernize-spelling, semanticate, clean, build-manifest, build-toc

Its spine order was set by hand. It keeps the print page numbers of the 1890 edition as
empty spans (id="page-14", epub:type="pagebreak"), because Newman's notes cite pages; the
site turns those citations into links. `se lint` objects to these spans.

Scan-derived books (trial: Knox, The Belief of Catholics, Chapter I only):

    tools/ingest/scan_text.py          text layer of a scanned PDF -> paragraphs, with page
                                       markers and a report of suspect words and broken words
    tools/ingest/knox_belief_ch1.py    every correction made to Chapter I, by kind, and the
                                       XHTML it produces

The corrections were made by reading each page image against the text. Words are never
corrected from a dictionary alone.
