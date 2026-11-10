"""Tests for the validation runner: the escape clause's reach, the strata, the blind
sample, the statistics, and the escape list."""

import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import corpus  # noqa: E402
from src import screening as sc  # noqa: E402
import screening_consensus as consensus  # noqa: E402
import screening_validation as validation  # noqa: E402
import screening_setup as setup  # noqa: E402


def d(n, decision):
    return corpus.Decision(n, decision, "high", "r", "q")


def rec(n, title, abstract=""):
    return corpus.Record.from_flat({"number": n, "title": title, "abstract": abstract})


def test_escape_terms_match_whole_words_after_normalisation():
    groups = [("problem facet: shop", ["flow shop scheduling", "shop scheduling"]),
              ("word: production", ["production"]), ("word: factory", ["factory"])]
    records = [rec(1, "Flow-shop scheduling by RL"), rec(2, "Flowshop scheduling"),
               rec(3, "", "Production lines"), rec(4, "Productions and factories"),
               rec(5, "A smart factory")]
    hits, any_hit = validation.escape_hits(records, groups)
    assert hits["problem facet: shop"] == {1}           # "flowshop" is not "shop scheduling"
    assert hits["word: production"] == {3}              # "productions" is another word
    assert hits["word: factory"] == {5}
    assert any_hit == {1, 3, 5}


def test_escape_groups_are_the_clauses_terms():
    cfg = consensus.load_config(os.path.join(REPO, "configs", "screening.toml"))
    assert validation.escape_groups(cfg) == [] and validation.compare_sets([], cfg) == []
    groups = dict(validation.escape_groups(setup.first_round(cfg)))
    assert list(groups) == ["job shop", "jobshop", "fjsp", "jssp", "fjssp", "dfjsp", "factory", "workshop"]
    assert groups["factory"] == ["factory"]


def test_vote_strata_take_the_votes_inclusions_not_only_the_unanimous_ones():
    votes = {"a": {1: d(1, "exclude"), 2: d(2, "include"), 3: d(3, "include"), 4: d(4, "include"), 5: d(5, "include")},
             "b": {1: d(1, "exclude"), 2: d(2, "include"), 3: d(3, "uncertain"), 4: d(4, "exclude"), 5: d(5, "include")},
             "c": {1: d(1, "exclude"), 2: d(2, "include"), 3: d(3, "include"), 4: d(4, "include")}}
    # 3: two include, one uncertain, so the vote includes it; 4: one excludes, a disagreement;
    # 5: a vote is missing.
    assert validation.by_vote([1, 2, 3, 4, 5], votes) == {"exclude": [1], "include": [2, 3]}
    assert validation.unanimous([1, 2, 3, 4, 5], votes) == {"exclude": [1], "include": [2]}


def test_this_reviews_sample_is_drawn_from_the_vote_in_proportion(tmp_path, monkeypatch):
    config, _ = setup.build(tmp_path, first_round=False, size=3, votes=setup.VOTES_COMPLETE)
    cfg = consensus.load_config(config)
    assert cfg["validation"]["strata"] == "vote" and "escape" not in cfg
    setup.run(validation, config, monkeypatch)
    text = report(tmp_path)
    # The strata, outside batch 01: exclusions 4, 7, 11; inclusions 5, 9, 10. Three records,
    # split in proportion (3 to 3): two exclusions and one inclusion, the tie to the first.
    assert "| the vote excludes | 3 | 2 | 2 |" in text and "| the vote includes | 3 | 1 | 1 |" in text
    assert "3 records are split between the strata in proportion" in text
    assert "(2 exclusions, 1 inclusions)" in text
    assert "escape" not in text.lower()
    seed = cfg["validation"]["seed"]
    drawn = sc.stratified_sample({"exclude": setup.FRAME_EXCLUDE, "include": setup.VOTE_INCLUDE},
                                 {"exclude": 2, "include": 1}, seed)
    sheet = setup.read_csv(os.path.join(tmp_path, "data", "screening", "validation", "validation-sample.csv"))
    assert [int(r["number"]) for r in sheet] == sc.blind_order(drawn["exclude"] + drawn["include"], seed)


def test_the_abstracts_withheld_the_sample_is_drawn_and_no_sheet_written(tmp_path, monkeypatch):
    # As in a clone: the records' abstracts are withheld and their authors' copy absent. The
    # sample is drawn and reported; its sheet, which shows the abstracts, is not written.
    config, _ = setup.build(tmp_path, first_round=False, quota_exclude=2, quota_include=1,
                            votes=setup.VOTES_COMPLETE)
    setup.without_abstracts(tmp_path, monkeypatch)
    setup.run(validation, config, monkeypatch)
    text = report(tmp_path)
    assert "| removed without a person | 4 | 2 | 2 |" in text
    assert ("The sample, in a seeded order that mixes the strata and without the votes, is "
            "withheld, since it shows the abstracts.") in text
    assert not os.path.exists(os.path.join(tmp_path, "data"))


def test_decision_strata_take_every_record_decided_without_a_person():
    votes = {"a": {1: d(1, "exclude"), 2: d(2, "include"), 3: d(3, "include"), 4: d(4, "include"),
                   5: d(5, "include"), 6: d(6, "uncertain"), 7: d(7, "include")},
             "b": {1: d(1, "exclude"), 2: d(2, "include"), 3: d(3, "uncertain"), 4: d(4, "exclude"),
                   5: d(5, "exclude"), 6: d(6, "uncertain"), 7: d(7, "include")},
             "c": {1: d(1, "exclude"), 2: d(2, "include"), 3: d(3, "include"), 4: d(4, "include"),
                   5: d(5, "exclude"), 6: d(6, "uncertain")}}
    # 3: the vote includes it; 4: two include and one excludes, so the rule includes it; 5: one
    # include, so the rule removes it; 6: all uncertain, removed as uncertain; 7: a vote missing.
    assert validation.by_decision([1, 2, 3, 4, 5, 6, 7], votes) == {
        "exclude": [1, 5, 6], "include": [2, 3, 4]}


def test_this_reviews_sample_is_drawn_from_every_record_decided_without_a_person(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, first_round=False, quota_exclude=2, quota_include=1,
                               votes=setup.VOTES_COMPLETE)
    cfg = consensus.load_config(config)
    v = cfg["validation"]
    assert v["strata"] == "decision" and "size" not in v and "escape" not in cfg
    setup.run(validation, config, monkeypatch)
    text = report(tmp_path)
    # Outside batch 01: removed 4, 7 and 11 by the vote and 6 by the rule (one include, one
    # exclusion); included 5, 9 and 10.
    assert "| removed without a person | 4 | 2 | 2 |" in text
    assert "| included without a person | 3 | 1 | 1 |" in text
    seed = v["seed"]
    drawn = sc.stratified_sample({"exclude": [4, 6, 7, 11], "include": setup.VOTE_INCLUDE},
                                 {"exclude": 2, "include": 1}, seed)
    sample = drawn["exclude"] + drawn["include"]
    sheet = setup.read_csv(os.path.join(tmp_path, "data", "screening", "validation", "validation-sample.csv"))
    assert [int(r["number"]) for r in sheet] == sc.blind_order(sample, seed)

    # The person keeps one removed record and excludes the included one.
    kept = drawn["exclude"][0]
    rows = [{"number": n, "title": "", "decision": "include" if n == kept else "exclude",
             "confidence": "high", "reason": "r", "evidence": "q"} for n in sample]
    setup.write_csv(os.path.join(data, "screening-validation.csv"), sc.SHEET_FIELDS, rows)
    setup.run(validation, config, monkeypatch)
    text = report(tmp_path)
    assert "## Wrong removals" in text and "| person includes | 1 of 2 |" in text
    assert "## Wrong inclusions" in text and "| person excludes | 1 of 1 |" in text
    assert "Wrong unanimous exclusions" not in text

    # The consensus carries the kept record forward, and leaves the included one as decided.
    setup.run(consensus, config, monkeypatch)
    screened = {int(r["number"]): r for r in setup.read_csv(os.path.join(data, "screening.csv"))}
    assert (screened[kept]["decision"], screened[kept]["basis"]) == ("include", "validation")
    assert screened[drawn["include"][0]]["decision"] == "include"


def person_row(n, decision):
    return {"number": n, "title": "", "decision": decision, "confidence": "high",
            "reason": "r", "evidence": "q"}


def decided(data):
    """{number: (decision, basis)} of the consensus."""
    return {int(r["number"]): (r["decision"], r["basis"])
            for r in setup.read_csv(os.path.join(data, "screening.csv"))}


def screened_sample(tmp_path, monkeypatch):
    """This review's settings with the sample screened: the person keeps both sampled
    removed records and excludes the sampled included one, so all three are disagreements.
    Returns (config, data, the two kept, the included one, the seed)."""
    config, data = setup.build(tmp_path, first_round=False, quota_exclude=2, quota_include=1,
                               votes=setup.VOTES_COMPLETE)
    seed = consensus.load_config(config)["validation"]["seed"]
    drawn = sc.stratified_sample({"exclude": [4, 6, 7, 11], "include": setup.VOTE_INCLUDE},
                                 {"exclude": 2, "include": 1}, seed)
    included = drawn["include"][0]
    setup.write_csv(os.path.join(data, "screening-validation.csv"), sc.SHEET_FIELDS,
                    [person_row(n, "include") for n in drawn["exclude"]]
                    + [person_row(included, "exclude")])
    setup.run(validation, config, monkeypatch)
    return config, data, list(drawn["exclude"]), included, seed


def test_the_disagreements_go_to_a_second_person_whose_decision_settles_them(tmp_path, monkeypatch):
    config, data, (first, second), included, seed = screened_sample(tmp_path, monkeypatch)
    folder = os.path.join(tmp_path, "data", "screening", "validation")
    sheet = setup.read_csv(os.path.join(folder, "adjudication-sheet.csv"))
    # The sheet lists the three disagreements in a seeded order, and no earlier decision.
    assert [int(r["number"]) for r in sheet] == sc.blind_order(
        sorted([first, second, included]), "%s:adjudication" % seed)
    assert not any(r["decision"] for r in sheet)
    assert os.path.isfile(os.path.join(folder, "adjudication-sheet.html"))
    assert "0 of 3 decided" in report(tmp_path)

    # Half done: nothing changes, and the first person's decision still carries the records.
    adjudication = os.path.join(data, "screening-adjudication.csv")
    setup.write_csv(adjudication, sc.SHEET_FIELDS, [person_row(first, "exclude")])
    setup.run(validation, config, monkeypatch)
    assert "1 of 3 decided" in report(tmp_path)
    setup.run(consensus, config, monkeypatch)
    assert decided(data)[first] == ("include", "validation")

    # Done: the second person excludes one kept record, keeps the other, and includes the
    # included record the first person excluded.
    setup.write_csv(adjudication, sc.SHEET_FIELDS,
                    [person_row(first, "exclude"), person_row(second, "include"),
                     person_row(included, "include")])
    setup.run(validation, config, monkeypatch)
    text = report(tmp_path)
    assert "| removed without a person | 2 | 1 | 0 | 1 |" in text
    assert "| included without a person | 1 | 1 | 0 | 0 |" in text
    assert "| removed; included after adjudication | 1 of 2 |" in text
    assert "| included; excluded after adjudication | 0 of 1 |" in text
    assert "| person includes | 2 of 2 |" in text          # the first person's reading stays
    setup.run(consensus, config, monkeypatch)
    after = decided(data)
    assert after[first][0] == "exclude" and after[first][1] != "validation"
    assert after[second] == ("include", "adjudication")
    assert after[included][0] == "include"


def test_an_adjudication_off_the_sheet_or_changed_after_its_lock_is_refused(tmp_path, monkeypatch):
    config, data, (first, second), included, _ = screened_sample(tmp_path, monkeypatch)
    adjudication = os.path.join(data, "screening-adjudication.csv")
    outside = next(n for n in (4, 6, 7, 11) if n not in (first, second))
    setup.write_csv(adjudication, sc.SHEET_FIELDS, [person_row(outside, "include")])
    with pytest.raises(SystemExit, match="not disagreements"):
        setup.run(validation, config, monkeypatch)
    rows = [person_row(first, "exclude"), person_row(second, "include"),
            person_row(included, "include")]
    setup.write_csv(adjudication, sc.SHEET_FIELDS, rows)
    setup.run(validation, config, monkeypatch)
    rows[0] = person_row(first, "include")
    setup.write_csv(adjudication, sc.SHEET_FIELDS, rows)
    with pytest.raises(SystemExit, match="changed since it was locked"):
        setup.run(validation, config, monkeypatch)
    with pytest.raises(SystemExit, match="changed since it was locked"):
        setup.run(consensus, config, monkeypatch)


def test_unanimous_strata_need_every_vote():
    votes = {"a": {1: d(1, "exclude"), 2: d(2, "include"), 3: d(3, "include"), 4: d(4, "uncertain")},
             "b": {1: d(1, "exclude"), 2: d(2, "include"), 3: d(3, "uncertain"), 4: d(4, "uncertain")},
             "c": {1: d(1, "exclude"), 2: d(2, "include"), 4: d(4, "uncertain")}}
    assert validation.unanimous([1, 2, 3, 4, 5], votes) == {"exclude": [1], "include": [2]}


def test_analyse_counts_both_readings_and_the_trigger():
    drawn = {"exclude": [1, 2, 3, 4], "include": [5, 6]}
    person = {1: d(1, "exclude"), 2: d(2, "include"), 3: d(3, "uncertain"), 4: d(4, "exclude"),
              5: d(5, "include"), 6: d(6, "exclude")}
    stats = validation.analyse(drawn, person, ["include", "uncertain"], 0.95, "linear")
    assert stats["per"]["exclude"]["agree"] == 2 and stats["per"]["include"]["agree"] == 1
    assert stats["strict"][0] == 1 and stats["broad"][0] == 2
    assert stats["strict"][1] == pytest.approx(sc.upper_bound(1, 4, 0.95))
    assert stats["triggered"] and stats["wrong_exclusions"] == [2, 3]
    pairs = [("exclude", "exclude"), ("exclude", "include"), ("exclude", "uncertain"),
             ("exclude", "exclude"), ("include", "include"), ("include", "exclude")]
    assert stats["kappa"] == pytest.approx(sc.weighted_kappa(pairs, "linear"))
    literal = validation.analyse(drawn, person, ["include"], 0.95, "linear")
    assert literal["configured"] == 1 and literal["wrong_exclusions"] == [2]
    # A sampled inclusion the person excludes: record 6, one of two.
    assert stats["wrong_inclusion"][0] == 1
    assert stats["wrong_inclusion"][1] == pytest.approx(sc.upper_bound(1, 2, 0.95))


def test_nothing_wrong_does_not_trigger():
    drawn = {"exclude": [1, 2], "include": [3]}
    person = {1: d(1, "exclude"), 2: d(2, "exclude"), 3: d(3, "uncertain")}
    stats = validation.analyse(drawn, person, ["include", "uncertain"], 0.95, "linear")
    assert not stats["triggered"] and stats["strict"] == (0, sc.upper_bound(0, 2, 0.95))


# ---------------------------------------------------------------------------- spot check

def test_spot_flags_name_the_flexible_job_shop_or_vehicles_in_a_job_shop():
    cfg = setup.first_round(consensus.load_config(os.path.join(REPO, "configs", "screening.toml")))
    assert validation.spot_flags(cfg, [rec(1, "Deep RL for the FJSP")], {1: "text"}) == {}   # withdrawn
    cfg["spot_check"]["enabled"] = True
    records = [rec(1, "Deep RL for the FJSP"), rec(2, "AGV scheduling in a job shop"),
               rec(3, "Material handling", "Robots move parts in a factory."),
               rec(4, "Guided vehicles in the flexible job shop"), rec(5, "A plant")]
    flags = validation.spot_flags(cfg, records, {1: "text", 4: "text", 5: "reasons"})
    assert flags[1] == [validation.SPOT_REASONS[0]]
    assert flags[2] == [validation.SPOT_REASONS[2]]
    assert 3 not in flags                                  # material handling, but no job shop
    assert flags[4] == [validation.SPOT_REASONS[0], validation.SPOT_REASONS[2]]
    assert flags[5] == [validation.SPOT_REASONS[1]]
    del cfg["spot_check"]
    assert validation.spot_flags(cfg, records, {1: "text"}) == {}


def test_the_spot_check_leaves_out_what_a_person_screens_already():
    flags = {2: ["x"], 5: ["x"], 13: ["x"], 14: ["x"], 20: ["x"]}
    assert validation.spot_check_list([2, 4, 13, 14, 20], flags, sample={13}, calibration={2}) == [14, 20]


def test_the_escape_list_leaves_out_the_spot_check():
    assert validation.escape_candidates({1, 4, 10, 11, 13}, {4, 11, 13}, {11}, {1}, [13]) == [4]
    assert validation.escape_candidates({4, 13}, {4, 13}, set(), set()) == [4, 13]


def test_the_withdrawn_spot_check_lists_nothing_and_refuses_a_decision_file(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, quota_exclude=0, quota_include=1,
                               votes={**setup.VOTES_COMPLETE, **setup.EXTRA_VOTES}, extra=True)
    setup.run(validation, config, monkeypatch)
    folder = os.path.join(tmp_path, "results", "screening", "validation")
    assert not os.path.exists(os.path.join(folder, "spot-check.csv"))
    assert not os.path.exists(os.path.join(folder, "spot-check.html"))
    assert "## Spot check" not in report(tmp_path)
    setup.run(consensus, config, monkeypatch)                         # no file: runs
    setup.write_csv(os.path.join(data, "screening-spot-check.csv"), sc.SHEET_FIELDS,
                    [{"number": 13, "title": "", "decision": "include", "confidence": "",
                      "reason": "", "evidence": ""}])
    with pytest.raises(SystemExit, match="spot check is withdrawn"):
        setup.run(consensus, config, monkeypatch)


def test_the_spot_check_end_to_end(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, quota_exclude=0, quota_include=1,
                               votes={**setup.VOTES_COMPLETE, **setup.EXTRA_VOTES}, extra=True,
                               spot_check=True)
    setup.run(validation, config, monkeypatch)
    folder = os.path.join(tmp_path, "results", "screening", "validation")
    sheet = setup.read_csv(os.path.join(folder, "spot-check.csv"))
    assert [int(r["number"]) for r in sheet] == setup.SPOT_CHECK
    assert list(sheet[0]) == sc.SHEET_FIELDS and sheet[0]["decision"] == ""
    text = report(tmp_path)
    assert "## Spot check" in text and "0 of 2 decided" in text
    spot_page = setup.page_data(os.path.join(folder, "spot-check.html"))   # beside its sheet
    assert [r["number"] for r in spot_page["records"]] == setup.SPOT_CHECK
    assert spot_page["save_as"].endswith("datasets/screening-spot-check.csv")
    assert "| flexible job shop, in title or abstract | 1 |" in text
    assert "| guided vehicles or material handling in a job shop | 1 |" in text
    assert "| listed, for any reason | 2 |" in text

    # A decision for a record not on the spot check is refused.
    spot = os.path.join(data, "screening-spot-check.csv")
    setup.write_csv(spot, sc.SHEET_FIELDS, [{"number": 4, "title": "", "decision": "include",
                                             "confidence": "", "reason": "", "evidence": ""}])
    with pytest.raises(SystemExit, match="not on the spot check"):
        setup.run(validation, config, monkeypatch)

    # The person carries both forward; the consensus records them on the spot check, and the
    # gate sends 13 (naming the flexible job shop) to full text and 14 to the abstract tier.
    setup.write_csv(spot, sc.SHEET_FIELDS, [
        {"number": 13, "title": "", "decision": "uncertain", "confidence": "low",
         "reason": "Inclusion 2: the learning may be reinforcement learning.", "evidence": "q"},
        {"number": 14, "title": "", "decision": "include", "confidence": "medium",
         "reason": "Inclusion 1: the job shop's vehicles are scheduled.", "evidence": "q"}])
    setup.run(validation, config, monkeypatch)
    assert "The spot check is fully screened." in report(tmp_path)
    setup.run(consensus, config, monkeypatch)
    rows = {int(r["number"]): r for r in setup.read_csv(os.path.join(data, "screening.csv"))}
    assert (rows[13]["decision"], rows[13]["basis"], rows[13]["gate"]) == ("uncertain", "spot check", "full text")
    assert (rows[14]["decision"], rows[14]["basis"], rows[14]["gate"]) == ("include", "spot check", "abstract only")


# ---------------------------------------------------------------------------- end to end

def report(tmp_path):
    return open(os.path.join(tmp_path, "results", "screening", "validation", "screening-validation.md"), encoding="utf-8").read()


def test_before_any_vote_the_reach_of_the_escape_clause_is_reported(tmp_path, monkeypatch):
    config, _ = setup.build(tmp_path, write_models=False)
    setup.run(validation, config, monkeypatch)
    text = report(tmp_path)
    assert "No vote yet" in text
    # Records to screen are 1 to 7 and 9 to 11; four carry a term of the clause: a job shop in
    # 1, 4 and 10, a factory in 11.
    assert "| any of them | 4 of 10 (40.0%) |" in text
    assert "| job shop | 3 |" in text and "| factory | 1 |" in text
    # The term sets weighed: as first worded, the clause also reached record 2 (flow shop
    # scheduling, production); a job shop alone, 3.
    assert "| a: as first worded (the problem facet and four words) |" in text
    assert "| 5 of 10 (50.0%) |" in text
    assert "| b: a job shop in any form | job shop, jobshop, fjsp, jssp, fjssp, dfjsp | 3 of 10 (30.0%) |" in text
    assert not os.path.exists(os.path.join(tmp_path, "data", "screening", "validation", "validation-sample.csv"))


def test_no_sample_while_a_record_lacks_a_vote(tmp_path, monkeypatch):
    config, _ = setup.build(tmp_path)                       # no model decided record 9 fully
    setup.run(validation, config, monkeypatch)
    assert "1 records to screen lack a vote" in report(tmp_path)
    assert not os.path.exists(os.path.join(tmp_path, "data", "screening", "validation", "validation-sample.csv"))


def test_sample_then_statistics_then_escape_list(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, quota_exclude=2, quota_include=1, votes=setup.VOTES_COMPLETE)
    cfg = consensus.load_config(config)
    seed = cfg["validation"]["seed"]
    # Batch 01 (records 1 to 3) is left out of both strata.
    drawn = sc.stratified_sample({"exclude": setup.FRAME_EXCLUDE, "include": setup.FRAME_INCLUDE},
                                 {"exclude": 2, "include": 1}, seed)
    sample = drawn["exclude"] + drawn["include"]

    # After the vote: the sheet holds the sample in the seeded order and says nothing of strata.
    setup.run(validation, config, monkeypatch)
    sheet = setup.read_csv(os.path.join(tmp_path, "data", "screening", "validation", "validation-sample.csv"))
    assert [int(r["number"]) for r in sheet] == sc.blind_order(sample, seed)
    assert not set(setup.BATCH_01) & {int(r["number"]) for r in sheet}
    assert list(sheet[0]) == sc.SHEET_FIELDS
    # Its page: the same records in the same order, what the screeners saw and nothing more.
    page = setup.page_data(os.path.join(tmp_path, "data", "screening", "validation", "validation-sample.html"))
    assert [r["number"] for r in page["records"]] == sc.blind_order(sample, seed)
    assert page["kind"] == "screening" and page["columns"] == sc.SHEET_FIELDS
    assert not any(k in r for r in page["records"] for k in ("models", "cells", "link", "answer"))
    assert set(page["records"][0]) == {"number", "title", "venue", "year", "type", "abstract"}
    text = report(tmp_path)
    assert "0 of 3 sampled records decided" in text
    assert "Batch 01 (3 records) is left out" in text and "(2 exclusions, 1 inclusions)" in text
    assert "Wrong unanimous exclusions" not in text

    # A partly filled file: still no statistics.
    wrong = drawn["exclude"][0]
    rows = [{"number": n, "title": "",
             "decision": "include" if n == wrong or n in drawn["include"] else "exclude",
             "confidence": "high", "reason": "r", "evidence": "q"} for n in sample]
    validation_file = os.path.join(data, "screening-validation.csv")
    setup.write_csv(validation_file, sc.SHEET_FIELDS, rows[:1])
    setup.run(validation, config, monkeypatch)
    assert "1 of 3 sampled records decided" in report(tmp_path)

    # Complete: statistics, trigger, the lock, and the escape list without the records the
    # person has already screened (the sample, and batch 01).
    setup.write_csv(validation_file, sc.SHEET_FIELDS, rows)
    setup.run(validation, config, monkeypatch)
    text = report(tmp_path)
    assert "Triggered: **yes** (1 records: %d)" % wrong in text
    assert os.path.exists(os.path.join(tmp_path, "results", "screening", "validation", "validation-lock.json"))
    escape = setup.read_csv(os.path.join(tmp_path, "results", "screening", "validation", "escape-list.csv"))
    expected = sorted({4, 11} - set(drawn["exclude"]))   # unanimous exclusions carrying a term
    assert [int(r["number"]) for r in escape] == expected
    assert "0 of them decided" in text
    assert ("The escape list is fully screened." in text) == (not expected)

    # The consensus carries the wrongly excluded record forward on the person's decision.
    setup.run(consensus, config, monkeypatch)
    screened = {int(r["number"]): r for r in setup.read_csv(os.path.join(data, "screening.csv"))}
    assert (screened[wrong]["decision"], screened[wrong]["basis"]) == ("include", "validation")

    # Once complete, the person's file is frozen: an edited answer is refused.
    rows[0]["decision"] = "exclude"
    setup.write_csv(validation_file, sc.SHEET_FIELDS, rows)
    with pytest.raises(SystemExit, match="has changed since it was locked"):
        setup.run(validation, config, monkeypatch)


def test_decisions_outside_the_sample_are_refused(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, votes=setup.VOTES_COMPLETE)
    setup.write_csv(os.path.join(data, "screening-validation.csv"), sc.SHEET_FIELDS,
                    [{"number": 5, "title": "", "decision": "include", "confidence": "",
                      "reason": "", "evidence": ""}])   # 5 is not unanimous
    with pytest.raises(SystemExit, match="not in the sample"):
        setup.run(validation, config, monkeypatch)


def test_an_escape_file_without_a_trigger_is_refused(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, votes=setup.VOTES_COMPLETE)
    setup.write_csv(os.path.join(data, "screening-escape.csv"), sc.SHEET_FIELDS,
                    [{"number": 4, "title": "", "decision": "include", "confidence": "",
                      "reason": "", "evidence": ""}])
    with pytest.raises(SystemExit, match="no complete validation sample has triggered"):
        setup.run(validation, config, monkeypatch)


def test_no_lock_while_the_sheet_and_the_saved_file_differ(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, votes=setup.VOTES_COMPLETE)
    setup.run(validation, config, monkeypatch)                    # the sample is issued
    sheet_path = os.path.join(tmp_path, "data", "screening", "validation", "validation-sample.csv")
    sheet = setup.read_csv(sheet_path)
    for row in sheet:
        row.update(decision="exclude", confidence="high", reason="r", evidence="q")
    setup.write_csv(os.path.join(data, "screening-validation.csv"), sc.SHEET_FIELDS, sheet)
    sheet[0]["reason"] = "corrected on the sheet, not saved yet"
    setup.write_csv(sheet_path, sc.SHEET_FIELDS, sheet)
    with pytest.raises(SystemExit, match="was edited and differs from"):
        setup.run(validation, config, monkeypatch)
    assert not os.path.exists(os.path.join(tmp_path, "results", "screening", "validation", "validation-lock.json"))


def test_an_escape_file_is_not_judged_without_the_votes(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, write_models=False)
    setup.write_csv(os.path.join(data, "screening-escape.csv"), sc.SHEET_FIELDS,
                    [{"number": 4, "title": "", "decision": "include", "confidence": "",
                      "reason": "", "evidence": ""}])
    setup.run(validation, config, monkeypatch)
    assert "No vote yet" in report(tmp_path)


def test_no_sample_before_calibration_is_complete(tmp_path, monkeypatch):
    config, _ = setup.build(tmp_path, votes=setup.VOTES_COMPLETE, calibrate=False)
    with pytest.raises(SystemExit, match="No calibration round yet"):
        setup.run(validation, config, monkeypatch)
    assert not os.path.exists(os.path.join(tmp_path, "data", "screening", "validation", "validation-sample.csv"))
