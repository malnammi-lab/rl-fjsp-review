"""Tests for the reading of a paper's full text (src/fulltext.py), on a small paper written
with CRLF line ends, its pages starting at {3}, a reference list and a corrigendum after it.
Characters beyond ASCII are built with chr(), so that this file stays ASCII."""

import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import fulltext as ft  # noqa: E402

LQ, RQ, NDASH, FI = chr(0x201C), chr(0x201D), chr(0x2013), chr(0xFB01)
BAR = "-" * 48
LINES = [
    "",                                                                          # 1
    "{3}" + BAR,                                                                 # 2
    "",                                                                          # 3
    "# **Learning to schedule**",                                                # 4
    "",                                                                          # 5
    "#### <span id=\"p1\"></span>**Abstract**",                                  # 6
    "The agent is trained with " + LQ + "proximal policy optimization" + RQ
    + " on the " + FI + "rst shop.",                                             # 7
    "",                                                                          # 8
    "{4}" + BAR,                                                                 # 9
    "",                                                                          # 10
    "## 2. Method",                                                              # 11
    "",                                                                          # 12
    "The state holds *each machine's* load and the jobs' due dates; a mask "
    "removes busy machines.",                                                    # 13
    "It is tested on Brandimarte" + NDASH + "s instances mk01 to mk10.",         # 14
    "The quote runs across",                                                     # 15
    "{5}" + BAR,                                                                 # 16
    "the page marker here.",                                                     # 17
    "## 7. References",                                                          # 18
    "[1] Brandimarte P. Routing and scheduling in a flexible job shop by tabu.", # 19
    "{6}" + BAR,                                                                 # 20
    "[2] Another reference about a policy.",                                     # 21
    "# Corrigendum",                                                             # 22
    "The authors regret a typo in the policy section.",                          # 23
]


@pytest.fixture
def paper(tmp_path):
    path = os.path.join(tmp_path, "9.md")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("\r\n".join(LINES) + "\r\n")
    return ft.load(path)


def test_pages_follow_their_markers_from_the_first_page_number(paper):
    assert paper.markers == {3: 1, 4: 8, 5: 15, 6: 19}
    assert paper.page_of[0] == -1 and paper.page_of[6] == 3 and paper.page_of[12] == 4
    assert paper.page_of[16] == 5 and paper.page_of[22] == 6
    # CRLF line ends are gone from the lines.
    assert all("\r" not in line for line in paper.lines)


def test_the_reference_list_runs_from_its_heading_to_the_next_heading(paper):
    assert paper.refs == (17, 21)
    assert ft.reference_list(["# Advantages of preferences learning", "text"]) is None
    assert ft.heading_text("#### <span id=\"x\"></span>**7. REFERENCES**") == "REFERENCES"


def test_the_outline_lists_the_headings_outside_the_reference_list(paper):
    found = ft.outline(paper)
    assert [(h["page"], h["line"], h["heading"]) for h in found] == [
        (3, 4, "Learning to schedule"), (3, 6, "Abstract"), (4, 11, "2. Method"),
        (6, 22, "Corrigendum")]


def test_search_ignores_case_and_the_reference_list(paper):
    found = ft.search(paper, "POLICY")
    assert found["total"] == 2
    assert [(h["page"], h["line"]) for h in found["hits"]] == [(3, 7), (6, 23)]
    assert ft.search(paper, "policy", limit=1)["hits"][0]["line"] == 7
    assert ft.search(paper, "tabu")["total"] == 0
    with pytest.raises(ValueError, match="does not compile"):
        ft.search(paper, "[unclosed")


def test_a_long_line_is_shown_around_its_match():
    line = "x" * 1000 + " needle " + "y" * 1000
    shown = ft.snippet(line, line.index("needle"))
    assert "needle" in shown and shown.startswith("...") and shown.endswith("...")
    assert len(shown) <= ft.SNIPPET + 6


def test_read_gives_a_page_or_a_range_and_leaves_out_the_reference_list(paper):
    assert [r["line"] for r in ft.read(paper, page=4)["lines"]] == [10, 11, 12, 13, 14, 15]
    assert [r["line"] for r in ft.read(paper, page=6)["lines"]] == [22, 23]
    assert [r["line"] for r in ft.read(paper, start=4, end=6)["lines"]] == [4, 5, 6]
    with pytest.raises(ValueError, match="no page 9"):
        ft.read(paper, page=9)
    with pytest.raises(ValueError, match="before the first"):
        ft.read(paper, start=6, end=4)
    with pytest.raises(ValueError, match="give a page"):
        ft.read(paper)


def test_normalize_folds_typography_markup_and_spacing():
    text = (LQ + "a  *b*" + RQ + "\n" + NDASH + " " + FI + "x <sup>2</sup> \\_y\\_ "
            + chr(0x2026))
    assert ft.normalize(text) == '"a b" - fix 2 y ...'


def test_a_bare_less_than_sign_is_text_not_a_tag():
    # A bare "<" (an inequality) and a later ">" do not hide the text between them; the
    # converter's tags still go.
    text = ("$$a = x \\text{if } \\xi < \\epsilon$$\nThe reward rises with the gain.\n"
            "$$r = 5 \\text{ if } \\Delta > 0.01$$ <span id=\"p2\"></span>end<br/>")
    out = ft.normalize(text)
    assert "The reward rises with the gain." in out
    assert "span" not in out and "br" not in out and out.endswith("0.01$$ end")
    assert ft.normalize("p < 0.05 and x<y and i<j and k>l") == (
        "p < 0.05 and x<y and i<j and k>l")
    assert ft.normalize("see <https://example.org/a> now <a href=\"#x\">here</a>") == (
        "see now here")


def test_a_quote_is_found_on_its_page_after_normalizing_both(paper):
    found = ft.check_quote(paper, 3, 'trained with "proximal policy optimization" on the '
                                     'first shop')
    assert found["found"] and found["words"] == 9
    assert ft.check_quote(paper, 4, "each machine's load and the jobs' due dates")["found"]


def test_a_quote_on_another_page_is_located(paper):
    found = ft.check_quote(paper, 3, "a mask removes busy machines")
    assert not found["found"] and found["pages"] == [4]


def test_a_quote_across_a_page_marker_is_reported(paper):
    found = ft.check_quote(paper, 4, "The quote runs across the page marker here.")
    assert not found["found"] and found["across"] and found["pages"] == []


def test_a_near_miss_gets_the_closest_passage_of_its_page(paper):
    found = ft.check_quote(paper, 4, "a mask removes idle machines")
    assert not found["found"] and found["pages"] == []
    assert found["closest"] == "a mask removes busy machines." and found["similarity"] >= 0.5


def test_the_reference_list_cannot_be_quoted(paper):
    found = ft.check_quote(paper, 5, "Routing and scheduling in a flexible job shop")
    assert not found["found"] and found["pages"] == []


def test_a_text_sharing_eight_words_in_a_row_with_the_paper_is_caught(paper):
    copied = "We train with proximal policy optimization on the first shop today"
    assert ft.shared_run(copied, paper) == ("with proximal policy optimization on the first "
                                            "shop")
    assert ft.shared_run("PPO with a graph encoder and a masked action space", paper) == ""
