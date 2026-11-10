"""Tests for the checks of the core's answers (src/coreblocks.py), on the real questions
(configs/core-coding.toml, configs/map.toml) and a small paper of two pages."""

import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import coreblocks as cb  # noqa: E402
from src import fulltext as ft  # noqa: E402

SPEC = os.path.join(REPO, "configs", "core-coding.toml")
MAP = os.path.join(REPO, "configs", "map.toml")
BAR = "-" * 48
PAPER = [
    "{0}" + BAR,
    "# **A learning scheduler**",
    "We propose a deep reinforcement learning method in which a single agent selects an "
    "operation and a machine at each decision point.",
    "The policy is trained with proximal policy optimization and a graph neural network "
    "encoder.",
    "{1}" + BAR,
    "## 5. Experiments",
    "Experiments use the Brandimarte instances mk01 to mk10.",
    "We compare against the dispatching rules SPT and MWKR, which run once, and a genetic "
    "algorithm given 60 seconds.",
    "The proposed method outperforms all dispatching rules on every instance.",
    "## References",
    "[1] A reference.",
]


def block(head, answer, *evidence, note="", fields=None):
    lines = ["## " + head, "answer: " + answer]
    lines += ["%s: %s" % (k, v) for k, v in (fields or {}).items()]
    lines += ['evidence: {%d} "%s"' % (page, quote) for page, quote in evidence]
    return "\n".join(lines + ["note: " + note])


ROLE = block("A01 policy_role", "end-to-end",
             (0, "a single agent selects an operation and a machine at each decision point"))
LEARNER = block("A04 learner_depth", "deep", (0, "a deep reinforcement learning method"))
PPO = block("B07 algorithm", "ppo", (0, "trained with proximal policy optimization"))
VALUE_BASED = block("A06 training_algorithm_family", "value-based",
                    (0, "trained with proximal policy optimization"))
BASELINES = block("D07 baselines", "2", (1, "We compare against the dispatching rules SPT and MWKR"))
RULES = block("D07.1 baseline", "SPT, MWKR", (1, "the dispatching rules SPT and MWKR, which run once"),
              fields={"kind": "dispatching-rule", "run": "rerun", "time_limit": "not-applicable"})
GA = block("D07.2 baseline", "genetic algorithm", (1, "a genetic algorithm given 60 seconds"),
           fields={"kind": "metaheuristic", "run": "rerun", "time_limit": "stated"},
           note="60 s")


@pytest.fixture(scope="module")
def spec():
    return cb.load_spec(SPEC, MAP)


@pytest.fixture
def paper(tmp_path):
    path = os.path.join(tmp_path, "5.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(PAPER) + "\n")
    return ft.load(path)


def kept(*texts):
    out = {}
    for text in texts:
        b, _ = cb.parse_block(text)
        out[b.id] = b
    return out


def whats(problems):
    return [(p["id"], p["what"]) for p in problems]


def test_the_spec_has_part_bs_questions_groups_rules_and_derived_columns(spec):
    assert len(spec.questions) == 76
    assert spec.questions["A01"].kind == "code" and spec.questions["A02"].kind == "codes"
    assert "not-applicable" in spec.questions["A03"].codes
    assert spec.questions["A01"].special == ("not-stated",)
    assert spec.questions["A07"].special == ()
    assert spec.by_name["algorithm"].qid == "B07"
    assert sorted(spec.groups) == ["baseline", "claim", "transfer_test"]
    assert sorted(spec.groups["baseline"].fields) == ["kind", "run", "time_limit"]
    # Six rules of Part B and Part A's five implications.
    assert len(spec.rules) == 11
    assert sorted(spec.derived) == ["algorithm_family", "multi_objective", "policy_update"]


def test_select_reads_ids_ranges_and_sections(spec):
    assert cb.select(spec, "C01 to C03, D07") == ["C01", "C02", "C03", "D07"]
    assert cb.select(spec, "section E") == ["E01", "E02", "E03"]
    assert cb.select(spec, "Q07 and A01") == ["A01", "Q07"]
    for bad in ("Z99", "C03 to C01", ""):
        with pytest.raises(ValueError):
            cb.select(spec, bad)


def test_a_block_is_read_line_by_line():
    b, problems = cb.parse_block(GA)
    assert problems == []
    assert (b.id, b.qid, b.item, b.name) == ("D07.2", "D07", 2, "baseline")
    assert b.fields == {"kind": "metaheuristic", "run": "rerun", "time_limit": "stated"}
    assert b.evidence == [(1, "a genetic algorithm given 60 seconds")] and b.note == "60 s"
    assert cb.parse_block("answer: ppo")[0] is None
    assert [w for w, _ in cb.parse_block("## B07 algorithm\nnote:")[1]] == ["no answer line"]
    _, problems = cb.parse_block('## B07 algorithm\nanswer: ppo\nanswer: sac\n'
                                 'evidence: 6 "x"\nfree text')
    assert [w for w, _ in problems] == [
        "two answer lines", 'an evidence line not in the form evidence: {N} "quote"',
        "a line that is not 'answer:', 'evidence:', 'note:' or a field"]


def test_values_take_the_questions_kind(spec):
    check = cb.check_value
    assert check("code", "PPO", ("ppo", "sac")) == ("ppo", [])
    assert check("code", "proximal", ("ppo",))[1][0][0] == "the answer is not one of the question's codes"
    assert check("codes", "sac | ppo", ("ppo", "sac")) == (("ppo", "sac"), [])
    assert check("codes", "none|transport", ("none", "transport"), ("none",))[1] == [("none stands alone", "")]
    assert check("codes", "not-stated", ("a",), (), ("not-stated",)) == ("not-stated", [])
    assert check("code", "not-reported", ("a",), (), ("not-stated",))[1][0][0] == \
        "not-reported is not an answer this question allows"
    assert check("number", "12")[0] == "12" and check("number", "about 12")[0] is None
    assert check("text", "one two three", words=2)[1] == [("3 words; at most 2", "")]
    assert check("level", "l3")[0] == "L3" and check("score", "0.5")[0] == "0.5"
    assert check("count", "none")[0] == "none" and check("count", "3", most_items=8)[0] == 3
    assert check("count", "9", most_items=8)[1] == [("9 items; at most 8", "")]
    # A code that is also a special answer's word is a code where the question lists it.
    assert check("code", "not-applicable", ("operation", "not-applicable")) == ("not-applicable", [])


def test_a_block_that_follows_the_scheme_has_no_problem(spec, paper):
    for text in (ROLE, LEARNER, PPO, BASELINES, RULES, GA):
        b, problems = cb.check_block(spec, paper, text, kept(ROLE, PPO))
        assert problems == [], b.id


def test_a_quote_not_word_for_word_gets_the_closest_passage_in_its_detail_only(spec, paper):
    text = block("A01 policy_role", "end-to-end",
                 (0, "a single agent chooses an operation and a machine at each decision point"))
    _, problems = cb.check_block(spec, paper, text)
    assert whats(problems) == [("A01", "quote 1 is not on page 0 word for word")]
    assert "selects an operation" in problems[0]["detail"]
    assert cb.refused(problems)


def test_a_quote_from_another_page_is_located(spec, paper):
    text = block("A04 learner_depth", "deep", (1, "a deep reinforcement learning method"))
    _, problems = cb.check_block(spec, paper, text)
    assert whats(problems) == [("A04", "quote 1 is not on page 1 but on page 0")]


def test_an_answer_needing_a_quote_without_one_is_refused(spec, paper):
    _, problems = cb.check_block(spec, paper, block("B07 algorithm", "ppo"))
    assert whats(problems) == [("B07", "no evidence line: quote the paper, one to three "
                                       "quotes")]


def test_not_stated_needs_a_note_listing_what_was_searched(spec, paper):
    _, problems = cb.check_block(spec, paper, block("C04 wait_action", "not-stated"))
    assert whats(problems) == [("C04", "a not-stated answer needs a note that begins "
                                       "'searched' and lists what was searched")]
    _, problems = cb.check_block(spec, paper, block("C04 wait_action", "not-stated",
                                                    note="searched: wait, idle, delay"))
    assert problems == []


def test_a_question_that_does_not_apply_is_a_warning_between_questions(spec, paper):
    text = block("B04 steering_action", "dispatching-rule",
                 (1, "We compare against the dispatching rules SPT and MWKR"))
    _, problems = cb.check_block(spec, paper, text, kept(ROLE))
    assert whats(problems) == [("B04", "the question does not apply here (policy_role is "
                                       "end-to-end): answer not-applicable")]
    assert problems[0]["between"] and not cb.refused(problems)
    text = block("B04 steering_action", "not-applicable", note="the policy is end to end")
    assert cb.check_block(spec, paper, text, kept(ROLE))[1] == []


def test_a_rule_between_questions_is_reported_on_the_question_it_names(spec, paper):
    _, problems = cb.check_block(spec, paper, VALUE_BASED, kept(PPO))
    assert [p["id"] for p in problems] == ["A06"] and problems[0]["between"]
    assert "REINFORCE, PPO and TRPO are policy gradient" in problems[0]["what"]


def test_an_items_fields_are_checked(spec, paper):
    no_limit = RULES.replace("time_limit: not-applicable\n", "")
    assert whats(cb.check_block(spec, paper, no_limit)[1]) == [("D07.1", "no time_limit line")]
    bad_kind = RULES.replace("kind: dispatching-rule", "kind: rule")
    _, problems = cb.check_block(spec, paper, bad_kind)
    assert problems[0]["what"].startswith("the kind is not one of") and problems[0]["detail"] == "rule"
    beyond = RULES.replace("D07.1", "D07.9")
    assert ("D07.9", "D07's items are numbered 1 to 8") in whats(cb.check_block(spec, paper, beyond)[1])


def test_a_text_answer_copying_eight_words_of_the_paper_is_refused(spec, paper):
    text = block("C13 model_summary", "policy is trained with proximal policy optimization "
                                      "and a graph neural network encoder",
                 (0, "a graph neural network encoder"))
    _, problems = cb.check_block(spec, paper, text)
    assert whats(problems) == [("C13", "the answer copies 8 or more words of the paper in a "
                                       "row: write it in your own words")]
    assert "proximal policy optimization" in problems[0]["detail"]


def test_the_response_check_finds_missing_answers_items_and_rules(spec, paper):
    claim = block("D19.1 claim", "beats-dispatching-rules",
                  (1, "outperforms all dispatching rules on every instance"))
    blocks = {"A01": ROLE, "A04": LEARNER, "A06": VALUE_BASED, "B07": PPO,
              "D07": BASELINES, "D07.1": RULES,
              "D19": block("D19 claims", "2", (1, "outperforms all dispatching rules")),
              "D19.1": claim, "D19.2": claim.replace("D19.1", "D19.2")}
    problems = whats(cb.check_response(spec, paper, blocks))
    assert ("B01", "no answer yet") in problems and ("A01", "no answer yet") not in problems
    assert ("D07", "item blocks missing for the count 2: D07.2") in problems
    assert ("D19", "an item answer given twice: beats-dispatching-rules") in problems
    assert sum(1 for i, w in problems if i == "A06" and "policy gradient" in w) == 1
    # A section agent's check covers its own questions only.
    assert whats(cb.check_response(spec, paper, blocks, ["D07"])) == [
        ("D07", "item blocks missing for the count 2: D07.2")]


def test_no_problems_what_quotes_the_paper(spec, paper):
    blocks = {"A01": block("A01 policy_role", "a single agent selects an operation",
                           (0, "a single agent selects operations")),
              "C13": block("C13 model_summary", "policy is trained with proximal policy "
                                                "optimization and a graph neural network",
                           (0, "a graph neural network encoder"))}
    for p in cb.check_response(spec, paper, blocks):
        assert "selects" not in p["what"] and "proximal" not in p["what"], p


def test_a_response_is_assembled_in_part_bs_order(spec):
    text = cb.assemble(spec, {"D07.2": GA, "D07.1": RULES, "B07": PPO, "D07": BASELINES,
                              "A01": ROLE}, ["# Record 5"])
    heads = [line for line in text.splitlines() if line.startswith("#")]
    assert heads == ["# Record 5", "## A01 policy_role", "## B07 algorithm",
                     "## D07 baselines", "## D07.1 baseline", "## D07.2 baseline"]
    header, blocks, problems = cb.split_response(text + "\n" + PPO)
    assert header == ["# Record 5", ""] and list(blocks)[:2] == ["A01", "B07"]
    assert whats(problems) == [("B07", "a block given twice; the first is kept")]


def test_the_derived_columns_follow_their_sources(spec):
    assert cb.derive(spec, {"algorithm": "ppo", "objective": ("makespan", "tardiness")}) == {
        "algorithm_family": "policy-gradient", "policy_update": "on-policy",
        "multi_objective": "yes"}
    assert cb.derive(spec, {"algorithm": "not-stated", "objective": ("makespan",)}) == {
        "algorithm_family": "not-stated", "policy_update": "not-stated",
        "multi_objective": "no"}
