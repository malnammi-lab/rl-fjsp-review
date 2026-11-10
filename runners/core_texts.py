"""Write the page on which a person gathers the core's full texts, and read the answers back.

The page lists each study of the locked core with its DOI link. The person records whether
the PDF was saved, its version, any supplement and whether the DOI is right. Reads
datasets/core.csv, references.json and results/core/core-lock.json. Writes the gatherer's
page, which is not released with this repository. Once the returned file is in place
(datasets/core-texts.csv), checks it against the core and datasets/full-texts-sha256.csv,
then writes results/core/core-texts.md and core-texts-flow.csv.

Run: python runners/run_all.py --only core-texts
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus  # noqa: E402
from src import screening as sc  # noqa: E402
from runners.core_selection import FLOW_FIELDS, core_digest, file_sha, table, write_csv  # noqa: E402
from runners.screening_consensus import load_config, rel, resolve  # noqa: E402

GIVEN = ["number", "title", "first_author", "year", "venue", "doi", "link"]
TO_FILL = ["pdf_saved", "version", "supplement_saved", "doi_correct", "correct_doi",
           "not_retrieved_reason", "note", "done_by"]
SHEET_FIELDS = GIVEN + TO_FILL
HEADING = "The core's full texts"
# The answers the page offers, as the returned file holds them.
CHOICES = {"pdf_saved": ("yes", "no"), "version": ("published", "accepted", "preprint"),
           "supplement_saved": ("yes", "no"), "doi_correct": ("yes", "no")}


def intro(export_name, count):
    return [
        "These are the %d studies of the review's core, the ones read in full. For each, open "
        "its DOI link, check that the page is this very paper (title, first author, year, and "
        "journal or conference), and save its PDF as pdfs/<number>.pdf in this folder, the "
        "record number from the first column. The steps are in README.md beside this page."
        % count,
        "Tick PDF saved and choose its version (published, or the accepted manuscript or a "
        "preprint when that is all you can get); tick Supplement saved when you saved "
        "supplementary material as pdfs/<number>-supp. Choose whether the DOI opens this "
        "paper, and give the right DOI when it does not. When a paper cannot be obtained, leave "
        "PDF saved empty and say why.",
        "Type your name once at the top. Your answers are kept in this browser as you go. When "
        "you finish, or to stop for the day, press Export CSV: it saves %s to your downloads "
        "folder; put it in this folder. Open this page from your computer, not in OneDrive's "
        "web viewer, which blocks the export." % export_name,
    ]


def read_core(path, lock_path):
    """The core's record numbers, ascending; refuses a missing core or lock, and a core other
    than the one the lock holds."""
    for p, what in ((path, "the core"), (lock_path, "the core's lock")):
        if not os.path.isfile(p):
            raise SystemExit("%s not found: %s, written by runners/core_selection.py." % (p, what))
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = [(int(r["number"]), (r.get("step") or "").strip())
                for r in csv.DictReader(fh) if (r.get("number") or "").strip()]
    with open(lock_path, encoding="utf-8") as fh:
        held = json.load(fh).get("core_sha256")
    if core_digest(rows) != held:
        raise SystemExit("%s is not the core locked in %s: rerun runners/core_selection.py."
                         % (path, lock_path))
    return sorted(n for n, _ in rows)


def page_records(numbers, records):
    """The studies as the page holds them: the seven columns the export repeats."""
    out = []
    for n in numbers:
        r = records[n]
        out.append({"number": n, "title": r.title or "", "first_author": r.first_author or "",
                    "year": r.year or "", "venue": r.venue or "", "doi": r.doi or "",
                    "link": "https://doi.org/%s" % r.doi if r.doi else ""})
    return out


def read_answers(path, rows):
    """The returned file, checked against the page's rows (page_records): one row for each
    study of the core and none other, the given columns as the page held them, each answer
    one the page offers, and each study finished. Refuses the file on any fault, naming every
    row that has it. Returns the rows with their answers, in the page's order."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        absent = [c for c in SHEET_FIELDS if c not in (reader.fieldnames or [])]
        if absent:
            raise SystemExit("%s has no column %s." % (path, ", ".join(absent)))
        # A row with more cells than the header holds the extra ones under the key None.
        sheet = [row for row in reader
                 if any((v or "").strip() for k, v in row.items() if k is not None)]

    faults = {}

    def fault(what, n):
        faults.setdefault(what, []).append(n)

    by_number = {}
    for i, row in enumerate(sheet, 2):
        n = corpus._int((row.get("number") or "").strip())
        if n is None:
            fault("a row with no record number (line of the file)", i)
        elif n in by_number:
            fault("more than one row", n)
        else:
            by_number[n] = row
    expected = {r["number"] for r in rows}
    for n in sorted(set(by_number) - expected):
        fault("not a study of the core", n)
    for n in sorted(expected - set(by_number)):
        fault("no row", n)

    answers = []
    for r in rows:
        n = r["number"]
        row = by_number.get(n)
        if row is None:
            continue
        for c in GIVEN[1:]:
            if (row.get(c) or "").strip() != str(r[c]).strip():
                fault("the given column %s differs from the record" % c, n)
        a = {c: (row.get(c) or "").strip() for c in TO_FILL}
        for c, allowed in CHOICES.items():
            a[c] = a[c].lower()
            if a[c] and a[c] not in allowed:
                fault("%s is not one of %s" % (c, ", ".join(allowed)), n)
        if a["pdf_saved"] == "yes":
            if not a["version"]:
                fault("a saved PDF with no version", n)
            if not a["supplement_saved"]:
                fault("a saved PDF with no answer on its supplementary material", n)
            if not a["doi_correct"]:
                fault("a saved PDF whose DOI was not checked", n)
            if a["not_retrieved_reason"]:
                fault("a saved PDF with a reason for not retrieving it", n)
        elif a["pdf_saved"] == "no":
            if not a["not_retrieved_reason"]:
                fault("not retrieved, with no reason", n)
            if a["version"] or a["supplement_saved"] == "yes":
                fault("not retrieved, with a version or a supplement", n)
        else:
            fault("neither saved nor given a reason: the gathering is not finished", n)
        if a["doi_correct"] == "no" and not a["correct_doi"]:
            fault("a DOI found wrong, with no right DOI", n)
        if a["doi_correct"] != "no" and a["correct_doi"]:
            fault("a right DOI for a DOI not found wrong", n)
        if not a["done_by"]:
            fault("no name of who did it", n)
        answers.append(dict(r, **a))
    if faults:
        raise SystemExit("%s is refused:\n%s" % (path, "\n".join(
            "  %s: %s" % (what, ", ".join(map(str, numbers))) for what, numbers in faults.items())))
    return answers


def check_saved_files(answers, path):
    """The studies marked saved must be exactly the full texts the checksums' list holds
    ([inputs] texts_checksums), so the file and the folder of PDFs agree."""
    if not os.path.isfile(path):
        raise SystemExit("%s not found: the list of the full texts saved, with their checksums "
                         "(datasets/MANIFEST.md)." % path)
    with open(path, encoding="utf-8-sig", newline="") as fh:
        listed = {int(r["number"]) for r in csv.DictReader(fh)}
    saved = {a["number"] for a in answers if a["pdf_saved"] == "yes"}
    if saved != listed:
        raise SystemExit("The studies marked saved and the checksums' list %s disagree: saved "
                         "but not listed %s; listed but not saved %s."
                         % (path, sorted(saved - listed) or "none", sorted(listed - saved) or "none"))


def texts_flow(answers):
    """The counts the flow diagram takes: the full texts sought (the core), not retrieved,
    each reason, read; and the DOIs corrected."""
    missing = [a for a in answers if a["pdf_saved"] == "no"]
    reasons = Counter(a["not_retrieved_reason"] for a in missing)
    rows = [("sought", "Full texts sought: the core", len(answers)),
            ("not-retrieved", "Full texts not retrieved", len(missing))]
    rows += [("not-retrieved-%d" % i, "Not retrieved: %s" % reason, count)
             for i, (reason, count) in enumerate(sorted(reasons.items()), 1)]
    rows += [("read", "The core read in full", len(answers) - len(missing)),
             ("doi-corrected", "DOIs corrected", sum(1 for a in answers if a["doi_correct"] == "no"))]
    return [{"key": k, "label": label, "count": c} for k, label, c in rows]


def cell(text):
    return str(text).replace("|", "\\|")


def render_texts(answers, flow, sheet, sheet_sha, checksums):
    saved = [a for a in answers if a["pdf_saved"] == "yes"]
    missing = [a for a in answers if a["pdf_saved"] == "no"]
    fixed = [a for a in answers if a["doi_correct"] == "no"]
    versions = Counter(a["version"] for a in saved)
    against = "the locked core"
    if checksums:
        against += " and the list of the full texts saved (`%s`)" % checksums
    lines = ["# The core's full texts, as gathered", "",
             "Read back by `runners/core_texts.py` from `%s` (SHA-256 %s), checked against %s. "
             "Every count below is taken from that file; the note of each of its rows records "
             "how its answer was reached." % (sheet, sheet_sha, against), "",
             "## Counts", ""]
    lines += table([("Stage", False), ("Studies", True)], [(cell(r["label"]), r["count"]) for r in flow])
    lines += ["", "## Not retrieved", ""]
    lines += (table([("Record", True), ("Title", False), ("Reason", False)],
                    [(a["number"], cell(a["title"]), cell(a["not_retrieved_reason"])) for a in missing])
              if missing else ["None."])
    lines += ["", "## The full texts read", "",
              "%d full texts: %s. Supplementary material saved for %d. DOI checked for %d, and "
              "found wrong for %d." % (
                  len(saved), ", ".join("%s %d" % kv for kv in sorted(versions.items())) or "none",
                  sum(1 for a in saved if a["supplement_saved"] == "yes"),
                  sum(1 for a in saved if a["doi_correct"]),
                  sum(1 for a in saved if a["doi_correct"] == "no")), "",
              "## DOIs corrected", ""]
    lines += (table([("Record", True), ("DOI of the record", False), ("Right DOI", False)],
                    [(a["number"], a["doi"], cell(a["correct_doi"])) for a in fixed])
              if fixed else ["None."])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "core.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")
    args = parser.parse_args()
    cfg = load_config(args.config, args.override)
    inputs, outputs = cfg["inputs"], cfg["outputs"]

    numbers = read_core(resolve(outputs["core"]), resolve(outputs["lock"]))
    records = {r.number: r for r in corpus.load_references(resolve(inputs["references"]))}
    absent = [n for n in numbers if n not in records]
    if absent:
        raise SystemExit("%s holds no record %s." % (inputs["references"],
                                                     ", ".join(map(str, absent))))
    with open(resolve(inputs["texts_template"]), encoding="utf-8") as fh:
        template = fh.read()
    settings = {"template": template, "criteria_brief": "", "criteria_full": "", "rules": []}
    page = resolve(outputs["texts_page"])
    rows = page_records(numbers, records)
    export_name = os.path.basename(inputs["texts"])
    sc.write_page(page, settings, HEADING, "texts", inputs["texts"], SHEET_FIELDS,
                  intro(export_name, len(rows)), rows)

    print("core              : %d studies" % len(rows))
    print("without a DOI     : %s" % (", ".join(str(r["number"]) for r in rows if not r["doi"])
                                      or "none"))
    print("written           : %s (exports %s)" % (rel(page), export_name))

    texts = resolve(inputs["texts"])
    if not os.path.isfile(texts):
        print("returned file     : not yet in place (%s); nothing read back" % inputs["texts"])
        return
    answers = read_answers(texts, rows)
    checksums = inputs.get("texts_checksums")
    if checksums:
        check_saved_files(answers, resolve(checksums))
    flow = texts_flow(answers)
    flow_path = resolve(outputs["texts_flow"])
    write_csv(flow_path, FLOW_FIELDS, flow)
    report = resolve(outputs["texts_report"])
    with open(report, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_texts(answers, flow, inputs["texts"], file_sha(texts), checksums))
    for r in flow:
        print("  %-60s %4d" % (r["label"], r["count"]))
    print("written           : %s, %s" % (rel(report), rel(flow_path)))


if __name__ == "__main__":
    main()
