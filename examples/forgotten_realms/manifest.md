# Forgotten Realms Example World Manifest

Package id: `forgotten-realms`

## Package Identity

- Display name: Dungeons & Dragons: Forgotten Realms
- Category: Fantasy
- Setting classification: `canon_existing_world`
- Primary setting scope: Faerûn on Toril
- Secondary scope: other parts of Toril and the planes only when the selected campaign requires them
- Content version: `0.1.0-research`
- Source snapshot date: 2026-07-23
- Package language: English
- Default rules assumption: revised 2024 D&D rules, labeled 5.5e by D&D Beyond as of the source snapshot
- Default timeline anchor: the present described by the 2025 Forgotten Realms tabletop sourcebooks
- Provisional display year: 1501 DR
- Provisional-year confidence: medium
- Default locale proposal: the Dalelands
- Default frame proposal: `fr-frame-silent-bell`

## Authority And Runtime Status

- Authority: reference only
- Auto-load: forbidden
- Campaign readiness: not evaluated
- Accepted user choices: none
- Active campaign state: none
- State mutation capability: none
- Current-scale lock permitted: no; Session 0 must first select a locale, source policy, frame, and opening scale
- Risk accepted: no package-level acceptance; the user must accept remaining uncertainty during Session 0

This package is not a second campaign root. It contains no profile, current state, snapshot, turn log, accepted boundary, or runtime instruction. It becomes relevant only after a future workflow presents it as an option and the user chooses what to materialize into the owning files under `campaign/`.

## Player-Facing Promise

Begin with a local obligation in Faerûn, a continent where ancient ruins shape present politics, gods are real, magic is powerful but unevenly available, and independent factions pursue goals beyond the heroes' sight. Grow from a person with ties and debts into a figure whose choices can alter a region or become legend.

## Fixed, Instanced, And Authored Layers

| Layer | Package responsibility | Must not do |
| --- | --- | --- |
| Template-fixed | Source policy, durable world truths, regional identities, stable faction models, knowledge defaults, cultural guardrails | Declare a campaign outcome or player history |
| Campaign-instance | Offer selectable locale, pressures, actors, clocks, local places, and opening frames | Treat proposals as accepted state before Session 0 |
| Player-authored | Supply prompts for identity, home, ties, faith, debts, secrets, ambitions, and boundaries | Prewrite the PC's interiority or force a personal relationship |

## Recommended Experience

- Beginner default: Dalelands, local heroic fantasy, one settlement and its road network
- Familiar alternative: Phandalin and the Sword Coast
- Urban alternative: Baldur's Gate
- High-magic political alternative: Calimshan
- Survival-horror alternative: Icewind Dale
- Seafaring and fey alternative: Moonshae Isles

## File Inventory

- [Canon Policy](canon_policy.md) — source hierarchy, timeline, continuity, conflict handling, and unresolved claims
- [World Operating Model](world_operating_model.md) — durable truths, causal structure, everyday life, and power limits
- [Regions](regions.md) — primary and supplementary campaign-region cards
- [Factions](factions.md) — stable faction motives, methods, limits, and hooks
- [Campaign Frames](campaign_frames.md) — five original, selectable opening frameworks
- [Session 0 Options](session_zero_options.md) — spoiler-safe decisions and player-authored prompts
- [Knowledge Layers](knowledge_layers.md) — default fact visibility, safe wording, and reveal gates
- [Source Provenance](source_provenance.md) — source register, claim index, confidence, and open research questions
- [Adaptation Notes](adaptation_notes.md) — future materialization mapping and validation checklist

## Compatibility Boundary

The world model is intentionally less mechanical than a rulebook. Named 5.5e subclasses, feats, spells, and backgrounds are optional character-facing integrations, not prerequisites for the setting to function. If another rules implementation is selected later, preserve the world's causal truths and replace only mechanical expressions.

## Distribution Boundary

- The package contains paraphrased text and links; it contains no copied artwork, maps, stat blocks, or long source excerpts.
- Forgotten Realms lore is not represented as SRD content.
- Licensing and publication decisions remain outside this package.
- See [Source Provenance](source_provenance.md) for attribution and research limitations.