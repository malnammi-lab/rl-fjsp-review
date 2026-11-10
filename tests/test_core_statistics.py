"""Tests for the statistics runner (runners/core_statistics.py): the citation bins, a list
axis's counting, the three tables of the small map of tests/test_core_selection.py worked out
by hand, and the cores it refuses."""

import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import mapcodes as mc  # noqa: E402
import core_selection as cs  # noqa: E402
import core_statistics as st  # noqa: E402
from screening_setup import read_csv, write_csv  # noqa: E402
from test_core_selection import build, run as run_selection  # noqa: E402

SETS = ("map", "candidates", "core")
BINS = ("0", "1 to 4", "5 to 9", "10 to 24", "25 to 49", "50 to 99", "100 or more")


def run(config, monkeypatch):
    monkeypatch.setattr("sys.argv", ["core_statistics", "--config", config])
    st.main()


def counts(rows, which, group):
    """{item: (count, percent)} of one set's group in the statistics' CSV."""
    return {r["item"]: (int(r["count"]), r["percent"]) for r in rows
            if r["set"] == which and r["group"] == group}


def test_shares_and_means_round_a_half_up_exactly():
    # 44.55 is 44.54999... in binary floating point, which "%.1f" prints as 44.5.
    assert st.one_decimal(st.Fraction(4455, 100)) == "44.6"
    assert st.one_decimal(3) == "3.0" and st.one_decimal(st.Fraction(11, 2)) == "5.5"
    assert st.share(1, 8) == "12.5" and st.share(1, 400) == "0.3" and st.share(0, 0) == ""
    assert st.median([1, 3, 4, 9]) == st.Fraction(7, 2) and st.median([]) == 0


def test_citation_bins_and_their_labels():
    assert [label for label, _, _ in st.citation_bins([0, 1, 5, 10, 25, 50, 100])] == list(BINS)
    assert st.citation_bins([0, 10]) == [("0 to 9", 0, 9), ("10 or more", 10, None)]
    for bad in ([], [1, 5], [0, 5, 5], [0, 2.5]):
        with pytest.raises(SystemExit, match="citation_bins"):
            st.citation_bins(bad)


def test_periods_are_ordered_disjoint_and_bounded():
    assert st.period_specs([
        {"label": "early", "start": 2011, "end": 2022},
        {"label": "recent", "start": 2023, "end": 2026},
    ]) == [("early", 2011, 2022), ("recent", 2023, 2026)]
    for bad in ([], [{"label": "", "start": 2011, "end": 2022}],
                [{"label": "backward", "start": 2022, "end": 2011}],
                [{"label": "one", "start": 2011, "end": 2022},
                 {"label": "overlap", "start": 2022, "end": 2026}]):
        with pytest.raises(SystemExit, match="period"):
            st.period_specs(bad)


def test_a_list_axis_counts_a_record_under_each_of_its_codes():
    axes = [a for a in mc.load_axes(os.path.join(REPO, "configs", "map.toml"))
            if a.name == "coordination"]
    the_map = {1: {"coordination": ("multi-agent", "hierarchical")},
               2: {"coordination": ("single-agent",)}}
    [(label, items)] = st.code_items(axes, the_map)
    rows = st.count_rows([1, 2], [("coordination", label, items)])
    assert [(item, count, share) for _, _, item, count, share in rows] == [
        ("single-agent", 1, "50.0"), ("multi-agent", 1, "50.0"), ("hierarchical", 1, "50.0"),
        ("not-stated", 0, "0.0")]


def test_period_table_counts_a_list_axis_under_each_code():
    axes = [a for a in mc.load_axes(os.path.join(REPO, "configs", "map.toml"))
            if a.name == "coordination"]
    the_map = {1: {"coordination": ("multi-agent", "hierarchical")},
               2: {"coordination": ("single-agent",)}}
    records = {
        1: st.corpus.Record.from_flat({"number": 1, "year": 2022}),
        2: st.corpus.Record.from_flat({"number": 2, "year": 2024}),
    }
    rows = st.period_rows(axes, the_map, records,
                          [("early", 2011, 2022), ("recent", 2023, 2026)],
                          ["coordination"])
    early = {r["code"]: (r["count"], r["percent"]) for r in rows
             if r["period"] == "early"}
    assert early == {
        "single-agent": (0, "0.0"), "multi-agent": (1, "100.0"),
        "hierarchical": (1, "100.0"), "not-stated": (0, "0.0")}
    assert sum(float(percent) for _, percent in early.values()) == 200.0
    with pytest.raises(SystemExit, match="outside.*periods"):
        st.period_rows(axes, the_map, {1: records[1], 2: st.corpus.Record.from_flat(
            {"number": 2, "year": 2030})},
            [("early", 2011, 2022), ("recent", 2023, 2026)], ["coordination"])


def test_an_axis_is_given_again_over_the_records_that_state_a_code():
    axes = [a for a in mc.load_axes(os.path.join(REPO, "configs", "map.toml"))
            if a.name == "policy_role"]
    the_map = {1: {"policy_role": "end-to-end"}, 2: {"policy_role": "steering-rules"},
               3: {"policy_role": "not-stated"}, 4: {"policy_role": "end-to-end"}}
    [group] = st.stated_items(axes, the_map, ["policy_role"])
    got = {item: (count, share) for _, _, item, count, share in st.count_rows([1, 2, 3, 4],
                                                                              [group])}
    # Three of the four state a role: two end to end (66.7%), one choosing rules (33.3%).
    assert got["end-to-end"] == (2, "66.7") and got["steering-rules"] == (1, "33.3")
    assert got["steering-heuristic"] == (0, "0.0") and "not-stated" not in got
    with pytest.raises(SystemExit, match="stated_axes"):
        st.stated_items(axes, the_map, ["no-such-axis"])


def test_the_three_tables_of_the_small_map(tmp_path, monkeypatch):
    config = build(tmp_path)
    run_selection(config, monkeypatch)
    run(config, monkeypatch)
    rows = read_csv(os.path.join(tmp_path, "results", "core", "core-statistics.csv"))
    # The map's 24 records; the 22 candidates (8 counted with 7, 24 without a stated
    # learner); the core's 14 studies.
    assert {s: sum(c for c, _ in counts(rows, s, "year").values()) for s in SETS} == {
        "map": 24, "candidates": 22, "core": 14}
    assert counts(rows, "map", "year") == {
        "2023": (4, "16.7"), "2024": (9, "37.5"), "2025": (8, "33.3"), "2026": (3, "12.5")}
    assert counts(rows, "candidates", "year") == {
        "2023": (4, "18.2"), "2024": (7, "31.8"), "2025": (8, "36.4"), "2026": (3, "13.6")}
    assert counts(rows, "core", "year") == {
        "2023": (3, "21.4"), "2024": (4, "28.6"), "2025": (5, "35.7"), "2026": (2, "14.3")}
    assert [counts(rows, "map", "citations")[b][0] for b in BINS] == [4, 7, 5, 3, 4, 1, 0]
    assert [counts(rows, s, "learner_depth")["not-stated"][0] for s in SETS] == [1, 0, 0]
    assert counts(rows, "core", "policy_role")["end-to-end"] == (5, "35.7")
    # The roles again over the records that state one: they count every record but those
    # whose role is not stated.
    for s, size in (("map", 24), ("candidates", 22), ("core", 14)):
        stated = counts(rows, s, "policy_role_stated")
        assert "not-stated" not in stated
        assert sum(c for c, _ in stated.values()) == size - counts(rows, s, "policy_role")[
            "not-stated"][0]
    assert counts(rows, "core", "venue_country") == {
        "United Kingdom": (11, "78.6"), "not in SJR": (3, "21.4")}
    order = {s: [(r["group"], r["item"]) for r in rows if r["set"] == s] for s in SETS}
    assert order["map"] == order["candidates"] == order["core"]
    with open(os.path.join(tmp_path, "results", "core", "core-statistics.md"),
              encoding="utf-8") as fh:
        report = fh.read()
    assert "## The map (24 records)" in report and "## The core (14 studies)" in report
    # The map's 24 citation counts add to 271; the candidates' 22 to 269 (8 and 24 out); the
    # core's 14 to 185.
    sections = report.split("\n## ")
    assert "Citations at the snapshot: median 5.5, mean 11.3." in sections[1]
    assert "Citations at the snapshot: median 6.5, mean 12.2." in sections[2]
    assert "Citations at the snapshot: median 7.5, mean 13.2." in sections[3]
    assert "| Year | 2023 | 4 | 16.7 |" in report and "|  | 2024 | 9 | 37.5 |" in report
    # No core study is uncited (4, 14, 18 and 24 are not in it).
    assert [counts(rows, "core", "citations")[b][0] for b in BINS] == [0, 4, 5, 2, 2, 1, 0]
    period_rows = read_csv(os.path.join(tmp_path, "results", "core", "map-by-period.csv"))
    periods = {r["period"]: int(r["records"]) for r in period_rows}
    assert periods == {"2011--2022": 0, "2023--2024": 13, "2025--2026": 11}
    assert os.path.isfile(os.path.join(tmp_path, "results", "core", "map-by-period.md"))
    assert os.path.isfile(os.path.join(tmp_path, "results", "core", "map-by-period.tex"))


def test_counts_of_data_other_than_the_core_was_drawn_from_are_refused(tmp_path, monkeypatch):
    config = build(tmp_path)
    run_selection(config, monkeypatch)
    path = os.path.join(tmp_path, "datasets", "references.json")
    with open(path, encoding="utf-8") as fh:
        refs = json.load(fh)
    refs["references"][0]["cited_by_count"] += 1
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(refs, fh)
    with pytest.raises(SystemExit, match="changed since the core was locked"):
        run(config, monkeypatch)


def test_a_core_other_than_the_locked_one_is_refused(tmp_path, monkeypatch):
    config = build(tmp_path)
    run_selection(config, monkeypatch)
    core_path = os.path.join(tmp_path, "datasets", "core.csv")
    lock_path = os.path.join(tmp_path, "results", "core", "core-lock.json")
    rows = read_csv(core_path)
    fields = list(rows[0])
    write_csv(core_path, fields, [dict(r, step="2") if r["number"] == "5" else r for r in rows])
    with pytest.raises(SystemExit, match="is not the core locked"):
        run(config, monkeypatch)
    # Record 24, not a candidate, added, with a lock made to match.
    added = rows + [dict(rows[0], number="24", step="3")]
    write_csv(core_path, fields, added)
    with open(lock_path, encoding="utf-8") as fh:
        lock = json.load(fh)
    lock["core_sha256"] = cs.core_digest([(int(r["number"]), r["step"]) for r in added])
    with open(lock_path, "w", encoding="utf-8") as fh:
        json.dump(lock, fh)
    with pytest.raises(SystemExit, match="not candidates: 24"):
        run(config, monkeypatch)
    os.remove(lock_path)
    with pytest.raises(SystemExit, match="core's lock"):
        run(config, monkeypatch)
