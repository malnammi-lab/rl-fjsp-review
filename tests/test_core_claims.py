"""Tests for the claims runner (runners/core_claims.py): the sheet of the claims of use beyond
simulation that step 1 of the core rule rests on, its page, and the person's confirmations
read back."""

import json
import os
import shutil
import sys
import tomllib

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import mapcodes as mc  # noqa: E402
from src import screening as sc  # noqa: E402
import core_claims  # noqa: E402
from screening_setup import page_data, read_csv, sheets, without_abstracts, write_csv  # noqa: E402
from test_map_vote import BASE, MODELS  # noqa: E402

AXES = mc.load_axes(os.path.join(REPO, "configs", "map.toml"))
NAMES = [a.name for a in AXES]
TABULAR = {"learner_depth": "tabular", "deep_architecture": "not-applicable",
           "state_encoding": "discrete-states", "training_algorithm_family": "value-based"}
UNSTATED = {"learner_depth": "not-stated", "deep_architecture": "not-stated"}

# number: (abstract, the map's codes, {model: (its level, its quote)}). Records 1 and 2 are
# candidates with a claim; record 3 claims one but its learner is not stated; 4 claims none.
RECORDS = {
    1: ("A policy is learned and then tested on data from an engine plant.",
        {"readiness_claim": "real-data"},
        {"qwen38": ("real-data", "tested on data from an engine plant"), "gemma26": ("none", ""),
         "glimmer30": ("real-data", "data from an engine plant")}),
    2: ("The policy ran in a digital twin of the shop.",
        {**TABULAR, "readiness_claim": "twin-or-hil"},
        {"qwen38": ("twin-or-hil", "ran in a digital twin of the shop"),
         "gemma26": ("twin-or-hil", "a digital twin"), "glimmer30": ("none", "")}),
    3: ("Real data from a factory.", {**UNSTATED, "readiness_claim": "real-data"},
        {m: ("real-data", "Real data from a factory") for m in MODELS}),
    4: ("Benchmarks only.", {}, {m: ("none", "") for m in MODELS}),
}
# The columns of an older confirmations file, which still reads; core_claims.SHEET_FIELDS
# adds level and read_from.
ANSWER_FIELDS = ["number", "confirmed", "note", "confirmed_by"]
LEVELS = ["real-data", "twin-or-hil", "testbed-or-shadow", "live-system"]


def meta(n):
    return {"title": "Paper %d" % n, "venue": "A journal", "year": 2024, "work_type": "article"}


def build(tmp_path):
    """The map, the models' coding files, the corpus, the scheme and the config under
    tmp_path; returns the config's path and the folder of the outputs."""
    d = tmp_path.as_posix()
    data = os.path.join(d, "datasets")
    os.makedirs(data, exist_ok=True)
    write_csv(os.path.join(data, "map.csv"), ["number"] + NAMES + list(mc.META),
              [{"number": n, **BASE, **codes, **meta(n)} for n, (_, codes, _) in RECORDS.items()])
    fields = (["number"] + NAMES + ["policy_role_evidence", "learner_depth_evidence",
                                    "readiness_claim_evidence"] + list(mc.META))
    for m in MODELS:
        write_csv(os.path.join(data, "map-%s.csv" % m), fields,
                  [{"number": n, **BASE, **codes, "readiness_claim": claims[m][0],
                    "readiness_claim_evidence": claims[m][1], **meta(n)}
                   for n, (_, codes, claims) in RECORDS.items()])
    refs = [{"number": n, "openalex_id": "https://openalex.org/W%d" % n, "doi": "10.1/x%d" % n,
             "abstract": abstract, **meta(n)} for n, (abstract, _, _) in RECORDS.items()]
    with open(os.path.join(data, "references.json"), "w", encoding="utf-8") as fh:
        json.dump({"references": refs}, fh)
    shutil.copy(os.path.join(REPO, "datasets", "coding-scheme.md"), data)
    with open(os.path.join(REPO, "configs", "core.toml"), encoding="utf-8") as fh:
        text = fh.read()
    # The sheet goes beside the authors' copies (../data/), here a folder of tmp_path.
    for old, new in (('"datasets/', '"%s/datasets/' % d), ('"results/', '"%s/results/' % d),
                     ('"../data/', '"%s/data/' % d)):
        assert old in text, old
        text = text.replace(old, new)
    config = os.path.join(d, "core.toml")
    with open(config, "w", encoding="utf-8") as fh:
        fh.write(text)
    return config, os.path.join(d, "results", "core")


def run(config, monkeypatch):
    monkeypatch.setattr("sys.argv", ["core_claims", "--config", config])
    core_claims.main()


def write_confirmations(tmp_path, rows, fields=ANSWER_FIELDS):
    write_csv(os.path.join(tmp_path, "datasets", "core-claims.csv"), fields, rows)


def report(results):
    with open(os.path.join(results, "claims.md"), encoding="utf-8") as fh:
        return fh.read()


def test_the_sheet_holds_the_candidates_that_claim_use_beyond_simulation(tmp_path, monkeypatch):
    config, results = build(tmp_path)
    run(config, monkeypatch)
    rows = read_csv(os.path.join(sheets(results), "claims-sheet.csv"))
    assert [(r["number"], r["claimed_level"], r["confirmed"]) for r in rows] == [
        ("1", "real-data", ""), ("2", "twin-or-hil", "")]
    data = page_data(os.path.join(sheets(results), "claims-sheet.html"))
    assert data["save_as"].endswith("datasets/core-claims.csv")
    assert data["columns"] == core_claims.SHEET_FIELDS
    assert data["levels"] == LEVELS
    assert data["criteria_brief"].startswith("### `readiness_claim`")
    first = data["records"][0]
    assert first["number"] == 1 and "engine plant" in first["abstract"]
    assert first["level"] == "real-data" and "(L2)" in first["level_text"]
    assert "`" not in first["level_text"]
    assert [(m["name"], m["level"], m["quote"]) for m in first["models"]] == [
        ("qwen38", "real-data", "tested on data from an engine plant"),
        ("gemma26", "none", ""), ("glimmer30", "real-data", "data from an engine plant")]
    text = report(results)
    assert "3 records of the map claim use beyond simulation" in text
    assert "2 of them are candidates for the core" in text
    assert "not candidates for the core: 3." in text and "not yet saved" in text
    # Step 1 counts only the claims above real data: record 2's digital twin.
    assert "The models' claims at these levels on the sheet: 1. Places at step 1: 0." in text
    assert "Levels the person changed: none." in text
    assert "Settled from the full text: none." in text
    said = " ".join(data["intro"])
    assert "choose that level under Level" in said
    assert "tick 'Settled from the full text'" in said


def test_the_abstracts_withheld_the_report_is_written_and_no_sheet(tmp_path, monkeypatch):
    # As in a clone: the records' abstracts are withheld and their authors' copy absent. The
    # report is written; the sheet and its page, which show the abstracts, are not.
    config, results = build(tmp_path)
    without_abstracts(tmp_path, monkeypatch)
    run(config, monkeypatch)
    assert "2 of them are candidates for the core" in report(results)
    assert not os.path.exists(sheets(results))


def test_every_level_has_its_text_from_the_scheme():
    section = core_claims.scheme_section(os.path.join(REPO, "datasets", "coding-scheme.md"),
                                         "readiness_claim")
    codes = next(a.codes for a in AXES if a.name == "readiness_claim")
    texts = core_claims.level_texts(section, codes)
    for level, code in enumerate(codes, 1):
        assert "L%d" % level in texts[code], code


def test_confirmations_are_read_back_counted_and_carried_on_the_sheet(tmp_path, monkeypatch):
    config, results = build(tmp_path)
    write_confirmations(tmp_path, [
        {"number": 1, "confirmed": "Yes", "confirmed_by": "osamah"},
        {"number": 2, "confirmed": "no", "note": "a simulator only", "confirmed_by": "osamah"}])
    run(config, monkeypatch)
    rows = {r["number"]: r for r in read_csv(os.path.join(sheets(results), "claims-sheet.csv"))}
    assert (rows["1"]["confirmed"], rows["2"]["confirmed"], rows["2"]["note"]) == (
        "yes", "no", "a simulator only")
    assert page_data(os.path.join(sheets(results), "claims-sheet.html"))["records"][0]["answer"][
        "confirmed"] == "yes"
    text = report(results)
    assert "| `real-data` | 1 | 1 | 0 | 0 |" in text
    assert "| `twin-or-hil` | 1 | 0 | 1 | 0 |" in text
    assert "2 of 2 answered" in text
    # Record 1's real-data claim is confirmed, but only record 2's level counts for step 1.
    assert "The models' claims at these levels on the sheet: 1. Places at step 1: 0." in text
    # A file without the level and read_from columns reads as the models' level.
    assert (rows["1"]["level"], rows["1"]["read_from"]) == ("", "")
    assert "| `real-data` | 1 |\n" in text and "| `twin-or-hil` | 0 |\n" in text


def test_the_persons_level_and_the_full_text_decide_step_1(tmp_path, monkeypatch):
    config, results = build(tmp_path)
    write_confirmations(tmp_path, [
        {"number": 1, "confirmed": "yes", "level": "twin-or-hil", "confirmed_by": "moayad"},
        {"number": 2, "confirmed": "Yes", "level": "Real-data", "read_from": "full-text",
         "note": "only the plant's data", "confirmed_by": "moayad"}],
        fields=core_claims.SHEET_FIELDS)
    run(config, monkeypatch)
    rows = {r["number"]: r for r in read_csv(os.path.join(sheets(results), "claims-sheet.csv"))}
    assert (rows["1"]["level"], rows["2"]["level"], rows["2"]["read_from"]) == (
        "twin-or-hil", "real-data", "full-text")
    assert page_data(os.path.join(sheets(results), "claims-sheet.html"))["records"][1]["answer"][
        "read_from"] == "full-text"
    text = report(results)
    # Record 1, claimed at real data, is confirmed in a digital twin and takes a place; record
    # 2, claimed in a digital twin, is confirmed at real data alone and takes none.
    assert "The models' claims at these levels on the sheet: 1. Places at step 1: 1 (1)." in text
    assert ("Levels the person changed: 1 (`real-data` to `twin-or-hil`), "
            "2 (`twin-or-hil` to `real-data`).") in text
    assert "Settled from the full text: 2." in text
    assert "| `real-data` | 1 |\n" in text and "| `twin-or-hil` | 1 |\n" in text
    answers = {1: {"confirmed": "yes", "level": "twin-or-hil"},
               2: {"confirmed": "no", "level": ""}}
    the_map = {1: {"readiness_claim": "real-data"}, 2: {"readiness_claim": "twin-or-hil"}}
    assert core_claims.step1_places([1, 2], the_map, answers, ["twin-or-hil"]) == [1]


def test_a_bad_confirmations_file_is_refused(tmp_path, monkeypatch):
    config, _ = build(tmp_path)
    for rows, message in (
            ([{"number": 1, "confirmed": "maybe", "confirmed_by": "osamah"}], "not yes or no"),
            ([{"number": 4, "confirmed": "yes", "confirmed_by": "osamah"}], "4 is not on the sheet"),
            ([{"number": 1, "confirmed": "yes", "confirmed_by": ""}], "1: no confirmed_by"),
            ([{"number": 1, "confirmed": "yes", "confirmed_by": "o"},
              {"number": 1, "confirmed": "no", "confirmed_by": "o"}], "1 given twice"),
            ([{"number": 1, "confirmed": "no", "level": "twin-or-hil", "confirmed_by": "o"}],
             "1: a level goes with yes"),
            ([{"number": 1, "confirmed": "yes", "level": "none", "confirmed_by": "o"}],
             "1: level 'none', not one of"),
            ([{"number": 1, "read_from": "full-text"}],
             "1: read from the full text, but no answer"),
            ([{"number": 1, "confirmed": "yes", "read_from": "paper", "confirmed_by": "o"}],
             "1: read_from 'paper', not abstract or full-text")):
        write_confirmations(tmp_path, rows, fields=core_claims.SHEET_FIELDS)
        with pytest.raises(SystemExit, match=message):
            run(config, monkeypatch)


def test_a_sheet_filled_in_place_is_not_overwritten(tmp_path, monkeypatch):
    config, results = build(tmp_path)
    run(config, monkeypatch)
    sheet = os.path.join(sheets(results), "claims-sheet.csv")
    rows = read_csv(sheet)
    rows[0].update({"confirmed": "yes", "confirmed_by": "osamah"})
    write_csv(sheet, list(rows[0]), rows)
    with pytest.raises(SystemExit, match="answers not saved"):
        run(config, monkeypatch)
    # Saved under the confirmations' name, the answers are read back and the sheet re-issued.
    shutil.copy(sheet, os.path.join(tmp_path, "datasets", "core-claims.csv"))
    run(config, monkeypatch)
    assert read_csv(sheet)[0]["confirmed"] == "yes"


def test_a_saved_file_corrected_directly_is_read_and_the_sheet_reissued(tmp_path, monkeypatch):
    config, results = build(tmp_path)
    write_confirmations(tmp_path, [{"number": 1, "confirmed": "yes", "confirmed_by": "osamah"}])
    run(config, monkeypatch)
    # The sheet is left as written; only the saved file changes.
    write_confirmations(tmp_path, [{"number": 1, "confirmed": "no", "confirmed_by": "osamah"}])
    run(config, monkeypatch)
    assert read_csv(os.path.join(sheets(results), "claims-sheet.csv"))[0]["confirmed"] == "no"


def test_the_page_template_holds_one_data_block():
    with open(os.path.join(REPO, "src", "confirm_page.html"), encoding="utf-8") as fh:
        assert fh.read().count(sc.PAGE_PLACEHOLDER) == 1


def test_the_coders_are_the_maps():
    def table(name):
        with open(os.path.join(REPO, "configs", name), "rb") as fh:
            return tomllib.load(fh)["coders"]
    assert list(table("core.toml")) == list(table("map-vote.toml"))
