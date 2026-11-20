# Event B: a concentrated refactoring window in a Steady Inactive project

CS4928 group project, G07 / P10. Pre-Event-B state: tag `PRE_EVENT_B` (commit `647d038`).
Prediction: `event_b/EVENT_B_PREDICTION.md`, written before any analysis.

**Event B:** a project previously classified as Steady Inactive now has one release with a
concentrated maintenance/refactoring window. Is it healthy refactoring, deferred debt or an
architectural warning, and what does that mean for our Week 9 design?

## 1. What we tested

Nothing was refitted or retuned. The frozen classification is the authors' preprocessing
(10 evenly spaced samples of each release's daily refactoring density) plus nearest M2 centroid by
soft-DTW. This rule reproduces all 1,604 M2 labels exactly (`results/burst_test.txt`).

- **Controlled test:** every real Steady Inactive release (484) got one burst window (10% of its
  days, density 0.6) at the start, middle or end, and was classified again.
- **Real cases:** the 16 projects whose first two or more releases are Steady Inactive and whose
  next release is active.

Scripts: `event_b/eventb_burst_test.py`, `event_b/eventb_evaluate_response.py`.

## 2. Results

**Controlled bursts** (`results/burst_test.txt`):

| Burst position | Still Steady Inactive | Early Active | Late Active | Burst lost between the 10 samples | Fit worse than M2 95th percentile |
|---|---|---|---|---|---|
| Start | 31.0% | 68.4% | 0.6% | 11.0% | 0.8% |
| Middle | 45.9% | 36.0% | 17.6% | 32.9% | 0.6% |
| End | 40.5% | 1.0% | 58.5% | 15.5% | 0.6% |

- Start and end bursts mostly get the expected label, but 31-41% stay Steady Inactive.
- A middle burst gets no consistent label: 46% Steady Inactive, 36% Early Active, 18% Late Active.
- Up to a third of bursts fall between the 10 sampled days and are invisible to the classifier.
- Burst releases do **not** fit their pattern worse than ordinary releases (under 1% beyond the M2
  95th percentile), so the classifier gives no sign that anything unusual happened.

**Real cases:** 16 projects. Their active release is labelled Early Active (11), Late Active (3) or
Steady Active (2); only 2 of 16 fit worse than the M2 95th percentile. Several bursts sit in the
middle or end of the release but are labelled Early Active (for example `jacoco` and `Jzvd`).

## 3. Prediction vs result

| Prediction (`EVENT_B_PREDICTION.md`) | Result | Held? |
|---|---|---|
| The classification step is what Event B affects | Yes; our Week 9 naming is not involved | yes |
| A burst is forced into one of the four patterns with no warning | Yes, and 31-46% are not even moved out of Steady Inactive | yes |
| 10-point interpolation partly smooths short windows | Worse than predicted: up to 33% are lost entirely | partly (underestimated) |
| Burst releases fit worse than typical releases (above the M2 95th percentile) | No: under 1% | **no** |
| A middle burst is the least stable case | Yes: 46 / 36 / 18% split | yes |
| Challenge: if bursts are not separable by fit, a "poor fit" flag would not help and no structural change is justified | This is what happened | the challenge condition was met |

## 4. Responses considered

| Option | Description | Main trade-off | Evidence | Decision |
|---|---|---|---|---|
| A. No additional structural change | Keep the frozen classification and the Week 9 naming; document the limitation; read bursts from project history in the analysis | Bursts can stay hidden in per-release labels | Section 2 | **Chosen** |
| B. Poor-fit flag | Flag releases whose distance to the nearest centroid is beyond the M2 95th percentile | Cheap, but only useful if bursts fit badly | Flags under 1% of burst releases | Rejected |
| C. Burst indicator | Report the share of refactoring in the busiest 20% of days (threshold 50%, fixed before evaluation) next to the label (`event_b/burst_indicator.py`) | Extra signal without changing labels | Flags 82.6% of *unmodified* Steady Inactive releases, so it cannot tell a new burst from normal sparse activity (`results/response_evaluation.txt`) | Rejected |
| D. Change the method | Burst-preserving resampling, or a fifth "burst" pattern (k = 5) | Could capture bursts | Changes every label, breaks the M2 reproduction and comparability with the paper; speculative generality for one scenario | Rejected |

Option C is kept in `event_b/` with its tests as evidence of the analysis; it is not part of the
pipeline. We did not tune its threshold after seeing the result.

## 5. Pre-Event-B vs post-response state

- **Pipeline code:** unchanged. No file outside `event_b/` and `tests/` differs from `PRE_EVENT_B`.
- **Labels:** the M2 labels and the Week 9 naming are unchanged (frozen rule = 1,604 / 1,604).
- **Tests:** 13 pass (`python -m unittest discover -s tests`): the 7 Week 9 naming tests, still
  passing, plus 6 tests of the rejected burst indicator.
- **Added:** this analysis, its two scripts and their outputs in `event_b/results/`.

## 6. Healthy refactoring, deferred debt or architectural warning?

From refactoring density alone the three cannot be told apart, and the pattern label for the burst
release is not reliable enough to try. Project history gives a tentative reading for the 16 real
cases:

- **5 projects return to Steady Inactive in the next release** (BanManager, storio, resilience4j,
  java-logging, JZVideo). An isolated burst followed by inactivity is consistent with **paying down
  deferred debt** in one go.
- **10 projects stay active afterwards.** This is consistent with **healthy refactoring**: a lasting
  change in how the project maintains its code.
- **1 project** (jacoco) has no later release to judge.
- **Architectural warning cannot be assessed:** that needs per-release architecture-smell data, and
  the package does not provide it (`releaseQuality.py` is missing).

## 7. Conclusion

**The Week 9 decision is supported.** Event B puts pressure on the classification inherited from the
authors (sampling and the four-pattern taxonomy), not on our naming change. All releases here are
classified against the M2 centroids, whose names the Week 9 rule confirms
(`test_m2_centroids_get_the_authors_names`). Neither cheap detector we tested (B, C) can
separate a burst from normal Steady Inactive activity, and changing the method (D) would break the
reproduction. So the smallest justified response is no additional structural change, plus
documenting the limitation.

- **Trade-off accepted:** per-release labels can hide a concentrated window. Up to 46% of controlled
  bursts kept the Steady Inactive label. Interpreting bursts needs project history, outside the code.
- **Anti-pattern avoided:** speculative generality. A fifth pattern or a new detector would add
  structure for one scenario without evidence that it works; both detectors we tried failed.
- **Risk remaining:** sampling 10 points loses up to a third of mid-release bursts. This is a threat
  to validity for any per-release claim, including the paper's.

## 8. AI use

An AI assistant (Claude) wrote the scripts and this analysis, ran them, and drafted this document.
Every number above comes from `event_b/results/`.
