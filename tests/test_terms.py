"""Tests for how a text is read for the names of the query (src/terms.py)."""

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import terms  # noqa: E402


def test_a_text_is_lower_case_with_punctuation_as_spaces():
    assert terms.norm("Deep Q-Network, for the FJSP!") == "deep q network for the fjsp"
    assert terms.norm(None) == ""


def test_a_term_is_found_only_as_whole_words():
    text = terms.norm("A flowshop scheduling study with job-shop scheduling")
    assert terms.has_any(["job shop scheduling"], text)
    assert not terms.has_any(["shop scheduling", "flow"], terms.norm("A flowshop scheduling study"))


def test_a_facets_terms_are_its_groups_in_order():
    assert terms.facet_terms({"names": ["a", "b"], "algorithms": ["c"]}) == ["a", "b", "c"]
