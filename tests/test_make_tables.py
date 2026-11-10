"""Tests for the flow diagram's rows from the map to the core and its full texts
(runners/make_tables.py, core_rows and load_flow)."""

import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import make_tables  # noqa: E402
from screening_setup import write_csv  # noqa: E402

# The counts runners/core_selection.py writes for a core of 14 (results/core/core-flow.csv).
CORE = {"map": 24, "not-candidates": 2, "candidates": 22, "duplicates": 0,
        "candidates-once": 22, "step1": 1, "step1-cap": 0, "step2": 8,
        "step3-end-to-end-band1": 2, "step3-end-to-end-band2": 0,
        "step3-steering-band1": 1, "step3-steering-band2": 1,
        "step3-role-not-stated-band1": 1, "step3-role-not-stated-band2": 0,
        "step3-cap": 1, "core": 14, "core-non-deep": 1}
# Those runners/core_texts.py writes from the returned file (results/core/core-texts-flow.csv).
TEXTS = {"sought": 14, "not-retrieved": 1, "not-retrieved-1": 1, "read": 13, "doi-corrected": 0}


def test_the_core_rows_take_each_step_and_the_full_texts():
    assert make_tables.core_rows(CORE, TEXTS) == [
        ("Candidates for the core: learner stated, each study once", 22),
        ("The core, step 1: use beyond simulation", 1),
        ("The core, step 2: coverage", 8),
        # Step 3's bands summed, then each stratum and band, and the cap's replacements.
        ("The core, step 3: the places left", 5),
        ("The core, step 3: end-to-end, band 1", 2),
        ("The core, step 3: end-to-end, band 2", 0),
        ("The core, step 3: steering, band 1", 1),
        ("The core, step 3: steering, band 2", 1),
        ("The core, step 3: role-not-stated, band 1", 1),
        ("The core, step 3: role-not-stated, band 2", 0),
        ("The core, step 3: non-deep studies left out by the cap", 1),
        ("Selected for full-text synthesis: the core", 14),
        ("Full texts sought", 14),
        ("Full texts not retrieved", 1),
        ("Full texts coded", 13)]


def test_without_the_full_texts_the_rows_stop_at_the_core():
    assert make_tables.core_rows(CORE)[-1] == ("Selected for full-text synthesis: the core", 14)


def test_steps_that_do_not_add_up_to_the_core_are_refused():
    with pytest.raises(SystemExit, match="do not add up to the core"):
        make_tables.core_rows(dict(CORE, core=15))


@pytest.mark.parametrize("texts", [dict(TEXTS, sought=13, read=12),
                                   dict(TEXTS, read=12)])
def test_full_texts_that_are_not_the_cores_or_do_not_add_up_are_refused(texts):
    with pytest.raises(SystemExit, match="do not add up, or are not the core's"):
        make_tables.core_rows(CORE, texts)


def test_a_file_of_counts_is_read_by_key(tmp_path):
    path = str(tmp_path / "core-texts-flow.csv")
    write_csv(path, ["key", "label", "count"],
              [{"key": k, "label": "label of %s" % k, "count": n} for k, n in TEXTS.items()])
    assert make_tables.load_flow(path) == TEXTS
