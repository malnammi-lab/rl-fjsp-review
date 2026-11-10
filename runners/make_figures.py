"""Draw the paper's figures from the runners' tables, and the supplement's list of core studies.

    python runners/run_all.py --only make-figures

Reads datasets/coded-studies.csv, datasets/references.json and the tables of [inputs]. A code
that [codes] does not list stops the run. Writes each figure under results/figures/ as PNG and
PDF, with a CSV of the values plotted, and the core-study table under results/tables/.
"""

import argparse
import csv
import math
import os
import sys
import textwrap
import tomllib
from collections import defaultdict
from fractions import Fraction

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus  # noqa: E402


def resolve(path):
    return os.path.normpath(os.path.join(REPO, path))


def rel(path):
    """Repo-relative path for printing; absolute when the path is on another drive.

    os.path.relpath raises on Windows when the two paths sit on different drives, and
    a runner must not crash on a progress line after its real work has succeeded.
    """
    try:
        return os.path.relpath(path, REPO)
    except ValueError:
        return path


def values(row, column, multi):
    raw = (row.get(column) or "").strip()
    if not raw:
        return []
    parts = raw.split("|") if column in multi else [raw]
    return [p.strip() for p in parts if p.strip()]


def load_coded(path, codes, multi):
    """Read the coded CSV and refuse any code the scheme does not define."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for i, row in enumerate(rows, 2):  # line numbers, header is line 1
        for column, allowed in codes.items():
            for v in values(row, column, multi):
                if v not in allowed:
                    raise SystemExit(
                        "coded-studies.csv line %d: %r is not a recognised %s code. "
                        "See datasets/coding-scheme.md." % (i, v, column)
                    )
        try:
            row["number"] = int(row["number"])
        except (KeyError, ValueError):
            raise SystemExit("coded-studies.csv line %d: missing or non-integer number" % i)
    return rows


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def read_csv(path):
    """Rows of a runner-written CSV, with its byte-order mark tolerated."""
    if not os.path.isfile(path):
        raise SystemExit("figure input not found: %s" % path)
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def one_decimal(value):
    """A percentage to one decimal, using the synthesis's half-up convention."""
    tenths = math.floor(Fraction(value) * 10 + Fraction(1, 2))
    return "%d.%d" % (tenths // 10, tenths % 10)


WIDTHS = {"column": "column_width_in", "text": "text_width_in"}
NO_CONTENT = ("other-codes",)


def figure_size(style, fig_cfg):
    """The figure's size in inches: the printed width it names in [style], and its height."""
    width = fig_cfg.get("width", "column")
    if width not in WIDTHS:
        raise SystemExit("figure %s: width must be column or text, not %r"
                         % (fig_cfg.get("name"), width))
    if "height_in" not in fig_cfg:
        raise SystemExit("figure %s has no height_in" % fig_cfg.get("name"))
    return float(style[WIDTHS[width]]), float(fig_cfg["height_in"])


def plotting(style):
    """Matplotlib and Seaborn, with the theme of [style] applied; or a named message when
    either is missing."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("%s is not installed; create the environment from repo_env.yml"
                         % exc.name)
    try:
        import seaborn as sns
    except ImportError as exc:
        raise SystemExit("%s is not installed; create the environment from repo_env.yml"
                         % exc.name)
    sns.set_theme(context=style["context"], style=style["style"], palette=style["palette"],
                  font=style["font"], font_scale=float(style["font_scale"]),
                  rc=dict(style.get("rc") or {}))
    return plt, sns


def code_colors(sns, cfg):
    """The color rule of [colors] over the Seaborn palette of [style]: the fixed roles, each
    listed axis's codes in order (the grey left out), the grey, the light grey, and the color
    of a figure of one series."""
    spec = cfg.get("colors") or {}
    base = sns.color_palette(cfg["style"]["palette"]).as_hex()
    grey = int(spec.get("grey", 7))
    free = [c for i, c in enumerate(base) if i != grey]
    axes = {}
    for axis, codes in (spec.get("axes") or {}).items():
        if len(codes) > len(free):
            raise SystemExit("[colors.axes] %s lists %d codes; the palette has %d colors"
                             % (axis, len(codes), len(free)))
        axes[axis] = {code: free[i] for i, code in enumerate(codes)}
    return {"base": base, "free": free, "grey": base[grey],
            "light": spec.get("light", "#D4D4D4"),
            "single": base[int(spec.get("single", 0))],
            "fixed": {code: base[int(i)] for code, i in (spec.get("fixed") or {}).items()},
            "axes": axes}


def panel_palette(sns, colors, axis, codes):
    """{code: color} for the codes one panel draws on `axis`; a code with no color is a
    named failure, so a code never takes an arbitrary color."""
    out = {}
    for code in codes:
        if code == "not-stated":
            out[code] = colors["grey"]
        elif code in NO_CONTENT:
            out[code] = colors["light"]
        elif code in colors["fixed"]:
            out[code] = colors["fixed"][code]
        elif code in colors["axes"].get(axis, {}):
            out[code] = colors["axes"][axis][code]
        else:
            raise SystemExit("no color for %s on %s: list it in configs/figures.toml [colors]"
                             % (code, axis))
    return out


class Drawing:
    """What every figure function draws with: Matplotlib, Seaborn, [style] and the colors."""

    def __init__(self, plt, sns, style, colors):
        self.plt, self.sns, self.style, self.colors = plt, sns, style, colors

    def figure(self, fig_cfg, nrows=1, ncols=1):
        """A figure at its printed size, laid out by constrained layout; `width_ratios` in
        the figure's config sets the panels' relative widths."""
        ratios = fig_cfg.get("width_ratios")
        if ratios is not None and len(ratios) != ncols:
            raise SystemExit("figure %s: width_ratios has %d values for %d panels"
                             % (fig_cfg.get("name"), len(ratios), ncols))
        return self.plt.subplots(nrows, ncols, figsize=figure_size(self.style, fig_cfg),
                                 layout="constrained", width_ratios=ratios)

    def palette(self, axis, codes):
        return panel_palette(self.sns, self.colors, axis, codes)

    def grid(self, ax, axis):
        """A light grid on the value axis, behind the data."""
        ax.grid(axis=axis, color=self.style.get("grid_color", "0.88"), linewidth=0.6)
        ax.set_axisbelow(True)

    def save(self, fig, base):
        """PNG and PDF at the figure's own size: no tight bounding box, so the PDF is exactly
        as wide as it prints."""
        fig.savefig(base + ".png", dpi=int(self.style.get("dpi", 300)))
        fig.savefig(base + ".pdf")
        self.plt.close(fig)


def frame():
    """pandas, imported only when a figure is drawn."""
    import pandas as pd
    return pd


def legend_name(code):
    """The legend text. The sidecar keeps the code `other-codes`."""
    return "Others" if code == "other-codes" else code


def take_legend(ax):
    """The handles and labels of the legend Seaborn drew on `ax`, which is then removed."""
    legend = ax.get_legend()
    if legend is None:
        return [], []
    handles = list(legend.legend_handles)
    labels = [t.get_text() for t in legend.get_texts()]
    legend.remove()
    return handles, labels


def legend_below_axes(ax, handles, labels, offset_in, ncol=1):
    """A legend under one panel, starting `offset_in` inches below its axes (below the tick
    labels), so constrained layout makes room for it and the panels of a row keep one height."""
    if not handles:
        return
    from matplotlib.transforms import ScaledTranslation
    place = ax.transAxes + ScaledTranslation(0, -float(offset_in), ax.figure.dpi_scale_trans)
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0),
              bbox_transform=place, ncol=ncol, title=None, frameon=False, handlelength=1.2)


def legend_below_figure(fig, handles, labels, ncol):
    """One legend for the whole figure, under its panels."""
    if handles:
        fig.legend(handles, labels, loc="outside lower center", ncol=min(ncol, len(labels)),
                   title=None, frameon=False)


def select_row(rows, field, code, source):
    """One row identified by the synthesis table's field and code."""
    found = [r for r in rows if r.get("field") == field and r.get("code") == code]
    if len(found) != 1:
        raise SystemExit("%s needs one row %s/%s, found %d"
                         % (source, field, code, len(found)))
    return found[0]


def grouped_period_rows(rows, fig_cfg):
    """The exact values plotted in the map-by-period figure."""
    axes = list(fig_cfg["axes"])
    singles = set(fig_cfg.get("single_axes") or [])
    others = {axis: set(codes) for axis, codes in (fig_cfg.get("others") or {}).items()}
    threshold = fig_cfg.get("small_share")
    limit = None if threshold is None else Fraction(threshold)
    out = []
    for axis in axes:
        axis_rows = [r for r in rows if r.get("axis") == axis]
        if not axis_rows:
            raise SystemExit("map-by-period.csv has no axis %s" % axis)
        periods = []
        for row in axis_rows:
            if row["period"] not in periods:
                periods.append(row["period"])
        by_period = []
        for period in periods:
            period_rows = [r for r in axis_rows if r["period"] == period]
            grouped = defaultdict(lambda: {"count": 0, "percent": Fraction(0)})
            for row in period_rows:
                code = "other-codes" if row["code"] in others.get(axis, set()) else row["code"]
                grouped[code]["count"] += int(row["count"])
                grouped[code]["percent"] += Fraction(row["percent"])
            by_period.append((period, int(period_rows[0]["records"]), grouped))
        if limit is not None:
            codes = []
            for _, _, grouped in by_period:
                for code in grouped:
                    if code not in codes:
                        codes.append(code)
            small = []
            for code in codes:
                if code in ("not-stated", "other-codes"):
                    continue
                shares = [grouped[code]["percent"] if code in grouped else Fraction(0)
                          for _, _, grouped in by_period]
                if shares and all(share < limit for share in shares):
                    small.append(code)
            if small:
                for _, _, grouped in by_period:
                    bucket = grouped["other-codes"]
                    for code in small:
                        if code not in grouped:
                            continue
                        moved = grouped.pop(code)
                        bucket["count"] += moved["count"]
                        bucket["percent"] += moved["percent"]
        kind = "single" if axis in singles else "multi"
        for period, records, grouped in by_period:
            for code, value in grouped.items():
                out.append({
                    "axis": axis, "period": period, "records": records, "code": code,
                    "count": value["count"], "percent": one_decimal(value["percent"]),
                    "kind": kind,
                })
    return out


def period_label(period, records=None):
    """A plot tick. The source period keeps its LaTeX dashes; the tick uses an en dash."""
    shown = str(period).replace("--", "\u2013")
    if records is None:
        return shown
    return "%s\n(n=%d)" % (shown, int(records))


def period_tick(period, records):
    """A short tick for a narrow panel: the end year to two digits ("2011-22", with an en
    dash) over the period's record count. The sidecar keeps the period as the table gives it."""
    start, _, end = str(period).partition("--")
    if len(start) == 4 and len(end) == 4 and start[:2] == end[:2]:
        shown = "%s%s%s" % (start, chr(0x2013), end[2:])
    else:
        shown = period_label(period)
    return "%s\n(n=%d)" % (shown, int(records))


def map_year_rows(rows):
    """The map's records per year from core-statistics.csv."""
    selected = [r for r in rows if r.get("set") == "map" and r.get("group") == "year"]
    if not selected:
        raise SystemExit("core-statistics.csv has no map/year rows")
    return [{"axis": "records-per-year", "period": r["item"], "records": int(r["count"]),
             "code": "map-records", "count": int(r["count"]), "percent": "", "kind": "year"}
            for r in selected]


def panel_title(axis):
    """A panel's title: the axis in words, first letter capital."""
    words = axis.replace("_", " ")
    return words[:1].upper() + words[1:]


def figure_map_periods(d, rows, year_rows, fig_cfg, out_base):
    """The map's annual output and its configured code panels in one row, time running left
    to right. A single-code axis is a 100% stack per period (Seaborn's histplot weighted by
    the shares); a list axis is one line per code."""
    data = map_year_rows(year_rows) + grouped_period_rows(rows, fig_cfg)
    axes = ["records-per-year"] + list(fig_cfg["axes"])
    write_csv(out_base + ".csv",
              ["axis", "period", "records", "code", "count", "percent", "kind"],
              [[r[k] for k in ("axis", "period", "records", "code", "count", "percent", "kind")]
               for r in data])
    fig, axs = d.figure(fig_cfg, 1, len(axes))
    axs = list(getattr(axs, "flat", [axs]))
    pd = frame()
    offset = fig_cfg.get("legend_offset_in", 0.4)
    for ax, axis in zip(axs, axes):
        panel = [r for r in data if r["axis"] == axis]
        if not panel:
            raise SystemExit("the map figure has no rows for %s" % axis)
        periods = list(dict.fromkeys(r["period"] for r in panel))
        codes = list(dict.fromkeys(r["code"] for r in panel))
        if panel[0]["kind"] == "year":
            labels = [r["period"] + ("*" if r["period"] == fig_cfg["partial_year"] else "")
                      for r in panel]
            d.sns.barplot(saturation=1, data=pd.DataFrame({"year": labels,
                                             "records": [r["count"] for r in panel]}),
                          x="year", y="records", order=labels, color=d.colors["single"], ax=ax)
            ax.set_ylabel("Map records")
            ax.set_xlabel("Publication year (* partial)")
            ax.tick_params(axis="x", rotation=90)
            ax.set_title("Records per year")
            d.grid(ax, "y")
            continue
        names = [legend_name(code) for code in codes]
        colors = {legend_name(code): c for code, c in d.palette(axis, codes).items()}
        records = {p: next(r["records"] for r in panel if r["period"] == p) for p in periods}
        ticks = [period_tick(p, records[p]) for p in periods]
        plotted = pd.DataFrame(panel)
        plotted["percent"] = plotted["percent"].astype(float)
        plotted["series"] = plotted["code"].map(legend_name)
        if panel[0]["kind"] == "single":
            plotted["tick"] = plotted["period"].map(dict(zip(periods, ticks)))
            d.sns.histplot(data=plotted, x="tick", weights="percent", hue="series",
                           hue_order=names, multiple="stack", discrete=True, shrink=0.75,
                           palette=colors, edgecolor="white", linewidth=0.5, alpha=1, ax=ax)
            ax.set_xlim(-0.4, len(periods) - 0.6)  # the line panels' spacing of the ticks
            ax.set_ylim(0, 100)
        else:
            plotted["x"] = plotted["period"].map({p: i for i, p in enumerate(periods)})
            d.sns.lineplot(data=plotted, x="x", y="percent", hue="series", hue_order=names,
                           palette=colors, marker="o", errorbar=None, ax=ax)
            ax.set_xticks(range(len(periods)), ticks)
            ax.set_xlim(-0.3, len(periods) - 0.7)
            ax.set_ylim(bottom=0)
        ax.set_ylabel("Share of records (%)")
        ax.set_xlabel("")
        ax.set_title(panel_title(axis))
        d.grid(ax, "y")
        handles, labels = take_legend(ax)
        legend_below_axes(ax, handles, labels, offset)
    d.save(fig, out_base)
    return len(data)


def readiness_rows(rows, fig_cfg):
    """The counts and shares plotted in the readiness figure."""
    out = []
    for level in fig_cfg["levels"]:
        found = [r for r in rows if r["field"] == "readiness_level" and r["code"] == level]
        row = found[0] if found else {}
        for role in fig_cfg["roles"]:
            out.append({"panel": "level", "measure": level, "role": role,
                        "value": row.get("n_%s" % role, "0")})
    for check in fig_cfg["checks"]:
        row = select_row(rows, check["field"], check["code"], "readiness")
        for role in fig_cfg["roles"]:
            out.append({"panel": "operational", "measure": check["label"], "role": role,
                        "value": row["pct_%s" % role]})
    return out


def figure_readiness(d, tables, fig_cfg, out_base):
    """Readiness levels (counts) above the operational checks (shares), one legend below."""
    data = readiness_rows(tables[fig_cfg["source"]], fig_cfg)
    write_csv(out_base + ".csv", ["panel", "measure", "role", "value"],
              [[r[k] for k in ("panel", "measure", "role", "value")] for r in data])
    pd = frame()
    plotted = pd.DataFrame(data)
    plotted["value"] = plotted["value"].astype(float)
    plotted["shown"] = plotted["measure"].map(
        lambda m: textwrap.fill(m, 12, break_long_words=False))
    roles = list(fig_cfg["roles"])
    fig, axs = d.figure(fig_cfg, 2, 1)
    handles, labels = [], []
    for ax, panel, ylabel, title in (
            (axs[0], "level", "Studies", "(a) Highest readiness level"),
            (axs[1], "operational", "Studies (%)", "(b) Operational evidence")):
        panel_rows = plotted[plotted["panel"] == panel]
        shown = list(dict.fromkeys(panel_rows["shown"]))
        d.sns.barplot(saturation=1, data=panel_rows, x="shown", y="value", order=shown,
                      hue="role", hue_order=roles, palette=d.palette("role", roles), ax=ax)
        ax.set_xlabel("")
        ax.set_ylabel(ylabel)
        ax.set_title(title, loc="left")
        d.grid(ax, "y")
        handles, labels = take_legend(ax)
    legend_below_figure(fig, handles, labels, ncol=2)
    d.save(fig, out_base)
    return len(data)


def tex_text(value):
    """Escape plain corpus metadata for a generated LaTeX table."""
    escaped = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
               "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}"}
    return "".join(escaped.get(char, char) for char in str(value or ""))


def write_core_studies(studies, records, csv_path, tex_path):
    """Write the supplement's core-study list from the synthesis list and corpus metadata."""
    by_number = {record.number: record for record in records}
    rows = []
    for study in studies:
        number = int(study["number"])
        if number not in by_number:
            raise SystemExit("studies-by-cell.csv names record %d absent from references.json"
                             % number)
        record = by_number[number]
        if not record.doi:
            raise SystemExit("core record %d has no DOI in references.json" % number)
        rows.append({
            "number": number, "key": study["key"], "first_author": record.first_author,
            "year": record.year, "cell": study["cell"], "doi": record.doi,
        })
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    write_csv(csv_path, ["number", "key", "first_author", "year", "cell", "doi"],
              [[r[k] for k in ("number", "key", "first_author", "year", "cell", "doi")]
               for r in rows])
    lines = [
        r"\begin{longtable}{r p{3.0cm} r p{4.2cm} p{4.6cm}}",
        r"\caption{The %d core studies, with their synthesis cell and DOI.}"
        % len(rows),
        r"\label{tab:core-studies}\\",
        r"\toprule",
        r"Record & First author & Year & Role and family & DOI \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Record & First author & Year & Role and family & DOI \\",
        r"\midrule",
        r"\endhead",
    ]
    for row in rows:
        lines.append(r"%d & %s & %s & %s & \url{https://doi.org/%s} \\" % (
            row["number"], tex_text(row["first_author"]), row["year"],
            tex_text(row["cell"]), row["doi"]))
    lines += [r"\bottomrule", r"\end{longtable}", ""]
    os.makedirs(os.path.dirname(tex_path), exist_ok=True)
    with open(tex_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "figures.toml"))
    args = parser.parse_args()
    with open(args.config, "rb") as fh:
        cfg = tomllib.load(fh)

    codes = cfg["codes"]
    multi = set(cfg.get("multi_label") or [])
    inputs = cfg["inputs"]
    out_dir = resolve(inputs["out_dir"])
    os.makedirs(out_dir, exist_ok=True)
    if not cfg.get("style"):
        raise SystemExit("configs/figures.toml has no [style] table")
    tables = {key: read_csv(resolve(path)) for key, path in inputs.items()
              if key.startswith("table_")}

    coded = load_coded(resolve(inputs["coded"]), codes, multi)

    refs_path = resolve(inputs["references"])
    if os.path.isfile(refs_path):
        references = corpus.load_references(refs_path)
        years = {r.number: r.year for r in references}
        missing = [r["number"] for r in coded if r["number"] not in years]
        if missing:
            raise SystemExit(
                "coded-studies.csv codes studies that are not in references.json: %s. "
                "A coded study must exist in the corpus." % missing[:10]
            )
    elif coded:
        raise SystemExit(
            "references.json not found at %s, while coded-studies.csv has %d rows; see "
            "datasets/MANIFEST.md." % (refs_path, len(coded))
        )
    else:
        references = []
        print("references.json not present and no studies coded: figures will be empty.")

    core_cfg = cfg.get("core_studies")
    if core_cfg:
        core_rows = write_core_studies(
            tables[core_cfg["source"]], references,
            resolve(core_cfg["csv"]), resolve(core_cfg["tex"]))
        print("core studies  : %d -> %s, %s" % (
            len(core_rows), rel(resolve(core_cfg["csv"])), rel(resolve(core_cfg["tex"]))))

    plt, sns = plotting(cfg["style"])
    d = Drawing(plt, sns, cfg["style"], code_colors(sns, cfg))
    print("coded studies: %d" % len(coded))
    for fig_cfg in cfg.get("figure", []):
        base = os.path.join(out_dir, fig_cfg["file"])
        kind = fig_cfg["kind"]
        if kind == "map-periods":
            figure_map_periods(d, tables[fig_cfg["source"]], tables[fig_cfg["year_source"]],
                               fig_cfg, base)
        elif kind == "readiness":
            figure_readiness(d, tables, fig_cfg, base)
        else:
            raise SystemExit("unknown figure kind %r for %s" % (kind, fig_cfg["name"]))
        width, height = figure_size(cfg["style"], fig_cfg)
        print("  %-22s %-13s %.2f x %.2f in  -> %s.{png,pdf,csv}"
              % (fig_cfg["name"], kind, width, height, rel(base)))


if __name__ == "__main__":
    main()
