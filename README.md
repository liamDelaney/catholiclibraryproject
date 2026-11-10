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

Not yet done: the OPF still carries the Standard Ebooks identifier, publisher and
description, and uncopyright.xhtml is unchanged. Both wait on the site's name and
licence. Paragraph ids are not assigned, because the book's status is draft.

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
