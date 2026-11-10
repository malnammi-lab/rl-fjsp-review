"""A person's check of questions on the fifth of the core, against the coding agent: the six
questions of the protocol, or some of them, as the config asks.

    python runners/run_all.py --only core-human-check

Reads the fifth (results/core-coding/draws.csv) and its records (datasets/references.json).
Writes the person's folder ([outputs] folder: the page, a README and each study's PDF) only
when [inputs] full_texts exists. Once the returned file ([inputs] answers) is in place, checks
it and writes its agreement with datasets/coded-studies.csv to [outputs] report and table.
"""

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import tomllib
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus  # noqa: E402
from runners.core_selection import table, write_csv  # noqa: E402
from runners.screening_consensus import load_config, rel, resolve  # noqa: E402

QUESTION_IDS = ["role", "algorithm", "readiness", "runs", "baselines", "transfer"]
GIVEN = ["number", "title"]
PLACEHOLDER = "__PAGE_DATA__"
NOT_REPORTED = "not-reported"
TABLE_FIELDS = ["question", "studies", "agree", "share", "kappa"]
REPORT_TITLE = "A person's check of six questions on the fifth"
COUNT_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}


def fields(questions):
    """The columns of the file the page exports and the runner reads back."""
    return GIVEN + ["coder"] + [q["id"] for q in questions] + ["note"]


def load_questions(cfg):
    """The config's questions: the six of QUESTION_IDS, or some of them, in that order.
    Refuses any other set."""
    questions = cfg.get("question") or []
    ids = [q.get("id") for q in questions]
    if not ids or ids != [i for i in QUESTION_IDS if i in ids]:
        raise SystemExit("The config's questions must be %s, or some of them, in that order; "
                         "it has %s." % (", ".join(QUESTION_IDS), ", ".join(map(str, ids))))
    for q in questions:
        if not q.get("codes"):
            raise SystemExit("The question %s offers no answer." % q["id"])
    return questions


def read_draw(path, draw):
    """The record numbers of the studies drawn as `draw`, ascending."""
    if not os.path.isfile(path):
        raise SystemExit("%s not found: the draws, written by runners/core_draws.py." % path)
    with open(path, encoding="utf-8-sig", newline="") as fh:
        numbers = sorted(int(r["number"]) for r in csv.DictReader(fh)
                         if (r.get("draw") or "").strip() == draw)
    if not numbers:
        raise SystemExit("%s holds no study drawn as %s." % (path, draw))
    return numbers


def page_rows(numbers, records):
    """The studies as the page shows them."""
    out = []
    for n in numbers:
        r = records[n]
        out.append({"number": n, "title": r.title or "", "first_author": r.first_author or "",
                    "year": r.year or "", "venue": r.venue or "", "doi": r.doi or "",
                    "link": "https://doi.org/%s" % r.doi if r.doi else "",
                    "pdf": "pdfs/%d.pdf" % n})
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def copy_pdfs(numbers, source, folder):
    """Copies each study's full text to folder/pdfs/<number>.pdf, leaving a copy that is
    already the same file; refuses a study whose full text is not saved."""
    missing = [n for n in numbers if not os.path.isfile(os.path.join(source, "%d.pdf" % n))]
    if missing:
        raise SystemExit("No full text saved in %s for %s." % (source, ", ".join(map(str, missing))))
    target = os.path.join(folder, "pdfs")
    os.makedirs(target, exist_ok=True)
    copied = 0
    for n in numbers:
        src, dst = os.path.join(source, "%d.pdf" % n), os.path.join(target, "%d.pdf" % n)
        if os.path.isfile(dst) and sha256(dst) == sha256(src):
            continue
        shutil.copyfile(src, dst)
        copied += 1
    return copied


def write_page(path, template, data):
    """The page: the template with the data in its placeholder, as JSON in which every "<" is
    escaped, so no text in a record can close the block."""
    if template.count(PLACEHOLDER) != 1:
        raise SystemExit("The page template must hold %s exactly once." % PLACEHOLDER)
    text = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(template.replace(PLACEHOLDER, text))


def page_data(rows, questions, export_name, title="", intro=""):
    """What the page holds: the studies, the questions and the name of the file it exports,
    and the page's own title and opening text when the config gives them. No model answer
    is among them."""
    data = {"sheet_id": os.path.splitext(export_name)[0], "save_as": export_name,
            "columns": fields(questions), "studies": rows,
            "questions": [{k: q.get(k) for k in ("id", "scheme", "label", "ask", "codes",
                                                 "number", "definition")} for q in questions]}
    if title:
        data["title"] = title
    if intro:
        data["intro"] = intro
    return data


def readme(count, export_name, asked=6, note=""):
    """The README beside the page, for a check of `asked` questions; `note`, when given,
    follows its first paragraph."""
    words = COUNT_WORDS.get(asked, str(asked))
    noun = "question" if asked == 1 else "questions"
    the = "the question" if asked == 1 else "the %s questions" % words
    return "\n".join([
        "# %s %s on %d papers" % (words.capitalize(), noun, count), "",
        "This folder is a check of the review's coding: you answer %s %s on each of "
        "%d papers, reading each paper yourself. Your answers are compared afterwards with "
        "the coding model's, which you do not see." % (words, noun, count), ""] +
        ([note, ""] if note else []) + [
        "1. Open `human-check.html` from your computer (double-click it), not in OneDrive's "
        "web viewer, which blocks the download.",
        "2. Type your name at the top.",
        "3. Press **Show guide** to read each question's definition and its answers. Apply "
        "them as written, even where your own reading of a paper would differ.",
        "4. For each paper, open its PDF (the link opens `pdfs/<number>.pdf` from this "
        "folder), and answer %s. A note per paper is optional, for example "
        "the page an answer rests on." % the,
        "5. Your answers are kept in this browser as you go, so you can stop and come back. "
        "To move to another computer, export, then use **Import CSV** there.",
        "6. When all %d papers are answered, press **Export CSV**. It saves `%s` to your "
        "downloads folder; put it in this folder." % (count, export_name), "",
        "Please do not look up the review's own answers for these papers, or discuss them "
        "with anyone, until you have exported your file.", ""])


def read_answers(path, rows, questions):
    """The returned file, checked against the page's studies: one row for each and none
    other, the given columns as the page gave them, every answer one the page offers, every
    question answered and the coder named. Refuses the file on any fault, naming every row
    that has it. Returns {number: {question id: answer, "coder": ..., "note": ...}}."""
    columns = fields(questions)
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        absent = [c for c in columns if c not in (reader.fieldnames or [])]
        if absent:
            raise SystemExit("%s has no column %s." % (path, ", ".join(absent)))
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
    expected = {r["number"]: r for r in rows}
    for n in sorted(set(by_number) - set(expected)):
        fault("not a study of the fifth", n)
    for n in sorted(set(expected) - set(by_number)):
        fault("no row", n)

    answers = {}
    for n, r in expected.items():
        row = by_number.get(n)
        if row is None:
            continue
        if (row.get("title") or "").strip() != r["title"].strip():
            fault("the title differs from the record", n)
        a = {"coder": (row.get("coder") or "").strip(), "note": (row.get("note") or "").strip()}
        if not a["coder"]:
            fault("no coder named", n)
        for q in questions:
            v = (row.get(q["id"]) or "").strip()
            a[q["id"]] = v
            if not v:
                fault("%s not answered" % q["id"], n)
            elif q.get("number"):
                if v not in q["codes"] and not (v.isdigit() and int(v) >= 1):
                    fault("%s is neither a whole number of at least 1 nor %s"
                          % (q["id"], " or ".join(q["codes"])), n)
            elif v not in q["codes"]:
                fault("%s is not one of %s" % (q["id"], ", ".join(q["codes"])), n)
        answers[n] = a
    if faults:
        raise SystemExit("%s is refused:\n%s" % (path, "\n".join(
            "  %s: %s" % (what, ", ".join(map(str, ns))) for what, ns in faults.items())))
    return answers


def reduce_baselines(count, runs):
    """D07 reduced: `none` with no baseline group, `yes` when every group was rerun,
    otherwise `no`."""
    if not runs or (count or "").strip() in ("", "0", "not-stated"):
        return "none"
    return "yes" if all(r == "rerun" for r in runs) else "no"


def reduce_transfer(count):
    """E01 reduced: `yes` with one transfer test or more."""
    value = (count or "").strip()
    return "yes" if value.isdigit() and int(value) >= 1 else "no"


def runs_bin(value):
    """D14's bin: `1`, `more than 1` or not reported."""
    value = (value or "").strip()
    if value.isdigit():
        return "1" if int(value) == 1 else "more than 1"
    return value


def agent_answers(numbers, coded_path, baselines_path):
    """The coding agent's answers to the six questions, D07 and E01 each reduced to one
    answer (protocol, Amendments: coding and checking the core)."""
    with open(coded_path, encoding="utf-8-sig", newline="") as fh:
        coded = {int(r["number"]): r for r in csv.DictReader(fh) if (r.get("number") or "").strip()}
    runs = {}
    with open(baselines_path, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            runs.setdefault(int(r["number"]), []).append((r.get("run") or "").strip())
    absent = [n for n in numbers if n not in coded]
    if absent:
        raise SystemExit("%s holds no study %s." % (coded_path, ", ".join(map(str, absent))))
    out = {}
    for n in numbers:
        r = coded[n]
        out[n] = {"role": r["policy_role"], "algorithm": r["algorithm"],
                  "readiness": r["readiness_level"], "runs": r["seeds"],
                  "baselines": reduce_baselines(r["baselines"], runs.get(n, [])),
                  "transfer": reduce_transfer(r["transfer_tests"])}
    return out


def kappa(pairs):
    """Cohen's kappa over (a, b) pairs, or None when either side gives a single code (the
    expected agreement is then 1 and kappa is undefined)."""
    n = len(pairs)
    if not n:
        return None
    a, b = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    if len(a) < 2 or len(b) < 2:
        return None
    observed = sum(1 for x, y in pairs if x == y) / n
    expected = sum(a[c] * b[c] for c in set(a) | set(b)) / (n * n)
    return (observed - expected) / (1 - expected)


def compare(numbers, person, agent, family, ids=QUESTION_IDS):
    """One row per question asked (and per derived view of it), and every disagreement."""
    views = [(q, q, None) for q in ids]
    if "algorithm" in ids:
        at = [v[0] for v in views].index("algorithm") + 1
        views.insert(at, ("algorithm family", "algorithm", lambda v: family.get(v, v)))
    if "runs" in ids:
        at = [v[0] for v in views].index("runs") + 1
        views.insert(at, ("training runs, by bin", "runs", runs_bin))
    rows, disagreements = [], []
    for name, key, view in views:
        pairs = []
        for n in numbers:
            p, g = person[n][key], agent[n][key]
            if view:
                p, g = view(p), view(g)
            pairs.append((p, g))
            if p != g and view is None:
                disagreements.append({"number": n, "question": key, "person": p, "agent": g})
        agree = sum(1 for p, g in pairs if p == g)
        k = kappa(pairs)
        rows.append({"question": name, "studies": len(pairs), "agree": agree,
                     "share": "%.1f" % (100.0 * agree / len(pairs)),
                     "kappa": "" if k is None else "%.2f" % k})
    return rows, disagreements


def render(rows, disagreements, coder, answers_name, answers_sha, title=REPORT_TITLE, note="",
           config="configs/core-human-check.toml"):
    lines = ["# " + title, "",
             "Written by `runners/core_human_check.py` from `%s`; do "
             "not edit, rerun the runner. The person's file `%s` (SHA-256 %s), coded by %s, "
             "against the coding agent's answers (`datasets/coded-studies.csv`, the authors' "
             "corrections laid over them), reduced as the protocol states (Amendments: coding "
             "and checking the core). Kappa is left blank where either side gives a single "
             "code." % (config, answers_name, answers_sha, coder), ""]
    if note:
        lines += [note, ""]
    lines += ["## Agreement", ""]
    lines += table([("Question", False), ("Studies", True), ("Agree", True), ("Share (%)", True),
                    ("Kappa", True)],
                   [(r["question"], r["studies"], r["agree"], r["share"], r["kappa"]) for r in rows])
    lines += ["", "## Disagreements", ""]
    lines += (table([("Record", True), ("Question", False), ("Person", False), ("Coding agent", False)],
                    [(d["number"], d["question"], d["person"], d["agent"]) for d in disagreements])
              if disagreements else ["None."])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "core-human-check.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")
    args = parser.parse_args()
    cfg = load_config(args.config, args.override)
    inputs, outputs = cfg["inputs"], cfg["outputs"]
    page_cfg, report_cfg = cfg.get("page", {}), cfg.get("report", {})
    questions = load_questions(cfg)

    numbers = read_draw(resolve(inputs["draws"]), inputs["draw"])
    records = {r.number: r for r in corpus.load_references(resolve(inputs["references"]))}
    absent = [n for n in numbers if n not in records]
    if absent:
        raise SystemExit("%s holds no record %s." % (inputs["references"], ", ".join(map(str, absent))))
    rows = page_rows(numbers, records)
    export_name = os.path.basename(inputs["answers"])

    # The page, its README and the PDFs need the full texts, which a clone does not have.
    full_texts = resolve(inputs["full_texts"])
    if os.path.isdir(full_texts):
        folder = resolve(outputs["folder"])
        copied = copy_pdfs(numbers, full_texts, folder)
        with open(resolve(inputs["template"]), encoding="utf-8") as fh:
            template = fh.read()
        page = resolve(outputs["page"])
        write_page(page, template, page_data(rows, questions, export_name,
                                             page_cfg.get("title", ""), page_cfg.get("intro", "")))
        with open(resolve(outputs["readme"]), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(readme(len(rows), export_name, len(questions), page_cfg.get("readme_note", "")))
        print("fifth             : %d studies (%s)" % (len(rows), ", ".join(map(str, numbers))))
        print("full texts copied : %d (the others already in place)" % copied)
        print("written           : %s (exports %s)" % (rel(page), export_name))
    else:
        print("full texts        : not found (%s); no page, README or PDF written"
              % inputs["full_texts"])

    answers_path = resolve(inputs["answers"])
    if not os.path.isfile(answers_path):
        print("returned file     : not yet in place (%s); nothing compared" % inputs["answers"])
        return
    person = read_answers(answers_path, rows, questions)
    agent = agent_answers(numbers, resolve(inputs["coded"]), resolve(inputs["baselines"]))
    with open(resolve(inputs["coding"]), "rb") as fh:
        family = tomllib.load(fh)["derived"]["algorithm_family"]["map"]
    result, disagreements = compare(numbers, person, agent, family, [q["id"] for q in questions])
    write_csv(resolve(outputs["table"]), TABLE_FIELDS, result)
    coders = sorted({a["coder"] for a in person.values()})
    config_name = rel(os.path.abspath(args.config)).replace("\\", "/")
    with open(resolve(outputs["report"]), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(result, disagreements, ", ".join(coders), inputs["answers"],
                        sha256(answers_path), report_cfg.get("title", REPORT_TITLE),
                        report_cfg.get("note", ""), config_name))
    for r in result:
        print("  %-24s %2d of %2d  %6s%%  kappa %s" % (r["question"], r["agree"], r["studies"],
                                                     r["share"], r["kappa"] or "-"))
    print("written           : %s, %s" % (rel(resolve(outputs["report"])),
                                          rel(resolve(outputs["table"]))))


if __name__ == "__main__":
    main()
