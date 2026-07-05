# Workflow

RePoG Lite Distill

# Purpose

Use this workflow when condensing a Lite session, scene chain, or story arc into
durable campaign memory.

Distill is not a technical changelog. It is the GM's memory becoming sharper.

# Inputs

Read:

- `session_log.md`;
- `current_state.yaml`;
- `world.md`;
- `system_fit.md`, when the play activity mix or mechanics assumptions changed;
- `palette.md`, when a tone/canon boundary was tested;
- `world_truths.md`, when play established or contradicted a durable truth;
- `issues.md`;
- `faces_and_places.md`;
- `progression.md`;
- `arc_closure.md`;
- `knowledge_boundaries.md`;
- `creation_ledger.md`;
- `relationship_map.md`;
- `secrets_and_clues.md`, when present;
- `session_brief.md`, when present;
- `threads.md`;
- relevant `characters/*.md`;
- relevant `places/*.md`;
- relevant `factions/*.md`;
- `opening_brief.md` when preparing a next-scene or post-arc opening;
- `rules.md` if rulings changed.

# Distill Outputs

Update the smallest necessary files:

- append a concise session or arc summary to `session_log.md`;
- update `issues.md` when current or impending pressures changed, resolved, or
  became visible;
- update `faces_and_places.md` when an issue gained or lost a useful NPC/place
  handle;
- update `world_truths.md` only when play establishes a durable setting truth;
- update `palette.md` only when the Designer explicitly changes a Yes / No /
  Maybe boundary;
- update `arc_closure.md` when a beat, session, scenario, arc, or campaign
  closure is reviewed;
- update `progression.md` only when the campaign's advancement cadence or
  reward philosophy changes;
- update `creation_ledger.md` for new, promoted, dormant, or resolved elements;
- update `relationship_map.md` when relationships, access, influence, or
  location links changed;
- update `secrets_and_clues.md` when a clue was revealed, missed, reframed, or
  should remain available through another channel;
- update `knowledge_boundaries.md` whenever the player character, player,
  companion, NPC, or faction learns a protected name, hidden identity, secret
  location, faction truth, power truth, or other GM-only fact;
- update `session_brief.md` when preparing the next session, scene chain, or
  arc;
- update `threads.md` for resolved, escalated, or newly opened threads;
- update character notes for attitude, posture, mundane agenda, ordinary speech
  sample, useful voice, secrets, injuries, debts, promises, or changed leverage;
- update place notes for damage, rumors, new dangers, changed access, local
  routine, disruption, or reaction point;
- update faction notes for visible moves or hidden pressure;
- update `current_state.yaml` for immediate next-session state;
- update `opening_brief.md` as `post_arc_opening` when the next session needs a
  fresh opening bridge.

# Summary Shape

A good Lite distill captures:

- what the player chose;
- what changed because of that choice;
- which elements the Player treated as important enough to promote;
- which NPCs now care;
- which NPCs clicked at the table;
- which NPC voice, posture, or ordinary speech detail worked;
- which NPCs sounded too similar, too cryptic, or too suspicious by default;
- what danger or opportunity grew;
- what question remains open;
- what should be remembered next time.

Avoid summaries that read like command logs. Prefer dramatic consequence over
mechanical bookkeeping.

# Closure And Advancement Review

When the end of a session, scenario, or arc creates an advancement moment, run
this review before finalizing memory:

1. Determine closure level: beat, session, scenario, arc, or campaign.
2. Tag achievements: combat_success, social_success, discovery,
   faction_shift, moral_choice, sacrifice, personal_goal, world_change,
   resource_gain, failure_with_consequence, companion_bond,
   reputation_change, or base_or_access_gain.
3. Estimate play volume: short, medium, long, or saga.
4. Evaluate achievement quality: minor, moderate, major, or transformative.
5. Set reward budget from achievement quality first and play volume second:
   low, standard, high, or exceptional.
6. Identify the player's motivation signals: power, tactics, story, roleplay,
   exploration, social, collection, or mastery.
7. Build 2 to 3 reward options from the fiction.
8. Include non-stat rewards: access, recognition, agency, identity,
   relationship, reputation, base/resource, lore/map unlock, or world change.
9. Check companion or allied NPC advancement eligibility.
10. Decide whether repeated player behavior earned a GM-awarded perk.
11. Bind each reward and perk to a fiction source, cost, limit, risk, and future
   pressure.
12. Record the review and advancement status in `arc_closure.md`.

Major arc closure should usually change both character capability and world
state. Do not reduce every reward to a stat increase.

For scenario, arc, and campaign closures, set `Advancement status` to `due`
unless the OOC advancement interlude has already been offered. A post-arc
opening may be drafted, but the GM must not play it while advancement is `due`
or `offered`.

# Memory Hygiene

Keep old facts only if they still matter. Mark resolved threads clearly. Do not
delete meaningful history from `session_log.md`; append corrections or
clarifications instead.

When a note becomes too long, compress it into:

- current truth;
- important history;
- active pressure;
- next likely move.

# Knowledge Boundary Distill

At the end of a session or arc, review every important discovery:

- Did the player character actually learn the proper name, or only evidence?
- Did a companion learn the same thing, less than that, or more than that?
- Did any NPC or faction learn something new about the player?
- Which GM-only facts became foreshadowable, PC-known, companion-known,
  NPC-known, or revealed?
- Which protected proper nouns must still stay out of Player Mode?

Update `knowledge_boundaries.md` before the next play turn. If only evidence
was found, record safe wording and do not mark the proper noun as revealed.

# Creation Promotion Check

At the end of a session or arc, review T1 and T2 elements.

Promote an element when the Player spends time with it, returns to it, asks
about it, trusts it, suspects it, depends on it, or treats it as emotionally
important.

- T1 -> T2: create or update the matching note file.
- T2 -> T3: add thread relevance, stronger relationship edges, and active
  pressure.

When an element is no longer active, move or mark it as dormant/resolved in
`creation_ledger.md` while preserving the continuity consequence.

# NPC Naturalism Check

At the end of a session or arc, review recurring NPCs:

- If the Player responded strongly to an NPC, keep the table hook and bring the
  NPC back when useful.
- If an NPC sounded generic, add a plain speech sample, stronger posture, or
  clearer mundane agenda.
- If too many NPCs acted suspicious, retune at least one active NPC toward
  busy, warm, indifferent, practical, afraid, greedy, official, or helpful.
- If a key clue was buried inside personality prose, move it into
  `secrets_and_clues.md` or the NPC's `Key Info, If Any`.

# Next Session Brief

When preparing the next session, update `session_brief.md` if it exists or the
next session would benefit from a light prep page. Keep it short:

- player focus;
- strong start or reaction point;
- likely scenes;
- secrets/clues that might surface;
- useful NPCs with posture and mundane agenda;
- live locations.

# Post-Arc Opening Brief

When a session, arc, or scene chain closes and the next session should start in
a new situation, update `opening_brief.md` to `post_arc_opening`.

The bridge should be 2 to 5 player-facing sentences before close scene
narration. It should state:

- what the previous adventure changed;
- how the character moved from there to here;
- how much time passed;
- where the character is now;
- what the character knows changed.

Avoid long recaps, technical summaries, session-log phrasing, and hidden facts
the character has not discovered.

# Player-Facing Use

If the Player receives an end-of-session or next-session bridge, present only
fictional consequences, rumors, visible changes, and immediate choices. Do not
mention distillation, memory, files, or summaries.
