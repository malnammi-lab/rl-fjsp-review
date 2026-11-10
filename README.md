# rl-fjsp-review

This repository holds the code and data behind the paper:

> Moayad Alnammi, Osamah H. Hussein, Ahmed Azab and Yasser Almoghathawi. *Reinforcement Learning
> for Flexible Job Shop Scheduling: A Systematic Review of End-to-End and Steering Policies.*

The review maps the 533 records included at screening, coded from their titles and abstracts.
It then codes a core of 99 studies from their full texts. The code here produces the paper's
results from fixed data files: the counts and shares of the search, the screening, the map and
the core, the two plotted figures and the supplement's two generated tables. The code does not
draw the two workflow diagrams; their counts come from `results/`.

## What is here

- `protocol.md`: the review protocol, consolidated.
- `protocol-history.md`: the protocol approved on 11 October 2026, with its dated amendments.
- `configs/screening-criteria.md`: the eligibility criteria. Its Eligibility section is the
  exact text the screening models received.
- `configs/`: the TOML configs of the steps, naming their inputs, outputs and settings. It also
  holds the search query (`search-query.md`), the instructions given to the coding agent and
  the judge, and the models' settings (`model-settings.md`).
- `datasets/`: the data files, the coding scheme (`coding-scheme.md`) and the bibliographies of
  the 533 studies of the map (`map-references.bib`) and of the core (`core-references.bib`).
  `MANIFEST.md` gives each file's provenance and the checksums recorded for it. The record
  file (`references.json`) gives each abstract's SHA-256 in place of its text.
- `runners/`: the scripts of the steps. `run_all.py` runs them in order.
- `src/`: the shared rules (duplicates, screening, the map's vote, the full-text checks) and
  the templates of the pages on which people gave their answers.
- `results/`: everything the runners write. `results/README.md` maps the folders.
- `tests/`: the pytest suite, with its fixtures.

## What is not here

The search of OpenAlex and every call to a language model are not done by code in this folder.
Three open-weight models screened the records and coded the map: Qwen3.8-27B,
Gemma 4 26B A4B and Muse Glimmer 30B. Qwen3.8-27B then coded the core's full texts as an agent,
and Muse Glimmer 30B judged its answers. This folder holds those outputs in `datasets/` and
needs no network.

The authors keep the files that cannot be distributed:

- the abstracts of the records, which came from OpenAlex, Scopus, Springer Nature, Semantic
  Scholar and publishers' pages, and may not all be redistributed;
- the sheets on which people screened, coded and confirmed records, which show the abstracts;
- the full texts of the 99 core papers, and their text converted to markdown;
- the coding agent's responses and the judge's reasons, which quote the papers (each verdict
  and the judge's proposal are in `datasets/core-answers.csv`);
- the pages on which the full texts were gathered and the person's check was answered, with
  that check's papers;
- the licensed venue lists, SJR 2025 and ICORE2026.

`datasets/MANIFEST.md` describes each, with the checksums recorded for it. The screeners' and
the people's reasons and quotes, and the map's quotes, keep at most 40 consecutive words of an
abstract in any one cell; a longer stretch is cut and marked `[cut]`, and the authors keep the
files as written. Read together, the files can still repeat more of an abstract than any one
cell (`datasets/MANIFEST.md`, Provenance notes).

The coding scheme and the two configs the checker's fingerprint covers (`configs/core-coding.toml`,
`configs/map.toml`) are kept as they were approved and coded.

## Reproduce

Create the environment, then run the tests from the repository root:

```
conda env create -f repo_env.yml
conda activate rl-scheduling-review
python -m pytest -q
```

From a clone of this repository alone, this command reruns every step that needs nothing
outside it:

```
python runners/run_all.py --only deduplicate screening-calibration screening-validation screening-consensus map-vote map-check core-claims core-selection core-statistics core-draws core-synthesis core-human-check make-tables make-figures
```

`run_all.py` runs the named steps in the order given and stops at the first that fails.
`python runners/run_all.py --list` lists every step with its config. The steps that issued a
sheet (screening-calibration, screening-validation, map-check and core-claims) write their
reports but not their sheets, which show the abstracts. The outputs match the committed files
in `results/` and `datasets/`, with two exceptions:

- The figure images depend on the fonts installed, and each PDF records when it was drawn.
  The CSV beside each figure holds the values it plots.
- Some reports record the system that wrote them. Each names its config with that system's
  path separator; the committed ones were written on Windows (`configs\core.toml`). The
  screening validation report also names the Python version that drew its sample.

Five steps need files that are not released with this repository and are left out above:

| Step | Why |
|---|---|
| `corpus-profile` | Counts the abstracts and the facets they carry. |
| `venue-bands` | Reads the SJR and ICORE lists. |
| `core-texts` | Writes the page for gathering the full texts, and that page is not released with this repository. |
| `core-check` | Reads the converted full texts and the coding agent's responses. Without them, it reports that there is nothing to check. |
| `core-gather` | Reads the same and the judge's verdicts. Without the responses or the converted texts, it stops and writes nothing. |

The steps after them read their committed outputs. Without the abstracts, `corpus-profile` stops
with a message naming `datasets/MANIFEST.md`; a plain `python runners/run_all.py` therefore
stops at it, after `build-query`.

One more step runs from a clone but is left out of the command: `build-query` re-renders
`configs/search-query.md`, with the day's date in its header, and
`configs/search-query-groupby.md`.

The screening runners hold options this review's config leaves off (a full-text gate,
disagreements resolved by a person, a spot check and an escape clause), with their tests. The
config still names the files that a person's resolutions and the disagreements' sheet would
use, which are not written while disagreements are settled by rule, and the consensus report
keeps a row of zeros for each basis these options would add.

## How the models were checked

The three models' votes decide the screening and the map; the authors calibrated the screening
and checked both on blind samples. Code checked every answer the
coding agent gave from a full text, including that each quotation is on the page it cites. A
judge model then read the answers against each paper; its verdicts are reported and never
applied. The checker's code, the scheme and the models' prompts and tools are 11 files, fixed
by a fingerprint recorded with every coded paper (`datasets/core-coding-runs.csv`).
Osamah H. Hussein answered six questions blind on 20 studies drawn at random
(`datasets/core-human-check.csv`), and `results/core-coding/human-check.md` reports his
agreement with the agent.

## License and citation

The code (`runners/`, `src/`, `tests/` and `repo_env.yml`) is released under the MIT License
(`LICENSE`). The data, results, configs and documents the authors made are released under the
Creative Commons Attribution 4.0 International License (CC BY 4.0,
https://creativecommons.org/licenses/by/4.0/). Third-party material keeps its own terms: the
bibliographic metadata from OpenAlex (CC0) and Crossref, the excerpts of abstracts in the quotes
and reasons, and the venue fields taken from SJR 2025 and ICORE2026, which `datasets/MANIFEST.md`
cites. If you use the repository, please cite the paper above. `CITATION.cff` gives the
repository's own citation.
