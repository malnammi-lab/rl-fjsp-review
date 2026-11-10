"""Combine the three model screeners' decisions by the vote rule, and count exclusions by
the criterion each cites.

A disagreement of the vote is settled by rule or by a person. A removed record that a
person screened and did not exclude is carried forward on that person's decision. The rules
are in src/screening.py. Reads the corpus, the models' decision files, the calibration
rounds (which must be complete) and the people's decision files once they exist. Writes
datasets/screening.csv, and screening-votes.csv and screening-consensus.md in
results/screening/consensus/. Without settling by rule it also writes a disagreements sheet
for a person; with [gate], the full-text lists.

Run: python runners/run_all.py --only screening-consensus
"""

import argparse
import csv
import os
import sys
import tomllib
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus  # noqa: E402
from src import screening as sc  # noqa: E402
from src import withheld  # noqa: E402
from runners.make_tables import load_duplicates  # noqa: E402


def resolve(path):
    return os.path.normpath(os.path.join(REPO, path))


def rel(path):
    try:
        return os.path.relpath(path, REPO)
    except ValueError:
        return path


def load_config(path, override=None):
    """The config, with the tables of an optional override file laid over it key by key.

    The override is meant to move paths only; every setting (the seed, the quotas, the rules)
    still comes from this repository's config."""
    with open(path, "rb") as fh:
        cfg = tomllib.load(fh)
    if override:
        with open(override, "rb") as fh:
            for table, values in tomllib.load(fh).items():
                if isinstance(values, dict) and isinstance(cfg.get(table), dict):
                    cfg[table] = {**cfg[table], **values}
                else:
                    cfg[table] = values
    return cfg


def spot_check_on(cfg):
    """Whether the spot check of [spot_check] is in force: the table is present and not
    switched off by its `enabled` key."""
    s = cfg.get("spot_check")
    return bool(s) and s.get("enabled", True)


def spot_check_decisions(cfg):
    """The person's spot-check decisions while the check is in force; {} otherwise. A
    decision file present while the check is off is refused, so that no override made
    under it is carried forward."""
    if spot_check_on(cfg):
        return load_person(cfg, "spot_check")[0]
    path = cfg["inputs"].get("spot_check")
    if path and os.path.isfile(resolve(path)):
        raise SystemExit("%s exists, but the spot check is withdrawn ([spot_check] enabled = "
                         "false); move the file aside." % path)
    return {}


def page_settings(cfg):
    """What the screening page needs from [page]: the template's text, the two criteria
    texts and the rules offered in the form; None when the config has no [page]. A criteria
    file that is missing reads as empty and is left out of the page."""
    p = cfg.get("page")
    if not p:
        return None

    def text(key):
        path = p.get(key)
        if not path or not os.path.isfile(resolve(path)):
            return ""
        with open(resolve(path), encoding="utf-8-sig") as fh:
            return fh.read()
    template = text("template")
    if not template:
        raise SystemExit("The screening page template %s is missing." % p.get("template"))
    return {"template": template, "criteria_brief": text("criteria_brief"),
            "criteria_full": text("criteria_full"), "rules": p.get("rules", [])}


def add_config_arguments(parser):
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "screening.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")


def load_corpus(cfg, abstracts=False):
    """(every record, the records to screen), in corpus order. The records to screen are the
    corpus less the duplicate rule's removals and, when the config names it ([inputs]
    dropped), the records dropped before screening for another reason. With `abstracts`, the
    records take their abstracts from the authors' copy when it is in place (src/withheld.py),
    as a sheet that shows them needs."""
    inputs = cfg["inputs"]
    records = corpus.load_references(resolve(inputs["references"]), abstracts=abstracts)
    dup_path = resolve(inputs["duplicates"])
    if not os.path.isfile(dup_path):
        raise SystemExit("%s not found. Run the duplicate rule first: "
                         "python runners/run_all.py --only deduplicate" % dup_path)
    removed = load_duplicates(dup_path)
    if inputs.get("dropped"):
        drop_path = resolve(inputs["dropped"])
        if not os.path.isfile(drop_path):
            raise SystemExit("%s not found: the records dropped before screening (protocol, "
                             "Search strategy)." % drop_path)
        dropped = load_duplicates(drop_path)
        unknown = sorted(dropped - {r.number for r in records})
        if unknown:
            raise SystemExit("%s names records not in the corpus: %s"
                             % (drop_path, ", ".join(map(str, unknown))))
        removed = removed | dropped
    return records, sc.to_screen(records, removed)


def load_models(cfg):
    """{model: {number: Decision}} in config order; refuses to run on other than three."""
    screeners = cfg["screeners"]
    if len(screeners) != 3:
        raise SystemExit("the vote rule is written for three screeners; %d configured"
                         % len(screeners))
    missing = [p for p in screeners.values() if not os.path.isfile(resolve(p))]
    if missing:
        raise SystemExit(
            "No consensus yet: %s not found (the models' decision files; datasets/MANIFEST.md)."
            % ", ".join(missing))
    return {name: sc.read_decisions(resolve(p))[0] for name, p in screeners.items()}


def unvoted(numbers, votes):
    """Records to screen that some screener has not decided yet."""
    return [n for n in numbers if any(n not in v for v in votes.values())]


def calibration_rescue(cfg):
    """The person's decisions in the last calibration round, or {}: batch 01 is screened by
    the person there, so a unanimous exclusion he did not exclude is carried forward like
    one from the validation sample. Refused if the file changed after the round was taken."""
    cal = cfg.get("calibration")
    if not cal:
        return {}
    people = [s for s in cal["screeners"] if s not in cal["models"]]
    if not people:
        return {}
    rnd, path = sc.latest_person_round(resolve(cal["dir"]), cal["screeners"], people[0])
    if not path:
        return {}
    decided = sc.read_decisions(path)[0]
    sc.verify_lock(resolve(cfg["outputs"]["calibration_lock"]), "round %d" % rnd, decided, path)
    return decided


def require_calibration(cfg, screen_records, votes):
    """Refuse to go on before calibration is complete: the newest calibration round must hold
    every screener's file, and each model's batch 01 decisions must be those taken into that
    round. Otherwise the bulk outputs would show the person models' decisions on batch 01
    before his own file for the round exists, or batch 01 would be left out of the
    validation sample without a person having screened it."""
    cal = cfg.get("calibration")
    if not cal:
        return
    numbers = [r.number for r in sc.calibration_batch(screen_records, cal)]
    found = sc.rounds(resolve(cal["dir"]), cal["screeners"])
    if not found:
        raise SystemExit("No calibration round yet: batch 01 is screened by the models and the "
                         "person, and the round taken (screening_calibration.py --take-round N), "
                         "before the bulk vote is used.")
    rnd, paths = list(found.items())[-1]
    missing = [s for s, p in paths.items() if not os.path.isfile(p)]
    if missing:
        raise SystemExit("Calibration round %d is not complete (waiting for %s); take it first "
                         "(screening_calibration.py --take-round %d)." % (rnd, ", ".join(missing), rnd))
    for m in cal["models"]:
        taken = sc.read_decisions(paths[m])[0]
        changed = [n for n in numbers if votes[m].get(n) != taken.get(n)]
        if changed:
            raise SystemExit("%s's batch 01 decisions differ from those taken into calibration "
                             "round %d (records %s). Take the new answers as a calibration round "
                             "first." % (m, rnd, ", ".join(map(str, changed))))


def person_validation(cfg):
    """The person's validation decisions, refused if they changed after the sample was
    complete (the lock is written by screening_validation.py)."""
    decided, _ = load_person(cfg, "validation")
    if decided:
        sc.verify_lock(resolve(cfg["outputs"]["validation_lock"]), "validation", decided,
                       cfg["inputs"]["validation"])
    return decided


def adjudicated(cfg):
    """The second person's decisions on the validation sample's disagreements, once
    screening_validation.py has found them complete and locked them; {} before that, so
    that a half-finished sheet changes nothing. Refused if they changed after the lock."""
    decided, _ = load_person(cfg, "adjudication")
    if not decided:
        return {}
    locked = sc.verify_lock(resolve(cfg["outputs"]["validation_lock"]), "adjudication",
                            decided, cfg["inputs"]["adjudication"])
    return decided if locked else {}


def load_person(cfg, key):
    """A person's decision file from [inputs], or empty until it exists:
    ({number: Decision}, {number: raw row})."""
    path = cfg["inputs"].get(key)
    if not path or not os.path.isfile(resolve(path)):
        return {}, {}
    decided, _, raw = sc.read_decisions(resolve(path))
    return decided, raw


def named_records(cfg, records, votes):
    """{number: "text" or "reasons"} for the records that name the flexible job shop by the
    rule of [gate]: by their title or abstract ("text"), or else by one of the three
    screeners' reasons or quoted sentences ("reasons"), when the config allows it. None when
    the config has no [gate]."""
    g = cfg.get("gate")
    if not g:
        return None
    terms, stems = g["terms"], g.get("stems", [])
    out = {}
    for r in records:
        if sc.carries((r.title or "") + " " + (r.abstract or ""), terms, stems):
            out[r.number] = "text"
        elif g.get("reasons") and any(
                sc.carries(d.reason, terms, stems) or sc.carries(d.evidence, terms, stems)
                for d in (v.get(r.number) for v in votes.values()) if d is not None):
            out[r.number] = "reasons"
    return out


def labeller(cfg):
    rules = cfg["rules"]
    prefer = [tuple(p) for p in rules.get("prefer", [])]

    def label(reason):
        return sc.rule_label(reason, rules["inclusion_rules"], rules["exclusion_rules"],
                             prefer, rules.get("aliases"))
    return label


def _lowest(confidences):
    known = [c for c in confidences if c in sc.CONFIDENCES]
    return min(known, key=sc.CONFIDENCES.index) if known else ""


SETTLED_BECAUSE = {
    "include": "at least two screeners include it",
    "exclude": "fewer than two screeners include it and at least one excludes it",
    "uncertain": "fewer than two screeners include it and none excludes it",
}


def settle_by_rule(row, ballot, tally, prefer=(), rescues=()):
    """Settle a disagreement by src/screening.settle, filling `row` in place: the decision,
    basis `rule`, the lowest confidence and a quote of the screeners whose decision it is,
    and for an exclusion the rule their reasons cite (the one reason's when a single
    screener excludes). A removed record, excluded or uncertain, that the person screened
    and did not exclude is carried forward on the person's decision, as a unanimous
    exclusion is."""
    decided = sc.settle(d.decision for d in ballot)
    counted = sc.prefer_labels(row["labels"], prefer)
    agreeing = [(d, lab) for d, lab in zip(ballot, counted) if d.decision == decided]
    rule = ""
    if decided == "exclude":
        cited = [lab for _, lab in agreeing]
        rule = cited[0] if len(cited) == 1 else sc.majority_label(cited)
    quoted = next((d for d, lab in agreeing if lab == rule), agreeing[0][0])
    row.update(decision=decided, basis="rule", rule=rule, evidence=quoted.evidence,
               confidence=_lowest(d.confidence for d, _ in agreeing),
               reason="Disagreement (%s), settled by rule: %s." % (tally, SETTLED_BECAUSE[decided])
                      + (" Counted under %s." % rule if rule else ""))
    if decided == "include":
        return
    for basis, screened in rescues:
        person = screened.get(row["number"])
        if person is not None and person.decision != "exclude":
            row.update(decision=person.decision, basis=basis, rule="",
                       confidence=person.confidence, evidence=person.evidence,
                       reason="Disagreement (%s), removed by rule, carried forward at %s: %s"
                              % (tally, basis, person.reason))
            break


def combine(numbers, votes, label, resolutions=None, resolved_by=None, rescues=(), prefer=(),
            named=None, settle=False):
    """One row per record number: its votes, the vote's outcome, the decision, the basis
    of the decision, the rule an exclusion is counted under, and the gate it passes.

    `votes` is {model: {number: Decision}}; `resolutions` the person's decisions on
    disagreements, with `resolved_by` {number: who}; `rescues` [(basis, {number: Decision})]
    the person's screenings that carry a unanimous exclusion forward when they do not
    exclude it. A resolution for a record that is not a disagreement on the person's sheet
    is refused. `prefer` applies the criteria's precedence across the three reasons before
    the majority is taken (src/screening.prefer_labels); `labels` keeps what each reason
    itself cites. `named` ({number: "text" or "reasons"}, from named_records) applies the
    full-text gate: a disagreement whose record is not in it is recorded as uncertain with
    basis `not named` and never put to the person, and every row gets its gate
    (src/screening.gate). With `named` None there is no gate. With `settle`, a disagreement
    the person has not resolved is settled by src/screening.settle (basis `rule`), and a
    removed one is open to the rescues like a unanimous exclusion.
    """
    resolutions = resolutions or {}
    resolved_by = resolved_by or {}
    models = list(votes)
    rows, disagreements, not_named = [], set(), set()
    for n in numbers:
        ballot = [votes[m].get(n) for m in models]
        row = {"number": n, "ballot": ballot, "labels": [label(d.reason) if d else "" for d in ballot],
               "outcome": "", "decision": "", "basis": "", "rule": "",
               "confidence": "", "reason": "", "evidence": "",
               "named": (named or {}).get(n, ""), "gate": ""}
        rows.append(row)
        if any(d is None for d in ballot):
            row["outcome"] = "incomplete"
            continue
        outcome = sc.vote(d.decision for d in ballot)
        row["outcome"] = outcome
        tally = ", ".join("%s %s" % (m, d.decision) for m, d in zip(models, ballot))
        if outcome == "disagreement":
            disagreements.add(n)
            if named is not None and n not in named:
                not_named.add(n)
                row.update(decision="uncertain", basis="not named",
                           reason="Disagreement (%s), not resolved: neither the record nor a "
                                  "screener's reason names the flexible job shop, so it is not "
                                  "sought at full text." % tally)
                continue
            person = resolutions.get(n)
            if person is None and settle:
                settle_by_rule(row, ballot, tally, prefer, rescues)
                continue
            if person is None:
                row["basis"] = "unresolved"
                continue
            row.update(decision=person.decision, basis="resolution",
                       confidence=person.confidence, evidence=person.evidence,
                       reason="Decided by %s after a disagreement (%s): %s"
                              % (resolved_by.get(n, "the person"), tally, person.reason))
            if person.decision == "exclude":
                row["rule"] = label(person.reason)
            continue
        counted = sc.prefer_labels(row["labels"], prefer)
        agreeing = [(d, lab) for d, lab in zip(ballot, counted) if d.decision == outcome]
        rule = sc.majority_label(counted) if outcome == "exclude" else ""
        quoted = next((d for d, lab in agreeing if lab == rule), agreeing[0][0])
        row.update(decision=outcome, basis="vote", rule=rule, evidence=quoted.evidence,
                   confidence=_lowest(d.confidence for d, _ in agreeing),
                   reason="Vote: %s." % tally + (" Counted under %s." % rule if rule else ""))
        if outcome == "exclude":
            for basis, screened in rescues:
                person = screened.get(n)
                if person is not None and person.decision != "exclude":
                    row.update(decision=person.decision, basis=basis, rule="",
                               confidence=person.confidence, evidence=person.evidence,
                               reason="Unanimous exclusion (%s) carried forward at %s: %s"
                                      % (tally, basis, person.reason))
                    break
    stray = sorted(set(resolutions) - (disagreements - not_named))
    if stray:
        raise SystemExit("Resolutions are for disagreements only, and only for those on the "
                         "person's sheet (a disagreement whose record names no flexible job "
                         "shop is not resolved); these records are not on it: %s"
                         % ", ".join(map(str, stray)))
    if named is not None:
        for row in rows:
            row["gate"] = sc.gate(row["decision"], row["number"] in named)
    return rows


def pairwise(votes, numbers, weights):
    """[(a, b, records both decided, agreeing, weighted kappa)] for every pair of screeners."""
    names, out = list(votes), []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pairs = [(votes[a][n].decision, votes[b][n].decision) for n in numbers
                     if n in votes[a] and n in votes[b]]
            out.append((a, b, len(pairs), sum(x == y for x, y in pairs),
                        sc.weighted_kappa(pairs, weights)))
    return out


def fmt_kappa(k):
    return "n/a" if k is None else "%.3f" % k


def pct(part, whole):
    return "%.1f%%" % (100.0 * part / whole) if whole else "n/a"


def render_gate(rows, gate_cfg, outputs):
    """The full-text gate: its rule, what names the flexible job shop by outcome of the
    vote, and where the records carried forward go."""
    out = ["## Full-text gate", "",
           "Full text is sought only for the flexible job shop. A record "
           "names it when its title or abstract carries one of the terms below as whole words "
           "after normalisation, or a word containing one of the stems, or, failing that, when "
           "one of the three screeners' reasons or quoted sentences does%s. A disagreement whose "
           "record names it goes to the person; one whose record does not is recorded as "
           "uncertain (basis `not named`) and set aside. A record carried forward that names "
           "it is sought at full text; an inclusion that does not is a job shop study outside "
           "the body, coded from its title and abstract; an uncertain record that does not is "
           "set aside." % ("" if gate_cfg.get("reasons") else " (not used: `reasons` is false)"),
           "",
           "Terms: %s. Stems: %s." % (", ".join(gate_cfg["terms"]),
                                      ", ".join(gate_cfg.get("stems", [])) or "none"), "",
           "| Outcome of the vote | Records | Named in title or abstract | Named in a screener's "
           "reason only | Not named |", "|---|---|---|---|---|"]
    for outcome in ("exclude", "include", "disagreement", "incomplete"):
        group = [r for r in rows if r["outcome"] == outcome]
        named = Counter(r["named"] for r in group)
        out.append("| %s | %d | %d | %d | %d |" % (outcome, len(group), named["text"],
                                                   named["reasons"], named[""]))
    named = Counter(r["named"] for r in rows)
    out += ["| total | %d | %d | %d | %d |" % (len(rows), named["text"], named["reasons"],
                                               named[""]), ""]
    gates = Counter((r["decision"], r["gate"]) for r in rows if r["gate"])
    out += ["Where each record carried forward goes, by its decision:", "",
            "| Decision | Sought at full text | Coded from title and abstract | Set aside |",
            "|---|---|---|---|"]
    for decision in ("include", "uncertain"):
        out.append("| %s | %d | %d | %d |" % (decision, gates[(decision, "full text")],
                                              gates[(decision, "abstract only")],
                                              gates[(decision, "set aside")]))
    totals = Counter(r["gate"] for r in rows if r["gate"])
    out += ["| total | %d | %d | %d |" % (totals["full text"], totals["abstract only"],
                                          totals["set aside"]), "",
            "The full texts to seek are in `%s` and `%s`; the inclusions coded from title and "
            "abstract in `%s`. Unresolved disagreements that name the flexible job shop pass "
            "no gate until the person decides them." % (outputs["fulltext_md"],
                                                        outputs["fulltext_csv"],
                                                        outputs["abstract_only_csv"]), ""]
    return out


def render(n_identified, numbers, votes, rows, pairs, weights, extras, gate_cfg=None,
           outputs=None, settled=False, prefer=()):
    models = list(votes)
    n = len(numbers)
    wanted = set(numbers)
    disagreement = ("anything else is a disagreement, settled by rule (`src/screening.py`, "
                    "`settle`; protocol, Screening): included when at least two "
                    "include, otherwise removed, as excluded when any screener excludes and as "
                    "uncertain when none does." if settled
                    else "anything else is a disagreement for a person.")
    out = ["# Screening consensus", "",
           "Generated by `runners/screening_consensus.py` from the three model screeners' "
           "decision files and, where they exist, the person's decisions "
           "(`configs/screening.toml`). The vote rule is in `src/screening.py`: exclude only "
           "when all three exclude; include when at least two include and none excludes; "
           + disagreement, "",
           "## Inputs", "",
           "| | Records |", "|---|---|",
           "| identified (`references.json`) | %d |" % n_identified,
           "| to screen, after the duplicate rule and any records dropped before screening "
           "| %d |" % n, ""]

    out += ["## Decisions by screener", "",
            "| Screener | Include | Uncertain | Exclude | Missing | Outside the records to screen |",
            "|---|---|---|---|---|---|"]
    for m in models:
        c = Counter(d.decision for k, d in votes[m].items() if k in wanted)
        missing = sum(1 for k in numbers if k not in votes[m])
        outside = sum(1 for k in votes[m] if k not in wanted)
        out.append("| %s | %d | %d | %d | %d | %d |" % (
            m, c["include"], c["uncertain"], c["exclude"], missing, outside))
    out += ["", "A missing decision leaves the record without a vote (outcome `incomplete`); "
            "a decision outside the records to screen (a removed duplicate, a dropped record, "
            "an unknown number) is ignored.", ""]

    out += ["## Agreement between screeners", "",
            "Over the records both screeners decided. Kappa is Cohen's, weighted (%s) over "
            "exclude < uncertain < include." % weights, "",
            "| Pair | Records | Agreeing | Share | Weighted kappa |", "|---|---|---|---|---|"]
    for a, b, both, agree, k in pairs:
        out.append("| %s, %s | %d | %d | %s | %s |" % (a, b, both, agree, pct(agree, both), fmt_kappa(k)))
    out.append("")

    outcomes = Counter(r["outcome"] for r in rows)
    unanimous_inc = sum(1 for r in rows if r["outcome"] == "include"
                        and all(d.decision == "include" for d in r["ballot"]))
    out += ["## Outcome of the vote", "",
            "| Outcome | Records |", "|---|---|",
            "| exclude (all three exclude) | %d |" % outcomes["exclude"],
            "| include (at least two include, none excludes) | %d |" % outcomes["include"],
            "| &nbsp;&nbsp; of which all three include | %d |" % unanimous_inc,
            "| disagreement | %d |" % outcomes["disagreement"],
            "| incomplete (a screener gave no decision) | %d |" % outcomes["incomplete"],
            "| total | %d |" % len(rows), ""]
    patterns = Counter((tuple(sorted((d.decision for d in r["ballot"]), key=sc.RANK.get, reverse=True)),
                        r["outcome"]) for r in rows if r["outcome"] not in ("", "incomplete"))
    out += ["Every combination of votes, in any order of screeners:", "",
            "| Votes | Outcome | Records |", "|---|---|---|"]
    for (ballot, outcome), count in sorted(patterns.items(), key=lambda kv: (-kv[1], kv[0])):
        out.append("| %s | %s | %d |" % (", ".join(ballot), outcome, count))
    out.append("")

    final = Counter((r["basis"], r["decision"]) for r in rows if r["basis"])
    out += ["## Decisions", "",
            "The decision each record carries into the flow diagram, by what decided it.", "",
            "| Basis | Include | Uncertain | Exclude | No decision |", "|---|---|---|---|---|"]
    for basis in ("vote", "resolution") + (("rule",) if settled else ()) + (
            "not named", "calibration", "validation", "adjudication", "spot check", "escape",
            "unresolved"):
        cells = [final[(basis, d)] for d in ("include", "uncertain", "exclude")]
        out.append("| %s | %d | %d | %d | %d |" % (basis, cells[0], cells[1], cells[2],
                                                    final[(basis, "")]))
    no_decision = sum(1 for r in rows if not r["decision"])
    out += ["", "Records with no decision yet (unresolved disagreements and incomplete "
            "votes): %d. `make-tables` reports them as not yet screened." % no_decision, ""]
    if gate_cfg:
        out += render_gate(rows, gate_cfg, outputs)

    excluded = [r for r in rows if r["decision"] == "exclude"]
    by_rule = Counter(r["rule"] for r in excluded)
    per_model = {m: Counter(r["labels"][i] for r in rows
                            if r["ballot"][i] is not None and r["ballot"][i].decision == "exclude")
                 for i, m in enumerate(models)}
    labels = sorted(set(by_rule) | {lab for c in per_model.values() for lab in c}, key=sc.label_order)
    # The precedence and the person's resolutions are described only where they apply.
    precedence = "".join(
        ", after rule %d's precedence over rule %d is applied to the record: when any of its "
        "reasons names rule %d, the reasons naming rule %d count under rule %d" % (a, b, a, b, a)
        for a, b in prefer)
    resolved = not settled or any(r["basis"] == "resolution" for r in rows)
    out += ["## Exclusions by rule", "",
            "The criterion each exclusion is counted under. For a unanimous exclusion, the "
            "rule at least two of the three reasons cite (`no majority` otherwise)"
            + precedence + "." + (
                " For a resolved disagreement, the rule the person's reason cites."
                if resolved else "") + (
                " For a disagreement settled by rule, the rule the excluding reasons cite (the "
                "one reason's when a single screener excludes)." if settled else "") +
            " The columns per screener count every exclusion that screener made, by the rule "
            "its own reason cites.", "",
            "| Rule | Excluded | " + " | ".join(models) + " |",
            "|---|---|" + "---|" * len(models)]
    for lab in labels:
        out.append("| %s | %d | %s |" % (lab, by_rule.get(lab, 0),
                                         " | ".join(str(per_model[m].get(lab, 0)) for m in models)))
    out.append("| total | %d | %s |" % (len(excluded), " | ".join(
        str(sum(per_model[m].values())) for m in models)))
    out.append("")

    if extras:
        out += ["## Notes", ""] + ["- " + e for e in extras] + [""]
    return "\n".join(out)


def render_disagreements(rows, by_number, models, sheet="results/screening/consensus/"
                         "screening-disagreements.csv", save_as="datasets/screening-resolutions.csv"):
    items = on_sheet(rows)
    open_ = sum(1 for r in items if r["basis"] == "unresolved")
    not_named = sum(1 for r in rows if r["basis"] == "not named")
    out = ["# Disagreements to decide", "",
           "Generated by `runners/screening_consensus.py`. Each record below split the three "
           "model screeners. Decide it against `screening-criteria.md`, with a reason naming "
           "the rule and, for an exclusion, the sentence that decides it. Record the decision "
           "in `%s` (columns decision, confidence, reason, evidence, decided_by) and save it "
           "as `%s`; refer a record you cannot decide to the advisor." % (sheet, save_as), "",
           "%d disagreements; %d still to decide." % (len(items), open_), ""]
    if not_named:
        out += ["Only disagreements whose record names the flexible job shop are listed. %d "
                "further disagreements name none, in their title, abstract or any screener's "
                "reason; they are not resolved and their full text is not sought."
                % not_named, ""]
    for r in items:
        rec = by_number[r["number"]]
        out += sc.record_block(rec)
        out += ["| Screener | Decision | Confidence | Reason | Evidence |", "|---|---|---|---|---|"]
        for m, d in zip(models, r["ballot"]):
            out.append("| %s | %s | %s | %s | %s |" % (m, d.decision, d.confidence,
                                                     sc.cell(d.reason), sc.cell(d.evidence)))
        out.append("")
        if r["basis"] == "resolution":
            out += ["Decided: **%s**. %s" % (r["decision"], r["reason"]), ""]
    return "\n".join(out)


def on_sheet(rows):
    """The disagreements put to the person: every disagreement but those the gate sets
    aside."""
    return [r for r in rows if r["outcome"] == "disagreement" and r["basis"] != "not named"]


FULLTEXT_FIELDS = ["number", "title", "first_author", "year", "venue", "doi", "openalex_id",
                   "is_open_access", "decision", "basis", "named"]
ABSTRACT_FIELDS = ["number", "title", "first_author", "year", "venue", "doi", "decision", "basis"]


def write_gate_lists(paths, rows, by_number):
    """The full texts to seek (markdown and CSV) and the inclusions coded from title and
    abstract (CSV), in record order."""
    def fields(r, names):
        rec = by_number[r["number"]]
        values = {"number": r["number"], "title": rec.title, "first_author": rec.first_author,
                  "year": rec.year or "", "venue": rec.venue, "doi": rec.doi,
                  "openalex_id": rec.openalex_id,
                  "is_open_access": "yes" if rec.is_open_access else "no",
                  "decision": r["decision"], "basis": r["basis"], "named": r["named"]}
        return {k: values[k] for k in names}

    full = [r for r in rows if r["gate"] == "full text"]
    for key, chosen, names in (("fulltext_csv", full, FULLTEXT_FIELDS),
                               ("abstract_only_csv", [r for r in rows if r["gate"] == "abstract only"],
                                ABSTRACT_FIELDS)):
        with open(paths[key], "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=names)
            w.writeheader()
            for r in chosen:
                w.writerow(fields(r, names))
    open_access = sum(1 for r in full if by_number[r["number"]].is_open_access)
    lines = ["# Full texts to seek", "",
             "Generated by `runners/screening_consensus.py`. Every record carried forward from "
             "title and abstract that names the flexible job shop, in record order: %d records, "
             "%d of them marked open access in the corpus. A disagreement still to be decided is "
             "added once the person carries it forward." % (len(full), open_access), "",
             "| Record | Title | First author | Year | Venue | DOI | Open access | Decision | Named in |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in full:
        v = fields(r, FULLTEXT_FIELDS)
        lines.append("| %d | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            v["number"], sc.cell(v["title"]), sc.cell(v["first_author"]), v["year"],
            sc.cell(v["venue"]), sc.cell(v["doi"]), v["is_open_access"], v["decision"],
            "title or abstract" if v["named"] == "text" else "a screener's reason"))
    with open(paths["fulltext_md"], "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def write_outputs(cfg, rows, by_number, models, resolutions, resolved_raw, gated=False,
                  settled=False):
    """Write the consensus, the votes and, unless the disagreements are settled by rule
    (`settled`), the person's disagreements sheet; with `gated`, the full-text lists."""
    outputs = cfg["outputs"]
    keys = ["consensus", "votes"] + ([] if settled else ["disagreements_md", "disagreements_csv"])
    if gated:
        keys += ["fulltext_md", "fulltext_csv", "abstract_only_csv"]
    paths = {k: resolve(outputs[k]) for k in keys}
    for p in paths.values():
        os.makedirs(os.path.dirname(p), exist_ok=True)
    if not settled:
        # The disagreements sheet is regenerated on every run; decisions typed on it and not
        # yet saved as the resolutions file would be lost.
        pending = sc.unsaved(paths["disagreements_csv"], resolutions,
                             sc.issued(paths["disagreements_csv"]))
        if pending:
            raise SystemExit(sc.differ_message(paths["disagreements_csv"],
                                               cfg["inputs"]["resolutions"], pending))
    page = None if settled else page_settings(cfg)
    try:
        _write(paths, rows, by_number, models, resolved_raw,
               (outputs["disagreements_csv"], cfg["inputs"]["resolutions"]), page)
        if not settled:
            sc.record_issued(paths["disagreements_csv"])
        if gated:
            write_gate_lists(paths, rows, by_number)
    except PermissionError as exc:
        raise SystemExit("Cannot write %s: close it in Excel and run again." % exc.filename)
    if page is not None:
        paths["disagreements_html"] = sc.page_path(paths["disagreements_csv"])
    return paths


DISAGREEMENT_PAGE_INTRO = [
    "Each record below split the three model screeners; their answers are under the "
    "abstract. Decide it against the criteria, with a reason naming the rule and, for an "
    "exclusion, the sentence that decides it. Refer a record you cannot decide to the advisor.",
    "For a record without an abstract, you may open the paper by its DOI and read the abstract "
    "at the publisher; say so in the reason (for example \"Inclusion 1 to 3: abstract read at "
    "the publisher; ...\"). Write who decided in \"Decided by\"."]


def _write(paths, rows, by_number, models, resolved_raw, sheet_names, page=None):
    """`sheet_names`: the disagreements sheet and the file it is saved as, as the config
    names them, for the instructions written above the disagreements. With `page` (from
    page_settings), the disagreements are also written as a screening page beside the
    sheet, with the three models' answers and a link to each paper."""
    fields = ["number", "decision", "confidence", "reason", "evidence",
              "title", "venue", "year", "work_type", "rule", "basis", "gate"]
    with open(paths["consensus"], "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            if not r["decision"]:
                continue
            rec = by_number[r["number"]]
            w.writerow({"number": r["number"], "decision": r["decision"],
                        "confidence": r["confidence"], "reason": r["reason"],
                        "evidence": r["evidence"], "title": rec.title, "venue": rec.venue,
                        "year": rec.year or "", "work_type": rec.work_type,
                        "rule": r["rule"], "basis": r["basis"], "gate": r["gate"]})

    vote_fields = ["number", "title"]
    for m in models:
        vote_fields += ["%s_decision" % m, "%s_confidence" % m, "%s_rule" % m]
    vote_fields += ["outcome", "decision", "basis", "rule", "named", "gate"]
    with open(paths["votes"], "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=vote_fields)
        w.writeheader()
        for r in rows:
            row = {"number": r["number"], "title": by_number[r["number"]].title,
                   "outcome": r["outcome"], "decision": r["decision"], "basis": r["basis"],
                   "rule": r["rule"], "named": r["named"], "gate": r["gate"]}
            for m, d, lab in zip(models, r["ballot"], r["labels"]):
                row["%s_decision" % m] = d.decision if d else ""
                row["%s_confidence" % m] = d.confidence if d else ""
                row["%s_rule" % m] = lab
            w.writerow(row)

    if "disagreements_md" not in paths:    # settled by rule: no sheet for a person
        return
    with open(paths["disagreements_md"], "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_disagreements(rows, by_number, models, *sheet_names))

    fill = ["number", "title"] + ["%s_decision" % m for m in models] + \
           ["decision", "confidence", "reason", "evidence", "decided_by"]
    with open(paths["disagreements_csv"], "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fill)
        w.writeheader()
        for r in on_sheet(rows):
            prior = resolved_raw.get(r["number"], {})
            row = {"number": r["number"], "title": by_number[r["number"]].title}
            for m, d in zip(models, r["ballot"]):
                row["%s_decision" % m] = d.decision
            for k in ("decision", "confidence", "reason", "evidence", "decided_by"):
                row[k] = (prior.get(k) or "").strip()
            w.writerow(row)

    if page is not None:
        records = []
        for r in on_sheet(rows):
            prior = resolved_raw.get(r["number"], {})
            answer = {k: (prior.get(k) or "").strip()
                      for k in ("decision", "confidence", "reason", "evidence", "decided_by")}
            records.append(sc.page_record(
                by_number[r["number"]], answer if any(answer.values()) else None,
                models=list(zip(models, r["ballot"])),
                cells={"%s_decision" % m: d.decision for m, d in zip(models, r["ballot"])},
                link=True))
        sc.write_page(sc.page_path(paths["disagreements_csv"]), page, "Disagreements to decide",
                      "disagreements", sheet_names[1], fill, DISAGREEMENT_PAGE_INTRO, records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_config_arguments(parser)
    args = parser.parse_args()
    cfg = load_config(args.config, args.override)

    # Only a [gate] reads the abstracts (src/withheld.py).
    gate = bool(cfg.get("gate"))
    if gate:
        withheld.require(resolve(cfg["inputs"]["references"]), "screening-consensus's [gate]")
    records, screen_records = load_corpus(cfg, abstracts=gate)
    by_number = {r.number: r for r in records}
    numbers = [r.number for r in screen_records]
    votes = load_models(cfg)
    models = list(votes)
    require_calibration(cfg, screen_records, votes)

    resolutions, resolved_raw = load_person(cfg, "resolutions")
    incomplete = [n for n, d in resolutions.items()
                  if not d.reason or not (resolved_raw[n].get("decided_by") or "").strip()]
    if incomplete:
        raise SystemExit("Every resolution needs a reason and decided_by; missing for: %s"
                         % ", ".join(map(str, sorted(incomplete))))
    resolved_by = {n: resolved_raw[n]["decided_by"].strip() for n in resolutions}
    # On the records a second person adjudicated, his decision takes the place of the first
    # person's: a removed record he excludes is not carried forward.
    adjudication = adjudicated(cfg)
    rescues = [("calibration", calibration_rescue(cfg)),
               ("adjudication", adjudication),
               ("validation", {n: d for n, d in person_validation(cfg).items()
                               if n not in adjudication}),
               ("spot check", spot_check_decisions(cfg)),
               ("escape", load_person(cfg, "escape")[0])]

    label = labeller(cfg)
    prefer = [tuple(p) for p in cfg["rules"].get("prefer", [])]
    named = named_records(cfg, screen_records, votes)
    settle = bool(cfg["rules"].get("settle_disagreements"))
    rows = combine(numbers, votes, label, resolutions, resolved_by, rescues, prefer, named,
                   settle)
    weights = cfg["agreement"]["kappa_weights"]
    pairs = pairwise(votes, numbers, weights)

    extras = []
    no_rule = [r["number"] for r in rows if r["decision"] == "exclude"
               and (r["rule"] in ("none named", "no majority") or r["rule"].startswith("criterion"))]
    if no_rule:
        extras.append("%d exclusions are not counted under a single rule (`none named`, "
                      "`no majority`, or a bare criterion number that could be either list); "
                      "their reasons are in `%s`." % (len(no_rule), cfg["outputs"]["votes"]))
    report = render(len(records), numbers, votes, rows, pairs, weights, extras,
                    cfg.get("gate") if named is not None else None, cfg["outputs"], settle,
                    prefer)
    paths = write_outputs(cfg, rows, by_number, models, resolutions, resolved_raw,
                          gated=named is not None, settled=settle)
    report_path = resolve(cfg["outputs"]["consensus_report"])
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(report)

    outcomes = Counter(r["outcome"] for r in rows)
    decided = Counter(r["decision"] for r in rows if r["decision"])
    print("records to screen : %d" % len(numbers))
    print("vote              : %s" % ", ".join("%s %d" % (k, outcomes[k]) for k in
                                               ("exclude", "include", "disagreement", "incomplete")))
    print("decisions         : %s; no decision %d" % (
        ", ".join("%s %d" % (k, decided[k]) for k in ("include", "uncertain", "exclude")),
        sum(1 for r in rows if not r["decision"])))
    if settle:
        ruled = Counter(r["decision"] for r in rows if r["basis"] == "rule")
        print("settled by rule   : %s" % ", ".join(
            "%s %d" % (k, ruled[k]) for k in ("include", "uncertain", "exclude")))
    if named is not None:
        gates = Counter(r["gate"] for r in rows if r["gate"])
        print("disagreements     : %d on the person's sheet, %d not naming the flexible job shop "
              "(set aside)" % (len(on_sheet(rows)),
                               sum(1 for r in rows if r["basis"] == "not named")))
        print("full-text gate    : sought %d, coded from the abstract %d, set aside %d" % (
            gates["full text"], gates["abstract only"], gates["set aside"]))
    for a, b, both, agree, k in pairs:
        print("agreement %s-%s: %d of %d, weighted kappa %s" % (a, b, agree, both, fmt_kappa(k)))
    print("wrote %s" % ", ".join(rel(p) for p in list(paths.values()) + [report_path]))


if __name__ == "__main__":
    main()
