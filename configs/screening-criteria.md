# Screening criteria

This file is the `## Eligibility criteria (title and abstract)` section of `protocol.md`,
verbatim: the text the screening models received.

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
