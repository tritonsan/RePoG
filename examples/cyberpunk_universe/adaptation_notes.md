# Cyberpunk Universe Adaptation Notes

## Current Integration Status

- Runtime loader: none
- Package registry: none
- Automatic campaign creation: none
- Active campaign mutation: none
- Schema contract: none
- Reference package completeness: sufficient for a future Session 0 route

This package adds reference content, not infrastructure. Its presence does not imply acceptance, auto-loading, or readiness. Future implementation may read or transform it only after separate design establishes schemas, versioning, validation, era selection, source ownership, spoiler handling, knowledge separation, consent, and explicit user approval.

## Future Selection Flow

1. Present the example-world catalog.
2. Ask whether the user wants the official Cyberpunk universe, a generic cyberpunk genre world, or another setting.
3. Present the era warning: 2013/2020, 2023 aftermath, 2045, and the 2070s are not one timeless present.
4. Select continuity, era, allowed official sources, and spoiler ceiling.
5. Select system-neutral fiction or an owned rules implementation.
6. Select Night City/original sub-district, named canonical district, Badlands route, or a separately researched theater.
7. Select one player fantasy, crew mandate, crew size, and scale.
8. Select one physical theater and at most one era-compatible connection layer.
9. Select a compatible frame or create a custom local need/supply/power pressure.
10. Run character-focused Session 0 for identity, body, chrome, capability, style, history, ties, debts, loyalties, and boundaries.
11. Set Net, cyberware, healthcare, Humanity/cyberpsychosis, lethality, and evidence contracts.
12. Run targeted research for every unresolved mechanic or named lore detail required by the opening.
13. Prune the package to relevant truths, actors, places, facts, and sources.
14. Materialize accepted content into existing campaign-owned files.
15. Run normal worldbuild, finalization, validation, and readiness gates.

Do not bypass existing workflow rules because the package is researched.

## Authority During Materialization

1. Explicit user choices and safety boundaries
2. Player-authored identity, body, history, relationships, and private context
3. Accepted campaign divergences and homebrew
4. Selected era, continuity, sourcebooks, and rules
5. Selected package truths, theater, powers, and frame
6. Package defaults
7. Unselected package content

Accepted campaign history outranks later package updates. Unselected material has no authority.

## Package-To-Campaign Mapping

| Package source | Campaign owner | Materialization rule |
| --- | --- | --- |
| `manifest.md` | Session 0 summary and research metadata | copy package id/version and selected defaults only |
| `canon_policy.md` | `campaign/research_dossier.md` and Session 0 canon fields | record franchise, era, continuity, sources, spoilers, rules, divergences, and unresolved details |
| `world_operating_model.md` | `campaign/world.md` and `campaign/world_truths.md` | copy only causal truths relevant to the opening; preserve claim ids |
| `regions.md` | `campaign/scale.md`, places, issues, and world | materialize one physical theater and at most one compatible connection layer |
| `factions.md` | `campaign/factions/`, faces, places, and issues | instantiate only active powers with local faces, methods, dependencies, limits, knowledge, and clocks |
| `campaign_frames.md` | pitch, issues, opening, projections, faces, and places | copy one visible premise and its protected GM truth; never copy alternate frames |
| `session_zero_options.md` | Session 0 interview and PC integration | ask decisions; never copy unanswered prompts as facts |
| `knowledge_layers.md` | `campaign/knowledge_boundaries.md` | create actual holders, evidence, spoiler bands, and reveal gates for selected facts only |
| `source_provenance.md` | `campaign/research_dossier.md` | preserve source and claim ids, confidence, limitations, era, and verification date |

Specialized campaign files remain owners. No package summary overrides them after materialization.

## Template-Fixed Content

Preserve unless the user explicitly selects another setting or divergence:

- this is the official Cyberpunk fictional universe, not a generic genre kit
- one era governs active technology, institutions, and events
- gameplay abstractions remain distinct from setting truth
- infrastructure, logistics, labor, information custody, and local relationships drive power
- corporations, governments, gangs, security providers, Nomads, and communities are internally diverse institutions
- ordinary people remain causal actors
- bodies and cyberware remain tied to personhood and consent, never inventory shorthand
- augmentation does not determine morality, humanity, violence, or identity
- technical actions require a system, access path, holder, capability, and limit
- famous characters retain published agency but are not default solutions
- player authorship controls identity, body, sensitive history, private ties, and boundaries
- campaign history outranks package updates

Record every change as a campaign continuity, era, or thematic decision.

## Campaign-Instance Content

Select or create during Session 0:

- exact era, year, date, and season
- continuity mode and divergence point
- allowed sourcebooks, DLC, anime/game spoilers, and rules
- physical theater and canonical adjacency
- district or route name, population, livelihoods, housing, services, and culture
- crew size, mandate, client posture, shared resource, and exit rules
- active corporations, contractors, district offices, gangs, security, Fixers, Nomads, media, and communities
- local faces, objectives, methods, dependencies, clocks, and limits
- utility, healthcare, market, transport, and communications conditions
- supply chain, missing link, substitute, deadline, and ownership claims
- Net model, devices, Architectures, quickhack rules, and evidence traces
- local cyberware access, maintenance, ownership, therapy, and medical context
- rumor, propaganda, official account, hidden truth, and reveal gates
- named-character proximity and spoiler visibility
- consequence severity and safety settings

These facts never write back into the reusable package during play.

## Player-Authored Content

Never prefill as accepted truth:

- PC name, pronouns, identity, appearance, body, and presentation
- culture, language, citizenship, legal identity, and community belonging
- style, fashion, music, art, and self-expression
- role, profession, capability, education, and reputation
- organic, cybernetic, assistive, medical, occupational, or expressive body choices
- cyberware visibility, function, installation, maintenance, data, debt, and ownership history
- disability, pain, dysphoria, medical treatment, therapy, and private health context
- Humanity/cyberpsychosis state, interpretation, or history
- family, Nomad ties, neighborhood, employer, gang, corporation, state, or client relationship
- debts, crimes, coercive contracts, trauma, betrayal, blackmail, and secret patron
- ambitions, loyalties, beliefs, politics, lines, and job refusal
- romance, sexuality, pregnancy, dependents, and private relationships
- crew ties, shared history, secrets, and desired PvP
- relationship to a published character or event

The package may offer prompts and compatible fantasies only.

## Era/Media-Specific Content

Never materialize outside its selected origin:

- 2013/2020 corporate, Net, technology, style, and officeholder assumptions
- 2023 war operations, detonation detail, and immediate aftermath
- 2045 scarcity, CitiNet, local NET Architectures, NeoCorp opportunity, district structure, and reconstruction
- 2070-era quickhacks, gear, cyberware, anime biographies, and Mission Kit events
- 2077 game-era technology, institutions, braindance presentation, named quests, and outcomes
- *Phantom Liberty* Dogtown/NUS actors, alliances, and outcomes
- gameplay UI, inventory, fast travel, skill trees, encounter levels, and rule abstractions
- announced but unverified or unreleased product claims

For every imported fact, record `era_origin`, `media_origin`, `spoiler_band`, and whether it is authoritative, adapted, divergent, or unresolved.

## Default Opening Pruning

A `cyberpunk-frame-last-light` materialization begins with no more than:

- 2045 and one selected rules source
- one original bounded Night City rebuilding district
- one housing cluster
- one clinic and emergency route
- one power/water controller and workshop
- one depot and one supply route
- one community/labor network
- one contractor/corporate or district claimant
- one security provider with a narrow contract
- one Fixer or broker
- one Nomad courier or transport unit
- five to seven active faces total
- one failing-service clock
- one institutional-seizure clock
- five to eight knowledge facts
- one protected hidden causal chain
- one CitiNet/data discrepancy only if the connection layer is selected

Keep citywide corporate leadership, every named gang, national politics, deep Old NET, Blackwall, Dogtown, orbital affairs, and famous characters offstage unless an accepted route requires them.

## Last Light Materialization Example

For `cyberpunk-frame-last-light`:

- Pitch receives only the player-facing promise.
- Research dossier receives `cyberpunk-2045-red`, package version, selected official sources, claims, confidence, and unresolved mechanics.
- World receives only relevant truths about history, infrastructure, scarcity, ordinary people, body autonomy, information custody, institutions, and crew dependency.
- Scale receives one district, utility junction, clinic, housing cluster, workshop, depot, and supply route.
- Issues receive the failing controller, duplicate serial, missing driver, ownership claim, security deadline, and service deadline.
- Factions instantiate the cooperative/community, claimant, security contract, Fixer/transport route, and technical custodian only.
- Faces receive names and identities only after Session 0 selection.
- Knowledge boundaries receive `cyberpunk-frame-last-light-secret-001` and its three-chain reveal gate.
- Opening begins with the first visible utility failure or disputed depot handoff, not a timeline lecture.
- PC integration receives only player-approved district, route, employer, body, debt, and crew ties.

## Source Preservation

Every materialized official claim should retain:

- package id and version
- claim id
- source id or package-original designation
- confidence
- selected era and continuity
- media origin
- canon status
- mutability
- spoiler band
- visibility and actual holders
- retrieval or verification date
- unresolved exact-mechanics flag when relevant

If prose is rewritten, preserve provenance on the proposition rather than treating new wording as a new source.

## Continuity Isolation

Store one selected continuity mode in campaign metadata. For every imported claim, record whether it is:

- authoritative in the selected era
- historical background
- subject-source detail
- later-era spoiler
- adaptation-only presentation
- gameplay abstraction
- explicit crossover
- campaign-original
- divergent
- unresolved
- rejected

Never use 2070 quickhacks to fill a 2045 capability gap. Never use 2045 scarcity unchanged in 2077 without a source. Never use a video-game interface as universal perception. Never use fan memory to settle official silence.

## Named Organization Materialization

For each active organization:

- select era and exact local office/unit
- cite the source supporting its presence
- define local decision authority
- define asset, contract, territory, or service actually controlled
- define capability available now
- define logistics and labor dependencies
- define one internal disagreement
- define information it lacks
- define what the crew can refuse
- define affected community and accountability route

A global logo is not a local actor.

## Crew And Role Materialization

For each PC:

- preserve player-authored identity and body
- map chosen capability into the selected system only after consent
- use an owned rules source for Role, Lifepath, cyberware, skill, and equipment mechanics
- distinguish rules result from personality and politics
- instantiate family, employer, gang, Nomad, corporate, or famous-character ties only when wanted
- record private and shared knowledge separately
- provide a nonviolent or nontechnical contribution path where selected
- preserve a way to refuse jobs and leave the crew

Do not assign one PC command authority merely because a game Role sounds senior.

## Mechanical Adaptation

Preserve across systems:

- selected era and historical consequences
- contested needs and infrastructure
- supply routes, scarcity, brokerage, and maintenance where era-appropriate
- bodily autonomy and cyberware dependency
- information custody and limited technical access
- asymmetric institutional power with concrete dependencies
- crew interdependence
- ordinary people's agency
- violence creating persistent consequences
- style, culture, and public narrative as social action

Replace per system:

- attributes, skills, Roles, Lifepaths, and advancement
- combat, armor, injury, healing, death, and initiative
- money, price categories, housing, lifestyle, Hustle, market, and reputation procedures
- cyberware slots, costs, Humanity, therapy, cyberpsychosis, and full-body conversion
- Netrunning, quickhacks, NET Actions, Architectures, devices, countermeasures, and range
- vehicles, chases, invention, medicine, social influence, investigation, and downtime

Do not copy proprietary rules text. Reject a conversion that makes era, bodily choice, infrastructure, evidence, or institutional dependency cosmetic.

## Net Adaptation

For 2045:

- distinguish Agent, CitiNet service, local NET Architecture, ordinary device, and physical control system
- require the selected rules for Netrunner capabilities
- retain physical access and human operators where sourced
- create specific logs, copies, and consequences
- do not import quickhacking from the 2070s

For the 2070s:

- cite the exact later-era rules source
- define quickhack/direct-connection boundaries
- define which bodies and devices are eligible
- respect player consent for bodily intrusion
- preserve countermeasures, trace, and physical endpoints
- do not claim the Mission Kit public preview is a complete Net source

For Blackwall, rogue AI, engrams, Soulkiller, or deep Old NET:

- stop and perform targeted research
- define observation separately from in-world theory
- define hard capabilities and limits
- avoid surprise omnipotence
- protect relevant spoilers

## Cyberware And Body Adaptation

Before an implant matters, decide:

- person and consent
- era and source-supported capability
- function and personal meaning
- payer and claimed ownership
- maintenance, repair, therapy, medicine, and replacement route
- network exposure and private data
- visible signs and who can interpret them
- hard limits and failure consequence
- portrayal boundary

Never detach, disable, repossess, hack, or reinterpret a PC's body as a twist without the player's explicit agreement and selected rules. A mechanical Humanity change cannot dictate interiority, morality, love, or real-world mental health.

## Violence And Security Adaptation

Every armed or coercive action needs:

- local actor and authority
- protected client, asset, or community
- information and confidence
- route and response time
- capability available now
- bystanders and workers affected
- evidence produced
- service or labor interrupted
- escalation threshold
- limit or disagreement
- aftermath owner

“Corporate hit team,” “gang attack,” “police response,” and “MAX-TAC arrives” are incomplete without these fields.

## Everyday-Life Adaptation

Every selected district must materialize:

- housing and displacement pressure
- food and clean-water access
- healthcare and emergency response
- ordinary work and shift rhythm
- transport and route dependency
- utilities and communication
- leisure, art, faith, sport, or social life
- care or mutual-aid relationships
- at least one institution that can refuse the crew
- a future locals pursue independently

A gig matters because it changes these conditions, not only because it pays.

## Cultural And Thematic Review Triggers

Require targeted review before locking content centered on:

- a real ethnic, national, linguistic, religious, Indigenous, migrant, or diasporic community
- a named Night City gang or culturally specific Nomad family/nation
- Free State, NUSA, border, military, intelligence, police, or incarceration stories
- racialized surveillance, identity documentation, citizenship, or displacement
- poverty, homelessness, food insecurity, debt, sex work, trafficking, and criminalized labor
- disability, prosthetics, chronic pain, cyberware, full-body conversion, disfigurement, and body ownership
- mental illness, addiction, trauma, therapy, cyberpsychosis, and institutional stigma
- surgery, medical abuse, organ/cyberware extraction, forced augmentation, and experimentation
- braindance intimacy, sexual content, romance, memory, coercion, and compromised consent
- war, terrorism, nuclear harm, contamination, ecological damage, and mass casualty
- overseas, oceanic, lunar, orbital, or Highrider communities

Review should increase specificity, agency, and consequence rather than remove all conflict.

## Update And Migration

When the package changes:

1. increment content version
2. list changed claims, sources, release statuses, and era assumptions
3. do not modify an active campaign automatically
4. compare only claims the campaign materialized
5. preserve continuity, divergence, source set, and spoiler bands
6. preserve campaign-created district history and outcomes
7. preserve player-authored identity, body, and private context
8. offer keep-current, adopt-update, or custom-reconcile choices
9. repeat safety review when a change affects cyberware, cyberpsychosis, Net intrusion, state violence, or body autonomy

## Validation Checklist

Before a future workflow declares a materialized Cyberpunk world ready:

- [ ] The user explicitly selected the official Cyberpunk-universe package.
- [ ] Era, continuity, source set, rules, and spoilers are accepted.
- [ ] Cross-era technology and gameplay abstractions remain isolated.
- [ ] One physical theater and at most one compatible connection layer are selected.
- [ ] Crew mandate, size, shared resource, refusal rules, and scale are accepted.
- [ ] Player identity, body, cyberware, history, and sensitive context were not prefilled.
- [ ] Net, Humanity/cyberpsychosis, healthcare, and body-autonomy contracts are explicit.
- [ ] Every active power has a local face, method, dependency, limit, and clock.
- [ ] At least one community/labor network has independent goals and refusal.
- [ ] Every supply problem has an origin, route, custody chain, and affected users.
- [ ] Every technical action has a system, access path, holder, evidence, and limit.
- [ ] Violence cannot silently replace labor, trust, care, or infrastructure.
- [ ] Famous characters are not required to resolve the premise.
- [ ] Player-facing and GM-only knowledge are separated.
- [ ] Only the selected frame and its hidden truth entered `campaign/`.
- [ ] Claim/source ids, confidence, era, media origin, mutability, spoilers, and visibility survived materialization.
- [ ] Normal workspace validation and audit gates pass.

## Do Not Copy During Materialization

- alternate eras and their technology
- alternate region cards or connection layers
- alternate campaign frames or hidden truths
- every corporation, gang, security provider, Nomad group, or state
- unselected rules and gameplay abstractions
- unresolved Blackwall, AI, Old NET, engram, or global lore
- hypothetical PC bodies, chrome, employers, families, debts, traumas, or secrets
- famous-character material without accepted proximity
- source descriptions that do not affect current decisions
- the package's full claim/source index when only a subset is active

## Future Infrastructure Boundary

A future ready-world system may define a machine-readable manifest and deterministic materializer. That work must be designed separately. It must not infer acceptance from this directory, auto-load the package, merge eras, expose GM truths during selection, prefill player bodies or histories, import gameplay abstractions as lore, or bypass campaign ownership, research, consent, finalization, and validation rules.
