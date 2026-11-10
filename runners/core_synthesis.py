"""Synthesize the core: the tables, five sensitivity analyses and coder-judge agreement.

Each table answers a research question by counting studies (or items) per role, or lists the
map's cells or the core's studies by role and algorithm family. Nothing is pooled (protocol,
Synthesis). Reads coded-studies.csv, core-answers.csv, the item tables, map.csv and
core-references.bib in datasets/, and results/map/map-votes.csv. Writes to
results/core-synthesis/ each table (.csv, .md, .tex), synthesis.md, quality-by-study.csv,
sensitivity.md, sensitivity/<analysis>/, and abstract-vs-full-text, map-unanimous and
agreement (.csv, .md).

Run: python runners/run_all.py --only core-synthesis
"""

import argparse
import csv
import os
import re
import statistics
import sys
import tomllib
from collections import Counter
from fractions import Fraction

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import coreblocks as cb  # noqa: E402
from src import mapcodes as mc  # noqa: E402
from runners.core_gather import GROUP_OUT  # noqa: E402
from runners.core_selection import table as md_table, write_csv  # noqa: E402
from runners.core_statistics import one_decimal, share  # noqa: E402
from runners.make_tables import tex_escape  # noqa: E402
from runners.screening_consensus import load_config, rel, resolve  # noqa: E402

ROLES = ("end-to-end", "steering", "not-stated")
FAMILIES = ("value-based", "policy-gradient", "actor-critic", "other", "not-stated")
# The abstract's role (the map's policy_role) as the paper files it.
MAP_ROLES = {"end-to-end": "end-to-end", "steering-rules": "steering",
             "steering-heuristic": "steering"}
TITLES = {"all": "All", "end-to-end": "End to end", "steering": "Steering",
          "not-stated": "Role not stated"}
SPECIAL = cb.SPECIAL
DISPUTED = ("partly", "not-supported")
VERDICTS = ("supported", "partly", "not-supported", "cannot-judge", "none")
BINS = ("none", "1", "2", "3 or more")
# The item tables: the [inputs] key, its group and the column its item's answer fills.
SOURCES = {key: (group, column) for group, (key, column) in GROUP_OUT.items()}
# The benchmark-set codes that name no one set: two studies coded other-benchmark may have used
# different sets, so neither code makes a set two studies share.
NAMED_SETS_EXCLUDED = ("none", "other-benchmark")
# Likewise the headline statistic that names no one statistic.
STATISTICS_EXCLUDED = ("other",)
# Question 3.4's tests of the evidence behind a shared claim (protocol amendment "the tests of
# question 3.4"). The first row counts the studies making the claim; each test after it is a
# share of those studies.
CLAIM_TESTS = (
    ("makes the claim", None),
    ("shares a named benchmark set with another study making it", "set"),
    ("shares an objective and a headline statistic with another study making it", "metric"),
    ("reruns every baseline, no time limit left unstated", "rerun"),
    ("comparable with another study making it on instances, metrics, baselines and time "
     "limits", "all"),
    ("several training runs with their spread", "spread"),
)
ANALYSES = (("lowest-quality", "(1) Without the lowest-quality fifth"),
            ("without-step-2", "(3) Without the studies admitted at step 2"),
            ("without-disputed", "(5) Without the answers the judge disputed"))


# ----------------------------------------------------------------------------- the data

def cell_of(study):
    """A study's cell: the role its full text gives and its algorithm family, as the
    supplement's list of the core's studies files it."""
    return "%s / %s" % (study.get("role", ""), study.get("algorithm_family", "") or "not-stated")


class Data:
    """The studies (rows of coded-studies.csv, with map_<axis> from the map), the items of
    each item table, and each answer's verdict."""

    def __init__(self, studies, items, verdicts, present=None, cells=None, filing=None):
        self.studies = studies
        self.items = items
        self.verdicts = verdicts
        self.role = {s["number"]: s.get("role", "") for s in studies}
        # A study's cell is its filing in the full data, kept when its answers are blanked.
        filing = filing or {}
        self.cell = {s["number"]: filing.get(s["number"]) or cell_of(s) for s in studies}
        # The role columns and the order of the cells: those of the full data, kept when
        # studies are left out, so that a sensitivity analysis compares the same columns.
        self.present = present or [r for r in ROLES if any(v == r for v in self.role.values())]
        order = ["%s / %s" % (r, f) for r in ROLES for f in FAMILIES]
        seen = set(self.cell.values())
        self.cells = cells or ([c for c in order if c in seen] + sorted(seen - set(order)))

    def columns(self, roles=None):
        """The columns of a table: all, then each role; `roles` keeps only those roles (and
        no column for all)."""
        chosen = [r for r in self.present if not roles or r in roles]
        return chosen if roles else ["all"] + chosen

    def in_column(self, number, column):
        return column == "all" or self.role.get(number) == column


def read_rows(path):
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_data(inputs):
    studies = read_rows(resolve(inputs["coded"]))
    the_map = {r["number"]: r for r in read_rows(resolve(inputs["the_map"]))}
    with open(resolve(inputs["map"]), "rb") as fh:
        axes = list(tomllib.load(fh)["axes"])
    for s in studies:
        m = the_map.get(s["number"], {})
        for axis in axes:
            s["map_" + axis] = m.get(axis, "")
    items = {key: read_rows(resolve(inputs[key])) for key in SOURCES if inputs.get(key)}
    verdicts, corrected = {}, {}
    for r in read_rows(resolve(inputs["answers"])):
        if r.get("field", "") == "":
            verdicts[(r["number"], r["id"])] = (r.get("verdict") or "").strip()
            if (r.get("authors_value") or "").strip():
                corrected[(r["number"], r["id"])] = r.get("value", "")
    data = Data(studies, items, verdicts)
    # The answers the authors corrected, with the coder's value: the studies' rows hold the
    # authors' value, the agreement of coder and judge is the coder's.
    data.corrected = corrected
    return data


def left_out(data):
    """The number of answers the analysis without the judge's disputes leaves out: those
    disputed, save the ones the authors corrected."""
    corrected = getattr(data, "corrected", {})
    return sum(1 for k, v in data.verdicts.items() if v in DISPUTED and k not in corrected)


# ------------------------------------------------------------------------- fields and codes

def field_info(spec, axes, name, source=None):
    """(kind, codes in order) of a field of the studies or of an item table."""
    if source is not None:
        group = spec.groups[SOURCES[source][0]]
        if name == SOURCES[source][1]:
            return group.kind, group.codes
        if name in group.fields:
            return "code", group.fields[name]
        raise SystemExit("the item table %s has no field %s" % (source, name))
    if name == "role":
        return "code", ROLES
    if name in ("year", "step", "stratum"):
        return "code", ()
    if name.startswith("map_") and name[4:] in axes:
        axis = axes[name[4:]]
        return ("codes" if axis.get("multi") else "code"), tuple(axis["codes"]) + ("not-stated",)
    if name in spec.by_name:
        q = spec.by_name[name]
        return q.kind, q.codes
    if name in spec.derived:
        d = spec.derived[name]
        values = tuple(dict.fromkeys(d["map"].values())) if "map" in d else ("yes", "no")
        return "code", values
    raise SystemExit("no question, derived column or map axis named %s" % name)


def codes_of(kind, cell):
    """The codes a cell counts under."""
    cell = (cell or "").strip()
    if not cell:
        return []
    if cell in SPECIAL:
        return [cell]
    if kind == "codes":
        return [c for c in cell.split("|") if c]
    if kind == "count":
        if not cell.isdigit():
            return [cell]
        n = int(cell)
        return [str(n)] if n < 3 else ["3 or more"]
    if kind == "number":
        return ["reported"]
    return [cell]


def ordered(kind, codes, seen):
    """The codes to show, in the question's order, then the special answers, then any other
    value seen, each only if seen."""
    base = (list(BINS) if kind == "count" else ["reported"] if kind == "number"
            else list(cb.SCORES) if kind == "score" else list(codes))
    order = base + [s for s in SPECIAL if s not in base]
    return [c for c in order if c in seen] + sorted(c for c in seen if c not in order)


def numbers_of(records, name):
    out = []
    for r in records:
        try:
            out.append(float(r.get(name, "")))
        except ValueError:
            pass
    return out


def fmt_number(x):
    return ("%d" % x) if float(x).is_integer() else ("%.1f" % x)


# --------------------------------------------------------------------------- the tables

def count_rows(data, spec, axes, t, records_of, per_study=False, source=None):
    """[row]: field, code, n_<column>, pct_<column>, for each field of the table."""
    columns = data.columns(t.get("roles"))
    rows = []
    for name in t["fields"]:
        kind, codes = field_info(spec, axes, name, source)
        by_col = {}
        for c in columns:
            recs = [r for r in records_of() if data.in_column(r["number"], c)]
            if per_study:
                size = sum(1 for s in data.studies if data.in_column(s["number"], c))
                held = {}
                for r in recs:
                    for code in codes_of(kind, r.get(name)):
                        held.setdefault(code, set()).add(r["number"])
                counts = {code: len(ns) for code, ns in held.items()}
            else:
                answered = [r for r in recs if (r.get(name) or "").strip()]
                size = len(answered)
                counts = Counter(code for r in answered for code in codes_of(kind, r.get(name)))
            by_col[c] = (counts, size, recs)
        seen = set().union(*(set(v[0]) for v in by_col.values())) if by_col else set()
        for code in ordered(kind, codes, seen):
            row = {"field": name, "code": code}
            for c in columns:
                counts, size, _ = by_col[c]
                row["n_" + c] = counts.get(code, 0)
                row["pct_" + c] = share(counts.get(code, 0), size)
            rows.append(row)
        if kind == "number":
            for label, fn in (("median", statistics.median), ("smallest", min), ("largest", max)):
                row = {"field": name, "code": label}
                for c in columns:
                    values = numbers_of(by_col[c][2], name)
                    row["n_" + c] = fmt_number(fn(values)) if values else ""
                    row["pct_" + c] = ""
                rows.append(row)
    return columns, rows


def crosstab_rows(data, spec, axes, t):
    """[row]: the row field's code, then a count for each code of the column field."""
    rk, rcodes = field_info(spec, axes, t["rows"])
    ck, ccodes = field_info(spec, axes, t["cols"])
    roles = t.get("roles")
    recs = [s for s in data.studies if not roles or data.role.get(s["number"]) in roles]
    pairs = Counter()
    for r in recs:
        for a in codes_of(rk, r.get(t["rows"])):
            for b in codes_of(ck, r.get(t["cols"])):
                pairs[(a, b)] += 1
    rows_seen = {a for a, _ in pairs}
    cols_seen = {b for _, b in pairs}
    cols = ordered(ck, ccodes, cols_seen)
    out = []
    for a in ordered(rk, rcodes, rows_seen):
        row = {"field": t["rows"], "code": a}
        for b in cols:
            row[b] = pairs.get((a, b), 0)
        row["total"] = sum(pairs.get((a, b), 0) for b in cols)
        out.append(row)
    return cols, out, len(recs)


def study_means(data, fields):
    """{number: mean score over the assessable items, or None}."""
    out = {}
    for s in data.studies:
        scores = [Fraction(s[f]) for f in fields if s.get(f) in ("1", "0.5", "0")]
        out[s["number"]] = sum(scores) / len(scores) if scores else None
    return out


def claims_rows(data, spec, t):
    """Question 3.4: for each claim, the studies that make it, and among them those whose
    evidence meets each of CLAIM_TESTS: a named benchmark set shared with another study making
    it; an objective and a headline statistic shared with one; every baseline rerun with no
    time limit left unstated; all of these with one other study making it, which reruns its
    baselines so too; and several training runs with their spread."""
    claims = data.items.get("claims", [])
    baselines = data.items.get("baselines", [])
    by_study = {s["number"]: s for s in data.studies}
    columns = data.columns(t.get("roles"))
    kind, codes = field_info(spec, {}, "claim", "claims")
    making = {}
    for r in claims:
        for code in codes_of(kind, r.get("claim")):
            making.setdefault(code, set()).add(r["number"])
    runs = {}
    for b in baselines:
        runs.setdefault(b["number"], []).append(b)

    def named(n):
        cell = by_study.get(n, {}).get("benchmark_sets", "")
        return {c for c in codes_of("codes", cell) if c not in SPECIAL + NAMED_SETS_EXCLUDED}

    def metric(n):
        s = by_study.get(n, {})
        objectives = {c for c in codes_of("codes", s.get("objective", "")) if c not in SPECIAL}
        statistic = s.get("headline_statistic", "")
        return objectives, ("" if statistic in SPECIAL + STATISTICS_EXCLUDED else statistic)

    def same_metric(x, y):
        (ox, sx), (oy, sy) = metric(x), metric(y)
        return bool(ox & oy) and sx != "" and sx == sy

    def rerun(n):
        bs = runs.get(n, [])
        return bool(bs) and all(b.get("run") == "rerun" and b.get("time_limit") != "not-stated"
                                for b in bs)

    def spread(n):
        s = by_study.get(n, {})
        try:
            several = float(s.get("seeds", "")) > 1
        except ValueError:
            several = False
        return several and s.get("seed_spread") == "reported"

    def passes(test, x, studies):
        others = [y for y in studies if y != x]
        if test == "set":
            return any(named(x) & named(y) for y in others)
        if test == "metric":
            return any(same_metric(x, y) for y in others)
        if test == "rerun":
            return rerun(x)
        if test == "all":
            return rerun(x) and any(named(x) & named(y) and same_metric(x, y) and rerun(y)
                                    for y in others)
        return spread(x)

    rows = []
    for code in ordered(kind, codes, set(making)):
        studies = making[code]
        for label, test in CLAIM_TESTS:
            row = {"field": code, "code": label}
            for c in columns:
                inside = {n for n in studies if data.in_column(n, c)}
                if test is None:
                    size = sum(1 for s in data.studies if data.in_column(s["number"], c))
                    n = len(inside)
                else:
                    size = len(inside)
                    n = sum(1 for x in inside if passes(test, x, studies))
                row["n_" + c], row["pct_" + c] = n, share(n, size)
            rows.append(row)
    return columns, rows


def map_cells_rows(axes, map_rows, t):
    """The map's cells: one row per populated cell of the abstract's role and family over the
    map's records, a record with several families under each; per field, its three most
    frequent codes with their records, and how many records name any code."""
    members = {}
    for r in map_rows:
        role = MAP_ROLES.get((r.get("policy_role") or "").strip(), "not-stated")
        families = [c for c in codes_of("codes", r.get("training_algorithm_family"))
                    if c not in SPECIAL] or ["not-stated"]
        for f in families:
            members.setdefault((role, f), []).append(r)
    order = [(r, f) for r in ROLES for f in FAMILIES]
    keys = [k for k in order if k in members] + sorted(k for k in members if k not in order)
    out = []
    for role, family in keys:
        recs = members[(role, family)]
        row = {"role": role, "family": family, "records": len(recs)}
        for field in t["fields"]:
            kind = "codes" if axes[field].get("multi") else "code"
            counts = Counter(c for r in recs for c in codes_of(kind, r.get(field))
                             if c not in SPECIAL)
            naming = sum(1 for r in recs if any(c not in SPECIAL
                                                for c in codes_of(kind, r.get(field))))
            top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
            row[field] = ("; ".join("%s %d" % kv for kv in top) + " (of %d naming one)" % naming
                          if top else "none named")
        out.append(row)
    return out


def bib_keys(path):
    """{record number: BibTeX key} from the core's block of the bibliography, where each entry
    follows a '% Record N' line; {} when there is no bibliography."""
    if not path or not os.path.isfile(path):
        return {}
    keys, pending = {}, None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            found = re.match(r"^%\s*Record\s+(\d+)\s*$", line)
            if found:
                pending = found.group(1)
                continue
            entry = re.match(r"^@\w+\{([^,\s]+),", line)
            if entry and pending:
                keys[pending] = entry.group(1)
                pending = None
    return keys


def list_rows(data, t, keys):
    """The core's studies, one row each in the order of their cells, with its cell and its
    BibTeX key."""
    rank = {c: i for i, c in enumerate(data.cells)}
    rows = []
    for s in sorted(data.studies, key=lambda s: (rank.get(data.cell[s["number"]], len(rank)),
                                                  int(s["number"]))):
        cell = data.cell[s["number"]]
        row = {"number": s["number"], "key": keys.get(s["number"], ""), "cell": cell}
        for f in t.get("fields", []):
            row[f] = s.get(f, "")
        rows.append(row)
    return rows


def compute(data, spec, axes, tables, map_rows=(), keys=None):
    """{table id: (kind, columns, rows, extra)} for every [[table]]."""
    out = {}
    for t in tables:
        kind, source = t["kind"], t.get("source")
        if kind == "map-cells":
            out[t["id"]] = (kind, list(t["fields"]), map_cells_rows(axes, map_rows, t),
                            len(map_rows))
        elif kind == "list":
            rows = list_rows(data, t, keys or {})
            out[t["id"]] = (kind, list(t.get("fields", [])), rows, len(rows))
        elif kind == "count":
            columns, rows = count_rows(data, spec, axes, t, lambda: data.studies)
            out[t["id"]] = (kind, columns, rows, None)
        elif kind == "items":
            columns, rows = count_rows(data, spec, axes, t, lambda: data.items.get(source, []),
                                       t.get("per", "item") == "study", source)
            out[t["id"]] = (kind, columns, rows, None)
        elif kind == "crosstab":
            cols, rows, n = crosstab_rows(data, spec, axes, t)
            out[t["id"]] = (kind, cols, rows, n)
        elif kind == "claims":
            columns, rows = claims_rows(data, spec, t)
            out[t["id"]] = (kind, columns, rows, None)
        else:
            raise SystemExit("a table of an unknown kind %s" % kind)
    return out


# -------------------------------------------------------------------------- the outputs

def headings(kind, columns):
    if kind == "map-cells":
        return ["role", "family", "records"] + list(columns)
    if kind == "list":
        return ["number", "key", "cell"] + list(columns)
    if kind == "crosstab":
        return ["field", "code"] + list(columns) + ["total"]
    return ["field", "code"] + [x for c in columns for x in ("n_" + c, "pct_" + c)]


def cell_text(row, c):
    n, p = row.get("n_" + c, ""), row.get("pct_" + c, "")
    return "%s (%s%%)" % (n, p) if p != "" else str(n)


def md_rows(kind, columns, rows):
    if kind in ("map-cells", "list"):
        heads = headings(kind, columns)
        return md_table([(h, h in ("records", "number")) for h in heads],
                        [[r.get(h, "") for h in heads] for r in rows])
    if kind == "crosstab":
        head = [("Field", False), ("Code", False)] + [(c, True) for c in columns] + [("Total", True)]
        body = [[r["field"], r["code"]] + [r[c] for c in columns] + [r["total"]] for r in rows]
        return md_table(head, body)
    head = [("Field", False), ("Code", False)] + [(TITLES.get(c, c), True) for c in columns]
    return md_table(head, [[r["field"], r["code"]] + [cell_text(r, c) for c in columns]
                           for r in rows])


def tex_rows(kind, columns, rows):
    out = []
    for r in rows:
        if kind in ("map-cells", "list"):
            cells = [str(r.get(h, "")) for h in headings(kind, columns)]
        elif kind == "crosstab":
            cells = [r["field"], r["code"]] + [str(r[c]) for c in columns] + [str(r["total"])]
        else:
            cells = [r["field"], r["code"]] + [cell_text(r, c) for c in columns]
        out.append(" & ".join(tex_escape(x) for x in cells) + r" \\")
    return out


def note_of(t, kind, extra, data):
    if kind == "map-cells":
        note = ("The map's %d records, each under every pair of its abstract's role and family "
                "(a record with several families counts under each)" % extra)
        if t.get("fields"):
            note += ("; per field, its three most frequent codes with their records, and the "
                     "records naming any code")
        return note + "."
    if kind == "list":
        return "The core's studies listed (%d), each with its cell and its BibTeX key." % extra
    if kind == "crosstab":
        return "Counts of studies (%d), each under every pair of its codes." % extra
    if kind == "items" and t.get("per", "item") == "study":
        return "Studies with at least one item of each code, as a share of the column's studies."
    if kind == "items":
        return "Items of the table, as a share of the column's items with an answer."
    if kind == "claims":
        return ("Per claim: the studies that make it (a share of the column's studies), then "
                "those of them whose evidence meets each of question 3.4's tests (a share of the "
                "studies making it): a named benchmark set shared with another study making the "
                "claim; an objective and a headline statistic shared with one; every baseline "
                "rerun with no time limit left unstated; all of these with one other study "
                "making it, which reruns its baselines so too; several training runs with their "
                "spread (protocol, Amendments: the tests of Question 3.4).")
    return ("Studies, as a share of the column's studies with an answer to the question; a study "
            "with several codes counts under each.")


def write_table(out_dir, config, t, result, data):
    kind, columns, rows, extra = result
    base = os.path.join(out_dir, t["id"])
    write_csv(base + ".csv", headings(kind, columns), rows)
    stamp = "Written by `runners/core_synthesis.py` from `%s`; do not edit, rerun the runner." % config
    lines = ["# %s" % t["title"], "", stamp, "",
             "RQ %s. %s" % (t.get("rq", ""), note_of(t, kind, extra, data)), ""]
    lines += md_rows(kind, columns, rows)
    with open(base + ".md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(base + ".tex", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("%% Generated by runners/core_synthesis.py from %s.\n" % config)
        fh.write("% Do not edit. Regenerate: python runners/run_all.py --only core-synthesis\n")
        fh.write("\n".join(tex_rows(kind, columns, rows)) + "\n")
    return lines[4:]


# ------------------------------------------------------------------ sensitivity analyses

def signed(value):
    """A difference to one decimal, with its sign, rounded as one_decimal rounds."""
    value = Fraction(value)
    return ("-" if value < 0 else "") + one_decimal(abs(value))


def shares_of(result):
    """{key: share in percent} of one table's result, for comparing two runs of it; none for
    the map's cells (the map is the same in every analysis) or a list of studies."""
    kind, columns, rows, extra = result
    out = {}
    if kind in ("map-cells", "list"):
        return out
    for r in rows:
        if kind == "crosstab":
            size = extra or 0
            for c in columns:
                out[(r["field"], r["code"], c)] = float(100 * r[c] / size) if size else 0.0
        else:
            for c in columns:
                p = r.get("pct_" + c, "")
                if p != "":
                    out[(r["field"], r["code"], c)] = float(p)
    return out


def largest_change(main, other):
    keys = set(main) | set(other)
    if not keys:
        return 0.0, None
    key = max(keys, key=lambda k: (abs(other.get(k, 0.0) - main.get(k, 0.0)), str(k)))
    return abs(other.get(key, 0.0) - main.get(key, 0.0)), key


def lowest_quality(data, fields):
    """The numbers of the lowest-quality fifth: the k studies (a fifth of the core, rounded
    half up) with the lowest mean score over their assessable items. The cut is the mean of the
    first study kept, so studies tied at the cut are all kept; a study with no assessable item
    is kept."""
    means = study_means(data, fields)
    scored = sorted(m for m in means.values() if m is not None)
    k = int(Fraction(len(data.studies), 5) + Fraction(1, 2))
    if not scored or k == 0:
        return set()
    if k >= len(scored):
        return {n for n, m in means.items() if m is not None}
    cut = scored[k]
    return {n for n, m in means.items() if m is not None and m < cut}


def without(data, numbers):
    keep = [dict(s) for s in data.studies if s["number"] not in numbers]
    items = {k: [dict(r) for r in v if r["number"] not in numbers] for k, v in data.items.items()}
    return Data(keep, items, data.verdicts, data.present, data.cells, data.cell)


def without_disputed(data, spec):
    """The data with every disputed answer blanked (and the derived columns that rest on it),
    and every disputed item left out; the studies' roles and cells kept, so that a study whose
    algorithm the judge disputed keeps the cell the list of the core's studies gives it. An
    answer the authors corrected stands: they read it against the paper."""
    corrected = getattr(data, "corrected", {})
    studies = []
    for s in data.studies:
        s = dict(s)
        for q in spec.questions.values():
            key = (s["number"], q.qid)
            if data.verdicts.get(key) in DISPUTED and key not in corrected:
                s[q.name] = ""
                for name, d in spec.derived.items():
                    if d["from"] == q.name:
                        s[name] = ""
        studies.append(s)
    items = {k: [dict(r) for r in v if r.get("verdict") not in DISPUTED]
             for k, v in data.items.items()}
    return Data(studies, items, data.verdicts, data.present, data.cells, data.cell)


def abstract_vs_full_text(data, axes):
    """[row] per axis and code: the studies, those whose abstract code (the map) is the full
    text's, those whose abstract said not-stated where the full text gives a code, and kappa of
    the code's presence between the two."""
    rows = []
    for axis, a in axes.items():
        kind = "codes" if a.get("multi") else "code"
        pairs = [(s.get("map_" + axis, ""), s.get(axis, "")) for s in data.studies
                 if s.get("map_" + axis, "")]
        same = sum(1 for m, f in pairs if set(codes_of(kind, m)) == set(codes_of(kind, f)))
        silent = sum(1 for m, f in pairs if m == "not-stated" and f not in ("", "not-stated"))
        exact = mc.kappa([(m, f) for m, f in pairs]) if kind == "code" else None
        rows.append({"axis": axis, "code": "", "studies": len(pairs), "same": same,
                     "same_pct": share(same, len(pairs)), "abstract_silent": silent,
                     "kappa": "" if exact is None else "%.3f" % exact})
        for code in tuple(a["codes"]) + ("not-stated",):
            k = mc.kappa([(code in codes_of(kind, m), code in codes_of(kind, f)) for m, f in pairs])
            n_map = sum(1 for m, _ in pairs if code in codes_of(kind, m))
            n_full = sum(1 for _, f in pairs if code in codes_of(kind, f))
            rows.append({"axis": axis, "code": code, "studies": len(pairs),
                         "same": "%d / %d" % (n_map, n_full), "same_pct": "",
                         "abstract_silent": "", "kappa": "" if k is None else "%.3f" % k})
    return rows


def map_unanimous(map_rows, vote_rows, axes):
    """[row] per axis and code: its share among all the map's records, and among the records
    whose codes all three models gave alike for that axis. A record no model coded (one a
    person coded) is not among them: its blank cells are no agreement."""
    header = list(vote_rows[0]) if vote_rows else []
    models = sorted({c[len("policy_role_"):] for c in header if c.startswith("policy_role_")})
    votes = {r["number"]: r for r in vote_rows}
    rows = []
    for axis, a in axes.items():
        if not models or any("%s_%s" % (axis, m) not in header for m in models):
            continue
        kind = "codes" if a.get("multi") else "code"
        unanimous = []
        for n, r in votes.items():
            given = {(r.get("%s_%s" % (axis, m)) or "").strip() for m in models}
            if len(given) == 1 and "" not in given:
                unanimous.append(n)
        held = [r for r in map_rows if r["number"] in set(unanimous)]
        for code in tuple(a["codes"]) + ("not-stated",):
            n_all = sum(1 for r in map_rows if code in codes_of(kind, r.get(axis)))
            n_un = sum(1 for r in held if code in codes_of(kind, r.get(axis)))
            p_all, p_un = share(n_all, len(map_rows)), share(n_un, len(held))
            change = "" if p_all == "" or p_un == "" else signed(Fraction(p_un) - Fraction(p_all))
            rows.append({"axis": axis, "code": code, "records": len(map_rows), "n": n_all,
                         "pct": p_all, "unanimous_records": len(held), "unanimous_n": n_un,
                         "unanimous_pct": p_un, "change_pp": change})
    return rows


def agreement(data, spec):
    """[row] per question: the judge's verdicts and kappa of the agent's value against the
    judge's (the agent's when supported, the proposal when disputed)."""
    answers = {}
    for (n, bid), verdict in data.verdicts.items():
        answers[(n, bid)] = verdict
    values = {}
    coder = getattr(data, "corrected", {})
    for s in data.studies:
        for q in spec.questions.values():
            key = (s["number"], q.qid)
            values[key] = coder.get(key, s.get(q.name, ""))
    proposals = data.proposals if hasattr(data, "proposals") else {}
    rows = []
    for q in spec.questions.values():
        counts = Counter(answers.get((s["number"], q.qid), "") for s in data.studies)
        pairs = []
        if q.kind != "text":
            for s in data.studies:
                key = (s["number"], q.qid)
                v, verdict = values.get(key, ""), answers.get(key, "")
                if verdict == "supported":
                    pairs.append((v, v))
                elif verdict in DISPUTED and proposals.get(key):
                    pairs.append((v, proposals[key]))
        judged = sum(counts[v] for v in ("supported", "partly", "not-supported"))
        k = mc.kappa(pairs) if pairs else None
        rows.append({"qid": q.qid, "name": q.name, "section": q.section, "rq": q.rq,
                     **{v.replace("-", "_"): counts.get(v, 0) for v in VERDICTS},
                     "judged": judged, "supported_pct": share(counts.get("supported", 0), judged),
                     "pairs": len(pairs), "kappa": "" if k is None else "%.3f" % k})
    return rows


# ----------------------------------------------------------------------------- the run

def synthesize(config_path, override=None):
    cfg = load_config(config_path, override)
    inputs, out_dir = cfg["inputs"], resolve(cfg["outputs"]["dir"])
    config = rel(config_path)
    spec = cb.load_spec(resolve(inputs["spec"]), resolve(inputs["map"]))
    with open(resolve(inputs["map"]), "rb") as fh:
        axes = tomllib.load(fh)["axes"]
    data = load_data(inputs)
    data.proposals = {(r["number"], r["id"]): r.get("judge_value", "")
                      for r in read_rows(resolve(inputs["answers"])) if r.get("field", "") == ""}
    map_rows = read_rows(resolve(inputs["the_map"]))
    keys = bib_keys(resolve(inputs["bib"])) if inputs.get("bib") else {}
    os.makedirs(out_dir, exist_ok=True)
    stamp = "Written by `runners/core_synthesis.py` from `%s`; do not edit, rerun the runner." % config
    index = ["# The core's synthesis", "", stamp, ""]
    if not data.studies:
        index.append("No studies gathered yet (`%s` has no rows): nothing to tabulate."
                     % inputs["coded"])
        with open(os.path.join(out_dir, "synthesis.md"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(index) + "\n")
        print("studies           : none yet; nothing written but synthesis.md")
        return
    tables = cfg["table"]
    columns = data.columns()
    index += ["%d studies: %s." % (len(data.studies), ", ".join(
        "%s %d" % (TITLES[c], sum(1 for s in data.studies if data.in_column(s["number"], c)))
        for c in columns if c != "all")), ""]
    main = compute(data, spec, axes, tables, map_rows, keys)
    for t in tables:
        index += ["## %s" % t["title"], ""] + write_table(out_dir, config, t, main[t["id"]], data)
        index.append("")
    with open(os.path.join(out_dir, "synthesis.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(index) + "\n")
    q_fields = [q.name for q in spec.questions.values() if q.kind == "score"]
    means = study_means(data, q_fields)
    write_csv(os.path.join(out_dir, "quality-by-study.csv"),
              ["number", "role"] + q_fields + ["mean"],
              [dict({f: s.get(f, "") for f in q_fields}, number=s["number"], role=s.get("role", ""),
                    mean="" if means[s["number"]] is None else "%.3f" % float(means[s["number"]]))
               for s in data.studies])
    # The sensitivity analyses.
    low = lowest_quality(data, q_fields)
    step2 = {s["number"] for s in data.studies if s.get("step") == "2"}
    variants = {"lowest-quality": (without(data, low), "%d studies left out" % len(low)),
                "without-step-2": (without(data, step2), "%d studies left out" % len(step2)),
                "without-disputed": (without_disputed(data, spec),
                                     "%d answers left out" % left_out(data))}
    sens = ["# The sensitivity analyses", "", stamp, "",
            "Each table recomputed without some studies or answers; the largest change in a "
            "share, in percentage points, with the cell where it falls. (2) and (4) are in "
            "abstract-vs-full-text.md and map-unanimous.md.", ""]
    for key, title in ANALYSES:
        variant, what = variants[key]
        sub = compute(variant, spec, axes, tables, map_rows, keys)
        folder = os.path.join(out_dir, "sensitivity", key)
        body = []
        for t in tables:
            kind, cols, rows, extra = sub[t["id"]]
            if kind == "map-cells":
                continue    # the map is the same in every analysis
            write_csv(os.path.join(folder, t["id"] + ".csv"), headings(kind, cols), rows)
            if kind == "list":
                continue    # a list of the studies left, with no share to compare
            change, cell = largest_change(shares_of(main[t["id"]]), shares_of(sub[t["id"]]))
            body.append((t["id"], "%.1f" % change, " / ".join(map(str, cell)) if cell else ""))
        sens += ["## %s" % title, "", "%s; %d studies remain." % (what, len(variant.studies)), ""]
        sens += md_table([("Table", False), ("Largest change (pp)", True), ("Cell", False)], body)
        sens.append("")
    with open(os.path.join(out_dir, "sensitivity.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(sens) + "\n")
    rows = abstract_vs_full_text(data, axes)
    fields = ["axis", "code", "studies", "same", "same_pct", "abstract_silent", "kappa"]
    write_csv(os.path.join(out_dir, "abstract-vs-full-text.csv"), fields, rows)
    lines = ["# (2) The abstract's codes against the full text's", "", stamp, "",
             "Per axis: the studies whose abstract (the map's vote) gave the full text's codes, "
             "those whose abstract said not-stated where the full text gives a code, and kappa; "
             "per code: studies holding it in the abstract / in the full text, and kappa of its "
             "presence.", ""]
    lines += md_table([("Axis", False), ("Code", False), ("Studies", True), ("Same", True),
                       ("Same %", True), ("Abstract silent", True), ("Kappa", True)],
                      [[r[f] for f in fields] for r in rows])
    with open(os.path.join(out_dir, "abstract-vs-full-text.md"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    map_rows = read_rows(resolve(inputs["the_map"]))
    rows = map_unanimous(map_rows, read_rows(resolve(inputs["map_votes"])), axes)
    fields = ["axis", "code", "records", "n", "pct", "unanimous_records", "unanimous_n",
              "unanimous_pct", "change_pp"]
    write_csv(os.path.join(out_dir, "map-unanimous.csv"), fields, rows)
    lines = ["# (4) The map's shares on the records all three models coded alike", "", stamp, "",
             "Per axis and code: its share among all the map's records, and among the records "
             "whose codes for that axis all three models gave alike.", ""]
    lines += md_table([(f, f not in ("axis", "code")) for f in fields],
                      [[r[f] for f in fields] for r in rows])
    with open(os.path.join(out_dir, "map-unanimous.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    rows = agreement(data, spec)
    fields = ["qid", "name", "section", "rq"] + [v.replace("-", "_") for v in VERDICTS] + [
        "judged", "supported_pct", "pairs", "kappa"]
    write_csv(os.path.join(out_dir, "agreement.csv"), fields, rows)
    lines = ["# The agreement of the coding agent and the judge", "", stamp, ""]
    if not any(data.verdicts.values()):
        lines.append("No verdicts yet.")
    else:
        lines += ["Per question: the judge's verdicts on the studies' answers, the share it "
                  "supported, and kappa of the agent's value against the judge's (the agent's "
                  "where supported, the judge's proposal where disputed). The agent's value is "
                  "its own where the authors corrected an answer (%d answers)."
                  % len(getattr(data, "corrected", {})), ""]
        lines += md_table([(f, f not in ("qid", "name", "section", "rq")) for f in fields],
                          [[r[f] for f in fields] for r in rows])
    with open(os.path.join(out_dir, "agreement.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("studies           : %d (%s)" % (len(data.studies), ", ".join(
        "%s %d" % (c, sum(1 for s in data.studies if data.in_column(s["number"], c)))
        for c in columns if c != "all")))
    print("tables            : %d, in %s" % (len(tables), rel(out_dir)))
    print("sensitivity       : lowest-quality %d left out, step 2 %d left out, %d disputed answers"
          % (len(low), len(step2), left_out(data)))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "core-synthesis.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")
    args = parser.parse_args()
    synthesize(args.config, args.override)


if __name__ == "__main__":
    main()
