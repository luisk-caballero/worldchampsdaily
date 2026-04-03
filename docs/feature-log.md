# Feature Log

This document tracks near-term improvements to the Venezuelan MLB daily report app.

## Current priorities

### 1. Additional mobile width optimization (player column)

Status: next up

Goal:
- Keep the sticky player column, but reclaim a bit more width for numeric columns on phones.

Current problem:
- The new sticky player column works well, but still consumes more space than ideal on narrower phone screens.

Planned work:
- Trim player cell width and spacing further while keeping names readable
- Test that name + full "Last Night" stat line remain easy to scan in one horizontal pass
- Keep sticky behavior in both last-night and snapshot tables

Success looks like:
- Better number visibility on mobile without losing player context

### 2. Seed list revision (add newly identified player)

Status: next up

Goal:
- Keep the tracked universe current when a new Venezuelan MLB player appears.

Current problem:
- One new player needs to be added to the seed and tracking flow.

Planned work:
- Add the player to the universe seed file
- Assign role/subrole and initial tracking tier
- Re-run live pull and validate they appear correctly in the report pipeline

Success looks like:
- The new player is present in snapshots and eligible for report inclusion by rules

### 3. Notes coverage and note quality

Status: done (locked for current strategy)

Goal:
- Improve the `Last Night` note column so it shows more useful linked notes without adding noise.

Current problem:
- Notes are intentionally conservative by design and may be blank for non-headline performances.

Planned work:
- Keep current approach:
- `MLB.com`: headline + blurb only
- Other outlets: equivalent short metadata only (headline + short description)
- No full-article parsing

Success looks like:
- Notes stay high-signal and worth clicking, even if coverage volume is lower

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

### 5. Pipeline resilience hardening (follow-up)

Status: partially done

Goal:
- Keep daily runs robust under transient MLB/network instability.

Current problem:
- Retries are now in place, but we still need stronger fallback behavior if an entire run fails.

Done:
- Added retries with backoff and timeouts for MLB API pulls
- Added retry handling for external note RSS requests

Planned work:
- Add fallback mode to keep last successful publish when live pull fails
- Improve failure visibility in automation output with clearer per-step diagnostics

Success looks like:
- Transient outages are absorbed; hard failures still preserve a usable published report

## Completed recently

- Mobile-first sticky player column implemented for horizontal table scrolling
- Narrower last-night table columns (`Opp`, tighter padding, reduced min widths)
- Daily pipeline retries added for API and note-source calls

## Parking lot

- League percentile context
- Similar player cohort comparisons
- More interactive web filtering and sorting
- Email delivery automation
