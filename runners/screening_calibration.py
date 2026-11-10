"""Compare the calibration rounds: batch 01 screened by the three models and by the person.

Writes the person's blind sheet for batch 01: calibration-sheet.md and .csv, with its page.
The sheet shows the abstracts, so it is written beside the authors' copy of the records, and
only where that copy is in place (src/withheld.py). With --take-round N, it first copies the
models' batch 01 decisions into round N. It does so only once the person's own file for that
round decides every record of the batch. Each complete round under [calibration] dir gets
calibration-round-<N>.md. It shows the decisions side by side, agreement and weighted kappa
per pair, and the records decided differently, without their abstracts. The person's
decisions are locked per round. Reads the corpus and the decision files. The reports and the
lock go to results/screening/calibration/.

Run: python runners/run_all.py --only screening-calibration
"""

import argparse
import csv
import hashlib
import os
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus  # noqa: E402
from src import screening as sc  # noqa: E402
from src import withheld  # noqa: E402
from runners.screening_consensus import (  # noqa: E402
    add_config_arguments, fmt_kappa, labeller, load_config, load_corpus, page_settings, pct,
    rel, resolve)


def rounds(cal):
    """{round number: {screener: path}} for every round-<N> folder under the calibration
    folder, in round order."""
    return sc.rounds(resolve(cal["dir"]), cal["screeners"])


def take_round(cfg, rnd, numbers):
    """Bring the models' decisions on batch 01 into round `rnd`, once the person's own file
    for that round decides every record of batch 01 and nothing else.

    The models' files are read from [screeners] of the config, and only their batch 01 rows
    are written to <dir>/round-<rnd>/<model>.csv, so decisions a model made on later batches
    stay out of the round. A round already taken is never given other models' answers: new
    answers are a new round. The person's decisions are locked when the round is taken,
    since the person sees the models' tables from then on. Nothing is written unless every
    check passes."""
    cal = cfg["calibration"]
    people = [s for s in cal["screeners"] if s not in cal["models"]]
    folder = os.path.join(resolve(cal["dir"]), "round-%d" % rnd)
    wanted = set(numbers)
    person_path = os.path.join(folder, "%s.csv" % people[0])
    if not os.path.isfile(person_path):
        raise SystemExit("%s is not in place. The models' decisions are not brought into the "
                         "round before the person's own file." % person_path)
    person, blank, _ = sc.read_decisions(person_path)
    short, extra = sorted(wanted - set(person)), sorted(set(person) - wanted)
    if short or extra:
        raise SystemExit("%s must decide every record of batch 01 and nothing else (undecided: "
                         "%s; outside batch 01: %s). Nothing has been copied."
                         % (person_path, ", ".join(map(str, short)) or "none",
                            ", ".join(map(str, extra)) or "none"))
    lock = resolve(cfg["outputs"]["calibration_lock"])
    sc.verify_lock(lock, "round %d" % rnd, person, person_path)
    taken = {}
    for m in cal["models"]:
        src = resolve(cfg["screeners"][m])
        if not os.path.isfile(src):
            raise SystemExit("%s not found; collect %s's decisions first. Nothing has been copied."
                             % (src, m))
        with open(src, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            fields = reader.fieldnames
            rows = [row for row in reader if corpus._int((row.get("number") or "").strip()) in wanted]
        decided, _, _ = sc.read_decisions(src)
        missing = sorted(wanted - set(decided))
        if missing:
            raise SystemExit("%s has no decision for batch 01 records %s. Nothing has been copied."
                             % (src, ", ".join(map(str, missing))))
        dest = os.path.join(folder, "%s.csv" % m)
        if os.path.isfile(dest):
            before = sc.read_decisions(dest)[0]
            if any(before.get(n) != decided.get(n) for n in wanted):
                raise SystemExit("Round %d was already taken, and %s's batch 01 decisions have "
                                 "changed since. Take the new answers as a new round. Nothing has "
                                 "been copied." % (rnd, m))
        taken[m] = (fields, rows, len(decided) - len(wanted & set(decided)))
    os.makedirs(folder, exist_ok=True)
    sc.write_lock(lock, "round %d" % rnd, person)
    for m, (fields, rows, dropped) in taken.items():
        dest = os.path.join(folder, "%s.csv" % m)
        with open(dest, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        with open(dest, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        print("round %d: %s, %d batch 01 rows (%d decisions on later batches left out); "
              "SHA-256 %s" % (rnd, rel(dest), len(rows), dropped, digest))


def check_round(rnd, files, wanted):
    """Refuse a round whose files decide other records than batch 01's, or not all of them."""
    problems = []
    for s, got in files.items():
        extra = sorted(set(got) - wanted)
        short = sorted(wanted - set(got))
        if extra:
            problems.append("%s has decisions outside batch 01: %s" % (s, ", ".join(map(str, extra))))
        if short:
            problems.append("%s has no decision for: %s" % (s, ", ".join(map(str, short))))
    if problems:
        raise SystemExit("Round %d cannot be compared:\n  %s" % (rnd, "\n  ".join(problems)))


def compare(numbers, files, models, label, weights):
    """The comparison of one round. `files` is {screener: {number: Decision}}, every
    screener having decided every record of the batch."""
    names = list(files)
    rows = []
    for n in numbers:
        ballot = {s: files[s][n] for s in names}
        labels = {s: (label(d.reason) if d.decision == "exclude" else "") for s, d in ballot.items()}
        # Two exclusions under different rules are a difference too: the criteria were read
        # differently even though the decision agrees.
        rows.append({"number": n, "ballot": ballot, "labels": labels,
                     "vote": sc.vote(ballot[m].decision for m in models),
                     "differ": len({d.decision for d in ballot.values()}) > 1
                               or len({lab for lab in labels.values() if lab}) > 1})
    pairs = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            p = [(files[a][n].decision, files[b][n].decision) for n in numbers]
            pairs.append((a, b, len(p), sum(x == y for x, y in p), sc.weighted_kappa(p, weights)))
    return rows, pairs


def render(rnd, rows, pairs, by_number, models, people, weights):
    names = models + people
    out = ["# Calibration, round %d" % rnd, "",
           "Generated by `runners/screening_calibration.py` (`configs/screening.toml`) from "
           "the decisions of %s on batch 01 (%d records). The vote is the rule of "
           "`src/screening.py`." % (", ".join(names), len(rows)), "",
           "## Agreement", "",
           "Kappa is Cohen's, weighted (%s) over exclude < uncertain < include; `n/a` when "
           "both screeners used a single decision." % weights, "",
           "| Pair | Records | Agreeing | Share | Weighted kappa |", "|---|---|---|---|---|"]
    for a, b, n, agree, k in pairs:
        out.append("| %s, %s | %d | %d | %s | %s |" % (a, b, n, agree, pct(agree, n), fmt_kappa(k)))
    out.append("")
    for person in people:
        cross = Counter((r["vote"], r["ballot"][person].decision) for r in rows)
        out += ["The models' vote against %s's decision:" % person, "",
                "| Vote | %s include | %s uncertain | %s exclude |" % (person, person, person),
                "|---|---|---|---|"]
        for v in ("include", "disagreement", "exclude"):
            out.append("| %s | %d | %d | %d |" % (v, cross[(v, "include")], cross[(v, "uncertain")],
                                                 cross[(v, "exclude")]))
        out.append("")
    out += ["## Decisions", "",
            "An exclusion is shown with the rule its reason cites.", "",
            "| # | Title | " + " | ".join(names) + " | Vote |",
            "|---|---|" + "---|" * len(names) + "---|"]
    for r in rows:
        cells = []
        for s in names:
            d, lab = r["ballot"][s], r["labels"][s]
            cells.append(d.decision + (" (%s)" % lab if lab else ""))
        out.append("| %d | %s | %s | %s |" % (r["number"], sc.cell(by_number[r["number"]].title)[:80],
                                              " | ".join(cells), r["vote"]))
    out.append("")
    differing = [r for r in rows if r["differ"]]
    out += ["## Records the screeners decided differently", "",
            "%d of %d records. Each is a place where a criterion may be ambiguous." % (
                len(differing), len(rows)), ""]
    for r in differing:
        out += sc.record_block(by_number[r["number"]], abstract=False)
        out += ["| Screener | Decision | Confidence | Reason | Evidence |", "|---|---|---|---|---|"]
        for s in names:
            d = r["ballot"][s]
            out.append("| %s | %s | %s | %s | %s |" % (s, d.decision, d.confidence,
                                                     sc.cell(d.reason), sc.cell(d.evidence)))
        out.append("")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_config_arguments(parser)
    parser.add_argument("--take-round", type=int, default=None, metavar="N",
                        help="first bring the models' batch 01 decisions into round N, once the "
                             "person's round N file is complete")
    args = parser.parse_args()
    cfg = load_config(args.config, args.override)
    cal, outputs = cfg["calibration"], cfg["outputs"]
    models = list(cal["models"])
    people = [s for s in cal["screeners"] if s not in models]

    records, screen_records = load_corpus(cfg, abstracts=True)
    by_number = {r.number: r for r in records}
    batch = sc.calibration_batch(screen_records, cal)
    numbers = [r.number for r in batch]
    if args.take_round is not None:
        take_round(cfg, args.take_round, numbers)

    # The sheet is blank on purpose, in every round: a person re-screening batch 01 after an
    # amendment should not be anchored by the answers of the round before. Decisions typed on
    # it count as saved once they are in the newest round's file.
    left = cal.get("leave_out", [])
    left_text = " (left out of the round: %s)" % ", ".join(map(str, left)) if left else ""
    written = []
    if withheld.available(resolve(cfg["inputs"]["references"])):
        md = resolve(outputs["calibration_sheet_md"])
        csv_ = resolve(outputs["calibration_sheet_csv"])
        os.makedirs(os.path.dirname(md), exist_ok=True)
        target = "%s/round-N/%s.csv" % (cal["dir"].rstrip("/\\").replace(os.sep, "/"),
                                        people[0] if people else "person")
        saved = {}
        if people:
            _, latest = sc.latest_person_round(resolve(cal["dir"]), cal["screeners"], people[0])
            saved = sc.read_decisions(latest)[0] if latest else {}
        sc.write_sheet(batch, md, csv_, "Calibration: batch 01",
                       ["Screen each record against `screening-criteria.md`, without looking at "
                        "any model's table: decision (include, uncertain, exclude), confidence "
                        "(high, medium, low), a reason beginning with the rule as the criteria "
                        "label it (for example \"Inclusion 1 to 3:\" or \"Exclusion 2:\"), and "
                        "the sentence of the title or abstract that decides it. Fill `%s` and "
                        "save it as `%s`, N being the round (1 for the first)."
                        % (outputs["calibration_sheet_csv"], target)],
                       saved=saved, save_as=target, page=page_settings(cfg))
        written = [md, csv_]
        print("batch 01: %d records%s; calibration sheet written" % (len(numbers), left_text))
    else:
        print("batch 01: %d records%s; the calibration sheet shows the abstracts, which this "
              "repository withholds: not written" % (len(numbers), left_text))

    weights = cfg["agreement"]["kappa_weights"]
    for rnd, paths in rounds(cal).items():
        # Every file present is checked at once, so a file from the wrong batch is caught
        # before the rest of the round arrives.
        files = {s: sc.read_decisions(p)[0] for s, p in paths.items() if os.path.isfile(p)}
        check_round(rnd, files, set(numbers))
        missing = [s for s in paths if s not in files]
        if missing:
            print("round %d: waiting for %s" % (rnd, ", ".join(missing)))
            continue
        # The person's decisions are frozen from the moment the models' tables are beside
        # them; a complete round found without a lock entry (a copy of the repository made
        # after the round) is recorded now.
        lock = resolve(outputs["calibration_lock"])
        for person in people:
            if not sc.verify_lock(lock, "round %d" % rnd, files[person], paths[person]):
                sc.write_lock(lock, "round %d" % rnd, files[person])
        rows, pairs = compare(numbers, {s: files[s] for s in models + people}, models,
                              labeller(cfg), weights)
        report = resolve(outputs["calibration_report"].format(round=rnd))
        os.makedirs(os.path.dirname(report), exist_ok=True)
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render(rnd, rows, pairs, by_number, models, people, weights))
        written.append(report)
        print("round %d: %d of %d records decided differently" % (
            rnd, sum(r["differ"] for r in rows), len(rows)))
        for a, b, n, agree, k in pairs:
            print("  agreement %s-%s: %d of %d, weighted kappa %s" % (a, b, agree, n, fmt_kappa(k)))
    print("wrote %s" % ", ".join(rel(p) for p in written))


if __name__ == "__main__":
    main()
