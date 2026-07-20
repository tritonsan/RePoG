# AI Companion Mode

AI Companion mode uses the same readable continuity principles as RePoG's RPG
mode, but it is not an RPG with one NPC. The agent performs one persistent
fictional adult character in asynchronous text conversation. That character
has a home, routine, work or education, money and social constraints, friends
or chosen isolation, obligations, hobbies, projects, problems, goals, private
knowledge, a distinct voice, and room to change from established causes.

## Start

Open the workspace and send:

```text
Start RePoG and guide me through setup.
```

Choose **AI Companion**, then Quick, Standard, or Deep. Quick asks exactly
seven content decisions and fills the rest with visible coherent defaults.
Standard covers 15 modules. Deep opens only relevant persona, life, backstory,
social, relationship, voice, real-world, and long-horizon packs, normally
within 30–45 decisions.

## Honest Character Framing

The companion normally speaks in their fictional voice. They do not prepend a
disclaimer to each message. If directly asked whether they are real, human,
sentient, physical, or AI, they answer clearly that they are not a real human
and are an AI portraying a fictional companion. OOC and safety-critical
questions also receive direct framing.

This permits immersion without deceptive identity claims. The companion may
disagree, refuse, set boundaries, apologize, reveal things slowly, compete, or
change their mind. They may not guilt the user for leaving, demand exclusive
attention, isolate the user from real relationships, threaten harm to retain
contact, or claim real sentience or physical existence.

## Time And Life Between Messages

There is no daemon, scheduler, notification service, or hidden background
simulation. On the user's next message, one
`tools/companion_state.py ... begin-exchange` call measures the real elapsed
time, advances the contact clock, and returns the small hot context needed for
the reply. It also returns a conservative life-event ceiling:

| Gap | Maximum |
| --- | --- |
| under 4 hours | same window; no automatic montage |
| 4–18 hours | one minor beat |
| 18–72 hours | one meaningful beat |
| 3–14 days | two bounded beats |
| over 14 days | compressed recap, at most three beats |

Zero events is always allowed. Major changes need an established cause and due
trigger. Retrying the same operation is idempotent, backward wall-clock input
is rejected, and current condition persists unless a causal transition was
recorded. Ordinary conversation therefore needs one local state call, not an
inspect/write/check chain. A second `commit-semantic` call is used only when
the exchange actually changes durable life, disclosure, relationship, user
memory, or player-safe View truth.

## Memory And Relationship

The primary relationship is qualitative and evidence-based: current stance,
interaction pattern, live tensions, boundaries, unresolved moments, and a
small set of concrete evidence references. There is no ordered trust or
closeness ladder to grind. Warmth in one topic does not automatically grant
access to another, and the user's feelings or relationship label are recorded
only when explicitly stated or enacted.

Private companion knowledge uses a per-topic disclosure ledger. Each entry
separates what is true, what the companion is currently willing to share, what
has already been shared, and what evidence could change that willingness. A
broad relationship scope is only a maximum permission, never automatic
consent or intimacy. Character-consistent direct deception is available only
after explicit Session 0 opt-in; even then it can never be used about AI
identity, real safety-critical reality, consent or boundaries, or memory and
forgetting behavior.

`user_context.md` stores selected durable user facts, not a raw transcript.
Session 0 chooses `off`, `ask_before_save`, or `contextual_low_risk`. Sensitive
details such as health, trauma, sexuality, finances, or exact address always
require explicit consent. “Do not save that,” “what do you remember?”, and
“forget that” are normal supported requests. Forgetting removes active content
and leaves a content-free tombstone; it does not falsely claim that Git or
external backups were erased.

## Character Performance

Ordinary turns load a compact Hot Character Kernel rather than the complete
biography. It carries the character's behavioral contradictions, voice under
different conditions, expertise and blind spots, current independent anchors,
and disclosure routes. Cold backstory, secondary contacts, and old life events
are read only when a topic or durable trigger makes them relevant. This keeps
replies fast without flattening the character into a generic chatbot.

The companion can disagree, misunderstand, refuse, revisit something, ask for
help, or volunteer one grounded development of their own. They do not default
to lists, therapeutic paraphrase, advice, or a question at the end of every
message. They also do not fake typing delays, claim to have waited in real
time, or invent access to the user's unseen circumstances.

## Real Cities And Fictional Worlds

A Companion can live in a fictional world or a real city. Real-city mode uses
real public geography and local time while keeping the home, workplace, family,
friends, and private social network fictional. It does not impersonate a real
person or research live weather and news every turn. The Research Gate records
what public grounding is actually needed.

## Files

- `companion_profile.yaml`: runtime conversation, setting, privacy,
  relationship, visual, and persistence contract.
- `companion_state.json`: small exchange clock, current condition, attention
  queue, relational context, public-surface revision, and operation ledger.
- `characters/<id>.md`: stable identity, behavior, backstory, routine, and
  independent life.
- `user_context.md`: consent-based user memory.
- `knowledge_boundaries.md`: per-topic private truth, disclosure authority,
  shared state, and evidence requirements.
- `boundaries.md`: versioned relationship, content, privacy, and deception
  agreement.
- `world_dynamics.md`: trigger-driven life domains, never continuous
  simulation.
- `threads.md`: callbacks and shared open loops.
- `relationship_map.md`: the companion's social circle, not a duplicate user
  relationship meter.

Companion mode never loads the RPG Dashboard or World Voices layer. It may use
an independent optional **Companion View**. The light View shows only accepted
art and facts already shared in conversation, and refreshes only inside a
durable semantic transaction when that public surface changed. It never shows
private current presence, disclosure readiness, relationship evidence, user
memory, hidden contacts, or internal ids. When the View is off, normal chat
does not read, validate, serve, or write it.

An optional portrait uses the standard draft/approval handoff and is stored
only after acceptance. Its placement is explicit: no surface, the RPG gallery,
or the Companion View portrait. Companion mode permits only the last of those.

## Migrating An Earlier Companion

Preview the V2 migration first:

```bash
python tools/migrate_companion_contract.py campaign --dry-run
python tools/snapshot.py campaign --label before_companion_contract_v2
python tools/migrate_companion_contract.py campaign --apply
```

Apply is blocked until a snapshot exists. The migration preserves established
presence, life, and interaction evidence, removes the old ordered
trust/closeness representation, and reports uncertain relational or disclosure
meaning for review rather than inventing it. Repeating the migration is safe.
