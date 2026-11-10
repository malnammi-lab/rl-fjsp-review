"""Draw the studies of the core's coding: the smoke study, the pilot and the fifth.

The smoke study is fixed in the config. The pilot takes one study per role on the map, then
the largest full text left. The fifth is a stratified sample of the studies left, drawn for
a person's check. Reads the locked core, datasets/core-texts.csv and
datasets/full-texts-md-sha256.csv. Writes results/core-coding/draws.csv, draws.md and
draws-lock.json. A later run that draws differently is refused.

Run: python runners/run_all.py --only core-draws
"""

import argparse
import csv
import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import screening as sc  # noqa: E402
from runners.core_selection import file_sha, table, write_csv  # noqa: E402
from runners.core_texts import read_core  # noqa: E402
from runners.screening_consensus import load_config, rel, resolve  # noqa: E402

FIELDS = ["number", "draw", "stratum", "policy_role", "md_bytes", "why"]
HEADING = "The draws of the core's coding"


def read_rows(path, what):
    """The rows of a CSV, keys and values stripped; refuses a missing file."""
    if not os.path.isfile(path):
        raise SystemExit("%s not found: %s." % (path, what))
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return [{(k or "").strip(): (v or "").strip() for k, v in row.items() if k}
                for row in csv.DictReader(fh)]


def frame(numbers, core_rows, texts_rows, md_rows):
    """{number: (stratum, policy_role, the markdown's bytes)} for the core's studies whose
    full text was saved and converted. Refuses a saved full text with no markdown."""
    saved = {int(r["number"]) for r in texts_rows if r.get("pdf_saved") == "yes"}
    sizes = {}
    for r in md_rows:
        n = int(r["number"])
        if r.get("file") == "%d/%d.md" % (n, n):
            sizes[n] = int(r["bytes"])
    unconverted = sorted(n for n in numbers if n in saved and n not in sizes)
    if unconverted:
        raise SystemExit("Saved full texts with no markdown: %s."
                         % ", ".join(map(str, unconverted)))
    out = {}
    for r in core_rows:
        n = int(r["number"])
        if n in numbers and n in saved:
            out[n] = (r["stratum"], r["policy_role"], sizes[n])
    return out


def draw(studies, smoke, roles, largest, size, seed):
    """[(number, draw, why)]: the smoke study, then the pilot, then the fifth, each in the
    order drawn."""
    if smoke not in studies:
        raise SystemExit("The smoke study %d is not among the core's converted full texts."
                         % smoke)
    out, taken = [(smoke, "smoke", "fixed in the config")], {smoke}
    for role in roles:
        pool = sorted(n for n, (_, r, _) in studies.items() if r == role and n not in taken)
        if not pool:
            raise SystemExit("No study left whose role on the map is %s." % role)
        pick = random.Random("%s:pilot:%s" % (seed, role)).choice(pool)
        out.append((pick, "pilot", "a study the map codes %s" % role))
        taken.add(pick)
    if largest:
        pool = [n for n in studies if n not in taken]
        pick = max(pool, key=lambda n: (studies[n][2], -n))
        out.append((pick, "pilot", "the largest full text left"))
        taken.add(pick)
    left = sorted(n for n in studies if n not in taken)
    strata = {}
    for n in left:
        strata.setdefault(studies[n][0], []).append(n)
    strata = {s: strata[s] for s in sorted(strata)}
    quotas = sc.proportional_quotas({s: len(m) for s, m in strata.items()}, size)
    drawn = sc.stratified_sample(strata, quotas, "%s:fifth" % seed)
    for s in strata:
        out += [(n, "fifth", "%d of the %d studies of stratum %s left"
                 % (quotas[s], len(strata[s]), s)) for n in drawn[s]]
    return out


def locked(path, seed, drawn, inputs):
    """True when the lock holds these draws, False when it was written now. Refuses draws
    that differ from the locked ones."""
    value = {"seed": seed, "draws": [[n, d] for n, d, _ in drawn], "inputs": inputs}
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            held = json.load(fh)
        if held.get("seed") != seed or held.get("draws") != value["draws"]:
            raise SystemExit("The draws differ from those locked in %s. A change once they "
                             "are drawn needs a dated amendment to the protocol; restore the "
                             "config and the inputs, or record the amendment and then remove "
                             "the lock." % path)
        return True
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(value, fh, indent=2)
        fh.write("\n")
    return False


def render(config, seed, studies, drawn):
    count = {d: sum(1 for _, x, _ in drawn if x == d) for d in ("smoke", "pilot", "fifth")}
    lines = ["# %s" % HEADING, "",
             "Written by `runners/core_draws.py` from `%s`; do not edit, rerun the runner."
             % config, "",
             "Drawn under seed %s from the %d studies of the locked core whose full text was "
             "saved and converted: %d smoke study, %d pilot studies, and the fifth of %d "
             "studies, for a person's check of six questions."
             % (seed, len(studies), count["smoke"], count["pilot"], count["fifth"]), ""]
    head = [("Number", True), ("Draw", False), ("Stratum", False), ("Role on the map", False),
            ("Markdown bytes", True), ("Why", False)]
    lines += table(head, [(n, d, studies[n][0], studies[n][1], studies[n][2], why)
                          for n, d, why in drawn])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "core-draws.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")
    args = parser.parse_args()
    cfg = load_config(args.config, args.override)
    inputs, settings, outputs = cfg["inputs"], cfg["draws"], cfg["outputs"]

    numbers = set(read_core(resolve(inputs["core"]), resolve(inputs["core_lock"])))
    studies = frame(numbers, read_rows(resolve(inputs["core"]), "the core"),
                    read_rows(resolve(inputs["texts"]), "the full texts' sheet"),
                    read_rows(resolve(inputs["md_checksums"]), "the markdown's checksums"))
    seed = settings["seed"]
    drawn = draw(studies, int(settings["smoke"]), list(settings["pilot_roles"]),
                 bool(settings.get("pilot_largest", True)), int(settings["fifth"]), seed)
    shas = {key: file_sha(resolve(inputs[key])) for key in ("core", "texts", "md_checksums")}
    held = locked(resolve(outputs["lock"]), seed, drawn, shas)

    write_csv(resolve(outputs["table"]), FIELDS,
              [{"number": n, "draw": d, "stratum": studies[n][0], "policy_role": studies[n][1],
                "md_bytes": studies[n][2], "why": why} for n, d, why in drawn])
    report = resolve(outputs["report"])
    with open(report, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(rel(args.config), seed, studies, drawn))

    print("studies drawn from: %d" % len(studies))
    for d in ("smoke", "pilot", "fifth"):
        print("%-18s: %s" % (d, ", ".join(str(n) for n, x, _ in drawn if x == d)))
    print("lock              : %s (%s)" % (rel(resolve(outputs["lock"])),
                                          "held" if held else "written now"))
    print("written           : %s, %s" % (rel(resolve(outputs["table"])), rel(report)))


if __name__ == "__main__":
    main()
