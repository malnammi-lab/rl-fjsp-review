"""The checks code makes of the core's answers (datasets/coding-scheme.md, Part B): for the
coding agent while it works, and over every response once the agents have finished.

    python runners/core_check.py --tool --paper <n>.md < request.json
    python runners/core_check.py --config configs/core-check.toml

--tool answers one request of the acquisition tool's agent loop, or of its judge's
preparation: a JSON object {"op": ..., ...} on stdin, one JSON object on stdout, both plain
ASCII: {"contract": CONTRACT, "fingerprint": ..., "ok": true, "result": ...}, or "ok": false
with an "error". In this mode it reads only FILES, found beside it in this repository, and it
refuses a copy whose fingerprint (the SHA-256 of FILES) differs from the one it was prepared
with. The operations
and their arguments:

    fingerprint                     nothing but the fingerprint
    files                           FILES, the files to copy, relative to the codebase
    questions       select          the questions `select` names ("C01 to C14", "D"; all
                                    when absent), in Part B's order, with names and sections
    scheme          sections        Part B's general rules and the sections named, all when
                                    absent; section A brings Part A, whose rules it takes
    outline                         the paper's headings
    search          pattern         the lines that match a regular expression
    read            page, or start_line and end_line
                                    a page, or a range of lines
    check_quote     page, quote     whether the quote is on the page; if not, where it is
    check_block     block, blocks   one block's problems, given the blocks already kept
                                    ({id: text}); "kept" false when it must be written again
    check_response  blocks, scope   the problems left among the blocks for the questions in
                                    scope (IDs, or text such as "C01 to C14"; all when absent)
    assemble        blocks, header  the response's text, its blocks in Part B's order
    blocks          response        a response's blocks in Part B's order, each with its
                                    question and the pages its quotes cite (for the judge)
    rules           ids             each question's rules as the scheme states them: Part B's
                                    section of the question, or, for section A, Part A's
                                    general rules and the axis's section (for the judge)
    excerpt         pages, or body  the text of some pages ("all" for every page), or the
                                    paper without its reference list

--config checks every response in [inputs] responses (files response-<number>.md) against
its paper, the paper first checked against its checksum, and writes [outputs] problems (a
CSV: number, id, what) and report. Neither holds a word of the papers: a problem's "what"
never quotes them (src/coreblocks.py). A response folder that does not exist yet is
reported as such.

Written on 20 October 2026, before any full text was coded.
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import coreblocks as cb  # noqa: E402
from src import fulltext  # noqa: E402

CONTRACT = 1
# The files the checker reads in --tool mode: the checks, the questions, the scheme, and the
# agents' instructions and tools.
FILES = ["src/__init__.py", "src/fulltext.py", "src/coreblocks.py", "src/mapcodes.py",
         "runners/core_check.py", "configs/core-coding.toml", "configs/map.toml",
         "datasets/coding-scheme.md", "configs/core-coding-prompt.md",
         "configs/core-coding-tools.json", "configs/core-judge-prompt.md"]
SPEC = os.path.join(REPO, "configs", "core-coding.toml")
MAP = os.path.join(REPO, "configs", "map.toml")
SCHEME = os.path.join(REPO, "datasets", "coding-scheme.md")
RESPONSE = re.compile(r"^response-0*(\d+)\.md$")
FIELDS = ["number", "id", "what"]
PAPER_OPS = ("outline", "search", "read", "check_quote", "check_block", "check_response",
             "excerpt")


def fingerprint(root=REPO):
    """SHA-256 over FILES' names and contents, in FILES' order."""
    h = hashlib.sha256()
    for name in FILES:
        with open(os.path.join(root, name), "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        h.update(("%s %s\n" % (name, digest)).encode("ascii"))
    return h.hexdigest()


def part(text, heading):
    """The part of the scheme under a level-two heading, up to the next one."""
    start = text.index("\n" + heading)
    end = text.find("\n## ", start + 1)
    return text[start:end if end > 0 else len(text)].strip()


# Part A's wording, for its axes coded again from the full text (Part B, section A): the
# rule of section A ("the paper" in place of "the title and abstract") applied to the text
# itself, since the models read the original words literally in the pilot of 20 October 2026.
# The last entry is section A's clause on `policy_role` (Part B, revised 21 October 2026, after
# the coders split on a policy that sets planning quantities beside a fixed dispatcher).
FULL_TEXT = [
    (r"from its title and abstract only", "from its full text"),
    (r"the\s+title\s+and\s+abstract\s+do\s+not\s+say", "the paper does not say"),
    (r"the\s+title\s+or\s+abstract", "the paper"),
    (r"title\s+and\s+abstract", "paper"),
    (r"Only what the record states", "Only what the paper states"),
    (r"\bthe(\s+)abstract\b", r"the\1paper"),
    (r"such\s+as\s+how\s+lots\s+are\s+split\s+into\s+sublots\.",
     "such as how lots are split into sublots, or the quantities to produce, release or order "
     "while a fixed rule or heuristic builds the schedule (such quantities are not scheduling "
     "decisions)."),
]
QUOTES_A = ("- **Quotes.** As section A's rules in Part B say: every answer is quoted, except a "
            "special answer and the codes its table marks as needing none.")


def full_text_reading(text):
    """Part A's text as section A reads it: "the paper" wherever it says "the title and
    abstract", "the abstract" or "the record", and its rule on quotes replaced by section
    A's."""
    for pattern, replacement in FULL_TEXT:
        text = re.sub(pattern, replacement, text)
    return re.sub(r"(?m)^- \*\*Quotes\.\*\*[^\n]*(?:\n  [^\n]*)*", lambda m: QUOTES_A, text)


def scheme_sections(sections=None):
    """The scheme as an agent reads it: Part B's general rules and its answers' form, then
    the sections named (all when None), each from Part B; section A's followed by Part A,
    whose rules its questions take. Part B's opening paragraph and coverage table are left
    out."""
    with open(SCHEME, encoding="utf-8") as fh:
        text = fh.read()
    part_b = part(text, "## Part B, the core")
    chunks = re.split(r"(?m)^(?=### )", part_b)[1:]
    named = {}
    for chunk in chunks:
        title = chunk.splitlines()[0][4:].strip()
        found = re.match(r"Section ([A-Z]):", title)
        named[found.group(1) if found else title] = chunk.strip()
    wanted = [s for s in named if len(s) == 1] if sections is None else list(sections)
    unknown = [s for s in wanted if s not in named]
    if unknown:
        raise ValueError("no section %s in Part B" % ", ".join(unknown))
    out = ["## The coding scheme", named["General rules"], named["Answers, evidence and blocks"]]
    for s in [s for s in named if len(s) == 1]:
        if s in wanted:
            out.append(named[s])
            if s == "A":
                part_a = part(text, "## Part A, the map").replace("## Part A, the map",
                                                                  "### Part A, the map", 1)
                out.append(full_text_reading(part_a))
    return "\n\n".join(out) + "\n"


def question_rules(spec, ids):
    """{ID: the scheme's rules for the question}: Part B's section of the question, from its
    `####` heading to the next heading; for a section A question, a line on reading it from
    the full text, Part A's general rules, and the axis's section of Part A. Raises
    ValueError for an ID that is not a question."""
    with open(SCHEME, encoding="utf-8") as fh:
        text = fh.read()
    part_a = full_text_reading(part(text, "## Part A, the map"))
    part_b = part(text, "## Part B, the core")
    intro = part_a.split("\n### ", 1)[0].split("\n", 1)[1].strip()
    out = {}
    for qid in ids:
        q = spec.questions.get(qid)
        if q is None:
            raise ValueError("no question %s" % qid)
        if q.section == "A":
            found = re.search(r"(?ms)^### `%s` .*?(?=^#{2,3} |\Z)" % re.escape(q.name), part_a)
            lead = ("Question %s is Part A's axis `%s`, coded from the paper's full text."
                    % (qid, q.name))
            rule = found and "%s\n\n%s\n\n%s" % (lead, intro, found.group(0).strip())
        else:
            found = re.search(r"(?ms)^#### %s `.*?(?=^#{2,4} |\Z)" % qid, part_b)
            rule = found and found.group(0).strip()
        if not rule:
            raise ValueError("no rules for %s in %s" % (qid, os.path.basename(SCHEME)))
        out[qid] = rule
    return out


def kept_blocks(texts):
    """{id: Block} for the blocks given ({id: text}) whose heading can be read."""
    out = {}
    for text in (texts or {}).values():
        block, _ = cb.parse_block(text)
        if block is not None:
            out[block.id] = block
    return out


def answer(request, paper_path):
    """The result of one --tool request; raises on a request that cannot be answered."""
    op = request.get("op")
    if op == "fingerprint":
        return {}
    if op == "files":
        return {"files": list(FILES)}
    spec = cb.load_spec(SPEC, MAP)
    if op == "questions":
        ids = cb.select(spec, request["select"]) if request.get("select") else list(spec.questions)
        return {"questions": [{"id": q, "name": spec.questions[q].name,
                               "section": spec.questions[q].section} for q in ids]}
    if op == "scheme":
        return {"text": scheme_sections(request.get("sections"))}
    if op == "assemble":
        return {"text": cb.assemble(spec, request.get("blocks") or {},
                                    request.get("header") or [])}
    if op == "rules":
        return {"rules": question_rules(spec, request.get("ids") or list(spec.questions))}
    if op == "blocks":
        _, blocks, problems = cb.split_response(request.get("response") or "")
        out = []
        for bid in cb.block_order(spec, blocks):
            block, _ = cb.parse_block(blocks[bid])
            pages = sorted({page for page, _ in block.evidence}) if block else []
            out.append({"id": bid, "question": bid.split(".")[0], "text": blocks[bid],
                        "pages": pages})
        return {"blocks": out, "problems": problems}
    if op not in PAPER_OPS:
        raise ValueError("unknown operation %r" % op)
    if not paper_path:
        raise ValueError("the operation %r needs --paper" % op)
    paper = fulltext.load(paper_path)
    if op == "outline":
        return {"headings": fulltext.outline(paper)}
    if op == "search":
        return fulltext.search(paper, request["pattern"])
    if op == "read":
        page = request.get("page")
        return fulltext.read(paper, None if page is None else int(page),
                             request.get("start_line"), request.get("end_line"))
    if op == "check_quote":
        return fulltext.check_quote(paper, int(request["page"]), request["quote"])
    if op == "check_block":
        block, problems = cb.check_block(spec, paper, request["block"],
                                         kept_blocks(request.get("blocks")))
        return {"id": block.id if block else None,
                "kept": block is not None and not cb.refused(problems), "problems": problems}
    if op == "check_response":
        scope = request.get("scope")
        if isinstance(scope, str):
            scope = cb.select(spec, scope)
        return {"problems": cb.check_response(spec, paper, request.get("blocks") or {}, scope)}
    if op == "excerpt":
        if request.get("body"):
            return {"text": fulltext.body_text(paper)}
        pages = request.get("pages") or []
        if pages == "all":
            pages = sorted(paper.markers)
        return {"pages": {str(int(p)): fulltext.page_text(paper, int(p)) for p in pages}}
    raise ValueError("unknown operation %r" % op)


def tool(paper_path):
    """Answers the request on stdin, on stdout."""
    try:
        request = json.loads(sys.stdin.read() or "{}")
        out = {"contract": CONTRACT, "fingerprint": fingerprint(), "ok": True,
               "result": answer(request, paper_path)}
    except Exception as e:  # every failure goes back to the caller, which decides
        out = {"contract": CONTRACT, "ok": False, "error": "%s: %s" % (type(e).__name__, e)}
    sys.stdout.write(json.dumps(out, ensure_ascii=True) + "\n")


def checksums(path):
    """{file (as "<n>/<n>.md"): SHA-256} from the markdown's checksums."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {r["file"].strip(): r["sha256"].strip() for r in csv.DictReader(fh)}


def responses(folder):
    """[(number, path)] of the response files in `folder`, by number."""
    found = []
    for name in os.listdir(folder):
        m = RESPONSE.match(name)
        if m:
            found.append((int(m.group(1)), os.path.join(folder, name)))
    return sorted(found)


def render(config, folder, studies, rows):
    lines = ["# The checks of the core's answers", "",
             "Written by `runners/core_check.py` from `%s`; do not edit, rerun the runner."
             % config, ""]
    if studies is None:
        return "\n".join(lines + ["No response folder yet (`%s`): nothing checked." % folder]) + "\n"
    clean = sum(1 for _, _, n in studies if n == 0)
    lines += ["%d responses checked against their papers: %d with no problem, %d with "
              "problems (%d in all). A problem names a study, a question and what is wrong, "
              "never the papers' words." % (len(studies), clean, len(studies) - clean,
                                            len(rows)), ""]
    from runners.core_selection import table
    lines += table([("Number", True), ("Blocks", True), ("Problems", True)],
                   [(n, blocks, k) for n, blocks, k in studies])
    return "\n".join(lines) + "\n"


def check_all(config_path, override=None):
    from runners.core_selection import file_sha, write_csv
    from runners.screening_consensus import load_config, rel, resolve
    cfg = load_config(config_path, override)
    inputs, outputs = cfg["inputs"], cfg["outputs"]
    spec = cb.load_spec(resolve(inputs["spec"]), resolve(inputs["map"]))
    folder = resolve(inputs["responses"])
    studies, rows = None, []
    if os.path.isdir(folder):
        sums = checksums(resolve(inputs["md_checksums"]))
        studies = []
        for number, path in responses(folder):
            key = "%d/%d.md" % (number, number)
            md = os.path.join(resolve(inputs["texts"]), key)
            if not os.path.isfile(md) or file_sha(md) != sums.get(key):
                raise SystemExit("%s is missing or differs from its checksum in %s."
                                 % (md, inputs["md_checksums"]))
            paper = fulltext.load(md)
            with open(path, encoding="utf-8") as fh:
                _, blocks, problems = cb.split_response(fh.read())
            problems += cb.check_response(spec, paper, blocks)
            studies.append((number, len(blocks), len(problems)))
            rows += [{"number": number, "id": p["id"], "what": p["what"]} for p in problems]
    write_csv(resolve(outputs["problems"]), FIELDS, rows)
    report = resolve(outputs["report"])
    with open(report, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(rel(config_path), inputs["responses"], studies, rows))
    if studies is None:
        print("responses         : none yet (%s)" % inputs["responses"])
    else:
        print("responses checked : %d" % len(studies))
        print("with problems     : %d (%d problems)" % (sum(1 for s in studies if s[2]), len(rows)))
    print("written           : %s, %s" % (rel(report), rel(resolve(outputs["problems"]))))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tool", action="store_true",
                        help="answer one request on stdin (the agent's tools)")
    parser.add_argument("--paper", default=None, help="the paper's markdown, with --tool")
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "core-check.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")
    args = parser.parse_args()
    if args.tool:
        tool(args.paper)
    else:
        check_all(args.config, args.override)


if __name__ == "__main__":
    main()
