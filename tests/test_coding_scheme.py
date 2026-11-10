"""Tests for the map's coding scheme: the schema the acquisition tool reads
(configs/map.toml), the rules the models read (datasets/coding-scheme.md, Part A), and the
protocol's table of the map's axes (protocol.md, Data extraction)."""

import os
import re
import tomllib

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(REPO, "configs", "map.toml")
SCHEME = os.path.join(REPO, "datasets", "coding-scheme.md")
PROTOCOL = os.path.join(REPO, "protocol.md")

# The axes whose reply quotes the record, and those whose scheme gives a default code
# instead of allowing `not-stated` (protocol, Data extraction).
QUOTED = ["learner_depth", "policy_role", "readiness_claim"]
WITH_A_DEFAULT = ["domain", "hybridization", "readiness_claim"]


def schema():
    with open(SCHEMA, "rb") as fh:
        return tomllib.load(fh)["axes"]


def part_a():
    """Part A of the scheme, from its heading to the next heading of its level: the
    section the coding task sends to the models."""
    with open(SCHEME, encoding="utf-8") as fh:
        text = fh.read()
    start = text.index("\n## Part A, the map")
    end = text.find("\n## ", start + 1)
    return text[start:end if end > 0 else len(text)]


def sections():
    """{axis: its section of Part A}, in the scheme's order."""
    parts = re.split(r"^### `([a-z_]+)`.*$", part_a(), flags=re.M)
    return dict(zip(parts[1::2], parts[2::2]))


def bullet(section, code):
    """The text of the bullet that defines `code` in an axis's section, or None."""
    found = re.search(r"^- `%s`:(.*?)(?=^- |\Z)" % re.escape(code), section, re.M | re.S)
    return found.group(1) if found else None


def test_the_schema_has_fifteen_axes_each_with_distinct_codes():
    axes = schema()
    assert len(axes) == 15
    for name, spec in axes.items():
        codes = spec["codes"]
        assert codes and len(set(codes)) == len(codes), name
        assert "not-stated" not in codes, name
        assert set(spec.get("alone", [])) <= set(codes), name
        assert set(spec.get("no_quote", [])) <= set(codes), name
        assert spec.get("multi", False) or not spec.get("alone"), name


def test_part_a_names_every_axis_and_every_code_in_backticks():
    text, axes = part_a(), schema()
    missing = [name for name in axes if "`%s`" % name not in text]
    missing += ["%s: %s" % (name, code) for name, spec in axes.items()
                for code in spec["codes"] if "`%s`" % code not in text]
    assert missing == []


def test_every_axis_has_a_section_with_a_bullet_for_each_of_its_codes():
    found, axes = sections(), schema()
    assert list(found) == list(axes)
    undefined = ["%s: %s" % (name, code) for name, spec in axes.items()
                 for code in spec["codes"] if bullet(found[name], code) is None]
    assert undefined == []


def test_each_sections_heading_gives_its_kind():
    headings = re.findall(r"^### `([a-z_]+)` \((one code|a list)", part_a(), flags=re.M)
    axes = schema()
    assert [name for name, _ in headings] == list(axes)
    for name, kind in headings:
        assert (kind == "a list") == bool(axes[name].get("multi")), name


def test_the_scheme_marks_alone_exactly_the_codes_the_schema_does():
    found = sections()
    for name, spec in schema().items():
        for code in spec["codes"]:
            marked = "Alone." in bullet(found[name], code)
            assert marked == (code in spec.get("alone", [])), "%s: %s" % (name, code)


def test_quotes_are_asked_for_the_role_the_learner_and_the_readiness_claim():
    axes = schema()
    assert sorted(name for name, spec in axes.items() if spec.get("quote")) == QUOTED
    assert axes["readiness_claim"]["no_quote"] == ["none"]


def test_only_the_axes_with_a_default_refuse_not_stated():
    axes, found = schema(), sections()
    refused = sorted(name for name, spec in axes.items() if not spec.get("not_stated", True))
    assert refused == WITH_A_DEFAULT
    for name in WITH_A_DEFAULT:
        assert "The default" in found[name], name


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def protocol_table():
    """{axis: (kind, codes, codes marked alone)} from the protocol's table headed
    Axis | Question | Kind | Codes. The protocol has one such table, in Data extraction; the
    last one is read. The table is found by its header cells, so a formatter that pads the
    columns changes nothing."""
    with open(PROTOCOL, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    starts = [i for i, line in enumerate(lines) if line.lstrip().startswith("|")
              and cells(line) == ["Axis", "Question", "Kind", "Codes"]]
    assert starts, "the protocol has no table headed Axis | Question | Kind | Codes"
    table = {}
    for line in lines[starts[-1] + 1:]:
        if not line.lstrip().startswith("|"):
            break
        row = cells(line)
        if all(set(c) <= set("-: ") for c in row):     # the separator row
            continue
        table[row[0].strip("`")] = (row[2], re.findall(r"`([a-z-]+)`", row[3]),
                                    re.findall(r"`([a-z-]+)` \(alone", row[3]))
    return table


@pytest.mark.skipif(not os.path.isfile(PROTOCOL),
                    reason="protocol.md is not in this copy of the repository")
def test_the_protocols_table_of_the_map_equals_the_schema():
    table, axes = protocol_table(), schema()
    assert list(table) == list(axes)
    for name, spec in axes.items():
        kind, codes, alone = table[name]
        assert kind == ("list" if spec.get("multi") else "single"), name
        assert codes == spec["codes"], name
        assert alone == spec.get("alone", []), name
