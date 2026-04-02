# Feature Log

This document tracks near-term improvements to the Venezuelan MLB daily report app.

## Current priorities

### 1. Pipeline resilience

Status: next up

Goal:
- Make the daily run more reliable when MLB or network calls fail temporarily.

Current problem:
- The April 2 scheduled run failed before the site rebuild because of a transient DNS / `URLError` during the first MLB API lookup.

Planned work:
- Add retries with backoff around MLB API calls
- Add better logging around which request failed
- Consider a fallback mode that preserves the last successful site output when a fresh pull fails

Success looks like:
- A short-lived network issue does not cause the entire morning publish to fail

### 2. Mobile-friendly report layout

Status: queued

Goal:
- Make the report easier to use on phone screens.

Current problem:
- The snapshot tables are wide, and horizontal scrolling is awkward on mobile.

Planned work:
- Explore freezing the player column while allowing horizontal scroll on the stat columns
- Review whether this should apply only to the hosted web version and not the email version
- Tighten spacing and column widths where possible

Success looks like:
- Player identity stays visible while scrolling across the stat groups on mobile

### 3. Notes coverage and note quality

Status: queued

Goal:
- Improve the `Last Night` note column so it shows more useful linked notes without adding noise.

Current problem:
- The current matching logic is too strict and often produces no notes.

Planned work:
- Revisit the source allowlist and matching thresholds
- Improve game-level matching for `MLB.com` and allowed national outlets
- Keep notes selective, linked, and short

Success looks like:
- More players who appeared last night get relevant linked notes, with low false-positive noise

### 4. Status label tuning

Status: queued

Goal:
- Improve the `Hot`, `Steady`, `Cooling off`, and `Slump` labels so they feel more intuitive.

Current problem:
- The current rules are useful, but some labels do not yet feel fully aligned with baseball intuition.

Planned work:
- Revisit thresholds separately for batters, starters, and relievers
- Compare `T7D` to both `YTD` and career with better weighting
- Reassess minimum-sample handling so small samples do not overreact

Success looks like:
- The labels feel credible on a quick read and match our baseball instincts more often

## Parking lot

- League percentile context
- Similar player cohort comparisons
- More interactive web filtering and sorting
- Email delivery automation
