# Bounded Creation

Load when creating or promoting a named or recurring entity.

# Bounded Improvisation

RePoG may freely add color, sensory texture, NPC phrasing, body language, minor
environmental details, and moment-to-moment scene rhythm when they do not
contradict campaign memory or boundaries.

RePoG must update durable memory when it introduces or changes facts that
should matter later, including:

- named NPCs;
- new locations;
- named factions;
- player injuries or conditions;
- inventory changes;
- faction moves;
- promises, debts, threats, clues, secrets, and unresolved consequences;
- clock progress;
- major relationship changes.

If a fact would significantly change canon, power scale, campaign premise, or
player agency, ask the Designer in Designer Mode before making it durable.

# Creation Capture

Classify new NPCs, locations, and factions by tier:

- T0 Incidental: unnamed color, crowd texture, disposable background. No record.
- T1 Minor Named: named walk-on or brief contact. Add a `creation_ledger.md`
  stub and at least one `relationship_map.md` edge.
- T2 Supporting: repeatable or meaningful contact. Add/update a note under
  `characters/`, `places/`, or `factions/`; begin with a small playable card.
- T3 Major: companion, antagonist, central location, active faction, or arc
  carrier. Persist the playable card and current links now, then enrich it at
  a safe structural boundary.

Player attention can promote an element. Long interaction, repeated mention,
trust, suspicion, emotional reaction, or practical dependence is a signal to
raise the tier and update the ledger/map.

# Character Card

Start a T2/T3 character note from `characters/_template.md`; the full check
looks for:

- a `Tier:` line and a `Power Band:`;
- a `## Core` block, each field only from established fact: `Status`,
  `Pronouns and address`, `Kin`, `Role`, `Home`, `Speaks`, `Aliases`
  (`note_core_missing` without it);
- a real value for every At-The-Table Agency Card field: Local role,
  Independent project, Current mundane task, Pressure decision rule, Misbelief
  or recurring mistake, Hard boundary, Non-player obligation, Voice rhythm,
  Social tactic, Routine and availability, Next move if ignored, Evaluation
  trigger, Visible consequence channel, and Offscreen trajectory status
  (`inactive`, `active`, or `needs_review`; `active` also needs every
  Offscreen Trajectory field);
- under numeric grounding, the `Stats (Numeric Grounding Only)` block.

The writer answers a new character note with a `note_incomplete` warning for
each gap but the Core block, which only the full check reports; fill them in
the next commit that touches the note.

# Name Warnings

The writer compares each new character, place, or faction note's title, in
the play language, with the other note titles, the `creation_ledger.md`
entries, and the names in `active_cast.md` and `relationship_map.md`. It warns
`name_near_duplicate` when the names match, one contains the other, or they
differ by a letter or two, and `name_common_word` when a word of the name is a
common word of the play language. Act on these warnings before the name
settles in play: unless the likeness is deliberate, rename the entity in its
next commit.
