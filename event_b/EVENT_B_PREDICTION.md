# Event B prediction (written before any Event B analysis)

CS4928 group project, G07 / P10. Starting state: tag `PRE_EVENT_B` (commit `647d038`).

**Event B:** a project previously classified as Steady Inactive now has one release with a
concentrated maintenance/refactoring window. Is it healthy refactoring, deferred debt or an
architectural warning?

## What part of the current design we expect it to affect

The **classification step**: our Week 9 naming (`cluster_naming.name_clusters`) plus
nearest-centroid assignment of a release to one of the four M2 patterns.

1. **It always picks one of the four patterns.** A release with a short, concentrated burst does
   not look like any of them, but it will still be given a name, with no warning that the fit is
   poor. A burst near the start should become Early Active, a burst near the end Late Active, and
   a burst in the middle will be forced into whichever pattern happens to be nearest.
2. **The 10-point interpolation smooths short windows,** so a burst of a few days is partly
   averaged away before classification.
3. **Nothing in the design looks at project history.** The pattern is per release, so the change
   from "Steady Inactive" to "one active release" is invisible to the code; deciding between
   healthy refactoring, deferred debt and an architectural warning is left to manual reading.

## Expected result

- Burst releases will be classified as an active pattern (Early or Late Active, depending on where
  the window is), and their distance to the nearest centroid will be larger than for typical M2
  releases (above the M2 95th percentile).
- A middle-of-release burst will be the least stable case: its label will depend on how large the
  burst is.

## Would challenge the Week 9 decision

- If nearest-centroid naming gives burst releases a label that contradicts where the burst is (for
  example an early burst named Late Active), the Week 9 naming decision is only partly supported.
- If burst releases are not distinguishable from typical releases by their distance to the nearest
  centroid, a "poor fit" flag would not help, and no structural change is justified.
