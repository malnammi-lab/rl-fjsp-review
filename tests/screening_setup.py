"""A small corpus, three model screeners' files and a config for the screening runner tests.

The config is the real configs/screening.toml with its paths moved into a temporary folder
and the sample and batch size made small, so the tests also check that file. The config's
three screeners are renamed to MODELS, so the tests read the same whatever the panel (the
real names are checked in test_screening.py).

The real config holds this review's settings. By default, build() lays the first round's
settings over it (FIRST_ROUND_*: its rules, seed, unanimous strata and fixed quotas,
disagreements for a person, escape clause, full-text gate and spot check). This keeps the
code of those features tested. build(first_round=False) keeps this review's settings. With
`size`, it uses a proportional draw of the vote's decisions instead.
"""

import csv
import json
import os
import re
import tomllib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = ["screener-a", "screener-b", "screener-c"]
FIELDS = ["number", "decision", "confidence", "reason", "evidence",
          "title", "venue", "year", "work_type"]

RECORDS = [
    (1, "Deep reinforcement learning for flexible job shop scheduling",
     "We train a policy for the flexible job shop of a manufacturing plant."),
    (2, "Reinforcement learning for flow shop scheduling",
     "A permutation flow shop scheduling method for production lines."),
    (3, "Reinforcement learning for cloud task scheduling",
     "Tasks are assigned to virtual machines in cloud computing."),
    (4, "Supervised dispatching for job shop scheduling",
     "A network imitates an expert for job shop scheduling."),
    (5, "Graph networks for routed jobs", "Operations are routed through work centres."),
    (6, "Scheduling with learning", "An approach is presented."),
    (7, "Learning vehicle routing", "Vehicles deliver goods to customers."),
    (8, "Deep reinforcement learning for flexible job shop scheduling", "A copy of record 1."),
    (9, "A record no model finished", "Nothing to say."),
    (10, "Deep reinforcement learning for flexible job shop scheduling with transformers",
     "A pointer network schedules the flexible job shop."),
    (11, "Reinforcement learning for flow shop scheduling in a factory",
     "A hybrid flow shop with parallel machines at each stage."),
]
DUPLICATES = [8]

# number: one (decision, confidence, reason) per model in MODELS order; None = no row.
VOTES = {
    1: [("include", "high", "Inclusion 1 to 3 hold."), ("include", "medium", "A job shop."),
        ("include", "high", "Job shop with RL.")],
    2: [("exclude", "high", "Exclusion 6: a flow shop."), ("exclude", "high", "Exclusion 6, flow shop."),
        ("exclude", "medium", "Exclusion rules 1 and 6.")],
    3: [("exclude", "high", "Exclusion 1: cloud."), ("exclude", "high", "Exclusion 1"),
        ("exclude", "low", "Criterion 1: cloud computing.")],
    4: [("exclude", "high", "Exclusion 7: supervised."),
        ("exclude", "medium", "Learning other than reinforcement learning."),
        ("exclude", "high", "Exclusion 7")],
    5: [("include", "high", "Job shop."), ("uncertain", "low", "Unclear."), ("include", "medium", "Job shop.")],
    # A disagreement whose record names no flexible job shop but whose first reason does: it
    # passes the full-text gate by the reasons and goes to the person.
    6: [("include", "low", "Maybe a flexible job shop."), ("exclude", "medium", "Exclusion 3: no results."),
        ("uncertain", "low", "Thin abstract.")],
    7: [("exclude", "high", "Vehicle routing."), ("exclude", "high", "Vehicle routing."),
        ("exclude", "high", "Vehicle routing.")],
    8: [("include", "high", "A duplicate screened by mistake."), None, None],
    9: [("include", "high", "x"), ("include", "high", "x"), None],
    10: [("include", "high", "Inclusion 1 to 3 hold."), ("include", "high", "A flexible job shop."),
         ("include", "medium", "Job shop.")],
    # Two reasons cite rule 1, one cites rule 6: counted under rule 6 for the record.
    11: [("exclude", "high", "Exclusion 1: not a job shop."),
         ("exclude", "high", "Exclusion 1: no job shop component."),
         ("exclude", "high", "Exclusion 6: a hybrid flow shop.")],
}
# Record 9 decided by every model, for the tests that need a complete vote.
VOTES_COMPLETE = {**VOTES, 9: [("include", "high", "x")] * 3}
UNANIMOUS_EXCLUDE = [2, 3, 4, 7, 11]
BATCH_01 = [1, 2, 3]                       # with batch_size 3
FRAME_EXCLUDE = [4, 7, 11]                 # unanimous exclusions outside batch 01
FRAME_INCLUDE = [9, 10]                    # unanimous inclusions outside batch 01, complete vote
# The vote's inclusions outside batch 01, complete vote: record 5 (two include, one
# uncertain) joins the unanimous ones ([validation] strata = "vote").
VOTE_INCLUDE = [5, 9, 10]
# A term of the escape clause: job shop (1, 4, 10), factory (11).
CARRY_ESCAPE_TERM = [1, 4, 10, 11]

# Added by build(extra=True) for the full-text gate and the spot check; the other tests
# keep the eleven records above.
EXTRA_RECORDS = [
    (12, "Reinforcement learning for production scheduling",
     "An agent assigns orders to the machines of a plant."),
    (13, "A genetic algorithm for the flexible job shop", "No learning is used."),
    (14, "Scheduling automated guided vehicles in a job shop",
     "Guided vehicles carry jobs between the machines."),
]
EXTRA_VOTES = {
    12: [("uncertain", "low", "Inclusion 1: the shop class is not stated.")] * 3,
    13: [("exclude", "high", "Exclusion 7: no reinforcement learning.")] * 3,
    14: [("exclude", "high", "Exclusion 1: vehicle routing.")] * 3,
}
NAMED_BY_TEXT = [1, 10, 13]                # records to screen naming the flexible job shop
SPOT_CHECK = [13, 14]                      # unanimous exclusions flagged, outside batch 01

# The first round's settings (an earlier configs/screening.toml), laid over
# this review's config by build(first_round=True) and first_round().
FIRST_ROUND_REPLACE = (
    ("exclusion_rules = 5", "exclusion_rules = 7"),
    ("prefer = []", "prefer = [[6, 1]]"),
    ("[rules.aliases]\n", '[rules.aliases]\n"shop class outside scope" = 6\n'
                          '"learning other than reinforcement learning" = 7\n'),
    ("seed = 20261012", "seed = 20260930"),
    ('strata = "decision"\n', ""),
    ("settle_disagreements = true\n", ""),
    ("adjudicate = true\n", ""),
)
# The real config's quotas, replaced by build()'s.
QUOTAS = "quota_exclude = 60\nquota_include = 40"
FIRST_ROUND_INPUTS = ('escape = "datasets/screening-escape.csv"\n'
                      'spot_check = "datasets/screening-spot-check.csv"\n')
FIRST_ROUND_OUTPUTS = """escape_md = "results/screening/validation/escape-list.md"
escape_csv = "results/screening/validation/escape-list.csv"
spot_check_md = "results/screening/validation/spot-check.md"
spot_check_csv = "results/screening/validation/spot-check.csv"
fulltext_md = "results/screening/fulltext/fulltext-list.md"
fulltext_csv = "results/screening/fulltext/fulltext-list.csv"
abstract_only_csv = "results/screening/fulltext/abstract-only.csv"
"""
FIRST_ROUND_TABLES = """
[escape]
terms = ["job shop", "jobshop", "fjsp", "jssp", "fjssp", "dfjsp", "factory", "workshop"]

[escape.compare]
"a: as first worded (the problem facet and four words)" = [
    "job shop scheduling", "job-shop scheduling", "jobshop scheduling", "flexible job shop",
    "flexible job-shop", "flow shop scheduling", "flow-shop scheduling", "open shop scheduling",
    "shop scheduling", "dynamic job shop", "production scheduling", "dynamic scheduling",
    "real-time scheduling", "manufacturing scheduling", "adaptive scheduling",
    "shop floor scheduling", "fjsp", "jssp", "fjssp", "dfjsp",
    "manufacturing", "production", "factory", "workshop"]
"b: a job shop in any form" = ["job shop", "jobshop", "fjsp", "jssp", "fjssp", "dfjsp"]

[gate]
terms = ["flexible job shop", "flexible job shops", "flexible jobshop", "flexible jobshops",
         "flexible assembly job shop", "flexible assembly job shops", "fajsp",
         "flexible workshop", "flexible workshops",
         "machine flexibility", "routing flexibility"]
stems = ["fjs"]
reasons = true

[spot_check]
enabled = false
vehicle_terms = ["guided vehicle", "guided vehicles", "agv", "agvs", "material handling",
                 "transport robot", "transport robots", "transportation robot",
                 "transportation robots", "mobile robot", "mobile robots"]
with_terms = ["job shop", "job shops", "jobshop", "jobshops", "fjsp", "jssp", "fjssp", "dfjsp"]
"""


def first_round(cfg):
    """A loaded config with the first round's settings laid over it: its rules, escape
    clause, full-text gate, spot check (withdrawn, so off), and their inputs and outputs."""
    cfg = {**cfg, **tomllib.loads(FIRST_ROUND_TABLES)}
    cfg["inputs"] = {**cfg["inputs"], **tomllib.loads(FIRST_ROUND_INPUTS)}
    cfg["outputs"] = {**cfg["outputs"], **tomllib.loads(FIRST_ROUND_OUTPUTS)}
    cfg["rules"] = {**cfg["rules"], "exclusion_rules": 7, "prefer": [[6, 1]],
                    "aliases": {"shop class outside scope": 6,
                                "learning other than reinforcement learning": 7}}
    return cfg


def write_csv(path, fields, rows, encoding="utf-8-sig"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding=encoding, newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def decision_rows(decisions):
    """[(number, decision, confidence, reason)] -> rows in the screener file format."""
    return [{"number": n, "decision": d, "confidence": c, "reason": r,
             "evidence": "quote %d" % n, "title": "", "venue": "", "year": "", "work_type": ""}
            for n, d, c, r in decisions]


def build(tmp_path, quota_exclude=2, quota_include=1, batch_size=3, write_models=True, votes=None,
          calibrate=True, leave_out=(), extra=False, spot_check=False, first_round=True, size=None,
          dropped=()):
    """Write the corpus, the duplicate list, the list of records dropped before screening,
    the models' files and the config under tmp_path; return the config path and the data
    folder. With `calibrate`, calibration round 1 is complete: the models' batch 01 rows as
    taken, and the person's file agreeing with the first model. `leave_out` replaces the real
    config's `[calibration] leave_out`. With `extra`, EXTRA_RECORDS join the corpus and
    EXTRA_VOTES the default votes. With `spot_check`, the spot check (off in the first
    round's settings) is switched on, so that its code stays tested. With `first_round`
    (the default), the first round's settings are laid over the config; without it, this
    review's settings stay. Either way the sample takes `quota_exclude` and `quota_include`,
    except that with `size` (this review's settings only) it takes `size` records of the
    vote's decisions split in proportion. `dropped` lists the records dropped before
    screening."""
    records = RECORDS + (EXTRA_RECORDS if extra else [])
    if votes is None:
        votes = {**VOTES, **EXTRA_VOTES} if extra else VOTES
    d = tmp_path.as_posix()
    data = os.path.join(tmp_path, "datasets")
    os.makedirs(data, exist_ok=True)
    refs = [{"number": n, "openalex_id": "https://openalex.org/W%d" % n, "title": t,
             "abstract": a, "venue": "A journal", "year": 2024, "work_type": "article",
             "verdict": "DISCOVERED"} for n, t, a in records]
    with open(os.path.join(data, "references.json"), "w", encoding="utf-8") as fh:
        json.dump({"references": refs}, fh)
    write_csv(os.path.join(data, "duplicates.csv"), ["number", "duplicate_of"],
              [{"number": n, "duplicate_of": 1} for n in DUPLICATES], encoding="utf-8")
    write_csv(os.path.join(data, "dropped.csv"), ["number", "year", "title", "reason"],
              [{"number": n, "year": 2024, "title": "", "reason": "no abstract and no DOI"}
               for n in dropped], encoding="utf-8")
    if write_models:
        for i, m in enumerate(MODELS):
            rows = [(n, *v[i]) for n, v in sorted(votes.items()) if v[i] is not None]
            write_csv(os.path.join(data, "screening-%s.csv" % m), FIELDS, decision_rows(rows))
        if calibrate:
            gone = set(DUPLICATES) | set(dropped)
            batch_01 = [n for n in [n for n, _, _ in RECORDS if n not in gone][:batch_size]
                        if n not in leave_out]
            folder = os.path.join(data, "calibration", "round-1")
            for i, m in enumerate(MODELS):
                write_csv(os.path.join(folder, "%s.csv" % m), FIELDS,
                          decision_rows([(n, *votes[n][i]) for n in batch_01]))
            write_csv(os.path.join(folder, "osamah.csv"), FIELDS,
                      decision_rows([(n, votes[n][0][0], "high", "calibration") for n in batch_01]))

    with open(os.path.join(REPO, "configs", "screening.toml"), encoding="utf-8") as fh:
        text = fh.read()
    panel = list(tomllib.loads(text)["screeners"])
    assert len(panel) == len(MODELS), panel
    for real, name in zip(panel, MODELS):
        text = re.sub(r"\b%s\b" % re.escape(real), name, text)
    assert QUOTAS in text, QUOTAS
    quotas = "quota_exclude = %d\nquota_include = %d" % (quota_exclude, quota_include)
    text = text.replace(QUOTAS, quotas)
    if first_round:
        for old, new in FIRST_ROUND_REPLACE + (
                ('dropped = "datasets/dropped.csv"\n',
                 'dropped = "datasets/dropped.csv"\n' + FIRST_ROUND_INPUTS),):
            assert old in text, old
            text = text.replace(old, new)
        text = text.rstrip("\n") + "\n" + FIRST_ROUND_OUTPUTS + FIRST_ROUND_TABLES
    elif size is not None:
        assert 'strata = "decision"\n' in text
        text = text.replace('strata = "decision"\n', 'strata = "vote"\n')
        text = text.replace(quotas, "size = %d" % size)
    # The sheets go beside the authors' copies (../data/), here a folder of tmp_path.
    for old, new in (('"datasets/', '"%s/datasets/' % d), ('"results/', '"%s/results/' % d),
                     ('"../data/', '"%s/data/' % d),
                     ("batch_size = 25", "batch_size = %d" % batch_size),
                     ("leave_out = []", "leave_out = [%s]" % ", ".join(map(str, leave_out)))):
        assert old in text, old
        text = text.replace(old, new)
    if spot_check:
        assert text.count("enabled = false") == 1
        text = text.replace("enabled = false", "enabled = true")
    config = os.path.join(tmp_path, "screening.toml")
    with open(config, "w", encoding="utf-8") as fh:
        fh.write(text)
    return config, data


def page_data(path):
    """The data a screening page holds, read back from its data block."""
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    match = re.search(r'<script[^>]*id="sheet-data"[^>]*>(.*?)</script>', html, re.S)
    return json.loads(match.group(1))


def run(module, config, monkeypatch, *extra):
    monkeypatch.setattr("sys.argv", [module.__name__, "--config", config, *extra])
    module.main()


def sheets(results):
    """The folder a stage's sheet is written to: beside the authors' copies (../data/<stage>/
    in the configs), here under tmp_path, given the stage's folder of results/."""
    return os.path.join(os.path.dirname(os.path.dirname(results)), "data",
                        os.path.basename(results))


def without_abstracts(tmp_path, monkeypatch):
    """Point src/withheld.py at a config that withholds the abstracts of tmp_path's
    datasets/references.json, the authors' copy absent, as in a clone."""
    from src import withheld
    d = tmp_path.as_posix()
    config = os.path.join(tmp_path, "withheld.toml")
    with open(config, "w", encoding="utf-8") as fh:
        fh.write('[abstracts]\n"%s/datasets/references.json" = "%s/data/search/references.json"\n'
                 % (d, d))
    monkeypatch.setattr(withheld, "CONFIG", config)
