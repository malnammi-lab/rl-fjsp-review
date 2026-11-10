"""Tests for the core-selection runner (runners/core_selection.py): the core rule's pieces one
by one, then a whole run on a small map whose core was worked out by hand, its lock, and the
inputs it refuses."""

import json
import os
import sys
from collections import Counter
from fractions import Fraction

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import corpus  # noqa: E402
from src import mapcodes as mc  # noqa: E402
import core_selection as cs  # noqa: E402
from screening_setup import read_csv, write_csv  # noqa: E402
from test_map_vote import BASE  # noqa: E402

NAMES = [a.name for a in mc.load_axes(os.path.join(REPO, "configs", "map.toml"))]


def cand(number, stratum="s", deep=True, band="1", tier=1, year=2024, cites=0, cats=()):
    return cs.Cand(number, stratum, deep, band, tier, year, cites, frozenset(cats))


def test_largest_remainders_and_their_ties():
    assert cs.largest_remainders(10, {"a": 35, "b": 35, "c": 30}, ["a", "b", "c"]) == {
        "a": 4, "b": 3, "c": 3}
    assert cs.largest_remainders(5, {2024: 3, 2025: 3, 2026: 1}, [2024, 2025, 2026]) == {
        2024: 2, 2025: 2, 2026: 1}
    # Equal remainders and equal weights: the key listed first.
    assert cs.largest_remainders(1, {"x": 1, "y": 1}, ["y", "x"]) == {"x": 0, "y": 1}
    # Equal remainders, unequal weights: the larger weight.
    assert cs.largest_remainders(2, {"a": 1, "b": 3}, ["a", "b"]) == {"a": 0, "b": 2}
    assert cs.largest_remainders(0, {"x": 1}, ["x"]) == {"x": 0}
    assert cs.year_order([2025, None, 2023]) == [2023, 2025, None]


def test_a_stratum_over_its_share_takes_no_more_and_a_short_one_takes_all():
    places, order = {"a": 4, "b": 4, "c": 2}, ["a", "b", "c"]
    many = {"a": 50, "b": 50, "c": 50}
    assert cs.allocate(10, places, Counter(a=5, b=1), many, order) == {"a": 5, "b": 3, "c": 2}
    assert cs.allocate(10, places, Counter(), {"a": 1, "b": 50, "c": 50}, order) == {
        "a": 1, "b": 6, "c": 3}
    # The stratum over its share is settled first and takes none of the places c cannot fill.
    assert cs.allocate(10, places, Counter(a=5), {"a": 50, "b": 50, "c": 1}, order) == {
        "a": 5, "b": 4, "c": 1}
    # Settled the other way round, c's empty share would first be divided between a and b
    # (6 each), and a, no longer over, would take one of them.
    assert cs.allocate(12, {"a": 4, "b": 4, "c": 4}, Counter(a=5), {"a": 50, "b": 50, "c": 0},
                       order) == {"a": 5, "b": 7, "c": 0}


def test_records_of_one_study_count_once():
    rows = [
        (1, "Scheduling by policy", "Wen Song", "journal", 2022, "10.1/a"),
        (2, "Scheduling by Policy!", "Wan-Ze Li", "conference", 2025, "10.1/b"),
        (3, "Another paper", "Ann Lee", "conference", 2023, "10.1/c"),
        (4, "Another Paper", "Lee Ann", "journal", 2024, "10.1/d"),
        (5, "A first title", "Kim", "journal", 2023, "10.1/X"),
        (6, "A second title", "Kim", "journal", 2024, "10.1/x"),
    ]
    records = {n: corpus.Record.from_flat({
        "number": n, "title": t, "first_author": a, "source_type": s, "year": y, "doi": d,
        "openalex_id": "https://openalex.org/W%d" % n}) for n, t, a, s, y, d in rows}
    # 3 and 4 share a title and a first author (the journal version kept); 5 and 6 a DOI (the
    # later kept); 1 and 2 only a title.
    assert cs.duplicates(sorted(records), records) == ([(4, [3]), (6, [5])], [(1, 2)])
    assert cs.duplicates(sorted(records), records, title_needs_first_author=False) == (
        [(1, [2]), (4, [3]), (6, [5])], [])


def test_duplicates_by_openalex_work_and_the_lower_number_kept():
    rows = [(1, "Alpha", "Kim", "W1"), (2, "Beta", "Lee", "W1"), (3, "Gamma study", "", "W3"),
            (4, "Gamma Study", "Park", "W4")]
    records = {n: corpus.Record.from_flat({
        "number": n, "title": t, "first_author": a, "source_type": "journal", "year": 2024,
        "openalex_id": "https://openalex.org/" + w}) for n, t, a, w in rows}
    # 1 and 2 are one OpenAlex work of the same type and year, so the lower number is kept;
    # 3 names no first author, so its shared title does not make it one study with 4.
    assert cs.duplicates(sorted(records), records) == ([(1, [2])], [(3, 4)])


def test_standing_is_the_share_of_the_year_cited_more():
    cands = {1: cand(1, cites=10), 2: cand(2, cites=5), 3: cand(3, cites=5),
             4: cand(4, year=2025), 5: cand(5, year=None, cites=3)}
    assert cs.standings(cands) == {1: Fraction(0), 2: Fraction(1, 3), 3: Fraction(1, 3),
                                   4: Fraction(0), 5: Fraction(0)}


def test_coverage_fills_the_most_places_and_passes_over_non_deep_past_the_cap():
    xa, xb, yc, zd = ("x", "a"), ("x", "b"), ("y", "c"), ("z", "d")
    cands = {1: cand(1, tier=2, cats=(xa, xb, yc)), 2: cand(2, cats=(xa,)),
             3: cand(3, deep=False, cats=(xb, zd)), 4: cand(4, deep=False, cats=(xb, zd)),
             5: cand(5, cats=(yc,))}
    standing = cs.standings(cands)
    picks, owed = cs.coverage(cands, [], [xa, xb, yc, zd], 2, 1, standing)
    # 1 fills three places; 3 two, before the cap passes 4 over; zd is left one short.
    assert picks == [(1, 3), (3, 2), (2, 1), (5, 1)]
    assert owed == {xa: 2, xb: 2, yc: 2, zd: 2}
    assert cs.category_status(zd, 2, 2, 1, 2) == "short by the cap on non-deep studies"
    assert cs.category_status(xa, 0, 0, 0, 2) == "empty: no record of the map holds it"
    assert cs.category_status(xa, 3, 0, 0, 2) == "empty: no candidate holds it"
    assert cs.category_status(xa, 3, 1, 1, 2) == "all its 1 candidates"


def test_step_3_takes_band_1_first_and_shares_the_last_band_among_years():
    cands = {1: cand(1, cites=5), 2: cand(2, cites=1), 3: cand(3, year=2025, cites=2),
             4: cand(4, band="2", tier=2, cites=1),
             5: cand(5, band="2", tier=2, year=2025, cites=3),
             6: cand(6, band="2", tier=4, year=2025, cites=2),
             7: cand(7, band="2", tier=2, year=2025)}
    picks, fell, shares = cs.fill(cands, sorted(cands), 5, cs.standings(cands))
    # Band 1 whole (three studies); band 2's two places by its years: 2024 has one candidate
    # and 2025 three, so 2025 takes both, its two most cited.
    assert [(n, b, how) for n, b, _, how in picks] == [
        (1, "1", cs.BAND_WHOLE), (3, "1", cs.BAND_WHOLE), (2, "1", cs.BAND_WHOLE),
        (5, "2", cs.YEAR_SHARE), (6, "2", cs.YEAR_SHARE)]
    assert fell == "2" and shares == {2024: (1, 0), 2025: (3, 2)}


def test_non_deep_studies_past_the_cap_give_their_places_to_deep_ones():
    cands = {1: cand(1, deep=False, cites=10), 2: cand(2, deep=False, cites=8),
             3: cand(3, cites=7), 4: cand(4, cites=1),
             5: cand(5, deep=False, year=2025, cites=3), 6: cand(6, year=2025, cites=2),
             7: cand(7, deep=False, year=2026, cites=1), 8: cand(8, band="2", year=2023)}
    standing = cs.standings(cands)
    picks = [(1, "1", 2024, cs.YEAR_SHARE), (2, "1", 2024, cs.YEAR_SHARE),
             (5, "1", 2025, cs.YEAR_SHARE)]
    out, swaps = cs.cap_step3(cands, picks, 1, [], standing)
    # 1 and 5 share the best standing, 1 has the lower number; 5 and 2 are replaced by the
    # next deep study of their year.
    assert out == [(1, "1", 2024, cs.YEAR_SHARE), (3, "1", 2024, "in place of 2"),
                   (6, "1", 2025, "in place of 5")]
    assert swaps == [(5, 6), (2, 3)]
    # A year with no deep candidate left: the stratum's deep candidate of best standing, band
    # 1 first.
    out, swaps = cs.cap_step3(cands, [(7, "1", 2026, cs.YEAR_SHARE)], 0, [3, 6], standing)
    assert swaps == [(7, 4)]
    assert cs.cap_step3(cands, picks, 3, [], standing) == (picks, [])
    # Two places of one year freed by the cap go to its two most cited deep candidates, the
    # better-standing non-deep study's first.
    same = {1: cand(1, deep=False, cites=10), 2: cand(2, deep=False, cites=9),
            3: cand(3, cites=5), 4: cand(4, cites=4), 5: cand(5, cites=1)}
    two = [(1, "1", 2024, cs.YEAR_SHARE), (2, "1", 2024, cs.YEAR_SHARE)]
    assert cs.cap_step3(same, two, 0, [], cs.standings(same))[1] == [(1, 3), (2, 4)]


def test_the_minimum_falls_when_steps_1_and_2_would_overflow_the_core():
    xa, xb, xc = ("x", "a"), ("x", "b"), ("x", "c")
    cands = {n: cand(n, cats=(k,)) for n, k in enumerate((xa, xb, xc, xa, xb, xc), 1)}
    # Each category has two candidates: a minimum of three or two asks for all six, more than
    # the three places; a minimum of one asks for three.
    sel = cs.select(cands, [], [xa, xb, xc], 3, 10, [3, 2, 1], {"s": 3}, ["s"])
    assert sel.minimum == 1 and [n for n, _ in sel.step2] == [1, 2, 3]
    with pytest.raises(SystemExit, match="even at a minimum of 1"):
        cs.select(cands, [], [xa, xb, xc], 2, 10, [1], {"s": 2}, ["s"])


def test_step_1_keeps_the_cap_and_refuses_to_overflow_the_core():
    cands = {1: cand(1, deep=False, cites=9), 2: cand(2, deep=False, cites=1), 3: cand(3)}
    sel = cs.select(cands, [1, 2, 3], [], 3, 1, [1], {"s": 3}, ["s"])
    # With a cap of one, the non-deep claim of the worse standing is left out.
    assert sel.step1 == [1, 3] and sel.left_out == [2]
    with pytest.raises(SystemExit, match="Step 1 alone takes 2 studies"):
        cs.select(cands, [1, 3], [], 1, 10, [1], {"s": 1}, ["s"])


def test_the_candidates_are_the_stated_learners_each_study_once():
    the_map = {1: {"learner_depth": "deep"}, 2: {"learner_depth": "not-stated"},
               3: {"learner_depth": "tabular"}, 4: {"learner_depth": "deep"}}
    records = {n: corpus.Record.from_flat({
        "number": n, "title": t, "first_author": "Ann Lee", "source_type": s, "year": 2024,
        "openalex_id": "https://openalex.org/W%d" % n})
        for n, t, s in ((1, "One", "journal"), (2, "Two", "journal"),
                        (3, "Same title", "conference"), (4, "Same Title", "journal"))}
    assert cs.candidates(the_map, records) == ([1, 3, 4], [(4, [3])], [], [1, 4])


def test_the_mirrored_order_turns_a_tie_of_step_3_the_other_way():
    def run_both(cites):
        cands = {n: cand(n, cites=c) for n, c in enumerate(cites, 1)}
        args = ([], [], 3, 10, [3], {"s": 3}, ["s"])
        sel = cs.select(cands, *args)
        rows = cs.core_rows(sel)
        reverse, _ = cs.reverse_core(cands, *args)
        # The mirrored run leaves the candidates, and so the selection, as they were.
        assert cs.core_rows(cs.select(cands, *args)) == rows
        return rows, cs.number_ties(cands, rows, reverse, sel.standing)

    # Records 2, 3 and 4 tie on five citations for the last two places: the lower numbers
    # take them, the mirrored order 4 and 3. One place changes: 2's, tied with 3 in the core
    # and 4 left out.
    rows, (out, instead) = run_both([9, 5, 5, 5, 1])
    assert sorted(n for n, _ in rows) == [1, 2, 3]
    assert out == [(2, "3", [3], [4])] and instead == [(4, "3")]
    assert run_both([9, 7, 5, 3, 1])[1] == ([], [])


def test_the_mirrored_order_turns_a_tie_of_step_2_the_other_way():
    xa = ("x", "a")
    cands = {1: cand(1, cites=2, cats=(xa,)), 2: cand(2, cites=2, cats=(xa,)),
             3: cand(3, cites=50)}
    args = ([], [xa], 2, 10, [1], {"s": 2}, ["s"])
    sel = cs.select(cands, *args)
    rows = cs.core_rows(sel)
    reverse, stopped = cs.reverse_core(cands, *args)
    # 1 and 2 fill the one place owed equally; 3, the most cited, takes step 3's place.
    assert rows == [(1, "2"), (3, "3")] and reverse == [(2, "2"), (3, "3")] and not stopped
    assert cs.number_ties(cands, rows, reverse, sel.standing) == (
        [(1, "2", [], [2])], [(2, "2")])


def test_the_mirrored_order_turns_a_replacement_past_the_cap_the_other_way():
    cands = {1: cand(1, deep=False, cites=9), 2: cand(2, cites=5), 3: cand(3, cites=1),
             4: cand(4, cites=1), 5: cand(5, deep=False, cites=1)}
    args = ([], [], 2, 0, [1], {"s": 2}, ["s"])
    sel = cs.select(cands, *args)
    rows = cs.core_rows(sel)
    reverse, _ = cs.reverse_core(cands, *args)
    # A cap of none drops 1; its place goes to the next deep study of its year, 3 or 4, each
    # cited once.
    assert sorted(rows) == [(2, "3"), (3, "3")] and sorted(reverse) == [(2, "3"), (4, "3")]
    how = {p[0]: p[3] for p in sel.step3}
    assert how[3] == "in place of 1"
    # Only deep candidates could take the place the cap freed, so 5, non-deep and also cited
    # once, is not in the tie.
    assert cs.number_ties(cands, rows, reverse, sel.standing, how)[0] == [(3, "3", [], [4])]
    assert cs.number_ties(cands, rows, reverse, sel.standing)[0] == [(3, "3", [], [4, 5])]


def test_the_ties_section_names_each_tie_and_says_when_it_could_not_count():
    cands = {n: cand(n, cites=5 if n < 4 else 0) for n in (1, 2, 3, 4, 5)}
    text = "\n".join(cs.render_ties(([(2, "3", [1], [3]), (4, "2", [], [])],
                                     [(3, "3"), (5, "2")]), "", cands, 10))
    assert ("Reversing the order changes 2 of the core's 10 studies (step 1: 0, step 2: 1, "
            "step 3: 1)") in text
    assert "| 2 | 3 | s | 1 | 2024 | 5 | in the core: 1; left out: 3 |" in text
    assert "| 4 | 2 | s | 1 | 2024 | 0 | not listed (step 2) |" in text
    assert "In the mirrored core instead: 3 (step 3), 5 (step 2)." in text
    assert cs.render_ties(None, "it stopped", cands, 10)[-1] == (
        "The mirrored selection stopped: it stopped")


# The small map of the whole run. number: (role, learner, band, tier, year, cites). Record 5
# claims a digital twin, confirmed (step 1); record 6 claims real data, confirmed (no place);
# 8 is 7's conference version; 1 and 22 share a title but not a first author; 24's learner is
# not stated; 19 and 20 are tabular.
E2E, RULES, HEUR, UNSTATED = "end-to-end", "steering-rules", "steering-heuristic", "not-stated"
RECORDS = {
    1: (E2E, "deep", "1", 1, 2024, 50), 2: (E2E, "deep", "1", 1, 2024, 40),
    3: (E2E, "deep", "2", 2, 2025, 30), 4: (E2E, "deep", "2", 4, 2025, 0),
    5: (E2E, "deep", "2", 3, 2023, 1), 6: (E2E, "deep", "1", 1, 2025, 5),
    7: (E2E, "deep", "1", 1, 2023, 9), 8: (E2E, "deep", "2", 4, 2024, 2),
    9: (RULES, "deep", "1", 1, 2024, 20), 10: (RULES, "deep", "1", 1, 2025, 15),
    11: (RULES, "deep", "2", 2, 2024, 3), 12: (RULES, "deep", "2", 4, 2025, 1),
    13: (RULES, "deep", "1", 1, 2023, 7), 14: (RULES, "deep", "1", 1, 2026, 0),
    15: (HEUR, "deep", "1", 1, 2024, 12), 16: (HEUR, "deep", "2", 2, 2025, 4),
    17: (HEUR, "deep", "1", 1, 2026, 2), 18: (HEUR, "deep", "2", 3, 2023, 0),
    19: (RULES, "tabular", "1", 1, 2024, 30), 20: (RULES, "tabular", "1", 1, 2025, 25),
    21: (UNSTATED, "deep", "1", 1, 2024, 8), 22: (UNSTATED, "deep", "2", 2, 2025, 6),
    23: (UNSTATED, "deep", "1", 1, 2026, 1), 24: (E2E, UNSTATED, "2", 4, 2024, 0),
}
CLAIMS = {5: "twin-or-hil", 6: "real-data"}
TITLES = {1: ("Scheduling by policy", "Wen Song"), 22: ("Scheduling by Policy", "Wan-Ze Li"),
          7: ("A shared title", "Ann Lee"), 8: ("A Shared Title!", "Lee Ann")}
CORE = [(5, "1"), (1, "2"), (7, "2"), (20, "2"), (17, "2"), (10, "2"), (13, "2"), (15, "2"),
        (16, "2"), (2, "3"), (6, "3"), (21, "3"), (23, "3"), (22, "3")]


def codes(role, learner, number):
    cells = dict(BASE, policy_role=role, learner_depth=learner,
                 readiness_claim=CLAIMS.get(number, "none"))
    if role != E2E:
        cells["scheduling_action"] = "not-applicable" if role != UNSTATED else UNSTATED
    if learner == "tabular":
        cells.update(deep_architecture="not-applicable", state_encoding="discrete-states")
    elif learner == UNSTATED:
        cells["deep_architecture"] = UNSTATED
    return cells


def write_bands(d, changes=None):
    rows = []
    for n, (_, _, band, tier, _, _) in RECORDS.items():
        band, tier = (changes or {}).get(n, (band, tier))
        rows.append({"number": n, "band": band, "tier": tier,
                     "sjr_country": "United Kingdom" if band == "1" else ""})
    write_csv(os.path.join(d, "datasets", "venue-bands.csv"),
              ["number", "band", "tier", "sjr_country"], rows)


def build(tmp_path, answers=None):
    """The small map, its corpus, venue bands, claims' answers and agreement, and the config
    (a core of 14: 5 end to end, 5 steering, 4 role not stated; at most one non-deep study);
    returns the config's path."""
    d = tmp_path.as_posix()
    data = os.path.join(d, "datasets")
    write_csv(os.path.join(data, "map.csv"), ["number"] + NAMES + list(mc.META),
              [{"number": n, **codes(role, learner, n), "title": "", "venue": "", "year": year,
                "work_type": "article"}
               for n, (role, learner, _, _, year, _) in RECORDS.items()])
    refs = []
    for n, (_, _, _, _, year, cites) in RECORDS.items():
        title, author = TITLES.get(n, ("Paper %d" % n, "Author %d" % n))
        refs.append({"number": n, "openalex_id": "https://openalex.org/W%d" % n,
                     "doi": "10.1/p%d" % n, "title": title, "first_author": author,
                     "year": year, "cited_by_count": cites, "venue": "Venue %d" % n,
                     "source_type": "conference" if n == 8 else "journal"})
    with open(os.path.join(data, "references.json"), "w", encoding="utf-8") as fh:
        json.dump({"references": refs}, fh)
    write_bands(d)
    write_csv(os.path.join(data, "core-claims.csv"),
              ["number", "confirmed", "level", "read_from", "note", "confirmed_by"],
              [{"number": n, "confirmed": a, "confirmed_by": "moayad"}
               for n, a in (answers or {5: "yes", 6: "yes"}).items()])
    write_csv(os.path.join(d, "results", "map", "map-agreement.csv"), ["axis", "code", "coverage"],
              [{"axis": "policy_role", "code": "", "coverage": "yes"},
               {"axis": "policy_role", "code": "end-to-end", "coverage": ""},
               {"axis": "learner_depth", "code": "", "coverage": "yes"},
               {"axis": "objective", "code": "", "coverage": "no"}])
    with open(os.path.join(REPO, "configs", "core.toml"), encoding="utf-8") as fh:
        text = fh.read()
    for old, new in (('"datasets/', '"%s/datasets/' % d), ('"results/', '"%s/results/' % d),
                     ('"../core-full-texts/', '"%s/core-full-texts/' % d),
                     ("size = 100", "size = 14"), ("non_deep_cap = 10", "non_deep_cap = 1"),
                     ("places = 35", "places = 5"), ("places = 30", "places = 4")):
        assert old in text, old
        text = text.replace(old, new)
    config = os.path.join(d, "core.toml")
    with open(config, "w", encoding="utf-8") as fh:
        fh.write(text)
    return config


def run(config, monkeypatch):
    monkeypatch.setattr("sys.argv", ["core_selection", "--config", config])
    cs.main()


def test_the_core_of_a_small_map_worked_out_by_hand(tmp_path, monkeypatch):
    config = build(tmp_path)
    run(config, monkeypatch)
    rows = read_csv(os.path.join(tmp_path, "datasets", "core.csv"))
    assert [(int(r["number"]), r["step"]) for r in rows] == CORE
    first = {int(r["number"]): r for r in rows}
    assert first[1]["filled_at_step2"] == "2" and first[16]["filled_at_step2"] == "1"
    assert first[22]["taken"] == cs.BAND_WHOLE and first[20]["learner_depth"] == "tabular"
    flow = {r["key"]: int(r["count"]) for r in read_csv(
        os.path.join(tmp_path, "results", "core", "core-flow.csv"))}
    assert (flow["map"], flow["not-candidates"], flow["candidates"], flow["duplicates"],
            flow["candidates-once"]) == (24, 1, 23, 1, 22)
    assert (flow["step1"], flow["step2"], flow["core"], flow["core-non-deep"]) == (1, 8, 14, 1)
    assert (flow["step3-end-to-end-band1"], flow["step3-steering-band1"],
            flow["step3-role-not-stated-band1"],
            flow["step3-role-not-stated-band2"]) == (2, 0, 2, 1)
    with open(os.path.join(tmp_path, "results", "core", "core-selection.md"),
              encoding="utf-8") as fh:
        report = fh.read()
    assert "Counted once with another record: 7 kept, 8 counted with it." in report
    assert "1 and 22 (Wen Song; Wan-Ze Li)" in report
    assert ("| `learner_depth` | `non-neural` | 0 | 0 | 0 | 0 | 0 | empty: no record of the map "
            "holds it |") in report
    # Two tabular candidates are owed (the minimum of three falls to all a category has), but
    # the cap of one takes only 20.
    assert ("| `learner_depth` | `tabular` | 2 | 2 | 2 | 1 | 1 | short by the cap on non-deep "
            "studies |") in report
    assert "Minimum used: 3." in report
    # Steering is over its five places after step 2 and takes no more; role not stated has
    # three candidates for four places, and end to end takes the place it cannot fill.
    assert "| steering | 6 | 5 | 6 | 0 | 0 | 0 | none |" in report
    assert "| role-not-stated | 3 | 4 | 0 | 3 | 2 | 1 | 2 |" in report
    assert "| end-to-end | 5 | 5 | 3 | 2 | 2 | 0 | 1 |" in report
    # Mirrored, step 2 takes the same eight studies in another order (17 before 1, 13 before
    # 10), and steps 1 and 3 do not reach the record number.
    assert ("Reversing the order changes 0 of the core's 14 studies (step 1: 0, step 2: 0, "
            "step 3: 0)") in report
    compare = {(r["axis"], r["code"]): r for r in read_csv(
        os.path.join(tmp_path, "results", "core", "core-vs-map.csv"))}
    assert compare[("policy_role", "end-to-end")]["core"] == "5"
    assert compare[("policy_role", "end-to-end")]["rest"] == "4"
    # Every core study in band 1 but 5, 16 and 22.
    assert compare[("venue_country", "United Kingdom")]["core"] == "11"
    with open(os.path.join(tmp_path, "results", "core", "core-lock.json"), encoding="utf-8") as fh:
        lock = json.load(fh)
    assert lock["studies"] == 14 and lock["core_sha256"] == cs.core_digest(CORE)

    core_path = os.path.join(tmp_path, "datasets", "core.csv")
    with open(core_path, "rb") as fh:
        first_bytes = fh.read()
    assert list(rows[0]) == cs.CORE_FIELDS

    # The same inputs again: the same core, byte for byte, and the lock left as it was.
    run(config, monkeypatch)
    with open(os.path.join(tmp_path, "results", "core", "core-lock.json"), encoding="utf-8") as fh:
        assert json.load(fh) == lock
    with open(core_path, "rb") as fh:
        assert fh.read() == first_bytes
    # Record 3 in band 1 changes the core, which the lock refuses.
    write_bands(tmp_path.as_posix(), {3: ("1", 1)})
    with pytest.raises(SystemExit, match="differs from the one locked"):
        run(config, monkeypatch)


def test_inputs_the_core_cannot_be_selected_from_are_refused(tmp_path, monkeypatch):
    config = build(tmp_path, answers={6: "yes"})
    with pytest.raises(SystemExit, match="not yet answered"):
        run(config, monkeypatch)
    config = build(tmp_path)
    write_bands(tmp_path.as_posix(), {9: ("", "")})
    with pytest.raises(SystemExit, match="waiting for an answer"):
        run(config, monkeypatch)
