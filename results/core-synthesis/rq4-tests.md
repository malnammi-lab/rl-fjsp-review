# Transfer tests: how the test instances differ, where they come from, the mode, the outcome

Written by `runners/core_synthesis.py` from `configs\core-synthesis.toml`; do not edit, rerun the runner.

RQ 4. Items of the table, as a share of the column's items with an answer.

| Field | Code | All | End to end | Steering |
| --- | --- | ---: | ---: | ---: |
| differs | size | 87 (55.8%) | 76 (60.3%) | 11 (36.7%) |
| differs | flexibility | 9 (5.8%) | 8 (6.3%) | 1 (3.3%) |
| differs | layout | 2 (1.3%) | 1 (0.8%) | 1 (3.3%) |
| differs | processing-times | 22 (14.1%) | 20 (15.9%) | 2 (6.7%) |
| differs | events | 15 (9.6%) | 5 (4.0%) | 10 (33.3%) |
| differs | objective-or-constraints | 5 (3.2%) | 2 (1.6%) | 3 (10.0%) |
| differs | other-factory | 3 (1.9%) | 2 (1.6%) | 1 (3.3%) |
| differs | public-benchmark | 63 (40.4%) | 59 (46.8%) | 4 (13.3%) |
| differs | real-data | 6 (3.8%) | 4 (3.2%) | 2 (6.7%) |
| differs | other | 9 (5.8%) | 6 (4.8%) | 3 (10.0%) |
| provenance | generated | 72 (46.2%) | 53 (42.1%) | 19 (63.3%) |
| provenance | public-benchmark | 75 (48.1%) | 67 (53.2%) | 8 (26.7%) |
| provenance | industrial | 7 (4.5%) | 5 (4.0%) | 2 (6.7%) |
| provenance | other | 2 (1.3%) | 1 (0.8%) | 1 (3.3%) |
| mode | unchanged | 150 (96.2%) | 126 (100.0%) | 24 (80.0%) |
| mode | fine-tuned | 5 (3.2%) | 0 (0.0%) | 5 (16.7%) |
| mode | not-stated | 1 (0.6%) | 0 (0.0%) | 1 (3.3%) |
| outcome | holds | 149 (95.5%) | 120 (95.2%) | 29 (96.7%) |
| outcome | mixed | 7 (4.5%) | 6 (4.8%) | 1 (3.3%) |
