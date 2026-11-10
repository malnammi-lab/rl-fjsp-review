# Coding scheme

This file fixes the categories of the review's two codings before any study is coded:

- **Part A, the map:** every included record, coded from its title and abstract by the
  three screening models in a second pass. `configs/map.toml` lists the axes and codes; the
  acquisition tool's coding task sends Part A, as it stands below, to the models, and
  refuses any reply off the codes.
- **Part B, the core:** the studies read in full, coded from their full texts.

The categories are not changed to fit the data. Once the map's coding has begun, a category
found wrong is fixed by a dated amendment at the bottom of this file, never in place,
because every study coded before the change would then have been coded against a rule that
no longer exists.

Revised on 14 October 2026, before any study was coded. Revised again on 14 October 2026,
after the pilot on the calibration batch, in wording only. No code was added or removed.

## Part A, the map

Code the paper on the fifteen axes below, from its title and abstract only.

- **The paper's own method.** Code the method the paper proposes, not its baselines or the
  related work it mentions; when it proposes several, the one the abstract presents as its
  main contribution, or whose results it headlines.
- **The learner's axes describe the agent.** `learner_depth`, `deep_architecture`,
  `training_algorithm_family`, `state_content` and `state_encoding` describe the
  reinforcement learning component, the agent (see `coordination`). In a steering study
  they describe the agent that steers, never the rules, heuristic or metaheuristic it
  steers, which `policy_role` and `hybridization` record.
- **Only what the record states.** When the title and abstract do not say what an axis
  asks, choose `not-stated`; do not infer it from what such papers usually do. The rules
  below give an axis's default where it has one, and the names that fix their content (a
  Q-table has discrete states; a disjunctive graph is made of operations).
- **What the paper models, not what it mentions.** Code an event, a constraint, an
  objective or a domain only when the paper's problem has it or its experiments use it, not
  when it is named as motivation, as a limit of earlier methods, or as something the method
  could handle.
- **One code or a list.** An axis marked "one code" takes exactly one; an axis marked "a
  list" takes every code that applies, and a code marked "alone" is never combined with
  another.
- **Quotes.** For `policy_role`, `learner_depth` and `readiness_claim`, quote verbatim one
  continuous span of the title or abstract that shows the code you chose, never two spans
  joined with "..."; `not-stated`, and `none` on `readiness_claim`, need no quote.

### `policy_role` (one code, quoted)

What does the learned policy decide? The role follows what one action of the policy
chooses, not the paper's name for it: operations, jobs, machines or the schedule make it end
to end; a dispatching rule, an operator, a neighborhood, a parameter or an acceptance
decision make it steering. Only statements about the paper's own policy count: the
problem's decisions ("job sequencing and machine selection"), rules named as baselines,
what earlier methods lack, and the words "heuristic-assisted" or "heuristic-guided" alone
do not.

- `end-to-end`: the policy's own outputs are the scheduling decisions. It builds the
  schedule step by step, choosing an operation (or the job whose next operation is
  processed), a machine, or both; outputs the whole schedule in one pass (every operation's
  priority or machine, decoded without a search); or changes a complete schedule, choosing
  which operations to move and where. Code it also when the abstract calls the method end to
  end, or says the policy builds, constructs or generates the schedule. It stays end to end
  when a rule only masks or restricts its choices, nominates its candidates, or completes
  its decision (the machine chosen by a rule), and when the paper calls it a learned
  dispatching rule that picks the operation or machine itself.
- `steering-rules`: the policy chooses or switches among predefined dispatching rules, or
  sets the weights or parameters of a rule or of a weighted combination of rules, and the
  rule decides. Actions designed from, based on or inspired by dispatching rules are rules.
  Such rules may be called composite, compound, combined, comprehensive or hybrid scheduling
  rules, priority rules (PDR, SDR), a rule base, scheduling behaviors, or simple
  constructive heuristics that pick the next job. Decide by what one action indexes: one
  output per rule is steering, one per job, operation or machine is end to end.
- `steering-heuristic`: the policy controls a heuristic or metaheuristic that builds or
  improves the schedule: it sets a parameter, chooses an operator or neighborhood that the
  heuristic then applies, or makes an acceptance decision, as in tuning a genetic algorithm
  or simulated annealing. Also when a heuristic or metaheuristic builds the schedule and the
  policy decides an auxiliary part beside it, such as how lots are split into sublots.
- `not-stated`: the abstract says only that reinforcement learning, an algorithm or a
  network solves, addresses, tackles or optimizes the problem, or that actions were
  designed, without saying what an action chooses or naming the rules, heuristic or
  parameters it chooses or sets.
- Mixed roles: `end-to-end` if any learned policy chooses operations or machines itself;
  with mixed steering kinds, `steering-heuristic` if a metaheuristic is in the procedure,
  else `steering-rules`. A higher-level policy that sets a goal, an objective or a reward
  for a lower one takes the role of the level that acts on the shop.

### `coordination` (a list)

How many learned decision-makers act, and how are they organized? The default is
`single-agent`: the abstract names one learned method and no second decision-maker. An
agent is anything learned by reinforcement learning that observes the shop and chooses its own actions: a
policy, or a value function whose values pick the action, as a deep Q-network's do. Count
what decides, whatever the paper calls it (agent, policy, actor, sub-policy, Q-network,
controller).

- Not agents: a critic or value network that only trains a separate policy; a network that
  only encodes the state; target or copy networks; the rules, heuristics or metaheuristics
  an agent chooses or steers; the simulator. One learner whose action has several parts
  (heads, tables or parameters) chosen from one state and updated on one reward is one
  agent, such as double Q-learning's two tables or one Q-table per parameter of a genetic
  algorithm. Two networks named without saying that each chooses actions are not two agents.
- `single-agent`: one learned method, policy, network or agent makes every decision,
  whether or not the abstract says agent; so do a multi-agent problem (jobs or machines as
  agents) solved by one learner, one network called in turn for whichever machine needs a
  decision, and a portfolio of policies that each build a whole schedule. Alone.
- `multi-agent`: two or more agents each choose their own actions: one per machine, per job
  or per objective, or one choosing the operation and another the machine. Copies of one
  shared network count when each acts on its own local observation. Code it when the
  abstract says several agents learn or decide, or names a multi-agent method (MARL,
  collaborative or cooperative agents, QMIX, QTRAN, VDN, MADDPG, MAPPO).
- `hierarchical`: agents in levels, a higher one whose action is a goal, a sub-goal, an
  option, an objective, or which lower agent acts. Separate networks per level (controller
  and actuator, manager and worker, meta-controller) are `hierarchical` and `multi-agent`,
  even when the paper says "a single agent"; one network whose decisions are organized in
  levels is `hierarchical` alone. Agents that split one decision in turn (an operation
  agent, then a machine agent), and levels named only by their objectives, are
  `multi-agent` alone.
- `not-stated`: no learned decision-maker is described.

### `scheduling_action` (one code)

For an end-to-end policy, what does one action choose? For a policy in levels, code the
level that chooses operations or machines.

- `operation`: the next operation, or the job whose next operation is processed
  (sequencing, dispatching, job selection); its machine is set by a rule or is fixed.
- `machine`: a machine for an operation a rule has already chosen (routing, assignment),
  including a job agent that picks a machine for its own next operation, or waits.
- `operation-machine-pair`: an operation and its machine in one action: a job with a
  machine, a 3-tuple of job, operation and machine, a pair with a transporter or worker,
  several pairs at one decision, or two agents choosing the operation and the machine
  between them ("one action space for both subproblems", "a sub-action pair").
- `whole-schedule`: the abstract says one output gives the whole schedule at once, such as
  every operation's priority or machine; "generates schedules" alone is `not-stated`.
- `schedule-change`: an action changes a complete schedule, moving an operation to another
  machine or position, or swapping two. A "rescheduling point" is a decision point, not a
  change.
- `other`: an end-to-end action that chooses neither an operation nor a machine and that a
  fixed rule completes: whether to schedule now or wait, or which factory or line a job
  goes to.
- `not-applicable`: the policy is steering (`steering-rules` or `steering-heuristic`).
- `not-stated`: the policy is end to end but the action is not stated, or `policy_role` is
  `not-stated`.

### `learner_depth` (one code, quoted)

What kind of learner represents the policy or value function? Decide by the sentence that
introduces the paper's method, not by sentences about other work. A `tabular` or
`non-neural` learner is `not-applicable` on `deep_architecture`, and a `not-stated` one is
`not-stated` there.

- `deep`: a neural network of any kind, however shallow, including deep reinforcement
  learning and graph neural networks. Algorithms that are neural by construction are `deep`
  without the word: DQN and its variants (double, dueling, D3QN, Rainbow), PPO, TRPO, A2C,
  A3C, DDPG, TD3, SAC, QMIX, QTRAN, VDN, MADDPG and MAPPO. The list is closed: "policy
  gradient" or "actor-critic" with no network and no listed algorithm is `not-stated`.
- `non-neural`: a linear function or another approximator that is not a neural network.
- `tabular`: a table of stored values. Q-learning, SARSA, double Q-learning or a Q-table
  with no network or approximator named is `tabular`.

### `deep_architecture` (a list)

For a deep learner, which architectures map the state to actions or values? Code only
those the abstract names. A network that combines families takes a code for each, but
heads, decoders, critics and embedding layers behind a named encoder add none.

- `fully-connected`: a multilayer perceptron (dense or feed-forward layers) that is itself
  the network from state to action or value.
- `convolutional`: a convolutional network (CNN), in one dimension or two.
- `recurrent`: a recurrent network (RNN, LSTM, GRU).
- `graph-neural-network`: GNN, GCN, GAT, GATv2, GIN, GaAN, HGNN, HAN, HGT, graph
  convolution, message passing, a graph encoder, and dual attention networks over
  operations and machines (DAN, DANIEL, DDAN). Attention inside message passing over a
  graph's edges is this code alone, whatever the network is called. A graph that only
  organizes agents, or yields hand-made features, is not one.
- `attention-transformer`: self-attention or a Transformer as a block of its own over items
  or tokens, including fusion or readout. A graph transformer (a Transformer over all of a
  graph's nodes) is this and `graph-neural-network`; a vision transformer is this, its
  image-like input `matrix` on `state_encoding`.
- `pointer-network`: a pointer network, or an attention decoder that points to items of its
  input. Attention that only points is this code alone; a self-attention encoder with a
  pointing decoder (as in Kool and colleagues) is this and `attention-transformer`. An MLP
  that scores each candidate before a softmax is not one.
- `other`: another named architecture, such as a capsule network or a mixture of experts
  (its gate over experts is not attention).
- In a GAN-style method, code the generator (the policy), never the discriminator; a reward
  predictor's network never counts.
- `not-stated`: a deep learner whose architecture is not named ("deep Q-network", "deep
  reinforcement learning" or "a deep neural network" alone names none), or a learner that
  is `not-stated`.
- `not-applicable`: the learner is `tabular` or `non-neural`. Alone.

### `training_algorithm_family` (a list)

The families of the reinforcement learning updates the paper's own agents are trained
with, for example two agents trained differently; not the method they build or steer. A
named algorithm decides its family, whatever the authors call it. A hybrid is recorded on
`hybridization`: a policy-gradient agent steering a genetic algorithm is `policy-gradient`
here and `metaheuristic` there.

- `value-based`: Q-learning, SARSA, deep Q-networks and their variants (double, dueling,
  prioritized, D3QN, Rainbow), TD(lambda), state-value or afterstate learning, approximate
  dynamic programming, and multi-agent value factorization (QMIX, QTRAN, VDN, WQMIX), even
  when the paper calls its mixing network a critic.
- `policy-gradient`: REINFORCE (with or without a learned baseline), PPO (PPO2, PPO-clip,
  masked PPO), TRPO, and their multi-agent forms (MAPPO, IPPO). PPO and TRPO are this code
  alone, although they also train a critic.
- `actor-critic`: A2C, A3C, DDPG (deep deterministic policy gradient), TD3, SAC, MADDPG, and
  other methods the abstract calls actor-critic, except PPO and TRPO.
- `other`: offline reinforcement learning (from a fixed logged dataset, with no
  interaction), model-based, safe or meta-learning reinforcement learning, coded together
  with the family of the algorithm it wraps (meta-learning around PPO is `other` and
  `policy-gradient`), and any other update. "Offline learning" meaning
  training before deployment, batch updates or PPO's old policy is not offline.
- `not-stated`: no algorithm named.

### `hybridization` (one code)

Does the agent share one procedure with a method that is not reinforcement learning: an
optimization method, or a learner of another kind? A second reinforcement learning agent
is recorded on `coordination`, not here. Code this axis whatever the role.

Never a hybrid: the agent's own parts (networks, simulator, masking, reward, the decoder of
its outputs); rules that restrict or complete its decisions (a machine or vehicle chosen by
a rule, a rule that filters its candidates); the rules a steering agent chooses among;
heuristic value initialization, reward shaping or guided exploration ("heuristic-guided",
"heuristic-assisted"); rule-based rescheduling; tuning of its hyperparameters, reward
weights or state features, by any method (Bayesian optimization, grid search or a genetic
algorithm); training instances or a static dataset made
before training; a solver that only labels validation instances or validates a model;
"hybrid" said of a reinforcement learning algorithm or of a metric; a baseline.

- `none`: no non-RL method named in the procedure. The default.
- `metaheuristic`: a metaheuristic or local search (genetic algorithm, simulated annealing,
  tabu search, variable neighborhood search, particle swarm or another) that the policy
  tunes or steers, that improves the policy's schedule, that generates the agent's training
  states inside its learning loop, or that evolves the rules the agent chooses among
  (genetic programming).
- `exact`: an exact solver (mathematical or constraint programming, branch and bound) that
  completes, repairs or optimizes part of the agent's schedule, or solves a subproblem the
  agent chooses.
- `other-learner`: a learner that is not reinforcement learning, used by the agent or in
  its training: imitation or behavior cloning, as pretraining or in its loss, adversarial
  imitation (GAIL) included, from expert, solver or rule schedules (a solver that only
  provides them is not `exact`); a reward or value model learned from preferences,
  demonstrations or labels (preference-based or inverse reinforcement learning, RLHF);
  supervised pretraining or a warm start from heuristic schedules; a supervised predictor
  whose outputs the agent uses; a language or pretrained model that proposes actions or
  gives embeddings. Transfer or meta-learning of the agent itself is not a hybrid.
- When several apply, the one the abstract gives the larger part; if that cannot be told,
  `metaheuristic`, then `exact`, then `other-learner`.

### `state_content` (a list)

What does the state of the policy describe? Code each kind of information the abstract
says it includes, whatever its encoding, and only what the acting policy observes, not what
a training-time critic alone sees. A named structure states its node kinds: a disjunctive
graph states `operations`, machine nodes `machines`. "State features" alone state nothing.
A feature belongs to the entity it describes, even when the paper lists it with another.

- `operations`: per-operation information: processing times, eligible machines,
  precedence, status, or the partial schedule (each operation's machine and position).
- `jobs`: per-job information: remaining operations or work, due dates, priorities or
  arrival times.
- `machines`: values given per machine: each machine's availability, load, utilization or
  queue.
- `shop-aggregate`: a statistic over jobs, operations or machines (mean, standard deviation,
  minimum, maximum, sum, range or rate), or over a line, cell or factory, whatever the
  authors call it; indicators of the shop or of the schedule so far, such as the completion
  rate or the current makespan; instance size descriptors.
- `events`: information about dynamic events: breakdowns, repairs, new arrivals, the
  arrival rate. An event type used only to select the action set is not content.
- `other-resources`: transporters, workers, energy (consumption, power, prices, tariffs) or
  other resources beyond the machines; added beside `shop-aggregate` when a statistic
  concerns them.
- `search-state`: for an agent that steers a heuristic or metaheuristic, or repairs a
  complete schedule, the state of its search: current parameters, such as the temperature
  or the mutation rate, and progress, such as recent improvement or population diversity.
- `other`: other information.
- `not-stated`: the abstract does not say what the state includes.

### `state_encoding` (a list)

How does the agent's network read the state? Code each structure it reads: a disjunctive
graph read with a global feature vector is `disjunctive-graph` and `feature-vector`. When
the abstract gives only the authors' word, code that word: a set of item vectors (one per
operation, job or machine) is `set`, a feature set `feature-vector`. Code the input, not
what the network computes from it: node embeddings that the agent's network computes belong
to `deep_architecture`, while ready-made embeddings from a separate model are input (one for
the shop is `feature-vector`, one per item `set` or `sequence`). Features on a graph's nodes
and edges add no code. A graph counts only when the network reads its nodes and edges, not
when it only models the environment, organizes agents or yields hand-made features.

- `discrete-states`: a tabular learner's state, a row of its table, often indicators cut
  into levels; code it for every `tabular` learner, even when the abstract does not
  describe the state. Categorical features read by a network are `feature-vector`. Alone.
- `feature-vector`: one fixed-length vector read whole: hand-designed indicators of the
  shop, or per-item features in fixed slots, flattened; "state features", with or without a
  number, or a feature set, list or tuple, when no graph or image is named; tokens that are
  features rather than items of the shop.
- `sequence`: items of the shop read in order, by a recurrent network or with positions.
- `set`: items of the shop, each with its features, read one by one by a shared network
  (scored as candidates, or read by attention without positions), even when stored as a
  matrix or sorted to keep the first k; node features given to attention with no edges.
- `matrix`: a grid read as a grid, by a convolutional network or as image channels: a
  processing-time matrix, a Gantt chart, a "dual-channel" input.
- `disjunctive-graph`: operation nodes (with a dummy start and end), conjunctive arcs for
  each job's precedence, and disjunctive edges between operations that can share a machine.
  A graph the abstract calls a disjunctive graph is this code unless it says the
  disjunctive edges were removed or replaced.
- `heterogeneous-graph`: nodes of two or more kinds, such as operations and machines, with
  edges between the kinds. The operation-machine graph (precedence arcs and
  operation-machine arcs, no disjunctive edges) is this code alone, whatever the authors
  call it; a graph called heterogeneous, improved, or extended with machine nodes adds
  `disjunctive-graph` only when the abstract says the disjunctive edges remain.
- `other-graph`: another graph of one node kind (machines, a hypergraph, operation-machine
  pairs as nodes), or an operation graph and a machine graph read side by side with no
  edges between them and no disjunctive edges (dual attention networks).
- `text`: the state written as text for a language model; its tokens are words, not items
  of the shop, so it is not also `sequence`.
- `other`: another structure that is not a graph.
- `not-stated`: the abstract does not describe the state.

### `dynamic_events` (a list)

Which unplanned events does the shop face during scheduling? "Dynamic", "real-time",
"online", "uncertain" or "disrupted" count only when they describe the problem: jobs
arrive, machines fail or data change during scheduling. Said of the method's speed, its
parameters or population, its graph or state, an iterative repair search, or its fitness
for real-time use, they do not, and a static problem described so is `none`. Nor does a
sentence of motivation that production in general is uncertain or complex.

- `none`: a static shop: every job and its data are known at the start. Code it when the
  abstract names no event and does not call the problem dynamic. Release dates known in
  advance, and parameters that differ between test scenarios, are not events. Alone.
- `job-arrivals`: new jobs arrive or are inserted during scheduling, including urgent or
  random orders.
- `machine-breakdowns`: machines fail or become unavailable without notice (breakdowns,
  breaks, failures, faults, outages, downtime).
- `uncertain-processing-times`: processing times vary or are random.
- `other`: another event, such as a transporter's breakdown, a fluctuating energy supply or
  price, an order's cancellation or change, a due-date change, an added machine, or a
  worker's absence.
- `not-stated`: the problem is called dynamic, but no event is named.

### `objective` (a list)

What does the schedule optimize? Code the measures the abstract says the method minimizes,
optimizes or reports results on. Not coded: a measure named only as the aim of a reward or
surrogate, as one the method could support, as the classical problem's, or as a general
benefit, and quality words with no measure (efficiency, performance, solution quality,
optimality, gap, productivity, convergence, reward, success rate). A composite index is
coded by the measures it combines, when named. Two or more codes mark a multi-objective
study, which has no code of its own.

- `makespan`: the maximum completion time; also completion time without total, mean, sum
  or weighted ("minimize job completion times" is `makespan`), production time, schedule
  length, or total duration.
- `tardiness`: tardiness or lateness (total, mean, maximum or weighted); earliness and
  tardiness, also as a weighted cost or penalty; the number or rate of tardy, delayed or
  overdue jobs; delay time; another due-date measure.
- `flow-time`: flow time, or completion time that is total, mean, summed or weighted,
  including waiting or response time.
- `workload`: the processing assigned to machines, robots or workers: total, maximum
  (critical) or balanced, including a min-max load that the paper calls utilization.
- `utilization`: machine utilization or idle time; the utilization of vehicles or workers is
  `other`.
- `energy`: energy consumption, power cost, peak power demand or carbon emissions.
- `cost`: production, processing or operating cost other than energy's, and profit or
  revenue.
- `robustness`: the robustness or stability of the schedule, such as its deviation from the
  original schedule after a disruption.
- `other`: another objective, such as throughput, work in process or transport distance.
- `not-stated`: no objective named.

### `constraints` (a list)

Which constraints beyond the flexible job shop's own does the problem add? Priority classes
and job weights are not constraints.

- `none`: the abstract names the problem (flexible job shop, dynamic flexible job shop, job
  shop) and none of the constraints below, even with a phrase such as "complex
  constraints". Alone.
- `transport`: transport or travel times between machines, stations or zones, of jobs,
  machines or workers, with or without transporters (guided vehicles, robots, cranes).
- `setup-times`: setup times, sequence-dependent or not.
- `workers`: workers, operators or robots needed to run, tend or load the machines, as a
  limited resource (dual-resource shops); a robot that moves jobs is `transport`.
- `energy`: a limit on, or a model of, the energy supply: an energy cap, time-of-use or
  demand-response prices, peak demand, renewable generation, storage or grid purchase.
  Minimizing energy without one is the objective `energy` only.
- `distributed`: several factories, plants or production lines, each scheduled as a shop of
  its own, with jobs assigned among them; not one factory divided into zones or cells.
- `other`: such as limited buffers, maintenance or machine-availability windows, release
  times, assembly or other precedence with several predecessors, batch processing, lot
  streaming, alternative process plans or routes, or workstations.
- `not-stated`: the abstract does not describe the problem well enough to tell.

### `instances` (a list)

On which instances is the method tested? Training-only instances are not coded.

- `public-benchmark`: a named benchmark (Brandimarte or mk; Hurink's edata, rdata, vdata or
  la; Dauzère-Pérès and Paulli or DP; Kacem; Barnes; Behnke and Geiger; Fattahi; the job
  shop sets of Taillard, Lawrence, Fisher and Thompson, Demirkol or the OR-Library), or
  instances the abstract calls benchmark, standard, classic, well-known or public, unless
  it calls them its own or generated. "Benchmarked against" names no instances.
- `generated`: randomly generated, synthetic, simulated or random instances, or instances
  defined by sizes, parameters or production configurations, including those generated
  from a real system's parameters; "simulation results" with no named benchmark or company
  data.
- `industrial`: the abstract says the instances are a real company's, factory's or system's
  data (actual, historical, collected or provided production data, logs or orders). "Case
  study", "practical case", "industrial example", "real-world" or "realistic" alone is not
  enough.
- A public benchmark extended with generated attributes (due dates, arrival or release
  times, energy or transport data, perturbed times) is `public-benchmark` and `generated`.
- `not-stated`: the abstract does not say.

### `domain` (a list)

In which application domains is the flexible job shop scheduled? Code every domain the
method is applied to or evaluated in.

- `manufacturing`: a factory, a workshop or production, including process industries
  (chemical, steel, furnaces, semiconductors) and industries within production
  (automotive, rail, aerospace, shipbuilding); cloud, edge, IoT or digital-twin
  infrastructure, cloud manufacturing and Industry 4.0 as enablers of a shop. The default:
  code it when the abstract names no domain, and not when it names only another one.
- `computing-networks`: the jobs scheduled are computing tasks or network traffic, in
  cloud, edge or fog computing, data centers or communication networks.
- `other`: another named domain outside production, such as healthcare, logistics or space
  operations.

### `readiness_claim` (one code, quoted unless `none`)

The furthest use beyond simulation the abstract claims: the highest level at which it
reports a run. Suitability or potential ("can be applied to", "feasible for deployment",
"suited for real-time industrial environments", "practical value", the "real
implementation" of a trained policy), "real-time", "data-driven", "online" or "smart
factory" wording, and Sim2Real experiments run in simulation claim no level.

- `none`: simulation only, on benchmark or generated instances, including when the abstract
  does not say where the method was tested (level L1). The default.
- `real-data`: tested offline on a real company's, factory's or system's data, by the test
  of `industrial` on `instances` (L2); a paper coded `industrial` there is at least this.
- `twin-or-hil`: the policy ran inside a digital twin of a named physical system, or with
  hardware in the loop (L3). A simulator, simulation software, a "digital factory", a
  "parallel" or "artificial" system, or a twin named only as an architecture or a source of
  data is `none`.
- `testbed-or-shadow`: the policy ran on physical equipment, or in shadow mode beside a live
  shop (L4); a modeled shop called a testbed is `none`.
- `live-system`: the policy ran inside a live production or manufacturing execution system
  (L5).

## Part B, the core

Fixed before the core's full texts are coded. Written on 20 October 2026, before any full
text was coded, from the protocol's Part B list, its quality instrument, and the synthesis
matrix. Revised the same day after a desk check of record 184: five rules made sharper
(C04, C06, C14, D07, E01) and one code added (`priority-filter` on C06). Revised again the
same day, after the coding agent's trial run on record 184: the rule for repeated items
now says that a count and its item blocks are quoted like any other answer. Revised again
the same day, after the pilot of five: the coding agent and the judge are given Part A's
rules with "the paper" in place of "the title and abstract" (and of "the abstract" and
"the record"), and with section A's rule on quotes in place of Part A's, as section A's
rule says to read them (`runners/core_check.py`, `full_text_reading`); some answers of
section A had been searched for in the abstract only. Revised again on 21 October 2026,
where the pilot's codes split on an open rule: each quality item now gives its scale;
E01, E02 and D11 say what holds for a policy trained on the instance it solves, or whose
training the paper does not state; section A, B04 and B05 place the quantities a policy
sets beside a fixed rule that builds the schedule; B03 and B07 say which policy they ask
about; and the evidence rule names the scores that need no quote. Frozen on 21 October
2026, before the full run, which codes the pilot's papers again under it, so no study
keeps a code given under a rule that has since changed; after that, a change is a dated
amendment at the bottom of this file. `configs/core-coding.toml` is its machine-readable
mirror (the questions, their kinds, codes, special answers and quote rules), which the
checker and the gather read; `tests/test_core_scheme.py` keeps the two in step.

Code the paper from its full text (the converted markdown, whose pages are marked `{N}`),
answering every question below, in order: section A (Part A's fifteen axes, coded again),
then sections B to F, then the seven quality items of section Q.

### General rules

- **The paper's own method.** Code the method the paper proposes and the experiments it
  runs, not its baselines, its related work, or methods it only mentions. When it proposes
  several, code the one its main results rest on.
- **What was done, not what is possible.** Code what the method has and what the
  experiments ran, not what the paper says the method could support, what earlier methods
  lack, or what is left for future work. A sentence about deployment with no run reported is
  a claim, not a level (F01).
- **Where the paper says it.** Take the method from the method section (its definitions,
  equations, algorithm boxes and figures) and the evidence from the experiments; the
  introduction and the related work decide nothing.
- **Contradictions.** When two passages disagree, code the one the results rest on (the
  experiments' settings over the introduction's summary), and say so in the note.
- **As printed.** Give numbers, names and sizes as the paper prints them; when two passages
  give different values, give the one the results rest on and note the other.
- **Nothing from outside the paper.** No knowledge of other papers, of the authors, or of
  what such methods usually do; a cited paper is not read.
- **Own words.** Notes and text answers are in your own words, apart from names such as an
  algorithm's or a baseline's; only the `evidence:` lines copy the paper.

### Answers, evidence and blocks

Each question is answered in one block, in this form (shown indented here; a block starts
at the line's beginning):

    ## B07 algorithm
    answer: ppo
    evidence: {6} "the policy is trained with proximal policy optimization"
    note:

- The heading gives the question's ID and its name.
- `answer:` holds the answer in the question's kind:
  - one code: one code from the question's list;
  - a list: every code that applies, joined by `|` (`makespan|tardiness`); a code marked
    "Alone." is never combined with another;
  - a number: digits, with a decimal point if needed;
  - a level: one of `L1` to `L5`;
  - a score: `1`, `0.5`, `0` or `not-assessable`;
  - text: names as the paper prints them, or your own words, within the question's limit;
  - a count: the number of item blocks that follow (1 or more), or `none`.
- Special answers, allowed only where a question lists them:
  - `not-stated`: the paper is silent on what the question asks. Give it only after
    searching the paper; the note begins "searched" and lists the terms searched.
  - `not-applicable`: the question does not apply to this study, for example the steering
    action of an end-to-end policy; the note says why.
  - `not-reported`: the paper does not report an evidence practice the question asks about
    (seeds, ablations, code). The note begins "searched" and lists the terms searched. It
    is a finding about the paper's reporting, where `not-stated` is a property of the method
    the paper leaves out.
- Evidence: every answer other than a special answer, `none` on a count, a score of `0` or
  `not-assessable`, and the codes marked "No quote.", is backed by one to three `evidence:`
  lines. Each copies one
  continuous span of the paper exactly as the markdown has it, at most 50 words, never two
  spans joined with "..." and never across a page marker, after `{N}`, the number of the
  page marker above it. The quotes of a list answer cover its codes between them.
  Differences of spacing and line breaks, of typographic quotation marks and dashes, and of
  markdown or HTML formatting are ignored when a quote is checked.
- `note:` is one line, empty when nothing needs saying, and required for a special answer
  and for a contradiction.
- Repeated items: baselines (D07), claims (D19) and transfer tests (E01) are counted in
  their question's block, then given one block each, numbered from 1 (`## D07.1 baseline`,
  `## D07.2 baseline`), with the fields the question lists, each on its own line after
  `answer:` (`kind: dispatching-rule`). The count's block, unless it is `none`, and every
  item block are backed by evidence like any other answer.

### Section A: the map's axes, from the full text

Part A's fifteen axes, coded again from the full text, so that the share of the abstract's
codes that the full text confirms can be measured (protocol, Synthesis). Each takes Part A's
codes, kinds, defaults and rules, read with "the paper" in place of "the title and
abstract", and the general rules above. For `policy_role`, the quantities a policy sets to
produce, release or order while a fixed rule or heuristic builds the schedule are an
auxiliary part beside it (`steering-heuristic`), not scheduling decisions; Part A's rule is
given to the models with this clause (`runners/core_check.py`, `full_text_reading`). Every
answer is quoted except the codes in the last column.

| ID | Axis | No quote |
|---|---|---|
| A01 | `policy_role` | |
| A02 | `coordination` | |
| A03 | `scheduling_action` | `not-applicable` |
| A04 | `learner_depth` | |
| A05 | `deep_architecture` | `not-applicable` |
| A06 | `training_algorithm_family` | |
| A07 | `hybridization` | `none` |
| A08 | `state_content` | |
| A09 | `state_encoding` | |
| A10 | `dynamic_events` | `none` |
| A11 | `objective` | |
| A12 | `constraints` | `none` |
| A13 | `instances` | |
| A14 | `domain` | `manufacturing` |
| A15 | `readiness_claim` | `none` |

### Section B: problem and approach (question 1)

#### B01 `study_type` (one code)

What does the paper contribute?

- `new-method`: a reinforcement learning method of its own, or a new part of one (a state,
  a reward, a network, a training scheme), and tests of it.
- `application`: a published reinforcement learning method applied to a shop or a case,
  changed only to fit it there.
- `comparison`: a comparison of reinforcement learning methods or settings as its main
  contribution, with none proposed as its own.
- `other`: another kind, such as a framework or a software system whose learning part is
  not its contribution.

Special answers: `not-stated`.

#### B02 `flexibility` (one code)

How flexible are the shops of the paper's experiments?

- `partial`: each operation can be processed on a subset of the machines, or the
  instances mix partially and totally flexible operations.
- `total`: every operation of every instance can be processed on every machine.
- `none-tested`: the problem is a flexible job shop, but every instance the experiments
  use gives each operation one machine (classical job shop instances).

Special answers: `not-stated`.

#### B03 `sub_decision` (one code)

Which of the flexible job shop's two decisions does the learned policy take, itself or
through the rules it chooses? A policy that chooses dispatching rules, or sets their weights,
takes the decisions its rules make: `sequencing` when they choose the next operation or job,
`assignment` when they choose machines, `both` when they make both; `not-applicable` is only
for a policy that steers a heuristic or metaheuristic.

- `sequencing`: which operation or job is processed next; each operation's machine is set
  by a rule or is fixed.
- `assignment`: which machine processes an operation a rule has chosen.
- `both`: sequencing and assignment, in one action, in turns, or by two agents.
- `other`: another decision, such as batching, lot splitting, a job's factory or line, or
  whether to wait.
- `not-applicable`: the policy steers a heuristic or metaheuristic (a parameter, an
  operator, a neighborhood or an acceptance decision), which makes both decisions itself.

Special answers: `not-stated`.

#### B04 `steering_action` (a list)

For a steering policy, what does one action choose or set? Applies when `policy_role` is
`steering-rules` or `steering-heuristic`.

- `dispatching-rule`: it chooses or switches among predefined dispatching rules.
- `rule-weights`: it sets the weights or parameters of a rule, or of a weighted
  combination of rules.
- `parameter`: it sets a parameter of a heuristic or metaheuristic, such as a rate, a
  temperature or a population size.
- `operator`: it chooses a search operator, such as a crossover, a mutation or a move.
- `neighborhood`: it chooses a neighborhood structure for a local search.
- `acceptance`: it decides whether a new solution is accepted.
- `other`: another steering action, such as an auxiliary decision beside a heuristic that
  builds the schedule, or the quantities to produce, release or order beside a fixed rule
  that builds it.

Special answers: `not-applicable`, `not-stated`.

#### B05 `steered_method` (a list)

Which methods does a steering policy choose among or control? Applies when `policy_role` is
`steering-rules` or `steering-heuristic`. For a policy that decides an auxiliary part beside
the method that builds the schedule, the method is that one; a fixed dispatching rule is
`dispatching-rules`.

- `dispatching-rules`: dispatching or priority rules, composite rules included.
- `genetic-algorithm`: a genetic or another evolutionary algorithm.
- `simulated-annealing`: simulated annealing.
- `tabu-search`: tabu search.
- `variable-neighborhood-search`: variable neighborhood search.
- `swarm`: particle swarm, ant colony, a bee colony or another swarm method.
- `local-search`: another local search or improvement heuristic.
- `constructive-heuristic`: another constructive heuristic.
- `other`: another method.

Special answers: `not-applicable`, `not-stated`.

#### B06 `paradigm` (a list)

Which learning paradigms does the paper's method use?

- `online`: the agent learns by interacting with a simulated or a real shop. The default.
- `offline`: the agent learns from a fixed logged dataset, with no interaction during
  training.
- `imitation`: the agent imitates expert, solver or rule schedules (behavior cloning or
  imitation pretraining), before or during reinforcement learning.
- `model-based`: the agent learns or uses a model of the shop's dynamics, to plan or to
  generate experience.
- `meta-learning`: the agent is trained to adapt quickly to new instances or tasks.
- `safe`: a safety layer or a constrained objective keeps the agent's exploration or
  actions within limits.
- `other`: another paradigm the paper presents as part of its method, such as curriculum
  learning or self-play.

Special answers: none.

#### B07 `algorithm` (one code)

Which algorithm trains the learned policy whose role A01 codes? For a steering policy, that
is the policy that steers, not the heuristic or metaheuristic it steers. A paper with two
learned policies is coded by the one whose role A01 codes.

- `monte-carlo`: Monte Carlo control.
- `sarsa`: SARSA and expected SARSA, with or without a network.
- `q-learning`: Q-learning and the deep Q-network family (DQN, double, dueling,
  prioritized, D3QN, Rainbow), multi-agent value factorization (QMIX, QTRAN, VDN)
  included.
- `reinforce`: REINFORCE, with or without a learned baseline.
- `ppo`: proximal policy optimization, its masked and multi-agent forms (MAPPO, IPPO)
  included.
- `trpo`: trust region policy optimization.
- `a2c-a3c`: advantage actor-critic, synchronous or asynchronous.
- `ddpg-td3`: DDPG, TD3 and MADDPG.
- `sac`: soft actor-critic.
- `other`: another algorithm, such as a search-based or evolutionary update.

Special answers: `not-stated`.

#### B08 `algorithm_name` (text, at most 8 words)

The algorithm as the paper names it, such as D3QN, masked PPO or MAPPO.

Special answers: `not-stated`.

#### B09 `agent_unit` (a list)

What does each agent stand for? Applies when `coordination` holds `multi-agent` or
`hierarchical`.

- `machine`: one agent per machine.
- `job`: one agent per job.
- `operation`: one agent per operation.
- `sub-decision`: one agent per decision, such as one that sequences and one that assigns
  machines.
- `objective`: one agent per objective.
- `level`: one agent per level of a hierarchy.
- `other`: another unit, such as a factory, a work center or a transporter.

Special answers: `not-applicable`, `not-stated`.

#### B10 `multi_agent_training` (a list)

How are several agents trained? Applies when `coordination` holds `multi-agent`.

- `independent`: each agent learns from its own experience and reward.
- `shared-parameters`: the agents share one network's parameters.
- `centralized-critic`: a critic sees every agent during training while each acts on its
  own observation (centralized training with decentralized execution).
- `value-factorization`: a joint value is factored over the agents (QMIX, QTRAN, VDN).
- `communication`: the agents exchange messages or embeddings while acting.
- `other`: another scheme.

Special answers: `not-applicable`, `not-stated`.

#### B11 `objective_combination` (a list)

How are two or more objectives combined? Applies when `objective` holds two or more codes.

- `weighted-sum`: a weighted sum with fixed weights.
- `one-model-per-weight`: one model trained for each weight vector.
- `preference-conditioned`: one model conditioned on the weights or preferences.
- `pareto`: a Pareto front or archive of solutions.
- `lexicographic`: the objectives in a fixed order of priority.
- `goal-setting`: a higher level chooses which objective a lower level pursues.
- `other`: another way.

Special answers: `not-applicable`, `not-stated`.

### Section C: formulation and model (question 2)

#### C01 `action_space` (one code)

What kind of action does the policy take?

- `discrete`: a choice from a finite set, such as an operation, a machine, a pair, a rule,
  an operator or a parameter level.
- `continuous`: real-valued outputs, such as weights, parameters or priorities.
- `hybrid`: a discrete choice with continuous parameters.

Special answers: `not-stated`.

#### C02 `action_set` (one code)

How is the set of discrete actions made? Applies when `action_space` is `discrete` or
`hybrid`.

- `fixed-list`: a fixed list whose length does not depend on the instance, such as rules,
  operators, parameter levels or a fixed number of slots.
- `per-candidate`: one action per candidate operation, job, machine or pair at the
  decision, so the set's size changes with the instance and the state.

Special answers: `not-applicable`, `not-stated`.

#### C03 `action_count` (a number)

How many actions does the fixed list hold, in the main experiments? Applies when
`action_set` is `fixed-list`.

Special answers: `not-applicable`, `not-stated`.

#### C04 `wait_action` (one code)

May the policy choose to wait, leaving a machine idle or delaying a decision, while an
assignment is possible?

- `yes`: an action, or a rule among the actions, waits or idles.
- `no`: the paper lists the actions, and none waits. A step the environment takes by
  itself when nothing can be assigned is not a wait action.

Special answers: `not-stated`.

#### C05 `invalid_actions` (a list)

How are invalid actions handled?

- `masked`: invalid actions are removed from the choice by a mask on the policy's output.
- `penalized`: invalid actions can be chosen and are penalized in the reward.
- `repaired`: a rule replaces an invalid choice with a valid one.
- `by-construction`: the actions can only be valid, such as rules or operators that always
  give a feasible schedule, or candidates limited to feasible ones.

Special answers: `not-stated`.

#### C06 `mask_enforces` (a list)

Which constraints does the mask enforce? Applies when `invalid_actions` holds `masked`.

- `precedence`: only each job's next unscheduled operation is offered.
- `capacity`: a busy machine is not offered.
- `eligibility`: an operation is offered only with the machines that can process it.
- `priority-filter`: the mask also removes feasible actions that a rule or a score ranks
  low, such as a top-k candidate filter, so it restricts quality and not only feasibility.
- `other`: another constraint, such as a due date, a resource or a transport.

Special answers: `not-applicable`, `not-stated`.

#### C07 `reward_measure` (a list)

What does the reward measure?

- `makespan`: the makespan, its change, or a bound on it.
- `idle-time`: machine idle time.
- `utilization`: machine utilization.
- `tardiness`: tardiness, lateness or earliness.
- `flow-time`: flow time or waiting time.
- `workload`: machine load or its balance.
- `energy`: energy consumption or its cost.
- `cost`: another cost, or profit.
- `other`: another measure, such as a penalty for invalid actions alone.

Special answers: `not-stated`.

#### C08 `reward_timing` (one code)

When is the reward given?

- `per-step`: after every decision.
- `terminal`: only when the episode or the schedule ends.
- `mixed`: after every decision and at the end.

Special answers: `not-stated`.

#### C09 `reward_source` (one code)

How is the reward made?

- `hand-designed`: by a formula the authors give. The default.
- `learned`: by a model learned from preferences, demonstrations or labels (inverse or
  preference-based reinforcement learning).

Special answers: none.

#### C10 `decision_points` (one code)

When does the policy decide?

- `event-driven`: when an event occurs on a simulated clock: a machine becomes free, an
  operation finishes, a job arrives or a machine fails.
- `fixed-interval`: at fixed intervals of time.
- `per-operation`: once for each operation placed, in a constructive pass with no
  simulated clock.
- `per-iteration`: once per iteration or generation of the heuristic or metaheuristic it
  steers.
- `other`: another trigger.

Special answers: `not-stated`.

#### C11 `observability` (one code)

Is the shop treated as fully or partially observed?

- `full`: the policy's state is the shop's state, as in a Markov decision process.
  The default.
- `partial`: the paper treats the problem as partially observed (a POMDP or a Dec-POMDP),
  or its agents act on local observations.

Special answers: none.

#### C12 `input_size` (one code)

Does the network's input depend on the instance's size? Applies when `learner_depth` is
`deep` or `non-neural`.

- `fixed`: the input's size is tied to the training shop (a fixed number of jobs or
  machines), so the trained network cannot read a larger shop.
- `padded`: a fixed maximum size, with smaller instances padded by dummy jobs, operations or
  machines.
- `size-agnostic`: the network reads any number of operations, jobs or machines (a graph, a
  set or a sequence), or a fixed-length summary of the shop.

Special answers: `not-applicable`, `not-stated`.

#### C13 `model_summary` (text, at most 15 words)

The policy's network, and its critic if it has one, in your own words: the encoder, the
decoder or head, and their sizes where given. Applies when `learner_depth` is `deep` or
`non-neural`.

Special answers: `not-applicable`, `not-stated`.

#### C14 `training_regime` (one code)

How is the policy trained before it is evaluated? In a dynamic shop, an instance includes
its events: a policy trained on random scenarios of a shop and tested on new scenarios of it
is trained on a distribution.

- `distribution`: once, on a set or distribution of instances, then applied to instances it
  was not trained on.
- `per-instance`: on the instance it then solves.
- `online`: it keeps learning while it schedules, during evaluation or use.

Special answers: `not-stated`.

### Section D: evidence (question 3)

#### D01 `benchmark_sets` (a list)

Which named benchmark sets do the experiments use?

- `brandimarte`: Brandimarte's instances (mk01 to mk10, BRdata).
- `hurink`: Hurink's edata, rdata or vdata.
- `dauzere-peres-paulli`: Dauzere-Peres and Paulli's instances (DP).
- `kacem`: Kacem's instances.
- `barnes`: Barnes and Chambers's instances.
- `fattahi`: Fattahi's instances.
- `behnke-geiger`: Behnke and Geiger's instances.
- `taillard`: Taillard's job shop instances.
- `lawrence`: Lawrence's job shop instances (la01 to la40).
- `other-benchmark`: another named public set, such as Fisher and Thompson's, Demirkol's or
  a published generated set.
- `none`: no named benchmark set; the instances are generated or industrial.
  Alone. No quote.

Special answers: `not-stated`.

#### D02 `largest_jobs` (a number)

The number of jobs in the largest instance the trained policy is tested on.

Special answers: `not-stated`.

#### D03 `largest_machines` (a number)

The number of machines in that instance.

Special answers: `not-stated`.

#### D04 `event_processes` (a list)

How are the dynamic events generated in the experiments? Applies when `dynamic_events`
holds an event.

- `poisson`: arrivals or failures with exponential times between them (a Poisson process).
- `uniform`: times drawn from a uniform distribution.
- `fixed-times`: events at given times.
- `real-trace`: events taken from a real shop's records.
- `other`: another process or distribution.

Special answers: `not-applicable`, `not-stated`.

#### D05 `events_in` (one code)

In which runs do the events occur? Applies when `dynamic_events` holds an event.

- `training-and-testing`: in training and in testing.
- `testing-only`: the policy is trained on static shops and tested with events.
- `training-only`: in training only.
- `robustness-only`: only in a secondary robustness experiment.

Special answers: `not-applicable`, `not-stated`.

#### D06 `reschedule_trigger` (one code)

When does the method react to an event? Applies when `dynamic_events` holds an event.

- `each-decision`: the policy decides at every decision point, so events are absorbed as
  they come.
- `event`: each event triggers a rescheduling.
- `periodic`: rescheduling at fixed periods.
- `batch`: rescheduling after several events accumulate.
- `other`: another trigger.

Special answers: `not-applicable`, `not-stated`.

#### D07 `baselines` (a count)

How many groups of baselines is the paper's method compared with? A group is one baseline,
or several of one kind run the same way (eight dispatching rules make one group); at most
eight groups. Give each group a block `## D07.k baseline` with:

- `answer:` the baselines' names as the paper prints them, at most 12 words;
- `kind:` one of `dispatching-rule`, `metaheuristic`, `exact-solver`, `learned-policy`,
  `other`;
- `run:` `rerun` (the authors ran it on their instances), `copied` (its results copied
  from the paper that published it) or `not-stated`;
- `time_limit:` `stated` (a time limit or budget is given; the note gives it), `not-stated`,
  or `not-applicable` (a rule, a constructive heuristic, or a learned policy that builds its
  schedule in one pass; the note gives a learned policy's training budget where stated).

Special answers: `not-stated`.

#### D08 `metrics` (a list)

Which measures does the paper report, beside its objectives and its decision and training
times?

- `gap`: a gap or relative deviation to a best-known or optimal value, or to a bound.
- `win-count`: counts of the instances each method wins.
- `statistical-test`: a test of the significance of differences.
- `robustness`: performance under disruptions or perturbations.
- `other`: another measure.

Special answers: `not-reported`.

#### D09 `decision_time` (one code)

Does the paper report the trained policy's decision (inference) time?

- `per-schedule`: the time to produce a whole schedule.
- `per-decision`: the time per decision.
- `both`: both.

Special answers: `not-reported`.

#### D10 `training_cost` (one code)

Does the paper report the cost of training?

- `time-and-hardware`: the training time and the hardware.
- `time`: the training time only.
- `hardware`: the hardware only.

Special answers: `not-reported`.

#### D11 `size_scaling` (one code)

Does the paper report how performance changes as instances grow? `beyond-training` only when
the paper states that the policy run on the larger instances was trained on smaller ones;
when it does not say what each run's policy was trained on, or the policy is trained on each
instance it solves, the answer is `within-training`, and the note says why.

- `beyond-training`: on instances larger than those it was trained on.
- `within-training`: across sizes, each within the training sizes or trained for its size.

Special answers: `not-reported`.

#### D12 `inference_mode` (one code)

How does the trained policy produce the schedules it reports?

- `greedy`: one deterministic pass, taking the best action each time.
- `sampling`: several sampled passes, the best kept.
- `search`: a search on top of the policy, such as beam search or tree search.
- `heuristic-run`: the heuristic or metaheuristic the policy steers runs, as in training.
- `other`: another way.

Special answers: `not-stated`.

#### D13 `headline_statistic` (one code)

Which statistic of the paper's own method do its main result tables give?

- `mean`: a mean over runs, samples or instances.
- `best`: the best of several runs or samples.
- `median`: a median.
- `single-run`: one run per instance.
- `other`: another statistic.

Special answers: `not-stated`.

#### D14 `seeds` (a number)

From how many independent training runs (random seeds) do the reported results come? `1`
when the paper trains once.

Special answers: `not-reported`.

#### D15 `seed_spread` (one code)

Is the spread across training runs reported? Applies when `seeds` is above 1.

- `reported`: a standard deviation, an interval, a range or a plot across the training
  runs.

Special answers: `not-applicable`, `not-reported`.

#### D16 `ablation` (one code)

Does the paper test its method with a component removed or replaced, to isolate that
component's contribution?

- `reported`: it does.

Special answers: `not-reported`.

#### D17 `code_release` (one code)

Is the method's code available?

- `released`: a link to the code is given.
- `on-request`: the code is available on request.
- `promised`: the paper says it will be released.

Special answers: `not-reported`.

#### D18 `data_release` (one code)

Are the paper's own instances or data available? Public benchmark sets do not count.

- `released`: a link is given.
- `on-request`: they are available on request.
- `promised`: the paper says they will be released.
- `public-only`: the experiments use only public benchmark sets, so there is nothing of its
  own to release.

Special answers: `not-reported`.

#### D19 `claims` (a count)

Which of the field's recurring claims does the paper make about its own method, in its
results or conclusions (protocol, question 3.4)? Count the kinds it makes, each at most
once, and give each a block `## D19.k claim` whose `answer:` is one of:

- `beats-dispatching-rules`: it outperforms dispatching rules;
- `beats-metaheuristics`: it outperforms a metaheuristic;
- `beats-exact-solver`: it outperforms, or matches within a time limit, an exact solver;
- `beats-learned-policies`: it outperforms other learned policies;
- `generalizes-across-sizes`: it generalizes to instance sizes it was not trained on;
- `trains-stably`: it trains more stably, or converges better, than an alternative.

Special answers: none.

#### D20 `training_stability` (one code)

Does the paper report evidence on training stability, such as learning curves or the
variance across runs during training?

- `reported`: it does.

Special answers: `not-reported`.

### Section E: transfer (question 4)

#### E01 `transfer_tests` (a count)

How many tests run the trained policy on instances unlike those it was trained on?
Instances of the same generator, with the same settings and sizes, are not such a test;
changed event rates or settings are (`events`); at most six tests. A test counts only when
the paper states that the policy run on it was trained on other instances. A policy trained
within each run on the instance it solves, as when it learns inside a search, has no
transfer test, whatever the paper calls its runs on other sets; a run whose policy's
training the paper does not state is not counted either, and the note says so. Give each a
block `## E01.k transfer_test` with:

- `answer:` how the test instances differ, a list of `size`, `flexibility`, `layout` (the
  machines or routes changed), `processing-times`, `events` (dynamic events changed or
  added), `objective-or-constraints`, `other-factory`, `public-benchmark` (trained on
  generated instances, tested on a benchmark set), `real-data`, `other`;
- `provenance:` where the test instances come from: `generated`, `public-benchmark`,
  `industrial`, `other`;
- `mode:` `unchanged` (the trained policy as it is), `fine-tuned` (trained further on the
  new instances), `retrained` (trained again on them) or `not-stated`;
- `outcome:` as the paper states it: `holds` (performance comparable to its other results,
  or better than its baselines), `degrades`, `mixed` or `not-stated`.

Special answers: `not-stated`.

#### E02 `train_test_overlap` (one code)

Are the policy's test instances different from its training instances?

- `disjoint`: the test instances differ from every training instance.
- `overlap`: some or all test instances were also used in training, as for a policy trained
  within each run on the instance it solves.

Special answers: `not-applicable`, `not-stated`.

#### E03 `training_instances` (a list)

Which instances is the policy trained on?

- `generated`: generated, random or synthetic instances.
- `public-benchmark`: instances of a named benchmark set.
- `industrial`: a real company's or system's data.

Special answers: `not-stated`.

### Section F: readiness and practice (question 5)

#### F01 `readiness_level` (a level)

The highest level the paper's own runs reach (protocol, question 5); a claim with no run
reported counts at the level its runs reach. Outside manufacturing, by analogy: the
domain's own real data (L2), a twin or hardware in the loop (L3), a testbed or shadow mode
(L4), its live production system (L5).

- `L1`: simulation only, on benchmark or generated instances. No quote.
- `L2`: tested offline on a real company's, factory's or system's data.
- `L3`: ran inside a digital twin of a named physical system, or with hardware in the loop.
- `L4`: ran on physical equipment (a testbed), or in shadow mode beside a live shop.
- `L5`: ran inside a live production or manufacturing execution system.

Special answers: none.

#### F02 `decision_deadlines` (one code)

Does the paper report decision deadlines: a time within which a decision or a schedule must
be ready?

- `tested`: a deadline is stated and the policy's time is checked against it.
- `discussed`: deadlines or real-time needs are discussed, with no check.

Special answers: `not-reported`.

#### F03 `imperfect_data` (one code)

Does the paper test the policy with imperfect data: noisy, missing, delayed or wrong
information in its state?

- `tested`: it does.
- `discussed`: imperfect data are discussed, with no test.

Special answers: `not-reported`.

#### F04 `interpretability` (one code)

Does the paper explain the policy's decisions, such as by rules extracted, attention or
feature importance shown, or decisions traced?

- `shown`: explanations are produced and shown.
- `discussed`: interpretability is discussed, with no explanation shown.

Special answers: `not-reported`.

#### F05 `robustness` (one code)

Does the paper test robustness: performance under disruptions, perturbed data, or
conditions not seen in training?

- `tested`: it does.
- `discussed`: robustness is discussed, with no test.

Special answers: `not-reported`.

#### F06 `limitations` (a list)

Which limitations of its own method does the paper state?

- `scalability`: instance size or computing time.
- `generalization`: to other instances, shops or objectives.
- `training-cost`: the cost or time of training.
- `real-world-validation`: no test in a real shop.
- `assumptions`: simplifying assumptions about the problem, such as no transport or
  deterministic times.
- `other`: another limitation.

Special answers: `not-reported`.

### Section Q: quality (protocol, Quality assessment)

Each item is scored `1` (met), `0.5` (partly) or `0` (not met), as the item defines them,
judging methodological quality rather than reporting quality; an item the paper does not
report enough to judge is `not-assessable`, never inferred. The note gives the reason in one
line, and for `0.5` names what is missing. A score of `1` or `0.5` is quoted; `0` and
`not-assessable` need no quote.

#### Q01 `q_shop` (a score)

The shop is specified: its jobs, machines, eligible machines, processing times and
constraints, or the generator that produces them. `1` when all of these are given for the
instances the main results come from (directly, by a named benchmark set, or by a generator
with its settings); `0.5` when some are and at least one is missing or given only in general
words; `0` when none is; `not-assessable` only when the paper reports too little to judge.

Special answers: none.

#### Q02 `q_mdp` (a score)

The decision process is specified: its state, actions and reward. `1` when all three are
defined (the state by its features, the actions by their set, the reward by its formula or
exact rule); `0.5` when all three are named but at least one only in general words, or one
is missing; `0` when two or more are missing; `not-assessable` only when the paper reports
too little to judge.

Special answers: none.

#### Q03 `q_algorithm` (a score)

The algorithm and its update are specified, with the settings needed to rerun it. `1` when
the algorithm, its update and every setting it needs are given, as they apply: network
sizes, learning rate, discount, exploration and its schedule, batch and buffer sizes,
target-network updates, training length; `0.5` when the algorithm and its update are given
but at least one setting it needs is not; `0` when the algorithm is only named;
`not-assessable` only when the paper reports too little to judge.

Special answers: none.

#### Q04 `q_instances` (a score)

The instances are repeatable: public, released, or generated by a stated procedure. `1` when
every instance set the results come from is public, released, or generated by a procedure
stated well enough to repeat (its distributions and their ranges); `0.5` when some sets are
and some are not, such as a set generated without a stated procedure or available only on
request; `0` when none is; `not-assessable` only when the paper reports too little to judge.

Special answers: none.

#### Q05 `q_baselines` (a score)

The baselines are run on the same instances, each with a stated time limit. `1` when the
study runs every baseline on its own instances and every search-based baseline has a stated
time or iteration limit; `0.5` when the baselines run on the same instances but some limits
are not stated, or some baseline results are copied from other papers; `0` when no baseline
runs on the same instances, or there is none; `not-assessable` only when the paper reports
too little to judge.

Special answers: none.

#### Q06 `q_runs` (a score)

Results come from more than one training run, with the spread across runs reported. `1` when
several independent training runs are stated and the spread across them (a standard
deviation, an interval, a range, or the runs plotted) is reported; `0.5` when several runs
are stated but no spread across them is reported, a spread across instances or test episodes
not counting as one; `0` when the results come from one training run; `not-assessable` only
when the paper reports too little to judge.

Special answers: none.

#### Q07 `q_claims` (a score)

Every claim of transfer or of use beyond simulation is tied to a test the study ran. `1` when
every such claim is backed by a test the study reports, and also when the paper makes no
such claim; `0.5` when some are and some are not; `0` when none is; `not-assessable` only
when the paper reports too little to judge.

Special answers: none.

### Coverage

Every item that Part B must cover, with the questions that answer it.

| Source | Item | Questions |
|---|---|---|
| Protocol, question 1 | study type; domain; problem variant and flexibility; dynamic events; objectives; extra constraints | B01; A14; B02, A12; A10; A11, B11; A12 |
| Protocol, question 1 | policy role; steering action; sub-decision; paradigm; algorithm and its update; hybridization; coordination; year | A01; B04, B05; B03, A03; B06; A06, B07, B08 (update derived from B07); A07; A02, B09, B10; the record |
| Protocol, question 2 | state; action type; invalid actions and the mask; reward and its timing; decision points; observability | A08; A03, C01 to C04; C05, C06; C07 to C09; C10; C11 |
| Protocol, question 2 | model type; state encoding | A04, A05, C13; A09, C12 |
| Protocol, question 3 | instances and benchmark sets; dynamic events and their processes | A13, D01 to D03, E03; A10, D04 to D06 |
| Protocol, question 3 | baselines and their time limits; metrics; decision time; training cost; performance as size grows | D07; D08; D09; D10; D11 |
| Protocol, question 3 | seeds and spread; ablations; code and data; claims; training stability | D14, D15; D16; D17, D18; D19; D20 |
| Protocol, question 4 | how test instances differ; provenance; transfer mode; outcome | E01 (items), E02 |
| Protocol, question 5 | readiness level and its passage; decision deadlines; imperfect data; interpretability; robustness; limitations | F01, A15; F02; F03; F04; F05; F06 |
| Quality instrument | items 1 to 7 | Q01 to Q07 |
| Synthesis matrix, Problem | problem class; dynamics; extra constraints | B02, A10; A10, D04; A12 |
| Synthesis matrix, Formulation | state representation; action; masking; reward timing; objective; decision epoch; observability | A08, A09; A03, B04, C01, C02; C05, C06; C08; A11; C10; C11 |
| Synthesis matrix, Learner | learning paradigm; algorithm; coordination | B06, A06; B07, B08; A02, B09, B10 |
| Synthesis matrix, Evidence | instances; generalization regime; baselines; metrics; seed variance; ablation; code or data; readiness | A13, D01; E01; D07; D08; D14, D15; D16; D17, D18; F01 |
| B1 | training regime; overlap of training and test; input size tied to the instance; scale tests; training instances | C14; E02; C12; D11; E03 |
| B2 | inference mode; equal time budgets; run time; the statistic behind the headline | D12; D07 (time limits); D09; D13 |
| B3 | the action space and its size; wait actions; a steering policy's rules and parameters; invalid actions | C01 to C03; C04; B04, B05; C05, C06 |
| B4 | several agents: the unit, the training scheme, communication | B09; B10 |
| B5 | several objectives combined | B11 |
| B6 | event processes; events in training or testing; the rescheduling trigger | D04; D05; D06 |
| B7 | baselines rerun or copied; the reward's source; a flexible job shop paper tested only on job shop instances; expert or offline data | D07 (run); C09; B02; B06 |
| B8 | code released, promised or none; `not-reported` apart from `not-stated`; contradictions; values as printed; the method from its own section; the experiments, not motivation; a deployment claim confirmed by a run | D17; the special answers; the general rules; F01 |

## Amendments

No amendment was added after the freeze of 21 October 2026.
