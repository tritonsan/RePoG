# World of Darkness: Vampire: The Masquerade Knowledge Layers

## Purpose

VTM depends on asymmetric knowledge. Mortals normalize or investigate fragments, coteries hide feeding, sects curate history, hunters classify incomplete evidence, blood sorcerers protect methods, and other supernatural beings do not explain themselves through vampire categories. This file defines defaults for future materialization; it does not make any frame solution player-known.

## Visibility Taxonomy

| Layer | Id | Who may know | Default use |
| --- | --- | --- | --- |
| Mortal public | `M0` | ordinary public and public institutions | mundane events, rumors, unexplained harm, no accepted vampire proof |
| Kindred common | `K0` | local vampires with basic induction | blood need, night limits, Masquerade, broad clan/sect names |
| Local common | `K1` | residents of one district or local Kindred scene | routines, visible authority, feeding customs, active rumors |
| Role-restricted | `K2` | specific office, coterie role, clan teacher, institution, or hunter cell | boon ledgers, domain maps, procedures, routes, case files |
| Occult contested | `K3` | named scholars, practitioners, believers, or witnesses | Noddist texts, blood craft, Oblivion claims, elder theories |
| Other-supernatural truth | `K4` | the non-player being and specifically justified holders | actual identity, motives, capabilities, cosmology fragments |
| Frame truth | `K5` | GM and discovered holders | package-original causal chain, hidden actors, and clocks |
| Continuity spoiler | `K6` | players who accepted the relevant source knowledge | named-city metaplot, published outcomes, elder identities |
| Player-private | `KP` | originating player and approved recipients | PC interiority, private history, boundaries, proposed secrets |

A fact moves layers only through evidence, a recorded reveal, player consent, or an accepted continuity change.

## General Rules

1. Separate player franchise knowledge from character knowledge without punishing either.
2. Record holders as people, coteries, offices, archives, devices, or cells—not “the Camarilla knows.”
3. Distinguish observation, inference, doctrine, rumor, and objective campaign truth.
4. Give every secret a reason, cost, observable edge, and reveal path.
5. Supernatural coercion cannot manufacture reliable context the target never possessed.
6. Deleting or altering one memory does not erase bodies, devices, routines, backups, or other witnesses.
7. Clan stereotype and sect propaganda always have a speaker.
8. Noddist text remains belief or contested evidence unless the campaign makes a specific truth decision.
9. Other-supernatural truth stays at `K4` even when players recognize a franchise term.
10. A PC's feelings, Convictions, Touchstone relationship, feeding history, and private secret remain player-authored.

## Fact Cards

### `wod-vtm-fact-masquerade-001` — Vampire Existence Is Hidden

- Default layer: broad rule at `K0`; evidence and enforcement at `K1`–`K2`; mortals hold fragments at `M0`
- Safe wording: Kindred survival depends on preventing convincing public proof of vampires, and local authorities may punish dangerous exposure.
- Do not say at `M0`: that every unexplained event is ignored or every institution has been controlled.
- Reveal requirement for a breach: identify evidence, holder, interpretation, reach, and response capacity.
- Source claims: `claim-wod-vtm-kindred-masquerade`, `claim-wod-vtm-digital-risk`.

### `wod-vtm-fact-hunger-001` — Hunger Changes Risk

- Default layer: `K0` broad; exact state belongs to each PC and selected rules
- Safe wording: Hunger can intrude on action and bring the Beast closer to harmful expression.
- Forbidden wording: “your character wants this” beyond rules and player agreement, or Hunger as permission to cross a safety boundary.
- Reveal requirement for another vampire's state: visible signs, relationship, or volunteered information.
- Source claims: `claim-wod-vtm-hunger-humanity`, `claim-wod-vtm-vampire-condition`.

### `wod-vtm-fact-humanity-001` — Humanity Has Chosen Anchors

- Default layer: system premise at `K0`; a PC's Convictions and Touchstones at `KP` until shared
- Safe wording: vampires can orient themselves through chosen principles and relationships while predation threatens distance from human life.
- Forbidden wording: a narrator-assigned real-world morality, compulsory love, or secret change to a PC's Conviction.
- Reveal requirement: originating player choice and selected V5 procedure.
- Source claims: `claim-wod-vtm-hunger-humanity`, `claim-wod-vtm-touchstones-convictions`.

### `wod-vtm-fact-night-001` — Daylight And Fire Are Grave Threats

- Default layer: `K0`
- Safe wording: vampires operate primarily at night and require secure daytime refuge; sunlight and fire can be catastrophic.
- Restricted detail: exact damage, fear, awakening, and recovery procedures.
- Reveal requirement for mechanics: owned current core rules and current errata.
- Source claims: `claim-wod-vtm-vampire-condition`.

### `wod-vtm-fact-blood-001` — Vitae Can Bind And Sustain

- Default layer: broad danger at `K0`; exact bonds, ghouls, and histories at `K2` or `KP`
- Safe wording: vampire blood may sustain, empower, and create dangerous dependence or supernatural attachment.
- Forbidden wording: every loyalty is a Blood Bond, a bound person has no agency, or a PC was secretly bound without consent.
- Reveal requirement: actual exposure, rules-supported signs, or a holder with evidence.
- Source claims: `claim-wod-vtm-blood-bonds-ghouls`, `claim-wod-vtm-vampire-condition`.

### `wod-vtm-fact-clans-001` — Clan Is Lineage, Not Personality

- Default layer: names and stereotypes at `K0`; local lineages and mechanics at `K1`–`K2`
- Safe wording: current V5 supports fourteen clan presentations across core and Players Guide, plus Caitiff and thin-blood options.
- Forbidden wording: clan determines ethnicity, morality, politics, profession, mental health, sexuality, or sect.
- Reveal requirement for a character's lineage secret: player choice or sourced evidence with consent.
- Source claims: `claim-wod-vtm-clans-current`.

### `wod-vtm-fact-sects-001` — Sect Labels Hide Local Difference

- Default layer: broad Camarilla, Anarch, and Sabbat identities at `K0`; local structure at `K1`–`K2`
- Safe wording: Camarilla seeks hierarchical security and Masquerade control, Anarchs resist elder authority through varied local structures, and V5 presents Sabbat primarily as antagonists.
- Forbidden wording: every member shares one morality, objective, office system, or clan composition.
- Reveal requirement for policy: a local decision-maker, precedent, and enforcement capacity.
- Source claims: `claim-wod-vtm-camarilla`, `claim-wod-vtm-anarch`, `claim-wod-vtm-sabbat-antagonists`.

### `wod-vtm-fact-thin-blood-001` — Thin-Bloods Are Vampires, Not A Clan

- Default layer: existence at `K0`; capabilities, network, and status at `K1`–`K2`
- Safe wording: V5 supports thin-blooded vampire play and Thin-Blood Alchemy, while local Kindred may marginalize, exploit, fear, or ally with them.
- Forbidden wording: uniform weakness, guaranteed prophecy, cure, daytime immunity, or social treatment without rules and local definition.
- Reveal requirement for capability: selected owned V5 material and the actual character.
- Source claims: `claim-wod-vtm-thin-bloods`, `claim-wod-vtm-blood-craft`.

### `wod-vtm-fact-hunters-001` — Hunters Have Partial Pictures

- Default layer: danger at `K0`; cells, data, and confidence at `K2`
- Safe wording: individual hunters and concealed institutions may investigate, classify, and attack vampires using daylight access, technology, community knowledge, and incomplete lore.
- Forbidden wording: a single omniscient Second Inquisition database or automatic moral heroism.
- Reveal requirement: identify cell, sponsor, evidence, confidence, jurisdiction, and capability.
- Source claims: `claim-wod-vtm-second-inquisition`, `claim-wod-h5-separate`, `claim-wod-vtm-digital-risk`.

### `wod-vtm-fact-beckoning-001` — Elder Absence Has Multiple Accounts

- Default layer: broad rumor at `K0`–`K1`; specific cause at `K3`, `K5`, or `K6`
- Safe wording: current V5 sources describe elder disappearance or Beckoning-related pressure and a Gehenna War, but local absences require evidence.
- Forbidden wording: every elder left, one global explanation is proven, or the package knows Gehenna's objective truth.
- Reveal requirement: selected Gehenna War material or campaign-original evidence.
- Source claims: `claim-wod-vtm-beckoning-gehenna`, `claim-wod-vtm-camarilla`.

### `wod-vtm-fact-nod-001` — The Book Of Nod Is An In-World Mythic Source

- Default layer: existence and broad reputation at `K0`; interpretations at `K3`
- Safe wording: Noddist texts tell stories of Caine, early vampires, hidden teachings, and Gehenna, and believers treat them as sacred or politically important.
- Forbidden wording: the text proves one objective origin, chronology, Antediluvian identity, or prophecy.
- Reveal requirement for campaign truth: explicit Storyteller decision, evidence, visibility, and group acceptance.
- Source claims: `claim-wod-vtm-noddist-myth`.

### `wod-vtm-fact-garou-001` — Garou Are Not Vampire Taxonomy

- Default layer: vampire rumor at `K1` or `K3`; actual W5 identity and motive at `K4`
- Safe vampire wording: dangerous shapeshifters or territorial beings may oppose predation or environmental harm.
- Safe GM truth after research: W5 frames Garou through Rage, spirit, and environmental-spiritual horror.
- Forbidden wording: werewolves are one vampire clan's natural enemy, all follow one Nation order, or W5 makes them PCs here.
- Reveal requirement: targeted W5 research and an instantiated individual or pack.
- Source claims: `claim-wod-w5-separate`.

### `wod-vtm-fact-ghosts-001` — The Dead Are A Contested Presence

- Default layer: haunting claims at `M0`–`K1`; actual identity and cosmology at `K3`–`K4`
- Safe wording: some VTM practices and stories allow contact with death or apparent ghosts, but vampires do not possess a complete afterlife map.
- Forbidden wording: every apparition follows a full Wraith cosmology or can be commanded by a Hecata vampire.
- Reveal requirement: selected V5 occult source and, if expanded, targeted Wraith research.
- Source claims: `claim-wod-vtm-blood-craft`, `claim-wod-legacy-lines`.

### `wod-vtm-fact-mages-001` — Occult Humans May Exceed Kindred Models

- Default layer: rumor at `K1`–`K3`; actual identity and capability at `K4`
- Safe wording: vampires tell stories of sorcerers or humans whose occult capabilities do not fit blood craft.
- Forbidden wording: a universal sphere list, consensus cosmology, effortless sunlight cure, or Mage PC.
- Reveal requirement: selected legacy source, local observation, and a bounded capability list.
- Source claims: `claim-wod-legacy-lines`.

### `wod-vtm-fact-other-supernatural-001` — Unknown Does Not Mean Unlimited

- Default layer: rumor at `M0`–`K3`; truth at `K4`
- Safe wording: fae, demons, mummies, and other beings may exist if the campaign selects and researches them.
- Forbidden wording: surprise crossover identity as a substitute for clues, imported PC options, or a power invented solely to defeat a player plan.
- Reveal requirement: source, individual motive, observed capability, hard limit, and fair foreshadowing.
- Source claims: `claim-wod-legacy-lines`, `claim-wod-cofd-separate`.

## Frame-Truth Register

| Fact id | Frame | Default holders | Reveal rule |
| --- | --- | --- | --- |
| `wod-vtm-frame-borrowed-night-secret-001` | Borrowed Night | GM plus separate grant, footage, and drive holders | three independent custody chains |
| `wod-vtm-frame-gilded-office-secret-001` | Gilded Office | GM, missing Keeper, retainer, broker fragments | document purpose, access path, and holder contact |
| `wod-vtm-frame-last-block-secret-001` | Last Block Awake | GM plus separate fund, predator, and Baron holders | ownership, incidents, and prior-knowledge evidence |
| `wod-vtm-frame-sigil-market-secret-001` | Sigil Market | GM, broker, apprentice, contractor fragments | sample custody, batch analysis, and data trail |
| `wod-vtm-frame-daylight-list-secret-001` | Daylight List | GM, local hunter, versioned data | version comparison, source verification, and testimony |
| `wod-vtm-frame-empty-throne-secret-001` | Empty Throne Below | GM, executor, selected retainers | logistics, provenance, and multi-claimant evidence |

Only the selected frame enters campaign knowledge boundaries.

## Claim Card Template

For every disputed in-world claim, record:

- claim text
- speaker or source
- visibility layer
- direct observations supporting it
- inference or doctrine added by the holder
- confidence
- who benefits if believed
- evidence that could change it
- whether the GM has fixed an objective answer
- safe player-facing wording

“The Prince said so,” “the Book of Nod says,” and “the hunters know” identify sources, not truth.

## Digital Evidence Procedure

For every digital lead, identify:

1. originating device or account
2. event actually recorded
3. metadata preserved
4. copies and backups
5. human or automated interpretation
6. access rights and current holders
7. mundane alternative explanation
8. threshold for escalation
9. physical consequence or location

A technical success may alter one link. It does not erase the chain by default.

## Other-Supernatural Reveal Procedure

Before revealing another line's creature or cosmology:

1. confirm it remains an NPC or world force
2. identify the exact source and edition
3. define only capabilities needed for this story
4. state hard limits and motives
5. separate vampire rumor from GM truth
6. provide observable clues before a label
7. decide who can recognize those clues
8. review cultural and safety implications
9. record what remains unknown

If any step is missing, preserve the phenomenon as an unresolved sign.

## Rumor Design

Every local rumor records:

- speaker and intended audience
- observed basis
- true component
- mistaken, doctrinal, or interested interpretation
- who benefits if believed
- who is harmed
- how it can be tested
- what remains unknowable

False rumor never authorizes contradiction of accepted campaign state.

## Player-Private Boundary

The following remain at `KP` until the originating player changes access:

- feelings, desires, and interiority
- private Convictions or interpretation of Humanity
- Touchstone meaning and boundaries
- sire relationship details not yet shared
- feeding history and consent details
- hidden clan or lineage hook proposed by the player
- Blood Bond, diablerie, ghoul, or cult history proposed by the player
- romance, sexuality, pregnancy, and family history
- mental health, trauma, and boundary rationale
- private Ambition, secret, and betrayal proposal

Institutional plausibility, Auspex-like power, Dominate-like power, or another PC's curiosity never overrides player authorship.
