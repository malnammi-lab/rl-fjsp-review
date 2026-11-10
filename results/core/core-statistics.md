# The map, the candidates and the core: counts

Written by `runners/core_statistics.py` from `configs\core.toml`; do not edit, rerun the runner.

Three sets, each row with its count and its share of the set's own records: the map, every included record (533); the candidates, the map's records whose learner is stated, each study once, from which the core is drawn (483); and the core, the studies read in full (100), the core locked in `results/core/core-lock.json`. The three tables have the same rows. Years and citations are the records' at the search snapshot (`datasets/references.json`). On a list axis a record counts under each code it holds, so the shares of one axis can add up to more than 100. The venue's country is the one SJR gives it (`datasets/venue-bands.csv`); `not in SJR` is a venue SJR does not list, or no venue. The codes of `policy_role` are given again over the set's records that state one, their share stating none being the axis's own `not-stated` row (protocol, Synthesis).

## The map (533 records)

Citations at the snapshot: median 3.0, mean 22.4.

| Group | Item | Count | % |
| --- | --- | ---: | ---: |
| Year | 2011 | 1 | 0.2 |
|  | 2013 | 1 | 0.2 |
|  | 2016 | 1 | 0.2 |
|  | 2019 | 2 | 0.4 |
|  | 2020 | 5 | 0.9 |
|  | 2021 | 15 | 2.8 |
|  | 2022 | 40 | 7.5 |
|  | 2023 | 41 | 7.7 |
|  | 2024 | 97 | 18.2 |
|  | 2025 | 179 | 33.6 |
|  | 2026 | 151 | 28.3 |
| `policy_role` | end-to-end | 163 | 30.6 |
|  | steering-rules | 60 | 11.3 |
|  | steering-heuristic | 152 | 28.5 |
|  | not-stated | 158 | 29.6 |
| `policy_role`, of the records that state one | end-to-end | 163 | 43.5 |
|  | steering-rules | 60 | 16.0 |
|  | steering-heuristic | 152 | 40.5 |
| `coordination` | single-agent | 410 | 76.9 |
|  | multi-agent | 120 | 22.5 |
|  | hierarchical | 37 | 6.9 |
|  | not-stated | 0 | 0.0 |
| `scheduling_action` | operation | 13 | 2.4 |
|  | machine | 2 | 0.4 |
|  | operation-machine-pair | 93 | 17.4 |
|  | whole-schedule | 0 | 0.0 |
|  | schedule-change | 2 | 0.4 |
|  | other | 2 | 0.4 |
|  | not-applicable | 212 | 39.8 |
|  | not-stated | 209 | 39.2 |
| `learner_depth` | deep | 388 | 72.8 |
|  | non-neural | 0 | 0.0 |
|  | tabular | 95 | 17.8 |
|  | not-stated | 50 | 9.4 |
| `deep_architecture` | fully-connected | 16 | 3.0 |
|  | convolutional | 6 | 1.1 |
|  | recurrent | 13 | 2.4 |
|  | graph-neural-network | 145 | 27.2 |
|  | attention-transformer | 52 | 9.8 |
|  | pointer-network | 5 | 0.9 |
|  | other | 2 | 0.4 |
|  | not-applicable | 95 | 17.8 |
|  | not-stated | 251 | 47.1 |
| `training_algorithm_family` | value-based | 218 | 40.9 |
|  | policy-gradient | 122 | 22.9 |
|  | actor-critic | 26 | 4.9 |
|  | other | 8 | 1.5 |
|  | not-stated | 170 | 31.9 |
| `hybridization` | none | 338 | 63.4 |
|  | metaheuristic | 179 | 33.6 |
|  | exact | 3 | 0.6 |
|  | other-learner | 13 | 2.4 |
|  | not-stated | 0 | 0.0 |
| `state_content` | operations | 123 | 23.1 |
|  | jobs | 39 | 7.3 |
|  | machines | 136 | 25.5 |
|  | shop-aggregate | 13 | 2.4 |
|  | events | 9 | 1.7 |
|  | other-resources | 28 | 5.3 |
|  | search-state | 16 | 3.0 |
|  | other | 0 | 0.0 |
|  | not-stated | 363 | 68.1 |
| `state_encoding` | discrete-states | 95 | 17.8 |
|  | feature-vector | 42 | 7.9 |
|  | sequence | 3 | 0.6 |
|  | set | 0 | 0.0 |
|  | matrix | 6 | 1.1 |
|  | disjunctive-graph | 44 | 8.3 |
|  | heterogeneous-graph | 97 | 18.2 |
|  | other-graph | 6 | 1.1 |
|  | text | 0 | 0.0 |
|  | other | 0 | 0.0 |
|  | not-stated | 260 | 48.8 |
| `dynamic_events` | none | 290 | 54.4 |
|  | job-arrivals | 104 | 19.5 |
|  | machine-breakdowns | 65 | 12.2 |
|  | uncertain-processing-times | 33 | 6.2 |
|  | other | 32 | 6.0 |
|  | not-stated | 78 | 14.6 |
| `objective` | makespan | 278 | 52.2 |
|  | tardiness | 76 | 14.3 |
|  | flow-time | 13 | 2.4 |
|  | workload | 35 | 6.6 |
|  | utilization | 26 | 4.9 |
|  | energy | 130 | 24.4 |
|  | cost | 23 | 4.3 |
|  | robustness | 18 | 3.4 |
|  | other | 26 | 4.9 |
|  | not-stated | 159 | 29.8 |
| `constraints` | none | 287 | 53.8 |
|  | transport | 98 | 18.4 |
|  | setup-times | 21 | 3.9 |
|  | workers | 47 | 8.8 |
|  | energy | 21 | 3.9 |
|  | distributed | 62 | 11.6 |
|  | other | 53 | 9.9 |
|  | not-stated | 18 | 3.4 |
| `instances` | public-benchmark | 186 | 34.9 |
|  | generated | 130 | 24.4 |
|  | industrial | 42 | 7.9 |
|  | not-stated | 251 | 47.1 |
| `domain` | manufacturing | 529 | 99.2 |
|  | computing-networks | 3 | 0.6 |
|  | other | 2 | 0.4 |
|  | not-stated | 0 | 0.0 |
| `readiness_claim` | none | 486 | 91.2 |
|  | real-data | 42 | 7.9 |
|  | twin-or-hil | 3 | 0.6 |
|  | testbed-or-shadow | 2 | 0.4 |
|  | live-system | 0 | 0.0 |
|  | not-stated | 0 | 0.0 |
| Citations | 0 | 163 | 30.6 |
|  | 1 to 4 | 128 | 24.0 |
|  | 5 to 9 | 55 | 10.3 |
|  | 10 to 24 | 77 | 14.4 |
|  | 25 to 49 | 57 | 10.7 |
|  | 50 to 99 | 19 | 3.6 |
|  | 100 or more | 34 | 6.4 |
| Venue country | United Kingdom | 159 | 29.8 |
|  | Netherlands | 98 | 18.4 |
|  | United States | 85 | 15.9 |
|  | Switzerland | 56 | 10.5 |
|  | Germany | 35 | 6.6 |
|  | China | 5 | 0.9 |
|  | Singapore | 4 | 0.8 |
|  | Australia | 1 | 0.2 |
|  | Austria | 1 | 0.2 |
|  | Canada | 1 | 0.2 |
|  | Slovenia | 1 | 0.2 |
|  | Spain | 1 | 0.2 |
|  | not in SJR | 86 | 16.1 |

## The candidates (483 records)

Citations at the snapshot: median 3.0, mean 22.3.

| Group | Item | Count | % |
| --- | --- | ---: | ---: |
| Year | 2011 | 0 | 0.0 |
|  | 2013 | 1 | 0.2 |
|  | 2016 | 1 | 0.2 |
|  | 2019 | 2 | 0.4 |
|  | 2020 | 4 | 0.8 |
|  | 2021 | 14 | 2.9 |
|  | 2022 | 33 | 6.8 |
|  | 2023 | 38 | 7.9 |
|  | 2024 | 90 | 18.6 |
|  | 2025 | 157 | 32.5 |
|  | 2026 | 143 | 29.6 |
| `policy_role` | end-to-end | 156 | 32.3 |
|  | steering-rules | 59 | 12.2 |
|  | steering-heuristic | 121 | 25.1 |
|  | not-stated | 147 | 30.4 |
| `policy_role`, of the records that state one | end-to-end | 156 | 46.4 |
|  | steering-rules | 59 | 17.6 |
|  | steering-heuristic | 121 | 36.0 |
| `coordination` | single-agent | 366 | 75.8 |
|  | multi-agent | 114 | 23.6 |
|  | hierarchical | 36 | 7.5 |
|  | not-stated | 0 | 0.0 |
| `scheduling_action` | operation | 12 | 2.5 |
|  | machine | 2 | 0.4 |
|  | operation-machine-pair | 89 | 18.4 |
|  | whole-schedule | 0 | 0.0 |
|  | schedule-change | 2 | 0.4 |
|  | other | 2 | 0.4 |
|  | not-applicable | 180 | 37.3 |
|  | not-stated | 196 | 40.6 |
| `learner_depth` | deep | 388 | 80.3 |
|  | non-neural | 0 | 0.0 |
|  | tabular | 95 | 19.7 |
|  | not-stated | 0 | 0.0 |
| `deep_architecture` | fully-connected | 16 | 3.3 |
|  | convolutional | 6 | 1.2 |
|  | recurrent | 13 | 2.7 |
|  | graph-neural-network | 145 | 30.0 |
|  | attention-transformer | 52 | 10.8 |
|  | pointer-network | 5 | 1.0 |
|  | other | 2 | 0.4 |
|  | not-applicable | 95 | 19.7 |
|  | not-stated | 201 | 41.6 |
| `training_algorithm_family` | value-based | 218 | 45.1 |
|  | policy-gradient | 121 | 25.1 |
|  | actor-critic | 25 | 5.2 |
|  | other | 5 | 1.0 |
|  | not-stated | 124 | 25.7 |
| `hybridization` | none | 325 | 67.3 |
|  | metaheuristic | 145 | 30.0 |
|  | exact | 2 | 0.4 |
|  | other-learner | 11 | 2.3 |
|  | not-stated | 0 | 0.0 |
| `state_content` | operations | 121 | 25.1 |
|  | jobs | 36 | 7.5 |
|  | machines | 133 | 27.5 |
|  | shop-aggregate | 12 | 2.5 |
|  | events | 9 | 1.9 |
|  | other-resources | 28 | 5.8 |
|  | search-state | 16 | 3.3 |
|  | other | 0 | 0.0 |
|  | not-stated | 317 | 65.6 |
| `state_encoding` | discrete-states | 95 | 19.7 |
|  | feature-vector | 42 | 8.7 |
|  | sequence | 3 | 0.6 |
|  | set | 0 | 0.0 |
|  | matrix | 6 | 1.2 |
|  | disjunctive-graph | 43 | 8.9 |
|  | heterogeneous-graph | 95 | 19.7 |
|  | other-graph | 6 | 1.2 |
|  | text | 0 | 0.0 |
|  | other | 0 | 0.0 |
|  | not-stated | 213 | 44.1 |
| `dynamic_events` | none | 261 | 54.0 |
|  | job-arrivals | 99 | 20.5 |
|  | machine-breakdowns | 61 | 12.6 |
|  | uncertain-processing-times | 28 | 5.8 |
|  | other | 29 | 6.0 |
|  | not-stated | 70 | 14.5 |
| `objective` | makespan | 251 | 52.0 |
|  | tardiness | 69 | 14.3 |
|  | flow-time | 10 | 2.1 |
|  | workload | 28 | 5.8 |
|  | utilization | 25 | 5.2 |
|  | energy | 111 | 23.0 |
|  | cost | 21 | 4.3 |
|  | robustness | 15 | 3.1 |
|  | other | 21 | 4.3 |
|  | not-stated | 145 | 30.0 |
| `constraints` | none | 265 | 54.9 |
|  | transport | 86 | 17.8 |
|  | setup-times | 16 | 3.3 |
|  | workers | 44 | 9.1 |
|  | energy | 20 | 4.1 |
|  | distributed | 56 | 11.6 |
|  | other | 47 | 9.7 |
|  | not-stated | 14 | 2.9 |
| `instances` | public-benchmark | 167 | 34.6 |
|  | generated | 124 | 25.7 |
|  | industrial | 36 | 7.5 |
|  | not-stated | 223 | 46.2 |
| `domain` | manufacturing | 479 | 99.2 |
|  | computing-networks | 2 | 0.4 |
|  | other | 2 | 0.4 |
|  | not-stated | 0 | 0.0 |
| `readiness_claim` | none | 442 | 91.5 |
|  | real-data | 37 | 7.7 |
|  | twin-or-hil | 3 | 0.6 |
|  | testbed-or-shadow | 1 | 0.2 |
|  | live-system | 0 | 0.0 |
|  | not-stated | 0 | 0.0 |
| Citations | 0 | 150 | 31.1 |
|  | 1 to 4 | 119 | 24.6 |
|  | 5 to 9 | 47 | 9.7 |
|  | 10 to 24 | 72 | 14.9 |
|  | 25 to 49 | 49 | 10.1 |
|  | 50 to 99 | 15 | 3.1 |
|  | 100 or more | 31 | 6.4 |
| Venue country | United Kingdom | 146 | 30.2 |
|  | Netherlands | 88 | 18.2 |
|  | United States | 73 | 15.1 |
|  | Switzerland | 54 | 11.2 |
|  | Germany | 32 | 6.6 |
|  | China | 5 | 1.0 |
|  | Singapore | 2 | 0.4 |
|  | Australia | 1 | 0.2 |
|  | Austria | 1 | 0.2 |
|  | Canada | 1 | 0.2 |
|  | Slovenia | 1 | 0.2 |
|  | Spain | 1 | 0.2 |
|  | not in SJR | 78 | 16.1 |

## The core (100 studies)

Citations at the snapshot: median 15.0, mean 44.6.

| Group | Item | Count | % |
| --- | --- | ---: | ---: |
| Year | 2011 | 0 | 0.0 |
|  | 2013 | 0 | 0.0 |
|  | 2016 | 0 | 0.0 |
|  | 2019 | 0 | 0.0 |
|  | 2020 | 1 | 1.0 |
|  | 2021 | 3 | 3.0 |
|  | 2022 | 7 | 7.0 |
|  | 2023 | 6 | 6.0 |
|  | 2024 | 14 | 14.0 |
|  | 2025 | 32 | 32.0 |
|  | 2026 | 37 | 37.0 |
| `policy_role` | end-to-end | 35 | 35.0 |
|  | steering-rules | 12 | 12.0 |
|  | steering-heuristic | 23 | 23.0 |
|  | not-stated | 30 | 30.0 |
| `policy_role`, of the records that state one | end-to-end | 35 | 50.0 |
|  | steering-rules | 12 | 17.1 |
|  | steering-heuristic | 23 | 32.9 |
| `coordination` | single-agent | 71 | 71.0 |
|  | multi-agent | 29 | 29.0 |
|  | hierarchical | 9 | 9.0 |
|  | not-stated | 0 | 0.0 |
| `scheduling_action` | operation | 3 | 3.0 |
|  | machine | 0 | 0.0 |
|  | operation-machine-pair | 23 | 23.0 |
|  | whole-schedule | 0 | 0.0 |
|  | schedule-change | 1 | 1.0 |
|  | other | 0 | 0.0 |
|  | not-applicable | 35 | 35.0 |
|  | not-stated | 38 | 38.0 |
| `learner_depth` | deep | 90 | 90.0 |
|  | non-neural | 0 | 0.0 |
|  | tabular | 10 | 10.0 |
|  | not-stated | 0 | 0.0 |
| `deep_architecture` | fully-connected | 4 | 4.0 |
|  | convolutional | 3 | 3.0 |
|  | recurrent | 6 | 6.0 |
|  | graph-neural-network | 42 | 42.0 |
|  | attention-transformer | 17 | 17.0 |
|  | pointer-network | 4 | 4.0 |
|  | other | 1 | 1.0 |
|  | not-applicable | 10 | 10.0 |
|  | not-stated | 34 | 34.0 |
| `training_algorithm_family` | value-based | 34 | 34.0 |
|  | policy-gradient | 30 | 30.0 |
|  | actor-critic | 7 | 7.0 |
|  | other | 2 | 2.0 |
|  | not-stated | 31 | 31.0 |
| `hybridization` | none | 69 | 69.0 |
|  | metaheuristic | 26 | 26.0 |
|  | exact | 2 | 2.0 |
|  | other-learner | 3 | 3.0 |
|  | not-stated | 0 | 0.0 |
| `state_content` | operations | 33 | 33.0 |
|  | jobs | 10 | 10.0 |
|  | machines | 35 | 35.0 |
|  | shop-aggregate | 6 | 6.0 |
|  | events | 7 | 7.0 |
|  | other-resources | 8 | 8.0 |
|  | search-state | 6 | 6.0 |
|  | other | 0 | 0.0 |
|  | not-stated | 52 | 52.0 |
| `state_encoding` | discrete-states | 10 | 10.0 |
|  | feature-vector | 13 | 13.0 |
|  | sequence | 3 | 3.0 |
|  | set | 0 | 0.0 |
|  | matrix | 3 | 3.0 |
|  | disjunctive-graph | 14 | 14.0 |
|  | heterogeneous-graph | 23 | 23.0 |
|  | other-graph | 3 | 3.0 |
|  | text | 0 | 0.0 |
|  | other | 0 | 0.0 |
|  | not-stated | 38 | 38.0 |
| `dynamic_events` | none | 53 | 53.0 |
|  | job-arrivals | 20 | 20.0 |
|  | machine-breakdowns | 14 | 14.0 |
|  | uncertain-processing-times | 9 | 9.0 |
|  | other | 9 | 9.0 |
|  | not-stated | 12 | 12.0 |
| `objective` | makespan | 50 | 50.0 |
|  | tardiness | 11 | 11.0 |
|  | flow-time | 3 | 3.0 |
|  | workload | 7 | 7.0 |
|  | utilization | 4 | 4.0 |
|  | energy | 24 | 24.0 |
|  | cost | 6 | 6.0 |
|  | robustness | 5 | 5.0 |
|  | other | 5 | 5.0 |
|  | not-stated | 36 | 36.0 |
| `constraints` | none | 48 | 48.0 |
|  | transport | 28 | 28.0 |
|  | setup-times | 4 | 4.0 |
|  | workers | 8 | 8.0 |
|  | energy | 3 | 3.0 |
|  | distributed | 12 | 12.0 |
|  | other | 9 | 9.0 |
|  | not-stated | 2 | 2.0 |
| `instances` | public-benchmark | 41 | 41.0 |
|  | generated | 33 | 33.0 |
|  | industrial | 4 | 4.0 |
|  | not-stated | 42 | 42.0 |
| `domain` | manufacturing | 98 | 98.0 |
|  | computing-networks | 2 | 2.0 |
|  | other | 0 | 0.0 |
|  | not-stated | 0 | 0.0 |
| `readiness_claim` | none | 91 | 91.0 |
|  | real-data | 5 | 5.0 |
|  | twin-or-hil | 3 | 3.0 |
|  | testbed-or-shadow | 1 | 1.0 |
|  | live-system | 0 | 0.0 |
|  | not-stated | 0 | 0.0 |
| Citations | 0 | 15 | 15.0 |
|  | 1 to 4 | 21 | 21.0 |
|  | 5 to 9 | 5 | 5.0 |
|  | 10 to 24 | 18 | 18.0 |
|  | 25 to 49 | 18 | 18.0 |
|  | 50 to 99 | 9 | 9.0 |
|  | 100 or more | 14 | 14.0 |
| Venue country | United Kingdom | 40 | 40.0 |
|  | Netherlands | 28 | 28.0 |
|  | United States | 20 | 20.0 |
|  | Switzerland | 7 | 7.0 |
|  | Germany | 1 | 1.0 |
|  | China | 0 | 0.0 |
|  | Singapore | 0 | 0.0 |
|  | Australia | 0 | 0.0 |
|  | Austria | 1 | 1.0 |
|  | Canada | 0 | 0.0 |
|  | Slovenia | 0 | 0.0 |
|  | Spain | 0 | 0.0 |
|  | not in SJR | 3 | 3.0 |
