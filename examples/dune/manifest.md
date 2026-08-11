# Dune Example World Manifest

Package id: `dune`

## Package Identity

- Display name: Dune
- Category: Science fiction
- Setting classification: `canon_existing_world`
- Primary setting scope: the Corrino Imperium, with Arrakis as the default opening world
- Secondary scope: other Imperial worlds and later eras only when the selected campaign requires them
- Content version: `0.1.0-research`
- Source snapshot date: 2026-07-23
- Package language: English
- Default rules assumption: system-neutral fiction; *Dune: Adventures in the Imperium* 2d20 is an optional play vocabulary
- Default literary continuity: Frank Herbert's six-novel saga
- Default play lens: licensed Modiphius campaign structures where they do not override the novels
- Default era proposal: late Corrino Imperium, before the Atreides transfer of Arrakis; exact year deliberately unset
- Default locale proposal: a bounded northern-Arrakis concession on the Hagga Basin fringe
- Default party proposal: a mixed field cell serving an original Minor House
- Default frame proposal: `dune-frame-dry-ledger`

## Authority And Runtime Status

- Authority: reference only
- Auto-load: forbidden
- Campaign readiness: not evaluated
- Accepted user choices: none
- Active campaign state: none
- State mutation capability: none
- Current-scale lock permitted: no; Session 0 must select continuity, era, locale, frame, party mandate, and boundaries
- Risk accepted: no package-level acceptance; the user must accept remaining uncertainty and thematic intensity during Session 0

This package is not a second campaign root. It contains no profile, current state, snapshot, turn log, accepted boundary, runtime instruction, or machine-readable loader contract. It becomes relevant only after a future workflow presents it as an option and the user chooses what to materialize into the owning files under `campaign/`.

## Player-Facing Promise

Enter a human future where interstellar power rests on feudal obligation, guarded knowledge, and a substance found on one lethal desert world. Begin as people with duties, divided loyalties, and scarce leverage. Navigate ecological limits, House politics, trade monopolies, faith, and violence without inheriting the destiny of the saga's famous protagonists.

## Fixed, Instanced, And Authored Layers

| Layer | Package responsibility | Must not do |
| --- | --- | --- |
| Template-fixed | Source hierarchy, continuity separation, durable causal truths, institutional limits, technology assumptions, knowledge defaults, and cultural guardrails | Merge incompatible continuities, predetermine a campaign outcome, or make imperial exploitation morally invisible |
| Campaign-instance | Offer selectable era, original House, local concession, pressures, actors, clocks, places, rumors, and opening frames | Treat a proposal as accepted state before Session 0 or require a canonical hero to solve the premise |
| Player-authored | Supply prompts for identity, training, home, loyalties, faith, ties, ambition, spice relationship, secrets, and boundaries | Assign a PC's beliefs, allegiance, ancestry, interiority, hidden conditioning, or relationship without consent |

## Recommended Experience

- Beginner default: original Minor House field cell, one Arrakis concession, agent-level intrigue and survival
- Political alternative: Landsraad petition, kanly mediation, or CHOAM leverage on Kaitain
- Community alternative: Arrakeen, a pyon settlement, smugglers, water workers, or merchants
- Fremen alternative: a player-approved sietch-centered campaign with targeted cultural review
- Strategic alternative: rulers of an original House using agent and architect scales
- Transit alternative: a bounded crisis aboard a Guild heighliner
- Explicit alternate continuity: *Dune: Awakening*'s timeline in which Paul Atreides was never born

## Why The Default Is Small And Original

The first novel's central figures already carry world-changing agency. The default therefore begins before its opening events, outside their immediate retinues, and at a scale where player decisions can matter without replacing Paul, Jessica, Leto, Chani, Stilgar, or other canonical actors. An original Minor House creates a shared mandate while leaving each PC's loyalty and identity open.

The exact year, House, settlement, concession, local officials, and crisis are campaign-instance content. They are not canon claims and must be named only after selection.

## File Inventory

- [Canon Policy](canon_policy.md) — literary authority, continuity modes, eras, conflict handling, and unresolved claims
- [World Operating Model](world_operating_model.md) — causal structure, durable truths, everyday life, ecology, technology, and violence limits
- [Regions](regions.md) — Arrakis and Imperium campaign-theater cards
- [Factions](factions.md) — stable institutional motives, methods, limits, and local-instantiation rules
- [Campaign Frames](campaign_frames.md) — six original opening frameworks, including one explicit alternate-continuity frame
- [Session 0 Options](session_zero_options.md) — spoiler-safe decisions, fourteen player fantasies, and player-authored prompts
- [Knowledge Layers](knowledge_layers.md) — visibility defaults, prescience handling, safe wording, and reveal gates
- [Source Provenance](source_provenance.md) — source register, claim index, confidence, limitations, and attribution
- [Adaptation Notes](adaptation_notes.md) — future materialization mapping, pruning rules, migration, and validation checklist

## Compatibility Boundary

The world model is intentionally less mechanical than a rulebook. Named 2d20 talents, drives, assets, and conflict procedures are not prerequisites. If another rules implementation is selected, preserve the causal force of water, spice, status, secrecy, transport, training, and consequence while replacing their numeric expression.

## Continuity Boundary

The package does not treat every Dune publication as one seamless canon.

- Frank Herbert's six novels are the primary literary layer.
- Brian Herbert and Kevin J. Anderson's expanded novels are opt-in.
- Modiphius material is a licensed playability source, not an automatic literary override.
- Legendary screen works are an opt-in adaptation layer.
- *Dune: Prophecy* occupies its own remote era and draws on expanded-novel material.
- *Dune: Awakening* is an explicit alternate timeline and never fills gaps in the default continuity.
- Package-original frames are playable proposals, not franchise canon.

See [Canon Policy](canon_policy.md) before selecting an era.

## Distribution Boundary

- The package contains paraphrased text and links; it contains no copied artwork, maps, stat blocks, rules text, or long source excerpts.
- No Dune lore or terminology is represented as open-license content.
- This research package grants no right to publish or commercially exploit the setting.
- Licensing and legal review remain outside this package.
- See [Source Provenance](source_provenance.md) for attribution and research limitations.
