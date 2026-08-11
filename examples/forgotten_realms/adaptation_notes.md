# Forgotten Realms Adaptation Notes

## Current Integration Status

- Runtime loader: none
- Package registry: none
- Automatic campaign creation: none
- Active campaign mutation: none
- Schema contract: none
- Reference package completeness: sufficient for a future Session 0 route

This package deliberately introduces content, not infrastructure. Future implementation may read or transform it only after a separate design establishes schemas, validation, versioning, and user approval behavior.

## Future Selection Flow

1. Present the example-world catalog.
2. Ask whether the user wants a researched example world or a new/custom world.
3. If Forgotten Realms is selected, present its player-facing promise and canon posture.
4. Select one region or request another region for targeted research.
5. Select a compatible campaign frame or create a custom local pressure.
6. Select canon mode, timeline precision, tone, and opening scale.
7. Run PC-focused Session 0 for identity, ties, beliefs, party glue, and boundaries.
8. Prune the package to facts and actors relevant to the opening scale.
9. Materialize accepted content into existing campaign-owned files.
10. Run the normal research, finalization, validation, and readiness gates.

Do not skip existing worldbuild workflow rules merely because the package is researched.

## Authority Order During Materialization

1. Explicit user choices and boundaries
2. User-supplied homebrew accepted for this campaign
3. Selected package canon policy
4. Selected package region and frame proposals
5. Package defaults
6. Unselected package content

Unselected content has no authority over the campaign.

## Package-To-Campaign Mapping

| Package source | Campaign owner | Materialization rule |
| --- | --- | --- |
| `manifest.md` | Session 0 summary and research metadata | Copy package id/version and selected defaults only |
| `canon_policy.md` | `campaign/research_dossier.md` and canon-policy fields in Session 0 | Record accepted scope, hierarchy, timeline, risks, and unresolved items |
| `world_operating_model.md` | `campaign/world.md` and `campaign/world_truths.md` | Copy only truths relevant to selected locale; preserve source ids |
| `regions.md` | `campaign/scale.md`, `campaign/world.md`, places, and issues | Materialize one opening region and a bounded local network |
| `factions.md` | `campaign/factions/`, issues, faces, and places | Instantiate only active factions with local face, place, objective, limit, and clock |
| `campaign_frames.md` | pitch, issues, opening, projections, faces, and places | Copy visible premise and selected GM truth; do not copy alternate frames |
| `session_zero_options.md` | Session 0 interview and PC integration | Ask decisions; never copy unanswered prompts as truth |
| `knowledge_layers.md` | `campaign/knowledge_boundaries.md` | Create actual holders and reveal conditions for selected facts only |
| `source_provenance.md` | `campaign/research_dossier.md` | Preserve links, claim ids, confidence, contradictions, and open research |

Specialized campaign files remain owners. Do not create a package summary that overrides them after materialization.

## Template-Fixed Content

Preserve unless the user explicitly selects a divergence:

- Primary scope is Faerûn
- Current tabletop source hierarchy
- Regional rather than universal law and culture
- Uneven magic access
- Real gods with fallible mortal institutions
- Independent faction action
- Meaningful travel and information limits
- Non-monolithic peoples and factions
- Campaign history outranks later package changes

If changed, record the change as a campaign continuity decision.

## Campaign-Instance Content

Generate or select during Session 0:

- Exact date
- Local settlement or district
- Local routes and connections
- Active issue
- Two or three active factions or powers
- Current objectives and clocks
- Local faces and places
- Rumors and false beliefs
- Opening scene
- Exact frame truth
- Published-adventure outcomes relevant to the locale
- Magic, travel, survival, and divine-visibility settings

These are not written back into the reusable package during play.

## Player-Authored Content

Never prefill as accepted truth:

- PC name, identity, appearance, class, species, or background
- Home and belonging
- Family, friend, rival, mentor, or dependent
- Faith and interpretation
- Debt, oath, secret, shame, or ambition
- Faction attitude or membership
- Feelings about the opening problem
- Personal knowledge of a frame secret
- Romance or interpersonal arc
- Boundaries and private context

The package may offer prompts and compatible fantasies only.

## Opening-Scale Pruning

A default Dalelands materialization should begin with no more than:

- One home settlement
- One neighboring settlement or destination
- One contested route
- One forest-edge or ruin site
- One community institution
- Two active factions and one competing power or affected group
- Three to five faces
- Four to seven connected places
- One visible issue
- One hidden causal chain
- Three to five knowledge facts

Everything else remains package reference until expansion is earned.

For a city frame, replace geographic breadth with one neighborhood, one gate or route, one authority, one hidden market, and one elite pressure point.

## Frame Materialization Example

For `fr-frame-silent-bell`:

- Pitch receives only the player-facing promise.
- World receives relevant truths about regional authority, travel, history, and magic.
- Scale receives the chosen dale, settlements, road, and forest edge.
- Issues receive the trade failure and its observable consequences.
- Factions instantiate local versions of selected actors; no generic faction acts without a face.
- Places receive the road, settlement hubs, ward sites, and one pressure location.
- Knowledge boundaries receive `fr-frame-dale-secret-001` and its foreshadowing limits.
- Opening receives an immediate situation, not the hidden answer.
- PC integration receives only player-approved ties to the road, missing people, communities, or factions.

## Source Preservation

Every materialized canon claim should retain:

- Package id and version
- Claim id
- Source id or package-original designation
- Confidence
- Canon status
- Selected continuity mode
- Visibility
- Last verification date when relevant

If prose is rewritten for the opening scale, preserve provenance on the underlying claim rather than treating new wording as a new source.

## Update And Migration

When the package changes:

- Increment its content version.
- Record changed claims and why.
- Do not modify an active campaign automatically.
- Compare only claims that the campaign materialized.
- Offer keep-current, adopt-update, or custom-reconcile choices.
- Preserve player-caused history in every option.

A source correction may update future package use while an existing campaign intentionally retains the earlier version.

## Mechanical Adaptation

The default fiction assumes 5.5e vocabulary, but the package does not depend on exact numbers.

Preserve across systems:

- What magic can mean socially
- Who controls access
- Why travel matters
- What factions want
- Which consequences advance
- What a region promises

Replace per system:

- Classes and subclasses
- Feats and backgrounds
- Spell names and levels when necessary
- Creature statistics
- Difficulty and encounter construction
- Rest, travel, injury, renown, and resource mechanics

Do not silently preserve a mechanical capability if the new system would make its fictional consequences impossible.

## Cultural Review Triggers

Require targeted review before locking content that centers:

- Calimshan beyond the broad 2025 region presentation
- Chult or a colonial-expedition structure
- Reghed communities
- Ffolk and Norlander relations
- Drow or other Underdark societies
- Species-based persecution
- Real-world-coded language, dress, religion, or social hierarchy
- Slavery, conquest, displacement, or cultural erasure

The review should increase local agency and specificity, not remove all conflict.

## Validation Checklist

Before a future workflow declares the materialized world ready:

- [ ] The user selected Forgotten Realms explicitly.
- [ ] Canon mode is accepted.
- [ ] The timeline is locked or deliberately date-neutral.
- [ ] The opening region and scale are accepted.
- [ ] Required local research has no unresolved error-level gap.
- [ ] Package defaults are distinguishable from user choices.
- [ ] PC-authored fields were not prefilled without approval.
- [ ] Boundaries are accepted.
- [ ] Active factions have local faces, methods, limits, and clocks.
- [ ] The opening issue has a cause, beneficiaries, costs, and inaction consequences.
- [ ] Player-facing and GM-only knowledge are separated.
- [ ] Famous characters are not required to resolve the premise.
- [ ] Only selected content entered `campaign/`.
- [ ] Source ids and confidence survived materialization.
- [ ] Normal workspace validation and audit gates pass.

## Do Not Copy During Materialization

- Alternate region cards
- Alternate campaign frames
- Research commentary that does not affect the selected scale
- Unselected continuity options
- Every faction in this package
- Every historical era
- GM secrets from unselected frames
- Hypothetical PC ties
- Generic setting lore that the opening cannot reveal or use

## Future Infrastructure Boundary

A future example-world system may define a machine-readable manifest and deterministic materializer. That work must be designed separately. It must not infer acceptance from the existence of this directory, and it must not bypass the worldbuild workflow, research gate, campaign ownership rules, or final validation.