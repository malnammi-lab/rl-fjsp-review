"""Tests for the screening rules (src/screening.py)."""

import math
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus  # noqa: E402
from src import screening as sc  # noqa: E402

RULES = dict(inclusion_rules=3, exclusion_rules=7, prefer=[(6, 1)],
             aliases={"shop class outside scope": 6,
                      "learning other than reinforcement learning": 7})


def label(reason):
    return sc.rule_label(reason, **RULES)


# ------------------------------------------------------------------------------ the vote

@pytest.mark.parametrize("ballot, outcome", [
    (["exclude", "exclude", "exclude"], "exclude"),
    (["include", "include", "include"], "include"),
    (["include", "include", "uncertain"], "include"),
    (["include", "uncertain", "include"], "include"),
    (["include", "include", "exclude"], "disagreement"),   # one objection keeps it from a vote
    (["include", "uncertain", "uncertain"], "disagreement"),
    (["uncertain", "uncertain", "uncertain"], "disagreement"),
    (["exclude", "exclude", "uncertain"], "disagreement"),  # exclusion needs all three
    (["exclude", "exclude", "include"], "disagreement"),
])
def test_vote_rule(ballot, outcome):
    assert sc.vote(ballot) == outcome


def test_vote_refuses_an_unknown_decision():
    with pytest.raises(ValueError):
        sc.vote(["include", "include", "maybe"])


@pytest.mark.parametrize("ballot, settled", [
    # Every disagreement of three screeners (protocol, Screening).
    (["include", "include", "exclude"], "include"),
    (["include", "exclude", "exclude"], "exclude"),
    (["include", "uncertain", "exclude"], "exclude"),
    (["uncertain", "exclude", "exclude"], "exclude"),
    (["uncertain", "uncertain", "exclude"], "exclude"),
    (["include", "uncertain", "uncertain"], "uncertain"),
    (["uncertain", "uncertain", "uncertain"], "uncertain"),
    # On a ballot the vote decides, the vote's own outcome.
    (["include", "include", "uncertain"], "include"),
    (["exclude", "exclude", "exclude"], "exclude"),
])
def test_settle_rule(ballot, settled):
    assert sc.settle(ballot) == settled
    if sc.vote(ballot) != "disagreement":
        assert sc.vote(ballot) == settled


def test_settle_refuses_an_unknown_decision():
    with pytest.raises(ValueError):
        sc.settle(["include", "exclude", "maybe"])


# --------------------------------------------------------------------- the full-text gate

GATE_TERMS, GATE_STEMS = ["flexible job shop", "flexible job shops"], ["fjs"]


@pytest.mark.parametrize("text, expected", [
    ("Deep RL for the Flexible Job-Shop problem", True),     # punctuation reads as a space
    ("Two flexible job shops", True),
    ("the DFJSP with transport (FJSPT)", True),             # abbreviations by the stem
    ("A multi-objective MO-FJSP", True),
    ("a job shop with flexible machines", False),           # not the term, not a stem
    ("a flexible job shopping list", False),                # whole words only
    ("flexible flow shop scheduling", False),
    ("", False),
])
def test_carries_whole_words_and_abbreviation_stems(text, expected):
    assert sc.carries(text, GATE_TERMS, GATE_STEMS) is expected


def test_carries_without_stems_matches_terms_only():
    assert not sc.carries("an FJSP", GATE_TERMS)
    assert sc.carries("Automated Guided-Vehicles", ["guided vehicles"])


@pytest.mark.parametrize("decision, named, gate", [
    ("include", True, "full text"),
    ("uncertain", True, "full text"),
    ("include", False, "abstract only"),
    ("uncertain", False, "set aside"),
    ("exclude", True, ""),
    ("exclude", False, ""),
    ("", True, ""),                                          # no decision yet: no gate
])
def test_gate(decision, named, gate):
    assert sc.gate(decision, named) == gate
    assert gate == "" or gate in sc.GATES


def test_the_config_is_this_reviews():
    """configs/screening.toml holds this review's settings: the panel, the protocol's rules
    and sample, and the records dropped before screening. It has no escape clause, full-text
    gate or spot check; screening_setup tests their code. Disagreements are settled by rule,
    and the sample is drawn from every record decided without a person: 60 removed and 40
    included (protocol, Screening)."""
    import tomllib
    with open(os.path.join(REPO, "configs", "screening.toml"), "rb") as fh:
        cfg = tomllib.load(fh)
    assert list(cfg["screeners"]) == ["qwen38", "gemma26", "glimmer30"]
    assert cfg["calibration"]["models"] == list(cfg["screeners"])
    assert cfg["calibration"]["screeners"] == list(cfg["screeners"]) + ["osamah"]
    assert cfg["calibration"]["batch_size"] == 25 and cfg["calibration"]["leave_out"] == []
    assert (cfg["rules"]["inclusion_rules"], cfg["rules"]["exclusion_rules"]) == (3, 5)
    assert cfg["rules"]["prefer"] == [] and cfg["rules"]["aliases"] == {}
    assert cfg["rules"]["settle_disagreements"] is True
    v = cfg["validation"]
    assert (v["strata"], v["seed"]) == ("decision", 20261012)
    assert (v["quota_exclude"], v["quota_include"]) == (60, 40) and "size" not in v
    assert cfg["inputs"]["dropped"] == "datasets/dropped.csv"
    assert not {"escape", "gate", "spot_check"} & set(cfg)
    assert not {"escape", "spot_check"} & set(cfg["inputs"])
    labels = [label for label, _ in cfg["page"]["rules"]]
    assert labels[0] == "Inclusion 1 to 3" and labels[-1] == "Exclusion 5"


def test_proportional_quotas_split_the_sample_by_stratum_size():
    q = sc.proportional_quotas
    assert q({"exclude": 300, "include": 100}, 100) == {"exclude": 75, "include": 25}
    assert q({"exclude": 413, "include": 194}, 100) == {"exclude": 68, "include": 32}
    assert q({"exclude": 3, "include": 3}, 3) == {"exclude": 2, "include": 1}   # a tie: the first
    assert q({"exclude": 2, "include": 7}, 100) == {"exclude": 2, "include": 7}  # taken whole
    assert q({"exclude": 0, "include": 150}, 100) == {"exclude": 0, "include": 100}


# ------------------------------------------------------------------- the rule a reason cites

@pytest.mark.parametrize("reason, expected", [
    ("Exclusion 6: a flow shop.", "exclusion 6"),
    ("exclusion rule 6 applies", "exclusion 6"),
    ("Exclusion criteria 1 and 6.", "exclusion 6"),        # both 1 and 6: rule 6 says 6
    ("Exclusion 6 and exclusion 1.", "exclusion 6"),
    ("Exclusion 7, and exclusion 3 as well.", "exclusion 7"),  # otherwise the first cited
    ("Criterion 7: supervised only.", "exclusion 7"),      # above the inclusion rules
    ("Criterion 2: vehicle routing.", "criterion 2, list not named"),
    ("Fails inclusion 1: not a job shop.", "inclusion 1"),
    ("Shop class outside scope: a flow line.", "exclusion 6"),
    ("Learning other than reinforcement learning.", "exclusion 7"),
    ("Vehicle routing, not manufacturing.", "none named"),
    ("Published in 2020 by a rule 12 committee.", "none named"),
    ("", "none named"),
])
def test_rule_label(reason, expected):
    assert label(reason) == expected


def test_cited_rules_keeps_the_order_of_citation():
    assert sc.cited_rules("Inclusion 1 fails; exclusion 3, 5 / 6 apply") == [
        ("inclusion", 1), ("exclusion", 3), ("exclusion", 5), ("exclusion", 6)]


def test_majority_label():
    assert sc.majority_label(["exclusion 1", "exclusion 6", "exclusion 1"]) == "exclusion 1"
    assert sc.majority_label(["exclusion 1", "exclusion 6", "none named"]) == "no majority"


def test_label_order_puts_exclusion_rules_first():
    labels = ["none named", "inclusion 1", "exclusion 7", "criterion 2, list not named",
              "exclusion 1", "no majority"]
    assert sorted(labels, key=sc.label_order)[:4] == [
        "exclusion 1", "exclusion 7", "inclusion 1", "criterion 2, list not named"]


# ------------------------------------------------------------------------- the statistics

E, U, I = "exclude", "uncertain", "include"


def test_weighted_kappa_by_hand():
    # A: E E U I, B: E U U I. Linear: po = 0.5/4, pe = 7/16, kappa = 1 - 2/7 = 5/7.
    pairs = [(E, E), (E, U), (U, U), (I, I)]
    assert math.isclose(sc.weighted_kappa(pairs, "linear"), 5 / 7)
    # Quadratic: po = 0.25/4, pe = 5/16, kappa = 1 - 0.2 = 0.8.
    assert math.isclose(sc.weighted_kappa(pairs, "quadratic"), 0.8)


def test_weighted_kappa_edges():
    assert sc.weighted_kappa([(E, E), (I, I)]) == 1.0
    assert sc.weighted_kappa([(E, I), (I, E)]) == -1.0
    assert sc.weighted_kappa([(E, E), (E, E)]) is None   # one category: chance disagreement 0
    assert sc.weighted_kappa([]) is None
    with pytest.raises(ValueError):
        sc.weighted_kappa([(E, E)], "cubic")


def test_upper_bound_closed_form_and_a_known_value():
    assert math.isclose(sc.upper_bound(0, 150, 0.95), 1 - 0.05 ** (1 / 150), rel_tol=1e-9)
    # One-sided 95% Clopper-Pearson for 1 of 10 is 0.3942 in published tables.
    assert abs(sc.upper_bound(1, 10, 0.95) - 0.3942) < 5e-4
    assert sc.upper_bound(5, 5) == 1.0
    assert sc.upper_bound(0, 0) is None
    assert sc.upper_bound(0, 250) < sc.upper_bound(0, 150) < sc.upper_bound(1, 150)


def test_upper_bound_holds_for_large_n_without_overflow():
    assert 0 < sc.upper_bound(3, 5000) < 0.01


# ----------------------------------------------------------------------------- the draw

def test_sample_is_seeded_and_independent_of_order_and_of_the_other_stratum():
    pool = list(range(1, 1001))
    a = sc.stratified_sample({"exclude": pool, "include": [1, 2]}, {"exclude": 150, "include": 100}, 7)
    b = sc.stratified_sample({"include": list(range(5000, 6000)), "exclude": pool[::-1]},
                             {"exclude": 150, "include": 100}, 7)
    assert a["exclude"] == b["exclude"]
    assert len(a["exclude"]) == 150 and len(set(a["exclude"])) == 150
    assert a["include"] == [1, 2]                      # smaller than its quota: taken whole
    assert len(b["include"]) == 100
    c = sc.stratified_sample({"exclude": pool}, {"exclude": 150}, 8)
    assert c["exclude"] != a["exclude"]


def test_blind_order_is_a_seeded_permutation():
    numbers = list(range(1, 51))
    first = sc.blind_order(numbers, 7)
    assert sorted(first) == numbers and first != numbers
    assert sc.blind_order(reversed(numbers), 7) == first


# ------------------------------------------------------------------- decision files

def write(path, text, encoding="utf-8-sig"):
    with open(path, "w", encoding=encoding, newline="") as fh:
        fh.write(text)


def test_read_decisions(tmp_path):
    path = tmp_path / "d.csv"
    write(path, "number,title,decision,confidence,reason,evidence\n"
                "1,A,Include,High,Exclusion 6,\"q\"\n2,B,,,,\n3,C,exclude,,x,\n")
    decided, blank, raw = sc.read_decisions(str(path))
    assert decided[1].decision == "include" and decided[1].confidence == "high"
    assert decided[3].decision == "exclude"
    assert blank == [2]
    assert raw[1]["title"] == "A"


@pytest.mark.parametrize("body", [
    "1,A,maybe,high,x,\n",
    "1,A,include,sure,x,\n",
    "1,A,include,high,x,\n1,A,exclude,high,x,\n",
])
def test_read_decisions_refuses_bad_rows(tmp_path, body):
    path = tmp_path / "d.csv"
    write(path, "number,title,decision,confidence,reason,evidence\n" + body)
    with pytest.raises(SystemExit):
        sc.read_decisions(str(path))


def test_read_decisions_names_an_excel_code_page_file(tmp_path):
    path = tmp_path / "d.csv"
    write(path, "number,title,decision\n1,Café,include\n", encoding="cp1252")
    with pytest.raises(SystemExit, match="CSV UTF-8"):
        sc.read_decisions(str(path))


def rec(n, title="T", abstract="A"):
    return corpus.Record.from_flat({"number": n, "title": title, "abstract": abstract})


def test_batch_skips_records_with_neither_title_nor_abstract():
    records = [rec(1), rec(2, "", ""), rec(3), rec(4, "", "only an abstract"), rec(5)]
    assert [r.number for r in sc.batch(records, 1, 2)] == [1, 3]
    assert [r.number for r in sc.batch(records, 2, 2)] == [4, 5]


def test_to_screen_drops_the_duplicates():
    assert [r.number for r in sc.to_screen([rec(1), rec(2), rec(3)], {2})] == [1, 3]


def test_sheet_shows_no_votes_and_prefills_what_is_decided(tmp_path):
    md, csv_ = str(tmp_path / "s.md"), str(tmp_path / "s.csv")
    done = {2: corpus.Decision(2, "exclude", "high", "Exclusion 6", "q")}
    sc.write_sheet([rec(1, "One"), rec(2, "Two | pipe")], md, csv_, "Sheet", ["Intro."], filled=done)
    text = open(md, encoding="utf-8").read()
    assert "## [1] One" in text and "Abstract: A" in text
    import csv
    with open(csv_, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert list(rows[0]) == sc.SHEET_FIELDS
    assert rows[0]["decision"] == "" and rows[1]["decision"] == "exclude"


@pytest.mark.parametrize("body", [
    "number;title;decision\n1;A;include\n",       # Excel with a semicolon separator
    "1,A,include,high,x,\n2,B,exclude,high,y,\n",  # the header row deleted
])
def test_read_decisions_refuses_a_file_without_its_columns(tmp_path, body):
    path = tmp_path / "d.csv"
    write(path, body)
    with pytest.raises(SystemExit, match="no 'number' and 'decision' columns"):
        sc.read_decisions(str(path))


def test_read_decisions_accepts_a_capitalised_header(tmp_path):
    path = tmp_path / "d.csv"
    write(path, " Number ,Title,Decision,Confidence\n1,A,Include,High\n")
    decided, _, _ = sc.read_decisions(str(path))
    assert decided[1].decision == "include" and decided[1].confidence == "high"


def test_prefer_labels_applies_to_the_record():
    assert sc.prefer_labels(["exclusion 1", "exclusion 1", "exclusion 6"], [(6, 1)]) == ["exclusion 6"] * 3
    assert sc.prefer_labels(["exclusion 1", "exclusion 7"], [(6, 1)]) == ["exclusion 1", "exclusion 7"]


def test_rounds_and_the_latest_persons_round(tmp_path):
    for rnd in (2, 10, 1):
        (tmp_path / ("round-%d" % rnd)).mkdir()
    (tmp_path / "round-x").mkdir()
    (tmp_path / "round-1" / "p.csv").write_text("number,decision\n", encoding="utf-8")
    (tmp_path / "round-2" / "p.csv").write_text("number,decision\n", encoding="utf-8")
    found = sc.rounds(str(tmp_path), ["m", "p"])
    assert list(found) == [1, 2, 10]
    rnd, path = sc.latest_person_round(str(tmp_path), ["m", "p"], "p")
    assert rnd == 2 and path.endswith(os.path.join("round-2", "p.csv"))
    assert sc.latest_person_round(str(tmp_path / "none"), ["p"], "p") == (None, None)


def test_a_sheet_is_written_into_folders_that_do_not_exist_yet(tmp_path):
    md = str(tmp_path / "results" / "screening" / "validation" / "s.md")
    csv_ = str(tmp_path / "results" / "screening" / "other" / "s.csv")
    sc.write_sheet([rec(1)], md, csv_, "Sheet", ["Intro."])
    assert "## [1]" in open(md, encoding="utf-8").read()
    assert (tmp_path / "results" / "screening" / "other" / "sheets-issued.json").exists()


def test_a_sheet_with_unsaved_decisions_is_not_overwritten(tmp_path):
    md, csv_ = str(tmp_path / "s.md"), str(tmp_path / "s.csv")
    sc.write_sheet([rec(1), rec(2)], md, csv_, "Sheet", ["Intro."])
    write(csv_, "number,title,decision,confidence,reason,evidence\n1,T,exclude,high,Exclusion 6,q\n2,T,,,,\n")
    with pytest.raises(SystemExit, match="was edited and differs from datasets/x.csv on records 1"):
        sc.write_sheet([rec(1), rec(2)], md, csv_, "Sheet", ["Intro."], save_as="datasets/x.csv")
    assert "exclude" in open(csv_, encoding="utf-8-sig").read()      # the typed work is kept
    saved = {1: corpus.Decision(1, "exclude", "high", "Exclusion 6", "q")}
    sc.write_sheet([rec(1), rec(2)], md, csv_, "Sheet", ["Intro."], saved=saved)  # saved: re-issued blank
    assert "exclude" not in open(csv_, encoding="utf-8-sig").read()


def test_unsaved_compares_every_field(tmp_path):
    csv_ = str(tmp_path / "s.csv")
    write(csv_, "number,title,decision,confidence,reason,evidence\n1,T,exclude,high,Exclusion 6: a flow shop,q\n")
    saved = {1: corpus.Decision(1, "exclude", "high", "Exclusion 1", "q")}
    assert sc.unsaved(csv_, saved) == [1]                       # same decision, a new reason
    saved[1] = corpus.Decision(1, "exclude", "high", "Exclusion 6: a flow shop", "q")
    assert sc.unsaved(csv_, saved) == []


def test_the_lock_ignores_formatting_but_not_decisions(tmp_path):
    a, b = str(tmp_path / "a.csv"), str(tmp_path / "b.csv")
    write(a, "number,decision,reason\n2,exclude,x\n1,include,y\n")
    write(b, '"number","decision","reason"\r\n1,Include,"y "\r\n2,exclude,x\r\n')
    da, db = sc.read_decisions(a)[0], sc.read_decisions(b)[0]
    assert sc.decisions_digest(da) == sc.decisions_digest(db)
    lock = str(tmp_path / "lock.json")
    assert sc.verify_lock(lock, "k", da, "a.csv") is False
    sc.write_lock(lock, "k", da, triggered=True)
    assert sc.verify_lock(lock, "k", db, "b.csv") is True
    da[1] = corpus.Decision(1, "exclude", "", "", "")
    with pytest.raises(SystemExit, match="has changed since it was locked"):
        sc.verify_lock(lock, "k", da, "a.csv")


def test_a_sheet_nobody_edited_is_reissued_after_the_saved_file_is_corrected(tmp_path):
    md, csv_ = str(tmp_path / "s.md"), str(tmp_path / "s.csv")
    first = {1: corpus.Decision(1, "exclude", "high", "Exclusion 1", "q")}
    sc.write_sheet([rec(1)], md, csv_, "Sheet", ["Intro."], filled=first)
    corrected = {1: corpus.Decision(1, "exclude", "high", "Exclusion 6: a flow shop", "q")}
    sc.write_sheet([rec(1)], md, csv_, "Sheet", ["Intro."], filled=corrected)
    assert "Exclusion 6: a flow shop" in open(csv_, encoding="utf-8-sig").read()


# ------------------------------------------------------------------- the screening page

def page_settings():
    with open(os.path.join(REPO, "src", "screening_page.html"), encoding="utf-8") as fh:
        template = fh.read()
    return {"template": template, "criteria_brief": "# Brief", "criteria_full": "",
            "rules": [["Exclusion 6", "no job shop"]]}


def read_page(path):
    import json
    import re
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    blocks = re.findall(r'<script[^>]*id="sheet-data"[^>]*>(.*?)</script>', html, re.S)
    assert len(blocks) == 1
    return html, json.loads(blocks[0])


def test_the_page_template_holds_one_data_block():
    template = page_settings()["template"]
    assert template.count(sc.PAGE_PLACEHOLDER) == 1
    assert "<script" in template and "http://" not in template and "src=" not in template


def test_a_page_holds_its_records_and_cannot_be_closed_by_a_record(tmp_path):
    path = str(tmp_path / "p.html")
    hostile = rec(1, "A </script><script>alert(1)</script> title", "x <!-- y")
    sc.write_page(path, page_settings(), "Sheet", "screening", "datasets/out.csv",
                  sc.SHEET_FIELDS, ["Intro."], [sc.page_record(hostile)])
    html, data = read_page(path)
    assert "</script><script>alert" not in html
    assert data["records"][0]["title"] == hostile.title
    assert data["records"][0]["abstract"] == "x <!-- y"
    assert (data["kind"], data["save_as"], data["columns"]) == ("screening", "datasets/out.csv", sc.SHEET_FIELDS)
    assert data["rules"] == [{"label": "Exclusion 6", "hint": "no job shop"}]
    assert data["sheet_id"] == "p" and "generated" not in data   # no time: same inputs, same page


def test_a_page_record_links_only_when_asked():
    r = corpus.Record.from_flat({"number": 3, "title": "T", "doi": "https://doi.org/10.1/x",
                                 "openalex_id": "https://openalex.org/W3"})
    assert "link" not in sc.page_record(r)
    assert sc.page_record(r, link=True)["link"] == "https://doi.org/10.1/x"
    no_doi = corpus.Record.from_flat({"number": 4, "title": "T", "openalex_id": "https://openalex.org/W4"})
    assert sc.page_record(no_doi, link=True)["link"] == "https://openalex.org/W4"


def test_a_sheet_with_a_page_writes_it_beside_the_csv_without_votes_or_links(tmp_path):
    md, csv_ = str(tmp_path / "sample.md"), str(tmp_path / "sample.csv")
    done = {2: corpus.Decision(2, "exclude", "high", "Exclusion 6: a flow shop", "q")}
    sc.write_sheet([rec(1, "One"), rec(2, "Two")], md, csv_, "Sample", ["Intro."], filled=done,
                   save_as="datasets/screening-validation.csv", page=page_settings())
    assert sc.page_path(csv_) == str(tmp_path / "sample.html")
    _, data = read_page(sc.page_path(csv_))
    assert [r["number"] for r in data["records"]] == [1, 2]
    assert "answer" not in data["records"][0]
    assert data["records"][1]["answer"]["reason"] == "Exclusion 6: a flow shop"
    assert not any(k in r for r in data["records"] for k in ("models", "cells", "link"))
    assert data["save_as"] == "datasets/screening-validation.csv"


def test_a_sheet_without_a_page_writes_none(tmp_path):
    md, csv_ = str(tmp_path / "s.md"), str(tmp_path / "s.csv")
    sc.write_sheet([rec(1)], md, csv_, "Sheet", ["Intro."])
    assert not os.path.exists(sc.page_path(csv_))
