# Datasets

This folder holds the data files the runners read and write. This file gives each file's
provenance and the checksums recorded for it. Paths are relative to this folder. Runners are
in `../runners/`, and the protocol is `../protocol.md`.

The search of OpenAlex, the resolution of reference lists and every call to a language model
are not done by code in this folder. Its outputs are the fixed inputs in this folder.
Nothing in this repository fetches anything.

## Files in this folder

### Search

| File | What it is | Made by |
|---|---|---|
| `references.json` | The searched corpus: the 664 records the query in `../configs/search-query.md` returned, each abstract replaced by its SHA-256 (Provenance notes, Abstracts). | From OpenAlex. `../results/search/search-record.md` records the run. |
| `duplicates.csv` | The 2 records removed as duplicates before screening, each with the record kept in its place. | `deduplicate.py`, by the rule in `../configs/deduplicate.toml`. |
| `dropped.csv` | The 3 records dropped before screening (118, 340 and 663), which have neither an abstract nor a DOI. | The authors, by hand (`../protocol.md`). |

### Screening

| File | What it is | Made by |
|---|---|---|
| `calibration/round-1/`: `osamah.csv`, `qwen38.csv`, `gemma26.csv`, `glimmer30.csv` | Decisions on calibration batch 01 (25 records): a person's, then each model's. | Osamah H. Hussein, on the calibration sheet. The models' rows were taken by `screening_calibration.py --take-round 1`. |
| `screening-qwen38.csv`, `screening-gemma26.csv`, `screening-glimmer30.csv` | One model's decision on each record to screen, against `../configs/screening-criteria.md`. The model saw the title, abstract, venue, year and type. Its reason and the sentence it quotes (`evidence`) may repeat the abstract's words, up to 40 in a row (Provenance notes, Abstracts). | The people who screened, and the run that wrote the files. |
| `screening-validation.csv` | A person's blind decisions on the validation sample: 100 records decided without a person. | Osamah H. Hussein, on the sample's page. |
| `screening-adjudication.csv` | A second person's blind decisions on the 18 sampled records where the first person's decision differs from the models'. Each decision settles its record. | Moayad Alnammi, on the adjudication sheet's page. |
| `screening.csv` | The consensus: one decision per screened record (533 include, 16 uncertain, 110 exclude), with the rule each exclusion counts under. | `screening_consensus.py`. |

### The map

| File | What it is | Made by |
|---|---|---|
| `map-qwen38.csv`, `map-gemma26.csv`, `map-glimmer30.csv` | One model's codes for 532 included records on the 15 axes of Part A, from title and abstract, with quotes from the abstract for three axes, up to 40 words in a row (Provenance notes, Abstracts). | Produced with `configs/map.toml` and Part A of `coding-scheme.md`, and not by code in this folder. |
| `map-person.csv` | The codes of record 74, the one included record the models did not code. | Moayad Alnammi, from its title and abstract. |
| `map-check.csv` | A person's blind codes of three axes on a random sample of 25 map records. | Moayad Alnammi, on the map check's page. |
| `map.csv` | The map: the 533 included records, each axis decided by majority vote after the scheme's rules. | `map_vote.py`. |
| `map-references.bib` | The BibTeX entries of the map's 533 studies, in record order, each after a `% Record N` line, in UTF-8. Records 287 and 654 have no DOI. Each core study has the key it has in `core-references.bib`, so that a key names one study in both files. | From the records' OpenAlex metadata, corrected by Crossref's record of each DOI where the two disagree, a venue OpenAlex lacks taken from Crossref's record. Where both sources are wrong or silent, a field is set from another source, and a `% Override:` line above the entry gives its old value, its new one and the evidence (six entries). |

### The core's selection

| File | What it is | Made by |
|---|---|---|
| `core-claims.csv` | A person's answer on each of the 41 claims of use beyond simulation (40 yes, 1 no), with the level confirmed. In this copy, the note of record 399, which quotes the paper's full text, is withheld, with its SHA-256; the authors keep the file as written. | Moayad Alnammi, on the claims' page. |
| `venue-matches.csv` | A person's yes or no on each of the 13 ICORE conferences proposed by name (4 yes, 9 no). | Moayad Alnammi, on `../results/core/venue-matches-sheet.csv`. |
| `venue-bands.csv` | Each map record's venue band and tier, from the SJR and ICORE lists. | `venue_bands.py`. |
| `core.csv` | The core: the 100 studies selected for reading in full, each with the step of the rule that took it. | `core_selection.py`. |
| `core-references.bib` | The BibTeX entries of the 100 core studies, in record order, each after a `% Record N` line. `core_synthesis.py` reads the core's BibTeX keys from it. | From the records' OpenAlex metadata corrected by Crossref's record of each DOI, then edited for the paper's bibliography (accented letters and dashes written in LaTeX, the one missing conference name filled in). |

### The full texts

| File | What it is | Made by |
|---|---|---|
| `core-texts.csv` | The core's full texts as gathered: 99 saved and 1 not retrieved (record 18), with each version and DOI check. In this copy, the notes that a returned sheet marked a supplement saved with no supplement file kept are left out (the supplements were not read for the review), and the other notes do not name whose sheet they concern; the authors keep the sheet as merged. | Osamah H. Hussein and Moayad Alnammi, on the page `core_texts.py` writes; their two sheets were merged into one. |
| `full-texts-sha256.csv` | The size and SHA-256 of each of the 99 full-text PDFs. | Computed when the PDFs were saved. |
| `full-texts-md-sha256.csv` | The size and SHA-256 of each converted full text and its metadata file (198 rows). | Written when the conversion was checked. |

### The coding of the core

| File | What it is | Made by |
|---|---|---|
| `coding-scheme.md` | The coding scheme: Part A, the map's 15 axes; Part B, the questions asked of each full text. | The authors, before coding. |
| `coded-studies.csv` | One row per core study (99), coded from its full text against Part B. | `core_gather.py`, from the coding agent's responses. |
| `core-answers.csv` | One row per answer: the agent's value, the judge's verdict and proposal, the authors' value where corrected, the pages cited and each quote's SHA-256. | `core_gather.py`. |
| `core-baselines.csv` | One row per baseline a study compares with (question D07), with the judge's verdict. | `core_gather.py`. |
| `core-study-claims.csv` | One row per claim a study makes (question D19), with the judge's verdict. | `core_gather.py`. |
| `core-transfer-tests.csv` | One row per transfer test (question E01), with the judge's verdict. | `core_gather.py`. |
| `core-coding-runs.csv` | The coding run of each paper: status, model and revision, seed, checker fingerprint, and the SHA-256 of the paper, response and transcript. | `core_gather.py`, from the run records, which this folder does not contain. |
| `core-corrections.csv` | The authors' corrections: 10 answers in studies 191 and 530, each with the pages read and the reason. | The authors, by hand. |
| `core-human-check.csv` | Osamah H. Hussein's blind answers to six questions on the 20 studies of the seeded fifth, returned through the answer page. This copy has no free-text note, because the repository publishes no quote text. | Osamah H. Hussein, on the page `core_human_check.py` writes. |

Multi-label cells in the coded files use `|` between codes.

## Provenance notes

**Abstracts.** OpenAlex does not serve every abstract, so missing abstracts were filled by DOI
before screening. The sources, in order, were Scopus exports, Crossref, Springer Nature,
Semantic Scholar and, by hand, the publisher's page. A Scopus or publisher abstract was taken
only when its title matched the record's. The fill added and removed no record. Each record's
`abstract_source` names where its abstract came from, and
`../results/corpus/corpus-profile.md` counts them. Not every abstract may be redistributed, so
the record file is released without them. Each
record gives its abstract's SHA-256 in `abstract_sha256`, computed over the abstract's UTF-8
text, and empty when the record has none. OpenAlex's other metadata, the titles included, is
CC0. The authors keep the file as written (Files the authors keep), and a step
that needs the abstracts takes them from there (`../src/withheld.py`). In the screeners' and
the people's reasons and quotes, and in the map's quotes, every stretch that repeats more than
40 consecutive words of the record's abstract is cut after its 40th word and marked ` [cut]`
(`../configs/withheld.toml`, [quotes]). Two records have an abstract of 40 words or fewer; 
a stretch that repeats the whole of one is cut after half its words. A stretch that runs on 
from one of a row's cells into the next is cut in the earlier cell, so that the quote beside 
it stays as it is in every file that copies it. A word is a run of letters or digits in any 
script, and each Chinese, Japanese or Korean character is a word. The writer's own words stay 
whole, and the authors keep the files as written. The cut bounds each cell, not each record: 
read together, the quotes and reasons of the several files repeat half or more of 45 abstracts, 
beyond their titles' words, three quarters or more of 6, and all of record 238's. The people's 
notes are their own words, with at most short quotes of an abstract.

**The full texts and the coding.** The coding agent read each full text as markdown converted
from its PDF, with page markers. Its responses and the judge's reasons quote the papers, so
they stay with the authors. `core_gather.py` publishes only codes, numbers, page numbers, the
judge's verdicts and proposals, and a SHA-256 of each quote.

**Licences.** The files the authors made are released under CC BY 4.0, and the code under the
MIT License (`../README.md`, License and citation). Third-party material in the files keeps its
own terms. That covers the bibliographic metadata from OpenAlex (CC0) and from Crossref, in
`references.json`, the two bibliographies and the titles other files repeat; the excerpts of
abstracts in the quotes and reasons; and the columns of `venue-bands.csv` and
`venue-matches.csv` taken from SJR 2025 (`sjr_`) and ICORE2026 (`icore_`), whose sources are
given under Files the authors keep. SCImago allows the use of the information on its website as
long as the website is cited (https://www.scimagolab.com/faqs-2/). The two lists are cited as
the paper cites them:

- SCImago (n.d.). SJR: SCImago Journal & Country Rank [Portal]. https://www.scimagojr.com,
  retrieved 18 October 2026.
- ICORE (2026). ICORE Conference Rankings: ICORE2026. https://portal.core.edu.au/conf-ranks/,
  accessed 18 October 2026.

## Files the authors keep

These files cannot be distributed. The configs name files the authors keep and do not release.

| Files | What they are | Provenance |
|---|---|---|
| Record file as written | `references.json` with its abstracts (`../configs/withheld.toml`). The file in this folder is it, each abstract replaced by its SHA-256; `../src/withheld.py` checks the copy against it, record by record, before it takes the abstracts. | Its checksum as written is recorded below. |
| Quotes as written | The 14 files of `../configs/withheld.toml` [quotes], with their quotes and reasons whole. | The people who screened, and the run that wrote the files. The checksums of the files as written are recorded below. |
| The full texts' sheet as merged | `core-texts.csv` with its notes as first written. `../results/core-coding/draws-lock.json` records its SHA-256. | As `core-texts.csv` above. |
| The claims' answers as written | `core-claims.csv` with every note. `../results/core/core-lock.json` records its SHA-256 (`confirmations`). | As `core-claims.csv` above. |
| Sheets | The pages on which people screened (the calibration sheet, the validation sample, the adjudication sheet), checked the map and confirmed the claims, with their tracking files. They show the abstracts. | Written by the steps that issued them. |
| Full texts | The 99 core papers as PDFs, the published versions, each named `<number>.pdf`. Record 54's file is a whole proceedings volume, with the study on pages 183 to 198. | Gathered by Osamah H. Hussein and Moayad Alnammi, each checked against its record. 492,734,263 bytes in all. Each file's size and SHA-256 are in `full-texts-sha256.csv`. |
| Converted full texts | The 99 full texts in markdown, one folder per study with the converter's metadata. Page markers count the PDF's pages from 0. For record 54, only the study's pages were converted. Records 131, 290, 504 and 575 were read from page images, since their text layer lacks some italic letters. | Converted with no language model. Every page count was checked against its PDF's. 15,179,272 bytes in 198 files. Each file's size and SHA-256 are in `full-texts-md-sha256.csv`. |
| Coding outputs | The coding agent's responses, its run records (`coding-runs.csv`), the judge's verdicts with their reasons (`verdicts.csv`) and every quote with its SHA-256 (`quotes.csv`). They quote the papers. | Each response's SHA-256 is in `core-coding-runs.csv`. `../results/core-coding/gather.md` gives the SHA-256 of the verdicts and the run records. |
| Pages not released with this repository | The page for gathering the full texts (from `core_texts.py`), and the person's check: its page, its README and copies of its 20 papers (from `core_human_check.py`). They show the records and the papers. | Written by those steps. |
| SJR 2025 (`scimagojr-2025.csv`) | The SCImago Journal Rank list: every source with its ISSNs, type and best quartile. | Downloaded from https://www.scimagojr.com/journalrank.php (all subject areas, all types) on 2026-10-18. SHA-256 `6f20399957173a13e3c1729a5fb3b5821844ba75e8d640c8b3040ab19a6f7180`. |
| ICORE2026 (`icore2026.csv`) | The ICORE conference ranking (formerly CORE): the id, title, acronym, edition and rank of each conference, with no header row. | Exported from https://portal.core.edu.au/conf-ranks/ on 2026-10-18. SHA-256 `607cb795bfadb47dbeab7db6ab91f96e5a5aef0c76fef1ec0d221926d7402242`. |

## Checksums

The SHA-256 recorded for each file. `references.json`, `duplicates.csv` and `dropped.csv` are
frozen. A file the release made from one the authors keep has two checksums: the file as
written, marked so, and the file as released, in the tables of the record file and of the files
of quotes below.

The corpus and the model outputs:

| File | SHA-256 |
|---|---|
| `references.json`, as written | `469aac2f3fcfc04de8d7e60b04d48b325f7a4981d19673841f9adc58acf737f8` |
| `duplicates.csv` | `3a74b2d2c4a308022336dc597a85b56010c5f07d6a5362aed9296db12ea1db9a` |
| `dropped.csv` | `d5f3e49c352f374bee21d9fdffbea17eed7b5467a265c06d74538ce04dc9ac1a` |
| `../results/search/search-record.md` | `740455818261a62eabe5981a52e7a295c678d76dae17a9b5a53991057380cf78` |
| `screening-qwen38.csv`, as written | `e9cb561d000967f1844d6a89a006879009b15560b2a9c0596eb6b8ba16e97932` |
| `screening-gemma26.csv`, as written | `d3ff9988094c5f51286d8cfe8eca5afa5b059e4e9768d801344091c8770185e1` |
| `screening-glimmer30.csv`, as written | `027958fda30df08e01875e91a64a56774f8e917e16ac23e158bfd0fdee159b96` |
| `map-qwen38.csv`, as written | `bd91261e473b31ae8fc13b0f47fc587c17a0b95f7a1d8a5189fb9922c942dab0` |
| `map-gemma26.csv`, as written | `23c2539b62d29c2c8e89032d73897161a5a2868a030021c6bfe7d3931e121e84` |
| `map-glimmer30.csv`, as written | `204d89d9f34ca26c1da42906baebb865a7af960dd30fdb3cf0ab6f2e49a34c0a` |
| `core-references.bib` | `3364642b127059c1b4f0ad851e1d3e19ed89689c9eb1c3b4304041149d043f8c` |
| `map-references.bib` | `7217f966c0ff07fdb5de154b62305b2b5b897e548b970d79b8d646285adb22a7` |

The record file as released, each abstract replaced by its SHA-256:

| File | SHA-256 |
|---|---|
| `references.json` | `e2385555e645e4b508402d81b62d50972b6471a5cdf2cd437bcff8d13ff4ca81` |

The files of quotes, the full texts' sheet and the claims' answers as released: the quotes cut,
the notes reworded and one withheld (Provenance notes, Abstracts; `core-texts.csv` and
`core-claims.csv` above). The cut left three files as they were written:
`calibration/round-1/glimmer30.csv`, `screening-adjudication.csv` and `map-person.csv`.

| File | SHA-256 |
|---|---|
| `calibration/round-1/osamah.csv` | `12ec2b422b471c740a82903562ad380179c3ff61861dca578306963e01473784` |
| `calibration/round-1/qwen38.csv` | `b6707d95e8a411196eb691df5fc166de0b430a603259600be549898432d87ad0` |
| `calibration/round-1/gemma26.csv` | `b4136bc5a0578143bf40006801d4dfbf239ab726acf2e59a3b27ccea09b8edc3` |
| `calibration/round-1/glimmer30.csv` | `199ac306d943044e8c5ff333f58be3bafe7a729f4c513ad2443116f40fda7ffe` |
| `screening-qwen38.csv` | `11d652cddebe36e33827cd58c93368676954bb3f82286ffe656dac92dd68ed72` |
| `screening-gemma26.csv` | `0e0f6585ef47ffa687088876d6e954bc7f3eb7fdcd8f463108dc9a37f0a0df83` |
| `screening-glimmer30.csv` | `1bf4a6c43d27612c85a218b6b23afff7c249d2004775a4627b5817406f28a871` |
| `screening-validation.csv` | `7eda8963730e73da4c57df049ac34a91545475632d9f6d58301056d46d6b3c37` |
| `screening-adjudication.csv` | `6575839d5ceb6f2cc2879b1d8e0b32a2ba13a73bc4b999b69c608b9a72787881` |
| `screening.csv` | `e41d976ef2e649e004568b8a487976f46b2862c3fbb8f3431118411f817cfadb` |
| `map-qwen38.csv` | `7be0adb8589b4d02bc7d5547728393f71b30df964f8c5b4772796325da91da6f` |
| `map-gemma26.csv` | `791b2e141f2c7af773afe6630f56d0cf7ab3c858f48af9767658f37b5e195945` |
| `map-glimmer30.csv` | `4e4287df62d51b3ad0aade9a3c303c227c79a46be8670de79ea2ee431fdc50d4` |
| `map-person.csv` | `2471e1748b5de5a08db66b97695303121385d2b2208233960a7bdf5495385c37` |
| `core-texts.csv` | `2061f2505f848351dce7ff631b88c8b3a8527db69ff054a5b74d612a663fd20f` |
| `core-claims.csv` | `6ed545ea02df8ecbe1adff79ee912882386c66d5a6ad8f3e14dbbe95350d930b` |

The files people filled, and the calibration round:

| File | SHA-256 |
|---|---|
| `calibration/round-1/osamah.csv`, as written | `2749138ee7f5239a39904f8fa46c52eae15ae450f03f7229fad3f364b75e777b` |
| `calibration/round-1/qwen38.csv`, as written | `52d6fba6a99c0c13afdde6d398792191c41c73f7ad44926e299108a8df7685aa` |
| `calibration/round-1/gemma26.csv`, as written | `9b9ae269772a4e886de5bdbdde642b76f218eb12f1f16f58c527b1d5dbf4e62a` |
| `calibration/round-1/glimmer30.csv`, as written | `199ac306d943044e8c5ff333f58be3bafe7a729f4c513ad2443116f40fda7ffe` |
| `screening-validation.csv`, as written | `60d4e81c34d92b9b62e7e011a76ff278a25101c760c12a0c117e2a9cb82727ee` |
| `screening-adjudication.csv`, as written | `6575839d5ceb6f2cc2879b1d8e0b32a2ba13a73bc4b999b69c608b9a72787881` |
| `map-person.csv`, as written | `2471e1748b5de5a08db66b97695303121385d2b2208233960a7bdf5495385c37` |
| `map-check.csv` | `3ea9a4eef40515c51da47497b61e0f100994e32b6d1d5336c96ea9fd8a8e7b02` |
| `core-claims.csv`, as written | `bd9e583e2db537a5fe1867e72e52423749156c2ab75f8f1c3ea5a689b63fefcb` |
| `venue-matches.csv` | `4b64a1f41e8d750e243351aa9db82abb20640dd97f5801737dc3fc2f289ac016` |
| `core-texts.csv`, as written | `3d8fdb4f498b503233ba4059eb69f83ad2b036b92fd552e3505ec3f3e7aafd91` |
| `core-corrections.csv` | `3af3c1442456900dd268b4749eda1d0b00583b55a5256e14fafe2b754f92cdd7` |
| `core-human-check.csv` | `0ef4ec1c4a2817d12f2190ebec2619e63bc39dd2f27a1d5c9afc6be7fab0d6ca` |

The files the runners wrote, and the checksum lists:

| File | SHA-256 |
|---|---|
| `screening.csv`, as written | `27bd53f77c1ef43f37c34aa3bec95cb3ad1b052dfc30b4b324d2865a06d91535` |
| `venue-bands.csv` | `5b8ab417cd38a5dd6670d64d353efd4035849174599cdc4845e2194c6d51e0e9` |
| `core.csv` | `dd459f48088e19409b192abb76400b493f647e0d203003c229d9d73ebcf05c56` |
| `full-texts-sha256.csv` | `5ac1a5e9e1a6261cefa2f4d7fe29737af8ef5c13ad6cf1d8651e40f27e30ecdb` |
| `full-texts-md-sha256.csv` | `54ba0adb0cc59d34a23a41759c750d29c9df4c7e085d0c1a47485240db7fd40c` |

The checksums of the venue lists are in the table of the files the authors keep, above.

`../results/core/core-lock.json` locks the core under the digest
`d8c5231aaaea3d7244736a31a88a6599afd3ae77ace7fdc6aabcf087336a2e17`. `core_selection.py`
refuses any other core. The lock also records the SHA-256 of its inputs when the core was
locked, `references.json` as written among them. `../configs/withheld.toml` pairs each record
file's SHA-256 as written with its released one, and `core_statistics.py` accepts the released
file in its place.

Every row of `core-coding-runs.csv` carries the checker fingerprint
`72c9123803e7525d86fa1a889f010aefb9182f6d4ff48ed599bd06bed8ef420d`. It is a SHA-256 over the
11 files that `FILES` lists in `../runners/core_check.py`. To print the current fingerprint, run
this from the repository root, in bash or PowerShell:

```
echo '{"op": "fingerprint"}' | python runners/core_check.py --tool
```

In cmd.exe, leave out the single quotes: `echo {"op": "fingerprint"} | python runners/core_check.py --tool`.

Verify a file's checksum with:

```
python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <file>
```
