# Dune Knowledge Layers

## Purpose

Dune depends on asymmetry: institutions protect methods, Houses compartmentalize plans, desert communities protect routes and water, prescience complicates certainty, and later novels transform what an earlier-era character could know. This file defines defaults for future materialization; it does not reveal a selected frame's answer to players.

## Visibility Taxonomy

| Layer | Id | Who may know | Default use |
| --- | --- | --- | --- |
| Public premise | `K0` | all players and most setting-aware characters | broad Imperium, Arrakis, spice, Houses, Guild |
| Local common | `K1` | residents or workers in the selected place | routines, hazards, visible authority, common rumors |
| Role-restricted | `K2` | specific profession, House office, or faction role | manifests, procedures, training, privileged routes |
| Protected community | `K3` | holders admitted by a specific community | sietch location, water stores, survival routes, internal decisions |
| Institutional secret | `K4` | named faction holders | operations, breeding plans, hidden contracts, Guild method |
| Frame truth | `K5` | GM and discovered holders | package-original causal answer and clocks |
| Continuity spoiler | `K6` | players who accepted the relevant saga knowledge | betrayals, outcomes, identities, later-era transformations |
| Player-private | `KP` | originating player and explicitly approved recipients | PC interiority, private history, boundaries, proposed secrets |

A fact can move layers only through a recorded reveal, player consent, or accepted era transition.

## General Rules

1. Separate player familiarity from character knowledge without punishing either.
2. Record holders as people or institutions, not abstract labels alone.
3. Give every secret a reason, cost, and observable edge.
4. A successful analysis can identify patterns without manufacturing missing inputs.
5. Prescience creates possibilities, pressure, and interpretation; it does not silently move all facts to public.
6. Community-protected facts require relationship and consent, not a generic investigation success.
7. A PC's private truth remains player-authored even if a faction plausibly wants to know it.
8. Famous future events stay at `K6` in a pre-*Dune* campaign.

## Fact Cards

### `dune-fact-spice-001` — Spice Is Systemically Central

- Default layer: `K0`
- Safe wording: Arrakis alone supplies melange, and Imperial powers depend on it for wealth, longevity, trained awareness, and Guild navigation.
- Do not say at K0: exact reserves, individual addiction, secret stockpiles, or complete ecological mechanism.
- Reveal requirement for specifics: role access, physical evidence, or selected source research.
- Source claims: `claim-dune-arrakis-spice`, `claim-dune-guild-travel`.

### `dune-fact-imperium-001` — Feudal Power Has Several Centers

- Default layer: `K0`
- Safe wording: the Emperor, Landsraad Houses, Guild, CHOAM interests, and other institutions possess different forms of leverage.
- Do not say at K0: that these powers are equal, transparent, or committed to ordinary people's rights.
- Reveal requirement for a current dispute: named actors, jurisdiction, and accepted era.
- Source claims: `claim-dune-feudal-imperium`, `claim-dune-power-balance`, `claim-dune-choam`.

### `dune-fact-machines-001` — Thinking Machines Are Proscribed

- Default layer: `K0`
- Safe wording: Imperial civilization rejects thinking machines and relies heavily on trained humans and bounded technologies.
- Do not say at K0: that all computation or advanced technology is absent, or that every disputed device has one obvious legal status.
- Reveal requirement for legality: device-specific and era-specific research.
- Source claims: `claim-dune-limits-computers`, `claim-dune-human-schools`.

### `dune-fact-shields-001` — Shields Change Combat

- Default layer: `K0` for trained characters, `K1` otherwise
- Safe wording: personal shields stop fast attacks and make controlled close combat important.
- Restricted detail: exact equipment behavior, tactical counters, local availability.
- Safety-critical detail: lasgun contact with a shield can produce catastrophic and unpredictable destruction; do not treat the combination casually.
- Reveal requirement: ordinary military or House training.
- Source claims: `claim-dune-shields`.

### `dune-fact-convention-001` — Convention Constrains Escalation

- Default layer: `K1` broad, `K2` legal detail
- Safe wording: inter-House convention, atomics restrictions, kanly forms, and fear of collective retaliation shape how conflict is presented.
- Do not say at K1: that an act is definitively lawful or that convention protects everyone equally.
- Reveal requirement for a ruling: authenticated facts, selected era, and targeted legal research.
- Source claims: `claim-dune-kanly-convention`, `claim-dune-atomics`.

### `dune-fact-water-001` — Water Has Different Social Meanings

- Default layer: `K1` on Arrakis
- Safe wording: water is scarce and structures daily routine, status, hospitality, labor, survival, and many Fremen practices.
- Do not say at K1: that city, village, smuggler, and sietch customs are identical.
- Reveal requirement for community practice: a specific local holder and relationship.
- Source claims: `claim-dune-water`, `claim-dune-class-daily-life`.

### `dune-fact-sietch-001` — A Specific Sietch Location

- Default layer: `K3`
- Safe public wording: Fremen communities live and move beyond the control imagined by Imperial authorities.
- Forbidden public wording: map coordinates, population, water reserves, entrances, internal divisions, or guaranteed alliance.
- Reveal requirement: the specific community chooses disclosure for a defined purpose; survival discovery alone does not grant free reuse.
- Source claims: `claim-dune-fremen`, `claim-dune-water`.

### `dune-fact-ecology-001` — Worm, Desert, Water, And Spice Are Coupled

- Default layer: `K4` for a complete model; observable fragments at `K1`–`K3`
- Safe public wording: spice production and sandworms belong to Arrakis's living desert system.
- Forbidden early wording: a complete sandtrout/water/spice cycle, exact intervention point, or claim that an outsider has mastered the system.
- Reveal requirement: multiple observations, era-appropriate primary-source research, and a holder with situated knowledge.
- Source claims: `claim-dune-worm-spice-cycle`, `claim-dune-arrakis-spice`.

### `dune-fact-missionaria-001` — Prepared Religious Patterns

- Default layer: `K4` Bene Gesserit; contextual fragments may reach `K2`
- Safe player-facing wording after reveal: the Sisterhood has planted adaptable legends in some cultures as emergency tools.
- Forbidden wording: Fremen belief is merely fabricated, all prophecy is controlled, or believers lack agency.
- Reveal requirement: Sisterhood access, recognized pattern, and evidence relevant to the selected community.
- Source claims: `claim-dune-missionaria`, `claim-dune-religion`.

### `dune-fact-guild-001` — Guild Dependence And Protected Method

- Default layer: transport dependence at `K0`; operational detail at `K4`
- Safe wording: the Guild controls ordinary strategic interstellar passage and depends on spice-linked navigation.
- Forbidden wording: exact Navigator procedure, universal schedule, price, or internal motive without source and holder.
- Reveal requirement: selected role, contract, or targeted research.
- Source claims: `claim-dune-guild-travel`, `claim-dune-arrakis-spice`.

### `dune-fact-bene-gesserit-001` — Trained Capacity Is Not Mind Control Omnipotence

- Default layer: broad reputation at `K1`, technique at `K2`–`K4`
- Safe wording: Bene Gesserit training can support exceptional observation, bodily discipline, and influence.
- Forbidden wording: automatic command over any person, infallible lie detection, uniform loyalty, or unconsented hidden control of a PC.
- Reveal requirement: character training, witnessed use, or institutional access.
- Source claims: `claim-dune-human-schools`.

### `dune-fact-prescience-001` — A Vision Is Not A Settled Future

- Default layer: `K2` for the experiencer; disclosure is their choice unless the player delegates it
- Safe wording: the vision presents images, pressures, absences, or branching possibilities whose interpretation has a cost.
- Forbidden wording: “you know this must happen,” forced PC emotion, or retroactive proof that the GM planned every result.
- Reveal requirement: agreed mechanic and player consent for private vision content.
- Source claims: `claim-dune-prescience`.

### `dune-fact-choam-001` — Economic Records Are Political

- Default layer: CHOAM's broad importance at `K1`; ownership and audit detail at `K2`–`K4`
- Safe wording: CHOAM connects House wealth, trade, contracts, and spice flow.
- Forbidden wording: invented exact share percentages, board procedure, or audit powers treated as canon.
- Reveal requirement: selected frame research and authenticated documents.
- Source claims: `claim-dune-choam`.

### `dune-fact-awakening-001` — Paul-Less Alternate Timeline

- Default layer: `K0` only when offering or selecting `awakening-alternate`
- Safe wording: *Dune: Awakening* explicitly asks what if Paul Atreides had never been born.
- Forbidden use: treating this as a hidden fact or gap-filler in `fh-core`.
- Reveal requirement: none after the continuity is offered; the premise defines informed selection.
- Source claims: `claim-dune-awakening-alternate`.

## Frame-Truth Register

| Fact id | Frame | Default holders | Reveal rule |
| --- | --- | --- | --- |
| `dune-frame-dry-ledger-secret-001` | Dry Ledger | GM plus separate scheme participants | two independent evidence chains |
| `dune-frame-ashes-secret-001` | Ashes of Kanly | GM, heir, fragments held by rival/protector | physical, signal, and motive evidence |
| `dune-frame-manifest-secret-001` | Silent Manifest | GM, hidden families, thief | custody, telemetry, and consent |
| `dune-frame-maker-secret-001` | Maker's Margin | GM and different partial witnesses | authorization, charge custody, testimony, site |
| `dune-frame-audience-secret-001` | Golden Audience | GM, sponsor's inner circle, archival fragments | multi-ledger provenance and excluded records |
| `dune-frame-bornless-secret-001` | Bornless Horizon | GM and divided survey team | structural evidence, custodial layers, survivor contact |

Only the selected frame enters campaign knowledge boundaries.

## Continuity Spoiler Matrix

| Knowledge | Pre-transfer default | Atreides transition | Muad'Dib ascension | Later eras | Awakening alternate |
| --- | --- | --- | --- | --- | --- |
| Arrakis and spice premise | `K0` | `K0` | `K0` | historical common knowledge | `K0` in game-specific form |
| Atreides appointment | `K6` until selected | `K0` | historical | historical | not assumed |
| Betrayals and deaths in *Dune* | `K6` | `K5`/`K6` by scene | historical or restricted | historical | not imported |
| Fremen scale and plans | `K3`/`K4` | `K3`/`K4` | era-specific | era-specific | game-specific mystery |
| Paul/Muad'Dib outcomes | `K6` | `K6` | `K0` as era premise | historical | absent by branch premise |
| Later-regime transformations | `K6` | `K6` | `K6` | era-specific | not imported |
| Package frame secrets | `K5` | `K5` | `K5` | `K5` | `K5` |

## Holder Materialization

For every non-public fact, record:

- fact id
- concise proposition
- visibility layer
- current holders
- basis of each holder's knowledge
- confidence and possible error
- safe observable signs
- reveal requirements
- forbidden early wording
- consequences of disclosure
- source claim or package-original designation

“Bene Gesserit know” or “Fremen know” is insufficient. Name the local person, cell, sietch, archive, or office.

## Prescience Procedure

Before using prescience, agree on:

1. who authors imagery: player, GM, or collaboration
2. whether a vision is private
3. how ambiguity is marked
4. which decisions can narrow or invalidate it
5. what cost or pressure accompanies clarity
6. how to prevent visions from dictating PC feelings or actions

A useful vision changes a decision. It should not merely spoil a hidden truth.

## Rumor Design

Every local rumor should record:

- speaker and audience
- observed basis
- true component
- mistaken or interested interpretation
- who benefits if believed
- how it can be tested

Do not use false rumor as permission to contradict established post-materialization state.

## Player-Private Boundary

The following stay at `KP` until the originating player changes access:

- feelings and interiority
- private faith or doubt
- secret ancestry proposed by that player
- hidden faction tie proposed by that player
- reproductive history or condition
- romance and attraction
- trauma detail
- personal boundary rationale

Institutional plausibility never overrides player authorship.
