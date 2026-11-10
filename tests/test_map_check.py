"""Tests for the person's blind check of the map (runners/map_check.py): the seeded sample
from the records included without a person outside the calibration batch, the blind sheet
and its page, the codes read back and checked, the report, and the lock."""

import os
import shutil
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import mapcodes as mc  # noqa: E402
import map_check  # noqa: E402
import screening_setup as setup  # noqa: E402
from screening_setup import sheets  # noqa: E402
from test_map_vote import MODELS, text, write_coding  # noqa: E402

AXES = mc.load_axes(os.path.join(REPO, "configs", "map.toml"))
NAMES = [a.name for a in AXES]
CHECKED = ["policy_role", "learner_depth", "readiness_claim"]
ANSWER_FIELDS = ["number"] + CHECKED + ["note", "coded_by"]

# The screening's decisions: record 1 is in batch 01 (batch size 3 in the fixture), 6 was
# carried forward by a person, 4 was excluded; 5, 9 and 10 were included without a person.
SCREENING = {1: ("include", "vote"), 4: ("exclude", "vote"), 5: ("include", "vote"),
             6: ("include", "validation"), 9: ("include", "vote"), 10: ("include", "rule")}
FRAME = [5, 9, 10]
# The map's codes of the included records; every model codes as the map does.
MAP = {1: text(), 5: text(), 6: text(),
       9: text(policy_role="steering-rules", scheduling_action="not-applicable"),
       10: text(policy_role="not-stated", scheduling_action="not-stated",
                readiness_claim="real-data")}


def build(tmp_path, size=2):
    """The screening fixture, the consensus, the map, the models' files, the scheme and the
    config under tmp_path; returns the config's path, the data folder and the results
    folder."""
    screening_config, data = setup.build(tmp_path, first_round=False, votes=setup.VOTES_COMPLETE)
    setup.write_csv(os.path.join(data, "screening.csv"),
                    ["number", "decision", "confidence", "reason", "evidence", "basis"],
                    [{"number": n, "decision": d, "confidence": "high", "reason": "r",
                      "evidence": "q", "basis": b} for n, (d, b) in SCREENING.items()])
    setup.write_csv(os.path.join(data, "map.csv"), ["number"] + NAMES + list(mc.META),
                    [{"number": n, **codes} for n, codes in MAP.items()])
    for m in MODELS:
        write_coding(os.path.join(data, "map-%s.csv" % m), MAP)
    shutil.copy(os.path.join(REPO, "datasets", "coding-scheme.md"), data)
    with open(os.path.join(REPO, "configs", "map-vote.toml"), encoding="utf-8") as fh:
        config_text = fh.read()
    d = tmp_path.as_posix()
    # The sheet goes beside the authors' copies (../data/), here a folder of tmp_path.
    for old, new in (('"datasets/', '"%s/datasets/' % d), ('"results/', '"%s/results/' % d),
                     ('"../data/', '"%s/data/' % d),
                     ('screening_config = "configs/screening.toml"',
                      'screening_config = "%s"' % screening_config.replace("\\", "/")),
                     ("size = 25", "size = %d" % size)):
        assert old in config_text, old
        config_text = config_text.replace(old, new)
    config = os.path.join(d, "map-vote.toml")
    with open(config, "w", encoding="utf-8") as fh:
        fh.write(config_text)
    return config, data, os.path.join(d, "results", "map")


def drawn(results):
    return sorted(int(r["number"]) for r in setup.read_csv(os.path.join(sheets(results), "map-check-sheet.csv")))


def codes_of(n):
    return tuple(MAP[n][axis] for axis in CHECKED)


def answer_rows(given, coded_by="moayad"):
    return [dict(zip(CHECKED, codes), number=n, note="", coded_by=coded_by)
            for n, codes in given.items()]


def report(results):
    with open(os.path.join(results, "map-check.md"), encoding="utf-8") as fh:
        return fh.read()


def test_the_sample_is_drawn_blind_from_records_included_without_a_person(tmp_path, monkeypatch):
    config, data, results = build(tmp_path)
    setup.run(map_check, config, monkeypatch)
    sample = drawn(results)
    # Record 1 is in batch 01 and record 6 was carried forward by a person: neither is drawn.
    assert sample == map_check.draw(FRAME, 2, 20261015) and set(sample) <= set(FRAME)
    sheet = setup.read_csv(os.path.join(sheets(results), "map-check-sheet.csv"))
    assert list(sheet[0]) == ["number", "title"] + CHECKED + ["note", "coded_by"]
    assert not any(r[axis] for r in sheet for axis in CHECKED)
    page = setup.page_data(os.path.join(sheets(results), "map-check-sheet.html"))
    options = {q["name"]: q["options"] for q in page["questions"]}
    assert list(options) == CHECKED
    assert "not-stated" in options["policy_role"] and "not-stated" not in options["readiness_claim"]
    assert page["criteria_brief"].startswith("### `policy_role`")
    assert not any("answer" in r and any(r["answer"][a] for a in CHECKED) for r in page["records"])
    with open(os.path.join(sheets(results), "map-check-sheet.md"), encoding="utf-8") as fh:
        sheet_md = fh.read()
    assert not any(m in sheet_md for m in MODELS)
    assert "0 of 2 sampled records coded" in report(results)


def test_the_abstracts_withheld_the_report_is_written_and_no_sheet(tmp_path, monkeypatch):
    # As in a clone: the records' abstracts are withheld and their authors' copy absent. The
    # report is written; the sheet, which shows the abstracts, is not.
    config, data, results = build(tmp_path)
    setup.without_abstracts(tmp_path, monkeypatch)
    setup.run(map_check, config, monkeypatch)
    assert "0 of 2 sampled records coded" in report(results)
    assert not os.path.exists(sheets(results))


def test_the_codes_are_compared_with_the_map_once_complete(tmp_path, monkeypatch):
    config, data, results = build(tmp_path)
    setup.run(map_check, config, monkeypatch)
    first, second = drawn(results)
    answers = os.path.join(data, "map-check.csv")
    setup.write_csv(answers, ANSWER_FIELDS, answer_rows({first: codes_of(first)}))
    setup.run(map_check, config, monkeypatch)
    assert "1 of 2 sampled records coded" in report(results)
    assert not os.path.exists(os.path.join(results, "map-check-lock.json"))

    # The person agrees with the map on the first record, and differs on the second's role.
    other = ("steering-heuristic",) + codes_of(second)[1:]
    setup.write_csv(answers, ANSWER_FIELDS,
                    answer_rows({first: codes_of(first), second: other}))
    setup.run(map_check, config, monkeypatch)
    text_ = report(results)
    assert "| `policy_role` | 1 of 2 (50%) |" in text_
    assert "| `learner_depth` | 2 of 2 (100%) | n/a |" in text_
    assert "| %d | `policy_role` | `steering-heuristic` | `%s` |" % (second, MAP[second]["policy_role"]) in text_
    assert os.path.isfile(os.path.join(results, "map-check-lock.json"))


def test_bad_codes_are_refused(tmp_path, monkeypatch):
    config, data, results = build(tmp_path)
    setup.run(map_check, config, monkeypatch)
    sample = drawn(results)
    n = sample[0]
    outside = next(x for x in FRAME if x not in sample)
    answers = os.path.join(data, "map-check.csv")
    for rows, message in (
            (answer_rows({n: ("end-to-end", "deep", "not-stated")}), "not a code of the axis"),
            (answer_rows({n: ("end-to-end", "neural", "none")}), "not a code of the axis"),
            (answer_rows({outside: ("end-to-end", "deep", "none")}), "is not in the sample"),
            (answer_rows({n: ("end-to-end", "deep", "none")}, coded_by=""), "no coded_by")):
        setup.write_csv(answers, ANSWER_FIELDS, rows)
        with pytest.raises(SystemExit, match=message):
            setup.run(map_check, config, monkeypatch)


def test_codes_changed_after_the_lock_are_refused(tmp_path, monkeypatch):
    config, data, results = build(tmp_path)
    setup.run(map_check, config, monkeypatch)
    first, second = drawn(results)
    answers = os.path.join(data, "map-check.csv")
    setup.write_csv(answers, ANSWER_FIELDS,
                    answer_rows({first: codes_of(first), second: codes_of(second)}))
    setup.run(map_check, config, monkeypatch)
    setup.write_csv(answers, ANSWER_FIELDS,
                    answer_rows({first: ("steering-heuristic",) + codes_of(first)[1:],
                                 second: codes_of(second)}))
    with pytest.raises(SystemExit, match="changed after they were locked"):
        setup.run(map_check, config, monkeypatch)


def test_the_coding_template_holds_one_data_block():
    from src import screening as sc
    with open(os.path.join(REPO, "src", "coding_page.html"), encoding="utf-8") as fh:
        assert fh.read().count(sc.PAGE_PLACEHOLDER) == 1
