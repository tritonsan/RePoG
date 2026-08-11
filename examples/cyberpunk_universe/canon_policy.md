# Cyberpunk Universe Canon Policy

## Research Posture

This package treats the shared R. Talsorian Games–CD PROJEKT RED Cyberpunk setting as one historical universe with era-dependent conditions. It does not flatten tabletop editions, anime, games, public marketing pages, and later sourcebooks into one simultaneous present.

Research snapshot: 2026-07-23. Official R. Talsorian and Cyberpunk/CD PROJEKT RED public pages were inspected. Full commercial books, the complete anime, and every game database entry were not independently re-read during this pass. Product scope, public previews, and broad continuity claims can therefore be high confidence while exact mechanics, corporate portfolios, global geopolitics, Blackwall details, AI capabilities, and named-event minutiae remain source-gated.

## Default Selection

- Continuity: `cyberpunk-2045-red`
- Era: `2045-time-of-the-red`
- Locale: `night-city-original-bounded-district`
- Crew: `mixed-original-crew`
- Crew size: three to five player characters
- Frame: `cyberpunk-frame-last-light`
- Rules: `system-neutral`, with owned *Cyberpunk RED* as the optional 2045 implementation
- Famous-character proximity: `background-or-absent`
- Canon-event dependence: `low`
- Net model: `2045-citinet-local-architectures`
- Campaign divergence: none

The default uses Night City without assigning the crew a published protagonist's role, retelling a published plot, or inventing a district that secretly caused a canonical event.

## Source Hierarchy

| Rank | Source layer | Default use | Limit |
| --- | --- | --- | --- |
| 1 | Selected era's current official R. Talsorian setting/rules source | Era conditions, Night City, organizations, technology, and tabletop implementation | Exact commercial text must be checked when mechanics or fine lore matter |
| 2 | Official R. Talsorian public product pages, previews, timelines, and DLC | Advertised scope, public lore, release status, and bounded examples | Preview language is incomplete and may predate final print |
| 3 | Official CD PROJEKT RED Cyberpunk portal and product pages | 2070s presentation, named people, Dogtown/NUS, game/anime media scope | Gameplay systems and protagonist outcomes are not universal setting rules |
| 4 | Selected licensed fiction or adaptation | Only the named adaptation's events, characters, and presentation | Must be marked era/media-specific and spoiler-scoped |
| 5 | Earlier official Cyberpunk editions | Their own period or individually accepted historical claims | Never used to fill a later era silently |
| 6 | RePoG package-original content | District situations, original crews, actors, clocks, frames, and hidden truths | Playable proposal only; not franchise canon |
| 7 | Fan references and unsourced memory | Research leads only | No authority in materialized claims |

Explicit user choices, safety boundaries, and accepted campaign history outrank package defaults.

## Continuity Modes

| Mode | Meaning | Default |
| --- | --- | --- |
| `cyberpunk-2013-2020` | Corporate-era play using a named early source set | No; requires targeted source review |
| `cyberpunk-2023-aftermath` | Fourth Corporate War, Night City catastrophe, and immediate consequences | No; high canon-event proximity |
| `cyberpunk-2045-red` | Time of the Red, rebuilding, scarcity, local CitiNets, and shifting powers | Yes |
| `cyberpunk-2070-edgerunners` | 2070s Night City using the *Edgerunners Mission Kit* and selected anime context | No; spoiler and technology review required |
| `cyberpunk-2077` | *Cyberpunk 2077* era using selected game/source material | No; named-event and gameplay separation required |
| `cyberpunk-2077-phantom-liberty` | 2077 plus Dogtown/NUS espionage context | No; named protagonist proximity must be resolved |
| `campaign-divergent` | One or more official premises deliberately changed | No; branch point and consequences must be recorded |

Do not use a broad label such as `modern-cyberpunk` to bypass era selection.

## Era Separation

| Period | Supported public baseline | Must not import automatically |
| --- | --- | --- |
| 2013/2020 | corporations dominate from fortified power centers; cyberware, gangs, urban action, Rockerboy and Netrunner culture are prominent | 2045 scarcity rules, modern CitiNet assumptions, 2070 quickhacks, 2077 officeholders |
| 2023 and aftermath | Fourth Corporate War damage, the Arasaka HQ nuclear detonation, mass death, displacement, and infrastructure collapse reshape Night City | a restored 2077 skyline, stable global logistics, later political settlements |
| 2045 | rebuilding Night City, distributed district authority, uneven utilities/security, scarcity, NeoCorps, Nomad logistics, Night Markets, local CitiNet/NET Architectures | 2070 quickhacks, universal wireless access, 2077 Dogtown/NUS plot, later corporate status |
| 2070s | dense 2070-era cyberware, weapons, quickhacks, megacorp/gang conflict, braindance culture, and later political conditions | 2045 shortages or district conditions unchanged by default; published protagonist outcomes as crew history |

Source claims: `claim-cyberpunk-era-bridge`, `claim-cyberpunk-2020-corporate-order`, `claim-cyberpunk-war-datakrash`, `claim-cyberpunk-net-2045`, `claim-cyberpunk-net-2070`.

## Setting Versus Game Mechanics

A rule exists to produce play. It becomes a setting fact only when the selected fiction source supports that interpretation.

- Price categories, role abilities, Humanity Loss numbers, quickhack lists, combat timing, inventory slots, map boundaries, fast travel, enemy levels, respawn behavior, interface highlights, and dialogue menus are mechanics.
- Broad scarcity, local brokerage, therapy, cyberware maintenance, quickhacking in the 2070s, district inequality, and bodily risk may be setting claims when sourced.
- A game allowing or forbidding an action does not prove that every person in the world experiences the same limit.
- A player-facing interface is not automatically a visible in-world display.
- System conversion must preserve causal pressures without copying proprietary rules text.

## Night City Policy

Night City is the default because official material presents it across multiple eras and because 2045 offers high local agency between 2020 and 2077. The city is never treated as one uniform crime zone.

For 2045:

- district governance, population, security, utilities, law, citizenship, transport, media, and recent history vary locally
- the City Council and district representatives do not create a fully centralized state
- NCPD, MAX-TAC, private corporations, gangs, Nomad peacekeepers, and other providers may perform different security functions
- services persist through labor, inertia, community action, and corporate need rather than omnipotent administration
- rebuilding, displacement, poverty, tourism, work, entertainment, care, and ordinary life coexist

Source claims: `claim-cyberpunk-night-city-history`, `claim-cyberpunk-2045-governance`, `claim-cyberpunk-district-variation`, `claim-cyberpunk-infrastructure-rebuild`, `claim-cyberpunk-identities-citizenship`.

An original opening district is a bounded campaign canvas. It may occupy an unspecified edge, redevelopment parcel, sub-neighborhood, or connection between canonical districts, but it may not erase a named district, claim secret authorship of the official timeline, or replace a published community.

## World Beyond Night City

The Cyberpunk universe is larger than Night City, but this research pass is Night-City-heavy. Badlands routes, Nomad logistics, Northern California/Free State structures, NUSA involvement, overseas missions, and orbital infrastructure are supported at broad levels. Exact conditions in another nation, continent, sea lane, space habitat, or Highrider community require a targeted source pass.

Use outside-world locations as routes and pressures before treating them as complete gazetteer entries. “The rest of the world” is never a single failed-state backdrop.

Source claims: `claim-cyberpunk-nomad-logistics`, `claim-cyberpunk-dogtown-nusa`, `claim-cyberpunk-global-scope-limited`.

## Corporations, States, And Local Powers

- Corporations are institutions made of offices, teams, contractors, assets, dependencies, and internal disagreements—not omniscient persons.
- Corporate status changes by era. A power at the city's founding, in 2020, in 2045, and in 2077 cannot be assumed to possess identical reach.
- Arasaka, Militech, Night Corp, Ziggurat, Network 54, Orbital Air, Petrochem, EBM, and other named organizations may be used only within sourced era scope.
- NUSA, Northern California, Free State structures, Night City authorities, and district managers have overlapping but non-identical claims.
- Gangs may provide protection, culture, work, identity, smuggling, entertainment, radicalization, exploitation, or violence. “Gang” does not mean one behavior.
- Security providers require a contract, jurisdiction, response capacity, and local limit.
- Fixers and Night Markets connect scarcity, trust, logistics, reputation, and access; they do not summon any item without a supply chain.
- Nomad families and nations are not generic bandits. In 2045 they are central transportation actors with internal obligations and specialized routes.

Source claims: `claim-cyberpunk-corporate-change`, `claim-cyberpunk-gangs-security`, `claim-cyberpunk-night-markets-fixers`, `claim-cyberpunk-nomad-logistics`.

## Technology And Net Policy

### 2045

The DataKrash and war broke the old global model. Official public descriptions support local CitiNet service, Data Pool access, isolated NET Architectures, physical access distinctions, and uneven infrastructure. An Agent or CitiNet is not automatically a NET Architecture that a Netrunner can enter. Every digital operation needs a specific system, access path, holder, and consequence.

### 2070s

The *Edgerunners Mission Kit* supports 2070-era cyberware, guns, quickhacks, and both quickhacking and direct-connection Netrunning. That does not authorize 2070 capabilities in 2045. Its public preview explicitly says the kit is not a complete extended 2070 Netrunning source.

### Source-Gated Topics

Blackwall structure, rogue AIs, Soulkiller/engram operation, deep Old NET expeditions, complete 2077 network architecture, and exact quickhack propagation require the selected commercial source. Until then they remain rumor, background, or unresolved research.

Source claims: `claim-cyberpunk-war-datakrash`, `claim-cyberpunk-net-2045`, `claim-cyberpunk-net-2070`.

## Cyberware, Bodies, And Personhood

Cyberware may be assistive technology, healthcare, fashion, labor equipment, communication, sensory access, identity expression, survival tool, weapon, status marker, corporate property claim, or any combination chosen by the person and campaign. Unaugmented bodies are not more authentic; heavily augmented bodies are not less human.

The inspected RED Q&A describes mechanical Humanity Loss, therapy, maximum Humanity changes, and a game state called borderline cyberpsychosis. Those procedures are rules-facing evidence, not permission to diagnose real people, equate disability or augmentation with violence, or declare a universal metaphysical loss of personhood. Exact cyberpsychosis etiology and portrayal remain source-gated.

Rules:

- never assign a PC's cyberware, body history, dysphoria, disability, medical need, or augmentation regret without player consent
- never use visible chrome as reliable evidence of danger or morality
- distinguish treatment access, repair, therapy, coercion, ownership, and social stigma
- record who paid for an implant, who claims rights over it, who maintains it, and what the person agreed to
- treat full-body conversion, experimental implants, forced modification, scavenged cyberware, and employer ownership as explicit safety topics
- do not use “cyberpsycho” as neutral narration for every violent augmented person

Source claims: `claim-cyberpunk-cyberware-body`, `claim-cyberpunk-humanity-therapy`, `claim-cyberpunk-healthcare-security`.

## Everyday Life Policy

A Cyberpunk campaign is not populated only by mercenaries. Every opening district must include people who work, care, organize, perform, drive, repair, report, sell, cook, clean, teach, treat, build, rest, and refuse.

Housing, food quality, rent, utilities, transit, healthcare, identity documentation, work, entertainment, and security are causal rather than decorative. Poverty is not a visual filter; wealth is not immunity from dependency. A gig or firefight can change who has power, water, medicine, transport, employment, or a bed.

Source claims: `claim-cyberpunk-everyday-life`, `claim-cyberpunk-housing-work`, `claim-cyberpunk-infrastructure-rebuild`.

## Named Characters And Published Events

Richard Night, Johnny Silverhand, Rogue, David, Lucy, V, Panam, Judy, Jackie, Adam Smasher, and other published people retain their source-defined agency. Their existence may establish history or culture, but they are not default patrons, party members, villains, emergency contacts, or solutions.

- Published outcomes are protected spoilers.
- A campaign may intersect a named event only after selecting the exact era/media continuity and divergence policy.
- Original PCs do not secretly replace a published protagonist.
- Famous people do not validate a crew's importance.
- The default opening is designed to work if every famous character remains offstage.

Source claims: `claim-cyberpunk-named-character-continuity`, `claim-cyberpunk-edgerunner-agency`, `claim-cyberpunk-2077-social-world`.

## Cyberpunk 2077 Campaign Book Status

The July 2025 R. Talsorian announcement described a future book containing comprehensive RED rules for the *Edgerunners*/*Cyberpunk 2077* era plus a multi-mission campaign, while explicitly saying it would not be a full rulebook or world sourcebook. No 2026 release post for that exact title appeared in the official WordPress search at this research cutoff, and it was not listed on the official downloads page updated 2026-07-20.

Treat it as `announced-unverified-release` at this snapshot. Absence from a search is not proof of cancellation or non-publication; check again before using it.

Source claim: `claim-cyberpunk-2077-book-status`.

## Conflict Resolution

When sources differ:

1. Identify the selected era and medium.
2. Distinguish historical change from contradiction.
3. Prefer the selected era's final official source for operational detail.
4. Treat previews as bounded evidence and note when they predate publication.
5. Separate gameplay implementation from fictional proposition.
6. Do not fill commercial-source silence with fan memory.
7. Ask the user when the choice changes a PC's body, identity, history, campaign promise, or spoiler exposure.
8. Record source ids, claim ids, confidence, mutability, era origin, and visibility.
9. Preserve a campaign divergence rather than retroactively rewriting accepted history.

Silence is not contradiction. Package-original local content may occupy blank space without claiming to be hidden canon.

## Spoiler Policy

| Band | Default treatment |
| --- | --- |
| Franchise premise, Night City, broad era names | Player-safe after package selection |
| 2023 catastrophe and broad 2045 reconstruction | Player-safe for a 2045 campaign |
| 2045 district details and named organizations | Shared only as relevant local knowledge |
| *Edgerunners* character biographies and ending-dependent material | Protected unless anime spoilers are accepted |
| *Cyberpunk 2077* quests, endings, Relic details, and named outcomes | Protected unless game spoilers are accepted |
| *Phantom Liberty* identities, alliances, and outcomes | Protected under a separate spoiler choice |
| Corporate secrets, Net architecture, black projects, and AI claims | Holder-bound, not franchise-player omniscience |
| Frame hidden truths | GM-only until reveal gates are met |
| PC history, body context, loyalties, and private motives | Player-private until the originating player changes access |

## Safety And Cultural Guardrails

- Set lines and veils for gun violence, body horror, surgery, dismemberment, forced augmentation, organ/cyberware extraction, torture, addiction, sex work, exploitation, poverty, homelessness, policing, incarceration, state violence, war, nuclear aftermath, and harm to children.
- Do not aestheticize poverty, displacement, contamination, or inaccessible healthcare without showing affected people's agency.
- Do not map gangs, Nomad families, corporations, or districts onto ethnic stereotypes.
- Treat language, migration, citizenship/SIN status, and cultural communities with targeted research when made specific.
- Do not present police, private security, gangs, corporations, states, rebels, or crews as automatically legitimate.
- Do not use mental illness as shorthand for cyberpsychosis, unpredictability, villainy, or reduced personhood.
- Never use a PC's body as employer property, hacked equipment, detachable inventory, or a hidden experiment without explicit player agreement.
- Define PvP, betrayal, coercive contracts, surveillance, brain editing, braindance intimacy, romance, and compromised consent before play.
- A dark future does not waive boundaries or require hopelessness.

## Open Uncertainties

Before strict operational use, verify from selected owned sources:

1. Exact rules and fiction for Humanity, Empathy, cyberpsychosis, therapy, medical-grade cyberware, and full-body conversion
2. Exact 2045 corporate status, portfolios, leadership, extraterritoriality, and security relationships
3. Exact 2070/2077 quickhack, direct-connection, Blackwall, rogue-AI, Soulkiller, engram, and Old NET capabilities
4. Exact Night City law, citizenship, SIN, policing, MAX-TAC, Trauma Team, and district governance needed by the frame
5. Exact Nomad family/nation structures, routes, cultural practices, and cross-border authority
6. Any campaign outside Night City, especially another nation, continent, ocean route, lunar/orbital site, or Highrider community
7. Any named gang, criminal organization, security provider, district manager, fixer, or published location used operationally
8. Any 2013/2020-era event, officeholder, technology, or corporate condition beyond the public summaries
9. Any named *Edgerunners*, *Cyberpunk 2077*, or *Phantom Liberty* outcome
10. Current release status and final scope of the announced *Cyberpunk 2077 Campaign Book*
11. Any product or official correction published after 2026-07-23

## Campaign Divergence Record

Every accepted divergence preserves:

- divergence id
- selected era and source set
- exact branch point
- official claim being changed
- user decision and date
- PC and campaign-promise impact
- technology, faction, and chronology consequences
- facts made uncertain
- spoiler and visibility changes
- safety review result

A divergence changes only the materialized campaign. It never rewrites this package.
