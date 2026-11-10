# Model settings

The language models that screened the records and coded the map, the coding agent that
coded the core's full texts, and the judge, are not run by code in this folder. These
settings are the ones used for the three screeners, the coding agent, and the judge, and
`datasets/core-coding-runs.csv` gives the model and revision that coded each paper.

## Screening and the map

| | Qwen3.8-27B | Gemma 4 26B A4B | Muse Glimmer 30B |
|---|---|---|---|
| Developer | Alibaba | Google | Meta |
| Weights (Hugging Face) | `Qwen/Qwen3.8-27B` | `google/gemma-4-26B-A4B-it` | `meta-models/Muse-Glimmer-30B` |
| Revision | `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` | `4d7ae4984b7db7de8f8457170b3f1a419ee76d52` | `a4e59da52a7bc87ae7251dd5545c0dd437c44b68` |
| Precision | As released, not quantized | As released, not quantized | As released, not quantized |
| Reasoning | On, effort medium | On (thinking; no levels) | On, strength medium |
| Temperature, top-p, top-k, min-p | 1.0, 0.95, 20, 0 | 1.0, 0.95, 64, 0 | 1.0, 0.95, 64, 0 |
| Presence, frequency, repetition penalty | 0, 0, 1.0 | 0, 0, 1.0 | 0, 0, 1.0 |
| Context | 49,152 tokens | 49,152 tokens | 49,152 tokens |
| Maximum output (reasoning and answer) | 32,768 tokens | 32,768 tokens | 32,768 tokens |

Common to the three:

- The sampling settings are those of each model card at the pinned revision.
- Each record is one request, with the prompt as its only message and no tools.
- Each call has its own seed, from the prompt's hash, the seed base and the calls already made
  for that prompt, so no seed is used twice.
- Served with vLLM 0.31.0, one NVIDIA H100 80 GB GPU per model.

## The coding agent and the judge

| | Coding agent | Judge |
|---|---|---|
| Model | Qwen3.8-27B, at the revision above | Muse Glimmer 30B, at the revision above |
| Precision | BF16, as released | As released, not quantized |
| Reasoning | Effort medium; the model's reasoning is not sent back to it | Strength medium |
| Temperature, top-p, top-k, min-p | 1.0, 0.95, 20, 0 | 1.0, 0.95, 64, 0 |
| Presence, frequency, repetition penalty | 0, 0, 1.0 | 0, 0, 1.0 |
| Context | 131,072 tokens | 131,072 tokens |
| Maximum output per call | 16,384 tokens | 16,384 tokens |
| Tools | The project's tools (`core-coding-tools.json`), read with vLLM's `qwen3_coder` parser | None |
| Seeds | Each call its own, from the seed base (`seed_base` in `../datasets/core-coding-runs.csv`), the paper, the agent and the call | Each call its own, as in screening |
| At once | 8 papers, at most 32 calls in flight | At most 32 prompts |
| Serving | vLLM 0.31.0 with prefix caching, one NVIDIA B200 | vLLM 0.31.0 with prefix caching, one NVIDIA B200 |

The coding agent's instructions are `core-coding-prompt.md`, and the judge's are
`core-judge-prompt.md`.
