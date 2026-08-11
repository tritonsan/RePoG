# Rules And Rulings

This file stores table rules, optional dice procedures, recurring rulings, and
campaign-specific mechanics.

## Core Approach

Codex handles ordinary fictional positioning directly. Use deterministic rules
only when they improve fairness, tension, or continuity.

`play_profile.yaml.mechanics.resolution_grounding` selects the campaign's
resolution basis:

- `fictional` (default): permissions, competence, approach, leverage, limits,
  opposition, and consequences decide outcomes in the fiction;
- `bands`: broad setting-appropriate capability bands support comparison
  without requiring a full stat block;
- `numeric`: the declared axis set below, the 1–5 scale, and the budgets are
  active. The axis count comes from the campaign's own declared set, not from a
  fixed number.

Do not require numeric player, NPC, faction, or obstacle stats unless the
selected grounding is `numeric`.

## Numeric Stat Scale

When numeric grounding is active, stats use a 1 to 5 scale:

- 1: weak or unreliable.
- 2: ordinary but usable.
- 3: capable and dependable.
- 4: exceptional.
- 5: elite or defining.

### Declared Stat Axes

Derive these axes from the researched world and the declared starting stage
instead of importing a generic set. Leave out capabilities the campaign's stage
has not reached, and add setting-specific axes when the stage warrants them.
Offer the Player two to four candidate sets and record the accepted one here; the
count may differ from the default of eight, and validation follows this list.

Give every axis a meaning before the Player distributes anything. One line each,
in this shape, so the block stays small enough to keep in hot context during
play:

`Axis — covers X; does not cover Y; at 1 …, at 3 …, at 5 … in this setting.`

An axis with a name but no meaning is decorative. The Player chooses numbers only
after reading what those numbers will do.

- Power
- Agility
- Endurance
- Technique
- Perception
- Wits
- Presence
- Will

## Numeric Starting Level Budgets

Starting distribution has one constraint: every declared axis receives at least
one point. There is no per-axis cap. A Player who wants a defining strength at
the top of the scale from the first scene may have it, and pays for it in the
axes they left low.

The totals below assume eight axes. With a different declared set, derive the
total from the axis count—roughly twice the number of axes places ordinary axes
near the middle of the scale—state it, and let the Player accept or change it.

- Beginner: 16 points.
- Competent: 20 points.
- Advanced: 24 points.
- Elite: 28 points.

Campaigns may rename tiers to match the setting. These budgets do not apply to
fictional grounding, and banded grounding uses band steps instead of points.

The 1 to 5 scale still bounds every value. Unnamed world figures are a separate
matter: giving an ordinary opponent elite numbers without declaring a high power
band remains a flagged inconsistency.

## Special Ability Points

Some settings carry capabilities the stat axes cannot describe—a fruit power, a
force discipline, a school of signs or spells, a bloodline. When the campaign has
such a layer and grounding is numeric or banded, it gets its own pool, separate
from stat points, so a special power never competes with ordinary competence for
the same currency.

- Does this setting have capabilities outside the axes: yes / no
- What the layer is called here:
- Starting special ability points:
- What one point buys, in this setting's terms:
- How a new power is acquired in the fiction:

When the setting has no such layer, this pool does not exist and is not invented.
Under fictional grounding, the same capabilities are recorded in prose with their
source, cost, and limit, and carry no points.

## Simulation Fidelity Obligations

Each tracking setting names an instrument and a turn obligation. A setting that
changes nothing about behavior is decoration, so treat this table as binding.

| Setting | Obligation during play |
| --- | --- |
| `dice_mode` other than `judgment_only` | A contested outcome comes from a recorded roll, not from narration. A durable change that records a contested result carries its roll reference; the durable writer rejects one that does not. Who rolls and whether it is open follows the selected mode |
| `dice_resolution` module | Contested resolution runs through the mechanic resolver where it applies |
| `inventory_tracking: quantified` or `encumbrance` | Gaining or spending an item is a mechanic operation inside the durable commit, never prose alone |
| `strict_consumables` | Supplies decrease when used, and running out is a state fact rather than a narrative flourish |
| `wounds`, or `wound_tracking: conditions` | An injury becomes a recorded condition with the criteria for clearing it |
| `clocks` | Named clocks advance only on their declared trigger, through a mechanic operation |
| `time_tracking: scene` or `step` | Fictional time advances in that unit as part of the turn's write |
| `travel_tracking: route_time`, `structured_travel` | Travel consumes recorded legs and time |
| `bounded_resources`, `abilities_costs` | Using an ability spends its cost or sets its cooldown |

The inverse is equally binding: when a setting is abstract or off, invent no
precision. Do not report counts, distances, clock positions, or wound values the
campaign does not track.

Fidelity is not tension. A fully tracked campaign may spend a quiet month in
port, and dice do not oblige danger. Pace, challenge density, and breathers are
separate settings and stay under their own policy.

Keep tracking out of the prose. Changed values belong in state; narration carries
only their fictional weight, such as the last two bottles of water rather than a
table. When a dashboard is enabled the numbers live there instead.

Changing fidelity mid-campaign is a stage-boundary revision: crossing into
waters that demand supplies and route discipline is a reason to turn those
settings on, recorded as a revision rather than a silent drift.

## Capability Model In Play

Whatever capability model the campaign accepted stays binding during play, and
the GM keeps it in hot context rather than recalling it. Under numeric or banded
grounding that is the declared axis block with its band meanings; under fictional
grounding it is the recorded competence, limit, cost, and counterplay.

Each turn, before deciding the world's response:

- name which axis or recorded capability the action leans on;
- read its value or band to decide whether this is routine competence that
  succeeds cleanly, a genuine contest, or beyond reach for now;
- read the opposition on the same scale, so a contest is between two known
  quantities rather than a feeling;
- treat a low value as a pressure, cost, or counterplay channel instead of
  automatic failure.

Narration may not contradict the sheet. A character weak in an axis does not
outperform someone strong in it because the moment wants drama, and a strong axis
is not quietly ignored to keep a scene tense. If the fiction demands an outcome
the sheet does not support, change the route to that outcome or let the sheet
stand—do not narrate past it.

## Stat Use And Opposition Model

Under numeric grounding, stats are not only for the player. Use the same 1 to
5 scale for T2+ NPCs, companions, major antagonists, important faction faces,
and significant obstacles. Under fictional or banded grounding, use the
equivalent prose permissions or broad bands instead.

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
