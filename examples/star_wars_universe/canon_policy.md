# Star Wars Universe Canon Policy

## Research Posture

This package uses official public sources and explicit labels. It does not treat every Star Wars-branded work, adaptation choice, licensed mechanic, anthology, LEGO remix, promotional crossover, or player-variable outcome as one continuity.

Lucasfilm's 2014 announcement provides the central public policy: the earlier Expanded Universe was retained under the Legends banner while a coordinated Canon program moved forward. A later Canon work may reuse a Legends name or idea without importing the old work's complete history. Source claims: `claim-star-wars-canon-legends`, `claim-star-wars-franchise-scope`.

## Continuity-Conditional Source Authority

Authority is selected by continuity and work, not assigned by one global Canon-first ranking.

| Selected mode | Primary authority | Supporting evidence | Inactive comparison material |
| --- | --- | --- | --- |
| `star-wars-canon` | selected Canon narrative work in its released form | compatible official Databank, era, catalog, and Lucasfilm explanations | Legends and alternate works unless proposition-level crossover is accepted |
| `star-wars-legends` | exact selected Legends work and edition | official Legends policy, product pages, and compatible selected Legends works | Canon reuses and outcomes unless explicitly imported |
| `star-wars-visions-selected` | exact selected *Visions* short | official anthology and creator-context pages | Canon, Legends, and other shorts except as labeled inspiration |
| `star-wars-lego-selected` | exact selected LEGO work | official work-specific descriptions | other LEGO works and mainline continuities unless explicitly imported |
| `star-wars-crossover-selected` | exact selected promotional/crossover work | official work-specific production context | mainline chronology unless the selected premise establishes a link |
| `star-wars-campaign-divergent` | accepted pre-divergence sources plus the recorded campaign replacement | selected comparison sources | later official outcomes as automatic corrections |

Within an active mode, direct selected-work events outrank public summaries; summaries support discovery and broad verification rather than replacing narrative context. Official production interviews can establish continuity, format, or intent but are not automatically in-world facts. Package-original content remains labeled and subordinate to accepted campaign choices. Fan wikis, search snippets, recollection, merchandise, and unsourced social posts carry no authority.

An explicit crossover requires proposition-level arbitration: identify which source supplies each fact, which conflicts are rejected, and what new campaign bridge is original. Material from an unselected continuity is comparison evidence, not lower-priority truth.

## Continuity And Editorial Modes

### `star-wars-canon`

Current coordinated Canon is the default. Import only propositions established by selected Canon works or compatible official summaries. A name with a Legends predecessor receives only the Canon history actually re-established.

### `star-wars-legends`

The former Expanded Universe is an opt-in continuity. Select exact works and editions. Legends contradictions, retcons, game branches, and long chronology require local arbitration rather than an assumption that every item coexists.

### `star-wars-visions-selected`

Select one *Star Wars: Visions* short and treat it as an alternate or continuity-independent work. Its aesthetics, history, technology, and Force presentation govern only the selected adaptation unless the campaign records a crossover. Source claim: `claim-star-wars-visions`.

### `star-wars-lego-selected`

Select one LEGO work and inspect its own premise. *Rebuild the Galaxy* is an explicit alternate remix; that does not establish one continuity status for all LEGO releases. LEGO construction logic and comedy are not universal physics. Source claim: `claim-star-wars-lego-alternate`.

### `star-wars-crossover-selected`

Promotional crossovers and parodies remain isolated selected works. Brand celebration does not make outside characters or events part of galactic history. Source claim: `claim-star-wars-crossover`.

### `star-wars-campaign-divergent`

Record a precise divergence point, selected prior history, replacement proposition, and downstream effects. Later official outcomes become comparison material rather than automatic corrections.

`selected-work` is an editorial scope, not a seventh continuity. Era, medium, continuity, and gameplay status remain independent fields.

## Official Era Register

The official era page supplies qualitative transitions, not universal hard BBY/ABY boundaries. Exact years require the selected work.

| Era id | Official name | Qualitative scope | Main package risk |
| --- | --- | --- | --- |
| `star-wars-era-dawn-jedi` | Dawn of the Jedi | earliest Force discovery and first Jedi context | importing later institutions or powers backward |
| `star-wars-era-old-republic` | The Old Republic | ancient Republic, Jedi protection, and Sith emergence | confusing Canon era name with Legends SWTOR continuity |
| `star-wars-era-high-republic` | The High Republic | Republic and Jedi expansion, exploration, and high confidence | treating the era as uniform prosperity everywhere |
| `star-wars-era-fall-jedi` | Fall of the Jedi | returning Sith threat, galactic war, and Jedi collapse | reducing all play to named Clone Wars outcomes |
| `star-wars-era-reign-empire` | Reign of the Empire | authoritarian consolidation, military expansion, and Jedi persecution | normalizing occupation or making rebellion inevitable |
| `star-wars-era-rebellion` | Age of Rebellion | expanding resistance against Imperial rule | replacing published heroes or making every cell identical |
| `star-wars-era-new-republic` | The New Republic | rebuilding, reunification, demilitarization, and Imperial remnants | importing one television series as the whole era |
| `star-wars-era-first-order` | Rise of the First Order | Imperial successor power, New Republic attack, and Resistance response | assuming complete public knowledge of the threat |
| `star-wars-era-new-jedi-order` | New Jedi Order | future after *The Rise of Skywalker* and renewed Jedi-building context | inventing unreleased outcomes as settled canon |

Source claim: `claim-star-wars-eras`.

## Chronology Selection Modes

Chronology is conditional on editorial mode rather than forced into a Canon-oriented era.

- `star-wars-chronology-official-era` — one official qualitative era governs; required for the default Canon opening.
- `star-wars-chronology-selected-work` — the selected Canon, Legends, Visions, game, or other work supplies its own chronology.
- `star-wars-chronology-remixed` — an explicitly alternate work combines multiple eras or roles; record every contributor without treating the remix as mainline history.
- `star-wars-chronology-not-applicable` — no useful in-world era mapping exists for the selected promotional, crossover, or abstract premise.

An optional official-era compatibility mapping supports discovery but never proves continuity. SWTOR may be associated with The Old Republic for navigation while remaining selected-work Legends chronology. Visions and LEGO selections may use work-local, remixed, or not-applicable chronology.

## Default Continuity Decision

The inert proposal combines:

1. `star-wars-canon`
2. `star-wars-chronology-official-era`
3. `star-wars-era-new-republic`
4. an early reconstruction interval without a package-imposed BBY/ABY year
5. one original frontier corridor and local communities
6. Imperial remnants as a possible pressure, not an omnipresent empire
7. no automatic import from a particular New Republic-era series, novel, comic, or game
8. no required Jedi, Sith, Mandalorian, Skywalker, Solo, Palpatine, or other published figure
9. no default Force-sensitive PC

The official anchors are narrow: the New Republic restores a Senate, negotiates with Imperial remnants, reduces military capacity, and remains vulnerable. Exact offices, fleets, local law, borders, technology access, and reconstruction programs remain campaign-instance or selected-work research. Source claim: `claim-star-wars-new-republic`.

## Media Metadata Contract

Every imported proposition records:

- continuity mode
- chronology mode, official era when applicable, selected-work chronology, and date confidence
- selected work and edition/release
- medium
- fixed event, setting fact, character claim, adaptation choice, presentation, gameplay mechanic, or player-variable outcome
- source and claim id
- confidence and unresolved tension
- spoiler band
- mutability after acceptance

When sources differ:

1. Preserve both propositions with labels.
2. Ask which continuity and selected work govern.
3. Choose one, reconcile explicitly, or record a divergence.
4. Carry consequences rather than blending details invisibly.
5. Never use visual familiarity or a game affordance as cross-media proof.

## Games And Interactive Works

An official game may contain a fixed Canon or Legends narrative, branching player-authored states, and gameplay abstraction at the same time.

- **Fixed narrative:** only events and facts the official work establishes regardless of ordinary play variation.
- **Player-variable:** avatar, class, appearance, dialogue, morality, route, companions, optional outcomes, and other branch-dependent states.
- **Mechanic-only:** HUD, checkpoints, respawn, repeated enemies, health bars, difficulty, cooldowns, inventory capacity, loot rarity, talent trees, map markers, fast travel, crafting, and progression.
- **Presentation:** camera, animation, music, loading transitions, map compression, and encounter density.

Do not convert any of the last three categories into universal lore without a separate fiction decision. Source claim: `claim-star-wars-game-layer`.

SWTOR is treated as a continuing Legends work because its story began before the 2014 reset and later official expansions continue it. This is an official-policy inference, not a visible badge on the current product page. Its class stories and decisions remain player-variable. The official era name The Old Republic does not canonize SWTOR. Source claim: `claim-star-wars-swtor-legends`.

## Force And Tradition Protocol

- The Force is mysterious, life-connected, and not exhausted by one rules list.
- Sensitivity, belief, training, institutional membership, and moral choice are separate.
- Jedi and Sith are historical institutions, not universal labels for every light- or dark-side user.
- Nightsisters and other traditions require their own selected sources.
- Chirrut Îmwe demonstrates that belief and discipline need not imply Jedi membership or overt Force powers.
- A player chooses whether their character is sensitive, believes, trains, joins a tradition, conceals it, or rejects the framing.
- No diegetic test may reveal a player's identity, morality, destiny, or consent boundary.

Source claims: `claim-star-wars-force`, `claim-star-wars-jedi`, `claim-star-wars-sith`, `claim-star-wars-force-traditions`.

## Politics And Era Separation

The Galactic Republic, Senate, Empire, Rebel Alliance, New Republic, First Order, and Resistance are not interchangeable or simultaneously dominant. Each opening records regime, jurisdiction, public legitimacy, military reach, local compliance, information, and dissent.

- Republic procedure is not proof of equal access or effective local governance.
- Imperial authority is coercive power, not moral or factual omniscience.
- Rebel membership does not make every tactic legitimate or every cell coordinated.
- New Republic recognition does not guarantee local capacity.
- First Order secrecy and Resistance warnings require era-specific knowledge boundaries.

Source claims: `claim-star-wars-republic`, `claim-star-wars-senate`, `claim-star-wars-empire`, `claim-star-wars-rebellion`, `claim-star-wars-new-republic`, `claim-star-wars-first-order`, `claim-star-wars-resistance`.

## Geography And Daily-Life Limits

Core Worlds, Mid Rim, Outer Rim, Unknown Regions, and named systems orient geography. They do not automatically establish species, language, prosperity, criminality, law, government, architecture, food, technology, or moral character.

Coruscant, Ferrix, Mandalore, and Pabu provide distinct examples, not templates for every city-world, industrial community, culture, or refugee haven. Currency, barter, medicine, communications, housing, labor, and travel must be defined locally. Source claims: `claim-star-wars-regions`, `claim-star-wars-coruscant`, `claim-star-wars-ferrix`, `claim-star-wars-economy`, `claim-star-wars-medicine`, `claim-star-wars-refugees`.

## Named Characters And Published Outcomes

Published people retain established agency and consequences. They may be absent, historical, public names, distant leaders, bounded contacts, or active figures only after explicit proximity and spoiler acceptance.

They are never automatic patrons, rescuers, relatives, mentors, villains, romantic interests, or proof of PC importance. A campaign that transfers a published decisive action to PCs must declare a divergence.

## Spoiler Bands

| Band | Scope |
| --- | --- |
| `S0` | premise-level galaxy, Force, travel, and broad faction concepts |
| `S1` | selected era institutions and places without major outcomes |
| `S2` | prequel/Clone Wars outcomes and identities |
| `S3` | Imperial era and Original Trilogy outcomes |
| `S4` | New Republic-era series, novels, comics, and games |
| `S5` | sequel-era identities and outcomes |
| `S6` | selected Legends work outcomes, including SWTOR branches |
| `S7` | selected Visions, LEGO alternate, crossover, or game-specific outcomes |

The default needs `S3` to acknowledge Imperial defeat and New Republic formation. It does not automatically reveal `S4` New Republic-era plots or `S5` later outcomes.

## Social And Cultural Guardrails

- Species and culture are separate; neither determines morality, intellect, profession, politics, accent, or Force relationship.
- Clone origin never removes personhood, distinct identity, consent, or the right to refuse a soldier role.
- Clone programming, accelerated aging, child-soldier framing, veteran abandonment, and Order 66 require explicit scope and safety choices.
- Droid chassis or function never settles consciousness, ownership, freedom, pronouns, memory, or moral standing. Memory wipes and restraining devices require consent boundaries.
- Mandalorians are not one creed, clan, political program, profession, or personality.
- Slavery, forced labor, trafficking, occupation, torture, interrogation, mind influence, genocide, planetary destruction, and refugee harm are never decorative darkness.
- Cybernetics and disability are not automatic corruption, cure, punishment, or villain coding.
- Force traditions are not universal analogies for real religions; no player must accept a spiritual or chosen-one arc.
- Minors require explicit safeguarding. War does not excuse sexualization, torture spectacle, or sole responsibility for institutional failure.
- Famous lineage, prophecy, and hidden ancestry require player request; they are never surprise upgrades or identity overrides.

Source claims: `claim-star-wars-clones`, `claim-star-wars-droids`, `claim-star-wars-mandalorians`, `claim-star-wars-syndicates`, `claim-star-wars-anti-essentialism`.

## Claim And Confidence Protocol

Every official proposition resolves to a defined claim entry in [Source Provenance](source_provenance.md).

- **High:** explicit on an inspected official public page.
- **Medium:** broad synthesis, official-policy inference, or selected commercial work needed for exact detail.
- **Low:** insufficient for operational use; research before materialization.
- **Package-original:** design proposal, not an official claim.

Absence from a page is not proof that a proposition is false. Dynamic catalog limitations, inaccessible commercial text, and search snippets do not become evidence.

## Divergence Record

Every accepted divergence preserves:

- divergence id and point
- prior continuity, chronology mode, official era or work-local chronology, selected work, and proposition
- campaign replacement and reason
- participant consent
- affected people, institutions, routes, technology, relationships, and knowledge
- public, restricted, secret, or player-private visibility
- treatment of later official material

A fictional divergence cannot activate an unselected proposal, alter another player's exclusive/private fields, collapse GM/player knowledge, or waive safety limits.
