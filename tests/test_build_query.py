"""Tests for rendering the query, for the variants used to size it, and for the agreement of
the committed query with the protocol's closed lists."""

import os
import re
import sys
import tomllib

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

import build_query as bq  # noqa: E402

CFG = {
    "method": {"explicit": ["reinforcement learning"]},
    "problem": {"shop": ["job shop scheduling"]},
    "limits": {"document_types": ["article", "conference-paper"]},
}

CFG2 = {
    "method": {"names": ["reinforcement learning"], "algorithms": ["ppo", "dqn"]},
    "problem": {"names": ["flexible job shop"]},
    "limits": {"document_types": ["article", "conference-paper"]},
}

QUERY = os.path.join(REPO, "configs", "search-query.toml")
PROTOCOL = os.path.join(REPO, "protocol.md")

# The names of the protocol's inclusions 2 (method) and 1 (problem), each of which the
# committed query lists.
PROTOCOL_NAMES = {
    "method": ["reinforcement learning", "q-learning", "q-network", "deep q-network", "dqn",
               "sarsa", "reinforce", "policy gradient", "actor-critic", "a2c", "a3c",
               "proximal policy optimization", "ppo", "trust region policy optimization", "trpo",
               "deep deterministic policy gradient", "ddpg", "twin delayed ddpg", "td3",
               "soft actor-critic", "sac", "temporal difference learning", "policy",
               "markov decision process", "mdp", "markov", "markovian", "decision process"],
    "problem": ["flexible job shop", "flexible assembly job shop", "flexible workshop", "fjs",
                "fjsp", "fjssp", "dfjsp", "dfjssp", "mofjsp", "fjspt", "fajsp"],
}

# The protocol's candidates not adopted: never in the query unless the criteria name them.
CANDIDATES = ["rl", "drl", "marl", "hrl", "ddqn", "d3qn", "maddpg", "mappo", "pomdp", "smdp",
              "td learning", "learning to dispatch", "approximate dynamic programming", "fjss"]


def load(path):
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def folded(term):
    """A term as OpenAlex reads a quoted phrase: its words, a hyphen read as a space."""
    return " ".join(re.findall(r"[^\W_]+", term.lower()))


def test_build_renders_both_facets_and_limits():
    clauses, method, problem = bq.build(CFG)
    assert clauses[1] == 'where title_and_abstract has ("reinforcement learning")'
    assert clauses[2] == 'and title_and_abstract has ("job shop scheduling")'
    assert clauses[3] == "and type is (article or conference-paper)"


def test_candidate_is_appended_without_changing_the_original():
    variant = bq.with_terms(CFG, [("problem", "dynamic job shop")])
    _, _, problem = bq.build(variant)
    assert problem == ["job shop scheduling", "dynamic job shop"]
    assert bq.build(CFG)[2] == ["job shop scheduling"]


def test_candidate_already_present_is_not_duplicated_and_bad_facet_is_refused():
    variant = bq.with_terms(CFG, [("problem", "job shop scheduling")])
    assert bq.build(variant)[2] == ["job shop scheduling"]
    with pytest.raises(SystemExit):
        bq.with_terms(CFG, [("venue", "x")])


def test_without_removes_a_group_or_a_term_and_leaves_the_original():
    assert bq.build(bq.without(CFG2, clusters=[("method", "algorithms")]))[1] == ["reinforcement learning"]
    assert bq.build(bq.without(CFG2, terms=[("method", "ppo")]))[1] == ["reinforcement learning", "dqn"]
    assert bq.build(CFG2)[1] == ["reinforcement learning", "ppo", "dqn"]


def test_a_flag_can_name_several_terms_of_one_facet():
    assert bq.parse_pairs(["method=policy;policies"], "--without-term", "=") == [
        ("method", "policy"), ("method", "policies")]
    assert bq.parse_pairs(["method.adjacent"], "--without-cluster", ".") == [("method", "adjacent")]
    for bad in ("method=policy;", "method=", "=policy", "policy"):
        with pytest.raises(SystemExit):
            bq.parse_pairs([bad], "--without-term", "=")


@pytest.mark.parametrize("kwargs", [
    {"clusters": [("method", "nope")]},          # no such group
    {"clusters": [("venue", "names")]},          # no such facet
    {"terms": [("method", "drl")]},              # no such term
    {"terms": [("venue", "ppo")]},
    {"clusters": [("problem", "names")]},        # leaves the problem facet empty
    {"terms": [("problem", "flexible job shop")]},
])
def test_without_refuses_unknown_names_and_an_emptied_facet(kwargs):
    with pytest.raises(SystemExit):
        bq.without(CFG2, **kwargs)


@pytest.mark.parametrize("cfg", [
    {"problem": {"names": ["flexible job shop"]}},                                    # no method
    {"method": {}, "problem": {"names": ["flexible job shop"]}},                      # empty table
    {"method": {"names": "reinforcement learning"}, "problem": {"names": ["fjsp"]}},  # a string
    {"method": {"names": ["", "ppo"]}, "problem": {"names": ["fjsp"]}},               # an empty term
    {"method": {"names": []}, "problem": {"names": ["fjsp"]}},                        # no term
])
def test_check_facets_refuses_a_config_the_query_cannot_be_rendered_from(cfg):
    with pytest.raises(SystemExit):
        bq.check_facets(cfg)


def test_prose_is_the_restarts_record_with_no_first_round_text():
    _, method, problem = bq.build(CFG2)
    text = bq.prose(CFG2, method, problem, 100)
    assert "| method | `algorithms` | ppo; dqn | 2 |" in text
    assert "The method facet has 3 distinct terms and the problem facet 1." in text
    assert "- Language: not restricted in the query; decided at screening." in text
    assert "sent as a GET" in text and "POST" in bq.prose(CFG2, method, problem, 8000)
    for old in ("derivation", "comparator", "seed", "mined", "citation chasing", "1994"):
        assert old not in text.lower(), old


def test_main_writes_two_files_and_marks_a_variant(tmp_path, monkeypatch):
    cfg_path = tmp_path / "q.toml"
    cfg_path.write_text('[method]\nnames = ["reinforcement learning"]\nalgorithms = ["ppo"]\n'
                        '[problem]\nnames = ["flexible job shop"]\n'
                        '[limits]\ndocument_types = ["article"]\n', encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["build_query.py", "--config", str(cfg_path)])
    bq.main()
    assert sorted(os.listdir(tmp_path)) == ["q.toml", "search-query-groupby.md", "search-query.md"]
    assert not (tmp_path / "search-query.md").read_text(encoding="utf-8").startswith("# VARIANT")

    out = tmp_path / "variant"
    monkeypatch.setattr(sys, "argv", ["build_query.py", "--config", str(cfg_path),
                                      "--without-term", "method=ppo", "--out-dir", str(out)])
    bq.main()
    assert sorted(os.listdir(out)) == ["search-query-groupby.md", "search-query.md"]
    text = (out / "search-query.md").read_text(encoding="utf-8")
    assert text.startswith("# VARIANT, not the search") and "--without-term method=ppo" in text
    assert 'has ("reinforcement learning")' in text and '"ppo"' not in text

    monkeypatch.setattr(sys, "argv", ["build_query.py", "--config", str(cfg_path),
                                      "--with-term", "method=drl"])
    with pytest.raises(SystemExit):
        bq.main()


def test_the_committed_query_is_the_protocols_closed_lists():
    cfg = load(QUERY)
    bq.check_facets(cfg)
    assert set(cfg) == {"method", "problem", "limits"}
    every = []
    for facet in bq.FACETS:
        terms = [t for cluster in cfg[facet].values() for t in cluster]
        assert all(t == t.lower().strip() for t in terms)
        assert len(terms) == len(set(terms)), "a term is listed twice in [%s]" % facet
        # Every name, as OpenAlex reads it; a hyphenated name is listed with a space.
        read = {folded(t) for t in terms}
        assert [n for n in PROTOCOL_NAMES[facet] if folded(n) not in read] == []
        # OpenAlex reads a quoted single hyphenated word as its parts anywhere in the text,
        # not as a phrase, so no term may be one; and a term whose hyphen is read as a space
        # would repeat its spaced form.
        assert [t for t in terms if "-" in t] == []
        every += terms
    assert [c for c in CANDIDATES if folded(c) in {folded(t) for t in every}] == []
    limits = cfg["limits"]
    assert limits["document_types"] == ["article", "conference-paper"]
    assert not limits.get("languages") and not limits.get("year_from") and not limits.get("year_to")


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def protocol_terms():
    """The terms of the protocol's table of the query's terms, in table order. The table is
    found by its header cells, so a formatter that pads the columns changes nothing."""
    with open(PROTOCOL, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    starts = [i for i, line in enumerate(lines)
              if line.lstrip().startswith("|") and cells(line) == ["Group", "Terms"]]
    assert starts, "the protocol has no table headed Group | Terms"
    terms = []
    for line in lines[starts[0] + 1:]:
        if not line.lstrip().startswith("|"):
            break
        row = cells(line)
        if all(set(c) <= set("-: ") for c in row):     # the separator row
            continue
        terms += [t.strip() for t in row[1].split(";")]
    return terms


@pytest.mark.skipif(not os.path.isfile(PROTOCOL),
                    reason="protocol.md is not in this copy of the repository")
def test_the_protocols_table_of_terms_equals_the_committed_query():
    cfg = load(QUERY)
    committed = [t for facet in bq.FACETS for cluster in cfg[facet].values() for t in cluster]
    assert sorted(protocol_terms()) == sorted(committed)
