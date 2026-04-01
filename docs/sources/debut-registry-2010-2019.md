# Venezuelan Debut Registry Source

User-provided source in Spanish covering Venezuelan MLB debuts from `2010` through `2019`.

## Why this source matters

This fills the exact hole left by the 2020-2026 debut registry:

- established veterans who debuted before 2020
- mid-career players still relevant in 2026
- players who are easy to miss if we only look at recent debuts

Examples captured here include:

- `Jose Altuve`
- `Salvador Perez`
- `Anthony Santander`
- `Ronald Acuna Jr.`
- `Gleyber Torres`
- `Pablo Lopez`
- `Ranger Suarez`
- `Luis Arraez`

## Build implication

With both debut registries now available:

- `2010-2019`
- `2020-2026`

we now have a much more comprehensive candidate-generation base.

The remaining work is no longer “find names from memory.”
It is:

1. merge the two debut registries
2. merge the protected WBC subset
3. dedupe by player identity
4. apply a relevance filter for daily tracking
