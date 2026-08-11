# Harry Potter Universe Knowledge Layers

## Purpose

This file separates setting truth from what players, PCs, institutions, sources, and the GM actually know. A canonical proposition is not automatically common knowledge. A published event may be a spoiler. A newspaper report is evidence of publication, not proof of every assertion. A game interface is never character knowledge.

## Visibility Taxonomy

| Layer | Meaning | Default holders | Player treatment |
| --- | --- | --- | --- |
| `P0` | public premise | most magical-community participants | may appear in the pitch |
| `E0` | selected-era baseline | people plausibly socialized in that era | explain before a decision depends on it |
| `L1` | local lived fact | residents, workers, students, or users | discover through relationships and observation |
| `R2` | rumor or contested account | named communities or publications | label source and uncertainty |
| `I3` | institutional information | bounded office, school, hospital, bank, or press desk | access requires role, trust, request, or process |
| `A4` | restricted specialist knowledge | trained practitioner or authorized custodian | require method and source |
| `S5` | published-event spoiler | table after accepted spoiler band | never reveal above ceiling |
| `F6` | selected frame truth | GM layer and justified evidence holders | reveal only through listed requirements |
| `C7` | campaign consequence | actual witnesses and records | update after play; no retroactive omniscience |
| `PP` | player-private fact | player and explicitly approved holders | never infer, expose, or weaponize without consent |

`S5` is a visibility class, not the spoiler-band number. Preserve both fields.

## Fact Cards

### `harry-potter-fact-secrecy-001`

- **Proposition:** Magical Britain operates under an international concealment regime that shapes law, travel, settlement, sport, and contact with non-magical people.
- **Default layer:** `P0`
- **Spoiler:** `S0`
- **Claims:** `claim-harry-potter-secrecy`
- **Caution:** exact detection, penalties, and response belong to era and jurisdiction.

### `harry-potter-fact-government-001`

- **Proposition:** The British Ministry of Magic was formally established in 1707 and governs magical affairs through an elected Minister and departments.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-ministry-government`
- **Caution:** exact office-holder and department practice are date-specific.

### `harry-potter-fact-law-001`

- **Proposition:** The Wizengamot is publicly described as combining high-court and legislative functions.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-wizengamot`
- **Caution:** do not infer a complete constitution or trial code.

### `harry-potter-fact-law-002`

- **Proposition:** Aurors are specialist Ministry law-enforcement practitioners focused on dangerous dark magic and apprehension.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-aurors`
- **Caution:** authority, staffing, and procedure vary by era.

### `harry-potter-fact-prison-001`

- **Proposition:** Azkaban's use and guard regime changed across history; official post-war writing describes Dementors being removed and rotating Aurors guarding it.
- **Default layer:** `S5`
- **Spoiler:** `S3`
- **Claims:** `claim-harry-potter-azkaban-reform`
- **Caution:** prison conditions and legal process require safety and source review.

### `harry-potter-fact-school-001`

- **Proposition:** Hogwarts is a British magical school whose education, Houses, staff, student life, and traditions are central to the core stories.
- **Default layer:** `P0`
- **Spoiler:** `S0`
- **Claims:** `claim-harry-potter-hogwarts-education`
- **Caution:** curriculum, staff, access, and safety are era-specific; House is not personality destiny.

### `harry-potter-fact-schools-001`

- **Proposition:** Multiple wizarding schools exist internationally, with different locations, student populations, and traditions.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-international-schools`
- **Caution:** research the selected school rather than inventing national stereotypes.

### `harry-potter-fact-commerce-001`

- **Proposition:** Diagon Alley is a concealed London center for magical shopping, supplies, services, and access to institutions such as Gringotts.
- **Default layer:** `P0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-diagon-commerce`
- **Caution:** exact shops and owners vary by date and continuity.

### `harry-potter-fact-settlement-001`

- **Proposition:** Hogsmeade is a magical village associated with Hogwarts, residents, businesses, and approved student visits in relevant eras.
- **Default layer:** `P0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-hogsmeade`
- **Caution:** do not import every named business or route without sources.

### `harry-potter-fact-bank-001`

- **Proposition:** Gringotts is a goblin-owned and operated wizarding bank in Diagon Alley with deep secured vaults and goblin-controlled operations.
- **Default layer:** `P0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-gringotts`
- **Caution:** public reputation does not grant PCs access or define exact law.

### `harry-potter-fact-care-001`

- **Proposition:** St Mungo's is a hidden London hospital staffed by Healers for magical maladies and injuries.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-healing`
- **Caution:** magic is not universal cure or diagnostic certainty.

### `harry-potter-fact-transport-001`

- **Proposition:** Floo travel uses regulated connected fireplaces and is useful for travelers who cannot or should not use other methods.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-transport`
- **Caution:** connection, permission, articulation, and destination still matter.

### `harry-potter-fact-press-001`

- **Proposition:** The Daily Prophet has broad British circulation but may sensationalize or yield to governing influence.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-press`
- **Caution:** each article remains a sourced in-world account.

### `harry-potter-fact-potions-001`

- **Proposition:** Potions require magic and skilled process; some produce distinctive effects and may be difficult to undo.
- **Default layer:** `A4`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-potions-bounded`
- **Caution:** exact formula, timing, effects, and antidotes require the selected source.

### `harry-potter-fact-wands-001`

- **Proposition:** Official wandlore distinguishes woods, cores, lengths, and flexibilities, but descriptions do not license deterministic personality or morality claims.
- **Default layer:** `A4`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-wands-variable`
- **Caution:** player identity and values cannot be inferred from a wand.

### `harry-potter-fact-blood-001`

- **Proposition:** Pure-blood classification is an in-world ancestry ideology associated with exclusion and supremacist politics, not proof of magical worth.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-blood-ideology`
- **Caution:** do not reproduce slurs or assign labels without consent.

### `harry-potter-fact-squib-001`

- **Proposition:** Squibs are born into magical families without manifesting magic and can face exclusion from institutions they can still perceive and inhabit.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-squib-access`
- **Caution:** inability to cast does not remove agency, knowledge, or community membership.

### `harry-potter-fact-werewolf-001`

- **Proposition:** Werewolves have faced stigma, unreliable registration, confused policy, and exclusion; moral character while human is not determined by lycanthropy.
- **Default layer:** `I3`
- **Spoiler:** `S2`
- **Claims:** `claim-harry-potter-werewolf-stigma`
- **Caution:** private status and transformation safety require consent protocols.

### `harry-potter-fact-house-elf-001`

- **Proposition:** House-elves are intelligent domestic beings magically bound under coercive service arrangements in the core setting.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-house-elf-bondage`
- **Caution:** obedience is not proof of consent; do not use servitude as comic furniture.

### `harry-potter-fact-goblin-001`

- **Proposition:** Goblins are intelligent makers and institutional actors with ownership concepts that can conflict with wizard inheritance practice.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-goblin-agency`
- **Caution:** no goblin speaks for all goblins.

### `harry-potter-fact-sport-001`

- **Proposition:** Quidditch supports international competition, governance, mass travel, media, safety, protest, and logistical pressure.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-quidditch-international`
- **Caution:** exact teams, results, and rules are source- and date-specific.

### `harry-potter-fact-era-001`

- **Proposition:** Nineteenth-century, Fantastic Beasts-era, main-series, post-war, and stage-future material cannot be treated as one simultaneous present.
- **Default layer:** `P0`
- **Spoiler:** `S0`
- **Claims:** `claim-harry-potter-era-chronology`
- **Caution:** set exact continuity and year before play.

### `harry-potter-fact-media-001`

- **Proposition:** Film design, stagecraft, and game mechanics belong to their media layers unless explicitly imported.
- **Default layer:** `P0`
- **Spoiler:** `S0`
- **Claims:** `claim-harry-potter-screen-adaptations`, `claim-harry-potter-cursed-child-continuation`, `claim-harry-potter-legacy-1800s`, `claim-harry-potter-technology-separation`
- **Caution:** visual familiarity is not cross-continuity evidence.

### `harry-potter-fact-daily-001`

- **Proposition:** Magical daily life combines distinctive dress, print and owl communication, hidden travel, commerce, work, sport, family, and selective use or avoidance of non-magical technology.
- **Default layer:** `E0`
- **Spoiler:** `S1`
- **Claims:** `claim-harry-potter-daily-life`, `claim-harry-potter-technology-separation`
- **Caution:** practices vary by era, household, class, and individual.

## Selected-Frame Truth Register

| Frame truth id | Default holders | Reveal gate | Safe player-facing category |
| --- | --- | --- | --- |
| `harry-potter-frame-mended-network-secret-001` | GM; surviving route collaborators | pattern + household testimony + record | legacy routing conflict |
| `harry-potter-frame-fifth-table-secret-001` | GM; former sponsor or records specialist | reproduction + charter + dual expertise | access ward mismatch |
| `harry-potter-frame-quiet-ward-secret-001` | GM; supplier and specific brewers | patient pattern + substitution evidence + testimony | undocumented supply change |
| `harry-potter-frame-ink-before-dawn-secret-001` | GM; source and draft custodians | document comparison + confirmation + witness consent | incomplete genuine leak |
| `harry-potter-frame-borrowed-key-secret-001` | GM; ledger custodians | both ledgers + maintenance record + representation | incompatible custody histories |
| `harry-potter-frame-lantern-delegation-secret-001` | GM; contractor and caretaker | migration evidence + ward record + controlled comparison | displaced habitat route |

Only the selected row enters GM memory. The safe category may guide foreshadowing; it is not the solution.

## Evidence Contract

For every consequential assertion, record:

- proposition
- actual holder
- acquisition method
- medium or trace
- date and era
- continuity and media origin
- direct observation, expert interpretation, institutional record, publication, rumor, or inference
- reliability and possible incentive
- who may be endangered by disclosure
- what would corroborate or falsify it

Magic may authenticate a mark, reveal a trace, or compel behavior only if the selected source and consent policy support that capability. It does not automatically explain context or make testimony ethically publishable.

## Rumor Contract

A rumor must have:

- a speaker or community
- a reason to believe or repeat it
- one accurate element
- one uncertainty, omission, or distortion
- a possible cost if repeated
- no automatic conversion into GM truth

Do not use rumor to smuggle unsupported canon into the campaign.

## Institutional Knowledge

A Ministry, school, hospital, bank, or newspaper does not know everything held anywhere under its name. For each institutional fact, identify:

- exact office or custodian
- record system and access rule
- who entered or interpreted it
- whether it survived war, reform, transfer, or media change
- who disputes it
- what practical action the holder can take

## Player-Private Boundary

`PP` facts include identity, body, disability, family, ancestry, House feelings, private relationships, trauma, fears, secret knowledge, and any requested private context. They remain under player control. The GM may not reveal a `PP` fact through Legilimency, Veritaserum, prophecy, a magical object, family archive, Sorting, wand behavior, transformation, or institutional record unless the player explicitly accepted that specific possibility.

## Update Procedure

After each consequential scene:

1. Add or revise only campaign facts actually established.
2. Record current holders rather than making the whole party omniscient.
3. Preserve source/claim ids for official propositions.
4. Mark frame revelations against their requirements.
5. Separate public report from objective event.
6. Keep player-private facts private.
7. Do not write new events back into this reusable package.