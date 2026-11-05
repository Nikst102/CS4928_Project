"""M4 / RQ2: re-fit the authors' clustering for random seeds 0-9 (all 1,604 releases).

Same method as M2 (Soft-DTW k-means, k = 4, 10-point interpolation, releases with
more than 3 data points); only `random_state` changes. This script saves the raw
output of each fit (labels and centroids) and nothing else: naming and the checks
are applied afterwards by m4_evaluate_seeds.py.

Run from the repository root after `unzip data.zip`:
    python m4_run_seeds.py            (seeds 0-9)
    python m4_run_seeds.py 9 8 7      (only these seeds, e.g. to split the work over two processes)
Writes results/m4/seeds/seed_<n>.json (skips seeds that already have a file).
About 5-10 minutes per seed.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

from tslearn.clustering import TimeSeriesKMeans

from clustering import Clustering

OUT_DIR = "results/m4/seeds"
os.makedirs(OUT_DIR, exist_ok=True)
series = Clustering().interpolated_release_time_series
print("releases:", len(series), flush=True)

seeds = [int(a) for a in sys.argv[1:]] or list(range(10))
for seed in seeds:
    path = f"{OUT_DIR}/seed_{seed}.json"
    if os.path.exists(path):
        print(f"seed {seed}: already done", flush=True)
        continue
    start = time.time()
    model = TimeSeriesKMeans(n_clusters=4, metric="softdtw", n_jobs=-1, random_state=seed).fit(series)
    result = {
        "seed": seed,
        "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seconds": round(time.time() - start, 1),
        "n_iter": int(model.n_iter_),
        "labels": model.labels_.tolist(),
        "centroids": model.cluster_centers_.reshape(4, -1).tolist(),
    }
    with open(path, "w") as f:
        json.dump(result, f)
    print(f"seed {seed}: {result['seconds']} s, {result['n_iter']} iterations", flush=True)
print("all seeds done", flush=True)
