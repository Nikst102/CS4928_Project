"""Tests for the M4 design change (cluster_naming.py and dataHelper.rename_cluster).

Run from the repository root:
    python -m unittest discover -s tests -v
Uses only committed files (no need to unzip data.zip): results/m2/outputs/cluster_center.json,
results/m2/outputs/cluster_labels.json, event_a/results/refit_centroids.npy,
event_a/results/eventa_result.json and reference_patterns.json.
"""
import itertools
import json
import os
import sys
import unittest

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import cluster_naming  # noqa: E402
import dataHelper  # noqa: E402

AUTHORS = dataHelper.AUTHORS_CLUSTER_NAMES


def m2_centroids():
    with open(os.path.join(ROOT, "results/m2/outputs/cluster_center.json")) as f:
        centres = json.load(f)
    return np.array([np.ravel(centres[str(k)]) for k in range(4)])


def shape_rule_holds(names, centroids):
    """The shape rule frozen in M1_PLAN.md, section 6, applied to named centroids."""
    by_name = {names[k]: np.ravel(centroids[k]) for k in range(4)}
    early, late = by_name["Early Active"], by_name["Late Active"]
    return (early[:3].mean() > early[-3:].mean()
            and late[-3:].mean() > late[:3].mean()
            and by_name["Steady Active"].mean() > by_name["Steady Inactive"].mean())


class BehaviourPreserved(unittest.TestCase):
    """Under the authors' seed-9 clustering nothing changes."""

    def test_m2_centroids_get_the_authors_names(self):
        self.assertEqual(cluster_naming.name_clusters(m2_centroids()), AUTHORS)

    def test_all_1604_m2_releases_keep_their_name(self):
        with open(os.path.join(ROOT, "results/m2/outputs/cluster_labels.json")) as f:
            labels = json.load(f)["cluster_label"]
        new_names = cluster_naming.name_clusters(m2_centroids())
        self.assertEqual(len(labels), 1604)
        self.assertEqual([dataHelper.rename_cluster(l, new_names) for l in labels],
                         [dataHelper.rename_cluster(l) for l in labels])

    def test_rename_cluster_without_names_behaves_as_before(self):
        for cluster_id, name in [(0, "Early Active"), ("0", "Early Active"), (1, "Steady Active"),
                                 ("2", "Late Active"), (3, "Steady Inactive"), (np.int64(3), "Steady Inactive")]:
            self.assertEqual(dataHelper.rename_cluster(cluster_id), name)
        for bad in (4, "x", None):
            with self.assertRaises(ValueError):
                dataHelper.rename_cluster(bad)


class ProblemFixed(unittest.TestCase):
    """When the cluster numbers change, the names follow the shapes."""

    def test_every_renumbering_of_m2_clusters_is_named_correctly(self):
        centroids = m2_centroids()
        for order in itertools.permutations(range(4)):  # all 24 possible numberings
            names = cluster_naming.name_clusters(centroids[list(order)])
            self.assertEqual(names, {new: AUTHORS[old] for new, old in enumerate(order)})

    def test_event_a_refit_swap_is_named_correctly(self):
        refit = np.load(os.path.join(ROOT, "event_a/results/refit_centroids.npy")).reshape(4, -1)
        names = cluster_naming.name_clusters(refit)
        # Event A found re-fit cluster 0 = M2 Steady Inactive and 3 = M2 Early Active
        self.assertEqual(names, {0: "Steady Inactive", 1: "Steady Active", 2: "Late Active", 3: "Early Active"})
        self.assertTrue(shape_rule_holds(names, refit))
        self.assertFalse(shape_rule_holds(AUTHORS, refit))  # the old mapping gets this re-fit wrong

    def test_names_are_one_to_one(self):
        refit = np.load(os.path.join(ROOT, "event_a/results/refit_centroids.npy")).reshape(4, -1)
        self.assertEqual(sorted(cluster_naming.name_clusters(refit).values()), sorted(AUTHORS.values()))

    def test_wrong_centroid_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            cluster_naming.name_clusters(np.zeros((3, 10)))


if __name__ == "__main__":
    unittest.main()
