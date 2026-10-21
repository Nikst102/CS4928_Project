"""M2 / RQ1: apply the decision rule frozen in M1_PLAN.md (section 6) to the run output.

Inputs (run m2_run_rq1.py first):
    data/softdtw/cluster_labels.json   our labels for the 1,604 releases
    data/softdtw/cluster_center.json   our four centroids
    data/feature_categories.json       the authors' shipped labels ("labels")
    results/m2/rq1_run.log             contains the printed silhouette score

Outputs:
    results/m2/rq1_evaluation.json     every number below, machine-readable
    printed summary                    copy into results/m2/rq1_evaluation.txt

Run from the repository root:
    python m2_evaluate_rq1.py | tee results/m2/rq1_evaluation.txt
"""
import json
import re
from collections import Counter

import numpy as np
from sklearn.metrics import adjusted_rand_score

from dataHelper import rename_cluster  # the authors' hard-coded cluster-number -> name mapping

PAPER_SHARES = {"Early Active": 30, "Steady Inactive": 30, "Late Active": 23, "Steady Active": 17}
PAPER_SILHOUETTE = 0.30
PATTERNS = list(PAPER_SHARES)

# Thresholds frozen in M1_PLAN.md, section 6.
SHARE_PASS, SHARE_FAIL = 3, 10           # percentage points
ARI_PASS, ARI_FAIL = 0.80, 0.50
SILHOUETTE_TOLERANCE = 0.05

ours = json.load(open("data/softdtw/cluster_labels.json"))
our_labels = ours["cluster_label"]
centres = json.load(open("data/softdtw/cluster_center.json"))
authors_labels = json.load(open("data/feature_categories.json"))["labels"]
log = open("results/m2/rq1_run.log").read()
after_marker = log.split("the first number is the silhouette score ---", 1)[1]
silhouette = float(re.search(r"^\s*(-?\d+\.\d+)\s*$", after_marker, re.M).group(1))

n = len(our_labels)
assert n == len(authors_labels) == 1604, (n, len(authors_labels))

# a. Distribution, using the authors' mapping
counts = Counter(rename_cluster(label) for label in our_labels)
shares = {p: round(100 * counts[p] / n, 1) for p in PATTERNS}
share_gaps = {p: round(abs(shares[p] - PAPER_SHARES[p]), 1) for p in PATTERNS}
check_a = all(gap <= SHARE_PASS for gap in share_gaps.values())

# b. Agreement with the authors' shipped labels (ARI is invariant to cluster numbering)
ari = adjusted_rand_score(authors_labels, our_labels)
check_b = ari >= ARI_PASS

# c. Separation
check_c = abs(silhouette - PAPER_SILHOUETTE) <= SILHOUETTE_TOLERANCE

# d. Shape rule on centroids, named by the authors' mapping
shape = {}
for cluster_id, centre in centres.items():
    values = np.array(centre).ravel()
    shape[rename_cluster(cluster_id)] = {
        "cluster_id": int(cluster_id),
        "first3_mean": round(float(values[:3].mean()), 4),
        "last3_mean": round(float(values[-3:].mean()), 4),
        "overall_mean": round(float(values.mean()), 4),
        "centroid": [round(float(v), 4) for v in values],
    }
shape_checks = {
    "Early Active: first3 > last3": shape["Early Active"]["first3_mean"] > shape["Early Active"]["last3_mean"],
    "Late Active: last3 > first3": shape["Late Active"]["last3_mean"] > shape["Late Active"]["first3_mean"],
    "Steady Active mean > Steady Inactive mean":
        shape["Steady Active"]["overall_mean"] > shape["Steady Inactive"]["overall_mean"],
}
check_d = all(shape_checks.values())

# Outcome, exactly as in M1_PLAN.md section 6
if check_a and check_b and check_c and check_d:
    outcome = "Reproduced"
elif ari < ARI_FAIL or any(gap > SHARE_FAIL for gap in share_gaps.values()) or not check_d:
    outcome = "Not reproduced"
else:
    outcome = "Partially reproduced"

# Supplementary diagnostics (not part of the decision rule)
exact_match = sum(a == b for a, b in zip(authors_labels, our_labels)) / n
confusion = Counter((rename_cluster(a), rename_cluster(b)) for a, b in zip(authors_labels, our_labels))

result = {
    "n_releases": n,
    "a_distribution": {"our_counts": {p: counts[p] for p in PATTERNS}, "our_shares_pct": shares,
                       "paper_shares_pct": PAPER_SHARES, "gap_pp": share_gaps, "pass": check_a},
    "b_agreement": {"adjusted_rand_index": round(ari, 4), "pass": check_b},
    "c_separation": {"silhouette": round(silhouette, 4), "paper": PAPER_SILHOUETTE, "pass": check_c},
    "d_shape": {"centroids": shape, "checks": shape_checks, "pass": check_d},
    "outcome": outcome,
    "supplementary": {
        "exact_label_match_with_authors": round(exact_match, 4),
        "confusion_authors_vs_ours": {f"{a} -> {b}": c for (a, b), c in sorted(confusion.items())},
    },
}
json.dump(result, open("results/m2/rq1_evaluation.json", "w"), indent=2)

print(f"Releases: {n}")
print("\na. Distribution (authors' mapping)          ours    paper   gap")
for p in PATTERNS:
    print(f"   {p:<18} {counts[p]:>5} releases  {shares[p]:>5.1f}%  {PAPER_SHARES[p]:>4}%  {share_gaps[p]:>4.1f} pp")
print(f"   pass (all gaps <= {SHARE_PASS} pp): {check_a}")
print(f"\nb. ARI vs authors' shipped labels: {ari:.4f}   pass (>= {ARI_PASS}): {check_b}")
print(f"\nc. Silhouette: {silhouette:.4f} (paper {PAPER_SILHOUETTE})   pass (within {SILHOUETTE_TOLERANCE}): {check_c}")
print("\nd. Centroid shape (first-3 mean / last-3 mean / overall mean)")
for p in PATTERNS:
    s = shape[p]
    print(f"   {p:<18} cluster {s['cluster_id']}: {s['first3_mean']:.4f} / {s['last3_mean']:.4f} / {s['overall_mean']:.4f}")
for name, ok in shape_checks.items():
    print(f"   {name}: {ok}")
print(f"   pass: {check_d}")
print(f"\nOUTCOME: {outcome}")
print(f"\nSupplementary: exact label match with authors = {exact_match:.4f}")
for (a, b), c in sorted(confusion.items()):
    print(f"   authors {a:<16} -> ours {b:<16} {c}")
