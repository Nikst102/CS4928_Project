"""Event B candidate response (option C): a burst indicator reported next to the pattern label.

STATUS: evaluated and REJECTED (event_b/EVENT_B.md). It is not used by the authors' pipeline.
With the threshold below, fixed before evaluation, it flags 82.6% of unmodified Steady Inactive
releases, because their few refactoring days are already "concentrated". So it cannot tell a new
burst apart from normal Steady Inactive activity. The tests show the function works as specified;
the rejection is about the idea, not a bug. Kept as evidence of the analysis.

Original rationale:

The frozen classification (10 evenly spaced samples + nearest M2 centroid) cannot be relied on to
show a concentrated window: in the controlled test (eventb_burst_test.py) 31-46% of Steady
Inactive releases with a burst kept their Steady Inactive label, up to 33% of bursts fell between
the 10 samples, and fewer than 1% of burst releases fitted their pattern worse than typical M2
releases. So the burst is measured separately, on the raw daily series, and reported next to the
label. The label and the authors' pipeline are not changed.

Threshold (set before it was evaluated): a release is "concentrated" when at least half of its
refactoring density falls in its busiest 20% of days.
"""
import numpy as np

TOP_SHARE_OF_DAYS = 0.20
CONCENTRATED_THRESHOLD = 0.50


def concentration(raw):
    """Share of a release's total refactoring density that falls in its busiest 20% of days.

    1.0 means all refactoring happened in a few days; about 0.2 means it was spread evenly.
    Returns 0.0 for a release with no refactoring at all.
    """
    days = np.asarray(raw, dtype=float)
    if days.size == 0 or days.sum() <= 0:
        return 0.0
    k = max(1, int(round(TOP_SHARE_OF_DAYS * days.size)))
    return float(np.sort(days)[::-1][:k].sum() / days.sum())


def burst_window(raw):
    """Where the busiest 20% of days sit, as (first, last) positions from 0 (start) to 1 (end)."""
    days = np.asarray(raw, dtype=float)
    if days.size < 2 or days.sum() <= 0:
        return None
    k = max(1, int(round(TOP_SHARE_OF_DAYS * days.size)))
    top = np.sort(np.argsort(days)[::-1][:k])
    return float(top[0] / (days.size - 1)), float(top[-1] / (days.size - 1))


def is_concentrated(raw):
    return concentration(raw) >= CONCENTRATED_THRESHOLD
