"""Compute the PRISMA flow counts, so that the paper never restates them by hand.

Reads datasets/references.json, duplicates.csv, dropped.csv and screening.csv, then the
core's counts in results/core/core-flow.csv and core-texts-flow.csv when the config names
them. Writes results/tables/flow-counts.csv and flow-counts.tex. When screening.csv carries
the full-text gate, the records carried forward are split by it. A record that reached
screening without a decision gets its own row and a warning.

Run: python runners/run_all.py --only make-tables
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


def resolve(path):
    return os.path.normpath(os.path.join(REPO, path))


def rel(path):
    """Repo-relative path for printing; absolute when the path is on another drive.

    os.path.relpath raises on Windows when the two paths sit on different drives, and
    a runner must not crash on a progress line after its real work has succeeded.
    """
    try:
        return os.path.relpath(path, REPO)
    except ValueError:
        return path


def load_duplicates(path):
    """Record numbers from a list with a `number` column: the duplicates runners/deduplicate.py
    writes, or the records dropped before screening (datasets/dropped.csv). A byte-order mark,
    as Excel writes, is read through."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return {int(row["number"]) for row in csv.DictReader(fh)}


def load_gates(path):
    """{number: gate} from the consensus file's `gate` column (the full-text gate), or None
    for a file written without it, or whose every gate is empty (a screening run with no
    [gate])."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if "gate" not in [(f or "").strip() for f in (reader.fieldnames or [])]:
            return None
        gates = {}
        for row in reader:
            number = corpus._int((row.get("number") or "").strip())
            if number is not None:
                gates[number] = (row.get("gate") or "").strip()
        return gates if any(gates.values()) else None


def flow_counts(records, screening, removed=frozenset(), gates=None, dropped=frozenset()):
    """Every stage of the flow, derived rather than restated. A record is a duplicate when
    the duplicate rule removed it (`removed`) or the acquisition tool marked it. `dropped`
    holds the records removed before screening for another reason (no abstract and no DOI;
    protocol, Search strategy); a record in both lists counts once, as a duplicate. With
    `gates` (load_gates), the records carried forward are split by the full-text gate."""
    duplicates = [r for r in records
                  if r.number in removed or (r.raw.get("duplicate_of") not in (None, ""))]
    dup_ids = {r.number for r in duplicates}
    others = [r for r in records if r.number in dropped and r.number not in dup_ids]
    gone = dup_ids | {r.number for r in others}
    screened = [r for r in records if r.number not in gone]

    decisions = Counter(
        screening[r.number].decision for r in screened if r.number in screening
    )
    unscreened = corpus.unscreened(screened, screening)
    included = corpus.included(screened, screening)

    rows = [
        ("Identified, databases and registers", len(records)),
        ("Duplicates removed", len(duplicates)),
    ]
    if dropped:
        rows.append(("Removed for other reasons", len(others)))
    rows += [
        ("Screened on title and abstract", len(screened)),
        ("Excluded at screening", decisions.get("exclude", 0)),
        ("Uncertain at screening", decisions.get("uncertain", 0)),
        ("Included", decisions.get("include", 0)),
    ]
    # With a gate, uncertain records go on to it beside the included ones. Without one they
    # stop at screening, so the records carried forward are the included ones alone, already
    # counted above.
    if gates is not None:
        passed = Counter(gates.get(r.number, "") for r in included)
        rows += [
            ("Studies carried forward (included plus uncertain)", len(included)),
            ("Naming the flexible job shop: full text sought", passed["full text"]),
            ("Included, not naming it: coded from title and abstract", passed["abstract only"]),
            ("Uncertain, not naming it: set aside", passed["set aside"]),
        ]
    rows.append(("Not yet screened", len(unscreened)))
    return rows, unscreened


def load_flow(path):
    """{key: count} from a file of counts with the columns key, label, count (the core's
    counts, results/core/core-flow.csv, and its full texts', core-texts-flow.csv)."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {row["key"]: int(row["count"]) for row in csv.DictReader(fh)}


def core_rows(core, texts=None):
    """The flow from the map to the core: the candidates, the core after each step of its
    rule and the core itself (`core`, load_flow of core-flow.csv); then, with `texts`
    (load_flow of core-texts-flow.csv), the full texts sought, not retrieved and read. Refuses
    steps that do not add up to the core, and full texts that do not add up to the ones
    sought or are not the core's."""
    step3 = sum(n for k, n in core.items() if k.startswith("step3-") and k != "step3-cap")
    if core["step1"] + core["step2"] + step3 != core["core"]:
        raise SystemExit("The core's steps (%d, %d, %d) do not add up to the core (%d): rerun "
                         "runners/core_selection.py." % (core["step1"], core["step2"], step3,
                                                         core["core"]))
    rows = [("Candidates for the core: learner stated, each study once", core["candidates-once"]),
            ("The core, step 1: use beyond simulation", core["step1"]),
            ("The core, step 2: coverage", core["step2"]),
            ("The core, step 3: the places left", step3),
            ("The core, step 3: end-to-end, band 1", core["step3-end-to-end-band1"]),
            ("The core, step 3: end-to-end, band 2", core["step3-end-to-end-band2"]),
            ("The core, step 3: steering, band 1", core["step3-steering-band1"]),
            ("The core, step 3: steering, band 2", core["step3-steering-band2"]),
            ("The core, step 3: role-not-stated, band 1", core["step3-role-not-stated-band1"]),
            ("The core, step 3: role-not-stated, band 2", core["step3-role-not-stated-band2"]),
            ("The core, step 3: non-deep studies left out by the cap", core["step3-cap"]),
            ("Selected for full-text synthesis: the core", core["core"])]
    if texts is not None:
        if texts["sought"] != core["core"] or texts["read"] + texts["not-retrieved"] != texts["sought"]:
            raise SystemExit("The full texts sought (%d), read (%d) and not retrieved (%d) do not "
                             "add up, or are not the core's %d: rerun runners/core_texts.py."
                             % (texts["sought"], texts["read"], texts["not-retrieved"], core["core"]))
        rows += [("Full texts sought", texts["sought"]),
                 ("Full texts not retrieved", texts["not-retrieved"]),
                 ("Full texts coded", texts["read"])]
    return rows


def tex_escape(text):
    return text.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "tables.toml"))
    args = parser.parse_args()
    with open(args.config, "rb") as fh:
        cfg = tomllib.load(fh)

    inputs, outputs = cfg["inputs"], cfg["outputs"]
    refs_path = resolve(inputs["references"])
    screen_path = resolve(inputs["screening"])
    for label, path in (("references.json", refs_path), ("screening.csv", screen_path)):
        if not os.path.isfile(path):
            raise SystemExit(
                "%s not found at %s; see datasets/MANIFEST.md." % (label, path)
            )

    records = corpus.load_references(refs_path)
    screening = corpus.load_screening(screen_path)
    removed = set()
    if inputs.get("duplicates"):
        dup_path = resolve(inputs["duplicates"])
        if not os.path.isfile(dup_path):
            raise SystemExit("%s not found. Run the duplicate rule first: "
                             "python runners/run_all.py --only deduplicate" % dup_path)
        removed = load_duplicates(dup_path)
    dropped = set()
    if inputs.get("dropped"):
        drop_path = resolve(inputs["dropped"])
        if not os.path.isfile(drop_path):
            raise SystemExit("%s not found: the records dropped before screening (protocol, "
                             "Search strategy)." % drop_path)
        dropped = load_duplicates(drop_path)
    rows, unscreened = flow_counts(records, screening, removed, load_gates(screen_path),
                                   dropped)
    if inputs.get("core_flow"):
        core_path = resolve(inputs["core_flow"])
        if not os.path.isfile(core_path):
            raise SystemExit("%s not found: the core's counts, written by "
                             "runners/core_selection.py." % core_path)
        texts = None
        if inputs.get("texts_flow"):
            texts_path = resolve(inputs["texts_flow"])
            if not os.path.isfile(texts_path):
                raise SystemExit("%s not found: the full texts' counts, written by "
                                 "runners/core_texts.py from datasets/core-texts.csv." % texts_path)
            texts = load_flow(texts_path)
        rows += core_rows(load_flow(core_path), texts)

    out_dir = resolve(inputs["out_dir"])
    os.makedirs(out_dir, exist_ok=True)

    csv_path = os.path.join(out_dir, outputs["csv"])
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stage", "records"])
        w.writerows(rows)

    tex_path = os.path.join(out_dir, outputs["tex"])
    with open(tex_path, "w", encoding="utf-8", newline="\n") as fh:
        # Leading percent signs are LaTeX comments. The first line is %-formatted, so
        # its literal percent is doubled; a bare "% G" would be read as a conversion spec.
        fh.write("%% Generated by runners/make_tables.py from %s.\n"
                 % ", ".join(inputs[k] for k in ("references", "screening", "core_flow",
                                                  "texts_flow") if inputs.get(k)))
        fh.write("% Do not edit. Regenerate: python runners/run_all.py --only make-tables\n")
        for stage, n in rows:
            fh.write("%s & %d \\\\\n" % (tex_escape(stage), n))

    for stage, n in rows:
        print("  %-52s %6d" % (stage, n))
    if unscreened:
        print("\nWARNING: %d record(s) reached screening with no decision. The flow diagram "
              "is not reportable until they are screened:" % len(unscreened))
        for r in unscreened[:10]:
            print("    [%d]" % r.number)
        if len(unscreened) > 10:
            print("    ... and %d more" % (len(unscreened) - 10))
    print("\nwrote %s and %s" % (rel(csv_path), rel(tex_path)))


if __name__ == "__main__":
    main()
