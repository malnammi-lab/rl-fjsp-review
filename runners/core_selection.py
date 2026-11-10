"""Select the core, the studies read in full, by the core rule (protocol, Two tiers).

Step 1 takes the studies whose claim of use beyond simulation a person confirmed at a
[step1] level. Step 2 fills each coverage category's minimum. Step 3 fills each stratum's
places by venue band, year and citations. The cap on non-deep studies binds at every step.
The docstrings of select() and its helpers give the rule's readings. Reads datasets/map.csv,
references.json, venue-bands.csv and core-claims.csv, and results/map/map-agreement.csv.
Writes datasets/core.csv and results/core/core-selection.md, core-flow.csv, core-vs-map.csv
and core-lock.json. A later run with another core is refused.

Run: python runners/run_all.py --only core-selection
"""

import argparse
import csv
import hashlib
import itertools
import json
import os
import sys
from collections import Counter, defaultdict, namedtuple
from fractions import Fraction

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus  # noqa: E402
from src import mapcodes as mc  # noqa: E402
from src.duplicates import norm, same_first_author  # noqa: E402
from runners.core_claims import AXIS as READINESS  # noqa: E402
from runners.core_claims import read_confirmations, step1_places  # noqa: E402
from runners.screening_consensus import load_config, rel, resolve  # noqa: E402

# One candidate: its stratum, whether its learner is deep, its venue band ("1" or "2") and
# tier (1 the best), its year (None when missing), its citations, and the categories of step 2
# it holds, as (axis, code) pairs.
Cand = namedtuple("Cand", "number stratum deep band tier year cites cats")
# How step 3 took a study: in its year's share of the band where its stratum's last place
# fell, as part of a band taken whole, or in place of a non-deep study past the cap.
YEAR_SHARE, BAND_WHOLE, IN_PLACE = "year share", "band taken whole", "in place of"
CORE_FIELDS = ["number", "step", "stratum", "policy_role", "learner_depth", "band", "tier",
               "year", "cited_by_count", "standing", "filled_at_step2", "taken", "title",
               "venue", "doi"]
FLOW_FIELDS = ["key", "label", "count"]
COMPARE_FIELDS = ["axis", "code", "map", "core", "rest", "core_share", "rest_share"]
NOT_IN_SJR = "not in SJR"


def largest_remainders(total, weights, order):
    """{key: places}: `total` places divided among the keys of `weights` in proportion to
    their weights, each key taking the whole part of its exact share and the places left going
    one each to the largest remainders; equal remainders go to the larger weight, then to the
    key that comes first in `order`."""
    whole = sum(weights.values())
    if total <= 0 or whole <= 0:
        return {k: 0 for k in weights}
    exact = {k: Fraction(total * w, whole) for k, w in weights.items()}
    out = {k: int(v) for k, v in exact.items()}
    ranked = sorted(weights, key=lambda k: (-(exact[k] - out[k]), -weights[k], order.index(k)))
    for k in ranked[:total - sum(out.values())]:
        out[k] += 1
    return out


def allocate(total, places, chosen, available, order):
    """{stratum: its places in the core, the studies of steps 1 and 2 among them}. `total` is
    divided in proportion to `places`; a stratum over its share keeps its `chosen` studies and
    takes no more, and one whose `available` candidates cannot fill its share takes them all;
    the places left are divided again among the other strata in proportion to their places,
    until none is over or short. Strata over their share are settled before any that is
    short, so that they never take the places another cannot fill."""
    final, active = {}, list(order)
    while active:
        rest = total - sum(final.values())
        quota = largest_remainders(rest, {s: places[s] for s in active}, order)
        over = [s for s in active if chosen[s] > quota[s]]
        if over:
            for s in over:
                final[s] = chosen[s]
                active.remove(s)
            continue
        short = [s for s in active if chosen[s] + available[s] < quota[s]]
        if not short:
            final.update(quota)
            break
        for s in short:
            final[s] = chosen[s] + available[s]
            active.remove(s)
    return {s: final[s] for s in order}


def duplicates(numbers, records, title_needs_first_author=True):
    """([(the record kept, [the records counted with it])], [(a, b) sharing a normalized
    title but kept apart, their first authors not agreeing]). Records are one study when they
    share a DOI or an OpenAlex work, or a normalized title, then only if their first authors
    agree when `title_needs_first_author`; groups join through any shared key. The journal
    version is kept over any other, then the later year, then the lower record number."""
    parent = {n: n for n in numbers}

    def root(n):
        while parent[n] != n:
            n = parent[n]
        return n

    keys = defaultdict(list)
    for n in numbers:
        r = records[n]
        if r.doi:
            keys["doi " + r.doi.lower()].append(n)
        if r.short_id:
            keys["openalex " + r.short_id].append(n)
        if norm(r.title):
            keys["title " + norm(r.title)].append(n)
    apart = []
    for key, ns in sorted(keys.items()):
        for a, b in itertools.combinations(sorted(ns), 2):
            if key.startswith("title ") and title_needs_first_author and \
                    same_first_author(records[a].first_author, records[b].first_author) is not True:
                if root(a) != root(b):
                    apart.append((a, b))
                continue
            ra, rb = root(a), root(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    groups = defaultdict(list)
    for n in numbers:
        groups[root(n)].append(n)
    out = []
    for ns in groups.values():
        if len(ns) > 1:
            kept = min(ns, key=lambda n: (records[n].source_type != "journal",
                                          -(records[n].year or 0), n))
            out.append((kept, sorted(n for n in ns if n != kept)))
    joined = {n for kept, others in out for n in [kept] + others}
    apart = [(a, b) for a, b in apart if not (a in joined and b in joined and root(a) == root(b))]
    return sorted(out), sorted(set(apart))


def candidates(the_map, records, title_needs_first_author=True):
    """(the map's records whose learner is stated, [(the record kept, [the records counted
    with it])], [(a, b) sharing a title but kept apart], the candidates: the first list less
    the records counted with another). The statistics runner reads the candidates here too, so
    that they are defined once."""
    numbers = sorted(n for n, cells in the_map.items() if cells["learner_depth"] != mc.NOT_STATED)
    groups, apart = duplicates(numbers, records, title_needs_first_author)
    others = {n for _, o in groups for n in o}
    return numbers, groups, apart, [n for n in numbers if n not in others]


def standings(cands):
    """{number: the share of the candidates of its year cited more, as a Fraction (the lower,
    the better)}; the candidates without a year are a year of their own."""
    by_year = defaultdict(list)
    for c in cands.values():
        by_year[c.year].append(c.cites)
    return {n: Fraction(sum(1 for x in by_year[c.year] if x > c.cites), len(by_year[c.year]))
            for n, c in cands.items()}


def tie_key(c, standing):
    """The protocol's order of ties: the better venue, then the better standing, then the
    lower record number."""
    return (c.tier, standing[c.number], c.number)


def most_cited(c, standing):
    """A year's order at step 3: the most cited first, then the order of ties."""
    return (-c.cites,) + tie_key(c, standing)


def coverage(cands, chosen, categories, minimum, cap, standing):
    """Step 2: ([(number, the places it filled)] in the order taken, {category: the places it
    is owed}). A category is owed `minimum` studies, or as many as the candidates holding it;
    the studies `chosen` at step 1 count. The candidate filling the most places still owed is
    added, ties by tie_key, until none fills any; a non-deep candidate is passed over once
    `cap` non-deep studies are in."""
    holders = Counter(k for c in cands.values() for k in c.cats)
    owed = {k: min(minimum, holders[k]) for k in categories}
    filled = Counter(k for n in chosen for k in cands[n].cats)
    non_deep = sum(1 for n in chosen if not cands[n].deep)
    taken, picks = set(chosen), []
    while True:
        short = {k for k in categories if filled[k] < owed[k]}
        best = None
        for n, c in cands.items():
            if n in taken or (not c.deep and non_deep >= cap):
                continue
            gain = len(c.cats & short)
            if gain and (best is None or (-gain,) + tie_key(c, standing) < best[0]):
                best = ((-gain,) + tie_key(c, standing), n, gain)
        if best is None:
            return picks, owed
        _, n, gain = best
        picks.append((n, gain))
        taken.add(n)
        filled.update(cands[n].cats)
        non_deep += not cands[n].deep


def year_order(years):
    """Years from the earliest, a missing year last."""
    return sorted(years, key=lambda y: (y is None, y or 0))


def fill(cands, pool, places, standing):
    """Step 3 in one stratum: ([(number, band, year, how)], the band where the last place
    fell or None for no place, {year: (the band's candidates, places)} where that band was
    shared among years). `pool` holds the stratum's candidates not yet chosen. Band 1 is taken
    before band 2; a band with no more candidates than the places left is taken whole, and in
    the band where the last place falls the places are shared among the years in proportion
    to its candidates in each, each year's going to its most cited."""
    picks, left, shares, fell = [], places, {}, None
    for band in ("1", "2"):
        if left <= 0:
            break
        ns = [n for n in pool if cands[n].band == band]
        if len(ns) <= left:
            picks += [(n, band, cands[n].year, BAND_WHOLE)
                      for n in sorted(ns, key=lambda n: most_cited(cands[n], standing))]
            left -= len(ns)
            fell = band if ns else fell
            continue
        by_year = defaultdict(list)
        for n in ns:
            by_year[cands[n].year].append(n)
        order = year_order(by_year)
        quota = largest_remainders(left, {y: len(by_year[y]) for y in order}, order)
        for y in order:
            ranked = sorted(by_year[y], key=lambda n: most_cited(cands[n], standing))
            picks += [(n, band, y, YEAR_SHARE) for n in ranked[:quota[y]]]
            shares[y] = (len(by_year[y]), quota[y])
        fell, left = band, 0
    return picks, fell, shares


def cap_step3(cands, picks, budget, taken, standing):
    """(the picks of step 3 within the cap, [(the non-deep study left out, the deep study in
    its place)]). When the picks hold more non-deep studies than `budget`, those with the
    best standing are kept (ties: the better venue, then the lower record number), and each
    of the others, in the same order, gives its place to the next deep candidate of its
    stratum, band and year not yet `taken`; if that year has none, to the stratum's deep
    candidate with the best standing, band 1 first."""
    non_deep = [p for p in picks if not cands[p[0]].deep]
    if len(non_deep) <= budget:
        return picks, []
    order = sorted(non_deep, key=lambda p: (standing[p[0]], cands[p[0]].tier, p[0]))
    taken = set(taken) | {p[0] for p in picks}
    out, swaps = list(picks), []
    for n, band, year, _ in order[budget:]:
        free = [m for m, c in cands.items()
                if m not in taken and c.deep and c.stratum == cands[n].stratum]
        same = [m for m in free if cands[m].band == band and cands[m].year == year]
        if same:
            m = min(same, key=lambda m: most_cited(cands[m], standing))
        elif free:
            m = min(free, key=lambda m: (cands[m].band, standing[m], cands[m].tier, m))
        else:
            raise SystemExit("No deep candidate of stratum %s is left to take the place of "
                             "record %d, a non-deep study past the cap." % (cands[n].stratum, n))
        i = next(i for i, p in enumerate(out) if p[0] == n)
        out[i] = (m, cands[m].band, cands[m].year, "%s %d" % (IN_PLACE, n))
        taken.add(m)
        swaps.append((n, m))
    return out, swaps


Selection = namedtuple("Selection", "step1 left_out step2 minimum owed allocation chosen_by "
                                    "step3 fell shares swaps budget standing")


def select(cands, confirmed, categories, size, cap, minimums, places, order):
    """The core rule over `cands` ({number: Cand}): step 1 from the numbers `confirmed` there,
    step 2 over `categories`, step 3 by `places` per stratum, in `order`; the cap binds at
    every step. Returns a Selection."""
    standing = standings(cands)
    step1 = sorted(confirmed, key=lambda n: tie_key(cands[n], standing))
    left_out = [n for n in step1 if not cands[n].deep][cap:]
    step1 = [n for n in step1 if n not in left_out]
    if len(step1) > size:
        raise SystemExit("Step 1 alone takes %d studies, more than the core's %d places; the "
                         "protocol's rule for that case is not implemented." % (len(step1), size))
    for minimum in minimums:
        step2, owed = coverage(cands, step1, categories, minimum, cap, standing)
        if len(step1) + len(step2) <= size:
            break
    else:
        raise SystemExit("Steps 1 and 2 need more than the core's %d places even at a minimum "
                         "of %d." % (size, minimums[-1]))
    chosen = step1 + [n for n, _ in step2]
    budget = cap - sum(1 for n in chosen if not cands[n].deep)
    pools = {s: [n for n, c in cands.items() if c.stratum == s and n not in chosen]
             for s in order}
    chosen_by = Counter(cands[n].stratum for n in chosen)
    available = {s: sum(1 for n in pools[s] if cands[n].deep)
                 + min(budget, sum(1 for n in pools[s] if not cands[n].deep)) for s in order}
    allocation = allocate(size, places, chosen_by, available, order)
    step3, fell, shares = [], {}, {}
    for s in order:
        picks, fell[s], shares[s] = fill(cands, pools[s], allocation[s] - chosen_by[s], standing)
        step3 += picks
    step3, swaps = cap_step3(cands, step3, budget, chosen, standing)
    return Selection(step1, left_out, step2, minimum, owed, allocation, chosen_by, step3, fell,
                     shares, swaps, budget, standing)


def core_rows(sel):
    """[(number, step)] of the core, in the order taken."""
    return ([(n, "1") for n in sel.step1] + [(n, "2") for n, _ in sel.step2]
            + [(p[0], "3") for p in sel.step3])


def reverse_core(cands, confirmed, categories, size, cap, minimums, places, order):
    """(the core the rule selects with every record number mirrored, the highest first, as
    [(number, step)] with the numbers mapped back, or None; the message if that selection
    stops). Every tie the lower record number broke goes the other way, and nothing else
    changes, since no other part of select() reads a record number; the difference between
    the two cores is what the record number decided."""
    top = max(cands) + 1
    flipped = {top - n: c._replace(number=top - n) for n, c in cands.items()}
    try:
        sel = select(flipped, [top - n for n in confirmed], categories, size, cap, minimums,
                     places, order)
    except SystemExit as exc:
        return None, str(exc)
    return [(top - n, step) for n, step in core_rows(sel)], ""


def number_ties(cands, rows, reverse, standing, how=None):
    """([(number, step, [tied with it, in the core], [tied with it, left out])] for the core's
    studies the mirrored order leaves out, [(number, step)] of the mirrored order's studies not
    in the core). Tied: of the same stratum, band and year, with as many citations, the same
    tier and the same standing; for a study step 3 took in place of a non-deep one past the
    cap (`how`, as cap_step3 marks it), deep candidates only, since only they could take it."""
    core, other, how = dict(rows), dict(reverse), how or {}

    def tied(n):
        c = cands[n]
        same = [m for m, d in cands.items()
                if m != n and standing[m] == standing[n]
                and (d.stratum, d.band, d.year, d.cites, d.tier)
                == (c.stratum, c.band, c.year, c.cites, c.tier)
                and (d.deep or not how.get(n, "").startswith(IN_PLACE))]
        return sorted(m for m in same if m in core), sorted(m for m in same if m not in core)

    return ([(n, step) + tied(n) for n, step in rows if n not in other],
            [(n, step) for n, step in reverse if n not in core])


def core_digest(rows):
    """SHA-256 of the core's records and their steps, by record number."""
    text = "\n".join("%d|%s" % (n, step) for n, step in sorted(rows))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def check_lock(path, rows):
    """True when the lock holds this core, False when there is no lock; refuses a core that
    differs from the locked one."""
    if not os.path.isfile(path):
        return False
    with open(path, encoding="utf-8") as fh:
        held = json.load(fh)
    if held.get("core_sha256") == core_digest(rows):
        return True
    before = {int(n): step for n, step in held.get("core", [])}
    now = dict(rows)
    gone = sorted(n for n in before if n not in now)
    new = sorted(n for n in now if n not in before)
    moved = sorted(n for n in now if n in before and before[n] != now[n])
    raise SystemExit("The core differs from the one locked in %s (left: %s; new: %s; another "
                     "step: %s). A change once the core is made needs a dated amendment to the "
                     "protocol; restore the inputs, or record the amendment and then remove "
                     "the lock." % (path, ", ".join(map(str, gone)) or "none",
                                    ", ".join(map(str, new)) or "none",
                                    ", ".join(map(str, moved)) or "none"))


def coverage_axes(path, axes):
    """The axes the map's agreement lets steer step 2, in the schema's order: the rows of the
    agreement file with no code and `coverage` yes."""
    if not os.path.isfile(path):
        raise SystemExit("%s not found: the map's agreement, written by runners/map_vote.py."
                         % path)
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    steer = {(r.get("axis") or "").strip() for r in rows
             if not (r.get("code") or "").strip() and (r.get("coverage") or "").strip() == "yes"}
    unknown = sorted(steer - {a.name for a in axes})
    if unknown:
        raise SystemExit("%s names axes the schema lacks: %s" % (path, ", ".join(unknown)))
    if READINESS in steer:
        raise SystemExit("%s lets `%s` steer step 2, which it never does." % (path, READINESS))
    return [a for a in axes if a.name in steer]


def codes_of(axis, cell):
    return cell if axis.multi else (cell,)


def read_bands(path, numbers):
    """{number: (band, tier, country)} from the venue bands; refuses a record of the map the
    file lacks, and one whose band waits for a person's answer."""
    if not os.path.isfile(path):
        raise SystemExit("%s not found: the venue bands, written by runners/venue_bands.py."
                         % path)
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not {"number", "band", "tier"} <= set(reader.fieldnames or []):
            raise SystemExit("%s has no band and tier columns: run runners/venue_bands.py "
                             "again." % path)
        rows = {int(r["number"]): r for r in reader if (r.get("number") or "").strip()}
    absent = [n for n in numbers if n not in rows]
    pending = [n for n in numbers if n in rows and not (rows[n]["band"] and rows[n]["tier"])]
    if absent or pending:
        raise SystemExit("%s: records of the map without a band (%s) or waiting for an answer "
                         "on their ICORE match (%s); run runners/venue_bands.py and answer its "
                         "sheet." % (path, ", ".join(map(str, absent)) or "none",
                                     ", ".join(map(str, pending)) or "none"))
    return {n: (rows[n]["band"], int(rows[n]["tier"]), (rows[n].get("sjr_country") or "").strip())
            for n in numbers}


def write_csv(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for row in rows:
                w.writerow(row)
    except PermissionError:
        raise SystemExit("%s is open in another program (Excel locks it): close it and run "
                         "again." % path)


def pct(part, whole):
    return "%.1f" % (100.0 * part / whole) if whole else ""


def comparison(axes, the_map, core, bands):
    """[row] of COMPARE_FIELDS: each code of every axis, each venue tier and each venue
    country, counted in the map, in the core and in the rest of the map."""
    rest = [n for n in the_map if n not in core]
    rows = []

    def add(axis, code, holds):
        m = sum(1 for n in the_map if holds(n))
        c = sum(1 for n in core if holds(n))
        rows.append({"axis": axis, "code": code, "map": m, "core": c, "rest": m - c,
                     "core_share": pct(c, len(core)), "rest_share": pct(m - c, len(rest))})

    for axis in axes:
        for code in axis.codes + (mc.NOT_STATED,):
            add(axis.name, code, lambda n, a=axis, k=code: k in codes_of(a, the_map[n][a.name]))
    for tier in sorted({t for _, t, _ in bands.values()}):
        add("venue_tier", str(tier), lambda n, t=tier: bands[n][1] == t)
    countries = Counter(bands[n][2] or NOT_IN_SJR for n in the_map)
    for country in sorted(countries, key=lambda c: (c == NOT_IN_SJR, -countries[c], c)):
        add("venue_country", country, lambda n, k=country: (bands[n][2] or NOT_IN_SJR) == k)
    return rows


def table(head, rows):
    """A markdown table: `head` [(title, right-aligned)] and `rows` of cells."""
    lines = ["| %s |" % " | ".join(h for h, _ in head),
             "| %s |" % " | ".join("---:" if right else "---" for _, right in head)]
    return lines + ["| %s |" % " | ".join(str(x) for x in row) for row in rows]


def tie_cell(tied_in, tied_out):
    """The ties table's last cell: the tied candidates in the core and those left out."""
    if not tied_in and not tied_out:
        return "none"
    return "in the core: %s; left out: %s" % (", ".join(map(str, tied_in)) or "none",
                                               ", ".join(map(str, tied_out)) or "none")


def render_ties(ties, stopped, cands, size):
    """The report's section on the ties the lower record number settled."""
    lines = ["", "## Ties settled by the record number", "",
             "Ties at steps 2 and 3 go to the better venue, then the better citation standing, "
             "then the lower record number (protocol, Two tiers). The record number is the order "
             "in which OpenAlex returned the works to the search, which asked for no sort; it "
             "says nothing of a study's method. Band 1 is a single venue tier, and within a year "
             "equal citations give equal standing, so within a year of band 1 a tie on citations "
             "falls to the record number. To count where it decided, the rule's steps were "
             "applied again with every record number mirrored, the highest first, which turns "
             "each such tie inside them the other way and changes nothing else (the de-duplication "
             "of the candidates, which also prefers the lower number, is not mirrored; its groups "
             "are listed under Candidates). The count is of the places that change when the order "
             "is reversed: in a tie of k candidates for j places, the record number decides the "
             "lesser of j and k - j."]
    if ties is None:
        return lines + ["", "The mirrored selection stopped: %s" % stopped]
    out, instead = ties
    steps = Counter(step for _, step, _, _ in out)
    lines += ["", "Reversing the order changes %d of the core's %d studies (step 1: %d, step 2: "
              "%d, step 3: %d); the mirrored core takes as many others in their place." % (
                  len(out), size, steps["1"], steps["2"], steps["3"]),
              "", "A difference can also follow from an earlier tie rather than be one: a "
              "different study taken at step 2 changes the categories still owed and the places "
              "left to each stratum. For a study of step 3 the last column gives the tie it was "
              "part of, the candidates sharing its stratum, band, year, citations, tier and "
              "standing, in the core and left out (deep ones only where it took a place the cap "
              "freed); one with none differs for that earlier reason. A study of step 2 is taken "
              "for the places it fills, so its partners in a tie are the candidates that would "
              "have filled as many, which this table does not list."]
    if out:
        lines += [""] + table(
            [("Record", True), ("Step", False), ("Stratum", False), ("Band", False),
             ("Year", False), ("Cited", True), ("Step 3: tied with it", False)],
            [(n, step, cands[n].stratum, cands[n].band, cands[n].year or "none", cands[n].cites,
              "not listed (step 2)" if step == "2" else tie_cell(tied_in, tied_out))
             for n, step, tied_in, tied_out in out])
        lines += ["", "In the mirrored core instead: %s." % ", ".join(
            "%d (step %s)" % (n, step) for n, step in instead)]
    return lines


def render(config, cfg, sel, cands, the_map, records, info, flow, compare, locked_before,
           ties=None, stopped=""):
    s = cfg["selection"]
    order = list(cfg["strata"])
    core = [n for n, _ in core_rows(sel)]
    lines = [
        "# The core: the studies read in full", "",
        "Written by `runners/core_selection.py` from `%s`; do not edit, rerun the runner. The "
        "rule is the protocol's (Two tiers); the runner's docstring gives the readings it "
        "applies." % rel(config), "",
        "Core of %d places; non-deep learners (%s) at most %d; step 2's minimum %s, falling "
        "as needed to %s; strata %s. A shared title makes two records one study %s." % (
            s["size"], ", ".join(s["non_deep"]), s["non_deep_cap"], s["minimums"][0],
            ", then ".join(map(str, s["minimums"][1:])) or "no lower",
            ", ".join("%s %d" % (name, cfg["strata"][name]["places"]) for name in order),
            "only when their first authors agree" if s["title_needs_first_author"]
            else "whatever their authors"),
        "", "## Candidates", "",
        "%d records in the map; %d whose learner is not stated, not candidates; %d candidates."
        % (len(the_map), info["unstated"], info["candidates"])]
    if info["groups"]:
        lines += ["", "Counted once with another record: %s." % "; ".join(
            "%d kept, %s counted with it" % (k, ", ".join(map(str, o))) for k, o in info["groups"])]
    else:
        lines += ["", "Counted once with another record: none."]
    lines += ["", "Records sharing a title, kept apart since their first authors do not agree or "
              "cannot be compared: "
              "%s." % ("; ".join("%d and %d (%s; %s)" % (a, b, records[a].first_author or "none",
                                                         records[b].first_author or "none")
                                 for a, b in info["apart"]) or "none")]
    by = Counter((c.stratum, c.deep) for c in cands.values())
    lines += [""] + table([("Stratum", False), ("Candidates", True), ("Deep", True),
                           ("Non-deep", True)],
                          [(name, by[(name, True)] + by[(name, False)], by[(name, True)],
                            by[(name, False)]) for name in order])
    lines += ["", "## Step 1: use beyond simulation", "",
              "%d studies, each a claim confirmed by the person at %s: %s." % (
                  len(sel.step1), ", ".join("`%s`" % lv for lv in cfg["step1"]["levels"]),
                  ", ".join(map(str, sel.step1)) or "none"),
              "", "Left out by the cap on non-deep studies, to be named under question 5: %s."
              % (", ".join(map(str, sel.left_out)) or "none")]
    if info["step1_dropped"]:
        lines += ["", "Confirmed claims on records counted with another: %s." % ", ".join(
            map(str, info["step1_dropped"]))]
    lines += ["", "## Step 2: coverage", "",
              "Minimum used: %d. %d studies, in the order taken, each with the places it filled:"
              " %s." % (sel.minimum, len(sel.step2), ", ".join(
                  "%d (%d)" % (n, gain) for n, gain in sel.step2) or "none"),
              "", "Coverage axes: %s." % ", ".join("`%s`" % a for a in info["axes"])]
    rows = []
    after2 = Counter(k for n in sel.step1 + [m for m, _ in sel.step2] for k in cands[n].cats)
    in_core = Counter(k for n in core for k in cands[n].cats)
    holders = Counter(k for c in cands.values() for k in c.cats)
    for k in info["categories"]:
        rows.append(("`%s`" % k[0], "`%s`" % k[1], info["in_map"][k], holders[k], sel.owed[k],
                     after2[k], in_core[k], category_status(k, info["in_map"][k], holders[k],
                                                           after2[k], sel.minimum)))
    lines += [""] + table([("Axis", False), ("Category", False), ("In the map", True),
                           ("Candidates", True), ("Owed", True), ("After step 2", True),
                           ("In the core", True), ("Status", False)], rows)
    lines += ["", "## Step 3: the places left", "",
              "Non-deep places the cap left for step 3: %d." % sel.budget, ""]
    taken3 = Counter((cands[p[0]].stratum, p[1]) for p in sel.step3)
    lines += table([("Stratum", False), ("Places", True), ("Its share", True),
                    ("Steps 1 and 2", True), ("Step 3", True), ("Band 1", True),
                    ("Band 2", True), ("Last place in band", False)],
                   [(name, sel.allocation[name], cfg["strata"][name]["places"],
                     sel.chosen_by[name], sel.allocation[name] - sel.chosen_by[name],
                     taken3[(name, "1")], taken3[(name, "2")], sel.fell[name] or "none")
                    for name in order])
    for name in order:
        if sel.shares[name]:
            lines += ["", "Years of %s, band %s (candidates not yet chosen, places): %s." % (
                name, sel.fell[name], ", ".join(
                    "%s %d, %d" % (y if y is not None else "no year", c, p)
                    for y, (c, p) in sel.shares[name].items()))]
    lines += ["", "Non-deep studies left out of step 3 by the cap, each with the deep study in "
              "its place: %s." % ("; ".join("%d by %d" % (a, b) for a, b in sel.swaps) or "none")]
    lines += render_ties(ties, stopped, cands, len(core))
    lines += ["", "## Flow counts", ""] + table(
        [("Count", False), ("Records", True)], [(r["label"], r["count"]) for r in flow])
    lines += ["", "## The core against the rest of the map", "",
              "Records holding each code, as a share of the core (%d) and of the rest of the map "
              "(%d); a record can hold several codes of a list axis. All codes of every axis are "
              "in `results/core/core-vs-map.csv`." % (len(core), len(the_map) - len(core)), ""]
    lines += table([("Axis", False), ("Code", False), ("Core", True), ("Core %", True),
                    ("Rest", True), ("Rest %", True)],
                   [("`%s`" % r["axis"], r["code"], r["core"], r["core_share"], r["rest"],
                     r["rest_share"]) for r in compare if r["map"]])
    lines += ["", "## The core", ""] + table(
        [("Record", True), ("Step", False), ("Stratum", False), ("Band", False), ("Year", False),
         ("Cited", True), ("Title", False)],
        [(n, step, cands[n].stratum, cands[n].band, cands[n].year or "none", cands[n].cites,
          records[n].title.replace("|", "/")) for n, step in core_rows(sel)])
    lines += ["", "Lock: %s." % ("the core is the one locked in `%s`" % cfg["outputs"]["lock"]
                                 if locked_before else "written, `%s`" % cfg["outputs"]["lock"])]
    return "\n".join(lines) + "\n"


def category_status(k, in_map, holders, after2, minimum):
    """What step 2 left a category with: met, all its candidates, empty, or short by the cap
    (the only other way the greedy stops short)."""
    if in_map == 0:
        return "empty: no record of the map holds it"
    if holders == 0:
        return "empty: no candidate holds it"
    if after2 >= minimum:
        return "met"
    if after2 >= holders:
        return "all its %d candidates" % holders
    return "short by the cap on non-deep studies"


def flow_rows(sel, info, cands, order):
    rows = [("map", "Records in the map", info["map"]),
            ("not-candidates", "Learner not stated: not candidates", info["unstated"]),
            ("candidates", "Candidates", info["candidates"]),
            ("duplicates", "Counted once with another record", info["duplicates"]),
            ("candidates-once", "Candidates, each study once", len(cands)),
            ("step1", "Step 1: use beyond simulation", len(sel.step1)),
            ("step1-cap", "Step 1: left out by the cap on non-deep studies", len(sel.left_out)),
            ("step2", "Step 2: coverage (minimum %d)" % sel.minimum, len(sel.step2))]
    for name in order:
        for band in ("1", "2"):
            rows.append(("step3-%s-band%s" % (name, band), "Step 3: %s, band %s" % (name, band),
                         sum(1 for p in sel.step3 if cands[p[0]].stratum == name and p[1] == band)))
    rows += [("step3-cap", "Step 3: non-deep studies left out by the cap", len(sel.swaps)),
             ("core", "The core", len(core_rows(sel))),
             ("core-non-deep", "Non-deep studies in the core",
              sum(1 for n, _ in core_rows(sel) if not cands[n].deep))]
    return [{"key": k, "label": label, "count": c} for k, label, c in rows]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "core.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")
    args = parser.parse_args()
    cfg = load_config(args.config, args.override)
    inputs, outputs, s = cfg["inputs"], cfg["outputs"], cfg["selection"]
    size, cap, minimums = int(s["size"]), int(s["non_deep_cap"]), [int(m) for m in s["minimums"]]
    if not minimums or any(m < 1 for m in minimums) or minimums != sorted(minimums, reverse=True):
        raise SystemExit("[selection] minimums must be whole numbers from 1 up, the highest "
                         "first: %r" % (s["minimums"],))
    order = list(cfg["strata"])
    places = {name: int(cfg["strata"][name]["places"]) for name in order}
    if sum(places.values()) != size:
        raise SystemExit("[strata] places add up to %d, not the core's %d places."
                         % (sum(places.values()), size))
    stratum_of = {}
    for name in order:
        for role in cfg["strata"][name]["roles"]:
            if role in stratum_of:
                raise SystemExit("[strata]: role %s is in two strata." % role)
            stratum_of[role] = name

    axes = mc.load_axes(resolve(inputs["schema"]))
    map_path = resolve(inputs["map"])
    if not os.path.isfile(map_path):
        raise SystemExit("%s not found: the map, written by runners/map_vote.py." % map_path)
    the_map, _ = mc.read_codes(map_path, axes)
    records = {r.number: r for r in corpus.load_references(resolve(inputs["references"]))}
    absent = [n for n in the_map if n not in records]
    if absent:
        raise SystemExit("%s holds no record %s." % (inputs["references"],
                                                     ", ".join(map(str, absent))))
    bands = read_bands(resolve(inputs["venue_bands"]), sorted(the_map))
    cov = coverage_axes(resolve(inputs["agreement"]), axes)
    categories = [(a.name, code) for a in cov for code in mc.counted(a)]
    kinds = set(categories)

    numbers, groups, apart, kept = candidates(the_map, records,
                                              bool(s["title_needs_first_author"]))
    roles = [the_map[n]["policy_role"] for n in numbers]
    unplaced = sorted({r for r in roles if r not in stratum_of})
    if unplaced:
        raise SystemExit("[strata] holds no stratum for the role %s." % ", ".join(unplaced))
    others = set(numbers) - set(kept)
    non_deep = set(s["non_deep"])
    cands = {}
    for n in kept:
        cells = the_map[n]
        cands[n] = Cand(n, stratum_of[cells["policy_role"]], cells["learner_depth"] not in non_deep,
                        bands[n][0], bands[n][1], records[n].year, records[n].cited_by_count or 0,
                        frozenset((a.name, code) for a in cov for code in codes_of(a, cells[a.name])
                                  if (a.name, code) in kinds))

    levels = [c for c in next(a.codes for a in axes if a.name == READINESS) if c != "none"]
    claims = [n for n in sorted(the_map) if the_map[n][READINESS] in levels
              and the_map[n]["learner_depth"] != mc.NOT_STATED]
    answers, open_ = read_confirmations(resolve(inputs["confirmations"]), claims, levels)
    step1_levels = cfg["step1"]["levels"]
    waiting = [n for n in open_ if the_map[n][READINESS] in step1_levels]
    if waiting:
        raise SystemExit("Claims at %s not yet answered in %s: %s. Step 1 needs them answered."
                         % (", ".join(step1_levels), inputs["confirmations"],
                            ", ".join(map(str, waiting))))
    confirmed = step1_places(numbers, the_map, answers, step1_levels)

    in_step1 = [n for n in confirmed if n in cands]
    sel = select(cands, in_step1, categories, size, cap, minimums, places, order)
    rows = core_rows(sel)
    lock = resolve(outputs["lock"])
    locked_before = check_lock(lock, rows)
    reverse, stopped = reverse_core(cands, in_step1, categories, size, cap, minimums, places,
                                    order)
    ties = (number_ties(cands, rows, reverse, sel.standing, {p[0]: p[3] for p in sel.step3})
            if reverse is not None else None)

    in_map = Counter(k for cells in the_map.values() for a in cov
                     for k in ((a.name, code) for code in codes_of(a, cells[a.name])) if k in kinds)
    info = {"map": len(the_map), "unstated": len(the_map) - len(numbers),
            "candidates": len(numbers), "duplicates": len(others), "groups": groups,
            "apart": apart, "step1_dropped": [n for n in confirmed if n in others],
            "axes": [a.name for a in cov], "categories": categories, "in_map": in_map}
    flow = flow_rows(sel, info, cands, order)
    core = [n for n, _ in rows]
    compare = comparison(axes, the_map, core, bands)

    how = {p[0]: p[3] for p in sel.step3}
    gains = dict(sel.step2)
    write_csv(resolve(outputs["core"]), CORE_FIELDS, [
        {"number": n, "step": step, "stratum": cands[n].stratum,
         "policy_role": the_map[n]["policy_role"], "learner_depth": the_map[n]["learner_depth"],
         "band": cands[n].band, "tier": cands[n].tier, "year": cands[n].year or "",
         "cited_by_count": cands[n].cites, "standing": "%.4f" % float(sel.standing[n]),
         "filled_at_step2": gains.get(n, ""), "taken": how.get(n, ""),
         "title": records[n].title, "venue": records[n].venue, "doi": records[n].doi}
        for n, step in rows])
    write_csv(resolve(outputs["flow"]), FLOW_FIELDS, flow)
    write_csv(resolve(outputs["comparison"]), COMPARE_FIELDS, compare)
    report = resolve(outputs["selection"])
    os.makedirs(os.path.dirname(report), exist_ok=True)
    with open(report, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(args.config, cfg, sel, cands, the_map, records, info, flow, compare,
                        locked_before, ties, stopped))
    if not locked_before:
        os.makedirs(os.path.dirname(lock), exist_ok=True)
        with open(lock, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"core_sha256": core_digest(rows), "studies": len(rows),
                       "core": [[n, step] for n, step in rows],
                       "inputs": {key: file_sha(resolve(inputs[key]))
                                  if os.path.isfile(resolve(inputs[key])) else None
                                  for key in ("map", "references", "venue_bands", "confirmations",
                                              "agreement")}}, fh, indent=2)

    steps = Counter(step for _, step in rows)
    print("candidates        : %d (%d counted once with another; %d without a stated learner "
          "left out)" % (len(cands), len(others), len(the_map) - len(numbers)))
    print("step 1            : %d%s" % (steps["1"], " (%s)" % ", ".join(map(str, sel.step1))
                                        if sel.step1 else ""))
    print("step 2            : %d (minimum %d)" % (steps["2"], sel.minimum))
    print("step 3            : %d (%s)" % (steps["3"], ", ".join(
        "%s %d" % (name, sel.allocation[name] - sel.chosen_by[name]) for name in order)))
    print("core              : %d, non-deep %d; left out by the cap: step 1 %d, step 3 %d"
          % (len(rows), sum(1 for n in core if not cands[n].deep), len(sel.left_out),
             len(sel.swaps)))
    if ties is None:
        print("record-number ties: not counted, the mirrored selection stopped")
    else:
        print("record-number ties: %d of the core's studies change when the order is reversed "
              "(step 2 %d, step 3 %d)"
              % (len(ties[0]), sum(1 for _, step, _, _ in ties[0] if step == "2"),
                 sum(1 for _, step, _, _ in ties[0] if step == "3")))
    print("lock              : %s" % ("unchanged" if locked_before else "written"))
    print("written           : %s, %s, %s, %s" % (rel(resolve(outputs["core"])), rel(report),
                                                  rel(resolve(outputs["flow"])),
                                                  rel(resolve(outputs["comparison"]))))


if __name__ == "__main__":
    main()
