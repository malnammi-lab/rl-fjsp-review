# The core's synthesis

Written by `runners/core_synthesis.py` from `configs\core-synthesis.toml`; do not edit, rerun the runner.

99 studies: End to end 53, Steering 46.

## Roles by algorithm family

RQ 1.1, 1.2. Counts of studies (99), each under every pair of its codes.

| Field | Code | value-based | policy-gradient | actor-critic | other | not-stated | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| policy_role | end-to-end | 5 | 43 | 3 | 1 | 1 | 53 |
| policy_role | steering-rules | 15 | 7 | 2 | 0 | 0 | 24 |
| policy_role | steering-heuristic | 19 | 2 | 1 | 0 | 0 | 22 |

## The approach: study type, coordination, learner, algorithm, paradigm, hybridization

RQ 1.1, 1.2. Studies, as a share of the column's studies with an answer to the question; a study with several codes counts under each.

| Field | Code | All | End to end | Steering |
| --- | --- | ---: | ---: | ---: |
| study_type | new-method | 99 (100.0%) | 53 (100.0%) | 46 (100.0%) |
| coordination | single-agent | 70 (70.7%) | 33 (62.3%) | 37 (80.4%) |
| coordination | multi-agent | 29 (29.3%) | 20 (37.7%) | 9 (19.6%) |
| coordination | hierarchical | 8 (8.1%) | 3 (5.7%) | 5 (10.9%) |
| agent_unit | machine | 6 (6.1%) | 4 (7.5%) | 2 (4.3%) |
| agent_unit | job | 4 (4.0%) | 3 (5.7%) | 1 (2.2%) |
| agent_unit | operation | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| agent_unit | sub-decision | 17 (17.2%) | 14 (26.4%) | 3 (6.5%) |
| agent_unit | level | 7 (7.1%) | 3 (5.7%) | 4 (8.7%) |
| agent_unit | other | 2 (2.0%) | 1 (1.9%) | 1 (2.2%) |
| agent_unit | not-applicable | 70 (70.7%) | 33 (62.3%) | 37 (80.4%) |
| multi_agent_training | independent | 16 (16.2%) | 11 (20.8%) | 5 (10.9%) |
| multi_agent_training | shared-parameters | 2 (2.0%) | 2 (3.8%) | 0 (0.0%) |
| multi_agent_training | centralized-critic | 11 (11.1%) | 9 (17.0%) | 2 (4.3%) |
| multi_agent_training | value-factorization | 1 (1.0%) | 0 (0.0%) | 1 (2.2%) |
| multi_agent_training | communication | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| multi_agent_training | other | 3 (3.0%) | 1 (1.9%) | 2 (4.3%) |
| multi_agent_training | not-applicable | 70 (70.7%) | 33 (62.3%) | 37 (80.4%) |
| sub_decision | sequencing | 10 (10.1%) | 6 (11.3%) | 4 (8.7%) |
| sub_decision | assignment | 3 (3.0%) | 3 (5.7%) | 0 (0.0%) |
| sub_decision | both | 65 (65.7%) | 44 (83.0%) | 21 (45.7%) |
| sub_decision | other | 1 (1.0%) | 0 (0.0%) | 1 (2.2%) |
| sub_decision | not-applicable | 20 (20.2%) | 0 (0.0%) | 20 (43.5%) |
| learner_depth | deep | 89 (89.9%) | 53 (100.0%) | 36 (78.3%) |
| learner_depth | tabular | 10 (10.1%) | 0 (0.0%) | 10 (21.7%) |
| training_algorithm_family | value-based | 44 (44.4%) | 9 (17.0%) | 35 (76.1%) |
| training_algorithm_family | policy-gradient | 53 (53.5%) | 44 (83.0%) | 9 (19.6%) |
| training_algorithm_family | actor-critic | 8 (8.1%) | 4 (7.5%) | 4 (8.7%) |
| training_algorithm_family | other | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| algorithm_family | value-based | 39 (39.4%) | 5 (9.4%) | 34 (73.9%) |
| algorithm_family | policy-gradient | 52 (52.5%) | 43 (81.1%) | 9 (19.6%) |
| algorithm_family | actor-critic | 6 (6.1%) | 3 (5.7%) | 3 (6.5%) |
| algorithm_family | other | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| algorithm_family | not-stated | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| algorithm | q-learning | 39 (39.4%) | 5 (9.4%) | 34 (73.9%) |
| algorithm | reinforce | 3 (3.0%) | 2 (3.8%) | 1 (2.2%) |
| algorithm | ppo | 49 (49.5%) | 41 (77.4%) | 8 (17.4%) |
| algorithm | a2c-a3c | 1 (1.0%) | 0 (0.0%) | 1 (2.2%) |
| algorithm | ddpg-td3 | 3 (3.0%) | 1 (1.9%) | 2 (4.3%) |
| algorithm | sac | 2 (2.0%) | 2 (3.8%) | 0 (0.0%) |
| algorithm | other | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| algorithm | not-stated | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| policy_update | on-policy | 53 (53.5%) | 43 (81.1%) | 10 (21.7%) |
| policy_update | off-policy | 44 (44.4%) | 8 (15.1%) | 36 (78.3%) |
| policy_update | other | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| policy_update | not-stated | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| paradigm | online | 99 (100.0%) | 53 (100.0%) | 46 (100.0%) |
| paradigm | imitation | 3 (3.0%) | 3 (5.7%) | 0 (0.0%) |
| paradigm | model-based | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| paradigm | other | 2 (2.0%) | 1 (1.9%) | 1 (2.2%) |
| hybridization | none | 65 (65.7%) | 43 (81.1%) | 22 (47.8%) |
| hybridization | metaheuristic | 30 (30.3%) | 6 (11.3%) | 24 (52.2%) |
| hybridization | exact | 2 (2.0%) | 2 (3.8%) | 0 (0.0%) |
| hybridization | other-learner | 2 (2.0%) | 2 (3.8%) | 0 (0.0%) |

## What a steering policy chooses or sets, and the methods it steers

RQ 1.1. Studies, as a share of the column's studies with an answer to the question; a study with several codes counts under each.

| Field | Code | Steering |
| --- | --- | ---: |
| steering_action | dispatching-rule | 24 (52.2%) |
| steering_action | rule-weights | 1 (2.2%) |
| steering_action | parameter | 5 (10.9%) |
| steering_action | operator | 14 (30.4%) |
| steering_action | neighborhood | 1 (2.2%) |
| steering_action | other | 6 (13.0%) |
| steered_method | dispatching-rules | 26 (56.5%) |
| steered_method | genetic-algorithm | 10 (21.7%) |
| steered_method | tabu-search | 1 (2.2%) |
| steered_method | variable-neighborhood-search | 4 (8.7%) |
| steered_method | swarm | 2 (4.3%) |
| steered_method | local-search | 7 (15.2%) |
| steered_method | constructive-heuristic | 2 (4.3%) |

## The decision process: state, action, mask, reward, decision points, observability

RQ 2.1. Studies, as a share of the column's studies with an answer to the question; a study with several codes counts under each.

| Field | Code | All | End to end | Steering |
| --- | --- | ---: | ---: | ---: |
| state_content | operations | 68 (68.7%) | 52 (98.1%) | 16 (34.8%) |
| state_content | jobs | 42 (42.4%) | 24 (45.3%) | 18 (39.1%) |
| state_content | machines | 67 (67.7%) | 49 (92.5%) | 18 (39.1%) |
| state_content | shop-aggregate | 40 (40.4%) | 21 (39.6%) | 19 (41.3%) |
| state_content | events | 6 (6.1%) | 2 (3.8%) | 4 (8.7%) |
| state_content | other-resources | 18 (18.2%) | 8 (15.1%) | 10 (21.7%) |
| state_content | search-state | 14 (14.1%) | 0 (0.0%) | 14 (30.4%) |
| state_content | other | 2 (2.0%) | 0 (0.0%) | 2 (4.3%) |
| scheduling_action | operation | 6 (6.1%) | 6 (11.3%) | 0 (0.0%) |
| scheduling_action | machine | 4 (4.0%) | 4 (7.5%) | 0 (0.0%) |
| scheduling_action | operation-machine-pair | 41 (41.4%) | 41 (77.4%) | 0 (0.0%) |
| scheduling_action | schedule-change | 2 (2.0%) | 2 (3.8%) | 0 (0.0%) |
| scheduling_action | not-applicable | 46 (46.5%) | 0 (0.0%) | 46 (100.0%) |
| action_space | discrete | 94 (94.9%) | 50 (94.3%) | 44 (95.7%) |
| action_space | continuous | 3 (3.0%) | 1 (1.9%) | 2 (4.3%) |
| action_space | hybrid | 2 (2.0%) | 2 (3.8%) | 0 (0.0%) |
| action_set | fixed-list | 46 (46.5%) | 3 (5.7%) | 43 (93.5%) |
| action_set | per-candidate | 50 (50.5%) | 49 (92.5%) | 1 (2.2%) |
| action_set | not-applicable | 3 (3.0%) | 1 (1.9%) | 2 (4.3%) |
| action_count | reported | 45 (45.5%) | 3 (5.7%) | 42 (91.3%) |
| action_count | not-stated | 1 (1.0%) | 0 (0.0%) | 1 (2.2%) |
| action_count | not-applicable | 53 (53.5%) | 50 (94.3%) | 3 (6.5%) |
| action_count | median | 9 | 25 | 8 |
| action_count | smallest | 3 | 12 | 3 |
| action_count | largest | 144 | 30 | 144 |
| wait_action | yes | 7 (7.1%) | 5 (9.4%) | 2 (4.3%) |
| wait_action | no | 80 (80.8%) | 41 (77.4%) | 39 (84.8%) |
| wait_action | not-stated | 12 (12.1%) | 7 (13.2%) | 5 (10.9%) |
| invalid_actions | masked | 28 (28.3%) | 26 (49.1%) | 2 (4.3%) |
| invalid_actions | repaired | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| invalid_actions | by-construction | 74 (74.7%) | 32 (60.4%) | 42 (91.3%) |
| invalid_actions | not-stated | 3 (3.0%) | 1 (1.9%) | 2 (4.3%) |
| mask_enforces | precedence | 19 (19.2%) | 19 (35.8%) | 0 (0.0%) |
| mask_enforces | capacity | 10 (10.1%) | 9 (17.0%) | 1 (2.2%) |
| mask_enforces | eligibility | 21 (21.2%) | 21 (39.6%) | 0 (0.0%) |
| mask_enforces | priority-filter | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| mask_enforces | other | 5 (5.1%) | 3 (5.7%) | 2 (4.3%) |
| mask_enforces | not-applicable | 71 (71.7%) | 27 (50.9%) | 44 (95.7%) |
| reward_measure | makespan | 73 (73.7%) | 47 (88.7%) | 26 (56.5%) |
| reward_measure | idle-time | 5 (5.1%) | 5 (9.4%) | 0 (0.0%) |
| reward_measure | utilization | 10 (10.1%) | 5 (9.4%) | 5 (10.9%) |
| reward_measure | tardiness | 17 (17.2%) | 8 (15.1%) | 9 (19.6%) |
| reward_measure | flow-time | 5 (5.1%) | 3 (5.7%) | 2 (4.3%) |
| reward_measure | workload | 8 (8.1%) | 6 (11.3%) | 2 (4.3%) |
| reward_measure | energy | 21 (21.2%) | 6 (11.3%) | 15 (32.6%) |
| reward_measure | cost | 5 (5.1%) | 3 (5.7%) | 2 (4.3%) |
| reward_measure | other | 19 (19.2%) | 6 (11.3%) | 13 (28.3%) |
| reward_timing | per-step | 88 (88.9%) | 45 (84.9%) | 43 (93.5%) |
| reward_timing | terminal | 4 (4.0%) | 4 (7.5%) | 0 (0.0%) |
| reward_timing | mixed | 7 (7.1%) | 4 (7.5%) | 3 (6.5%) |
| reward_source | hand-designed | 98 (99.0%) | 52 (98.1%) | 46 (100.0%) |
| reward_source | learned | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| decision_points | event-driven | 37 (37.4%) | 19 (35.8%) | 18 (39.1%) |
| decision_points | fixed-interval | 2 (2.0%) | 1 (1.9%) | 1 (2.2%) |
| decision_points | per-operation | 39 (39.4%) | 31 (58.5%) | 8 (17.4%) |
| decision_points | per-iteration | 20 (20.2%) | 1 (1.9%) | 19 (41.3%) |
| decision_points | other | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| observability | full | 94 (94.9%) | 49 (92.5%) | 45 (97.8%) |
| observability | partial | 5 (5.1%) | 4 (7.5%) | 1 (2.2%) |
| training_regime | distribution | 76 (76.8%) | 51 (96.2%) | 25 (54.3%) |
| training_regime | per-instance | 12 (12.1%) | 1 (1.9%) | 11 (23.9%) |
| training_regime | online | 11 (11.1%) | 1 (1.9%) | 10 (21.7%) |

## The scheduling action by role

RQ 2.1. Counts of studies (99), each under every pair of its codes.

| Field | Code | operation | machine | operation-machine-pair | schedule-change | not-applicable | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| policy_role | end-to-end | 6 | 4 | 41 | 2 | 0 | 53 |
| policy_role | steering-rules | 0 | 0 | 0 | 0 | 24 | 24 |
| policy_role | steering-heuristic | 0 | 0 | 0 | 0 | 22 | 22 |

## Models and the encoding of the state

RQ 2.2. Studies, as a share of the column's studies with an answer to the question; a study with several codes counts under each.

| Field | Code | All | End to end | Steering |
| --- | --- | ---: | ---: | ---: |
| deep_architecture | fully-connected | 50 (50.5%) | 24 (45.3%) | 26 (56.5%) |
| deep_architecture | convolutional | 8 (8.1%) | 4 (7.5%) | 4 (8.7%) |
| deep_architecture | recurrent | 6 (6.1%) | 5 (9.4%) | 1 (2.2%) |
| deep_architecture | graph-neural-network | 45 (45.5%) | 38 (71.7%) | 7 (15.2%) |
| deep_architecture | attention-transformer | 14 (14.1%) | 12 (22.6%) | 2 (4.3%) |
| deep_architecture | pointer-network | 7 (7.1%) | 7 (13.2%) | 0 (0.0%) |
| deep_architecture | other | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| deep_architecture | not-applicable | 10 (10.1%) | 0 (0.0%) | 10 (21.7%) |
| deep_architecture | not-stated | 5 (5.1%) | 0 (0.0%) | 5 (10.9%) |
| state_encoding | discrete-states | 10 (10.1%) | 0 (0.0%) | 10 (21.7%) |
| state_encoding | feature-vector | 49 (49.5%) | 19 (35.8%) | 30 (65.2%) |
| state_encoding | sequence | 6 (6.1%) | 4 (7.5%) | 2 (4.3%) |
| state_encoding | set | 8 (8.1%) | 8 (15.1%) | 0 (0.0%) |
| state_encoding | matrix | 3 (3.0%) | 0 (0.0%) | 3 (6.5%) |
| state_encoding | disjunctive-graph | 23 (23.2%) | 19 (35.8%) | 4 (8.7%) |
| state_encoding | heterogeneous-graph | 23 (23.2%) | 19 (35.8%) | 4 (8.7%) |
| state_encoding | other-graph | 5 (5.1%) | 5 (9.4%) | 0 (0.0%) |
| input_size | fixed | 11 (11.1%) | 5 (9.4%) | 6 (13.0%) |
| input_size | padded | 2 (2.0%) | 2 (3.8%) | 0 (0.0%) |
| input_size | size-agnostic | 73 (73.7%) | 45 (84.9%) | 28 (60.9%) |
| input_size | not-stated | 3 (3.0%) | 1 (1.9%) | 2 (4.3%) |
| input_size | not-applicable | 10 (10.1%) | 0 (0.0%) | 10 (21.7%) |

## Instances, benchmark sets and dynamic events

RQ 3.1. Studies, as a share of the column's studies with an answer to the question; a study with several codes counts under each.

| Field | Code | All | End to end | Steering |
| --- | --- | ---: | ---: | ---: |
| instances | public-benchmark | 72 (72.7%) | 44 (83.0%) | 28 (60.9%) |
| instances | generated | 84 (84.8%) | 46 (86.8%) | 38 (82.6%) |
| instances | industrial | 14 (14.1%) | 5 (9.4%) | 9 (19.6%) |
| benchmark_sets | brandimarte | 47 (47.5%) | 31 (58.5%) | 16 (34.8%) |
| benchmark_sets | hurink | 37 (37.4%) | 30 (56.6%) | 7 (15.2%) |
| benchmark_sets | dauzere-peres-paulli | 8 (8.1%) | 8 (15.1%) | 0 (0.0%) |
| benchmark_sets | kacem | 4 (4.0%) | 1 (1.9%) | 3 (6.5%) |
| benchmark_sets | barnes | 7 (7.1%) | 7 (13.2%) | 0 (0.0%) |
| benchmark_sets | fattahi | 5 (5.1%) | 2 (3.8%) | 3 (6.5%) |
| benchmark_sets | behnke-geiger | 4 (4.0%) | 4 (7.5%) | 0 (0.0%) |
| benchmark_sets | taillard | 3 (3.0%) | 2 (3.8%) | 1 (2.2%) |
| benchmark_sets | lawrence | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| benchmark_sets | other-benchmark | 22 (22.2%) | 8 (15.1%) | 14 (30.4%) |
| benchmark_sets | none | 27 (27.3%) | 9 (17.0%) | 18 (39.1%) |
| largest_jobs | reported | 92 (92.9%) | 50 (94.3%) | 42 (91.3%) |
| largest_jobs | not-stated | 7 (7.1%) | 3 (5.7%) | 4 (8.7%) |
| largest_jobs | median | 60 | 50 | 100 |
| largest_jobs | smallest | 5 | 15 | 5 |
| largest_jobs | largest | 10000 | 10000 | 1200 |
| largest_machines | reported | 91 (91.9%) | 50 (94.3%) | 41 (89.1%) |
| largest_machines | not-stated | 8 (8.1%) | 3 (5.7%) | 5 (10.9%) |
| largest_machines | median | 15 | 15 | 15 |
| largest_machines | smallest | 3 | 3 | 5 |
| largest_machines | largest | 60 | 60 | 50 |
| event_processes | poisson | 20 (20.2%) | 9 (17.0%) | 11 (23.9%) |
| event_processes | uniform | 13 (13.1%) | 7 (13.2%) | 6 (13.0%) |
| event_processes | fixed-times | 6 (6.1%) | 2 (3.8%) | 4 (8.7%) |
| event_processes | other | 10 (10.1%) | 3 (5.7%) | 7 (15.2%) |
| event_processes | not-stated | 3 (3.0%) | 0 (0.0%) | 3 (6.5%) |
| event_processes | not-applicable | 58 (58.6%) | 37 (69.8%) | 21 (45.7%) |
| events_in | training-and-testing | 36 (36.4%) | 14 (26.4%) | 22 (47.8%) |
| events_in | testing-only | 4 (4.0%) | 2 (3.8%) | 2 (4.3%) |
| events_in | robustness-only | 1 (1.0%) | 0 (0.0%) | 1 (2.2%) |
| events_in | not-applicable | 58 (58.6%) | 37 (69.8%) | 21 (45.7%) |
| reschedule_trigger | each-decision | 24 (24.2%) | 9 (17.0%) | 15 (32.6%) |
| reschedule_trigger | event | 16 (16.2%) | 7 (13.2%) | 9 (19.6%) |
| reschedule_trigger | other | 1 (1.0%) | 0 (0.0%) | 1 (2.2%) |
| reschedule_trigger | not-applicable | 58 (58.6%) | 37 (69.8%) | 21 (45.7%) |

## Baselines: the studies that compare with each kind

RQ 3.2. Studies with at least one item of each code, as a share of the column's studies.

| Field | Code | All | End to end | Steering |
| --- | --- | ---: | ---: | ---: |
| kind | dispatching-rule | 73 (73.7%) | 46 (86.8%) | 27 (58.7%) |
| kind | metaheuristic | 77 (77.8%) | 41 (77.4%) | 36 (78.3%) |
| kind | exact-solver | 38 (38.4%) | 27 (50.9%) | 11 (23.9%) |
| kind | learned-policy | 74 (74.7%) | 44 (83.0%) | 30 (65.2%) |
| kind | other | 12 (12.1%) | 5 (9.4%) | 7 (15.2%) |
| run | rerun | 97 (98.0%) | 51 (96.2%) | 46 (100.0%) |
| run | copied | 19 (19.2%) | 16 (30.2%) | 3 (6.5%) |
| run | not-stated | 7 (7.1%) | 3 (5.7%) | 4 (8.7%) |
| time_limit | stated | 61 (61.6%) | 34 (64.2%) | 27 (58.7%) |
| time_limit | not-stated | 48 (48.5%) | 27 (50.9%) | 21 (45.7%) |
| time_limit | not-applicable | 77 (77.8%) | 47 (88.7%) | 30 (65.2%) |

## Metrics and reporting: time, cost, scaling, runs, ablation, release, stability

RQ 3.2, 3.3. Studies, as a share of the column's studies with an answer to the question; a study with several codes counts under each.

| Field | Code | All | End to end | Steering |
| --- | --- | ---: | ---: | ---: |
| baselines | 1 | 5 (5.1%) | 2 (3.8%) | 3 (6.5%) |
| baselines | 2 | 13 (13.1%) | 4 (7.5%) | 9 (19.6%) |
| baselines | 3 or more | 81 (81.8%) | 47 (88.7%) | 34 (73.9%) |
| metrics | gap | 71 (71.7%) | 45 (84.9%) | 26 (56.5%) |
| metrics | win-count | 44 (44.4%) | 21 (39.6%) | 23 (50.0%) |
| metrics | statistical-test | 44 (44.4%) | 22 (41.5%) | 22 (47.8%) |
| metrics | robustness | 17 (17.2%) | 8 (15.1%) | 9 (19.6%) |
| metrics | other | 38 (38.4%) | 12 (22.6%) | 26 (56.5%) |
| metrics | not-reported | 2 (2.0%) | 1 (1.9%) | 1 (2.2%) |
| decision_time | per-schedule | 52 (52.5%) | 37 (69.8%) | 15 (32.6%) |
| decision_time | per-decision | 7 (7.1%) | 6 (11.3%) | 1 (2.2%) |
| decision_time | both | 2 (2.0%) | 1 (1.9%) | 1 (2.2%) |
| decision_time | not-reported | 38 (38.4%) | 9 (17.0%) | 29 (63.0%) |
| training_cost | time-and-hardware | 18 (18.2%) | 12 (22.6%) | 6 (13.0%) |
| training_cost | time | 2 (2.0%) | 2 (3.8%) | 0 (0.0%) |
| training_cost | hardware | 57 (57.6%) | 31 (58.5%) | 26 (56.5%) |
| training_cost | not-reported | 22 (22.2%) | 8 (15.1%) | 14 (30.4%) |
| size_scaling | beyond-training | 43 (43.4%) | 37 (69.8%) | 6 (13.0%) |
| size_scaling | within-training | 48 (48.5%) | 12 (22.6%) | 36 (78.3%) |
| size_scaling | not-reported | 8 (8.1%) | 4 (7.5%) | 4 (8.7%) |
| inference_mode | greedy | 38 (38.4%) | 28 (52.8%) | 10 (21.7%) |
| inference_mode | sampling | 12 (12.1%) | 9 (17.0%) | 3 (6.5%) |
| inference_mode | search | 2 (2.0%) | 2 (3.8%) | 0 (0.0%) |
| inference_mode | heuristic-run | 33 (33.3%) | 3 (5.7%) | 30 (65.2%) |
| inference_mode | other | 5 (5.1%) | 5 (9.4%) | 0 (0.0%) |
| inference_mode | not-stated | 9 (9.1%) | 6 (11.3%) | 3 (6.5%) |
| headline_statistic | mean | 75 (75.8%) | 38 (71.7%) | 37 (80.4%) |
| headline_statistic | best | 8 (8.1%) | 5 (9.4%) | 3 (6.5%) |
| headline_statistic | single-run | 15 (15.2%) | 10 (18.9%) | 5 (10.9%) |
| headline_statistic | other | 1 (1.0%) | 0 (0.0%) | 1 (2.2%) |
| seeds | reported | 76 (76.8%) | 36 (67.9%) | 40 (87.0%) |
| seeds | not-reported | 23 (23.2%) | 17 (32.1%) | 6 (13.0%) |
| seeds | median | 1 | 1 | 10 |
| seeds | smallest | 1 | 1 | 1 |
| seeds | largest | 20 | 20 | 20 |
| seed_spread | reported | 23 (23.2%) | 4 (7.5%) | 19 (41.3%) |
| seed_spread | not-applicable | 65 (65.7%) | 45 (84.9%) | 20 (43.5%) |
| seed_spread | not-reported | 11 (11.1%) | 4 (7.5%) | 7 (15.2%) |
| ablation | reported | 73 (73.7%) | 37 (69.8%) | 36 (78.3%) |
| ablation | not-reported | 26 (26.3%) | 16 (30.2%) | 10 (21.7%) |
| code_release | released | 16 (16.2%) | 13 (24.5%) | 3 (6.5%) |
| code_release | on-request | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| code_release | not-reported | 82 (82.8%) | 39 (73.6%) | 43 (93.5%) |
| data_release | released | 14 (14.1%) | 7 (13.2%) | 7 (15.2%) |
| data_release | on-request | 49 (49.5%) | 27 (50.9%) | 22 (47.8%) |
| data_release | public-only | 7 (7.1%) | 2 (3.8%) | 5 (10.9%) |
| data_release | not-reported | 29 (29.3%) | 17 (32.1%) | 12 (26.1%) |
| training_stability | reported | 79 (79.8%) | 46 (86.8%) | 33 (71.7%) |
| training_stability | not-reported | 20 (20.2%) | 7 (13.2%) | 13 (28.3%) |

## Shared claims and the comparability of their evidence

RQ 3.4. Per claim: the studies that make it (a share of the column's studies), then those of them whose evidence meets each of question 3.4's tests (a share of the studies making it): a named benchmark set shared with another study making the claim; an objective and a headline statistic shared with one; every baseline rerun with no time limit left unstated; all of these with one other study making it, which reruns its baselines so too; several training runs with their spread (protocol, Amendments: the tests of Question 3.4).

| Field | Code | All | End to end | Steering |
| --- | --- | ---: | ---: | ---: |
| beats-dispatching-rules | makes the claim | 73 (73.7%) | 46 (86.8%) | 27 (58.7%) |
| beats-dispatching-rules | shares a named benchmark set with another study making it | 42 (57.5%) | 32 (69.6%) | 10 (37.0%) |
| beats-dispatching-rules | shares an objective and a headline statistic with another study making it | 72 (98.6%) | 46 (100.0%) | 26 (96.3%) |
| beats-dispatching-rules | reruns every baseline, no time limit left unstated | 27 (37.0%) | 18 (39.1%) | 9 (33.3%) |
| beats-dispatching-rules | comparable with another study making it on instances, metrics, baselines and time limits | 8 (11.0%) | 6 (13.0%) | 2 (7.4%) |
| beats-dispatching-rules | several training runs with their spread | 10 (13.7%) | 4 (8.7%) | 6 (22.2%) |
| beats-metaheuristics | makes the claim | 67 (67.7%) | 33 (62.3%) | 34 (73.9%) |
| beats-metaheuristics | shares a named benchmark set with another study making it | 38 (56.7%) | 23 (69.7%) | 15 (44.1%) |
| beats-metaheuristics | shares an objective and a headline statistic with another study making it | 65 (97.0%) | 33 (100.0%) | 32 (94.1%) |
| beats-metaheuristics | reruns every baseline, no time limit left unstated | 30 (44.8%) | 12 (36.4%) | 18 (52.9%) |
| beats-metaheuristics | comparable with another study making it on instances, metrics, baselines and time limits | 10 (14.9%) | 3 (9.1%) | 7 (20.6%) |
| beats-metaheuristics | several training runs with their spread | 17 (25.4%) | 1 (3.0%) | 16 (47.1%) |
| beats-exact-solver | makes the claim | 21 (21.2%) | 13 (24.5%) | 8 (17.4%) |
| beats-exact-solver | shares a named benchmark set with another study making it | 15 (71.4%) | 11 (84.6%) | 4 (50.0%) |
| beats-exact-solver | shares an objective and a headline statistic with another study making it | 19 (90.5%) | 12 (92.3%) | 7 (87.5%) |
| beats-exact-solver | reruns every baseline, no time limit left unstated | 9 (42.9%) | 3 (23.1%) | 6 (75.0%) |
| beats-exact-solver | comparable with another study making it on instances, metrics, baselines and time limits | 5 (23.8%) | 2 (15.4%) | 3 (37.5%) |
| beats-exact-solver | several training runs with their spread | 5 (23.8%) | 1 (7.7%) | 4 (50.0%) |
| beats-learned-policies | makes the claim | 77 (77.8%) | 41 (77.4%) | 36 (78.3%) |
| beats-learned-policies | shares a named benchmark set with another study making it | 45 (58.4%) | 30 (73.2%) | 15 (41.7%) |
| beats-learned-policies | shares an objective and a headline statistic with another study making it | 76 (98.7%) | 41 (100.0%) | 35 (97.2%) |
| beats-learned-policies | reruns every baseline, no time limit left unstated | 30 (39.0%) | 16 (39.0%) | 14 (38.9%) |
| beats-learned-policies | comparable with another study making it on instances, metrics, baselines and time limits | 9 (11.7%) | 6 (14.6%) | 3 (8.3%) |
| beats-learned-policies | several training runs with their spread | 16 (20.8%) | 3 (7.3%) | 13 (36.1%) |
| generalizes-across-sizes | makes the claim | 57 (57.6%) | 43 (81.1%) | 14 (30.4%) |
| generalizes-across-sizes | shares a named benchmark set with another study making it | 36 (63.2%) | 30 (69.8%) | 6 (42.9%) |
| generalizes-across-sizes | shares an objective and a headline statistic with another study making it | 55 (96.5%) | 42 (97.7%) | 13 (92.9%) |
| generalizes-across-sizes | reruns every baseline, no time limit left unstated | 21 (36.8%) | 16 (37.2%) | 5 (35.7%) |
| generalizes-across-sizes | comparable with another study making it on instances, metrics, baselines and time limits | 8 (14.0%) | 6 (14.0%) | 2 (14.3%) |
| generalizes-across-sizes | several training runs with their spread | 5 (8.8%) | 2 (4.7%) | 3 (21.4%) |
| trains-stably | makes the claim | 20 (20.2%) | 14 (26.4%) | 6 (13.0%) |
| trains-stably | shares a named benchmark set with another study making it | 13 (65.0%) | 10 (71.4%) | 3 (50.0%) |
| trains-stably | shares an objective and a headline statistic with another study making it | 19 (95.0%) | 14 (100.0%) | 5 (83.3%) |
| trains-stably | reruns every baseline, no time limit left unstated | 6 (30.0%) | 5 (35.7%) | 1 (16.7%) |
| trains-stably | comparable with another study making it on instances, metrics, baselines and time limits | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| trains-stably | several training runs with their spread | 3 (15.0%) | 2 (14.3%) | 1 (16.7%) |

## Transfer: whether studies test it, on what, and how

RQ 4. Studies, as a share of the column's studies with an answer to the question; a study with several codes counts under each.

| Field | Code | All | End to end | Steering |
| --- | --- | ---: | ---: | ---: |
| transfer_tests | none | 28 (28.3%) | 4 (7.5%) | 24 (52.2%) |
| transfer_tests | 1 | 21 (21.2%) | 11 (20.8%) | 10 (21.7%) |
| transfer_tests | 2 | 17 (17.2%) | 12 (22.6%) | 5 (10.9%) |
| transfer_tests | 3 or more | 28 (28.3%) | 25 (47.2%) | 3 (6.5%) |
| transfer_tests | not-stated | 5 (5.1%) | 1 (1.9%) | 4 (8.7%) |
| train_test_overlap | disjoint | 59 (59.6%) | 46 (86.8%) | 13 (28.3%) |
| train_test_overlap | overlap | 31 (31.3%) | 5 (9.4%) | 26 (56.5%) |
| train_test_overlap | not-stated | 7 (7.1%) | 2 (3.8%) | 5 (10.9%) |
| train_test_overlap | not-applicable | 2 (2.0%) | 0 (0.0%) | 2 (4.3%) |
| training_instances | generated | 81 (81.8%) | 49 (92.5%) | 32 (69.6%) |
| training_instances | public-benchmark | 31 (31.3%) | 10 (18.9%) | 21 (45.7%) |
| training_instances | industrial | 7 (7.1%) | 1 (1.9%) | 6 (13.0%) |
| training_instances | not-stated | 3 (3.0%) | 1 (1.9%) | 2 (4.3%) |

## Transfer tests: how the test instances differ, where they come from, the mode, the outcome

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

## Readiness: the level reached, and decision deadlines, data, interpretability, robustness, limitations

RQ 5. Studies, as a share of the column's studies with an answer to the question; a study with several codes counts under each.

| Field | Code | All | End to end | Steering |
| --- | --- | ---: | ---: | ---: |
| readiness_level | L1 | 82 (82.8%) | 46 (86.8%) | 36 (78.3%) |
| readiness_level | L2 | 14 (14.1%) | 5 (9.4%) | 9 (19.6%) |
| readiness_level | L3 | 2 (2.0%) | 1 (1.9%) | 1 (2.2%) |
| readiness_level | L4 | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| readiness_claim | none | 82 (82.8%) | 46 (86.8%) | 36 (78.3%) |
| readiness_claim | real-data | 14 (14.1%) | 5 (9.4%) | 9 (19.6%) |
| readiness_claim | twin-or-hil | 2 (2.0%) | 1 (1.9%) | 1 (2.2%) |
| readiness_claim | testbed-or-shadow | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| decision_deadlines | tested | 5 (5.1%) | 4 (7.5%) | 1 (2.2%) |
| decision_deadlines | discussed | 51 (51.5%) | 30 (56.6%) | 21 (45.7%) |
| decision_deadlines | not-reported | 43 (43.4%) | 19 (35.8%) | 24 (52.2%) |
| imperfect_data | tested | 1 (1.0%) | 1 (1.9%) | 0 (0.0%) |
| imperfect_data | discussed | 1 (1.0%) | 0 (0.0%) | 1 (2.2%) |
| imperfect_data | not-reported | 97 (98.0%) | 52 (98.1%) | 45 (97.8%) |
| interpretability | shown | 6 (6.1%) | 3 (5.7%) | 3 (6.5%) |
| interpretability | discussed | 11 (11.1%) | 4 (7.5%) | 7 (15.2%) |
| interpretability | not-reported | 82 (82.8%) | 46 (86.8%) | 36 (78.3%) |
| robustness | tested | 59 (59.6%) | 32 (60.4%) | 27 (58.7%) |
| robustness | discussed | 11 (11.1%) | 6 (11.3%) | 5 (10.9%) |
| robustness | not-reported | 29 (29.3%) | 15 (28.3%) | 14 (30.4%) |
| limitations | scalability | 37 (37.4%) | 19 (35.8%) | 18 (39.1%) |
| limitations | generalization | 44 (44.4%) | 23 (43.4%) | 21 (45.7%) |
| limitations | training-cost | 14 (14.1%) | 10 (18.9%) | 4 (8.7%) |
| limitations | real-world-validation | 29 (29.3%) | 17 (32.1%) | 12 (26.1%) |
| limitations | assumptions | 53 (53.5%) | 26 (49.1%) | 27 (58.7%) |
| limitations | other | 42 (42.4%) | 21 (39.6%) | 21 (45.7%) |
| limitations | not-reported | 2 (2.0%) | 1 (1.9%) | 1 (2.2%) |

## The level the full text shows, against the claim the abstract makes

RQ 5. Counts of studies (99), each under every pair of its codes.

| Field | Code | none | real-data | twin-or-hil | testbed-or-shadow | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| readiness_level | L1 | 79 | 1 | 1 | 1 | 82 |
| readiness_level | L2 | 11 | 3 | 0 | 0 | 14 |
| readiness_level | L3 | 1 | 0 | 1 | 0 | 2 |
| readiness_level | L4 | 0 | 1 | 0 | 0 | 1 |

## The map's cells: the records of each role and family the abstracts give

RQ 1, 2. The map's 533 records, each under every pair of its abstract's role and family (a record with several families counts under each).

| role | family | records |
| --- | --- | ---: |
| end-to-end | value-based | 36 |
| end-to-end | policy-gradient | 66 |
| end-to-end | actor-critic | 11 |
| end-to-end | other | 3 |
| end-to-end | not-stated | 54 |
| steering | value-based | 135 |
| steering | policy-gradient | 17 |
| steering | actor-critic | 9 |
| steering | not-stated | 52 |
| not-stated | value-based | 47 |
| not-stated | policy-gradient | 39 |
| not-stated | actor-critic | 6 |
| not-stated | other | 5 |
| not-stated | not-stated | 64 |

## Every core study with its cell and its BibTeX key

RQ 1. The core's studies listed (99), each with its cell and its BibTeX key.

| number | key | cell | algorithm | policy_role | year |
| ---: | --- | --- | --- | --- | --- |
| 191 | hou2025evolutionary | end-to-end / value-based | q-learning | end-to-end | 2025 |
| 469 | zhang2025multi | end-to-end / value-based | q-learning | end-to-end | 2025 |
| 530 | su2023self | end-to-end / value-based | q-learning | end-to-end | 2022 |
| 582 | magalhaes2021encoder | end-to-end / value-based | q-learning | end-to-end | 2021 |
| 609 | wang2020adaptive | end-to-end / value-based | q-learning | end-to-end | 2020 |
| 8 | yang2026hga | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 24 | lei2022multi | end-to-end / policy-gradient | ppo | end-to-end | 2022 |
| 32 | wang2025attention | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 57 | wang2024flexible | end-to-end / policy-gradient | ppo | end-to-end | 2023 |
| 66 | wang2025end | end-to-end / policy-gradient | ppo | end-to-end | 2024 |
| 68 | liu2025preference | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 76 | han2021deep | end-to-end / policy-gradient | reinforce | end-to-end | 2021 |
| 78 | lei2024large | end-to-end / policy-gradient | ppo | end-to-end | 2023 |
| 90 | zhang2025mamhsan | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 94 | kuai2022fair | end-to-end / policy-gradient | ppo | end-to-end | 2022 |
| 108 | song2023flexible | end-to-end / policy-gradient | ppo | end-to-end | 2022 |
| 109 | hu2025graph | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 120 | chen2026hybrid | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 133 | huang2025optimizing | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 157 | zhu2026distributed | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 158 | liu2025flexible | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 160 | yuan2025dynamic | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 184 | he2026priority | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 201 | yu2025integrated | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 213 | jesus2026enhancing | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 216 | pang2026multi | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 228 | cao2026mamba | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 237 | lin2027cross | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 244 | wang2025uncertain | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 245 | li2027feature | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 255 | wang2026preference | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 258 | lv2025schedule | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 259 | shen2026transformer | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 262 | ning2026deep | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 265 | cheng2025cooperative | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 293 | zhang2025graph | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 297 | yu2026multi | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 300 | liu2026two | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 315 | liu2026document | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 336 | yang2025heterogeneous | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 339 | yi2026end | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 350 | zhang2025meta | end-to-end / policy-gradient | reinforce | end-to-end | 2025 |
| 354 | huang2025deep | end-to-end / policy-gradient | ppo | end-to-end | 2024 |
| 383 | ma2026progressive | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 409 | gan2026robust | end-to-end / policy-gradient | ppo | end-to-end | 2025 |
| 437 | zhao2026heterogeneous | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 583 | heik2024study | end-to-end / policy-gradient | ppo | end-to-end | 2024 |
| 588 | chen2026digital | end-to-end / policy-gradient | ppo | end-to-end | 2026 |
| 46 | wan2024flexible | end-to-end / actor-critic | sac | end-to-end | 2024 |
| 77 | zhang2024novel | end-to-end / actor-critic | sac | end-to-end | 2024 |
| 101 | jing2024multi | end-to-end / actor-critic | ddpg-td3 | end-to-end | 2022 |
| 214 | su2024fast | end-to-end / other | other | end-to-end | 2024 |
| 504 | zhang2026budget | end-to-end / not-stated | not-stated | end-to-end | 2026 |
| 1 | yuan2025research | steering / value-based | q-learning | steering-rules | 2023 |
| 21 | li2022real | steering / value-based | q-learning | steering-rules | 2021 |
| 41 | du2024reinforcement | steering / value-based | q-learning | steering-rules | 2022 |
| 52 | yan2025multi | steering / value-based | q-learning | steering-rules | 2025 |
| 65 | yue2024two | steering / value-based | q-learning | steering-rules | 2024 |
| 72 | lu2024double | steering / value-based | q-learning | steering-rules | 2024 |
| 92 | li2024evolution | steering / value-based | q-learning | steering-heuristic | 2023 |
| 103 | dong2025heuristic | steering / value-based | q-learning | steering-rules | 2025 |
| 106 | dung2027predictive | steering / value-based | q-learning | steering-heuristic | 2026 |
| 127 | ren2026dynamic | steering / value-based | q-learning | steering-rules | 2026 |
| 130 | cheng2025deep | steering / value-based | q-learning | steering-rules | 2025 |
| 131 | ma2025deep | steering / value-based | q-learning | steering-heuristic | 2025 |
| 135 | zheng2025dynamic | steering / value-based | q-learning | steering-rules | 2025 |
| 136 | lei2026dynamic | steering / value-based | q-learning | steering-rules | 2025 |
| 140 | du2023knowledge | steering / value-based | q-learning | steering-heuristic | 2022 |
| 161 | chang2025reinforcement | steering / value-based | q-learning | steering-heuristic | 2024 |
| 204 | li2026deep | steering / value-based | q-learning | steering-heuristic | 2026 |
| 211 | zhang2024deep | steering / value-based | q-learning | steering-heuristic | 2024 |
| 226 | yang2026dynamic | steering / value-based | q-learning | steering-rules | 2026 |
| 249 | zhou2025deep | steering / value-based | q-learning | steering-heuristic | 2025 |
| 274 | fu2026digital | steering / value-based | q-learning | steering-rules | 2026 |
| 290 | chen2024learning | steering / value-based | q-learning | steering-heuristic | 2024 |
| 353 | zhang2026improving | steering / value-based | q-learning | steering-heuristic | 2026 |
| 393 | yang2025learning | steering / value-based | q-learning | steering-heuristic | 2025 |
| 447 | zhang2026dynamic | steering / value-based | q-learning | steering-rules | 2026 |
| 465 | jiang2026learning | steering / value-based | q-learning | steering-heuristic | 2026 |
| 477 | li2026dual | steering / value-based | q-learning | steering-heuristic | 2026 |
| 503 | zhao2026tri | steering / value-based | q-learning | steering-heuristic | 2026 |
| 555 | zhao2025iterative | steering / value-based | q-learning | steering-heuristic | 2025 |
| 565 | zhang2024learning | steering / value-based | q-learning | steering-heuristic | 2024 |
| 574 | fu2025multi | steering / value-based | q-learning | steering-heuristic | 2025 |
| 575 | yi2026graph | steering / value-based | q-learning | steering-rules | 2026 |
| 577 | destouet2026machine | steering / value-based | q-learning | steering-heuristic | 2025 |
| 606 | liang2026digital | steering / value-based | q-learning | steering-heuristic | 2026 |
| 12 | zhang2023deep | steering / policy-gradient | ppo | steering-rules | 2023 |
| 40 | mo2026adaptive | steering / policy-gradient | ppo | steering-rules | 2026 |
| 54 | vanstraaten2026deep | steering / policy-gradient | ppo | steering-heuristic | 2026 |
| 197 | qiao2026hierarchical | steering / policy-gradient | ppo | steering-rules | 2026 |
| 247 | shi2025production | steering / policy-gradient | ppo | steering-rules | 2025 |
| 291 | wang2025multia | steering / policy-gradient | ppo | steering-rules | 2025 |
| 357 | wang2026reinforcement | steering / policy-gradient | reinforce | steering-heuristic | 2026 |
| 399 | gu2024dynamic | steering / policy-gradient | ppo | steering-rules | 2024 |
| 572 | yixun2024adaptive | steering / policy-gradient | ppo | steering-rules | 2024 |
| 15 | gui2023dynamic | steering / actor-critic | ddpg-td3 | steering-rules | 2023 |
| 132 | wang2025multi | steering / actor-critic | ddpg-td3 | steering-rules | 2025 |
| 527 | liang2026heterogeneous | steering / actor-critic | a2c-a3c | steering-heuristic | 2026 |

