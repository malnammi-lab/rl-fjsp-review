"""Tests for the consensus runner: the vote applied to three screeners' files, the person's
resolutions and rescues, the counts by rule, and the flow counts that follow."""

import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import corpus  # noqa: E402
from src import screening as sc  # noqa: E402
import make_tables  # noqa: E402
import screening_consensus as consensus  # noqa: E402
import screening_setup as setup  # noqa: E402

CFG = {"rules": {"inclusion_rules": 3, "exclusion_rules": 7, "prefer": [[6, 1]],
                 "aliases": {"shop class outside scope": 6}}}
LABEL = consensus.labeller(CFG)


def d(n, decision, confidence="high", reason="", evidence=""):
    return corpus.Decision(n, decision, confidence, reason, evidence or "quote %d" % n)


def votes(table):
    """{number: (a, b, c)} of (decision, reason) -> {model: {number: Decision}}."""
    out = {m: {} for m in setup.MODELS}
    for n, ballot in table.items():
        for m, cast in zip(setup.MODELS, ballot):
            if cast is not None:
                out[m][n] = d(n, cast[0], reason=cast[1])
    return out


BALLOTS = {
    1: [("exclude", "Exclusion 1"), ("exclude", "Exclusion 6"), ("exclude", "exclusion 6: flow shop")],
    2: [("include", ""), ("include", ""), ("uncertain", "")],
    3: [("include", ""), ("exclude", "Exclusion 3"), ("uncertain", "")],
    4: [("include", ""), ("include", ""), None],
}


def by_number(rows):
    return {r["number"]: r for r in rows}


def test_vote_outcomes_basis_and_rule():
    rows = by_number(consensus.combine([1, 2, 3, 4], votes(BALLOTS), LABEL))
    assert (rows[1]["decision"], rows[1]["basis"], rows[1]["rule"]) == ("exclude", "vote", "exclusion 6")
    assert rows[1]["evidence"] == "quote 1"
    assert (rows[2]["decision"], rows[2]["basis"]) == ("include", "vote")
    assert (rows[3]["outcome"], rows[3]["decision"], rows[3]["basis"]) == ("disagreement", "", "unresolved")
    assert (rows[4]["outcome"], rows[4]["decision"]) == ("incomplete", "")


def test_confidence_is_the_lowest_of_the_agreeing_votes():
    v = votes({1: [("include", ""), ("include", ""), ("uncertain", "")]})
    v["screener-b"][1] = d(1, "include", "low")
    v["screener-c"][1] = d(1, "uncertain", "")   # not agreeing: ignored
    assert consensus.combine([1], v, LABEL)[0]["confidence"] == "low"


def test_a_resolution_decides_a_disagreement_and_names_who():
    rows = consensus.combine([3], votes(BALLOTS), LABEL,
                             resolutions={3: d(3, "exclude", reason="Exclusion 3: a position paper")},
                             resolved_by={3: "osamah"})
    r = rows[0]
    assert (r["decision"], r["basis"], r["rule"]) == ("exclude", "resolution", "exclusion 3")
    assert r["reason"].startswith("Decided by osamah after a disagreement")


def test_a_resolution_for_a_record_that_is_not_a_disagreement_is_refused():
    with pytest.raises(SystemExit, match="disagreements only"):
        consensus.combine([1, 2, 3], votes(BALLOTS), LABEL, resolutions={2: d(2, "exclude")})


def test_a_person_carries_a_unanimous_exclusion_forward_but_never_excludes_an_inclusion():
    rescues = [("validation", {1: d(1, "uncertain", reason="Might be a job shop"),
                               2: d(2, "exclude", reason="Not a job shop")})]
    rows = by_number(consensus.combine([1, 2], votes(BALLOTS), LABEL, rescues=rescues))
    assert (rows[1]["decision"], rows[1]["basis"], rows[1]["rule"]) == ("uncertain", "validation", "")
    assert (rows[2]["decision"], rows[2]["basis"]) == ("include", "vote")


def test_a_person_who_also_excludes_leaves_the_exclusion_as_voted():
    rescues = [("validation", {1: d(1, "exclude")})]
    row = consensus.combine([1], votes(BALLOTS), LABEL, rescues=rescues)[0]
    assert (row["decision"], row["basis"]) == ("exclude", "vote")


# ----------------------------------------------------------------- the full-text gate

def test_a_disagreement_that_names_no_flexible_job_shop_is_set_aside():
    rows = by_number(consensus.combine([2, 3], votes(BALLOTS), LABEL, named={2: "text"}))
    assert (rows[3]["outcome"], rows[3]["decision"], rows[3]["basis"]) == ("disagreement", "uncertain", "not named")
    assert rows[3]["gate"] == "set aside" and rows[3]["rule"] == ""
    assert rows[3]["reason"].startswith("Disagreement (screener-a include, screener-b exclude, screener-c uncertain), not resolved")
    assert (rows[2]["gate"], rows[2]["named"]) == ("full text", "text")


def test_a_named_disagreement_waits_for_the_person_and_an_unnamed_inclusion_is_coded_from_the_abstract():
    rows = by_number(consensus.combine([1, 2, 3], votes(BALLOTS), LABEL, named={3: "reasons"}))
    assert (rows[3]["decision"], rows[3]["basis"], rows[3]["gate"]) == ("", "unresolved", "")
    assert rows[2]["gate"] == "abstract only"
    assert rows[1]["gate"] == ""                                     # an exclusion passes no gate
    resolved = consensus.combine([3], votes(BALLOTS), LABEL, named={3: "reasons"},
                                 resolutions={3: d(3, "uncertain", reason="Inclusion 1: unclear")},
                                 resolved_by={3: "osamah"})[0]
    assert (resolved["decision"], resolved["basis"], resolved["gate"]) == ("uncertain", "resolution", "full text")


def test_without_the_gate_every_disagreement_goes_to_the_person():
    row = consensus.combine([3], votes(BALLOTS), LABEL)[0]
    assert (row["basis"], row["gate"], row["named"]) == ("unresolved", "", "")


# -------------------------------------------------------- disagreements settled by rule

SETTLE_BALLOTS = {
    1: [("include", ""), ("include", ""), ("exclude", "Exclusion 2: not RL")],
    2: [("include", ""), ("exclude", "Exclusion 1: a flow shop"), ("exclude", "Exclusion 1, flow shop")],
    3: [("include", ""), ("uncertain", ""), ("exclude", "Exclusion 3: a review")],
    4: [("uncertain", ""), ("exclude", "Exclusion 1"), ("exclude", "Exclusion 2")],
    5: [("include", ""), ("uncertain", ""), ("uncertain", "")],
    6: [("uncertain", ""), ("uncertain", ""), ("uncertain", "")],
}


def test_a_disagreement_is_settled_by_rule():
    rows = by_number(consensus.combine(list(SETTLE_BALLOTS), votes(SETTLE_BALLOTS), LABEL, settle=True))
    assert {n: (r["outcome"], r["decision"], r["basis"]) for n, r in rows.items()} == {
        1: ("disagreement", "include", "rule"), 2: ("disagreement", "exclude", "rule"),
        3: ("disagreement", "exclude", "rule"), 4: ("disagreement", "exclude", "rule"),
        5: ("disagreement", "uncertain", "rule"), 6: ("disagreement", "uncertain", "rule")}
    assert rows[2]["rule"] == "exclusion 1"          # both excluding reasons cite it
    assert rows[3]["rule"] == "exclusion 3"          # the one excluding reason's
    assert rows[4]["rule"] == "no majority"          # the two excluding reasons differ
    assert rows[1]["rule"] == rows[5]["rule"] == ""
    assert rows[3]["evidence"] == "quote 3"
    assert rows[5]["reason"].startswith("Disagreement (screener-a include, screener-b uncertain, screener-c "
                                        "uncertain), settled by rule: fewer than two screeners")


def test_a_record_removed_by_rule_is_carried_forward_by_the_person_and_an_inclusion_stays():
    rescues = [("validation", {1: d(1, "exclude", reason="Exclusion 2"),
                               2: d(2, "include", reason="Inclusion 1 to 3: a flexible job shop"),
                               5: d(5, "uncertain", reason="Inclusion 2: unclear")})]
    rows = by_number(consensus.combine([1, 2, 5], votes(SETTLE_BALLOTS), LABEL, rescues=rescues,
                                       settle=True))
    assert (rows[2]["decision"], rows[2]["basis"], rows[2]["rule"]) == ("include", "validation", "")
    assert "removed by rule, carried forward at validation" in rows[2]["reason"]
    assert (rows[5]["decision"], rows[5]["basis"]) == ("uncertain", "validation")
    assert (rows[1]["decision"], rows[1]["basis"]) == ("include", "rule")


def test_a_persons_resolution_still_decides_a_disagreement_under_the_rule():
    row = consensus.combine([2], votes(SETTLE_BALLOTS), LABEL, settle=True,
                            resolutions={2: d(2, "include", reason="Inclusion 1 to 3: it is")},
                            resolved_by={2: "moayad"})[0]
    assert (row["decision"], row["basis"]) == ("include", "resolution")


def test_this_reviews_runner_settles_disagreements_and_writes_no_sheet_for_a_person(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, first_round=False, votes=setup.VOTES_COMPLETE)
    setup.run(consensus, config, monkeypatch)
    results = os.path.join(tmp_path, "results", "screening", "consensus")
    rows = {int(r["number"]): r for r in setup.read_csv(os.path.join(data, "screening.csv"))}
    # Record 6 (include, exclude, uncertain): one include and an exclusion, so it is removed.
    assert (rows[6]["decision"], rows[6]["basis"], rows[6]["rule"]) == ("exclude", "rule", "exclusion 3")
    assert (rows[5]["decision"], rows[5]["basis"]) == ("include", "vote")
    assert not any(os.path.exists(os.path.join(results, "screening-disagreements.%s" % ext))
                   for ext in ("md", "csv", "html"))
    report = open(os.path.join(results, "screening-consensus.md"), encoding="utf-8").read()
    assert "settled by rule" in report and "| rule | 0 | 0 | 1 | 0 |" in report


def test_a_resolution_for_a_disagreement_off_the_sheet_is_refused():
    with pytest.raises(SystemExit, match="disagreements only"):
        consensus.combine([3], votes(BALLOTS), LABEL, named={},
                          resolutions={3: d(3, "include", reason="A job shop")},
                          resolved_by={3: "osamah"})


def test_a_rescued_exclusion_passes_the_gate_like_any_record():
    rescues = [("spot check", {1: d(1, "include", reason="Inclusion 1 to 3 hold")})]
    named = consensus.combine([1], votes(BALLOTS), LABEL, rescues=rescues, named={1: "text"})[0]
    unnamed = consensus.combine([1], votes(BALLOTS), LABEL, rescues=rescues, named={})[0]
    assert (named["decision"], named["basis"], named["gate"]) == ("include", "spot check", "full text")
    assert unnamed["gate"] == "abstract only"


def test_records_named_by_their_text_or_by_a_screeners_reason():
    cfg = setup.first_round(consensus.load_config(os.path.join(REPO, "configs", "screening.toml")))
    records = [corpus.Record.from_flat({"number": 1, "title": "Deep RL for the FJSP"}),
               corpus.Record.from_flat({"number": 2, "title": "Learning to schedule a plant"}),
               corpus.Record.from_flat({"number": 3, "title": "Learning to schedule a line"}),
               corpus.Record.from_flat({"number": 4, "title": "A plant", "abstract": "Routing flexibility of jobs."})]
    v = votes({2: [("uncertain", "Unclear whether a flexible job shop."), ("uncertain", ""), ("uncertain", "")],
               3: [("uncertain", "A flow line."), ("uncertain", ""), ("uncertain", "")]})
    assert consensus.named_records(cfg, records, v) == {1: "text", 2: "reasons", 4: "text"}
    cfg["gate"]["reasons"] = False
    assert consensus.named_records(cfg, records, v) == {1: "text", 4: "text"}
    del cfg["gate"]
    assert consensus.named_records(cfg, records, v) is None


def test_the_gate_end_to_end(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, extra=True)
    setup.run(consensus, config, monkeypatch)
    folder = os.path.join(tmp_path, "results", "screening", "fulltext")

    # Sought at full text: the inclusions naming it (1 and 10); 6 waits for the person.
    full = setup.read_csv(os.path.join(folder, "fulltext-list.csv"))
    assert [int(r["number"]) for r in full] == [1, 10]
    assert list(full[0]) == consensus.FULLTEXT_FIELDS and full[0]["named"] == "text"
    assert [int(r["number"]) for r in setup.read_csv(os.path.join(folder, "abstract-only.csv"))] == [5]
    assert "2 records" in open(os.path.join(folder, "fulltext-list.md"), encoding="utf-8").read()

    # Record 12 split the screeners and names none: uncertain, set aside, not on the sheet.
    rows = {int(r["number"]): r for r in setup.read_csv(os.path.join(data, "screening.csv"))}
    assert (rows[12]["decision"], rows[12]["basis"], rows[12]["gate"]) == ("uncertain", "not named", "set aside")
    assert rows[13]["gate"] == "" and rows[5]["gate"] == "abstract only"
    results = os.path.join(tmp_path, "results", "screening", "consensus")
    sheet = setup.read_csv(os.path.join(results, "screening-disagreements.csv"))
    assert [int(r["number"]) for r in sheet] == [6]                  # named by a reason
    listing = open(os.path.join(results, "screening-disagreements.md"), encoding="utf-8").read()
    assert "1 further disagreements name none" in listing and "[12]" not in listing
    votes_file = {int(r["number"]): r for r in setup.read_csv(os.path.join(results, "screening-votes.csv"))}
    assert (votes_file[6]["named"], votes_file[13]["named"], votes_file[12]["named"]) == ("reasons", "text", "")

    report = open(os.path.join(results, "screening-consensus.md"), encoding="utf-8").read()
    assert "## Full-text gate" in report
    assert "| disagreement | 2 | 0 | 1 | 1 |" in report             # 6 by a reason, 12 not named
    assert "| not named | 0 | 1 | 0 | 0 |" in report
    assert "| total | 2 | 1 | 1 |" in report                          # sought, abstract, set aside

    # The flow counts split what is carried forward by the gate.
    path = os.path.join(data, "screening.csv")
    records = corpus.load_references(os.path.join(data, "references.json"))
    counts, unscreened = make_tables.flow_counts(records, corpus.load_screening(path), {8},
                                                 make_tables.load_gates(path))
    counts = dict(counts)
    assert counts["Studies carried forward (included plus uncertain)"] == 4
    assert counts["Naming the flexible job shop: full text sought"] == 2
    assert counts["Included, not naming it: coded from title and abstract"] == 1
    assert counts["Uncertain, not naming it: set aside"] == 1
    assert sorted(r.number for r in unscreened) == [6, 9]


def test_the_disagreements_page_carries_the_models_answers_and_a_link(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, extra=True)
    setup.run(consensus, config, monkeypatch)
    folder = os.path.join(tmp_path, "results", "screening", "consensus")
    page = setup.page_data(os.path.join(folder, "screening-disagreements.html"))
    sheet = setup.read_csv(os.path.join(folder, "screening-disagreements.csv"))
    assert page["kind"] == "disagreements"
    assert page["columns"] == list(sheet[0])                         # exports the sheet's columns
    assert page["save_as"].endswith("datasets/screening-resolutions.csv")
    assert [r["number"] for r in page["records"]] == [6]             # 12 is set aside, not here
    r = page["records"][0]
    assert [m["name"] for m in r["models"]] == setup.MODELS
    assert r["models"][0]["reason"] == "Maybe a flexible job shop."
    assert r["cells"] == {"screener-a_decision": "include", "screener-b_decision": "exclude",
                          "screener-c_decision": "uncertain"}
    assert r["link"] == "https://openalex.org/W6"                    # no DOI in the fixture
    assert "answer" not in r

    # A saved resolution comes back as the page's answer.
    sheet[0].update(decision="exclude", confidence="medium",
                    reason="Exclusion 3: no results reported.", decided_by="osamah")
    setup.write_csv(os.path.join(data, "screening-resolutions.csv"), list(sheet[0]), sheet)
    setup.run(consensus, config, monkeypatch)
    again = setup.page_data(os.path.join(folder, "screening-disagreements.html"))
    assert again["records"][0]["answer"]["decided_by"] == "osamah"


def test_flow_counts_without_a_gate_column_have_no_gate_rows(tmp_path):
    path = tmp_path / "screening.csv"
    setup.write_csv(str(path), ["number", "decision"], [{"number": 1, "decision": "include"}])
    assert make_tables.load_gates(str(path)) is None
    records = [corpus.Record.from_flat({"number": 1, "title": "x"})]
    rows, _ = make_tables.flow_counts(records, corpus.load_screening(str(path)))
    assert not any(stage.startswith("Naming the flexible") for stage, _ in rows)
    # Without a gate, uncertain records stop at screening: no row carries them forward.
    assert not any(stage.startswith("Studies carried forward") for stage, _ in rows)


def test_an_empty_gate_column_is_no_gate(tmp_path):
    # A screening run with no [gate] still writes the column, with every gate empty.
    path = tmp_path / "screening.csv"
    setup.write_csv(str(path), ["number", "decision", "gate"],
                    [{"number": 1, "decision": "include", "gate": ""},
                     {"number": 2, "decision": "exclude", "gate": ""}])
    assert make_tables.load_gates(str(path)) is None


def test_flow_counts_count_records_dropped_before_screening():
    records = [corpus.Record.from_flat({"number": n, "title": "x"}) for n in range(1, 7)]
    screening = {n: corpus.Decision(n, "exclude", "high", "r", "q") for n in (1, 3, 5)}
    rows, unscreened = make_tables.flow_counts(records, screening, {2}, None, {2, 4})
    counts = dict(rows)
    assert [stage for stage, _ in rows][:4] == [
        "Identified, databases and registers", "Duplicates removed",
        "Removed for other reasons", "Screened on title and abstract"]
    assert counts["Duplicates removed"] == 1                 # 2 is in both lists: a duplicate
    assert counts["Removed for other reasons"] == 1          # 4
    assert counts["Screened on title and abstract"] == 4     # 1, 3, 5, 6
    assert [r.number for r in unscreened] == [6]
    rows, _ = make_tables.flow_counts(records, screening, {2})
    assert "Removed for other reasons" not in dict(rows)


def test_records_dropped_before_screening_are_not_screened(tmp_path):
    config, data = setup.build(tmp_path, dropped=[6])
    cfg = consensus.load_config(config)
    records, screen = consensus.load_corpus(cfg)
    assert len(records) == 11
    assert [r.number for r in screen] == [1, 2, 3, 4, 5, 7, 9, 10, 11]   # less 8 and 6
    # The list must exist once the config names it, and name records of the corpus; a file
    # Excel saved with a byte-order mark is read through.
    os.remove(os.path.join(data, "dropped.csv"))
    with pytest.raises(SystemExit, match="dropped before screening"):
        consensus.load_corpus(cfg)
    setup.write_csv(os.path.join(data, "dropped.csv"), ["number"], [{"number": 99}])
    with pytest.raises(SystemExit, match="names records not in the corpus: 99"):
        consensus.load_corpus(cfg)


def test_pairwise_agreement():
    pairs = consensus.pairwise(votes(BALLOTS), [1, 2, 3, 4], "linear")
    first_pair = pairs[0]
    assert first_pair[:4] == ("screener-a", "screener-b", 4, 3)   # disagree only on record 3


def test_fewer_than_three_screeners_is_refused():
    with pytest.raises(SystemExit, match="three"):
        consensus.load_models({"screeners": {"a": "x.csv", "b": "y.csv"}})


# ---------------------------------------------------------------------------- end to end

def test_runner_end_to_end_with_a_resolution_round_trip(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path)
    setup.run(consensus, config, monkeypatch)
    results = os.path.join(tmp_path, "results", "screening", "consensus")

    rows = {int(r["number"]): r for r in setup.read_csv(os.path.join(data, "screening.csv"))}
    assert sorted(rows) == [1, 2, 3, 4, 5, 7, 10, 11]  # 6 unresolved, 9 incomplete, 8 a duplicate
    assert rows[2]["rule"] == "exclusion 6"
    assert rows[3]["rule"] == "exclusion 1"            # two of three name it
    assert rows[4]["rule"] == "exclusion 7"            # one by the alias
    assert rows[7]["rule"] == "none named"
    assert rows[11]["rule"] == "exclusion 6"           # rule 1 twice, rule 6 once: 6 for the record
    assert rows[5]["decision"] == "include"
    assert set(rows[1]) >= {"number", "decision", "confidence", "reason", "evidence",
                            "title", "venue", "year", "work_type", "rule", "basis"}

    report = open(os.path.join(results, "screening-consensus.md"), encoding="utf-8").read()
    assert "| exclusion 6 | 2 |" in report and "| exclusion 7 | 1 |" in report
    assert "| screener-a | 5 | 0 | 5 | 0 | 1 |" in report      # includes 1 5 6 9 10; excludes 2 3 4 7 11; 8 outside
    assert "| screener-c | 3 | 1 | 5 | 1 | 0 |" in report    # nothing for 9

    # The disagreements sheet, filled and saved as the resolutions file, is read back.
    sheet = setup.read_csv(os.path.join(results, "screening-disagreements.csv"))
    assert [int(r["number"]) for r in sheet] == [6] and sheet[0]["decision"] == ""
    assert sheet[0]["screener-a_decision"] == "include"
    sheet[0].update(decision="exclude", confidence="medium",
                    reason="Exclusion 3: no results reported.", decided_by="osamah")
    setup.write_csv(os.path.join(data, "screening-resolutions.csv"), list(sheet[0]), sheet)
    setup.run(consensus, config, monkeypatch)
    rows = {int(r["number"]): r for r in setup.read_csv(os.path.join(data, "screening.csv"))}
    assert (rows[6]["decision"], rows[6]["basis"], rows[6]["rule"]) == ("exclude", "resolution", "exclusion 3")
    again = setup.read_csv(os.path.join(results, "screening-disagreements.csv"))
    assert again[0]["decided_by"] == "osamah"          # re-issued with the decision kept

    # The flow counts: record 9 has no decision and is reported, not folded in.
    records = corpus.load_references(os.path.join(data, "references.json"))
    counts, unscreened = make_tables.flow_counts(
        records, corpus.load_screening(os.path.join(data, "screening.csv")), {8})
    counts = dict(counts)
    assert counts["Duplicates removed"] == 1
    assert counts["Screened on title and abstract"] == 10
    assert counts["Excluded at screening"] == 6
    assert [r.number for r in unscreened] == [9]


def test_a_resolution_without_who_decided_is_refused(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path)
    setup.write_csv(os.path.join(data, "screening-resolutions.csv"),
                    ["number", "decision", "reason", "decided_by"],
                    [{"number": 6, "decision": "include", "reason": "A job shop.", "decided_by": ""}])
    with pytest.raises(SystemExit, match="decided_by"):
        setup.run(consensus, config, monkeypatch)


def test_no_model_files_means_no_consensus(tmp_path, monkeypatch):
    config, _ = setup.build(tmp_path, write_models=False)
    with pytest.raises(SystemExit, match="No consensus yet"):
        setup.run(consensus, config, monkeypatch)


def test_an_override_moves_paths_and_keeps_every_setting(tmp_path):
    over = tmp_path / "blind.toml"
    over.write_text('[screeners]\nqwen38 = "elsewhere/qwen38.csv"\n\n'
                    '[outputs]\nconsensus = "elsewhere/screening.csv"\n', encoding="utf-8")
    cfg = consensus.load_config(os.path.join(REPO, "configs", "screening.toml"), str(over))
    assert cfg["screeners"] == {"qwen38": "elsewhere/qwen38.csv",
                                "gemma26": "datasets/screening-gemma26.csv",
                                "glimmer30": "datasets/screening-glimmer30.csv"}
    assert cfg["outputs"]["consensus"] == "elsewhere/screening.csv"
    assert cfg["outputs"]["votes"] == "results/screening/consensus/screening-votes.csv"
    assert cfg["validation"]["seed"] == 20261012 and cfg["validation"]["quota_exclude"] == 60


def test_rule_6_takes_precedence_over_rule_1_across_the_three_reasons():
    ballots = {1: [("exclude", "Exclusion 1: no job shop"), ("exclude", "Exclusion 1"),
                   ("exclude", "Exclusion 6: a flow shop")],
               2: [("exclude", "Exclusion 1"), ("exclude", "Exclusion 6"), ("exclude", "Exclusion 7")]}
    by_reason = by_number(consensus.combine([1, 2], votes(ballots), LABEL))
    assert by_reason[1]["rule"] == "exclusion 1" and by_reason[2]["rule"] == "no majority"
    by_record = by_number(consensus.combine([1, 2], votes(ballots), LABEL, prefer=[(6, 1)]))
    assert by_record[1]["rule"] == "exclusion 6" and by_record[2]["rule"] == "exclusion 6"
    assert by_record[1]["labels"] == ["exclusion 1", "exclusion 1", "exclusion 6"]   # as cited


def test_the_persons_last_calibration_round_carries_an_exclusion_forward(tmp_path):
    config, data = setup.build(tmp_path, calibrate=False)
    cfg = consensus.load_config(config)
    assert consensus.calibration_rescue(cfg) == {}
    for rnd, decision in ((1, "exclude"), (2, "uncertain")):
        setup.write_csv(os.path.join(data, "calibration", "round-%d" % rnd, "osamah.csv"),
                        setup.FIELDS, setup.decision_rows([(2, decision, "low", "r")]))
    rescue = consensus.calibration_rescue(cfg)
    assert rescue[2].decision == "uncertain"                       # the newest round
    row = consensus.combine([2], votes({2: BALLOTS[1]}), LABEL, rescues=[("calibration", rescue)])[0]
    assert (row["decision"], row["basis"]) == ("uncertain", "calibration")


def test_unsaved_decisions_on_the_disagreements_sheet_stop_the_run(tmp_path, monkeypatch):
    config, _ = setup.build(tmp_path)
    setup.run(consensus, config, monkeypatch)
    path = os.path.join(tmp_path, "results", "screening", "consensus", "screening-disagreements.csv")
    sheet = setup.read_csv(path)
    sheet[0].update(decision="include", reason="A job shop.", decided_by="osamah")
    setup.write_csv(path, list(sheet[0]), sheet)
    with pytest.raises(SystemExit, match="was edited and differs from .* on records 6"):
        setup.run(consensus, config, monkeypatch)
    assert setup.read_csv(path)[0]["decision"] == "include"       # the typed work is kept


def test_no_consensus_before_calibration_is_complete(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, calibrate=False)
    with pytest.raises(SystemExit, match="No calibration round yet"):
        setup.run(consensus, config, monkeypatch)
    setup.write_csv(os.path.join(data, "calibration", "round-1", "osamah.csv"), setup.FIELDS,
                    setup.decision_rows([(n, "include", "high", "x") for n in setup.BATCH_01]))
    with pytest.raises(SystemExit, match="round 1 is not complete"):
        setup.run(consensus, config, monkeypatch)
    assert not os.path.exists(os.path.join(tmp_path, "results", "screening", "consensus", "screening-disagreements.csv"))


def test_model_answers_that_differ_from_the_taken_round_are_refused(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path)
    path = os.path.join(data, "calibration", "round-1", "screener-a.csv")
    rows = setup.read_csv(path)
    rows[0]["reason"] = "Changed after the round was taken."
    setup.write_csv(path, list(rows[0]), rows)
    with pytest.raises(SystemExit, match="screener-a's batch 01 decisions differ"):
        setup.run(consensus, config, monkeypatch)


def test_a_validation_file_changed_after_its_lock_is_refused(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path)
    path = os.path.join(data, "screening-validation.csv")
    setup.write_csv(path, setup.FIELDS, setup.decision_rows([(4, "exclude", "high", "r")]))
    cfg = consensus.load_config(config)
    sc.write_lock(consensus.resolve(cfg["outputs"]["validation_lock"]), "validation",
                  sc.read_decisions(path)[0])
    setup.write_csv(path, setup.FIELDS, setup.decision_rows([(4, "include", "high", "r")]))
    with pytest.raises(SystemExit, match="has changed since it was locked"):
        setup.run(consensus, config, monkeypatch)
