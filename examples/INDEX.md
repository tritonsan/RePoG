# Example World Packages

This directory contains researched, reusable world packages that can accelerate Session 0 without becoming campaign state.

## Package Contract

- Every package is reference content only.
- Packages are never loaded automatically and never override `AGENTS.md`, `workflows/`, profiles, or accepted campaign files.
- `campaign/` remains the only active campaign root.
- A package may propose defaults, regions, pressures, and opening frames; none are accepted until the user selects them through Session 0.
- Player identity, personal ties, boundaries, and unresolved creative decisions remain player-authored.
- Materialization must prune the package to the selected opening scale rather than copying the whole setting into active memory.
- Canon claims must carry source, confidence, mutability, and spoiler information.

## Catalog

### Cyberpunk Universe

- Package id: `cyberpunk-universe`
- Category: Dark-future science fiction
- Classification: `canon_existing_world`
- Content status: researched reference package
- Default rules assumption: system-neutral fiction; optional owned Cyberpunk RED rules for 2045
- Default locale proposal: one original rebuilding district in Night City, 2045
- Default campaign-frame proposal: `cyberpunk-frame-last-light`
- Manifest: [Cyberpunk Universe Example World Manifest](cyberpunk_universe/manifest.md)

### Dungeons & Dragons: Forgotten Realms

- Package id: `forgotten-realms`
- Category: Fantasy
- Classification: `canon_existing_world`
- Content status: researched reference package
- Default rules assumption: revised 2024 D&D rules, currently labeled 5.5e by D&D Beyond
- Default locale proposal: the Dalelands
- Default campaign-frame proposal: `fr-frame-silent-bell`
- Manifest: [Forgotten Realms Example World Manifest](forgotten_realms/manifest.md)

### Dune

- Package id: `dune`
- Category: Science fiction
- Classification: `canon_existing_world`
- Content status: researched reference package
- Default rules assumption: system-neutral fiction; optional *Dune: Adventures in the Imperium* 2d20 vocabulary
- Default locale proposal: a northern-Arrakis concession on the Hagga Basin fringe
- Default campaign-frame proposal: `dune-frame-dry-ledger`
- Manifest: [Dune Example World Manifest](dune/manifest.md)

### Harry Potter Universe

- Package id: `harry-potter-universe`
- Category: Modern magical fantasy
- Classification: `canon_existing_world`
- Content status: researched reference package
- Default rules assumption: system-neutral fiction; no game interface or rules engine assumed
- Default locale proposal: one original British magical recovery quarter, 2001
- Default campaign-frame proposal: `harry-potter-frame-mended-network`
- Manifest: [Harry Potter Universe Example World Manifest](harry_potter_universe/manifest.md)

### Star Wars Universe

- Package id: `star-wars-universe`
- Category: Space fantasy / science-fantasy
- Classification: `canon_existing_world`
- Content status: researched reference package
- Default rules assumption: system-neutral fiction; no screen grammar or game interface assumed
- Default locale proposal: one original frontier reconstruction corridor in The New Republic era
- Default campaign-frame proposal: `star-wars-frame-broken-beacon`
- Manifest: [Star Wars Universe Example World Manifest](star_wars_universe/manifest.md)

### World of Darkness: Vampire: The Masquerade

- Package id: `world-of-darkness-vtm`
- Category: Gothic-punk urban horror
- Classification: `canon_existing_world`
- Content status: researched reference package
- Default rules assumption: Vampire: The Masquerade 5th Edition
- Default locale proposal: one contested mixed-use district in an original contemporary city
- Default campaign-frame proposal: `wod-vtm-frame-borrowed-night`
- Manifest: [World of Darkness: Vampire: The Masquerade Example World Manifest](world_of_darkness_vtm/manifest.md)

## Future Packages

Add future worlds as sibling directories with the same semantic separation. Matching filenames are recommended for portability, but this index does not define a runtime schema or loader.