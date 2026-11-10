"""Tests for the gather of the core's answers (runners/core_gather.py): two studies' responses,
built from the real questions so that they pass the checks, a small paper, the judge's
verdicts and the coding run's record, all in tmp_path."""

import csv
import hashlib
import json
import os
import shutil
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

import core_gather as cg  # noqa: E402
from src import coreblocks as cb  # noqa: E402
from runners.core_selection import core_digest  # noqa: E402

BAR = "-" * 48
PAPER = [
    "{0}" + BAR,
    "# **A learning scheduler**",
    "We propose a deep reinforcement learning method in which a single agent selects an "
    "operation and a machine at each decision point.",
    "The agent learns online by interacting with a simulated job shop.",
    "The reward is a hand-designed function of the makespan.",
    "The agent observes the full state of the shop at each step.",
    "The policy is trained with proximal policy optimization.",
    "{1}" + BAR,
    "## 5. Experiments",
    "We compare against the dispatching rules SPT and MWKR, which run once.",
    "The trained policy is tested unchanged on instances twice as large as those it was "
    "trained on.",
    "The shop of each instance gives its jobs, machines, eligible machines and processing "
    "times.",
    "## References",
    "[1] A reference.",
]
# The questions that allow no special answer and need a quoted code.
QUOTED = {"B06": ("online", 0, "The agent learns online by interacting with a simulated job shop."),
          "C09": ("hand-designed", 0, "The reward is a hand-designed function of the makespan."),
          "C11": ("full", 0, "The agent observes the full state of the shop at each step.")}
NOTE = "searched: quokka"
SPEC = cb.load_spec(os.path.join(REPO, "configs", "core-coding.toml"),
                    os.path.join(REPO, "configs", "map.toml"))


def block(qid, name, answer, evidence=(), note="", fields=None):
    lines = ["## %s %s" % (qid, name), "answer: %s" % answer]
    lines += ["%s: %s" % (k, v) for k, v in (fields or {}).items()]
    lines += ['evidence: {%d} "%s"' % (p, q) for p, q in evidence]
    return "\n".join(lines + ["note: %s" % note])


def plain_blocks():
    """{qid: block} answering every question with no content where it allows that."""
    out = {}
    for qid, q in SPEC.questions.items():
        if q.kind == "count":
            out[qid] = block(qid, q.name, "none")
        elif "not-stated" in q.special:
            out[qid] = block(qid, q.name, "not-stated", note=NOTE)
        elif "not-reported" in q.special:
            out[qid] = block(qid, q.name, "not-reported", note=NOTE)
        elif q.kind == "score":
            out[qid] = block(qid, q.name, "0")
        elif q.kind == "level":
            out[qid] = block(qid, q.name, "L1")
        elif q.no_quote:
            out[qid] = block(qid, q.name, q.no_quote[0])
        else:
            answer, page, quote = QUOTED[qid]
            out[qid] = block(qid, q.name, answer, [(page, quote)])
    return out


def end_to_end_blocks():
    """Study 6: an end-to-end policy, one baseline, one transfer test, a name and a score."""
    out = plain_blocks()
    out["A01"] = block("A01", "policy_role", "end-to-end", [(0, "a single agent selects an "
                                                              "operation and a machine")])
    out["B04"] = block("B04", "steering_action", "not-applicable", note="end to end")
    out["B05"] = block("B05", "steered_method", "not-applicable", note="end to end")
    out["B08"] = block("B08", "algorithm_name", "proximal policy optimization",
                       [(0, "The policy is trained with proximal policy optimization.")])
    sentence = "We compare against the dispatching rules SPT and MWKR, which run once."
    out["D07"] = block("D07", "baselines", "1", [(1, sentence)])
    out["D07.1"] = block("D07.1", "baseline", "SPT and MWKR rules", [(1, sentence)],
                         fields={"kind": "dispatching-rule", "run": "rerun",
                                 "time_limit": "not-applicable"})
    larger = "The trained policy is tested unchanged on instances twice as large"
    out["E01"] = block("E01", "transfer_tests", "1", [(1, larger)])
    out["E01.1"] = block("E01.1", "transfer_test", "size", [(1, larger)],
                         fields={"provenance": "generated", "mode": "unchanged",
                                 "outcome": "not-stated"})
    out["Q01"] = block("Q01", "q_shop", "1", [(1, "gives its jobs, machines, eligible machines "
                                                  "and processing times")])
    return out


def response(number, blocks):
    return cb.assemble(SPEC, blocks, ["# Record %d" % number,
                                      "model: Qwen/Qwen3.8-27B @ abc123",
                                      "date: 2026-10-22T01:00:00+00:00"])


VERDICTS = [
    {"number": 6, "id": "A01", "verdict": "supported"},
    {"number": 6, "id": "Q01", "verdict": "partly", "proposed_answer": "0.5",
     "reason": "The paper gives its jobs, machines and wombats.",
     "proposed_evidence": json.dumps([{"page": 1, "quote": "eligible machines and processing"}])},
    {"number": 6, "id": "B08", "verdict": "partly", "proposed_answer": "PPO with masking"},
    {"number": 6, "id": "D07.1", "verdict": "not-supported", "proposed_answer": "rules",
     "proposed_fields": json.dumps({"kind": "metaheuristic", "run": "copied"})},
]


def build(tmp_path, numbers=(5, 6), with_responses=(5, 6), blocks=None, runs_sha=None,
          corrections=None):
    """A config gathering the studies' responses, with their papers, the locked core, the
    judge's verdicts, the coding run's record and, given rows, the authors' corrections."""
    base = tmp_path.as_posix()
    sums = []
    for n in numbers:
        path = os.path.join(base, "texts", str(n), "%d.md" % n)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(PAPER) + "\n")
        with open(path, "rb") as fh:
            sums.append([n, "%d/%d.md" % (n, n), 1, hashlib.sha256(fh.read()).hexdigest()])
    with open(os.path.join(base, "sums.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["number", "file", "bytes", "sha256"])
        w.writerows(sums)
    steps = {5: "3", 6: "2"}
    with open(os.path.join(base, "core.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["number", "step", "stratum", "year"])
        for n in numbers:
            w.writerow([n, steps[n], "end-to-end", 2024])
    with open(os.path.join(base, "core-lock.json"), "w", encoding="utf-8") as fh:
        json.dump({"core_sha256": core_digest([(n, steps[n]) for n in numbers])}, fh)
    folder = os.path.join(base, "responses")
    os.makedirs(folder)
    runs = []
    for n in with_responses:
        text = response(n, (blocks or {}).get(n) or (end_to_end_blocks() if n == 6
                                                        else plain_blocks()))
        path = os.path.join(folder, "response-%04d.md" % n)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        with open(path, "rb") as fh:
            runs.append({"number": n, "status": "finished",
                         "response_sha256": runs_sha or hashlib.sha256(fh.read()).hexdigest()})
    with open(os.path.join(base, "coding-runs.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["number", "status", "response_sha256"])
        w.writeheader()
        w.writerows(runs)
    fields = ["number", "id", "question", "verdict", "disputed", "units", "reason",
              "proposed_answer", "proposed_fields", "proposed_evidence", "proposed_note"]
    with open(os.path.join(base, "verdicts.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, restval="")
        w.writeheader()
        w.writerows(VERDICTS)
    repo = REPO.replace("\\", "/")
    config = os.path.join(base, "core-gather.toml")
    with open(config, "w", encoding="utf-8") as fh:
        fh.write('[inputs]\nspec = "%s/configs/core-coding.toml"\nmap = "%s/configs/map.toml"\n'
                 'core = "%s/core.csv"\ncore_lock = "%s/core-lock.json"\ntexts = "%s/texts"\n'
                 'md_checksums = "%s/sums.csv"\nresponses = "%s/responses"\n'
                 'verdicts = "%s/verdicts.csv"\nruns = "%s/coding-runs.csv"\n'
                 % (repo, repo, base, base, base, base, base, base, base))
        if corrections is not None:
            with open(os.path.join(base, "corrections.csv"), "w", encoding="utf-8",
                      newline="") as out:
                w = csv.writer(out)
                w.writerow(cg.CORRECTION_FIELDS)
                w.writerows(corrections)
            fh.write('corrections = "%s/corrections.csv"\n' % base)
        fh.write('[outputs]\n' + "".join('%s = "%s/out/%s"\n' % (k, base, f) for k, f in [
            ("coded", "coded-studies.csv"), ("answers", "core-answers.csv"),
            ("baselines", "core-baselines.csv"), ("claims", "core-study-claims.csv"),
            ("transfer_tests", "core-transfer-tests.csv"), ("runs", "core-coding-runs.csv"),
            ("report", "gather.md"), ("quotes", "private/quotes.csv")]))
    return config


def run(config, monkeypatch):
    monkeypatch.setattr("sys.argv", ["core_gather", "--config", config])
    cg.main()


def rows(tmp_path, name):
    with open(os.path.join(tmp_path, "out", name), encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def test_the_fixture_responses_pass_the_checks(tmp_path):
    from src import fulltext
    path = os.path.join(tmp_path, "5.md")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(PAPER) + "\n")
    paper = fulltext.load(path)
    for blocks in (plain_blocks(), end_to_end_blocks()):
        assert cb.check_response(SPEC, paper, blocks) == []


def test_each_study_is_one_row_and_each_answer_one_line_with_its_verdict(tmp_path,
                                                                        monkeypatch):
    run(build(tmp_path), monkeypatch)
    studies = {int(r["number"]): r for r in rows(tmp_path, "coded-studies.csv")}
    assert sorted(studies) == [5, 6]
    six = studies[6]
    assert six["role"] == "end-to-end" and six["policy_role"] == "end-to-end"
    assert six["step"] == "2" and six["year"] == "2024" and six["coder"].startswith("Qwen")
    assert six["baselines"] == "1" and six["transfer_tests"] == "1" and six["q_shop"] == "1"
    assert six["algorithm_name"] == "proximal policy optimization"
    assert studies[5]["role"] == "not-stated" and studies[5]["baselines"] == "none"
    assert all(q.name in six for q in SPEC.questions.values())
    assert all(name in six for name in SPEC.derived)
    answers = rows(tmp_path, "core-answers.csv")
    by = {(int(r["number"]), r["id"], r["field"]): r for r in answers}
    assert len([r for r in answers if r["number"] == "5" and r["field"] == ""]) == 76
    assert by[(6, "A01", "")]["verdict"] == "supported" and by[(5, "A01", "")]["verdict"] == "none"
    q01 = by[(6, "Q01", "")]
    assert q01["verdict"] == "partly" and q01["judge_value"] == "0.5" and q01["pages"] == "1"
    assert q01["quote_sha256"] == hashlib.sha256(
        "gives its jobs, machines, eligible machines and processing times".encode()).hexdigest()
    assert by[(6, "B08", "")]["verdict"] == "partly" and by[(6, "B08", "")]["judge_value"] == ""
    assert by[(6, "D07.1", "")]["judge_value"] == ""
    assert by[(6, "D07.1", "kind")]["judge_value"] == "metaheuristic"
    assert by[(6, "D07.1", "run")]["judge_value"] == "copied"
    assert by[(6, "D07.1", "time_limit")]["value"] == "not-applicable"
    baselines = rows(tmp_path, "core-baselines.csv")
    assert [(r["number"], r["item"], r["baseline"], r["kind"], r["run"], r["verdict"])
            for r in baselines] == [("6", "1", "SPT and MWKR rules", "dispatching-rule",
                                     "rerun", "not-supported")]
    tests = rows(tmp_path, "core-transfer-tests.csv")
    assert [(r["differs"], r["provenance"], r["mode"]) for r in tests] == [
        ("size", "generated", "unchanged")]
    assert rows(tmp_path, "core-study-claims.csv") == []
    assert [r["number"] for r in rows(tmp_path, "core-coding-runs.csv")] == ["5", "6"]


def test_no_quote_note_or_judge_reason_reaches_a_published_file(tmp_path, monkeypatch):
    run(build(tmp_path), monkeypatch)
    published = ""
    for name in os.listdir(os.path.join(tmp_path, "out")):
        path = os.path.join(tmp_path, "out", name)
        if os.path.isfile(path):
            with open(path, encoding="utf-8-sig") as fh:
                published += fh.read()
    for words in ("single agent selects", "which run once", "twice as large", "quokka",
                  "wombats", "eligible machines and processing", "learns online by"):
        assert words not in published
    with open(os.path.join(tmp_path, "out", "private", "quotes.csv"), encoding="utf-8-sig") as fh:
        quotes = list(csv.DictReader(fh))
    assert any(q["quote"].startswith("We compare against") for q in quotes)
    assert all(q["sha256"] == hashlib.sha256(q["quote"].encode()).hexdigest() for q in quotes)


def test_the_report_counts_the_studies_items_and_verdicts(tmp_path, monkeypatch):
    run(build(tmp_path), monkeypatch)
    with open(os.path.join(tmp_path, "out", "gather.md"), encoding="utf-8") as fh:
        text = fh.read()
    assert "2 studies gathered" in text and "| baseline | 1 | 1 |" in text
    assert "## The judge's verdicts" in text and "## Inputs" in text


def test_a_study_read_in_full_with_no_response_is_refused(tmp_path, monkeypatch):
    with pytest.raises(SystemExit, match="no response for the studies read in full 6"):
        run(build(tmp_path, with_responses=(5,)), monkeypatch)
    assert not os.path.exists(os.path.join(tmp_path, "out", "coded-studies.csv"))


def test_a_response_with_a_problem_or_another_sha_is_refused(tmp_path, monkeypatch):
    broken = end_to_end_blocks()
    del broken["C11"]
    with pytest.raises(SystemExit, match="C11: no answer yet"):
        run(build(tmp_path, blocks={6: broken}), monkeypatch)
    with pytest.raises(SystemExit, match="differs from its SHA-256"):
        run(build(tmp_path / "again", runs_sha="0" * 64), monkeypatch)


def test_copied_wording_in_a_published_text_is_refused(tmp_path, monkeypatch):
    copied = end_to_end_blocks()
    copied["D07.1"] = block("D07.1", "baseline", "the dispatching rules SPT and MWKR which run once",
                            [(1, "We compare against the dispatching rules SPT and MWKR, which "
                                 "run once.")],
                            fields={"kind": "dispatching-rule", "run": "rerun",
                                    "time_limit": "not-applicable"})
    with pytest.raises(SystemExit, match="D07.1"):
        run(build(tmp_path, blocks={6: copied}), monkeypatch)


FIX = "Moayad Alnammi, 2026-10-22"


def test_the_authors_corrections_are_laid_over_the_coders_answers(tmp_path, monkeypatch):
    fixes = [[5, "A01", "policy_role", "end-to-end", "0", FIX, "one action picks the machine"],
             [5, "B04", "steering_action", "not-applicable", "", FIX, "follows from the role"],
             [5, "B05", "steered_method", "not-applicable", "", FIX, "follows from the role"]]
    run(build(tmp_path, corrections=fixes), monkeypatch)
    five = {r["number"]: r for r in rows(tmp_path, "coded-studies.csv")}["5"]
    assert (five["role"], five["policy_role"], five["steering_action"]) == (
        "end-to-end", "end-to-end", "not-applicable")
    by = {(r["number"], r["id"], r["field"]): r for r in rows(tmp_path, "core-answers.csv")}
    a01 = by[("5", "A01", "")]
    assert (a01["value"], a01["verdict"], a01["authors_value"]) == ("not-stated", "none",
                                                                     "end-to-end")
    assert by[("5", "B04", "")]["value"] == "not-stated"
    assert by[("6", "A01", "")]["authors_value"] == ""
    with open(os.path.join(tmp_path, "out", "gather.md"), encoding="utf-8") as fh:
        text = fh.read()
    line = next(x for x in text.splitlines() if "A01 policy_role" in x)
    assert "not-stated" in line and line.rstrip().endswith("end-to-end |")
    assert "corrections (corrections.csv)" in text


def test_corrections_that_break_the_schemes_rules_are_refused(tmp_path, monkeypatch):
    # The role alone: B04 and B05 apply only to a steering policy.
    fixes = [[5, "A01", "policy_role", "end-to-end", "", FIX, "the role alone"]]
    with pytest.raises(SystemExit, match="B04: the question does not apply"):
        run(build(tmp_path, corrections=fixes), monkeypatch)
    assert not os.path.exists(os.path.join(tmp_path, "out", "coded-studies.csv"))


def test_a_correction_the_question_does_not_allow_or_of_no_study_is_refused(tmp_path,
                                                                           monkeypatch):
    with pytest.raises(SystemExit, match="line 2: A01"):
        run(build(tmp_path, corrections=[[6, "A01", "policy_role", "end to end", "", FIX, "x"]]),
            monkeypatch)
    with pytest.raises(SystemExit, match="no response: 7"):
        run(build(tmp_path / "again",
                  corrections=[[7, "A01", "policy_role", "end-to-end", "", FIX, "x"]]),
            monkeypatch)


def test_with_inputs_missing_nothing_is_written(tmp_path, monkeypatch):
    # As in a clone of the repository alone: no responses and no papers' markdown.
    config = build(tmp_path)
    shutil.rmtree(os.path.join(tmp_path, "responses"))
    shutil.rmtree(os.path.join(tmp_path, "texts"))
    out = os.path.join(tmp_path, "out")
    os.makedirs(out)
    published = os.path.join(out, "coded-studies.csv")
    before = b"number,role\r\n6,end-to-end\r\n"
    with open(published, "wb") as fh:
        fh.write(before)
    with pytest.raises(SystemExit) as refused:
        run(config, monkeypatch)
    message = str(refused.value)
    assert message.startswith("Nothing was written: missing input")
    assert "texts (" in message and "responses (" in message
    with open(published, "rb") as fh:
        assert fh.read() == before
    assert os.listdir(out) == ["coded-studies.csv"]


def test_an_empty_responses_folder_is_refused(tmp_path, monkeypatch):
    with pytest.raises(SystemExit) as refused:
        run(build(tmp_path, with_responses=()), monkeypatch)
    message = str(refused.value)
    assert "responses (" in message and "texts (" not in message
    assert not os.path.exists(os.path.join(tmp_path, "out"))
