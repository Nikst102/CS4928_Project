# Event A: transfer test (G07 / P10, Release-Wise Refactoring Patterns)

State frozen before this event: tag `PRE_EVENT_A` (M2 commit c911715). The M2 result is not rewritten.
Prediction and held-out cases: `EVENT_A_PREDICTION.md` (written 2026-10-30 16:17-16:18 UTC, before any run).

## What was held out and why
M2 used all 157 eligible projects, so there were no unused ones for "the next eight". Substitute: the last 8
eligible projects in file order (46 releases) were held out of a re-fit. These 8 WERE in the M2 fit; they are
unseen only by the re-fitted model. M2 method unchanged (Soft-DTW k-means, k=4, seed 9, 10 points, >3 data points),
fitted on the other 149 projects (1,558 releases). Same Python 3.10.20 and pinned libraries as M2.

## Result (frozen first result; no retuning)
Verdict under the pre-registered rule: **supports M2 transfer**. Raw output: `results/eventa_run.log`, `results/eventa_result.json`.
- 44 of 46 held-out releases (95.7%) got the same pattern as at M2 (prediction: >= 85%).
- Shares of the 46 vs M2 overall: Early 28.3% (M2 29.7), Steady Active 8.7% (17.0), Late 30.4% (23.1), Steady Inactive 32.6% (30.2).
  Largest gap 8.3 points (Steady Active; only 4 releases). Prediction: within 10. Held.
- Re-fitted centroids still show all three shape conditions. Training labels agree with M2: ARI 0.953, 98.1% exact.
- The only 2 disagreements: Steady Inactive at M2 -> Late Active in the re-fit.

## What transfers, what does not
- Transfers: the four shapes, the pattern assignment of unseen releases (0 errors for Early, Steady Active and Late at M2), the group sizes.
- Does not transfer: **cluster numbering.** Re-fit cluster 0 is M2's Steady Inactive and re-fit cluster 3 is M2's Early Active
  (0 <-> 3 swapped; clusters 1 and 2 kept their numbers). Strongest evidence: `refit_to_m2_cluster` in `eventa_result.json`
  ({0:3, 1:1, 2:2, 3:0}, centroid distances 0.006-0.021).
- Borderline releases between Steady Inactive and Late Active are the unstable ones.

## Design implication (module concepts: coupling, information hiding, change)
The authors' `dataHelper.rename_cluster` hard-codes cluster number -> pattern name. It is a magic-number coupling between
the clustering output (which depends on the data and seed) and the naming logic. Removing 8 projects was enough to swap two
cluster numbers, so the hard-coded names would have been wrong for 28 of the 46 held-out releases (13 Early + 15 Steady
Inactive, swapped) with no error raised. A small change that names clusters from centroid shape or nearest reference centroid
removes this coupling. No design pattern is justified by this evidence. (Taken to Week 9 / RQ2.)

## Deviations, threats, AI use
- Held-out projects were in the M2 fit, so this is a hold-out test of the re-fit, not new material. 46 releases is small;
  Steady Active has only 4 releases, so its share is noisy.
- M2 pattern labels for the 46 come from a model that included them; agreement is therefore expected to be high.
- The first run of `eventa_holdout.py` crashed on a shape bug (centroids 10x1 vs 10) before any result was produced; the bug was fixed
  (no change to the method) and the run repeated. Only the second run is reported.
- AI use: Claude wrote and ran `eventa_holdout.py`. Every number above is from `results/eventa_run.log` / `eventa_result.json`.

Re-run: from a folder containing `data/timeseries_final_Major_Minor.json` (unzip `data.zip`) with the repo code on the path:
`python eventa_holdout.py <repo_dir> <repo>/results/m2/outputs <out_dir>` (about 7 minutes).
