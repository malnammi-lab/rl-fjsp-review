# The map: the vote and the models' agreement

Written by `runners/map_vote.py` from `configs\map-vote.toml`; do not edit, rerun the runner.

533 records, the screening's inclusions: 532 coded by qwen38, gemma26, glimmer30 from their titles and abstracts (protocol, Two tiers), and 1 (74) by a person, from the title and abstract with the same scheme. A record a person coded takes the person's codes after the rules, without a vote, and is not in the agreement below, which is the models'.

The vote: a cell takes the code at least two models give, code by code on a list axis, and is `not-stated` when no code has a majority; on `readiness_claim`, whose codes are levels, it takes the highest level at least two models reach.

## The scheme's rules

Cells each rule changed in each model's codes, before the vote, and in the voted codes, and in the codes a person gave. Every changed cell is listed in `results/map/map-implications.csv`.

| Rule | qwen38 | gemma26 | glimmer30 | after the vote | person |
| --- | ---: | ---: | ---: | ---: | ---: |
| steering role: no action | 0 | 0 | 0 | 0 | 0 |
| role not stated: action not stated | 0 | 0 | 0 | 2 | 0 |
| non-deep learner: no architecture | 0 | 0 | 0 | 0 | 0 |
| learner not stated: architecture not stated | 0 | 1 | 0 | 0 | 0 |
| tabular learner: discrete states | 1 | 84 | 82 | 0 | 0 |

## Agreement per axis

Kappa: the agreement compared with the bar. Each code is read as present or absent, Cohen's kappa is taken between two models on their codes after the rules and averaged over the three pairs, and the axis's kappa is the mean over its categories at step 2 of the core rule that the map holds: every code but `not-stated`, `other`, `not-applicable` that the voted map gives to at least one record. The kappas of the other codes are shown below and are not in the mean; an axis with no such category does not steer. Multiclass kappa: on a single axis, Cohen's kappa over all its codes as given, for reference. `readiness_claim` never steers step 2, so it has no kappa compared with the bar, and its multiclass kappa is its agreement. No majority: cells the vote makes `not-stated` because no code has a majority. Coverage: the axis counts toward the core's coverage minimum, its kappa being at least 0.6.

| Axis | Kind | Kappa | Multiclass kappa | All three agree | No majority | Coverage |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `policy_role` | single | 0.817 | 0.765 | 397 (74.6%) | 4 | yes |
| `coordination` | list | 0.890 |  | 491 (92.3%) | 0 | yes |
| `scheduling_action` | single | 0.565 | 0.849 | 454 (85.3%) | 4 | no |
| `learner_depth` | single | 0.978 | 0.968 | 521 (97.9%) | 0 | yes |
| `deep_architecture` | list | 0.897 |  | 466 (87.6%) | 3 | yes |
| `training_algorithm_family` | list | 0.986 |  | 520 (97.7%) | 0 | yes |
| `hybridization` | single | 0.931 | 0.932 | 506 (95.1%) | 0 | yes |
| `state_content` | list | 0.665 |  | 371 (69.7%) | 0 | yes |
| `state_encoding` | list | 0.743 |  | 437 (82.1%) | 2 | yes |
| `dynamic_events` | list | 0.944 |  | 465 (87.4%) | 2 | yes |
| `objective` | list | 0.914 |  | 467 (87.8%) | 0 | yes |
| `constraints` | list | 0.887 |  | 405 (76.1%) | 14 | yes |
| `instances` | list | 0.821 |  | 441 (82.9%) | 0 | yes |
| `domain` | list | 0.882 |  | 528 (99.2%) | 0 | yes |
| `readiness_claim` | single | n/a | 0.644 | 493 (92.7%) | 0 | no |

Axes that count toward the core's coverage: `policy_role`, `coordination`, `learner_depth`, `deep_architecture`, `training_algorithm_family`, `hybridization`, `state_content`, `state_encoding`, `dynamic_events`, `objective`, `constraints`, `instances`, `domain`.

## The map's codes

Records the map gives each code, among the records the models coded (on a list axis, a record counts once under each of its codes), the code's kappa, read as present or absent, and whether it is in the axis's kappa.

| Axis | Code | Records | Kappa | In the axis's kappa |
| --- | --- | ---: | ---: | --- |
| `policy_role` | `end-to-end` | 163 | 0.699 | yes |
| `policy_role` | `steering-rules` | 60 | 0.841 | yes |
| `policy_role` | `steering-heuristic` | 152 | 0.911 | yes |
| `policy_role` | `not-stated` | 157 | 0.648 | no |
| `coordination` | `single-agent` | 409 | 0.901 | yes |
| `coordination` | `multi-agent` | 120 | 0.929 | yes |
| `coordination` | `hierarchical` | 37 | 0.839 | yes |
| `coordination` | `not-stated` | 0 | -0.002 | no |
| `scheduling_action` | `operation` | 13 | 0.664 | yes |
| `scheduling_action` | `machine` | 2 | 0.265 | yes |
| `scheduling_action` | `operation-machine-pair` | 93 | 0.809 | yes |
| `scheduling_action` | `whole-schedule` | 0 | 0.000 | no |
| `scheduling_action` | `schedule-change` | 2 | 0.522 | yes |
| `scheduling_action` | `other` | 2 | 0.443 | no |
| `scheduling_action` | `not-applicable` | 212 | 0.921 | no |
| `scheduling_action` | `not-stated` | 208 | 0.846 | no |
| `learner_depth` | `deep` | 388 | 0.965 | yes |
| `learner_depth` | `non-neural` | 0 |  | no |
| `learner_depth` | `tabular` | 95 | 0.991 | yes |
| `learner_depth` | `not-stated` | 49 | 0.933 | no |
| `deep_architecture` | `fully-connected` | 16 | 0.896 | yes |
| `deep_architecture` | `convolutional` | 6 | 1.000 | yes |
| `deep_architecture` | `recurrent` | 13 | 1.000 | yes |
| `deep_architecture` | `graph-neural-network` | 145 | 0.912 | yes |
| `deep_architecture` | `attention-transformer` | 52 | 0.766 | yes |
| `deep_architecture` | `pointer-network` | 5 | 0.807 | yes |
| `deep_architecture` | `other` | 2 | 0.092 | no |
| `deep_architecture` | `not-applicable` | 95 | 0.991 | no |
| `deep_architecture` | `not-stated` | 250 | 0.929 | no |
| `training_algorithm_family` | `value-based` | 218 | 0.987 | yes |
| `training_algorithm_family` | `policy-gradient` | 122 | 0.996 | yes |
| `training_algorithm_family` | `actor-critic` | 26 | 0.974 | yes |
| `training_algorithm_family` | `other` | 7 | 0.736 | no |
| `training_algorithm_family` | `not-stated` | 170 | 0.983 | no |
| `hybridization` | `none` | 337 | 0.935 | yes |
| `hybridization` | `metaheuristic` | 179 | 0.935 | yes |
| `hybridization` | `exact` | 3 | 1.000 | yes |
| `hybridization` | `other-learner` | 13 | 0.855 | yes |
| `hybridization` | `not-stated` | 0 |  | no |
| `state_content` | `operations` | 123 | 0.749 | yes |
| `state_content` | `jobs` | 39 | 0.807 | yes |
| `state_content` | `machines` | 136 | 0.785 | yes |
| `state_content` | `shop-aggregate` | 13 | 0.558 | yes |
| `state_content` | `events` | 9 | 0.407 | yes |
| `state_content` | `other-resources` | 28 | 0.741 | yes |
| `state_content` | `search-state` | 16 | 0.610 | yes |
| `state_content` | `other` | 0 | -0.003 | no |
| `state_content` | `not-stated` | 362 | 0.703 | no |
| `state_encoding` | `discrete-states` | 95 | 0.991 | yes |
| `state_encoding` | `feature-vector` | 42 | 0.694 | yes |
| `state_encoding` | `sequence` | 3 | 0.441 | yes |
| `state_encoding` | `set` | 0 | 0.000 | no |
| `state_encoding` | `matrix` | 6 | 0.858 | yes |
| `state_encoding` | `disjunctive-graph` | 44 | 0.907 | yes |
| `state_encoding` | `heterogeneous-graph` | 97 | 0.890 | yes |
| `state_encoding` | `other-graph` | 6 | 0.421 | yes |
| `state_encoding` | `text` | 0 | 0.000 | no |
| `state_encoding` | `other` | 0 | 0.000 | no |
| `state_encoding` | `not-stated` | 259 | 0.822 | no |
| `dynamic_events` | `none` | 289 | 0.917 | yes |
| `dynamic_events` | `job-arrivals` | 104 | 0.964 | yes |
| `dynamic_events` | `machine-breakdowns` | 65 | 0.959 | yes |
| `dynamic_events` | `uncertain-processing-times` | 33 | 0.937 | yes |
| `dynamic_events` | `other` | 32 | 0.723 | no |
| `dynamic_events` | `not-stated` | 78 | 0.780 | no |
| `objective` | `makespan` | 278 | 0.952 | yes |
| `objective` | `tardiness` | 76 | 0.970 | yes |
| `objective` | `flow-time` | 13 | 0.888 | yes |
| `objective` | `workload` | 35 | 0.947 | yes |
| `objective` | `utilization` | 26 | 0.895 | yes |
| `objective` | `energy` | 130 | 0.976 | yes |
| `objective` | `cost` | 23 | 0.909 | yes |
| `objective` | `robustness` | 18 | 0.777 | yes |
| `objective` | `other` | 26 | 0.685 | no |
| `objective` | `not-stated` | 158 | 0.940 | no |
| `constraints` | `none` | 286 | 0.809 | yes |
| `constraints` | `transport` | 98 | 0.926 | yes |
| `constraints` | `setup-times` | 21 | 0.918 | yes |
| `constraints` | `workers` | 47 | 0.945 | yes |
| `constraints` | `energy` | 21 | 0.762 | yes |
| `constraints` | `distributed` | 62 | 0.962 | yes |
| `constraints` | `other` | 53 | 0.565 | no |
| `constraints` | `not-stated` | 18 | 0.058 | no |
| `instances` | `public-benchmark` | 186 | 0.972 | yes |
| `instances` | `generated` | 130 | 0.821 | yes |
| `instances` | `industrial` | 42 | 0.669 | yes |
| `instances` | `not-stated` | 250 | 0.854 | no |
| `domain` | `manufacturing` | 528 | 0.765 | yes |
| `domain` | `computing-networks` | 3 | 1.000 | yes |
| `domain` | `other` | 2 | 0.554 | no |
| `domain` | `not-stated` | 0 |  | no |
| `readiness_claim` | `none` | 485 | 0.663 |  |
| `readiness_claim` | `real-data` | 42 | 0.670 |  |
| `readiness_claim` | `twin-or-hil` | 3 | 0.282 |  |
| `readiness_claim` | `testbed-or-shadow` | 2 | 0.222 |  |
| `readiness_claim` | `live-system` | 0 |  |  |
| `readiness_claim` | `not-stated` | 0 |  |  |
