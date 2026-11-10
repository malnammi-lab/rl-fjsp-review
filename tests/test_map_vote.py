"""Tests for the map's vote (src/mapcodes.py and runners/map_vote.py): the scheme's rules
applied to each model's codes, the majority per cell, the rules again after the vote, the
models' agreement, and the runner end to end (protocol, Two tiers)."""

import csv
import os
import re
import sys
import tomllib

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import mapcodes as mc  # noqa: E402
import map_vote  # noqa: E402
from test_coding_scheme import bullet, sections  # noqa: E402

AXES = mc.load_axes(os.path.join(REPO, "configs", "map.toml"))
AXIS = {a.name: a for a in AXES}
MODELS = ["qwen38", "gemma26", "glimmer30"]

# One record as a model codes it: a deep, end-to-end study that every rule already fits.
BASE = {
    "policy_role": "end-to-end", "coordination": "single-agent",
    "scheduling_action": "operation", "learner_depth": "deep",
    "deep_architecture": "graph-neural-network", "training_algorithm_family": "policy-gradient",
    "hybridization": "none", "state_content": "operations|machines",
    "state_encoding": "disjunctive-graph", "dynamic_events": "none", "objective": "makespan",
    "constraints": "none", "instances": "public-benchmark", "domain": "manufacturing",
    "readiness_claim": "none",
}
TABULAR = {"learner_depth": "tabular", "deep_architecture": "not-applicable",
           "training_algorithm_family": "value-based"}
FIELDS = (["number"] + [a.name for a in AXES]
          + ["policy_role_evidence", "learner_depth_evidence", "readiness_claim_evidence"]
          + list(mc.META))


def text(**changes):
    return {**BASE, **changes}


def cells(**changes):
    """BASE with `changes`, read as the runner reads a coding file."""
    out = {}
    for axis in AXES:
        out[axis.name], problem = mc.parse_cell(axis, text(**changes)[axis.name])
        assert not problem, (axis.name, problem)
    return out


def rule(name):
    return next(r for r in mc.IMPLICATIONS if r.name == name)


def test_every_rule_reads_and_sets_codes_the_schema_and_the_scheme_hold():
    part_a = sections()
    for r in mc.IMPLICATIONS:
        when, then = AXIS[r.when_axis], AXIS[r.then_axis]
        assert not when.multi, r.name
        assert set(r.when_codes) <= set(when.codes) | {mc.NOT_STATED}, r.name
        assert r.then_code in then.codes + (mc.NOT_STATED,), r.name
        # The scheme states the rule in the bullet of the code it sets.
        stated = bullet(part_a[r.then_axis], r.then_code)
        assert stated is not None, r.name
        for code in r.when_codes:
            assert "`%s`" % code in stated, (r.name, code)
    assert not {r.when_axis for r in mc.IMPLICATIONS} & {r.then_axis for r in mc.IMPLICATIONS}


def test_a_steering_role_has_no_action_and_an_unstated_role_no_stated_action():
    out, changed = mc.imply(cells(policy_role="steering-rules"), AXES)
    assert out["scheduling_action"] == "not-applicable"
    assert [(c[0].name, c[1], c[2], c[3]) for c in changed] == [
        ("steering role: no action", "scheduling_action", "operation", "not-applicable")]
    out, _ = mc.imply(cells(policy_role="not-stated"), AXES)
    assert out["scheduling_action"] == "not-stated"
    assert mc.imply(cells(), AXES) == (cells(), [])


def test_a_tabular_learner_has_discrete_states_and_no_architecture():
    out, changed = mc.imply(cells(learner_depth="tabular", deep_architecture="not-stated",
                                  state_encoding="not-stated"), AXES)
    assert out["deep_architecture"] == ("not-applicable",)
    assert out["state_encoding"] == ("discrete-states",)
    assert {c[0].name for c in changed} == {"non-deep learner: no architecture",
                                            "tabular learner: discrete states"}
    out, _ = mc.imply(cells(learner_depth="non-neural"), AXES)
    assert out["deep_architecture"] == ("not-applicable",)
    assert out["state_encoding"] == ("disjunctive-graph",)
    out, _ = mc.imply(cells(learner_depth="not-stated"), AXES)
    assert out["deep_architecture"] == ("not-stated",)


def test_the_vote_on_a_single_axis():
    role = AXIS["policy_role"]
    assert mc.vote(role, ["end-to-end", "end-to-end", "steering-rules"]) == "end-to-end"
    three = ["end-to-end", "steering-rules", "steering-heuristic"]
    assert mc.vote(role, three) == "not-stated" and mc.no_majority(role, three)
    unstated = ["not-stated", "not-stated", "end-to-end"]
    assert mc.vote(role, unstated) == "not-stated" and not mc.no_majority(role, unstated)


def test_the_vote_on_a_list_axis_is_taken_code_by_code():
    objective = AXIS["objective"]
    assert mc.vote(objective, [("energy", "makespan"), ("makespan",), ("tardiness", "energy")]) \
        == ("makespan", "energy")
    split = [("makespan",), ("tardiness",), ("energy",)]
    assert mc.vote(objective, split) == ("not-stated",) and mc.no_majority(objective, split)
    coordination = AXIS["coordination"]
    assert mc.vote(coordination, [("single-agent",), ("single-agent",),
                                  ("multi-agent", "hierarchical")]) == ("single-agent",)


def test_the_readiness_claim_takes_the_highest_level_two_models_reach():
    readiness = AXIS["readiness_claim"]
    split = ["none", "real-data", "twin-or-hil"]
    assert mc.vote(readiness, split) == "real-data" and not mc.no_majority(readiness, split)
    assert mc.vote(readiness, ["real-data", "twin-or-hil", "testbed-or-shadow"]) == "twin-or-hil"
    assert mc.vote(readiness, ["none", "none", "live-system"]) == "none"
    assert mc.vote(readiness, ["twin-or-hil", "none", "twin-or-hil"]) == "twin-or-hil"
    assert mc.vote(readiness, ["not-stated", "not-stated", "live-system"]) == "not-stated"


def test_the_axes_of_levels_are_single_and_their_codes_rise_level_by_level():
    part_a = sections()
    for name in mc.LEVELS:
        axis = AXIS[name]
        assert not axis.multi, name
        for level, code in enumerate(axis.codes, 1):
            assert re.search(r"\bL%d\b" % level, bullet(part_a[name], code)), (name, code)


def test_the_rules_keep_a_tabular_learners_encoding_that_the_plain_vote_loses():
    # Two of three models leave a tabular learner's encoding unstated.
    coded = {"qwen38": {1: cells(**TABULAR, state_encoding="discrete-states")},
             "gemma26": {1: cells(**TABULAR, state_encoding="not-stated")},
             "glimmer30": {1: cells(**TABULAR, state_encoding="not-stated")}}
    plain = [coded[m][1]["state_encoding"] for m in MODELS]
    assert mc.vote(AXIS["state_encoding"], plain) == ("not-stated",)
    voted, implied, changes = mc.combine(coded, AXES, [1])
    assert voted[1]["state_encoding"] == ("discrete-states",)
    assert all(implied[m][1]["state_encoding"] == ("discrete-states",) for m in MODELS)
    assert [(n, who, r.name) for n, who, r, *_ in changes] == [
        (1, "gemma26", "tabular learner: discrete states"),
        (1, "glimmer30", "tabular learner: discrete states")]


def test_the_rules_are_applied_again_to_the_voted_cells():
    # Two models call the study steering but differ on its kind: the role has no majority,
    # while their two `not-applicable` actions carry the vote on the action.
    coded = {"qwen38": {1: cells()},
             "gemma26": {1: cells(policy_role="steering-rules", scheduling_action="not-applicable")},
             "glimmer30": {1: cells(policy_role="steering-heuristic",
                                    scheduling_action="not-applicable")}}
    voted, _, changes = mc.combine(coded, AXES, [1])
    assert (voted[1]["policy_role"], voted[1]["scheduling_action"]) == ("not-stated", "not-stated")
    assert [(who, r, axis, before, after) for _, who, r, axis, before, after in changes] == [
        ("vote", rule("role not stated: action not stated"), "scheduling_action",
         "not-applicable", "not-stated")]


def test_kappa():
    assert mc.kappa([("a", "a"), ("b", "b")]) == 1.0
    assert mc.kappa([("a", "a"), ("a", "b"), ("b", "b"), ("b", "b")]) == pytest.approx(0.5)
    assert mc.kappa([("a", "a"), ("a", "a")]) is None
    assert mc.kappa([]) is None


def test_agreement_on_a_list_axis_is_the_mean_over_its_categories_at_step_2():
    objective = AXIS["objective"]
    first = [("makespan",), ("makespan",), ("energy",), ("energy", "other")]
    third = [("makespan", "energy"), ("makespan",), ("energy",), ("energy",)]
    implied = {m: {n + 1: {"objective": cell} for n, cell in enumerate(cells_)}
               for m, cells_ in zip(MODELS, [first, first, third])}
    k, pairs, per_code, multiclass = mc.agreement(objective, implied, [1, 2, 3, 4])
    # makespan: all three alike (1). energy: the first two alike (1), each with the third
    # 0.5. other: the first two alike (1), each with the third 0; reported, not averaged.
    assert per_code["makespan"][0] == pytest.approx(1.0)
    assert per_code["energy"][0] == pytest.approx(2 / 3)
    assert per_code["other"][0] == pytest.approx(1 / 3)
    assert per_code["tardiness"][0] is None and per_code["not-stated"][0] is None
    assert "other" not in mc.counted(objective) and "makespan" in mc.counted(objective)
    assert k == pytest.approx(5 / 6) and multiclass is None
    assert pairs[("qwen38", "gemma26")] == pytest.approx(1.0)
    assert pairs[("qwen38", "glimmer30")] == pytest.approx(0.75)
    # Held by the map: energy alone (other is no category), so the mean is energy's kappa.
    assert mc.agreement(objective, implied, [1, 2, 3, 4], {"energy", "other"})[0] == \
        pytest.approx(2 / 3)
    single = {m: {n: {"policy_role": "end-to-end" if n < 3 else "steering-rules"}
                  for n in (1, 2, 3, 4)} for m in MODELS}
    k, pairs, per_code, multiclass = mc.agreement(AXIS["policy_role"], single, [1, 2, 3, 4])
    assert k == 1.0 and multiclass == 1.0 and len(pairs) == 3
    assert per_code["end-to-end"][0] == 1.0 and per_code["steering-heuristic"][0] is None


def test_a_single_axis_is_scored_by_its_categories_not_by_codes_the_role_sets():
    # Four steering studies, whose action the role's rule sets for every model, and two end
    # to end, whose action the models code differently.
    action = AXIS["scheduling_action"]
    given = {"qwen38": ["operation", "operation"], "gemma26": ["machine", "machine"],
             "glimmer30": ["operation", "machine"]}
    implied = {m: {n: {"scheduling_action": "not-applicable" if n <= 4 else given[m][n - 5]}
                   for n in range(1, 7)} for m in MODELS}
    held = {"not-applicable", "operation", "machine"}
    k, _, per_code, multiclass = mc.agreement(action, implied, list(range(1, 7)), held)
    # The multiclass kappa is lifted by the four shared `not-applicable` cells; the mean
    # over operation and machine is not.
    assert multiclass == pytest.approx(26 / 45)
    assert per_code["operation"][0] == pytest.approx(4 / 21)
    assert k == pytest.approx(4 / 21)


def test_a_category_the_map_does_not_hold_leaves_the_mean():
    # One model adds `text` once; the map holds only the two codes all three give.
    encoding = AXIS["state_encoding"]
    alike = [("feature-vector",), ("feature-vector",), ("disjunctive-graph",),
             ("disjunctive-graph",)]
    stray = alike[:3] + [("disjunctive-graph", "text")]
    implied = {m: {n + 1: {"state_encoding": cell} for n, cell in enumerate(cells_)}
               for m, cells_ in zip(MODELS, [stray, alike, alike])}
    numbers = [1, 2, 3, 4]
    voted = {n: {"state_encoding": mc.vote(encoding, [implied[m][n]["state_encoding"]
                                                      for m in MODELS])} for n in numbers}
    held = mc.held_codes(encoding, voted, numbers)
    assert held == {"feature-vector", "disjunctive-graph"}
    k_all, _, per_code, _ = mc.agreement(encoding, implied, numbers)
    assert per_code["text"][0] == pytest.approx(0.0) and k_all == pytest.approx(2 / 3)
    assert mc.agreement(encoding, implied, numbers, held)[0] == pytest.approx(1.0)
    assert mc.agreement(encoding, implied, numbers, {"other"})[0] is None


def write_coding(path, rows):
    """{number: codes as text} as the acquisition tool collects a coding file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for n, codes in rows.items():
            w.writerow({"number": n, **codes, "policy_role_evidence": "a quote, with a comma",
                        "title": "Paper %d" % n, "venue": "A journal", "year": 2024,
                        "work_type": "article"})


def test_reading_a_coding_file(tmp_path):
    path = str(tmp_path / "coding.csv")
    write_coding(path, {1: text(objective="energy|makespan")})
    codes, meta = mc.read_codes(path, AXES)
    assert codes[1]["objective"] == ("makespan", "energy")
    assert codes[1]["policy_role"] == "end-to-end"
    assert meta[1]["title"] == "Paper 1"
    for bad, message in ((text(objective="speed"), "not a code of the axis: speed"),
                         (text(objective="not-stated|makespan"), "not-stated with other codes"),
                         (text(coordination="single-agent|multi-agent"), "stands alone"),
                         (text(policy_role="end-to-end|steering-rules"), "more than one code"),
                         (text(instances=""), "no code")):
        write_coding(path, {1: bad})
        with pytest.raises(SystemExit, match=message):
            mc.read_codes(path, AXES)


def build(tmp_path, included=(1, 2, 3), person=None):
    """Three coding files, a person's codes (none unless `person` gives them), the
    screening's decisions and the config under tmp_path; returns the config's path and the
    folder of the outputs."""
    d = tmp_path.as_posix()
    data = os.path.join(d, "datasets")
    tabular = text(**TABULAR)
    rows = {
        "qwen38": {1: text(readiness_claim="real-data"),
                   2: {**tabular, "state_encoding": "discrete-states"}, 3: text()},
        "gemma26": {1: text(), 2: tabular,
                    3: text(policy_role="steering-rules", scheduling_action="not-applicable")},
        "glimmer30": {1: text(readiness_claim="twin-or-hil"), 2: tabular,
                      3: text(policy_role="steering-heuristic", scheduling_action="not-applicable")},
    }
    rows["gemma26"][2]["state_encoding"] = rows["glimmer30"][2]["state_encoding"] = "not-stated"
    for m in MODELS:
        write_coding(os.path.join(data, "map-%s.csv" % m), rows[m])
    write_coding(os.path.join(data, "map-person.csv"), person or {})
    with open(os.path.join(data, "screening.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["number", "decision", "confidence", "reason"])
        w.writeheader()
        for n in (1, 2, 3, 4):
            w.writerow({"number": n, "decision": "include" if n in included else "exclude",
                        "confidence": "high", "reason": "Inclusion 1"})
    with open(os.path.join(REPO, "configs", "map-vote.toml"), encoding="utf-8") as fh:
        config_text = fh.read()
    for old, new in (('"datasets/', '"%s/datasets/' % d), ('"results/', '"%s/results/' % d)):
        assert old in config_text, old
        config_text = config_text.replace(old, new)
    config = os.path.join(d, "map-vote.toml")
    with open(config, "w", encoding="utf-8") as fh:
        fh.write(config_text)
    return config, os.path.join(d, "results", "map")


def run(config, monkeypatch, *extra):
    monkeypatch.setattr("sys.argv", ["map_vote", "--config", config, *extra])
    map_vote.main()


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def test_the_runner_end_to_end(tmp_path, monkeypatch):
    config, results = build(tmp_path)
    run(config, monkeypatch)
    the_map = {int(r["number"]): r for r in read_csv(os.path.join(tmp_path, "datasets", "map.csv"))}
    assert sorted(the_map) == [1, 2, 3]
    assert the_map[1]["state_content"] == "operations|machines"
    assert the_map[1]["readiness_claim"] == "real-data"
    assert (the_map[2]["state_encoding"], the_map[2]["deep_architecture"]) == \
        ("discrete-states", "not-applicable")
    assert (the_map[3]["policy_role"], the_map[3]["scheduling_action"]) == ("not-stated", "not-stated")
    assert the_map[3]["title"] == "Paper 3"
    changed = [(r["number"], r["model"], r["axis"], r["before"], r["after"])
               for r in read_csv(os.path.join(results, "map-implications.csv"))]
    assert changed == [("2", "gemma26", "state_encoding", "not-stated", "discrete-states"),
                       ("2", "glimmer30", "state_encoding", "not-stated", "discrete-states"),
                       ("3", "vote", "scheduling_action", "not-applicable", "not-stated")]
    votes = {r["number"]: r for r in read_csv(os.path.join(results, "map-votes.csv"))}
    assert votes["2"]["state_encoding_gemma26"] == "discrete-states"
    agreement = read_csv(os.path.join(results, "map-agreement.csv"))
    assert [r["axis"] for r in agreement if not r["code"]] == [a.name for a in AXES]
    readiness = next(r for r in agreement if r["axis"] == "readiness_claim" and not r["code"])
    assert readiness["coverage"] == "no"
    # The readiness claim never steers: no kappa against the bar, its multiclass kappa only.
    assert readiness["kappa"] == "" and readiness["kappa_multiclass"] == "0.133"
    inside = {(r["axis"], r["code"]): r["in_axis_kappa"] for r in agreement if r["code"]}
    assert inside[("state_encoding", "disjunctive-graph")] == "yes"
    assert inside[("state_encoding", "other")] == inside[("state_encoding", "not-stated")] == "no"
    assert inside[("deep_architecture", "not-applicable")] == "no"
    # Single axes count their categories too; the map holds end-to-end, not steering-rules.
    assert inside[("policy_role", "end-to-end")] == "yes"
    assert inside[("policy_role", "steering-rules")] == "no"
    assert inside[("readiness_claim", "real-data")] == ""
    with open(os.path.join(results, "map-vote.md"), encoding="utf-8") as fh:
        report = fh.read()
    assert "| tabular learner: discrete states | 0 | 1 | 1 | 0 |" in report
    assert "| role not stated: action not stated | 0 | 0 | 0 | 1 |" in report
    assert "| `policy_role` | single | " in report and "| 2 (66.7%) | 1 |" in report
    assert "on `readiness_claim`, whose codes are levels" in report


def test_a_record_included_but_not_coded_stops_the_run(tmp_path, monkeypatch):
    config, _ = build(tmp_path, included=(1, 2, 3, 4))
    with pytest.raises(SystemExit, match="has not coded 1 included record"):
        run(config, monkeypatch)


def test_a_record_coded_but_not_included_stops_the_run(tmp_path, monkeypatch):
    config, _ = build(tmp_path, included=(1, 2))
    with pytest.raises(SystemExit, match="did not include: 3"):
        run(config, monkeypatch)


def test_a_record_a_person_coded_joins_the_map_without_a_vote(tmp_path, monkeypatch):
    config, results = build(tmp_path, included=(1, 2, 3, 4), person={4: text(**TABULAR)})
    run(config, monkeypatch)
    the_map = {int(r["number"]): r
               for r in read_csv(os.path.join(tmp_path, "datasets", "map.csv"))}
    assert sorted(the_map) == [1, 2, 3, 4]
    # The scheme's rules apply to the person's codes: a tabular learner reads discrete states.
    assert (the_map[4]["learner_depth"], the_map[4]["state_encoding"]) == (
        "tabular", "discrete-states")
    assert the_map[4]["title"] == "Paper 4"
    votes = {r["number"]: r for r in read_csv(os.path.join(results, "map-votes.csv"))}
    assert (votes["4"]["coded_by"], votes["1"]["coded_by"]) == ("person", "models")
    assert (votes["4"]["learner_depth_qwen38"], votes["4"]["learner_depth"]) == ("", "tabular")
    changed = [(r["number"], r["model"], r["axis"])
               for r in read_csv(os.path.join(results, "map-implications.csv"))]
    assert ("4", "person", "state_encoding") in changed
    # The agreement is the models' alone: as over records 1 to 3 without record 4.
    agreement = read_csv(os.path.join(results, "map-agreement.csv"))
    readiness = next(r for r in agreement if r["axis"] == "readiness_claim" and not r["code"])
    assert readiness["kappa_multiclass"] == "0.133"
    with open(os.path.join(results, "map-vote.md"), encoding="utf-8") as fh:
        report = fh.read()
    assert "4 records, the screening's inclusions: 3 coded by qwen38" in report
    assert "and 1 (4) by a person" in report
    assert "| Rule | qwen38 | gemma26 | glimmer30 | after the vote | person |" in report
    assert "| tabular learner: discrete states | 0 | 1 | 1 | 0 | 1 |" in report
    # The share of records all three models code alike is of the records they coded.
    assert "| `policy_role` | single | " in report and "| 2 (66.7%) | 1 |" in report


def test_a_person_codes_only_included_records_no_model_coded(tmp_path, monkeypatch):
    for person, message in (({3: text()}, "glimmer30 coded 3, which a person coded too"),
                            ({5: text()}, "A person coded 5, which the screening did not "
                                          "include")):
        config, _ = build(tmp_path, person=person)
        with pytest.raises(SystemExit, match=message):
            run(config, monkeypatch)


def test_the_override_moves_the_paths_and_keeps_the_settings(tmp_path, monkeypatch):
    config, _ = build(tmp_path)
    elsewhere = (tmp_path / "private").as_posix()
    override = tmp_path / "override.toml"
    override.write_text('[outputs]\nmap = "%s/map.csv"\nvotes = "%s/votes.csv"\n'
                        'implications = "%s/implications.csv"\nagreement = "%s/agreement.csv"\n'
                        'report = "%s/report.md"\n' % ((elsewhere,) * 5), encoding="utf-8")
    run(config, monkeypatch, "--override", str(override))
    assert sorted(os.listdir(elsewhere)) == ["agreement.csv", "implications.csv", "map.csv",
                                             "report.md", "votes.csv"]
    assert not os.path.exists(os.path.join(tmp_path, "datasets", "map.csv"))


def test_the_coders_are_the_screening_panel():
    def table(name, key):
        with open(os.path.join(REPO, "configs", name), "rb") as fh:
            return list(tomllib.load(fh)[key])
    assert table("map-vote.toml", "coders") == table("screening.toml", "screeners")
