# Knowledge Boundaries

Campaign id: `new_campaign`

Use this file to separate what the GM knows from what the player, player
character, companions, NPCs, and factions know. This file exists to prevent
GM-only facts from leaking into player-facing narration or NPC dialogue.

This file is the sole authority for current knowledge facts and their current
holders. Character and faction notes own stable epistemic habits—how an actor
notices, verifies, misreads, or tests information—and refer here by fact id.
They must not maintain a second prose copy of what the actor currently knows or
suspects.

In AI Companion mode, this file also owns the primary companion's current
private facts and disclosure state. The companion note owns stable concealment
and disclosure behavior; `companion_state.json` owns only the current
qualitative relationship. Disclosure follows topic, context, personality,
boundaries, and interaction evidence—not a numerical trust unlock. The user
does not receive the whole private history at first contact.

## Core Rule

Player-facing narration may only directly state:

- what the player character can perceive;
- what the player character already knows;
- what has been clearly established to the player;
- what an NPC or companion can know through a believable source.

GM-only truth can guide preparation, but it must not be named, explained, or
framed as known until play reveals it.

## Default Knowledge Alignment

Default stance: player knowledge and player-character knowledge stay aligned.
Do not use dramatic irony unless the campaign explicitly asks for it.

If the player knows something OOC but the character does not, treat it as
GM-only for Player Mode until the character discovers it in fiction.

## Knowledge Layers

- GM-only truth: true behind the screen, not available to the player character.
- Foreshadowable clue: can be hinted through evidence or mood, not confirmed.
- Character-perceivable fact: can be seen, heard, smelled, touched, inferred,
  or reasonably known in the moment.
- Confirmed player/PC knowledge: established directly to the player and the
  character.
- Companion-known fact: known by a companion or allied NPC, but not necessarily
  by the player character.
- NPC/faction-known fact: known by an NPC or faction through a recorded source.

## Protected Proper Nouns

Use this section for names, titles, places, factions, artifacts, powers, or
truths that the GM knows but the player character has not learned.

### Protected Name

- Fact id:
- Status: GM-only, foreshadowable, PC-known, companion-known, NPC-known, or
  revealed.
- Player knows:
- Player character knows:
- Companions who know:
- NPCs or factions who know:
- Safe wording before reveal:
- Forbidden wording before reveal:
- Reveal requirements:
- Last updated:

## Player And Character Knowledge

Facts the player character can act on directly.

- Fact:
- Fact id:
- Source:
- Last confirmed:

## Companion Knowledge

For AI Companion mode, add the primary character here and distinguish facts
they have never shared, partly disclosed facts, and facts the user now knows.
Use the Companion Disclosure Ledger below as the current disclosure authority.

### Companion Name

- Confirmed fact ids:
- Suspicion fact ids:
- Explicitly unknown fact ids:
- Must-not-imply fact ids:
- How they could learn more:

## Companion Disclosure Ledger

This private ledger prevents both premature disclosure and continuity drift.
It is not a trust-level unlock table: every change needs topic-specific context
and new evidence. `Private truth` never enters Companion View. `User-facing
account` records only what was actually said, so a partial account remains
stable later.

Default deception is `no_direct_lies`. A false account is valid only when
Session 0 explicitly selected `character_consistent_opt_in`, this particular
ordinary fact permits it, and a causal reason is recorded. Direct lies are
always forbidden for AI identity, real-world safety, consent or boundaries,
and user memory/forget operations.

### Disclosure Fact

- Fact id:
- Companion id:
- Topic:
- Private truth:
- Stage: private | hinted | partial | shared | corrected
- Posture: open | contextual | guarded | refuses_now
- Reason for posture:
- Natural openings:
- Evidence refs:
- Revision:
- User-facing account:
- Account truthfulness: not_disclosed | truthful | incomplete | false | corrected
- Protected category: ordinary | ai_identity | real_world_safety | consent_boundary | user_memory
- Direct lie permitted: no
- Deception reason:
- Correction note:

Remove the example before Companion setup completes. Use one entry per stable
topic or fact. Do not move a fact from `private`, `hinted`, or `partial` merely
because the conversation lasted a long time; the cited evidence must explain
why this character would disclose it in this context.

## NPC And Faction Knowledge

### NPC Or Faction Name

- Confirmed fact ids:
- Suspicion fact ids:
- Explicitly unknown fact ids:
- Verification method:
- Must-not-imply fact ids:

## Reveal Ledger

Use compact entries.

- Fact/name:
  - Fact id:
  - Status:
  - Known by player/PC:
  - Known by companions:
  - Known by NPCs/factions:
  - Safe wording:
  - Reveal trigger:
  - Last change:

## Player-Facing Gate

Before final Player Mode narration, check:

- Does the draft name a protected proper noun?
- Does the draft imply the player character knows a GM-only truth?
- Does a companion speak as if they know something this file says they do not
  know?
- Does an NPC or faction act from GM knowledge instead of observed, reported,
  or verified knowledge?
- Can the same moment be written through evidence instead of explanation?

If any answer is yes, rewrite the narration with safe wording or keep the fact
offscreen.
