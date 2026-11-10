"""Tests for the draws of the core's coding (runners/core_draws.py): on a small core of
thirty studies, then on the real core with its outputs written elsewhere."""

import csv
import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

from src import screening as sc  # noqa: E402
import core_draws as cd  # noqa: E402
from core_selection import core_digest  # noqa: E402

# A small core: 1 to 12 end to end, 13 to 17 steering rules, 18 to 22 steering a heuristic,
# 23 to 30 with no role on the map. Study 30's full text was not obtained; study 29's is the
# largest.
ROLES = ([(n, "end-to-end", "end-to-end") for n in range(1, 13)]
         + [(n, "steering", "steering-rules") for n in range(13, 18)]
         + [(n, "steering", "steering-heuristic") for n in range(18, 23)]
         + [(n, "role-not-stated", "not-stated") for n in range(23, 31)])
NOT_SAVED = {30}
LARGEST = 29


def write_rows(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def build(tmp_path, seed=7, smoke=5, fifth=6, unconverted=()):
    """The small core's inputs and a config reading them; returns the config's path."""
    base = tmp_path.as_posix()
    core = [{"number": n, "step": "3", "stratum": s, "policy_role": r} for n, s, r in ROLES]
    write_rows(os.path.join(base, "datasets", "core.csv"),
               ["number", "step", "stratum", "policy_role"], core)
    os.makedirs(os.path.join(base, "results", "core"))
    with open(os.path.join(base, "results", "core", "core-lock.json"), "w") as fh:
        json.dump({"core_sha256": core_digest([(n, "3") for n, _, _ in ROLES])}, fh)
    write_rows(os.path.join(base, "datasets", "core-texts.csv"), ["number", "pdf_saved"],
               [{"number": n, "pdf_saved": "no" if n in NOT_SAVED else "yes"}
                for n, _, _ in ROLES])
    md = []
    for n, _, _ in ROLES:
        if n in NOT_SAVED or n in unconverted:
            continue
        size = 99999 if n == LARGEST else 1000 * n
        md += [{"number": n, "file": "%d/%d.md" % (n, n), "bytes": size, "sha256": "x"},
               {"number": n, "file": "%d/%d_meta.json" % (n, n), "bytes": 5, "sha256": "y"}]
    write_rows(os.path.join(base, "datasets", "full-texts-md-sha256.csv"),
               ["number", "file", "bytes", "sha256"], md)
    config = os.path.join(base, "core-draws.toml")
    with open(config, "w", encoding="utf-8") as fh:
        fh.write('[inputs]\ncore = "%s/datasets/core.csv"\n'
                 'core_lock = "%s/results/core/core-lock.json"\n'
                 'texts = "%s/datasets/core-texts.csv"\n'
                 'md_checksums = "%s/datasets/full-texts-md-sha256.csv"\n'
                 '[draws]\nseed = %d\nsmoke = %d\n'
                 'pilot_roles = ["end-to-end", "steering-rules", "steering-heuristic", '
                 '"not-stated"]\npilot_largest = true\nfifth = %d\n'
                 '[outputs]\ntable = "%s/out/draws.csv"\nreport = "%s/out/draws.md"\n'
                 'lock = "%s/out/draws-lock.json"\n'
                 % (base, base, base, base, seed, smoke, fifth, base, base, base))
    return config


def run(config, monkeypatch, override=None):
    argv = ["core_draws", "--config", config] + (["--override", override] if override else [])
    monkeypatch.setattr("sys.argv", argv)
    cd.main()


def drawn(base):
    with open(os.path.join(base, "out", "draws.csv"), encoding="utf-8-sig", newline="") as fh:
        return [(int(r["number"]), r["draw"], r["stratum"], r["policy_role"])
                for r in csv.DictReader(fh)]


def test_the_smoke_study_one_pilot_per_role_the_largest_then_the_fifth_by_stratum(
        tmp_path, monkeypatch):
    run(build(tmp_path), monkeypatch)
    rows = drawn(tmp_path.as_posix())
    numbers = [n for n, _, _, _ in rows]
    assert len(numbers) == len(set(numbers)) == 1 + 5 + 6
    assert rows[0][:2] == (5, "smoke")
    pilot = [r for r in rows if r[1] == "pilot"]
    assert [r[3] for r in pilot[:4]] == ["end-to-end", "steering-rules",
                                        "steering-heuristic", "not-stated"]
    # The largest full text left: 29, unless the not-stated draw took it, then 28.
    assert pilot[4][0] == (28 if pilot[3][0] == LARGEST else LARGEST)
    assert 30 not in numbers
    fifth = [r for r in rows if r[1] == "fifth"]
    left = {}
    for n, s, _ in ROLES:
        if n not in NOT_SAVED and n not in numbers[:6]:
            left[s] = left.get(s, 0) + 1
    quotas = sc.proportional_quotas({s: left[s] for s in sorted(left)}, 6)
    assert {s: sum(1 for r in fifth if r[2] == s) for s in quotas} == quotas


def test_a_second_run_holds_the_lock_and_draws_the_same(tmp_path, monkeypatch):
    config = build(tmp_path)
    run(config, monkeypatch)
    first = drawn(tmp_path.as_posix())
    run(config, monkeypatch)
    assert drawn(tmp_path.as_posix()) == first
    with open(os.path.join(tmp_path, "out", "draws-lock.json"), encoding="utf-8") as fh:
        lock = json.load(fh)
    assert lock["seed"] == 7 and [n for n, _ in lock["draws"]] == [r[0] for r in first]
    assert sorted(lock["inputs"]) == ["core", "md_checksums", "texts"]


def test_another_seed_after_the_lock_is_refused(tmp_path, monkeypatch):
    config = build(tmp_path)
    run(config, monkeypatch)
    override = os.path.join(tmp_path, "seed.toml")
    with open(override, "w", encoding="utf-8") as fh:
        fh.write("[draws]\nseed = 8\n")
    with pytest.raises(SystemExit, match="differ from those locked"):
        run(config, monkeypatch, override)


def test_a_saved_full_text_with_no_markdown_is_refused(tmp_path, monkeypatch):
    with pytest.raises(SystemExit, match="with no markdown: 12"):
        run(build(tmp_path, unconverted=(12,)), monkeypatch)


def test_a_smoke_study_without_a_converted_text_is_refused(tmp_path, monkeypatch):
    with pytest.raises(SystemExit, match="smoke study 30"):
        run(build(tmp_path, smoke=30), monkeypatch)


def test_a_core_other_than_the_locked_one_is_refused(tmp_path, monkeypatch):
    config = build(tmp_path)
    with open(os.path.join(tmp_path, "results", "core", "core-lock.json"), "w") as fh:
        json.dump({"core_sha256": "another"}, fh)
    with pytest.raises(SystemExit, match="is not the core locked"):
        run(config, monkeypatch)


def test_the_real_config_draws_from_the_retrieved_core(tmp_path, monkeypatch):
    override = os.path.join(tmp_path, "outputs.toml")
    base = tmp_path.as_posix()
    with open(override, "w", encoding="utf-8") as fh:
        fh.write('[outputs]\ntable = "%s/out/draws.csv"\nreport = "%s/out/draws.md"\n'
                 'lock = "%s/out/draws-lock.json"\n' % (base, base, base))
    run(os.path.join(REPO, "configs", "core-draws.toml"), monkeypatch, override)
    rows = drawn(base)
    assert rows[0][:2] == (184, "smoke")
    assert [r[3] for r in rows[1:5]] == ["end-to-end", "steering-rules", "steering-heuristic",
                                        "not-stated"]
    assert sum(1 for r in rows if r[1] == "fifth") == 20
    numbers = [r[0] for r in rows]
    assert len(set(numbers)) == len(numbers) == 26 and 18 not in numbers
