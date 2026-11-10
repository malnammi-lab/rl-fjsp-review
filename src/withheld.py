"""The abstracts this repository withholds, and the authors' copies that hold them.

The record file of the search (references.json) is released with each abstract replaced by its
SHA-256, in an `abstract_sha256` field. The abstracts came from OpenAlex, Scopus, Springer
Nature, Semantic Scholar and publishers' pages, and not every one of them may be redistributed.
The authors keep the file as it was written, with its abstracts, and `configs/withheld.toml`
records the released file's checksum.

A step that needs the abstracts takes them from the authors' copy, once the copy is checked
against the released file: the same records in the same order, every other field the same,
and each abstract the one whose SHA-256 the released record gives. Without the copy, as in a
clone, the abstracts are blank, and a step that cannot do without them stops (`require`).
Nothing here reads a file at import.
"""

import hashlib
import json
import os
import tomllib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(REPO, "configs", "withheld.toml")
FIELD = "abstract"
HASH = "abstract_sha256"
_tables = {}
_pairs = {}


def resolve(path):
    return os.path.normpath(os.path.join(REPO, path))


def rel(path):
    try:
        return os.path.relpath(path, REPO).replace(os.sep, "/")
    except ValueError:
        return path


def sha256_text(text):
    """The SHA-256 of a text's UTF-8 bytes, as runners/core_gather.py hashes a quote; "" for
    no text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else ""


def _key(path):
    return os.path.normcase(os.path.abspath(path))


def load(config=None):
    """{released file: the authors' copy} of the config's [abstracts], resolved, read once."""
    config = config or CONFIG
    if config not in _tables:
        with open(config, "rb") as fh:
            table = tomllib.load(fh).get("abstracts", {})
        _tables[config] = {resolve(a): resolve(b) for a, b in table.items()}
    return _tables[config]


def checksums(config=None):
    """{released file: (SHA-256 as written, SHA-256 as released)} of the config's [sha256],
    resolved, read once."""
    config = config or CONFIG
    if config not in _pairs:
        with open(config, "rb") as fh:
            table = tomllib.load(fh).get("sha256", {})
        _pairs[config] = {resolve(a): (b["written"], b["released"]) for a, b in table.items()}
    return _pairs[config]


def file_sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def stands_for(path, written, config=None):
    """Whether the file at `path` is the released form of the record file whose SHA-256 as
    written was `written`, as the config's [sha256] pairs them."""
    for released, (was, now) in checksums(config).items():
        if _key(released) == _key(path):
            return was == written and file_sha(path) == now
    return False


def original(path, config=None):
    """The authors' copy of a released record file, or None for a file whose abstracts this
    repository does not withhold."""
    for released, copy in load(config).items():
        if _key(released) == _key(path):
            return copy
    return None


def available(path, config=None):
    """Whether the abstracts of a record file can be read: the file withholds none, or the
    authors' copy is in place."""
    copy = original(path, config)
    return copy is None or os.path.isfile(copy)


def require(path, step, config=None):
    """Stop a step that cannot run without the abstracts of a record file, as in a clone."""
    if not available(path, config):
        raise SystemExit("%s reads the abstracts of %s, which this repository withholds "
                         "(datasets/MANIFEST.md, Files the authors keep). Its committed outputs "
                         "stand." % (step, rel(path)))


def abstracts(path, config=None):
    """{record number: abstract} from the authors' copy of `path`, checked against the released
    file record by record; None when the copy is absent or the file withholds nothing."""
    copy = original(path, config)
    if copy is None or not os.path.isfile(copy):
        return None
    for released_path, (written, _) in checksums(config).items():
        if _key(released_path) == _key(path) and file_sha(copy) != written:
            raise SystemExit("%s is not the file as written: its SHA-256 is not the one "
                             "configs/withheld.toml records. Restore it." % rel(copy))
    with open(path, encoding="utf-8") as fh:
        released = json.load(fh)["references"]
    with open(copy, encoding="utf-8") as fh:
        kept = json.load(fh)["references"]
    if len(released) != len(kept):
        raise SystemExit("%s holds %d records and %s %d: restore the one that changed."
                         % (rel(copy), len(kept), rel(path), len(released)))
    for r, k in zip(released, kept):
        same = ({f: v for f, v in r.items() if f != HASH}
                == {f: v for f, v in k.items() if f != FIELD})
        if not same or r.get(HASH, "") != sha256_text(k.get(FIELD) or ""):
            raise SystemExit("%s and %s differ in more than the abstract of record %s: restore "
                             "the one that changed." % (rel(copy), rel(path), k.get("number")))
    return {k.get("number"): k.get(FIELD) or "" for k in kept}


def merge(path, records, config=None):
    """Give each record (src/corpus.py, Record) its abstract from the authors' copy of `path`,
    in place; the records unchanged when the copy is absent. The records' `raw` dicts are left
    as released."""
    texts = abstracts(path, config)
    if texts is not None:
        for r in records:
            r.abstract = texts.get(r.number, "")
    return records
