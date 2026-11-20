"""Tests for the Event B burst indicator (event_b/burst_indicator.py).

Run from the repository root:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "event_b"))

import burst_indicator as bi  # noqa: E402


class Concentration(unittest.TestCase):
    def test_even_refactoring_is_not_concentrated(self):
        self.assertAlmostEqual(bi.concentration([0.1] * 20), 0.2)
        self.assertFalse(bi.is_concentrated([0.1] * 20))

    def test_single_window_is_concentrated(self):
        release = [0.0] * 18 + [0.6, 0.6]
        self.assertAlmostEqual(bi.concentration(release), 1.0)
        self.assertTrue(bi.is_concentrated(release))

    def test_threshold_boundary(self):
        # busiest 2 of 10 days hold exactly half of the density
        release = [0.5, 0.5] + [0.125] * 8
        self.assertAlmostEqual(bi.concentration(release), 0.5)
        self.assertTrue(bi.is_concentrated(release))

    def test_no_refactoring(self):
        self.assertEqual(bi.concentration([0, 0, 0, 0]), 0.0)
        self.assertEqual(bi.concentration([]), 0.0)
        self.assertIsNone(bi.burst_window([0, 0, 0]))

    def test_short_release_uses_at_least_one_day(self):
        self.assertAlmostEqual(bi.concentration([0.0, 0.0, 1.0, 0.0]), 1.0)


class Window(unittest.TestCase):
    def test_window_position(self):
        start = [0.6, 0.6] + [0.0] * 8
        end = [0.0] * 8 + [0.6, 0.6]
        middle = [0.0] * 4 + [0.6, 0.6] + [0.0] * 4
        self.assertEqual(bi.burst_window(start), (0.0, 1 / 9))
        self.assertEqual(bi.burst_window(end), (8 / 9, 1.0))
        self.assertEqual(bi.burst_window(middle), (4 / 9, 5 / 9))


if __name__ == "__main__":
    unittest.main()
