# The gather of the core's answers

Written by `runners/core_gather.py` from `configs\core-gather.toml`; do not edit, rerun the runner.

99 studies gathered, each response checked again against its paper with no problem left: 7524 answers to the questions, 839 item blocks. Published: codes, numbers, page numbers and a SHA-256 of each quote; no quote text and no note.

## Items

| Group | Studies with items | Items |
| --- | ---: | ---: |
| baseline | 99 | 368 |
| claim | 98 | 315 |
| transfer_test | 66 | 156 |

## Answers that report no content

Special answers and counts of none, over all the studies' answers to the questions (the authors' value where they corrected one).

| Answer | Answers |
| --- | ---: |
| not-stated | 69 |
| not-applicable | 764 |
| not-reported | 514 |
| none | 299 |

## The judge's verdicts

Every block's verdict, by section (`none`: the judge gave no valid reply for the unit that held it).

| Section | supported | partly | not-supported | cannot-judge | none |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 1273 | 162 | 48 | 0 | 2 |
| B | 924 | 66 | 94 | 2 | 3 |
| C | 1112 | 144 | 117 | 12 | 1 |
| D | 2115 | 313 | 220 | 13 | 2 |
| E | 321 | 88 | 44 | 0 | 0 |
| F | 473 | 71 | 49 | 0 | 1 |
| Q | 532 | 124 | 33 | 4 | 0 |

## Answers corrected by the authors

Answers the authors read against the paper and corrected, with the answers that follow from them by Part B's rules (protocol, Amendments: answers corrected by the authors; `datasets/core-corrections.csv`, with the pages read and the reasons). The published rows and the tables take the authors' value; the answers' file keeps the coder's value and the judge's verdict beside it, and the agreement of coder and judge is computed on the coder's.

| Study | Question | Coder | Judge | Judge's proposal | Authors |
| ---: | --- | --- | --- | --- | --- |
| 191 | A01 policy_role | steering-heuristic | not-supported | end-to-end | end-to-end |
| 191 | A03 scheduling_action | not-applicable | supported |  | machine |
| 191 | B03 sub_decision | not-applicable | not-supported | assignment | assignment |
| 191 | B04 steering_action | operator | not-supported | not-applicable | not-applicable |
| 191 | B05 steered_method | genetic-algorithm | not-supported | not-applicable | not-applicable |
| 530 | A01 policy_role | steering-heuristic | not-supported | end-to-end | end-to-end |
| 530 | A03 scheduling_action | not-applicable | supported |  | schedule-change |
| 530 | B03 sub_decision | not-applicable | not-supported | sequencing | both |
| 530 | B04 steering_action | operator | not-supported | other | not-applicable |
| 530 | B05 steered_method | local-search | not-supported | not-applicable | not-applicable |

## Inputs

| Input | SHA-256 |
| --- | --- |
| spec (configs/core-coding.toml) | 86d16a47e4c93201f36b713a8ba9620141a1507889724bddd4103c14c8e40509 |
| map (configs/map.toml) | ddd37840a2e6b452d33d0d7bff27e9ada953d056fbf2b6f7accbb3a66721bc7a |
| core (datasets/core.csv) | dd459f48088e19409b192abb76400b493f647e0d203003c229d9d73ebcf05c56 |
| responses, over their files' SHA-256 (99 files) | a408f4ffb18b5f52d8960f3cfe9d4a9910ae153312538a5c5f9b5b84f7463b67 |
| verdicts (verdicts.csv) | d0d6e7100942d83d0251b75be91d08547a99cc3219cccf9de2339ccd204a11c9 |
| runs (coding-runs.csv) | 254191310ba6cb90b3e7d60c5a7eccd289d30ce198227e1d5539c0b448853f24 |
| corrections (core-corrections.csv) | 3af3c1442456900dd268b4749eda1d0b00583b55a5256e14fafe2b754f92cdd7 |
