#!/usr/bin/env python3
"""Corrections to Chapter I of Knox, The Belief of Catholics (Harper, 1927),
made by reading the Internet Archive scan beliefofcatholic0000knox_h2r4 page by page.

Usage: python3 knox_belief_ch1.py <ch1.txt from scan_text.py> <out chapter-1.xhtml>

Every change to the recognised text is listed here with its kind, so the proof
can be audited and counted:

  misread   a non-word the recognition produced (found by a dictionary)
  realword  a real but wrong word (found only by reading against the page)
  damage    text lost under a stamp or mark, keyed in from the page image
  layout    running matter, stamps, stray marks, paragraph joins and splits
  hyphen    a decision about a word broken across lines
  italic    italics, which the text layer does not carry
"""
import re
import sys
from collections import Counter
from pathlib import Path

J = "⁀"   # the join mark scan_text.py leaves where a word was broken across lines

C = [
    # ---- page 7 (PDF 11)
    ("layout", "[[page 11]] CHAPTER I.\n\nThe Modern Distaste for Religion IN a too", "[[page 11 = 7]] In a too"),
    ("misread", "I tefer,", "I refer,"),
    ("realword", "modern evils ate symptoms", "modern evils are symptoms"),
    ("realword", "modern results ate the true", "modern results are the true"),
    ("hyphen", "guess- work", "guess-work"),
    ("layout", "\n\nZz\n\n[[page 12 = 8]] Amidst", "\n\n[[page 12 = 8]] Amidst"),
    # ---- page 8
    ("misread", "a cateless and", "a careless and"),
    ("realword", "last few yeats we", "last few years we"),
    ("misread", "year to yeat.", "year to year."),
    ("layout", "at random— Trollope", "at random—Trollope"),
    ("misread", "“a fourth” P", "“a fourth”?"),
    ("realword", "of a mote exact", "of a more exact"),
    # ---- page 9
    ("layout", "[[page 13 = THE]]", "[[page 13 = 9]]"),
    ("misread", "who wete ordained", "who were ordained"),
    ("misread", "in the petiod", "in the period"),
    ("realword", "forty-five yeats the", "forty-five years the"),
    ("misread", f"re{J}ctuited", "recruited"),
    ("realword", "in themselves ate surely", "in themselves are surely"),
    ("misread", "falling-of in", "falling-off in"),
    ("misread", "the ptestige of", "the prestige of"),
    ("hyphen", f"re{J}cruiting", "recruiting"),
    ("italic", "the stupor mundi now", "the <i xml:lang='la'>stupor mundi</i> now"),
    # ---- page 10
    ("layout", "[[page 14 = Io]]", "[[page 14 = 10]]"),
    ("layout", "towards religion? at\n\n", "towards religion?\n\n"),
    ("layout", "birth-rate;some", "birth-rate; some"),
    ("misread", "to this -7s# or that", "to this <i>-ism</i> or that"),
    # ---- page 11
    ("layout", "[[page 15 = THE]]", "[[page 15 = 11]]"),
    ("italic", "mean, pro tanto, a", "mean, <i xml:lang='la'>pro tanto</i>, a"),
    ("misread", "a prayer, ot consciously", "a prayer, or consciously"),
    ("misread", "country whete he", "country where he"),
    ("misread", "were teally growing", "were really growing"),
    ("realword", "human wills, ate manifest", "human wills, are manifest"),
    ("layout", "knowledge;some", "knowledge; some"),
    ("layout", "minds trained\n\nLibrary of the\n\nTIDOT\n\n3 bu iu\n\nOCICAI,\n\nSJ VARI LE Sd\n\nSEMINAR\n\npossi aAe&eY J\n\n[[page 16 = {2]] to tread but",
               "minds trained [[page 16 = 12]] to read but"),
    # ---- page 12
    ("misread", "eternity. Ido not", "eternity. I do not"),
    ("misread", "our doots;", "our doors;"),
    ("realword", "; anesthetics and", "; anæsthetics and"),
    ("realword", "A tush age", "A rush age"),
    ("layout", "the pew;meanwhile", "the pew; meanwhile"),
    ("misread", "ago. ‘The rise", "ago. The rise"),
    ("misread", "own patticular scheme", "own particular scheme"),
    # ---- page 13
    ("layout", "[[page 17 = THE]]", "[[page 17 = 13]]"),
    ("misread", "to cfiticism,", "to criticism,"),
    ("misread", "the temarriage of", "the remarriage of"),
    ("misread", "the tendency 1s there", "the tendency is there"),
    ("misread", "have no teason to", "have no reason to"),
    ("realword", "might be attested by force", "might be arrested by force"),
    ("layout", "in certain _ points", "in certain points"),
    # ---- page 14
    ("layout", "the adoption — of ceremonies", "the adoption of ceremonies"),
    ("realword", "such as ate found", "such as are found"),
    ("layout", "them-_ selves", "themselves"),
    ("hyphen", f"safe{J}guarded", "safeguarded"),
    ("layout", "branded as — unorthodox", "branded as unorthodox"),
    ("realword", "more and mote, are _ becoming", "more and more, are becoming"),
    ("misread", "their sur- | toundings", "their surroundings"),
    ("layout", "theology while — they", "theology while they"),
    ("layout", "a pathetic — error", "a pathetic error"),
    ("layout", "when it © must", "when it must"),
    ("layout", "so wide as ' it stands", "so wide as it stands"),
    ("layout", "will hardly, — I suppose", "will hardly, I suppose"),
    ("damage", "accustomed to area nise in", "accustomed to recognise in"),
    ("layout", "the Holy | Spirit", "the Holy Spirit"),
    ("damage", "see them gchar: up Sunday", "see them pasted up Sunday"),
    ("damage", f"notice{J}oatds—high-flown", "notice-boards—high-flown"),
    ("realword", "tickle the eat of", "tickle the ear of"),
    ("misread", "music, thena hearty", "music, then a hearty"),
    # ---- page 15
    ("layout", f"so accom{J}[[page 19]] Epis. THE MODERN DISTASTE FOR RELIGION _ 15 modating", "so accom" + J + "[[page 19 = 15]] modating"),
    ("misread", "organised religiori is pattly an", "organised religion is partly an"),
    ("layout", "the parsons. preach.”", "the parsons preach.”"),
    ("layout", "the preacher . reconsider", "the preacher reconsider"),
    # ---- page 16
    ("layout", "[[page 20 = 16]]", "[[page 20 = 16]]"),
    ("italic", "or a fortiori any", "or <i xml:lang='la'>a fortiori</i> any"),
    ("damage", f"deliberately aloe the credi{J}bility", "deliberately judge the credibility"),
    ("misread", "does exetcise a", "does exercise a"),
    ("misread", "a docttine which", "a doctrine which"),
    ("misread", "to be affitmed is", "to be affirmed is"),
    # ---- page 17
    ("layout", "[[page 21 = THE]]", "[[page 21 = 17]]"),
    ("layout", "the old tradition. )", "the old tradition."),
    # ---- page 18
    ("realword", "Christian camp, ate beginning", "Christian camp, are beginning"),
    # ---- page 19
    ("layout", "[[page 23 = THE]]", "[[page 23 = 19]]"),
    ("misread", "“joint setvices”", "“joint services”"),
    ("misread", "importance; eventhe inauguration", "importance; even the inauguration"),
    ("layout", "“Anglo-Catholic”? movement", "“Anglo-Catholic” movement"),
    # ---- page 20
    ("misread", f"contro{J}[[page 24 = 20]] vetsial", f"contro{J}[[page 24 = 20]] versial"),
    ("misread", "incubus of tadition.", "incubus of tradition."),
    # ---- page 21: a stamp or tear has taken the right-hand side of several lines
    ("layout", "on any terms? It is not only the theological speculations of the _ modern",
               "on any terms?\n\nIt is not only the theological speculations of the modern"),
    ("damage", f"and their pro{J}fe ing, and for that reason not reassuring. It is an infinitely small point, but does the abandonment, total or partial, of the clerical\n\nby some modern clergymen really make the\n\nity feel more at home with them? Does it not\n\ncteate the icion that they are ashamed of\n\nbeing what they are? Distrust may even be aroused, sometimes, the modern",
               "and their professors—accommodating, and for that reason not reassuring. It is an infinitely small point, but does the abandonment, total or partial, of the clerical garb by some modern clergymen really make the laity feel more at home with them? Does it not rather create the suspicion that they are ashamed of being what they are? Distrust may even be aroused, sometimes, by the modern"),
    ("misread", f"many prte{J}ferred", "many preferred"),
    ("layout", "sympathised,no doubt", "sympathised, no doubt"),
    ("damage", "but it is ionable whether", "but it is questionable whether"),
    ("damage", "could differ so fu ‘\n\n", "could differ so fundamentally.\n\n"),
    # ---- page 22
    ("realword", "but they ate, to my mind", "but they are, to my mind"),
    ("layout", "“‘ Let the Churches", "“Let the Churches"),
    ("misread", "heir to along line", "heir to a long line"),
    ("layout", "before “‘ the Churches”", "before “the Churches”"),
    ("hyphen", f"fellow-country{J}men", "fellow-countrymen"),
    ("misread", "Prodigal’s retutn.", "Prodigal’s return."),
]


def main(source, out):
    text = Path(source).read_text(encoding="utf-8")
    counts = Counter()
    for kind, old, new in C:
        n = text.count(old)
        if n != 1:
            sys.exit(f"expected exactly one {old!r}, found {n}")
        text = text.replace(old, new)
        counts[kind] += 1

    # Remaining broken words: the join mark means the scan tool judged them ordinary
    # line-end breaks. Each was read against the page; all close up.
    counts["hyphen (closed up, as printed)"] = text.count(J)
    # A page that ends in the middle of a word: the break is marked inside the word, unspaced.
    text = re.sub(J + r"\[\[page \d+ = (\d+)\]\]\s*", r"[[inword \1]]", text)
    text = text.replace(J, "")

    text = text.replace("xml:lang='la'", 'xml:lang="la"')
    paragraphs = [p.strip() for p in text.strip().split("\n\n")]
    body = []
    for p in paragraphs:
        p = re.sub(r"\s*\[\[page \d+ = (\d+)\]\]\s*", lambda m: f' <span id="page-{m.group(1)}" title="{m.group(1)}" epub:type="pagebreak"/>', p)
        p = re.sub(r"\[\[inword (\d+)\]\]", lambda m: f'<span id="page-{m.group(1)}" title="{m.group(1)}" epub:type="pagebreak"/>', p)
        p = re.sub(r"^ (<span)", r"\1", p)
        p = re.sub(r'(\S)(<span id="page-\d+"[^>]*/>)(\S)', r"\1\2\3", p)      # page break inside a word
        p = re.sub(r'(/>)\s+', r"\1", p)
        p = p.replace(' <span id="page-', ' <span id="page-')
        body.append(f"\t\t\t<p>{p}</p>")
    xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" epub:prefix="z3998: http://www.daisy.org/z3998/2012/vocab/structure/, se: https://standardebooks.org/vocab/1.0" xml:lang="en-GB">
	<head>
		<title>I: The Modern Distaste for Religion</title>
		<link href="../css/core.css" rel="stylesheet" type="text/css"/>
		<link href="../css/local.css" rel="stylesheet" type="text/css"/>
	</head>
	<body epub:type="bodymatter z3998:non-fiction">
		<section id="chapter-1" epub:type="chapter">
			<hgroup>
				<h2 epub:type="z3998:ordinal z3998:roman">I</h2>
				<p epub:type="title">The Modern Distaste for Religion</p>
			</hgroup>
{chr(10).join(body)}
		</section>
	</body>
</html>
'''
    Path(out).write_text(xhtml, encoding="utf-8")
    words = len(re.sub(r"<[^>]+>", " ", "\n".join(body)).split())
    print(f"{len(paragraphs)} paragraphs, {words} words")
    for kind, n in counts.most_common():
        print(f"  {n:3d}  {kind}")
    print(f"  {sum(v for k, v in counts.items() if not k.startswith('hyphen (closed'))} listed corrections in all")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
