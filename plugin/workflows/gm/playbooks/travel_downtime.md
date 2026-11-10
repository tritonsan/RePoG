# Travel And Downtime Playbook

Use this playbook when characters move between places, meaningful time passes,
or the Player pursues routine care, work, training, research, crafting, or a
personal project.

## Choose Compression

Zoom in only when travel or downtime contains a consequential decision,
meaningful uncertainty, relationship beat, discovery, or established pressure.
Otherwise compress the passage cleanly and state the useful change in time,
place, condition, resources, or readiness.

Do not manufacture an encounter to justify the transition. A safe route or an
uneventful work period is a valid result.

## Travel Logic

Use `location_graph.md` for directed access, plausible route, travel time,
visibility, and known/unknown connections. Respect the profile's travel and
time tracking. Do not reveal a hidden route merely because the graph contains
it.

Before moving an NPC with the Player or meeting one at the destination, check:

- last known location and elapsed time;
- route feasibility and access;
- routine/availability and current task;
- reason to travel or already be present;
- whether the Player knows any of this.

Absence, a closed business, a missed connection, or a delayed arrival can be
the honest state of the world without becoming a punishment.

## Downtime Projects

Start from the Player's declared purpose and method. Establish the time,
materials, access, assistance, and capability actually required. Let ordinary
maintenance and established competence succeed without a test. Use a mechanic
only when its module is approved and a meaningful uncertain outcome remains.

Progress should be concrete: a repaired item, learned fact, practiced move,
earned contact, restored condition, changed resource, or clearer next step.
Do not convert every personal project into a hook for the main pressure.

## Triggered World Motion

Evaluate only domains touched by elapsed time, route, contact, return, or a
tracked threshold. Use a stable evaluation id when deterministic uncertainty is
needed. Record notable changes and their believable reveal channels; hidden
motion remains hidden until news, evidence, witnesses, or consequences reach
the Player.

Do not continuously simulate all factions or NPCs, and do not refresh unrelated
domains for completeness.

## Offscreen Trajectories

When a T3 or player-important T2 NPC leaves the active cast, preserve a compact
trajectory in its designated authority:

- independent goal and current method;
- obstacle or resource;
- next decision if ignored;
- evaluation trigger and time horizon;
- possible success/setback shape;
- visible consequence or communication channel;
- last evaluated revision/time.

Evaluate it only on a relevant time passage, return, news, relationship change,
or linked-domain trigger. Reuse the same evaluation for the same trigger; do
not reroll history.

## Timed Threats

A threat with a deadline is a fact the world keeps, not one the GM remembers.
When it starts, give it an `active_clocks` entry in `current_state.yaml` (a
`list_add` op) naming what fills it and what happens when it does, and, with
the `clocks` module on, its clock through `add_clock`. Time passing then moves
it: a skip ticks it and a filled clock fires on its own record. At an act
close, run `python tools/world_pulse.py --input-file -` once for the domains
whose trigger the act made due (scene and arc transition playbook).

## Time Skip

Use this procedure when skipped time is long enough for relationships,
threats, or recurring costs to move; a short compressed passage needs only the
change it produced.

### Time-Skip Brief

The Player owns what the character does with the time, so start from their
brief. When they ask to skip ahead without one, offer this short template in
their language:

- Span: from when to when, or "until something happens".
- Stops: each place or stretch of time in order, and what the character does
  there.
- Accounts: what the character spends, earns, buys, pays, or owes on the way.
- In or out: anything they want to happen, or to stay off the page.

The GM answers with a sectioned montage: one short section per stop, in the
order given, each ending on what changed there. Keep the whole reply to about
800 words unless the Player asks for more. The commit comes first, and the
montage is the turn's last message.

### Skip Until Something Happens

When the Player asks to let time run until something happens, compress the
days until the first established trigger fires: a clock fills, a domain's
trigger comes due, an NPC's next move arrives, or a condition the Player named
is met. Give the quiet stretch a few lines, stop at that moment, and return
control there. Nothing is invented to end the skip early; if no trigger is
due within the span the Player allowed, the skip ends at that span quietly.

### Resolving The Skip

1. Resolve the skip silently before writing. The montage shows only what the
   character knows by its end, in the Player's language and without file,
   tool, or id names; hidden moves are decided and recorded, not shown. Cover:
   - the span, with its start and end;
   - each significant relationship's change, weighted by what `player.md` says
     the Player values;
   - each active threat, faction, or domain's move: due domains go through one
     `python tools/world_pulse.py --input-file -` call with a `domains` batch
     (at most 12, stable evaluation ids, so a redraft returns the same
     envelopes). `elapsed_steps` counts the domain's own step: one week unless
     its `world_dynamics.md` entry names another unit. Clocks tick only through
     `advance_time` in the step 3 commit, so count from each clock's `tick`
     which ones fill and draft their `on_fill`; a threat that starts during the
     skip gets its clock through `add_clock`;
   - closures: a threat closes only on evidence the record names (a roll id, a
     Player decision, or a played scene), never silently; `remove_clock`
     retires its clock;
   - the ledger per period, where `mechanics_state.json` tracks it: one
     `settle_obligation` for each period the skip covers. Derive the period key
     from `fictional_time.day` so it is stable, such as `week:<day // 7>` or
     `month:<day // 30>`, never from a count within this skip; a period already
     paid is then refused instead of charged twice. An obligation is paid from
     a resource, or from an inventory item (`item_id`) when the money is kept
     as one; `add_obligation` records a new recurring cost first;
   - projects, pending rewards, and whether the skip answers or forecloses the
     act's question.
2. Without a brief, when the GM must propose what the character did, draft
   that part OOC first and wait for the Player's approval or edits; an edit may
   change what the character did, and world moves change only where that
   causes them to.
3. Commit the skip in one `commit-durable` call: its owner mutations (the new
   `fictional_time.day` among them), mechanic operations (at most 16 per
   commit), every roll cited or voided, and a checkpoint with scene mode
   `downtime` and its `open_choices` (boundary `scene_checkpoint` unless a full
   distill is due).
4. Write the montage as the reply. It ends at the arrival scene's first
   reaction point (scene-entry playbook). A change the Player asks for after
   the montage is an amend of the last beat (OOC adjustment playbook).

## Handoff

When travel opens a new scene, use the scene-entry playbook. When downtime is
primarily safe relationship or recovery space, use the breather playbook.
Persist only durable changes and a checkpoint at the actual transition; soft
descriptive travel receives no write or check.
