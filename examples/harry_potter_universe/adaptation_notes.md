# Harry Potter Universe Adaptation Notes

## Current Integration Status

- Runtime loader: none
- Package registry: none
- Automatic campaign creation: none
- Active campaign mutation: none
- Schema contract: none
- Reference package completeness: sufficient for a future Session 0 route

This package adds reference content, not infrastructure. Its presence does not imply acceptance, auto-loading, or readiness. Future implementation may read or transform it only after separate design establishes schemas, versioning, validation, continuity selection, source ownership, spoilers, knowledge separation, consent, and explicit user approval.

## Future Selection Flow

1. Present the example-world catalog.
2. Ask whether the user wants the Harry Potter fictional universe, a generic hidden-magic world, or another setting.
3. Offer an out-of-fiction property-engagement choice without requiring debate.
4. Present the continuity warning: novels, official web writings, Harry Potter films, Fantastic Beasts, Cursed Child, and Hogwarts Legacy are not one unlabeled source layer.
5. Select continuity, era, exact date range, allowed official sources, and spoiler ceiling.
6. Select system-neutral fiction or an owned rules implementation.
7. Select one group fantasy, mandate, size, refusal right, and scale.
8. Select one physical theater and at most one compatible connection layer.
9. Select one frame or create a custom local need/institution/knowledge pressure.
10. Run character-focused Session 0 for identity, body, magical status, family, school, House, wand, capability, history, ties, private facts, and boundaries.
11. Set magic-invention, evidence, healing, coercion, secrecy, violence, minors, social-theme, and accessibility contracts.
12. Run targeted research for every unresolved spell, law, institution, creature, place, named person, or media-specific detail required by the opening.
13. Prune the package to relevant truths, actors, places, facts, and sources.
14. Materialize accepted content into existing campaign-owned files.
15. Run normal worldbuild, finalization, validation, and readiness gates.

Do not bypass existing workflow rules because the package is researched.

## Authority During Materialization

1. Explicit user choices and safety boundaries
2. Player-authored identity, body, magical status, family, history, relationships, and private context
3. Accepted campaign divergences and homebrew
4. Selected continuity, era, official sources, and rules
5. Selected package truths, theater, powers, and frame
6. Package defaults
7. Unselected package content

Accepted campaign history outranks later package updates. Unselected material has no authority.

## Package-To-Campaign Mapping

| Package source | Campaign owner | Materialization rule |
| --- | --- | --- |
| `manifest.md` | Session 0 summary and research metadata | copy package id/version and selected defaults only |
| `canon_policy.md` | `campaign/research_dossier.md` and Session 0 canon fields | record continuity, era, sources, spoilers, divergences, and unresolved detail |
| `world_operating_model.md` | `campaign/world.md` and `campaign/world_truths.md` | copy only causal truths relevant to the opening; preserve claim ids |
| `regions.md` | current workflow's places, issues, routes, and world owners | materialize one physical theater and at most one connection layer |
| `factions.md` | `campaign/factions/`, faces, places, and issues | instantiate only active powers with local faces, methods, dependencies, limits, knowledge, and clocks |
| `campaign_frames.md` — visible material | player-visible pitch, issues, opening, faces, and places | copy only the selected visible premise, actors, causal pressure, and safe foreshadowing |
| `campaign_frames.md` — protected material | `campaign/knowledge_boundaries.md` GM-only section and a workflow-designated GM-exclusive projection/notes owner | copy only the matching protected truth, reveal gates, and forbidden-early wording; block materialization if no GM-exclusive owner exists |
| `session_zero_options.md` | Session 0 interview and PC integration | ask decisions; never copy unanswered prompts as facts |
| `knowledge_layers.md` | `campaign/knowledge_boundaries.md` | create actual holders, evidence, spoilers, and reveal gates for selected facts only |
| `source_provenance.md` | `campaign/research_dossier.md` | preserve source/claim ids, confidence, limitations, era, media origin, and verification date |

Specialized campaign files remain owners. No package summary overrides them after materialization.

## Template-Fixed Content

This section contains two distinct authority classes.

### Divergeable Fictional Invariants

Once affirmatively selected, preserve these unless the table records a fictional continuity or setting divergence:

- this is the Harry Potter fictional universe, not a generic magic-school kit
- one continuity policy and one era govern active history and capabilities
- the seven novels are the default narrative spine, with official web writing used transparently as supplement
- film design, stagecraft, and game mechanics remain distinct from setting truth
- secrecy operates through law, infrastructure, labor, behavior, and consequence
- magic is method-bound and does not erase evidence, labor, or institutional consequence
- government, schools, hospitals, banks, press, and enforcement are fallible institutions, not omniscient abstractions
- blood status is ideology, not objective worth
- Houses do not determine morality or personality
- goblins, house-elves, werewolves, Squibs, creatures, and other affected groups retain agency and diverse interests
- famous characters retain published agency but are not default solutions

### Process Safeguards

These are not fictional propositions and cannot be changed by a continuity divergence:

- package proposals remain inert until affirmatively selected
- player authorship controls identity, body, magical status, family, House, wand, sensitive history, private ties, and boundaries
- only the affected player may grant narrow, explicit permission over an exclusive or private field
- consent, accessibility, and safety boundaries outrank fiction and mechanics
- player-visible, GM-only, institutional, spoiler, and player-private knowledge remain separated
- campaign history outranks package updates

Record fictional changes as continuity, era, thematic, or campaign divergences. Record any player-authority delegation separately, with its scope and the affected player's consent; never represent it as a fictional divergence.

## Campaign-Instance Content

Select or create during Session 0:

- exact continuity, era, year, date, season, and divergence point
- allowed novels, web writings, films, screenplays, stage scripts, games, and spoilers
- rules system and interpretation of magical capabilities
- physical theater, connection layer, and adjacency
- original community, school year, department, ward, business network, route, or event boundary
- group size, mandate, client posture, shared responsibility, refusal, and exit rules
- active offices, school teams, Healers, bank functions, traders, press, rights groups, families, and international actors
- local faces, objectives, methods, dependencies, clocks, limits, and knowledge
- travel connections, permissions, fallback routes, witnesses, and secrecy procedures
- care capacity, ingredients, referrals, confidentiality, accessibility, and consent
- economy, custody, ownership, labor, apprenticeship, supply, and repair conditions
- spell, potion, object, creature, plant, wand, and countermeasure inventory actually needed
- public account, rumor, evidence, institutional record, hidden truth, and reveal gates
- named-character proximity
- consequence severity and safety settings

These facts never write back into the reusable package during play.

## Player-Authored Content

Never prefill as accepted truth:

- name, pronouns, gender, identity, appearance, body, and presentation
- disability, health, access needs, and relationship to magical care
- culture, language, nationality, citizenship, and community belonging
- magical or non-magical status and relationship to magical society
- family, ancestry, blood-status label, lineage, inheritance, and reputation
- school, House, educational history, and feelings about Sorting
- wand, magical practice, companion, pet, or creature relationship
- profession, capability, ambitions, ethics, beliefs, and loyalties
- war experience, trauma, bereavement, imprisonment, coercion, or victimization
- friendships, romance, rivals, debts, dependents, secrets, and private knowledge
- relationship to published characters
- lines, veils, desired themes, and content boundaries

A blank field remains unknown, not permission for inference.

## Era/Media-Specific Content

Never import without the matching selection:

- `harry-potter-era-1800s`: nineteenth-century institutions, transport, people, and social conditions
- `harry-potter-game-hogwarts-legacy`: game story, locations, ancient-magic premise, companions, and accepted narrative facts
- `harry-potter-era-fantastic-beasts`: dates and events established by the selected film or screenplay; wider twentieth-century history needs separate sources or an original label
- `harry-potter-screen-fantastic-beasts`: film-specific people, events, designs, and outcomes
- `harry-potter-era-first-war`: 1968–1981 offices, resistance, conflict, and family consequences
- `harry-potter-era-main-series`: annual 1991–1998 events, staff, school conditions, deaths, and institutional capture
- `harry-potter-screen-hp`: adaptation-only chronology, architecture, costumes, objects, and spell presentation
- `harry-potter-era-postwar`: verified reforms plus explicitly original reconstruction detail
- `harry-potter-era-stage-future` and `harry-potter-stage-cursed-child`: next-generation and stage-story facts

## Source Preservation

Every materialized official claim should retain:

- package id and version
- claim id
- source id or package-original designation
- confidence
- selected continuity and era
- media origin
- canon status
- mutability
- spoiler band
- visibility and actual holders
- retrieval or verification date
- unresolved exact-mechanics flag when relevant

If prose is rewritten, preserve provenance on the proposition rather than treating new wording as a new source.

## Continuity Isolation

Store one selected continuity policy in campaign metadata. For every imported proposition, record whether it is:

- authoritative in selected continuity and era
- compatible official supplement
- historical background
- later-era spoiler
- film-only adaptation
- Fantastic Beasts screen material
- Cursed Child stage material
- Hogwarts Legacy narrative material
- gameplay abstraction
- production or presentation detail
- explicit crossover
- package-original
- campaign-original
- divergent
- unresolved
- rejected

Never use a Hogwarts Legacy combat loop to define nineteenth-century daily danger. Never use film architecture as proof of book geography. Never use Cursed Child outcomes to fill a post-war gap without selecting the stage layer. Never use fan memory to settle official silence.

## Region Materialization

For the selected theater:

- define a hard opening boundary
- cite every canonical anchor
- label every original street, room, business, service, ward, route, and resident
- include only places needed for current decisions
- define ordinary livelihoods and access needs
- define one threshold to the wider world
- define what is off-stage
- attach at most one connection layer

A famous place name is not a complete playable region.

## Organization Materialization

For each active organization or power:

- select era and exact local office, team, ward, desk, branch function, club, or coalition
- cite the source supporting its broad presence
- define local decision authority
- define service, asset, record, territory, or relationship actually controlled
- define capability available now
- define logistics and labor dependencies
- define one internal disagreement
- define information it lacks
- define what PCs can refuse
- define affected people and accountability route

A Ministry, Hogwarts, Gringotts, St Mungo's, or newspaper logo is not a local actor.

## Magical Capability Materialization

For every capability needed in the opening:

1. Name the effect in fiction.
2. Identify official source, rules source, or campaign-original status.
3. Identify practitioner knowledge and access.
4. Identify wand, ingredient, object, creature relationship, time, place, or permission.
5. Define target, range, duration, counters, evidence, and consequence only as far as sourced or accepted.
6. Record consent implications.
7. Record what success cannot solve.
8. Keep one ruling local unless later promoted through research and agreement.

Do not build a universal spell encyclopedia during materialization.

## School And Minor Safeguards

For a student campaign:

- set PC and NPC age bands
- define adult safeguarding responsibility
- identify trusted and challengeable adults
- establish curfew, discipline, privacy, dormitory, and family-contact boundaries
- separate adventure permission from institutional neglect
- keep romance age-appropriate and consent-bound
- exclude sexual content involving minors
- provide non-punitive ways to seek help
- do not make children solely responsible for institutional reform or lethal defense

## Social-Conflict Materialization

When selecting blood status, Squib exclusion, werewolf stigma, house-elf bondage, goblin-wizard conflict, prison conditions, or another structural issue:

- record whether it is foreground, background, transformed, or excluded
- let affected PCs define private identity and disclosure
- instantiate affected people with goals beyond oppression
- identify material policy, service, labor, ownership, or access at stake
- avoid a single spokesperson for an entire category
- define consent and content limits
- include institutional dependencies and possible remedies
- avoid mapping a fictional category universally onto a real marginalized group
- never make prejudice a mechanical truth about capability or morality

## Mechanical Adaptation

Preserve across systems:

- selected continuity and era
- secrecy and its practical consequences
- method-bound magic
- institutional fallibility and concrete dependencies
- evidence and knowledge custody
- ordinary work, care, trade, transport, and education
- social classifications as power, not worth
- player authorship and private facts
- persistent relational and service consequences

Replace per system:

- attributes, skills, moves, difficulty, resource tracks, damage, healing, advancement, and downtime
- spell lists, slots, points, rolls, cooldowns, crafting, inventory, and action economy
- social, investigation, chase, duel, sport, and travel procedures

No imported mechanic becomes lore without a separate fiction decision.

## Migration And Package Updates

When this package changes, offer:

- **keep-current:** campaign retains accepted material
- **adopt-update:** import selected corrected propositions after review
- **custom-reconcile:** compare and record campaign-specific resolution

Never overwrite accepted continuity, player authorship, private facts, safety settings, revealed knowledge, or campaign history. Preserve previous source ids or map them explicitly when an id changes.

## Validation Checklist

Before a future workflow declares a materialized Harry Potter world ready:

- [ ] The user explicitly selected this package and accepted property engagement.
- [ ] Continuity, era, exact year, sources, rules, and spoilers are accepted.
- [ ] A post-war opening records whether the seven-novel epilogue is fixed, selectively fixed, or divergent; Cursed Child remains separately opt-in.
- [ ] Novel, web, film, Fantastic Beasts, stage, and game layers remain labeled.
- [ ] One physical theater and at most one connection layer are selected.
- [ ] Group mandate, size, shared responsibility, refusal, exit, and scale are accepted.
- [ ] Player identity, body, magical status, ancestry, House, wand, history, and sensitive context were not prefilled.
- [ ] Magic-invention, evidence, healing, coercion, secrecy, and violence contracts are explicit.
- [ ] Social themes and accessibility boundaries are explicit.
- [ ] Minor safeguards are explicit if students are involved.
- [ ] Every active power has a local face, method, dependency, limit, information gap, and documented next action.
- [ ] The retained clock model is capped and reconciled; the default has exactly two shared clocks and no faction clocks.
- [ ] Every service failure has users, labor, custody, fallback, evidence, and consequence.
- [ ] Famous characters are not required to resolve the premise.
- [ ] Player-facing, institutional, spoiler, GM-only, and player-private knowledge are separated.
- [ ] Only the selected frame and matching secret entered campaign state.
- [ ] The protected truth, reveal gates, forbidden wording, and every `*-secret-*` id exist only in a named GM-exclusive owner; materialization blocks if none exists.
- [ ] Campaign-original magic and places are labeled.
- [ ] Claim/source ids, confidence, era, media origin, mutability, spoilers, and visibility survived materialization.
- [ ] Normal workspace validation and audit gates pass.

## Do Not Copy During Materialization

- alternate continuities, eras, and media presentations
- alternate regions or connection layers
- alternate campaign frames or protected truths
- every Ministry department, Hogwarts room, shop, ward, bank function, school, sport team, creature, or spell
- game interfaces, combat density, map compression, collectibles, or progression systems
- film-only architecture, costume, props, sound, or choreography without acceptance
- stage effects or production logistics as setting physics
- hypothetical PC ancestry, House, wand, disability, trauma, family, relationships, or secrets
- famous-character material without accepted proximity
- source descriptions that do not affect current decisions
- the full claim/source index when only a subset is active

## Future Infrastructure Boundary

A future ready-world system may define a machine-readable manifest and deterministic materializer. That work must be designed separately. It must not infer acceptance from this directory, auto-load the package, merge continuities, expose GM truths during selection, prefill player identity or history, turn game mechanics into lore, normalize fictional prejudice, or bypass campaign ownership, research, consent, finalization, and validation rules.