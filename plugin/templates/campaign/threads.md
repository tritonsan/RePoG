# Threads

Use this file for open dramatic questions, consequences, debts, mysteries,
threats, promises, and opportunities.

Threads are player-facing dramatic continuity: what question, promise, debt,
or consequence remains meaningful because of the player's choices and
interests. `issues.md` owns systemic problems, `world_dynamics.md` owns current
offscreen evaluation, and `current_state.yaml.scene_frame` owns the live causal
beat. Reference those authorities instead of copying their state here.

As of revision: 0

In AI Companion mode, use Active Threads for shared callbacks, promises,
upcoming conversations, and user-relevant open loops. The companion's private
work/family/project movement belongs in `world_dynamics.md`; an explicitly
shared upcoming user event belongs in `user_context.md` and may be referenced
here without copying sensitive detail.

## Companion Shared Continuity

Use this section instead of Arc Compass when Experience is `companion`. Do not
force ordinary conversation into dramatic pressure or a climax structure.

### Shared Loop

- Thread id:
- Kind: callback | shared_plan | unfinished_conversation | invitation
- What was explicitly established:
- Due window:
- Companion interest:
- User interest: explicit | inferred_for_lookup_only | unknown
- Status: open | addressed | cancelled
- Source reference:
- Last changed revision: 0

## Campaign Horizon

RPG-only and optional. Keep only the few campaign-scale questions or promises
actually accepted by the Player. Sandbox or episodic play may leave this empty;
there is no mandatory main plot. Stable setting truth stays in its owner.

For each relevant horizon, keep a short id, open question/promise, source of the
accepted interest, status (`open`, `transformed`, or `retired`), and source revision.
Possible answers remain possibilities, not promised endings. A new player goal may
change which question matters; do not infer a permanent taste from one action.
A material change to the accepted campaign promise follows the Designer boundary.

## Arc Compass

RPG-only. Leave inactive in Companion mode. This is the single current-act owner,
not just a first-act setup note. Fill the first Compass during Session 0. For later
acts follow `workflows/gm/playbooks/scene_arc_transition.md`: archive the closed
Compass and establish its successor here before opening the new act.

- Act id:
- Act status: planned
- Previous act id: none
- Opened at revision:
- Act name:
- Dramatic question:
- Active pressures:
- Setups awaiting payoff:
- Climax availability conditions:
- Closure conditions:
- Player interest signals:
- Horizon reference: none
- Link to current player choices:
- Independent space:

Use a stable, non-reused act id. `planned` belongs to draft preparation, `active`
to the current playable question, and `closed` to an answered/foreclosed question
whose aftermath may still be played. `Previous act id` is `none` for the first act;
otherwise it points to a closed entry in Act Archive. `Opened at revision` is the
continuity revision at activation (0 is valid for initial setup), not setup revision.

The horizon reference links an optional campaign-scale question to this act; it
may be `none`. In one or two lines explain how actual player choices changed that
connection and what remains independent of it. Do not make every personal project
serve the same plot or prescribe an answer, event order, or climax date.

`Setups awaiting payoff` references relevant Planted Expectations below; unshown
preparation is not something the Player should remember. Climax conditions describe
reachability, not a scheduled event. Closure is independent of reward cadence.

### Act Scope

Keep the concrete reachable extent in names rather than category labels. A small
act may occupy one place if its question and choices genuinely support that scope;
do not add locations or cast merely to make preparation look large.

- Places this act can reach:
- People who belong to it:
- What is already in motion as it opens:
- What stays true if the character does nothing:

### Closure Record

Fill only when this act actually closes. Mark the Compass `closed` in the same
owner transaction as the decisive result, regardless of whether an award is due.
Do not reconstruct or credit a later turn as the decisive action.

- Closing action:
- Condition met or foreclosed:
- Recorded at revision:

## Act Archive

After an act closes, keep its Compass here when a successor activates. Each entry
uses `### <act id>` and retains its Act id, `Act status: closed`, Previous act id,
Opened at revision, question, scope, closure conditions, and Closure Record. Demote
its nested Act Scope and Closure Record headings to `####` (or retain flat fields);
only `### <act id>` begins an archive entry. Include compact relevant horizon/
expectation references, not duplicate entity history.
Archive the outgoing Compass and create the new active Compass in one `threads.md`
candidate; do not erase the old evidence or recycle its id.

Legacy campaigns without a meaningful Act id keep their existing behavior. Offer
adoption only at an explicit Designer review or accepted safe transition; never
invent missing historical ids or closing evidence. Adoption can record the current
act as the first tracked act (`Previous act id: none`) with an explicit migration
note rather than claiming reconstructed history is verified.

## Planted Expectations

Optional, selective memory for a few important promises, recurring details, debts,
or unresolved capabilities. Do not track every prop, motif, or line of dialogue.
Use source references instead of copying knowledge or relationship authority.

For an important entry, record:

- Expectation id and source fact/owner reference:
- Status: prepared | planted | available | paid_off | transformed | retired
- First shown evidence: turn/revision and what was actually presented, or not shown
- Audience/knowledge reference:
- Related horizon or act question:
- Availability or return trigger:
- Resolution/change evidence and resulting reference:

`prepared` is a GM possibility never presented as remembered player experience.
`planted` requires real shown evidence; `available` means a causal opportunity for
response exists, not a due date. `paid_off` needs an actual result; `transformed`
records how play gave it a different meaning. `retired` is valid for either an
unshown plan or an abandoned expectation; preserve whether it was ever shown.
Never upgrade an unshown plan to a remembered clue or force a payoff to clear a list.

At an act boundary consult only entries affected by the actual outcome, player
interest, or due return trigger. An expectation may carry forward unchanged.
New shown facts and meaningful status changes use the ordinary durable owner
transaction; reading or reviewing the list creates no revision by itself.

## Active Threads

### Thread Title

- Status: active
- Pressure:
- Who cares:
- What the player knows:
- What is hidden:
- Related issue or world-domain reference:
- Next player-relevant question or consequence:
- Player stance and source, if established: engaged | declined | deferred | unknown
- Last changed revision: 0

## Resolved Threads

Move completed threads here with a short note about how they resolved and what
consequence remains.

## Dormant Threads

Threads that are not currently pressing but may return later.
