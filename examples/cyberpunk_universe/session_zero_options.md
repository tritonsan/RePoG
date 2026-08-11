# Cyberpunk Universe Session 0 Options

## Player-Safe Use

This file contains no frame solutions. It proposes decisions but accepts none. Present one unresolved decision at a time, record answers only in campaign-owned files, and leave unselected options as inert reference.

This package is for the specific Cyberpunk fictional universe. If the group wants a generic neon dystopia, another franchise, or a genre remix unconstrained by this timeline, stop and create a different package rather than mislabeling it.

## Recommended Default Pitch

It is 2045 in Night City. You are an original mixed crew of three to five people tied to one rebuilding district. Its clinic, pumps, and occupied housing depend on a failing utility controller. A replacement disappeared on a damaged supply route, while a corporate subcontractor and its security provider claim any recovered unit. You have forty-eight hours to keep the district running and decide whose contracts, needs, and future your skills will serve.

Default selections proposed, not accepted:

- Universe: official Cyberpunk continuity
- Era: 2045, Time of the Red
- Locale: Night City, one original bounded rebuilding district
- Frame: `cyberpunk-frame-last-light`
- Crew: mixed original crew, three to five PCs
- Scale: crew influence over one district dependency
- Corporate proximity: one local office, contractor, or claimant
- Famous characters: absent
- Net: 2045 CitiNet and local NET Architectures only as sourced
- Rules: system-neutral fiction; owned *Cyberpunk RED* if mechanics are wanted
- Tone: material pressure with room for solidarity, style, humor, and change

## Decision Order

1. Confirm Cyberpunk-universe rather than generic-genre scope
2. Select era and continuity
3. Set spoiler ceiling and famous-character proximity
4. Select rules implementation and allowed sources
5. Select physical theater and one connection layer at most
6. Select campaign fantasy, crew mandate, and scale
7. Define corporate, civic, community, gang, security, and Nomad proximity
8. Define technology, Net, cyberware, healthcare, and body-autonomy contracts
9. Set tone, consequence, and safety boundaries
10. Author PCs and crew ties
11. Select one frame or create an original local pressure
12. Approve pruned materialization into `campaign/`

Do not request a complete encyclopedia of answers at once.

## Scope Confirmation

Ask first:

> Do you want Mike Pondsmith and R. Talsorian Games' Cyberpunk universe, including its continuity into *Cyberpunk: Edgerunners* and *Cyberpunk 2077*, rather than a generic cyberpunk setting or a campaign that retells one game's protagonist plot?

If the answer is no, stop materialization and design the requested world. If yes, keep eras separate until one is selected.

## Era And Continuity Choice

| Option | Player-safe promise | Complexity | Key review |
| --- | --- | ---: | --- |
| `cyberpunk-2013-2020` | corporate fortresses, street movements, classic edgerunners, early Net and urban action | 4 | named source set, legacy technology, exact history |
| `cyberpunk-2023-aftermath` | Fourth Corporate War and Night City catastrophe at close range | 5 | mass death, war, canon-event collision |
| `cyberpunk-2045-red` | reconstruction, scarcity, local power, Night Markets, Nomad logistics, high local agency | 2 | default; exact RED mechanics from owned rules |
| `cyberpunk-2070-edgerunners` | anime-era Night City, 2070 chrome and quickhacks, original crew after or beside published events | 4 | anime spoilers, Mission Kit scope, named-character distance |
| `cyberpunk-2077` | later Night City, braindance, dense corporate/gang conflict, game-era technology | 5 | game spoilers, protagonist outcomes, complete rules source |
| `cyberpunk-2077-phantom-liberty` | Dogtown espionage, NUS politics, shattered loyalties | 5 | expansion spoilers and named-character collision |
| `campaign-divergent` | one explicit changed event, institution, or technology premise | variable | branch point and downstream consequences |

Recommended first campaign: `cyberpunk-2045-red`. It is the official bridge between 2020 and 2077, supplies strong material constraints, and leaves more local future unsettled.

Source claims: `claim-cyberpunk-era-bridge`, `claim-cyberpunk-night-city-2045-release`.

## Spoiler And Famous-Character Choice

Choose separately for each selected work:

- no spoilers beyond broad premise
- broad setting and cast identities only
- events through a named episode, act, or mission
- full spoilers accepted
- published outcomes intentionally diverge at a recorded point

Then choose famous-character proximity:

- absent
- historical/background reference only
- distant contemporary rumor
- one sourced cameo with no solution authority
- direct intersection after targeted continuity design

The default is absent. Player franchise knowledge and character knowledge remain separate without punishing either.

## Sixteen Player Fantasies

| Fantasy | What players do | Best era/scale | Onboarding | Main caution |
| --- | --- | --- | ---: | --- |
| 1. Edgerunner or merc crew | take dangerous jobs while deciding which clients and costs remain acceptable | any sourced era; crew | 5 | do not reduce every session to combat or cash |
| 2. Neighborhood protectors | keep services and people safe without claiming ownership | 2045; district | 5 | avoid saviorism and protection rackets |
| 3. Fixer network | source goods, connect people, price risk, and maintain reputation | 2045; crew → district | 4 | access is not universal inventory |
| 4. Nomad convoy | transport, repair, negotiate routes, and protect a mobile community | 2045 or researched later era; regional | 4 | Nomads are not generic smugglers or bandits |
| 5. Media investigation | verify evidence, protect sources, publish, and survive retaliation | any sourced era; crew → city | 5 | publication is not automatic safety or truth |
| 6. Rockerboy movement | perform, organize, persuade, and turn audiences into action | 2013–2077 with era source; district → city | 4 | fame must not erase collective labor |
| 7. Tech/Medtech rebuild team | repair bodies and infrastructure while allocating scarce care | 2045; crew → district | 5 | body autonomy and triage require consent |
| 8. Netrunner/data-recovery crew | recover local data, map custody, and work across physical systems | era-specific; crew | 4 | no magic hacking or cross-era capability |
| 9. Corporate defectors/extraction team | move people, evidence, and families beyond employer control | any sourced era; crew → regional | 4 | do not treat a person as cargo or reward |
| 10. Trauma/security responders | answer crises while confronting contracts and unequal protection | era-specific; district | 3 | policing, healthcare, and coercive authority need limits |
| 11. Night Market operators | host, verify, protect, and reform a market under scarcity | 2045; district | 5 | markets affect hosts, workers, and patients |
| 12. Badlands couriers | cross damaged routes, serve settlements, and negotiate cargo obligations | 2045; regional | 4 | land is not empty and mobility has social infrastructure |
| 13. Law/security internal-affairs team | investigate misuse of force, data, dispatch, and contracts | era-specific; district → city | 3 | avoid competence fantasies built on state violence |
| 14. Orbital/Highrider campaign | navigate life support, labor, jurisdiction, and Earth-orbit supply | source-gated; global/orbital | 1 | requires a separate research and cultural pass |
| 15. 2070 quickhack crew | combine bodily and device intrusion with direct-connection operations | 2070s; crew | 3 | exact rules, consent, and target limits required |
| 16. Political/espionage team | manage sources, extraction, state claims, and fractured loyalties | 2077/Dogtown or researched era; city → regional | 2 | high spoilers, surveillance, and betrayal intensity |

Recommended default combination: fantasies 1, 2, and 7, with one member or contact drawing from 3, 5, 8, or 12. This creates a capable mixed crew without requiring everyone to be a professional mercenary.

## Crew Mandate Options

Choose one practical reason to work together:

- district infrastructure and emergency crew
- independent edgerunner team with a shared client rule
- neighborhood defense compact
- Fixer-backed problem-solving crew
- Night Market operating team
- Nomad convoy or city-route liaison team
- Media investigation and source-protection team
- Tech/Medtech salvage and care collective
- local data-recovery and systems team
- corporate extraction and resettlement crew
- responder or internal-affairs unit
- performance and organizing collective
- political/espionage cell under an explicit high-trust contract
- custom original mandate

A mandate assigns practical cooperation, not affection, morality, permanent membership, or permission for betrayal.

## Crew Scale

Default: three to five player characters.

Choose one opening scale:

- personal survival around one job
- crew reputation and one shared resource
- one district service or network
- mobile route between two endpoints
- citywide investigation after a slower onboarding
- regional, global, or orbital only after a separate scope pass

Ask:

- What can the crew decide without permission?
- What resource does it share?
- Who outside the crew depends on or contests that resource?
- What job will the crew refuse?
- What exit remains possible for a PC?
- What happens if the mandate ends?

## Physical Theater Choice

Select one from [Regions](regions.md):

- `cyberpunk-region-rebuilding-district`: best default balance
- `cyberpunk-region-port-industrial`: cargo, labor, factories, and security
- `cyberpunk-region-night-market`: brokerage, care, reputation, and verification
- `cyberpunk-region-zone-edge`: salvage, hazards, residents, and abandonment claims
- `cyberpunk-region-civic-executive`: contracts, unequal protection, and civic/corporate intrigue
- `cyberpunk-region-entertainment-media`: performance, reporting, and attention
- `cyberpunk-region-badlands-route`: convoys, settlements, repair, and mobility
- `cyberpunk-region-free-state-border`: source-gated jurisdiction and transport
- `cyberpunk-region-dogtown`: 2077/*Phantom Liberty* only
- `cyberpunk-region-global-orbital`: separate source pass required

Then select at most one connection layer:

- `cyberpunk-region-citinet-layer` for 2045
- `cyberpunk-region-quickhack-layer` for a sourced 2070s mode
- none

Never select both network layers for one opening.

## Canonical Versus Original Locale

Choose one:

- original sub-district or redevelopment parcel adjacent to canonical Night City geography
- named canonical district with selected source review
- Badlands/route campaign with named endpoints
- another real-world-derived Cyberpunk location after cultural and setting research
- campaign-original city inside an explicit divergent branch

For any original area, define:

- relationship to canonical districts
- population and community composition without stereotypes
- housing and displacement pressure
- livelihoods and shift rhythms
- utilities and service reliability
- transport and supply links
- security provider and response limits
- media and communications environment
- one public issue unrelated to the crew
- one reason no institution fully controls it

## Power Proximity Choice

Select no more than three or four active powers from [Factions](factions.md):

- district authority
- one megacorporate office
- one NeoCorp or contractor
- one Nomad transport unit
- one Fixer/Night Market network
- one gang
- one security provider
- one criminal operation
- at least one community or labor network
- one media/cultural network
- one technical custodian
- one state or interstate office after source review

At least one community or labor stakeholder is mandatory. A famous corporation is optional.

For each active power ask:

- Who can decide?
- What does it actually control?
- What does it need from others?
- Who inside disagrees?
- What can the crew refuse?
- Who bears the cost of its next action?

## Character Capability Choice

Use concepts rather than mandatory classes until rules are selected:

- combat and protection
- negotiation and brokerage
- repair and invention
- medicine and care
- Netrunning and systems
- driving and logistics
- investigation and media
- performance and organizing
- corporate or civic access
- survival and route knowledge
- stealth and extraction
- custom capability

No player must fill a tactical slot. A rules role, lifepath result, or videogame build never decides personality, politics, identity, or crew authority.

## Body And Cyberware Contract

Each player may choose, decline, or defer:

- body, appearance, presentation, and style
- organic, cybernetic, assistive, medical, occupational, expressive, or weaponized modifications
- whether cyberware is visible, concealed, removable, networked, or personally sensitive
- who installed, paid for, maintains, or claims rights over it
- therapy, medication, repair, and healthcare access
- whether employer-owned or debt-bound augmentation is in play
- desired portrayal of pain, maintenance, sensory difference, disability, and body horror
- whether hostile hacking of bodily systems is possible
- what information implants produce and who may access it
- whether full-body conversion is available under selected sources

Unanswered details remain unknown. No GM or random table may secretly assign forced modification, regret, cyberpsychosis, hidden ownership, or body history.

## Cyberpsychosis And Humanity Choice

Before using any Humanity or cyberpsychosis mechanic, decide:

- exact owned rules source
- what is mechanical pressure versus in-world belief or diagnosis
- who can observe a value or condition
- how therapy and care are portrayed
- what narration remains under player control
- whether violent loss of control is included
- which real-world mental-health analogies are forbidden
- how stigma, media, policing, and medical institutions respond
- what safety tool can redirect or veil an outcome

Never equate augmentation, disability, trauma, low empathy, or mental illness with inevitable violence or reduced personhood.

## Net And Information Choice

Choose one:

- 2045 CitiNet/local NET Architecture play
- 2070 quickhacking plus direct connection under selected rules
- minimal Net focus; data remains ordinary custody and devices
- deep Old NET, Blackwall, rogue AI, engram, or Soulkiller focus only after a dedicated source pass

Then define:

- what systems exist
- what requires physical access
- what can be reached remotely
- what bodily targets are eligible
- what logs or evidence intrusion creates
- how non-Netrunner characters remain active
- which effects require explicit player consent
- what a successful action cannot accomplish

## Rules And Resolution Choice

Default: system-neutral setting fiction. If using *Cyberpunk RED* for 2045, use an owned current rulebook and errata.

Decide:

- exact system and edition
- allowed official books and DLC
- roles, lifepaths, skills, and character creation
- combat, armor, injury, death, healing, and recovery severity
- economy, housing, lifestyle, Hustle, Fixer, and Night Market implementation
- cyberware, Humanity, therapy, and cyberpsychosis procedures
- Netrunning, Architecture, Agent, CitiNet, and quickhack procedures
- vehicle and chase procedures
- reputation, social, investigation, and invention mechanics
- house rules and whether they change fiction or procedure

This package supplies no copied rules, stat blocks, item catalogs, or proprietary tables.

## Tone Dials

Rate each from 0 (absent/background) to 3 (central/explicit):

- scarcity and survival
- community and rebuilding
- corporate exploitation
- street and gang politics
- state and security pressure
- workplace and labor conflict
- medical stakes and bodily autonomy
- cyberware/body horror
- cyberpsychosis themes
- Net intrusion and surveillance
- gun violence and lethality
- investigation and evidence
- media, performance, and public action
- crime and heists
- vehicle action and travel
- espionage and betrayal
- romance and sexuality
- humor, style, leisure, and hope
- famous-character/metaplot proximity

Dark tone never waives a player boundary.

## Safety Topics

Discuss lines, veils, opt-ins, and stop tools for:

- gun violence, death, gore, torture, captivity, and execution
- surgery, amputation, implants, body horror, forced augmentation, and cyberware removal
- disability, prosthetics, chronic pain, medication, therapy, and healthcare denial
- cyberpsychosis, mental illness, trauma, addiction, intoxication, and stigma
- hostile bodily hacking, mind alteration, braindance intimacy, memory, and compromised consent
- sex work, sexual content, romance, exploitation, and workplace coercion
- poverty, hunger, homelessness, displacement, debt, and unsafe labor
- gangs, organized crime, extortion, trafficking, smuggling, and incarceration
- policing, private security, raids, surveillance, borders, military and state violence
- war, terrorism, nuclear aftermath, contamination, and mass casualty
- racism, xenophobia, citizenship, migration, language, religion, and cultural representation
- family pressure, children, dependents, and community harm
- corporate ownership of bodies, identities, data, housing, and employment
- PvP, secret employers, betrayal, coercive contracts, and crew expulsion

No hidden PC romance, sexual history, pregnancy, family harm, mental-health diagnosis, addiction, cyberpsychosis, forced cyberware, employer ownership, betrayal, or secret identity may be introduced without that player's explicit agreement.

## Player-Authored Character Prompts

Each player may answer, decline, or defer:

- What is your name, identity, appearance, body, and presentation?
- What era and place shaped you?
- What style do you choose, and who recognizes it?
- What capability do you bring to the crew?
- What profession, role, or livelihood do you claim?
- What cyberware, assistive technology, or unaugmented capability do you choose?
- Who controls maintenance and data from your equipment?
- What community, family, employer, client, or route matters to you?
- What do you owe, and which debt do you reject?
- What line will you not cross for a job?
- What person or institution may call on you but not own you?
- What ambition do you want the campaign to engage?
- What reputation is accurate, exaggerated, false, or still unset?
- What tie do you want with another PC?
- What secret do you want in play, and who may know it?
- What part of your history remains private even from other players?
- What bodily, medical, romantic, family, or trauma context must remain under your control?

Unanswered prompts remain unknown, not invitations for GM invention.

## Crew Design Questions

- What practical need keeps the crew together now?
- What shared resource exists: workshop, vehicle, clinic access, market stall, channel, safehouse, contract, route, or reputation?
- Who outside the crew is affected by that resource?
- What requires unanimous consent?
- Who may accept a job?
- How are pay, salvage, care, and debt divided?
- How can a member refuse or leave?
- What intra-crew coercion, hacking, violence, or theft is forbidden?
- How are private scenes and secret information handled?
- What kind of betrayal is off-limits or opt-in only?

## Frame Choice

Choose one from [Campaign Frames](campaign_frames.md):

- `cyberpunk-frame-last-light`: default district infrastructure and supply conflict
- `cyberpunk-frame-market-ghost`: defective cyberware and Night Market accountability
- `cyberpunk-frame-open-channel`: Media/Rockerboy investigation and publication
- `cyberpunk-frame-broken-convoy`: Nomad logistics, rescue, and medical scarcity
- `cyberpunk-frame-clean-hands`: responder/internal-affairs contract investigation
- `cyberpunk-frame-shattered-loyalty`: source-gated 2077 Dogtown espionage
- custom original pressure using the operating model

Select exactly one. Present only its player-facing promise before acceptance.

## Knowledge And Privacy Choice

Decide separately:

- what all players know about the franchise
- what all PCs know about their era
- which district facts are common
- which corporate, gang, state, or Nomad claims need a holder
- whether false beliefs and propaganda are welcome
- how technical uncertainty is displayed
- which published outcomes are protected spoilers
- which PC facts remain player-private
- whether private information may create dramatic irony
- how a player may revise or withdraw a private hook

Use [Knowledge Layers](knowledge_layers.md) only after acceptance.

## Materialization Gate

Do not create or alter active campaign state until all are true:

- [ ] The user explicitly selected this Cyberpunk-universe package.
- [ ] The group confirmed it wants the franchise universe rather than a generic cyberpunk genre world.
- [ ] Era, continuity, and allowed source set are named.
- [ ] Spoiler ceiling and famous-character proximity are accepted.
- [ ] Rules system and mechanical source are accepted.
- [ ] One physical theater and at most one era-compatible connection layer are accepted.
- [ ] Campaign fantasy, crew mandate, crew size, and scale are accepted.
- [ ] Active powers and community stakeholders are accepted.
- [ ] Net, cyberware, healthcare, Humanity/cyberpsychosis, and body-autonomy policies are accepted.
- [ ] Tone dials, lethality, and safety boundaries are accepted.
- [ ] Player-authored fields remain open unless answered.
- [ ] One frame or custom local pressure is selected.
- [ ] Era/media-specific facts remain isolated.
- [ ] The user approves pruned materialization into the existing `campaign/` root.

Unselected options and prompts remain non-authoritative.
