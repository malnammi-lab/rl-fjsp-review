"""Gather the coding agent's answers on the core into the published dataset.

    python runners/run_all.py --only core-gather

Reads [inputs]: Part B's questions, the locked core, the papers' markdown and checksums, the
responses, and the verdicts, runs and corrections when they exist. Checks each response again;
on a missing input or any problem it stops and writes nothing. Writes [outputs]: one row per
study, the answer and item tables (no quote text), a report, and the private quotes file.
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

from src import coreblocks as cb  # noqa: E402
from src import fulltext  # noqa: E402
from runners.core_check import checksums, kept_blocks, responses  # noqa: E402
from runners.core_selection import file_sha, table, write_csv  # noqa: E402
from runners.core_texts import read_core  # noqa: E402
from runners.screening_consensus import load_config, rel, resolve  # noqa: E402

# A study's role, end to end or steering, from the role its full text gives (A01).
ROLES = {"end-to-end": "end-to-end", "steering-rules": "steering",
         "steering-heuristic": "steering"}
# Each item group's side table: the [outputs] key and the column its item's answer fills.
GROUP_OUT = {"baseline": ("baselines", "baseline"), "claim": ("claims", "claim"),
             "transfer_test": ("transfer_tests", "differs")}
STUDY_FIELDS = ["number", "year", "step", "stratum", "role"]
ANSWER_FIELDS = ["number", "id", "qid", "name", "section", "rq", "item", "field", "value",
                 "verdict", "judge_value", "authors_value", "pages", "quote_sha256"]
QUOTE_FIELDS = ["number", "id", "page", "quote", "sha256"]
# The authors' corrections (protocol, Amendments: answers corrected by the authors): one row
# per answer, its value one the question allows, the pages read, who decided and when, and
# the reason.
CORRECTION_FIELDS = ["number", "qid", "name", "value", "pages", "decided", "reason"]
PAGES = re.compile(r"^(\d+(\|\d+)*)?$")
# The [inputs] files the gather cannot run without. Verdicts, runs and corrections are optional.
REQUIRED = ["spec", "map", "core", "core_lock", "md_checksums"]
DISPUTED = ("partly", "not-supported")
VERDICTS = ("supported", "partly", "not-supported", "cannot-judge", "none")
MD = re.compile(r"^(\d+)/(\d+)\.md$")
HEADER = re.compile(r"^([a-z][a-z ]*):\s*(.*)$")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_in_full(path):
    """The numbers of the studies whose markdown the checksums list."""
    return sorted(int(m.group(1)) for m in map(MD.match, checksums(path))
                  if m and m.group(1) == m.group(2))


def core_rows(path, lock_path):
    """{number: {step, stratum, year}} of the locked core."""
    numbers = set(read_core(path, lock_path))
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {int(r["number"]): {"step": r.get("step", "").strip(),
                                   "stratum": r.get("stratum", "").strip(),
                                   "year": r.get("year", "").strip()}
                for r in csv.DictReader(fh) if int(r["number"]) in numbers}


def header_fields(lines):
    """{key: value} of a response's header lines such as 'model: Qwen/... @ <revision>'."""
    out = {}
    for line in lines:
        found = HEADER.match(line.strip())
        if found:
            out[found.group(1)] = found.group(2).strip()
    return out


def read_verdicts(path):
    """{(number, block id): (verdict, proposed answer, {field: proposed value})}, or None when
    there is no verdicts file. Reads no quote: the proposals' evidence, the reasons and the
    notes are left in the file."""
    if not path or not os.path.isfile(path):
        return None
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            try:
                fields = json.loads(r.get("proposed_fields") or "{}")
            except ValueError:
                fields = {}
            out[(int(r["number"]), r["id"].strip())] = (
                (r.get("verdict") or "").strip().lower(), (r.get("proposed_answer") or "").strip(),
                fields if isinstance(fields, dict) else {})
    return out


def read_runs(path):
    """({number: row}, fieldnames) of the coding run's coding-runs.csv, or (None, []) when it
    does not exist."""
    if not path or not os.path.isfile(path):
        return None, []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = {int(r["number"]): r for r in reader}
        return rows, list(reader.fieldnames or [])


def read_corrections(path, spec):
    """{number: [(question, cell, row)]} of the authors' corrections, or {} when there is no
    file. Refuses, writing nothing: a row whose question is not one of Part B's questions (an
    item cannot be corrected) or whose name is not its question's, a value the question does
    not allow, pages that are not page numbers, an answer corrected twice."""
    if not path or not os.path.isfile(path):
        return {}
    out, seen, wrong = {}, set(), []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for line, r in enumerate(csv.DictReader(fh), start=2):
            qid, name = (r.get("qid") or "").strip(), (r.get("name") or "").strip()
            q = spec.questions.get(qid)
            if q is None or q.name != name:
                wrong.append("line %d: %s is not the question of Part B named %s"
                             % (line, qid, name))
                continue
            try:
                number = int(r.get("number") or "")
            except ValueError:
                wrong.append("line %d: no study number" % line)
                continue
            cell, problems = cb.check_value(q.kind, r.get("value"), q.codes, q.alone, q.special,
                                            q.words, cb.most(spec, q))
            if problems:
                wrong.append("line %d: %s, %s" % (line, qid, problems[0][0]))
            elif not PAGES.match((r.get("pages") or "").strip()):
                wrong.append("line %d: %s, pages are page numbers joined by |" % (line, qid))
            elif (number, qid) in seen:
                wrong.append("line %d: %d %s corrected twice" % (line, number, qid))
            else:
                seen.add((number, qid))
                out.setdefault(number, []).append((q, cell, r))
    if wrong:
        raise SystemExit("Nothing was written: the corrections in %s: %s."
                         % (path, "; ".join(wrong)))
    return out


def apply_corrections(spec, values, answers, fixes, paper):
    """The authors' corrections of one study laid over its answers: each corrected cell put in
    `values` (so its row and its derived columns follow it) and beside the coder's value in
    its answer row, which keeps the coder's value and the judge's verdict. [problems] when
    the corrected answers break the scheme: a question that does not apply answered, one that
    applies answered not-applicable, a rule between questions, or a published text that shares
    eight words in a row with the paper."""
    problems = []
    rows = {a["qid"]: a for a in answers if a["field"] == "" and a["item"] == ""}
    for q, cell, r in fixes:
        values[q.name] = cell
        rows[q.qid]["authors_value"] = cb.show(cell)
        for text in ((cb.show(cell) if q.kind == "text" else ""), r.get("reason") or ""):
            if text and fulltext.shared_run(text, paper):
                problems.append("%s: the correction shares %d words in a row with the paper"
                                % (q.qid, fulltext.RUN))
    for q in spec.questions.values():
        cell = values.get(q.name)
        if cell is None or not q.conditions:
            continue
        fits = cb.applies(q, values)
        if fits is False and cell != "not-applicable":
            problems.append("%s: the question does not apply (%s), answer not-applicable"
                            % (q.qid, cb.why(q, values)))
        if fits is True and cell == "not-applicable":
            problems.append("%s: the question applies (%s), answer it" % (q.qid, cb.why(q, values)))
    problems += ["%s: %s" % (spec.by_name[rule.then].qid, what)
                 for rule, what in cb.broken_rules(spec, values)]
    return problems


def judged(kind, codes, alone, special, words, proposed):
    """The judge's proposal as a published cell: only a valid answer of a question that is not
    text, so that no proposal can carry the paper's words; blank otherwise."""
    if kind == "text" or not proposed:
        return ""
    cell, problems = cb.check_value(kind, proposed, codes, alone, special, words)
    return cb.show(cell) if cell is not None and not problems else ""


def gather_study(spec, number, path, paper, verdicts):
    """(row values, answer rows, item rows by group, quote rows, problems in words) of one
    study's response."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    head, blocks, split = cb.split_response(text)
    problems = ["%s: %s" % (p["id"], p["what"]) for p in split]
    problems += ["%s: %s" % (p["id"], p["what"]) for p in cb.check_response(spec, paper, blocks)]
    kept = kept_blocks(blocks)
    values = cb.cells(spec, kept)
    answers, items, quotes = [], {g: [] for g in spec.groups}, []
    for bid in cb.block_order(spec, kept):
        b = kept[bid]
        q = spec.questions.get(b.qid)
        if q is None:
            continue
        g = spec.groups[q.group] if b.item is not None else None
        cell = cb.value(spec, b)
        if verdicts is None:
            verdict, proposed, fields = "", "", {}
        else:
            verdict, proposed, fields = verdicts.get((number, bid), ("none", "", {}))
        disputed = verdict in DISPUTED
        kind = g.kind if g else q.kind
        if kind == "text" and cell is not None and not cb.is_special(q, cell):
            run = fulltext.shared_run(cell, paper)
            if run:
                problems.append("%s: the published text shares %d words in a row with the paper"
                                % (bid, fulltext.RUN))
        base = {"number": number, "id": bid, "qid": q.qid, "name": g.name if g else q.name,
                "section": q.section, "rq": q.rq, "item": b.item or "", "verdict": verdict,
                "authors_value": ""}
        answers.append(dict(base, field="", value=cb.show(cell),
                            judge_value=judged(kind, g.codes if g else q.codes,
                                               () if g else q.alone, () if g else q.special,
                                               g.words if g else q.words, proposed)
                            if disputed else "",
                            pages="|".join(str(p) for p in sorted({p for p, _ in b.evidence})),
                            quote_sha256="|".join(sha(quote) for _, quote in b.evidence)))
        for page, quote in b.evidence:
            quotes.append({"number": number, "id": bid, "page": page, "quote": quote,
                           "sha256": sha(quote)})
        if g is None:
            continue
        row = {"number": number, "item": b.item, GROUP_OUT[g.name][1]: cb.show(cell),
               "verdict": verdict}
        for field, codes in g.fields.items():
            given = b.fields.get(field, "").strip().lower()
            row[field] = given
            proposal = str(fields.get(field, "")).strip().lower() if disputed else ""
            answers.append(dict(base, field=field, value=given,
                                judge_value=proposal if proposal in codes else "",
                                pages="", quote_sha256=""))
        items[g.name].append(row)
    return head, values, answers, items, quotes, problems


def study_row(spec, number, core, head, values):
    info = header_fields(head)
    row = {"number": number, "year": core["year"], "step": core["step"],
           "stratum": core["stratum"],
           "role": ROLES.get(values.get("policy_role"), cb.show(values.get("policy_role")))}
    for q in spec.questions.values():
        row[q.name] = cb.show(values.get(q.name))
    for name, cell in cb.derive(spec, values).items():
        row[name] = cb.show(cell)
    row["coder"], row["date"] = info.get("model", ""), info.get("date", "")
    return row


def coded_fields(spec):
    return (STUDY_FIELDS + [q.name for q in spec.questions.values()] + list(spec.derived)
            + ["coder", "date"])


def item_fields(spec, group):
    return ["number", "item", GROUP_OUT[group][1]] + list(spec.groups[group].fields) + ["verdict"]


def render(config, folder, spec, studies, answers, items, verdicts, inputs, corrections=""):
    lines = ["# The gather of the core's answers", "",
             "Written by `runners/core_gather.py` from `%s`; do not edit, rerun the runner."
             % config, ""]
    questions = [a for a in answers if a["field"] == "" and a["item"] == ""]
    lines += ["%d studies gathered, each response checked again against its paper with no "
              "problem left: %d answers to the questions, %d item blocks. Published: codes, "
              "numbers, page numbers and a SHA-256 of each quote; no quote text and no note."
              % (len(studies), len(questions), sum(len(v) for v in items.values())), ""]
    lines += ["## Items", ""]
    lines += table([("Group", False), ("Studies with items", True), ("Items", True)],
                   [(g, len({r["number"] for r in rows}), len(rows)) for g, rows in items.items()])
    final = [a.get("authors_value") or a["value"] for a in questions]
    special = Counter(v for v in final if v in cb.SPECIAL + ("none",))
    lines += ["", "## Answers that report no content", "",
              "Special answers and counts of none, over all the studies' answers to the "
              "questions (the authors' value where they corrected one).", ""]
    lines += table([("Answer", False), ("Answers", True)],
                   [(k, special[k]) for k in cb.SPECIAL + ("none",)])
    lines += ["", "## The judge's verdicts", ""]
    if verdicts is None:
        lines += ["No verdicts yet: the verdict column is empty."]
    else:
        lines += ["Every block's verdict, by section (`none`: the judge gave no valid reply for "
                  "the unit that held it).", ""]
        by = Counter((a["section"], a["verdict"]) for a in answers if a["field"] == "")
        sections = sorted({a["section"] for a in answers}, key=lambda s: (s == "Q", s))
        lines += table([("Section", False)] + [(v, True) for v in VERDICTS],
                       [[s] + [by[(s, v)] for v in VERDICTS] for s in sections])
    fixed = [a for a in questions if a.get("authors_value")]
    lines += ["", "## Answers corrected by the authors", ""]
    if not fixed:
        lines += ["None."]
    else:
        lines += ["Answers the authors read against the paper and corrected, with the answers "
                  "that follow from them by Part B's rules (protocol, Amendments: answers "
                  "corrected by the authors; `%s`, with the pages read and the reasons). The "
                  "published rows and the tables take the authors' value; the answers' file "
                  "keeps the coder's value and the judge's verdict beside it, and the agreement "
                  "of coder and judge is computed on the coder's." % corrections, ""]
        lines += table([("Study", True), ("Question", False), ("Coder", False),
                        ("Judge", False), ("Judge's proposal", False), ("Authors", False)],
                       [(a["number"], "%s %s" % (a["qid"], a["name"]), a["value"], a["verdict"],
                         a["judge_value"], a["authors_value"]) for a in fixed])
    lines += ["", "## Inputs", ""]
    lines += table([("Input", False), ("SHA-256", False)], [(k, v) for k, v in inputs])
    return "\n".join(lines) + "\n"


def write_all(cfg, spec, studies, answers, items, runs, run_fields):
    out = cfg["outputs"]
    write_csv(resolve(out["coded"]), coded_fields(spec), studies or [])
    write_csv(resolve(out["answers"]), ANSWER_FIELDS, answers)
    for group, (key, _) in GROUP_OUT.items():
        write_csv(resolve(out[key]), item_fields(spec, group), items.get(group, []))
    write_csv(resolve(out["runs"]), run_fields or ["number"], runs)


def require_inputs(inputs):
    """Stops, writing nothing, when an input is missing: a file of REQUIRED, the papers'
    folder, or the responses (at least one). A clone of the repository has neither folder, so
    its published datasets stay as they are."""
    missing = ["%s (%s)" % (key, inputs[key]) for key in REQUIRED
               if not os.path.isfile(resolve(inputs[key]))]
    if not os.path.isdir(resolve(inputs["texts"])):
        missing.append("texts (%s)" % inputs["texts"])
    folder = resolve(inputs["responses"])
    if not os.path.isdir(folder) or not responses(folder):
        missing.append("responses (%s, at least one response-<number>.md)" % inputs["responses"])
    if missing:
        raise SystemExit("Nothing was written: missing input(s): %s." % "; ".join(missing))


def gather(config_path, override=None):
    cfg = load_config(config_path, override)
    inputs, outputs = cfg["inputs"], cfg["outputs"]
    require_inputs(inputs)
    spec = cb.load_spec(resolve(inputs["spec"]), resolve(inputs["map"]))
    folder = resolve(inputs["responses"])
    report = resolve(outputs["report"])
    os.makedirs(os.path.dirname(report), exist_ok=True)
    core = core_rows(resolve(inputs["core"]), resolve(inputs["core_lock"]))
    read = read_in_full(resolve(inputs["md_checksums"]))
    found = dict(responses(folder))
    outside = sorted(n for n in found if n not in read or n not in core)
    absent = sorted(n for n in read if n in core and n not in found)
    missing = []
    if absent:
        missing.append("no response for the studies read in full %s"
                       % ", ".join(map(str, absent)))
    if outside:
        missing.append("responses for studies not read in full or outside the core: %s"
                       % ", ".join(map(str, outside)))
    if missing:
        raise SystemExit("Nothing was written: %s." % "; ".join(missing))
    sums = checksums(resolve(inputs["md_checksums"]))
    verdicts = read_verdicts(resolve(inputs["verdicts"]) if inputs.get("verdicts") else None)
    runs, run_fields = read_runs(resolve(inputs["runs"]) if inputs.get("runs") else None)
    corrections = read_corrections(resolve(inputs["corrections"]) if inputs.get("corrections")
                                   else None, spec)
    stray = sorted(n for n in corrections if n not in found)
    if stray:
        raise SystemExit("Nothing was written: corrections for studies with no response: %s."
                         % ", ".join(map(str, stray)))
    studies, answers, quotes, wrong = [], [], [], []
    items = {g: [] for g in spec.groups}
    for number, path in sorted(found.items()):
        key = "%d/%d.md" % (number, number)
        md = os.path.join(resolve(inputs["texts"]), key)
        if not os.path.isfile(md) or file_sha(md) != sums.get(key):
            raise SystemExit("Nothing was written: %s is missing or differs from its checksum "
                             "in %s." % (md, inputs["md_checksums"]))
        if runs is not None:
            held = runs.get(number, {}).get("response_sha256", "")
            if held != file_sha(path):
                wrong.append("%d: the response differs from its SHA-256 in %s"
                             % (number, inputs["runs"]))
        paper = fulltext.load(md)
        head, values, rows, its, qs, problems = gather_study(spec, number, path, paper, verdicts)
        if number in corrections:
            problems += apply_corrections(spec, values, rows, corrections[number], paper)
        wrong += ["%d, %s" % (number, p) for p in problems]
        studies.append(study_row(spec, number, core[number], head, values))
        answers += rows
        quotes += qs
        for g, r in its.items():
            items[g] += r
    if wrong:
        raise SystemExit("Nothing was written: %d problem(s), first: %s. Run "
                         "runners/core_check.py over the responses for the details."
                         % (len(wrong), "; ".join(wrong[:10])))
    run_rows = [runs[n] for n in sorted(found)] if runs is not None else []
    write_all(cfg, spec, studies, answers, items, run_rows, run_fields)
    write_csv(resolve(outputs["quotes"]), QUOTE_FIELDS, quotes)
    digest = sha("".join("%d %s\n" % (n, file_sha(p)) for n, p in sorted(found.items())))
    sources = [("spec (%s)" % inputs["spec"], file_sha(resolve(inputs["spec"]))),
               ("map (%s)" % inputs["map"], file_sha(resolve(inputs["map"]))),
               ("core (%s)" % inputs["core"], file_sha(resolve(inputs["core"]))),
               ("responses, over their files' SHA-256 (%d files)" % len(found), digest)]
    for key in ("verdicts", "runs", "corrections"):
        if inputs.get(key) and os.path.isfile(resolve(inputs[key])):
            sources.append(("%s (%s)" % (key, os.path.basename(inputs[key])),
                            file_sha(resolve(inputs[key]))))
    with open(report, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(rel(config_path), inputs["responses"], spec, studies, answers, items,
                        verdicts, sources, inputs.get("corrections", "")))
    print("studies gathered  : %d" % len(studies))
    print("answers           : %d rows (%d item blocks)"
          % (len(answers), sum(len(v) for v in items.values())))
    print("verdicts          : %s" % ("none yet" if verdicts is None else "joined"))
    print("corrections       : %d answer(s) of %d stud(ies) by the authors"
          % (sum(len(v) for v in corrections.values()), len(corrections)))
    print("written           : %s, %s and the side tables; no quote text is published"
          % (rel(resolve(outputs["coded"])), rel(report)))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "core-gather.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")
    args = parser.parse_args()
    gather(args.config, args.override)


if __name__ == "__main__":
    main()
