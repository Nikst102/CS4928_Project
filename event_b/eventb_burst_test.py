"""Event B: how does the frozen M2 classification treat a concentrated refactoring window?

Event B (P10): a project previously classified as Steady Inactive now has one release with a
concentrated maintenance/refactoring window. This script tests what the Week 9 design (state at
tag PRE_EVENT_B) does with such a release. Nothing is refitted or retuned.

1. Classification rule (frozen): the authors' preprocessing (10 evenly spaced samples by linear
   interpolation, clustering.py) and nearest M2 centroid by soft-DTW (gamma = 1, tslearn's
   default for TimeSeriesKMeans). This rule reproduces all 1,604 M2 labels exactly (printed below).
2. Controlled test: every real Steady Inactive release (M2 label) gets one burst window covering
   10% of its days (at least 1 day) at the start, the middle or the end, with density 0.6 (above
   the Steady Active centroid's level of about 0.4). Each modified release is classified.
3. Real cases: projects whose first two or more releases are Steady Inactive and whose next
   release is active.

Run from the repository root after `unzip data.zip`:
    python event_b/eventb_burst_test.py | tee event_b/results/burst_test.txt
Writes event_b/results/burst_test.json.
"""
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np
from scipy.interpolate import interp1d
from tslearn.metrics import cdist_soft_dtw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataHelper import AUTHORS_CLUSTER_NAMES as NAMES  # noqa: E402  (correct for the M2 numbering)

OUT = "event_b/results"
os.makedirs(OUT, exist_ok=True)
WIDTH, AMPLITUDE, LENGTH = 0.10, 0.6, 10


def interpolate(raw):
    """Exactly the authors' release preprocessing (clustering.py, __interpolate)."""
    x = np.arange(len(raw))
    return interp1d(x, raw, kind="linear")(np.linspace(0, len(raw) - 1, LENGTH))


def classify(series_10):
    """Frozen M2 rule: nearest M2 centroid by soft-DTW. Returns (cluster id, soft-DTW value)."""
    d = cdist_soft_dtw(np.asarray(series_10, float).reshape(1, LENGTH, 1), CENTROIDS, gamma=1.0)[0]
    return int(d.argmin()), float(d.min())


def with_burst(raw, where):
    raw = np.array(raw, float)
    n = len(raw)
    w = max(1, int(round(WIDTH * n)))
    start = {"start": 0, "middle": (n - w) // 2, "end": n - w}[where]
    raw[start:start + w] = AMPLITUDE
    return raw


ts = json.load(open("data/timeseries_final_Major_Minor.json"))
m2 = json.load(open("results/m2/outputs/cluster_labels.json"))
labels, details = m2["cluster_label"], m2["timeseries_details"]
centres = json.load(open("results/m2/outputs/cluster_center.json"))
CENTROIDS = np.array([np.ravel(centres[str(k)]) for k in range(4)]).reshape(4, LENGTH, 1)

# 1. The frozen rule and how well typical M2 releases fit their own pattern
X = np.array([interpolate(ts[d[0]][d[1]]["timeseries"]) for d in details]).reshape(-1, LENGTH, 1)
D = cdist_soft_dtw(X, CENTROIDS, gamma=1.0)
rule_matches_m2 = float((D.argmin(1) == np.array(labels)).mean())
fit_m2 = D[np.arange(len(labels)), labels]
p95 = float(np.percentile(fit_m2, 95))
print(f"Frozen rule reproduces M2 labels: {rule_matches_m2:.4f} of {len(labels)} releases")
print(f"M2 fit to own pattern (soft-DTW, lower = better): median {np.median(fit_m2):.3f}, 95th percentile {p95:.3f}")

# 2. Controlled bursts on every Steady Inactive release
si = [d for d, l in zip(details, labels) if NAMES[l] == "Steady Inactive"]
controlled = {}
print(f"\nControlled bursts: {len(si)} Steady Inactive releases, window = {WIDTH:.0%} of days, density {AMPLITUDE}")
print("position | still Steady Inactive | Early Active | Late Active | Steady Active | burst lost in sampling | fit worse than M2 95th pct")
for where in ("start", "middle", "end"):
    got, lost, poor = Counter(), 0, 0
    for repo, key, *_ in si:
        raw = ts[repo][key]["timeseries"]
        before, after = interpolate(raw), interpolate(with_burst(raw, where))
        if np.max(after - before) < 0.5 * AMPLITUDE:
            lost += 1  # the 10 samples barely see the window
        label, fit = classify(after)
        got[NAMES[label]] += 1
        poor += fit > p95
    n = len(si)
    controlled[where] = {"labels": dict(got), "burst_lost_in_sampling": lost, "fit_worse_than_m2_p95": int(poor), "n": n}
    print(f"{where:>8} | {got['Steady Inactive']/n:>21.1%} | {got['Early Active']/n:>12.1%} | {got['Late Active']/n:>11.1%} | "
          f"{got['Steady Active']/n:>13.1%} | {lost/n:>22.1%} | {poor/n:>25.1%}")

# 3. Real cases in the data
proj = defaultdict(list)
for l, (repo, key, *_) in zip(labels, details):
    proj[repo].append((int(key.split("-")[0]), key, NAMES[l]))
real = []
for repo, rels in proj.items():
    rels.sort()
    seq = [r[2] for r in rels]
    for i in range(2, len(rels)):
        if all(s == "Steady Inactive" for s in seq[:i]) and seq[i] != "Steady Inactive":
            raw = np.array(ts[repo][rels[i][1]]["timeseries"], float)
            k = max(1, int(round(0.2 * len(raw))))
            top = np.argsort(raw)[::-1][:k]
            label, fit = classify(interpolate(raw))
            real.append({
                "repo": repo, "release": rels[i][1], "release_index": i + 1, "releases": len(rels),
                "history": seq, "label": NAMES[label], "days": len(raw),
                "share_in_top20pct_days": round(float(raw[top].sum() / raw.sum()), 2) if raw.sum() > 0 else 0,
                "burst_position": round(float(np.mean(top) / max(1, len(raw) - 1)), 2),
                "fit": round(fit, 3), "fit_worse_than_m2_p95": fit > p95,
                "next_release_back_to_steady_inactive": i + 1 < len(seq) and seq[i + 1] == "Steady Inactive",
            })
            break
print(f"\nReal cases (first >= 2 releases Steady Inactive, then an active release): {len(real)}")
print("repo | release | label | days | share of density in top 20% of days | burst position (0 start, 1 end) | poor fit | next release back to SI")
for r in sorted(real, key=lambda r: -r["share_in_top20pct_days"]):
    print(f"{r['repo']} | {r['release_index']}/{r['releases']} | {r['label']} | {r['days']} | {r['share_in_top20pct_days']} | "
          f"{r['burst_position']} | {r['fit_worse_than_m2_p95']} | {r['next_release_back_to_steady_inactive']}")

json.dump({"rule_matches_m2": rule_matches_m2, "m2_fit_p95": p95, "width": WIDTH, "amplitude": AMPLITUDE,
           "controlled": controlled, "real_cases": real}, open(f"{OUT}/burst_test.json", "w"), indent=2)
