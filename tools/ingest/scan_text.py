#!/usr/bin/env python3
"""Turn the text layer of a scanned book into paragraphs, and list what needs a human eye.

Usage: python3 scan_text.py <scan.pdf> <first-page> <last-page> <out.txt> [corpus-dir ...]

Pages are PDF page numbers. The output is one paragraph per line, with a
[[page N]] marker where each printed page begins. A report of suspect words is
printed: words the scan's recognition probably got wrong, judged against the
vocabulary of the corpus directories (books already in the library).

This does the mechanical part only. It never corrects a word on its own
authority: every suggestion is confirmed against the page image by a reader.
"""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

WORD = re.compile(r"[A-Za-zÀ-ÿ]+(?:[’'][A-Za-z]+)?")


def page_lines(pdf, n):
    out = subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), "-layout", pdf, "-"],
                         capture_output=True, text=True, check=True).stdout
    return [line.rstrip() for line in out.replace("\f", "").split("\n")]


def vocabulary(dirs):
    words = Counter()
    for d in dirs:
        for f in Path(d).rglob("*.xhtml"):
            text = re.sub(r"<[^>]+>", " ", f.read_text(encoding="utf-8"))
            words.update(w.lower().replace("’", "'") for w in WORD.findall(text))
    return words


def main(pdf, first, last, out, corpus):
    paragraphs, joins, current = [], [], None
    for n in range(first, last + 1):
        lines = [l for l in page_lines(pdf, n) if l.strip()]
        if not lines:
            continue
        # A page opens with its running head: the book or chapter title in capitals with the
        # page number. A speck above it is sometimes read as a line of its own, so the head
        # is looked for among the first three lines, and anything above it goes with it.
        printed = None
        for k, line in enumerate(lines[:3]):
            letters = [ch for ch in line if ch.isalpha()]
            if len(letters) >= 10 and sum(ch.isupper() for ch in letters) / len(letters) > 0.8 and "CHAPTER" not in line:
                m = re.search(r"^\s*(\d{1,3})\b|\b(\d{1,3})\s*$", line)
                printed = (m.group(1) or m.group(2)) if m else "?"
                lines = lines[k + 1:]
                break
        if not lines:
            continue
        # The left margin is where most lines begin; a stray mark in the margin must not move it.
        indents = Counter(len(l) - len(l.lstrip()) for l in lines)
        base = indents.most_common(1)[0][0]
        first_on_page = True
        for line in lines:
            indent = len(line) - len(line.lstrip())
            text = " ".join(line.split())
            starts = base + 2 <= indent < base + 12
            centred = indent >= base + 12
            marker = f"[[page {n}{' = ' + printed if printed else ''}]] " if first_on_page else ""
            first_on_page = False
            if centred or starts or current is None:
                current = marker + text
                paragraphs.append(current)
                if centred:
                    current = None
                continue
            previous = paragraphs[-1]
            if previous.endswith("-") and not previous.endswith(("—-", " -")):
                # A word broken at the line end. Whether the hyphen belongs to the word
                # cannot be known from the page alone, so every such join is listed.
                stem = previous[:-1]
                tail = text.split()[0]
                joins.append((stem.split()[-1], tail))
                paragraphs[-1] = stem + "⁀" + marker + text      # ⁀ marks the join for review
            else:
                paragraphs[-1] = previous + " " + marker + text
    text = "\n\n".join(paragraphs)

    # Punctuation set off by spaces is the printer's habit, not the author's.
    text = re.sub(r"\s+([;:?!])", r"\1", text)
    text = re.sub(r"“\s+", "“", text)
    text = re.sub(r"\s+”", "”", text)
    Path(out).write_text(text + "\n", encoding="utf-8")

    known = vocabulary(corpus)
    try:
        from spellchecker import SpellChecker      # pip install pyspellchecker
        english = SpellChecker()
    except ImportError:
        english = None

    def is_word(w):
        key = w.lower().replace("’", "'")
        bare = re.sub(r"'s$", "", key)
        return bool(known[key] or known[bare] or (english and (key in english or bare in english)))

    plain = re.sub(r"\u2040?\s*\[\[page[^\]]*\]\]\s*", lambda m: "" if m.group(0).startswith("\u2040") else " ", text)
    plain = plain.replace("\u2040", "")
    words = WORD.findall(plain)
    print(f"{len(paragraphs)} paragraphs, {len(words)} words, pages {first}-{last}")

    # 1. Not words at all: certain errors, found without reading.
    nonwords = Counter(w for w in words if not is_word(w))
    print(f"\n{sum(nonwords.values())} non-words ({len(nonwords)} distinct):")
    for w, c in sorted(nonwords.items(), key=lambda x: x[0].lower()):
        guesses = sorted({w[:i] + b + w[i + 1:] for a, b in (("t", "r"), ("r", "t"), ("c", "e"), ("f", "r"))
                          for i, ch in enumerate(w) if ch == a and is_word(w[:i] + b + w[i + 1:])})
        print(f"  {w}{' x' + str(c) if c > 1 else ''}{'  -> ' + ' / '.join(guesses) if guesses else ''}")

    # 2. Real words that are probably a misread of a commoner word (r and t confused).
    #    These cannot be found by a dictionary; only the context, or the page, settles them.
    confusable = Counter()
    for w in words:
        key = w.lower()
        if not is_word(w):
            continue
        for a, b in (("t", "r"), ("r", "t")):
            for i, ch in enumerate(key):
                if ch == a:
                    g = key[:i] + b + key[i + 1:]
                    if known[g] > 20 * max(known[key], 1) and known[g] > 40:
                        confusable[(w, g)] += 1
    print(f"\n{sum(confusable.values())} real words that may be misreadings ({len(confusable)} distinct):")
    for (w, g), c in sorted(confusable.items(), key=lambda x: -x[1]):
        print(f"  {w} x{c}  -> {g}?")

    print(f"\n{len(joins)} words broken across lines (does the hyphen stay?):")
    for stem, tail in joins:
        whole = (stem + tail).lower()
        tail_word = WORD.match(tail)
        joined = (stem + (tail_word.group(0) if tail_word else tail)).lower()
        verdict = "join" if known[joined] else "keep hyphen?" if known[stem.lower()] and tail_word and known[tail_word.group(0).lower()] else "?"
        print(f"  {stem}-{tail}  [{verdict}]")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5:])
