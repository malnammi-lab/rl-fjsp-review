"""Count the map, the candidates and the core, in three tables with the same rows.

The rows are the publication years, every code of the map's axes, citation bins and venue
countries, each with its count and its share of the set. The map's codes are also counted
by publication period. Reads datasets/map.csv, references.json, venue-bands.csv and
core.csv, and results/core/core-lock.json. Refuses a core other than the locked one, and
inputs changed since the lock. Writes results/core/core-statistics.md, core-statistics.csv,
map-by-period.csv, map-by-period.md and map-by-period.tex.

Run: python runners/run_all.py --only core-statistics
"""

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter
from fractions import Fraction

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus  # noqa: E402
from src import mapcodes as mc  # noqa: E402
from src import withheld  # noqa: E402
from runners.core_selection import (NOT_IN_SJR, candidates, core_digest,  # noqa: E402
                                    file_sha, read_bands, table, write_csv, year_order)
from runners.screening_consensus import load_config, rel, resolve  # noqa: E402

FIELDS = ["set", "group", "item", "count", "percent"]
PERIOD_FIELDS = ["period", "start_year", "end_year", "records", "axis", "code", "count",
                 "percent", "multi"]
# The sets, in the order of the report: key, heading, what a member is called.
SETS = (("map", "The map", "records"), ("candidates", "The candidates", "records"),
        ("core", "The core", "studies"))


def one_decimal(value):
    """A number to one decimal, computed exactly and a half rounded up, as a reader counting
    by hand would round it (44.55 is 44.6; binary floating point would print 44.5)."""
    tenths = math.floor(Fraction(value) * 10 + Fraction(1, 2))
    return "%d.%d" % (tenths // 10, tenths % 10)


def share(count, size):
    """A count as a percentage of `size`, to one decimal; blank for an empty set."""
    return one_decimal(Fraction(100 * count, size)) if size else ""


def citation_bins(bounds):
    """[(label, low, high)] from the bins' lower bounds, `high` None for the last, open-ended
    bin: [0, 1, 5] gives '0', '1 to 4', '5 or more'. Refuses bounds that are not whole numbers
    from 0 up, each above the one before."""
    whole = isinstance(bounds, list) and bounds and all(
        isinstance(b, int) and not isinstance(b, bool) for b in bounds)
    if not whole or bounds[0] != 0 or any(b <= a for a, b in zip(bounds, bounds[1:])):
        raise SystemExit("[statistics] citation_bins must be whole numbers from 0, each above "
                         "the one before: %r" % (bounds,))
    out = []
    for i, low in enumerate(bounds):
        high = bounds[i + 1] - 1 if i + 1 < len(bounds) else None
        if high is None:
            label = "%d or more" % low
        elif high == low:
            label = str(low)
        else:
            label = "%d to %d" % (low, high)
        out.append((label, low, high))
    return out


def read_core(path, lock_path, kept, sources=None):
    """The core's record numbers, from datasets/core.csv. Refuses a missing core or lock, a
    core other than the one the lock holds, an input in `sources` ({key: path}) whose SHA-256
    differs from the one the lock recorded for that key, and a study that is not a
    candidate. A record file released without its abstracts stands for the file as written
    whose SHA-256 the lock recorded, as configs/withheld.toml pairs them (src/withheld.py)."""
    for p, what in ((path, "the core"), (lock_path, "the core's lock")):
        if not os.path.isfile(p):
            raise SystemExit("%s not found: %s, written by runners/core_selection.py." % (p, what))
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = [(int(r["number"]), (r.get("step") or "").strip())
                for r in csv.DictReader(fh) if (r.get("number") or "").strip()]
    with open(lock_path, encoding="utf-8") as fh:
        lock = json.load(fh)
    if core_digest(rows) != lock.get("core_sha256"):
        raise SystemExit("%s is not the core locked in %s: rerun runners/core_selection.py."
                         % (path, lock_path))
    held = lock.get("inputs") or {}
    changed = [p for key, p in (sources or {}).items()
               if held.get(key) and file_sha(p) != held[key]
               and not withheld.stands_for(p, held[key])]
    if changed:
        raise SystemExit("%s changed since the core was locked (%s): the counts would describe "
                         "other data than the core was drawn from." % (", ".join(changed),
                                                                      lock_path))
    strange = [n for n, _ in rows if n not in set(kept)]
    if strange:
        raise SystemExit("%s holds records that are not candidates: %s."
                         % (path, ", ".join(map(str, strange))))
    return [n for n, _ in rows]


def code_items(axes, the_map):
    """[(group, [(item, holds)])] for the map's codes: each axis, its codes in the schema's
    order, then `not-stated`; holds(n) tells whether record n holds the code."""
    def holds(a, code):
        return lambda n: mc.has(a, the_map[n][a.name], code)

    return [("`%s`" % a.name, [(code, holds(a, code)) for code in a.codes + (mc.NOT_STATED,)])
            for a in axes]


def stated_items(axes, the_map, names):
    """[(group key, label, [(item, holds)], base)] for each axis of `names`: its codes other
    than `not-stated`, whose shares are taken over the records that state a code, base(n)
    (question 1.1 reports the roles over the records that state them, beside the share that
    does not)."""
    known = {a.name: a for a in axes}
    unknown = [name for name in names if name not in known]
    if unknown:
        raise SystemExit("[statistics] stated_axes names no axis of the schema: %s"
                         % ", ".join(unknown))
    out = []
    for name in names:
        a = known[name]
        out.append(("%s_stated" % a.name, "`%s`, of the records that state one" % a.name,
                    [(code, lambda n, a=a, code=code: mc.has(a, the_map[n][a.name], code))
                     for code in a.codes],
                    lambda n, a=a: not mc.has(a, the_map[n][a.name], mc.NOT_STATED)))
    return out


def groups_of(axes, the_map, records, bands, bins, stated=()):
    """The rows of every table: [(group key, group label, [(item, holds)])], an axis of
    `stated` followed by its group over the records that state a code (with its base)."""
    years = year_order({records[n].year for n in the_map})
    countries = Counter(bands[n][2] or NOT_IN_SJR for n in the_map)

    def cites(n):
        return records[n].cited_by_count or 0

    def within(low, high):
        return lambda n: cites(n) >= low and (high is None or cites(n) <= high)

    out = [("year", "Year", [(str(y) if y is not None else "no year",
                              lambda n, y=y: records[n].year == y) for y in years])]
    extra = {g[0][:-len("_stated")]: g for g in stated_items(axes, the_map, stated)}
    for label, items in code_items(axes, the_map):
        out.append((label.strip("`"), label, items))
        if label.strip("`") in extra:
            out.append(extra[label.strip("`")])
    out.append(("citations", "Citations",
                [(label, within(low, high)) for label, low, high in bins]))
    out.append(("venue_country", "Venue country", [
        (country, lambda n, country=country: (bands[n][2] or NOT_IN_SJR) == country)
        for country in sorted(countries, key=lambda c: (c == NOT_IN_SJR, -countries[c], c))]))
    return out


def count_rows(numbers, groups):
    """[(group key, group label, item, count, percent)] for one set; a group with a base takes
    its shares over the set's records the base holds (an axis's records that state a code)."""
    out = []
    for key, label, items, *base in groups:
        size = sum(1 for n in numbers if base[0](n)) if base else len(numbers)
        for item, holds in items:
            count = sum(1 for n in numbers if holds(n))
            out.append((key, label, item, count, share(count, size)))
    return out


def period_specs(raw):
    """Validated [(label, start, end)] from [statistics] periods.

    The periods must be ordered, disjoint, and bounded by whole publication years. Their
    labels are presentation text only; counts always come from the map.
    """
    if not isinstance(raw, list) or not raw:
        raise SystemExit("[statistics] periods must be a non-empty list of tables")
    out = []
    for spec in raw:
        if not isinstance(spec, dict):
            raise SystemExit("[statistics] periods must contain tables")
        label, start, end = spec.get("label"), spec.get("start"), spec.get("end")
        whole = all(isinstance(v, int) and not isinstance(v, bool) for v in (start, end))
        if not isinstance(label, str) or not label.strip() or not whole or start > end:
            raise SystemExit("[statistics] each period needs a label and whole start <= end")
        if out and start <= out[-1][2]:
            raise SystemExit("[statistics] periods must be ordered and must not overlap")
        out.append((label.strip(), start, end))
    return out


def period_rows(axes, the_map, records, periods, names):
    """Rows of map codes by publication period, from the map and its schema.

    A list axis counts a record under every code it holds. Every map record must have a
    publication year in exactly one pre-specified period.
    """
    known = {a.name: a for a in axes}
    unknown = [name for name in names if name not in known]
    if unknown:
        raise SystemExit("[statistics] period_axes names no axis of the schema: %s"
                         % ", ".join(unknown))
    axes = [known[name] for name in names]
    assigned = {}
    for number in the_map:
        year = records[number].year
        matches = [label for label, start, end in periods
                   if year is not None and start <= year <= end]
        if len(matches) != 1:
            raise SystemExit("map record %d has year %r, outside [statistics] periods"
                             % (number, year))
        assigned[number] = matches[0]

    rows = []
    for label, start, end in periods:
        numbers = [n for n in the_map if assigned[n] == label]
        for axis in axes:
            for code in axis.codes + (mc.NOT_STATED,):
                count = sum(1 for n in numbers if mc.has(axis, the_map[n][axis.name], code))
                rows.append({
                    "period": label, "start_year": start, "end_year": end,
                    "records": len(numbers), "axis": axis.name, "code": code,
                    "count": count, "percent": share(count, len(numbers)),
                    "multi": "yes" if axis.multi else "no",
                })
    return rows


def render_periods(config, rows):
    """Markdown rendering of the map-by-period CSV."""
    lines = [
        "# The map by publication period", "",
        "Written by `runners/core_statistics.py` from `%s`; do not edit, rerun the runner."
        % rel(config), "",
        "Counts and shares use each period's map records as their denominator. On a list axis, "
        "a record counts under every code it holds, so an axis's shares need not sum to 100%.",
        "",
        "| Period | Records | Axis | Code | Count | % | List axis |",
        "|---|---:|---|---|---:|---:|:---:|",
    ]
    for row in rows:
        lines.append("| %(period)s | %(records)s | `%(axis)s` | %(code)s | %(count)s | "
                     "%(percent)s | %(multi)s |" % row)
    return "\n".join(lines) + "\n"


def tex_escape(text):
    """The small subset of TeX escaping needed by generated labels and codes."""
    return str(text).replace("\\", r"\textbackslash{}").replace("_", r"\_").replace(
        "&", r"\&").replace("%", r"\%").replace("#", r"\#")


def render_periods_tex(rows):
    """A compact generated table for the supplement."""
    lines = [
        r"\begin{longtable}{lllr@{\hspace{1.0em}}r}",
        r"\caption{The map's codes by pre-specified publication period. "
        r"Shares on list axes need not sum to 100\%.}",
        r"\label{tab:map-by-period}\\",
        r"\toprule",
        r"Period & Axis & Code & Count & \% \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Period & Axis & Code & Count & \% \\",
        r"\midrule",
        r"\endhead",
    ]
    prior = (None, None)
    for row in rows:
        key = (row["period"], row["axis"])
        period = tex_escape(row["period"]) if row["period"] != prior[0] else ""
        axis = r"\texttt{%s}" % tex_escape(row["axis"]) if key != prior else ""
        lines.append("%s & %s & %s & %s & %s \\\\" % (
            period, axis, tex_escape(row["code"]), row["count"], row["percent"]))
        prior = key
    lines += [r"\bottomrule", r"\end{longtable}", ""]
    return "\n".join(lines)


def median(values):
    """The middle value, or the mean of the two middle values, as a Fraction; 0 for none."""
    s = sorted(values)
    k = len(s)
    return Fraction(s[(k - 1) // 2] + s[k // 2], 2) if k else Fraction(0)


def render(config, sets, rows, records, stated=()):
    sizes = {key: len(numbers) for key, _, _, numbers in sets}
    lines = [
        "# The map, the candidates and the core: counts", "",
        "Written by `runners/core_statistics.py` from `%s`; do not edit, rerun the runner."
        % rel(config), "",
        "Three sets, each row with its count and its share of the set's own records: the map, "
        "every included record (%d); the candidates, the map's records whose learner is stated, "
        "each study once, from which the core is drawn (%d); and the core, the studies read in "
        "full (%d), the core locked in `results/core/core-lock.json`. The three tables have "
        "the same rows. Years and citations are the records' at the search snapshot "
        "(`datasets/references.json`). On a list axis a record counts under each code it "
        "holds, so the shares of one axis can add up to more than 100. The venue's country is "
        "the one SJR gives it (`datasets/venue-bands.csv`); `%s` is a venue SJR does not list, "
        "or no venue." % (sizes["map"], sizes["candidates"], sizes["core"], NOT_IN_SJR)]
    if stated:
        lines[-1] += (" The codes of %s are given again over the set's records that state one, "
                      "their share stating none being the axis's own `not-stated` row "
                      "(protocol, Synthesis)."
                      % ", ".join("`%s`" % name for name in stated))
    for key, heading, member, numbers in sets:
        cited = [records[n].cited_by_count or 0 for n in numbers]
        lines += ["", "## %s (%d %s)" % (heading, len(numbers), member), "",
                  "Citations at the snapshot: median %s, mean %s." % (
                      one_decimal(median(cited)),
                      one_decimal(Fraction(sum(cited), len(cited)) if cited else 0)), ""]
        shown, body = None, []
        for group, label, item, count, share in rows[key]:
            body.append((label if label != shown else "", item, count, share))
            shown = label
        lines += table([("Group", False), ("Item", False), ("Count", True), ("%", True)], body)
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "core.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")
    args = parser.parse_args()
    cfg = load_config(args.config, args.override)
    inputs, outputs = cfg["inputs"], cfg["outputs"]
    bins = citation_bins(cfg["statistics"]["citation_bins"])

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
    _, _, _, kept = candidates(the_map, records,
                               bool(cfg["selection"]["title_needs_first_author"]))
    core = read_core(resolve(outputs["core"]), resolve(outputs["lock"]), kept,
                     {key: resolve(inputs[key]) for key in ("map", "references", "venue_bands")})

    stated = list(cfg["statistics"].get("stated_axes", []))
    groups = groups_of(axes, the_map, records, bands, bins, stated)
    numbers = {"map": sorted(the_map), "candidates": kept, "core": core}
    sets = [(key, heading, member, numbers[key]) for key, heading, member in SETS]
    rows = {key: count_rows(numbers[key], groups) for key, _, _ in SETS}

    write_csv(resolve(outputs["statistics_table"]), FIELDS, [
        {"set": key, "group": group, "item": item, "count": count, "percent": share}
        for key, _, _ in SETS for group, _, item, count, share in rows[key]])
    periods = period_specs(cfg["statistics"].get("periods"))
    period_table = period_rows(
        axes, the_map, records, periods, list(cfg["statistics"].get("period_axes") or []))
    write_csv(resolve(outputs["period_table"]), PERIOD_FIELDS, period_table)
    period_report = resolve(outputs["period_statistics"])
    period_tex = resolve(outputs["period_tex"])
    os.makedirs(os.path.dirname(period_report), exist_ok=True)
    with open(period_report, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_periods(args.config, period_table))
    with open(period_tex, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_periods_tex(period_table))
    report = resolve(outputs["statistics"])
    os.makedirs(os.path.dirname(report), exist_ok=True)
    with open(report, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(args.config, sets, rows, records, stated))

    print("sets              : map %d, candidates %d, core %d"
          % (len(numbers["map"]), len(numbers["candidates"]), len(numbers["core"])))
    print("rows per table    : %d" % len(rows["map"]))
    print("written           : %s, %s" % (rel(report), rel(resolve(outputs["statistics_table"]))))
    print("map by period     : %s, %s, %s" % (
        rel(resolve(outputs["period_table"])), rel(period_report), rel(period_tex)))


if __name__ == "__main__":
    main()
