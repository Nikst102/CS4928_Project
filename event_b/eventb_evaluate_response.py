"""Event B: compare the pre-Event-B state (pattern label only) with the response (label + burst indicator).

Uses the same controlled bursts and real cases as eventb_burst_test.py, plus every unmodified
M2 release as a baseline for false alarms. The classification and the M2 labels are not changed.

Run from the repository root after `unzip data.zip` (and after eventb_burst_test.py):
    python event_b/eventb_evaluate_response.py | tee event_b/results/response_evaluation.txt
Writes event_b/results/response_evaluation.json.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import burst_indicator as bi  # noqa: E402
import eventb_burst_test as bt  # noqa: E402  (re-runs the frozen classification test; same output)

print("\n" + "=" * 100)
print(f"Response: burst indicator (concentrated if >= {bi.CONCENTRATED_THRESHOLD:.0%} of density in busiest "
      f"{bi.TOP_SHARE_OF_DAYS:.0%} of days), reported next to the unchanged label")

# Baseline: how often the indicator fires on unmodified releases
m2_flags = {}
for name in ("Early Active", "Late Active", "Steady Active", "Steady Inactive"):
    rel = [d for d, l in zip(bt.details, bt.labels) if bt.NAMES[l] == name]
    m2_flags[name] = float(np.mean([bi.is_concentrated(bt.ts[r][k]["timeseries"]) for r, k, *_ in rel]))
all_flag = float(np.mean([bi.is_concentrated(bt.ts[r][k]["timeseries"]) for r, k, *_ in bt.details]))
print("\nUnmodified M2 releases flagged as concentrated (baseline):")
for name, share in m2_flags.items():
    print(f"   {name:<16} {share:.1%}")
print(f"   all 1,604        {all_flag:.1%}")

# Controlled bursts: label only vs label + indicator
rows = {}
print("\nControlled bursts on Steady Inactive releases: share where the burst is visible")
print("position | before (label changes from Steady Inactive) | after (label changes OR indicator fires) | indicator alone")
si_unmodified_flagged = np.array([bi.is_concentrated(bt.ts[r][k]["timeseries"]) for r, k, *_ in bt.si])
for where in ("start", "middle", "end"):
    label_moved, flagged = [], []
    for repo, key, *_ in bt.si:
        raw = bt.with_burst(bt.ts[repo][key]["timeseries"], where)
        label, _ = bt.classify(bt.interpolate(raw))
        label_moved.append(bt.NAMES[label] != "Steady Inactive")
        flagged.append(bi.is_concentrated(raw))
    label_moved, flagged = np.array(label_moved), np.array(flagged)
    rows[where] = {"before_label_only": float(label_moved.mean()),
                   "after_label_or_indicator": float((label_moved | flagged).mean()),
                   "indicator_alone": float(flagged.mean()),
                   "newly_flagged_hidden_by_label": int((flagged & ~label_moved & ~si_unmodified_flagged).sum()),
                   "n": len(bt.si)}
    print(f"{where:>8} | {label_moved.mean():>43.1%} | {(label_moved | flagged).mean():>40.1%} | {flagged.mean():>15.1%}")

# Real cases
print("\nReal cases (Steady Inactive history, then one active release):")
real = []
for r in bt.real:
    raw = bt.ts[r["repo"]][r["release"]]["timeseries"]
    c, w = bi.concentration(raw), bi.burst_window(raw)
    real.append({**r, "concentration": round(c, 2), "concentrated": c >= bi.CONCENTRATED_THRESHOLD,
                 "window": None if w is None else [round(w[0], 2), round(w[1], 2)]})
flagged_real = [r for r in real if r["concentrated"]]
isolated = [r for r in flagged_real if r["next_release_back_to_steady_inactive"]]
print(f"   flagged as concentrated: {len(flagged_real)} of {len(real)}")
print(f"   of those, next release back to Steady Inactive (isolated burst): {len(isolated)}")
for r in sorted(flagged_real, key=lambda r: -r["concentration"]):
    print(f"   {r['repo']} release {r['release_index']}/{r['releases']}: label {r['label']}, concentration {r['concentration']}, "
          f"window {r['window']}, next release back to SI: {r['next_release_back_to_steady_inactive']}")

json.dump({"threshold": bi.CONCENTRATED_THRESHOLD, "top_share_of_days": bi.TOP_SHARE_OF_DAYS,
           "baseline_flag_rate": {"by_pattern": m2_flags, "all": all_flag},
           "controlled": rows, "real_cases": real},
          open(os.path.join(bt.OUT, "response_evaluation.json"), "w"), indent=2)
