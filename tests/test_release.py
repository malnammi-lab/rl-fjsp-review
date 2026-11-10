"""Tests of the release itself, which run in any clone: the checker is the one every paper was
coded with, no released record file holds an abstract, and no released quote or reason is a
whole abstract (configs/withheld.toml)."""

import csv
import json
import os
import sys
import tomllib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

from src import withheld  # noqa: E402
import core_check as cc  # noqa: E402


def test_the_checker_is_the_one_every_paper_was_coded_with():
    with open(os.path.join(REPO, "datasets", "core-coding-runs.csv"), encoding="utf-8-sig",
              newline="") as fh:
        prints = {r["checker_fingerprint"] for r in csv.DictReader(fh)}
    assert prints == {cc.fingerprint()}


def test_no_released_record_file_holds_an_abstract():
    for released in withheld.load():
        with open(released, encoding="utf-8") as fh:
            payload = json.load(fh)
        assert withheld.FIELD not in payload["columns"], released
        assert withheld.HASH in payload["columns"], released
        bad = [r.get("number") for r in payload["references"]
               if withheld.FIELD in r or withheld.HASH not in r]
        assert not bad, (released, bad[:10])


def test_each_released_record_file_is_the_one_its_checksums_pair():
    # The config pairs each file as written with its released form; the core's lock names the
    # file as written, and core-statistics accepts the released file through the pair.
    pairs = withheld.checksums()
    assert sorted(pairs) == sorted(withheld.load())
    for released, (written, now) in pairs.items():
        assert withheld.file_sha(released) == now, released
        assert withheld.stands_for(released, written)
    with open(os.path.join(REPO, "results", "core", "core-lock.json"), encoding="utf-8") as fh:
        held = json.load(fh)["inputs"]["references"]
    assert withheld.stands_for(os.path.join(REPO, "datasets", "references.json"), held)


def test_no_released_quote_or_reason_is_a_whole_abstract():
    # The release cuts every stretch of more than [quotes] words of an abstract; a clone can
    # check, through each record's abstract_sha256, that no cell is still a whole abstract.
    with open(withheld.CONFIG, "rb") as fh:
        quotes = tomllib.load(fh)["quotes"]
    with open(withheld.resolve(quotes["records"]), encoding="utf-8") as fh:
        hashes = {str(r["number"]): r[withheld.HASH] for r in json.load(fh)["references"]}
    for name in quotes["files"]:
        with open(withheld.resolve(name), encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        whole = [r["number"] for r in rows for c in quotes["columns"]
                 if (r.get(c) or "").strip() and hashes.get(r["number"])
                 and hashes[r["number"]] in (withheld.sha256_text(r[c]),
                                             withheld.sha256_text(r[c].strip()))]
        assert not whole, (name, whole[:10])
