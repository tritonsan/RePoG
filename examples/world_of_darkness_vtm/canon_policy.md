# World of Darkness: Vampire: The Masquerade Canon Policy

## Research Posture

This package supports current V5 play without pretending that every edition, splat, novel, video game, city book, and adaptation forms one frictionless chronology. It prefers broad, play-relevant structures over exact officeholders, exhaustive bloodlines, or one universal supernatural cosmology.

Research snapshot: 2026-07-23. Official Paradox/World of Darkness pages and public Renegade product descriptions were inspected. Full commercial rulebooks and sourcebooks were not independently re-read during this pass. Fine mechanical, city-specific, and legacy-cosmology claims therefore remain narrower in confidence than advertised themes and product scope.

## Default Selection

- Continuity: `wod5-v5-current`
- Era: `contemporary-date-unset`
- Locale mode: `original-city-canon-adjacent`
- Playable scope: `vampire-only-coterie`
- Sect posture: `locally-negotiated`
- Metaplot intensity: `background-mutable`
- Other-supernatural detail: `bounded-and-perspective-limited`
- Exact date, city, and country: unset
- Famous-character dependence: forbidden by default

`original-city-canon-adjacent` permits original local people and events that obey selected V5 structures without secretly causing, replacing, or resolving published metaplot. Accepted campaign history outranks later package updates.

## Source Hierarchy

| Rank | Source layer | Default use | Limit |
| --- | --- | --- | --- |
| 1 | V5 Core Rulebook and current official VTM errata | Vampiric condition, Hunger, Humanity, Masquerade, character and coterie foundations | Owned text must be checked for exact mechanics; this package does not reproduce rules |
| 2 | Current V5 Players Guide | Consolidated current clan menu, coterie options, thin-blood and non-traditional chronicle support | Does not make every option locally common or accepted by a sect |
| 3 | Current official V5 sect and subject sourcebooks | Camarilla, Anarch, Sabbat, Second Inquisition, blood craft, Gehenna War, and selected city detail | Applies only to the subject and edition selected; antagonist books do not silently create PC options |
| 4 | Current official World of Darkness / Paradox framing | Franchise identity, current line positioning, and broad themes | Marketing summaries do not settle fine lore disputes |
| 5 | Legacy VTM editions and V20 | Opt-in history, tone, bloodlines, locations, and unresolved gaps | Never imported silently; edition conflicts must be recorded |
| 6 | W5 and H5 | Non-player context for Garou, spirits, and mortal hunters | Separate games; no player-character or mechanic import by default |
| 7 | Legacy Mage, Wraith, Changeling, Demon, Mummy, and other World of Darkness lines | Rumor, bounded NPC context, and research leads | No unified cosmology; operational use requires a focused source pass |
| 8 | Screen, interactive, actual-play, and other licensed adaptations | Opt-in presentation or adaptation continuity | Does not override tabletop V5 unless explicitly selected |
| 9 | RePoG package-original content | Original city, district, local offices, actors, clocks, frames, and hidden truths | Playable proposal only; not franchise canon |

Explicit user choices, boundaries, and accepted campaign history outrank this hierarchy for that campaign.

## Continuity Modes

| Mode | Meaning | Default |
| --- | --- | --- |
| `wod5-v5-current` | Current VTM 5th Edition assumptions, with only selected current supplements active | Yes |
| `v5-named-city` | V5 plus one named published city and its source-specific officeholders | No; targeted research required |
| `v5-plus-selected-legacy` | V5 foundation with named legacy claims imported individually | No; every import needs origin and conflict review |
| `v20-legacy` | V20 or another named legacy edition governs the chronicle | No; requires a separate operating-model pass |
| `adaptation-specific` | A named game, show, actual-play, or other adaptation governs visible continuity | No; adaptation must be named |
| `campaign-divergent` | The group knowingly changes one or more selected premises | No; divergence point must be recorded |

Do not use `v5-plus-selected-legacy` as permission to import whatever is convenient. List each legacy source, proposition, and consequence.

## Edition And Family Separation

### V5 Versus Legacy VTM

V5 advances and revises the setting, changes mechanics and emphasis, and redistributes some clan and sect material across current books. Legacy material may inspire a campaign, but a legacy title, bloodline, office, Discipline expression, or metaplot event is not current V5 merely because it shares a name.

### World Of Darkness Versus Chronicles Of Darkness

*Chronicles of Darkness* and *Vampire: The Requiem* are separate game lines with different metaphysics, factions, terminology, and assumptions. They are excluded. Importing a Requiem concept requires an adaptation decision, not a canon claim.

### V5, W5, And H5

V5, W5, and H5 share current World of Darkness branding, but each establishes its own playable perspective. W5's Garou and H5's mortal hunters remain non-player here. Shared branding does not guarantee that every cosmological statement is objective, complete, or mutually known.

Source claims: `claim-wod-vtm-franchise-scope`, `claim-wod-vtm-contemporary-metaplot`, `claim-wod-w5-separate`, `claim-wod-h5-separate`, `claim-wod-legacy-lines`, `claim-wod-cofd-separate`.

## Default Era And Metaplot Menu

| Era or intensity | Play promise | Collision risk | Required action |
| --- | --- | ---: | --- |
| `contemporary-date-unset` | Present-day tools and pressures without a fragile calendar | Low | Default; define technology actually present at the table |
| `post-shake-up-local` | Elders absent or distracted, Camarilla retrenchment, Anarch opportunity, hunter pressure | Medium | Select only the local consequences needed |
| `named-v5-date` | Exact year tied to current publications | Medium | Verify every time-sensitive product and officeholder |
| `gehenna-war-active` | Elders, secret societies, diablerie temptation, and action conflict | High | Select Gehenna War sources and an explicit spoiler/intensity contract |
| `legacy-era` | A named earlier-edition city or metaplot interval | High | Make the legacy edition primary for that branch |
| `campaign-divergent` | A chosen sect victory, failed Masquerade, changed clan status, or altered metaplot | Variable | Record the branch point and downstream uncertainties |

The default treats Beckoning and Gehenna War as reports with local consequences, not an order to remove every elder or stage an apocalypse.

## Template-Fixed Boundaries

Unless Session 0 selects a divergence:

- Player characters are VTM vampires in one coterie-scale chronicle.
- Vampires depend on blood, operate primarily at night, and face grave danger from sunlight and fire.
- Hunger and the Beast make predation and power use consequential rather than cosmetic.
- Humanity, Convictions, and Touchstones keep moral and relational choices in play without assigning a player's feelings.
- The Masquerade conceals vampire existence and turns mortal evidence into political danger.
- Feeding access, havens, domain, boons, status, and secrecy create local power.
- Camarilla, Anarch, independent, thin-blood, and other Kindred positions are internally diverse.
- Sabbat is antagonist-first under the inspected V5 source.
- Current technology creates both useful cover and persistent evidence; it does not grant either vampires or hunters omniscience.
- The Second Inquisition is a label for dangerous, partly hidden hunter forces, not one perfectly coordinated global hive mind.
- Caine, Antediluvians, Gehenna, and many ancient accounts remain belief, disputed evidence, or perspective-bound lore until a campaign makes a specific truth decision.
- Other supernatural beings may exist, but their own cosmologies do not automatically become objective truth or PC knowledge.
- Published protagonists and officeholders retain published agency unless a divergent campaign explicitly changes it.

Source claims: `claim-wod-vtm-vampire-condition`, `claim-wod-vtm-hunger-humanity`, `claim-wod-vtm-kindred-masquerade`, `claim-wod-vtm-domain-boons`, `claim-wod-vtm-touchstones-convictions`, `claim-wod-vtm-digital-risk`, `claim-wod-vtm-noddist-myth`.

## Clan Scope Policy

The current menu contains fourteen clan presentations across the Core Rulebook and Players Guide, plus Caitiff and thin-blood options. The package uses clans as lineages, inherited pressures, social expectations, and character prompts—not personality templates or mandatory political parties.

- A clan does not determine ethnicity, nationality, gender, sexuality, class, profession, morality, or sect.
- A clan stereotype is an in-world claim held by a speaker, not neutral narration.
- Bane, Compulsion, Discipline, Blood Potency, generation, and character-creation details must come from owned current rules.
- Salubri rarity, Caitiff marginalization, and thin-blood treatment must be instantiated locally rather than assumed identical everywhere.
- No player receives a sire, clan secret, blood bond, lineage duty, or hidden diablerie without consent.

Source claims: `claim-wod-vtm-clans-current`, `claim-wod-vtm-coterie-play`, `claim-wod-vtm-thin-bloods`.

## Sect Policy

- **Camarilla:** usable as patron, polity, employer, refuge, rival, or oppressor; its Masquerade claim and neo-feudal structure do not make every court identical.
- **Anarch Movement:** usable as decentralized local authority, coalition, neighborhood project, or contested promise of freedom; it is not automatically egalitarian or leaderless.
- **Sabbat:** antagonist-first. A Sabbat coterie requires explicit campaign divergence, owned source review, and stronger consent around dehumanization, coercion, cult abuse, and atrocity.
- **Autarkis and independents:** valid positions with practical costs; neutrality does not erase domain, feeding, or hunter pressure.
- **Ashirra and culturally specific institutions:** may be used only with relevant current sources and cultural review; they are not interchangeable with a generic Camarilla reskin.

Source claims: `claim-wod-vtm-camarilla`, `claim-wod-vtm-anarch`, `claim-wod-vtm-sabbat-antagonists`.

## Other-Supernatural Policy

Use the minimum fact needed for the vampire chronicle.

| Presence | Default status | Permitted assertion before targeted research |
| --- | --- | --- |
| Garou and spirits | Current W5 non-player context | Some Garou fight a desperate environmental and spiritual war; their motives and spirit relations are not reducible to vampire categories |
| Mortal hunters | Current H5 context plus V5 Second Inquisition | Human cells and institutions may hunt monsters for different reasons and with incomplete knowledge |
| Ghosts and the dead | VTM overlap plus legacy Wraith context | The dead may persist or be contacted in some stories; no complete afterlife map is assumed |
| Mages and sorcerers | Legacy/contextual | Some occult humans may wield capabilities vampires misunderstand; no universal power list or cosmology is assumed |
| Changelings and fae | Legacy/contextual | Strange beings tied to dream, story, or other hidden realities may appear only after focused research |
| Demons, mummies, and others | Legacy/contextual | Their existence, identity, and capabilities remain unset until selected |

Never reveal a non-player creature's true nature merely because the players recognize the franchise. Never convert it into a PC option inside this package.

## Myth And Cosmology Policy

The *Book of Nod* is explicitly presented as an in-world mythic collection. Treat Noddist accounts as texts with believers, interpreters, rivals, fragments, and political uses. A campaign may decide that one claim is true, false, symbolic, manipulated, or unknowable, but that decision is campaign-instance and visibility-bound.

When splat cosmologies disagree:

1. identify the speaker and source
2. separate observation from interpretation
3. prefer bounded uncertainty over harmonization
4. decide only what the current vampire story requires
5. record who can know the decision
6. keep other lines' mysteries out of player-facing common knowledge

Source claims: `claim-wod-vtm-noddist-myth`, `claim-wod-w5-separate`, `claim-wod-legacy-lines`.

## Conflict Resolution

When sources disagree:

1. Check whether they belong to different game families.
2. Check edition, publication date, and selected continuity.
3. Prefer current V5 core/errata for V5 mechanics and broad condition.
4. Prefer the current subject sourcebook for its advertised domain.
5. Do not let a legacy detail silently fill a V5 silence.
6. Treat in-world testimony and myth as claims, not narrator truth.
7. Ask the user when the choice changes playable identity, campaign promise, or safety profile.
8. Record the ruling, source ids, confidence, mutability, and visibility.

Silence is not contradiction. Package-original local content may occupy blank space but may not claim secret authorship of a published event.

## Naming, City, And Date Policy

- Do not invent an exact year merely to look current.
- Do not select a real city without deciding how closely real institutions, neighborhoods, and harms will be represented.
- Prefer an original city for the default; define climate, night economy, transit, inequality, surveillance, and jurisdiction during Session 0.
- Do not name a Prince, Baron, Sheriff, Primogen, Harpy, Hound, cult, hunter unit, or famous elder until the opening needs that office and the local polity supports it.
- Label every invented proper noun as campaign-instance or package-original until accepted.
- A modern device is not automatically present, networked, hackable, or monitored; instantiate its actual custody and data path.

## Spoiler Policy

| Spoiler band | Default treatment |
| --- | --- |
| Broad vampire premise, Masquerade, Hunger, sect names | Player-safe after VTM selection |
| Current clan menu and broad identities | Player-safe; exact mechanics require owned rules |
| Local court, domain, hunter, and coterie secrets | Restricted by actual holders |
| Named-city metaplot and published-character outcomes | Protected until that source is selected |
| Beckoning and Gehenna War specifics | Background-only or protected unless high-metaplot play is accepted |
| Noddist claims | Presented as in-world belief, never unmarked objective truth |
| Other-supernatural identities and cosmology | Protected and perspective-limited |
| Frame hidden truths | GM-only until their reveal gates are met |
| PC interiority and private history | Player-private until the originating player changes access |

## Safety And Cultural Guardrails

- Feeding is an act involving bodies, consent, power, and risk; never reduce mortals to scenery or refill stations.
- Do not use supernatural coercion to bypass a player's sexual, romantic, or bodily boundaries.
- Establish whether feeding scenes fade to black, remain abstract, or become explicit.
- Distinguish addiction metaphor from real-world substance use; do not force a player's lived experience into allegory.
- Blood bonds, ghouling, Dominate-like control, memory alteration, imprisonment, and abusive sire relationships require explicit boundaries.
- Humanity mechanics do not authorize the GM to declare a player's real morality or emotions.
- Mental illness is not a monster aesthetic or a synonym for Malkavian identity.
- Clan and sect stereotypes must not become ethnic, religious, disability, class, gender, or sexuality stereotypes.
- Hunters and law-enforcement-like institutions must not make real-world surveillance, policing, torture, or state violence consequence-free.
- Give mortal communities goals, competence, and refusal; vampires are protagonists, not moral owners of the city.
- Define PvP, frenzy risk, compulsory feeding, betrayal, haven invasion, and Final Death expectations before play.

Source claim: `claim-wod-vtm-mature-content`.

## Open Uncertainties

Before strict use, verify from the selected owned books:

1. Exact Hunger, frenzy, Humanity, Stain, remorse, torpor, healing, and Final Death procedures
2. Exact clan Banes, Compulsions, Disciplines, and character-creation options
3. Local legality and social meaning of Embrace, domain, feeding, boons, Blood Bonds, ghouls, and diablerie
4. The selected city's current sect offices and named metaplot actors
5. Exact Second Inquisition capabilities, data access, equipment, and response doctrine
6. Blood Sorcery, Oblivion, Thin-Blood Alchemy, rituals, ceremonies, and artifacts central to a solution
7. Gehenna War factions, elder identities, and Beckoning claims used operationally
8. Any Sabbat player option or Path-centered chronicle
9. Any Garou, spirit, ghost, mage, fae, demon, mummy, or other non-vampire capability
10. Cultural context for Ashirra, Banu Haqim, Ministry, Hecata families, Ravnos, or a real-world religious/ethnic community
11. Product changes published after the 2026-07-23 snapshot

The announced *Tradition of Destruction* release dated 2026-08-05 was not yet available at the snapshot and supplies no claims here.

## Campaign Divergence Record

Every accepted divergence should preserve:

- divergence id
- selected continuity and source set
- exact branch point
- source claim being changed
- user decision and date
- playable-scope impact
- immediate and downstream consequences
- facts made uncertain
- visibility and holders
- safety review result

A divergence changes only the materialized campaign. It never rewrites this reusable package.
