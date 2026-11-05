"""M4 / RQ2: apply checks a and d to the seed 0-9 re-fits, with the old and the new naming.

Inputs:  results/m4/seeds/seed_<n>.json (from m4_run_seeds.py),
         results/m2/outputs/cluster_labels.json (M2 labels, authors' seed 9)
Outputs: results/m4/seeds_evaluation.json, printed table (save as results/m4/seeds_evaluation.txt)

Rules come from M1_PLAN.md (tag M1_PLAN):
  check a  each pattern share within 3 percentage points of the paper (section 6)
  check d  shape rule on the named centroids (section 6)
  RQ2      seed stability = mean ARI of seeds 0-8 against seed 9:
           >= 0.80 stable, 0.50-0.80 moderately stable, < 0.50 unstable
  RQ2      naming = number of seeds (of 10) where the hard-coded mapping gives a cluster a
           name that contradicts the shape rule

Run from the repository root:
    python m4_evaluate_seeds.py | tee results/m4/seeds_evaluation.txt
"""
import json
from collections import Counter

import numpy as np
from sklearn.metrics import adjusted_rand_score

import cluster_naming
from dataHelper import AUTHORS_CLUSTER_NAMES as OLD

PAPER = {"Early Active": 30, "Steady Inactive": 30, "Late Active": 23, "Steady Active": 17}
PATTERNS = list(PAPER)


def shares(labels, names):
    counts = Counter(names[l] for l in labels)
    return {p: 100 * counts[p] / len(labels) for p in PATTERNS}


def check_a(labels, names):
    return all(abs(s - PAPER[p]) <= 3 for p, s in shares(labels, names).items())


def shape_violations(centroids, names):
    """Names (under this naming) whose centroid breaks the shape rule."""
    c = {names[k]: np.ravel(centroids[k]) for k in range(4)}
    bad = []
    if not c["Early Active"][:3].mean() > c["Early Active"][-3:].mean():
        bad.append("Early Active")
    if not c["Late Active"][-3:].mean() > c["Late Active"][:3].mean():
        bad.append("Late Active")
    if not c["Steady Active"].mean() > c["Steady Inactive"].mean():
        bad.append("Steady Active/Inactive")
    return bad


m2_labels = json.load(open("results/m2/outputs/cluster_labels.json"))["cluster_label"]
m2_names = [OLD[l] for l in m2_labels]  # M2 names (verified by M2 check d)
runs = {s: json.load(open(f"results/m4/seeds/seed_{s}.json")) for s in range(10)}
seed9 = runs[9]["labels"]

rows = []
for seed, run in runs.items():
    labels, centroids = run["labels"], np.array(run["centroids"])
    new = cluster_naming.name_clusters(centroids)
    row = {
        "seed": seed,
        "new_names": {str(k): v for k, v in new.items()},
        "renumbered_vs_authors": new != OLD,
        "ari_vs_seed9": round(adjusted_rand_score(seed9, labels), 4),
        "ari_vs_m2": round(adjusted_rand_score(m2_labels, labels), 4),
        "shares_new_pct": {p: round(v, 1) for p, v in shares(labels, new).items()},
        "check_a_new": check_a(labels, new),
        "check_a_old": check_a(labels, OLD),
        "shape_violations_new": shape_violations(centroids, new),
        "shape_violations_old": shape_violations(centroids, OLD),
        "same_name_as_m2_new_pct": round(100 * np.mean([new[l] == m for l, m in zip(labels, m2_names)]), 1),
        "same_name_as_m2_old_pct": round(100 * np.mean([OLD[l] == m for l, m in zip(labels, m2_names)]), 1),
    }
    row["check_d_new"] = not row["shape_violations_new"]
    row["check_d_old"] = not row["shape_violations_old"]
    rows.append(row)

mean_ari = float(np.mean([r["ari_vs_seed9"] for r in rows if r["seed"] != 9]))
stability = "stable" if mean_ari >= 0.80 else "moderately stable" if mean_ari >= 0.50 else "unstable"
old_mislabel_seeds = sum(1 for r in rows if not r["check_d_old"])
summary = {
    "seed9_identical_to_m2": runs[9]["labels"] == m2_labels,
    "mean_ari_seeds0_8_vs_seed9": round(mean_ari, 4),
    "min_ari_vs_seed9": min(r["ari_vs_seed9"] for r in rows),
    "rq2_seed_stability": stability,
    "seeds_renumbered": sum(r["renumbered_vs_authors"] for r in rows),
    "seeds_where_old_mapping_breaks_shape_rule": old_mislabel_seeds,
    "seeds_passing_check_a_new": sum(r["check_a_new"] for r in rows),
    "seeds_passing_check_a_old": sum(r["check_a_old"] for r in rows),
    "seeds_passing_check_d_new": sum(r["check_d_new"] for r in rows),
    "seeds_passing_check_d_old": sum(r["check_d_old"] for r in rows),
}
json.dump({"summary": summary, "seeds": rows}, open("results/m4/seeds_evaluation.json", "w"), indent=2)

print("seed | ARI vs 9 | renumbered | check a old/new | check d old/new | same name as M2 old/new | shares (new naming) EA/SI/LA/SA")
for r in rows:
    s = r["shares_new_pct"]
    print(f"{r['seed']:>4} | {r['ari_vs_seed9']:>8.4f} | {str(r['renumbered_vs_authors']):>10} | "
          f"{str(r['check_a_old']):>5} / {str(r['check_a_new']):<5} | {str(r['check_d_old']):>5} / {str(r['check_d_new']):<5} | "
          f"{r['same_name_as_m2_old_pct']:>5.1f}% / {r['same_name_as_m2_new_pct']:>5.1f}% | "
          f"{s['Early Active']:.1f}/{s['Steady Inactive']:.1f}/{s['Late Active']:.1f}/{s['Steady Active']:.1f}")
print()
for k, v in summary.items():
    print(f"{k}: {v}")
