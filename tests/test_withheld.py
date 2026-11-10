"""Tests for the withheld abstracts (src/withheld.py): a released record file, the authors' copy
of it and a config naming both, all in tmp_path."""

import hashlib
import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus, withheld  # noqa: E402

ABSTRACT = "An invented abstract about a policy for the shop."
COPY = [
    {"number": 1, "title": "A policy for the shop", "doi": "10.1/a", "abstract_source": "openalex",
     "abstract": ABSTRACT},
    {"number": 2, "title": "Another policy", "doi": "10.1/b", "abstract_source": None,
     "abstract": None},
]


def released(records):
    """The records as released: each abstract replaced by its SHA-256, in the same place."""
    return [{("abstract_sha256" if k == "abstract" else k):
             (withheld.sha256_text(v or "") if k == "abstract" else v) for k, v in r.items()}
            for r in records]


def write(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"source": "a query", "count": len(records), "references": records}, fh, indent=1)


def build(tmp_path, copy=COPY, out=None):
    """The released file, the authors' copy and a config naming both; returns their paths."""
    path, kept = str(tmp_path / "repo" / "references.json"), str(tmp_path / "data" / "references.json")
    write(path, out if out is not None else released(copy))
    write(kept, copy)
    config = tmp_path / "withheld.toml"
    config.write_text('[abstracts]\n"%s" = "%s"\n' % (path.replace("\\", "/"), kept.replace("\\", "/")),
                      encoding="utf-8")
    return path, kept, str(config)


def test_a_text_hashes_as_the_quotes_do():
    assert withheld.sha256_text("") == ""
    assert withheld.sha256_text("abc") == hashlib.sha256(b"abc").hexdigest()


def test_the_records_take_their_abstracts_from_the_checked_copy(tmp_path, monkeypatch):
    path, _, config = build(tmp_path)
    monkeypatch.setattr(withheld, "CONFIG", config)
    assert [r.abstract for r in corpus.load_references(path)] == ["", ""]
    merged = corpus.load_references(path, abstracts=True)
    assert [r.abstract for r in merged] == [ABSTRACT, ""]
    assert "abstract" not in merged[0].raw and merged[0].raw["abstract_sha256"]


def test_a_copy_that_differs_beyond_the_abstracts_is_refused(tmp_path):
    # Another title in the released file, then another abstract in the copy.
    out = released(COPY)
    out[0]["title"] = "A policy for a shop"
    path, _, config = build(tmp_path, out=out)
    with pytest.raises(SystemExit, match="differ in more than the abstract of record 1"):
        withheld.abstracts(path, config)
    changed = [dict(COPY[0], abstract="Another abstract."), COPY[1]]
    path, kept, config = build(tmp_path)
    write(kept, changed)
    with pytest.raises(SystemExit, match="differ in more than the abstract of record 1"):
        withheld.abstracts(path, config)


def test_without_the_copy_a_step_stops_and_the_abstracts_stay_blank(tmp_path):
    path, kept, config = build(tmp_path)
    os.remove(kept)
    assert not withheld.available(path, config)
    with pytest.raises(SystemExit, match="which this repository withholds"):
        withheld.require(path, "a step", config)
    records = corpus.load_references(path)
    assert [r.abstract for r in withheld.merge(path, records, config)] == ["", ""]
    # A file the config does not list withholds nothing.
    other = str(tmp_path / "elsewhere.json")
    assert withheld.available(other, config)
    withheld.require(other, "a step", config)
