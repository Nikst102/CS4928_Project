# M4: design change (Week 9)

CS4928 group project, G07 / P10, Release-Wise Refactoring Patterns. State frozen by the tag `PRE_EVENT_B`.

- **Members:** Nikolay Stoiakine, Fergus Butler, Myron Butler, Philip Toriola
- **Builds on:** `M2_REPRO.md` (tag `M2_REPRO`), `event_a/EVENT_A.md`, and the RQ2 rules in `M1_PLAN.md` (tag `M1_PLAN`)

## 1. Scope of the M2 result

M2 showed that the authors' clustering **re-executes** exactly under their seed (9) and their
cluster-number-to-name mapping. On its own it did not show that the patterns or their names are
robust to other seeds or data. Section 5 tests that. `M2_REPRO.md` is frozen and has not been
edited.

## 2. Design problem

The authors' `dataHelper.rename_cluster` names patterns by hard-coded cluster number
(0 = Early Active, 1 = Steady Active, 2 = Late Active, 3 = Steady Inactive). k-means numbers its
clusters arbitrarily, so the numbers depend on the seed and the data. This is a hidden coupling
between the clustering output and the naming code: when the numbers change, patterns are silently
given the wrong name and no error is raised.

Evidence before the change:

- **Event A:** removing 8 projects swapped clusters 0 and 3, so 28 of the 46 held-out releases
  would have been mislabelled (`event_a/EVENT_A.md`; `event_a/results/eventa_result.json`).
- **Seeds 0-9** (section 5): 8 of 10 seeds number the clusters differently from the authors. Under
  the hard-coded map, check a fails for 8 of 10 seeds, and in 4 seeds fewer than 25% of releases
  get the same pattern name as at M2.

## 3. Alternatives considered

| Option | Description | For | Against |
|---|---|---|---|
| A. No change | Keep the map; document that it is valid only for seed 9 on the full data | No code change | Every re-run (other seeds, Event A, Event B) can mislabel silently |
| B. Shape rule | Name clusters with the M1 shape rule (early vs late mean, overall level), as recommended by the G08 review | No reference file needed | **Too weak to name clusters.** In seeds 1 and 5 the wrong hard-coded names still satisfy the shape rule; in seed 5 all four names are wrong (0.4% of releases keep their M2 name) yet every shape condition holds |
| C. Nearest reference centroid | Give each new cluster the name of the nearest M2 centroid, one-to-one | Unambiguous; works for any seed or data; already used in Event A | Depends on the frozen M2 centroids (`reference_patterns.json`) |

## 4. Decision

**Option C.** It is the smallest change that removes the coupling:

- `cluster_naming.py` (new): `name_clusters(centroids)` matches each centroid to the nearest
  reference centroid with a one-to-one assignment (Hungarian algorithm), so two clusters can never
  get the same name.
- `reference_patterns.json` (new): the four M2 centroids with their names, copied from
  `results/m2/outputs/cluster_center.json`. Their names were verified by M2 check d.
- `dataHelper.rename_cluster(cluster_id, names=None)`: takes the names for the run being analysed.
  Without them it behaves exactly as before, so `patterns.py` and the M2 scripts are unchanged.
- `dtwWrapper.py`: after fitting, saves the names to `data/softdtw/cluster_names.json`, and the
  plotting and Table 1 code use them. `radar_plots` deliberately keeps the authors' map, because
  it reads the authors' shipped labels (`data/feature_categories.json`), which use their numbering.

The shape rule (B) is kept as an independent check (check d), not as the naming rule. No design
pattern is introduced: the evidence justifies one function, not a new class structure.

## 5. Verification

### Tests: `tests/test_cluster_naming.py` (7 tests, all pass; `results/m4/tests_output.txt`)

| Test | Shows |
|---|---|
| M2 centroids get the authors' names | behaviour preserved |
| All 1,604 M2 releases keep their name | behaviour preserved |
| `rename_cluster` without names behaves as before (including invalid ids) | behaviour preserved |
| All 24 possible renumberings of the M2 clusters are named correctly | problem fixed |
| Event A re-fit (0/3 swap) is named correctly, and the old map breaks the shape rule on it | problem fixed |
| Names are one-to-one; wrong centroid shapes are rejected | robustness |

Run: `python -m unittest discover -s tests -v` (uses committed files only; no need to unzip data).

### Seeds 0-9 (RQ2, G08 recommendation): `results/m4/seeds_evaluation.txt`

Each seed re-fits the M2 method on all 1,604 releases (`m4_run_seeds.py`); naming and checks are
applied afterwards (`m4_evaluate_seeds.py`), with the old map and with the new naming.

| Seed | ARI vs seed 9 | Renumbered | Check a old / new | Check d old / new | Same name as M2, old / new |
|---|---|---|---|---|---|
| 0 | 0.957 | yes | fail / pass | fail / pass | 0.7% / 98.4% |
| 1 | 0.940 | yes | fail / pass | pass / pass | 52.8% / 97.8% |
| 2 | 0.811 | yes | fail / pass | fail / pass | 45.5% / 92.3% |
| 3 | 0.938 | yes | fail / pass | fail / pass | 1.3% / 97.6% |
| 4 | 0.815 | yes | fail / pass | fail / pass | 45.5% / 92.5% |
| 5 | 0.934 | yes | fail / pass | pass / pass | 0.4% / 97.4% |
| 6 | 0.815 | yes | fail / pass | fail / pass | 24.3% / 92.5% |
| 7 | 0.941 | no | pass / pass | pass / pass | 97.8% / 97.8% |
| 8 | 0.811 | yes | fail / pass | fail / pass | 32.4% / 92.3% |
| 9 | 1.000 | no | pass / pass | pass / pass | 100% / 100% |

- **New naming:** checks a and d pass for **10 of 10** seeds, and 92-100% of releases keep their M2
  pattern name.
- **Old map:** check a passes for 2 of 10 seeds and check d for 4 of 10.
- **Seed 9** reproduces the M2 labels exactly, so the seed script matches the M2 run.

**RQ2 against the rules and predictions frozen in `M1_PLAN.md`:**

| RQ2 measure (M1_PLAN section 6) | Result | Prediction (section 7) | Held? |
|---|---|---|---|
| Seed stability: mean ARI, seeds 0-8 vs seed 9 | 0.885 (min 0.811): **stable** | stable (>= 0.80) | yes |
| Cluster numbers reorder | 8 of 10 seeds | most seeds | yes |
| Seeds where the hard-coded map breaks the shape rule | 6 of 10 | at least half | yes |
| k = 3, 4, 5 silhouette comparison | not run in M4 | k = 4 close to, not clearly above | not yet tested |

The four patterns are stable across seeds. Only their numbering is not, which is exactly what the
design change addresses.

### Full pipeline with the new code: `results/m4/pipeline_regression.txt`

The authors' full analysis (`m2_run_rq1.py`, seed 9) was re-run with the new code. Every output
is identical to the committed M2 output: labels, centroids, per-cluster time series, feature
distributions, Table 1 (`operations-patterns.csv`), the 108 MB `label_operations.json` (by SHA-256),
both figures, and the printed silhouette, chi-square and Table 1 results. The run wrote
`cluster_names.json` = {0: Early Active, 1: Steady Active, 2: Late Active, 3: Steady Inactive},
the authors' names. Run log: `results/m4/pipeline_regression_run.log`.

## 6. Cross-team review (G08)

**Finding:** M2's "reproduced" shows re-execution, not robustness; checks a and d rely on the
hard-coded map. Recommended naming clusters by shape and re-running checks a/d for seeds 0-9.

**Response: Partly accept.**

- **Accepted:** the scoping (section 1); replacing the hard-coded map before `PRE_EVENT_B`
  (section 4); re-running checks a and d for seeds 0-9 (section 5).
- **Not accepted:** using the shape rule as the naming rule. The seed runs show it is too weak:
  in seeds 1 and 5 the wrong hard-coded names still pass it, and in seed 5 all four names are wrong
  while every shape condition holds. We use nearest-reference-centroid naming instead and keep the
  shape rule as a check.
- **Clarification:** check d already tested the names against the shapes, so under seed 9 the map
  was verified, not assumed. Check b (ARI) does not use the map.

## 7. Deviations and notes

- Seeds were run in two parallel processes to save time. Near the end both started seed 5; one was
  stopped (`exit=143` in `results/m4/seeds_run.log`) and seed 5 comes from the other
  (`results/m4/seeds_run_b.log`). Each seed's raw output is in `results/m4/seeds/seed_<n>.json`.
- The k = 3, 4, 5 part of RQ2 has not been run yet.
- `patterns.py` (the paper's RQ3 code) still uses the authors' map. It cannot run anyway, because
  `releaseQuality.py` is missing from the package.

## 8. AI use

An AI assistant (Claude) wrote the code changes, tests and scripts, ran them, and drafted this
document. Every result above points to a file in `results/m4/` or a test in `tests/`.
