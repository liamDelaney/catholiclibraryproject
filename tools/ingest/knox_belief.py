"""Knox, The Belief of Catholics (Harper, 1927): the reader's decisions for the scan
beliefofcatholic0000knox_h2r4, used by scan_build.py.

Chapter I was proofed separately, page by page (knox_belief_ch1.py). The rest was
collated from three machine readings (collate.py); the numbered ANSWERS settle the
questions that collation left, and FIXES are further corrections found on review.
Answers marked "image" in a comment were settled by looking at the page; the rest
were settled from the other readings and the sense of the sentence.
"""

OFFSET = 4      # PDF page 11 is printed page 7

_TITLES = {
    2: ("II", "The Shop Window"), 3: ("III", "Telling the First Lie"), 4: ("IV", "The God Who Hides Himself"),
    5: ("V", "The Catholic Notion of God"), 6: ("VI", "The Seed-Ground of Revelation"),
    7: ("VII", "The Christian Evidences"), 8: ("VIII", "Our Lord’s Claim Stated"),
    9: ("IX", "Our Lord’s Claim Justified"), 10: ("X", "Where Protestantism Goes Wrong"),
    11: ("XI", "The Foundation of the Church"), 12: ("XII", "The Object and the Act of Faith"),
    13: ("XIII", "The Air Catholics Breathe"), 14: ("XIV", "The Truths Catholics Hold"),
    15: ("XV", "The Rules Catholics Acknowledge"), 16: ("XVI", "The Strength Catholics Receive"),
    17: ("XVII", "The Ambitions Catholics Honour"), 18: ("XVIII", "Catholics and Those Outside"),
    19: ("XIX", "Catholicism and the Future"),
}

# How each section opens in the collated text, and how it should read. The first
# word of a chapter is set in small capitals, which the recognition often garbles.
_OPENINGS = {
    "preface": ("Ir may easily", "It may easily"),
    2: ("Ir so happens", "It so happens"), 3: ("THAT phrase about", "That phrase about"),
    4: ("PHILOSOPHERS have continually", "Philosophers have continually"),
    5: ("Ir the arguments", "If the arguments"), 6: ("Ir would be wholly", "It would be wholly"),
    7: ("I~ the last chapter,", "In the last chapter,"), 8: ("THE statement that", "The statement that"),
    9: ("Ir belongs to", "It belongs to"), 10: ("WHEN we have come", "When we have come"),
    11: ("WHAT did our Lord", "What did our Lord"), 12: ("WE can now elucidate", "We can now elucidate"),
    13: ("In this and the following", "In this and the following"), 14: ("IN this chapter", "In this chapter"),
    15: ("THE Church exercises", "The Church exercises"), 16: ("“AND they bring", "“And they bring"),
    17: ("IN the last three", "In the last three"), 18: ("NortHInG, probably,", "Nothing, probably,"),
    19: ("IF the Church", "If the Church"),
}

SECTIONS = {"preface": {"slug": "preface", "kind": "preface", "ordinal": None, "title": "Preface",
                        "first": _OPENINGS["preface"][0], "first_as": _OPENINGS["preface"][1]}}
for _n, (_ord, _title) in _TITLES.items():
    SECTIONS[str(_n)] = {"slug": f"chapter-{_n}", "kind": "chapter", "ordinal": _ord, "title": _title,
                         "first": _OPENINGS[_n][0], "first_as": _OPENINGS[_n][1]}

ANSWERS = {
    "preface": {4: "", 5: "", 6: "", 7: "me", 8: "explanations,", 9: ""},
    "2": {5: "æsthetic", 8: "business-like", 9: "The", 11: "“", 13: "property", 14: "insinuating", 15: "its",
          16: "example,", 17: "“", 19: "decent", 20: "Consequently,", 21: "decision", 22: "family,", 23: "authority",
          24: "moral", 32: "only"},
    "3": {1: "<i>all</i>", 2: "“", 3: "hell!”;", 4: "“With", 5: "grotesque", 6: "", 8: "not", 9: "<i>if</i>",
          12: "unreflectively,", 13: "unreasoning"},
    "4": {1: "our", 4: "ours;", 5: "<i>possible</i>", 6: "<i>necessarily</i>", 7: "The", 8: "equally", 9: "our",
          12: "explaining", 13: "Power,", 15: "mere"},
    "5": {1: "unbeliever,", 2: "a", 3: "Dichotomising", 5: "our", 6: "", 8: "distinguish", 9: "from", 10: "miracle.",
          12: "to be", 13: "conclusions", 14: "incuriosity"},
    "6": {1: "But Judaism", 2: "every", 3: "<i>i.e.</i>,", 4: "Jews", 5: "a", 7: "<i>hypothesi</i>", 8: "B.C.",
          9: "shadowed.", 11: "political", 12: "of", 14: "privileges,", 15: "because", 16: "facility"},
    "7": {2: "", 5: "Christians—breaking", 6: "", 7: "identifies", 8: "headquarters;", 9: "B.C.", 10: "<i>sui</i>",
          12: "Macedonia,", 14: "bears", 15: "<i>impossibile</i>,", 16: "and", 17: "are", 18: "sufficiently",
          19: "practical", 20: "tradition.", 21: "pursue,", 22: "a footnote.", 24: ""},
    "8": {1: "“Messiahship”", 2: "meet", 3: "I", 4: "<i>hypothesi</i>,", 5: "(ii.)", 6: "(iii.)", 7: "", 8: "",
          9: "divine?", 12: "accustomed"},
    "9": {1: "accompanied", 2: "his", 3: "be", 4: "for a", 5: "It", 6: "<i>rôle</i>.", 7: "on", 8: "a", 9: "merits.",
          10: "", 12: "Which", 14: "our", 15: "like", 16: "<i>hypothesi</i>,", 17: "of", 18: "disturbance”—it",
          19: "beauty.", 21: "extraordinary", 22: "through"},
    "10": {2: "it;", 3: "therefore,", 5: "a", 6: "confidence", 8: "are", 9: "fraternise", 10: ""},
    "11": {1: "later,", 3: "", 4: "souls", 5: "external", 6: "<i>hypothesi</i>,", 7: "devolves", 8: "", 9: "me;",
           11: "to", 12: "it", 13: "energises", 14: "in", 15: "his", 16: "miracle-working", 18: "no unprecedented",
           19: "appoint such", 24: "a", 26: "singling", 28: "jurisdiction,", 29: "“notes”", 30: "a", 31: "the", 34: "quoted"},
    "12": {1: "paper,", 2: "we", 3: "conditio", 5: "relic", 6: "", 7: "germs of", 9: "Irenæus", 10: "<i>e.g.</i>,",
           12: "intellectually", 13: "“pulling", 14: "I", 15: "conclusions.", 16: "seen", 18: "theology"},
    "13": {1: "<i>malgré</i>", 2: "“You", 3: "angels”—the", 7: "<i>talk</i>", 8: "<i>i.e.</i>,", 10: "formula",
           11: "the foundation"},
    "14": {2: "<i>liaison</i>", 3: "were", 4: "independently", 5: "Man in", 6: "our", 7: "since", 9: "", 11: "“",
           12: "“sacramentals”", 13: "answer,", 15: "accidents", 16: "I", 17: "mere"},
    "15": {5: "is", 7: "artificialise", 8: "“", 9: "things?", 10: "a personal", 12: "guidance.", 13: "feeling"},
    "16": {1: "<i>miraculé</i>", 2: "<i>Sacramentum</i>,", 3: "<i>mysterion</i>", 4: "“sacramentum”", 5: "unprimitive.",
           6: "", 7: "life”—that", 8: "“", 9: "great"},
    "17": {1: "in", 2: "what", 5: "(ii.)", 6: "<i>i.e.</i>,", 9: "to", 10: "organisation", 11: "“", 12: "grace.", 13: "ages"},
    "18": {2: "“undivided”", 4: "<i>miseriæ</i>,", 5: "<i>Miseria</i>", 6: "<i>felicitas</i>", 7: "<i>vis</i>",
           8: "<i>eundem</i>", 9: "own"},
    "19": {1: "time", 2: "good”!", 3: "human", 5: "subpœnaed", 6: "I", 7: "experiment", 9: "which", 10: "our",
           11: "clamours", 13: "more", 14: "non-Christian", 15: "grosser", 16: "ours.", 17: "tendency",
           18: "by sacramentalists", 19: "“But", 20: "", 21: "", 22: ""},
}

# Replacements applied wherever they occur, in every section.
GLOBAL = [
    ("“‘ ", "“"), ("‘“ ", "“"),
    ("ex <i>hypothesi</i>", "<i>ex hypothesi</i>"),
    (" a priori", " <i>a priori</i>"), (" a fortiori", " <i>a fortiori</i>"), (" ad infinitum", " <i>ad infinitum</i>"),
]

def _ref(n):
    return f'<a href="endnotes.xhtml#note-{n}" id="noteref-{n}" epub:type="noteref">{n}</a>'


# Kinds: misread (a wrong word), damage (text lost or garbled, restored from the page or the
# other readings), layout (stray marks, fragments, paragraphing), italic, hyphen, note
# (a footnote reference), early-note (the footnote's text lifted out of the body).
FIXES = {
    "preface": [
        ("misread", "and Qit follows", "and it follows"),
        ("layout", "reference. a This book", "reference. This book"),
        ("layout", "the specialist! feels", "the specialist feels"),
        ("layout", "discourtesy of ( hurrying", "discourtesy of hurrying"),
        ("misread", "apart 5from", "apart from"),
        ("layout", "no space for them. Neither,", "no space for them.\n\nNeither,"),
        ("layout", "THe OLD PALACE, OXFORD, July 1927.", "The Old Palace, Oxford, July 1927."),
    ],
    "4": [
        ("damage", "ultimate Agent the whole cycle", "ultimate Agent in the whole cycle"),       # image
        ("misread", "proceeds from 1111.", "proceeds from him."),                                # image
    ],
    "5": [
        ("layout", "read or to be to be suspected", "read or to be suspected"),
        ("damage", "put a spoke the wheels", "put a spoke in the wheels"),
    ],
    "6": [
        ("layout", "singular de privileges", "singular privileges"),
        ("italic", "they are Ais people", "they are <i>his</i> people"),
    ],
    "7": [
        ("italic", "world-wide institution, the Church.", "world-wide institution, <i>the</i> Church."),   # image (audit)
        ("misread", "Ephesus and Colossae.", "Ephesus and Colossæ."),                              # image (audit)
        ("italic", "<i>sui</i> general,", "<i>sui generis</i>,"),
        ("italic", "per <i>impossibile</i>", "<i>per impossibile</i>"),
    ],
    "9": [("layout", "challenged? enged?", "challenged?")],
    "10": [
        ("hyphen", "meta-. phor,", "metaphor,"),
        ("layout", "eighteen hteen—", "eighteen—"),
    ],
    "11": [
        ("layout", "jurisdiction, diction,", "jurisdiction,"),
        ("layout", "these two-tests,", "these two tests,"),                                      # image (audit)
        ("layout", "it would ‘be difficult", "it would be difficult"),                           # image (audit)
    ],
    "12": [
        ("damage", "that rye/jar est conditio possidentis,", "that <i>melior est conditio possidentis</i>,"),
        ("misread", "stream of or tradition", "stream of oral tradition"),
        ("misread", "diminish wit time", "diminish with time"),
    ],
    "13": [("italic", "<i>malgré</i> luz'.", "<i>malgré lui</i>.")],
    "14": [
        ("early-note", "I am giving here one theological view, which is not the only view possible to Catholics.", ""),  # image
        ("note", "We answer, that", "We answer," + _ref(1) + " that"),                                                # image
        ("layout", "God became. Man in", "God became Man in"),
    ],
    "15": [
        ("italic", "Scienti et volenti non fit injuria,", "<i>Scienti et volenti non fit injuria</i>,"),
        ("italic", "the Ne temere decree", "the <i>Ne temere</i> decree"),
        ("layout", "all things?. If", "all things?… If"),                                        # image
    ],
    "17": [("italic", "amps ignotum pro magnifico", "<i>omne ignotum pro magnifico</i>")],
    "18": [
        ("early-note", "1 <i>Miseria</i> is the scholastic opposite of <i>felicitas</i> (Summa, II/2, 30, i.), and the felicity here in question is the supernatural felicity which consists in the vision of God.", ""),
        ("note", "in statu <i>miseriæ</i>,", "<i>in statu miseriæ</i>," + _ref(2)),
        ("layout", "supernatural life The opinion", "supernatural life. The opinion"),
        ("italic", "<i>vis</i> inertia", "<i>vis inertiæ</i>"),
        ("italic", "ad <i>eundem</i>", "<i>ad eundem</i>"),
        ("layout", "claim that a [[page 246]] right", "claim that [[page 246]] right"),                       # image
        ("italic", "penalise in any way differences", "penalise <i>in any way</i> differences"),  # image
    ],
    "19": [("layout", "\n\nLIBRARY i", "")],
}

# The book's two footnotes, in order, as they are written to endnotes.xhtml.
NOTES = [
    ("chapter-14", "I am giving here one theological view, which is not the only view possible to Catholics."),
    ("chapter-18", "<i>Miseria</i> is the scholastic opposite of <i>felicitas</i> (<i>Summa</i>, II/2, 30, i.), and the felicity here in question is the supernatural felicity which consists in the vision of God."),
]
