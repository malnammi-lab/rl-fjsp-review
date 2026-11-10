"""The screening rules, and the sheets, locks and pages that carry them.

Three model screeners decide every record at title and abstract (protocol, Screening). The
vote combines their decisions by a fixed rule, and settle decides a disagreement by rule.
A person screens a blind random sample of the decisions (stratified_sample,
proportional_quotas, blind_order). weighted_kappa and upper_bound measure how far those
decisions can be trusted. write_page writes a sheet as one self-contained HTML page
(template src/screening_page.html). This module decides; the runners read and write.
"""

import csv
import hashlib
import json
import math
import os
import random
import re

from src import corpus
from src.duplicates import norm

# Ordered: a disagreement between exclude and include is further apart than either is from
# uncertain. The order is what the weighted kappa weighs.
DECISIONS = ("exclude", "uncertain", "include")
RANK = {d: i for i, d in enumerate(DECISIONS)}
CONFIDENCES = ("low", "medium", "high")


# ------------------------------------------------------------------------------ the vote

def vote(decisions):
    """The vote rule of the protocol: `exclude` only when every screener excludes;
    `include` when at least two include and none excludes; anything else is a
    `disagreement`, which `settle` or a person's resolution decides.

    The rule is asymmetric on purpose. A wrongly excluded record is never looked at again,
    a wrongly included one is caught at full text, so one objection keeps a record from
    exclusion. A missing vote is not a vote: the caller must not pass one.
    """
    decisions = list(decisions)
    for d in decisions:
        if d not in RANK:
            raise ValueError("not a screening decision: %r" % (d,))
    if decisions and all(d == "exclude" for d in decisions):
        return "exclude"
    if decisions.count("include") >= 2 and "exclude" not in decisions:
        return "include"
    return "disagreement"


def settle(decisions):
    """The rule for a disagreement of the vote, so that no person resolves one (protocol,
    Screening): `include` when at least two screeners include; otherwise the record is
    removed, as `exclude` when any screener excludes it and as `uncertain` when none does.

    On a ballot the vote decides, it gives the vote's own outcome, so together they read:
    a record is included when at least two screeners include it.
    """
    decisions = list(decisions)
    for d in decisions:
        if d not in RANK:
            raise ValueError("not a screening decision: %r" % (d,))
    if decisions.count("include") >= 2:
        return "include"
    return "exclude" if "exclude" in decisions else "uncertain"


# ------------------------------------------------------------------- the full-text gate

GATES = ("full text", "abstract only", "set aside")


def carries(text, terms=(), stems=()):
    """Whether `text` carries one of `terms` as whole words, or a word containing one of
    `stems`, both after normalization (lower case, punctuation to spaces), as the search
    matched: "flexible job-shop" reads as "flexible job shop", and "job shop" is not found
    in "job shops". A stem catches the abbreviations of a problem however they are prefixed
    or suffixed: "fjs" finds FJSP, DFJSP, FJSSP, MOFJSP and FJSPT."""
    words = norm(text)
    padded = " " + words + " "
    if any(" " + norm(t) + " " in padded for t in terms):
        return True
    stems = [norm(s) for s in stems if norm(s)]
    return any(s in w for w in words.split() for s in stems)


def gate(decision, named):
    """Where a record goes after title and abstract, when the config has a [gate].

    A record carried forward (include or uncertain) that names the flexible job shop is
    sought at full text; an inclusion that does not is coded from its title and abstract
    only, and an uncertain one that does not is set aside. An exclusion, or a record with no
    decision yet, passes no gate ("")."""
    if decision not in ("include", "uncertain"):
        return ""
    if named:
        return "full text"
    return "abstract only" if decision == "include" else "set aside"


# ------------------------------------------------------------- which rule a reason cites

# "Exclusion 6", "exclusion rule 6", "Exclusion criteria 1 and 6", "Inclusion 3",
# "Criterion 2", "rule 7". The number list after the keyword may be joined by commas,
# "and", "or", "/" or "&".
_CITE = re.compile(
    r"\b(exclusion|inclusion|criterion|criteria|rule)s?"
    r"(?:\s+(?:rule|criterion|criteria)s?)?"
    r"\s*(?:no\.?|number|#)?\s*"
    r"(\d+(?:\s*(?:,|and|or|/|&)\s*\d+)*)",
    re.IGNORECASE,
)


def cited_rules(reason, aliases=None):
    """[(list, number)] in the order the reason cites them. `list` is "exclusion",
    "inclusion", or None when the reason says only "criterion N" or "rule N". `aliases`
    maps a phrase the criteria tell the screener to record (such as "shop class outside
    scope") to the exclusion rule it stands for."""
    text = reason or ""
    found = []
    for match in _CITE.finditer(text):
        keyword = match.group(1).lower()
        kind = keyword if keyword in ("exclusion", "inclusion") else None
        for n in re.findall(r"\d+", match.group(2)):
            found.append((match.start(), kind, int(n)))
    lowered = text.lower()
    for phrase, n in (aliases or {}).items():
        at = lowered.find(phrase.lower())
        if at >= 0:
            found.append((at, "exclusion", int(n)))
    found.sort(key=lambda f: f[0])
    return [(kind, n) for _, kind, n in found]


def rule_label(reason, inclusion_rules, exclusion_rules, prefer=(), aliases=None):
    """The one criterion a reason is counted under, as a label for the report.

    An exclusion rule is named first. A bare "criterion N" is read as exclusion rule N only
    when N is above the inclusion rules, since the two lists share the numbers below it.
    When a reason cites several exclusion rules, `prefer` ([preferred, over] pairs) settles
    the pairs the criteria settle; otherwise the first cited counts. Then an inclusion rule
    ("inclusion 1": the record fails it). What remains is reported, never guessed.
    """
    cites = cited_rules(reason, aliases)
    excl = [n for kind, n in cites if kind == "exclusion" and 1 <= n <= exclusion_rules]
    bare = [n for kind, n in cites if kind is None and 1 <= n <= exclusion_rules]
    excl += [n for n in bare if inclusion_rules < n <= exclusion_rules]
    if excl:
        chosen = excl[0]
        for preferred, over in prefer:
            if preferred in excl and over in excl and chosen == over:
                chosen = preferred
        return "exclusion %d" % chosen
    incl = [n for kind, n in cites if kind == "inclusion" and 1 <= n <= inclusion_rules]
    if incl:
        return "inclusion %d" % incl[0]
    if bare:
        return "criterion %d, list not named" % bare[0]
    return "none named"


def majority_label(labels):
    """The label at least two of the reasons give, or "no majority"."""
    labels = list(labels)
    for label in labels:
        if labels.count(label) >= 2:
            return label
    return "no majority"


def label_order(label):
    """Sort key for rule labels: exclusion rules, inclusion rules, then the rest."""
    head, _, rest = label.partition(" ")
    number = int(rest.split(",")[0]) if rest[:1].isdigit() else 0
    group = {"exclusion": 0, "inclusion": 1, "criterion": 2}.get(head, 3)
    return (group, number, label)


# ------------------------------------------------------------------------- the statistics

def weighted_kappa(pairs, weights="linear"):
    """Cohen's weighted kappa for two raters over the ordered DECISIONS.

    `pairs` is [(rater_a, rater_b)]. Disagreement weights are |i - j| / (k - 1) (linear)
    or its square (quadratic). None when there is nothing to compare or chance
    disagreement is zero, which happens when both raters used a single category.
    """
    k = len(DECISIONS)
    pairs = list(pairs)
    n = len(pairs)
    if n == 0:
        return None
    if weights not in ("linear", "quadratic"):
        raise ValueError("weights must be linear or quadratic, not %r" % (weights,))
    observed = [[0] * k for _ in range(k)]
    for a, b in pairs:
        observed[RANK[a]][RANK[b]] += 1
    rows = [sum(observed[i]) for i in range(k)]
    cols = [sum(observed[i][j] for i in range(k)) for j in range(k)]

    def w(i, j):
        d = abs(i - j) / (k - 1)
        return d if weights == "linear" else d * d

    po = sum(w(i, j) * observed[i][j] for i in range(k) for j in range(k)) / n
    pe = sum(w(i, j) * rows[i] * cols[j] for i in range(k) for j in range(k)) / (n * n)
    if pe == 0:
        return None
    return 1 - po / pe


def _binom_cdf(k, n, p):
    """P(X <= k) for X ~ Binomial(n, p), in log space so that large n cannot overflow."""
    if p <= 0:
        return 1.0
    if p >= 1:
        return 1.0 if k >= n else 0.0
    lp, lq = math.log(p), math.log1p(-p)
    top = math.lgamma(n + 1)
    return sum(math.exp(top - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq)
               for i in range(k + 1))


def upper_bound(k, n, confidence=0.95):
    """One-sided Clopper-Pearson upper confidence bound on a rate observed as k of n.

    The p at which seeing k or fewer events has probability 1 - confidence. With k = 0 it
    is 1 - (1 - confidence) ** (1 / n), close to 3 / n at 95 percent (the rule of three).
    Found by bisection, because the environment has no statistics library.
    """
    if n <= 0:
        return None
    if k >= n:
        return 1.0
    alpha = 1 - confidence
    lo, hi = k / n, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if _binom_cdf(k, n, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return hi


# ----------------------------------------------------------------------------- the draw

def proportional_quotas(sizes, total):
    """{stratum: quota}: `total` records split across the strata in proportion to their
    sizes, each quota rounded down and the records left over given one each to the strata
    with the largest remainders (a tie to the stratum listed first). When the strata hold
    `total` records or fewer, each is taken whole.
    """
    whole = sum(sizes.values())
    if whole <= total:
        return dict(sizes)
    names = list(sizes)
    exact = {s: total * sizes[s] / whole for s in names}
    quotas = {s: int(math.floor(exact[s])) for s in names}
    left = total - sum(quotas.values())
    for s in sorted(names, key=lambda s: (-(exact[s] - quotas[s]), names.index(s)))[:left]:
        quotas[s] += 1
    return quotas


def stratified_sample(strata, quotas, seed):
    """{stratum: sorted record numbers drawn}.

    Each stratum is sorted before drawing and has its own generator, seeded from the
    recorded seed and the stratum's name, so a draw depends only on the seed and the set
    of numbers: not on file order, and not on the other stratum. A stratum smaller than
    its quota is taken whole.
    """
    drawn = {}
    for name, members in strata.items():
        pool = sorted(members)
        quota = quotas[name]
        if len(pool) <= quota:
            drawn[name] = pool
        else:
            drawn[name] = sorted(random.Random("%s:%s" % (seed, name)).sample(pool, quota))
    return drawn


def blind_order(numbers, seed):
    """The sample in a seeded shuffled order, so that its strata are mixed on the sheet."""
    order = sorted(numbers)
    random.Random("%s:order" % seed).shuffle(order)
    return order


# ------------------------------------------------------------- a person's decision sheets

SHEET_FIELDS = ["number", "title", "decision", "confidence", "reason", "evidence"]


def read_decisions(path):
    """A decision file (a screener's screening.csv or a person's filled sheet) as
    ({number: Decision}, [numbers left blank], {number: the row as read}). Column names are
    matched without regard to case or surrounding spaces. Refuses a file without `number`
    and `decision` columns (a header row deleted, or Excel's semicolon separator), a
    decision outside DECISIONS, a confidence outside CONFIDENCES, a number given twice, and
    a file Excel saved in its local code page."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = [{(k or "").strip().lower(): v for k, v in row.items()} for row in reader]
            fields = [(f or "").strip().lower() for f in (reader.fieldnames or [])]
    except UnicodeDecodeError:
        raise SystemExit("%s is not UTF-8. In Excel, save it as 'CSV UTF-8 (Comma "
                         "delimited)', not 'CSV (Comma delimited)'." % path)
    if not {"number", "decision"} <= set(fields):
        raise SystemExit("%s has no 'number' and 'decision' columns (header found: %s). Keep "
                         "the header row, and in Excel save it as 'CSV UTF-8 (Comma "
                         "delimited)' with a comma as the separator." % (path, ", ".join(fields) or "none"))
    decided, blank, bad, raw = {}, [], [], {}
    for row in rows:
        number = corpus._int((row.get("number") or "").strip())
        if number is None:
            continue
        if number in raw:
            bad.append("%d given twice" % number)
        raw[number] = row
        decision = (row.get("decision") or "").strip().lower()
        confidence = (row.get("confidence") or "").strip().lower()
        if not decision:
            blank.append(number)
            continue
        if decision not in RANK:
            bad.append("%d: decision %r" % (number, decision))
            continue
        if confidence and confidence not in CONFIDENCES:
            bad.append("%d: confidence %r" % (number, confidence))
            continue
        decided[number] = corpus.Decision(
            number=number, decision=decision, confidence=confidence,
            reason=(row.get("reason") or "").strip(),
            evidence=(row.get("evidence") or "").strip())
    if bad:
        raise SystemExit("%s: %s" % (path, "; ".join(bad)))
    return decided, blank, raw


def to_screen(records, removed):
    """The records screening covers: the corpus less `removed`, the duplicate rule's
    removals and any records dropped before screening (screening_consensus.load_corpus)."""
    return [r for r in records if r.number not in removed]


def batch(records, index, size):
    """Batch `index` (from 1) as the acquisition tool cuts it: records with a title or an
    abstract, in corpus order, `size` at a time."""
    usable = [r for r in records if r.title or r.abstract]
    return usable[(index - 1) * size: index * size]


def calibration_batch(records, cal):
    """Batch 01 as the calibration round uses it: the first batch, less the records the
    config's `[calibration] leave_out` takes off the person's sheet. The models still judge
    those records, and the vote decides them; they are not compared in the round."""
    left = set(cal.get("leave_out", []))
    return [r for r in batch(records, 1, cal["batch_size"]) if r.number not in left]


def rounds(base, screeners):
    """{round number: {screener: path}} for every folder round-<N> under `base` (the
    calibration folder, already resolved), in round order."""
    found = {}
    if os.path.isdir(base):
        for name in os.listdir(base):
            match = re.fullmatch(r"round-(\d+)", name)
            if match and os.path.isdir(os.path.join(base, name)):
                found[int(match.group(1))] = {s: os.path.join(base, name, "%s.csv" % s)
                                              for s in screeners}
    return dict(sorted(found.items()))


def latest_person_round(base, screeners, person):
    """(round, path) of the newest round holding the person's file, or (None, None)."""
    for rnd, paths in reversed(list(rounds(base, screeners).items())):
        if os.path.isfile(paths[person]):
            return rnd, paths[person]
    return None, None


def prefer_labels(labels, prefer):
    """Apply the criteria's precedence across the reasons for one record: when any reason
    counts it under the preferred rule, the reasons counting it under the rule it takes
    precedence over are read as the preferred rule, since a precedence holds of the record,
    not of one reason."""
    labels = list(labels)
    for preferred, over in prefer:
        if "exclusion %d" % preferred in labels:
            labels = ["exclusion %d" % preferred if lab == "exclusion %d" % over else lab
                      for lab in labels]
    return labels


def cell(text):
    """Text safe inside a markdown table cell."""
    return " ".join(str(text or "").replace("|", "/").split())


def record_block(record, abstract=True):
    """One record as a screener sees it: title, venue, year, type and abstract; no topic
    label, no votes, no source of the abstract. Without `abstract`, a report's heading for the
    record: the abstract left out, since the released record files withhold it."""
    lines = ["## [%d] %s" % (record.number, record.title or "(no title)"), ""]
    meta = []
    if record.venue:
        meta.append("Venue: %s" % record.venue)
    if record.year:
        meta.append("Year: %d" % record.year)
    if record.work_type:
        meta.append("Type: %s" % record.work_type)
    if meta:
        lines += ["; ".join(meta), ""]
    if abstract:
        lines += ["Abstract: %s" % (record.abstract or "(no abstract available)"), ""]
    return lines


def records_digest(decided):
    """SHA-256 of whole records (decision, confidence, reason, evidence), record by record."""
    text = "\n".join("%d|%s|%s|%s|%s" % (n, d.decision, d.confidence, d.reason, d.evidence)
                     for n, d in sorted(decided.items()))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _issued_path(csv_path):
    return os.path.join(os.path.dirname(csv_path), "sheets-issued.json")


def issued(csv_path):
    """The digest of what the runner last wrote to this sheet, or None."""
    return read_lock(_issued_path(csv_path)).get(os.path.basename(csv_path))


def record_issued(csv_path):
    """Remember what the runner has just written to this sheet, so that a sheet nobody has
    touched since can always be re-issued."""
    path = _issued_path(csv_path)
    record = read_lock(path)
    record[os.path.basename(csv_path)] = records_digest(read_decisions(csv_path)[0])
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)


def unsaved(csv_path, saved, last_issued=None):
    """Numbers whose row on an existing sheet (decision, confidence, reason or evidence) is
    missing from, or differs from, `saved`: work typed on the sheet and not yet saved under
    datasets/. A sheet still as the runner last issued it (`last_issued`, its digest) holds
    no such work, whatever the saved file now says: the saved file was corrected directly."""
    if not os.path.isfile(csv_path):
        return []
    on_sheet, _, _ = read_decisions(csv_path)
    if last_issued is not None and records_digest(on_sheet) == last_issued:
        return []
    return sorted(n for n, d in on_sheet.items() if saved.get(n) != d)


def differ_message(csv_path, saved_path, numbers):
    """The refusal when a sheet was edited and differs from its saved file."""
    return ("%s was edited and differs from %s on records %s. If the sheet holds the newer "
            "work, save it as %s; if the saved file does, delete the sheet. Then run again."
            % (csv_path, saved_path, ", ".join(map(str, numbers[:10]))
               + (" ..." if len(numbers) > 10 else ""), saved_path))


# ------------------------------------------------------------------------------ the locks

def decisions_digest(decided):
    """SHA-256 of the decisions alone, record by record. A lock on this, not on the file's
    bytes, survives a re-save in Excel or a change of line endings in git, and still catches
    any changed decision."""
    text = "\n".join("%d,%s" % (n, decided[n].decision) for n in sorted(decided))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_lock(path):
    if not path or not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def verify_lock(path, key, decided, what):
    """Refuse `decided` when the lock at `path` holds `key` with other decisions. Returns
    True when the lock holds the key and it matches, False when the key is not locked."""
    entry = read_lock(path).get(key)
    if entry is None:
        return False
    if entry.get("decisions_sha256") != decisions_digest(decided):
        raise SystemExit(
            "%s has changed since it was locked (%s, %s). A change after that point needs a "
            "dated amendment to the protocol; restore the file, or record the amendment and "
            "then remove the entry from the lock." % (what, path, key))
    return True


def write_lock(path, key, decided, **extra):
    """Record `decided` under `key` in the lock at `path`, keeping the other keys."""
    lock = read_lock(path)
    lock[key] = dict({"decisions_sha256": decisions_digest(decided), "records": len(decided)},
                     **extra)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(lock, fh, indent=2, sort_keys=True)


# ---------------------------------------------------------------------- the screening page

PAGE_PLACEHOLDER = "__SHEET_DATA__"


def page_record(record, answer=None, models=None, cells=None, link=False):
    """One record as the screening page holds it: what a screener sees (title, venue, year,
    type, abstract) and the answer already saved; for a disagreement, also the models'
    answers (`models`, [(name, Decision)]), their decisions as sheet columns (`cells`), and,
    with `link`, the paper's DOI (else its OpenAlex address)."""
    out = {"number": record.number, "title": record.title or "", "venue": record.venue or "",
           "year": record.year, "type": record.work_type or "", "abstract": record.abstract or ""}
    if answer:
        out["answer"] = answer
    if models:
        out["models"] = [{"name": name, "decision": d.decision, "confidence": d.confidence,
                          "reason": d.reason, "evidence": d.evidence} for name, d in models]
    if cells:
        out["cells"] = cells
    if link:
        url = "https://doi.org/" + record.doi if record.doi else (record.openalex_id or "")
        if url.startswith("https://"):
            out["link"] = url
    return out


def answer_of(decision, decided_by=""):
    """A saved Decision as the page's answer ({} for none)."""
    if decision is None:
        return {}
    return {"decision": decision.decision, "confidence": decision.confidence,
            "reason": decision.reason, "evidence": decision.evidence, "decided_by": decided_by}


def write_page(path, settings, sheet, kind, save_as, columns, intro, records, extra=None):
    """The screening page: one self-contained HTML file, the template
    `settings["template"]` with the sheet's data in its data block. `kind` is
    "screening" or "disagreements"; `columns` are those of the file the page exports, named
    as `save_as`. The data is JSON with every "<" written as an escape, so that no text in a
    record can close the block. Nothing in it depends on the time of the run. `extra` adds
    keys a page of another kind reads, such as the questions of the coding page."""
    template = settings["template"]
    if template.count(PAGE_PLACEHOLDER) != 1:
        raise SystemExit("The screening page template must hold %s exactly once."
                         % PAGE_PLACEHOLDER)
    data = {"sheet": sheet, "sheet_id": os.path.splitext(os.path.basename(path))[0],
            "kind": kind, "save_as": save_as, "columns": list(columns), "intro": list(intro),
            "rules": [{"label": label, "hint": hint} for label, hint in settings.get("rules", [])],
            "criteria_brief": settings.get("criteria_brief", ""),
            "criteria_full": settings.get("criteria_full", ""),
            "records": records}
    data.update(extra or {})
    text = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(template.replace(PAGE_PLACEHOLDER, text))


def page_path(csv_path):
    """The page written beside a sheet: the sheet's name with .html."""
    return os.path.splitext(csv_path)[0] + ".html"


def write_sheet(records, md_path, csv_path, heading, intro, filled=None, saved=None, save_as="",
                page=None):
    """A blind screening sheet: the records to read (markdown) and a table to fill (CSV,
    UTF-8 with a byte-order mark so that Excel opens it correctly). `filled` pre-fills
    decisions already made, so a sheet can be re-issued without losing work. With `page`
    (the settings of [page], from screening_consensus.page_settings), the screening page is
    written beside the CSV too, showing what the screeners saw and nothing else.

    The sheet is regenerated on every run, so a person who filled it in place and has not
    yet saved it as `save_as` would lose that work: when the sheet was edited since the
    runner last wrote it (`sheets-issued.json`, beside the sheet) and differs from `saved` (by default
    `filled`) in any field of any row, the run stops instead, naming both files. A sheet
    open in Excel is locked on Windows; the run stops with a message rather than a
    traceback."""
    filled = filled or {}
    pending = unsaved(csv_path, filled if saved is None else saved, issued(csv_path))
    if pending:
        raise SystemExit(differ_message(csv_path, save_as or "the datasets/ file", pending))
    lines = ["# " + heading, ""] + intro + [""]
    for r in records:
        lines += record_block(r)
    for path in (csv_path, md_path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    try:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=SHEET_FIELDS)
            w.writeheader()
            for r in records:
                d = filled.get(r.number)
                w.writerow({"number": r.number, "title": r.title,
                            "decision": d.decision if d else "",
                            "confidence": d.confidence if d else "",
                            "reason": d.reason if d else "",
                            "evidence": d.evidence if d else ""})
        record_issued(csv_path)
        with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines))
        if page is not None:
            write_page(page_path(csv_path), page, heading, "screening", save_as, SHEET_FIELDS,
                       intro, [page_record(r, answer_of(filled.get(r.number))) for r in records])
    except PermissionError as exc:
        raise SystemExit("Cannot write %s: close it in Excel and run again." % exc.filename)
