# Dune Canon Policy

## Research Posture

This package supports play without pretending that Dune has one frictionless transmedia continuity. It distinguishes primary literary text, licensed adaptation, screen continuity, explicit alternate history, and package-original material. Broad durable claims are favored over fragile dates, officeholders, or exhaustive genealogies.

Research snapshot: 2026-07-23. Public product descriptions and official landing pages were inspected; full commercial book and RPG text was not independently re-read during this package pass. Fine-grained claims therefore carry narrower confidence than broad setting structures.

## Default Selection

- Literary continuity: `fh-core`
- Era: `late-corrino-pre-transfer`
- Play lens: `modiphius-compatible-system-neutral`
- Canon posture: `canon-adjacent-local`
- Exact year: unset
- Famous-character dependence: forbidden by default
- Future-event knowledge: protected unless the group opts into saga spoilers

`canon-adjacent-local` means original people and events may exist in unfilled local space provided they do not change, preempt, or secretly cause the published saga. Campaign history outranks later package updates after materialization.

## Source Hierarchy

| Rank | Source layer | Default use | Limit |
| --- | --- | --- | --- |
| 1 | Frank Herbert's six novels | Primary literary facts, themes, institutions, ecology, and era changes | Later books may reveal or transform earlier understandings; use only era-relevant knowledge |
| 2 | Era-relevant statements within the selected original novel | Tie-breaker for a campaign anchored to that era | Does not import later-character knowledge into earlier play |
| 3 | Licensed Modiphius *Dune: Adventures in the Imperium* material | Playable roles, House/agent/architect scales, Arrakis theaters, campaign affordances | Does not overrule the original novels or become accepted campaign state automatically |
| 4 | Brian Herbert and Kevin J. Anderson expanded novels | Opt-in history, institutions, and remote eras | Never used silently to fill a Frank Herbert gap |
| 5 | Legendary screen adaptations, including *Dune: Prophecy* | Opt-in visual, dramatic, or screen-continuity choices | Film/series changes do not rewrite literary continuity |
| 6 | *Dune: Awakening* | Its own explicit alternate timeline and survival play mode | Never mixed into the default timeline without a declared crossover divergence |
| 7 | RePoG package-original content | Local Houses, settlements, faces, frames, clocks, and hidden truths | Playable proposal only; not franchise canon |

Explicit user choices and accepted campaign history outrank this hierarchy for that campaign.

## Two Independent Selection Axes

Do not use a play aid as an undeclared lore authority. Session 0 selects both axes.

### Literary Or Screen Continuity

| Mode | Meaning | Default |
| --- | --- | --- |
| `fh-core` | Frank Herbert's six novels; only era-relevant facts are active | Yes |
| `expanded-novels` | `fh-core` plus selected Brian Herbert/Kevin J. Anderson works | No; opt-in titles must be named |
| `legendary-screen` | The Legendary film/television presentation governs visible continuity | No |
| `prophecy-era` | Remote pre-Paul screen/expanded setting inspired by *Sisterhood of Dune* | No; requires fresh era research |
| `awakening-alternate` | Paul was never born; official game-specific alternate history | No; isolated continuity |
| `campaign-divergent` | The group knowingly changes a selected premise | No; divergence point must be recorded |

### Play Lens

| Lens | Meaning |
| --- | --- |
| `system-neutral` | Use only fiction, pressures, decisions, and consequences |
| `modiphius-compatible` | Use House agents, architect play, and licensed campaign categories as design vocabulary |
| `screen-cinematic` | Favor screen-production visual language without importing unselected plot changes |
| `custom-rules` | Translate the fiction into another selected game system |

## Frank Herbert Core

The core sequence is:

1. *Dune* (1965)
2. *Dune Messiah* (1969)
3. *Children of Dune* (1976)
4. *God Emperor of Dune* (1981)
5. *Heretics of Dune* (1984)
6. *Chapterhouse: Dune* (1985)

The default package draws most directly on *Dune*. Later-original-novel facts are not ordinary knowledge in the default era. They may clarify source analysis, but narration must not reveal future institutions, transformations, identities, or outcomes unless the group chooses the relevant era or spoiler level.

Source claims: `claim-dune-original-six`, `claim-dune-core-scope`, `claim-dune-later-era-change`.

## Era Menu And Collision Risk

| Era id | Play promise | Canon-collision risk | Required action |
| --- | --- | --- | --- |
| `late-corrino-pre-transfer` | Great House rivalry, spice concessions, Harkonnen administration, local Arrakis pressure | Low at bounded local scale | Default; exact year remains unset |
| `atreides-transition` | Arrival, security, sabotage, divided loyalties | High | Name which published events are fixed and keep PCs from replacing canonical protagonists |
| `muaddib-ascension` | Regime collapse, spice interruption, Fremen power, House survival | High and spoiler-heavy | Accept first-novel outcomes and war/religious-violence intensity |
| `messiah-and-regency` | Imperial religion, conspiracy, governance, prescience | High | Targeted research in the relevant original novels |
| `god-emperor` | Long imperial transformation and constrained political life | High | Separate operating-model pass |
| `scattering-aftermath` | Later institutions, migration, memory, and transformed powers | Very high | Use *Heretics*/*Chapterhouse* as primary era sources |
| `prophecy-era` | Sisterhood formation ten millennia before Paul | Very high and cross-continuity | Select screen/expanded sources explicitly |
| `awakening-alternate` | Open-world survival and faction ascent on a Paul-less Arrakis | Isolated rather than colliding | Use only in its own branch |

Source claims: `claim-dune-fall-era`, `claim-dune-prophecy-era`, `claim-dune-awakening-alternate`, `claim-dune-later-era-change`.

## Default Fixed Canon Boundaries

Unless Session 0 selects a divergence:

- Arrakis is the unique source of melange in the opening era.
- Spice is strategically necessary to the Imperium and deeply tied to Guild navigation, longevity, awareness, and prescient capacity.
- Imperial society is feudal and unequal; the Emperor, Houses, Landsraad, Guild, and CHOAM constrain one another without creating democratic parity.
- Thinking machines are culturally and legally proscribed; trained humans and bounded devices fill many analytical roles.
- The Spacing Guild controls ordinary interstellar transport at strategic scale.
- Water is a material, social, and sacred constraint on Arrakis.
- Sandworms, desert ecology, and spice production form one coupled system that outsiders incompletely understand.
- Personal shields reshape combat; lasgun/shield interaction is catastrophically dangerous; atomics are constrained by inter-House convention.
- Bene Gesserit, Mentats, Suk doctors, Swordmasters, Fremen, and other trained groups are not interchangeable superpower lists.
- Prescience is consequential but not clean omniscience or a GM license to negate choice.
- Religion can be sincere, communal, adaptive, political, and manipulated at the same time.
- Published protagonists retain their published agency unless the group explicitly chooses a divergent retelling.

Source claims: `claim-dune-arrakis-spice`, `claim-dune-feudal-imperium`, `claim-dune-power-balance`, `claim-dune-limits-computers`, `claim-dune-human-schools`, `claim-dune-guild-travel`, `claim-dune-water`, `claim-dune-worm-spice-cycle`, `claim-dune-shields`, `claim-dune-atomics`, `claim-dune-prescience`, `claim-dune-religion`.

## Conflict Resolution

When sources disagree:

1. Check whether the apparent conflict belongs to different eras.
2. Check whether it belongs to different continuities.
3. Prefer the selected era's Frank Herbert novel in `fh-core` mode.
4. Treat adaptation-specific inventions as true only in their selected adaptation.
5. Prefer a bounded unknown over forced harmonization.
6. Ask the user when the choice changes the campaign promise.
7. Record the ruling, source ids, confidence, and mutability in campaign research metadata.

Silence is not contradiction. A package-original local fact may occupy genuine blank space, but it may not explain away a canonical event or claim secret authorship of the saga.

## Naming And Date Policy

- Do not invent an exact Imperial year merely to make the package look precise.
- Do not name a current officeholder unless the opening needs that person and the selected era supports the claim.
- Use an original Minor House, settlement, concession, and local officials by default.
- Label every invented proper noun as campaign-instance or package-original until accepted.
- Do not treat film appearance, costume, pronunciation, or architecture as literary fact unless `legendary-screen` is selected.

## Spoiler Policy

| Spoiler band | Default treatment |
| --- | --- |
| Broad premise of *Dune* | Player-safe after the group selects Dune |
| Atreides transfer and danger | Session 0 may disclose as era context, but not every betrayal or outcome |
| Identities, betrayals, deaths, ecological mechanism, prescient outcomes | Protected until needed or explicitly accepted |
| Later-novel regimes and transformations | Hidden in default-era play |
| Frame hidden truths | GM-only regardless of franchise familiarity |
| *Dune: Awakening*'s Paul-less premise | Disclosed when offering that continuity because it defines the option |

See [Knowledge Layers](knowledge_layers.md) for fact-level treatment.

## Expanded And Adaptation Rules

### Brian Herbert And Kevin J. Anderson

Use only after the group names the relevant work or era. Record imported claims separately. Do not use expanded history to settle an ambiguity in Frank Herbert's text without labeling the choice.

### Modiphius

The licensed RPG is strong evidence for playable campaign forms: original Houses, House agents, architect-level action, Arrakis campaigns, Fremen/smuggler/merchant options, Landsraad politics, CHOAM, Guild travel, and Imperial court play. These forms may shape package design. Specific RPG campaign plots, characters, mechanics, or alternate premises are not copied into this package.

### Legendary Screen Works

Use for selected visual and dramatic continuity. *Dune: Prophecy* is set ten thousand years before Paul and is inspired by *Sisterhood of Dune*; it does not supply default-era history silently.

### Dune: Awakening

The official game asks what happens if Paul Atreides was never born. That premise is not a minor variant; it is a branch point affecting major people, factions, and events. `awakening-alternate` must remain isolated in provenance, knowledge, and campaign state.

Source claims: `claim-dune-play-scales`, `claim-dune-prophecy-era`, `claim-dune-awakening-alternate`, `claim-dune-alternate-house-governor`.

## Thematic And Cultural Guardrails

- Do not present colonial extraction as a neutral optimization puzzle. Show who bears thirst, danger, displacement, and coercion.
- Do not reduce Fremen to a monolithic warrior culture, mystical guides, or resources for an outsider's destiny.
- Do not imply that Missionaria Protectiva explains away all Fremen belief or agency.
- Do not celebrate eugenic control, reproductive coercion, slavery, torture, or holy war without space for consequence and player boundaries.
- Do not equate nobility with virtue or low status with ignorance.
- Do not make every Bene Gesserit, Guild representative, smuggler, House retainer, or Imperial servant share one motive.
- Avoid direct one-to-one claims that fictional cultures represent a single real people or faith.
- Keep ecological knowledge situated: no outsider masters Arrakis after one briefing.
- Give local and oppressed people goals that do not begin and end with helping the player characters.

## Open Uncertainties

Before a strict canon lock, verify from the selected primary texts:

1. Exact date and officeholders if an opening requires them
2. The legal boundary of kanly, Great Convention, atomics, and House retaliation for the chosen incident
3. Fine detail of the sandtrout–worm–spice cycle if it becomes an investigative solution
4. Exact capabilities and limits of a named School graduate
5. Guild procedure, price, communication, and travel timing for a route-centered frame
6. CHOAM ownership and voting detail for an economic frame
7. Culture and internal politics of a specific sietch before Fremen-centered play
8. Any later-era institution before importing it into an early era
9. Any screen-only visual or plot element before calling it literary canon

Unknowns remain questions; they are not invitations to rely on fan-wiki synthesis as authority.

## Campaign Divergence Record

Every accepted divergence should preserve:

- divergence id
- selected continuity and era
- exact branch point
- source claim being changed
- user decision and date
- immediate consequences
- later claims made uncertain
- whether the change is public, restricted, or GM-only

A divergence changes only the materialized campaign. It never rewrites this reusable package.
