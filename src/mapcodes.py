"""The map's rules: how the three models' codes on the axes of Part A become one code per
cell, and how their agreement is measured.

Protocol, Two tiers ("The map" and "The map's reliability"), and its amendment of
15 October 2026 ("the scheme's rules applied before the map's vote"). This module decides;
the runner (runners/map_vote.py) reads and writes. It was written on 15 October 2026, after
the models had coded the included records and before any vote or agreement was computed
from their codes:

    load_axes      the axes of configs/map.toml, in the schema's order
    read_codes     one model's codes, as the acquisition tool's coding task collects them
    IMPLICATIONS   the scheme's five rules that set one axis's code from another's
    imply          a record's codes made consistent with those rules
    LEVELS         the axes whose codes are levels (the readiness claim)
    vote           one cell's code from the models' codes
    combine        the whole procedure for every record: the rules, the vote, the rules again
    kappa          Cohen's kappa for two coders over nominal codes
    agreement      an axis's mean pairwise kappa, per code, the axis's agreement being the
                   mean over its categories at step 2 that the voted map holds (`counted`,
                   `held_codes`); a single axis's multiclass kappa beside it
    unanimous, no_majority
                   whether the models give one cell, and whether the vote finds no majority

A cell holds one code on a single axis, and a tuple of codes in the schema's order on a list
axis; `not-stated` is a code like any other here, alone on a list axis. The vote can give
`not-stated` on any axis, including the three whose models may not give it (hybridization,
domain, readiness_claim): the protocol codes every cell without a majority so.
"""

import csv
import itertools
import tomllib
from collections import Counter, namedtuple

NOT_STATED = "not-stated"
META = ("title", "venue", "year", "work_type")
# The codes that are not categories at step 2 of the core rule (protocol, Two tiers), and
# so are left out of an axis's agreement, though their kappas are reported.
NOT_CATEGORIES = (NOT_STATED, "other", "not-applicable")

Axis = namedtuple("Axis", "name codes multi alone")
Implication = namedtuple("Implication", "name when_axis when_codes then_axis then_code")

# The scheme's rules that set one axis's code from another's (datasets/coding-scheme.md,
# Part A: the sections of scheduling_action, learner_depth, deep_architecture and
# state_encoding). Each reads only policy_role or learner_depth, which no rule sets, so
# their order does not matter.
IMPLICATIONS = (
    Implication("steering role: no action", "policy_role",
                ("steering-rules", "steering-heuristic"), "scheduling_action", "not-applicable"),
    Implication("role not stated: action not stated", "policy_role", (NOT_STATED,),
                "scheduling_action", NOT_STATED),
    Implication("non-deep learner: no architecture", "learner_depth", ("tabular", "non-neural"),
                "deep_architecture", "not-applicable"),
    Implication("learner not stated: architecture not stated", "learner_depth", (NOT_STATED,),
                "deep_architecture", NOT_STATED),
    Implication("tabular learner: discrete states", "learner_depth", ("tabular",),
                "state_encoding", "discrete-states"),
)


# Axes whose codes are levels, in the schema's order from the lowest to the highest: the
# vote takes the highest level that more than half of the models reach (protocol amendment
# of 15 October 2026). The readiness claim's codes are the levels L1 to L5 of
# datasets/coding-scheme.md, so a record two models place beyond simulation, at different
# levels, keeps the lower of their two levels instead of becoming `not-stated`.
LEVELS = ("readiness_claim",)


def load_axes(path):
    """[Axis] from the schema (configs/map.toml), in its order."""
    with open(path, "rb") as fh:
        table = tomllib.load(fh)["axes"]
    return [Axis(name, tuple(spec["codes"]), bool(spec.get("multi", False)),
                 tuple(spec.get("alone", ()))) for name, spec in table.items()]


def show(value):
    """A cell as the files write it: a list axis's codes joined by '|'."""
    return "|".join(value) if isinstance(value, tuple) else value


def parse_cell(axis, text):
    """One cell of a coding file as (the cell, "") or (None, what is wrong)."""
    codes = [c.strip().lower() for c in (text or "").split("|")]
    if "" in codes:
        return None, "no code"
    if len(set(codes)) != len(codes):
        return None, "a code given twice"
    if NOT_STATED in codes:
        if len(codes) > 1:
            return None, "not-stated with other codes"
        return ((NOT_STATED,) if axis.multi else NOT_STATED), ""
    unknown = [c for c in codes if c not in axis.codes]
    if unknown:
        return None, "not a code of the axis: %s" % ", ".join(unknown)
    if not axis.multi:
        if len(codes) > 1:
            return None, "more than one code"
        return codes[0], ""
    if len(codes) > 1 and any(c in axis.alone for c in codes):
        return None, "a code that stands alone given with others"
    return tuple(c for c in axis.codes if c in codes), ""


def read_codes(path, axes):
    """One model's codes as ({number: {axis: cell}}, {number: {title, venue, year,
    work_type}}). Refuses a file without a column for every axis, a number given twice, and
    a cell that is not a valid code for its axis."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = [(f or "").strip() for f in (reader.fieldnames or [])]
        missing = [name for name in ["number"] + [a.name for a in axes] if name not in fields]
        if missing:
            raise SystemExit("%s has no column for: %s" % (path, ", ".join(missing)))
        codes, meta, bad = {}, {}, []
        for row in reader:
            row = {(k or "").strip(): v for k, v in row.items()}
            try:
                number = int((row.get("number") or "").strip())
            except ValueError:
                bad.append("a row without a number")
                continue
            if number in codes:
                bad.append("%d given twice" % number)
                continue
            cells = {}
            for axis in axes:
                cells[axis.name], problem = parse_cell(axis, row.get(axis.name))
                if problem:
                    bad.append("%d %s: %s" % (number, axis.name, problem))
            codes[number] = cells
            meta[number] = {k: (row.get(k) or "").strip() for k in META}
    if bad:
        raise SystemExit("%s: %s" % (path, "; ".join(bad)))
    return codes, meta


def imply(cells, axes):
    """(the cells made consistent with IMPLICATIONS, [(rule, axis, before, after)] for each
    cell a rule changed)."""
    multi = {a.name: a.multi for a in axes}
    out, changed = dict(cells), []
    for rule in IMPLICATIONS:
        if out[rule.when_axis] in rule.when_codes:
            value = (rule.then_code,) if multi[rule.then_axis] else rule.then_code
            if out[rule.then_axis] != value:
                changed.append((rule, rule.then_axis, out[rule.then_axis], value))
                out[rule.then_axis] = value
    return out, changed


def vote(axis, values):
    """One cell from the models' cells. On a single axis, the code more than half of them
    give, else `not-stated`; on an axis of LEVELS, the highest level more than half of them
    reach, `not-stated` ranking below every level. On a list axis, every code more than half
    of them give, in the schema's order, and `not-stated` when no code is. With three models,
    more than half is two: on an axis of levels, the middle of the three; and a code that
    stands alone stays alone, since two models giving it leave one model for any other
    code."""
    need = len(values) // 2 + 1
    if axis.name in LEVELS:
        rank = {c: i for i, c in enumerate(axis.codes)}
        reached = [c for c in axis.codes
                   if sum(rank.get(v, -1) >= rank[c] for v in values) >= need]
        return reached[-1] if reached else NOT_STATED
    if not axis.multi:
        code, count = Counter(values).most_common(1)[0]
        return code if count >= need else NOT_STATED
    counts = Counter(c for value in values for c in value)
    return tuple(c for c in axis.codes if counts[c] >= need) or (NOT_STATED,)


def combine(coded, axes, numbers):
    """The map for `numbers` from `coded` ({model: {number: cells}}): each model's cells made
    consistent with the rules, the vote cell by cell, and the rules applied again to the
    voted cells. Returns (the map {number: cells}, the models' cells after the rules
    {model: {number: cells}}, [(number, model or "vote", rule, axis, before, after)])."""
    implied, changes = {m: {} for m in coded}, []
    for model, codes in coded.items():
        for n in numbers:
            implied[model][n], changed = imply(codes[n], axes)
            changes += [(n, model) + c for c in changed]
    voted = {}
    for n in numbers:
        cells = {a.name: vote(a, [implied[m][n][a.name] for m in implied]) for a in axes}
        voted[n], changed = imply(cells, axes)
        changes += [(n, "vote") + c for c in changed]
    return voted, implied, changes


def kappa(pairs):
    """Cohen's kappa for two coders over nominal codes; `pairs` is [(code_a, code_b)]. None
    when there is nothing to compare or chance agreement is complete, which happens when
    both coders gave one and the same code throughout."""
    pairs = list(pairs)
    n = len(pairs)
    if n == 0:
        return None
    observed = sum(a == b for a, b in pairs) / n
    left = Counter(a for a, _ in pairs)
    right = Counter(b for _, b in pairs)
    chance = sum(left[c] * right[c] for c in left) / (n * n)
    if chance == 1:
        return None
    return (observed - chance) / (1 - chance)


def mean(values):
    """The mean of the values that are not None; None if none is."""
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def pair_kappas(implied, numbers, read):
    """{(model_a, model_b): kappa} over `numbers`, for every pair of models, comparing
    read(cells) of one with read(cells) of the other."""
    return {(a, b): kappa([(read(implied[a][n]), read(implied[b][n])) for n in numbers])
            for a, b in itertools.combinations(list(implied), 2)}


def has(axis, cell, code):
    """Whether a cell holds `code`."""
    return code in cell if axis.multi else cell == code


def held_codes(axis, voted, numbers):
    """The codes the voted map gives to at least one of `numbers` on the axis."""
    return {code for n in numbers
            for code in (voted[n][axis.name] if axis.multi else (voted[n][axis.name],))}


def counted(axis, held=None):
    """The codes whose kappas make an axis's agreement: its categories at step 2 of the core
    rule, every code but those of NOT_CATEGORIES, and of those, when `held` is given, only
    the codes the voted map gives to at least one record."""
    return [c for c in axis.codes if c not in NOT_CATEGORIES and (held is None or c in held)]


def agreement(axis, implied, numbers, held=None):
    """(the axis's kappa, {pair: kappa}, {code: (the code's kappa, {pair: kappa})}, the
    multiclass kappa). A kappa is the mean over the pairs of models for which one is
    defined; None where none is.

    Every code, `not-stated` among them, is compared as present or absent, on a single axis
    as on a list axis, and the axis's kappa is the mean of the kappas of `counted(axis,
    held)`, over those for which one is defined: the codes that are categories at step 2
    and that the voted map holds. The kappas of the other codes are reported and are not in
    that mean (protocol amendment of 15 October 2026). A pair's kappa on the axis is the
    mean of that pair's kappas over the same codes. The multiclass kappa compares a single
    axis's cells as given, over all its codes, `not-stated` among them; it is reported for
    reference, and is None on a list axis."""
    per_code = {}
    for code in axis.codes + (NOT_STATED,):
        pairs = pair_kappas(implied, numbers,
                            lambda cells, code=code: has(axis, cells[axis.name], code))
        per_code[code] = (mean(pairs.values()), pairs)
    codes = counted(axis, held)
    pairs = {p: mean(per_code[c][1][p] for c in codes)
             for p in itertools.combinations(list(implied), 2)}
    multiclass = None
    if not axis.multi:
        multiclass = mean(pair_kappas(implied, numbers, lambda cells: cells[axis.name]).values())
    return mean(per_code[c][0] for c in codes), pairs, per_code, multiclass


def unanimous(values):
    """Whether every model gives the same cell."""
    return len(set(values)) == 1


def no_majority(axis, values):
    """Whether the vote gives `not-stated` only because no code has a majority, rather than
    because most models gave `not-stated`."""
    blank = (NOT_STATED,) if axis.multi else NOT_STATED
    return vote(axis, values) == blank and values.count(blank) < len(values) // 2 + 1
