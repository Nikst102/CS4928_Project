"""Name clusters by their shape instead of by their cluster number (M4 design change).

Problem (M4_DESIGN.md, section 2): the authors' `dataHelper.rename_cluster` maps cluster
*numbers* to pattern names. k-means numbers its clusters arbitrarily, so the numbers
change with the seed or the data (Event A: removing 8 projects swapped clusters 0 and 3)
and the patterns are then silently mislabelled.

Fix: give each new cluster the name of the reference pattern whose centroid it is
closest to, one-to-one. The reference centroids are the M2 ones (reference_patterns.json),
whose names M2 check d verified against the shape rule.
"""
import json
import os

import numpy as np
from scipy.optimize import linear_sum_assignment

REFERENCE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference_patterns.json")
CLUSTER_NAMES_FILE = "data/softdtw/cluster_names.json"


def load_reference(path=REFERENCE_FILE):
    """Return (names, centroids): pattern names and a (k, length) array of their centroids."""
    with open(path) as f:
        patterns = json.load(f)["patterns"]
    names = list(patterns)
    return names, np.array([patterns[name] for name in names], dtype=float)


def name_clusters(centroids, reference_path=REFERENCE_FILE):
    """Map each cluster number to a pattern name by nearest reference centroid.

    centroids: one centroid per cluster, in cluster-number order (any shape that
    reshapes to (k, length), e.g. TimeSeriesKMeans.cluster_centers_).
    Returns {cluster_number: pattern_name}. The assignment is one-to-one (Hungarian
    algorithm on Euclidean distance), so two clusters can never get the same name.
    """
    names, reference = load_reference(reference_path)
    centroids = np.asarray(centroids, dtype=float).reshape(len(centroids), -1)
    if centroids.shape != reference.shape:
        raise ValueError(f"expected centroids of shape {reference.shape}, got {centroids.shape}")
    cost = np.linalg.norm(centroids[:, None, :] - reference[None, :, :], axis=2)
    rows, cols = linear_sum_assignment(cost)
    return {int(r): names[c] for r, c in zip(rows, cols)}


def save_cluster_names(mapping, path=CLUSTER_NAMES_FILE):
    with open(path, "w") as f:
        json.dump({str(k): v for k, v in sorted(mapping.items())}, f, indent=2)


def load_cluster_names(path=CLUSTER_NAMES_FILE):
    """Names written by the last clustering run, or None if there is no such file."""
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return {int(k): v for k, v in json.load(f).items()}
