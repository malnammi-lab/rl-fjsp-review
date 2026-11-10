# results

The runners write every file here, except `search/search-record.md`, which was written with
the search and not by a runner in this folder. Rerun a runner rather than editing its output. Each config names the files its runner
writes. The last column names the steps of `../runners/run_all.py`.

| Folder | What it holds | Steps |
|---|---|---|
| `search/` | The record of the search (`search-record.md`), written with the search and not by a runner in this folder. | None |
| `corpus/` | The corpus profile (`corpus-profile.md`) and the duplicates removed (`duplicates.md`). | `corpus-profile`, `deduplicate` |
| `screening/calibration/` | The comparison of round 1 (`calibration-round-1.md`) and its lock. | `screening-calibration` |
| `screening/validation/` | The result of the blind sample and of the second person's screening (`screening-validation.md`) and the lock. | `screening-validation` |
| `screening/consensus/` | The votes per record (`screening-votes.csv`) and the consensus report (`screening-consensus.md`). | `screening-consensus` |
| `map/` | The map's vote (`map-vote.md`, `map-votes.csv`), the cells the scheme's rules changed (`map-implications.csv`) and the models' agreement per axis (`map-agreement.csv`). Also a person's check: the report (`map-check.md`) and its lock. | `map-vote`, `map-check` |
| `core/` | The claims confirmed (`claims.md`) and the venue bands (`venue-bands.md`, `venue-matches-sheet.csv`). The selection (`core-selection.md`, `core-flow.csv`, `core-vs-map.csv`, `core-lock.json`). The counts (`core-statistics.md`, `.csv`; `map-by-period.md`, `.csv`, `.tex`). The full texts gathered (`core-texts.md`, `core-texts-flow.csv`). | `core-claims`, `venue-bands`, `core-selection`, `core-statistics`, `core-texts` |
| `core-coding/` | The draws of the coding (`draws.md`, `draws.csv`, `draws-lock.json`), the gather's report (`gather.md`), which records each response checked again against its paper, and the person's check (`human-check.md`, `.csv`). | `core-draws`, `core-gather`, `core-human-check` |
| `core-synthesis/` | The research questions' tables as `.csv`, `.md` and `.tex`, with the map's records by role and family (`map-cells`) and the core's studies by cell (`studies-by-cell`), all on one page in `synthesis.md`, and quality by study (`quality-by-study.csv`). The sensitivity analyses: `sensitivity.md`, the core's tables recomputed under `sensitivity/lowest-quality/`, `sensitivity/without-disputed/` and `sensitivity/without-step-2/`, `abstract-vs-full-text` and `map-unanimous` (`.md`, `.csv`). The agreement of the coding agent and the judge (`agreement.md`, `.csv`). | `core-synthesis` |
| `tables/` | The PRISMA flow counts (`flow-counts.csv`, `.tex`) and the list of core studies (`core-studies.csv`, `.tex`). | `make-tables`, `make-figures` |
| `figures/` | Each figure as `.png` and `.pdf`, with a `.csv` of the values it plots. | `make-figures` |

The sheets people filled (the calibration sheet, the validation sample, the adjudication sheet,
the map check's sheet and the claims' sheet) show the abstracts and are withheld; a step writes
them, with their tracking files, only where the authors' copies of the records are in place
(`../configs/withheld.toml`). A tracking file lets a run detect answers typed on a sheet but not
yet saved. The venue matches' sheet shows no abstract and keeps its tracking file
(`sheets-written.json`) in `core/`.

`core-check`, which only the authors can run, writes its report and problem list to
`core-coding/` (`check.md`, `check-problems.csv`); they are not committed.
