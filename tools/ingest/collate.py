#!/usr/bin/env python3
"""Collate three machine readings of a scanned book and settle what can be settled.

Usage: python3 collate.py <scan.pdf> <first-page> <last-page> <dirB> <dirC> <out.txt> <corpus-dir ...>

  A  the text layer already in the scan's PDF (also gives lines, paragraphs, pages)
  B  a fresh recognition of the page images with tesseract's neural engine  (dirB/pN.txt)
  C  a recognition with tesseract's older engine, which errs differently    (dirC/pN.txt)

A and B come from the same family of recogniser and share some errors, so two
of them agreeing against C settles nothing. The rule is:

  all three agree                      -> accepted
  they differ, exactly one is a word   -> that word, recorded as an automatic correction
  they differ, several are words       -> listed for a reader to decide, A kept meanwhile
  they differ, none is a word          -> listed for a reader
  words C and B both have but A lacks  -> inserted (text lost from A), and listed

The output keeps scan_text.py's conventions: a paragraph per block, [[page N = n]]
markers, and the join mark where a word was broken across lines. A report on
stdout lists every automatic correction and every open question with its context.
"""
import difflib
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import scan_text  # noqa: E402

J = "⁀"
TOKEN = re.compile(r"\[\[page[^\]]*\]\]|\S+")


def normalise(text):
    for a, b in (("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬀ", "ff"), ("ﬃ", "ffi"), ("ﬄ", "ffl"), ("''", "”"), ("``", "“"),
                 ("——", "—"), ("—-", "—"), ("-—", "—"), ("--", "—")):
        text = text.replace(a, b)
    text = re.sub(r"[ \t]+([;:?!])", r"\1", text)
    text = re.sub(r"“[ \t]+", "“", text)
    text = re.sub(r"[ \t]+”", "”", text)
    # a question mark after a spaced quotation mark is often read as a lone letter
    text = re.sub(r"(?<=[\w”’]) (?:P|r|f)(?=\s|$)", "?", text)
    # two words run together over a comma or semicolon
    text = re.sub(r"([a-z])([,;])([a-z])", r"\1\2 \3", text)
    text = re.sub(r"\bI(do|am|have|had|did|was|can|could|should|would|shall|will|may|think|know|believe|suppose|mean)\b", r"I \1", text)
    return text


def key(tok):
    """What two readings must share to count as the same word."""
    t = tok.replace(J, "")
    t = t.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    return t


def other_reading(directory, first, last):
    words = []
    for n in range(first, last + 1):
        f = Path(directory) / f"p{n}.txt"
        if not f.exists():
            continue
        lines = [l.strip() for l in f.read_text(encoding="utf-8", errors="replace").split("\n") if l.strip()]
        # drop the running head (and any speck read as a line above it)
        for k, line in enumerate(lines[:3]):
            letters = [ch for ch in line if ch.isalpha()]
            if len(letters) >= 10 and sum(ch.isupper() for ch in letters) / len(letters) > 0.75 and "CHAPTER" not in line.upper()[:9]:
                lines = lines[k + 1:]
                break
        # and a page number standing alone at the foot
        if lines and re.fullmatch(r"[\dIlo]{1,3}", lines[-1]):
            lines = lines[:-1]
        text = ""
        for line in lines:
            if text.endswith("-") and not text.endswith(("—-", " -")):
                text = text[:-1] + J + line
            else:
                text += (" " if text else "") + line
        words += TOKEN.findall(normalise(text))
    # a word broken across pages
    out = []
    for w in words:
        if out and out[-1].endswith("-") and len(out[-1]) > 1 and w[:1].islower():
            out[-1] = out[-1][:-1] + J + w
        else:
            out.append(w)
    return out


def is_head(line):
    letters = [ch for ch in line if ch.isalpha()]
    return len(letters) >= 10 and sum(ch.isupper() for ch in letters) / len(letters) > 0.75 and "CHAPTER" not in line.upper()[:9]


def base_text(directory, first, last):
    """Paragraphs from a tesseract reading: blocks separated by blank lines, joined across pages."""
    paragraphs = []
    for n in range(first, last + 1):
        f = Path(directory) / f"p{n}.txt"
        if not f.exists():
            continue
        blocks = [[l.strip() for l in b.split("\n") if l.strip()] for b in re.split(r"\n\s*\n", f.read_text(encoding="utf-8", errors="replace"))]
        blocks = [b for b in blocks if b]
        # running head and anything above it; a page number alone at the foot
        flat = [(i, k) for i, b in enumerate(blocks) for k in range(len(b))][:3]
        for i, k in flat:
            if is_head(blocks[i][k]):
                blocks = ([blocks[i][k + 1:]] if blocks[i][k + 1:] else []) + blocks[i + 1:]
                break
        if blocks and len(blocks[-1]) == 1 and re.fullmatch(r"[\dIlo]{1,3}", blocks[-1][0]):
            blocks = blocks[:-1]
        first_block = True
        for b in blocks:
            text = ""
            for line in b:
                if text.endswith("-") and not text.endswith(("—-", " -")):
                    text = text[:-1] + J + line
                else:
                    text += (" " if text else "") + line
            marker = f"[[page {n}]] " if first_block else ""
            if first_block and paragraphs:
                prev = paragraphs[-1]
                broken = prev.endswith("-") and not prev.endswith(("—-", " -"))
                if broken:
                    paragraphs[-1] = prev[:-1] + J + marker + text
                    first_block = False
                    continue
                if not re.search(r"[.?!”’)]$", prev) or text[:1].islower():
                    paragraphs[-1] = prev + " " + marker + text
                    first_block = False
                    continue
            paragraphs.append(marker + text)
            first_block = False
    return "\n\n".join(paragraphs)


def raw_layer(pdf, first, last):
    """The scan's own text layer in reading order, as words."""
    import subprocess
    words = []
    for n in range(first, last + 1):
        out = subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), pdf, "-"], capture_output=True, text=True).stdout
        lines = [l.strip() for l in out.replace("\f", "").split("\n") if l.strip()]
        for k, line in enumerate(lines[:3]):
            if is_head(line):
                lines = lines[k + 1:]
                break
        text = ""
        for line in lines:
            if text.endswith("-") and not text.endswith(("—-", " -")):
                text = text[:-1] + J + line
            else:
                text += (" " if text else "") + line
        words += TOKEN.findall(normalise(text))
    return words


def main(pdf, first, last, dir_b, dir_c, out, corpus):
    # The base is reading B; the scan's own layer (same family of recogniser) and C vote on it.
    a_text = normalise(base_text(dir_b, first, last))
    a_text = re.sub(rf"(\S+){J}(\[\[page[^\]]*\]\])\s*(\S+)", rf"\2 \1{J}\3", a_text)
    paragraphs = a_text.split("\n\n")
    a = []                      # (token, paragraph index)
    for i, p in enumerate(paragraphs):
        a += [(t, i) for t in TOKEN.findall(p)]
    a_words = [(j, t) for j, (t, _) in enumerate(a) if not t.startswith("[[page")]
    b = raw_layer(pdf, first, last)
    c = other_reading(dir_c, first, last)

    known = scan_text.vocabulary(corpus)
    try:
        from spellchecker import SpellChecker
        english = SpellChecker()
    except ImportError:
        english = None

    def is_word(tok):
        parts = scan_text.WORD.findall(key(tok))
        if not parts:
            return True         # punctuation or a number: nothing to judge
        for w in parts:
            k = w.lower()
            bare = re.sub(r"'s$", "", k)
            if not (known[k] or known[bare] or (english and (k in english or bare in english))):
                return False
        return True

    def align(other):
        """For each A word, the other reading's word(s) at that place; plus insertions."""
        ak = [key(t) for _, t in a_words]
        ok = [key(t) for t in other]
        at, ins = {}, {}
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ak, ok, autojunk=False).get_opcodes():
            if tag == "equal":
                for d in range(i2 - i1):
                    at[i1 + d] = other[j1 + d]
            elif tag == "replace" and i2 - i1 == j2 - j1:
                for d in range(i2 - i1):
                    at[i1 + d] = other[j1 + d]
            elif tag == "replace":
                at[i1] = " ".join(other[j1:j2])
                for d in range(1, i2 - i1):
                    at[i1 + d] = ""
            elif tag == "insert":
                ins[i1] = other[j1:j2]
            # delete: the other reading has nothing here
        return at, ins

    b_at, b_ins = align(b)
    c_at, c_ins = align(c)

    def freq(tok):
        ws = scan_text.WORD.findall(key(tok))
        return min((known[w.lower()] for w in ws), default=0)

    def rt_only(x, y):
        """True if x and y differ only by r and t standing in for each other."""
        x, y = key(x), key(y)
        return len(x) == len(y) and x != y and all(p == q or {p, q} == {"r", "t"} for p, q in zip(x, y))

    def all_words(r):
        return bool(r) and all(is_word(part) for part in r.split())

    auto, rt_auto, dropped, open_q, inserted = [], [], [], [], []
    new = {}
    for n, (j, tok) in enumerate(a_words):
        rb, rc = b_at.get(n), c_at.get(n)
        ka, kb, kc = key(tok), key(rb) if rb else rb, key(rc) if rc else rc
        has_letters = bool(scan_text.WORD.search(tok))
        if kb == ka and kc == ka:
            if not has_letters and not re.search(r"\d", tok) and not re.fullmatch(r"[.,;:—-]+", tok) and len(tok) > 1:
                open_q.append((tok, rb, rc, " ".join(t for _, t in a_words[max(0, n - 5):n]) + " [" + tok + "] " + " ".join(t for _, t in a_words[n + 1:n + 6])))
            continue
        context = " ".join(t for _, t in a_words[max(0, n - 5):n]) + " [" + tok + "] " + " ".join(t for _, t in a_words[n + 1:n + 6])
        has_letters = bool(scan_text.WORD.search(tok))

        # A word or mark that neither other reading has anything for: usually a stamp.
        if rb is None and rc is None and is_word(tok) and has_letters:
            open_q.append((tok, rb, rc, context))
            continue
        # A split one word in two (a mark fell inside it) and the others read it whole.
        if (rb == "" or rc == "") and not rb and not rc:
            new[j] = ""
            dropped.append((tok, context))
            continue
        # Marks that only A saw (stamps, specks in the margin): nothing there in B or C.
        if not rb and not rc and not is_word(tok):
            new[j] = ""
            dropped.append((tok, context))
            continue
        if not has_letters and not rb and not rc:
            new[j] = ""
            dropped.append((tok, context))
            continue

        # A lone character where a question mark was printed after a spaced quotation mark.
        if len(tok) == 1 and tok not in "aAIO—" and tok.isalnum():
            open_q.append((tok, rb, rc, context))
            continue
        # C is independent of A and B. If C agrees with either, two independent readings agree.
        if rc and kc in (ka, kb) and all_words(rc):
            if kc != ka:
                new[j] = rb
                auto.append((tok, rb, context))
            continue
        # The base is not a word (or is a bare mark), and another reading offers words.
        if not is_word(tok) or not has_letters:
            cands = [r for r in (rb, rc) if r and all_words(r) and scan_text.WORD.search(r) and len(r.split()) <= 2]
            cands = [r for i, r in enumerate(cands) if key(r) not in [key(c_) for c_ in cands[:i]]]
            if len(cands) == 1 and (has_letters or (rb and rc is not None and not rc) or (rb and rc and key(rb) == key(rc))):
                new[j] = cands[0]
                auto.append((tok, cands[0], context))
                continue
            if len(cands) == 2 and has_letters:
                score = [difflib.SequenceMatcher(None, key(tok).lower(), key(r).lower()).ratio() for r in cands]
                if max(score) > 0.7 and abs(score[0] - score[1]) > 0.15:
                    pick = cands[score.index(max(score))]
                    new[j] = pick
                    auto.append((tok, pick, context))
                    continue
        # A and B agree and C differs.
        if kb == ka or (rb is None and rc):
            if rc and rt_only(tok, rc) and is_word(rc) and is_word(tok):
                # both are words; r and t are this scan's habitual confusion
                if freq(rc) > 20 * max(freq(tok), 1) and freq(rc) > 40:
                    new[j] = rc
                    rt_auto.append((tok, rc, context))
                else:
                    open_q.append((tok, rb, rc, context))
                continue
            if is_word(tok):
                continue        # C alone disagrees, and not in the habitual way: C's noise
            if rc and all_words(rc):
                new[j] = rc
                auto.append((tok, rc, context))
                continue
            open_q.append((tok, rb, rc, context))
            continue
        # All three differ, or C is missing.
        good = [r for r in (tok, rb, rc) if r and all_words(r)]
        good = [r for i, r in enumerate(good) if key(r) not in [key(g) for g in good[:i]]]
        if len(good) == 1:
            if key(good[0]) != ka:
                new[j] = good[0]
                auto.append((tok, good[0], context))
            continue
        open_q.append((tok, rb, rc, context))

    # text that B and C both have and A lacks
    for n in sorted(set(b_ins) & set(c_ins)):
        if [key(x) for x in b_ins[n]] == [key(x) for x in c_ins[n]]:
            j = a_words[n][0] if n < len(a_words) else len(a)
            inserted.append((n, " ".join(c_ins[n])))
            new.setdefault(("ins", j), " ".join(c_ins[n]))

    # Noise the reader need not see: names, and British spellings the dictionary lacks.
    def noise(tok, rb, rc):
        if not (rb is not None and rc is not None and key(rb) == key(tok) == key(rc)):
            return False
        bare = tok.strip("“”‘’\"'.,;:!?()")
        return bare[:1].isupper() or J in tok or bool(re.search(r"is(e|ed|es|ing|ation|ations|er|ers)$|our(s|ed|ing|ite|able)?$", bare))

    listed = {ctx for *_, ctx in open_q}
    for n, (j, tok) in enumerate(a_words):
        final = new.get(j, tok)
        if final and not all_words(final):
            context = " ".join(t for _, t in a_words[max(0, n - 5):n]) + " [" + tok + "] " + " ".join(t for _, t in a_words[n + 1:n + 6])
            if context not in listed:
                open_q.append((final, b_at.get(n), c_at.get(n), context))
    open_q = [q for q in open_q if not noise(q[0], q[1], q[2])]
    ids = {}
    by_context = {ctx: k for k, (*_, ctx) in enumerate(open_q, 1)}
    for n, (j, tok) in enumerate(a_words):
        context = " ".join(t for _, t in a_words[max(0, n - 5):n]) + " [" + tok + "] " + " ".join(t for _, t in a_words[n + 1:n + 6])
        if context in by_context:
            ids[j] = by_context[context]
    out_pars = [[] for _ in paragraphs]
    for j, (tok, pi) in enumerate(a):
        if ("ins", j) in new:
            out_pars[pi].append(new[("ins", j)])
        w = new.get(j, tok)
        if w and w != tok and w[-1] in "’'‘" and tok[-1] not in "’'‘”\"" and not w[:-1].lower().endswith("s"):
            w = w[:-1]
        if w:
            # keep the join mark A recorded, so the hyphen decision is still visible
            if J in tok and J not in w and w.replace("-", "") == key(tok).replace("-", ""):
                w = tok
            out_pars[pi].append(f"\u27e6{ids[j]}|{w}\u27e7" if j in ids else w)
        elif j in ids:
            out_pars[pi].append(f"\u27e6{ids[j]}|\u27e7")
    Path(out).write_text("\n\n".join(" ".join(p) for p in out_pars if p) + "\n", encoding="utf-8")

    print(f"pages {first}-{last}: {len(a_words)} words in A, {len(b)} in B, {len(c)} in C")
    print(f"\nAUTO {len(auto)} corrections on the agreement of independent readings, or the only reading that is a word:")
    for (x, y), n in Counter((x, y) for x, y, _ in auto).most_common():
        print(f"  {x} -> {y}{' x' + str(n) if n > 1 else ''}")
    print(f"\nAUTO-RT {len(rt_auto)} corrections of r/t confusion where both are words and one is far commoner:")
    for x, y, ctx in rt_auto:
        print(f"  {x} -> {y} | {ctx}")
    print(f"\nDROPPED {len(dropped)} marks only A recorded:")
    print("  " + " ".join(t for t, _ in dropped))
    print(f"\nINSERTED {len(inserted)} passages missing from A but agreed by B and C:")
    for n, words in inserted:
        ctx = " ".join(t for _, t in a_words[max(0, n - 4):n]) + " {+" + words + "+} " + " ".join(t for _, t in a_words[n:n + 4])
        print(f"  {ctx}")
    print(f"\nOPEN {len(open_q)} places for a reader (A | B | C | context):")
    for k, (tok, rb, rc, ctx) in enumerate(open_q, 1):
        left, _, right = ctx.partition(" [" + tok + "] ")
        print(f"  {k}. {tok} | {rb} | {rc} | {' '.join(left.split()[-4:])} [] {' '.join(right.split()[:4])}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7:])
