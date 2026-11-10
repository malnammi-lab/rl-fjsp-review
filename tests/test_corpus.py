"""Tests for the interchange-format reader.

Fixtures under tests/fixtures/ are three real rows copied from an audit run of the
acquisition tool, their abstracts replaced by invented text (the repository withholds the
abstracts), plus a screening.csv written with the same UTF-8 byte-order mark the tool emits.

    pytest -q
"""

import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus  # noqa: E402

FIX = os.path.join(REPO, "tests", "fixtures")
REFS = os.path.join(FIX, "references.json")
SCREEN = os.path.join(FIX, "screening.csv")


@pytest.fixture
def records():
    return corpus.load_references(REFS)


@pytest.fixture
def screening():
    return corpus.load_screening(SCREEN)


# --- helpers --------------------------------------------------------------------

def test_split_list_undoes_the_semicolon_join():
    assert corpus.split_list("a; b;c ; ") == ["a", "b", "c"]


def test_split_list_of_empty_is_empty_not_one_blank():
    assert corpus.split_list("") == []
    assert corpus.split_list(None) == []


def test_short_id_strips_the_url():
    assert corpus.short_id("https://openalex.org/W4401393686") == "W4401393686"
    assert corpus.short_id("W4401393686") == "W4401393686"
    assert corpus.short_id("") == ""


# --- references.json ------------------------------------------------------------

def test_loads_every_row(records):
    assert len(records) == 3
    assert [r.number for r in records] == [1, 12, 10]


def test_types_are_coerced(records):
    r = records[0]
    assert isinstance(r.number, int)
    assert isinstance(r.year, int) and r.year == 2024
    assert isinstance(r.cited_by_count, int)
    assert isinstance(r.is_open_access, bool)


def test_list_fields_are_split(records):
    r = records[0]
    assert isinstance(r.authors, list) and len(r.authors) == 4
    assert isinstance(r.topics, list) and len(r.topics) >= 1
    assert isinstance(r.keywords, list) and "Reinforcement learning" in r.keywords


def test_short_id_is_derived(records):
    assert records[0].short_id == "W4401393686"
    assert records[0].openalex_id.startswith("https://openalex.org/")


def test_doi_prefix_is_stripped(records):
    assert not records[0].doi.startswith("https://")


def test_verdict_survives(records):
    by = {r.number: r for r in records}
    assert by[1].verdict == "VERIFIED"
    assert by[12].verdict == "MISMATCH"


def test_raw_keeps_fields_the_class_does_not_name(records):
    # discrepancy_fields is written by the audit tool but not promoted to an attribute.
    assert "discrepancy_fields" in records[1].raw


def test_missing_optional_fields_do_not_crash():
    """Discovery output lacks the audit-only columns; the reader must not care."""
    r = corpus.Record.from_flat({"number": "7", "title": "x", "openalex_id": "W1"})
    assert r.number == 7 and r.year is None and r.authors == [] and r.verdict == ""
    assert r.rank is None and r.already_known is None


def test_found_reflects_presence_of_an_openalex_id():
    assert corpus.Record.from_flat({"number": 1, "openalex_id": "W1"}).found
    assert not corpus.Record.from_flat({"number": 2}).found


# --- screening.csv --------------------------------------------------------------

def test_screening_reads_through_the_bom(screening):
    """The byte-order mark does not hide the first column, `number`."""
    assert set(screening) == {1, 12, 10}


def test_decisions_are_normalised(screening):
    assert screening[1].decision == "include"
    assert screening[12].decision == "exclude"
    assert screening[10].decision == "uncertain"
    assert screening[1].confidence == "high"


def test_kept_follows_the_default_policy(screening):
    assert screening[1].kept and screening[10].kept
    assert not screening[12].kept


# --- the join -------------------------------------------------------------------

def test_included_keeps_include_and_uncertain_by_default(records, screening):
    kept = corpus.included(records, screening)
    assert sorted(r.number for r in kept) == [1, 10]


def test_included_can_be_narrowed(records, screening):
    kept = corpus.included(records, screening, keep=("include",))
    assert [r.number for r in kept] == [1]


def test_silence_is_not_consent(records, screening):
    """A record with no decision is not included, and is reported as unscreened."""
    del screening[10]
    assert [r.number for r in corpus.included(records, screening)] == [1]
    assert [r.number for r in corpus.unscreened(records, screening)] == [10]


def test_nothing_unscreened_when_every_record_has_a_decision(records, screening):
    assert corpus.unscreened(records, screening) == []
