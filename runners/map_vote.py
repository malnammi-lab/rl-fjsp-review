"""Vote the three models' codes into the map, and measure their agreement per axis.

The scheme's rules (src/mapcodes.py) make each model's codes consistent, and each cell takes
the models' majority (protocol, Two tiers). An axis counts toward the core's coverage when
the models' kappa reaches [agreement] kappa_bar. Reads configs/map.toml, the screening's
decisions, one coding file per model and a person's codes for included records no model
coded. The coded records must be exactly the screening's inclusions. Writes datasets/map.csv,
and map-votes.csv, map-implications.csv, map-agreement.csv and map-vote.md in results/map/.

Run: python runners/run_all.py --only map-vote
"""

import argparse
import csv
import itertools
import os
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import mapcodes as mc  # noqa: E402
from src import screening as sc  # noqa: E402
from runners.screening_consensus import load_config, rel, resolve  # noqa: E402


def load_coders(cfg, axes):
    """({model: {number: cells}}, {number: title, venue, year, work_type}), in config order;
    refuses to run on other than three models."""
    coders = cfg["coders"]
    if len(coders) != 3:
        raise SystemExit("the map's vote is written for three models; %d configured"
                         % len(coders))
    missing = [p for p in coders.values() if not os.path.isfile(resolve(p))]
    if missing:
        raise SystemExit(
            "No map yet: %s not found (the models' coding files; datasets/MANIFEST.md)."
            % ", ".join(missing))
    coded, meta = {}, {}
    for model, path in coders.items():
        coded[model], found = mc.read_codes(resolve(path), axes)
        for n, m in found.items():
            meta.setdefault(n, m)
    return coded, meta


def included(cfg):
    """The records the screening included, in order."""
    path = resolve(cfg["inputs"]["screening"])
    if not os.path.isfile(path):
        raise SystemExit("%s not found: the screening's decisions, whose inclusions the map "
                         "codes." % path)
    return sorted(n for n, d in sc.read_decisions(path)[0].items() if d.decision == "include")


def short(numbers, limit=20):
    shown = ", ".join(map(str, numbers[:limit]))
    return shown + (" and %d more" % (len(numbers) - limit) if len(numbers) > limit else "")


def load_person(cfg, axes):
    """({number: cells}, {number: title, venue, year, work_type}) of the included records a
    person coded instead of the models ([map] by_person), read as a model's coding file is;
    empty when the config names no such file."""
    path = cfg.get("map", {}).get("by_person")
    if not path:
        return {}, {}
    if not os.path.isfile(resolve(path)):
        raise SystemExit("%s not found: the codes a person gave the included records the "
                         "models did not code ([map] by_person of the config)." % resolve(path))
    return mc.read_codes(resolve(path), axes)


def check_records(coded, numbers, by_person=()):
    """Refuses unless every model coded exactly the included records but those a person
    coded, and the person only included records that no model coded."""
    person = set(by_person)
    stray = sorted(person - set(numbers))
    if stray:
        raise SystemExit("A person coded %s, which the screening did not include ([map] "
                         "by_person)." % short(stray))
    wanted, problems = set(numbers) - person, []
    for model, codes in coded.items():
        absent = sorted(wanted - set(codes))
        twice = sorted(person & set(codes))
        extra = sorted(set(codes) - wanted - person)
        if absent:
            problems.append("%s has not coded %d included record(s): %s"
                            % (model, len(absent), short(absent)))
        if twice:
            problems.append("%s coded %s, which a person coded too ([map] by_person): one "
                            "coding per record" % (model, short(twice)))
        if extra:
            problems.append("%s coded %d record(s) the screening did not include: %s"
                            % (model, len(extra), short(extra)))
    if problems:
        raise SystemExit("; ".join(problems) + ". The map codes every included record and no "
                         "other; a record no model coded is coded by a person ([map] by_person).")


def fmt(k):
    return "" if k is None else "%.3f" % k


def agreement_rows(axes, implied, voted, numbers, bar, not_coverage):
    """(the rows of map-agreement.csv: one per axis, each followed by one per code, then
    `not-stated`; the axes that count toward the core's coverage). An axis that
    `not_coverage` names never steers step 2: it has no kappa compared with the bar, and its
    multiclass kappa is its agreement."""
    models = list(implied)
    pairs = list(itertools.combinations(models, 2))
    rows, coverage = [], []
    for axis in axes:
        steers = axis.name not in not_coverage
        held = mc.held_codes(axis, voted, numbers)
        k, by_pair, per_code, multiclass = mc.agreement(axis, implied, numbers, held)
        if not steers:
            k, by_pair = None, {}
        inside = set(mc.counted(axis, held))
        cells = [[implied[m][n][axis.name] for m in models] for n in numbers]
        counts = steers and k is not None and k >= bar
        if counts:
            coverage.append(axis.name)
        row = {"axis": axis.name, "code": "", "kind": "list" if axis.multi else "single",
               "kappa": fmt(k), "kappa_multiclass": fmt(multiclass),
               "unanimous": sum(mc.unanimous(c) for c in cells),
               "no_majority": sum(mc.no_majority(axis, c) for c in cells), "records": "",
               "in_axis_kappa": "", "coverage": "yes" if counts else "no"}
        row.update({"kappa_%s_%s" % p: fmt(by_pair.get(p)) for p in pairs})
        rows.append(row)
        for code in axis.codes + (mc.NOT_STATED,):
            code_k, code_pairs = per_code[code]
            row = {"axis": axis.name, "code": code, "kind": "", "kappa": fmt(code_k),
                   "kappa_multiclass": "", "unanimous": "", "no_majority": "", "coverage": "",
                   "in_axis_kappa": "" if not steers else "yes" if code in inside else "no",
                   "records": sum(mc.has(axis, voted[n][axis.name], code) for n in numbers)}
            row.update({"kappa_%s_%s" % p: fmt(code_pairs.get(p)) for p in pairs})
            rows.append(row)
    return rows, coverage


def pct(part, whole):
    return "%.1f%%" % (100.0 * part / whole) if whole else "n/a"


def render(config, models, numbers, rows, changes, coverage, agreement_cfg, outputs,
           person=()):
    n = len(numbers)
    tally = Counter((who, rule.name) for _, who, rule, *_ in changes)
    by_person = sorted(person)
    whos = models + ["vote"] + (["person"] if by_person else [])
    if by_person:
        held = ("%d records, the screening's inclusions: %d coded by %s from their titles and "
                "abstracts (protocol, Two tiers), and %d (%s) by a person, from the title and "
                "abstract with the same scheme. A record a person coded takes the person's "
                "codes after the rules, without a vote, and is not in the agreement below, "
                "which is the models'." % (n, n - len(by_person), ", ".join(models),
                                            len(by_person), ", ".join(map(str, by_person))))
    else:
        held = ("%d records, the screening's inclusions, each coded by %s from its title and "
                "abstract (protocol, Two tiers)." % (n, ", ".join(models)))
    lines = [
        "# The map: the vote and the models' agreement", "",
        "Written by `runners/map_vote.py` from `%s`; do not edit, rerun the runner." % rel(config),
        "", held, "",
        "The vote: a cell takes the code at least two models give, code by code on a list "
        "axis, and is `not-stated` when no code has a majority; on %s, whose codes are "
        "levels, it takes the highest level at least two models reach." % ", ".join(
            "`%s`" % a for a in mc.LEVELS),
        "", "## The scheme's rules", "",
        "Cells each rule changed in each model's codes, before the vote, and in the voted "
        "codes%s. Every changed cell is listed in `%s`." % (
            ", and in the codes a person gave" if by_person else "", outputs["implications"]),
        "", "| Rule | %s |" % " | ".join(models + ["after the vote"] + whos[len(models) + 1:]),
        "| --- |" + " ---: |" * len(whos)]
    for rule in mc.IMPLICATIONS:
        lines.append("| %s | %s |" % (rule.name, " | ".join(
            str(tally[(who, rule.name)]) for who in whos)))
    never = agreement_cfg.get("not_coverage", [])
    lines += [
        "", "## Agreement per axis", "",
        "Kappa: the agreement compared with the bar. Each code is read as present or absent, "
        "Cohen's kappa is taken between two models on their codes after the rules and "
        "averaged over the three pairs, and the axis's kappa is the mean over its categories "
        "at step 2 of the core rule that the map holds: every code but %s that the voted map "
        "gives to at least one record. The kappas of the other codes are shown below and are "
        "not in the mean; an axis with no such category does not steer. Multiclass kappa: on "
        "a single axis, Cohen's kappa over all its codes as given, for reference.%s No "
        "majority: cells the vote makes `not-stated` because no code has a majority. "
        "Coverage: the axis counts toward the core's coverage minimum, its kappa being at "
        "least %s." % (
            ", ".join("`%s`" % c for c in mc.NOT_CATEGORIES),
            " %s never steers step 2, so it has no kappa compared with the bar, and its "
            "multiclass kappa is its agreement." % ", ".join("`%s`" % a for a in never)
            if never else "",
            agreement_cfg["kappa_bar"]),
        "", "| Axis | Kind | Kappa | Multiclass kappa | All three agree | No majority | Coverage |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |"]
    for row in rows:
        if not row["code"]:
            lines.append("| `%s` | %s | %s | %s | %d (%s) | %d | %s |" % (
                row["axis"], row["kind"], row["kappa"] or "n/a", row["kappa_multiclass"],
                row["unanimous"], pct(row["unanimous"], n - len(by_person)), row["no_majority"],
                row["coverage"]))
    lines += ["", "Axes that count toward the core's coverage: %s." % (
        ", ".join("`%s`" % a for a in coverage) or "none")]
    lines += [
        "", "## The map's codes", "",
        "Records the map gives each code, among the records the models coded (on a list axis, "
        "a record counts once under each of its codes), the code's kappa, read as present or "
        "absent, and whether it is in the axis's kappa.", "",
        "| Axis | Code | Records | Kappa | In the axis's kappa |",
        "| --- | --- | ---: | ---: | --- |"]
    for row in rows:
        if row["code"]:
            lines.append("| `%s` | `%s` | %d | %s | %s |" % (
                row["axis"], row["code"], row["records"], row["kappa"], row["in_axis_kappa"]))
    return "\n".join(lines) + "\n"


def write_csv(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "map-vote.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")
    args = parser.parse_args()
    cfg = load_config(args.config, args.override)

    axes = mc.load_axes(resolve(cfg["inputs"]["schema"]))
    coded, meta = load_coders(cfg, axes)
    models = list(coded)
    person, person_meta = load_person(cfg, axes)
    numbers = included(cfg)
    check_records(coded, numbers, person)
    by_models = [n for n in numbers if n not in person]
    voted, implied, changes = mc.combine(coded, axes, by_models)
    for n in sorted(person):
        voted[n], changed = mc.imply(person[n], axes)
        changes += [(n, "person") + c for c in changed]
        meta.setdefault(n, person_meta[n])
    order = {who: i for i, who in enumerate(models + ["vote", "person"])}
    changes.sort(key=lambda c: (c[0], order[c[1]]))

    out = {key: resolve(path) for key, path in cfg["outputs"].items()}
    names = [a.name for a in axes]
    write_csv(out["map"], ["number"] + names + list(mc.META),
              [{"number": n, **{a: mc.show(voted[n][a]) for a in names}, **meta[n]}
               for n in numbers])
    vote_fields = ["number", "title", "coded_by"]
    for a in names:
        vote_fields += ["%s_%s" % (a, m) for m in models] + [a]
    write_csv(out["votes"], vote_fields,
              [{"number": n, "title": meta[n]["title"],
                "coded_by": "person" if n in person else "models",
                **{"%s_%s" % (a, m): mc.show(implied[m][n][a]) if n in implied[m] else ""
                   for a in names for m in models},
                **{a: mc.show(voted[n][a]) for a in names}} for n in numbers])
    write_csv(out["implications"], ["number", "model", "rule", "axis", "before", "after"],
              [{"number": n, "model": who, "rule": rule.name, "axis": axis,
                "before": mc.show(before), "after": mc.show(after)}
               for n, who, rule, axis, before, after in changes])
    agreement_cfg = cfg["agreement"]
    # The agreement is the models': over the records they coded, and the categories their
    # voted codes hold.
    rows, coverage = agreement_rows(axes, implied, voted, by_models, agreement_cfg["kappa_bar"],
                                    agreement_cfg.get("not_coverage", []))
    pairs = ["kappa_%s_%s" % p for p in itertools.combinations(models, 2)]
    write_csv(out["agreement"], ["axis", "code", "kind"] + pairs +
              ["kappa", "kappa_multiclass", "unanimous", "no_majority", "records",
               "in_axis_kappa", "coverage"], rows)
    os.makedirs(os.path.dirname(out["report"]), exist_ok=True)
    with open(out["report"], "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(args.config, models, numbers, rows, changes, coverage, agreement_cfg,
                        cfg["outputs"], person))

    tally = Counter(who for _, who, *_ in changes)
    print("records           : %d" % len(numbers))
    if person:
        print("coded by a person : %s" % ", ".join(map(str, sorted(person))))
    print("cells the rules changed: %s" % ", ".join(
        "%s %d" % (who, tally[who]) for who in models + ["vote"] + (["person"] if person else [])))
    print("coverage axes     : %s" % (", ".join(coverage) or "none"))
    print("written           : %s" % ", ".join(rel(p) for p in out.values()))


if __name__ == "__main__":
    main()
