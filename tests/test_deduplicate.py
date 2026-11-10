"""Tests for the duplicate rule (configs/deduplicate.toml) and its use in the flow counts."""

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

from src import corpus, duplicates  # noqa: E402
import deduplicate  # noqa: E402
import make_tables  # noqa: E402

PREFIXES = ["10.5281", "10.48550"]
# The kinds the duplicate rule removes (configs/deduplicate.toml, [rule] removable_kinds).
RULE_A = ["same_doi", "doi_variant", "no_doi", "repository_copy"]


def rec(n, title, doi="", author="Jin Huang", source_type="journal", work_type="article", rank=None):
    return corpus.Record.from_flat({
        "number": n, "openalex_id": "https://openalex.org/W%d" % n, "title": title, "doi": doi,
        "first_author": author, "source_type": source_type, "work_type": work_type,
        "rank": rank if rank is not None else n, "verdict": "DISCOVERED"})


RECORDS = [
    # Repository copies of a journal article: the journal record is kept, whatever its rank.
    rec(1, "Paper one", "10.5281/zenodo.1", rank=1),
    rec(2, "Paper one", "10.5281/zenodo.2", rank=2),
    rec(3, "Paper one", "10.1/one", rank=3),
    # A DOI with a /pdf suffix: the base DOI is kept.
    rec(4, "Paper two", "10.1/two/pdf", rank=4),
    rec(5, "Paper two", "10.1/two", rank=5),
    # Two publisher DOIs, same first author: kept whole (a conference and a journal version).
    rec(6, "Paper three", "10.1/conf", work_type="conference-paper"),
    rec(7, "Paper three", "10.2/journal"),
    # Same title, different first authors: different papers, kept whole.
    rec(8, "Paper four", "10.5281/zenodo.8", author="Wen Song"),
    rec(9, "Paper four", "10.1/four", author="Wan-Ze Li"),
    # A first author printed in another script: cannot be compared, kept whole.
    rec(10, "Paper five", "10.1/five", author="Yingzi Wei"),
    rec(11, "Paper five", "", author="魏英姿"),
    # A single record: never touched.
    rec(12, "Paper six", "10.1/six"),
]


def test_rule_a_removes_only_certain_same_author_copies():
    removed, kept = duplicates.decide(RECORDS, PREFIXES, RULE_A)
    assert sorted((r.number, keep.number, kind) for r, keep, kind in removed) == [
        (1, 3, "repository_copy"), (2, 3, "repository_copy"), (4, 5, "doi_variant")]
    kept_titles = sorted((g[0].title, kind, agree) for g, kind, agree in kept)
    assert kept_titles == [("Paper five", "no_doi", "unknown"),
                           ("Paper four", "repository_copy", "no"),
                           ("Paper three", "two_venues", "yes")]


def test_rule_b_would_also_remove_two_venues():
    removed, _ = duplicates.decide(RECORDS, PREFIXES, RULE_A + ["two_venues"])
    assert 6 in {r.number for r, _, _ in removed} or 7 in {r.number for r, _, _ in removed}


def test_runner_rows_and_report():
    removed, kept = duplicates.decide(RECORDS, PREFIXES, RULE_A)
    rows = deduplicate.rows(removed)
    assert [(r["number"], r["duplicate_of"]) for r in rows] == [(1, 3), (2, 3), (4, 5)]
    text = deduplicate.render(len(RECORDS), removed, kept, RULE_A)
    assert "| Duplicates removed | 3 |" in text and "| Records to screen | 9 |" in text
    assert "| Groups kept whole | 3 |" in text


def test_flow_counts_use_the_removed_list(tmp_path):
    path = tmp_path / "duplicates.csv"
    removed, _ = duplicates.decide(RECORDS, PREFIXES, RULE_A)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=deduplicate.FIELDS)
        w.writeheader()
        w.writerows(deduplicate.rows(removed))
    numbers = make_tables.load_duplicates(str(path))
    assert numbers == {1, 2, 4}
    rows, unscreened = make_tables.flow_counts(RECORDS, {}, numbers)
    counts = dict(rows)
    assert counts["Identified, databases and registers"] == 12
    assert counts["Duplicates removed"] == 3
    assert counts["Screened on title and abstract"] == 9
