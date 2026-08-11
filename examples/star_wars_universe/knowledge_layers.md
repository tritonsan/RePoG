# Star Wars Universe Knowledge Layers

## Purpose

This file separates setting truth from what players, PCs, institutions, sources, and the GM know. A Canon proposition is not automatically common knowledge. A published event may exceed the spoiler ceiling. A government statement, bounty, vision, sensor reading, or game interface is not objective omniscience.

## Visibility Taxonomy

| Layer | Meaning | Default holders | Player treatment |
| --- | --- | --- | --- |
| `P0` | public premise | people plausibly familiar with the selected era | may appear in the pitch |
| `E0` | selected-era baseline | people socialized in that era and region | explain before a decision depends on it |
| `L1` | local lived fact | residents, workers, crews, or service users | discover through relationship and observation |
| `R2` | rumor, propaganda, or contested account | named speakers, communities, or channels | label source, motive, and uncertainty |
| `I3` | institutional information | bounded office, unit, guild, archive, or council | access requires role, trust, request, or process |
| `A4` | restricted specialist knowledge | trained practitioner, technician, navigator, healer, or custodian | require method and provenance |
| `S5` | published-event spoiler | table after accepted spoiler band | never reveal above ceiling |
| `F6` | selected-frame truth | GM layer and justified evidence holders | reveal only through listed requirements |
| `C7` | campaign consequence | actual witnesses, sensors, records, and affected people | update after play; no retroactive omniscience |
| `PP` | player-private fact | player and explicitly approved holders | never infer, expose, or weaponize without consent |

`S5` is a visibility class, not the spoiler-band number. Preserve both fields.

## Fact Cards

### `star-wars-fact-media-001`

- **Proposition:** Canon, Legends, selected alternate works, fixed game narrative, player-variable outcomes, mechanics, and presentation are separate layers.
- **Default layer:** `P0`
- **Spoiler:** `S0`
- **Claims:** `claim-star-wars-franchise-scope`, `claim-star-wars-canon-legends`, `claim-star-wars-visions`, `claim-star-wars-lego-alternate`, `claim-star-wars-crossover`, `claim-star-wars-game-layer`, `claim-star-wars-swtor-legends`
- **Caution:** familiar names or visuals do not merge histories.

### `star-wars-fact-era-001`

- **Proposition:** Official Star Wars history is organized into nine qualitative eras; exact hard dates require selected works.
- **Default layer:** `P0`
- **Spoiler:** `S0`
- **Claims:** `claim-star-wars-eras`
- **Caution:** era is independent from continuity and medium.

### `star-wars-fact-force-001`

- **Proposition:** The Force is connected to life and binds the galaxy; sensitivity may enable unusual perception and action.
- **Default layer:** `P0`
- **Spoiler:** `S0`
- **Claims:** `claim-star-wars-force`
- **Caution:** exact powers, limits, and interpretations need selected sources.

### `star-wars-fact-jedi-001`

- **Proposition:** The Jedi Order is a historical institution whose peacekeeping, wartime, persecuted, surviving, and rebuilding conditions differ by era.
- **Default layer:** `E0`
- **Spoiler:** selected era
- **Claims:** `claim-star-wars-jedi`
- **Caution:** sensitivity or benevolent action does not establish membership.

### `star-wars-fact-sith-traditions-001`

- **Proposition:** Sith membership, dark-side use, Nightsister practice, Force belief, sensitivity, and Jedi affiliation are distinct.
- **Default layer:** `A4`
- **Spoiler:** selected work
- **Claims:** `claim-star-wars-sith`, `claim-star-wars-force-traditions`
- **Caution:** do not impose one universal taxonomy or mechanic.

### `star-wars-fact-republic-senate-001`

- **Proposition:** The Galactic Republic uses a Senate-based political order whose authority, bureaucracy, corruption, emergency power, and war role change over time.
- **Default layer:** `E0`
- **Spoiler:** `S1`–`S2`
- **Claims:** `claim-star-wars-republic`, `claim-star-wars-senate`
- **Caution:** representation does not prove effective local service or a complete constitution.

### `star-wars-fact-empire-001`

- **Proposition:** The Galactic Empire rules through authoritarian administration, armed force, fear, surveillance, and mass-destruction capacity.
- **Default layer:** `E0`
- **Spoiler:** `S2`–`S3`
- **Claims:** `claim-star-wars-empire`
- **Caution:** define one local office or unit rather than an omniscient abstraction.

### `star-wars-fact-rebellion-001`

- **Proposition:** The Rebel Alliance develops from varied resistance movements seeking to defeat Imperial rule and restore democracy.
- **Default layer:** `E0`
- **Spoiler:** `S3`
- **Claims:** `claim-star-wars-rebellion`
- **Caution:** cell knowledge, tactics, and civilian accountability are local.

### `star-wars-fact-new-republic-001`

- **Proposition:** The New Republic restores a Senate, negotiates with Imperial remnants, reduces military capacity, and remains vulnerable during reconstruction.
- **Default layer:** `E0`
- **Spoiler:** `S3`
- **Claims:** `claim-star-wars-new-republic`
- **Caution:** exact reconstruction programs and local law are not supplied.

### `star-wars-fact-first-order-resistance-001`

- **Proposition:** The First Order develops from Imperial successors in the Unknown Regions, while the Resistance is a separate small organization with limited covert support from some New Republic figures.
- **Default layer:** `S5`
- **Spoiler:** `S5`
- **Claims:** `claim-star-wars-first-order`, `claim-star-wars-resistance`
- **Caution:** public knowledge and territorial reach depend on date and selected work.

### `star-wars-fact-regions-001`

- **Proposition:** Core Worlds, Mid Rim, Outer Rim, Unknown Regions, planets, and systems supply geography, not cultural or moral destiny.
- **Default layer:** `P0`
- **Spoiler:** `S0`
- **Claims:** `claim-star-wars-regions`, `claim-star-wars-anti-essentialism`
- **Caution:** define each local culture, law, economy, and environment separately.

### `star-wars-fact-coruscant-001`

- **Proposition:** Coruscant is a densely layered, culturally varied city-world and changing political center.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-star-wars-coruscant`
- **Caution:** one district or level cannot represent the entire world.

### `star-wars-fact-ferrix-001`

- **Proposition:** Ferrix is one sourced Outer Rim example of salvage, repair, labor, trade, local memory, and route connection.
- **Default layer:** `S5`
- **Spoiler:** selected *Andor* scope
- **Claims:** `claim-star-wars-ferrix`
- **Caution:** do not generalize it to all Outer Rim communities.

### `star-wars-fact-hyperspace-001`

- **Proposition:** Hyperspace travel requires compatible equipment, fuel, navigation information, and hazard management.
- **Default layer:** `E0`
- **Spoiler:** `S0`
- **Claims:** `claim-star-wars-hyperspace`
- **Caution:** route, access, and travel time remain source- and campaign-specific.

### `star-wars-fact-starships-001`

- **Proposition:** Starship capability depends on design, modification, crew, cargo, maintenance, and functioning systems.
- **Default layer:** `A4`
- **Spoiler:** `S0`
- **Claims:** `claim-star-wars-starships`
- **Caution:** one famous ship is an example, not a universal stat block.

### `star-wars-fact-comms-001`

- **Proposition:** Comlinks are common and may be encrypted, but universal instantaneous HoloNet service is not established.
- **Default layer:** `E0`
- **Spoiler:** `S0`
- **Claims:** `claim-star-wars-comms`
- **Caution:** record range, relay, delay, interception, language, and censorship locally.

### `star-wars-fact-droids-001`

- **Proposition:** Droids have specialized functions and may hold consequential memory and relationships; no universal personhood, ownership, or wipe law is inferred.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-star-wars-droids`
- **Caution:** establish each droid's self-understanding, consent, and local status individually.

### `star-wars-fact-economy-001`

- **Proposition:** Currency acceptance, rations, barter, salvage, cargo, and trade vary by place and regime.
- **Default layer:** `L1`
- **Spoiler:** `S0`
- **Claims:** `claim-star-wars-economy`
- **Caution:** do not invent galaxy-wide prices, wages, taxes, or exchange rates.

### `star-wars-fact-bounty-001`

- **Proposition:** Bounty work may be brokered through guild relationships, but a contract is not universal proof of guilt or jurisdiction.
- **Default layer:** `I3`
- **Spoiler:** `S1`
- **Claims:** `claim-star-wars-bounty`
- **Caution:** identify client, evidence, payment, authority, and challenge route.

### `star-wars-fact-syndicates-001`

- **Proposition:** Distinct criminal organizations may control routes, mining, smuggling, debt, or forced labor and may form unstable coalitions.
- **Default layer:** `I3`
- **Spoiler:** selected era
- **Claims:** `claim-star-wars-syndicates`
- **Caution:** there is no one timeless unified underworld.

### `star-wars-fact-clones-001`

- **Proposition:** Clone troopers share a genetic origin but retain distinct names, identities, choices, relationships, and possible lives beyond soldiering.
- **Default layer:** `E0`
- **Spoiler:** `S2`
- **Claims:** `claim-star-wars-clones`, `claim-star-wars-anti-essentialism`
- **Caution:** programming, aging, command, medical status, and privacy require selected sources and consent.

### `star-wars-fact-stormtroopers-001`

- **Proposition:** Stormtroopers are Imperial shock troops with specialized branches and are not assumed to be clones in every era.
- **Default layer:** `E0`
- **Spoiler:** `S2`–`S3`
- **Claims:** `claim-star-wars-stormtroopers`
- **Caution:** a uniform does not reveal every recruit's history, belief, or knowledge.

### `star-wars-fact-mandalorians-001`

- **Proposition:** Mandalorian history includes varied clans, creeds, governments, pacifist and martial politics, rebellion, occupation, and diaspora.
- **Default layer:** `S5`
- **Spoiler:** selected work
- **Claims:** `claim-star-wars-mandalorians`, `claim-star-wars-anti-essentialism`
- **Caution:** no single helmet practice, profession, temperament, or lineage defines all Mandalorians.

### `star-wars-fact-care-refuge-001`

- **Proposition:** Bacta can treat serious injury and some communities shelter refugees and rebuild, but universal access, prognosis, asylum, housing, and medical law are not established.
- **Default layer:** `L1`
- **Spoiler:** selected work
- **Claims:** `claim-star-wars-medicine`, `claim-star-wars-refugees`
- **Caution:** define capacity, consent, cost, host relationships, disability, and local rights.

## Selected-Frame Truth Register

| Frame truth id | Default holders | Reveal gate | Safe player-facing category |
| --- | --- | --- | --- |
| `star-wars-frame-broken-beacon-secret-001` | GM; surviving route collaborators | pattern + protected-community testimony + maintenance record | legacy route conflict |
| `star-wars-frame-empty-seat-secret-001` | GM; delegate and dual-office custodians | both custody chains + resident testimony + consent-safe contact | representation mismatch |
| `star-wars-frame-unmarked-cargo-secret-001` | GM; individual droids and sponsor | consensual inspection + direct communication + corroborated wipe order | disputed cargo custody |
| `star-wars-frame-last-salvage-secret-001` | GM; workers and record custodians | title + diagnostics + maintenance ledger | transformed war asset |
| `star-wars-frame-names-in-armor-secret-001` | GM; consenting clones, medic, quartermaster | individual consent + protected medical evidence + readiness-pressure proof | protective roster conflict |
| `star-wars-frame-quiet-current-secret-001` | GM; caretaker and affected witnesses | ecology + instruments + consensual testimony + caretaker evidence | stewardship and route phenomenon |

Only the selected row enters GM memory. Safe categories may guide foreshadowing; they are not solutions.

## Evidence Contract

For every consequential assertion, record:

- proposition and actual holder
- acquisition method and medium
- era, continuity, work, and date confidence
- direct observation, sensor return, expert interpretation, record, testimony, vision, propaganda, rumor, or inference
- reliability and incentive
- people endangered by disclosure
- corroboration and falsification paths
- whether a Force experience is private, shared by consent, or independently evidenced

Authentication proves origin, not completeness, interpretation, legitimacy, or ethical publication.

## Rumor And Propaganda Contract

A rumor or official message needs a speaker, intended audience, reason for repetition, accurate element, uncertainty or distortion, possible harm, and no automatic conversion into GM truth. Imperial propaganda is not false in every detail; Rebel, Republic, Resistance, guild, and local accounts are not automatically complete.

## Institutional Knowledge

No Senate, Empire, New Republic, Resistance, Jedi archive, guild, syndicate, or ship knows everything held under its name. Identify the exact office, unit, custodian, system, access rule, author, survival through war or transition, dispute, and practical action available.

## Player-Private Boundary

`PP` facts include identity, species relationship, body, disability, cybernetics, droid or clone status, Force sensitivity, belief, family, lineage, relationships, trauma, fears, secret knowledge, and requested private context. The GM may not expose a `PP` fact through the Force, prophecy, mind tricks, scans, genetics, droid diagnostics, Imperial records, Jedi archives, visions, or famous relatives unless the player explicitly accepted that specific possibility.

## Update Procedure

After each consequential scene:

1. Add only campaign facts actually established.
2. Record current holders rather than making the party omniscient.
3. Preserve claim ids for official propositions.
4. Mark frame revelations against requirements.
5. Separate public report from event and interpretation.
6. Keep player-private facts private.
7. Do not write campaign events back into this reusable package.
