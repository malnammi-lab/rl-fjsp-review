"""Describe the searched corpus with the numbers the method section quotes about it.

Three tables count document types and years, abstract sources, and the abstracts the index
did not serve, by publisher and publisher group. A fourth checks whether the index searched
those abstracts or only the titles. A fifth groups the records that share a normalized
title; none is removed. Facet terms match whole words, as in the source's phrase search.
Reads datasets/references.json and the facets in configs/search-query.toml. Writes
results/corpus/corpus-profile.md. The abstracts are withheld from the released records, so the
step runs only where the authors' copy is in place (src/withheld.py); in a clone it stops, and
its committed report stands.

Run: python runners/run_all.py --only corpus-profile
"""

import argparse
import os
import sys
import tomllib
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus, withheld  # noqa: E402
# One definition of the groups and kinds, shared with runners/deduplicate.py.
from src.duplicates import KINDS as REPEAT_KINDS, authors_agree, repeat_kind, title_repeats  # noqa: E402,F401
from src.terms import facet_terms, has_any, norm  # noqa: E402

SERVED = "openalex"   # the abstract_source value for an abstract the index itself served


def resolve(path):
    return os.path.normpath(os.path.join(REPO, path))


def source_of(record):
    return (record.raw.get("abstract_source") or "").strip() or "none"


def types_and_years(records):
    years = [r.year for r in records if r.year]
    return Counter(r.work_type or "(untyped)" for r in records), (min(years) if years else None), (max(years) if years else None)


def abstract_sources(records):
    return Counter(source_of(r) for r in records)


def missing_at_source(records):
    """(publisher, records, of which not served by the index), largest gap first."""
    total, missing = Counter(), Counter()
    for r in records:
        pub = r.publisher or "(no publisher)"
        total[pub] += 1
        if source_of(r) != SERVED:
            missing[pub] += 1
    return sorted(((p, total[p], missing[p]) for p in missing), key=lambda x: (-x[2], x[0]))


def retrieval_check(records, method, problem):
    """How the records whose abstract the index did not serve can have been retrieved."""
    def both(text):
        return has_any(method, text) and has_any(problem, text)

    out = Counter()
    for r in records:
        if source_of(r) == SERVED:
            continue
        out["not served"] += 1
        title = norm(r.title)
        if both(title):
            out["title carries both facets"] += 1
            continue
        out["title lacks a facet"] += 1
        if not r.abstract.strip():
            out["title lacks a facet; no abstract from any source"] += 1
        elif both(title + " " + norm(r.abstract)):
            out["title lacks a facet; the filled abstract carries both"] += 1
        else:
            out["title lacks a facet; the filled abstract does not carry both"] += 1
    return out


def missing_by_group(records, groups):
    """Records and unserved abstracts summed into named publisher groups. A record joins
    the group whose prefix its publisher's name starts with (a publisher's imprints are
    listed under separate names). Returns [(group, records, not served, publishers in it)]
    in the config's order."""
    out = []
    for name, prefix in groups.items():
        rows = [r for r in records if (r.publisher or "").lower().startswith(prefix.lower())]
        out.append((name, len(rows), sum(1 for r in rows if source_of(r) != SERVED),
                    sorted({r.publisher for r in rows})))
    return out


RETRIEVAL_ORDER = ["not served", "title carries both facets", "title lacks a facet",
                   "title lacks a facet; the filled abstract carries both",
                   "title lacks a facet; the filled abstract does not carry both",
                   "title lacks a facet; no abstract from any source"]


def render_repeats(repeats, prefixes=()):
    out = ["", "## Records sharing a title", "",
           "Candidate duplicates: records the source holds under separate ids, grouped by "
           "normalised title. None is removed here.", "",
           "| Measure | Count |", "|---|---|",
           "| Groups | %d |" % len(repeats),
           "| Records in them | %d |" % sum(len(g) for g in repeats),
           "| Records beyond the first of each group | %d |" % sum(len(g) - 1 for g in repeats)]
    if not repeats:
        return out
    kinds = [(g, repeat_kind(g, prefixes), authors_agree(g)) for g in repeats]
    out += ["", "By kind, the first that applies in this order, and whether the first authors "
            "agree (the kinds are defined in `src/duplicates.py`, `KINDS`; "
            "repository DOI prefixes in `configs/corpus-profile.toml`):", "",
            "| Kind | Meaning | Groups | Records beyond the first | First authors agree | Disagree | Unknown |",
            "|---|---|---|---|---|---|---|"]
    for kind, meaning in REPEAT_KINDS:
        rows = [(g, a) for g, k, a in kinds if k == kind]
        out.append("| %s | %s | %d | %d | %d | %d | %d |" % (
            kind, meaning, len(rows), sum(len(g) - 1 for g, _ in rows),
            sum(1 for _, a in rows if a == "yes"), sum(1 for _, a in rows if a == "no"),
            sum(1 for _, a in rows if a == "unknown")))
    out += ["", "| Title | Records | Kind | First authors agree | First authors | Types | Years | DOIs |",
            "|---|---|---|---|---|---|---|---|"]
    for g, k, a in kinds:
        out.append("| %s | %d | %s | %s | %s | %s | %s | %s |" % (
            (g[0].title or "").replace("|", "/"), len(g), k, a,
            "; ".join(r.first_author or "(none)" for r in g),
            ", ".join(sorted({r.work_type or "(untyped)" for r in g})),
            ", ".join(sorted({str(r.year) for r in g if r.year})),
            "; ".join(r.doi or "(none)" for r in g)))
    return out


def render(n, types, y0, y1, sources, missing, retrieval, top, grouped=(), repeats=None,
           prefixes=()):
    out = ["# Corpus profile", "",
           "Generated by `runners/corpus_profile.py` from `configs/corpus-profile.toml`. "
           "Do not edit; regenerate.", "",
           "## Types and years", "",
           "%d records, published %s to %s." % (n, y0, y1), "",
           "| Document type | Records |", "|---|---|"]
    out += ["| %s | %d |" % (t, c) for t, c in types.most_common()]
    out += ["", "## Abstract sources", "",
            "`openalex` is an abstract the index served; any other value names the source "
            "that filled it; `none` means no source had one.", "",
            "| abstract_source | Records |", "|---|---|"]
    out += ["| %s | %d |" % (s, c) for s, c in sources.most_common()]
    out += ["", "## Abstracts the index did not serve, by publisher (top %d)" % top, "",
            "| Publisher | Records | Not served by the index | Share |", "|---|---|---|---|"]
    for pub, tot, miss in missing[:top]:
        out.append("| %s | %d | %d | %.0f%% |" % (pub, tot, miss, 100.0 * miss / tot))
    if grouped:
        out += ["", "Summed by publisher group (a publisher joins the group whose name prefix "
                "its own name starts with; `configs/corpus-profile.toml`):", "",
                "| Group | Records | Not served by the index | Share | Publishers |",
                "|---|---|---|---|---|"]
        for name, tot, miss, pubs in grouped:
            share = ("%.0f%%" % (100.0 * miss / tot)) if tot else ""
            out.append("| %s | %d | %d | %s | %s |" % (name, tot, miss, share, "; ".join(pubs)))
        out.append("| All groups | %d | %d | | |" % (sum(g[1] for g in grouped), sum(g[2] for g in grouped)))
    out += ["", "## Retrieval check on the records whose abstract the index did not serve", "",
            "| Records | Count |", "|---|---|"]
    for k in RETRIEVAL_ORDER:
        label = ("&nbsp;&nbsp; " + k.split("; ", 1)[1]) if k.startswith("title lacks a facet; ") else k
        out.append("| %s | %d |" % (label, retrieval.get(k, 0)))
    if repeats is not None:
        out += render_repeats(repeats, prefixes)
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "corpus-profile.toml"))
    args = parser.parse_args()
    with open(args.config, "rb") as fh:
        cfg = tomllib.load(fh)

    path = resolve(cfg["inputs"]["corpus"])
    withheld.require(path, "corpus-profile")
    records = corpus.load_references(path, abstracts=True)
    with open(resolve(cfg["inputs"]["facets"]), "rb") as fh:
        facets = tomllib.load(fh)
    method, problem = facet_terms(facets["method"]), facet_terms(facets["problem"])

    types, y0, y1 = types_and_years(records)
    sources = abstract_sources(records)
    missing = missing_at_source(records)
    retrieval = retrieval_check(records, method, problem)
    top = cfg["report"]["top_publishers"]
    grouped = missing_by_group(records, cfg.get("publisher_groups", {}))
    repeats = title_repeats(records)

    out = resolve(cfg["outputs"]["report"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(len(records), types, y0, y1, sources, missing, retrieval, top,
                        grouped, repeats,
                        cfg.get("duplicates", {}).get("repository_doi_prefixes", [])))

    print("records           : %d (%s to %s)" % (len(records), y0, y1))
    print("abstract sources  : " + ", ".join("%s %d" % kv for kv in sources.most_common()))
    print("not served        : %d; title lacks a facet but filled abstract carries both: %d"
          % (retrieval.get("not served", 0),
             retrieval.get("title lacks a facet; the filled abstract carries both", 0)))
    print("sharing a title   : %d groups, %d records, %d beyond the first of each"
          % (len(repeats), sum(len(g) for g in repeats), sum(len(g) - 1 for g in repeats)))
    print("wrote %s" % os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
