# A person's check of six questions on the fifth

Written by `runners/core_human_check.py` from `configs/core-human-check.toml`; do not edit, rerun the runner. The person's file `datasets/core-human-check.csv` (SHA-256 0ef4ec1c4a2817d12f2190ebec2619e63bc39dd2f27a1d5c9afc6be7fab0d6ca), coded by Osamah H. Hussein, against the coding agent's answers (`datasets/coded-studies.csv`, the authors' corrections laid over them), reduced as the protocol states (Amendments: coding and checking the core). Kappa is left blank where either side gives a single code.

## Agreement

| Question | Studies | Agree | Share (%) | Kappa |
| --- | ---: | ---: | ---: | ---: |
| role | 20 | 20 | 100.0 | 1.00 |
| algorithm | 20 | 19 | 95.0 | 0.92 |
| algorithm family | 20 | 19 | 95.0 | 0.92 |
| readiness | 20 | 9 | 45.0 | 0.16 |
| runs | 20 | 12 | 60.0 | 0.43 |
| training runs, by bin | 20 | 12 | 60.0 | 0.40 |
| baselines | 20 | 17 | 85.0 | 0.58 |
| transfer | 20 | 16 | 80.0 | 0.53 |

## Disagreements

| Record | Question | Person | Coding agent |
| ---: | --- | --- | --- |
| 132 | algorithm | q-learning | ddpg-td3 |
| 68 | readiness | L2 | L1 |
| 90 | readiness | L2 | L1 |
| 130 | readiness | L2 | L1 |
| 132 | readiness | L2 | L1 |
| 133 | readiness | L2 | L1 |
| 157 | readiness | L2 | L1 |
| 226 | readiness | L2 | L1 |
| 237 | readiness | L2 | L1 |
| 290 | readiness | L2 | L1 |
| 383 | readiness | L2 | L1 |
| 447 | readiness | L2 | L1 |
| 24 | runs | not-reported | 1 |
| 46 | runs | not-reported | 1 |
| 65 | runs | not-reported | 1 |
| 72 | runs | not-reported | 1 |
| 132 | runs | not-reported | 10 |
| 383 | runs | not-reported | 1 |
| 527 | runs | not-reported | 1 |
| 588 | runs | not-reported | 1 |
| 24 | baselines | yes | no |
| 130 | baselines | yes | no |
| 132 | baselines | yes | no |
| 65 | transfer | no | yes |
| 68 | transfer | no | yes |
| 132 | transfer | yes | no |
| 447 | transfer | no | yes |
