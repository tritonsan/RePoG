# Cyberpunk Universe Knowledge Layers

## Purpose

The Cyberpunk universe depends on asymmetric and damaged knowledge. Records disappear in catastrophe, corporations compartmentalize, districts preserve local memory, Nomad routes use relationship-based intelligence, Fixers protect sources, Medias contest official accounts, Netrunners see only systems they can reach, and published protagonists know things an original crew does not.

This file defines defaults for future materialization. It does not make any frame solution player-known.

## Visibility Taxonomy

| Layer | Id | Who may know | Default use |
| --- | --- | --- | --- |
| Public surface | `P0` | ordinary public and public institutions | advertised services, visible places, public reports, broad history |
| Era common | `E0` | people ordinarily familiar with the selected time/place | broad 2045 or 2070 conditions without specialist detail |
| Local common | `L1` | residents, workers, regular travelers, or a district scene | routines, outages, visible authority, local reputation, active rumors |
| Role-restricted | `R2` | a profession, crew role, community, family unit, office, or contracted team | routes, procedures, maintenance, patient data, source networks, incident files |
| Organization-restricted | `O3` | named corporate office, state unit, gang cell, security provider, Fixer network, or leadership group | contracts, strategy, black projects, internal disagreement, proprietary records |
| Technical/contested | `T4` | named specialists, witnesses, systems, or researchers | Net architecture, cyberware behavior, disputed history, AI claims, forensic interpretation |
| Frame truth | `F5` | GM and discovered holders | package-original causal chain, hidden actions, and clocks |
| Continuity spoiler | `C6` | players who accepted the relevant work and PCs with justified access | published character outcomes, quests, anime events, secret programs |
| Player-private | `PP` | originating player and approved recipients | PC interiority, body history, private ties, employer history, boundaries, and proposed secrets |

A fact moves layers only through evidence, recorded disclosure, player consent, or an accepted continuity change.

## General Rules

1. Separate player franchise knowledge from character knowledge without punishment.
2. Record holders as people, teams, offices, devices, archives, vehicles, clinics, channels, or communities—not “the corporation knows.”
3. Distinguish observation, record, inference, sales claim, propaganda, rumor, memory, and objective campaign truth.
4. Give every secret a reason, cost, observable edge, and reveal path.
5. A technical success cannot manufacture context the target never possessed.
6. Deleting one file does not erase backups, bodies, damaged equipment, worker memory, physical routes, or public consequences.
7. Institutional names predict access and pressure, not unanimous knowledge.
8. A gameplay interface does not grant character knowledge unless the selected fiction and rules support it.
9. Published outcomes remain at `C6` until the spoiler contract admits them.
10. A PC's identity, feelings, body history, augmentation meaning, loyalty, trauma, and private relationships remain player-authored.

## Fact Cards

### `cyberpunk-fact-franchise-001` — The Timeline Is Shared But Era-Dependent

- Default layer: broad continuity at `E0`; exact events at `T4` or `C6`
- Safe wording: the official setting connects 2020, the 2023 catastrophe, 2045, the 2070s, and 2077, while conditions change materially between them.
- Forbidden wording: every technology, corporation, character, and district condition exists unchanged in every era.
- Reveal requirement for detail: selected era source and a justified character holder.
- Source claims: `claim-cyberpunk-franchise-continuity`, `claim-cyberpunk-era-bridge`.

### `cyberpunk-fact-night-city-001` — Night City Has A Dated History

- Default layer: major public events at `P0`–`E0`; disputed causes and local consequences at `L1`–`T4`
- Safe wording: Night City developed from Richard Night's Coronado City project, changed name after his assassination, endured wars and disasters, and rebuilt under changing institutions.
- Forbidden wording: one actor controlled the whole timeline or every resident interprets it alike.
- Reveal requirement: dated official source plus local evidence for current consequence.
- Source claims: `claim-cyberpunk-night-city-history`, `claim-cyberpunk-night-city-2045-release`.

### `cyberpunk-fact-2023-001` — The 2023 Catastrophe Reshaped Night City

- Default layer: broad event at `E0` in 2045 and later; operational detail at `T4` or `C6`
- Safe wording: a nuclear device detonated at Arasaka HQ in 2023, causing mass death and ending Night City's direct involvement in the Fourth Corporate War.
- Forbidden wording: exact responsibility, device history, survivor account, or named-character perspective beyond selected sources.
- Reveal requirement: targeted historical source for disputed detail.
- Source claims: `claim-cyberpunk-war-datakrash`, `claim-cyberpunk-night-city-history`.

### `cyberpunk-fact-governance-001` — 2045 Authority Is Distributed

- Default layer: broad district/Council structure at `E0`; exact contracts and decisions at `L1`–`O3`
- Safe wording: 2045 Night City uses district representation and a central Council amid uneven local authority and services.
- Forbidden wording: no government exists, the Council controls every street, or one district's offices apply everywhere.
- Reveal requirement: identify district, office, service, and decision-maker.
- Source claims: `claim-cyberpunk-2045-governance`, `claim-cyberpunk-district-variation`.

### `cyberpunk-fact-infrastructure-001` — Services Vary By Place

- Default layer: visible condition at `L1`; maintenance and contracts at `R2`–`O3`
- Safe wording: power, water, CitiNet, transit, and security may function differently across 2045 districts and locations.
- Forbidden wording: every outage is sabotage or a numeric district code describes every building.
- Reveal requirement: local observation, maintenance records, and responsible holder.
- Source claims: `claim-cyberpunk-district-variation`, `claim-cyberpunk-infrastructure-rebuild`.

### `cyberpunk-fact-scarcity-001` — 2045 Goods Have Supply Chains

- Default layer: broad scarcity at `E0`; source and price at `R2`
- Safe wording: transport disruption and rebuilding make barter, brokerage, Night Markets, repair, and substitute goods important in 2045.
- Forbidden wording: nothing is available, Eurobucks are meaningless, or a Fixer can obtain any item instantly.
- Reveal requirement: identify producer, route, broker, custody, and current stock.
- Source claims: `claim-cyberpunk-scarcity-economy`, `claim-cyberpunk-night-markets-fixers`.

### `cyberpunk-fact-nomads-001` — Nomads Are Logistics Powers

- Default layer: broad 2045 role at `E0`; family routes and decisions at `R2`–`O3`
- Safe wording: Nomad groups became central transport actors across roads, sea lanes, ports, and waystations after global disruption.
- Forbidden wording: every Nomad is a smuggler, one culture, rootless, or loyal to every other group.
- Reveal requirement: selected family/unit, route, cargo, obligation, and source.
- Source claim: `claim-cyberpunk-nomad-logistics`.

### `cyberpunk-fact-corporations-001` — Corporate Power Changes By Era

- Default layer: named public presence at `P0`–`E0`; portfolios and strategy at `O3`
- Safe wording: old MegaCorps, rising NeoCorps, contractors, and local offices hold different power after the Fourth Corporate War and in later eras.
- Forbidden wording: a corporation's 2020, 2045, and 2077 reach is identical or every employee knows global strategy.
- Reveal requirement: era, office, asset, contract, capability, and decision-maker.
- Source claims: `claim-cyberpunk-2020-corporate-order`, `claim-cyberpunk-corporate-change`.

### `cyberpunk-fact-gangs-001` — Gangs And Security Are Plural

- Default layer: visible local presence at `L1`; objectives and contracts at `R2`–`O3`
- Safe wording: Night City contains many gangs, criminal organizations, and security providers with different social and operational functions.
- Forbidden wording: all gangs are random predators, all security is public law, or one label determines morality.
- Reveal requirement: local face, constituency or client, method, capability, and limit.
- Source claim: `claim-cyberpunk-gangs-security`.

### `cyberpunk-fact-everyday-001` — The City Is Not Only Mercenaries

- Default layer: `P0`–`L1`
- Safe wording: workers, drivers, bartenders, bouncers, paramedics, artists, vendors, residents, and many others make Night City function and act on what they witness.
- Forbidden wording: ordinary people are interchangeable civilians, helpless clients, or background casualties.
- Reveal requirement for a local claim: speak to or observe the actual person or institution.
- Source claims: `claim-cyberpunk-everyday-life`, `claim-cyberpunk-housing-work`.

### `cyberpunk-fact-identity-001` — Records Affect Access

- Default layer: broad condition at `E0`; a person's status at `R2` or `PP`
- Safe wording: damaged or absent identity records and SIN recognition can affect work, services, housing, security response, and corporate treatment.
- Forbidden wording: every SINless person has no identity, community, rights, or agency.
- Reveal requirement: actual record, issuing/recognizing institution, and person consent where sensitive.
- Source claim: `claim-cyberpunk-identities-citizenship`.

### `cyberpunk-fact-net2045-001` — CitiNet Is Not The Old Global NET

- Default layer: broad 2045 condition at `E0`; system topology at `R2`–`T4`
- Safe wording: the DataKrash destroyed the prior global model; 2045 uses local CitiNet services and isolated NET Architectures with specific access paths.
- Forbidden wording: every Agent or CitiNet service can be Netrun, every system is wireless, or a Netrunner can enter “Night City.”
- Reveal requirement: name the device, service, Architecture, controller, connection, and physical endpoint.
- Source claims: `claim-cyberpunk-war-datakrash`, `claim-cyberpunk-net-2045`.

### `cyberpunk-fact-net2070-001` — Quickhacking Is Later-Era And Source-Bounded

- Default layer: broad existence at `E0` in a selected 2070s mode; exact targets/effects at `R2`–`T4`
- Safe wording: official 2070-era material supports quickhacks and direct-connection Netrunning alongside later cyberware and weapons.
- Forbidden wording: the public Mission Kit preview supplies complete extended 2070 Netrunning or quickhacks work unchanged in 2045.
- Reveal requirement: selected rules source, eligible target, access, defense, effect, and evidence.
- Source claim: `claim-cyberpunk-net-2070`.

### `cyberpunk-fact-cyberware-001` — Cyberware Does Not Define Personhood

- Default layer: broad prevalence at `E0`; individual body and meaning at `PP`
- Safe wording: cyberware can be medical, assistive, expressive, occupational, communicative, protective, or weaponized, and later-era material includes full-body conversion.
- Forbidden wording: chrome makes someone less human, unaugmented bodies are pure, or appearance predicts capability and violence.
- Reveal requirement for a person's body: their disclosure, visible evidence, or a consent-respecting medical/technical context.
- Source claims: `claim-cyberpunk-cyberware-body`, `claim-cyberpunk-2077-social-world`.

### `cyberpunk-fact-cyberpsychosis-001` — Cyberpsychosis Requires A Selected Model

- Default layer: public/in-world labels at `P0`–`L1`; exact condition and mechanics at `T4`; PC state at `PP`
- Safe wording: RED rules publicly describe Humanity, therapy, and cyberpsychosis-related thresholds, but exact portrayal belongs to the selected source and table contract.
- Forbidden wording: augmentation, disability, trauma, low empathy, or mental illness inevitably causes violence or erases personhood.
- Reveal requirement: owned rules, agreed portrayal, qualified in-world holder where relevant, and player consent for PC facts.
- Source claim: `claim-cyberpunk-humanity-therapy`.

### `cyberpunk-fact-healthcare-001` — Care And Response Are Unequal Systems

- Default layer: visible access differences at `L1`; contract and patient detail at `R2`–`O3`
- Safe wording: clinics, paramedics, corporate or private services, and security providers offer unequal response depending on place, contract, resources, and payment.
- Forbidden wording: everyone has Trauma Team, no one receives public/community care, or a provider's brand guarantees a specific response.
- Reveal requirement: local service, contract, dispatch path, current capacity, and patient consent.
- Source claim: `claim-cyberpunk-healthcare-security`.

### `cyberpunk-fact-media-001` — Attention And Truth Are Different Resources

- Default layer: public output at `P0`; sources and editorial decisions at `R2`–`O3`
- Safe wording: corporate and independent Medias, performers, Rockerboys, broadcasts, and cultural networks can shape public interpretation across eras.
- Forbidden wording: a broadcast automatically convinces everyone, corporate media always lies, or performer fame replaces evidence.
- Reveal requirement: source, evidence, distribution, audience, editorial action, and response.
- Source claim: `claim-cyberpunk-media-culture`.

### `cyberpunk-fact-famous-001` — Published People Have Protected Histories

- Default layer: broad public identity at `P0` or `E0`; plot outcomes at `C6`
- Safe wording: published figures exist according to the selected era and source, but original crews have their own consequential stories.
- Forbidden wording: V, Johnny, David, Lucy, Rogue, Panam, Judy, Jackie, Adam Smasher, or another named figure is available as a default patron or solution.
- Reveal requirement: accepted spoiler band and source-justified character knowledge.
- Source claims: `claim-cyberpunk-named-character-continuity`, `claim-cyberpunk-edgerunner-agency`, `claim-cyberpunk-2077-social-world`.

### `cyberpunk-fact-dogtown-001` — Dogtown Is A 2077 Political Theater

- Default layer: broad expansion premise at `E0` after selection; identities and outcomes at `C6`
- Safe wording: *Phantom Liberty* frames Dogtown through espionage, NUS presidential stakes, fractured loyalties, and political intrigue.
- Forbidden wording: expansion-specific alliances, outcomes, or protagonist decisions before spoiler acceptance.
- Reveal requirement: selected expansion spoiler band and exact source.
- Source claim: `claim-cyberpunk-dogtown-nusa`.

### `cyberpunk-fact-outside-001` — The Wider World Requires Specific Sources

- Default layer: broad existence at `E0`; local conditions at `T4`
- Safe wording: Free States, NUSA interests, Badlands, overseas routes, and orbital infrastructure exist, but this package is not a complete global atlas.
- Forbidden wording: every place outside Night City shares one collapse, law, culture, technology level, or corporate order.
- Reveal requirement: named place, era, source, cultural review, and bounded operating model.
- Source claim: `claim-cyberpunk-global-scope-limited`.

## Frame-Truth Register

| Fact id | Frame | Default holders | Reveal rule |
| --- | --- | --- | --- |
| `cyberpunk-frame-last-light-secret-001` | Last Light On The Block | GM plus separate supplier, convoy, depot, and claimant fragments | supplier record, route evidence, and depot custody |
| `cyberpunk-frame-market-ghost-secret-001` | Ghost Stock | GM plus patients, whistleblower, supplier, contractor, and recovery office fragments | consented diagnostics, serial provenance, and disposal chain |
| `cyberpunk-frame-open-channel-secret-001` | Keep The Channel Open | GM plus source, workers, clinic/responders, contractor, gang, and outlets | utility, casualty, testimony, and event chronology |
| `cyberpunk-frame-broken-convoy-secret-001` | Convoy That Arrived Twice | GM plus convoy, settlement, clinic, elder, broker, and false-delivery fragments | credential, cargo, route, and rescue evidence |
| `cyberpunk-frame-clean-hands-secret-001` | Clean Hands, Dirty Contract | GM plus dispatch, software, responder, patient, client, and management fragments | versioned system, operational timeline, and consented medical evidence |
| `cyberpunk-frame-shattered-loyalty-secret-001` | A Country In The Dead Drop | GM plus analyst, offices, victims, distributor, and broker fragments | source-supported code, clinic pattern, and competing office orders |

Only the selected frame enters campaign knowledge boundaries.

## Evidence Card Template

For every disputed proposition, record:

- proposition
- observation or source
- visibility layer
- holder and custody
- timestamp and era
- direct evidence
- inference, sales claim, doctrine, or propaganda added
- confidence
- who benefits if believed
- privacy or safety limit
- evidence that could change it
- whether the GM has fixed an objective answer
- safe player-facing wording

“The corporation says,” “the gang knows,” “the Net shows,” and “the government confirmed” identify speakers, not truth.

## Data And Net Evidence Procedure

For every digital lead identify:

1. selected era
2. originating device, sensor, person, or account
3. system category and connection path
4. event actually recorded
5. metadata preserved
6. copies, backups, and offline records
7. current controller and access rights
8. automated and human interpretation
9. mundane or competing explanation
10. intrusion trace
11. physical endpoint and consequence
12. threshold for escalation

A Netrunner may alter one or more links under selected rules. They do not erase the chain by default.

## Institutional Claim Procedure

Before saying an organization knows, owns, orders, or attacks, identify:

- exact office, cell, unit, team, or representative
- authority and era
- evidence or contract relied upon
- capability available now
- route of action
- people who execute it
- internal disagreement
- missing information
- hard limit
- consequence if the claim is exposed as wrong

## Rumor Design

Every local rumor records:

- speaker and intended audience
- observed basis
- true component
- mistaken, interested, or propagandistic interpretation
- era assumptions embedded in it
- who benefits if believed
- who is harmed
- how it can be tested
- what remains unknowable

False rumor never authorizes contradiction of accepted campaign state.

## Player-Private Boundary

The following remain at `PP` until the originating player changes access:

- identity, feelings, desires, beliefs, and interiority
- body history, disability, pain, dysphoria, augmentation meaning, and medical context
- cyberware ownership, maintenance, therapy, and private telemetry
- mental health, trauma, addiction, cyberpsychosis proposal, and boundary rationale
- family, community, romance, sexuality, pregnancy, and dependents
- private employer, state, gang, Nomad, or corporate history
- debt, coercive contract, criminal act, betrayal, and secret patron proposed by the player
- ambition, shame, loyalty, reputation truth, and hidden motive
- desired relationship to a famous event or character
- any private crew tie or exit plan

Corporate plausibility, technical access, a quickhack, a medical scan, interrogation, or another PC's curiosity never overrides player authorship or table boundaries.
