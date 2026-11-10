# Sanity check: year distribution of the corpus

Run this before fetching anything. One cheap request returns the number of
records the query matches, by publication year, and their total.

Same query as search-query.md with a group-by appended.

```
works
where title_and_abstract has ("reinforcement learning" or "q learning" or "q network" or "q networks" or "deep q network" or "deep q networks" or "dqn" or "dqns" or "sarsa" or "reinforce" or "policy gradient" or "policy gradients" or "actor critic" or "a2c" or "a3c" or "proximal policy optimization" or "proximal policy optimisation" or "ppo" or "trust region policy optimization" or "trust region policy optimisation" or "trpo" or "deep deterministic policy gradient" or "ddpg" or "twin delayed ddpg" or "td3" or "soft actor critic" or "sac" or "temporal difference learning" or "policy" or "policies" or "markov decision process" or "mdp" or "mdps" or "markov" or "markovian" or "decision process" or "decision processes")
and title_and_abstract has ("flexible job shop" or "flexible jobshop" or "flexible job shops" or "flexible jobshops" or "flexible assembly job shop" or "flexible assembly jobshop" or "flexible assembly job shops" or "flexible assembly jobshops" or "flexible workshop" or "flexible workshops" or "fjs" or "fjsp" or "fjsps" or "fjssp" or "fjssps" or "dfjsp" or "dfjsps" or "dfjssp" or "dfjssps" or "mofjsp" or "mofjsps" or "fjspt" or "fjspts" or "fajsp" or "fajsps")
and type is (article or conference-paper)
group by publication_year
```
