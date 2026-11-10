"""Draw the validation sample of the decisions made without a person, and measure how far
they can be trusted once a person has screened it.

Once calibration and the vote are complete, the sample is drawn by stratum under the seed,
batch 01 left out, and written as a blind sheet. The report gives agreement, weighted
kappa, and one-sided upper bounds on the rates of wrong removal and wrong inclusion. With
[validation] adjudicate, a second person screens the records on which the first person's
decision differs. Optional [escape] and [spot_check] tables add an escape clause and a spot
check. Reads the corpus and the decision files. Writes the lock and screening-validation.md to
results/screening/validation/. The sheets show the abstracts, so they are written beside the
authors' copy of the records, and only where that copy is in place (src/withheld.py).

Run: python runners/run_all.py --only screening-validation
"""

import argparse
import os
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src import screening as sc  # noqa: E402
from src import withheld  # noqa: E402
from src.terms import has_any, norm  # noqa: E402
from runners.screening_consensus import (  # noqa: E402
    add_config_arguments, fmt_kappa, load_config, load_corpus, load_models, load_person,
    named_records, page_settings, pct, rel, require_calibration, resolve, spot_check_on,
    unvoted)

STRATA = ("exclude", "include")


def text_of(record):
    """A record's title and abstract, normalized as the search matched them."""
    return norm(record.title) + " " + norm(record.abstract)


def escape_groups(cfg):
    """[(term, [term])]: the escape clause's terms, one group each; [] when the config has no
    escape clause."""
    return [(t, [t]) for t in cfg.get("escape", {}).get("terms", [])]


def escape_hits(records, groups):
    """({group: set of numbers carrying one of its terms}, set carrying any), whole words in
    title and abstract after norm, as the search matched."""
    texts = {r.number: text_of(r) for r in records}
    hits = {g: {n for n, t in texts.items() if has_any(terms, t)} for g, terms in groups}
    return hits, set().union(*hits.values()) if hits else set()


SPOT_REASONS = ("flexible job shop, in title or abstract",
                "flexible job shop, in a screener's reason only",
                "guided vehicles or material handling in a job shop")


def spot_flags(cfg, records, named):
    """{number: [why]} for the records the spot check lists when they are unanimously
    excluded: naming the flexible job shop by the rule of [gate] (`named`, from
    screening_consensus.named_records), or naming one of [spot_check]'s vehicle terms
    together with one of its job shop terms in title and abstract."""
    s = cfg.get("spot_check")
    if not spot_check_on(cfg):
        return {}
    out = {}
    for r in records:
        why = []
        if named and r.number in named:
            why.append(SPOT_REASONS[0] if named[r.number] == "text" else SPOT_REASONS[1])
        text = (r.title or "") + " " + (r.abstract or "")
        if sc.carries(text, s["vehicle_terms"]) and sc.carries(text, s["with_terms"]):
            why.append(SPOT_REASONS[2])
        if why:
            out[r.number] = why
    return out


def spot_check_list(excluded, flags, sample, calibration):
    """The spot check: the unanimous exclusions flagged, less the records a person screens
    already (the validation sample, and batch 01 at calibration)."""
    return sorted((set(flags) & set(excluded)) - set(sample) - set(calibration))


def escape_candidates(any_hit, excluded, sample, calibration, spot=()):
    """The escape list: unanimous exclusions carrying an escape-clause term, less the records
    a person screens already (the sample, batch 01 at calibration, and the spot check)."""
    return sorted((set(any_hit) & set(excluded)) - set(sample) - set(calibration) - set(spot))


def unanimous(numbers, votes):
    """{"exclude": [...], "include": [...]}: records every screener decided the same way."""
    out = {s: [] for s in STRATA}
    for n in numbers:
        ballot = [v.get(n) for v in votes.values()]
        if all(d is not None for d in ballot):
            kinds = {d.decision for d in ballot}
            if len(kinds) == 1 and next(iter(kinds)) in out:
                out[next(iter(kinds))].append(n)
    return out


def by_vote(numbers, votes):
    """{"exclude": [...], "include": [...]}: the records the vote rule (sc.vote) excludes
    (all three exclude) and includes (at least two include, none excludes), over records
    every screener decided; a disagreement is in neither."""
    out = {s: [] for s in STRATA}
    for n in numbers:
        ballot = [v.get(n) for v in votes.values()]
        if all(d is not None for d in ballot):
            outcome = sc.vote(d.decision for d in ballot)
            if outcome in out:
                out[outcome].append(n)
    return out


def by_decision(numbers, votes):
    """{"exclude": [...], "include": [...]}: every record decided without a person, over
    records every screener decided: by the vote and, for a disagreement, by the rule of
    src/screening.settle, which gives the vote's own outcome on a ballot the vote decides.
    "include" holds the records included; "exclude" the records removed, whether excluded
    or left uncertain because no screener excluded them."""
    out = {s: [] for s in STRATA}
    for n in numbers:
        ballot = [v.get(n) for v in votes.values()]
        if all(d is not None for d in ballot):
            settled = sc.settle(d.decision for d in ballot)
            out["include" if settled == "include" else "exclude"].append(n)
    return out


STRATA_BY = {"vote": by_vote, "decision": by_decision}


def analyse(drawn, person, wrong, confidence, weights):
    """The statistics of the protocol, over a sample every record of which the person
    decided. `drawn` is {stratum: numbers}; `wrong` the person's decisions that make a
    unanimous exclusion wrong."""
    per = {}
    pairs = []
    for s in STRATA:
        got = Counter(person[n].decision for n in drawn[s])
        per[s] = {"n": len(drawn[s]), "counts": got, "agree": got[s]}
        pairs += [(s, person[n].decision) for n in drawn[s]]
    n_ex = per["exclude"]["n"]
    got_ex = per["exclude"]["counts"]
    strict = got_ex["include"]
    broad = got_ex["include"] + got_ex["uncertain"]
    configured = sum(got_ex[d] for d in wrong)
    n_in = per["include"]["n"]
    wrong_in = per["include"]["counts"]["exclude"]
    return {
        "per": per,
        "kappa": sc.weighted_kappa(pairs, weights),
        "strict": (strict, sc.upper_bound(strict, n_ex, confidence)),
        "broad": (broad, sc.upper_bound(broad, n_ex, confidence)),
        "wrong_inclusion": (wrong_in, sc.upper_bound(wrong_in, n_in, confidence)),
        "configured": configured,
        "triggered": configured > 0,
        "wrong_exclusions": sorted(n for n in drawn["exclude"] if person[n].decision in wrong),
    }


def disagreements(drawn, person):
    """The sampled records on which the person's decision differs from the decision made
    without a person, as the bounds count them: removed records the person did not exclude,
    and included records the person did not include."""
    return sorted([n for n in drawn["exclude"] if person[n].decision != "exclude"]
                  + [n for n in drawn["include"] if person[n].decision != "include"])


ADJUDICATION_INTRO = (
    "Each record below is one of the validation sample's records on which the person's "
    "decision and the decision made without a person differ. Screen each against "
    "`screening-criteria.md`, from its title and abstract alone, as the screeners did: "
    "decision (include, uncertain, exclude), confidence, a reason beginning with the rule "
    "(for example \"Exclusion 1:\"), and the sentence that decides it. Your decision settles "
    "the record (protocol amendment of 2026-10-15). Fill `%s` and save it as `%s`.")


def adjudicate(cfg, drawn, person, by_number, page, written):
    """The second person's screening of the sample's disagreements: the sheet, showing no
    earlier decision, in a seeded order; his decisions read back and locked once complete;
    and the statistics with his decision in place of the first person's on those records.
    Returns {"set", "decided", "blank", "by_stratum", "stats"}, the statistics None until
    every record on the sheet is decided."""
    v, outputs = cfg["validation"], cfg["outputs"]
    listed = disagreements(drawn, person)
    path = cfg["inputs"]["adjudication"]
    decided, _ = load_person(cfg, "adjudication")
    stray = sorted(set(decided) - set(listed))
    if stray:
        raise SystemExit("The adjudication file has decisions for records that are not "
                         "disagreements of the validation sample: %s"
                         % ", ".join(map(str, stray)))
    blank = sorted(set(listed) - set(decided))
    lock = resolve(outputs["validation_lock"])
    stats, locked = None, False
    if not blank:
        final = dict(person)
        final.update(decided)
        stats = analyse(drawn, final, v["wrong_exclusion"], v["confidence"],
                        cfg["agreement"]["kappa_weights"])
        locked = sc.verify_lock(lock, "adjudication", decided, path)
    if withheld.available(resolve(cfg["inputs"]["references"])):
        md, csv_ = resolve(outputs["adjudication_md"]), resolve(outputs["adjudication_csv"])
        os.makedirs(os.path.dirname(md), exist_ok=True)
        order = sc.blind_order(listed, "%s:adjudication" % v["seed"])
        sc.write_sheet([by_number[n] for n in order], md, csv_,
                       "Adjudication of the validation sample's disagreements",
                       [ADJUDICATION_INTRO % (outputs["adjudication_csv"], path)],
                       filled=decided, save_as=path, page=page)
        written += [md, csv_] + ([sc.page_path(csv_)] if page else [])
    if stats is not None and not locked:
        sc.write_lock(lock, "adjudication", decided)
        written.append(lock)
    by_stratum = {s: Counter(decided[n].decision for n in listed if n in drawn[s] and n in decided)
                  for s in STRATA}
    return {"set": listed, "decided": decided, "blank": blank, "by_stratum": by_stratum,
            "stats": stats}


def render_adjudication(cfg, adj, names):
    """The report's section on the second person's screening of the disagreements."""
    conf = int(round(100 * cfg["validation"]["confidence"]))
    listed, blank, stats = adj["set"], adj["blank"], adj["stats"]
    out = ["## Adjudication", "",
           "The sampled records on which the person's decision differs from the decision made "
           "without a person (removed records the person did not exclude, included records the "
           "person did not include) are screened again by a second person, from their titles "
           "and abstracts, without the votes or the first person's decisions, and his decision "
           "settles each (protocol, Screening). The sheet is withheld, since it shows the "
           "abstracts.", ""]
    if stats is None:
        out += ["%d of %d decided. The statistics after adjudication are computed once every "
                "record on the sheet has a decision." % (len(listed) - len(blank), len(listed)),
                ""]
        return out
    out += ["| Stratum | Disagreements | Second person include | Second person uncertain "
            "| Second person exclude |", "|---|---|---|---|---|"]
    for s in STRATA:
        c = adj["by_stratum"][s]
        out.append("| %s | %d | %d | %d | %d |" % (names[s], sum(c.values()), c["include"],
                                                   c["uncertain"], c["exclude"]))
    per = stats["per"]
    n_ex, n_in = per["exclude"]["n"], per["include"]["n"]
    out += ["", "The statistics again, with the second person's decision in place of the first "
            "person's on these records; one-sided %d%% Clopper-Pearson upper bounds as above."
            % conf, "", "| Reading | Wrong | Rate | Upper bound |", "|---|---|---|---|"]
    for label, key, n in (("removed; included after adjudication", "strict", n_ex),
                          ("removed; included or uncertain after adjudication", "broad", n_ex),
                          ("included; excluded after adjudication", "wrong_inclusion", n_in)):
        k, ub = stats[key]
        out.append("| %s | %d of %d | %s | %s |" % (label, k, n, pct(k, n),
                                                    "n/a" if ub is None else "%.1f%%" % (100 * ub)))
    out += ["", "Weighted kappa over the whole sample after adjudication: %s."
            % fmt_kappa(stats["kappa"]), ""]
    return out


def compare_sets(records, cfg):
    """[(name, numbers carrying any of its terms)] for the term sets in [escape.compare]."""
    sets = cfg.get("escape", {}).get("compare", {})
    return [(name, escape_hits(records, [(name, terms)])[1]) for name, terms in sets.items()]


def render_spot(cfg, spot_list, spot_blank, flags):
    """The spot check: why each record is listed, and how many are decided."""
    out = ["## Spot check", "",
           "Unanimous exclusions screened by a person whatever the validation sample shows: "
           "those that name the flexible job shop by the "
           "rule of the full-text gate, and those that name guided vehicles or material "
           "handling together with a job shop. Records a person screens already are left out: "
           "the validation sample, and batch 01 at calibration. A record the person does not "
           "exclude is carried forward on that decision.", "",
           "| Listed because | Records |", "|---|---|"]
    for why in SPOT_REASONS:
        out.append("| %s | %d |" % (why, sum(1 for n in spot_list if why in flags[n])))
    out += ["| listed, for any reason | %d |" % len(spot_list), "",
            "They are in `%s` and `%s`; %d of %d decided."
            % (cfg["outputs"]["spot_check_md"], cfg["outputs"]["spot_check_csv"],
               len(spot_list) - len(spot_blank), len(spot_list)), ""]
    if not spot_blank:
        out += ["The spot check is fully screened.", ""]
    return out


def render(cfg, n_screen, groups, hits, any_hit, excl_hits, strata, drawn, blank, stats,
           escape_list, escape_blank=(), n_unvoted=0, left_out=None, compared=(), spot=None,
           quotas=None, adjudication=None):
    v = cfg["validation"]
    left_out = left_out or {}
    mode = v.get("strata")
    names = {"vote": {"exclude": "the vote excludes", "include": "the vote includes"},
             "decision": {"exclude": "removed without a person",
                          "include": "included without a person"}}.get(
        mode, {"exclude": "all three exclude", "include": "all three include"})
    against = {"vote": "the vote's decision", "decision": "the decision made without a person"}.get(
        mode, "the unanimous decision")
    decided = {"vote": "records the vote decides",
               "decision": "records decided without a person"}.get(mode, "unanimous records")
    out = ["# Screening validation", "",
           "Generated by `runners/screening_validation.py` (`configs/screening.toml`). The "
           "draw, the weighted kappa and the bound are in `src/screening.py`.", ""]
    if groups:
        out += ["## Reach of the escape clause", "",
                "If any sampled unanimous exclusion is judged wrong, the person also screens "
                "every unanimous exclusion whose title or abstract carries one of the clause's "
                "terms. Records carrying each term, as whole words after normalisation:",
                "",
                "| Term | Records to screen | Unanimous exclusions |", "|---|---|---|"]
        for g, _ in groups:
            out.append("| %s | %d | %s |" % (g, len(hits[g]),
                                             "" if excl_hits is None else len(hits[g] & excl_hits)))
        out.append("| any of them | %d of %d (%s) | %s |" % (
            len(any_hit), n_screen, pct(len(any_hit), n_screen),
            "" if excl_hits is None else "%d of %d" % (len(any_hit & excl_hits), len(excl_hits))))
        out.append("")
    if compared:
        out += ["The term sets of `[escape.compare]` in the config, for comparison.", "",
                "| Term set | Terms | Records to screen | Unanimous exclusions |",
                "|---|---|---|---|"]
        for name, found in compared:
            terms = ", ".join(cfg["escape"]["compare"][name])
            out.append("| %s | %s | %d of %d (%s) | %s |" % (
                name, terms, len(found), n_screen, pct(len(found), n_screen),
                "" if excl_hits is None else "%d of %d" % (len(found & excl_hits), len(excl_hits))))
        out.append("")
    if n_unvoted:
        out += ["## The sample", "",
                "%d records to screen lack a vote from at least one screener, so no sample is "
                "drawn: the strata are defined over the complete vote." % n_unvoted, ""]
        return "\n".join(out)
    if strata is None:
        out += ["No vote yet: the model screeners' decision files are not in place, so no "
                "sample can be drawn.", ""]
        return "\n".join(out)

    out += ["## The sample", "",
            "Seed %s, drawn with Python %s. Each stratum is sorted and drawn with its own "
            "generator, so the draw depends only on the seed and the stratum's records."
            % (v["seed"], sys.version.split()[0]), ""]
    if left_out:
        out += ["Batch 01 (%d records) is left out of both strata: the person screened it at "
                "calibration and then saw the models' decisions on it, so it cannot be screened "
                "blind. Its %s (%d exclusions, %d inclusions) are compared with the person's "
                "own decisions in the calibration report."
                % (left_out["batch"], decided, left_out["exclude"], left_out["include"]), ""]
    quotas = quotas or {"exclude": v.get("quota_exclude"), "include": v.get("quota_include")}
    if "size" in v:
        out += ["%d records are split between the strata in proportion to their sizes: each "
                "quota is rounded down, and a record left over goes to the stratum with the "
                "larger remainder." % v["size"], ""]
    out += ["| Stratum | Records | Quota | Drawn |", "|---|---|---|---|"]
    out += ["| %s | %d | %d | %d |" % (names[s], len(strata[s]), quotas[s], len(drawn[s]))
            for s in STRATA]
    out += ["", "The sample, in a seeded order that mixes the strata and without the votes, is "
            "withheld, since it shows the abstracts.", ""]
    if spot is not None:
        out += render_spot(cfg, *spot)
    total = sum(len(x) for x in drawn.values())
    if stats is None:
        out += ["## The person's screening", "",
                "%d of %d sampled records decided. The statistics are computed once every "
                "sampled record has a decision." % (total - len(blank), total), ""]
        return "\n".join(out)

    per = stats["per"]
    out += ["## Agreement", "",
            "The person's decision on each sampled record, against %s." % against, "",
            "| Stratum | Records | Person include | Person uncertain | Person exclude | Agreeing |",
            "|---|---|---|---|---|---|"]
    for s in STRATA:
        c = per[s]["counts"]
        out.append("| %s | %d | %d | %d | %d | %d (%s) |" % (
            names[s], per[s]["n"], c["include"], c["uncertain"], c["exclude"], per[s]["agree"],
            pct(per[s]["agree"], per[s]["n"])))
    out += ["", "Cohen's kappa, weighted (%s) over exclude < uncertain < include, between the "
            "person and %s over the whole sample: %s. The sample is stratified, %d "
            "exclusions to %d inclusions, so this kappa describes the sample, not the corpus."
            % (cfg["agreement"]["kappa_weights"], against, fmt_kappa(stats["kappa"]),
               per["exclude"]["n"], per["include"]["n"]), ""]
    conf = int(round(100 * v["confidence"]))
    n_ex = per["exclude"]["n"]
    if mode == "decision":
        out += ["## Wrong removals", "",
                "A sampled removed record (excluded, or left uncertain) the person did not "
                "exclude. The bound is the one-sided %d%% Clopper-Pearson upper bound on the rate "
                "among the removed records the sample was drawn from." % conf, ""]
    else:
        out += ["## Wrong unanimous exclusions", "",
                "A sampled unanimous exclusion the person did not exclude. The bound is the "
                "one-sided %d%% Clopper-Pearson upper bound on the rate among the unanimous "
                "exclusions the sample was drawn from." % conf, ""]
    out += ["| Reading | Wrong | Rate | Upper bound |", "|---|---|---|---|"]
    for label, key in (("person includes", "strict"), ("person includes or is uncertain", "broad")):
        k, ub = stats[key]
        out.append("| %s | %d of %d | %s | %s |" % (label, k, n_ex, pct(k, n_ex),
                                                    "n/a" if ub is None else "%.1f%%" % (100 * ub)))
    if mode == "decision":
        n_in = per["include"]["n"]
        k, ub = stats["wrong_inclusion"]
        out += ["", "## Wrong inclusions", "",
                "A sampled included record the person excluded. The bound is the one-sided %d%% "
                "Clopper-Pearson upper bound on the rate among the included records the sample "
                "was drawn from." % conf, "",
                "| Reading | Wrong | Rate | Upper bound |", "|---|---|---|---|",
                "| person excludes | %d of %d | %s | %s |" % (
                    k, n_in, pct(k, n_in), "n/a" if ub is None else "%.1f%%" % (100 * ub))]
    if groups:
        out += ["", "The escape clause is triggered when the person's decision is one of: %s. "
                "Triggered: **%s** (%d records: %s)." % (
                    ", ".join(v["wrong_exclusion"]), "yes" if stats["triggered"] else "no",
                    stats["configured"], ", ".join(map(str, stats["wrong_exclusions"])) or "none"),
                ""]
    else:
        out += [""]
    if adjudication is not None:
        out += render_adjudication(cfg, adjudication, names)
    if escape_list is not None:
        decided = len(escape_list) - len(escape_blank)
        out += ["## Escape list", "",
                "%d unanimous exclusions carry an escape-clause term and were screened by a "
                "person neither in the sample, nor at calibration, nor on the spot check; they "
                "are in `%s` and `%s` for the person to screen. %d of them decided."
                % (len(escape_list), cfg["outputs"]["escape_md"], cfg["outputs"]["escape_csv"],
                   decided), ""]
        if not escape_blank:
            out += ["The escape list is fully screened.", ""]
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_config_arguments(parser)
    args = parser.parse_args()
    cfg = load_config(args.config, args.override)
    v, outputs = cfg["validation"], cfg["outputs"]

    # The escape clause and the spot check read the abstracts; the sheets show them where
    # they are in place.
    refs = resolve(cfg["inputs"]["references"])
    if escape_groups(cfg) or spot_check_on(cfg):
        withheld.require(refs, "screening-validation's [escape] and [spot_check]")
    sheets = withheld.available(refs)
    records, screen_records = load_corpus(cfg, abstracts=True)
    by_number = {r.number: r for r in records}
    numbers = [r.number for r in screen_records]
    groups = escape_groups(cfg)
    hits, any_hit = escape_hits(screen_records, groups)
    calibration = set()
    if v.get("leave_out_calibration_batch"):
        calibration = {r.number for r in sc.batch(screen_records, 1, cfg["calibration"]["batch_size"])}

    page = page_settings(cfg)    # a screening page beside each sheet
    have_votes = all(os.path.isfile(resolve(p)) for p in cfg["screeners"].values())
    strata = drawn = stats = escape_list = excl_hits = votes = spot = quotas = None
    adjudication = None
    blank, escape_blank, left_out, n_unvoted = [], [], {}, 0
    written = []
    escape_path = cfg["inputs"].get("escape")
    escape_exists = bool(escape_path) and os.path.isfile(resolve(escape_path))
    if have_votes:
        votes = load_models(cfg)
        require_calibration(cfg, screen_records, votes)
        n_unvoted = len(unvoted(numbers, votes))
    if votes is not None and not n_unvoted:
        every = STRATA_BY.get(v.get("strata"), unanimous)(numbers, votes)
        excl_hits = set(every["exclude"])
        strata = {s: [n for n in every[s] if n not in calibration] for s in STRATA}
        if calibration:
            left_out = {"batch": len(calibration),
                        "exclude": len(every["exclude"]) - len(strata["exclude"]),
                        "include": len(every["include"]) - len(strata["include"])}
        quotas = (sc.proportional_quotas({s: len(strata[s]) for s in STRATA}, v["size"])
                  if "size" in v else {"exclude": v["quota_exclude"], "include": v["quota_include"]})
        drawn = sc.stratified_sample(strata, quotas, v["seed"])
        sample = set(drawn["exclude"]) | set(drawn["include"])
        person, _ = load_person(cfg, "validation")
        extra = sorted(set(person) - sample)
        if extra:
            raise SystemExit("The validation file has decisions for records not in the sample "
                             "(was the sample drawn from other votes?): %s"
                             % ", ".join(map(str, extra)))
        blank = sorted(sample - set(person))
        lock = resolve(outputs["validation_lock"])
        locked = False
        if not blank:
            stats = analyse(drawn, person, v["wrong_exclusion"], v["confidence"],
                            cfg["agreement"]["kappa_weights"])
            # An existing lock is checked before the sheet is re-issued, so that a changed
            # file is named as such; a new lock is written only once the sheet is consistent.
            locked = sc.verify_lock(lock, "validation", person, cfg["inputs"]["validation"])
        if sheets:
            order = sc.blind_order(sample, v["seed"])
            md, csv_ = resolve(outputs["sample_md"]), resolve(outputs["sample_csv"])
            os.makedirs(os.path.dirname(md), exist_ok=True)
            sc.write_sheet([by_number[n] for n in order], md, csv_, "Validation sample",
                           ["Screen each record against `screening-criteria.md`, as in the "
                            "calibration round: decision (include, uncertain, exclude), "
                            "confidence, a reason beginning with the rule (for example "
                            "\"Exclusion 1:\"), and the sentence that decides it. Fill `%s` and "
                            "save it as `%s`." % (outputs["sample_csv"], cfg["inputs"]["validation"])],
                           filled=person, save_as=cfg["inputs"]["validation"], page=page)
            written += [md, csv_] + ([sc.page_path(csv_)] if page else [])
        if spot_check_on(cfg):
            # Issued as soon as the vote is complete, whatever the sample shows.
            flags = spot_flags(cfg, screen_records, named_records(cfg, screen_records, votes))
            spot_list = spot_check_list(excl_hits, flags, sample, calibration)
            spot_path = cfg["inputs"]["spot_check"]
            done, _ = load_person(cfg, "spot_check")
            stray = sorted(set(done) - set(spot_list))
            if stray:
                raise SystemExit("The spot-check file has decisions for records not on the spot "
                                 "check: %s" % ", ".join(map(str, stray)))
            spot = (spot_list, sorted(set(spot_list) - set(done)), flags)
            smd, scsv = resolve(outputs["spot_check_md"]), resolve(outputs["spot_check_csv"])
            sc.write_sheet([by_number[n] for n in spot_list], smd, scsv, "Spot check",
                           ["Every record below was excluded by all three model screeners. Each "
                            "names the flexible job shop, or guided vehicles or material "
                            "handling together with a job shop, so a wrong exclusion here would "
                            "lose a study the review needs. "
                            "Screen each against `screening-criteria.md`: decision (include, "
                            "uncertain, exclude), confidence, a reason beginning with the rule, "
                            "and the sentence that decides it. Fill `%s` and save it as `%s`."
                            % (outputs["spot_check_csv"], spot_path)],
                           filled=done, save_as=spot_path, page=page)
            written += [smd, scsv] + ([sc.page_path(scsv)] if page else [])
        if stats is not None:
            if not locked:
                # Once the escape list is issued the person knows the clause was triggered,
                # and an answer edited after that could undo it: the decisions are frozen.
                sc.write_lock(lock, "validation", person, triggered=stats["triggered"],
                              wrong_exclusions=stats["wrong_exclusions"])
                written.append(lock)
            if v.get("adjudicate"):
                adjudication = adjudicate(cfg, drawn, person, by_number, page, written)
            if stats["triggered"] and groups:
                # Records a person has already screened (the sample, batch 01 at
                # calibration, and the spot check) are not listed again.
                escape_list = escape_candidates(any_hit, excl_hits, sample, calibration,
                                                spot[0] if spot else ())
                done, _ = load_person(cfg, "escape")
                stray = sorted(set(done) - set(escape_list))
                if stray:
                    raise SystemExit("The escape file has decisions for records not on the escape "
                                     "list: %s" % ", ".join(map(str, stray)))
                escape_blank = sorted(set(escape_list) - set(done))
                emd, ecsv = resolve(outputs["escape_md"]), resolve(outputs["escape_csv"])
                sc.write_sheet([by_number[n] for n in escape_list], emd, ecsv, "Escape list",
                               ["The validation sample found a unanimous exclusion that should "
                                "not have been excluded, so every unanimous exclusion carrying "
                                "an escape-clause term is screened by a person. Fill `%s` and "
                                "save it as `%s`." % (outputs["escape_csv"], escape_path)],
                               filled=done, save_as=escape_path, page=page)
                written += [emd, ecsv] + ([sc.page_path(ecsv)] if page else [])
    # Only a run that has the complete vote can tell whether the clause was triggered.
    if groups and escape_exists and strata is not None and not (stats and stats["triggered"]):
        raise SystemExit("%s exists, but no complete validation sample has triggered the escape "
                         "clause; the escape list is screened only when it has." % escape_path)

    compared = compare_sets(screen_records, cfg)
    report = render(cfg, len(numbers), groups, hits, any_hit, excl_hits, strata, drawn,
                    blank, stats, escape_list, escape_blank, n_unvoted, left_out,
                    compared, spot, quotas, adjudication)
    report_path = resolve(outputs["validation_report"])
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(report)
    written.append(report_path)

    print("records to screen        : %d" % len(numbers))
    if groups:
        print("carrying an escape term  : %d (%s)" % (len(any_hit), pct(len(any_hit), len(numbers))))
    for name, found in compared:
        print("  term set %s: %d (%s)" % (name, len(found), pct(len(found), len(numbers))))
    if n_unvoted:
        print("incomplete vote          : %d records lack a vote; no sample drawn" % n_unvoted)
    elif strata is None:
        print("no vote yet: no sample drawn")
    else:
        print("%s exclude/include: %d / %d in the frame; drawn %d / %d" % (
            {"vote": "vote's    ", "decision": "decision's"}.get(v.get("strata"), "unanimous"),
            len(strata["exclude"]), len(strata["include"]),
            len(drawn["exclude"]), len(drawn["include"])))
        if spot is not None:
            print("spot check               : %d listed, %d decided" % (
                len(spot[0]), len(spot[0]) - len(spot[1])))
        if stats is None:
            print("person's screening       : %d of %d sampled records decided" % (
                len(drawn["exclude"]) + len(drawn["include"]) - len(blank),
                len(drawn["exclude"]) + len(drawn["include"])))
        else:
            print("weighted kappa           : %s" % fmt_kappa(stats["kappa"]))
            if groups:
                print("wrong exclusions         : %d strict, %d broad; escape clause %s" % (
                    stats["strict"][0], stats["broad"][0],
                    "TRIGGERED, %d records to screen" % len(escape_list) if stats["triggered"]
                    else "not triggered"))
            else:
                print("wrong exclusions         : %d strict, %d broad" % (
                    stats["strict"][0], stats["broad"][0]))
            if v.get("strata") == "decision":
                print("wrong inclusions         : %d of %d" % (
                    stats["wrong_inclusion"][0], len(drawn["include"])))
            if adjudication is not None:
                a = adjudication["stats"]
                if a is None:
                    print("adjudication             : %d of %d disagreements decided" % (
                        len(adjudication["set"]) - len(adjudication["blank"]),
                        len(adjudication["set"])))
                else:
                    print("after adjudication       : wrong removals %d strict, %d broad; "
                          "wrong inclusions %d of %d" % (a["strict"][0], a["broad"][0],
                                                         a["wrong_inclusion"][0],
                                                         len(drawn["include"])))
    print("wrote %s" % ", ".join(rel(p) for p in written))


if __name__ == "__main__":
    main()
