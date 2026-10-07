# M1 plan: study, research questions and preregistration

CS4928 group project, Week 5 (M1). Frozen by the tag `M1_PLAN`.

- **Members:** Nikolay Stoiakine, Fergus Butler, Myron Butler, Philip Toriola
- **Date frozen:** 7 October 2026

Nothing in this file may be rewritten after the tag. If an RQ, threshold or prediction
genuinely has to change, the old wording stays here and the change is added to
section 11 with the reason and date.

## 1. Study and artefact

| Item | Value |
|---|---|
| Paper | S. Noei, H. Li, Y. Zou, "An Empirical Study on Release-Wise Refactoring Patterns", FSE 2025 |
| DOI | https://doi.org/10.1145/3715734 |
| Authors' package | https://github.com/Software-Evolution-Analytics-Lab-SEAL/FSE2025-Refactoring-Release |
| Package commit used | `d6319849d822b08ad102302d88978f84f75cd5ff` ("Replication Package") |
| Data file | `data.zip`, SHA-256 `a1a38d2e2b24cf7f6efa475276f0c1ee219ee3cc146f89d15ea7e306ea1a766f` |

## 2. Research questions

**RQ1 (bounded reproduction).** To what extent can the release-wise refactoring patterns reported by Noei et al. be reproduced on a bounded subset of releases using the authors' released data and analysis method?
**RQ2 (extension and design).** Are the four patterns stable when the clustering is
re-run under conditions the paper does not report (random seeds 0-9; k = 3, 4, 5),
and what is the smallest justified design change to the replication package so that
pattern naming no longer depends on a seed-specific cluster-ID mapping, compared with
making no structural change?

## 3. Bounded target

**In scope.** The pattern-identification step of the paper's RQ1: linear interpolation
of each release's daily refactoring density to 10 points, Soft-DTW k-means with k = 4,
the four resulting centroids, the share of releases per pattern, and the silhouette
score.

**Out of scope.**

- Repository mining, RefactoringMiner, Designite and Understand runs. The package ships
  only the already-computed time series, not the raw data or the scripts that built it.
- The paper's RQ2 and RQ3 code-quality analysis. `main.py` imports `releaseQuality`,
  and that file is not in the package (see section 9).
- The refactoring-granularity and project-feature analyses inside the paper's RQ1.

## 4. Sample

- **Unit of analysis:** one release of one project.
- **Sample:** every release in `data/timeseries_final_Major_Minor.json` whose
  `timeseries` has more than 3 data points. This is the filter already applied in
  `clustering.py`. It gives **1,604 releases from 157 repositories**.
- **Sample IDs:** repository name plus release key (the `start-end` Unix timestamps
  used as keys in the JSON file), in file order. Example:
  `erlang/erlide_eclipse / 1397202397-1403608455`.
- No sub-sampling. The clusters depend on the whole sample, so a subset could not be
  compared fairly with the paper's percentages.

## 5. Method

### Environment

Python 3.10 with the versions pinned in `requirements.txt` (numpy 1.26.4, scipy 1.12.0,
tslearn 0.6.3, scikit-learn 1.4.0, matplotlib 3.8.2, seaborn 0.13.2), plus `pandas`,
which the code imports but `requirements.txt` does not list. R and `rpy2` are not
installed: no shipped `.py` file imports them.

### RQ1

1. `unzip data.zip` in the repository root.
2. Run `Clustering().cluster_and_analyze()` with the authors' defaults and no code
   changes (k = 4, metric `softdtw`, `random_state=9`).
3. Keep the outputs as evidence: the printed silhouette score, and
   `data/softdtw/cluster_center.json` and `data/softdtw/cluster_labels.json`.
4. Compare with the paper and with the authors' own labels, which are shipped as the
   `labels` list in `data/feature_categories.json`.

### RQ2

1. With our own script (the authors' files stay unmodified), repeat the clustering for
   seeds 0 to 9 at k = 4, and for k = 3, 4, 5 at seed 9. Seed 9 is the authors' seed.
2. For each run record the labels, centroids and silhouette score.
3. Design question. The design pressure is `dataHelper.rename_cluster`, which
   hard-codes cluster number to pattern name (0 = Early Active, 1 = Steady Active,
   2 = Late Active, 3 = Steady Inactive). At M4 we compare at least these responses:
   - **A. No structural change**: keep the mapping and document that it is valid for
     seed 9 only.
   - **B. Name clusters from centroid shape**, using the shape rule in section 6.
   - **C. Load the authors' shipped labels** instead of re-clustering.
4. Whichever is chosen is verified by a test that the names given to clusters are the
   same under every seed for which the clusters themselves agree.

## 6. Metrics and decision rules

**Shape rule (used in both RQs).** For a 10-point centroid, compare the mean of its
first three points with the mean of its last three. Early Active: first > last.
Late Active: last > first. Steady Active must have a higher overall mean than Steady
Inactive.

**RQ1 checks.**

| Check | Measure | Pass |
|---|---|---|
| a. Distribution | Share of releases per pattern, using the authors' mapping | Each within 3 percentage points of the paper |
| b. Agreement | Adjusted Rand Index (ARI) between our labels and the authors' shipped labels | ARI >= 0.80 |
| c. Separation | Silhouette score | Within 0.05 of the paper's 0.30 |
| d. Shape | Shape rule applied to the four centroids as named by the authors' mapping | Every named centroid meets its condition |

| Outcome | Rule |
|---|---|
| Reproduced | a, b, c and d all pass |
| Not reproduced | ARI < 0.50, or any share more than 10 points from the paper, or d fails |
| Partially reproduced | Anything else |

**RQ2 checks.**

- **Seed stability:** mean ARI between each of seeds 0-8 and seed 9. Stable if
  >= 0.80, moderately stable if 0.50 to 0.80, unstable if < 0.50.
- **Choice of k:** k = 4 is supported by the silhouette score if it is the highest of
  k = 3, 4, 5. If it is not, we report that the silhouette score alone does not single
  out four patterns (the paper also used manual inspection).
- **Naming:** the number of seeds, out of 10, for which the hard-coded mapping gives a
  cluster a name that contradicts the shape rule.

The thresholds (3 and 10 points, ARI 0.80 and 0.50, silhouette 0.05) are our own
choices, not the paper's.

## 7. Expected results, written before execution

- **RQ1:** we expect "Reproduced". The seed is fixed, the data is shipped, and the
  authors' shipped labels already match the paper: 476 Early Active, 484 Steady
  Inactive, 371 Late Active and 273 Steady Active out of 1,604, which is 29.7%, 30.2%,
  23.1% and 17.0%.
- **RQ2:** we expect the four shapes to be stable across seeds (mean ARI >= 0.80), but
  the cluster numbers to come out in a different order for most seeds. We therefore
  expect the hard-coded mapping to mislabel patterns for at least half of the seeds,
  and option B to be the smallest change that fixes it. We expect k = 4 to have a
  silhouette score close to, but not clearly above, k = 3 and k = 5.

## 8. What counts as non-reproduction

RQ1 is recorded as not reproduced if the ARI against the authors' labels is below 0.50,
or any pattern's share is more than 10 percentage points from the paper, or the four
centroids do not satisfy the shape rule. A negative or partial result is reported as
found and is not adjusted to match the paper.

**Contingency.** If the clustering cannot be run at all, we document the exact failure
and fall back to auditing the authors' shipped labels and metrics files.

## 9. Known deviations and threats, recorded before execution

1. **Missing file.** `main.py` fails with `ModuleNotFoundError: No module named
   'releaseQuality'`. The paper's RQ2 and RQ3 quality analysis cannot be run from the
   package, which is why the bounded target is the clustering step.
2. **Undeclared dependency.** `pandas` is imported but not listed in
   `requirements.txt`.
3. **Python version.** We use Python 3.10.20; the README recommends 3.10.12.
4. **Projects.** The paper reports 207 projects. The data file has 207 repository
   entries, but 40 contain no releases and only 157 contribute a release with more than
   3 data points. The release count, 1,604, matches the paper.
5. **Label order.** Check b assumes the shipped `labels` list is in the same order as
   the releases produced by `clustering.py`. Both have length 1,604, but the package
   does not state the order. If the shares match and the ARI is near zero, we will
   report misalignment as a possible cause.
6. **Naming inconsistency.** The appendix and `data/patterns_switches_metrics.json`
   use a pattern called "Early Inactive", which is not one of the paper's four names.
7. **Determinism.** The clustering runs with `n_jobs=-1`; results could differ slightly
   between machines even with a fixed seed.
8. **Scope of the claim.** We reproduce the clustering from the authors' processed
   data. We do not check that the time series were built correctly from the original
   repositories.

## 10. What was done before this freeze

- Environment set-up and inspection of the code and data files (counts in sections 4
  and 9).
- A tally of the authors' shipped labels (section 7).
- A feasibility smoke test, `m1_smoke_test.py`: 200 random releases, seed 123, labels
  discarded. It ran in about 17 seconds.
- The full clustering on the 1,604 releases with seed 9 was **not** run, and no RQ2
  runs were made.

**AI use.** An AI assistant (Claude) was used to read the paper and package, run the
set-up checks above and draft this plan. The counts and the missing-file error come
from commands run against the package. AI output is not treated as evidence: every
claim made from M2 onwards will point to a script, output file or commit.

## 11. Change log

No changes since the freeze.
