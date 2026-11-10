"""Turn the facet vocabulary into an OQL query file for the acquisition tool.

The query is (any [method] term) AND (any [problem] term) over titles and abstracts, within
the config's [limits]. Reads configs/search-query.toml. Writes search-query.md (the query
and its prose record) and search-query-groupby.md (its count per year, a cheap check before
fetching), beside the config or in --out-dir. --with-term, --without-cluster and
--without-term render a variant for sizing the query; a variant needs --out-dir.

Run: python runners/run_all.py --only build-query
"""

import argparse
import copy
import os
import tomllib
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FACETS = ("method", "problem")

# The acquisition tool sends a GET up to this many bytes and switches to POST above it.
GET_QUERY_LIMIT = 7000


def rel(path):
    """Repo-relative path for printing; absolute when the path is on another drive.

    os.path.relpath raises on Windows when the two paths sit on different drives, and
    a runner must not crash on a progress line after its real work has succeeded.
    """
    try:
        return os.path.relpath(path, REPO)
    except ValueError:
        return path


def unique(seq):
    seen, out = set(), []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def facet_terms(table):
    """All terms across a facet's clusters, in file order, deduplicated."""
    return unique(term for cluster in table.values() for term in cluster)


def check_facets(cfg):
    """Refuse a config the query cannot be rendered from: a facet table that is missing, a
    cluster that is not a list of non-empty strings (a string would be split into
    one-letter terms), or a facet with no term (it would render as `has ()`)."""
    for facet in FACETS:
        table = cfg.get(facet)
        if not isinstance(table, dict) or not table:
            raise SystemExit("the config has no [%s] table of clusters" % facet)
        for name, cluster in table.items():
            if not isinstance(cluster, list) or not all(isinstance(t, str) and t.strip()
                                                         for t in cluster):
                raise SystemExit("[%s] %s must be a list of non-empty strings" % (facet, name))
        if not facet_terms(table):
            raise SystemExit("[%s] has no term" % facet)


def or_block(terms):
    """OQL disjunction. Quoted terms match exactly, which is what listed variants want."""
    quoted = ['"' + t.replace('"', "") + '"' for t in terms]
    return "(" + " or ".join(quoted) + ")"


def with_terms(cfg, additions):
    """A copy of the facet config with candidate terms appended, for sizing a candidate.

    `additions` is a list of (facet, term). The committed config is never changed; the
    candidate goes into a cluster of its own, named `candidate`, at the end of its facet.
    """
    out = copy.deepcopy(cfg)
    for facet, term in additions:
        if facet not in FACETS:
            raise SystemExit("--with-term: facet must be method or problem, not %r" % facet)
        out[facet].setdefault("candidate", [])
        if term not in facet_terms(out[facet]):
            out[facet]["candidate"].append(term)
    return out


def without(cfg, clusters=(), terms=()):
    """A copy of the facet config with whole clusters and single terms removed, for
    measuring what each adds to the record count.

    `clusters` is a list of (facet, cluster) and `terms` a list of (facet, term). A name the
    config does not hold is refused, so a typing slip cannot pass for a measurement, and so
    is a removal that leaves a facet with no term.
    """
    out = copy.deepcopy(cfg)
    for facet, cluster in clusters:
        if facet not in FACETS:
            raise SystemExit("--without-cluster: facet must be method or problem, not %r" % facet)
        if cluster not in out.get(facet, {}):
            raise SystemExit("--without-cluster: [%s] has no cluster %r" % (facet, cluster))
        del out[facet][cluster]
    for facet, term in terms:
        if facet not in FACETS:
            raise SystemExit("--without-term: facet must be method or problem, not %r" % facet)
        found = False
        for name, cluster in out.get(facet, {}).items():
            if term in cluster:
                out[facet][name] = [t for t in cluster if t != term]
                found = True
        if not found:
            raise SystemExit("--without-term: [%s] has no term %r" % (facet, term))
    for facet in FACETS:
        if not facet_terms(out.get(facet, {})):
            raise SystemExit("the removals leave [%s] with no term" % facet)
    return out


def build(cfg):
    check_facets(cfg)
    method = facet_terms(cfg["method"])
    problem = facet_terms(cfg["problem"])
    limits = cfg.get("limits", {})

    clauses = [
        "works",
        "where title_and_abstract has " + or_block(method),
        "and title_and_abstract has " + or_block(problem),
    ]
    types = limits.get("document_types") or []
    if types:
        clauses.append("and type is (" + " or ".join(types) + ")")
    langs = limits.get("languages") or []
    if langs:
        clauses.append("and language is (" + " or ".join(langs) + ")")
    if limits.get("year_from"):
        clauses.append("and year >= (%d)" % limits["year_from"])
    if limits.get("year_to"):
        clauses.append("and year <= (%d)" % limits["year_to"])
    return clauses, method, problem


def prose(cfg, method, problem, one_line_bytes, source="configs/search-query.toml"):
    """The record above the fenced query: what the query implements, its terms by group,
    its scope and its transport. Every count is taken from the config."""
    limits = cfg.get("limits", {})
    transport = "POST" if one_line_bytes > GET_QUERY_LIMIT else "GET"
    if not limits.get("year_from") and not limits.get("year_to"):
        year = "unrestricted"
    else:
        year = "%s to %s" % (limits.get("year_from") or "open", limits.get("year_to") or "open")
    types = ", ".join(limits.get("document_types") or ["all"])
    langs = ", ".join(limits.get("languages") or [])

    lines = [
        "# Search query: reinforcement learning for the flexible job shop",
        "",
        "Generated %s by `runners/build_query.py` from `%s`." % (date.today().isoformat(), source),
        "Do not edit this file by hand; edit the TOML and regenerate, so the query and its",
        "record cannot drift apart.",
        "",
        "## What the query is",
        "",
        "The query implements the two naming rules of the review protocol's eligibility",
        "criteria. A record is retrieved when its title or abstract carries a name of",
        "reinforcement learning, of one of its algorithms or of an adjacent term (the method",
        "facet, inclusion 2), and a name of the flexible job shop (the problem facet,",
        "inclusion 1). The terms are the criteria's closed lists, with every spelling or",
        "plural that no other term of the same group already matches. The source runs",
        "quoted terms as an exact search with no stemming, so a plural, or a spelling",
        "written as one word, is a term of its own. It reads a hyphen inside a quoted",
        "phrase as a space, so each name is written with spaces and also matches its",
        "hyphenated form; no term is a single hyphenated word, which the source reads as",
        "its parts anywhere in the text rather than as a phrase.",
        "",
        "## The terms",
        "",
        "| Facet | Group | Terms | Count |",
        "|---|---|---|---|",
    ]
    for facet in FACETS:
        for name, cluster in cfg[facet].items():
            lines.append("| %s | `%s` | %s | %d |" % (facet, name, "; ".join(cluster), len(cluster)))
    lines += [
        "",
        "The method facet has %d distinct terms and the problem facet %d."
        % (len(method), len(problem)),
        "",
        "## Scope",
        "",
        "- Source: OpenAlex alone, searched in titles and abstracts.",
        "- Publication year: %s." % year,
        "- Document types: %s." % types,
    ]
    if langs:
        lines.append("- Language: %s." % langs)
    else:
        lines.append("- Language: not restricted in the query; decided at screening.")
    lines += [
        "",
        "## Transport",
        "",
    ]
    if transport == "POST":
        lines += [
            "The collapsed query is %d bytes, above the %d-byte GET limit, so the"
            % (one_line_bytes, GET_QUERY_LIMIT),
            "acquisition tool sends it as a POST body. Expected; it changes nothing about the",
            "query.",
        ]
    else:
        lines += ["The collapsed query is %d bytes and is sent as a GET." % one_line_bytes]
    return "\n".join(lines) + "\n"


def parse_pairs(items, flag, sep):
    """FACET<sep>NAME arguments as (facet, name) pairs. NAME may list several names separated
    by semicolons, so that one variant adds or removes a name with all its spellings, as in
    method=policy;policies."""
    pairs = []
    for item in items:
        facet, found, names = item.partition(sep)
        parts = [n.strip() for n in names.split(";")]
        if not found or not facet.strip() or not all(parts):
            raise SystemExit("%s takes FACET%sNAME[;NAME...], got %r" % (flag, sep, item))
        pairs += [(facet.strip(), name) for name in parts]
    return pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "search-query.toml"))
    parser.add_argument("--with-term", action="append", default=[], metavar="FACET=TERM[;TERM]",
                        help="render a variant with TERM added to FACET (method or problem), "
                             "for sizing a candidate")
    parser.add_argument("--without-cluster", action="append", default=[],
                        metavar="FACET.CLUSTER",
                        help="render a variant without a whole group, for measuring what it "
                             "adds")
    parser.add_argument("--without-term", action="append", default=[], metavar="FACET=TERM[;TERM]",
                        help="render a variant without one term, or one name with all its "
                             "spellings, for measuring what it adds")
    parser.add_argument("--out-dir",
                        help="where to write the query files (default: beside the config); "
                             "required for a variant")
    args = parser.parse_args()

    with open(args.config, "rb") as fh:
        cfg = tomllib.load(fh)
    check_facets(cfg)

    variant = bool(args.with_term or args.without_cluster or args.without_term)
    if variant and not args.out_dir:
        raise SystemExit("a variant (--with-term, --without-cluster, --without-term) needs "
                         "--out-dir, so the committed query files are not overwritten")
    if args.without_cluster or args.without_term:
        cfg = without(cfg, parse_pairs(args.without_cluster, "--without-cluster", "."),
                      parse_pairs(args.without_term, "--without-term", "="))
    if args.with_term:
        cfg = with_terms(cfg, parse_pairs(args.with_term, "--with-term", "="))

    clauses, method, problem = build(cfg)
    one_line = " ".join(" ".join(clauses).split())
    nbytes = len(one_line.encode("utf-8"))

    out_dir = os.path.abspath(args.out_dir) if args.out_dir else os.path.dirname(os.path.abspath(args.config))
    os.makedirs(out_dir, exist_ok=True)
    source = rel(os.path.abspath(args.config)).replace(os.sep, "/")
    header = prose(cfg, method, problem, nbytes, source)
    if variant:
        flags = (["--with-term %s" % x for x in args.with_term]
                 + ["--without-cluster %s" % x for x in args.without_cluster]
                 + ["--without-term %s" % x for x in args.without_term])
        header = ("# VARIANT, not the search\n\n"
                  "Rendered with `%s` to size a variant of the query. The\n"
                  "committed query is `configs/search-query.md`.\n\n" % " ".join(flags)) + header

    query_path = os.path.join(out_dir, "search-query.md")
    with open(query_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(header + "\n```\n" + "\n".join(clauses) + "\n```\n")

    group_path = os.path.join(out_dir, "search-query-groupby.md")
    with open(group_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(
            "# Sanity check: year distribution of the corpus\n\n"
            "Run this before fetching anything. One cheap request returns the number of\n"
            "records the query matches, by publication year, and their total.\n\n"
            "Same query as search-query.md with a group-by appended.\n\n"
            "```\n" + "\n".join(clauses) + "\ngroup by publication_year\n```\n"
        )

    print("method terms : %d" % len(method))
    print("problem terms: %d" % len(problem))
    print("query bytes  : %d  (%s)" % (nbytes, "POST" if nbytes > GET_QUERY_LIMIT else "GET"))
    print("wrote        : %s" % rel(query_path))
    print("wrote        : %s" % rel(group_path))


if __name__ == "__main__":
    main()
