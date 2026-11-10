# Venue bands: the order of the core's step 3

Written by `runners/venue_bands.py` from `configs\venues.toml`; do not edit, rerun the runner.

533 records of the map: 517 in 184 venues, and 16 without a venue. Lists: SJR 2025 and ICORE2026, downloaded 2026-10-18. Tiers, best first: 1, Q1 or A*; 2, Q2 or A; 3, Q3; 4, every other venue; a venue takes the first tier that its SJR best quartile or its confirmed ICORE rank reaches. Band 1 is the first tier, band 2 every other venue, and a record without one (protocol, Two tiers). An ICORE match counts once a person has confirmed it.

| Band | Records | Venues |
| --- | ---: | ---: |
| 1 | 301 | 68 |
| 2 | 232 | 116 |
| pending | 0 | 0 |

| Tier | Records | Venues |
| --- | ---: | ---: |
| 1 (Q1 or A*) | 301 | 68 |
| 2 (Q2 or A) | 95 | 34 |
| 3 (Q3) | 14 | 11 |
| 4 (the rest) | 123 | 71 |
| pending | 0 | 0 |

| Basis | Records | Venues |
| --- | ---: | ---: |
| SJR Q1 | 297 | 64 |
| SJR Q2 | 95 | 34 |
| no match | 69 | 56 |
| SJR no quartile | 28 | 9 |
| no venue | 16 | 0 |
| SJR Q3 | 14 | 11 |
| SJR Q4 | 10 | 6 |
| ICORE A* | 4 | 4 |

## Records by the venue's country

The country SJR gives each source, as its `Country` column reads; a record whose venue SJR does not list, or that has no venue, is counted as not in SJR. It describes the venues and decides nothing.

| Country | Records | In band 1 |
| --- | ---: | ---: |
| United Kingdom | 159 | 139 |
| Netherlands | 98 | 86 |
| United States | 85 | 58 |
| Switzerland | 56 | 13 |
| Germany | 35 | 1 |
| China | 5 | 2 |
| Singapore | 4 | 0 |
| Australia | 1 | 1 |
| Austria | 1 | 0 |
| Canada | 1 | 0 |
| Slovenia | 1 | 0 |
| Spain | 1 | 0 |
| not in SJR | 86 | 1 |

## ICORE matches proposed

13 venues, each shown with the ICORE conference ranked A* or A proposed as its own; a person answers on the sheet whether the two are the same conference.

| Venue | Records | ICORE conference | Rank | Similarity | Answer |
| --- | ---: | --- | --- | ---: | --- |
| Genetic and Evolutionary Computation Conference Companion (GECCO Companion) | 1 | Genetic and Evolutionary Computations (GECCO) | A | 0.75 | no |
| IEEE Congress on Evolutionary Computation (CEC) | 1 | Genetic and Evolutionary Computations (GECCO) | A | 0.67 | no |
| International Conference on Computer Engineering and Application (ICCEA) | 1 | Annual Computer Security Applications Conference (ACSAC) | A | 0.50 | no |
| International Conference on Computer Supported Cooperative Work in Design (CSCWD) | 3 | ACM Conference on Computer Supported Cooperative Work (CSCW) | A | 0.80 | no |
| International Conference on Computer and Communications (ICCC) | 1 | IEEE International Conference on Computer Communications (INFOCOM) | A* | 1.00 | no |
| International Conference on Machine Learning and Computer Application (ICMLCA) | 1 | International Conference on Machine Learning (ICML) | A* | 0.50 | no |
| International Conference on Network Communication and Information Security (ICNCIS) | 1 | Asia Conference on Information, Computer and Communications Security (AsiaCCS) | A | 0.50 | no |
| International Joint Conference on Artificial Intelligence | 1 | International Joint Conference on Artificial Intelligence (IJCAI) | A* | 1.00 | yes |
| International Joint Symposium on Artificial Intelligence and Natural Language Processing (iSAI-NLP) | 1 | International Joint Conference on Artificial Intelligence (IJCAI) | A* | 0.50 | no |
| Proceedings - IEEE International Conference on Robotics and Automation/Proceedings | 1 | IEEE International Conference on Robotics and Automation (ICRA) | A* | 1.00 | yes |
| Proceedings of the AAAI Conference on Artificial Intelligence | 1 | National Conference of the American Association for Artificial Intelligence (AAAI) | A* | 0.40 | yes |
| Proceedings of the International Conference on Automated Planning and Scheduling | 1 | International Conference on Automated Planning and Scheduling (ICAPS) | A* | 1.00 | yes |
| Proceedings of the International Conference on Parallel Processing | 1 | IEEE International Parallel and Distributed Processing Symposium (was IPPS and SPDP) (IPDPS) | A | 0.67 | no |

## Venues with no match

56 venues, in band 2 and the last tier: no SJR source found by ISSN-L, and no confirmed ICORE match ranked A* or A. ICORE ranks below that are not looked up, so some of these are conferences ICORE lists at a lower rank.

| Venue | Type | ISSN-L | Records |
| --- | --- | --- | ---: |
| Asian Conference on Artificial Intelligence Technology (ACAIT) | conference | none | 1 |
| China Automation Congress (CAC) | conference | none | 5 |
| Chinese Control Conference (CCC) | conference | none | 2 |
| Chinese Control and Decision Conference (CCDC) | conference | none | 3 |
| DOAJ (DOAJ: Directory of Open Access Journals) | repository | none | 2 |
| Digital Twin | journal | 2752-5783 | 1 |
| Genetic and Evolutionary Computation Conference Companion (GECCO Companion) | conference | none | 1 |
| IEEE Advanced Information Management, Communicates, Electronic and Automation Control Conference (IMCEC) | conference | none | 1 |
| IEEE Conference on Industrial Electronics and Applications (ICIEA) | conference | none | 1 |
| IEEE Congress on Evolutionary Computation (CEC) | conference | none | 1 |
| IEEE International Conference on Cyber Technology in Automation, Control, and Intelligent Systems | conference | none | 1 |
| IEEE International Conference on Electrical, Automation and Computer Engineering (ICEACE) | conference | none | 1 |
| IEEE International Conference on Mechatronics and Automation (ICMA) | conference | none | 1 |
| IEEE International Conference on e-Business Engineering (ICEBE) | conference | none | 1 |
| IEEE Smart World Congress (SWC) | conference | none | 2 |
| IEEE Symposium Series on Computational Intelligence (SSCI) | conference | none | 1 |
| IEEE/ACS International Conference on Computer Systems and Applications (AICCSA) | conference | none | 1 |
| IISE Annual Conference & Expo | conference | none | 1 |
| Industrial Engineering and Innovation Management | journal | 2522-6924 | 1 |
| International Annual Conference on Complex Systems and Intelligent Science (CSIS-IAC) | conference | none | 1 |
| International Conference on Advanced Algorithms and Control Engineering (ICAACE) | conference | none | 1 |
| International Conference on Algorithms, High Performance Computing and Artificial Intelligence (AHPCAI) | conference | none | 1 |
| International Conference on Artificial Intelligence, Human-Computer Interaction and Robotics (AIHCIR) | conference | none | 3 |
| International Conference on Computational Science and Computational Intelligence (CSCI) | conference | none | 1 |
| International Conference on Computer Engineering and Application (ICCEA) | conference | none | 1 |
| International Conference on Computer Network, Electronic and Automation (ICCNEA) | conference | none | 1 |
| International Conference on Computer Supported Cooperative Work in Design (CSCWD) | conference | none | 3 |
| International Conference on Computer and Communications (ICCC) | conference | none | 1 |
| International Conference on Computer, Control and Robotics (ICCCR) | conference | none | 1 |
| International Conference on Control and Intelligent Robotics (ICCIR) | conference | none | 1 |
| International Conference on Control, Automation and Diagnosis (ICCAD) | conference | none | 1 |
| International Conference on Data-driven Optimization of Complex Systems (DOCS) | conference | none | 1 |
| International Conference on Electrical Engineering, Control and Robotics (EECR) | conference | none | 1 |
| International Conference on Electrical, Computer, Communications and Mechatronics Engineering (ICECCME) | conference | none | 1 |
| International Conference on Electronic Communication and Artificial Intelligence (ICECAI) | conference | none | 1 |
| International Conference on Electronic Technology and Information Science (ICETIS) | conference | none | 1 |
| International Conference on Intelligent Computing (ICIC) | conference | none | 1 |
| International Conference on Intelligent Computing and Information Systems (ICICIS) | conference | none | 1 |
| International Conference on Machine Learning and Computer Application (ICMLCA) | conference | none | 1 |
| International Conference on Machine Learning and Intelligent Systems Engineering (MLISE) | conference | none | 1 |
| International Conference on Network Communication and Information Security (ICNCIS) | conference | none | 1 |
| International Conference on New Trends in Computational Intelligence (NTCI) | conference | none | 1 |
| International Conference on Optimization and Applications (ICOA) | conference | none | 1 |
| International Joint Symposium on Artificial Intelligence and Natural Language Processing (iSAI-NLP) | conference | none | 1 |
| International Journal of Hybrid Information Technology | journal | 1738-9968 | 1 |
| International Seminar on Artificial Intelligence, Networking and Information Technology (AINIT) | conference | none | 1 |
| International Symposium on Sensors, Mechatronics, and Automation System (ISSMAS) | conference | none | 1 |
| Journal of Management and Engineering Integration | journal | 1939-7984 | 1 |
| Journal of Mechanical & Electrical Engineering | journal | none | 1 |
| Journal of applied artificial intelligence. | journal | 3008-1874 | 1 |
| Leeds Beckett Repository (Leeds Beckett University) | repository | none | 1 |
| Proceedings of the Annual Conference of the IEEE Industrial Electronics Society | conference | 1553-572X | 1 |
| Proceedings of the IEEE Conference on Decision & Control, including the Symposium on Adaptive Processes | conference | 0191-2216 | 1 |
| Proceedings of the International Conference on Parallel Processing | conference | 0190-3918 | 1 |
| Singapore Institute of Technology | repository | none | 1 |
| TU/e Research Portal | repository | none | 1 |

Records without a venue, in band 2: 9, 18, 110, 134, 138, 164, 218, 227, 248, 271, 285, 368, 449, 489, 554, 561.
