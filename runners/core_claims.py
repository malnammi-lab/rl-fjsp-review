"""Write the sheet of the claims of use beyond simulation, and read a person's answers back.

Step 1 of the core rule rests on these claims (protocol, Two tiers). The sheet holds each
record of the map with a stated learner and a claim of L2 to L5. Its page shows the abstract
with the models' levels and quotes. The person answers yes or no, with the level where it
differs from the models'. Reads the map, the corpus, the models' coding files, the coding
scheme and datasets/core-claims.csv. Writes results/core/claims.md. The sheet
(claims-sheet.csv, claims-sheet.html and sheets-written.json) shows the abstracts, so it is
written beside the authors' copy of the records, and only where that copy is in place
(src/withheld.py). A sheet filled in place but not saved stops the run.

Run: python runners/run_all.py --only core-claims
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus  # noqa: E402
from src import mapcodes as mc  # noqa: E402
from src import screening as sc  # noqa: E402
from src import withheld  # noqa: E402
from runners.screening_consensus import load_config, rel, resolve  # noqa: E402

AXIS = "readiness_claim"
SHEET_FIELDS = ["number", "title", "claimed_level", "confirmed", "level", "read_from", "note",
                "confirmed_by"]
ANSWER_FIELDS = ("confirmed", "level", "read_from", "note", "confirmed_by")
ANSWERS = ("yes", "no")
FULL_TEXT = "full-text"
HEADING = "Claims of use beyond simulation to confirm"


def intro(save_as, levels):
    return [
        "Each record below is a study the map codes as claiming use beyond simulation. A "
        "claim confirmed at a higher level (%s) decides a place: it puts the study in the "
        "core at step 1 of the core rule, whatever its venue or citations. A claim confirmed "
        "at a test on real data alone decides no place and is reported under question 5 "
        "(protocol, Two tiers)." % ", ".join(levels),
        "For each record, read the title and abstract and answer one question: does the "
        "abstract report that the method was run beyond simulation? Answer No if it reports "
        "simulation only, or only says the method could be used in practice. If you answer "
        "Yes at a level other than the models' claim, higher or lower, choose that level "
        "under Level: a claim of real data whose abstract reports a run in a digital twin, "
        "for example, or a claim of a digital twin whose abstract shows only a test on real "
        "data. Leave Level as claimed when the models' level is right.",
        "Judge by the title and abstract alone, as the models did, unless the abstract leaves "
        "open whether the run reached a higher level (a digital twin or hardware in the loop, "
        "a physical testbed or shadow mode, a live system): then read the full text, answer "
        "from it, and tick 'Settled from the full text'. The coding scheme's rule for this "
        "axis is below; the models' quotes are marked in the abstract where they occur word "
        "for word.",
        "Type your name once at the top. Your answers are kept in this browser as you go. "
        "When you finish, press Export CSV and save the file as %s (a path from the codebase "
        "folder). Open this page from your computer, not in OneDrive's web viewer, which "
        "blocks the export." % save_as,
    ]


def scheme_section(path, axis):
    """The coding scheme's section for one axis of Part A, from its heading to the next."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    found = re.search(r"^### `%s`.*?(?=^#{2,3} |\Z)" % re.escape(axis), text, re.M | re.S)
    if not found:
        raise SystemExit("%s has no section for `%s`." % (path, axis))
    return found.group(0).strip()


def level_texts(section, codes):
    """{code: the text of its bullet in the section}, on one line, without backticks."""
    out = {}
    for code in codes:
        found = re.search(r"^- `%s`:(.*?)(?=^- |\Z)" % re.escape(code), section, re.M | re.S)
        out[code] = " ".join(found.group(1).split()).replace("`", "") if found else ""
    return out


def model_claims(cfg, axes, numbers):
    """{model: {number: (level, quote)}} from the models' coding files, in config order."""
    out = {}
    for model, path in cfg["coders"].items():
        p = resolve(path)
        if not os.path.isfile(p):
            raise SystemExit("%s not found: %s's coding file ([coders] of the config)."
                             % (p, model))
        codes, _ = mc.read_codes(p, axes)
        with open(p, encoding="utf-8-sig", newline="") as fh:
            quotes = {int(r["number"]): (r.get(AXIS + "_evidence") or "").strip()
                      for r in csv.DictReader(fh) if (r.get("number") or "").strip()}
        absent = [n for n in numbers if n not in codes]
        if absent:
            raise SystemExit("%s has not coded records %s, which the map holds."
                             % (p, ", ".join(map(str, absent))))
        out[model] = {n: (codes[n][AXIS], quotes.get(n, "")) for n in numbers}
    return out


def blank():
    return {f: "" for f in ANSWER_FIELDS}


def read_answers(path):
    """[(line, {column: value})] of a sheet or confirmations file, column names in lower
    case; [] when the file does not exist."""
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            fields = [(f or "").strip().lower() for f in (reader.fieldnames or [])]
            rows = [{(k or "").strip().lower(): v for k, v in row.items() if k}
                    for row in reader]
    except UnicodeDecodeError:
        raise SystemExit("%s is not UTF-8. In Excel, save it as 'CSV UTF-8 (Comma "
                         "delimited)', not 'CSV (Comma delimited)'." % path)
    if not {"number", "confirmed"} <= set(fields):
        raise SystemExit("%s has no 'number' and 'confirmed' columns (header found: %s). "
                         "Keep the header row, and in Excel save it as 'CSV UTF-8 (Comma "
                         "delimited)'." % (path, ", ".join(fields) or "none"))
    return [(i + 2, {k: (v or "").strip() for k, v in row.items() if isinstance(v, str)})
            for i, row in enumerate(rows)]


def answer_of(row):
    """A person's answer as a row of the sheet or of the saved file gives it, its codes in
    lower case; read_from is blank for the abstract."""
    a = {f: row.get(f, "") for f in ANSWER_FIELDS}
    for f in ("confirmed", "level", "read_from"):
        a[f] = a[f].lower()
    if a["read_from"] == "abstract":
        a["read_from"] = ""
    return a


def read_confirmations(path, numbers, levels):
    """The person's answers as ({number: {confirmed, level, read_from, note, confirmed_by}}
    for every row given, [numbers on the sheet not yet answered yes or no]). Refuses a number
    not on the sheet or given twice, an answer other than yes or no, an answer without who
    gave it, a level not among `levels` or without a yes, and a read_from other than abstract
    or full-text, or without an answer. A file without the level and read_from columns reads
    as the models' level, from the abstract."""
    wanted, answers, bad = set(numbers), {}, []
    for line, row in read_answers(path):
        text = row.get("number", "")
        if not text:
            continue
        try:
            n = int(text)
        except ValueError:
            bad.append("line %d: number %r" % (line, text))
            continue
        if n not in wanted:
            bad.append("%d is not on the sheet" % n)
            continue
        if n in answers:
            bad.append("%d given twice" % n)
            continue
        a = answer_of(row)
        if a["confirmed"] and a["confirmed"] not in ANSWERS:
            bad.append("%d: confirmed %r, not yes or no" % (n, a["confirmed"]))
            continue
        if a["confirmed"] and not a["confirmed_by"]:
            bad.append("%d: no confirmed_by" % n)
            continue
        if a["level"] and a["level"] not in levels:
            bad.append("%d: level %r, not one of %s" % (n, a["level"], ", ".join(levels)))
            continue
        if a["level"] and a["confirmed"] != "yes":
            bad.append("%d: a level goes with yes" % n)
            continue
        if a["read_from"] and a["read_from"] != FULL_TEXT:
            bad.append("%d: read_from %r, not abstract or %s" % (n, a["read_from"], FULL_TEXT))
            continue
        if a["read_from"] and not a["confirmed"]:
            bad.append("%d: read from the full text, but no answer" % n)
            continue
        answers[n] = a
    if bad:
        raise SystemExit("%s: %s" % (path, "; ".join(bad)))
    return answers, [n for n in numbers if not answers.get(n, blank())["confirmed"]]


def confirmed_level(answer, claimed):
    """The level a claim is confirmed at: the person's where given, else the models' claimed
    level; None for a claim not confirmed (protocol, Amendments)."""
    if answer.get("confirmed") != "yes":
        return None
    return answer.get("level") or claimed


def step1_places(candidates, the_map, answers, step1):
    """The candidates step 1 of the core rule puts in the core: those confirmed at one of
    its levels, by the person's level where given."""
    return [n for n in candidates
            if confirmed_level(answers.get(n, blank()), the_map[n][AXIS]) in step1]


def _written_path(sheet_path):
    return os.path.join(os.path.dirname(sheet_path), "sheets-written.json")


def file_sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def record_written(sheet_path):
    """Remember the bytes the runner has just written to this sheet, so that a sheet nobody
    has touched since is never mistaken for one filled in place."""
    path = _written_path(sheet_path)
    held = {}
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            held = json.load(fh)
    held[os.path.basename(sheet_path)] = file_sha(sheet_path)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(held, fh, indent=2, sort_keys=True)


def as_written(sheet_path):
    """Whether the sheet is byte for byte as the runner last wrote it."""
    path = _written_path(sheet_path)
    if not (os.path.isfile(path) and os.path.isfile(sheet_path)):
        return False
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get(os.path.basename(sheet_path)) == file_sha(sheet_path)


def unsaved(sheet_path, saved):
    """Records whose answers on the sheet as it stands differ from the saved ones: a sheet
    filled in place and not yet saved under the confirmations' name. A sheet still as the
    runner last wrote it holds no such work, whatever the saved file now says: the saved
    file was corrected directly."""
    if as_written(sheet_path):
        return []
    out = []
    for _, row in read_answers(sheet_path):
        try:
            n = int(row.get("number", ""))
        except ValueError:
            continue
        if answer_of(row) != saved.get(n, blank()):
            out.append(n)
    return out


def write_sheet(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=SHEET_FIELDS)
            w.writeheader()
            for row in rows:
                w.writerow(row)
    except PermissionError:
        raise SystemExit("%s is open in another program (Excel locks it): close it and run "
                         "again." % path)


def render(config, levels, claimed, candidates, the_map, answers, confirmations, outputs,
           step1=()):
    by_level = Counter(the_map[n][AXIS] for n in candidates)
    said = Counter((the_map[n][AXIS], a["confirmed"]) for n, a in answers.items()
                   if a["confirmed"])
    lines = [
        "# Claims of use beyond simulation: the core's step 1", "",
        "Written by `runners/core_claims.py` from `%s`; do not edit, rerun the runner." % rel(config),
        "",
        "%d records of the map claim use beyond simulation (readiness level L2 to L5); %d of "
        "them are candidates for the core, their learner being stated, and are on the sheet "
        "(withheld with its page, since it shows the abstracts)."
        % (len(claimed), len(candidates)),
        "",
        "| Level the models claim | On the sheet | Confirmed | Not confirmed | Not yet answered |",
        "| --- | ---: | ---: | ---: | ---: |"]
    for level in levels:
        yes, no = said[(level, "yes")], said[(level, "no")]
        lines.append("| `%s` | %d | %d | %d | %d |" % (level, by_level[level], yes, no,
                                                      by_level[level] - yes - no))
    yes = sum(v for (_, a), v in said.items() if a == "yes")
    no = sum(v for (_, a), v in said.items() if a == "no")
    lines.append("| all | %d | %d | %d | %d |" % (len(candidates), yes, no,
                                                  len(candidates) - yes - no))
    saved = os.path.isfile(resolve(confirmations))
    lines += ["", "Confirmations: `%s`, %s." % (
        confirmations, "%d of %d answered" % (yes + no, len(candidates)) if saved
        else "not yet saved")]
    at = Counter(confirmed_level(a, the_map[n][AXIS]) for n, a in answers.items())
    lines += ["", "| Level confirmed, the person's where given | Records |", "| --- | ---: |"]
    lines += ["| `%s` | %d |" % (level, at[level]) for level in levels]
    changed = [n for n in candidates
               if answers.get(n, blank())["level"] not in ("", the_map[n][AXIS])]
    full = [n for n in candidates if answers.get(n, blank())["read_from"] == FULL_TEXT]
    lines += ["", "Levels the person changed: %s." % (", ".join(
        "%d (`%s` to `%s`)" % (n, the_map[n][AXIS], answers[n]["level"]) for n in changed)
        or "none"),
        "", "Settled from the full text: %s." % (", ".join(map(str, full)) or "none")]
    if step1:
        step = [n for n in candidates if the_map[n][AXIS] in step1]
        places = step1_places(candidates, the_map, answers, step1)
        lines += ["", "Step 1 of the core rule (protocol, Two tiers): a claim "
                  "confirmed at %s, by the person's level where given, guarantees a place. "
                  "The models' claims at these levels on the sheet: %d. Places at step 1: "
                  "%d%s. A claim confirmed at a test on real data alone guarantees none and "
                  "is reported under question 5." % (
                      ", ".join("`%s`" % lv for lv in step1), len(step), len(places),
                      " (%s)" % ", ".join(map(str, places)) if places else "")]
    others = [n for n in claimed if n not in candidates]
    lines += ["", "Claims whose learner is not stated, so not candidates for the core: %s." % (
        ", ".join(map(str, others)) or "none")]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "core.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")
    args = parser.parse_args()
    cfg = load_config(args.config, args.override)
    inputs, outputs = cfg["inputs"], cfg["outputs"]

    axes = mc.load_axes(resolve(inputs["schema"]))
    codes = next(a.codes for a in axes if a.name == AXIS)
    levels = [c for c in codes if c != "none"]
    map_path = resolve(inputs["map"])
    if not os.path.isfile(map_path):
        raise SystemExit("%s not found: the map, written by runners/map_vote.py." % map_path)
    the_map, _ = mc.read_codes(map_path, axes)
    claimed = sorted(n for n, cells in the_map.items() if cells[AXIS] in levels)
    candidates = [n for n in claimed if the_map[n]["learner_depth"] != mc.NOT_STATED]

    models = model_claims(cfg, axes, candidates)
    refs = resolve(inputs["references"])
    records = {r.number: r for r in corpus.load_references(refs, abstracts=True)}
    missing = [n for n in candidates if n not in records]
    if missing:
        raise SystemExit("%s holds no record %s." % (inputs["references"],
                                                     ", ".join(map(str, missing))))
    section = scheme_section(resolve(inputs["scheme"]), AXIS)
    texts = level_texts(section, codes)

    confirmations = inputs["confirmations"]
    answers, open_ = read_confirmations(resolve(confirmations), candidates, levels)
    sheet_path = resolve(outputs["sheet"])
    pending = unsaved(sheet_path, answers)
    if pending:
        raise SystemExit("%s holds answers not saved in %s (records %s): save the sheet under "
                         "that name, or move it aside, before it is written again."
                         % (sheet_path, confirmations, ", ".join(map(str, pending))))

    step1 = cfg.get("step1", {}).get("levels", [])
    # The page shows the abstracts: the sheet and its page are written beside the authors'
    # copy, where it is in place.
    if withheld.available(refs):
        rows, page = [], []
        for n in candidates:
            record, answer = records[n], answers.get(n, blank())
            level = the_map[n][AXIS]
            rows.append({"number": n, "title": record.title, "claimed_level": level, **answer})
            entry = sc.page_record(record, link=True)
            entry.update({"level": level, "level_text": texts.get(level, ""), "answer": answer,
                          "models": [{"name": m, "level": models[m][n][0],
                                      "quote": models[m][n][1]} for m in models]})
            page.append(entry)
        write_sheet(sheet_path, rows)
        record_written(sheet_path)
        with open(resolve(inputs["template"]), encoding="utf-8") as fh:
            template = fh.read()
        settings = {"template": template, "criteria_brief": section, "criteria_full": "",
                    "rules": []}
        sc.write_page(sc.page_path(sheet_path), settings, HEADING, "confirm", confirmations,
                      SHEET_FIELDS, intro(confirmations, step1), page, extra={"levels": levels})
    else:
        print("the claims' sheet shows the abstracts, which this repository withholds: not "
              "written")
    report_path = resolve(outputs["report"])
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(args.config, levels, claimed, candidates, the_map, answers,
                        confirmations, outputs, step1))

    said = Counter(a["confirmed"] for a in answers.values() if a["confirmed"])
    print("claims in the map : %d" % len(claimed))
    print("on the sheet      : %d (%s)" % (len(candidates), ", ".join(
        "%s %d" % (lv, sum(1 for n in candidates if the_map[n][AXIS] == lv)) for lv in levels)))
    print("answered          : %d (yes %d, no %d); open %d"
          % (said["yes"] + said["no"], said["yes"], said["no"], len(open_)))
    if step1:
        places = step1_places(candidates, the_map, answers, step1)
        print("places at step 1  : %d%s" % (len(places), " (%s)" % ", ".join(map(str, places))
                                            if places else ""))
    shown = [sheet_path, sc.page_path(sheet_path)] if withheld.available(refs) else []
    print("written           : %s" % ", ".join(rel(p) for p in shown + [report_path]))


if __name__ == "__main__":
    main()
