# Venezuelan Debut Registry Source

User-provided source in Spanish covering Venezuelan MLB debuts from `2020` through `2026`, plus:

- players on active MLB rosters without debuting
- players who accumulated MLB service time only via injured list placement

## Why this source matters

This is a strong candidate-generation source because it captures many recent Venezuelan MLB entrants that are easy to miss in a memory-based pass.

It is especially useful for:

- young or recent debut players
- borderline active-roster players
- catching misses in the broader draft

## Limits

This source is **not** by itself a full current-universe source because:

- it is centered on recent debuts, not all currently relevant Venezuelan MLB players
- it does not cover older established Venezuelan veterans who debuted before 2020
- it includes players who may no longer be relevant to a 2026-focused reporting universe
- the “active roster without debut” and “injured list only” sections need separate handling

## Build logic we should use

The reporting universe should come from merging:

1. `WBC 2026 protected subset`
2. `recent debut registry 2020-2026`
3. `older established Venezuelan MLB players still relevant in 2026`

Then we review manually and lock the curated list.
