# Player Universe Strategy

## Correct source logic

The player universe should not be built from memory.

It should be built from three merged layers:

1. `Protected subset`
   - the 2026 Venezuela WBC team
2. `Recent entrants`
   - Venezuelan MLB debuts from 2020-2026
   - plus active-roster/no-debut players worth tracking
3. `Established veterans`
   - Venezuelan MLB players who debuted before 2020 but are still relevant in 2026

## What each layer contributes

### WBC 2026 protected subset

- Guarantees the report never loses sight of the national-team core

### Debut registry 2020-2026

- Catches younger and more recent players
- Reduces misses like `Francisco Alvarez`, `Gabriel Moreno`, and `Leo Rivas`

### Established veterans

- Captures players the debut source will never include because they debuted earlier
- Examples:
  - `Jose Altuve`
  - `Salvador Perez`
  - `Anthony Santander`
  - `Wilmer Flores`

## Review goal

The final curated universe should have:

- one record per player
- `must_track` flag
- `wbc_2026` flag
- role
- starter/reliever split for pitchers where applicable
- notes only when needed for ambiguity

## Recommended audit workflow

1. Merge the three layers into one draft
2. Dedupe by player identity
3. Review the final list in grouped audit form
4. Lock the curated universe and stop changing it frequently
