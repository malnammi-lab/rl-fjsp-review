"""Tests for the venue bands (runners/venue_bands.py): SJR found by ISSN, ICORE proposed by
name and confirmed by a person, and the band and tier of every record of the map."""

import json
import os
import shutil
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import venue_bands  # noqa: E402
from screening_setup import read_csv, write_csv  # noqa: E402

AAAI = "Proceedings of the AAAI Conference on Artificial Intelligence"
KEY_AAAI = "name:" + AAAI
CP = "International Conference on Principles and Practice of Constraint Programming (CP)"
KEY_CP = "name:" + CP
TIERS = 'tiers = [["Q1", "A*"], ["Q2", "A"], ["Q3"]]'
# number: (venue, source type, ISSN-L). 1 is a Q1 journal, 2 a Q3 journal, 3 a conference
# that ICORE ranks A*, 4 a conference whose acronym ICORE gives to another, 5 has no venue,
# 6 a proceedings series that SJR lists with no quartile, 7 a conference ICORE ranks C,
# which is never proposed since no tier names C, 8 a Q2 journal, and 9 a conference that
# ICORE ranks A, which a match places in the second tier but not in band 1.
RECORDS = {
    1: ("Journal A", "journal", "1234-5678"),
    2: ("Journal B", "journal", "2345-678x"),
    3: (AAAI, "conference", ""),
    4: ("International Conference on Computer and Communications (ICCC)", "conference", ""),
    5: ("", "", ""),
    6: ("2022 IEEE 18th International Conference on Automation Science and Engineering (CASE)",
        "conference", "2161-8070"),
    7: ("International Conference on Computational Creativity (ICCC)", "conference", ""),
    8: ("Journal C", "journal", "3456-7890"),
    9: (CP, "conference", ""),
}
# SJR's download: semicolons, decimal commas, and `Publisher` twice in the header.
SJR = """Rank;Sourceid;Title;Type;Issn;Publisher;SJR;SJR Best Quartile;Country;Publisher;Categories
1;101;"Journal A";journal;"87654321, 12345678";"P";1,5;Q1;United Kingdom;"P";"X (Q1)"
2;102;"Journal B";journal;"2345678X";"P";0,3;Q3;China;"P";"X (Q3)"
3;103;"IEEE International Conference on Automation Science and Engineering";conference and proceedings;"21618070";"P";0,4;-;United States;"P";"X"
4;104;"Journal C";journal;"34567890";"P";0,8;Q2;China;"P";"X (Q2)"
"""
# ICORE's export: no header row. Record 3 shares more words with 10 than with 1629, but
# gives 1629's acronym; record 4 gives 2199's acronym and shares no word with it.
ICORE = """1629,National Conference of the American Association for Artificial Intelligence,AAAI,ICORE2026,A*,Yes,4602,,
10,International Conference on Artificial Intelligence,ICAI,ICORE2026,C,Yes,4602,,
2199,International Conference on Computational Creativity,ICCC,ICORE2026,C,Yes,46,,
500,International Conference on Principles and Practice of Constraint Programming,CP,ICORE2026,A,Yes,4602,,
"""
ANSWERS = ["key", "icore_id", "confirmed", "note", "confirmed_by"]


def build(tmp_path):
    """The map, the corpus, the two lists and the config under tmp_path; returns the
    config's path."""
    d = tmp_path.as_posix()
    data = os.path.join(d, "datasets")
    os.makedirs(os.path.join(d, "data", "venue-lists"), exist_ok=True)
    write_csv(os.path.join(data, "map.csv"), ["number"], [{"number": n} for n in RECORDS])
    refs = [{"number": n, "openalex_id": "https://openalex.org/W%d" % n, "title": "Paper %d" % n,
             "venue": venue, "source_type": kind, "issn_l": issn}
            for n, (venue, kind, issn) in RECORDS.items()]
    with open(os.path.join(data, "references.json"), "w", encoding="utf-8") as fh:
        json.dump({"references": refs}, fh)
    with open(os.path.join(d, "data", "venue-lists", "scimagojr-2025.csv"), "w",
              encoding="utf-8", newline="") as fh:
        fh.write(SJR)
    with open(os.path.join(d, "data", "venue-lists", "icore2026.csv"), "w",
              encoding="utf-8", newline="") as fh:
        fh.write(ICORE)
    with open(os.path.join(REPO, "configs", "venues.toml"), encoding="utf-8") as fh:
        text = fh.read()
    for old, new in (('"datasets/', '"%s/datasets/' % d), ('"results/', '"%s/results/' % d),
                     ('"../data/', '"%s/data/' % d)):
        assert old in text, old
        text = text.replace(old, new)
    config = os.path.join(d, "venues.toml")
    with open(config, "w", encoding="utf-8") as fh:
        fh.write(text)
    return config


def run(config, monkeypatch):
    monkeypatch.setattr("sys.argv", ["venue_bands", "--config", config])
    venue_bands.main()


def bands(tmp_path):
    return {int(r["number"]): (r["band"], r["tier"], r["basis"])
            for r in read_csv(os.path.join(tmp_path, "datasets", "venue-bands.csv"))}


def report(tmp_path):
    with open(os.path.join(tmp_path, "results", "core", "venue-bands.md"), encoding="utf-8") as fh:
        return fh.read()


def confirm(tmp_path, rows):
    write_csv(os.path.join(tmp_path, "datasets", "venue-matches.csv"), ANSWERS, rows)


def fill(sheet, key, **answer):
    """Answers one row of the sheet in place, found by its key, as a person might."""
    rows = read_csv(sheet)
    next(r for r in rows if r["key"] == key).update(answer)
    write_csv(sheet, list(rows[0]), rows)


def test_names_are_read_as_words_and_acronyms():
    assert venue_bands.words(RECORDS[6][0]) == {"automation", "science", "engineering"}
    assert venue_bands.acronyms(RECORDS[6][0]) == {"case"}
    assert venue_bands.words("IEEE Transactions on Systems, Man & Cybernetics") == {
        "transaction", "system", "man", "cybernetic"}
    assert venue_bands.issn_key("2345-678x") == "2345678X"


def test_an_acronym_the_venue_gives_comes_before_a_closer_name():
    rows = [dict(zip(venue_bands.ICORE_COLUMNS, line.split(",")[:5]))
            for line in ICORE.strip().splitlines()]
    match, s = venue_bands.propose(AAAI, rows, 0.5)
    assert match["acronym"] == "AAAI" and round(s, 2) == 0.4
    # The same acronym is no match when the names share no word.
    assert venue_bands.propose(RECORDS[4][0], rows, 0.5) is None


def test_the_better_of_the_two_ranks_counts():
    tiers = [["Q1", "A*"], ["Q2", "A"], ["Q3"]]
    q2 = {"SJR Best Quartile": "Q2"}
    star, a = ({"id": "1", "rank": "A*"}, 1.0), ({"id": "2", "rank": "A"}, 1.0)
    assert venue_bands.decide(q2, star, "yes", tiers) == ("1", "1", "ICORE A*")
    # The same tier from both lists: SJR's is the basis.
    assert venue_bands.decide(q2, a, "yes", tiers) == ("2", "2", "SJR Q2")
    assert venue_bands.decide(q2, a, "no", tiers) == ("2", "2", "SJR Q2")
    assert venue_bands.decide(None, a, "yes", tiers) == ("2", "2", "ICORE A")
    assert venue_bands.decide({"SJR Best Quartile": "Q4"}, None, "", tiers) == (
        "2", "4", "SJR Q4")
    assert venue_bands.decide(None, a, "", tiers) == ("", "", "pending")
    assert venue_bands.describe_tiers(tiers) == (
        "1, Q1 or A*; 2, Q2 or A; 3, Q3; 4, every other venue")


def test_the_bands_before_and_after_the_person_confirms(tmp_path, monkeypatch):
    config = build(tmp_path)
    with open(config, encoding="utf-8") as fh:
        assert TIERS in fh.read()
    run(config, monkeypatch)
    assert bands(tmp_path) == {1: ("1", "1", "SJR Q1"), 2: ("2", "3", "SJR Q3"),
                               3: ("", "", "pending"), 4: ("2", "4", "no match"),
                               5: ("2", "4", "no venue"), 6: ("2", "4", "SJR no quartile"),
                               7: ("2", "4", "no match"), 8: ("2", "2", "SJR Q2"),
                               9: ("", "", "pending")}
    sheet = read_csv(os.path.join(tmp_path, "results", "core", "venue-matches-sheet.csv"))
    assert [(r["key"], r["icore_id"], r["icore_rank"], r["confirmed"]) for r in sheet] == [
        (KEY_CP, "500", "A", ""), (KEY_AAAI, "1629", "A*", "")]
    text = report(tmp_path)
    assert "9 records of the map: 8 in 8 venues, and 1 without a venue" in text
    assert "| pending | 2 | 2 |" in text and "Records without a venue, in band 2: 5." in text
    assert "| 4 (the rest) | 4 | 3 |" in text
    assert "| China | 2 | 0 |" in text and "| not in SJR | 5 | 0 |" in text

    confirm(tmp_path, [{"key": KEY_AAAI, "icore_id": "1629", "confirmed": "Yes",
                        "confirmed_by": "moayad"},
                       {"key": KEY_CP, "icore_id": "500", "confirmed": "yes",
                        "confirmed_by": "moayad"}])
    run(config, monkeypatch)
    # A* places the conference in band 1; A only in the second tier.
    assert bands(tmp_path)[3] == ("1", "1", "ICORE A*")
    assert bands(tmp_path)[9] == ("2", "2", "ICORE A")
    row = next(r for r in read_csv(os.path.join(tmp_path, "datasets", "venue-bands.csv"))
               if r["number"] == "3")
    assert (row["icore_acronym"], row["icore_rank"], row["sjr_country"]) == ("AAAI", "A*", "")
    assert "| not in SJR | 5 | 1 |" in report(tmp_path)
    confirm(tmp_path, [{"key": KEY_AAAI, "icore_id": "1629", "confirmed": "no",
                        "note": "a companion volume", "confirmed_by": "moayad"}])
    run(config, monkeypatch)
    assert bands(tmp_path)[3] == ("2", "4", "no match")


def test_tiers_are_checked(tmp_path, monkeypatch):
    config = build(tmp_path)
    with open(config, encoding="utf-8") as fh:
        text = fh.read()
    for tiers, message in (('tiers = [["Q1", "A*"], ["Q2", "A*"]]', "none in two tiers"),
                           ('tiers = []', "none in two tiers"),
                           ('tiers = [["Q1", "A+"]]', "which neither list holds")):
        with open(config, "w", encoding="utf-8") as fh:
            fh.write(text.replace(TIERS, tiers))
        with pytest.raises(SystemExit, match=message):
            run(config, monkeypatch)


def test_a_bad_confirmations_file_is_refused(tmp_path, monkeypatch):
    config = build(tmp_path)
    for rows, message in (
            ([{"key": KEY_AAAI, "icore_id": "1629", "confirmed": "maybe", "confirmed_by": "m"}],
             "not yes or no"),
            ([{"key": KEY_AAAI, "icore_id": "1629", "confirmed": "yes"}], "no confirmed_by"),
            ([{"key": KEY_AAAI, "icore_id": "1629", "confirmed": "yes", "confirmed_by": "m"},
              {"key": KEY_AAAI, "icore_id": "1629", "confirmed": "no", "confirmed_by": "m"}],
             "given twice")):
        confirm(tmp_path, rows)
        with pytest.raises(SystemExit, match=message):
            run(config, monkeypatch)


def test_answers_on_venues_no_longer_proposed_are_set_aside(tmp_path, monkeypatch):
    config = build(tmp_path)
    # Journal A is in band 1 by SJR, so never proposed; record 3 is now proposed AAAI, not 10.
    confirm(tmp_path, [{"key": "name:Journal A", "icore_id": "1", "confirmed": "yes",
                        "confirmed_by": "m"},
                       {"key": KEY_AAAI, "icore_id": "10", "confirmed": "yes",
                        "confirmed_by": "m"}])
    run(config, monkeypatch)
    assert bands(tmp_path)[3] == ("", "", "pending")
    assert "now proposed another conference: 2." in report(tmp_path)
    # An answer on the venue's new proposal, given on the sheet in place, is not lost to the
    # set-aside answer on its old one.
    sheet = os.path.join(tmp_path, "results", "core", "venue-matches-sheet.csv")
    fill(sheet, KEY_AAAI, confirmed="yes", confirmed_by="m")
    with pytest.raises(SystemExit, match="answers not saved"):
        run(config, monkeypatch)


def test_a_sheet_filled_in_place_is_not_overwritten(tmp_path, monkeypatch):
    config = build(tmp_path)
    run(config, monkeypatch)
    sheet = os.path.join(tmp_path, "results", "core", "venue-matches-sheet.csv")
    fill(sheet, KEY_AAAI, confirmed="yes", confirmed_by="moayad")
    with pytest.raises(SystemExit, match="answers not saved"):
        run(config, monkeypatch)
    shutil.copy(sheet, os.path.join(tmp_path, "datasets", "venue-matches.csv"))
    run(config, monkeypatch)
    assert bands(tmp_path)[3] == ("1", "1", "ICORE A*")
