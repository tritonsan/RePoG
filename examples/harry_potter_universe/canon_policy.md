# Harry Potter Universe Canon Policy

## Research Posture

This package uses a transparent evidence hierarchy rather than claiming that every work marketed under Wizarding World occupies one frictionless canon. The official public surfaces inspected for this research do not publish a complete arbitration rule that resolves every difference among novels, web writings, films, stage work, and games. The hierarchy below is therefore a RePoG research policy, not a quotation of an official canon decree.

The policy favors propositions that can be traced to public official sources, identifies commercial works bibliographically without reproducing them, and keeps media-specific presentation attached to its origin. Fan wikis, search snippets, recollection, theme-park implementation, merchandise, and unsourced social posts carry no authority here.

Source claims: `claim-harry-potter-universe-scope`, `claim-harry-potter-no-universal-canon-policy`, `claim-harry-potter-seven-books`.

## Source Hierarchy

| Priority | Source class | Package use | Conflict rule |
| --- | --- | --- | --- |
| 1 | Seven original Harry Potter novels | primary narrative and setting spine for `harry-potter-book-core` | explicit novel events outrank summaries and adaptation changes in book-core play |
| 2 | Author-attributed official setting writings on HarryPotter.com | supplemental history, institutions, customs, and limits | supplement silence; record tension rather than silently overwrite a novel |
| 3 | Official Harry Potter Encyclopedia/fact files and official publisher descriptions | concise public verification and discovery | useful summaries, not substitutes for full narrative context |
| 4 | Published companion works or screenplays selected and actually owned/read by the table | subject-specific expansion | source-gated; edition and media origin must be recorded |
| 5 | Harry Potter films and Fantastic Beasts films | screen-continuity events and presentation | adaptation-only details remain in their screen layer |
| 6 | *Harry Potter and the Cursed Child* | opt-in stage continuation | never back-propagated into book-core or earlier eras without acceptance |
| 7 | *Hogwarts Legacy* and other licensed games | opt-in interactive continuity and inspiration | gameplay systems and map compression never become automatic lore |
| 8 | Package-original and campaign-divergent material | bounded play scaffolding | labeled original or divergent; never represented as official canon |

A lower tier may provide a campaign's chosen primary continuity. Priority describes the default package policy, not the artistic worth of a medium.

## Continuity Modes

### `harry-potter-book-core`

The seven novels govern narrative history. Official setting writings may fill gaps when compatible. Film, stage, and game material require explicit import. This is the package default.

### `harry-potter-screen-hp`

The eight Harry Potter films govern visible events, casting-independent characterization, architecture, objects, and screen-specific chronology. Novel material may fill only accepted gaps; deleted scenes, production trivia, and theme-park design are not automatic facts. Source claims: `claim-harry-potter-screen-adaptations`.

### `harry-potter-screen-fantastic-beasts`

The selected Fantastic Beasts film or published screenplay governs only the dates, places, people, and events that work establishes. Broader 1920s–1940s history requires separately cited novel/web material or explicitly original campaign bridges; selecting this mode does not grant screen authority over an entire multi-decade band. It never retroactively makes every screen invention true in book-core campaigns. Source claim: `claim-harry-potter-fantastic-beasts-era`.

### `harry-potter-stage-cursed-child`

The official stage story governs a post-epilogue continuation centered on the next generation. Staging, cast, venue configuration, and revised production length are presentation data unless a selected script makes them fiction. Source claim: `claim-harry-potter-cursed-child-continuation`.

### `harry-potter-game-hogwarts-legacy`

The official game's nineteenth-century setting and accepted story facts govern. Combat frequency, cooldowns, inventory, talents, map density, fast travel, puzzle repetition, collectible placement, and player-avatar omnipotence remain gameplay abstractions. Source claim: `claim-harry-potter-legacy-1800s`.

### `harry-potter-campaign-divergent`

The campaign records a named divergence point and owns all consequences. Official material before that point remains evidence; later published outcomes are comparison material, not automatic corrections.

## Era Register

| Era id | Approximate band | Primary source posture | Package use | Main risk |
| --- | --- | --- | --- | --- |
| `harry-potter-era-secrecy-foundation` | 1692–1707 and institutional aftermath | official setting writings | Statute, government formation, hidden infrastructure | treating later institutions as timeless |
| `harry-potter-era-1800s` | nineteenth century | setting writings; optional Legacy layer | historical school, Ministry, transport, and social change | importing game loops or 1990s conditions |
| `harry-potter-era-fantastic-beasts` | dates established by the selected film/script; wider 1920s–1940s only with separate sources | selected Fantastic Beasts work plus separately cited setting history | international field teams and Grindelwald-period pressure | granting screen authority over unsourced decades |
| `harry-potter-era-first-war` | 1968–1981 | novel history and official summaries | resistance, Ministry strain, family and community survival | named-event determinism and trauma saturation |
| `harry-potter-era-interwar` | 1981–1991 | book-core background | recovery, denial, childhood, institutional memory | assuming peace erased prejudice or harm |
| `harry-potter-era-main-series` | 1991–1998 | seven novels or selected film continuity | school years and second conflict | retelling the published protagonists' plot |
| `harry-potter-era-postwar` | 1998–2017 | ending/epilogue, official post-war writings, bounded invention | reconstruction, reform, care, accountability | presenting invented recovery detail as canon |
| `harry-potter-era-stage-future` | 2017+ | Cursed Child stage layer when selected | next-generation family and institutional consequences | back-propagating time or stage devices |

The dates above are navigation bands. Exact day, office-holder, law, curriculum, technology, war status, and named-character position require selected sources. Source claims: `claim-harry-potter-era-chronology`, `claim-harry-potter-ministry-government`, `claim-harry-potter-azkaban-reform`.

## Default Continuity Decision

The proposed default, which remains inert until affirmative Session 0 acceptance, combines:

1. `harry-potter-book-core`
2. compatible public official setting writings
3. `harry-potter-era-postwar`
4. 2001 as a package-original campaign date, before the seven-novel epilogue
5. an epilogue-preserving future: established epilogue facts remain fixed unless the table records a divergence, but only facts relevant to current decisions are loaded
6. no automatic Harry Potter film, Fantastic Beasts, Cursed Child, or game import
7. no required appearance by a published character

The official anchors are deliberately narrow: official minister history records a 1998 political transition after Voldemort's death, Kingsley Shacklebolt's caretaker appointment and later election, and official writing describes post-war changes to Azkaban. The package does not claim a complete 2001 political program, curriculum, economy, or cast roster. Those remain campaign-instance decisions or targeted research. Source claims: `claim-harry-potter-1998-transition`, `claim-harry-potter-kingsley-postwar`, `claim-harry-potter-azkaban-reform`.

## Media Difference Protocol

For every imported proposition, record:

- continuity mode
- era and date range
- media origin
- source and claim id
- whether it is event, setting fact, presentation, mechanic, adaptation choice, or campaign invention
- confidence and unresolved tensions
- spoiler band
- mutability after acceptance

When sources differ:

1. Preserve both propositions with labels.
2. Ask which continuity governs the campaign.
3. Select one, reconcile explicitly, or create a divergence.
4. Record consequences instead of blending details invisibly.
5. Never use visual familiarity as proof that a detail exists in every medium.

## Fiction Versus Mechanics

The following require separate acceptance and may not be inferred from a game or adaptation:

- exact spell range, speed, cooldown, targeting, or damage
- unlimited inventory or instantaneous outfit changes
- repeated hostile populations and respawning creatures
- map compression, locked doors, fast travel, quest markers, and level gates
- talent trees, rarity colors, crafting recipes, and economy prices
- film-only architecture, costume, color, sound, or wand movement
- stage effects, actor doubling, scene compression, and auditorium-dependent events
- theme-park geography and visitor operations

A magical action in play must identify a method, practitioner, access, target, evidence, consequence, and limit. Source claims: `claim-harry-potter-potions-bounded`, `claim-harry-potter-wands-variable`, `claim-harry-potter-magic-not-universal-remedy`.

## Named Characters And Published Outcomes

Published people retain their established agency and consequences. They may be:

- absent
- historical context
- distant office-holders
- public names in press or records
- bounded contacts with a narrow mandate
- active figures only after explicit proximity and spoiler acceptance

They are never automatic patrons, rescuers, villains, teachers, relatives, or proof of PC importance. A campaign must not erase a published character's decisive action merely to hand it to a PC unless it declares a divergence.

## Spoiler Bands

| Band | Meaning | Examples of handling |
| --- | --- | --- |
| `S0` | premise-level setting | Hogwarts exists; magic is concealed |
| `S1` | early-series institutions and places | Diagon Alley, Houses, Ministry, Quidditch |
| `S2` | later-series conditions without outcomes | war pressure, contested institutions, advanced magic |
| `S3` | main-series outcomes | deaths, allegiances, final conflict, post-war offices |
| `S4` | Fantastic Beasts outcomes | identities, betrayals, Grindelwald-era resolutions |
| `S5` | Cursed Child outcomes | next-generation and stage-story revelations |
| `S6` | Hogwarts Legacy outcomes | game plot, ancient-magic story, companion outcomes |

The package default uses `S3` because post-war play assumes the main-series ending. A table wanting `S0`–`S2` must choose another era or a spoiler-safe divergent recovery premise.

## Social And Cultural Guardrails

- Blood status is a supremacist social classification, not an objective measure of magical value.
- House affiliation is not a moral caste or personality test.
- Squibs and Muggle-born people are not lesser magical-community members.
- Werewolf status may involve danger under specific conditions, but it does not establish permanent moral corruption.
- Goblins, centaurs, house-elves, and other beings have interests and agency; they are not encounter categories or comic property.
- House-elf bondage is not normalized by cheerful presentation. A table must decide whether it is foregrounded, changed, resisted, or excluded.
- Coercive magic, memory alteration, prison conditions, child endangerment, torture, and institutional discrimination require explicit boundaries.
- A school campaign must define adult responsibility and may not use minors to excuse sexualization or unchecked authority abuse.
- Magical transformation, ancestry, names, bodies, or pronouns may not be used to invalidate a participant's real identity.
- No fictional category is a universal metaphor for a real marginalized group without that group's participants choosing the comparison.

Source claims: `claim-harry-potter-blood-ideology`, `claim-harry-potter-squib-access`, `claim-harry-potter-werewolf-stigma`, `claim-harry-potter-house-elf-bondage`, `claim-harry-potter-goblin-agency`.

## Real-World Attribution Boundary

The package records authors, publishers, studios, and official sites as provenance. Attribution identifies where a proposition came from; it is not endorsement of a creator's statements or conduct. Real-world controversy is not imported as lore. Session 0 may include an out-of-fiction decision about whether and how participants want to engage with the property, without requiring anyone to debate or disclose personal identity.

## Claim And Confidence Protocol

Every official proposition must resolve to a `claim-harry-potter-*` entry in [Source Provenance](source_provenance.md). Each claim records one or more `src-harry-potter-*` sources and a confidence statement.

- **High:** explicit on an inspected official public page.
- **Medium:** broad synthesis across official surfaces, bibliographic identification without full-text review, or chronology requiring selected works.
- **Low:** insufficient for operational use; research before materialization.
- **Package-original:** design proposal, not an official claim.

Absence from a sitemap or public page is not proof that a fact is false. Search snippets and inaccessible commercial text are not silently promoted to evidence.

## Divergence Record

For every accepted divergence, preserve:

- divergence id and date
- selected continuity and era
- official proposition being changed
- campaign replacement
- reason and player consent
- downstream institutions, relationships, laws, and knowledge affected
- whether the change is public, restricted, or secret
- whether later official material will be ignored, compared, or selectively adopted

A divergence is a campaign truth, never an edit to this reusable package.
A fictional divergence cannot activate an unselected package proposal, alter another player's exclusive or private fields, collapse GM/player knowledge boundaries, or waive a safety limit. Only the affected participant may grant narrow, explicit permission over their own authored material, recorded separately from the divergence.