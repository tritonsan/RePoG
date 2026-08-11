# World of Darkness: Vampire: The Masquerade Adaptation Notes

## Current Integration Status

- Runtime loader: none
- Package registry: none
- Automatic campaign creation: none
- Active campaign mutation: none
- Schema contract: none
- Reference package completeness: sufficient for a future Session 0 route

This package adds reference content, not infrastructure. Its presence does not imply acceptance, auto-loading, or readiness. Future implementation may read or transform it only after separate design establishes schemas, versioning, validation, edition selection, spoiler handling, knowledge separation, consent, and explicit user approval.

## Future Selection Flow

1. Present the example-world catalog.
2. Ask whether the user wants VTM, another researched world, or a custom world.
3. Confirm that every PC will be a VTM vampire.
4. Present the player-facing promise and continuity warning.
5. Select edition, continuity, allowed sourcebooks, era, and metaplot intensity.
6. Select original/real/published city mode and one opening district.
7. Select one vampire fantasy, coterie mandate, sect relationship, and scale.
8. Select a compatible frame or create a custom local feeding/Masquerade pressure.
9. Run PC-focused Session 0 for clan or non-clan condition, identity, sire history, Convictions, Touchstones, feeding practice, ties, and boundaries.
10. Select the opening posture for hunters and other supernatural beings; keep them non-player.
11. Run targeted research for every unresolved rule or lore detail required by the opening.
12. Prune the package to relevant truths, actors, places, facts, and sources.
13. Materialize accepted content into existing campaign-owned files.
14. Run normal worldbuild, finalization, validation, and readiness gates.

Do not bypass existing workflow rules because the package is researched.

## Authority During Materialization

1. Explicit user choices and safety boundaries
2. Player-authored vampire facts and approved private context
3. Accepted campaign divergences and homebrew
4. Selected edition, continuity, and sourcebooks
5. Selected package truths, theater, factions, and frame
6. Package defaults
7. Unselected package content

Accepted campaign history outranks later package updates. Unselected content has no authority.

## Package-To-Campaign Mapping

| Package source | Campaign owner | Materialization rule |
| --- | --- | --- |
| `manifest.md` | Session 0 summary and research metadata | copy package id/version and selected defaults only |
| `canon_policy.md` | `campaign/research_dossier.md` and Session 0 canon fields | record edition, continuity, era, metaplot, playable scope, divergences, risks, and unresolved details |
| `world_operating_model.md` | `campaign/world.md` and `campaign/world_truths.md` | copy only causal truths relevant to the opening; preserve claim ids |
| `regions.md` | `campaign/scale.md`, places, issues, and world | materialize one physical district and at most one connection layer |
| `factions.md` | `campaign/factions/`, faces, places, and issues | instantiate only active powers with local faces, methods, limits, knowledge, and clocks |
| `campaign_frames.md` | pitch, issues, opening, projections, faces, and places | copy one visible premise and its GM truth; never copy alternate frames |
| `session_zero_options.md` | Session 0 interview and PC integration | ask decisions; never copy unanswered prompts as facts |
| `knowledge_layers.md` | `campaign/knowledge_boundaries.md` | create actual holders and reveal gates for selected facts only |
| `source_provenance.md` | `campaign/research_dossier.md` | preserve source and claim ids, confidence, limitations, continuity, and verification date |

Specialized campaign files remain owners. No package summary overrides them after materialization.

## Template-Fixed Content

Preserve unless the user explicitly selects another edition or divergence:

- vampire-only player-character and coterie scope
- current V5 as primary continuity
- blood dependence, nocturnal limits, Hunger, and the Beast as pressure
- Humanity, Convictions, and Touchstones as relational moral play
- Masquerade, feeding, domain, boons, and evidence as causal systems
- Camarilla, Anarch, Sabbat, independent, clan, and thin-blood positions as internally diverse
- Sabbat antagonist-first posture under inspected V5 sources
- modern hunter and surveillance risk without omniscience
- Noddist myth separated from objective campaign truth
- W5, H5, legacy WoD, and Chronicles of Darkness boundaries
- other supernatural beings as non-player, source-gated, and perspective-limited
- player authorship over interiority and sensitive history
- campaign history outranking package updates

Record every change as a campaign continuity or playable-scope decision.

## Campaign-Instance Content

Select or create during Session 0:

- exact year or deliberate date-neutrality
- original, fictionalized, real, or published city
- city name, country, climate, night length, inequality, transit, industries, and public conflicts
- one opening district and connection network
- local Camarilla, Anarch, independent, or mixed settlement
- offices, titles, domain borders, feeding customs, and enforcement
- coterie mandate, patron, rivals, provisional authority, and shared resources
- havens, feeding venues, mortal institutions, and data paths
- local faces, objectives, methods, clocks, and limits
- current Hunger, feeding, boon, breach, and hunter pressures
- rumors, false interpretations, and hidden truth
- other-supernatural opening posture and any sourced non-player presence
- rules books, house rules, consequence severity, and metaplot intensity
- exact knowledge holders and reveal gates

These facts never write back into the reusable package during play.

## Player-Authored Content

Never prefill as accepted truth:

- PC name, identity, appearance, body, and presentation
- clan, Caitiff, or thin-blood choice
- sire, Embrace, generation, age, and lineage history
- beliefs about Caine, clan, sect, Humanity, or Gehenna
- Convictions, Touchstones, Ambition, Desire, and private interpretation
- feeding practice, targets, consent, shame, pleasure, and boundaries
- Hunger expression and desired loss-of-control portrayal
- haven contribution and personal resources
- family, friend, rival, mentor, dependent, romance, ghoul, or coterie tie
- Blood Bond, diablerie, cult, abuse, coercion, trauma, or betrayal history
- hidden allegiance, ancestry, prophecy, or supernatural secret
- sexuality, pregnancy, reproductive history, mental health, and private context
- willingness to use coercive Disciplines or accept PvP

The package may offer prompts and compatible fantasies only.

## Non-Player Supernatural Content

Never materialize as a PC path from this package:

- Garou or other shapeshifters
- mortal Hunters
- ghosts or wraiths
- mages or sorcerers
- changelings or fae
- demons, mummies, imbued, or other legacy beings
- Chronicles of Darkness characters
- ghouls as alternate player protagonists

For any selected presence, materialize only:

- exact source and edition
- observed identity or deliberately hidden identity
- local motive
- bounded capabilities
- hard limits
- relationship to one vampire-facing issue
- knowledge holders
- fair signs and reveal gate
- safety and cultural review

If a player wants one of these character types, stop and design a separate package or explicit crossover campaign contract.

## Default Opening Pruning

A `wod-vtm-frame-borrowed-night` materialization should begin with no more than:

- one original city
- one contested mixed-use district
- one shared or connected haven
- two feeding venues or routes
- one mortal community institution
- one transit, clinic, or late-work site
- one physical evidence site and one data custodian
- one local vampire authority
- one rival coterie or thin-blood/independent network
- four to six active faces total
- one disputed boon or grant
- one feeding contradiction
- one Masquerade clock
- one daylight deadline
- five to seven knowledge facts
- one hidden causal chain

Keep citywide court, national hunter programs, named elders, Sabbat, Garou, ghosts, mages, and Gehenna War distant unless the selected frame creates a direct, sourced connection.

## Borrowed Night Materialization Example

For `wod-vtm-frame-borrowed-night`:

- Pitch receives only the player-facing promise.
- Research dossier receives `wod5-v5-current`, `contemporary-date-unset`, package version, selected books, claims, and unresolved mechanics.
- World receives only relevant truths about predation, Hunger, Humanity, Masquerade, domain, evidence, and coterie dependence.
- Scale receives one district, haven, two venues, transit node, community institution, and data path.
- Issues receive overlapping grants, unsafe feeding, copied footage, scapegoat pressure, and three deadlines.
- Factions instantiate one patron, one rival or thin-blood network, and one mortal stakeholder.
- Faces receive the steward, worker, courier, rival, patron, and analyst only after naming and pruning.
- Knowledge boundaries receive `wod-vtm-frame-borrowed-night-secret-001` and its three-chain reveal gate.
- Opening begins with an immediate feeding or evidence conflict, not an encyclopedia of sects.
- PC integration receives only player-approved clan, feeding, Touchstone, and coterie ties.

## Playable-Scope Enforcement

A future materializer must reject or pause when:

- a selected PC type is not a VTM vampire
- a non-player supernatural card is mapped into character creation
- W5, H5, Mage, Wraith, Changeling, Demon, or Requiem mechanics are imported automatically
- a ghoul or mortal retainer is promoted to a parallel PC without a new contract
- the campaign premise changes from coterie play to equal-weight crossover play

The safe response is to preserve accepted VTM choices, stop materialization, and request a new scope decision.

## Source Preservation

Every materialized canon claim should retain:

- package id and version
- claim id
- source id or package-original designation
- confidence
- selected edition and continuity
- canon status
- mutability
- visibility and actual holders
- retrieval or verification date
- unresolved exact-mechanics flag when relevant

If prose is rewritten, preserve provenance on the proposition rather than treating new wording as a new source.

## Continuity Isolation

Store one selected continuity in campaign metadata. For every imported claim, record `continuity_origin` and whether it is:

- authoritative in the selected mode
- subject-source detail
- legacy opt-in
- adaptation-only color
- explicit crossover
- campaign-original
- unresolved
- rejected

Never use V20 to fill a V5 gap silently. Never use W5 or H5 mechanics as VTM mechanics. Never use Chronicles of Darkness or *Vampire: The Requiem* terminology as World of Darkness canon. Never use an in-world Noddist text as unmarked narrator truth.

## Clan And Sect Materialization

For each selected PC clan or non-clan condition:

- preserve player choice
- cite the exact owned rules source
- record only local stereotypes held by actual speakers
- define what the PC knows about lineage
- instantiate a sire or clan contact only if wanted
- avoid automatic sect allegiance
- keep Bane, Compulsion, Discipline, and creation mechanics in rules-owned references rather than copied prose

For each active sect:

- define local decision process
- define territory and practical capacity
- define one internal disagreement
- define one mortal dependency
- define what the coterie can refuse
- define response to breach, trespass, and thin-blood presence

## Mechanical Adaptation

Preserve across systems:

- blood dependence and feeding consequence
- Hunger or an equivalent intrusive pressure
- the Beast and risk of loss of control with agreed boundaries
- Humanity and player-authored moral/relational anchors
- night, daylight, haven, fire, torpor, and Final Death limits
- Masquerade evidence and mortal interpretation
- domain, boons, status, and sect enforcement
- coterie interdependence
- Disciplines as visible, risky power rather than free solutions
- modern hunter and data pressure
- myth and knowledge uncertainty

Replace per system:

- dice pools, Hunger dice, critical and failure procedures
- Attributes, Skills, Disciplines, Advantages, Flaws, and Loresheets
- Humanity, Stain, remorse, frenzy, and Compulsion procedures
- Blood Potency, generation, Rouse, healing, and damage numbers
- predator type, coterie, haven, domain, and boon mechanics
- combat, chase, social conflict, and project procedures
- Blood Sorcery, Thin-Blood Alchemy, and Oblivion mechanics

Do not copy proprietary rules text. Reject a conversion that makes predation, Hunger, or the Masquerade cosmetically irrelevant.

## Hunger And Agency Adaptation

Before play, decide:

- how Hunger is represented and who can see its state
- which results may complicate action
- how frenzy is telegraphed and resisted
- what the GM may describe without assigning PC feeling
- which safety boundaries remain absolute during loss of control
- how responsibility, repair, and aftermath work
- whether a player may redirect or veil a Hunger complication

No random result authorizes sexual violence, unagreed harm to a Touchstone, or hidden permanent character change.

## Feeding Adaptation

- Track feeding only as much as needed to create meaningful choices.
- Record access, consent, harm, trace, and territorial consequence.
- Do not make vulnerable populations an optimized resource category.
- A blood bag, animal, consensual donor, or ghoul arrangement still has a supply chain and ethical context.
- A successful hunt does not erase a victim's memory, injury, or agency unless selected rules and fiction establish how.
- Never assume a player's preferred portrayal from their clan or predator option.

## Hunter And Data Adaptation

Every institutional hunter action needs:

- named local cell or team
- sponsor and jurisdiction
- actual evidence
- confidence and error
- data or witness custody
- capability available now
- daylight route
- threshold for escalation
- human limit or disagreement
- consequence if exposed

Every digital operation needs a physical or human endpoint. “The algorithm found you” and “I delete the footage” are incomplete causal statements.

## Other-Supernatural Adaptation

- Start with observed phenomena, not franchise labels.
- Use one non-player presence at most in a beginner opening.
- Research the selected edition and title before assigning capability.
- Give the being a motive outside vampire politics.
- Define what it cannot do.
- Keep its cosmological account perspective-bound.
- Do not reward recognition with automatic character knowledge.
- Do not turn mystery into arbitrary immunity.
- Never let a crossover NPC displace the vampire coterie's decisions.

## Cultural And Thematic Review Triggers

Require targeted review before locking content centered on:

- Ashirra, Banu Haqim, Ministry, Ravnos, Hecata families, or culturally specific Kindred institutions
- Indigenous land, spirits, Garou territory, or environmental guardianship
- real faiths, sacred texts, ritual practice, blasphemy, or demonology
- mental illness, Malkavian portrayal, disability, scarring, disfigurement, or appearance
- racialized policing, surveillance, migration, trafficking, incarceration, or state violence
- addiction, recovery, intoxication, and sexualized feeding
- abusive relationships, blood bonds, ghouling, cults, or coercive control
- poverty, homelessness, housing displacement, sex work, and criminalized labor
- body horror, medical abuse, pregnancy, reproductive coercion, or children
- historical atrocity, colonialism, fascism, genocide, or clan stereotypes mapped to real peoples

Review should increase specificity, agency, and consequence rather than remove all conflict.

## Update And Migration

When the package changes:

1. increment content version
2. list changed claims, sources, and release dates
3. do not modify an active campaign automatically
4. compare only claims the campaign materialized
5. preserve edition, continuity, divergences, and player scope
6. preserve campaign-created city history
7. offer keep-current, adopt-update, or custom-reconcile choices
8. repeat safety review when a change alters feeding, coercion, or other-supernatural content
9. preserve player-authored history in every option

## Validation Checklist

Before a future workflow declares a materialized VTM world ready:

- [ ] The user explicitly selected this package.
- [ ] Every PC is a VTM vampire.
- [ ] Edition, continuity, sourcebooks, era, and metaplot intensity are accepted.
- [ ] Legacy, adaptation, W5/H5, and Chronicles of Darkness material remains isolated.
- [ ] City mode, opening district, frame, coterie mandate, sect posture, and scale are accepted.
- [ ] Clan and non-clan mechanics point to owned current rules.
- [ ] Player-authored fields were not prefilled.
- [ ] Feeding portrayal and safety boundaries are explicit.
- [ ] Every active power has a local face, method, limit, and clock.
- [ ] Mortal communities possess independent goals and daylight agency.
- [ ] Hunger and Humanity cannot dictate player interiority.
- [ ] Evidence records holders, custody, interpretation, and escalation.
- [ ] Hunter forces are capable but not omniscient.
- [ ] Other supernatural beings remain non-player, source-gated, and bounded.
- [ ] Noddist belief is distinct from objective truth.
- [ ] Player-facing and GM-only knowledge are separated.
- [ ] Famous characters are not required to resolve the premise.
- [ ] Only selected content entered `campaign/`.
- [ ] Claim/source ids, confidence, continuity, mutability, and visibility survived materialization.
- [ ] Normal workspace validation and audit gates pass.

## Do Not Copy During Materialization

- alternate region cards
- alternate campaign frames or hidden truths
- unselected clans as active local factions
- every sect or office
- unselected continuity and legacy modes
- every other World of Darkness creature
- speculative cosmology
- unresolved mechanics unrelated to the opening
- hypothetical PC sires, Touchstones, feeding histories, or secrets
- famous-character material without accepted proximity
- source descriptions that do not affect current decisions

## Future Infrastructure Boundary

A future ready-world system may define a machine-readable manifest and deterministic materializer. That work must be designed separately. It must not infer acceptance from this directory, auto-load the package, merge editions, expose GM truths during selection, create non-vampire PCs, or bypass campaign ownership, research, consent, finalization, and validation rules.
