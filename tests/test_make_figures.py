"""Tests for runners/make_figures.py: the exact values each plotting function receives
(list axes, absent readiness levels), the theme and colors of [style] and [colors], the
supplement's list of core studies, and every figure kind drawn at its printed width."""

import os
import re
import sys
import tomllib

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

import make_figures as mf  # noqa: E402
from src import corpus  # noqa: E402

CONFIG = os.path.join(REPO, "configs", "figures.toml")


def config():
    with open(CONFIG, "rb") as fh:
        return tomllib.load(fh)


@pytest.fixture(scope="module")
def drawing():
    cfg = config()
    plt, sns = mf.plotting(cfg["style"])
    return mf.Drawing(plt, sns, cfg["style"], mf.code_colors(sns, cfg))


def pdf_width_in(path):
    """The width of a one-page PDF, from its MediaBox, in inches."""
    with open(path, "rb") as fh:
        found = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", fh.read())
    assert found, "no MediaBox in %s" % path
    return float(found.group(1)) / 72.0


def figure_cfg(name):
    return dict(next(f for f in config()["figure"] if f["name"] == name))


def test_figure_config_names_every_new_source():
    cfg = config()
    kinds = {f["kind"] for f in cfg["figure"]}
    assert kinds == {"map-periods", "readiness"}
    # Every table input is read before any figure is drawn, so each must be one a figure or
    # the core-study list reads.
    tables = {key for key in cfg["inputs"] if key.startswith("table_")}
    used = {cfg["core_studies"]["source"]}
    for f in cfg["figure"]:
        used |= {f[k] for k in ("source", "year_source") if k in f}
    assert tables == used


def test_the_style_prints_at_the_widths_of_elsarticle_5p():
    style = config()["style"]
    # elsarticle 5p: textwidth 522 pt and columnsep 18 pt, so a column is 252 pt (TeX points).
    assert style["text_width_in"] == pytest.approx(522 / 72.27, abs=0.01)
    assert style["column_width_in"] == pytest.approx(252 / 72.27, abs=0.01)
    assert style["context"] == "paper" and style["palette"] == "colorblind"
    assert style["rc"]["pdf.fonttype"] == 42
    for fig_cfg in config()["figure"]:
        width, height = mf.figure_size(style, fig_cfg)
        assert width in (style["column_width_in"], style["text_width_in"]) and height > 0


def test_no_font_or_figure_size_is_written_in_the_runner():
    with open(os.path.join(REPO, "runners", "make_figures.py"), encoding="utf-8") as fh:
        source = fh.read()
    assert not re.search(r"fontsize\s*=", source)
    assert not re.search(r"labelsize\s*=", source)
    assert not re.search(r"figsize\s*=\s*\(", source)
    assert "bbox_inches" not in source


def test_every_plotted_code_has_a_color_and_the_roles_keep_theirs():
    import seaborn as sns
    cfg = config()
    colors = mf.code_colors(sns, cfg)
    base = sns.color_palette("colorblind").as_hex()
    assert colors["grey"] == base[7]
    for column, codes in cfg["codes"].items():
        palette = mf.panel_palette(sns, colors, column, codes)
        assert set(palette) == set(codes)
        assert palette.get("not-stated", colors["grey"]) == colors["grey"]
    # The roles keep one color on the full-text axis and on the map's axis.
    for code in ("end-to-end", "steering"):
        assert mf.panel_palette(sns, colors, "role", [code])[code] == colors["fixed"][code]
    assert (mf.panel_palette(sns, colors, "policy_role", ["end-to-end"])["end-to-end"]
            == mf.panel_palette(sns, colors, "role", ["end-to-end"])["end-to-end"])
    # Others is light grey; not-applicable and not-stated are told apart from it.
    arch = mf.panel_palette(sns, colors, "deep_architecture",
                            ["other-codes", "not-applicable", "not-stated"])
    assert len(set(arch.values())) == 3
    with pytest.raises(SystemExit, match="no color for"):
        mf.panel_palette(sns, colors, "deep_architecture", ["an-unlisted-code"])


def test_map_periods_keep_single_axis_shares_and_group_configured_list_codes():
    rows = [
        {"axis": "policy_role", "period": "early", "records": "2",
         "code": "end-to-end", "count": "1", "percent": "50.0"},
        {"axis": "policy_role", "period": "early", "records": "2",
         "code": "steering-rules", "count": "1", "percent": "50.0"},
        {"axis": "deep_architecture", "period": "early", "records": "2",
         "code": "graph-neural-network", "count": "1", "percent": "50.0"},
        {"axis": "deep_architecture", "period": "early", "records": "2",
         "code": "pointer-network", "count": "1", "percent": "50.0"},
        {"axis": "deep_architecture", "period": "early", "records": "2",
         "code": "other", "count": "1", "percent": "50.0"},
    ]
    got = mf.grouped_period_rows(rows, {
        "axes": ["policy_role", "deep_architecture"],
        "single_axes": ["policy_role"],
        "others": {"deep_architecture": ["pointer-network", "other"]},
    })
    role = [r for r in got if r["axis"] == "policy_role"]
    grouped = [r for r in got if r["code"] == "other-codes"]
    assert sum(float(r["percent"]) for r in role) == 100.0
    assert grouped == [{
        "axis": "deep_architecture", "period": "early", "records": 2,
        "code": "other-codes", "count": 2, "percent": "100.0", "kind": "multi"}]


def test_codes_under_two_percent_in_every_period_join_others_and_not_stated_stays():
    def row(period, code, percent):
        return {"axis": "deep_architecture", "period": period, "records": "100",
                "code": code, "count": "1", "percent": percent}
    rows = []
    for period, rare, seen, silent in (
            ("2011--2022", "1.0", "1.0", "0.0"),
            ("2023--2024", "1.5", "1.0", "0.0"),
            ("2025--2026", "0.5", "2.0", "0.0")):
        rows.extend([row(period, "rare", rare), row(period, "seen", seen),
                     row(period, "not-stated", silent), row(period, "kept", "10.0")])
    got = mf.grouped_period_rows(rows, {
        "axes": ["deep_architecture"], "small_share": 2})
    assert [r for r in got if r["code"] == "rare"] == []
    assert [r["percent"] for r in got if r["code"] == "other-codes"] == ["1.0", "1.5", "0.5"]
    assert [r["percent"] for r in got if r["code"] == "seen"] == ["1.0", "1.0", "2.0"]
    assert [r["percent"] for r in got if r["code"] == "not-stated"] == ["0.0", "0.0", "0.0"]
    assert mf.legend_name("other-codes") == "Others"
    assert mf.legend_name("not-stated") == "not-stated"


def test_map_year_panel_uses_only_the_map_year_rows():
    rows = [
        {"set": "map", "group": "year", "item": "2025", "count": "7"},
        {"set": "map", "group": "year", "item": "2026", "count": "3"},
        {"set": "core", "group": "year", "item": "2026", "count": "1"},
    ]
    assert mf.map_year_rows(rows) == [
        {"axis": "records-per-year", "period": "2025", "records": 7,
         "code": "map-records", "count": 7, "percent": "", "kind": "year"},
        {"axis": "records-per-year", "period": "2026", "records": 3,
         "code": "map-records", "count": 3, "percent": "", "kind": "year"},
    ]


def test_period_labels_use_an_en_dash_and_keep_source_order():
    assert mf.period_label("2011--2022") == "2011\u20132022"
    labeled = mf.period_label("2011--2022", 65)
    assert "--" not in labeled and labeled == "2011\u20132022\n(n=65)"
    periods = ["2011--2022", "2023--2024", "2025--2026"]
    assert [mf.period_label(period) for period in periods] == [
        "2011\u20132022", "2023\u20132024", "2025\u20132026"]


def test_the_map_config_drops_the_domain_panel():
    with open(os.path.join(REPO, "configs", "figures.toml"), "rb") as fh:
        cfg = tomllib.load(fh)
    mapped = next(fig for fig in cfg["figure"] if fig["kind"] == "map-periods")
    assert "domain" not in mapped["axes"]
    # Four panels: records per year, then these three axes.
    assert mapped["axes"] == ["policy_role", "training_algorithm_family", "deep_architecture"]


def test_readiness_rows_preserve_the_runner_values():
    readiness = [
        {"field": "readiness_level", "code": "L1",
         "n_end-to-end": "2", "n_steering": "1"},
        {"field": "decision_deadlines", "code": "tested",
         "pct_end-to-end": "10.0", "pct_steering": "20.0"},
    ]
    got = mf.readiness_rows(readiness, {
        "levels": ["L1", "L2"], "roles": ["end-to-end", "steering"],
        "checks": [{"label": "Deadline", "field": "decision_deadlines", "code": "tested"}],
    })
    assert got[0] == {"panel": "level", "measure": "L1", "role": "end-to-end", "value": "2"}
    assert got[2] == {"panel": "level", "measure": "L2", "role": "end-to-end", "value": "0"}
    assert got[-1] == {"panel": "operational", "measure": "Deadline",
                       "role": "steering", "value": "20.0"}


def test_core_study_table_takes_every_value_from_its_two_sources(tmp_path):
    studies = [{"number": "7", "key": "lee2026study",
                "cell": "end-to-end / policy-gradient"}]
    records = [corpus.Record.from_flat({
        "number": 7, "first_author": "Lee & Park", "year": 2026,
        "title": "A study", "doi": "10.1/a_b",
    })]
    csv_path = os.path.join(tmp_path, "core-studies.csv")
    tex_path = os.path.join(tmp_path, "core-studies.tex")
    rows = mf.write_core_studies(studies, records, csv_path, tex_path)
    assert rows[0]["doi"] == "10.1/a_b" and rows[0]["key"] == "lee2026study"
    with open(tex_path, encoding="utf-8") as fh:
        tex = fh.read()
    assert r"Lee \& Park" in tex and r"\url{https://doi.org/10.1/a_b}" in tex


# Every figure kind drawn on small rows, into a temporary folder: the PDF must be exactly as
# wide as the figure prints (no tight bounding box), so its fonts print at the theme's sizes.

PERIODS = ["2011--2022", "2023--2024", "2025--2026"]


def period_rows():
    shares = {
        "policy_role": {"end-to-end": 40, "steering-rules": 20, "steering-heuristic": 20,
                        "not-stated": 20},
        "training_algorithm_family": {"value-based": 50, "policy-gradient": 30,
                                      "actor-critic": 10, "other": 5, "not-stated": 20},
        "deep_architecture": {"fully-connected": 20, "convolutional": 1,
                              "graph-neural-network": 30, "attention-transformer": 10,
                              "pointer-network": 5, "other": 5, "not-applicable": 20,
                              "not-stated": 30},
    }
    return [{"axis": axis, "period": period, "records": "10", "code": code,
             "count": str(share // 10), "percent": "%.1f" % share}
            for axis, codes in shares.items() for period in PERIODS
            for code, share in codes.items()]


def check_width(drawing, fig_cfg, base):
    width, _ = mf.figure_size(drawing.style, fig_cfg)
    assert pdf_width_in(base + ".pdf") == pytest.approx(width, abs=1 / 72.0)
    assert os.path.isfile(base + ".png") and os.path.isfile(base + ".csv")


def test_the_map_figure_has_four_panels_at_text_width(drawing, tmp_path):
    fig_cfg = figure_cfg("map-trends")
    years = [{"set": "map", "group": "year", "item": "2025", "count": "7"},
             {"set": "map", "group": "year", "item": "2026", "count": "3"}]
    base = str(tmp_path / "map")
    mf.figure_map_periods(drawing, period_rows(), years, fig_cfg, base)
    check_width(drawing, fig_cfg, base)
    import csv
    with open(base + ".csv", encoding="utf-8") as fh:
        axes = list(dict.fromkeys(r["axis"] for r in csv.DictReader(fh)))
    assert axes == ["records-per-year"] + fig_cfg["axes"]


def test_the_readiness_figure_prints_at_its_width(drawing, tmp_path):
    ready_cfg = figure_cfg("readiness")
    ready = [{"field": "readiness_level", "code": level, "n_end-to-end": "2", "n_steering": "1"}
             for level in ready_cfg["levels"]]
    ready += [{"field": c["field"], "code": c["code"], "pct_end-to-end": "10.0",
               "pct_steering": "20.0"} for c in ready_cfg["checks"]]
    base = str(tmp_path / "readiness")
    mf.figure_readiness(drawing, {ready_cfg["source"]: ready}, ready_cfg, base)
    check_width(drawing, ready_cfg, base)


def test_map_panels_use_short_period_ticks_and_the_sidecar_keeps_the_period():
    assert mf.period_tick("2011--2022", 65) == "2011" + chr(0x2013) + "22\n(n=65)"
    assert mf.period_tick("2025--2026", 330) == "2025" + chr(0x2013) + "26\n(n=330)"
    # A period whose years differ in their century, or that is not a range, keeps its label.
    assert mf.period_tick("1999--2004", 3) == "1999" + chr(0x2013) + "2004\n(n=3)"
    assert mf.period_tick("2026", 7) == "2026\n(n=7)"


def test_the_map_panels_have_one_width_ratio_each():
    fig_cfg = figure_cfg("map-trends")
    assert len(fig_cfg["width_ratios"]) == 1 + len(fig_cfg["axes"])
