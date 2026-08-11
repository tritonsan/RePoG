# Dune Adaptation Notes

## Current Integration Status

- Runtime loader: none
- Package registry: none
- Automatic campaign creation: none
- Active campaign mutation: none
- Schema contract: none
- Reference package completeness: sufficient for a future Session 0 route

This package introduces reference content, not infrastructure. Its existence does not imply acceptance, auto-loading, or readiness. Future implementation may read or transform it only after a separate design establishes schemas, versioning, validation, continuity selection, spoiler handling, and explicit user approval.

## Future Selection Flow

1. Present the example-world catalog.
2. Ask whether the user wants Dune, another researched world, or a custom world.
3. If Dune is selected, present the player-facing promise and continuity warning.
4. Select literary/screen continuity and play lens separately.
5. Select era and spoiler ceiling.
6. Select one campaign fantasy, party mandate, theater, and opening scale.
7. Select a compatible frame or create a custom local pressure.
8. Run PC-focused Session 0 for identity, training, loyalties, beliefs, ties, spice relationship, and boundaries.
9. Run targeted research for every unresolved detail required by the selected opening.
10. Prune the package to relevant truths, actors, places, and knowledge facts.
11. Materialize accepted content into existing campaign-owned files.
12. Run normal worldbuild, finalization, validation, and readiness gates.

Do not skip existing workflow rules because the package is researched.

## Authority During Materialization

1. Explicit user choices and boundaries
2. Player-authored character facts and approved private context
3. Accepted campaign divergences and homebrew
4. Selected continuity and era policy
5. Selected package truths, region, factions, and frame
6. Package defaults
7. Unselected package content

Accepted campaign history outranks later package updates. Unselected content has no authority.

## Package-To-Campaign Mapping

| Package source | Campaign owner | Materialization rule |
| --- | --- | --- |
| `manifest.md` | Session 0 summary and research metadata | copy package id/version and selected defaults only |
| `canon_policy.md` | `campaign/research_dossier.md` and Session 0 canon fields | record continuity, play lens, era, spoiler ceiling, divergences, risks, and unresolved items |
| `world_operating_model.md` | `campaign/world.md` and `campaign/world_truths.md` | copy only truths that causally affect the opening; preserve claim ids |
| `regions.md` | `campaign/scale.md`, world, places, and issues | materialize one theater and a bounded local connection network |
| `factions.md` | `campaign/factions/`, faces, places, and issues | instantiate only active powers with local face, objective, method, limit, and clock |
| `campaign_frames.md` | pitch, issues, opening, projections, faces, places | copy one visible premise and its GM truth; never copy alternate frames |
| `session_zero_options.md` | Session 0 interview and PC integration | ask decisions; never copy unanswered prompts as truth |
| `knowledge_layers.md` | `campaign/knowledge_boundaries.md` | create actual holders and reveal gates for selected facts only |
| `source_provenance.md` | `campaign/research_dossier.md` | preserve sources, claim ids, confidence, limitations, and last verification |

Specialized campaign files remain owners. No package summary overrides them after materialization.

## Template-Fixed Content

Preserve unless the user explicitly selects another continuity or divergence:

- source and continuity separation
- Arrakis/spice systemic dependence in the default era
- feudal, unequal Imperial power
- Guild transport leverage
- post-thinking-machine human specialization
- water and ecology as causal systems
- asymmetric violence and escalation constraints
- limited, situated information
- prescience as possibility and pressure rather than omniscience
- religious meaning coexisting with institutional manipulation
- non-monolithic factions and communities
- published protagonists retaining their agency
- campaign history outranking package updates

Record every change as a campaign continuity decision.

## Campaign-Instance Content

Select or create during Session 0:

- exact era position or deliberate date-neutrality
- original House name, scale, heraldry, homeworld, virtue claim, contradiction, and dependencies
- settlement, district, concession, route, and facility names
- governing office and local legal authority
- two or three active powers
- local faces, places, objectives, clocks, and limits
- current spice, water, labor, transport, and weather pressures
- rumors and false interpretations
- opening scene and frame truth
- famous-character proximity
- rules implementation and consequence severity
- intensity of survival, religion, prescience, violence, and body horror
- exact knowledge holders and reveal gates

These facts never write back into the reusable package during play.

## Player-Authored Content

Never prefill as accepted truth:

- PC name, identity, appearance, body, and home
- House, sietch, School, faction, or community belonging
- feelings about the patron, Imperium, Fremen, faith, spice, or prophecy
- family, friend, rival, mentor, dependent, romance, or party tie
- loyalty, oath, debt, ambition, shame, grief, secret, or betrayal
- hidden ancestry, conditioning, breeding-program place, pregnancy, or reproductive history
- private vision, prescient interpretation, spice exposure, addiction, or withdrawal
- willingness to use Voice-like influence, poison, assassination, or coercion
- trauma detail, boundaries, and private context

The package may offer prompts and compatible fantasies only.

## Default Opening Pruning

A `dune-frame-dry-ledger` materialization should begin with no more than:

- one original Minor House
- one bounded concession settlement
- one harvester zone
- one contested route
- one rock refuge or weather site
- one water institution
- two active factions and one affected community organization
- four to six faces
- five to eight connected places
- one visible ledger contradiction
- one hidden causal chain
- four to six knowledge facts
- one weather or audit deadline

Keep Arrakeen, Kaitain, the Guild, CHOAM leadership, canonical Great Houses, and sietch interiors distant unless the opening creates a direct connection.

## Frame Materialization Example

For `dune-frame-dry-ledger`:

- Pitch receives only the player-facing promise.
- Research dossier receives `fh-core`, `late-corrino-pre-transfer`, package version, selected claims, and unresolved legal/ecological details.
- World receives only relevant truths about spice dependence, water, unequal power, information, and ecology.
- Scale receives the settlement, concession, harvester zone, route, and environmental deadline.
- Issues receive the quota contradiction, ration harm, audit clock, and inaction consequences.
- Factions instantiate the patron field office, governing-House office, and affected community organization.
- Faces receive the steward, factor, overseer, worker representative, and selected broker only after naming.
- Places receive actual custody and access relationships, not a scenic list.
- Knowledge boundaries receive `dune-frame-dry-ledger-secret-001` and its two-chain reveal gate.
- Opening begins with an immediate deployment or inspection problem, not an explanation of the ledgers.
- PC integration receives only player-approved duties, ties, and beliefs.

## Source Preservation

Every materialized canon claim should retain:

- package id and version
- claim id
- source id or package-original designation
- confidence
- selected continuity and era
- canon status
- mutability
- visibility and holders
- last verification date when relevant

If opening-scale prose is rewritten, preserve provenance on the underlying proposition rather than treating new wording as a new source.

## Continuity Isolation

Store one selected continuity in campaign metadata. For imported claims, record `continuity_origin` and whether they are:

- authoritative in the selected mode
- adaptation-only color
- explicit crossover
- unresolved
- rejected

Never use *Dune: Awakening* to fill an `fh-core` gap. Never use *Dune: Prophecy* as default-era Bene Gesserit history without selecting its source layer. Never treat Modiphius alternate campaigns as events that happened in the novels.

## Famous-Character Boundary

By default:

- named saga characters do not hire the PCs directly
- the opening does not require their rescue, defeat, approval, or secret parentage
- PCs do not unknowingly cause a canonical turning point
- rumors may mention a Great House without placing its principals on stage
- a canonical appearance requires a purpose, source check, knowledge boundary, and user acceptance

If the group chooses canon-adjacent proximity, define which events are fixed and where players retain meaningful agency.

## Mechanical Adaptation

Preserve across systems:

- water and spice as contextual leverage
- social position and jurisdiction
- transport dependence
- secret custody and evidence
- trained-human scarcity
- environmental deadlines
- House assets and institutional limits
- consequences that propagate across people, resources, reputation, and ecology

Replace per system:

- drives, skills, talents, assets, and determination
- stress, conflict, and extended-task procedures
- injury, poison, and recovery mechanics
- resource tracks and equipment statistics
- agent/architect action economy
- House creation and advancement numbers
- prescience procedure if the selected rules already provide one

Do not copy proprietary rules text. Do not preserve a mechanic if it contradicts accepted fiction.

## Prescience Adaptation

Before play, decide:

- rarity and eligibility
- who authors vision content
- privacy and holder state
- ambiguity markers
- cost of clarity
- how decisions alter branches
- what the GM may not dictate

A vision never assigns PC emotion or removes the ability to choose. If a system's prophecy mechanic would do so, revise the mechanic or reject that implementation.

## Ecology And Resource Adaptation

- Track water only if scarcity produces meaningful decisions, not routine bookkeeping.
- Never turn a person or body into an unexamined resource token.
- Spice production always records labor, ecological, and political consequences.
- Fremen knowledge is held by specific people and communities, not unlocked as a technology tree.
- A technical success does not erase worm, storm, route, or social context.
- Ecological transformation requires era-appropriate research and consequence modeling.

## Faction Instantiation Checklist

Every active power needs:

- local face
- local place
- current objective
- method it can execute now
- capability and resource
- hard limit
- internal disagreement or uncertainty
- information it lacks
- next action if ignored
- people who bear the cost
- source claims and continuity origin

“House Harkonnen acts” is not enough. Identify the local office and why it acts.

## Cultural And Thematic Review Triggers

Require targeted review before locking content centered on:

- a player-character Fremen sietch or ritual
- Arabic, Islamic, Amazigh, Bedouin, Persian, or other real-world comparisons
- outsider leadership of an oppressed or Indigenous-coded community
- colonialism, ecological exploitation, and displacement
- slavery, forced labor, torture, or dehumanization
- eugenics, breeding programs, reproductive coercion, or arranged marriage
- holy war, genocide, fanaticism, or religious manipulation
- Voice-like coercion and loss of agency
- Tleilaxu body/identity horror
- disability, fatness, appearance, or bodily difference used as moral shorthand

Review should increase specificity, agency, and consequence rather than erase conflict.

## Update And Migration

When the package changes:

1. increment content version
2. list changed claims and sources
3. do not modify an active campaign automatically
4. compare only claims the campaign materialized
5. preserve selected continuity and divergence points
6. offer keep-current, adopt-update, or custom-reconcile choices
7. preserve player-caused history in every option

A source correction may update future use while an existing campaign deliberately retains its earlier branch.

## Validation Checklist

Before a future workflow declares a materialized Dune world ready:

- [ ] The user explicitly selected Dune.
- [ ] Continuity and play lens are separately accepted.
- [ ] Era and spoiler ceiling are locked.
- [ ] Alternate continuities remain isolated.
- [ ] Opening theater, frame, party mandate, and scale are accepted.
- [ ] The original House or community was created collaboratively.
- [ ] Player-authored fields were not prefilled.
- [ ] Boundaries cover selected thematic intensity.
- [ ] Required targeted research has no unresolved error-level gap.
- [ ] Every active power has a local face, method, limit, and clock.
- [ ] The issue records who benefits, who pays, and what inaction changes.
- [ ] Labor and ecology are visible where extraction is central.
- [ ] Prescience cannot dictate player action.
- [ ] Player-facing and GM-only knowledge are separated.
- [ ] Famous characters are not required to resolve the premise.
- [ ] Only selected content entered `campaign/`.
- [ ] Claim/source ids, confidence, continuity, and visibility survived materialization.
- [ ] Normal workspace validation and audit gates pass.

## Do Not Copy During Materialization

- alternate region cards
- alternate campaign frames or secrets
- unselected continuity modes
- every Imperial faction
- every historical era
- unresolved research commentary unrelated to the opening
- all setting lore “for completeness”
- hypothetical PC ties, loyalties, beliefs, or visions
- famous-character material without accepted proximity
- source descriptions that do not affect current decisions

## Future Infrastructure Boundary

A future ready-world system may define a machine-readable manifest and deterministic materializer. That work must be designed separately. It must not infer acceptance from this directory, merge continuities automatically, expose GM facts during selection, or bypass campaign ownership, research, consent, finalization, and validation rules.
