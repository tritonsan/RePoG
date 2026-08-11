# Star Wars Universe Adaptation Notes

## Current Integration Status

- Runtime loader: none
- Package registry: none
- Automatic campaign creation: none
- Active campaign mutation: none
- Schema contract: none
- Reference package completeness: sufficient for a future Session 0 route

This package adds Markdown reference content, not infrastructure. Its presence does not imply acceptance, auto-loading, or readiness. Future implementation may transform it only after separate design establishes schemas, versioning, selection, source ownership, spoilers, knowledge separation, consent, and explicit user approval.

## Future Selection Flow

1. Present the example-world catalog.
2. Ask whether the user wants official Star Wars, generic space fantasy, a divergent setting, or another world.
3. Present Canon/Legends and media-separation warnings.
4. Select continuity, chronology policy, official era when applicable, exact date policy, allowed works, media, and spoiler ceiling.
5. Separate fixed game narrative, player-variable outcomes, gameplay mechanics, and presentation.
6. Select system-neutral fiction or an owned rules implementation.
7. Select one of sixteen group fantasies, mandate, size, authority, refusal, and exit rights.
8. Select one physical theater and at most one connection layer.
9. Select one frame or create a custom bounded pressure.
10. Run character-focused Session 0 for species, culture, body, disability, clone/droid status, Force relationship, history, ties, private facts, and boundaries.
11. Set travel, technology, Force, evidence, medicine, combat, coercion, war, minors, social-theme, and accessibility contracts.
12. Research every unresolved law, power, species, place, technology, organization, or named figure needed for the opening.
13. Prune to relevant truths, powers, places, facts, and sources.
14. Materialize accepted content into existing campaign-owned files.
15. Run normal worldbuild, finalization, validation, and readiness gates.

Do not bypass existing workflow rules because the package is researched.

## Authority During Materialization

1. Explicit user choices and safety boundaries
2. Player-authored identity, body, species/culture relationship, clone/droid status, Force relationship, history, ties, and private context
3. Accepted campaign divergences and homebrew
4. Selected continuity, era, works, official sources, and rules
5. Selected package truths, theater, powers, and frame
6. Package defaults
7. Unselected package content

Accepted campaign history outranks later package updates. Unselected material has no authority.

## Semantic-Layer Mapping

| Semantic layer | Relationship to materialization precedence |
| --- | --- |
| Template-Fixed | selected fictional invariants constrain package use but remain below explicit campaign choices, player authority, and accepted divergences |
| Campaign-Instance | accepted continuity choices, local facts, rules, divergences, and established campaign history govern the active world |
| Player-Authored | affected-player authority is highest for identity, concept, body, private history, relationships, and boundaries |
| Era/Media-Specific | selected chronology, official era or work-local chronology, continuity, work, and media status determine which official propositions are eligible |

Cross-cutting process safeguards are not a fifth semantic layer. Affirmative selection, consent, accessibility, safety, and knowledge separation constrain every precedence level and are never fictional divergences.

Package defaults occupy the lowest selectable position. Unselected content remains inert.

## Package-To-Campaign Mapping

| Package source | Campaign owner | Materialization rule |
| --- | --- | --- |
| `manifest.md` | Session 0 summary and research metadata | copy id/version and accepted selections only |
| `canon_policy.md` | `campaign/research_dossier.md` and Session 0 canon fields | record continuity, chronology policy, official era or work-local chronology, works, media, game layer, spoilers, and divergences |
| `world_operating_model.md` | `campaign/world.md` and `campaign/world_truths.md` | copy only opening-relevant causal truths; preserve claim ids |
| `regions.md` | current workflow's places, issues, routes, and world owners | one physical theater and at most one connection layer |
| `factions.md` | `campaign/factions/`, faces, places, and issues | instantiate only active bounded powers with local faces, dependencies, limits, knowledge, and next actions |
| `campaign_frames.md` — visible material | player-visible pitch, issues, opening, faces, and places | copy only the selected visible premise, actors, causal pressure, and safe foreshadowing |
| `campaign_frames.md` — protected material | `campaign/knowledge_boundaries.md` GM-only section | store the complete selected truth, reveal gates, protected wording, and reveal status only in this authoritative owner; optional clue or prep artifacts contain fact-ID references and flexible delivery channels only; block if the GM-only owner is unavailable |
| `session_zero_options.md` | Session 0 interview and PC integration | ask decisions; never copy unanswered prompts as facts |
| `knowledge_layers.md` | `campaign/knowledge_boundaries.md` | create actual holders, evidence, spoilers, and reveal gates for selected facts only |
| `source_provenance.md` | `campaign/research_dossier.md` | preserve source/claim ids, confidence, limits, era, medium, and verification date |

No `*-secret-*` id or protected body may enter a player-visible target. Specialized campaign files remain owners; package prose never overrides them after materialization.

## Template-Fixed Content

### Divergeable Fictional Invariants

Once affirmatively selected, preserve unless the table records a fictional divergence:

- this is official Star Wars fiction, not an unlabeled generic space opera
- one continuity policy and one chronology policy govern active history; an official era is required only when that chronology maps to one
- Canon and Legends remain distinct
- era, medium, selected-work scope, continuity, fixed narrative, player-variable state, mechanics, and presentation remain labeled
- the Force is life-connected and plural rather than one universal game power list
- distance, ships, routes, fuel, navigation, communications, medicine, and machines have local dependencies
- political regimes, law, and public knowledge change across eras
- regions supply geography, not cultural destiny
- species, culture, genetics, chassis, and homeworld do not determine morality or allegiance
- ordinary labor, care, repair, trade, diplomacy, evidence, and community choices matter
- famous characters retain published agency but are not default solutions

### Process Safeguards

These cannot be changed by a fictional divergence:

- package proposals remain inert until affirmatively selected
- player authorship controls identity, species/culture relationship, body, disability, cybernetics, clone/droid status, Force relationship, sensitive history, ties, and boundaries
- only the affected player may grant narrow explicit permission over an exclusive/private field
- consent, accessibility, and safety boundaries outrank fiction and mechanics
- player-visible, GM-only, institutional, spoiler, and player-private knowledge remain separated
- `campaign/knowledge_boundaries.md` is the sole authoritative owner of complete protected truth, holders, wording, and reveal status
- optional GM-only clue or prep artifacts contain references only—fact ids and flexible delivery channels—never a duplicated truth body or independent status
- materialization blocks if the authoritative GM-only section is unavailable or protected content would project to a player-visible target
- campaign history outranks package updates

## Campaign-Instance Content

Select or create during Session 0:

- continuity, chronology policy, official era when applicable, selected-work chronology, exact date or qualitative interval, works, media, game layers, and spoilers
- rules system and interpretation of travel, Force, combat, medicine, technology, and consequences
- physical theater, connection layer, route map, worlds, adjacency, and off-stage boundary
- local government, jurisdiction, law, economy, currency acceptance, labor, food, housing, and care capacity
- ship, station, settlement, yard, clinic, council, unit, cell, guild, tradition, or mission boundary
- group mandate, authority, client relationship, shared responsibility, refusal, exit, and scale
- active powers, local faces, objectives, methods, constituencies, dependencies, limits, information, and next actions
- ship capabilities, fuel, parts, nav data, communications, cargo, maintenance, and access
- droid and clone local status, memory, privacy, maintenance, rights, and relationships
- Force traditions, teachers, sites, powers, evidence, visions, and consent
- public account, propaganda, rumor, sensor record, hidden truth, and reveal gates
- famous-character and famous-lineage proximity
- consequence severity and safety settings

These facts never write back into the reusable package during play.

## Player-Authored Content

Never prefill as accepted truth:

- name, pronouns, gender, identity, appearance, body, and presentation
- species, ancestry, culture, language, homeworld, citizenship, and belonging
- disability, health, cybernetics, access needs, and relationship to medicine
- clone origin, chosen name, military relationship, programming concerns, aging, and veteran history
- droid chassis relationship, pronouns, autonomy, ownership history, memory, wipe history, and personhood position
- Force sensitivity, belief, practice, tradition, morality, visions, temptation, and destiny
- family, lineage, famous relationship, inheritance, and reputation
- profession concept, desired competency direction, ambition, ethics, loyalties, and debts; rules-compatible capability implementation is shared and cannot override the concept or player veto
- occupation, rebellion, war, enslavement, displacement, trauma, bereavement, imprisonment, or coercion
- friendship, romance, rivals, dependents, secrets, and private knowledge
- lines, veils, desired themes, and content boundaries

A blank field remains unknown, not permission for inference.

## Era/Media-Specific Content

Never import without the matching selection:

- `star-wars-era-dawn-jedi`: earliest-Jedi and Force-discovery material
- `star-wars-era-old-republic`: selected Canon ancient history or selected Legends work; SWTOR branches remain player-variable
- `star-wars-era-high-republic`: selected publication, phase, date, institutions, and frontier conditions
- `star-wars-era-fall-jedi`: Clone Wars, Republic crisis, Jedi military role, clones, and known collapse
- `star-wars-era-reign-empire`: Imperial consolidation, occupation, purge, and local resistance
- `star-wars-era-rebellion`: alliance structure, published battles, and Imperial defeat
- `star-wars-era-new-republic`: reconstruction, remnants, demilitarization, and selected series/prose outcomes
- `star-wars-era-first-order`: New Republic, First Order, Resistance, and sequel-era outcomes
- `star-wars-era-new-jedi-order`: only released official future material
- `star-wars-legends`: exact selected Legends work and its own contradictions or retcons
- `star-wars-visions-selected`: exact anthology short and alternate premise
- `star-wars-lego-selected`: exact LEGO work and alternate/comedic logic
- `star-wars-crossover-selected`: exact promotional/parody work
- selected game: fixed narrative, selected branch, presentation, and mechanics as four separate fields

## Source Preservation

Every materialized official proposition retains:

- package id and version
- claim and source ids
- confidence and retrieval date
- continuity, chronology policy, and official era or selected-work chronology as applicable
- selected work, release/edition, and medium
- fixed narrative, player-variable, presentation, or mechanic status
- canon status and mutability
- spoiler band
- visibility and actual holders
- unresolved-detail flag

Rewording preserves provenance on the proposition.

## Continuity Isolation

For every imported proposition, record whether it is:

- authoritative in selected Canon work and era
- compatible official summary
- Legends selected-work material
- selected Visions alternate material
- selected LEGO alternate material
- promotional/crossover material
- fixed game narrative
- player-variable game outcome
- gameplay abstraction
- production/presentation detail
- package-original
- campaign-original
- divergent
- unresolved
- rejected

Never use an era label as continuity proof. Never use SWTOR to fill Canon Old Republic silence. Never use a Canon reuse to import a Legends biography. Never use a game loop, film shot, animation style, LEGO gag, or crossover as universal physics.

## Region Materialization

For the selected theater:

- define a hard opening boundary
- cite every canonical anchor
- label every original world, district, settlement, station, route, ship, business, and resident
- define livelihoods, services, accessibility, and environmental needs
- define one threshold to the wider galaxy
- define what is off-stage
- attach at most one connection layer
- avoid turning region into species, culture, poverty, crime, or morality

## Organization Materialization

For each active power:

- select exact era and bounded office, unit, cell, crew, council, guild branch, syndicate crew, or tradition circle
- cite the broad anchor
- define local decision authority, constituency, and accountability
- define controlled service, asset, record, territory, or relationship
- define capability available now
- define logistical and labor dependencies
- define one internal disagreement and information gap
- define what PCs may refuse
- define affected people and next action

A logo is not a local actor.

## Capability Materialization

For every ship, Force, weapon, medical, droid, communications, or technical capability:

1. Name the fictional effect.
2. Identify official source, rules source, or original status.
3. Identify user knowledge and access.
4. Identify ship, component, fuel, part, training, site, medicine, record, permission, or helper.
5. Define target, range, duration, counters, evidence, and consequence only as sourced or accepted.
6. Record consent and accessibility implications.
7. Record what success cannot solve.
8. Keep one ruling local unless later promoted through research and agreement.

Do not build a universal encyclopedia during materialization.

## Droid And Clone Safeguards

- Ask each affected player how their character understands personhood, manufacture, naming, programming, memory, body, and service.
- Never equate a clone's genetics with obedience or personality.
- Never equate a droid's chassis, owner claim, or function with consent or inner life.
- Treat memory wipes, restraining devices, behavioral overrides, command conditioning, accelerated aging, and medical records as consent-sensitive.
- Define local law separately from a character's self-understanding and the table's dignity contract.
- Do not use slavery or child-soldier framing for surprise darkness.

## Mechanical Adaptation

Preserve across systems:

- selected continuity, era, work, and media labels
- costly connection and infrastructure
- changing regimes and bounded authority
- plural Force relationships
- ordinary labor, care, repair, diplomacy, and evidence
- local economy and law
- anti-essentialism, player authorship, and knowledge custody
- persistent social and material consequences

Replace per system:

- attributes, skills, moves, difficulty, resources, damage, healing, advancement, and downtime
- Force powers, points, dice, morality tracks, talents, cooldowns, crafting, inventory, and action economy
- chase, duel, space combat, negotiation, investigation, travel, and mass-conflict procedures

No imported mechanic becomes lore without a separate fiction decision.

## Migration And Package Updates

Offer:

- **keep-current:** retain accepted campaign material
- **adopt-update:** import selected corrected propositions after review
- **custom-reconcile:** compare and record a campaign-specific resolution

Never overwrite continuity, player authorship, private facts, safety settings, revealed knowledge, or campaign history.

## Validation Checklist

Before a future workflow declares a materialized Star Wars world ready:

- [ ] The user explicitly selected this package.
- [ ] Continuity, chronology policy, official era when applicable, selected-work chronology, date policy, works, media, game layers, rules, and spoilers are accepted.
- [ ] Canon, Legends, Visions, LEGO, crossover, fixed narrative, player-variable outcomes, mechanics, and presentation remain labeled.
- [ ] One physical theater and at most one connection layer are selected.
- [ ] Group mandate, size, authority, refusal, exit, and scale are accepted.
- [ ] Player species/culture, body, clone/droid status, Force relationship, lineage, history, and private context were not prefilled.
- [ ] Travel, Force, technology, evidence, medicine, coercion, and combat contracts are explicit.
- [ ] Species, droid, clone, disability, war, slavery, refugee, and minor safeguards are explicit.
- [ ] Every active power has a local face, constituency, method, dependency, limit, information gap, and next action.
- [ ] The retained clock model is capped; the default has exactly two shared clocks and zero faction clocks.
- [ ] Every route/service failure has users, labor, custody, fallback, evidence, and consequence.
- [ ] Famous characters and lineage are not required to resolve the premise.
- [ ] Player-visible, institutional, spoiler, GM-only, and player-private knowledge are separated.
- [ ] Only the selected frame and matching protected truth entered campaign state.
- [ ] The complete protected truth, protected wording, holder set, and authoritative reveal status exist only in the GM-only section of `campaign/knowledge_boundaries.md`; optional GM-only clue/prep artifacts may contain fact-ID references and delivery channels only, and no `*-secret-*` id or protected content enters a player-visible target.
- [ ] Original worlds, incidents, technologies, and Force phenomena are labeled.
- [ ] Source/claim ids, confidence, era, medium, mutability, spoilers, and visibility survived.
- [ ] Normal workspace validation and audit gates pass.

## Do Not Copy During Materialization

- alternate continuities, eras, media, game branches, or presentation layers
- alternate regions, connection layers, frames, or protected truths
- every planet, government, army, cell, guild, syndicate, tradition, ship, droid, species, or technology
- UI, respawn, combat density, map compression, loot, inventory, fast travel, or progression
- film/animation composition, sound, costume, scale, or choreography without acceptance
- hypothetical player species, culture, clone/droid status, Force sensitivity, lineage, disability, trauma, relationships, or secrets
- famous-character material without accepted proximity
- source descriptions irrelevant to current decisions
- the full source index when only a subset is active

## Future Infrastructure Boundary

A future ready-world system may define a machine-readable manifest and deterministic materializer. That work must be designed separately. It must not infer acceptance from this directory, auto-load the package, merge continuities, expose protected truths, prefill player identity or history, turn media mechanics into lore, essentialize species or cultures, or bypass campaign ownership, consent, finalization, and validation.
