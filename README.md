# Venezuelan MLB Daily Report

This project generates a daily email-style report for a curated list of Venezuelan MLB players.

The MVP is designed around four sections:

1. Batters: Last Night
2. Pitchers: Last Night
3. Batters: Full Snapshot
4. Pitchers: Full Snapshot

Each player can be labeled as:

- `Hot`
- `Steady`
- `Cooling off`
- `Slump`

## Project goals

- Keep a stable, curated player list with occasional human review
- Separate hitter and pitcher logic from the beginning
- Compare each player across three windows:
  - trailing 7 days
  - year to date
  - historical baseline
- Produce an email-style report first, then add delivery later

## Layout

- `data/player_universe.sample.json`: starter curated player list format
- `src/venezuelan_mlb_report/models.py`: report and stat models
- `src/venezuelan_mlb_report/storage.py`: SQLite schema bootstrap
- `src/venezuelan_mlb_report/labels.py`: rules engine for Hot/Steady/Cooling off/Slump
- `src/venezuelan_mlb_report/report.py`: report rendering
- `src/venezuelan_mlb_report/sample_data.py`: seeded sample data for local iteration

## Quick start

```bash
cd /Users/lcaballer1/Documents/venezuelan-mlb-report
PYTHONPATH=src python3 -m venezuelan_mlb_report sample-report
PYTHONPATH=src python3 -m venezuelan_mlb_report init-db
```

## Static Site Output

The project can publish a host-ready static site folder.

Example:

```bash
PYTHONPATH=src python3 -m venezuelan_mlb_report build-live-report \
  --season 2026 \
  --as-of-date 2026-04-01 \
  --live-input var/live_player_stats.json \
  --history-input var/historical_player_stats_full.json \
  --output var/live_report.html \
  --publish-site-dir site
```

This writes:

- `site/index.html`: latest report
- `site/reports/YYYY-MM-DD.html`: dated archive page

That `site/` folder is the one to deploy to static hosting.

## Daily Pipeline

The project also supports a single daily pipeline command that refreshes live data,
reuses or refreshes history, rebuilds the report, republishes the static site, and
optionally pushes the updated `site/` output to GitHub for Cloudflare Pages.

Example:

```bash
PYTHONPATH=src python3 -m venezuelan_mlb_report run-daily \
  --season 2026 \
  --as-of-date 2026-04-01 \
  --history-mode if-missing \
  --publish-site-dir site \
  --git-push
```

If `--git-push` is used, only the `site/` output is staged, committed, and pushed.
That keeps deployment changes separate from any in-progress code edits in the repo.

## MVP roadmap

- Replace sample data with MLB data ingestion
- Add one-time historical backfill per player
- Add nightly refresh for prior-night performances
- Export email-ready HTML/Markdown output
- Add delivery automation post MVP

## Current note

This machine currently reports missing Apple command line developer tools when invoking `/usr/bin/python3`, so the project scaffold is in place but runtime verification is blocked until Python is usable in the local environment.
