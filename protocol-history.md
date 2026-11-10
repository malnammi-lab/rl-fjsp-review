# Protocol amendments

The approved protocol is `protocol.md`. Each amendment below quotes the wording it replaced.
The protocol was approved by Moayad AlNammi on 11 October 2026, before the search.

## Amendments

### 2026-10-11, three records dropped before screening

Records 118, 340 and 663 of the search have neither an abstract nor a DOI. We dropped them
before screening, instead of screening them from their titles (Eligibility criteria, "No
abstract"). They are listed in `datasets/dropped.csv` and counted in the flow
diagram as records removed for other reasons. Decided by Moayad AlNammi.

### 2026-10-12, the screening panel

The screeners are three open-weight language models: Qwen3.8-27B (Alibaba), Gemma 4 26B
A4B (Google) and Muse Glimmer 30B (Meta), each at a pinned revision, with reasoning on and
the sampling settings of its model card, served with vLLM 0.31.0 on one NVIDIA H100 80 GB
GPU per model. Each model was admitted after a pilot against Osamah Hussein's
calibration decisions, under a pass rule fixed before the pilot. This settles open
decision 2 (Screening). Decided by Moayad AlNammi.

### 2026-10-12, every reason begins with its criterion

Every reason a screener gives, whatever its decision, begins with the label of the criterion
that decided it: "Inclusion N" or "Exclusion N", and for an uncertain record the inclusion
criterion its record leaves open. A reply whose reason does not begin so is not accepted, and
the screener is asked again; every attempt is recorded. This extends to inclusions and
uncertain records the rule the eligibility criteria give for exclusions. Decided by Moayad
AlNammi before any record of this review was screened.

### 2026-10-12, how the calibration is read

The calibration is read by agreement rather than by kappa. For each model, we count the
records of the 25 on which its decision and Osamah's are the same, of include, uncertain and
exclude, so that an uncertain against an include is a disagreement. The criteria are
clarified once, as Screening states, if any model agrees with Osamah on fewer than 20 of the
25. Each model's Cohen's kappa with Osamah, weighted over exclude < uncertain < include, is
reported beside its agreement, and the vote's decisions are set against Osamah's in a table
of counts. Kappa corrects agreement for chance from how often each screener gives each
decision; when one decision dominates a batch, it can fall to zero although two screeners
disagree on a single record, and a kappa threshold would then call for a clarification that
the agreement does not support. If a model still agrees with Osamah on fewer than 20 of the
25 after the clarification, the bulk run proceeds with the clarified criteria and the
shortfall is reported; the validation sample measures its effect on the vote. Decided by
Moayad AlNammi after the models had screened the calibration batch and before Osamah did.

### 2026-10-13, disagreements settled by rule, and the validation sample redrawn

The vote's disagreements are settled by rule instead of by a person. A disagreement is
included when at least two screeners include it; otherwise it is removed, as excluded when
any screener excludes it and as uncertain when none does (`src/screening.py`,
`settle`). Together with the vote, the rule reads: a record is included when at least two of
the three screeners include it. A record removed as uncertain is counted on its own in the
flow diagram, as Screening provides for records left uncertain, and enters neither the map
nor the core.

The validation sample is redrawn before any of its records was screened. It now covers every
record decided without a person, by the vote or by the rule: 60 records drawn from those
removed (excluded or left uncertain) and 40 from those included, batch 01 left out, under
the recorded seed, screened by Osamah without the votes. We report two bounds: on the
relevant records among those removed, and on the ineligible records among those included.
The removed records receive more of the sample than their share, since a relevant study
removed at screening is never looked at again; the included ones are checked as well, since
most of the map is coded from titles and abstracts and never read in full. A removed record
that Osamah does not exclude is carried forward on his decision. The first draw, in
proportion to the vote's counts, was replaced before use: it held few removed records and
none of those the rule removes.

Both changes were decided by Moayad AlNammi on 13 October 2026, after the vote's totals were
known and before any disagreement was examined or resolved, so that the screening could
proceed without a person resolving disagreements.

### 2026-10-14, the map's coding scheme, and the core's candidates

The map's decision rules are now in `datasets/coding-scheme.md`, Part A, and its
schema in `configs/map.toml`, both written on 13 and 14 October 2026 before any
record was coded. Data extraction said: "Until `datasets/coding-scheme.md` is
rewritten with Part A's decision rules, this table is the scheme; the file as it stands is
the first round's and is not used." That no longer holds. The scheme is the rulebook the
models receive, and the table of fourteen axes of 10 October 2026 is replaced by the table
below. The changes are these:

- A fifteenth axis, `state_content`, records what the state describes (question 2.1),
  beside `state_encoding`, which records how the network reads it.
- `model` becomes `deep_architecture`, coded for a deep learner only (`not-applicable`
  replaces `table`), and `convolutional-recurrent` is split in two.
- `algorithm_family` becomes `training_algorithm_family`, now a list, so that a study whose
  agents are trained with two families keeps both. PPO and TRPO stay under policy gradient,
  and count as actor-critic where question 3.4 weighs actor-critic claims.
- `hybridisation` is spelled `hybridization`.
- `scheduling_action` gains `whole-schedule`, `schedule-change` and `other`;
  `state_encoding` becomes a list, with `matrix-or-sequence` split and `discrete-states`,
  `set`, `other-graph` and `text` added; `objective` gains `workload`, `cost` and
  `robustness`; `constraints` gains `none`; `domain` becomes a list.
- Data extraction also said: "Every axis also allows `not-stated`". Three axes now take a
  default instead and do not allow it: `hybridization` (`none`), `domain`
  (`manufacturing`) and `readiness_claim` (`none`).

| Axis | Question | Kind | Codes |
| --- | --- | --- | --- |
| `policy_role` | 1.1 | single | `end-to-end`; `steering-rules` (chooses among dispatching rules, or sets their weights); `steering-heuristic` (controls a heuristic or metaheuristic, or decides an auxiliary part of the solution beside one) |
| `coordination` | 1.1 | list | `single-agent` (alone); `multi-agent`; `hierarchical` (with separate agents per level, also multi-agent) |
| `scheduling_action` | 1.1, 2.1 | single | `operation`; `machine`; `operation-machine-pair`; `whole-schedule`; `schedule-change`; `other`; `not-applicable` (a steering study) |
| `learner_depth` | 1.2 | single | `deep`; `non-neural`; `tabular` |
| `deep_architecture` | 2.2 | list | `fully-connected`; `convolutional`; `recurrent`; `graph-neural-network`; `attention-transformer`; `pointer-network`; `other`; `not-applicable` (alone: a tabular or non-neural learner) |
| `training_algorithm_family` | 1.2 | list | `value-based`; `policy-gradient` (REINFORCE, PPO, TRPO); `actor-critic` (A2C, A3C, DDPG, TD3, SAC); `other` (offline, model-based, safe or meta-learning) |
| `hybridization` | 1.2 | single | `none` (the default); `metaheuristic`; `exact`; `other-learner` |
| `state_content` | 2.1 | list | `operations`; `jobs`; `machines`; `shop-aggregate`; `events`; `other-resources`; `search-state`; `other` |
| `state_encoding` | 2.2 | list | `discrete-states` (alone: a tabular learner); `feature-vector`; `sequence`; `set`; `matrix`; `disjunctive-graph`; `heterogeneous-graph`; `other-graph`; `text`; `other` |
| `dynamic_events` | 1.3 | list | `none` (alone: a static shop); `job-arrivals`; `machine-breakdowns`; `uncertain-processing-times`; `other` |
| `objective` | 1.3 | list | `makespan`; `tardiness`; `flow-time`; `workload`; `utilization`; `energy`; `cost`; `robustness`; `other` |
| `constraints` | 1.3 | list | `none` (alone); `transport`; `setup-times`; `workers`; `energy` (a limit on, or a model of, the energy supply); `distributed` (several factories or lines); `other` |
| `instances` | 3.1 | list | `public-benchmark`; `generated`; `industrial` |
| `domain` | 1.3 | list | `manufacturing` (the default); `computing-networks`; `other` |
| `readiness_claim` | 5 | single | `none` (the default); `real-data`; `twin-or-hil`; `testbed-or-shadow`; `live-system` (the highest claimed) |

The role is coded only from what the abstract states. Many abstracts say only that
reinforcement learning solves the problem, without saying what the policy chooses,
and the full texts of such studies showed both roles. A default role would
misfile the steering studies among them, so their role is `not-stated`. Two
tiers said: "A record whose role or learner is not stated is counted in the
report and is not a candidate; no person checks it." This now reads: a record
whose learner is not stated is counted in the report and is not a candidate,
while a record whose role is not stated, but whose learner is, is a candidate.
At step 3, the places are divided among three strata, end to end, steering,
and role not stated, in proportion to the map's records in each (largest
remainders), in place of the two roles; a stratum already over its share
takes no more, and places a stratum cannot fill pass to the others in proportion
to their shares. The role of each core study of the third stratum is read
from its full text. Question 1.1 reports the roles over the records that
state them, beside the share that does not, and the flow diagram gives the
counts of step 3 per stratum. Osamah's blind coding of the role, the learner
and the readiness claim on the calibration batch follows the same rules.

Before the map is coded, the three models code the 24 included records of the screening's
calibration batch with the scheme, and their replies are read for whether they follow its
rules. This pilot is not part of the map: the scheme may still be revised after it, in place
and dated, since no record of the map has been coded. The map's run then codes every
included record, those 24 among them. It waits for the screening's release, since records
the validation sample carries forward can join the included set.

Decided by Moayad AlNammi on 14 October 2026, before any record was coded.

### 2026-10-14, the map coded before the screening's release

The amendment above said of the map's run: "It waits for the screening's release, since
records the validation sample carries forward can join the included set." The map's run
instead codes the included records now, before the release, so that the coding does not
wait on the validation sample. Its keep list, prompts and codes are withheld until
the release, since a list of coded records would show the person screening the
validation sample which records were included. A record the validation sample carries
forward is coded afterwards in a top-up run, by the same three models with the same scheme
and settings, and its codes join the map before the map is analysed. The validation sample
cannot remove an included record, so no code is withdrawn. Decided by Moayad AlNammi on
14 October 2026, after the pilot and before the map's run.

### 2026-10-15, the scheme's rules applied before the map's vote

Two tiers said of the map: "A code is taken by majority. A cell with no majority (the three
models give three answers) is coded `not-stated`, and no person resolves it." This now
reads: each model's codes are first made consistent with the five rules of the coding
scheme that set one axis's code from another's; a code is then taken by majority, a cell
with no majority is coded `not-stated`, and no person resolves it; and the same five rules
are applied once more to the voted codes. The five rules are those Part A of
`datasets/coding-scheme.md` states:

- a steering role (`steering-rules` or `steering-heuristic`) has the scheduling action
  `not-applicable`;
- a role that is `not-stated` has a scheduling action that is `not-stated`;
- a `tabular` or `non-neural` learner has the deep architecture `not-applicable`;
- a learner that is `not-stated` has a deep architecture that is `not-stated`;
- a `tabular` learner's state encoding is `discrete-states`.

On a list axis, the majority is taken code by code: a code is in the map when at least two
models give it, and the cell is `not-stated` when no code is. On `readiness_claim`, whose
codes are the levels L1 to L5, the cell takes the highest level that at least two models
reach, the middle of the three. A record that two models place beyond simulation, at
different levels, while the third does not, is therefore coded at the lower of the two
levels instead of `not-stated`, and stays among the claims Osamah confirms at step 1. The
rules read only each model's own codes and add no judgement of ours. They are applied a
second time because a vote taken axis by axis can leave a pair the scheme does not allow:
two models that call a study steering but differ on its kind leave its role without a
majority, while their two `not-applicable` actions carry the vote on the action.

Agreement between the models is computed on their codes after the rules and before the
vote. Two tiers said: "Agreement between the three models is computed by script for every
axis, on every included record: the mean pairwise Cohen's kappa, per code for a
multi-label axis." This now reads: on every axis that can steer step 2 of the core rule,
single or list, each code is read as present or absent, and the agreement compared with 0.6
is the mean of the kappas of the axis's categories at step 2 that the map holds, over those
for which a kappa is defined. These are the axis's codes other than `not-stated`, `other`
and `not-applicable` that the voted map gives to at least one record, counted after the
second pass of the rules; an axis with none does not steer. The kappas of the other codes
are reported and are not in that mean, and a single axis's kappa over all its codes is
reported beside it, for reference. `readiness_claim`, whose codes are levels and which
never steers step 2, is reported by its kappa over all its codes alone. We read agreement
this way for three reasons:

- The bar decides whether an axis steers step 2, which leaves `not-stated`, `other` and
  `not-applicable` out, so these codes should not decide it. The rules also set them from
  another axis: `not-applicable` and `not-stated` on `scheduling_action` from the role, and
  `not-applicable` on `deep_architecture` from the learner, so a kappa that includes them
  measures agreement on that other axis.
- Each category counts once, as at step 2, where every category is owed the same three
  places. One kappa pooled over all codes would let the common codes carry an axis while
  its rare categories, the ones step 2 acts on, stayed unreliable.
- A category the map gives to no record cannot be filled at step 2, while a code one model
  gives once would enter the mean with a kappa of zero.

The cost is accepted: a rare category with a low kappa can keep its whole axis from
steering, `hybridization` among the axes at risk, since its rare codes count as much as
`none`. The map's runner (`runners/map_vote.py`, with the rules in
`src/mapcodes.py`) reports every code's kappa, and how many cells each rule
changed, for each model and after the vote, and lists every changed cell.

Decided by Moayad AlNammi on 15 October 2026, after the three models had coded the
included records and before the runner computed any vote or agreement. A check
showed that two of the models had left the state encoding of most tabular
learners `not-stated`, against the scheme's rule, so that the vote as written
would have turned those cells `not-stated` although the scheme decides them.
The pilot, on far fewer records, did not show it. The same check found a few
records split three ways on the readiness claim, two models claiming use beyond
simulation at different levels; the vote by levels was decided on the same day,
before any vote was computed. The reading of agreement was decided the same day
too, before any kappa was computed.

### 2026-10-15, the claims of step 1 confirmed by Moayad AlNammi

Two tiers said of step 1 of the core rule that a candidate claiming use beyond simulation
"is in the core, whatever its venue or citations, once Osamah has confirmed the claim
against its abstract", and the amendment above says that such a record "stays among the
claims Osamah confirms at step 1". The claims are confirmed instead by Moayad AlNammi, each
against its abstract, on a sheet that shows him the models' claim (the voted level, each
model's level and quote) and asks yes or no. A run the abstract reports at any level from
L2 to L5 confirms the claim, even at a level other than the models'. His answers are kept
out of the codebase until the screening's release and until Osamah has coded the role, the
learner and the readiness claim blind on the calibration batch, since the sheet lists
included records, some of them in that batch. Osamah's blind coding of
those three axes is unchanged. Decided by Moayad AlNammi on 15 October 2026, after the
map's vote.

### 2026-10-15, the validation's disagreements adjudicated by a second person

The amendment of 13 October 2026 says: "A removed record that Osamah does not exclude is
carried forward on his decision." Screening says of the validation that "the bound on the
relevant records the vote excluded is reported with it". Both now read as follows. The
sampled records on which Osamah's decision differs from the decision made without a
person, the removed records he did not exclude and the included records he did not include,
are screened again by Moayad AlNammi, from their titles and abstracts, on a sheet that shows
neither the votes nor Osamah's decisions, and his decision settles each. A removed record is
carried forward on his decision, and one he excludes stays removed; an included record stays
included, since an exclusion never overturns an inclusion. The bounds are reported twice:
against Osamah's decisions as screened, and against the decisions after adjudication.

Decided by Moayad AlNammi on 15 October 2026, after the validation's result was known. The
validation carried a large share of the sampled removed records forward, so the bound
rested on a single reading of borderline records. A second person's reading of the
disagreements is the usual remedy. Because the change follows the result, both bounds
are reported.

### 2026-10-15, the three axes coded by Moayad AlNammi on a random sample of the map

Two tiers said: "Osamah codes three axes blind, the role, the learner and the readiness
claim, on the 25 records of the screening's calibration batch. These axes decide who can
enter the core, and agreement among the models shows consistency, not correctness. His
agreement with the panel on each is reported." This now reads: Moayad AlNammi codes the
role, the learner and the readiness claim blind on a random sample of 25 of the map's
records, from their titles and abstracts and under the scheme's rules, on a sheet that shows
none of the models' codes, before he confirms the claims of step 1; his agreement with the
map and with each model on each axis is reported. The sample is drawn under a recorded seed
from the records included without a person, outside the calibration batch, so that a record
a person carried forward later does not change it. The calibration batch is not used
because its records were coded in the pilot of 14 October 2026, whose replies Moayad has
seen, so his coding of them would not be blind.

Two sentences of earlier amendments no longer apply: that Osamah's blind coding of the three
axes on the calibration batch "follows the same rules" (14 October), and that the answers of
step 1 are kept out of the codebase "until Osamah has coded the role, the learner and the
readiness claim blind on the calibration batch" (15 October). The map's codes and the
answers of step 1 enter the codebase once the map is complete, after its top-up run.
Decided by Moayad AlNammi on 15 October 2026.

### 2026-10-17, step 1 of the core rule kept for the digital twin, the testbed and the live system

Two tiers said of step 1: "Every candidate whose abstract claims use beyond simulation
(readiness level L2 to L5: a real shop's or system's data, a digital twin or hardware in the
loop, a physical testbed or shadow mode, or a live production system) is in the core,
whatever its venue or citations, once Osamah has confirmed the claim against its abstract.
Question 5 asks about exactly these studies, and they are few." This now reads: every
candidate whose abstract claims a run in a digital twin or with hardware in the loop, on a
physical testbed or in shadow mode, or in a live production system (levels L3 to L5) is in
the core, whatever its venue or citations, once Moayad AlNammi has confirmed the claim
against its abstract. For this step, a claim is confirmed only when the abstract reports a
run at one of these three levels, and not by a test on real data alone, which the amendment
of 15 October had let confirm any claim ("A run the abstract reports at any level from L2
to L5 confirms the claim"). A candidate whose abstract claims a test on a real shop's or
system's data alone (L2) has no place by this step and competes at steps 2 and 3 like any
other candidate. Question 5 reports the claims at every level from the map, the real-data
ones among them with Moayad's confirmations where he gave them, and reads in full the
studies of each level that the core holds. The cap on non-deep studies still binds at every
step.

The reason is the count, known after the map's vote and before any core study was selected
or read: of the 41 candidates whose abstract claims use beyond simulation, 37 claim a test
on real data and 4 a higher level (`runners/core_claims.py`). Step 1 as
written would have filled about two fifths of the core before coverage and the
proportional fill, while the premise that these studies are few holds only above real
data. Decided by Moayad AlNammi on 17 October 2026.

### 2026-10-17, the level of a claim at step 1 read by the person, and the full text where the abstract leaves it open

The amendment of 15 October 2026 says that the claims of step 1 are confirmed on a sheet
that "shows him the models' claim (the voted level, each model's level and quote) and asks
yes or no", and the amendment above that a candidate whose abstract claims a run at levels
L3 to L5 "is in the core, whatever its venue or citations, once Moayad AlNammi has confirmed
the claim against its abstract". Both now read as follows. For each claim on the sheet,
Moayad AlNammi answers from the abstract whether it reports a run beyond simulation, yes or
no, and where the level the abstract supports differs from the models' voted level, higher
or lower, he records that level. Step 1 takes the level he confirms: a candidate is in the
core when its claim is confirmed at L3 to L5, whatever level the models voted, and is not
when he confirms it at a test on real data alone. Where the abstract leaves open whether the
run reached L3 to L5, the full text settles the claim, and the answer is marked as read from
the full text (`read_from` in `datasets/core-claims.csv`). A yes confirms what the
abstract, or that full text, states; for the core's studies, Part B codes the level again
from the full text, as it codes every Part A axis. The map's readiness codes are not changed
by these answers: they remain the models' vote, coded from abstracts, and question 5 reports
the map's codes beside the levels confirmed. Only the claims on the sheet are read by a
person; a record the vote codes `none` is not.

The reason is two records seen while confirming, before any core study was selected or
read. Record 588's abstract reports a digital twin of the workshop, its geometric model
built by point-cloud reconstruction, which compares the physical and virtual workshops and
schedules within its closed loop, with results from a real-world workshop. One model coded
it `twin-or-hil`, one `real-data` and one `none`, so the vote, the highest level at least
two models reach, was `real-data`, and a yes on the models' claim could not give it the
level its abstract states. Record 399's abstract says that "relevant experiments are
executed in a prototype experiment platform", for an IoT-based system whose agents have a
physical layer, which leaves open whether the platform was physical equipment; the scheme
counts only a run on physical equipment as `testbed-or-shadow`. The models agree least on
these two levels (mean pairwise kappa 0.282 on `twin-or-hil` and 0.222 on
`testbed-or-shadow`, against 0.670 on `real-data`, in the map's agreement report,
`results/map/map-vote.md` once the map is released), so where a person's reading
of the level differs from the vote, the person's is taken. Decided by Moayad
AlNammi on 17 October 2026.

### 2026-10-18, record 74 coded by Moayad AlNammi instead of a top-up run

The amendment of 14 October 2026 says: "A record the validation sample carries forward is
coded afterwards in a top-up run, by the same three models with the same scheme and
settings, and its codes join the map before the map is analysed." The validation carried
one record forward, 74, on Moayad AlNammi's adjudication (amendment of 15 October 2026). It
is coded instead by Moayad AlNammi, from its title and abstract, on the fifteen axes of
Part A with the same scheme, and the scheme's rules that tie one axis to another are
applied to his codes. His codes enter the map as they stand, without a vote, and the record
stays out of the models' agreement, which is computed over the 532 records the models
coded. The map's report names the record and how it was coded. Leaving the record uncoded
would keep an included study out of the map and out of the core's candidates. Decided by Moayad
AlNammi on 18 October 2026.

Two sentences of earlier amendments, overtaken without being quoted, are named here. "The
map's codes and the answers of step 1 enter the codebase once the map is complete, after
its top-up run" (15 October, the three axes coded by Moayad AlNammi) now reads: once the
map is complete, with record 74 coded as above; the map was released into the codebase on
18 October 2026. "Osamah's blind coding of those three axes is unchanged" (15 October, the
claims of step 1 confirmed by Moayad AlNammi) stopped applying with the amendment of the
same day that gave the coding of those axes to Moayad AlNammi, on a random sample. One
correction to the second amendment of 17 October 2026: "the three other records on which
one model coded a level above the vote's" means the records on which one model coded a
level of L3 to L5 above a vote below L3; record 18, where one model coded
`testbed-or-shadow` above the vote's `twin-or-hil`, and the records where one model coded
`real-data` above a vote of `none` are not among them. Recorded on 18 October 2026.

### 2026-10-18, the venue bands as applied

Two tiers says: "Band 1 is a journal or proceedings series ranked Q1 or Q2 in the SCImago
Journal Rank, or a conference ranked A* or A by CORE, in the editions current at the
snapshot date; band 2 is every other venue. For ties, venues are ordered Q1 or A*, then Q2
or A, then Q3 or B, then the rest, the better of a venue's two ranks counting. Venues are
matched by ISSN, or by name where a record has none, and each name match is listed." This
now reads as follows. The lists are the SCImago Journal Rank for 2025 and ICORE2026, the
CORE ranking under its new name, the editions current at the snapshot date, downloaded on
18 October 2026. A source's SJR quartile is its best across its subject categories, as SJR
gives it. A venue is matched to SJR by the record's ISSN-L, among the ISSNs SJR lists for a
source; a record without an ISSN-L is not matched to SJR by name. A venue that SJR does not
place in band 1, and that may be a conference, is matched to ICORE by name, whether or not
the record has an ISSN, since ICORE lists none; only conferences ranked A* or A are
proposed, and a match counts once Moayad AlNammi has confirmed it. Every proposal is listed
with its answer (`results/core/venue-bands.md`; `datasets/venue-matches.csv`).
Either list can place a venue in band 1; a venue in neither, or with a quartile or rank
outside band 1, is in band 2. For ties, venues are ordered Q1 or A*, then Q2 or A, then Q3,
then the rest: a conference's ICORE rank below A is not looked up, so a conference ICORE
ranks B falls with the rest unless SJR gives its proceedings Q3.

The reason is cost and effect. ICORE lists no ISSN, so a conference can be matched only by
name, and each name match needs a person's answer. A rank below A cannot move a venue into
band 1, and the first run, which proposed matches at every rank, asked for 33 answers, most
of which could not change a band. Leaving the lower ranks unmatched changes only how band-2
venues are ordered among themselves, in the ties of steps 2 and 3. Decided by Moayad AlNammi
on 18 October 2026, before the core was selected.

### 2026-10-18, the research questions confirmed by Ahmed Azab

Open decisions, item 1, left confirmation of the five research questions
open at the approval. Dr. Ahmed Azab has confirmed the five research questions as this
protocol states them, in both forms (the working form and the form the paper states),
including the changes to his wording of questions 3.2, 3.3, 3.4 and 4; the questions are
final, and a change to them is an amendment like any other. Reported by Moayad AlNammi on
18 October 2026, before the core was selected or read; the date of the confirmation itself
is not recorded.

### 2026-10-18, the shares of step 3 fixed at 35, 35 and 30

The amendment of 14 October 2026 says of step 3: "the places are divided among three
strata, end to end, steering, and role not stated, in proportion to the map's records in
each (largest remainders), in place of the two roles; a stratum already over its share
takes no more, and places a stratum cannot fill pass to the others in proportion to their
shares." This now reads: the 100 places are divided as 35 end to end, 35 steering and 30
role not stated. The studies chosen at steps 1 and 2 count toward their stratum's share; a
stratum already over its share takes no more, and places a stratum cannot fill pass to the
others in proportion to their shares. The two roles thus take equal shares, where the map's
proportions would have given steering more places than end to end. Within a stratum,
venue band, publication year and citations decide as before. Decided by Moayad AlNammi on
18 October 2026, before the core was selected.

### 2026-10-18, band 1 narrowed to Q1 and A*

Two tiers says: "Band 1 is a journal or proceedings series ranked Q1 or Q2 in the SCImago
Journal Rank, or a conference ranked A* or A by CORE, in the editions current at the
snapshot date; band 2 is every other venue." This now reads: band 1 is a journal or
proceedings series whose best quartile in the SCImago Journal Rank is Q1, or a conference
ranked A* by ICORE; band 2 is every other venue, Q2 journals and conferences ranked A among
them. The lists, the matching and the order of ties are those of the amendment "the venue
bands as applied" of the same day: ties still order venues Q1 or A*, then Q2 or A, then Q3,
then the rest, and conferences ranked A* or A are still the ones looked up. A venue that SJR
ranks Q2 and that may be a conference is therefore now matched to ICORE by name, as a venue
in Q3 or in neither list already was. Each stratum of step 3 still holds more
band-1 candidates than its share of the 100 places; the core-selection runner
reports the counts. The reason is Moayad AlNammi's judgement that the most
selective venues raise the chance of finding rigorous studies among the places left
after the minimums. The rank orders places and judges no study: journal metrics are still
not used as a measure of any study's quality (Two tiers, Limitations), and each core study
is assessed for quality on its full text. Decided by Moayad AlNammi on 18 October 2026,
before the core was selected.

### 2026-10-19, records of one study, and the cap at step 3

Two tiers says: "Records sharing a DOI, an OpenAlex work or a normalised title count once:
the journal version is kept over a conference version, then the later version, then the
lower record number." This now reads: records sharing a DOI or an OpenAlex work count once,
and so do records sharing a normalised title whose first authors agree, as in the rule that
removed duplicates before screening (`configs/deduplicate.toml`); the journal
version is kept over any other, then the later version, then the lower record number. The
reason is two candidates seen while the selection runner was written, before the core was
selected: records 108 and 292 share a title but are different studies by different first
authors, and the rule as written would have counted them as one study and kept record 108
alone.

Precedence says: "The cap on non-deep studies binds at every step." At steps 1 and 2 a
non-deep candidate past the cap is passed over. At step 3 the cap is applied as follows: if
step 3 would take more non-deep studies than the cap leaves, those with the best citation
standing are kept (ties: the better venue, then the lower record number), and each of the
others gives its place to the next deep candidate of its stratum, band and publication
year, or, if that year has none left, to the deep candidate of its stratum with the best
standing, band 1 first; the shares among years are not computed again. Both decided by
Moayad AlNammi on 19 October 2026, before the core was selected.

The other readings the selection applies were accepted by Moayad AlNammi on 18 October
2026, with the fixed shares of step 3, and are recorded here so that the rule is stated in
one place:

- If step 1 and the minimums of step 2 hold more studies than the core has places, step 2 is
  run again with a minimum of two, then of one.
- At step 3, the places of the band where a stratum's last place falls are shared among
  publication years in proportion to that band's candidates not yet chosen in each year.
- The lock holds the SHA-256 of the core's records and their steps, with the records; a
  rerun that would change the core is refused.

The runner, `runners/core_selection.py`, also fixes three details the text leaves
open, confirmed by Moayad AlNammi on 19 October 2026, before the core was selected: a
stratum over its places is settled before one that cannot fill its own, so that
it takes none of the places the other leaves; equal remainders between strata go to the
stratum with more places, then to the stratum listed first (end to end, steering, role not
stated); and equal remainders between years go to the year with more candidates, then to
the earlier year.

No criterion on a venue's country is added. The country the SCImago Journal Rank gives each
venue is reported for the map (`results/core/venue-bands.md`) and for the core
against the rest of the map (`results/core/core-vs-map.csv`), and decides nothing.
Decided by Moayad AlNammi on 19 October 2026, after the venue bands showed 5 of the map's 
533 records in venues that SJR places in China, 2 of them in band 1, and before the core was selected.

Two sentences of Two tiers, overtaken by the amendment of 18 October 2026 that narrowed band
1 to Q1 or A*, are named here. "In the newest year, where most candidates have few or no
citations yet, the venue decides most places" (Venue and citations) and "the newest papers
compete on venue alone" (Limitations) no longer hold: band 1 is now a single venue tier, so
among its newest papers equal citations give equal standing, and the tie falls to the lower
record number, the order in which OpenAlex returned the works to the search. The selection's
report counts the places this decides by applying the rule's steps again with the record
numbers mirrored (`results/core/core-selection.md`, Ties settled by the record
number), and the paper states it among the limitations. The rule is unchanged. Recorded on
19 October 2026, after the core was selected.

### 2026-10-21, the core coded and checked without a person

Data extraction says of Part B: "Coder and date are recorded per row; a second coder codes
the same seeded random fifth of the core as the quality assessment, and agreement is
reported." This now reads: the core is coded from its full texts by a coding agent,
Qwen3.8-27B (revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0, reasoning effort medium),
working through the project's tools and served by the project, so that no full text of the
core goes to a model's provider. Every answer is checked by code
(each quote verbatim on the page it cites, each code in its question's list, the rules
between questions, every question answered), during the run and again over the finished
responses (`runners/core_check.py`). Every answer is then read against the paper by
a judge, Muse Glimmer 30B (revision a4e59da52a7bc87ae7251dd5545c0dd437c44b68, reasoning
strength medium), a model of another family, which returns supported, partly, not supported
or cannot judge, with a proposed answer when it disputes one; its verdicts are reported and
never applied. The coding model, its revision and the date are recorded per row, with the
judge's verdict beside each answer, and the agreement of coder and judge is reported per
question. No person checks the answers, and the paper states this among its limitations.
The fifth drawn on 20 October 2026 for a person's check (`results/core-coding/draws.md`:
20 studies stratified by the core's strata, seed 20261020) is kept and not used; a person
check of it could be added later only by its own amendment. The published dataset holds the
answers, the codes, the page numbers and a SHA-256 of each quote, and no quote text.

Quality assessment says: "One coder assesses every core study; a second coder assesses a
seeded random fifth of the core independently, and their agreement is reported." This now
reads: the coding agent scores every core study on the seven items, each score as Part B's
section Q defines it (`datasets/coding-scheme.md`), and the judge reads every score
against the paper; the agreement of coder and judge is reported per item.

Synthesis says: "Four sensitivity analyses, fixed now: the core's conclusions with the
lowest-quality studies removed; [...]". This now reads, for the first: the lowest-quality
studies are the fifth of the core with the lowest mean score over their assessable items,
the studies tied at the cut kept in. A fifth analysis is added: the core's conclusions with
the answers the judge disputed (partly or not supported) left out.

Part B of the coding scheme was revised after Qwen3.8-27B coded a pilot of five
studies, and frozen on 21 October 2026, before the full run. The checker's fingerprint over the frozen
files is recorded with every response.

The reasons. The extraction's reliability rests on the checks by code on every
answer and the judge's reading of every answer. Rules the pilot left open were
stated more precisely in Part B before the freeze. Decided by Moayad AlNammi on
21 October 2026, before the core was coded.

### 2026-10-22, answers corrected by the authors

The amendment of 21 October 2026 says that no person checks the answers and that the judge's
verdicts are reported and never applied. This stands, with one addition: where an answer contradicts 
Part B's own rule, as the judge's reading shows, or a claim was confirmed at step 1 of the core 
rule, the authors read that answer against the paper. Where they find it wrong under Part B,
they correct it, together with every answer that follows from it by Part B's conditions and
rules between questions. Each correction is recorded in `datasets/core-corrections.csv`
(the study, the question, the authors' value, the pages read, who decided and when, and the
reason in the authors' words, with no quote). The gather lays the corrections over the
coding agent's answers, refuses a set that leaves the study's answers breaking Part B's
conditions or rules, and keeps the coder's value and the judge's verdict beside each
corrected answer. The tables take the authors' value; the agreement of coder and judge is 
computed on the coder's value; and in the sensitivity analysis without the judge's disputes, 
a corrected answer stands. Where the authors agree with the coder, nothing is corrected. 
This is no check of the core: only the answers so brought to the authors' attention are read, 
and the paper says which and how many.

The reasons. Under the frozen scheme, a few codes are wrong on its own terms, as the judge's 
reading cited the rule; leaving a known error in the published dataset would misfile a study 
between Sections 5 and 6. The first corrections, each with its scheduling action, sub-decision, 
steering action and steered method following: record 191, whose learned policy chooses the 
machine of each operation inside NSGA-III, is end to end by Part A's rule on mixed roles; and 
record 530, whose learned policy picks which operation of a complete schedule to move and where, 
is end to end by the rule's clause on changing a complete schedule (22 October 2026). Read the 
same day and kept as coded: record 315's readiness and record 504's role. Decided by Moayad AlNammi 
on 22 October 2026.

### 2026-10-22, the tests of question 3.4

Question 3.4 asks, of the studies that make the same claim, whether the evidence behind it is
comparable across them: "the same instances, baselines, metrics and time limits". The
protocol did not say how this is read from the coded answers. It is read so, for each of the
six recurring claims Part B codes (D19) and each core study making it, every test reported as
a share of the studies making the claim:

- Instances: the study shares a named benchmark set (D01) with another study making the
  claim. A set coded as another named set (`other-benchmark`) or as none names no one set,
  so it is shared with no study.
- Metrics: the study shares an objective (A10) and a headline statistic (D13: a mean, the
  best, a median, or a single run) with another study making the claim. A statistic coded as
  another statistic names no one statistic.
- Baselines and time limits: every baseline the study compares with (D07) was rerun by its
  authors on their own instances, and no baseline's time limit is left unstated (a
  dispatching rule, or a policy that builds its schedule in one pass, needs none). That the
  studies compare with the same baselines is not tested: a baseline's name is free text, and
  its kind is the claim's own.
- All of the question's terms: the study and one other study making the claim share a named
  benchmark set, an objective and a headline statistic, and both meet the test of baselines
  and time limits.
- Training runs: the study reports results over several training runs with their spread
  (D14, D15), the evidence question 3.3 asks for, kept here because a result from a single
  run cannot be set beside another study's.

The tests of instances, of baselines and time limits and of training runs were fixed in the
synthesis runner on 21 October 2026, while the core was being coded and before any result
was seen (`runners/core_synthesis.py`); the test of instances left out a code
that does not exist in place of `other-benchmark` until 22 October 2026, when the fault
was found and fixed. The tests of
metrics and of all the question's terms together were added on 22 October 2026, after the
results were seen, so that every term the question names is tested; the paper says so.
Decided by Moayad AlNammi on 22 October 2026.

### 2026-10-22, the second sensitivity analysis as read

Synthesis names, among its sensitivity analyses, "the core's conclusions using only the codes
its full texts confirm". This now reads: how far the map's codes, given from the titles and
abstracts, hold in the core's full texts, axis by axis and code by code: for each axis, the
core studies whose abstract's code the full text gives, those whose abstract said not stated
where the full text gives a code, and Cohen's kappa; for each code, the studies holding it in
the abstract and in the full text, and the kappa of its presence
(`results/core-synthesis/abstract-vs-full-text.md`, written by
`runners/core_synthesis.py`). The analysis was planned when the core's conclusions
could rest in part on the map's codes; once every core study was coded from its full text
(Part B, which codes Part A's fifteen axes again), the core's conclusions rest on the full
texts' codes alone, so a recomputation as first worded would repeat them, and what the
analysis can still test is how far the map, on which question 1 and every field-wide count
rest, is borne out where a study was read in full. The comparison was written into the
synthesis runner on 21 October 2026, before any result was seen; this amendment records it
after the results. Decided by Moayad AlNammi on 22 October 2026.

### 2026-10-22, a reference corrected in the tests of question 3.4

The amendment "the tests of question 3.4" reads, under Metrics, "the study shares an
objective (A10)". This now reads "an objective (A11)": in Part B, A10 is the dynamic events
and A11 the objective (`configs/core-coding.toml`). The test reads the objective by
its name, so no result changes. Recorded on 22 October 2026 by Moayad AlNammi.

### 2026-10-24, a person's check of six questions on the fifth

The amendment of 21 October 2026, "the core coded and checked without a person", says: "No
person checks the answers, and the paper states this among its limitations. The fifth drawn
on 20 October 2026 for a person's check [...] is kept and not used; a person check of it
could be added later only by its own amendment." This is that amendment. It now reads: on
the 20 studies of the fifth (`results/core-coding/draws.csv`, draw `fifth`), Osamah
H. Hussein codes six questions from the full texts, blind to every model's answer and verdict:

- A01 `policy_role`: `end-to-end`, `steering-rules`, `steering-heuristic` or `not-stated`;
- B07 `algorithm`: the algorithm that trains the policy A01 codes, in B07's codes, compared
  also by its family as the coding scheme derives it;
- F01 `readiness_level`: `L1` to `L5`;
- D14 `seeds`: the number of training runs behind the reported results, or `not-reported`,
  compared also by its bin (`1`, more than 1, `not-reported`);
- D07, reduced to one answer: every baseline rerun by the authors on their own instances
  (`yes`), at least one copied or not stated (`no`), or no baseline (`none`);
- E01, reduced to one answer: whether the paper tests the trained policy on instances unlike
  those it was trained on, as E01 defines such a test (`yes` or `no`).

Each question carries its definition and codes from Part B of the coding scheme
(`datasets/coding-scheme.md`), shown on the page the person answers on, which holds
no model answer. The coding agent's answers are reduced the same way: D07 `yes` when every
baseline group's `run` is `rerun`, `none` when D07 is 0 or `not-stated`, otherwise `no`; E01
`yes` when its count is 1 or more. Reported per question: the share of the 20 studies on
which the person and the coding agent agree, and Cohen's kappa where both give more than one
code; and each disagreement, with both answers. The person's answers replace none of the
coding agent's: the synthesis counts the agent's answers as before, and the agreement is
reported in the paper's method and limitations.

The reasons. On 21 October 2026 the coding left no time for a person to read the
answers, and the paper was to state that among its limitations. The work then
moved ahead of that schedule, and time was available for six questions on the 20
studies of the fifth. Those questions are the ones the main findings rest on: the 
filing by role and algorithm, readiness, training runs, baselines and transfer. 
The questions, the sample, the reductions and the measures are fixed here before 
the page is written or opened. Decided by Moayad AlNammi on 24 October 2026.
