# MVP Plan

## Product shape

The first version is an email-style daily report for a curated, mostly stable list of Venezuelan MLB players.

The report is split into four sections:

1. Batters: Last Night
2. Pitchers: Last Night
3. Batters: Full Snapshot
4. Pitchers: Full Snapshot

## Core concepts

- The player universe is curated once, then reviewed manually when needed
- Batter and pitcher logic remain separate throughout the pipeline
- Every player is compared across:
  - `T7D`
  - `YTD`
  - `Historical baseline`
- Every player gets a status label:
  - `Hot`
  - `Steady`
  - `Cooling off`
  - `Slump`

## Data strategy

### One-time setup

- Pull an initial candidate list of Venezuelan MLB players
- Review and trim the list manually
- Store the approved universe locally
- Backfill historical season aggregates for each player

### Nightly workflow

- Pull previous-night appearances for the curated player list
- Refresh season-to-date stats
- Recompute trailing 7 day windows
- Compare T7D to YTD and historical baseline
- Render the daily report

## MVP implementation order

1. Curated player universe
2. SQLite schema
3. Historical backfill layer
4. Nightly prior-game ingest
5. Labeling engine
6. Email-style report rendering
7. Report persistence and scheduling

## Post MVP

- Send the report by email automatically
- Add league percentile context
- Add clickability and filtering
- Compare players to similar cohorts
