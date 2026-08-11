# Forgotten Realms Knowledge Layers

## Purpose

This file defines default visibility for reusable package facts. It does not declare that any active PC, NPC, or faction currently holds a fact. Holder state is created only during campaign materialization.

## Layer Definitions

- Public-common: broadly safe to tell players before character creation
- Region-common: safe after a region is selected; ordinary local residents generally know it
- Trained: requires relevant education, profession, background, or successful discovery
- Faction-held: available to appropriate members or contacts, with internal variation
- Foreshadowable: the GM may show symptoms without revealing the conclusion
- GM-only: objective frame truth or hidden causal relation
- Player-private: authored by one player and shared only under accepted boundaries
- Confirmed: learned during play and safe to use in narration thereafter

## Reusable World Facts

### `fr-fact-scope-001`

- Default layer: public-common
- Fact: Faerûn is the package's primary geographic scope; it is part of Toril and not the whole D&D multiverse.
- Safe wording: Faerûn contains many lands and cultures within a much larger world.
- Forbidden wording: Do not imply that every D&D setting is a neighboring Faerûnian country.
- Reveal requirement: none
- Source: `claim-fr-scope`

### `fr-fact-magic-001`

- Default layer: public-common
- Fact: Magic is real and socially known, but access to expertise and services varies greatly.
- Safe wording: People know magic exists; what they can obtain depends on place, wealth, institutions, and circumstance.
- Forbidden wording: Do not assign a universal spellcaster percentage or promise every settlement a magic shop.
- Reveal requirement: none
- Source: `claim-fr-identity`, `claim-heroes-contents`

### `fr-fact-weave-001`

- Default layer: trained
- Fact: The Weave is central to common Faerûnian explanations of arcane magic and is associated with Mystra.
- Safe wording: Learned characters may understand spells as shaping or accessing the Weave.
- Forbidden wording: Do not claim that every magical tradition describes its practice identically.
- Reveal requirement: relevant training or ordinary instruction if the selected campaign treats this as common schooling
- Source: `claim-weave`

### `fr-fact-divine-001`

- Default layer: public-common
- Fact: Gods, divine magic, temples, and afterlife beliefs have demonstrable weight in the world.
- Safe wording: Faith is part of public life, even when people distrust a temple or disagree over a sign.
- Forbidden wording: Do not equate a god's existence with the correctness of every priest.
- Reveal requirement: none
- Source: `claim-deities-2025`

### `fr-fact-history-001`

- Default layer: public-common
- Fact: The present is built amid remnants of older powers and magical disasters.
- Safe wording: Ruins and old boundaries are ordinary parts of regional memory, though their true histories may be disputed.
- Forbidden wording: Do not give exact hidden ruin history to every character.
- Reveal requirement: none for broad truth; trained or discovered for specifics
- Source: `claim-fr-identity`

### `fr-fact-canon-001`

- Default layer: Session 0 meta-knowledge
- Fact: Current tabletop canon is the default; old editions and other media are not automatically merged.
- Safe wording: The group can opt into a favorite continuity explicitly.
- Forbidden wording: Do not present a continuity choice as an in-world fact.
- Reveal requirement: explain before canon selection
- Source: `claim-canon-editions`

### `fr-fact-year-001`

- Default layer: Session 0 meta-knowledge
- Fact: The package uses the 2025 sourcebook present; 1501 DR is provisional with medium confidence.
- Safe wording: We can remain date-neutral or lock 1501 DR after primary-source confirmation.
- Forbidden wording: Do not call 1501 DR immutable package truth yet.
- Reveal requirement: explain if exact dating matters
- Source: `claim-current-year`

## Region-Common Facts

### `fr-fact-dale-001`

- Default layer: region-common after Dalelands selection
- Fact: The dales value local independence, and relations with Cormanthor and nearby powers shape security and trade.
- Safe wording: Roads, councils, old alliances, and forest boundaries matter to daily life.
- Forbidden wording: Do not reveal a selected frame's damaged ward or hidden profiteer.
- Source: `claim-dalelands-2025`

### `fr-fact-gate-001`

- Default layer: region-common after Baldur's Gate selection
- Fact: Wealth, district, connections, the Flaming Fist, and the Guild affect how safety and law operate.
- Safe wording: The city is prosperous, stratified, and politically hard-edged.
- Forbidden wording: Do not claim every officer, noble, or Guild member has the same motive.
- Source: `claim-baldurs-gate-2025`

### `fr-fact-calim-001`

- Default layer: region-common after Calimshan selection
- Fact: Trade, water, magical sophistication, mortal institutions, and genie powers all affect regional politics.
- Safe wording: Agreements and routes can matter as much as raw magical power.
- Forbidden wording: Do not reduce the region to genies, desert, or exotic spectacle.
- Source: `claim-calimshan-2025`

### `fr-fact-ice-001`

- Default layer: region-common after Icewind Dale selection
- Fact: Weather, supplies, routes, and cooperation are political as well as practical concerns.
- Safe wording: Local and mobile communities hold expertise outsiders need.
- Forbidden wording: Do not reveal a selected frame's buried mechanism.
- Source: `claim-icewind-dale-2025`

### `fr-fact-moon-001`

- Default layer: region-common after Moonshae selection
- Fact: Sea travel, sacred nature, old promises, and relations among island peoples and fey powers shape life.
- Safe wording: Ecological change can signal a social or supernatural rupture.
- Forbidden wording: Do not describe fey as random or island peoples as monoliths.
- Source: `claim-moonshae-2025`

## Frame Secrets

### `fr-frame-dale-secret-001`

- Default layer: GM-only proposal
- Fact: Removed components from an old protection network caused displacement; profiteers are prolonging the resulting road crisis.
- Foreshadowable signs: inconsistent routes, missing fittings, frightened raiders, prepared land buyers
- Safe pre-reveal wording: Several actors appear to be responding to the crisis faster than they could have planned from public information.
- Forbidden pre-reveal wording: The wards and buyers caused everything.
- Reveal requirement: physical evidence at two sites plus testimony from opposed actors
- Source: package-original frame design

### `fr-frame-gate-secret-001`

- Default layer: GM-only proposal
- Fact: A missing ledger records political obligations disguised as ordinary commercial debt.
- Foreshadowable signs: page-number questions, repeated contract marks, fear of debt rather than arson charges
- Safe pre-reveal wording: Powerful people care more about the record's structure than the lost cargo.
- Forbidden pre-reveal wording: The ledger proves an infernal debt network.
- Reveal requirement: surviving records, debtor testimony, and notation key
- Source: package-original frame design

### `fr-frame-calim-secret-001`

- Default layer: GM-only proposal
- Fact: The missing party to an old water accord was a shared mortal office, not one bloodline.
- Foreshadowable signs: plural titles, repeated civic symbols, contradictory translations
- Safe pre-reveal wording: Existing claimants may be using a translation that benefits them.
- Forbidden pre-reveal wording: The fifth signatory was collective.
- Reveal requirement: oral history, physical inscription, and two rival institutional records
- Source: package-original frame design

### `fr-frame-ice-secret-001`

- Default layer: GM-only proposal
- Fact: A failed rescue accidentally activated part of a buried climate system, and simple shutdown transfers danger elsewhere.
- Foreshadowable signs: geometric frost, displaced warm zones, rescue marks, migrating predators
- Safe pre-reveal wording: The cold follows a pattern that does not match weather alone.
- Forbidden pre-reveal wording: The expedition activated a zero-sum climate machine.
- Reveal requirement: survivor account, temperature pattern, and one control site
- Source: package-original frame design

### `fr-frame-moon-secret-001`

- Default layer: GM-only proposal
- Fact: A moved boundary marker caused several valid old promises and environments to overlap.
- Foreshadowable signs: symmetric harm, displaced stones, ritual border language, multiple communities suffering
- Safe pre-reveal wording: The damage does not behave like a one-sided attack.
- Forbidden pre-reveal wording: The storm caused an accidental boundary overlap.
- Reveal requirement: investigate both sides, recover a ritual account, and hear opposed testimony
- Source: package-original frame design

## Faction Knowledge Defaults

- A faction's public mask may be public-common or region-common.
- Stable desire and broad reputation may be trained knowledge.
- Current local objective is never package-common; instantiate it in campaign state.
- Cell membership, internal disagreement, route, code, compromised official, and hidden resource default to faction-held or GM-only.
- A symbol, uniform, or rumor does not prove affiliation without verification.

## Holder Materialization

When a package fact becomes campaign content:

1. Copy only the selected fact into the appropriate campaign-owned knowledge file.
2. Assign actual holders; do not inherit hypothetical holders from this package.
3. Preserve safe and forbidden wording.
4. Define reveal requirements that can occur at the opening scale.
5. Link the fact to its owning world, issue, faction, place, or frame note.
6. Update holder and confirmation state only through accepted workflow or runtime state changes.

## Spoiler Policy

Player-facing Session 0 may reveal:

- World promise
- Regional identity
- Visible opening pressure
- Broad faction reputation
- Character-fit prompts
- Known continuity choices

It must not reveal:

- Frame secret answers
- Hidden faction control
- Unconfirmed betrayals
- Exact future clocks
- Private PC material
- A mystery's required solution

A player may deliberately request spoilers. Record that choice before changing the default audience.