"""The core's answers (datasets/coding-scheme.md, Part B): the questions as their mirror
configs/core-coding.toml gives them, the block in which each is answered, and the checks code
makes of the blocks, for the coding agent as it writes them and over every response after.

Written on 20 October 2026, before any full text was coded. It runs on Python 3.11 or later
and reads nothing but its arguments.

    load_spec(spec_path, map_path)   the questions, the item groups, the rules between
                                     questions (Part A's implications among them) and the
                                     derived columns
    parse_block(text)                one block's heading and lines
    split_response(text)             a response's header and blocks
    check_block(spec, paper, text, kept)
                                     the problems of one block, given the blocks already kept
    refused(problems)                whether those problems refuse the block
    check_response(spec, paper, blocks, scope)
                                     the problems left in a response: questions unanswered,
                                     blocks that fail, items that do not match their count,
                                     the conditions and rules between questions
    select(spec, text)               the question IDs that text such as "C01 to C14, D02"
                                     names, in Part B's order
    assemble(spec, blocks, header)   a response, its blocks in Part B's order
    block_order(spec, ids)           block IDs in that order
    value(spec, block)               a block's answer as a cell
    derive(spec, values)             the derived columns

A cell is a code or a special answer (a string); a tuple of codes, in the order the question
lists them, for a list; a number, a text, a level or a score as a string; and an int or
"none" for a count. A problem is {"id", "what", "detail", "between"}: "what" never holds the
paper's text, so problems can be written to the published reports, while "detail" helps the
agent fix the block and may quote the paper. "between" marks a problem between questions (a
condition or a rule): when a block is written it is a warning, since the other answer may be
the wrong one, and the block is kept; every problem must be gone before the agent finishes.
"""

import re
import tomllib
from collections import namedtuple

from src import fulltext
from src import mapcodes

SPECIAL = ("not-stated", "not-applicable", "not-reported")
SEARCHED = ("not-stated", "not-reported")
SCORES = ("1", "0.5", "0", "not-assessable")
LEVELS = ("L1", "L2", "L3", "L4", "L5")
MAX_QUOTES = 3

Question = namedtuple("Question", "qid name section rq kind codes alone default special "
                      "conditions no_quote words group label")
Group = namedtuple("Group", "name parent max_items kind codes words fields unique label")
Rule = namedtuple("Rule", "name when when_codes then then_codes then_not")
Spec = namedtuple("Spec", "questions groups rules derived by_name")
# id: "D07", or "D07.2" for an item; qid: the question ("D07"); item: the item's number or
# None; name: the heading's name; answer, note: the lines' text; fields: {field: text};
# evidence: [(page, quote)].
Block = namedtuple("Block", "id qid item name answer fields evidence note")

HEAD = re.compile(r"^##\s+([A-Z]\d\d)(?:\.(\d+))?\s+([a-z_]+)\s*$")
LINE = re.compile(r"^([a-z_]+):(.*)$")
EVIDENCE = re.compile(r'^\{(\d+)\}\s*"(.*)"$')


# ---------------------------------------------------------------------------- the spec

def load_spec(spec_path, map_path):
    """The Spec: section A's questions completed from the map's axes; every other question,
    group, rule and derived column as configs/core-coding.toml gives it; Part A's five
    implications added to the rules."""
    with open(spec_path, "rb") as fh:
        table = tomllib.load(fh)
    with open(map_path, "rb") as fh:
        axes = tomllib.load(fh)["axes"]
    questions = {}
    for qid, q in table["questions"].items():
        if "axis" in q:
            a = axes[q["axis"]]
            questions[qid] = Question(
                qid, q["axis"], q["section"], q["rq"], "codes" if a.get("multi") else "code",
                tuple(a["codes"]), tuple(a.get("alone", ())), None,
                ("not-stated",) if a.get("not_stated", True) else (), (),
                tuple(q.get("no_quote", ())), None, None, a.get("label", q["axis"]))
        else:
            questions[qid] = Question(
                qid, q["name"], q["section"], q["rq"], q["type"], tuple(q.get("codes", ())),
                tuple(q.get("alone", ())), q.get("default"), tuple(q.get("special", ())),
                tuple(q.get("applies_when", ())), tuple(q.get("no_quote", ())),
                q.get("words"), q.get("group"), q.get("label", ""))
    groups = {}
    for name, g in table.get("groups", {}).items():
        groups[name] = Group(name, g["parent"], int(g["max_items"]), g["answer"],
                             tuple(g.get("codes", ())), g.get("words"),
                             {f: tuple(v["codes"]) for f, v in g.get("fields", {}).items()},
                             bool(g.get("unique", False)), g.get("label", ""))
    rules = [Rule(r["name"], r["if"], tuple(r["if_codes"]), r["then"],
                  tuple(r.get("then_codes", ())), tuple(r.get("then_not", ())))
             for r in table.get("rule", [])]
    rules += [Rule("Part A, " + i.name, i.when_axis, tuple(i.when_codes), i.then_axis,
                   (i.then_code,), ()) for i in mapcodes.IMPLICATIONS]
    by_name = {q.name: q for q in questions.values()}
    return Spec(questions, groups, rules, dict(table.get("derived", {})), by_name)


def most(spec, q):
    """A count's most items; None for any other question."""
    return spec.groups[q.group].max_items if q.kind == "count" else None


def select(spec, text):
    """The question IDs `text` names, in Part B's order: IDs, ranges such as "C01 to C14", or
    sections such as "C", separated by commas, semicolons or "and". Raises ValueError for
    anything else."""
    ids = list(spec.questions)
    chosen = set()
    for part in re.split(r",|;|\band\b", text or ""):
        part = re.sub(r"(?i)^section\s+", "", part.strip())
        if not part:
            continue
        span = re.fullmatch(r"([A-Z]\d\d)\s*(?:to|-)\s*([A-Z]\d\d)", part)
        if span:
            first, last = span.group(1), span.group(2)
            if first not in spec.questions or last not in spec.questions:
                raise ValueError("no such question in %r" % part)
            i, j = ids.index(first), ids.index(last)
            if j < i:
                raise ValueError("the range %r runs backwards" % part)
            chosen.update(ids[i:j + 1])
        elif part in spec.questions:
            chosen.add(part)
        elif re.fullmatch(r"[A-Z]", part) and any(q.startswith(part) for q in ids):
            chosen.update(q for q in ids if q.startswith(part))
        else:
            raise ValueError("not a question ID: %r" % part)
    if not chosen:
        raise ValueError("no question named")
    return [q for q in ids if q in chosen]


# --------------------------------------------------------------------------- the blocks

def parse_block(text):
    """(the Block, [(what, detail)]); the Block is None when its heading cannot be read."""
    lines = [line.strip() for line in (text or "").splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return None, [("the block is empty", "")]
    head = HEAD.match(lines[0])
    if not head:
        return None, [("the first line is not a heading such as '## B07 algorithm'",
                       lines[0][:80])]
    qid, item, name = head.group(1), head.group(2), head.group(3)
    bid = qid if item is None else "%s.%d" % (qid, int(item))
    answer, note, fields, evidence, problems = None, None, {}, [], []
    for line in lines[1:]:
        found = LINE.match(line)
        if not found:
            problems.append(("a line that is not 'answer:', 'evidence:', 'note:' or a field",
                             line[:80]))
            continue
        key, rest = found.group(1), found.group(2).strip()
        if key == "answer":
            if answer is not None:
                problems.append(("two answer lines", ""))
            else:
                answer = rest
        elif key == "note":
            if note is not None:
                problems.append(("two note lines", ""))
            else:
                note = rest
        elif key == "evidence":
            ev = EVIDENCE.match(rest)
            if ev:
                evidence.append((int(ev.group(1)), ev.group(2)))
            else:
                problems.append(('an evidence line not in the form evidence: {N} "quote"',
                                 rest[:80]))
        elif key in fields:
            problems.append(("two %s lines" % key, ""))
        else:
            fields[key] = rest
    if answer is None:
        problems.append(("no answer line", ""))
    return Block(bid, qid, int(item) if item else None, name, answer or "", fields,
                 evidence, note or ""), problems


def split_response(text):
    """(the header's lines, {id: block text}, [problems]): the blocks of a response, each
    from its heading to the next; a block given twice is reported and its first kept."""
    header, blocks, problems = [], {}, []
    current = None
    for line in (text or "").splitlines():
        if line.startswith("## "):
            head = HEAD.match(line.strip())
            if not head:
                problems.append(problem("?", "a heading that is not '## <ID> <name>'",
                                        line[:80]))
                current = None
                continue
            bid = head.group(1) + ("." + str(int(head.group(2))) if head.group(2) else "")
            if bid in blocks:
                problems.append(problem(bid, "a block given twice; the first is kept"))
                current = None
                continue
            blocks[bid] = [line]
            current = bid
        elif current is None:
            if not blocks:
                header.append(line)
        else:
            blocks[current].append(line)
    return header, {b: "\n".join(lines).strip() for b, lines in blocks.items()}, problems


def block_order(spec, ids):
    """The block IDs in Part B's order, each question followed by its items; IDs of no known
    question come last."""
    def item_key(bid):
        tail = bid.split(".", 1)[1]
        return int(tail) if tail.isdigit() else 0
    order = []
    for qid in spec.questions:
        if qid in ids:
            order.append(qid)
        order += sorted((b for b in ids if b.startswith(qid + ".")), key=item_key)
    return order + [b for b in ids if b not in order]


def assemble(spec, blocks, header=()):
    """A response: the header's lines, then the blocks ({id: text}) in Part B's order, each
    question followed by its items; blocks of no known question come last."""
    parts = ["\n".join(header).strip()] if header else []
    parts += [blocks[b].strip() for b in block_order(spec, blocks)]
    return "\n\n".join(p for p in parts if p) + "\n"


# ---------------------------------------------------------------------------- the values

def check_value(kind, text, codes=(), alone=(), special=(), words=None, most_items=None):
    """(the cell, [(what, detail)]) of an answer of this kind; the answer's own text goes in
    the detail only, since a wrong answer may hold the paper's words."""
    v = (text or "").strip()
    if not v:
        return None, [("no answer", "")]
    low = v.lower()
    if low in SPECIAL and low not in codes:
        if low in special:
            return low, []
        return None, [("%s is not an answer this question allows" % low, "")]
    if kind == "code":
        if low in codes:
            return low, []
        return None, [("the answer is not one of the question's codes", v[:80])]
    if kind == "codes":
        parts = [p.strip().lower() for p in v.split("|")]
        if "" in parts:
            return None, [("an empty code in the list", v[:80])]
        if len(set(parts)) != len(parts):
            return None, [("a code given twice", v[:80])]
        unknown = [p for p in parts if p not in codes]
        if unknown:
            if any(p in SPECIAL for p in unknown):
                return None, [("a special answer stands alone", v[:80])]
            return None, [("codes the question does not have", ", ".join(unknown)[:120])]
        lone = [p for p in parts if p in alone]
        if len(parts) > 1 and lone:
            return None, [("%s stands alone" % ", ".join(lone), "")]
        return tuple(c for c in codes if c in parts), []
    if kind == "number":
        if re.fullmatch(r"\d+(\.\d+)?", v):
            return v, []
        return None, [("not a number: give digits only", v[:80])]
    if kind == "text":
        n = len(v.split())
        if words and n > words:
            return None, [("%d words; at most %d" % (n, words), "")]
        return v, []
    if kind == "level":
        if v.upper() in LEVELS:
            return v.upper(), []
        return None, [("not a level: give one of L1 to L5", v[:80])]
    if kind == "score":
        if low in SCORES:
            return low, []
        return None, [("not a score: give 1, 0.5, 0 or not-assessable", v[:80])]
    if kind == "count":
        if low == "none":
            return "none", []
        if re.fullmatch(r"[1-9]\d*", v):
            n = int(v)
            if most_items and n > most_items:
                return None, [("%d items; at most %d" % (n, most_items), "")]
            return n, []
        return None, [("not a count: give the number of item blocks that follow, or none",
                       v[:80])]
    return None, [("a question of an unknown kind %s" % kind, "")]


def show(cell):
    if isinstance(cell, tuple):
        return "|".join(cell)
    return "" if cell is None else str(cell)


def is_special(q, cell):
    return isinstance(cell, str) and cell in SPECIAL and cell not in q.codes


def target(spec, block):
    """(the question, the group or None, [problems in words]) a block answers; the question
    is None when the block answers none."""
    q = spec.questions.get(block.qid)
    if block.item is None:
        if q is None:
            return None, None, ["no question %s" % block.qid]
        if block.name != q.name:
            return q, None, ["%s is %s, not %s" % (q.qid, q.name, block.name)]
        return q, None, []
    if q is None or q.kind != "count":
        return None, None, ["%s has no item blocks" % block.qid]
    g = spec.groups[q.group]
    problems = []
    if block.name != g.name:
        problems.append("the items of %s are %s, not %s" % (q.qid, g.name, block.name))
    if not 1 <= block.item <= g.max_items:
        problems.append("%s's items are numbered 1 to %d" % (q.qid, g.max_items))
    return q, g, problems


def value(spec, block):
    """A block's answer as a cell, or None when it is not valid."""
    q, g, problems = target(spec, block)
    if q is None or problems:
        return None
    if g is None:
        return check_value(q.kind, block.answer, q.codes, q.alone, q.special, q.words,
                           most(spec, q))[0]
    return check_value(g.kind, block.answer, g.codes, (), (), g.words)[0]


def cells(spec, kept):
    """{question name: cell} for the question blocks among `kept` ({id: Block}) whose answer
    is valid."""
    out = {}
    for b in kept.values():
        if b.item is None:
            cell = value(spec, b)
            if cell is not None:
                out[spec.questions[b.qid].name] = cell
    return out


def holds(cell, codes):
    if isinstance(cell, tuple):
        return any(c in codes for c in cell)
    return cell in codes


def condition(cond, values):
    """True or False; None when the question it names is unanswered or has a special
    answer."""
    cell = values.get(cond["question"])
    if cell is None or (isinstance(cell, str) and cell in SPECIAL):
        return None
    if "codes" in cond:
        return holds(cell, cond["codes"])
    if "min_codes" in cond:
        return len(cell if isinstance(cell, tuple) else (cell,)) >= cond["min_codes"]
    if "above" in cond:
        try:
            return float(cell) > float(cond["above"])
        except (TypeError, ValueError):
            return None
    return None


def applies(q, values):
    """True when the question applies, False when it does not, None when that cannot be
    told yet."""
    results = [condition(c, values) for c in q.conditions]
    if any(r is False for r in results):
        return False
    if any(r is None for r in results):
        return None
    return True


def why(q, values):
    return "; ".join("%s is %s" % (c["question"], show(values.get(c["question"])))
                     for c in q.conditions)


def broken_rules(spec, values, names=None):
    """[(the rule, what is wrong)] for the rules between questions that the answers in
    `values` break; with `names`, only the rules that touch one of them."""
    out = []
    for r in spec.rules:
        if names is not None and r.when not in names and r.then not in names:
            continue
        a, b = values.get(r.when), values.get(r.then)
        if a is None or b is None or not holds(a, r.when_codes):
            continue
        if (r.then_codes and not holds(b, r.then_codes)) or (r.then_not and holds(b, r.then_not)):
            wanted = ("one of %s" % ", ".join(r.then_codes) if r.then_codes
                      else "none of %s" % ", ".join(r.then_not))
            out.append((r, "the rule '%s' is not met: %s is %s, so %s should hold %s, not %s"
                        % (r.name, r.when, show(a), r.then, wanted, show(b))))
    return out


# ---------------------------------------------------------------------------- the checks

def problem(bid, what, detail="", between=False):
    return {"id": bid, "what": what, "detail": detail, "between": between}


def quote_problems(paper, bid, evidence):
    out = []
    if len(evidence) > MAX_QUOTES:
        out.append(problem(bid, "%d evidence lines; at most %d" % (len(evidence), MAX_QUOTES)))
    for k, (page, quote) in enumerate(evidence, 1):
        if not fulltext.normalize(quote):
            out.append(problem(bid, "quote %d is empty" % k))
            continue
        r = fulltext.check_quote(paper, page, quote)
        if r["words"] > fulltext.QUOTE_WORDS:
            out.append(problem(bid, "quote %d has %d words; at most %d"
                               % (k, r["words"], fulltext.QUOTE_WORDS)))
        if r["found"]:
            continue
        if page not in paper.markers:
            out.append(problem(bid, "quote %d cites page %d, which the paper does not have"
                               % (k, page)))
        elif r["pages"]:
            out.append(problem(bid, "quote %d is not on page %d but on page %s"
                               % (k, page, ", ".join(map(str, r["pages"])))))
        elif r["across"]:
            out.append(problem(bid, "quote %d runs across the page marker after page %d: "
                                    "quote only the part on one page" % (k, page)))
        else:
            detail = ('the closest passage on page %d: "%s"' % (page, r["closest"])
                      if r["closest"] else "no passage of that page comes close")
            out.append(problem(bid, "quote %d is not on page %d word for word" % (k, page),
                               detail))
    return out


def check_block(spec, paper, text, kept=None):
    """(the Block or None, [problems]) of one block: its form, its answer, its fields, its
    quotes against the paper, its note, and, given the blocks already kept ({id: Block}),
    the conditions and rules it takes part in."""
    block, parsed = parse_block(text)
    if block is None:
        return None, [problem("?", what, detail) for what, detail in parsed]
    out = [problem(block.id, what, detail) for what, detail in parsed]
    q, g, wrong = target(spec, block)
    out += [problem(block.id, w) for w in wrong]
    if q is None:
        return block, out
    if g is None:
        cell, wrong = check_value(q.kind, block.answer, q.codes, q.alone, q.special, q.words,
                                  most(spec, q))
        if block.fields:
            out.append(problem(block.id, "fields belong only to item blocks: %s"
                               % ", ".join(sorted(block.fields))))
        special = is_special(q, cell)
        quoted = not (cell is None or special or cell == "none" and q.kind == "count"
                      or q.no_quote and all(c in q.no_quote for c in
                                            (cell if isinstance(cell, tuple) else (cell,))))
        kind = q.kind
    else:
        cell, wrong = check_value(g.kind, block.answer, g.codes, (), (), g.words)
        for field, codes in g.fields.items():
            given = block.fields.get(field)
            if given is None:
                out.append(problem(block.id, "no %s line" % field))
            elif given.strip().lower() not in codes:
                out.append(problem(block.id, "the %s is not one of %s"
                                   % (field, ", ".join(codes)), given[:80]))
        extra = sorted(set(block.fields) - set(g.fields))
        if extra:
            out.append(problem(block.id, "fields that %s does not have: %s"
                               % (g.name, ", ".join(extra))))
        special, quoted, kind = False, cell is not None, g.kind
    out += [problem(block.id, what, detail) for what, detail in wrong]
    if quoted and not block.evidence:
        out.append(problem(block.id, "no evidence line: quote the paper, one to three quotes"))
    out += quote_problems(paper, block.id, block.evidence)
    if special and cell in SEARCHED and not block.note.lower().startswith("searched"):
        out.append(problem(block.id, "a %s answer needs a note that begins 'searched' and "
                                     "lists what was searched" % cell))
    if special and cell == "not-applicable" and not block.note:
        out.append(problem(block.id, "a not-applicable answer needs a note that says why"))
    if kind == "text" and cell is not None and not special:
        run = fulltext.shared_run(cell, paper)
        if run:
            out.append(problem(block.id, "the answer copies %d or more words of the paper in "
                                         "a row: write it in your own words"
                               % fulltext.RUN, "the words copied: %s" % run))
    if g is None and cell is not None:
        values = cells(spec, kept or {})
        values[q.name] = cell
        if q.conditions:
            fits = applies(q, values)
            if fits is False and cell != "not-applicable":
                out.append(problem(block.id, "the question does not apply here (%s): answer "
                                             "not-applicable" % why(q, values), between=True))
            if fits is True and cell == "not-applicable":
                out.append(problem(block.id, "the question applies here (%s): answer it"
                                   % why(q, values), between=True))
        out += [problem(spec.by_name[r.then].qid, w, between=True)
                for r, w in broken_rules(spec, values, {q.name})]
    return block, out


def refused(problems):
    """Whether a block with these problems is refused: any problem of its own, as against a
    problem between questions."""
    return any(not p["between"] for p in problems)


def check_response(spec, paper, blocks, scope=None):
    """[problems] of a response's blocks ({id: text}) for the questions in `scope` (their
    IDs; all of Part B's by default) and their items: every question answered, every block
    passing, every count matched by its items, and the rules between questions."""
    wanted = list(spec.questions) if scope is None else [q for q in spec.questions
                                                         if q in set(scope)]
    kept = {}
    for text in blocks.values():
        b, _ = parse_block(text)
        if b is not None:
            kept[b.id] = b
    out = [problem(qid, "no answer yet") for qid in wanted if qid not in kept]
    for bid, text in blocks.items():
        b = kept.get(bid)
        if b is not None and b.qid in wanted:
            out += check_block(spec, paper, text, kept)[1]
        elif b is None and bid.split(".")[0] in wanted:
            out += check_block(spec, paper, text, kept)[1]
    values = cells(spec, kept)
    for qid in wanted:
        q = spec.questions[qid]
        if q.kind != "count" or qid not in kept:
            continue
        g = spec.groups[q.group]
        items = sorted(b.item for b in kept.values() if b.qid == qid and b.item is not None)
        n = values.get(q.name)
        expected = list(range(1, n + 1)) if isinstance(n, int) else []
        missing = [i for i in expected if i not in items]
        extra = [i for i in items if i not in expected]
        if missing:
            out.append(problem(qid, "item blocks missing for the count %s: %s"
                               % (show(n), ", ".join("%s.%d" % (qid, i) for i in missing))))
        if extra:
            out.append(problem(qid, "item blocks beyond the count %s: %s"
                               % (show(n), ", ".join("%s.%d" % (qid, i) for i in extra))))
        if g.unique:
            answers = [kept["%s.%d" % (qid, i)].answer.strip().lower() for i in items]
            twice = sorted({a for a in answers if answers.count(a) > 1})
            if twice:
                out.append(problem(qid, "an item answer given twice: %s" % ", ".join(twice)))
    names = {spec.questions[qid].name for qid in wanted}
    for rule, what in broken_rules(spec, values, names):
        out.append(problem(spec.by_name[rule.then].qid, what, between=True))
    seen, unique = set(), []
    for p in out:
        key = (p["id"], p["what"])
        if key not in seen:
            seen.add(key)
            unique.append(p)
    order = {qid: i for i, qid in enumerate(spec.questions)}
    unique.sort(key=lambda p: (order.get(p["id"].split(".")[0], len(order)), p["id"]))
    return unique


# ------------------------------------------------------------------- the derived columns

def derive(spec, values):
    """{derived column: value} from the answers' cells ({question name: cell})."""
    out = {}
    for name, d in spec.derived.items():
        cell = values.get(d["from"])
        if cell is None:
            out[name] = None
        elif isinstance(cell, str) and cell in SPECIAL:
            out[name] = cell
        elif "map" in d:
            out[name] = d["map"].get(cell)
        else:
            n = len(cell if isinstance(cell, tuple) else (cell,))
            out[name] = "yes" if n >= d["min_codes"] else "no"
    return out
