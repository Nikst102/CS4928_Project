"""Event A: hold out the last 8 eligible projects, re-fit the M2 method unchanged on the rest,
classify the held-out releases, compare with M2. Frozen before running (see EVENT_A_PREDICTION.md).

Run from a folder that contains data/timeseries_final_Major_Minor.json, with the repo code on
the path:   python eventa_holdout.py <repo_dir> <m2_outputs_dir> <out_dir>
Method (unchanged from M2): 10-point linear interpolation, >3 data points, TimeSeriesKMeans
(metric softdtw, k=4, random_state=9, n_jobs=-1, tslearn defaults).
"""
import json
import sys
import time
from datetime import datetime, timezone

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score
from tslearn.clustering import TimeSeriesKMeans

repo_dir, m2_dir, out_dir = sys.argv[1:4]
sys.path.insert(0, repo_dir)
from clustering import Clustering  # authors' loader + interpolation, unchanged

NAMES = {0: "Early Active", 1: "Steady Active", 2: "Late Active", 3: "Steady Inactive"}  # authors' mapping (M2)
HELD_OUT = ["Linxfeng/flow-eda", "HummerRisk/HummerRisk", "woowacourse-teams/2022-dallog",
            "CloudExplorer-Dev/CloudExplorer-Lite", "qwdigital/LinkWechat", "SaptarshiSarkar12/Drifty",
            "mybatis-flex/mybatis-flex", "chat2db/Chat2DB"]

print("started (UTC):", datetime.now(timezone.utc).isoformat(timespec="seconds"))
c = Clustering()
X = c.interpolated_release_time_series
details = c.release_time_series_details
print("releases loaded:", len(X))

m2 = json.load(open(f"{m2_dir}/cluster_labels.json"))
m2_labels = np.array(m2["cluster_label"])
m2_centers = json.load(open(f"{m2_dir}/cluster_center.json"))
m2_C = np.array([m2_centers[str(i)] for i in range(4)]).reshape(4, -1)
assert len(m2_labels) == len(X)
assert [d[:2] for d in m2["timeseries_details"]] == [d[:2] for d in details], "M2 label order mismatch"
print("alignment with M2 labels: OK")

repos = np.array([d[0] for d in details])
held = np.isin(repos, HELD_OUT)
print("held-out releases:", int(held.sum()), "| training releases:", int((~held).sum()),
      "| training projects:", len(set(repos[~held])))
assert held.sum() == 46

t0 = time.time()
km = TimeSeriesKMeans(n_clusters=4, metric="softdtw", n_jobs=-1, random_state=9).fit(X[~held])
print("fit seconds:", round(time.time() - t0, 1))
np.save(f"{out_dir}/refit_centroids.npy", km.cluster_centers_)
np.save(f"{out_dir}/refit_train_labels.npy", km.labels_)
new_C = km.cluster_centers_.reshape(4, -1)

# one-to-one nearest M2 centroid (Euclidean on 10-point centroids, Hungarian)
cost = np.linalg.norm(new_C[:, None, :] - m2_C[None, :, :], axis=2)
rows, cols = linear_sum_assignment(cost)
new_to_m2 = {int(r): int(cc) for r, cc in zip(rows, cols)}
print("re-fit cluster -> M2 cluster:", new_to_m2, "| distances:", [round(float(cost[r, cc]), 4) for r, cc in new_to_m2.items()])
nearest_free = {int(r): int(np.argmin(cost[r])) for r in range(4)}
print("(plain nearest, for info):", nearest_free)

train_new = np.array([new_to_m2[int(l)] for l in km.labels_])
ari_train = adjusted_rand_score(m2_labels[~held], train_new)
exact_train = float(np.mean(m2_labels[~held] == train_new))
print("training: ARI vs M2 labels =", round(ari_train, 4), "| exact agreement =", round(exact_train, 4))

pred_new = km.predict(X[held])  # nearest centroid under the same Soft-DTW metric
pred = np.array([new_to_m2[int(l)] for l in pred_new])
m2_held = m2_labels[held]
agree = float(np.mean(pred == m2_held))
print("HELD-OUT agreement with M2 pattern:", int((pred == m2_held).sum()), "/", int(held.sum()), "=", round(agree, 4))

paper_m2_share = {k: float(np.mean(m2_labels == k) * 100) for k in range(4)}
shares_refit = {k: float(np.mean(pred == k) * 100) for k in range(4)}
shares_m2_same46 = {k: float(np.mean(m2_held == k) * 100) for k in range(4)}
print("\npattern            M2 overall | 46 via M2 label | 46 via re-fit | gap vs M2 overall (pp)")
max_gap = 0
for k in range(4):
    gap = shares_refit[k] - paper_m2_share[k]
    max_gap = max(max_gap, abs(gap))
    print(f"{NAMES[k]:<16}  {paper_m2_share[k]:6.1f}%   {shares_m2_same46[k]:6.1f}% ({int((m2_held==k).sum()):>2})   "
          f"{shares_refit[k]:6.1f}% ({int((pred==k).sum()):>2})   {gap:+.1f}")

# shape rule on re-fitted centroids, named via the matching
shape = {}
cent_named = {new_to_m2[r]: new_C[r] for r in range(4)}
f3 = {k: float(cent_named[k][:3].mean()) for k in range(4)}
l3 = {k: float(cent_named[k][-3:].mean()) for k in range(4)}
mn = {k: float(cent_named[k].mean()) for k in range(4)}
shape["Early Active: first3 > last3"] = f3[0] > l3[0]
shape["Late Active: last3 > first3"] = l3[2] > f3[2]
shape["Steady Active mean > Steady Inactive mean"] = mn[1] > mn[3]
print("\nre-fitted centroid shapes (first3 / last3 / mean):")
for k in range(4):
    print(f"  {NAMES[k]:<16} {f3[k]:.4f} / {l3[k]:.4f} / {mn[k]:.4f}")
for k, v in shape.items():
    print(" ", k, "->", v)
shapes_ok = all(shape.values())

# confusion matrix rows = M2 pattern, cols = re-fit pattern, held-out only
conf = np.zeros((4, 4), dtype=int)
for a, b in zip(m2_held, pred):
    conf[a, b] += 1
print("\nconfusion (rows = M2 pattern, cols = re-fit pattern) for the 46 held-out releases:\n", conf)

if agree >= 0.85 and max_gap <= 10 and shapes_ok:
    verdict = "SUPPORTS M2 TRANSFER"
elif agree < 0.70 or max_gap > 15 or not shapes_ok:
    verdict = "CHALLENGES M2"
else:
    verdict = "PARTIAL"
print(f"\nmax share gap = {max_gap:.1f} pp | agreement = {agree*100:.1f}% | shapes hold = {shapes_ok}")
print("VERDICT (pre-registered rule):", verdict)

out = {
    "verdict": verdict, "agreement": agree, "n_heldout": int(held.sum()),
    "n_train": int((~held).sum()), "train_projects": len(set(repos[~held])),
    "refit_to_m2_cluster": new_to_m2, "train_ari_vs_m2": ari_train, "train_exact_agreement": exact_train,
    "shares_refit_pct": {NAMES[k]: shares_refit[k] for k in range(4)},
    "shares_m2_overall_pct": {NAMES[k]: paper_m2_share[k] for k in range(4)},
    "shares_m2_same46_pct": {NAMES[k]: shares_m2_same46[k] for k in range(4)},
    "max_share_gap_pp": max_gap, "shapes": shape,
    "centroids_refit_named": {NAMES[k]: cent_named[k].tolist() for k in range(4)},
    "confusion_rows_m2_cols_refit": conf.tolist(),
    "heldout": [{"repo": d[0], "release": d[1], "m2_pattern": NAMES[int(a)], "refit_pattern": NAMES[int(b)]}
                for d, a, b in zip([d for d, h in zip(details, held) if h], m2_held, pred)],
}
json.dump(out, open(f"{out_dir}/eventa_result.json", "w"), indent=2)
print("finished (UTC):", datetime.now(timezone.utc).isoformat(timespec="seconds"))
