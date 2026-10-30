# Event A: held-out material and prediction (written BEFORE running the analysis)

Group G07 / P10. Written: see file timestamp and `date -u` line below.

## Held-out material
M2 used all 157 eligible projects (1,604 releases with >3 data points) in
data/timeseries_final_Major_Minor.json, so no unused eligible projects remain
(the other 50 projects have no releases or only releases with <=3 data points).
Substitute: hold out the last 8 eligible projects in file order (46 releases):
Linxfeng/flow-eda (4), HummerRisk/HummerRisk (15), woowacourse-teams/2022-dallog (1),
CloudExplorer-Dev/CloudExplorer-Lite (4), qwdigital/LinkWechat (11),
SaptarshiSarkar12/Drifty (4), mybatis-flex/mybatis-flex (5), chat2db/Chat2DB (2).
These 8 WERE in the M2 fit; they are unseen only by the re-fitted model.

## Frozen method (no retuning)
Re-fit the M2 method unchanged (Soft-DTW k-means, k=4, random_state=9, same 10-point
interpolation and >3 data point filter) on the other 149 projects (1,558 releases).
Name each re-fitted cluster by one-to-one nearest M2 centroid (Euclidean, Hungarian
matching). Classify the 46 held-out releases with the re-fitted model (nearest centroid
under the same Soft-DTW metric). Compare with the pattern each release had at M2.

## Prediction
Removing ~3% of the data should barely move the centroids, so at least 85% of the 46
held-out releases keep their M2 pattern, and each pattern's share of the 46 stays within
10 percentage points of its M2 share (noisy: only 46 releases).

## What would challenge the M2 conclusion
Agreement below 70%, any pattern share more than 15 points from M2, or re-fitted
centroids that no longer show the four shapes (Early: first3>last3; Late: last3>first3;
Steady Active mean > Steady Inactive mean).
written (UTC): 2026-10-30T16:17:43Z

## Addendum (still before running): how the comparison is scored
Primary share test: each pattern's share of the 46 held-out releases (under the
re-fitted model) vs that pattern's M2 overall share (29.7 / 30.2 / 23.1 / 17.0%).
Also reported (not used for the verdict): the shares of the same 46 releases under
their M2 labels, and ARI between re-fit and M2 labels on the 1,558 training releases.
Verdict rule: SUPPORTS M2 transfer if agreement >= 85% and all shares within 10 pp and
the four shapes hold; CHALLENGES M2 if agreement < 70% or any share > 15 pp off or a
shape fails; otherwise PARTIAL. Thresholds are the ones above; none changed after running.
addendum written (UTC): 2026-10-30T16:18:51Z
