"""M2 / RQ1: run the authors' clustering exactly as preregistered in M1_PLAN.md.

`main.py` cannot be used because it imports `releaseQuality`, which is missing
from the replication package (M1_PLAN.md, section 9, item 1). This script calls
the same RQ1 entry point that `main.py` would call, with the authors' defaults
and no code changes: k = 4, metric "softdtw", random_state = 9.

Run from the repository root after `unzip data.zip`:
    MPLBACKEND=Agg python m2_run_rq1.py | tee results/m2/rq1_run.log

Outputs written by the authors' code:
    data/softdtw/cluster_center.json, cluster_labels.json,
    label_timeseries.json, label_operations.json,
    feature_distributions.json, operations-patterns.csv
    images/release-patterns.png, images/radar_plots.png (overwrites the authors' copies)
"""
import platform
import sys
import time
from datetime import datetime, timezone

import matplotlib
import numpy
import pandas
import scipy
import seaborn
import sklearn
import tslearn

from clustering import Clustering

print("started (UTC):", datetime.now(timezone.utc).isoformat(timespec="seconds"))
print("python:", sys.version.split()[0], "| platform:", platform.platform())
print("numpy", numpy.__version__, "| scipy", scipy.__version__, "| tslearn", tslearn.__version__,
      "| scikit-learn", sklearn.__version__, "| pandas", pandas.__version__,
      "| matplotlib", matplotlib.__version__, "| seaborn", seaborn.__version__)

start = time.time()
clustering = Clustering()
print("releases clustered:", len(clustering.interpolated_release_time_series))
print("--- authors' cluster_and_analyze() output follows; the first number is the silhouette score ---")
clustering.cluster_and_analyze()  # authors' defaults: random_state=9, k=4, softdtw
print("--- end of authors' output ---")
print("elapsed seconds:", round(time.time() - start, 1))
