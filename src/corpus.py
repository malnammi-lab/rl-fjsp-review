"""Reader for the corpus files this repository analyzes.

A separate, private tool acquires the corpus from OpenAlex and coordinates screening. Its
files are the whole interface: references.json (one record per work) and one
screening-*.csv per screener, combined into screening.csv by runners/screening_consensus.py.
Nothing here fetches anything. The search is reproduced from the query, source and date in
results/search/search-record.md. The schema below mirrors what that tool writes and is not
imported from it, so the repository depends on no private package. The abstracts are
withheld from the released record files (src/withheld.py).
"""

import csv
import json
from dataclasses import dataclass, field

from src import withheld

# Screening decisions that `included` and `Decision.kept` keep by default: the two a full-text
# gate carries forward (src/screening.py, gate). Without a gate, runners/make_tables.py counts
# uncertain records on their own.
DEFAULT_KEEP = ("include", "uncertain")


def split_list(value):
    """The acquisition tool joins list fields with '; '. Undo that.

    Authors, topics and keywords all arrive this way. An empty string means an empty
    list, not a list containing one empty string.
    """
    if not value:
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def short_id(openalex_id):
    """'https://openalex.org/W4401393686' -> 'W4401393686'. Already-short ids pass through."""
    if not openalex_id:
        return ""
    return str(openalex_id).rstrip("/").rsplit("/", 1)[-1]


def _int(value):
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes")


@dataclass
class Record:
    """One work in the corpus, as the acquisition tool recorded it.

    Fields the tool did not populate are None or empty rather than absent, so analysis
    code can read them without checking for KeyError. The original flat dict is kept in
    ``raw`` so that nothing the tool wrote is lost, even fields this class does not name.
    """

    number: int
    openalex_id: str
    short_id: str
    doi: str
    title: str
    year: int
    verdict: str
    resolved_by: str
    work_type: str
    source_type: str
    venue: str
    publisher: str
    primary_topic: str
    primary_field: str
    topics: list
    keywords: list
    authors: list
    first_author: str
    cited_by_count: int
    is_open_access: bool
    abstract: str
    # Present only in discovery output: position in the result set, and whether the
    # work was already in a library the search was checked against.
    rank: int
    already_known: bool
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_flat(cls, d):
        return cls(
            number=_int(d.get("number")),
            openalex_id=d.get("openalex_id") or "",
            short_id=short_id(d.get("openalex_id")),
            doi=(d.get("doi") or "").replace("https://doi.org/", ""),
            title=d.get("title") or "",
            year=_int(d.get("year")),
            verdict=d.get("verdict") or "",
            resolved_by=d.get("resolved_by") or "",
            work_type=d.get("work_type") or "",
            source_type=d.get("source_type") or "",
            venue=d.get("venue") or "",
            publisher=d.get("publisher") or "",
            primary_topic=d.get("primary_topic") or "",
            primary_field=d.get("primary_field") or "",
            topics=split_list(d.get("topics")),
            keywords=split_list(d.get("keywords")),
            authors=split_list(d.get("authors")),
            first_author=d.get("first_author") or "",
            cited_by_count=_int(d.get("cited_by_count")),
            is_open_access=_bool(d.get("is_open_access")),
            abstract=d.get("abstract") or "",
            rank=_int(d.get("rank")),
            already_known=_bool(d.get("already_known")) if d.get("already_known") not in (None, "") else None,
            raw=dict(d),
        )

    @property
    def found(self):
        """The tool located this work in OpenAlex. NOT_FOUND rows carry no metadata."""
        return bool(self.openalex_id)


@dataclass
class Decision:
    """One screening decision against the written criteria: a screener's, a person's or the
    consensus's."""

    number: int
    decision: str
    confidence: str
    reason: str
    evidence: str

    @property
    def kept(self):
        return self.decision in DEFAULT_KEEP


def load_references(path, abstracts=False):
    """Read references.json. Returns records in file order.

    The file is a dict with ``source``, ``count``, ``columns`` and ``references``; only
    the last is needed here. The others are provenance and are left for the manifest.
    With ``abstracts``, a file whose abstracts this repository withholds takes them from the
    authors' copy when it is in place (src/withheld.py); otherwise they stay blank.
    """
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    rows = payload["references"] if isinstance(payload, dict) else payload
    records = [Record.from_flat(row) for row in rows]
    if abstracts:
        withheld.merge(path, records)
    return records


def load_screening(path):
    """Read screening.csv into {number: Decision}.

    The file starts with a UTF-8 byte-order mark, which utf-8-sig strips; read as plain
    UTF-8, the first column would not be ``number``.
    """
    decisions = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            number = _int(row.get("number"))
            if number is None:
                continue
            decisions[number] = Decision(
                number=number,
                decision=(row.get("decision") or "").strip().lower(),
                confidence=(row.get("confidence") or "").strip().lower(),
                reason=row.get("reason") or "",
                evidence=row.get("evidence") or "",
            )
    return decisions


def included(records, screening, keep=DEFAULT_KEEP):
    """The corpus after screening: records whose decision is in ``keep``.

    A record with no decision at all is NOT included. Silence is not consent; an
    unscreened work is a gap in the process, and ``unscreened`` reports it.
    """
    keep = set(keep)
    return [r for r in records if r.number in screening and screening[r.number].decision in keep]


def unscreened(records, screening):
    """Records that reached the corpus but never received a decision."""
    return [r for r in records if r.number not in screening]
