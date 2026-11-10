"""Tests for the calibration runner: the person's blind sheet for batch 01, and the
comparison of a round once every screener's file is in place."""

import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import corpus  # noqa: E402
import screening_calibration as calibration  # noqa: E402
import screening_consensus as consensus  # noqa: E402
import screening_setup as setup  # noqa: E402

LABEL = consensus.labeller({"rules": {"inclusion_rules": 3, "exclusion_rules": 7, "prefer": []}})


def d(n, decision, reason=""):
    return corpus.Decision(n, decision, "high", reason, "q")


def test_compare_flags_different_decisions_and_different_rules():
    files = {"a": {1: d(1, "include"), 2: d(2, "exclude", "Exclusion 1"), 3: d(3, "exclude", "Exclusion 6")},
             "b": {1: d(1, "include"), 2: d(2, "exclude", "Exclusion 6"), 3: d(3, "exclude", "Exclusion 6")},
             "c": {1: d(1, "uncertain"), 2: d(2, "exclude", "Exclusion 1"), 3: d(3, "exclude", "Exclusion 6")},
             "p": {1: d(1, "include"), 2: d(2, "exclude", "Exclusion 1"), 3: d(3, "exclude", "Exclusion 6")}}
    rows, pairs = calibration.compare([1, 2, 3], files, ["a", "b", "c"], LABEL, "linear")
    assert [r["differ"] for r in rows] == [True, True, False]
    assert [r["vote"] for r in rows] == ["include", "exclude", "exclude"]
    assert len(pairs) == 6 and pairs[0][:4] == ("a", "b", 3, 3)


def write_round(data, decisions_by_screener):
    folder = os.path.join(data, "calibration", "round-1")
    for s, rows in decisions_by_screener.items():
        setup.write_csv(os.path.join(folder, "%s.csv" % s), setup.FIELDS, setup.decision_rows(rows))


def test_sheet_first_then_the_round(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, batch_size=3, calibrate=False)
    results = os.path.join(tmp_path, "results", "screening", "calibration")
    sheets = os.path.join(tmp_path, "data", "screening", "calibration")

    # Nothing screened: the person's sheet for batch 01 (records 1 to 3; 8 is a duplicate).
    setup.run(calibration, config, monkeypatch)
    sheet = setup.read_csv(os.path.join(sheets, "calibration-sheet.csv"))
    assert [int(r["number"]) for r in sheet] == [1, 2, 3]
    assert not os.path.exists(os.path.join(results, "calibration-round-1.md"))
    assert "datasets/calibration/round-N/osamah.csv" in open(
        os.path.join(sheets, "calibration-sheet.md"), encoding="utf-8").read()
    page = setup.page_data(os.path.join(sheets, "calibration-sheet.html"))
    assert [r["number"] for r in page["records"]] == [1, 2, 3]
    assert page["save_as"].endswith("round-N/osamah.csv")            # exported as osamah.csv

    # The person's file alone: the round waits, and nothing is compared yet.
    write_round(data, {"osamah": [(1, "include", "high", "x"), (2, "exclude", "high", "Exclusion 1"),
                                  (3, "exclude", "medium", "Exclusion 1")]})
    setup.run(calibration, config, monkeypatch)
    assert not os.path.exists(os.path.join(results, "calibration-round-1.md"))

    same = [(1, "include", "high", "Inclusion 1 to 3."), (2, "exclude", "high", "Exclusion 6"),
            (3, "exclude", "high", "Exclusion 1")]
    write_round(data, {"screener-a": same, "screener-b": same, "screener-c": same})
    setup.run(calibration, config, monkeypatch)
    text = open(os.path.join(results, "calibration-round-1.md"), encoding="utf-8").read()
    assert "1 of 3 records" in text                      # record 2: rule 6 against rule 1
    assert "| screener-a, osamah | 3 | 3 | 100.0% |" in text
    assert "| exclude | 0 | 0 | 2 |" in text             # the vote against the person

    # A second round after an amendment is compared too; the first stays.
    folder2 = os.path.join(data, "calibration", "round-2")
    for s in ("screener-a", "screener-b", "screener-c", "osamah"):
        setup.write_csv(os.path.join(folder2, "%s.csv" % s), setup.FIELDS, setup.decision_rows(same))
    setup.run(calibration, config, monkeypatch)
    text2 = open(os.path.join(results, "calibration-round-2.md"), encoding="utf-8").read()
    assert "0 of 3 records" in text2
    assert os.path.exists(os.path.join(results, "calibration-round-1.md"))


def test_the_abstracts_withheld_the_round_is_compared_and_no_sheet_written(tmp_path, monkeypatch):
    # As in a clone: the records' abstracts are withheld and their authors' copy absent. The
    # round's report is written, without the differing record's abstract; the sheet is not.
    config, data = setup.build(tmp_path, batch_size=3, calibrate=False)
    setup.without_abstracts(tmp_path, monkeypatch)
    same = [(1, "include", "high", "Inclusion 1 to 3."), (2, "exclude", "high", "Exclusion 6"),
            (3, "exclude", "high", "Exclusion 1")]
    write_round(data, {"screener-a": same, "screener-b": same, "screener-c": same,
                       "osamah": [(1, "include", "high", "x"), (2, "exclude", "high", "Exclusion 1"),
                                  (3, "exclude", "medium", "Exclusion 1")]})
    setup.run(calibration, config, monkeypatch)
    results = os.path.join(tmp_path, "results", "screening", "calibration")
    text = open(os.path.join(results, "calibration-round-1.md"), encoding="utf-8").read()
    assert "1 of 3 records" in text and "## [2]" in text and "Abstract:" not in text
    assert not os.path.exists(os.path.join(tmp_path, "data"))


def test_a_file_from_another_batch_is_refused_before_the_round_is_complete(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, batch_size=3, calibrate=False)
    write_round(data, {"screener-a": [(1, "include", "high", ""), (4, "exclude", "high", "")]})
    with pytest.raises(SystemExit, match="outside batch 01"):
        setup.run(calibration, config, monkeypatch)


def test_take_round_waits_for_the_persons_complete_file_and_copies_batch_01_only(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, batch_size=3, calibrate=False)
    folder = os.path.join(data, "calibration", "round-1")
    with pytest.raises(SystemExit, match="is not in place"):
        setup.run(calibration, config, monkeypatch, "--take-round", "1")

    # A person's file still being filled: nothing is copied into the shared round folder.
    write_round(data, {"osamah": [(1, "include", "high", "x"), (2, "exclude", "high", "Exclusion 6")]})
    with pytest.raises(SystemExit, match="must decide every record of batch 01"):
        setup.run(calibration, config, monkeypatch, "--take-round", "1")
    assert not os.path.exists(os.path.join(folder, "screener-a.csv"))

    # Complete: each model's batch 01 rows only (the models' files hold records 1 to 11).
    write_round(data, {"osamah": [(1, "include", "high", "x"), (2, "exclude", "high", "Exclusion 6"),
                                  (3, "exclude", "high", "Exclusion 1")]})
    setup.run(calibration, config, monkeypatch, "--take-round", "1")
    for m in setup.MODELS:
        assert [int(r["number"]) for r in setup.read_csv(os.path.join(folder, "%s.csv" % m))] == [1, 2, 3]
    assert os.path.exists(os.path.join(tmp_path, "results", "screening", "calibration", "calibration-round-1.md"))


def test_a_record_left_out_is_off_the_sheet_and_out_of_the_round(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, batch_size=3, calibrate=False, leave_out=(1,))
    results = os.path.join(tmp_path, "results", "screening", "calibration")
    sheets = os.path.join(tmp_path, "data", "screening", "calibration")
    setup.run(calibration, config, monkeypatch)
    sheet = setup.read_csv(os.path.join(sheets, "calibration-sheet.csv"))
    assert [int(r["number"]) for r in sheet] == [2, 3]
    # The person's file without record 1 completes the round; the models' rows for it are
    # not taken, and the round compares the two records the person screened.
    write_round(data, {"osamah": [(2, "exclude", "high", "Exclusion 6"),
                                  (3, "exclude", "high", "Exclusion 1")]})
    setup.run(calibration, config, monkeypatch, "--take-round", "1")
    folder = os.path.join(data, "calibration", "round-1")
    for m in setup.MODELS:
        assert [int(r["number"]) for r in setup.read_csv(os.path.join(folder, "%s.csv" % m))] == [2, 3]
    assert "of 2 records" in open(os.path.join(results, "calibration-round-1.md"),
                                  encoding="utf-8").read()
    # The vote may now be used: the round is complete without record 1.
    consensus.require_calibration(*_calibration_inputs(config))


def _calibration_inputs(config):
    cfg = consensus.load_config(config, None)
    _, screen_records = consensus.load_corpus(cfg)
    return cfg, screen_records, consensus.load_models(cfg)


def test_a_taken_round_keeps_its_model_answers_and_the_persons_decisions(tmp_path, monkeypatch):
    config, data = setup.build(tmp_path, batch_size=3, calibrate=False)
    person = [(1, "include", "high", "x"), (2, "exclude", "high", "Exclusion 6"),
              (3, "exclude", "high", "Exclusion 1")]
    write_round(data, {"osamah": person})
    setup.run(calibration, config, monkeypatch, "--take-round", "1")
    model_round = os.path.join(data, "calibration", "round-1", "screener-a.csv")
    taken = open(model_round, encoding="utf-8-sig").read()
    setup.run(calibration, config, monkeypatch, "--take-round", "1")    # the same answers: allowed

    # The models answer batch 01 again, and round 1 is taken by mistake: refused, unchanged.
    model_file = os.path.join(data, "screening-screener-a.csv")
    rows = setup.read_csv(model_file)
    rows[0]["decision"] = "exclude"
    setup.write_csv(model_file, list(rows[0]), rows)
    with pytest.raises(SystemExit, match="already taken"):
        setup.run(calibration, config, monkeypatch, "--take-round", "1")
    assert open(model_round, encoding="utf-8-sig").read() == taken

    # The person's decisions are frozen once the models' tables are beside them.
    write_round(data, {"osamah": [(1, "exclude", "high", "x")] + person[1:]})
    with pytest.raises(SystemExit, match="has changed since it was locked"):
        setup.run(calibration, config, monkeypatch)
