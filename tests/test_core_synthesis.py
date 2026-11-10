"""Tests for the synthesis of the core (runners/core_synthesis.py): six studies whose counts are
worked out by hand, their item tables and verdicts, a small map and its votes, all in tmp_path."""

import csv
import os
import sys
import tomllib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

import core_synthesis as cs  # noqa: E402
from src import coreblocks as cb  # noqa: E402

SPEC = cb.load_spec(os.path.join(REPO, "configs", "core-coding.toml"),
                    os.path.join(REPO, "configs", "map.toml"))
with open(os.path.join(REPO, "configs", "map.toml"), "rb") as _fh:
    AXES = tomllib.load(_fh)["axes"]

FIELDS = ["number", "year", "step", "role", "policy_role", "algorithm", "algorithm_family",
          "coordination", "objective", "seeds", "seed_spread", "baselines", "benchmark_sets",
          "q_shop", "q_runs", "readiness_level", "headline_statistic"]
STUDIES = [
    [1, 2023, "3", "end-to-end", "end-to-end", "ppo", "policy-gradient", "single-agent",
     "makespan", "5", "reported", "2", "brandimarte", "1", "1", "L1", "mean"],
    [2, 2023, "3", "end-to-end", "end-to-end", "q-learning", "value-based",
     "multi-agent|hierarchical", "makespan|tardiness", "1", "not-applicable", "1",
     "brandimarte|hurink", "0.5", "0", "L1", "mean"],
    [3, 2024, "2", "end-to-end", "end-to-end", "ppo", "policy-gradient", "single-agent",
     "makespan", "not-reported", "not-reported", "none", "none", "0", "0", "L2", "best"],
    [4, 2024, "3", "steering", "steering-rules", "q-learning", "value-based", "single-agent",
     "tardiness", "3", "reported", "3", "hurink", "1", "0.5", "L1", "mean"],
    [5, 2025, "3", "steering", "steering-heuristic", "other", "other", "single-agent", "energy",
     "", "", "1", "kacem", "not-assessable", "0", "L1", "single-run"],
    [6, 2025, "2", "not-stated", "not-stated", "ppo", "policy-gradient", "single-agent",
     "makespan", "2", "reported", "none", "not-stated", "1", "1", "L3", "mean"],
]
BASELINES = [(1, 1, "dispatching-rule", "rerun", "not-applicable", "supported"),
             (1, 2, "metaheuristic", "rerun", "stated", "supported"),
             (2, 1, "dispatching-rule", "copied", "not-applicable", "not-supported"),
             (4, 1, "dispatching-rule", "rerun", "not-applicable", "supported"),
             (4, 2, "metaheuristic", "rerun", "stated", "supported"),
             (4, 3, "exact-solver", "rerun", "not-stated", "supported"),
             (5, 1, "metaheuristic", "rerun", "stated", "supported")]
CLAIMS = [(1, 1, "beats-dispatching-rules"), (2, 1, "beats-dispatching-rules"),
          (4, 1, "beats-dispatching-rules"), (4, 2, "generalizes-across-sizes"),
          (3, 1, "generalizes-across-sizes")]
MAP_ROLES = {1: "end-to-end", 2: "not-stated", 3: "end-to-end", 4: "steering-rules",
             5: "steering-rules", 6: "not-stated", 7: "end-to-end", 8: "steering-heuristic"}
# Each model's role for the map's records: 1, 3 and 4 unanimous.
VOTES = {1: ("end-to-end",) * 3, 2: ("not-stated", "end-to-end", "not-stated"),
         3: ("end-to-end",) * 3, 4: ("steering-rules",) * 3,
         5: ("steering-rules", "steering-heuristic", "steering-rules"),
         6: ("not-stated", "end-to-end", "not-stated"), 7: ("end-to-end", "end-to-end", "other"),
         8: ("steering-heuristic", "steering-rules", "steering-heuristic")}
TABLES = """
[[table]]
id = "count"
title = "Counts"
rq = "1"
kind = "count"
fields = ["coordination", "objective", "seeds", "baselines"]

[[table]]
id = "cross"
title = "Role by family"
rq = "1"
kind = "crosstab"
rows = "policy_role"
cols = "algorithm_family"

[[table]]
id = "kinds"
title = "Baseline kinds"
rq = "3.2"
kind = "items"
source = "baselines"
fields = ["kind"]
per = "study"

[[table]]
id = "claims"
title = "Claims"
rq = "3.4"
kind = "claims"
"""


def write(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        w.writerows(rows)


def build(tmp_path, studies=STUDIES):
    base = tmp_path.as_posix()
    write(os.path.join(base, "coded.csv"), FIELDS, studies)
    write(os.path.join(base, "baselines.csv"),
          ["number", "item", "kind", "run", "time_limit", "verdict"], BASELINES)
    write(os.path.join(base, "claims.csv"), ["number", "item", "claim", "verdict"],
          [c + ("supported",) for c in CLAIMS])
    write(os.path.join(base, "transfer.csv"), ["number", "item", "differs", "provenance", "mode",
                                               "outcome", "verdict"], [])
    answers = [[n, "A02", "A02", "coordination", "A", "1.1", "", "", "", "supported", "", "", ""]
               for n in range(2, 7)]
    answers.append([1, "A02", "A02", "coordination", "A", "1.1", "", "", "single-agent",
                    "partly", "multi-agent", "", ""])
    write(os.path.join(base, "answers.csv"),
          ["number", "id", "qid", "name", "section", "rq", "item", "field", "value", "verdict",
           "judge_value", "pages", "quote_sha256"], answers)
    write(os.path.join(base, "map.csv"), ["number", "policy_role", "readiness_claim"],
          [[n, r, "none"] for n, r in MAP_ROLES.items()])
    write(os.path.join(base, "votes.csv"),
          ["number", "policy_role_qwen38", "policy_role_gemma26", "policy_role_glimmer30",
           "policy_role"], [[n] + list(v) + [MAP_ROLES[n]] for n, v in VOTES.items()])
    repo = REPO.replace("\\", "/")
    config = os.path.join(base, "core-synthesis.toml")
    with open(config, "w", encoding="utf-8") as fh:
        fh.write('[inputs]\nspec = "%s/configs/core-coding.toml"\nmap = "%s/configs/map.toml"\n'
                 'coded = "%s/coded.csv"\nanswers = "%s/answers.csv"\n'
                 'baselines = "%s/baselines.csv"\nclaims = "%s/claims.csv"\n'
                 'transfer_tests = "%s/transfer.csv"\nthe_map = "%s/map.csv"\n'
                 'map_votes = "%s/votes.csv"\n[outputs]\ndir = "%s/out"\n'
                 % ((repo, repo) + (base,) * 8) + TABLES)
    return config


def run(config, monkeypatch):
    monkeypatch.setattr("sys.argv", ["core_synthesis", "--config", config])
    cs.main()


def rows(tmp_path, name):
    with open(os.path.join(tmp_path, "out", name), encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def cells(tmp_path, name):
    return {(r["field"], r["code"]): r for r in rows(tmp_path, name)}


def test_counts_split_by_role_count_each_code_of_a_study(tmp_path, monkeypatch):
    run(build(tmp_path), monkeypatch)
    c = cells(tmp_path, "count.csv")
    single = c[("coordination", "single-agent")]
    assert (single["n_all"], single["pct_all"]) == ("5", "83.3")
    assert (single["n_end-to-end"], single["pct_end-to-end"]) == ("2", "66.7")
    assert single["pct_steering"] == "100.0" and single["pct_not-stated"] == "100.0"
    assert c[("coordination", "hierarchical")]["n_all"] == "1"
    assert c[("objective", "makespan")]["n_all"] == "4"
    # A number: those reporting it among those answering, then its median and range.
    assert (c[("seeds", "reported")]["n_all"], c[("seeds", "reported")]["pct_all"]) == ("4", "80.0")
    assert c[("seeds", "median")]["n_all"] == "2.5" and c[("seeds", "largest")]["n_all"] == "5"
    # A count: in bins.
    assert [c[("baselines", b)]["n_all"] for b in ("none", "1", "2", "3 or more")] == [
        "2", "2", "1", "1"]
    codes = [r["code"] for r in rows(tmp_path, "count.csv") if r["field"] == "coordination"]
    assert codes == ["single-agent", "multi-agent", "hierarchical"]


def test_a_crosstab_items_by_study_and_claims(tmp_path, monkeypatch):
    run(build(tmp_path), monkeypatch)
    cross = {r["code"]: r for r in rows(tmp_path, "cross.csv")}
    assert cross["end-to-end"]["policy-gradient"] == "2" and cross["end-to-end"]["value-based"] == "1"
    assert cross["steering-heuristic"]["other"] == "1" and cross["not-stated"]["total"] == "1"
    kinds = cells(tmp_path, "kinds.csv")
    assert (kinds[("kind", "dispatching-rule")]["n_all"],
            kinds[("kind", "dispatching-rule")]["pct_all"]) == ("3", "50.0")
    assert kinds[("kind", "exact-solver")]["n_steering"] == "1"
    claims = cells(tmp_path, "claims.csv")
    beats = "beats-dispatching-rules"
    assert claims[(beats, "makes the claim")]["pct_all"] == "50.0"
    assert claims[(beats, "shares a named benchmark set with another study making it")][
        "pct_all"] == "100.0"
    assert claims[(beats, "reruns every baseline, no time limit left unstated")]["n_all"] == "1"
    assert claims[(beats, "several training runs with their spread")]["n_all"] == "2"
    sizes = "generalizes-across-sizes"
    assert claims[(sizes, "shares a named benchmark set with another study making it")][
        "n_all"] == "0"
    with open(os.path.join(tmp_path, "out", "count.tex"), encoding="utf-8") as fh:
        tex = fh.read()
    assert "single-agent & 5 (83.3\\%)" in tex and tex.startswith("% Generated by")


def test_another_named_set_is_no_set_that_two_studies_share(tmp_path, monkeypatch):
    # other-benchmark names no one set: studies 3 and 4 coded with it share nothing.
    changed = [list(s) for s in STUDIES]
    changed[2][12] = changed[3][12] = "other-benchmark"
    run(build(tmp_path, changed), monkeypatch)
    claims = cells(tmp_path, "claims.csv")
    shared = "shares a named benchmark set with another study making it"
    assert claims[("generalizes-across-sizes", shared)]["n_all"] == "0"
    assert (claims[("beats-dispatching-rules", shared)]["n_all"],
            claims[("beats-dispatching-rules", shared)]["pct_all"]) == ("2", "66.7")


def test_question_3_4s_metrics_and_all_its_terms_with_one_study():
    studies = [dict(zip(FIELDS, map(str, s))) for s in STUDIES]
    names = ["number", "item", "kind", "run", "time_limit", "verdict"]
    baselines = [dict(zip(names, map(str, b))) for b in BASELINES]
    claims = [{"number": str(n), "item": str(i), "claim": c} for n, i, c in CLAIMS]
    test = {label: key for label, key in cs.CLAIM_TESTS}
    label = {key: lab for lab, key in test.items()}

    def got(rows, claim, key):
        r = next(r for r in rows if r["field"] == claim and r["code"] == label[key])
        return r["n_all"], r["pct_all"]

    beats, sizes = "beats-dispatching-rules", "generalizes-across-sizes"
    _, rows = cs.claims_rows(cs.Data(studies, {"claims": claims, "baselines": baselines}, {}),
                             SPEC, {})
    # Studies 1, 2 and 4 claim to beat the rules: 1 and 2 share makespan and a mean, 2 and 4
    # tardiness and a mean. Studies 3 and 4 (generalizing) share neither an objective nor a
    # statistic. Study 2 copies its rules and study 4 leaves a time limit unstated, so no study
    # is comparable on every term.
    assert got(rows, beats, "metric") == (3, "100.0") and got(rows, sizes, "metric") == (0, "0.0")
    assert got(rows, beats, "all") == (0, "0.0")
    # With study 2's rules rerun, studies 1 and 2 are comparable on every term.
    baselines[2]["run"] = "rerun"
    _, rows = cs.claims_rows(cs.Data(studies, {"claims": claims, "baselines": baselines}, {}),
                             SPEC, {})
    assert got(rows, beats, "all") == (2, "66.7")


def test_the_lowest_quality_fifth_keeps_the_studies_tied_at_the_cut():
    data = cs.Data([dict(zip(FIELDS, map(str, s))) for s in STUDIES], {}, {})
    # Means: 1 and 6 at 1, 4 at 0.75, 2 at 0.25, 3 and 5 at 0: a fifth of six is one study,
    # and the two lowest tie at the cut, so both are kept.
    assert cs.lowest_quality(data, ["q_shop", "q_runs"]) == set()
    changed = [list(s) for s in STUDIES]
    changed[4][15 - 1] = "0.5"
    data = cs.Data([dict(zip(FIELDS, map(str, s))) for s in changed], {}, {})
    assert cs.lowest_quality(data, ["q_shop", "q_runs"]) == {"3"}


def test_the_sensitivity_analyses_and_the_agreement(tmp_path, monkeypatch):
    run(build(tmp_path), monkeypatch)
    disputed = cells(tmp_path, os.path.join("sensitivity", "without-disputed", "count.csv"))
    # Study 1's coordination is disputed: left out, five studies answer.
    assert disputed[("coordination", "single-agent")]["pct_all"] == "80.0"
    step = cells(tmp_path, os.path.join("sensitivity", "without-step-2", "count.csv"))
    assert step[("coordination", "single-agent")]["n_all"] == "3"
    kinds = cells(tmp_path, os.path.join("sensitivity", "without-disputed", "kinds.csv"))
    assert kinds[("kind", "dispatching-rule")]["n_all"] == "2"
    with open(os.path.join(tmp_path, "out", "sensitivity.md"), encoding="utf-8") as fh:
        text = fh.read()
    assert "(5) Without the answers the judge disputed" in text and "| count |" in text
    agree = {r["qid"]: r for r in rows(tmp_path, "agreement.csv")}
    a02 = agree["A02"]
    assert (a02["supported"], a02["partly"], a02["judged"], a02["supported_pct"]) == (
        "5", "1", "6", "83.3")
    assert a02["pairs"] == "6" and a02["kappa"] != ""
    assert agree["B01"]["judged"] == "0"


def test_without_the_disputes_each_study_keeps_its_cell():
    # Study 2's algorithm is disputed: its family is blanked, and it stays in its cell.
    data = cs.Data([dict(zip(FIELDS, map(str, s))) for s in STUDIES], {},
                   {("2", "B07"): "not-supported"})
    out = cs.without_disputed(data, SPEC)
    two = next(s for s in out.studies if s["number"] == "2")
    assert two["algorithm"] == "" and two["algorithm_family"] == ""
    assert out.cell["2"] == "end-to-end / value-based" and out.in_column("2", "end-to-end")
    # Leaving studies out keeps the others' cells and counts only those kept.
    kept = cs.without(out, {"1", "3"})
    assert sorted(kept.cell) == ["2", "4", "5", "6"]
    assert kept.cell["2"] == "end-to-end / value-based"
    assert [s["number"] for s in kept.studies] == ["2", "4", "5", "6"]


def test_an_answer_the_authors_corrected_stands_and_its_agreement_is_the_coders():
    # Study 2's algorithm: the coder gave ppo, the judge proposed q-learning, and the authors
    # corrected it to q-learning (its row); study 1's ppo is supported.
    studies = [dict(zip(FIELDS, map(str, s))) for s in STUDIES]
    data = cs.Data(studies, {}, {("1", "B07"): "supported", ("2", "B07"): "not-supported",
                                 ("2", "A02"): "partly"})
    data.corrected = {("2", "B07"): "ppo"}
    data.proposals = {("2", "B07"): "q-learning"}
    out = cs.without_disputed(data, SPEC)
    two = next(s for s in out.studies if s["number"] == "2")
    assert two["algorithm"] == "q-learning" and two["coordination"] == ""
    assert cs.left_out(data) == 1
    # The coder's ppo against the judge's q-learning, not the authors' value: kappa 0.
    b07 = {r["qid"]: r for r in cs.agreement(data, SPEC)}["B07"]
    assert b07["pairs"] == 2 and b07["kappa"] == "0.000"


def test_the_abstract_against_the_full_text_and_the_unanimous_map(tmp_path, monkeypatch):
    run(build(tmp_path), monkeypatch)
    role = {r["code"]: r for r in rows(tmp_path, "abstract-vs-full-text.csv")
            if r["axis"] == "policy_role"}
    assert (role[""]["studies"], role[""]["same"], role[""]["abstract_silent"]) == ("6", "4", "1")
    unanimous = {(r["axis"], r["code"]): r for r in rows(tmp_path, "map-unanimous.csv")}
    e2e = unanimous[("policy_role", "end-to-end")]
    assert (e2e["records"], e2e["n"], e2e["unanimous_records"], e2e["unanimous_n"]) == (
        "8", "3", "3", "2")
    assert e2e["unanimous_pct"] == "66.7" and e2e["change_pp"] == "29.2"


def test_a_record_no_model_coded_is_not_among_those_the_models_coded_alike():
    # Record 2 was coded by a person: its three model cells are blank, which is no agreement.
    axes = {"policy_role": {"codes": ["end-to-end", "steering-rules", "steering-heuristic"]}}
    map_rows = [{"number": "1", "policy_role": "end-to-end"},
                {"number": "2", "policy_role": "not-stated"}]
    votes = [{"number": "1", "policy_role_a": "end-to-end", "policy_role_b": "end-to-end",
              "policy_role_c": "end-to-end", "policy_role": "end-to-end"},
             {"number": "2", "policy_role_a": "", "policy_role_b": "", "policy_role_c": "",
              "policy_role": "not-stated"}]
    rows = {r["code"]: r for r in cs.map_unanimous(map_rows, votes, axes)}
    assert rows["end-to-end"]["unanimous_records"] == 1
    assert rows["not-stated"]["unanimous_n"] == 0 and rows["not-stated"]["n"] == 1


def test_every_table_of_the_real_config_names_fields_that_exist():
    with open(os.path.join(REPO, "configs", "core-synthesis.toml"), "rb") as fh:
        tables = tomllib.load(fh)["table"]
    assert len({t["id"] for t in tables}) == len(tables)
    for t in tables:
        assert t["kind"] in ("count", "crosstab", "items", "claims", "map-cells", "list")
        source = t.get("source")
        if t["kind"] == "crosstab":
            assert source is None, t["id"]
        for name in t.get("fields", []) + [t[k] for k in ("rows", "cols") if k in t]:
            kind, _ = cs.field_info(SPEC, AXES, name, source)
            assert kind != "text", (t["id"], name)


def test_the_maps_cells_count_a_record_under_each_of_its_families():
    records = [{"policy_role": "end-to-end", "training_algorithm_family": "policy-gradient|actor-critic",
                "deep_architecture": "graph-neural-network"},
               {"policy_role": "end-to-end", "training_algorithm_family": "policy-gradient",
                "deep_architecture": "graph-neural-network|attention-transformer"},
               {"policy_role": "steering-rules", "training_algorithm_family": "value-based",
                "deep_architecture": "fully-connected"},
               {"policy_role": "not-stated", "training_algorithm_family": "not-stated",
                "deep_architecture": "not-stated"}]
    rows = cs.map_cells_rows(AXES, records, {"fields": ["deep_architecture"]})
    by = {(r["role"], r["family"]): r for r in rows}
    assert [k for k in by] == [("end-to-end", "policy-gradient"), ("end-to-end", "actor-critic"),
                               ("steering", "value-based"), ("not-stated", "not-stated")]
    assert by[("end-to-end", "policy-gradient")]["records"] == 2
    assert by[("end-to-end", "policy-gradient")]["deep_architecture"] == (
        "graph-neural-network 2; attention-transformer 1 (of 2 naming one)")
    assert by[("end-to-end", "actor-critic")]["records"] == 1
    assert by[("not-stated", "not-stated")]["deep_architecture"] == "none named"


def test_a_list_gives_each_study_its_bibtex_key(tmp_path):
    bib = os.path.join(tmp_path, "refs.bib")
    with open(bib, "w", encoding="utf-8") as fh:
        fh.write("% Record 1\n% Crossref: year: 2023 -> 2025\n@article{one2025x,\n  title = {A}\n}\n"
                 "\n% Record 4\n@inproceedings{four2025y,\n  title = {B}\n}\n@misc{other2020,\n}\n")
    keys = cs.bib_keys(bib)
    assert keys == {"1": "one2025x", "4": "four2025y"}
    assert cs.bib_keys(os.path.join(tmp_path, "none.bib")) == {}
    data = cs.Data([dict(zip(FIELDS, map(str, s))) for s in STUDIES], {}, {})
    rows = cs.list_rows(data, {"fields": ["algorithm"]}, keys)
    # Every study, in the order of the cells: end to end value-based (2), end to end policy
    # gradient (1 and 3), steering value-based (4) and other (5), role not stated (6).
    assert [(r["number"], r["key"], r["cell"]) for r in rows] == [
        ("2", "", "end-to-end / value-based"), ("1", "one2025x", "end-to-end / policy-gradient"),
        ("3", "", "end-to-end / policy-gradient"), ("4", "four2025y", "steering / value-based"),
        ("5", "", "steering / other"), ("6", "", "not-stated / policy-gradient")]
    assert rows[0]["algorithm"] == "q-learning"


def test_with_no_studies_yet_only_the_index_is_written(tmp_path, monkeypatch):
    run(build(tmp_path, studies=[]), monkeypatch)
    with open(os.path.join(tmp_path, "out", "synthesis.md"), encoding="utf-8") as fh:
        assert "No studies gathered yet" in fh.read()
    assert not os.path.exists(os.path.join(tmp_path, "out", "count.csv"))
