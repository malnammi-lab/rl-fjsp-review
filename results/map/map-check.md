# The map checked by a person

Written by `runners/map_check.py` from `configs\map-vote.toml`; do not edit, rerun the runner.

25 records drawn under seed 20261015 from the 508 the screening included without a person outside the calibration batch, coded by Moayad Alnammi from their titles and abstracts under the scheme's rules, blind to the models' codes (protocol, Two tiers).

| Axis | Agreement with the map | Cohen's kappa with the map | Agreement with qwen38 | Agreement with gemma26 | Agreement with glimmer30 |
|---|---:|---:|---:|---:|---:|
| `policy_role` | 18 of 25 (72%) | 0.615 | 15 of 25 | 18 of 25 | 19 of 25 |
| `learner_depth` | 25 of 25 (100%) | 1.000 | 25 of 25 | 25 of 25 | 24 of 25 |
| `readiness_claim` | 25 of 25 (100%) | n/a | 25 of 25 | 25 of 25 | 24 of 25 |

With 25 records, a kappa is a rough figure; the agreement counts are the plainer reading.

## Where the person and the map differ

| Record | Axis | Person | Map | qwen38 | gemma26 | glimmer30 |
|---|---|---|---|---|---|---|
| 237 | `policy_role` | `not-stated` | `end-to-end` | `end-to-end` | `not-stated` | `end-to-end` |
| 263 | `policy_role` | `not-stated` | `end-to-end` | `end-to-end` | `not-stated` | `end-to-end` |
| 302 | `policy_role` | `not-stated` | `end-to-end` | `end-to-end` | `end-to-end` | `end-to-end` |
| 316 | `policy_role` | `not-stated` | `steering-heuristic` | `steering-heuristic` | `steering-heuristic` | `steering-heuristic` |
| 411 | `policy_role` | `steering-rules` | `end-to-end` | `end-to-end` | `end-to-end` | `steering-rules` |
| 450 | `policy_role` | `steering-heuristic` | `steering-rules` | `steering-rules` | `steering-rules` | `steering-heuristic` |
| 509 | `policy_role` | `not-stated` | `steering-heuristic` | `steering-heuristic` | `steering-heuristic` | `not-stated` |
