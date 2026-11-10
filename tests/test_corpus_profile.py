"""Tests for the corpus profile: the descriptive numbers the method section quotes."""

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

from src import corpus  # noqa: E402
import corpus_profile as cp  # noqa: E402

METHOD = ["reinforcement learning"]
PROBLEM = ["job shop scheduling"]


def rec(n, title, abstract="", source="openalex", publisher="Elsevier BV",
        work_type="article", year=2024):
    return corpus.Record.from_flat({
        "number": n, "openalex_id": "https://openalex.org/W%d" % n, "title": title,
        "abstract": abstract, "abstract_source": source, "publisher": publisher,
        "work_type": work_type, "year": year, "verdict": "DISCOVERED"})


RECORDS = [
    rec(1, "Reinforcement learning for job shop scheduling", "An abstract.", "openalex", "IEEE"),
    rec(2, "Reinforcement learning for job shop scheduling", "", "none", "Elsevier BV", year=1990),
    rec(3, "A learned scheduler", "Reinforcement learning for job shop scheduling.", "scopus"),
    rec(4, "A learned scheduler", "Heuristics for shops.", "springer", "Springer", "conference-paper"),
    rec(5, "A learned scheduler", "", "none", "Springer"),
]


def test_types_years_and_sources():
    types, y0, y1 = cp.types_and_years(RECORDS)
    assert types == {"article": 4, "conference-paper": 1} and (y0, y1) == (1990, 2024)
    assert cp.abstract_sources(RECORDS) == {"openalex": 1, "none": 2, "scopus": 1, "springer": 1}


def test_missing_at_source_by_publisher():
    rows = cp.missing_at_source(RECORDS)
    assert rows[0] == ("Elsevier BV", 2, 2) and rows[1] == ("Springer", 2, 2)
    assert all(p != "IEEE" for p, _, _ in rows)


def test_retrieval_check_reads_the_filled_abstract():
    out = cp.retrieval_check(RECORDS, METHOD, PROBLEM)
    assert out["not served"] == 4
    assert out["title carries both facets"] == 1
    assert out["title lacks a facet; the filled abstract carries both"] == 1
    assert out["title lacks a facet; the filled abstract does not carry both"] == 1
    assert out["title lacks a facet; no abstract from any source"] == 1
    assert out["title lacks a facet"] == 3


def test_title_repeats_are_grouped_not_removed():
    records = RECORDS + [rec(8, "A Learned Scheduler!", "", "none", "Zenodo")]
    repeats = cp.title_repeats(records)
    # Records 3, 4, 5 and 8 share a title once normalised; records 1 and 2 share another.
    assert [len(g) for g in repeats] == [4, 2]
    assert len(records) == 6  # nothing removed
    text = "\n".join(cp.render_repeats(repeats))
    assert "| Records beyond the first of each group | 4 |" in text


def dup(n, doi, first_author="Jin Huang", source_type="journal", work_type="article"):
    return corpus.Record.from_flat({
        "number": n, "openalex_id": "https://openalex.org/W%d" % n, "title": "Same title",
        "doi": doi, "first_author": first_author, "source_type": source_type,
        "work_type": work_type, "verdict": "DISCOVERED"})


PREFIXES = ["10.5281", "10.48550"]


def test_repeat_kinds_in_order():
    assert cp.repeat_kind([dup(1, "10.1/a"), dup(2, "10.1/A")], PREFIXES) == "same_doi"
    assert cp.repeat_kind([dup(1, "10.1/a"), dup(2, "10.1/a/pdf")], PREFIXES) == "doi_variant"
    assert cp.repeat_kind([dup(1, "10.1/a"), dup(2, "10.1/a.v1")], PREFIXES) == "doi_variant"
    assert cp.repeat_kind([dup(1, "10.1/a"), dup(2, "")], PREFIXES) == "no_doi"
    assert cp.repeat_kind([dup(1, "10.1/a"), dup(2, "10.5281/zenodo.9")], PREFIXES) == "repository_copy"
    assert cp.repeat_kind([dup(1, "10.1/a"), dup(2, "10.2/b", work_type="preprint")], PREFIXES) == "repository_copy"
    assert cp.repeat_kind([dup(1, "10.1/a"), dup(2, "10.2/b")], PREFIXES) == "two_venues"
    # An extra digit is a different DOI, not a variant.
    assert cp.repeat_kind([dup(1, "10.1/a.10"), dup(2, "10.1/a.103")], PREFIXES) == "two_venues"


def test_first_authors_agree_in_either_name_order():
    assert cp.authors_agree([dup(1, "10.1/a", "Jin Huang"), dup(2, "10.1/b", "Huang Jin")]) == "yes"
    assert cp.authors_agree([dup(1, "10.1/a", "Jin Huang"), dup(2, "10.1/b", "Wen Song")]) == "no"
    assert cp.authors_agree([dup(1, "10.1/a", "Jin Huang"), dup(2, "10.1/b", "")]) == "unknown"


def test_publisher_groups_sum_imprints_by_prefix():
    records = RECORDS + [
        rec(6, "A learned scheduler", "An abstract.", "openalex", "Springer Nature"),  # served
        rec(7, "A learned scheduler", "", "none", "Birkhäuser"),  # not a prefix match
    ]
    grouped = cp.missing_by_group(records, {"Elsevier": "Elsevier", "Springer": "springer"})
    # Springer: records 4, 5 (Springer) and 6 (Springer Nature, served); 4 and 5 not served.
    assert [(g, t, m) for g, t, m, _ in grouped] == [("Elsevier", 2, 2), ("Springer", 3, 2)]
    assert grouped[1][3] == ["Springer", "Springer Nature"]
