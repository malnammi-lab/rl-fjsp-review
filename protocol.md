# Review protocol

**Status.** Approved by Moayad Alnammi on 11 October 2026, before the search. Consolidated on 26
October 2026. The dated record of every change is in `protocol-history.md`.

**Roles.** The authors led the review from start to finish. They designed the questions, the
criteria, the coding scheme and the method, and made every decision. Three open-weight language
models screened the records and coded the map: Qwen3.8-27B, Gemma 4 26B A4B and
Muse Glimmer 30B. Qwen3.8-27B then coded the core's full texts, Muse Glimmer 30B judged that
coding, and the authors checked the models at each stage. Under the authors' direction,
Anthropic's AI assistant Claude drafted code and text to their specifications, refined their
writing and helped them work through options.

**Before this protocol.** The terms, the research questions, and the eligibility criteria were
drawn from domain expertise and from studies that preliminary searches found in an exploratory
scoping phase before the protocol. It drew on the authors' domain expertise and on studies that
preliminary searches found in an exploratory scoping phase before the protocol.

## Background

Reinforcement learning (RL) for the flexible job shop is published across manufacturing,
operations research and machine learning venues, under inconsistent terminology.

## Objective

To map how reinforcement learning, alone or combined with other methods, has been applied to the
flexible job shop. Any domain that schedules jobs on alternative machines counts. We ask how the
problem is turned into a learning problem and which architectures learn it. We also ask how the
methods are evaluated, how far they generalize, and how close they are to use in practice.

## Research questions

Ahmed Azab confirmed the five questions as stated here, in both forms. His
confirmation was recorded on 18 October 2026, before the core was selected.

1. **Approaches.** How has reinforcement learning been applied to the flexible job shop?
  - 1.1 In which role: does the learned policy make the scheduling decisions itself
   (end-to-end: at each decision it chooses an operation, a machine or an operation-machine
   pair, and its sequence of choices is the schedule), or does it steer another method
   that builds the schedule (steering, also called RL-assisted: it chooses or switches
   among predefined dispatching rules, or sets a parameter, an operator, a neighbourhood
   or an acceptance decision of a heuristic or a metaheuristic)? With a single agent,
   several agents, or a hierarchy of agents? The role follows the policy's action, not
   the study's name for it: a policy its authors call a learned dispatching rule, which
   picks the operation itself, is end-to-end.
  - 1.2 With which learning paradigm and algorithm: value-based, policy gradient or
  actor-critic, a hybrid with a metaheuristic, or another (offline, model-based, safe,
  meta-learning)?
  - 1.3 For which problem variants and domains: static or dynamic (job arrivals, machine
  breakdowns, uncertain processing times); which objectives (makespan, tardiness,
  utilisation, energy, several at once); which extra constraints (transport or automated
  guided vehicles, energy, setups, several factories); and in which application domain
  (manufacturing, or another, such as computing or networks)?
2. **Formulation and architecture.** How is the flexible job shop turned into a learning
  problem, and what learns it?
  - 2.1 How is the problem formulated for reinforcement learning (its Markov decision
  process): its state (what the state contains); its actions (choosing a dispatching
  rule, assigning an operation to a machine directly, or a hierarchical or joint
  action); the masking of invalid actions; its rewards and their timing; its decision
  points (event-driven or a fixed time step); and whether the shop is treated as fully
  or partially observed?
  - 2.2 Which model represents the policy or the value function: a table, a fully
  connected network, a convolutional or recurrent network, a graph neural network, an
  attention or Transformer encoder, a pointer network, or any other model; and how is
  the state encoded as the model's input (a feature vector, a matrix, a disjunctive or
  heterogeneous graph, a sequence)?
3. **Evaluation.** How are the methods evaluated?
  - 3.1 On which instances: named public benchmarks, generated instances or industrial
   data, and, for dynamic shops, with which job-arrival and breakdown processes?
  - 3.2 Against which baselines (dispatching rules, metaheuristics, exact methods, other
  learned policies), and with which metrics, among them solution quality, decision
  (inference) time, training cost, and performance as instance size grows, wherever a
  study reports them?
  - 3.3 Do the studies report results over several training runs (random seeds),
  including the spread across those runs, and ablations that isolate each component's
  contribution, and do they release code and data?
  - 3.4 Where studies make the same claim, for example that their learned policy
  outperforms a baseline (dispatching rules, a metaheuristic, an exact solver or another
  learned policy), that a graph or attention encoding generalises across shop sizes, or
  that an actor-critic method trains more stably, is the evidence behind the claim
  comparable across them: the same instances, baselines, metrics and time limits? We do
  not judge whether a claim is true, only whether the studies that make it tested it in
  comparable ways.
4. **Transfer.** When a trained policy is tested on instances unlike those it was trained
  on, how do they differ (for example, in size, flexibility, layout, processing times,
   dynamic events, objective or constraints, a move to another factory, a public benchmark,
   or real data), and how does the policy perform?
5. **Readiness.** What evidence of use beyond simulation do the studies contain, by
  readiness level, and what do they report on decision deadlines, imperfect data,
   interpretability and robustness? The levels are Ahmed Azab's:

  | Level | What the study did                                                |
  | ----- | ----------------------------------------------------------------- |
  | L1    | Simulation (the baseline)                                         |
  | L2    | Tested on a real factory's data, still offline                    |
  | L3    | Ran inside a digital twin, or with hardware in the loop           |
  | L4    | Ran on a physical testbed, or in shadow mode beside the live shop |
  | L5    | Ran inside a live manufacturing execution system                  |


The review's scope:


| Element      | Definition                                                                                                                                                                                                                                    |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Population   | Flexible job shop scheduling problems, static or dynamic, with their variants, in any application domain, named as such in the title or abstract                                                                                              |
| Intervention | Reinforcement learning as the paper's own method, named in the title or abstract (or by an algorithm or an adjacent term such as policy or Markov decision process), making the decisions end-to-end or steering another method (RL-assisted) |
| Comparison   | The baselines the studies themselves report                                                                                                                                                                                                   |
| Outcome      | Per question: the distribution of studies over role, algorithm and variant (over the map); their formulations and architectures, evaluation practice, transfer tests and readiness level (over the core)                                      |
| Context      | Any application domain (manufacturing, computing, networks and others), simulated or real; no year floor; English journal and conference papers indexed by OpenAlex                                                                           |




### The questions as the paper states them

1. How has reinforcement learning been applied to the flexible job shop: in which role
  (end-to-end, or steering another method), with which algorithms, and for which problem
   variants and domains?
2. How is the flexible job shop formulated as a reinforcement learning problem, and which
  models represent the policy or the value function, with the state encoded as their
   input?
3. How are the methods evaluated, and is the evidence behind recurring claims comparable
  across studies?
4. When trained policies are tested on instances unlike those they were trained on, how do
  the instances differ, and what performance do the studies report?
5. What evidence of use beyond simulation do the studies contain, and what do they report
  on decision deadlines, imperfect data, interpretability and robustness?



## Questions this review does not ask

- Which method is best. Improvement figures are recorded as claims, never pooled or ranked.
- Whether the field's claims hold under a common test. Question 3.4 reports their evidence.
- What would make a learned schedule trustworthy, as a norm. Question 5 reports the evidence.
- Other shop settings and the classical job shop. Non-learning methods appear only as baselines.
- Learning other than RL: supervised or imitation learning alone, and rules evolved by genetic
programming or written by a language model.



## Eligibility criteria (title and abstract)



### Include if all of these hold

1. The title or abstract names the flexible job shop, and the paper's own problem is one:
  jobs have their own routes through the machines, and at least some operations can be
   processed on more than one machine. The names are: flexible job shop (also written
   job-shop or jobshop, with any qualifier, such as fully or partially flexible, dynamic,
   distributed or multi-objective), flexible assembly job shop, flexible workshop, and the
   abbreviations FJS, FJSP, FJSSP, DFJSP, DFJSSP, MOFJSP, FJSPT and FAJSP. The list is
   closed, so that the query can run it: an abbreviation not listed counts only where the
   abstract also spells out a listed name. Any application domain counts: the machines may
   be machine tools, robots, processors, network nodes or other resources. Dynamic
   variants, variants with extra constraints and distributed flexible job shops are
   included (question 1.3).
2. The title or abstract names reinforcement learning, one of its algorithms or variants,
  or a term adjacent to it, and reinforcement learning is the paper's own method: a
   policy or value function learned from experience or reward makes the scheduling
   decisions, or steers another method (a heuristic, a metaheuristic, a choice among
   dispatching rules). The names are: reinforcement learning (with any qualifier, such as
   deep, multi-agent, hierarchical, inverse or offline); its algorithms, Q-learning,
   Q-network, deep Q-network (DQN), SARSA, REINFORCE, policy gradient, actor-critic
   (including A2C and A3C), proximal policy optimization (PPO), trust region policy
   optimization (TRPO), deep deterministic policy gradient (DDPG), twin delayed DDPG (TD3),
   soft actor-critic (SAC) and temporal difference learning; and the adjacent terms policy,
   Markov decision process (MDP), Markov or Markovian, and decision process. The list is
   closed, so that the query can run it. Tabular and deep, single- and multi-agent
   reinforcement learning all count, as do imitation used as pretraining for a
   reinforcement learning method, and a learned encoder inside a reinforcement learning
   agent.
3. The paper is a primary study that reports quantitative results on benchmark
  instances, generated instances or a described case.



### Exclude if any of these hold

Each reason begins with its label ("Exclusion 2:") and quotes the sentence of the title or
abstract that decides it; under rule 5 the record's "Type" line may be quoted instead.
Where the deciding fact is that a name is absent, the reason says so and quotes the
sentence that states the paper's problem or method.

1. The flexible job shop is not named in the title or abstract, or is named but is not
  the paper's own problem: a classical job shop; a job shop described with alternative
   machines but never named as a flexible job shop; a flow shop of any kind (including
   hybrid and flexible flow shops); a flexible manufacturing system that is not named as a
   flexible job shop; an open shop; a single machine; parallel machines as the only stage;
   or a flexible job shop that is only cited or contrasted.
2. None of the names of inclusion 2 is in the title or abstract, or reinforcement
  learning is not the paper's own method: a non-learning method (metaheuristic, exact
   method, dispatching rule), including a "policy" that is a fixed or hand-designed rule
   and a Markov model solved or used without learning; learning other than reinforcement
   learning; or reinforcement learning only in the motivation, related work or future
   work.
3. Not a primary study with quantitative results: surveys and reviews of any kind
  (systematic or narrative), position papers, abstracts, proposals.
4. Not in English: the title or the abstract is not in English.
5. Not a journal article or a conference paper: preprints, theses, books and book
  chapters.



### Borderline guidance

- Names are read from the title and abstract as written, never inferred. An abstract that
describes operations with alternative machines but does not name the flexible job shop
is excluded under rule 1; one that carries none of the names of inclusion 2 is excluded
under rule 2 (decided by the authors on 9 October 2026, with the adjacent terms added
the same day).
- A name is necessary, not sufficient: the named flexible job shop must be the paper's own
problem, and the paper's own method must be reinforcement learning. "Flexible" alone is
not enough: a flexible flow shop is a flow shop.
- An abbreviation names the flexible job shop only where it stands for it. FJS also
stands for a joint score in knee surgery and for fixed job scheduling, and FJSSP and
DFJSSP also stand for the fuzzy job shop scheduling problem: a record whose only name is
such an abbreviation, standing for something else, is excluded under rule 1. No rule
removes these records before screening; the screeners judge them as they judge any
other record (decided by the authors on 11 October 2026).
- An adjacent term alone (a policy, an MDP, a Markov or decision process): include when
the paper's method learns a policy or value function from experience or reward,
whatever it calls that learning; approximate dynamic programming that learns counts.
Exclude under rule 2 when the "policy" is a fixed or hand-designed rule, a heuristic or
a metaheuristic, when a Markov decision process is solved exactly without learning, or
when a Markov model only describes uncertainty (for example, machine breakdowns as a
Markov chain) and the method does not learn.
- Application domain: any. A flexible job shop that schedules computing tasks, network
traffic or other jobs on alternative resources is included, and its domain is recorded
(question 1.3).
- Several shop settings in one paper: include when the method is evaluated on a flexible
job shop. A citation of the flexible job shop, or a contrast with it, is not enough.
- A policy that chooses or switches among predefined dispatching rules at each decision:
include, as steering (RL-assisted, question 1.1); its method is reinforcement learning,
and the rule choice is its action (question 2.1). A paper whose own method is a
dispatching rule: exclude under rule 2.
- Reinforcement learning that tunes a metaheuristic or chooses its operators: include, as
steering (RL-assisted, question 1.1).
- Digital twin or simulation papers: include only if a scheduling policy is trained or
evaluated.
- Surveys and reviews: excluded under rule 3 (decided by the authors on 9 October 2026).
The introduction positions the review against them from an exploratory scoping phase
before the protocol, and none is counted.
- No abstract: a record shown with its title alone, whose title does not carry both names,
is `uncertain`, since the search matched it on the abstract the source indexes.
- Thin abstract: beyond the two names, `uncertain`, never `exclude`, when the abstract does
not decide a question (for example, whether reinforcement learning is the paper's own
method). This does not apply when the abstract decides it by describing a different
problem or method.



## Search strategy

OpenAlex is the only source, searched in titles and abstracts, with no second database and no
citation chasing. Field-wide statements therefore cover the English journal and conference papers
that OpenAlex indexes. The query is the two naming rules of the eligibility criteria (inclusions 1
and 2), with their closed lists. OpenAlex matches quoted terms exactly, without stemming, and reads
a hyphen in a quoted phrase as a space. Each name is therefore written with spaces, and each plural
or variant spelling the query relies on is listed. There is no year floor and no language filter.
The query was frozen on 11 October 2026 (`configs/search-query.toml`, rendered into
`configs/search-query.md` by `runners/build_query.py`). The official search, run the same day,
returned 664 works (`results/search/search-record.md`). The corpus was frozen when the screening
prompts were prepared. Three records with neither an abstract nor a DOI (118, 340 and 663) were
dropped before screening (`datasets/dropped.csv`).

Checks of how OpenAlex reads the names, and of candidate names outside the lists, preceded the
freeze. The stop rule, met on 11 October 2026, required every spelling and candidate name to be
decided by the authors.

### The frozen query (11 October 2026)

The query as OpenAlex receives it, in its query language (OQL):

```
works
where title_and_abstract has ("reinforcement learning" or "q learning" or "q network" or "q networks" or "deep q network" or "deep q networks" or "dqn" or "dqns" or "sarsa" or "reinforce" or "policy gradient" or "policy gradients" or "actor critic" or "a2c" or "a3c" or "proximal policy optimization" or "proximal policy optimisation" or "ppo" or "trust region policy optimization" or "trust region policy optimisation" or "trpo" or "deep deterministic policy gradient" or "ddpg" or "twin delayed ddpg" or "td3" or "soft actor critic" or "sac" or "temporal difference learning" or "policy" or "policies" or "markov decision process" or "mdp" or "mdps" or "markov" or "markovian" or "decision process" or "decision processes")
and title_and_abstract has ("flexible job shop" or "flexible jobshop" or "flexible job shops" or "flexible jobshops" or "flexible assembly job shop" or "flexible assembly jobshop" or "flexible assembly job shops" or "flexible assembly jobshops" or "flexible workshop" or "flexible workshops" or "fjs" or "fjsp" or "fjsps" or "fjssp" or "fjssps" or "dfjsp" or "dfjsps" or "dfjssp" or "dfjssps" or "mofjsp" or "mofjsps" or "fjspt" or "fjspts" or "fajsp" or "fajsps")
and type is (article or conference-paper)
```



### The query's terms (frozen on 11 October 2026)

The query is (any term of the first three groups) AND (any term of the last two).


| Group                  | Terms                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Reinforcement learning | reinforcement learning                                                                                                                                                                                                                                                                                                                                                                                                        |
| Its algorithms         | q learning; q network; q networks; deep q network; deep q networks; dqn; dqns; sarsa; reinforce; policy gradient; policy gradients; actor critic; a2c; a3c; proximal policy optimization; proximal policy optimisation; ppo; trust region policy optimization; trust region policy optimisation; trpo; deep deterministic policy gradient; ddpg; twin delayed ddpg; td3; soft actor critic; sac; temporal difference learning |
| Adjacent terms         | policy; policies; markov decision process; mdp; mdps; markov; markovian; decision process; decision processes                                                                                                                                                                                                                                                                                                                 |
| The flexible job shop  | flexible job shop; flexible jobshop; flexible job shops; flexible jobshops; flexible assembly job shop; flexible assembly jobshop; flexible assembly job shops; flexible assembly jobshops; flexible workshop; flexible workshops                                                                                                                                                                                             |
| Its abbreviations      | fjs; fjsp; fjsps; fjssp; fjssps; dfjsp; dfjsps; dfjssp; dfjssps; mofjsp; mofjsps; fjspt; fjspts; fajsp; fajsps                                                                                                                                                                                                                                                                                                                |


Two candidate names, q network and fjs, were drawn from domain expertise and from studies that
preliminary searches found in an exploratory scoping phase before the protocol. Others, such as
rl, drl, ddqn, pomdp and fjss, were not.

## Screening

Three open-weight models screened every record: Qwen3.8-27B (Alibaba), Gemma 4 26B A4B (Google)
and Muse Glimmer 30B (Meta). Each ran at a pinned revision, with reasoning on and its model card's
sampling settings. Each was served with vLLM 0.31.0 on its own NVIDIA H100 80 GB GPU. Each call
holds one record and no tools. The prompt is the Eligibility section verbatim
(`configs/screening-criteria.md`) with the record's title, abstract, venue, year and document
type. Every reason begins with its deciding criterion, "Inclusion N" or "Exclusion N". A reply
without one is asked again, and every attempt is recorded.

- Calibration. Osamah H. Hussein and the models screened a first batch of 25 records, the
calibration batch (batch 01), before the bulk run. A pilot against his calibration decisions
admitted each model, under a pass rule fixed in advance. The criteria were to be clarified once,
and the batch screened again, if any model matched his decision on fewer than 20 of the 25. Each
model's Cohen's kappa with him, weighted over exclude < uncertain < include, is reported beside
its agreement.
- Vote and settlement (`src/screening.py`, `vote` and `settle`). A record is included when at
least two of the three screeners include it. Otherwise it is removed, as excluded when any
screener excludes it and as uncertain when none does. No person resolves a disagreement among
the screeners. Uncertain records are counted on their own and enter neither the map nor the core.
- Validation. Osamah H. Hussein screened, blind to the votes, a random sample of 60 removed and 40
included records. The calibration batch was left out, and the seed is recorded in
`configs/screening.toml`. Where his decision differs from the one made without a person, Moayad
Alnammi screened the record again. Moayad Alnammi's sheet showed neither the votes nor Hussein's
decision, and his own decision settles the record. An inclusion is never overturned. Two bounds
are reported: relevant records among those removed, and ineligible records among those included.
Each is reported as first screened and after adjudication.



## Two tiers: the map and the core

The map is the review's included set: every record the screening included. The core is 100 of its
studies, selected for full-text synthesis; a mapped study outside the core stays included. The map
answers question 1 over the field, and the core answers questions 2 to 5 in depth. The map follows
Kitchenham and Charters' classification of a broad set of studies (2007, section 8). The core is a
purposive sample of maximum variation, chosen for coverage (Ames, Glenton and Lewin, 2019).
Eligibility rests on each study's own features. Field-wide counts therefore never depend on the
core. The core's frame was fixed before screening and refined only before the core was selected.
Findings from the core are about its studies, never about the field, and say so ("in the core").

### The map

The three screening models coded the included records from their titles and abstracts, one paper
per call. They used the fifteen axes of Part A of the coding scheme (`datasets/coding-scheme.md`;
Data extraction). Moayad Alnammi coded record 74, carried forward later by the validation, under the
same scheme and rules. It enters the map without a vote and stays out of the models' agreement,
computed over 532 records. The vote (`runners/map_vote.py`, `src/mapcodes.py`) first applies to
each model's codes the five rules of Part A that set one axis from another:

- a steering role has the scheduling action `not-applicable`;
- a `not-stated` role has a `not-stated` scheduling action;
- a `tabular` or `non-neural` learner has the deep architecture `not-applicable`;
- a `not-stated` learner has a `not-stated` deep architecture;
- a `tabular` learner's state encoding is `discrete-states`.

A code then enters by majority, on a list axis code by code. On `readiness_claim`, the cell takes
the highest level that at least two models reach. A cell with no majority is `not-stated` (the vote
can give `not-stated` on any axis), and no person resolves it. The five rules are applied again to
the voted codes.

Agreement is computed on the models' codes after the rules and before the vote. Each code's kappa
is the mean of the pairwise Cohen's kappas on its presence. An axis steers the core rule's coverage
step (step 2, below) only if its categories' mean kappa reaches 0.6. Its categories exclude
`not-stated`, `other`, `not-applicable` and codes the voted map never gives. Moayad Alnammi coded
the role, the learner and the readiness claim on 25 map records, blind to the models' codes. He did
this before he confirmed the claims of step 1 (below). The records were drawn under a recorded seed
from those included without a person, outside the calibration batch. His agreement with the map
and with each model is reported.

### The core's candidates

Every map record whose learner is stated is a candidate; one whose learner is not stated is not.
The role is coded only from what the abstract states. A record whose role is `not-stated` is a
candidate in a stratum of its own. Records of one study count once: those sharing a DOI, an
OpenAlex work, or a normalized title with agreeing first authors (`configs/deduplicate.toml`). The
journal version is kept, then the later version, then the lower record number. Non-deep studies
(tabular or other non-neural learners) take at most 10 places.

### Venue and citations

Venues are ranked by the SCImago Journal Rank (SJR) for 2025 and by ICORE2026, downloaded on 18
October 2026. Band 1 is a journal or proceedings series whose best SJR quartile is Q1, or a
conference ranked A* by ICORE. Band 2 is every other venue. SJR is matched by the record's ISSN-L
only. A venue outside SJR's band 1 that may be a conference is matched to ICORE by name, at ranks
A* and A. A name match counts once Moayad Alnammi confirms it (`results/core/venue-bands.md`;
`datasets/venue-matches.csv`). For ties, venues are ordered Q1 or A*, then Q2 or A, then Q3, then
the rest. A candidate's citation standing is the share of same-year candidates cited more at the
snapshot. Standing is computed within a year, since raw citations favor older papers. Venue rank
orders places and judges no study's quality. No criterion on a venue's country is applied; SJR's
country is only reported (`results/core/core-vs-map.csv`).

### The core rule

A script (`runners/core_selection.py`) selects 100 studies from the map's codes and the records'
metadata at the search snapshot. The selection is locked by the SHA-256 of the core's records and
their steps, and a rerun that would change it is refused.

1. Use beyond simulation. Every candidate whose abstract claims a run at L3 to L5 enters, whatever
  its venue or citations. Moayad Alnammi first confirmed each claim against the abstract, and step
   1 takes the level he confirmed. Where the abstract leaves the level open, the full text settles
   it (`read_from` in `datasets/core-claims.csv`). A claim of real data alone (L2) competes at
   steps 2 and 3. The map's readiness codes stay the models' vote.
2. Coverage. Every category of the coverage axes gets at least three studies, or all its
  candidates if fewer. The coverage axes are the Part A axes, other than the readiness claim,
   whose agreement reaches 0.6. The script repeatedly adds the candidate that fills the most unmet
   places, one place per code. If more than 100 places are needed, the minimum drops to two, then
   one. An unmet minimum is reported with its cause.
3. Fill. The places are divided among three strata: 35 end-to-end, 35 steering and 30 role not
  stated. The two roles take equal shares, where the map's proportions would have given steering
   more places. Studies from steps 1 and 2 count toward their stratum's share. A stratum over its
   share takes no more, and places it cannot fill pass to the others in proportion. Within a
   stratum, band 1 comes before band 2. In the band where the last place falls, places are shared
   among years in proportion to their candidates not yet chosen. Each year's places go to its most
   cited candidates. Equal remainders go to the stratum with more places, then the one listed
   first, and to the year with more candidates, then the earlier one. The role of each study in the
   third stratum is read from its full text.

Ties at steps 2 and 3 go to the better venue, then the better standing, then the lower record
number. The record number is OpenAlex's return order. The selection's report counts the places the
record number decides (`results/core/core-selection.md`).

### Precedence

The cap on non-deep studies binds at every step. At steps 1 and 2, a non-deep candidate past the
cap is passed over. If step 3 would exceed the cap, the non-deep studies with the best citation
standing are kept. Each of the others gives its place to the next deep candidate of its stratum,
band and year. If that year has none, the stratum's best deep candidate takes it, band 1 first. A
category that would need an eleventh non-deep study is reported as unmet. A confirmed claim at L3
to L5 that the cap leaves out is named under question 5.

### Limitations of the core's selection

The core over-represents rare categories by design, and step 2 favors studies with many codes.
Places beyond the minimums lean toward older, better-known work. Venue rank and citations
describe a paper's publication and attention, not its method's quality. Citations also favor
positive results (Duyx and colleagues, 2017). Among the newest papers, ties fall to the lower
record number. A study can enter the core under an abstract code its full text does not bear
out. Journal metrics are not used to measure a study's quality (DORA, 2012).

## Data extraction

Part A, the map, codes every included record from its title and abstract on fifteen axes. Its rules
are Part A of `datasets/coding-scheme.md`, and its schema is `configs/map.toml`. Both were written
before any record was coded, piloted on the 24 included records of the calibration batch, and then
fixed. Every axis allows `not-stated` except three with a default: `hybridization` (`none`),
`domain` (`manufacturing`) and `readiness_claim` (`none`). The reply quotes the abstract for the
role, the learner and the readiness claim. A code marked "alone" is not combined with another.


| Axis                        | Question | Kind   | Codes                                                                                                                                                                                                          |
| --------------------------- | -------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `policy_role`               | 1.1      | single | `end-to-end`; `steering-rules` (chooses among dispatching rules, or sets their weights); `steering-heuristic` (controls a heuristic or metaheuristic, or decides an auxiliary part of the solution beside one) |
| `coordination`              | 1.1      | list   | `single-agent` (alone); `multi-agent`; `hierarchical` (with separate agents per level, also multi-agent)                                                                                                       |
| `scheduling_action`         | 1.1, 2.1 | single | `operation`; `machine`; `operation-machine-pair`; `whole-schedule`; `schedule-change`; `other`; `not-applicable` (a steering study)                                                                            |
| `learner_depth`             | 1.2      | single | `deep`; `non-neural`; `tabular`                                                                                                                                                                                |
| `deep_architecture`         | 2.2      | list   | `fully-connected`; `convolutional`; `recurrent`; `graph-neural-network`; `attention-transformer`; `pointer-network`; `other`; `not-applicable` (alone: a tabular or non-neural learner)                        |
| `training_algorithm_family` | 1.2      | list   | `value-based`; `policy-gradient` (REINFORCE, PPO, TRPO); `actor-critic` (A2C, A3C, DDPG, TD3, SAC); `other` (offline, model-based, safe or meta-learning)                                                      |
| `hybridization`             | 1.2      | single | `none` (the default); `metaheuristic`; `exact`; `other-learner`                                                                                                                                                |
| `state_content`             | 2.1      | list   | `operations`; `jobs`; `machines`; `shop-aggregate`; `events`; `other-resources`; `search-state`; `other`                                                                                                       |
| `state_encoding`            | 2.2      | list   | `discrete-states` (alone: a tabular learner); `feature-vector`; `sequence`; `set`; `matrix`; `disjunctive-graph`; `heterogeneous-graph`; `other-graph`; `text`; `other`                                        |
| `dynamic_events`            | 1.3      | list   | `none` (alone: a static shop); `job-arrivals`; `machine-breakdowns`; `uncertain-processing-times`; `other`                                                                                                     |
| `objective`                 | 1.3      | list   | `makespan`; `tardiness`; `flow-time`; `workload`; `utilization`; `energy`; `cost`; `robustness`; `other`                                                                                                       |
| `constraints`               | 1.3      | list   | `none` (alone); `transport`; `setup-times`; `workers`; `energy` (a limit on, or a model of, the energy supply); `distributed` (several factories or lines); `other`                                            |
| `instances`                 | 3.1      | list   | `public-benchmark`; `generated`; `industrial`                                                                                                                                                                  |
| `domain`                    | 1.3      | list   | `manufacturing` (the default); `computing-networks`; `other`                                                                                                                                                   |
| `readiness_claim`           | 5        | single | `none` (the default); `real-data`; `twin-or-hil`; `testbed-or-shadow`; `live-system` (the highest claimed)                                                                                                     |


Part B, the core, codes each core study from its full text, one row per study in
`datasets/coded-studies.csv`. Part B of `datasets/coding-scheme.md` was revised after a pilot of
five studies and frozen on 21 October 2026, before the full run. Its columns follow Ahmed Azab's
synthesis matrix (`Problem`, `Formulation`, `Learner`, `Evidence`), with the architecture added.
They repeat every Part A axis from the full text and add, per question:

- 1: study type, flexibility, steering action, sub-decision, paradigm, algorithm and its update;
- 2: state contents, action type, masking, reward and its timing, decision points, observability;
- 3: benchmark sets, baselines and time limits, metrics, inference time, training cost, scaling,
runs and spread, ablations, code and data, claims, training stability;
- 4: how test instances differ from the training ones, their provenance, transfer mode, outcome;
- 5: readiness level with its passage, deadlines, imperfect data, interpretability, robustness.

A study's result is recorded as its claim, never as an improvement percentage. Question identifiers
such as D07 refer to Part B of `datasets/coding-scheme.md`. The coding agent, Qwen3.8-27B, codes
every core study from its full text through the project's tools. The project serves it with vLLM
0.31.0 on one NVIDIA B200 GPU. Code checks each answer during and after the run (`runners/core_check.py`): 
quotes verbatim on the cited page, codes in their lists, rules between questions. The judge, Muse Glimmer
30B, reads every answer against the paper. Its verdicts are reported and never applied, with the
agreement of coder and judge. Osamah H. Hussein codes six questions on a seeded fifth of the core,
blind to the models' answers and verdicts (`results/core-coding/draws.csv`). The authors correct an
answer that breaks Part B, as the judge's reading shows (`datasets/core-corrections.csv`). Both are 
set out under Amendments. The published dataset holds the answers, the codes, the pages and a 
SHA-256 of each quote, but no quote text.

## Quality assessment

Every core study is assessed on its full text; the assessment is not an inclusion filter. The seven
items are adapted from the CASP checklists and Kitchenham and Charters:

1. The shop is specified: its jobs, machines, eligible machines, processing times and
  constraints, or the generator that produces them.
2. The decision process is specified: its state, actions and reward.
3. The algorithm and its update are specified, with the settings needed to rerun it.
4. The instances are repeatable: public, released, or generated by a stated procedure.
5. The baselines are run on the same instances, each with a stated time limit.
6. Results come from more than one training run, with the spread across runs reported.
7. Every claim of transfer or of use beyond simulation is tied to a test the study ran.

Each item is scored 1 (met), 0.5 (partly) or 0 (not met), for methodological rather than reporting
quality. An item the study does not report enough to judge is not assessable, never inferred. Part
B's section Q defines each score (`datasets/coding-scheme.md`). The coding agent scores every
study, and the judge reads every score. Scores are published per study and used only in
sensitivity analysis, never to weight a synthesis.

## Synthesis

The synthesis is descriptive. Question 1 and the field-wide counts come from the map, and questions
2 to 5 from the core. No outcome is pooled; each result is the study's own claim in its own metric.
The certainty of evidence is not graded. The map's counts for model, encoding and instances are
lower bounds, since abstracts may omit them. Question 1.1 reports roles over the records that state
one, beside the share that does not. Every figure is regenerated from the coded dataset by
`runners/make_figures.py`. The flow-diagram counts come from `runners/make_tables.py`, over
`datasets/references.json` and `datasets/screening.csv`. Question 3.4 is read through five tests,
defined under Amendments (2026-10-22, the tests of Question 3.4).

Five sensitivity analyses are run:

1. without the lowest-quality fifth, by mean score over assessable items, ties at the cut kept;
2. the map's abstract codes against the core's full-text codes, per axis and per code, with Cohen's
  kappa (`results/core-synthesis/abstract-vs-full-text.md`);
3. without the studies admitted at step 2 (coverage);
4. the map's shares recomputed on the records whose codes all three models gave alike;
5. without the answers the judge disputed (partly or not supported); corrected answers stand.



## Reporting

- PRISMA 2020, with its flow diagram. The included set is the map. The path continues to the core,
labeled "selected for full-text synthesis". It counts each step of the core rule, per stratum and
band at step 3. It also counts the studies the cap left out, and the full texts sought and not
retrieved.
- Records left uncertain after screening are counted on their own. Records with neither an abstract
nor a DOI are counted as removed for other reasons.
- This protocol and `protocol-history.md` are public in the repository, and the paper points to
the protocol's amendments, which date every change (PRISMA 2020, item 24c).



## Amendments

`protocol-history.md` holds 25 dated amendments. The ten that changed the review after its data
were seen, or that replaced a planned check, are restated below as five. The other fifteen refined
a step before it ran. They are written into the sections above.

### 2026-10-13 and 2026-10-15, screening disagreements and the validation

The approved protocol sent every disagreement of the vote to a person. Instead, a rule settles each:
a record is included when at least two of the three screeners include it. The rule was set on 13
October 2026, after the vote's totals were known and before any disagreement was examined. The
approved validation sample, drawn in proportion to the vote, held few removed records and none the
rule removes. It was redrawn before use as 60 removed and 40 included records. On 15 October 2026,
after the validation's result was known, a second reading of its disagreements was added. The first
reading had carried a large share of the sampled removed records forward. The bound then rested on
a single reading of borderline records, and a second reading is the usual remedy. Moayad Alnammi
screened each disagreement again, on a sheet that showed neither the votes nor the first screener's
decisions. Because the change followed the result, both bounds are reported, before and after
adjudication. Decided by Moayad Alnammi on 13 October 2026 and 15 October 2026.

### 2026-10-15 and 2026-10-17, step 1 of the core

The approved step 1 took every candidate whose abstract claimed use beyond simulation (L2 to L5),
once Osamah H. Hussein confirmed it. Moayad Alnammi took over the confirmation on 15 October 2026,
after the map's vote. On 17 October 2026, before any core study was selected, step 1 was limited to
claims at L3 to L5. Of the 41 candidates claiming use beyond simulation, 37 claimed a test on real
data and 4 a higher level. Step 1 as written would have filled about two fifths of the core. Its
premise, that these studies are few, holds only above real data. The same day, at step 1, the
person's level replaced the vote's, and the full text settles a level the abstract leaves open. The
map's readiness codes stay the models' vote. The vote gave record 588 `real-data` although its
abstract reports a digital twin. Record 399's abstract leaves its level open. The models agree least
on L3 and L4 (mean pairwise kappa 0.282 and 0.222). Decided by Moayad Alnammi on 15 October 2026
and 17 October 2026.

### 2026-10-21 and 2026-10-24, coding and checking the core

The approved plan had a second coder code a seeded random fifth of the core. A person's check of
the disputed answers and of a fifth of the core did not fit before submission on 31 October 2026.
Instead, the coding agent, Qwen3.8-27B (revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0,
reasoning effort medium), codes every study through the project's tools. Code checks
every answer during and after the run, against Part B as frozen on 21 October 2026. A judge, Muse
Glimmer 30B (revision a4e59da52a7bc87ae7251dd5545c0dd437c44b68, reasoning strength medium), reads
every answer and quality score; its verdicts are reported, never applied. The agreement of coder
and judge is reported, and the published dataset holds no quote text. The lowest-quality fifth is
set by mean score with ties kept, and a fifth sensitivity analysis leaves out the judge's disputes.
On 24 October 2026, a person's check was added, because the model-only check left the coding without
a human reading. Osamah H. Hussein codes six questions on the fifth's 20 studies, drawn on 20
October 2026 (seed 20261020), blind to every model's answer and verdict. They are A01
`policy_role`, B07 `algorithm`, F01 `readiness_level` and D14 `seeds`, with D07 (baselines rerun)
and E01 (a transfer test) each reduced to one answer. The paper's main findings rest on these six
questions. Agreement and Cohen's kappa are reported per question, with every disagreement, and his
answers replace none of the agent's. Decided by Moayad Alnammi on 21 October 2026 and 24 October
2026.

### 2026-10-22, answers corrected by the authors

Neither the approved plan nor the coding of 21 October 2026 provided for correcting a coded answer.
When an answer contradicted Part B, or was a claim confirmed at step 1, the authors read it against 
the paper. A flagged answer breaks Part B's own rules, as the judge's reading shows, or is a claim 
confirmed at step 1. Where the authors find it wrong, they correct it with every answer that follows, 
in `datasets/core-corrections.csv`. The tables take the authors' value, while the agreement of coder
and judge uses the coder's. In the analysis without the judge's disputes, a corrected answer stands.
Only flagged answers are read. This is therefore no check of the core. The judge's disputes showed
records 191 and 530 filed as steering, although the scheme's rules make them end-to-end. Their
correction changed 10 answers in 2 studies. Record 315's readiness and record 504's role were also
read, and kept as coded. Decided by Moayad Alnammi on 22 October 2026.

### 2026-10-22, the tests of Question 3.4

Question 3.4 asks whether studies making the same claim used the same instances, baselines, metrics
and time limits. The approved protocol did not say how this is read from the coded answers. For
each of the six recurring claims Part B codes (D19), five tests are reported as shares of the
studies making it:

- instances: a named benchmark set (D01) shared with another study making the claim;
- metrics: an objective (A11) and a headline statistic (D13) shared with another such study;
- baselines and time limits: every baseline (D07) rerun by the study's authors, no time limit
unstated;
- all of the question's terms: a set, an objective and a statistic shared with one other study,
both passing the baselines test;
- training runs: results over several training runs, with their spread (D14, D15).

A dispatching rule, or a policy that builds its schedule in one pass, needs no time limit. Whether
studies used the same baselines is not tested, since a baseline's name is free text. The tests of
instances, of baselines and time limits, and of training runs were fixed on 21 October 2026, before
any result was seen. The tests of metrics and of all terms were added on 22 October 2026, after the
results were seen, to test every term. The paper says so. The instances test had left out a code
that does not exist in place of `other-benchmark`. This fault was found and fixed on 22 October
2026, after the results were seen. Decided by Moayad Alnammi on 22 October 2026.