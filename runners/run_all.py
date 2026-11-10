"""Run the steps of the review, which write the results the paper reports.

With the environment of repo_env.yml and the data files of datasets/MANIFEST.md, the steps
reproduce the committed results; README.md names those a clone can run. Each entry of
EXPERIMENTS is one step. It is named after what it produces and reads one config in configs/.
Outputs go under results/.

Run: python runners/run_all.py [--only <step> ...] [--list]
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# name -> (config file, command to run). Name it after the paper artifact it produces.
EXPERIMENTS = {
    # The protocol's closed lists -> OQL query file for the acquisition tool. Offline.
    "build-query": ("configs/search-query.toml", [sys.executable, "runners/build_query.py"]),
    # Descriptive numbers about the corpus that the method quotes: types and years, abstract
    # sources, abstracts the index does not serve, and whether retrieval depended on them.
    # Reads the abstracts, which the authors keep (src/withheld.py); in a clone it stops, and
    # its committed outputs stand.
    "corpus-profile": ("configs/corpus-profile.toml", [sys.executable, "runners/corpus_profile.py"]),
    # The duplicate rule: which records are removed before screening. Writes
    # datasets/duplicates.csv, which the screening steps leave out and make-tables counts.
    # Offline.
    "deduplicate": ("configs/deduplicate.toml", [sys.executable, "runners/deduplicate.py"]),
    # Screening at title and abstract (protocol, Screening); the rules are in
    # src/screening.py. Calibration: the person's blind sheet for batch 01, then the
    # comparison of each round. Validation: a blind sample of the records decided without a
    # person; once screened, agreement, kappa and bounds on wrong removal and wrong
    # inclusion, with a second person settling the sample's disagreements. Consensus: the
    # vote, its disagreements settled by rule, the records the people carried forward, and
    # exclusions by rule. Writes datasets/screening.csv. The sheets show the abstracts: they
    # are written beside the authors' copy of the records, and only where it is in place
    # (src/withheld.py).
    "screening-calibration": ("configs/screening.toml", [sys.executable, "runners/screening_calibration.py"]),
    "screening-validation": ("configs/screening.toml", [sys.executable, "runners/screening_validation.py"]),
    "screening-consensus": ("configs/screening.toml", [sys.executable, "runners/screening_consensus.py"]),
    # The map (protocol, Two tiers): the three models' codes of the included records, made
    # consistent with the scheme's rules and combined by majority, with their agreement per
    # axis. A record that a person coded takes the person's codes ([map] by_person). Writes
    # datasets/map.csv.
    "map-vote": ("configs/map-vote.toml", [sys.executable, "runners/map_vote.py"]),
    # A person's blind check of the map: three axes coded on a seeded random sample of its
    # records, and the person's agreement with the map and with each model. The codes are
    # locked once complete. Its sheet is written as the screening's sheets are.
    "map-check": ("configs/map-vote.toml", [sys.executable, "runners/map_check.py"]),
    # The claims of use beyond simulation that step 1 of the core rule rests on: the sheet
    # and page on which a person confirms each claim (written as the screening's sheets are),
    # and the answers read back from datasets/core-claims.csv.
    "core-claims": ("configs/core.toml", [sys.executable, "runners/core_claims.py"]),
    # The venue band of every record of the map, which orders the places left at step 3 of
    # the core rule: SJR found by ISSN, ICORE proposed by name and confirmed by a person
    # (datasets/venue-matches.csv). Reads the two venue lists, which are not released, so the
    # step does not run from a clone.
    "venue-bands": ("configs/venues.toml", [sys.executable, "runners/venue_bands.py"]),
    # The core rule (protocol, Two tiers): step 1 from the confirmed claims, step 2 for
    # coverage, step 3 in fixed shares by venue band, year and citations, with a cap on
    # non-deep studies. Writes datasets/core.csv and locks the core on its first run.
    "core-selection": ("configs/core.toml", [sys.executable, "runners/core_selection.py"]),
    # Counts of the map, the candidates and the core, in three tables with the same rows (year,
    # the map's codes, citations, venue country), each row's count and share of its set. Reads
    # the locked core, and refuses a core other than the one the lock holds.
    "core-statistics": ("configs/core.toml", [sys.executable, "runners/core_statistics.py"]),
    # The page on which a person gathers the core's full texts is not released with this
    # repository. Then the returned sheet in datasets/ is read back and checked against the
    # locked core and the full texts saved. Writes the counts the flow diagram takes.
    "core-texts": ("configs/core.toml", [sys.executable, "runners/core_texts.py"]),
    # The draws of the core's coding: the smoke study, the pilot, and the fifth drawn for a
    # person's check. Locked on the first run. Reads the locked core, the returned sheet of
    # the full texts (datasets/core-texts.csv) and the converted texts' checksums
    # (datasets/full-texts-md-sha256.csv).
    "core-draws": ("configs/core-draws.toml", [sys.executable, "runners/core_draws.py"]),
    # The checks of the core's answers over every response the coding agents wrote, each
    # paper first checked against its checksum: the problems by study and question, never a
    # word of the papers. Reports that there is nothing to check until the responses exist.
    "core-check": ("configs/core-check.toml", [sys.executable, "runners/core_check.py"]),
    # The core's answers gathered into the published dataset (one row per study, one line
    # per answer, the item tables), each response checked again and joined to the judge's
    # verdicts; no quote text and no note are published.
    # Stops and writes nothing while its inputs are missing, as in a clone.
    "core-gather": ("configs/core-gather.toml", [sys.executable, "runners/core_gather.py"]),
    # The research questions' tables, the five sensitivity analyses and the agreement of
    # coder and judge, from the gathered dataset; split by the role the full text gives.
    "core-synthesis": ("configs/core-synthesis.toml",
                       [sys.executable, "runners/core_synthesis.py"]),
    # A person's check of six questions on the fifth: the page and the fifth's full texts are
    # not released, and they carry no model answer. Then the person's
    # agreement with the coding agent, question by question, from
    # datasets/core-human-check.csv.
    "core-human-check": ("configs/core-human-check.toml",
                         [sys.executable, "runners/core_human_check.py"]),
    # PRISMA flow counts from references.json, duplicates.csv, dropped.csv and screening.csv
    # (written by screening-consensus), then the core's rows from the counts core-selection
    # and core-texts write.
    "make-tables": ("configs/tables.toml", [sys.executable, "runners/make_tables.py"]),
    # The paper's figures and the supplement's list of the core's studies, from the tables
    # the statistics and synthesis steps write. No count is typed into the script.
    "make-figures": ("configs/figures.toml", [sys.executable, "runners/make_figures.py"]),
}


def run(name, config, command):
    print(f"=== {name} ({config}) ===", flush=True)
    result = subprocess.run(
        command + ["--config", str(REPO / config)],
        cwd=REPO,
    )
    if result.returncode != 0:
        raise SystemExit(f"{name} failed with exit code {result.returncode}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="run only these experiments (default: all)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list the experiments and exit",
    )
    args = parser.parse_args()

    if args.list:
        for name, (config, _) in EXPERIMENTS.items():
            print(f"{name}\t{config}")
        return

    selected = args.only or list(EXPERIMENTS)
    unknown = [name for name in selected if name not in EXPERIMENTS]
    if unknown:
        raise SystemExit(f"Unknown experiment(s): {', '.join(unknown)}")

    for name in selected:
        config, command = EXPERIMENTS[name]
        run(name, config, command)

    print(f"\nDone. {len(selected)} experiment(s); outputs under results/.")


if __name__ == "__main__":
    main()
