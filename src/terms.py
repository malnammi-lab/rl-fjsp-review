"""How a text is read for the names of the query: lower case, punctuation to spaces, and a
name found only as whole words, as the source's phrase search matches it."""

import re


def norm(text):
    """Lower case, punctuation to spaces, whitespace collapsed."""
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", (text or "").lower()).split())


def has_any(terms, text):
    """Whether any term occurs in `text` (already normalized) as whole words, as the source's
    phrase search matches. A substring test would find 'shop scheduling' inside 'flowshop
    scheduling', which the search does not."""
    padded = " " + text + " "
    return any(" " + norm(t) + " " in padded for t in terms)


def facet_terms(table):
    """Every term of a facet of configs/search-query.toml, its groups in order."""
    return [t for cluster in table.values() for t in cluster]
