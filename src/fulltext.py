"""A paper's full text as the core's coding reads it: the markdown converted from its PDF,
which is not released with this repository, each page opened by a line `{N}`
followed by 48 dashes, N the PDF's page counted from 0.

Written on 20 October 2026, before any full text was coded, for the coding agent's tools and
the checks of its answers (runners/core_check.py). Nothing here reaches the network, and the
module runs on Python 3.11 or later.

    load(path)                    the Paper: its lines, each line's page, its reference list
    outline(paper)                the headings, with their pages and lines
    search(paper, pattern)        the lines that match a regular expression, case ignored
    read(paper, page=, start=, end=)
                                  a page, or a range of lines
    page_text(paper, page)        one page's text
    body_text(paper)              the paper without its reference list, page markers kept
    normalize(text)               the form in which a quote is compared with the paper
    check_quote(paper, page, quote)
                                  whether a quote is on the page it cites; if not, the pages
                                  it is on and the closest passage of the page cited
    shared_run(text, paper)       the first run of RUN words that a text shares with the paper

The reference list is the section under the paper's references heading (a heading whose text,
without markup or a section number, is References, Reference, Bibliography, Literature cited
or References and notes), up to the next heading or the end of the file. Every one of the 99
full texts has exactly one such heading; only record 77 has headings after its reference list
(a corrigendum), which stay in the paper. The tools and the checks read the paper without its
reference list; line numbers are the file's.

A quote is compared after `normalize`: Unicode compatibility forms folded (NFKC, so that
ligatures and full-width characters match), typographic quotation marks, apostrophes, dashes
and ellipses read as their ASCII forms, HTML tags, markdown's backslash escapes and its
emphasis characters (* and _) removed, and runs of white space, line breaks included, read as
one space. Case and every other character are kept.
"""

import difflib
import re
import unicodedata
from collections import namedtuple

MARKER = re.compile(r"^\{(\d+)\}-{48}\s*$")
HEADING = re.compile(r"^#{1,6}\s+(.*)$")
REFERENCES = ("references", "reference", "bibliography", "literature cited",
              "references and notes")
RUN = 8              # the most words a published text may share in a row with the paper
QUOTE_WORDS = 50     # the longest quote, in words
SEARCH_HITS = 40     # the most lines a search returns
SNIPPET = 300        # the characters of a matching line a search shows
READ_LINES = 200     # the most lines a read returns
READ_CHARS = 40000   # the most characters a read returns
CLOSE_ENOUGH = 0.5   # the least similarity for a passage to be offered as the closest

# Typographic characters read as their ASCII forms, by code point, so that this file stays
# ASCII: quotation marks and apostrophes, primes, hyphens and dashes, the minus sign, the
# ellipsis.
TYPOGRAPHIC = {
    0x2018: "'", 0x2019: "'", 0x201A: "'", 0x201B: "'", 0x2032: "'",
    0x201C: '"', 0x201D: '"', 0x201E: '"', 0x201F: '"', 0x2033: '"',
    0x2010: "-", 0x2011: "-", 0x2012: "-", 0x2013: "-", 0x2014: "-", 0x2015: "-",
    0x2212: "-", 0x2026: "...",
}
ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|<>])")
# The HTML tags the converter writes (span, br, sup, sub, i, b and a few more), with
# attributes only on the tags that take them, and autolinks, each within one line. A bare
# "<", as in an inequality (p < 0.05), is text: the earlier pattern <[^>]+> took everything
# from such a "<" to the next ">" on the page, across lines, and hid it from the quote checks.
# Found on 21 October 2026 on record 477, whose page 7 lost ten lines between two equations.
TAG = re.compile(r"</?(?:span|br|sup|sub|i|b|em|strong|u|s|del|code|a|math|li|ul|ol|p|div|"
                 r"img|hr|small|table|thead|tbody|tr|td|th)\s*/?>"
                 r"|<(?:span|a|img|math|div|table|td|th)\s[^<>\n]*>"
                 r"|<https?://[^<>\s]*>", re.IGNORECASE)

# lines: the file's lines, without line ends; page_of[i]: the page of line i (counted from
# 0; -1 before the first marker); markers: {page: the index of its marker line}; refs: the
# reference list as (its first line's index, the index after its last line), or None;
# norms: {page: the page's text, normalized}; path: where it was read from.
Paper = namedtuple("Paper", "path lines page_of markers refs norms")


def heading_text(line):
    """A heading line's text without markup or a section number; None if not a heading."""
    found = HEADING.match(line)
    if not found:
        return None
    text = TAG.sub("", found.group(1)).replace("*", "").replace("_", "").strip()
    return re.sub(r"^\d+(\.\d+)*\.?\s*", "", text)


def reference_list(lines):
    """(first, end) of the reference list, end exclusive; None if the paper has none."""
    starts = [i for i, line in enumerate(lines)
              if (heading_text(line) or "").lower() in REFERENCES]
    if not starts:
        return None
    first = starts[-1]
    end = next((i for i in range(first + 1, len(lines)) if HEADING.match(lines[i])),
               len(lines))
    return first, end


def in_body(paper, i):
    """Whether line i is outside the reference list."""
    return not (paper.refs and paper.refs[0] <= i < paper.refs[1])


def load(path):
    """The Paper read from `path`."""
    with open(path, encoding="utf-8-sig") as fh:
        lines = fh.read().splitlines()
    page_of, markers, page = [], {}, -1
    for i, line in enumerate(lines):
        found = MARKER.match(line)
        if found:
            page = int(found.group(1))
            markers[page] = i
        page_of.append(page)
    paper = Paper(path, lines, page_of, markers, reference_list(lines), {})
    for p in markers:
        paper.norms[p] = normalize(page_text(paper, p))
    return paper


def page_range(paper, page):
    """(first, end) of a page's lines after its marker, end exclusive."""
    start = paper.markers[page]
    later = [i for i in paper.markers.values() if i > start]
    return start + 1, min(later) if later else len(paper.lines)


def page_text(paper, page):
    """A page's text without its marker line and the reference list; "" for a page the paper
    does not have."""
    if page not in paper.markers:
        return ""
    first, end = page_range(paper, page)
    return "\n".join(paper.lines[i] for i in range(first, end) if in_body(paper, i))


def body_text(paper):
    """The paper without its reference list, its page markers kept."""
    return "\n".join(line for i, line in enumerate(paper.lines) if in_body(paper, i))


def clean_heading(line):
    found = HEADING.match(line)
    text = TAG.sub("", found.group(1)) if found else line
    return " ".join(text.replace("*", "").split())


def outline(paper):
    """[{page, line, heading}] for the headings outside the reference list."""
    return [{"page": paper.page_of[i], "line": i + 1, "heading": clean_heading(line)}
            for i, line in enumerate(paper.lines)
            if in_body(paper, i) and HEADING.match(line)]


def snippet(line, start):
    """At most SNIPPET characters of a line around a match that begins at `start`."""
    if len(line) <= SNIPPET:
        return line
    begin = max(0, min(start - SNIPPET // 3, len(line) - SNIPPET))
    text = line[begin:begin + SNIPPET]
    return ("..." if begin > 0 else "") + text + ("..." if begin + SNIPPET < len(line) else "")


def search(paper, pattern, limit=SEARCH_HITS):
    """{"hits": [{page, line, text}], "total": the lines matching} for the lines outside the
    reference list that match `pattern`, a regular expression with case ignored, in the
    file's order; at most `limit` hits, each shown around its first match. Raises ValueError
    for a pattern that does not compile."""
    try:
        rx = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        raise ValueError("the pattern does not compile: %s" % e)
    hits, total = [], 0
    for i, line in enumerate(paper.lines):
        if not in_body(paper, i) or MARKER.match(line):
            continue
        found = rx.search(line)
        if not found:
            continue
        total += 1
        if len(hits) < limit:
            hits.append({"page": paper.page_of[i], "line": i + 1,
                         "text": snippet(line, found.start())})
    return {"hits": hits, "total": total}


def read(paper, page=None, start=None, end=None):
    """{"lines": [{line, page, text}], "more": the next line not shown, or None} for one page,
    or for lines `start` to `end` (counted from 1, both included), at most READ_LINES lines
    and READ_CHARS characters, the reference list left out. Raises ValueError for a page the
    paper does not have, or neither a page nor a first line."""
    if page is not None:
        if page not in paper.markers:
            raise ValueError("the paper has no page %d; its pages are %d to %d"
                             % (page, min(paper.markers), max(paper.markers)))
        first, stop = page_range(paper, page)
    elif start is not None:
        first = max(int(start), 1) - 1
        stop = min(int(end) if end is not None else first + READ_LINES, len(paper.lines))
        if stop <= first:
            raise ValueError("the last line comes before the first, or after the paper's "
                             "end (line %d)" % len(paper.lines))
    else:
        raise ValueError("give a page, or a first and a last line")
    rows, chars, more = [], 0, None
    for i in range(first, stop):
        if not in_body(paper, i):
            continue
        if len(rows) >= READ_LINES or chars + len(paper.lines[i]) > READ_CHARS and rows:
            more = i + 1
            break
        rows.append({"line": i + 1, "page": paper.page_of[i], "text": paper.lines[i]})
        chars += len(paper.lines[i])
    return {"lines": rows, "more": more}


def normalize(text):
    """`text` in the form a quote is compared in (the module's docstring)."""
    text = unicodedata.normalize("NFKC", text or "")
    text = "".join(TYPOGRAPHIC.get(ord(c), c) for c in text)
    text = ESCAPE.sub(r"\1", TAG.sub("", text))
    return " ".join(text.replace("*", "").replace("_", "").split())


def closest(quote, text):
    """(the passage of `text` most like `quote`, as printed, and its similarity from 0 to
    1): every run of the quote's length in words, compared word by word with punctuation and
    case set aside; the first of equally similar runs."""
    qw, tw = quote.split(), text.split()
    if not qw or not tw:
        return "", 0.0
    n = len(qw)
    bare = [re.sub(r"\W", "", w).lower() for w in tw]
    matcher = difflib.SequenceMatcher(autojunk=False)
    matcher.set_seq2([re.sub(r"\W", "", w).lower() for w in qw])
    best, at = -1.0, 0
    for i in range(max(1, len(tw) - n + 1)):
        matcher.set_seq1(bare[i:i + n])
        r = matcher.ratio()
        if r > best:
            best, at = r, i
    return " ".join(tw[at:at + n]), round(best, 2)


def check_quote(paper, page, quote):
    """{"found", "words", "pages", "across", "closest", "similarity"}: whether the quote is
    on page `page` (both normalized); its words; where it is not, the other pages it is on,
    whether it runs across the marker into the next page, and the closest passage of the page
    cited when it is similar enough."""
    q = normalize(quote)
    out = {"found": False, "words": len(q.split()), "pages": [], "across": False,
           "closest": "", "similarity": 0.0}
    if not q:
        return out
    if q in paper.norms.get(page, ""):
        out["found"] = True
        return out
    out["pages"] = sorted(p for p, text in paper.norms.items() if q in text)
    if page in paper.norms:
        later = sorted(p for p in paper.norms if p > page)
        if later and q in paper.norms[page] + " " + paper.norms[later[0]]:
            out["across"] = True
        passage, score = closest(q, paper.norms[page])
        if score >= CLOSE_ENOUGH:
            out["closest"], out["similarity"] = passage, score
    return out


_GRAMS = {}


def words(text):
    """A text's words, normalized and in lower case."""
    return re.findall(r"\w+", normalize(text).lower())


def shared_run(text, paper, n=RUN):
    """The first run of `n` words of `text` that also occurs in the paper outside its
    reference list, or "" when there is none."""
    w = words(text)
    if len(w) < n:
        return ""
    key = (paper.path, n, len(paper.lines))
    if key not in _GRAMS:
        body = words(body_text(paper))
        _GRAMS[key] = {tuple(body[i:i + n]) for i in range(len(body) - n + 1)}
    grams = _GRAMS[key]
    for i in range(len(w) - n + 1):
        if tuple(w[i:i + n]) in grams:
            return " ".join(w[i:i + n])
    return ""
