# World of Darkness: Vampire: The Masquerade Example World Manifest

Package id: `world-of-darkness-vtm`

## Package Identity

- Display name: World of Darkness: Vampire: The Masquerade
- Category: Gothic-punk urban horror
- Setting classification: `canon_existing_world`
- Primary setting scope: contemporary World of Darkness viewed through Vampire: The Masquerade 5th Edition
- Playable scope: vampire player characters and vampire-coterie chronicles only
- Secondary setting scope: other World of Darkness supernatural lines as non-player context, threats, rumors, and unknowns
- Content version: `0.1.0-research`
- Source snapshot date: 2026-07-23
- Package language: English
- Default rules assumption: Vampire: The Masquerade 5th Edition; fiction may be translated only after preserving its core pressures
- Default continuity: current World of Darkness 5th Edition / V5
- Default era proposal: contemporary nights; exact year deliberately unset
- Default locale proposal: one contested mixed-use district in an original contemporary city
- Default party proposal: a mixed young or otherwise precarious coterie with negotiated local standing
- Default frame proposal: `wod-vtm-frame-borrowed-night`

## Authority And Runtime Status

- Authority: reference only
- Auto-load: forbidden
- Campaign readiness: not evaluated
- Accepted user choices: none
- Active campaign state: none
- State mutation capability: none
- Current-scale lock permitted: no; Session 0 must select continuity, city, district, coterie mandate, sect relationship, rules, and boundaries
- Risk accepted: no package-level acceptance; feeding, coercion, addiction metaphor, sexuality, violence, abuse, and loss of control require table consent

This directory is not a second campaign root. It contains no profile, current state, snapshot, turn log, accepted boundary, runtime instruction, or machine-readable loader contract. A future workflow may present it as an option, but only explicit Session 0 choices may be materialized into the owning files under `campaign/`.

## Player-Facing Promise

You are vampires surviving the contemporary night: predators who still carry human commitments, depend on blood, and risk exposing a hidden society built from favors, territory, fear, and selective memory. Begin with one district and a coterie that needs one another. Decide what you will protect, whom you will exploit, and what remains of you when Hunger, power, and the Masquerade demand incompatible answers.

## Fixed, Instanced, Authored, And Non-Player Layers

| Layer | Package responsibility | Must not do |
| --- | --- | --- |
| Template-fixed | Preserve V5 continuity, vampiric condition, Hunger and Humanity pressure, Masquerade, domain politics, modern hunter risk, source hierarchy, and myth-versus-truth separation | Merge editions silently, make predation consequence-free, or permit non-vampire PCs by implication |
| Campaign-instance | Offer an original city, bounded district, domain, local sect settlement, actors, clocks, rumors, feeding pressure, breach risk, and one opening frame | Treat a proposal as accepted state, import famous metaplot actors as solutions, or predefine every supernatural cause |
| Player-authored | Prompt for identity, clan or non-clan condition, sire and Embrace history, Convictions, Touchstones, feeding practice, sect attitude, coterie ties, secrets, and boundaries | Assign a PC's interiority, lineage, mortal relationships, coercive history, sexuality, trauma, or betrayal without consent |
| Non-player supernatural | Carry Werewolf, Hunter, ghost, mage, fae, demon, and other World of Darkness context as bounded NPC, threat, rumor, or unknown layers | Build equal-weight crossover parties, expose another game's cosmology as universal truth, or supply non-vampire character options |

## Playable-Scope Lock

Every player character in material derived from this package must be a VTM vampire: a member of a selected clan, Caitiff, or thin-blood when the chosen V5 rules support that option. Ghouls, mortal hunters, Garou, mages, ghosts, changelings, demons, and other beings may be important people or forces, but they are not default PCs, sidekick character sheets, or rotating crossover protagonists.

Expanding the playable scope requires a new campaign divergence, a new source pass, a new balance and knowledge design, and explicit consent. It is not a small toggle.

## Recommended Experience

- Beginner default: mixed fledgling or young coterie, one contested district, one feeding-right dispute, one boon pressure, and one Masquerade risk
- Camarilla alternative: court retainers, Hounds, or provisional domain holders navigating neo-feudal obligation
- Anarch alternative: neighborhood defenders negotiating freedom, responsibility, and local authority
- Thin-blood alternative: an all-thin-blood or thin-blood-centered survival network using owned V5 material
- Occult alternative: blood sorcery and thin-blood alchemy scene after explicit body-horror and coercion review
- Flight alternative: vampires evading a hunter list or rebuilding after a burned haven
- High-metaplot alternative: Gehenna War or elder legacy only after continuity, power, and spoiler review
- Independent alternative: Autarkis or locally unaffiliated coterie whose neutrality has costs

## Why The Default Is Small And Original

Named VTM cities carry published officeholders, sect histories, signature conflicts, and fan expectations. An original city preserves the current setting's causal pressures without making player agency subordinate to a canonical Prince, Baron, elder, or famous coterie. One mixed-use district is large enough to contain feeding, havens, mortal communities, nightlife, surveillance, and competing claims, but small enough for consequences to remain legible.

The city's name, country, exact date, demographics, institutions, local clans, sect balance, domain borders, and supernatural inhabitants are campaign-instance facts. No placeholder becomes true before Session 0.

## File Inventory

- [Canon Policy](canon_policy.md) — edition hierarchy, continuity modes, metaplot treatment, myths, crossover limits, and unresolved claims
- [World Operating Model](world_operating_model.md) — vampiric condition, causal truths, nightly life, predation, modern risk, and scale
- [Regions](regions.md) — ten selectable urban theaters and a bounded default district network
- [Factions](factions.md) — sect and institution models, the current clan menu, local-instantiation rules, and faction clocks
- [Campaign Frames](campaign_frames.md) — six original vampire-only opening frameworks and protected hidden truths
- [Session 0 Options](session_zero_options.md) — fifteen vampire fantasies, coterie choices, player-authored prompts, and safety gates
- [Knowledge Layers](knowledge_layers.md) — mortal, Kindred, occult, crossover, frame, and player-private visibility rules
- [Source Provenance](source_provenance.md) — official source register, claim index, confidence, limitations, and attribution
- [Adaptation Notes](adaptation_notes.md) — future materialization, pruning, mechanical translation, migration, and validation

## Current Clan Coverage

The package recognizes the fourteen V5 clan presentations available across the Core Rulebook and Players Guide: Banu Haqim, Brujah, Gangrel, Hecata, Lasombra, Malkavian, Ministry, Nosferatu, Ravnos, Salubri, Toreador, Tremere, Tzimisce, and Ventrue. Caitiff and thin-blooded vampires are separate non-clan or liminal options rather than additional clans.

These names define a player menu, not fourteen mandatory factions. No clan receives a required personality, sect loyalty, ethnicity, profession, morality, or local population. See [Factions](factions.md) and [Session 0 Options](session_zero_options.md).

## Other World of Darkness Boundary

- *Werewolf: The Apocalypse 5th Edition* supports Garou, spirits, Rage, and environmental-spiritual horror in its own game. Here those elements are non-player and source-gated.
- *Hunter: The Reckoning 5th Edition* supports mortal hunters taking desperate measures in its own game. Here hunters are NPC cells, rivals, victims, or antagonists.
- Ghosts and Oblivion may intersect VTM stories, but a full *Wraith* cosmology is not imported automatically.
- Mages, sorcerers, changelings, demons, mummies, and other legacy beings may exist as bounded possibilities. Their capabilities and cosmologies require targeted research before they become operational facts.
- *Chronicles of Darkness* and *Vampire: The Requiem* are a separate game family and are excluded from the default continuity.

## Compatibility Boundary

The package assumes V5 because Hunger, Humanity, Touchstones, Convictions, coterie design, and contemporary sect pressures shape its play promise. A different rules engine may express those forces differently, but it must preserve:

- blood dependence and risky predation
- Hunger intruding on competence and choice
- moral and relational anchors without dictating player feelings
- Masquerade exposure and mortal consequence
- domain, status, boons, and contested authority
- daylight, fire, torpor, injury, and Final Death as meaningful limits
- modern surveillance and organized hunter pressure
- asymmetric knowledge and uncertain mythology

It must not copy proprietary rules text or pretend a mechanical conversion is canon.

## Continuity Boundary

- Current V5 is primary.
- Legacy VTM and V20 are opt-in references, never silent gap-fillers.
- V5 city books may be selected for a named-city campaign after a targeted source pass.
- Sabbat is antagonist-first under the inspected V5 source; Sabbat PCs require an explicit divergence and further research.
- Beckoning and Gehenna War material is mutable background, not an obligation to center elders or apocalypse.
- The *Book of Nod* is an in-world mythic source, not proof of one objective origin story.
- W5 and H5 are related current World of Darkness games, not extra VTM player classes.
- Legacy Mage, Wraith, Changeling, Demon, and other cosmologies remain perspective-bound.
- Chronicles of Darkness and *Vampire: The Requiem* remain separate.
- Package-original cities, frames, actors, and secrets are playable proposals, not franchise canon.

See [Canon Policy](canon_policy.md) before materialization.

## Distribution Boundary

- This package contains paraphrased research and links; it contains no copied artwork, maps, stat blocks, proprietary procedures, or long source excerpts.
- World of Darkness and Vampire: The Masquerade names, lore, and rules remain protected intellectual property.
- The package grants no right to publish, stream, license, or commercially exploit the setting.
- Legal and licensing review remains outside this package.
- See [Source Provenance](source_provenance.md) for attribution and limitations.
