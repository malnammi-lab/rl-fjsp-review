# The sensitivity analyses

Written by `runners/core_synthesis.py` from `configs\core-synthesis.toml`; do not edit, rerun the runner.

Each table recomputed without some studies or answers; the largest change in a share, in percentage points, with the cell where it falls. (2) and (4) are in abstract-vs-full-text.md and map-unanimous.md.

## (1) Without the lowest-quality fifth

10 studies left out; 89 studies remain.

| Table | Largest change (pp) | Cell |
| --- | ---: | --- |
| rq1-role-by-family | 1.9 | policy_role / end-to-end / policy-gradient |
| rq1-approach | 3.4 | hybridization / metaheuristic / all |
| rq1-steering | 3.9 | steering_action / other / steering |
| rq2-formulation | 4.7 | mask_enforces / not-applicable / all |
| rq2-action-by-role | 2.1 | policy_role / end-to-end / operation-machine-pair |
| rq2-models | 4.2 | state_encoding / heterogeneous-graph / end-to-end |
| rq3-instances | 3.3 | benchmark_sets / hurink / end-to-end |
| rq3-baselines | 5.8 | run / copied / end-to-end |
| rq3-practice | 5.4 | data_release / not-reported / end-to-end |
| rq3-claims | 10.0 | trains-stably / shares a named benchmark set with another study making it / steering |
| rq4-transfer | 4.8 | transfer_tests / 2 / end-to-end |
| rq4-tests | 3.8 | differs / public-benchmark / all |
| rq5-readiness | 5.6 | limitations / training-cost / end-to-end |
| rq5-level-by-abstract-claim | 1.0 | readiness_level / L4 / real-data |

## (3) Without the studies admitted at step 2

36 studies left out; 63 studies remain.

| Table | Largest change (pp) | Cell |
| --- | ---: | --- |
| rq1-role-by-family | 5.5 | policy_role / steering-rules / value-based |
| rq1-approach | 10.6 | training_algorithm_family / value-based / steering |
| rq1-steering | 6.3 | steering_action / other / steering |
| rq2-formulation | 9.7 | decision_points / event-driven / end-to-end |
| rq2-action-by-role | 3.0 | policy_role / end-to-end / operation-machine-pair |
| rq2-models | 13.1 | deep_architecture / graph-neural-network / end-to-end |
| rq3-instances | 9.6 | benchmark_sets / other-benchmark / steering |
| rq3-baselines | 6.2 | run / copied / end-to-end |
| rq3-practice | 13.0 | code_release / not-reported / end-to-end |
| rq3-claims | 20.8 | beats-exact-solver / comparable with another study making it on instances, metrics, baselines and time limits / steering |
| rq4-transfer | 8.7 | transfer_tests / 1 / end-to-end |
| rq4-tests | 13.7 | provenance / public-benchmark / steering |
| rq5-readiness | 9.0 | limitations / generalization / steering |
| rq5-level-by-abstract-claim | 1.6 | readiness_level / L2 / none |

## (5) Without the answers the judge disputed

1565 answers left out; 99 studies remain.

| Table | Largest change (pp) | Cell |
| --- | ---: | --- |
| rq1-role-by-family | 2.0 | policy_role / steering-rules / value-based |
| rq1-approach | 16.3 | multi_agent_training / not-applicable / end-to-end |
| rq1-steering | 12.9 | steered_method / genetic-algorithm / steering |
| rq2-formulation | 18.8 | training_regime / distribution / steering |
| rq2-action-by-role | 4.0 | policy_role / end-to-end / operation-machine-pair |
| rq2-models | 12.0 | deep_architecture / fully-connected / end-to-end |
| rq3-instances | 25.9 | reschedule_trigger / each-decision / steering |
| rq3-baselines | 26.4 | kind / learned-policy / end-to-end |
| rq3-practice | 40.6 | seeds / reported / end-to-end |
| rq3-claims | 37.2 | beats-learned-policies / shares an objective and a headline statistic with another study making it / steering |
| rq4-transfer | 18.8 | training_instances / public-benchmark / steering |
| rq4-tests | 16.7 | mode / fine-tuned / steering |
| rq5-readiness | 25.3 | limitations / other / end-to-end |
| rq5-level-by-abstract-claim | 2.0 | readiness_level / L1 / none |

