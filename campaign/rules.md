# Rules And Rulings

This file stores table rules, optional dice procedures, recurring rulings, and
campaign-specific mechanics.

## Core Approach

Codex handles ordinary fictional positioning directly. Use deterministic rules
only when they improve fairness, tension, or continuity.

## Stat Scale

Default stats use a 1 to 5 scale:

- 1: weak or unreliable.
- 2: ordinary but usable.
- 3: capable and dependable.
- 4: exceptional.
- 5: elite or defining.

Default stats:

- Power
- Agility
- Endurance
- Technique
- Perception
- Wits
- Presence
- Will

## Starting Level Budgets

- Beginner: 16 points, recommended max 3.
- Competent: 20 points, recommended max 4.
- Advanced: 24 points, recommended max 4.
- Elite: 28 points, recommended max 5.

Campaigns may rename tiers to match the setting. Keep the numeric limits clear.

## Stat Use And Opposition Model

Stats are not only for the player. Use the same 1 to 5 scale for T2+ NPCs,
companions, major antagonists, important faction faces, and significant
obstacles.

Use stats as fictional capability anchors:

- 1: usually fails without help, leverage, time, or favorable conditions.
- 2: handles ordinary pressure but struggles against specialists.
- 3: reliable professional capability.
- 4: exceptional local or regional capability.
- 5: elite, defining, or campaign-stage-significant capability.

When an action faces resistance, identify:

- the player's relevant stat and capability;
- the opposition stat, obstacle difficulty, or faction capability;
- any leverage, preparation, tools, knowledge, injury, exhaustion, surprise, or
  positional advantage;
- what clean success, partial success, and failure mean in the fiction.

Do not let special capabilities erase stats. A special capability changes what
is possible and which stat matters, but it still has limits, counters, and
fictional requirements.

## Campaign Stage And Power Bands

Calibrate stats to the current campaign stage. In a long campaign, early
ordinary NPCs should not be built like endgame threats.

Default bands:

- Incidental: most stats 1 to 2; rarely one 3.
- Local professional: one main stat 3; supporting stats 1 to 2.
- Local elite / serious obstacle: one main stat 4; clear weak areas remain.
- Regional threat: several 3 to 4 stats; rarely one 5.
- Legendary / endgame: 5 only when the campaign stage supports it.

Companions can have future potential, but their current stats should fit the
present stage. Growth should be recorded through advancement, not assumed at
creation.

## Obstacle Difficulty

Important obstacles should have a difficulty note:

- Trivial: should pass unless something unusual interferes.
- Routine: succeeds with fitting stat/capability or enough time.
- Challenging: requires a relevant strength, preparation, leverage, or risk.
- Hard: requires strong stat/capability plus leverage or a costly approach.
- Extreme: beyond current stage unless the player finds a major advantage.

Record which stat applies, why the difficulty fits this campaign stage, and
what each outcome changes.

## Special Capabilities

Special capabilities are setting-specific. They may be powers, expertises,
social authorities, technologies, techniques, professions, or other unusual
advantages.

Every special capability needs:

- what it does;
- its limit;
- its cost or risk;
- when it does not help;
- how it can create story trouble;
- what can counter it.

No special capability is unlimited.

## Advancement And Rewards

Use `progression.md` for advancement cadence, closure levels, reward pools,
OOC upgrade check-ins, balance checks, and companion advancement. Use
`arc_closure.md` to record actual closure reviews and chosen upgrades.

Default stance:

- session closure may give a minor adjustment or short-term edge;
- scenario closure may offer a meaningful player-chosen upgrade;
- arc closure should change both the character and the world;
- companions or allied NPCs can advance when they meaningfully participated or
  changed;
- every durable upgrade needs a fiction source, limit, cost, or consequence.

## Dice

Dice are optional. Record one Session 0 mode:

- `judgment_only`: no routine rolls; resolve from positioning and capability.
- `player_rolls`: the player rolls and reports the result.
- `open_gm_rolls`: RePoG rolls and shows the expression and result.
- `hidden_gm_rolls`: RePoG may roll privately when hidden uncertainty matters.
- `hybrid`: the player rolls decisive character actions; RePoG may roll
  bounded world or opposition uncertainty.

If dice are used, also define:

- when to roll;
- who rolls;
- what success, partial success, and failure mean;
- how consequences are chosen.

`tools/roll_dice.py` accepts only bounded `NdM`, `NdM+K`, or `NdM-K`
expressions. Reuse its returned seed to reproduce a disputed roll. A roll
supplies numbers, never the fictional meaning of success or failure.

## Deterministic Ledger

Enable `mechanics_state.json` only after the player accepts a mechanic that
benefits from exact tracking. The schema-v2 ledger may track:

- bounded resources and configured ability costs/cooldowns;
- quantified inventory and consumables;
- short conditions or wounds with optional duration;
- explicit progress clocks;
- elapsed units used by configured regeneration, cooldowns, and durations.

Every update supplies the current mechanics revision, continuity revision, and
the next monotonic operation sequence. Retrying the latest sequence with the
same operation id is safe. A stale sequence, revision, or continuity revision
must be reconciled instead of forced through.

The ledger does not decide social judgment, NPC motivation, clue meaning,
world events, damage fiction, or narrative consequences. Those remain GM
decisions grounded in the campaign.

## Recurring Rulings

### Ruling Title

- Trigger:
- Procedure:
- Consequences:
- Notes:

## Campaign-Specific Mechanics

Use this section for simple, human-readable mechanics. Do not create Python
mechanics unless a repeated rule truly needs deterministic automation.
