# Tracking Filter

The player universe and the daily report should not be the same thing.

## Two layers

### 1. Universe

Every Venezuelan MLB player we want to retain in the master list.

### 2. Daily tracking set

The players who appear by default in nightly pulls and the email report.

## Default filter

### Batters

- include if `plate appearances >= 25` this season
- or player is in `wbc_2026_venezuela`
- or player appeared in MLB during the last `14` days
- or player is manually pinned

### Pitchers

- include if `innings pitched >= 8.0` this season
- or, for relievers, `appearances >= 5`
- or player is in `wbc_2026_venezuela`
- or player appeared in MLB during the last `21` days
- or player is manually pinned

## Why this helps

- keeps fringe bench players from bloating the report
- keeps the WBC core protected
- still allows recent callups to surface
- lets us preserve a comprehensive universe without flooding the daily email

## Next tuning questions

- whether batter threshold should be `20`, `25`, or `30` PA
- whether starter threshold should be based on innings or starts
- whether relievers need a separate innings threshold in addition to appearances
