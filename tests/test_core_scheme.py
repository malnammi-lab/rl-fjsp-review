"""Tests for the core's coding scheme: the questions of Part B as the agent reads them
(datasets/coding-scheme.md, Part B) against their machine-readable mirror
(configs/core-coding.toml), and section A against the map's axes (configs/map.toml)."""

import os
import re
import tomllib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(REPO, "configs", "core-coding.toml")
MAP = os.path.join(REPO, "configs", "map.toml")
SCHEME = os.path.join(REPO, "datasets", "coding-scheme.md")

SECTIONS = ["A", "B", "C", "D", "E", "F", "Q"]
TYPES = ["code", "codes", "number", "text", "level", "score", "count"]
SPECIAL = ["not-stated", "not-applicable", "not-reported"]
SCORES = ["1", "0.5", "0", "not-assessable"]
KINDS = {"code": "one code", "codes": "a list", "number": "a number", "level": "a level",
         "score": "a score", "count": "a count"}


def spec():
    with open(SPEC, "rb") as fh:
        return tomllib.load(fh)


def axes():
    with open(MAP, "rb") as fh:
        return tomllib.load(fh)["axes"]


def questions():
    """{ID: its table}, in the file's order, section A's completed from the map's axis."""
    table, found = spec()["questions"], axes()
    out = {}
    for qid, q in table.items():
        q = dict(q)
        if q.get("axis"):
            axis = found[q["axis"]]
            q["name"] = q["axis"]
            q["type"] = "codes" if axis.get("multi") else "code"
            q["codes"] = list(axis["codes"])
            q["alone"] = list(axis.get("alone", []))
            q["special"] = ["not-stated"] if axis.get("not_stated", True) else []
        out[qid] = q
    return out


def part_b():
    """Part B of the scheme, from its heading to the next heading of its level."""
    with open(SCHEME, encoding="utf-8") as fh:
        text = fh.read()
    start = text.index("\n## Part B, the core")
    end = text.find("\n## ", start + 1)
    return text[start:end if end > 0 else len(text)]


HEADING = re.compile(r"^#### ([A-Z]\d\d) `([a-z_]+)` \((.+)\)$", re.M)


def written():
    """{ID: (name, kind, the text under the heading)}, in Part B's order."""
    text = part_b()
    found = list(HEADING.finditer(text))
    out = {}
    for i, m in enumerate(found):
        end = found[i + 1].start() if i + 1 < len(found) else len(text)
        body = text[m.end():end]
        cut = re.search(r"^### ", body, re.M)
        out[m.group(1)] = (m.group(2), m.group(3), body[:cut.start()] if cut else body)
    return out


def bullet(body, code):
    """The text of the bullet that defines `code`, or None."""
    found = re.search(r"^- `%s`:(.*?)(?=^- |^\s*$|\Z)" % re.escape(code), body, re.M | re.S)
    return found.group(1) if found else None


def special_line(body):
    """The special answers a question's text allows, or None if it has no such line."""
    found = re.search(r"^Special answers: (.*)$", body, re.M)
    if not found:
        return None
    text = found.group(1).strip()
    return [] if text == "none." else re.findall(r"`([a-z-]+)`", text)


def kind_of(q):
    if q["type"] == "text":
        return "text, at most %d words" % q["words"]
    return KINDS[q["type"]]


def test_the_ids_run_in_order_within_each_section():
    found = questions()
    assert [qid[0] for qid in found] == sorted((qid[0] for qid in found), key=SECTIONS.index)
    for section in SECTIONS:
        ids = [qid for qid in found if qid[0] == section]
        assert ids == ["%s%02d" % (section, i) for i in range(1, len(ids) + 1)], section
        assert all(found[qid]["section"] == section for qid in ids), section


def test_section_a_asks_the_maps_fifteen_axes_in_the_maps_order():
    table = spec()["questions"]
    ids = [qid for qid in table if qid.startswith("A")]
    assert [table[qid]["axis"] for qid in ids] == list(axes())


def test_every_name_is_unique_and_no_derived_column_takes_one():
    found = questions()
    names = [q["name"] for q in found.values()]
    assert len(set(names)) == len(names)
    assert not set(spec().get("derived", {})) & set(names)


def test_every_question_is_well_formed():
    found, groups = questions(), spec().get("groups", {})
    bad = []
    for qid, q in found.items():
        kind = q.get("type")
        if kind not in TYPES:
            bad.append("%s: type %r" % (qid, kind))
            continue
        codes = q.get("codes", [])
        if kind in ("code", "codes", "level"):
            if not codes or len(set(codes)) != len(codes):
                bad.append("%s: codes" % qid)
            if any(c in SPECIAL and c != "not-applicable" for c in codes):
                bad.append("%s: a special answer among the codes" % qid)
        elif codes:
            bad.append("%s: codes on a %s question" % (qid, kind))
        if q.get("alone") and kind != "codes":
            bad.append("%s: alone on a %s question" % (qid, kind))
        if not set(q.get("alone", [])) <= set(codes):
            bad.append("%s: alone" % qid)
        if not set(q.get("special", [])) <= set(SPECIAL):
            bad.append("%s: special" % qid)
        if "default" in q:
            if q["default"] not in codes or "not-stated" in q.get("special", []):
                bad.append("%s: default" % qid)
        quotable = SCORES if kind == "score" else codes
        if not set(q.get("no_quote", [])) <= set(quotable):
            bad.append("%s: no_quote" % qid)
        if (kind == "text") != ("words" in q):
            bad.append("%s: words" % qid)
        if kind == "count":
            group = groups.get(q.get("group"))
            if not group or group.get("parent") != qid:
                bad.append("%s: group" % qid)
        if q["section"] != "A" and not q.get("label"):
            bad.append("%s: label" % qid)
    assert bad == []


def test_conditions_rules_and_derived_columns_name_real_questions_and_codes():
    found = questions()
    by_name = {q["name"]: q for q in found.values()}
    bad = []
    for qid, q in found.items():
        for cond in q.get("applies_when", []):
            other = by_name.get(cond.get("question"))
            keys = [k for k in ("codes", "min_codes", "above") if k in cond]
            if other is None or len(keys) != 1:
                bad.append("%s: condition %r" % (qid, cond))
            elif "codes" in cond and not set(cond["codes"]) <= set(other.get("codes", [])):
                bad.append("%s: condition codes" % qid)
            elif "min_codes" in cond and other["type"] != "codes":
                bad.append("%s: min_codes on a %s question" % (qid, other["type"]))
            elif "above" in cond and other["type"] != "number":
                bad.append("%s: above on a %s question" % (qid, other["type"]))
        if q.get("applies_when") and "not-applicable" not in q.get("special", []):
            bad.append("%s: a condition with no not-applicable" % qid)
    for rule in spec().get("rule", []):
        when, then = by_name.get(rule["if"]), by_name.get(rule["then"])
        if when is None or then is None:
            bad.append("rule %r: a question" % rule["name"])
            continue
        if not set(rule["if_codes"]) <= set(when.get("codes", [])):
            bad.append("rule %r: if_codes" % rule["name"])
        named = set(rule.get("then_codes", [])) | set(rule.get("then_not", []))
        if not named or not named <= set(then.get("codes", [])):
            bad.append("rule %r: then" % rule["name"])
    for name, d in spec().get("derived", {}).items():
        source = by_name.get(d["from"])
        if source is None:
            bad.append("derived %s: from" % name)
        elif "map" in d and set(d["map"]) != set(source["codes"]):
            bad.append("derived %s: map does not cover the codes" % name)
        elif "map" not in d and source["type"] != "codes":
            bad.append("derived %s: min_codes on a %s question" % (name, source["type"]))
    assert bad == []


def test_every_group_has_a_parent_count_and_coded_fields():
    found, bad = questions(), []
    for name, group in spec().get("groups", {}).items():
        parent = found.get(group.get("parent"))
        if not parent or parent["type"] != "count" or parent.get("group") != name:
            bad.append("%s: parent" % name)
        if group.get("answer") not in ("text", "code", "codes"):
            bad.append("%s: answer" % name)
        if (group.get("answer") == "text") != ("words" in group):
            bad.append("%s: words" % name)
        if group.get("answer") in ("code", "codes") and not group.get("codes"):
            bad.append("%s: codes" % name)
        if not isinstance(group.get("max_items"), int) or group["max_items"] < 1:
            bad.append("%s: max_items" % name)
        for field, f in group.get("fields", {}).items():
            if not f.get("codes") or len(set(f["codes"])) != len(f["codes"]):
                bad.append("%s.%s: codes" % (name, field))
    assert bad == []


def test_part_b_has_a_heading_for_every_question_but_section_as_in_order_with_its_kind():
    found = questions()
    expected = [(qid, q["name"], kind_of(q)) for qid, q in found.items() if q["section"] != "A"]
    text = written()
    assert [(qid, name, kind) for qid, (name, kind, _) in text.items()] == expected


def test_each_code_has_a_bullet_marked_alone_default_and_no_quote_as_the_spec_says():
    found, text, bad = questions(), written(), []
    for qid, (name, kind, body) in text.items():
        q = found[qid]
        if q["type"] not in ("code", "codes", "level"):
            continue
        for code in q["codes"]:
            b = bullet(body, code)
            if b is None:
                bad.append("%s: no bullet for %s" % (qid, code))
                continue
            for marker, held in (("Alone.", code in q.get("alone", [])),
                                 ("The default.", code == q.get("default")),
                                 ("No quote.", code in q.get("no_quote", []))):
                if (marker in b) != held:
                    bad.append("%s: %s %s" % (qid, code, marker))
    assert bad == []


def test_each_question_states_its_special_answers_and_its_conditions():
    found, text, bad = questions(), written(), []
    for qid, (name, kind, body) in text.items():
        q = found[qid]
        if special_line(body) != q.get("special", []):
            bad.append("%s: special answers %r" % (qid, special_line(body)))
        if ("Applies when" in body) != bool(q.get("applies_when")):
            bad.append("%s: applies when" % qid)
    assert bad == []


def test_a_count_names_its_items_fields_and_codes():
    found, text, bad = questions(), written(), []
    for name, group in spec()["groups"].items():
        parent = group["parent"]
        body = text[parent][2]
        if "`## %s.k %s`" % (parent, name) not in body:
            bad.append("%s: the item heading" % name)
        named = list(group.get("codes", []))
        for field, f in group.get("fields", {}).items():
            if "`%s:`" % field not in body:
                bad.append("%s: field %s" % (name, field))
            named += f["codes"]
        bad += ["%s: %s" % (name, c) for c in named if "`%s`" % c not in body]
    assert bad == []


def test_section_as_table_gives_each_axis_and_its_unquoted_codes():
    rows = re.findall(r"^\| (A\d\d) \| `([a-z_]+)` \| (.*?) ?\|$", part_b(), re.M)
    table = spec()["questions"]
    expected = [(qid, q["axis"], q.get("no_quote", [])) for qid, q in table.items()
                if q["section"] == "A"]
    assert [(qid, axis, re.findall(r"`([a-z-]+)`", cell)) for qid, axis, cell in rows] \
        == expected


def test_the_coverage_table_names_every_question():
    text = part_b()
    coverage = text[text.index("\n### Coverage"):]
    named = set(re.findall(r"\b([A-FQ]\d\d)\b", coverage))
    for letter, first, last in re.findall(r"\b([A-FQ])(\d\d) to [A-FQ](\d\d)\b", coverage):
        named |= {"%s%02d" % (letter, i) for i in range(int(first), int(last) + 1)}
    assert sorted(set(questions()) - named) == []


def test_part_b_keeps_part_as_parsers_and_the_sections_intact():
    text = part_b()
    assert not re.search(r"^### `", text, re.M)
    assert re.findall(r"^## .*$", text, re.M) == ["## Part B, the core"]
    sections = re.findall(r"^### Section ([A-Z]):", text, re.M)
    assert sections == SECTIONS


def test_part_b_is_plain_ascii():
    assert all(ord(c) < 128 for c in part_b())
