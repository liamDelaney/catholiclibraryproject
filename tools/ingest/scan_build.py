#!/usr/bin/env python3
"""Build one section of a scan-derived book from its collated text and a reader's decisions.

Usage: python3 scan_build.py <book-module> <section> <collated-dir> <out-dir> <corpus-dir ...>

<book-module> is a Python file that defines:

  OFFSET     PDF page number minus printed page number
  SECTIONS   {name: {"slug", "kind", "ordinal", "title", "first": "the opening words, as printed"}}
  ANSWERS    {name: {question number: text}}   answers to the questions collate.py numbered
  FIXES      {name: [(kind, old, new), ...]}   further decisions, each applied exactly once

The collated text comes from collate.py. This step applies the decisions, removes
the heading lines and stray marks, settles words broken across lines, turns page
markers into page anchors, and writes XHTML. It then lists whatever still does not
look like a word, with its page, so the reader can see what remains.
"""
import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import scan_text  # noqa: E402

J = "⁀"
MARK = re.compile(r"^(?:[_|©~*#<>=\\/§¢{}\[\]°•«»]+|['‘’`]|—|-|\.|,)$")


def load(path):
    spec = importlib.util.spec_from_file_location("book", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(module, name, collated_dir, out_dir, corpus):
    book = load(module)
    sec = book.SECTIONS[name]
    text = (Path(collated_dir) / f"col.{name}.txt").read_text(encoding="utf-8")
    counts = Counter()

    # the reader's answers to the numbered questions collate.py left in the text;
    # an unanswered question keeps the first reading if it has letters, and is dropped if not
    answers = book.ANSWERS.get(name, {})

    def answer(m):
        k, tok = int(m.group(1)), m.group(2)
        if k in answers:
            counts["questions answered"] += 1
            return answers[k]
        counts["questions left as read"] += 1
        return tok if re.search(r"[A-Za-z]", tok) else ""

    text = re.sub(r"\u27e6(\d+)\|([^\u27e7]*)\u27e7", answer, text)
    text = re.sub(r"“[ \t]+", "“", text)
    text = re.sub(r"[ \t]+([;:?!,.])(?=\s|$)", r"\1", text)

    # decisions that must come before paragraphs are joined (a footnote lifted out of the text)
    for kind, old, new in book.FIXES.get(name, []):
        if kind.startswith("early"):
            if text.count(old) != 1:
                sys.exit(f"{name}: expected exactly one {old!r} (early), found {text.count(old)}")
            text = text.replace(old, new)
            counts[kind] += 1

    for old, new in getattr(book, "GLOBAL", []):
        counts["global replacements"] += text.count(old)
        text = text.replace(old, new)

    known = scan_text.vocabulary(corpus)
    try:
        from spellchecker import SpellChecker
        english = SpellChecker()
    except ImportError:
        english = None

    def is_word(w):
        k = w.lower().replace("’", "'")
        bare = re.sub(r"'s$", "", k)
        return bool(known[k] or known[bare] or (english and (k in english or bare in english)))

    paragraphs = []
    for p in text.strip().split("\n\n"):
        toks = [t for t in p.split() if not (MARK.match(t) and not t.startswith("[["))]
        counts["stray marks removed"] += len(p.split()) - len(toks)
        if toks:
            paragraphs.append(" ".join(toks))

    # a paragraph break in mid-sentence is the recogniser's, not the author's
    merged = []
    for p in paragraphs:
        plain = re.sub(r"\[\[page[^\]]*\]\]\s*", "", p)
        numbered = re.match(r"\((?:[ivx]+|\d+)\.?\)", plain)       # "(i.) ..." opens a paragraph of its own
        if merged and not numbered and (not re.search(r"[.?!”’)]$", merged[-1]) or plain[:1].islower()) and "HAPTER" not in merged[-1][:30].upper():
            merged[-1] += " " + p
            counts["paragraphs joined"] += 1
        else:
            merged.append(p)
    paragraphs = merged

    # heading lines: everything before the section's opening words
    body = "\n\n".join(paragraphs)
    first = sec["first"]
    at = body.find(first)
    if at < 0:
        sys.exit(f"{name}: opening words {first!r} not found; the text begins {body[:160]!r}")
    lead = re.findall(r"\[\[page[^\]]*\]\]", body[:at])
    body = (lead[0] + " " if lead else "") + sec.get("first_as", first) + body[at + len(first):]

    # words broken across lines
    kept = []

    def settle(m):
        stem, tail = m.group(1), m.group(2)
        whole = stem + tail
        if is_word(whole) or not (is_word(stem) and is_word(tail)):
            return whole
        kept.append(f"{stem}-{tail}")
        return f"{stem}-{tail}"

    body = re.sub(rf"([A-Za-zÀ-ÿ]+){J}([A-Za-zÀ-ÿ]+)", settle, body)
    body = body.replace(J, "")
    body = re.sub(r"(\w)— (\w)", r"\1—\2", body)
    body = re.sub(r"(\w) —(\w)", r"\1—\2", body)

    # further decisions, as exact replacements
    for kind, old, new in book.FIXES.get(name, []):
        if kind.startswith("early"):
            continue
        n = body.count(old)
        if n != 1:
            sys.exit(f"{name}: expected exactly one {old!r}, found {n}")
        body = body.replace(old, new)
        counts[kind] += 1

    out = []
    for p in body.split("\n\n"):
        p = re.sub(r"\s*\[\[page (\d+)[^\]]*\]\]\s*",
                   lambda m: f' <span id="page-{int(m.group(1)) - book.OFFSET}" title="{int(m.group(1)) - book.OFFSET}" epub:type="pagebreak"/>', p)
        p = p.strip().replace("&", "&amp;")
        out.append(f"\t\t\t<p>{p}</p>")

    if sec.get("ordinal"):
        heading = (f'\t\t\t<hgroup>\n\t\t\t\t<h2 epub:type="z3998:ordinal z3998:roman">{sec["ordinal"]}</h2>\n'
                   f'\t\t\t\t<p epub:type="title">{sec["title"]}</p>\n\t\t\t</hgroup>')
        doc_title = f'{sec["ordinal"]}: {sec["title"]}'
    else:
        heading = f'\t\t\t<h2 epub:type="title">{sec["title"]}</h2>'
        doc_title = sec["title"]
    matter = "frontmatter" if sec["kind"] == "preface" else "bodymatter"
    xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" epub:prefix="z3998: http://www.daisy.org/z3998/2012/vocab/structure/, se: https://standardebooks.org/vocab/1.0" xml:lang="en-GB">
	<head>
		<title>{doc_title}</title>
		<link href="../css/core.css" rel="stylesheet" type="text/css"/>
		<link href="../css/local.css" rel="stylesheet" type="text/css"/>
	</head>
	<body epub:type="{matter} z3998:non-fiction">
		<section id="{sec["slug"]}" epub:type="{sec["kind"]}">
{heading}
{chr(10).join(out)}
		</section>
	</body>
</html>
'''
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / f'{sec["slug"]}.xhtml').write_text(xhtml, encoding="utf-8")

    # what still does not look like a word
    page, left = None, []
    for tok in re.split(r"(\[\[page \d+[^\]]*\]\])|\s+", body):
        if not tok:
            continue
        m = re.match(r"\[\[page (\d+)", tok)
        if m:
            page = int(m.group(1))
            continue
        for w in scan_text.WORD.findall(re.sub(r"<[^>]+>", " ", tok)):
            if not is_word(w) and not re.search(r"is(e|ed|es|ing|ation|ations|er|ers)$|our(s|ed|ing|ite|able)?$", w):
                left.append((page, w))
    words = len(re.sub(r"<[^>]+>|\[\[[^\]]*\]\]", " ", body).split())
    print(f"{name}: {len(out)} paragraphs, {words} words; decisions: " +
          ", ".join(f"{n} {k}" for k, n in counts.most_common()))
    if kept:
        print("  hyphen kept: " + ", ".join(kept))
    if left:
        seen = Counter(w for _, w in left)
        shown = []
        for p_, w in left:
            if w not in shown:
                shown.append(w)
        pages = {w: p_ for p_, w in reversed(left)}
        print("  not words: " + ", ".join(f"p{pages[w]}:{w}" + (f"x{seen[w]}" if seen[w] > 1 else "") for w in shown))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
