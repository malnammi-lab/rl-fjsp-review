"""Tests for the checker of the core's answers (runners/core_check.py): its --tool mode, as
the acquisition tool's agent loop calls it, and its check of every response (--config)."""

import csv
import hashlib
import io
import json
import os
import re
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

import core_check as cc  # noqa: E402

BAR = "-" * 48
PAPER = [
    "{0}" + BAR,
    "# **A learning scheduler**",
    "We propose a deep reinforcement learning method in which a single agent selects an "
    "operation and a machine at each decision point.",
    "{1}" + BAR,
    "## 5. Experiments",
    "We compare against the dispatching rules SPT and MWKR, which run once.",
    "## References",
    "[1] A reference.",
]
ROLE = ("## A01 policy_role\nanswer: end-to-end\n"
        'evidence: {0} "a single agent selects an operation and a machine"\nnote:')
BASELINES = ('## D07 baselines\nanswer: 1\n'
             'evidence: {1} "We compare against the dispatching rules SPT and MWKR"\nnote:')


def write_paper(folder, number=5):
    path = os.path.join(folder, str(number), "%d.md" % number)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(PAPER) + "\n")
    return path


def ask(monkeypatch, capsys, request, paper=None):
    argv = ["core_check", "--tool"] + (["--paper", paper] if paper else [])
    monkeypatch.setattr("sys.argv", argv)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(request)))
    cc.main()
    return json.loads(capsys.readouterr().out)


def test_every_answer_carries_the_contract_and_the_checkers_fingerprint(monkeypatch, capsys):
    out = ask(monkeypatch, capsys, {"op": "fingerprint"})
    assert out["ok"] and out["contract"] == cc.CONTRACT and out["result"] == {}
    assert out["fingerprint"] == cc.fingerprint() and len(out["fingerprint"]) == 64
    out = ask(monkeypatch, capsys, {"op": "files"})
    assert out["result"]["files"] == cc.FILES


def test_the_fingerprint_covers_the_files_the_tool_copies(tmp_path):
    for name in cc.FILES:
        target = os.path.join(tmp_path, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(os.path.join(REPO, name), "rb") as src, open(target, "wb") as dst:
            dst.write(src.read())
    assert cc.fingerprint(str(tmp_path)) == cc.fingerprint()
    with open(os.path.join(tmp_path, "configs", "core-coding.toml"), "ab") as fh:
        fh.write(b"\n")
    assert cc.fingerprint(str(tmp_path)) != cc.fingerprint()


def test_the_agents_instructions_have_their_parts_and_name_every_tool():
    with open(os.path.join(REPO, "configs", "core-coding-prompt.md"), encoding="utf-8") as fh:
        parts = re.split(r"(?m)^## ", fh.read())[1:]
    assert [p.splitlines()[0].strip() for p in parts] == ["Shared", "Lead", "Section agent",
                                                          "Without tools"]
    shared, section, plain = parts[0], parts[2], parts[3]
    # The system message is the same for every paper, so the server computes it once.
    assert not any(name in shared for name in ("{number}", "{questions}", "{task}"))
    assert "{questions}" in section and "{task}" in section
    assert "{number}" in plain and "{questions}" in plain
    with open(os.path.join(REPO, "configs", "core-coding-tools.json"), encoding="utf-8") as fh:
        names = [t["function"]["name"] for t in json.load(fh)]
    assert names == ["outline", "search", "read", "check_quote", "write_block", "get_block",
                     "check_response", "delegate", "finish"]
    assert all("`%s(" % name in shared for name in names)


def test_the_judges_instructions_have_their_parts_and_a_valid_form_of_reply():
    with open(os.path.join(REPO, "configs", "core-judge-prompt.md"), encoding="utf-8") as fh:
        parts = re.split(r"(?m)^## ", fh.read())[1:]
    assert [p.splitlines()[0].strip() for p in parts] == ["Shared", "The paper", "Block unit",
                                                          "Paper unit"]
    shared, paper, block, quiet = parts
    names = ("{unit}", "{cited}", "{rules}", "{blocks}")
    # The opening (the instructions, the general rules and the paper) is the same for every
    # unit of a paper, so the server computes it once.
    assert not any(name in shared + paper for name in names)
    assert "{paper}" in paper and "{paper}" not in shared + block + quiet
    assert all(name in block for name in names)
    assert all(name in quiet for name in ("{unit}", "{rules}", "{blocks}"))
    assert "{cited}" not in quiet
    # Each unit's form of reply is one JSON object: a list of verdicts.
    for part in (block, quiet):
        form = re.search(r"(?m)^    \{\"unit\".*?\]\}$", part, re.S).group(0)
        reply = json.loads(form.replace("{unit}", "7001"))
        assert reply["unit"] == 7001 and len(reply["verdicts"]) == 2
        assert {v["verdict"] for v in reply["verdicts"]} <= {
            "supported", "partly", "not-supported", "cannot-judge"}


def test_questions_and_the_scheme_need_no_paper(monkeypatch, capsys):
    out = ask(monkeypatch, capsys, {"op": "questions", "select": "C01 to C03"})
    assert [q["id"] for q in out["result"]["questions"]] == ["C01", "C02", "C03"]
    assert out["result"]["questions"][0] == {"id": "C01", "name": "action_space",
                                             "section": "C"}
    text = ask(monkeypatch, capsys, {"op": "scheme", "sections": ["C"]})["result"]["text"]
    assert "### General rules" in text and "### Answers, evidence and blocks" in text
    assert "#### C01 `action_space`" in text and "#### D01" not in text
    assert "### Coverage" not in text and "Part A, the map" not in text
    text = ask(monkeypatch, capsys, {"op": "scheme", "sections": ["A"]})["result"]["text"]
    assert "| A01 | `policy_role` |" in text and "### Part A, the map" in text
    assert "### `policy_role` (one code, quoted)" in text
    # Part A is read from the full text: its words for the title and abstract become the
    # paper's, and its rule on quotes gives way to section A's.
    part_a = text.split("### Part A, the map", 1)[1]
    assert "abstract" not in part_a.lower() and "the record states" not in part_a
    assert "from its full text" in part_a and cc.QUOTES_A in part_a
    assert "**Only what the paper states.** When the paper does not say what an axis" in part_a
    text = ask(monkeypatch, capsys, {"op": "scheme"})["result"]["text"]
    assert "#### B01" in text and "#### Q07" in text and "### Part A, the map" in text
    out = ask(monkeypatch, capsys, {"op": "scheme", "sections": ["Z"]})
    assert not out["ok"] and "no section Z" in out["error"]


def test_the_papers_tools_answer_from_the_paper(tmp_path, monkeypatch, capsys):
    paper = write_paper(tmp_path)
    out = ask(monkeypatch, capsys, {"op": "search", "pattern": "dispatching"}, paper)
    assert [(h["page"], h["line"]) for h in out["result"]["hits"]] == [(1, 6)]
    out = ask(monkeypatch, capsys, {"op": "read", "page": 1}, paper)
    assert [r["line"] for r in out["result"]["lines"]] == [5, 6]
    out = ask(monkeypatch, capsys, {"op": "outline"}, paper)
    assert [h["heading"] for h in out["result"]["headings"]] == ["A learning scheduler",
                                                                  "5. Experiments"]
    out = ask(monkeypatch, capsys, {"op": "check_quote", "page": 0,
                                    "quote": "a single agent selects"}, paper)
    assert out["result"]["found"]
    out = ask(monkeypatch, capsys, {"op": "excerpt", "pages": [1]}, paper)
    assert "SPT and MWKR" in out["result"]["pages"]["1"]
    every = ask(monkeypatch, capsys, {"op": "excerpt", "pages": "all"}, paper)["result"]["pages"]
    assert sorted(every) == ["0", "1"] and "A reference" not in every["1"]
    body = ask(monkeypatch, capsys, {"op": "excerpt", "body": True}, paper)["result"]["text"]
    assert body.startswith("{0}") and "A reference" not in body


def test_a_block_is_kept_or_refused(tmp_path, monkeypatch, capsys):
    paper = write_paper(tmp_path)
    out = ask(monkeypatch, capsys, {"op": "check_block", "block": ROLE, "blocks": {}}, paper)
    assert out["result"] == {"id": "A01", "kept": True, "problems": []}
    wrong = ROLE.replace("end-to-end", "end to end")
    out = ask(monkeypatch, capsys, {"op": "check_block", "block": wrong, "blocks": {}}, paper)
    assert not out["result"]["kept"]
    assert out["result"]["problems"][0]["what"] == "the answer is not one of the question's codes"
    steering = ('## B04 steering_action\nanswer: dispatching-rule\n'
                'evidence: {1} "the dispatching rules SPT and MWKR"\nnote:')
    out = ask(monkeypatch, capsys, {"op": "check_block", "block": steering,
                                    "blocks": {"A01": ROLE}}, paper)
    assert out["result"]["kept"] and out["result"]["problems"][0]["between"]


def test_the_response_check_takes_a_scope_as_text(tmp_path, monkeypatch, capsys):
    paper = write_paper(tmp_path)
    out = ask(monkeypatch, capsys, {"op": "check_response", "scope": "D07",
                                    "blocks": {"D07": BASELINES}}, paper)
    assert [(p["id"], p["what"]) for p in out["result"]["problems"]] == [
        ("D07", "item blocks missing for the count 1: D07.1")]
    out = ask(monkeypatch, capsys, {"op": "assemble", "blocks": {"D07": BASELINES, "A01": ROLE},
                                    "header": ["# Record 5"]})
    assert out["result"]["text"].index("## A01") < out["result"]["text"].index("## D07")


def test_the_judge_gets_a_responses_blocks_and_each_questions_rules(monkeypatch, capsys):
    item = ('## D07.1 baseline\nanswer: SPT, MWKR\nkind: dispatching-rule\nrun: rerun\n'
            'time_limit: not-applicable\n'
            'evidence: {1} "We compare against the dispatching rules SPT and MWKR"\nnote:')
    response = "# Record 5\n\n" + BASELINES + "\n\n" + item + "\n\n" + ROLE + "\n"
    blocks = ask(monkeypatch, capsys, {"op": "blocks", "response": response})["result"]["blocks"]
    assert [(b["id"], b["question"], b["pages"]) for b in blocks] == [
        ("A01", "A01", [0]), ("D07", "D07", [1]), ("D07.1", "D07", [1])]
    assert blocks[0]["text"] == ROLE
    rules = ask(monkeypatch, capsys,
                {"op": "rules", "ids": ["A01", "B05", "Q07"]})["result"]["rules"]
    assert rules["B05"].startswith("#### B05 `steered_method` (a list)")
    assert "#### B06" not in rules["B05"]
    assert rules["Q07"].startswith("#### Q07 ") and "### Coverage" not in rules["Q07"]
    assert rules["A01"].startswith("Question A01 is Part A's axis `policy_role`")
    assert "**The paper's own method.**" in rules["A01"]
    assert "### `policy_role` (one code, quoted)" in rules["A01"]
    assert "### `coordination`" not in rules["A01"]
    assert "abstract" not in rules["A01"].lower()
    out = ask(monkeypatch, capsys, {"op": "rules", "ids": ["Z99"]})
    assert not out["ok"] and "no question Z99" in out["error"]


def test_both_models_read_the_role_of_a_policy_that_sets_quantities_beside_a_rule(monkeypatch,
                                                                                  capsys):
    # Part B: the quantities a policy sets beside a fixed rule that builds the schedule are
    # an auxiliary part of a steering-heuristic policy. The clause reaches the coding agent
    # (the scheme) and the judge (A01's rules), while Part A's own text, under which the map
    # was coded, stays as it was.
    clause = "the quantities to produce, release or order while a fixed rule or heuristic"
    text = ask(monkeypatch, capsys, {"op": "scheme", "sections": ["A"]})["result"]["text"]
    assert clause in text.split("### Part A, the map", 1)[1]
    rules = ask(monkeypatch, capsys, {"op": "rules", "ids": ["A01"]})["result"]["rules"]
    assert clause in rules["A01"] and "abstract" not in rules["A01"].lower()
    with open(cc.SCHEME, encoding="utf-8") as fh:
        assert clause not in cc.part(fh.read(), "## Part A, the map")


def test_a_request_that_cannot_be_answered_is_an_error_not_a_crash(monkeypatch, capsys):
    out = ask(monkeypatch, capsys, {"op": "nonsense"})
    assert not out["ok"] and "unknown operation" in out["error"]
    out = ask(monkeypatch, capsys, {"op": "search", "pattern": "x"})
    assert not out["ok"] and "needs --paper" in out["error"]


def build(tmp_path, response=None, sha=None):
    """A config checking one study's response, with its paper and checksum."""
    base = tmp_path.as_posix()
    texts = os.path.join(base, "texts")
    path = write_paper(texts)
    with open(path, "rb") as fh:
        digest = sha or hashlib.sha256(fh.read()).hexdigest()
    sums = os.path.join(base, "sums.csv")
    with open(sums, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["number", "file", "bytes", "sha256"])
        w.writerow([5, "5/5.md", 1, digest])
    if response is not None:
        os.makedirs(os.path.join(base, "responses"))
        with open(os.path.join(base, "responses", "response-0005.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(response)
    config = os.path.join(base, "core-check.toml")
    repo = REPO.replace("\\", "/")
    with open(config, "w", encoding="utf-8") as fh:
        fh.write('[inputs]\nspec = "%s/configs/core-coding.toml"\nmap = "%s/configs/map.toml"\n'
                 'texts = "%s/texts"\nmd_checksums = "%s/sums.csv"\n'
                 'responses = "%s/responses"\n[outputs]\nreport = "%s/out/check.md"\n'
                 'problems = "%s/out/check-problems.csv"\n'
                 % (repo, repo, base, base, base, base, base))
    return config


def run(config, monkeypatch):
    monkeypatch.setattr("sys.argv", ["core_check", "--config", config])
    cc.main()


def test_every_response_is_checked_and_reported_without_the_papers_words(tmp_path,
                                                                          monkeypatch):
    wrong_quote = ROLE.replace("selects", "chooses")
    config = build(tmp_path, "# Record 5\n\n" + wrong_quote + "\n\n" + BASELINES + "\n")
    run(config, monkeypatch)
    with open(os.path.join(tmp_path, "out", "check-problems.csv"), encoding="utf-8-sig") as fh:
        text = fh.read()
    with open(os.path.join(tmp_path, "out", "check-problems.csv"), encoding="utf-8-sig") as fh:
        rows = [(r["number"], r["id"], r["what"]) for r in csv.DictReader(fh)]
    assert ("5", "A01", "quote 1 is not on page 0 word for word") in rows
    assert ("5", "B01", "no answer yet") in rows
    assert ("5", "D07", "item blocks missing for the count 1: D07.1") in rows
    assert "single agent" not in text and "SPT" not in text
    with open(os.path.join(tmp_path, "out", "check.md"), encoding="utf-8") as fh:
        report = fh.read()
    assert "1 responses checked against their papers: 0 with no problem, 1 with problems" \
        in report


def test_no_response_folder_is_reported_as_nothing_to_check(tmp_path, monkeypatch):
    run(build(tmp_path), monkeypatch)
    with open(os.path.join(tmp_path, "out", "check.md"), encoding="utf-8") as fh:
        assert "No response folder yet" in fh.read()


def test_a_paper_that_differs_from_its_checksum_is_refused(tmp_path, monkeypatch):
    config = build(tmp_path, "# Record 5\n", sha="0" * 64)
    with pytest.raises(SystemExit, match="differs from its checksum"):
        run(config, monkeypatch)
