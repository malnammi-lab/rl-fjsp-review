# The core: the studies read in full

Written by `runners/core_selection.py` from `configs\core.toml`; do not edit, rerun the runner. The rule is the protocol's (Two tiers); the runner's docstring gives the readings it applies.

Core of 100 places; non-deep learners (tabular, non-neural) at most 10; step 2's minimum 3, falling as needed to 2, then 1; strata end-to-end 35, steering 35, role-not-stated 30. A shared title makes two records one study only when their first authors agree.

## Candidates

533 records in the map; 50 whose learner is not stated, not candidates; 483 candidates.

Counted once with another record: none.

Records sharing a title, kept apart since their first authors do not agree or cannot be compared: 108 and 292 (Wen Song; Wan-Ze Li).

| Stratum | Candidates | Deep | Non-deep |
| --- | ---: | ---: | ---: |
| end-to-end | 156 | 149 | 7 |
| steering | 180 | 103 | 77 |
| role-not-stated | 147 | 136 | 11 |

## Step 1: use beyond simulation

4 studies, each a claim confirmed by the person at `twin-or-hil`, `testbed-or-shadow`, `live-system`: 315, 588, 583, 18.

Left out by the cap on non-deep studies, to be named under question 5: none.

## Step 2: coverage

Minimum used: 3. 36 studies, in the order taken, each with the places it filled: 527 (16), 245 (13), 565 (11), 136 (10), 503 (9), 606 (8), 197 (7), 184 (6), 109 (5), 237 (5), 132 (5), 204 (4), 258 (3), 76 (3), 54 (3), 300 (3), 140 (2), 40 (2), 577 (2), 572 (2), 78 (1), 213 (1), 228 (1), 12 (1), 353 (1), 293 (1), 68 (1), 201 (1), 120 (1), 297 (1), 530 (1), 94 (1), 409 (1), 609 (1), 447 (1), 582 (1).

Coverage axes: `policy_role`, `coordination`, `learner_depth`, `deep_architecture`, `training_algorithm_family`, `hybridization`, `state_content`, `state_encoding`, `dynamic_events`, `objective`, `constraints`, `instances`, `domain`.

| Axis | Category | In the map | Candidates | Owed | After step 2 | In the core | Status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `policy_role` | `end-to-end` | 163 | 156 | 3 | 14 | 35 | met |
| `policy_role` | `steering-rules` | 60 | 59 | 3 | 4 | 12 | met |
| `policy_role` | `steering-heuristic` | 152 | 121 | 3 | 9 | 23 | met |
| `coordination` | `single-agent` | 410 | 366 | 3 | 27 | 71 | met |
| `coordination` | `multi-agent` | 120 | 114 | 3 | 13 | 29 | met |
| `coordination` | `hierarchical` | 37 | 36 | 3 | 6 | 9 | met |
| `learner_depth` | `deep` | 388 | 388 | 3 | 36 | 90 | met |
| `learner_depth` | `non-neural` | 0 | 0 | 0 | 0 | 0 | empty: no record of the map holds it |
| `learner_depth` | `tabular` | 95 | 95 | 3 | 4 | 10 | met |
| `deep_architecture` | `fully-connected` | 16 | 16 | 3 | 3 | 4 | met |
| `deep_architecture` | `convolutional` | 6 | 6 | 3 | 3 | 3 | met |
| `deep_architecture` | `recurrent` | 13 | 13 | 3 | 6 | 6 | met |
| `deep_architecture` | `graph-neural-network` | 145 | 145 | 3 | 12 | 42 | met |
| `deep_architecture` | `attention-transformer` | 52 | 52 | 3 | 9 | 17 | met |
| `deep_architecture` | `pointer-network` | 5 | 5 | 3 | 3 | 4 | met |
| `training_algorithm_family` | `value-based` | 218 | 218 | 3 | 10 | 34 | met |
| `training_algorithm_family` | `policy-gradient` | 122 | 121 | 3 | 16 | 30 | met |
| `training_algorithm_family` | `actor-critic` | 26 | 25 | 3 | 3 | 7 | met |
| `hybridization` | `none` | 338 | 325 | 3 | 25 | 69 | met |
| `hybridization` | `metaheuristic` | 179 | 145 | 3 | 10 | 26 | met |
| `hybridization` | `exact` | 3 | 2 | 2 | 2 | 2 | all its 2 candidates |
| `hybridization` | `other-learner` | 13 | 11 | 3 | 3 | 3 | met |
| `state_content` | `operations` | 123 | 121 | 3 | 13 | 33 | met |
| `state_content` | `jobs` | 39 | 36 | 3 | 5 | 10 | met |
| `state_content` | `machines` | 136 | 133 | 3 | 12 | 35 | met |
| `state_content` | `shop-aggregate` | 13 | 12 | 3 | 4 | 6 | met |
| `state_content` | `events` | 9 | 9 | 3 | 4 | 7 | met |
| `state_content` | `other-resources` | 28 | 28 | 3 | 3 | 8 | met |
| `state_content` | `search-state` | 16 | 16 | 3 | 4 | 6 | met |
| `state_encoding` | `discrete-states` | 95 | 95 | 3 | 4 | 10 | met |
| `state_encoding` | `feature-vector` | 42 | 42 | 3 | 6 | 13 | met |
| `state_encoding` | `sequence` | 3 | 3 | 3 | 3 | 3 | met |
| `state_encoding` | `set` | 0 | 0 | 0 | 0 | 0 | empty: no record of the map holds it |
| `state_encoding` | `matrix` | 6 | 6 | 3 | 3 | 3 | met |
| `state_encoding` | `disjunctive-graph` | 44 | 43 | 3 | 3 | 14 | met |
| `state_encoding` | `heterogeneous-graph` | 97 | 95 | 3 | 7 | 23 | met |
| `state_encoding` | `other-graph` | 6 | 6 | 3 | 3 | 3 | met |
| `state_encoding` | `text` | 0 | 0 | 0 | 0 | 0 | empty: no record of the map holds it |
| `dynamic_events` | `none` | 290 | 261 | 3 | 22 | 53 | met |
| `dynamic_events` | `job-arrivals` | 104 | 99 | 3 | 8 | 20 | met |
| `dynamic_events` | `machine-breakdowns` | 65 | 61 | 3 | 6 | 14 | met |
| `dynamic_events` | `uncertain-processing-times` | 33 | 28 | 3 | 4 | 9 | met |
| `objective` | `makespan` | 278 | 251 | 3 | 21 | 50 | met |
| `objective` | `tardiness` | 76 | 69 | 3 | 4 | 11 | met |
| `objective` | `flow-time` | 13 | 10 | 3 | 3 | 3 | met |
| `objective` | `workload` | 35 | 28 | 3 | 3 | 7 | met |
| `objective` | `utilization` | 26 | 25 | 3 | 4 | 4 | met |
| `objective` | `energy` | 130 | 111 | 3 | 7 | 24 | met |
| `objective` | `cost` | 23 | 21 | 3 | 4 | 6 | met |
| `objective` | `robustness` | 18 | 15 | 3 | 4 | 5 | met |
| `constraints` | `none` | 287 | 265 | 3 | 22 | 48 | met |
| `constraints` | `transport` | 98 | 86 | 3 | 5 | 28 | met |
| `constraints` | `setup-times` | 21 | 16 | 3 | 3 | 4 | met |
| `constraints` | `workers` | 47 | 44 | 3 | 4 | 8 | met |
| `constraints` | `energy` | 21 | 20 | 3 | 3 | 3 | met |
| `constraints` | `distributed` | 62 | 56 | 3 | 3 | 12 | met |
| `instances` | `public-benchmark` | 186 | 167 | 3 | 16 | 41 | met |
| `instances` | `generated` | 130 | 124 | 3 | 13 | 33 | met |
| `instances` | `industrial` | 42 | 36 | 3 | 3 | 4 | met |
| `domain` | `manufacturing` | 529 | 479 | 3 | 38 | 98 | met |
| `domain` | `computing-networks` | 3 | 2 | 2 | 2 | 2 | all its 2 candidates |

## Step 3: the places left

Non-deep places the cap left for step 3: 6.

| Stratum | Places | Its share | Steps 1 and 2 | Step 3 | Band 1 | Band 2 | Last place in band |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| end-to-end | 35 | 35 | 14 | 21 | 21 | 0 | 1 |
| steering | 35 | 35 | 13 | 22 | 22 | 0 | 1 |
| role-not-stated | 30 | 30 | 13 | 17 | 17 | 0 | 1 |

Years of end-to-end, band 1 (candidates not yet chosen, places): 2022 7, 2, 2023 4, 1, 2024 10, 3, 2025 28, 8, 2026 23, 7.

Years of steering, band 1 (candidates not yet chosen, places): 2019 1, 0, 2020 2, 0, 2021 4, 1, 2022 4, 1, 2023 8, 2, 2024 22, 4, 2025 40, 8, 2026 28, 6.

Years of role-not-stated, band 1 (candidates not yet chosen, places): 2022 4, 1, 2023 2, 1, 2024 12, 4, 2025 22, 6, 2026 17, 5.

Non-deep studies left out of step 3 by the cap, each with the deep study in its place: 376 by 135; 86 by 41; 463 by 575; 384 by 106.

## Ties settled by the record number

Ties at steps 2 and 3 go to the better venue, then the better citation standing, then the lower record number (protocol, Two tiers). The record number is the order in which OpenAlex returned the works to the search, which asked for no sort; it says nothing of a study's method. Band 1 is a single venue tier, and within a year equal citations give equal standing, so within a year of band 1 a tie on citations falls to the record number. To count where it decided, the rule's steps were applied again with every record number mirrored, the highest first, which turns each such tie inside them the other way and changes nothing else (the de-duplication of the candidates, which also prefers the lower number, is not mirrored; its groups are listed under Candidates). The count is of the places that change when the order is reversed: in a tie of k candidates for j places, the record number decides the lesser of j and k - j.

Reversing the order changes 8 of the core's 100 studies (step 1: 0, step 2: 4, step 3: 4); the mirrored core takes as many others in their place.

A difference can also follow from an earlier tie rather than be one: a different study taken at step 2 changes the categories still owed and the places left to each stratum. For a study of step 3 the last column gives the tie it was part of, the candidates sharing its stratum, band, year, citations, tier and standing, in the core and left out (deep ones only where it took a place the cap freed); one with none differs for that earlier reason. A study of step 2 is taken for the places it fills, so its partners in a tie are the candidates that would have filled as many, which this table does not list.

| Record | Step | Stratum | Band | Year | Cited | Step 3: tied with it |
| ---: | --- | --- | --- | --- | ---: | --- |
| 503 | 2 | steering | 1 | 2026 | 3 | not listed (step 2) |
| 237 | 2 | end-to-end | 1 | 2026 | 0 | not listed (step 2) |
| 300 | 2 | end-to-end | 2 | 2026 | 0 | not listed (step 2) |
| 40 | 2 | steering | 1 | 2026 | 0 | not listed (step 2) |
| 255 | 3 | end-to-end | 1 | 2026 | 1 | in the core: 262, 383, 504; left out: none |
| 106 | 3 | steering | 1 | 2026 | 0 | in the core: 40, 120; left out: 112, 142, 143, 251, 442, 450, 467, 502, 544, 564, 578 |
| 52 | 3 | role-not-stated | 1 | 2025 | 12 | in the core: 133; left out: 195 |
| 127 | 3 | role-not-stated | 1 | 2026 | 4 | in the core: 213; left out: 266 |

In the mirrored core instead: 431 (step 2), 463 (step 2), 82 (step 3), 256 (step 3), 71 (step 3), 578 (step 3), 195 (step 3), 266 (step 3).

## Flow counts

| Count | Records |
| --- | ---: |
| Records in the map | 533 |
| Learner not stated: not candidates | 50 |
| Candidates | 483 |
| Counted once with another record | 0 |
| Candidates, each study once | 483 |
| Step 1: use beyond simulation | 4 |
| Step 1: left out by the cap on non-deep studies | 0 |
| Step 2: coverage (minimum 3) | 36 |
| Step 3: end-to-end, band 1 | 21 |
| Step 3: end-to-end, band 2 | 0 |
| Step 3: steering, band 1 | 22 |
| Step 3: steering, band 2 | 0 |
| Step 3: role-not-stated, band 1 | 17 |
| Step 3: role-not-stated, band 2 | 0 |
| Step 3: non-deep studies left out by the cap | 4 |
| The core | 100 |
| Non-deep studies in the core | 10 |

## The core against the rest of the map

Records holding each code, as a share of the core (100) and of the rest of the map (433); a record can hold several codes of a list axis. All codes of every axis are in `results/core/core-vs-map.csv`.

| Axis | Code | Core | Core % | Rest | Rest % |
| --- | --- | ---: | ---: | ---: | ---: |
| `policy_role` | end-to-end | 35 | 35.0 | 128 | 29.6 |
| `policy_role` | steering-rules | 12 | 12.0 | 48 | 11.1 |
| `policy_role` | steering-heuristic | 23 | 23.0 | 129 | 29.8 |
| `policy_role` | not-stated | 30 | 30.0 | 128 | 29.6 |
| `coordination` | single-agent | 71 | 71.0 | 339 | 78.3 |
| `coordination` | multi-agent | 29 | 29.0 | 91 | 21.0 |
| `coordination` | hierarchical | 9 | 9.0 | 28 | 6.5 |
| `scheduling_action` | operation | 3 | 3.0 | 10 | 2.3 |
| `scheduling_action` | machine | 0 | 0.0 | 2 | 0.5 |
| `scheduling_action` | operation-machine-pair | 23 | 23.0 | 70 | 16.2 |
| `scheduling_action` | schedule-change | 1 | 1.0 | 1 | 0.2 |
| `scheduling_action` | other | 0 | 0.0 | 2 | 0.5 |
| `scheduling_action` | not-applicable | 35 | 35.0 | 177 | 40.9 |
| `scheduling_action` | not-stated | 38 | 38.0 | 171 | 39.5 |
| `learner_depth` | deep | 90 | 90.0 | 298 | 68.8 |
| `learner_depth` | tabular | 10 | 10.0 | 85 | 19.6 |
| `learner_depth` | not-stated | 0 | 0.0 | 50 | 11.5 |
| `deep_architecture` | fully-connected | 4 | 4.0 | 12 | 2.8 |
| `deep_architecture` | convolutional | 3 | 3.0 | 3 | 0.7 |
| `deep_architecture` | recurrent | 6 | 6.0 | 7 | 1.6 |
| `deep_architecture` | graph-neural-network | 42 | 42.0 | 103 | 23.8 |
| `deep_architecture` | attention-transformer | 17 | 17.0 | 35 | 8.1 |
| `deep_architecture` | pointer-network | 4 | 4.0 | 1 | 0.2 |
| `deep_architecture` | other | 1 | 1.0 | 1 | 0.2 |
| `deep_architecture` | not-applicable | 10 | 10.0 | 85 | 19.6 |
| `deep_architecture` | not-stated | 34 | 34.0 | 217 | 50.1 |
| `training_algorithm_family` | value-based | 34 | 34.0 | 184 | 42.5 |
| `training_algorithm_family` | policy-gradient | 30 | 30.0 | 92 | 21.2 |
| `training_algorithm_family` | actor-critic | 7 | 7.0 | 19 | 4.4 |
| `training_algorithm_family` | other | 2 | 2.0 | 6 | 1.4 |
| `training_algorithm_family` | not-stated | 31 | 31.0 | 139 | 32.1 |
| `hybridization` | none | 69 | 69.0 | 269 | 62.1 |
| `hybridization` | metaheuristic | 26 | 26.0 | 153 | 35.3 |
| `hybridization` | exact | 2 | 2.0 | 1 | 0.2 |
| `hybridization` | other-learner | 3 | 3.0 | 10 | 2.3 |
| `state_content` | operations | 33 | 33.0 | 90 | 20.8 |
| `state_content` | jobs | 10 | 10.0 | 29 | 6.7 |
| `state_content` | machines | 35 | 35.0 | 101 | 23.3 |
| `state_content` | shop-aggregate | 6 | 6.0 | 7 | 1.6 |
| `state_content` | events | 7 | 7.0 | 2 | 0.5 |
| `state_content` | other-resources | 8 | 8.0 | 20 | 4.6 |
| `state_content` | search-state | 6 | 6.0 | 10 | 2.3 |
| `state_content` | not-stated | 52 | 52.0 | 311 | 71.8 |
| `state_encoding` | discrete-states | 10 | 10.0 | 85 | 19.6 |
| `state_encoding` | feature-vector | 13 | 13.0 | 29 | 6.7 |
| `state_encoding` | sequence | 3 | 3.0 | 0 | 0.0 |
| `state_encoding` | matrix | 3 | 3.0 | 3 | 0.7 |
| `state_encoding` | disjunctive-graph | 14 | 14.0 | 30 | 6.9 |
| `state_encoding` | heterogeneous-graph | 23 | 23.0 | 74 | 17.1 |
| `state_encoding` | other-graph | 3 | 3.0 | 3 | 0.7 |
| `state_encoding` | not-stated | 38 | 38.0 | 222 | 51.3 |
| `dynamic_events` | none | 53 | 53.0 | 237 | 54.7 |
| `dynamic_events` | job-arrivals | 20 | 20.0 | 84 | 19.4 |
| `dynamic_events` | machine-breakdowns | 14 | 14.0 | 51 | 11.8 |
| `dynamic_events` | uncertain-processing-times | 9 | 9.0 | 24 | 5.5 |
| `dynamic_events` | other | 9 | 9.0 | 23 | 5.3 |
| `dynamic_events` | not-stated | 12 | 12.0 | 66 | 15.2 |
| `objective` | makespan | 50 | 50.0 | 228 | 52.7 |
| `objective` | tardiness | 11 | 11.0 | 65 | 15.0 |
| `objective` | flow-time | 3 | 3.0 | 10 | 2.3 |
| `objective` | workload | 7 | 7.0 | 28 | 6.5 |
| `objective` | utilization | 4 | 4.0 | 22 | 5.1 |
| `objective` | energy | 24 | 24.0 | 106 | 24.5 |
| `objective` | cost | 6 | 6.0 | 17 | 3.9 |
| `objective` | robustness | 5 | 5.0 | 13 | 3.0 |
| `objective` | other | 5 | 5.0 | 21 | 4.8 |
| `objective` | not-stated | 36 | 36.0 | 123 | 28.4 |
| `constraints` | none | 48 | 48.0 | 239 | 55.2 |
| `constraints` | transport | 28 | 28.0 | 70 | 16.2 |
| `constraints` | setup-times | 4 | 4.0 | 17 | 3.9 |
| `constraints` | workers | 8 | 8.0 | 39 | 9.0 |
| `constraints` | energy | 3 | 3.0 | 18 | 4.2 |
| `constraints` | distributed | 12 | 12.0 | 50 | 11.5 |
| `constraints` | other | 9 | 9.0 | 44 | 10.2 |
| `constraints` | not-stated | 2 | 2.0 | 16 | 3.7 |
| `instances` | public-benchmark | 41 | 41.0 | 145 | 33.5 |
| `instances` | generated | 33 | 33.0 | 97 | 22.4 |
| `instances` | industrial | 4 | 4.0 | 38 | 8.8 |
| `instances` | not-stated | 42 | 42.0 | 209 | 48.3 |
| `domain` | manufacturing | 98 | 98.0 | 431 | 99.5 |
| `domain` | computing-networks | 2 | 2.0 | 1 | 0.2 |
| `domain` | other | 0 | 0.0 | 2 | 0.5 |
| `readiness_claim` | none | 91 | 91.0 | 395 | 91.2 |
| `readiness_claim` | real-data | 5 | 5.0 | 37 | 8.5 |
| `readiness_claim` | twin-or-hil | 3 | 3.0 | 0 | 0.0 |
| `readiness_claim` | testbed-or-shadow | 1 | 1.0 | 1 | 0.2 |
| `venue_tier` | 1 | 91 | 91.0 | 210 | 48.5 |
| `venue_tier` | 2 | 6 | 6.0 | 89 | 20.6 |
| `venue_tier` | 3 | 0 | 0.0 | 14 | 3.2 |
| `venue_tier` | 4 | 3 | 3.0 | 120 | 27.7 |
| `venue_country` | United Kingdom | 40 | 40.0 | 119 | 27.5 |
| `venue_country` | Netherlands | 28 | 28.0 | 70 | 16.2 |
| `venue_country` | United States | 20 | 20.0 | 65 | 15.0 |
| `venue_country` | Switzerland | 7 | 7.0 | 49 | 11.3 |
| `venue_country` | Germany | 1 | 1.0 | 34 | 7.9 |
| `venue_country` | China | 0 | 0.0 | 5 | 1.2 |
| `venue_country` | Singapore | 0 | 0.0 | 4 | 0.9 |
| `venue_country` | Australia | 0 | 0.0 | 1 | 0.2 |
| `venue_country` | Austria | 1 | 1.0 | 0 | 0.0 |
| `venue_country` | Canada | 0 | 0.0 | 1 | 0.2 |
| `venue_country` | Slovenia | 0 | 0.0 | 1 | 0.2 |
| `venue_country` | Spain | 0 | 0.0 | 1 | 0.2 |
| `venue_country` | not in SJR | 3 | 3.0 | 83 | 19.2 |

## The core

| Record | Step | Stratum | Band | Year | Cited | Title |
| ---: | --- | --- | --- | --- | ---: | --- |
| 315 | 1 | end-to-end | 1 | 2026 | 0 | Document-driven masked scheduling for flexible job shops: From standardized semantics to twin-closed-loop deployment |
| 588 | 1 | end-to-end | 1 | 2026 | 0 | Digital twin-driven disturbance recognition and adaptive scheduling for discrete manufacturing workshops |
| 583 | 1 | role-not-stated | 1 | 2024 | 26 | Study on the application of single-agent and multi-agent reinforcement learning to dynamic scheduling in manufacturing environments with growing complexity: Case study on the synthesis of an industrial IoT Test Bed |
| 18 | 1 | role-not-stated | 2 | 2026 | 0 | A reptile-PPO-clip meta-learning framework for make-to-order-oriented flexible job shop scheduling |
| 527 | 2 | steering | 2 | 2026 | 0 | Heterogeneous Graph Neural Network-Guided Adaptive Large Neighborhood Search for Flexible Job Shop Scheduling in Panel Furniture Production |
| 245 | 2 | end-to-end | 1 | 2026 | 0 | Feature fusion-enhanced multi-agent reinforcement learning algorithm for human–robot collaborative flexible job shop scheduling |
| 565 | 2 | steering | 1 | 2024 | 99 | A learning-driven multi-objective cooperative artificial bee colony algorithm for distributed flexible job shop scheduling problems with preventive maintenance and transportation operations |
| 136 | 2 | steering | 1 | 2025 | 3 | Dynamic scheduling for distributed flexible job shop using deep reinforcement learning |
| 503 | 2 | steering | 1 | 2026 | 3 | A Tri-Stage Cooperative Optimization Algorithm With Q-Learning Mechanism for the Multiobjective Distributed Flexible Job Shop Scheduling With Worker Factors |
| 606 | 2 | role-not-stated | 1 | 2026 | 1 | Digital twin-enabled nested Q-learning for multi-layer production planning and inventory control |
| 197 | 2 | steering | 2 | 2026 | 0 | A Hierarchical Reinforcement Learning Approach with Multi-Dimensional State Feature Extraction for Energy-Aware Flexible Job Shop Scheduling |
| 184 | 2 | end-to-end | 1 | 2026 | 0 | Priority-Guided Action-Masked Proximal Policy Optimization for Dynamic Scheduling of Electric Power Material Verification Tasks Under Multi-Source Disturbances |
| 109 | 2 | end-to-end | 1 | 2025 | 13 | Graph-based deep reinforcement learning for dynamic scheduling of flexible job-shop considering worker fatigue and multi-skill factors |
| 237 | 2 | end-to-end | 1 | 2026 | 0 | Cross-attention multi-scale graph reinforcement learning for dynamic flexible job-shop scheduling under hybrid uncertainty |
| 132 | 2 | steering | 1 | 2025 | 4 | Multi-Objective Scheduling for Green Flexible Assembly Job-Shop System via Multi-Agent Deep Reinforcement Learning With Game Theory |
| 204 | 2 | steering | 1 | 2026 | 2 | A deep Q-network enhanced variable neighborhood search algorithm based on NSGA-II for the multi-AGV flexible job shop scheduling problem with battery constraint |
| 258 | 2 | end-to-end | 1 | 2025 | 11 | Schedule repair for flexible job shops under machine breakdowns by deep reinforcement learning |
| 76 | 2 | end-to-end | 2 | 2021 | 100 | A Deep Reinforcement Learning Based Solution for Flexible Job Shop Scheduling Problem |
| 54 | 2 | steering | 2 | 2026 | 0 | Deep Reinforcement Learning Based Genetic Framework for Flexible Job-Shop Scheduling Under Practical Constraints |
| 300 | 2 | end-to-end | 2 | 2026 | 0 | A Two-Layer Multi-Agent Deep Reinforcement Learning Framework for Flexible Job-Shop Scheduling with Multiple Batch-Processing Machines |
| 140 | 2 | steering | 1 | 2022 | 202 | Knowledge-Based Reinforcement Learning and Estimation of Distribution Algorithm for Flexible Job Shop Scheduling Problem |
| 40 | 2 | steering | 1 | 2026 | 0 | Adaptive scheduling for FJSPT: a two-stage deep reinforcement learning approach with scale-invariant action space |
| 577 | 2 | steering | 1 | 2025 | 6 | Machine learning-driven solutions for sustainable and dynamic flexible job shop scheduling under worker absences and renewable energy variability |
| 572 | 2 | role-not-stated | 2 | 2024 | 0 | An adaptive scheduling framework for dynamic scheduling problem with random job arrivals and cancellations |
| 78 | 2 | end-to-end | 1 | 2023 | 199 | Large-Scale Dynamic Scheduling for Flexible Job-Shop With Random Arrivals of New Jobs by Hierarchical Reinforcement Learning |
| 213 | 2 | role-not-stated | 1 | 2026 | 4 | Enhancing multi-agent deep reinforcement learning for flexible job-shop scheduling through constraint programming |
| 228 | 2 | role-not-stated | 1 | 2026 | 2 | Mamba-CrossAttention: Solving Flexible Job Shop Scheduling via sequence modeling and reinforcement learning |
| 12 | 2 | role-not-stated | 1 | 2023 | 143 | Deep reinforcement learning for dynamic flexible job shop scheduling problem considering variable processing times |
| 353 | 2 | steering | 1 | 2026 | 1 | Improving energy efficiency in flexible job-shop scheduling through photovoltaic storage integration: A Q-learning guided evolutionary approach |
| 293 | 2 | end-to-end | 1 | 2025 | 18 | Graph neural network and expert-guided deep reinforcement learning for solving flexible job-shop scheduling problem |
| 68 | 2 | role-not-stated | 1 | 2025 | 14 | Preference learning based deep reinforcement learning for flexible job shop scheduling problem |
| 201 | 2 | role-not-stated | 1 | 2025 | 11 | An Integrated Mathematical Programming and Reinforcement Learning Algorithm for the Flexible Job Shop Scheduling with Variable Lot-sizing |
| 120 | 2 | steering | 1 | 2026 | 0 | Hybrid discrete PSO with reinforcement learning for flexible job shop scheduling |
| 297 | 2 | end-to-end | 1 | 2025 | 8 | Multi-agent deep reinforcement learning for low-carbon flexible job shop scheduling with variable sublots |
| 530 | 2 | role-not-stated | 1 | 2022 | 31 | Self-Organizing Neural Scheduler for the Flexible Job Shop Problem With Periodic Maintenance and Mandatory Outsourcing Constraints |
| 94 | 2 | end-to-end | 1 | 2022 | 26 | Fair Virtual Network Function Mapping and Scheduling Using Proximal Policy Optimization |
| 409 | 2 | role-not-stated | 1 | 2025 | 1 | Robust Scheduling Based on Deep Reinforcement Learning for Flexible Job Shop With Machine Breakdown and New Job Arrival |
| 609 | 2 | role-not-stated | 1 | 2020 | 25 | Adaptive Service Function Chain Scheduling in Mobile Edge Computing via Deep Reinforcement Learning |
| 447 | 2 | role-not-stated | 2 | 2026 | 0 | Dynamic Node Entropy QMIX Algorithm for Flexible Job Shop Dynamic Scheduling Problem |
| 582 | 2 | end-to-end | 2 | 2021 | 11 | Encoder-Decoder Neural Network Architecture for solving Job Shop Scheduling Problems using Reinforcement Learning |
| 108 | 3 | end-to-end | 1 | 2022 | 522 | Flexible Job-Shop Scheduling via Graph Neural Network and Deep Reinforcement Learning |
| 24 | 3 | end-to-end | 1 | 2022 | 355 | A multi-action deep reinforcement learning framework for flexible Job-shop scheduling problem |
| 57 | 3 | end-to-end | 1 | 2023 | 183 | Flexible Job Shop Scheduling via Dual Attention Network-Based Reinforcement Learning |
| 77 | 3 | end-to-end | 1 | 2024 | 76 | A novel collaborative agent reinforcement learning framework based on an attention mechanism and disjunctive graph embedding for flexible job shop scheduling problem |
| 46 | 3 | end-to-end | 1 | 2024 | 70 | Flexible job shop scheduling via deep reinforcement learning with meta-path-based heterogeneous graph neural network |
| 66 | 3 | end-to-end | 1 | 2024 | 51 | End-to-End Multitarget Flexible Job Shop Scheduling With Deep Reinforcement Learning |
| 160 | 3 | end-to-end | 1 | 2025 | 28 | Dynamic scheduling for multi-objective flexible job shop via deep reinforcement learning |
| 32 | 3 | end-to-end | 1 | 2025 | 26 | Attention enhanced reinforcement learning for flexible job shop scheduling with transportation constraints |
| 336 | 3 | end-to-end | 1 | 2025 | 26 | A heterogeneous graph attention-enhanced deep reinforcement learning framework for flexible job shop scheduling problem with variable sublots |
| 158 | 3 | end-to-end | 1 | 2025 | 24 | Flexible Job Shop Scheduling Problem using graph neural networks and reinforcement learning |
| 103 | 3 | end-to-end | 1 | 2025 | 21 | A heuristic-assisted deep reinforcement learning algorithm for flexible job shop scheduling with transport constraints |
| 244 | 3 | end-to-end | 1 | 2025 | 19 | Uncertain Interruptibility Multiobjective Flexible Job Shop via Deep Reinforcement Learning Based on Heterogeneous Graph Self-Attention |
| 90 | 3 | end-to-end | 1 | 2025 | 16 | MAMHSAN: A multi-agent deep reinforcement learning framework based on multi-head self-attention network with heterogeneous graph embedding for flexible job shop scheduling |
| 265 | 3 | end-to-end | 1 | 2025 | 16 | A cooperative agent deep reinforcement learning framework for solving flexible job shop scheduling problem with automated guided vehicles |
| 157 | 3 | end-to-end | 1 | 2026 | 4 | Distributed Flexible Job Shop Scheduling With Heterogeneous Transportation Resources Constraints via Deep Reinforcement Learning and Graph Neural Network |
| 259 | 3 | end-to-end | 1 | 2026 | 3 | Transformer-based multi-agent reinforcement learning for flexible job shop scheduling with AGVs |
| 339 | 3 | end-to-end | 1 | 2026 | 2 | An end-to-end deep reinforcement learning method for dynamic flexible job shop scheduling problem considering multi-skilled worker constraints |
| 255 | 3 | end-to-end | 1 | 2026 | 1 | Preference-Guided Reinforcement Learning for Dynamic Green Flexible Assembly Job Shop Scheduling with Learning–Forgetting Effects |
| 262 | 3 | end-to-end | 1 | 2026 | 1 | A deep reinforcement learning method based on scale perception and heterogeneous graph neural network for flexible job shop scheduling |
| 383 | 3 | end-to-end | 1 | 2026 | 1 | Progressive curriculum learning with adaptive graph attention networks for flexible job shop scheduling problem |
| 504 | 3 | end-to-end | 1 | 2026 | 1 | Budget-scalable inference-time hybrid MCTS for enhancing DRL-based flexible job shop scheduling |
| 21 | 3 | steering | 1 | 2021 | 265 | Real-time data-driven dynamic scheduling for flexible job shop with insufficient transportation resources using hybrid deep Q network |
| 41 | 3 | steering | 1 | 2022 | 194 | A Reinforcement Learning Approach for Flexible Job Shop Scheduling Problem With Crane Transportation and Setup Times |
| 15 | 3 | steering | 1 | 2023 | 186 | Dynamic scheduling for flexible job shop using a deep reinforcement learning approach |
| 92 | 3 | steering | 1 | 2023 | 158 | Co-Evolution With Deep Reinforcement Learning for Energy-Aware Distributed Heterogeneous Flexible Job Shop Scheduling |
| 211 | 3 | steering | 1 | 2024 | 116 | Deep reinforcement learning-based memetic algorithm for energy-aware flexible job shop scheduling with multi-AGV |
| 290 | 3 | steering | 1 | 2024 | 104 | A Q -Learning based NSGA-II for dynamic flexible job shop scheduling with limited transportation resources |
| 72 | 3 | steering | 1 | 2024 | 92 | A Double Deep Q-Network framework for a flexible job shop scheduling problem with dynamic job arrivals and urgent job insertions |
| 161 | 3 | steering | 1 | 2024 | 77 | A reinforcement learning enhanced memetic algorithm for multi-objective flexible job shop scheduling toward Industry 5.0 |
| 393 | 3 | steering | 1 | 2025 | 50 | A Q-learning-based improved multi-objective genetic algorithm for solving distributed heterogeneous assembly flexible job shop scheduling problems with transfers |
| 191 | 3 | steering | 1 | 2025 | 43 | Co-Evolutionary NSGA-III with deep reinforcement learning for multi-objective distributed flexible job shop scheduling |
| 249 | 3 | steering | 1 | 2025 | 43 | Deep reinforcement learning-based memetic algorithm for solving dynamic distributed green flexible job shop scheduling problem with finite transportation resources |
| 555 | 3 | steering | 1 | 2025 | 40 | An Iterative Greedy Algorithm for Solving a Multiobjective Distributed Assembly Flexible Job Shop Scheduling Problem With Fuzzy Processing Time |
| 131 | 3 | steering | 1 | 2025 | 39 | A deep reinforcement learning assisted adaptive genetic algorithm for flexible job shop scheduling |
| 574 | 3 | steering | 1 | 2025 | 35 | Multi-Objective Integrated Energy-Efficient Scheduling of Distributed Flexible Job Shop and Vehicle Routing by Knowledge-and-Learning-Based Hyper-Heuristics |
| 135 | 3 | steering | 1 | 2025 | 24 | Dynamic scheduling for flexible job-shop with reconfigurable manufacturing cells considering dynamic job arrivals based on deep reinforcement learning |
| 130 | 3 | steering | 1 | 2025 | 31 | Deep reinforcement learning for solving efficient and energy-saving flexible job shop scheduling problem with multi-AGV |
| 465 | 3 | steering | 1 | 2026 | 7 | A Q-learning-driven evolutionary algorithm for energy-aware flexible job shop scheduling with preventive maintenance and finite AGVs |
| 226 | 3 | steering | 1 | 2026 | 3 | Dynamic flexible job shop co-scheduling optimization based on graph neural network and deep reinforcement learning |
| 357 | 3 | steering | 1 | 2026 | 3 | A reinforcement learning framework based on graph embedding mechanism for fuzzy flexible job-shop scheduling problem |
| 477 | 3 | steering | 1 | 2026 | 3 | A dual-population memetic algorithm based on a producer-consumer paradigm for energy-aware dynamic flexible job shop scheduling with AGVs |
| 575 | 3 | steering | 1 | 2026 | 1 | A graph-based Q-network with expert-rule enhancement for integrated scheduling and maintenance optimization |
| 106 | 3 | steering | 1 | 2026 | 0 | A predictive-reactive double deep Q-network model for real-time flexible job shop scheduling problem under uncertainties |
| 101 | 3 | role-not-stated | 1 | 2022 | 117 | Multi-agent reinforcement learning based on graph convolutional network for flexible job shop scheduling |
| 1 | 3 | role-not-stated | 1 | 2023 | 76 | Research on flexible job shop scheduling problem with AGV using double DQN |
| 65 | 3 | role-not-stated | 1 | 2024 | 50 | Two-stage double deep Q-network algorithm considering external non-dominant set for multi-objective dynamic flexible job shop scheduling problems |
| 399 | 3 | role-not-stated | 1 | 2024 | 44 | Dynamic scheduling mechanism for intelligent workshop with deep reinforcement learning method based on multi-agent system architecture |
| 214 | 3 | role-not-stated | 1 | 2024 | 35 | Fast Pareto set approximation for multi-objective flexible job shop scheduling via parallel preference-conditioned graph reinforcement learning |
| 354 | 3 | role-not-stated | 1 | 2024 | 31 | A deep reinforcement learning method based on a multiexpert graph neural network for flexible job shop scheduling |
| 291 | 3 | role-not-stated | 1 | 2025 | 40 | Multi-agent deep reinforcement learning-based approach for dynamic flexible assembly job shop scheduling with uncertain processing and transport times |
| 247 | 3 | role-not-stated | 1 | 2025 | 29 | Production-logistics collaborative scheduling in dynamic flexible job shops using nested-hierarchical deep reinforcement learning |
| 350 | 3 | role-not-stated | 1 | 2025 | 22 | Meta-relation-based heterogeneous graph neural network with deep reinforcement learning for flexible job shop scheduling |
| 469 | 3 | role-not-stated | 1 | 2025 | 14 | Multi-agent cooperative multi-network group framework for energy-efficient distributed fuzzy flexible job shop scheduling problem |
| 52 | 3 | role-not-stated | 1 | 2025 | 12 | Multi-Agent Reinforcement Learning for Distributed Flexible Job Shop Scheduling With Random Job Arrival |
| 133 | 3 | role-not-stated | 1 | 2025 | 12 | Optimizing the flexible job shop scheduling problem via deep reinforcement learning with mean multichannel graph attention |
| 437 | 3 | role-not-stated | 1 | 2026 | 22 | A Heterogeneous Graph Reinforcement Learning Framework With Question-Aware Neighborhood Aggregation and Interoption Prompt Attention for Dynamic Flexible Job Shop Scheduling Problem |
| 216 | 3 | role-not-stated | 1 | 2026 | 10 | Multi-relational graph reinforcement learning for dynamic flexible job-shop scheduling under machine breakdowns |
| 274 | 3 | role-not-stated | 1 | 2026 | 7 | Digital-twin-based reinforcement learning method for flexible assembly job-shop scheduling with dynamic material kitting |
| 8 | 3 | role-not-stated | 1 | 2026 | 6 | HGA-MPPO: A unified heterogeneous graph attention and multi-policy PPO framework for AGV-assisted flexible job shop scheduling |
| 127 | 3 | role-not-stated | 1 | 2026 | 4 | Dynamic scheduling of flexible job-shop considering automatic guided vehicle transportation via deep reinforcement learning |

Lock: the core is the one locked in `results/core/core-lock.json`.
