"""Tests for the page of the core's full texts (runners/core_texts.py, src/texts_page.html),
on the small map of tests/test_core_selection.py."""

import os
import re
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import screening as sc  # noqa: E402
import core_texts as ct  # noqa: E402
from screening_setup import page_data, read_csv, write_csv  # noqa: E402
from test_core_selection import CORE, build, run as run_selection  # noqa: E402

TEMPLATE = os.path.join(REPO, "src", "texts_page.html")


def run(config, monkeypatch):
    monkeypatch.setattr("sys.argv", ["core_texts", "--config", config])
    ct.main()


def test_the_page_lists_the_locked_core_by_record_number(tmp_path, monkeypatch):
    config = build(tmp_path)
    run_selection(config, monkeypatch)
    run(config, monkeypatch)
    folder = os.path.join(tmp_path, "core-full-texts")
    data = page_data(os.path.join(folder, "core-papers.html"))
    assert [r["number"] for r in data["records"]] == sorted(n for n, _ in CORE)
    assert data["columns"] == ct.SHEET_FIELDS and data["kind"] == "texts"
    assert data["save_as"].endswith("datasets/core-texts.csv")
    assert data["records"][0] == {
        "number": 1, "title": "Scheduling by policy", "first_author": "Wen Song", "year": 2024,
        "venue": "Venue 1", "doi": "10.1/p1", "link": "https://doi.org/10.1/p1"}
    assert data["intro"][0].startswith("These are the 14 studies")
    assert "core-texts.csv" in data["intro"][2]
    # The page is the worksheet: no blank sheet is written beside it.
    assert os.listdir(folder) == ["core-papers.html"]
    # With no returned file in place, nothing is read back.
    assert not os.path.exists(os.path.join(tmp_path, "results", "core", "core-texts.md"))


def test_the_template_holds_one_data_block_and_exports_the_runners_columns():
    with open(TEMPLATE, encoding="utf-8") as fh:
        template = fh.read()
    assert template.count(sc.PAGE_PLACEHOLDER) == 1
    # The answers the page keeps and exports are the runner's columns to fill, in order.
    fields = re.search(r"var FIELDS = \[(.*?)\];", template, re.S).group(1)
    assert re.findall(r"'([a-z_]+)'", fields) == ct.TO_FILL
    # Plain ASCII, as the other pages: characters beyond it are written by code.
    assert all(ord(c) < 128 for c in template)


def test_a_core_other_than_the_locked_one_is_refused(tmp_path, monkeypatch):
    config = build(tmp_path)
    run_selection(config, monkeypatch)
    core = os.path.join(tmp_path, "datasets", "core.csv")
    kept = read_csv(core)
    write_csv(core, list(kept[0]), kept[1:])
    with pytest.raises(SystemExit, match="is not the core locked"):
        run(config, monkeypatch)


NOT_SUBSCRIBED = "not in the library's subscriptions"


def gathered(tmp_path, monkeypatch, answers=None):
    """The small core's page written, and its returned file: every study saved (published, no
    supplementary material, its DOI right, by A. Person) but where `answers` {number: fields}
    say otherwise. Returns the config and the file's rows."""
    config = build(tmp_path)
    run_selection(config, monkeypatch)
    run(config, monkeypatch)
    data = page_data(os.path.join(tmp_path, "core-full-texts", "core-papers.html"))
    rows = []
    for r in data["records"]:
        row = {c: r[c] for c in ct.GIVEN}
        row.update(pdf_saved="yes", version="published", supplement_saved="no", doi_correct="yes",
                   correct_doi="", not_retrieved_reason="", note="", done_by="A. Person")
        row.update((answers or {}).get(r["number"], {}))
        rows.append(row)
    return config, rows


def returned(tmp_path, rows, listed=None):
    """The returned file, and the checksums' list of the full texts saved (by default, the
    studies the file marks saved)."""
    write_csv(os.path.join(tmp_path, "datasets", "core-texts.csv"), ct.SHEET_FIELDS, rows)
    if listed is None:
        listed = [r["number"] for r in rows if r["pdf_saved"] == "yes"]
    write_csv(os.path.join(tmp_path, "datasets", "full-texts-sha256.csv"),
              ["number", "file", "bytes", "sha256"],
              [{"number": n, "file": "%d.pdf" % n, "bytes": 1, "sha256": "0" * 64} for n in listed])


def test_the_returned_file_is_read_back_into_the_flow_counts(tmp_path, monkeypatch):
    config, rows = gathered(tmp_path, monkeypatch, {
        5: dict(pdf_saved="no", version="", supplement_saved="", doi_correct="",
                not_retrieved_reason=NOT_SUBSCRIBED, done_by="B. Person"),
        2: dict(doi_correct="no", correct_doi="10.9/right")})
    returned(tmp_path, rows)
    run(config, monkeypatch)
    flow = {r["key"]: r for r in read_csv(os.path.join(tmp_path, "results", "core",
                                                       "core-texts-flow.csv"))}
    assert [flow[k]["count"] for k in ("sought", "not-retrieved", "not-retrieved-1", "read",
                                       "doi-corrected")] == ["14", "1", "1", "13", "1"]
    assert flow["not-retrieved-1"]["label"] == "Not retrieved: " + NOT_SUBSCRIBED
    with open(os.path.join(tmp_path, "results", "core", "core-texts.md"), encoding="utf-8") as fh:
        report = fh.read()
    assert "| 5 | Paper 5 | %s |" % NOT_SUBSCRIBED in report
    assert "| 2 | 10.1/p2 | 10.9/right |" in report
    assert "13 full texts: published 13." in report


def drop_last(rows):
    rows.pop()


def add_a_study(rows):
    rows.append(dict(rows[0], number=99))


@pytest.mark.parametrize("change, message", [
    (drop_last, "no row"),
    (add_a_study, "not a study of the core: 99"),
    (lambda rows: rows[0].update(title="Another title"), "the given column title differs"),
    (lambda rows: rows[0].update(version="final"), "version is not one of"),
    (lambda rows: rows[0].update(version=""), "a saved PDF with no version"),
    (lambda rows: rows[0].update(pdf_saved="no", version="", supplement_saved=""),
     "not retrieved, with no reason"),
    (lambda rows: rows[0].update(pdf_saved=""), "neither saved nor given a reason"),
    (lambda rows: rows[0].update(doi_correct="no"), "a DOI found wrong, with no right DOI"),
    (lambda rows: rows[0].update(done_by=""), "no name of who did it"),
])
def test_a_returned_file_not_the_cores_or_not_finished_is_refused(tmp_path, monkeypatch, change,
                                                                  message):
    config, rows = gathered(tmp_path, monkeypatch)
    change(rows)
    returned(tmp_path, rows, listed=[r["number"] for r in rows])
    with pytest.raises(SystemExit, match=message):
        run(config, monkeypatch)


def test_the_studies_saved_must_be_the_full_texts_listed(tmp_path, monkeypatch):
    config, rows = gathered(tmp_path, monkeypatch)
    numbers = [r["number"] for r in rows]
    returned(tmp_path, rows, listed=numbers[1:])
    with pytest.raises(SystemExit, match="saved but not listed \\[%d\\]" % numbers[0]):
        run(config, monkeypatch)
