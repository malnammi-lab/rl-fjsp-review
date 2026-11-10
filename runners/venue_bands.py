"""Give each record of the map a venue band and tier, for the core rule's steps 2 and 3.

Band 1 is the first of [bands] tiers (SJR Q1 or ICORE A*); band 2 is every other venue
(protocol, Two tiers). A venue is found in SJR by its ISSN-L. A possible conference is matched
to ICORE by name, and a person confirms each match. Reads `datasets/map.csv`,
`datasets/references.json`, the SJR and ICORE lists, which are not released, and
`datasets/venue-matches.csv`. Writes datasets/venue-bands.csv, and venue-matches-sheet.csv,
sheets-written.json and venue-bands.md in results/core/.

Run: python runners/run_all.py --only venue-bands
"""

import argparse
import csv
import os
import re
import sys
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import corpus  # noqa: E402
from runners.core_claims import as_written, record_written  # noqa: E402
from runners.screening_consensus import load_config, rel, resolve  # noqa: E402

# Words a venue's name shares with too many others to tell two venues apart.
STOP = {"a", "an", "and", "annual", "at", "conference", "congress", "for", "ieee", "acm", "in",
        "international", "national", "of", "on", "proceeding", "proceedings", "series",
        "symposium", "the", "to", "workshop"}
# Words that mark a venue's name as a conference's or a proceedings'.
EVENT = ("conference", "proceedings", "symposium", "congress", "workshop")
SJR_COLUMNS = ("Sourceid", "Title", "Type", "Issn", "SJR Best Quartile", "Country")
ICORE_COLUMNS = ("id", "title", "acronym", "source", "rank")
BANDS_FIELDS = ["number", "venue", "source_type", "issn_l", "sjr_sourceid", "sjr_title",
                "sjr_type", "sjr_quartile", "sjr_country", "icore_id", "icore_title",
                "icore_acronym", "icore_rank", "band", "tier", "basis"]
NOT_IN_SJR = "not in SJR"
NO_COUNTRY = "none given by SJR"
SHEET_FIELDS = ["key", "venue", "records", "icore_id", "icore_title", "icore_acronym",
                "icore_rank", "similarity", "confirmed", "note", "confirmed_by"]
ANSWER_FIELDS = ("confirmed", "note", "confirmed_by")
ANSWERS = ("yes", "no")


def write_csv(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for row in rows:
                w.writerow(row)
    except PermissionError:
        raise SystemExit("%s is open in another program (Excel locks it): close it and run "
                         "again." % path)


def issn_key(text):
    """An ISSN as SJR writes it: eight characters, no hyphen, X in upper case."""
    return (text or "").replace("-", "").strip().upper()


def read_sjr(path):
    """{ISSN: the SJR source}, over every ISSN SJR lists for a source; an ISSN listed for two
    sources keeps the first, the higher ranked. The file is SJR's download: separated by
    semicolons, with one header row, in which `Publisher` appears twice."""
    if not os.path.isfile(path):
        raise SystemExit("%s not found: SJR's list, downloaded from scimagojr.com ([inputs] "
                         "sjr of the config; datasets/MANIFEST.md)." % path)
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = csv.reader(fh, delimiter=";")
        head = [h.strip() for h in next(rows, [])]
        absent = [c for c in SJR_COLUMNS if c not in head]
        if absent:
            raise SystemExit("%s has no column %s: is it SJR's download?"
                             % (path, ", ".join(absent)))
        index = {}
        for row in rows:
            source = {h: v.strip() for h, v in zip(head, row)}
            for issn in source.get("Issn", "").split(","):
                key = issn_key(issn)
                if key and key not in index:
                    index[key] = source
    return index


def read_icore(path):
    """[{id, title, acronym, source, rank}] from ICORE's export, which has no header row: its
    first five columns are these."""
    if not os.path.isfile(path):
        raise SystemExit("%s not found: ICORE's list, exported from portal.core.edu.au "
                         "([inputs] icore of the config; datasets/MANIFEST.md)." % path)
    out = []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.reader(fh):
            if len(row) >= len(ICORE_COLUMNS) and row[0].strip().isdigit():
                out.append({k: v.strip() for k, v in zip(ICORE_COLUMNS, row)})
    if not out:
        raise SystemExit("%s holds no conference: is it ICORE's export?" % path)
    return out


def words(name):
    """A venue's name as a set of words: lower case, '&' read as 'and', its parenthesized
    part, numbers, ordinals, single letters and the words of STOP left out, and a final s
    dropped from a word of more than three letters."""
    text = re.sub(r"\([^)]*\)", " ", name or "").lower().replace("&", " and ")
    out = set()
    for w in re.findall(r"\b[a-z][a-z0-9@]*", text):
        if w in STOP or len(w) < 2:
            continue
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


def acronyms(name):
    """The acronyms a venue's name gives in parentheses, such as CASE in '... (CASE)', in
    lower case: the words there with two capitals or more."""
    out = set()
    for inner in re.findall(r"\(([^)]*)\)", name or ""):
        out |= {w.lower() for w in re.findall(r"[A-Za-z@]+", inner)
                if sum(c.isupper() for c in w) >= 2}
    return out


def similarity(a, b):
    """Words in common over words in either."""
    return len(a & b) / len(a | b) if a | b else 0.0


def propose(name, icore, threshold):
    """(the ICORE conference proposed as the venue's, its similarity), or None. A conference
    whose acronym the venue gives, in its parentheses or among its words, qualifies at half
    of `threshold`, and any other at `threshold`; a qualifying acronym comes first, then the
    higher similarity, then the lower ICORE id."""
    mine = words(name)
    named = acronyms(name) | mine
    best, best_rank = None, None
    for c in icore:
        s = similarity(mine, c.get("words") or words(c["title"]))
        shared = bool(c["acronym"]) and c["acronym"].lower() in named
        if not (s >= threshold or (shared and s >= threshold / 2)):
            continue
        rank = (shared and s >= threshold / 2, s, -int(c["id"]))
        if best_rank is None or rank > best_rank:
            best, best_rank = (c, s), rank
    return best


def event_like(record, source, name):
    """Whether a venue may be a conference: the corpus types it so, SJR does, or its name
    says so."""
    if record.source_type == "conference":
        return True
    if source and source.get("Type", "").lower() == "conference and proceedings":
        return True
    return any(w in name.lower() for w in EVENT)


def venue_key(record):
    """A venue's key: its ISSN-L, else its name; blank for a record without a venue."""
    issn = issn_key(record.raw.get("issn_l"))
    if issn:
        return "issn:" + issn
    return "name:" + record.venue if record.venue else ""


def blank():
    return {f: "" for f in ANSWER_FIELDS}


def answer_of(row):
    a = {f: (row.get(f) or "").strip() for f in ANSWER_FIELDS}
    a["confirmed"] = a["confirmed"].lower()
    return a


def read_rows(path):
    """[(line, {column: value})] of a sheet or confirmations file, column names in lower case;
    [] when the file does not exist."""
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            fields = [(f or "").strip().lower() for f in (reader.fieldnames or [])]
            rows = [{(k or "").strip().lower(): (v or "").strip() for k, v in row.items()
                     if k and isinstance(v, str)} for row in reader]
    except UnicodeDecodeError:
        raise SystemExit("%s is not UTF-8. In Excel, save it as 'CSV UTF-8 (Comma "
                         "delimited)'." % path)
    if not {"key", "confirmed"} <= set(fields):
        raise SystemExit("%s has no 'key' and 'confirmed' columns (header found: %s). Keep "
                         "the header row, and in Excel save it as 'CSV UTF-8 (Comma "
                         "delimited)'." % (path, ", ".join(fields) or "none"))
    return [(i + 2, row) for i, row in enumerate(rows)]


def read_confirmations(path, proposals):
    """({key: answer} for every row answering a current proposal, [(key, ICORE id) set
    aside]). A row whose venue is no longer proposed, or is now proposed another ICORE
    conference, answers nothing current and is set aside; its venue, if proposed, waits for a
    new answer. Refuses a venue answered twice, an answer other than yes or no, and an answer
    without who gave it."""
    answers, aside, bad = {}, [], []
    for line, row in read_rows(path):
        key = row.get("key", "")
        if not key:
            continue
        if key not in proposals or row.get("icore_id", "") != proposals[key][0]["id"]:
            aside.append((key, row.get("icore_id", "")))
            continue
        if key in answers:
            bad.append("%s given twice" % key)
            continue
        a = answer_of(row)
        if a["confirmed"] and a["confirmed"] not in ANSWERS:
            bad.append("%s: confirmed %r, not yes or no" % (key, a["confirmed"]))
            continue
        if a["confirmed"] and not a["confirmed_by"]:
            bad.append("%s: no confirmed_by" % key)
            continue
        answers[key] = a
    if bad:
        raise SystemExit("%s: %s" % (path, "; ".join(bad)))
    return answers, aside


def unsaved(sheet_path, saved, aside=()):
    """Keys whose answers on the sheet as it stands differ from the saved ones: a sheet filled
    in place and not yet saved under the confirmations' name. A row the saved file holds and
    sets aside, for the same venue and the same ICORE conference, counts as saved; an answer
    on a venue's new proposal does not."""
    if as_written(sheet_path):
        return []
    skip = set(aside)
    return [row["key"] for _, row in read_rows(sheet_path)
            if row.get("key") and (row["key"], row.get("icore_id", "")) not in skip
            and answer_of(row) != saved.get(row["key"], blank())]


def check_tiers(tiers):
    """Refuses [bands] tiers unless it is a list of tiers, each a list of quartiles or ranks,
    none empty, and no quartile or rank in two."""
    ok = isinstance(tiers, list) and tiers and all(
        isinstance(t, list) and t and all(isinstance(x, str) and x for x in t) for t in tiers)
    labels = [x for t in tiers for x in t] if ok else []
    if not ok or len(labels) != len(set(labels)):
        raise SystemExit("[bands] tiers must be a list of tiers, each a list of SJR quartiles "
                         "and ICORE ranks, none empty and none in two tiers: %r" % (tiers,))


def tier_of(label, tiers):
    """The tier, counted from 1, that holds `label` (an SJR quartile or an ICORE rank); the
    one after the last for a blank label or one in no tier."""
    for i, tier in enumerate(tiers, 1):
        if label and label in tier:
            return i
    return len(tiers) + 1


def describe_tiers(tiers):
    """The tiers in words: '1, Q1 or A*; 2, Q2 or A; 3, Q3; 4, every other venue'."""
    parts = ["%d, %s" % (i, " or ".join(t)) for i, t in enumerate(tiers, 1)]
    return "; ".join(parts + ["%d, every other venue" % (len(tiers) + 1)])


def decide(source, proposal, answer, tiers):
    """(band, tier, basis) of a venue: band '1' (the first tier) or '2' and its tier, both
    blank while its proposal waits for an answer. The better of its SJR quartile and its
    confirmed ICORE rank counts, and SJR's is the basis when the two give the same tier."""
    if proposal and not answer:
        return "", "", "pending"
    quartile = (source or {}).get("SJR Best Quartile", "")
    rank = proposal[0]["rank"] if proposal and answer == "yes" else ""
    by_sjr = tier_of(quartile if source else "", tiers)
    by_icore = tier_of(rank, tiers)
    tier = min(by_sjr, by_icore)
    if rank and by_icore < by_sjr:
        basis = "ICORE %s" % rank
    elif source:
        basis = "SJR %s" % (quartile if quartile and quartile != "-" else "no quartile")
    else:
        basis = "no match"
    return ("1" if tier == 1 else "2"), str(tier), basis


def render(config, cfg, numbers, venues, unplaced, rows, looked_up, aside=()):
    lists, tiers = cfg["lists"], cfg["bands"]["tiers"]
    lines = [
        "# Venue bands: the order of the core's step 3", "",
        "Written by `runners/venue_bands.py` from `%s`; do not edit, rerun the runner."
        % rel(config), "",
        "%d records of the map: %d in %d venues, and %d without a venue. Lists: %s and %s, "
        "downloaded %s. Tiers, best first: %s; a venue takes the first tier that its SJR best "
        "quartile or its confirmed ICORE rank reaches. Band 1 is the first tier, band 2 every "
        "other venue, and a record without one (protocol, Two tiers). An ICORE match counts "
        "once a person has confirmed it." % (
            len(numbers), len(numbers) - len(unplaced), len(venues), len(unplaced),
            lists["sjr_edition"], lists["icore_edition"], lists["downloaded"],
            describe_tiers(tiers)),
        "", "| Band | Records | Venues |", "| --- | ---: | ---: |"]
    by_band = Counter(r["band"] for r in rows)
    venue_band = Counter(v["band"] for v in venues.values())
    for band, label in (("1", "1"), ("2", "2"), ("", "pending")):
        lines.append("| %s | %d | %d |" % (label, by_band[band], venue_band[band]))
    lines += ["", "| Tier | Records | Venues |", "| --- | ---: | ---: |"]
    by_tier = Counter(r["tier"] for r in rows)
    venue_tier = Counter(v["tier"] for v in venues.values())
    for i in range(1, len(tiers) + 2):
        label = "%d (%s)" % (i, " or ".join(tiers[i - 1]) if i <= len(tiers) else "the rest")
        lines.append("| %s | %d | %d |" % (label, by_tier[str(i)], venue_tier[str(i)]))
    lines.append("| pending | %d | %d |" % (by_tier[""], venue_tier[""]))
    lines += ["", "| Basis | Records | Venues |", "| --- | ---: | ---: |"]
    by_basis = Counter(r["basis"] for r in rows)
    venue_basis = Counter(v["basis"] for v in venues.values())
    for basis in sorted(by_basis, key=lambda b: (-by_basis[b], b)):
        lines.append("| %s | %d | %d |" % (basis, by_basis[basis], venue_basis[basis]))
    def country_of(r):
        return r["sjr_country"] or (NO_COUNTRY if r["sjr_sourceid"] else NOT_IN_SJR)
    countries = Counter(country_of(r) for r in rows)
    in_band1 = Counter(country_of(r) for r in rows if r["band"] == "1")
    lines += ["", "## Records by the venue's country", "",
              "The country SJR gives each source, as its `Country` column reads; a record whose "
              "venue SJR does not list, or that has no venue, is counted as %s. It describes "
              "the venues and decides nothing." % NOT_IN_SJR, "",
              "| Country | Records | In band 1 |", "| --- | ---: | ---: |"]
    last = (NO_COUNTRY, NOT_IN_SJR)
    for country in sorted(countries, key=lambda c: (c in last, -countries[c], c)):
        lines.append("| %s | %d | %d |" % (country, countries[country], in_band1[country]))
    proposed = sorted((v for v in venues.values() if v["proposal"]), key=lambda v: v["name"])
    lines += ["", "## ICORE matches proposed", "",
              "%d venues, each shown with the ICORE conference ranked %s proposed as its own; "
              "a person answers on the sheet whether the two are the same conference." % (
                  len(proposed), " or ".join(looked_up))]
    if proposed:
        lines += ["", "| Venue | Records | ICORE conference | Rank | Similarity | Answer |",
                  "| --- | ---: | --- | --- | ---: | --- |"]
        for v in proposed:
            c, s = v["proposal"]
            lines.append("| %s | %d | %s (%s) | %s | %.2f | %s |" % (
                v["name"], len(v["records"]), c["title"], c["acronym"], c["rank"], s,
                v["answer"]["confirmed"] or "not yet"))
    if aside:
        lines += ["", "Answers set aside, their venue no longer proposed or now proposed "
                  "another conference: %d." % len(aside)]
    missing = sorted((v for v in venues.values() if v["basis"] == "no match"),
                     key=lambda v: v["name"])
    lines += ["", "## Venues with no match", "",
              "%d venues, in band 2 and the last tier: no SJR source found by ISSN-L, and no "
              "confirmed ICORE match ranked %s. ICORE ranks below that are not looked up, so "
              "some of these are conferences ICORE lists at a lower rank." % (
                  len(missing), " or ".join(looked_up))]
    if missing:
        lines += ["", "| Venue | Type | ISSN-L | Records |", "| --- | --- | --- | ---: |"]
        for v in missing:
            lines.append("| %s | %s | %s | %d |" % (v["name"], v["type"] or "none",
                                                   v["issn"] or "none", len(v["records"])))
    lines += ["", "Records without a venue, in band 2: %s." % (
        ", ".join(map(str, unplaced)) or "none")]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.path.join(REPO, "configs", "venues.toml"))
    parser.add_argument("--override", default=None,
                        help="a TOML file whose tables are laid over the config's, key by key")
    args = parser.parse_args()
    cfg = load_config(args.config, args.override)
    inputs, outputs, bands = cfg["inputs"], cfg["outputs"], cfg["bands"]
    tiers = bands["tiers"]
    check_tiers(tiers)

    map_path = resolve(inputs["map"])
    if not os.path.isfile(map_path):
        raise SystemExit("%s not found: the map, written by runners/map_vote.py." % map_path)
    with open(map_path, encoding="utf-8-sig", newline="") as fh:
        numbers = [int(r["number"]) for r in csv.DictReader(fh) if (r.get("number") or "").strip()]
    records = {r.number: r for r in corpus.load_references(resolve(inputs["references"]))}
    absent = [n for n in numbers if n not in records]
    if absent:
        raise SystemExit("%s holds no record %s." % (inputs["references"],
                                                     ", ".join(map(str, absent))))
    sjr = read_sjr(resolve(inputs["sjr"]))
    every = read_icore(resolve(inputs["icore"]))
    ranks = {c["rank"] for c in every}
    quartiles = {s.get("SJR Best Quartile", "") for s in sjr.values()}
    unknown = [x for t in tiers for x in t if x not in ranks and x not in quartiles]
    if unknown:
        raise SystemExit("[bands] tiers names %s, which neither list holds." % ", ".join(unknown))
    # Only a conference of a rank the tiers name can lift a venue above the rest, so only
    # those are proposed.
    looked_up = [x for t in tiers for x in t if x in ranks]
    icore = [c for c in every if c["rank"] in looked_up]
    for c in icore:
        c["words"] = words(c["title"])

    groups, unplaced = defaultdict(list), []
    for n in numbers:
        key = venue_key(records[n])
        (groups[key] if key else unplaced).append(n)
    venues = {}
    for key, ns in groups.items():
        name = Counter(records[n].venue for n in ns).most_common(1)[0][0]
        source = sjr.get(key[5:]) if key.startswith("issn:") else None
        proposal = None
        if (source or {}).get("SJR Best Quartile", "") not in tiers[0] and \
                event_like(records[ns[0]], source, name):
            proposal = propose(name, icore, bands["similarity"])
        venues[key] = {"name": name, "records": ns, "source": source, "proposal": proposal,
                       "type": records[ns[0]].source_type,
                       "issn": records[ns[0]].raw.get("issn_l") or ""}

    proposals = {k: v["proposal"] for k, v in venues.items() if v["proposal"]}
    confirmations = inputs["confirmations"]
    answers, aside = read_confirmations(resolve(confirmations), proposals)
    sheet_path = resolve(outputs["sheet"])
    pending = unsaved(sheet_path, answers, aside)
    if pending:
        raise SystemExit("%s holds answers not saved in %s (%s): save the sheet under that "
                         "name, or move it aside, before it is written again."
                         % (sheet_path, confirmations, ", ".join(pending)))
    for key, v in venues.items():
        v["answer"] = answers.get(key, blank())
        v["band"], v["tier"], v["basis"] = decide(v["source"], v["proposal"],
                                                  v["answer"]["confirmed"], tiers)

    sheet = []
    for key, v in sorted(proposals.items(), key=lambda kv: venues[kv[0]]["name"]):
        c, s = v
        sheet.append({"key": key, "venue": venues[key]["name"],
                      "records": len(venues[key]["records"]), "icore_id": c["id"],
                      "icore_title": c["title"], "icore_acronym": c["acronym"],
                      "icore_rank": c["rank"], "similarity": "%.2f" % s,
                      **venues[key]["answer"]})
    write_csv(sheet_path, SHEET_FIELDS, sheet)
    record_written(sheet_path)

    rows, where = [], {n: key for key, ns in groups.items() for n in ns}
    for n in numbers:
        r = records[n]
        if n in where:
            v = venues[where[n]]
            source = v["source"] or {}
            c = v["proposal"][0] if v["proposal"] and v["answer"]["confirmed"] == "yes" else {}
            band, tier, basis = v["band"], v["tier"], v["basis"]
        else:
            source, c, band, tier, basis = {}, {}, "2", str(len(tiers) + 1), "no venue"
        rows.append({"number": n, "venue": r.venue, "source_type": r.source_type,
                     "issn_l": r.raw.get("issn_l") or "",
                     "sjr_sourceid": source.get("Sourceid", ""),
                     "sjr_title": source.get("Title", ""), "sjr_type": source.get("Type", ""),
                     "sjr_quartile": source.get("SJR Best Quartile", ""),
                     "sjr_country": source.get("Country", ""),
                     "icore_id": c.get("id", ""), "icore_title": c.get("title", ""),
                     "icore_acronym": c.get("acronym", ""), "icore_rank": c.get("rank", ""),
                     "band": band, "tier": tier, "basis": basis})
    write_csv(resolve(outputs["bands"]), BANDS_FIELDS, rows)
    report_path = resolve(outputs["report"])
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(args.config, cfg, numbers, venues, unplaced, rows, looked_up, aside))

    by_band = Counter(r["band"] for r in rows)
    by_tier = Counter(r["tier"] for r in rows)
    said = Counter(v["answer"]["confirmed"] for v in venues.values() if v["proposal"])
    print("records           : %d in %d venues, %d without a venue"
          % (len(numbers), len(venues), len(unplaced)))
    print("band 1            : %d records" % by_band["1"])
    print("band 2            : %d records" % by_band["2"])
    print("pending           : %d records" % by_band[""])
    print("tiers             : %s" % ", ".join(
        "%d: %d" % (i, by_tier[str(i)]) for i in range(1, len(tiers) + 2)))
    print("ICORE proposals   : %d (yes %d, no %d, open %d); answers set aside %d"
          % (len(proposals), said["yes"], said["no"], said[""], len(aside)))
    print("written           : %s, %s, %s" % (rel(resolve(outputs["bands"])), rel(sheet_path),
                                               rel(report_path)))


if __name__ == "__main__":
    main()
