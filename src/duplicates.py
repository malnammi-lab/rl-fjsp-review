"""Records the source holds more than once, and the rule that decides which to keep.

The index can hold one paper under several OpenAlex ids: repository deposits of a journal
article, a DOI with a component suffix (`/pdf`, `.v1`), a copy without a DOI, the same DOI
on two works. Records that share a normalized title are grouped. Each group is classified
by the first kind in KINDS that describes it, with a check on whether the first authors
agree. `corpus_profile.py` reports the groups. `deduplicate.py` removes the extra records
of a group only when its kind is removable and every first author agrees.
"""

import re

KINDS = [
    ("same_doi", "two records carry the same DOI"),
    ("doi_variant", "one DOI is another followed by a suffix (/pdf, .v1)"),
    ("no_doi", "a record without a DOI beside one with a DOI"),
    ("repository_copy", "a repository deposit or preprint beside another record"),
    ("two_venues", "distinct publisher DOIs, none a repository deposit"),
]


def norm(text):
    """Lower case, punctuation to spaces, whitespace collapsed, as src/terms.py reads a text."""
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", (text or "").lower()).split())


def title_repeats(records):
    """Groups of records sharing a normalized title, largest first; singletons omitted."""
    groups = {}
    for r in records:
        key = norm(r.title)
        if key:
            groups.setdefault(key, []).append(r)
    repeated = [g for g in groups.values() if len(g) > 1]
    return sorted(repeated, key=lambda g: (-len(g), norm(g[0].title)))


def same_first_author(a, b):
    """True when the last name of one printed name appears in the other, so that
    'Jin Huang' and 'Huang Jin' agree; None when either name is missing or has no Latin
    letters (a name printed in another script cannot be compared here)."""
    ta, tb = norm(a).split(), norm(b).split()
    if not ta or not tb:
        return None
    return ta[-1] in tb or tb[-1] in ta


def authors_agree(group):
    """'yes' if every member's first author agrees with the first member's, 'no' if one
    disagrees, 'unknown' if a name is missing and none disagrees."""
    verdicts = [same_first_author(group[0].first_author, r.first_author) for r in group[1:]]
    if any(v is False for v in verdicts):
        return "no"
    return "unknown" if any(v is None for v in verdicts) else "yes"


def _doi(r):
    return (r.doi or "").lower()


def is_repository(r, prefixes):
    """A repository deposit or preprint: so typed by the index, or a DOI from a
    repository prefix (Zenodo, figshare, arXiv, SSRN in this project's config)."""
    doi = _doi(r)
    return (r.source_type == "repository" or r.work_type == "preprint"
            or any(doi.startswith(p.lower() + "/") for p in prefixes))


def _extends(a, b):
    """DOI b is DOI a followed by a component suffix."""
    return a != b and (b.startswith(a + "/") or b.startswith(a + "."))


def repeat_kind(group, prefixes):
    """The first kind in KINDS that describes a group of same-title records."""
    dois = [_doi(r) for r in group]
    present = [d for d in dois if d]
    if len(set(present)) < len(present):
        return "same_doi"
    if any(_extends(a, b) for a in present for b in present):
        return "doi_variant"
    if len(present) < len(dois):
        return "no_doi"
    if any(is_repository(r, prefixes) for r in group):
        return "repository_copy"
    return "two_venues"


def keep_order(r, group, prefixes):
    """Sort key for choosing the record to keep: a journal or conference record over a
    repository deposit, then a record with a DOI, then the base DOI over a suffixed one,
    then the higher-ranked record (lower rank), then the lower record number."""
    others = [_doi(o) for o in group if o is not r and _doi(o)]
    is_variant = any(_extends(o, _doi(r)) for o in others) if _doi(r) else False
    return (is_repository(r, prefixes), not _doi(r), is_variant,
            r.rank if r.rank else 10 ** 9, r.number)


def decide(records, prefixes, removable_kinds):
    """Apply the rule. Returns (removed, kept_groups): `removed` is a list of
    (record, kept_record, kind), and `kept_groups` a list of (group, kind, agree) for the
    groups left intact, so they can be reported and linked at full text."""
    removed, kept_groups = [], []
    for group in title_repeats(records):
        kind, agree = repeat_kind(group, prefixes), authors_agree(group)
        if kind in removable_kinds and agree == "yes":
            ordered = sorted(group, key=lambda r: keep_order(r, group, prefixes))
            keep = ordered[0]
            removed += [(r, keep, kind) for r in ordered[1:]]
        else:
            kept_groups.append((group, kind, agree))
    return removed, kept_groups
