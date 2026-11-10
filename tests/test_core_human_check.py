"""Tests for a person's check of six questions on the fifth (runners/core_human_check.py,
src/human_check_page.html; protocol, Amendments: coding and checking the core), on a small
fifth of three studies built in a temporary folder."""

import csv
import json
import os
import re
import shutil
import sys
import tomllib

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

import core_human_check as hc  # noqa: E402

CONFIG = os.path.join(REPO, "configs", "core-human-check.toml")
TEMPLATE = os.path.join(REPO, "src", "human_check_page.html")
FIFTH = [12, 5, 40]
SIX_COLUMNS = ["number", "title", "coder", "role", "algorithm", "readiness", "runs",
               "baselines", "transfer", "note"]


def write_rows(path, fields, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def build(tmp_path, answers=None, source=CONFIG, columns=SIX_COLUMNS):
    """A config whose inputs and outputs all sit in tmp_path, over a fifth of three studies
    (5, 12 and 40) and one pilot study (7), with the questions, page and report settings of
    the real config `source`, and the real template and Part B."""
    d = tmp_path
    (d / "texts").mkdir()
    for n in FIFTH + [7]:
        (d / "texts" / ("%d.pdf" % n)).write_bytes(b"%PDF-1.4 study " + str(n).encode())
    write_rows(d / "draws.csv", ["number", "draw"],
               [{"number": 7, "draw": "pilot"}] + [{"number": n, "draw": "fifth"} for n in FIFTH])
    refs = [{"number": n, "title": "Study <%d> of the shop" % n, "first_author": "A. Author",
             "year": 2025, "venue": "Journal", "doi": "10.1/%d" % n} for n in FIFTH + [7]]
    (d / "references.json").write_text(json.dumps({"references": refs}), encoding="utf-8")
    coded = [
        {"number": 5, "policy_role": "end-to-end", "algorithm": "ppo", "readiness_level": "L1",
         "seeds": "1", "baselines": "2", "transfer_tests": "3"},
        {"number": 12, "policy_role": "steering-rules", "algorithm": "q-learning",
         "readiness_level": "L2", "seeds": "not-reported", "baselines": "1", "transfer_tests": "0"},
        {"number": 40, "policy_role": "steering-heuristic", "algorithm": "sarsa",
         "readiness_level": "L1", "seeds": "10", "baselines": "0", "transfer_tests": "not-stated"},
    ]
    write_rows(d / "coded.csv", list(coded[0]), coded)
    write_rows(d / "baselines.csv", ["number", "item", "run"],
               [{"number": 5, "item": 1, "run": "rerun"}, {"number": 5, "item": 2, "run": "rerun"},
                {"number": 12, "item": 1, "run": "copied"}])
    with open(source, "rb") as fh:
        cfg = tomllib.load(fh)
    p = lambda name: (d / name).as_posix()  # noqa: E731
    lines = ['[inputs]',
             'references = "%s"' % p("references.json"), 'draws = "%s"' % p("draws.csv"),
             'draw = "fifth"', 'coded = "%s"' % p("coded.csv"),
             'baselines = "%s"' % p("baselines.csv"), 'full_texts = "%s"' % p("texts"),
             'coding = "%s"' % os.path.join(REPO, "configs", "core-coding.toml").replace("\\", "/"),
             'template = "%s"' % TEMPLATE.replace("\\", "/"),
             'answers = "%s"' % p("core-human-check.csv"),
             '[outputs]', 'folder = "%s"' % p("out"), 'page = "%s"' % p("out/human-check.html"),
             'readme = "%s"' % p("out/README.md"), 'report = "%s"' % p("report.md"),
             'table = "%s"' % p("report.csv")]
    for name in ("page", "report"):
        if name in cfg:
            lines.append("[%s]" % name)
            for k, v in cfg[name].items():
                lines.append("%s = %s" % (k, json.dumps(v)))
    for q in cfg["question"]:
        lines.append("[[question]]")
        for k, v in q.items():
            lines.append("%s = %s" % (k, json.dumps(v)))
    config = d / "check.toml"
    config.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if answers is not None:
        write_rows(d / "core-human-check.csv", columns, answers)
    return str(config)


def run(config, monkeypatch):
    monkeypatch.setattr("sys.argv", ["core_human_check", "--config", config])
    hc.main()


def page_json(path):
    text = open(path, encoding="utf-8").read()
    block = re.search(r'<script id="data" type="application/json">(.*?)</script>', text, re.S)
    return text, json.loads(block.group(1))


def person(rows):
    out = []
    for n, role, alg, level, runs, base, transfer in rows:
        out.append({"number": n, "title": "Study <%d> of the shop" % n, "coder": "O. H. Hussein",
                    "role": role, "algorithm": alg, "readiness": level, "runs": runs,
                    "baselines": base, "transfer": transfer, "note": ""})
    return out


AGREEING = person([(5, "end-to-end", "ppo", "L1", "1", "yes", "yes"),
                   (12, "steering-rules", "q-learning", "L2", "not-reported", "no", "no"),
                   (40, "steering-heuristic", "sarsa", "L1", "10", "none", "no")])


def test_the_page_holds_the_fifth_and_no_model_answer(tmp_path, monkeypatch):
    config = build(tmp_path)
    run(config, monkeypatch)
    text, data = page_json(tmp_path / "out" / "human-check.html")
    assert [s["number"] for s in data["studies"]] == [5, 12, 40]  # the pilot study is not drawn
    assert [q["id"] for q in data["questions"]] == hc.QUESTION_IDS
    assert data["save_as"] == "core-human-check.csv"
    assert data["columns"] == hc.fields(data["questions"])
    # No model answer reaches the page: the studies carry only their records and PDF links.
    assert set(data["studies"][0]) == {"number", "title", "first_author", "year", "venue",
                                       "doi", "link", "pdf"}
    assert "Study <5>" not in text  # every "<" of the data is escaped
    assert hc.PLACEHOLDER not in text


def test_the_folder_is_self_contained(tmp_path, monkeypatch):
    config = build(tmp_path)
    run(config, monkeypatch)
    out = tmp_path / "out"
    assert sorted(os.listdir(out / "pdfs")) == ["12.pdf", "40.pdf", "5.pdf"]
    assert (out / "pdfs" / "12.pdf").read_bytes() == (tmp_path / "texts" / "12.pdf").read_bytes()
    assert "Show guide" in (out / "README.md").read_text(encoding="utf-8")
    run(config, monkeypatch)  # a second run leaves identical copies in place
    assert hc.copy_pdfs(FIFTH, str(tmp_path / "texts"), str(out)) == 0


def test_a_missing_full_text_is_refused(tmp_path, monkeypatch):
    config = build(tmp_path)
    os.remove(tmp_path / "texts" / "40.pdf")
    with pytest.raises(SystemExit, match="No full text saved .* for 40"):
        run(config, monkeypatch)


def test_nothing_is_compared_before_the_file_is_returned(tmp_path, monkeypatch, capsys):
    config = build(tmp_path)
    run(config, monkeypatch)
    assert "nothing compared" in capsys.readouterr().out
    assert not (tmp_path / "report.md").exists()


def test_without_the_full_texts_the_file_is_still_compared(tmp_path, monkeypatch, capsys):
    # As in a clone of the repository alone: no full texts, the returned file in datasets/.
    config = build(tmp_path, AGREEING)
    shutil.rmtree(tmp_path / "texts")
    run(config, monkeypatch)
    assert "no page, README or PDF written" in capsys.readouterr().out
    assert not (tmp_path / "out").exists()
    with open(tmp_path / "report.csv", encoding="utf-8-sig") as fh:
        rows = {r["question"]: r for r in csv.DictReader(fh)}
    assert len(rows) == 8
    assert all(r["agree"] == "3" and r["share"] == "100.0" for r in rows.values())
    assert "None." in (tmp_path / "report.md").read_text(encoding="utf-8")


def test_the_reductions():
    assert hc.reduce_baselines("2", ["rerun", "rerun"]) == "yes"
    assert hc.reduce_baselines("2", ["rerun", "copied"]) == "no"
    assert hc.reduce_baselines("1", ["not-stated"]) == "no"
    assert hc.reduce_baselines("0", []) == "none"
    assert hc.reduce_baselines("not-stated", []) == "none"
    assert hc.reduce_transfer("3") == "yes"
    assert hc.reduce_transfer("0") == "no"
    assert hc.reduce_transfer("not-stated") == "no"
    assert hc.runs_bin("1") == "1"
    assert hc.runs_bin("20") == "more than 1"
    assert hc.runs_bin("not-reported") == "not-reported"


def test_kappa():
    assert hc.kappa([("a", "a"), ("b", "b")]) == pytest.approx(1.0)
    assert hc.kappa([("a", "b"), ("b", "a")]) == pytest.approx(-1.0)
    assert hc.kappa([("a", "a"), ("a", "b")]) is None  # one side gives a single code
    assert hc.kappa([]) is None


def test_full_agreement_is_reported(tmp_path, monkeypatch):
    config = build(tmp_path, AGREEING)
    run(config, monkeypatch)
    with open(tmp_path / "report.csv", encoding="utf-8-sig") as fh:
        rows = {r["question"]: r for r in csv.DictReader(fh)}
    assert list(rows) == ["role", "algorithm", "algorithm family", "readiness", "runs",
                          "training runs, by bin", "baselines", "transfer"]
    assert all(r["agree"] == "3" and r["share"] == "100.0" for r in rows.values())
    assert "None." in (tmp_path / "report.md").read_text(encoding="utf-8")


def test_disagreements_are_listed_and_families_compared(tmp_path, monkeypatch):
    answers = person([(5, "end-to-end", "reinforce", "L1", "5", "yes", "yes"),
                      (12, "steering-heuristic", "q-learning", "L2", "not-reported", "no", "no"),
                      (40, "steering-heuristic", "sarsa", "L1", "10", "none", "yes")])
    config = build(tmp_path, answers)
    run(config, monkeypatch)
    with open(tmp_path / "report.csv", encoding="utf-8-sig") as fh:
        rows = {r["question"]: r for r in csv.DictReader(fh)}
    assert rows["algorithm"]["agree"] == "2"
    assert rows["algorithm family"]["agree"] == "3"  # reinforce and ppo are both policy gradient
    assert rows["runs"]["agree"] == "2"
    assert rows["training runs, by bin"]["agree"] == "2"  # 5 against 1
    assert rows["role"]["agree"] == "2"
    assert rows["transfer"]["agree"] == "2"
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "| 12 | role | steering-heuristic | steering-rules |" in report
    assert "| 40 | transfer | yes | no |" in report


@pytest.mark.parametrize("change, message", [
    (lambda rows: rows[:2], "no row: 40"),
    (lambda rows: [dict(rows[0], role="steering")] + rows[1:], "role is not one of"),
    (lambda rows: [dict(rows[0], runs="0")] + rows[1:], "runs is neither a whole number"),
    (lambda rows: [dict(rows[0], transfer="")] + rows[1:], "transfer not answered"),
    (lambda rows: [dict(rows[0], coder="")] + rows[1:], "no coder named"),
    (lambda rows: [dict(rows[0], title="Another study")] + rows[1:], "the title differs"),
    (lambda rows: rows + [dict(rows[0], number=7)], "not a study of the fifth: 7"),
])
def test_a_faulty_file_is_refused(tmp_path, monkeypatch, change, message):
    config = build(tmp_path, change(list(AGREEING)))
    with pytest.raises(SystemExit, match=message):
        run(config, monkeypatch)


def test_the_config_holds_the_amendments_six_questions():
    with open(CONFIG, "rb") as fh:
        cfg = tomllib.load(fh)
    questions = hc.load_questions(cfg)
    assert [q["id"] for q in questions] == hc.QUESTION_IDS
    by_id = {q["id"]: q for q in questions}
    with open(os.path.join(REPO, "configs", "core-coding.toml"), "rb") as fh:
        family = tomllib.load(fh)["derived"]["algorithm_family"]["map"]
    # Every algorithm the page offers, but not-stated, has a family in Part B's mirror.
    assert set(by_id["algorithm"]["codes"]) - {"not-stated"} == set(family)
    assert by_id["readiness"]["codes"] == ["L1", "L2", "L3", "L4", "L5"]
    assert by_id["runs"]["number"] is True and by_id["runs"]["codes"] == ["not-reported"]
    assert all(q["definition"] for q in questions)


def test_some_of_the_questions_may_be_asked_in_order():
    q = lambda i: {"id": i, "codes": ["x"]}  # noqa: E731
    assert [x["id"] for x in hc.load_questions({"question": [q("readiness")]})] == ["readiness"]
    asked = hc.load_questions({"question": [q("role"), q("runs")]})
    assert [x["id"] for x in asked] == ["role", "runs"]
    for ids in (["runs", "role"], ["readiness", "readiness"], ["level"], []):
        with pytest.raises(SystemExit, match="or some of them"):
            hc.load_questions({"question": [q(i) for i in ids]})
