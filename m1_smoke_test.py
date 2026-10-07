"""M1 feasibility smoke test (run BEFORE the M1_PLAN freeze).

Purpose: confirm that the authors' Soft-DTW k-means step executes in our
environment and estimate its runtime. It is NOT the reproduction:
it uses 200 randomly chosen releases and seed 123 (not the paper's
1,604 releases / seed 9), and the resulting labels are discarded.

Run from the repository root after `unzip data.zip`:
    python m1_smoke_test.py
"""
import time

import numpy as np
from tslearn.clustering import TimeSeriesKMeans

from clustering import Clustering

start = time.time()
clustering = Clustering()
series = clustering.interpolated_release_time_series
print("load + interpolate (s):", round(time.time() - start, 1), "shape:", series.shape)

rng = np.random.default_rng(123)
subset = series[rng.choice(len(series), 200, replace=False)]

start = time.time()
model = TimeSeriesKMeans(n_clusters=4, metric="softdtw", n_jobs=-1, random_state=123).fit(subset)
print("fit on 200 releases (s):", round(time.time() - start, 1),
      "| iterations:", model.n_iter_, "| labels produced:", len(model.labels_))
