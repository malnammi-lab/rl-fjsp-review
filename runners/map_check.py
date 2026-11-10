"""Check the map: a person codes three axes, blind, on a random sample of its records.

Reports the person's agreement with the map and with each model (protocol, Two tiers). The
sample is drawn under [check] seed from the records the screening included without a person,
outside the calibration batch. Reads the screening's decisions and corpus, the coding scheme,
datasets/map-check.csv (the person's codes), the map and each model's codes. Writes
results/map/map-check.md and, once every record is coded, map-check-lock.json. Codes changed
after the lock are refused. The sheet to fill (map-check-sheet.csv, .md and .html, with
sheets-written.json) shows the abstracts, so it is written beside the authors' copy of the
records, and only where that copy is in place (src/withheld.py).

Run: python runners/run_all.py --only map-check
"""

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import tomllib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import mapcodes as mc  # noqa: E402
from src import screening as sc  # noqa: E402
from src import withheld  # noqa: E402
from runners.core_claims import as_written, record_written, scheme_section  # noqa: E402
from runners.map_vote import load_coders  # noqa: E402
from runners.screening_consensus import load_config, load_corpus, rel, resolve  # noqa: E402

WITHOUT_A_PERSON = ("vote", "rule")
HEADING = "The map checked by a person: three axes"
INTRO = (
    "Each record below is one of a random sample of the map's records. Code each from its "
    "title and abstract alone, under the coding scheme's rules for these axes (in the box "
    "above): what the learned policy decides, the kind of learner, and the furthest use "
    "beyond simulation the abstract claims. The page shows no model's code. Type your name "
    "once at the top; your answers are kept in this browser as you go. When you finish, "
    "press Export CSV and save the file as %s (a path from the codebase folder).")


def schema_axes(cfg, names):
    """({axis: the codes a person may give}, {axis: its label}): the schema's codes, and
    `not-stated` where the schema allows it."""
    with open(resolve(cfg["inputs"]["schema"]), "rb") as fh:
        table = tomllib.load(fh)["axes"]
    codes, labels = {}, {}
    for name in names:
        spec = table[name]
        codes[name] = list(spec["codes"]) + ([mc.NOT_STATED] if spec.get("not_stated", True)
                                             else [])
        labels[name] = spec.get("label", name)
    return codes, labels


def frame(cfg, screen_records, batch_size):
    """The records the screening included without a person (basis `vote` or `rule`),
    outside the calibration batch, in record order."""
    path = resolve(cfg["inputs"]["screening"])
    if not os.path.isfile(path):
        raise SystemExit("%s not found: the screening's decisions." % path)
    decided, _, raw = sc.read_decisions(path)
    batch = {r.number for r in sc.batch(screen_records, 1, batch_size)}
    return sorted(n for n, d in decided.items()
                  if d.decision == "include" and n not in batch
                  and (raw[n].get("basis") or "").strip() in WITHOUT_A_PERSON)


def draw(numbers, size, seed):
    """`size` records drawn from `numbers` under the seed, in record order."""
    if size > len(numbers):
        raise SystemExit("The sample of %d is larger than its frame of %d records."
                         % (size, len(numbers)))
    return sorted(random.Random("%s:map-check" % seed).sample(list(numbers), size))


def read_rows(path):
    """(the column names in lower case, the rows) of a sheet or answers file; ([], []) when
    the file does not exist."""
    if not os.path.isfile(path):
        return [], []
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            fields = [(f or "").strip().lower() for f in (reader.fieldnames or [])]
            rows = [{(k or "").strip().lower(): (v or "").strip() for k, v in row.items()
                     if k and isinstance(v, str)} for row in reader]
    except UnicodeDecodeError:
        raise SystemExit("%s is not UTF-8. In Excel, save it as 'CSV UTF-8 (Comma "
                         "delimited)', not 'CSV (Comma delimited)'." % path)
    return fields, rows


def read_answers(path, sample, codes):
    """The person's codes as ({number: {axis: code, note, coded_by}} for every row given,
    [numbers of the sample not yet coded on every axis]). Refuses a file without a column
    for the number and each axis, a number not in the sample or given twice, a code the axis
    does not have, and codes given without who gave them."""
    fields, rows = read_rows(path)
    if fields:
        missing = [c for c in ["number"] + list(codes) if c not in fields]
        if missing:
            raise SystemExit("%s has no column for: %s" % (path, ", ".join(missing)))
    wanted, answers, bad = set(sample), {}, []
    for row in rows:
        text = row.get("number", "")
        if not text:
            continue
        try:
            n = int(text)
        except ValueError:
            bad.append("number %r" % text)
            continue
        if n not in wanted:
            bad.append("%d is not in the sample" % n)
            continue
        if n in answers:
            bad.append("%d given twice" % n)
            continue
        a = {axis: row.get(axis, "").lower() for axis in codes}
        for axis in codes:
            if a[axis] and a[axis] not in codes[axis]:
                bad.append("%d: %s %r is not a code of the axis" % (n, axis, a[axis]))
        a.update(note=row.get("note", ""), coded_by=row.get("coded_by", ""))
        if any(a[axis] for axis in codes) and not a["coded_by"]:
            bad.append("%d: no coded_by" % n)
        answers[n] = a
    if bad:
        raise SystemExit("%s: %s" % (path, "; ".join(bad)))
    return answers, [n for n in sample if not all(answers.get(n, {}).get(a) for a in codes)]


def blank(codes):
    return dict({axis: "" for axis in codes}, note="", coded_by="")


def unsaved(sheet_path, answers, codes):
    """Records whose codes on the sheet as it stands differ from the saved ones: a sheet
    filled in place and not yet saved under the answers' name. A sheet still as the runner
    last wrote it holds no such work, whatever the saved file now says."""
    if as_written(sheet_path):
        return []
    out = []
    for row in read_rows(sheet_path)[1]:
        try:
            n = int(row.get("number", ""))
        except ValueError:
            continue
        given = {f: row.get(f, "") for f in blank(codes)}
        given.update({axis: given[axis].lower() for axis in codes})
        if given != answers.get(n, blank(codes)):
            out.append(n)
    return out


def digest(answers, sample, codes):
    """SHA-256 of the person's codes, record by record."""
    text = "\n".join("%d|%s" % (n, "|".join(answers[n][a] for a in codes)) for n in sample)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def locked(path, value):
    """True when the lock holds these codes; False when there is no lock yet. Refuses codes
    that changed after they were locked."""
    if not os.path.isfile(path):
        return False
    with open(path, encoding="utf-8") as fh:
        held = json.load(fh).get("codes_sha256")
    if held != value:
        raise SystemExit("The person's codes changed after they were locked (%s). A change "
                         "after that point needs a dated amendment to the protocol; restore "
                         "the file, or record the amendment and then remove the lock." % path)
    return True


def write_sheet(cfg, order, records, answers, codes, labels, rules):
    """The sheet to fill (CSV), the records to read (markdown) and the page."""
    c = cfg["check"]
    csv_path = resolve(c["sheet"])
    md_path = os.path.splitext(csv_path)[0] + ".md"
    columns = ["number", "title"] + list(codes) + ["note", "coded_by"]
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    try:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=columns)
            w.writeheader()
            for n in order:
                w.writerow(dict(answers.get(n, blank(codes)), number=n, title=records[n].title))
    except PermissionError:
        raise SystemExit("%s is open in another program (Excel locks it): close it and run "
                         "again." % csv_path)
    record_written(csv_path)
    lines = ["# " + HEADING, "", INTRO % c["answers"], "", rules, ""]
    for n in order:
        lines += sc.record_block(records[n])
    with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(resolve(c["template"]), encoding="utf-8") as fh:
        template = fh.read()
    page = []
    for n in order:
        entry = sc.page_record(records[n], link=True)
        entry["answer"] = answers.get(n, blank(codes))
        page.append(entry)
    settings = {"template": template, "criteria_brief": rules, "criteria_full": "", "rules": []}
    sc.write_page(sc.page_path(csv_path), settings, HEADING, "coding", c["answers"], columns,
                  [INTRO % c["answers"]], page,
                  extra={"questions": [{"name": a, "label": labels[a], "options": codes[a]}
                                       for a in codes]})
    return [csv_path, md_path, sc.page_path(csv_path)]


def fmt(k):
    return "n/a" if k is None else "%.3f" % k


def render(config, seed, frame_size, sample, answers, the_map, coded, codes):
    n = len(sample)
    who = ", ".join(sorted({answers[s]["coded_by"] for s in sample})) or "the person"
    models = list(coded)
    lines = [
        "# The map checked by a person", "",
        "Written by `runners/map_check.py` from `%s`; do not edit, rerun the runner." % rel(config),
        "",
        "%d records drawn under seed %s from the %d the screening included without a person "
        "outside the calibration batch, coded by %s from their titles and abstracts under the "
        "scheme's rules, blind to the models' codes (protocol, Two tiers)."
        % (n, seed, frame_size, who), "",
        "| Axis | Agreement with the map | Cohen's kappa with the map | %s |"
        % " | ".join("Agreement with %s" % m for m in models),
        "|---|---:|---:|%s" % ("---:|" * len(models))]
    for axis in codes:
        pairs = [(answers[s][axis], the_map[s][axis]) for s in sample]
        agree = sum(a == b for a, b in pairs)
        with_models = [sum(answers[s][axis] == coded[m][s][axis] for s in sample) for m in models]
        lines.append("| `%s` | %d of %d (%.0f%%) | %s | %s |" % (
            axis, agree, n, 100.0 * agree / n, fmt(mc.kappa(pairs)),
            " | ".join("%d of %d" % (k, n) for k in with_models)))
    lines += ["", "With %d records, a kappa is a rough figure; the agreement counts are the "
              "plainer reading." % n, "",
              "## Where the person and the map differ", "",
              "| Record | Axis | Person | Map | %s |" % " | ".join(models),
              "|---|---|---|---|%s" % ("---|" * len(models))]
    differ = [(s, axis) for s in sample for axis in codes
              if answers[s][axis] != the_map[s][axis]]
    for s, axis in differ:
        lines.append("| %d | `%s` | `%s` | `%s` | %s |" % (
            s, axis, answers[s][axis], the_map[s][axis],
            " | ".join("`%s`" % coded[m][s][axis] for m in models)))
    if not differ:
        lines.append("| none | | | | %s |" % " | ".join("" for _ in models))
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "map-vote.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")
    args = parser.parse_args()
    cfg = load_config(args.config, args.override)
    c = cfg["check"]

    codes, labels = schema_axes(cfg, c["axes"])
    scfg = load_config(resolve(c["screening_config"]))
    _, screen_records = load_corpus(scfg, abstracts=True)
    records = {r.number: r for r in screen_records}
    numbers = frame(cfg, screen_records, scfg["calibration"]["batch_size"])
    sample = draw(numbers, c["size"], c["seed"])
    order = sc.blind_order(sample, "%s:map-check" % c["seed"])
    scheme = resolve(c["scheme"])
    rules = "\n\n".join(scheme_section(scheme, axis) for axis in codes)

    answers_path = resolve(c["answers"])
    answers, open_ = read_answers(answers_path, sample, codes)
    pending = unsaved(resolve(c["sheet"]), answers, codes)
    if pending:
        raise SystemExit("%s holds codes not saved in %s (records %s): save the sheet under "
                         "that name, or move it aside, before it is written again."
                         % (c["sheet"], c["answers"], ", ".join(map(str, pending))))
    complete = not open_
    lock = resolve(c["lock"])
    if complete:
        is_locked = locked(lock, digest(answers, sample, codes))
    # The sheet shows the abstracts: written beside the authors' copy, where it is in place.
    written = []
    if withheld.available(resolve(scfg["inputs"]["references"])):
        written = write_sheet(cfg, order, records, answers, codes, labels, rules)
    else:
        print("the check's sheet shows the abstracts, which this repository withholds: "
              "not written")

    report_path = resolve(c["report"])
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    if complete:
        axes = mc.load_axes(resolve(cfg["inputs"]["schema"]))
        map_path = resolve(cfg["outputs"]["map"])
        if not os.path.isfile(map_path):
            raise SystemExit("%s not found: the map, written by runners/map_vote.py." % map_path)
        the_map, _ = mc.read_codes(map_path, axes)
        coded, _ = load_coders(cfg, axes)
        absent = [s for s in sample if s not in the_map or any(s not in v for v in coded.values())]
        if absent:
            raise SystemExit("The map or a model's codes lack sampled records: %s"
                             % ", ".join(map(str, absent)))
        report = render(args.config, c["seed"], len(numbers), sample, answers, the_map, coded,
                        codes)
        if not is_locked:
            with open(lock, "w", encoding="utf-8", newline="\n") as fh:
                json.dump({"codes_sha256": digest(answers, sample, codes),
                           "records": len(sample)}, fh, indent=2)
            written.append(lock)
    else:
        report = ("# The map checked by a person\n\n%d of %d sampled records coded on every "
                  "axis. The agreement is computed once every record is coded.\n"
                  % (len(sample) - len(open_), len(sample)))
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(report)
    written.append(report_path)

    print("frame             : %d records included without a person, outside batch 01"
          % len(numbers))
    print("sample            : %d, seed %s" % (len(sample), c["seed"]))
    print("coded             : %d of %d" % (len(sample) - len(open_), len(sample)))
    print("written           : %s" % ", ".join(rel(p) for p in written))


if __name__ == "__main__":
    main()
