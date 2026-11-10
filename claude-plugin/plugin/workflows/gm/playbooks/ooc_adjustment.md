# OOC Adjustment Playbook

Use for an unmistakable out-of-fiction direction, including one without an OOC
tag. Answer it directly and preserve its scope. It is not a character action,
consent to a fictional cost, or an excuse to rerun Session 0.

## Decide The Scope

| Request | Effect and owner |
| --- | --- |
| Shorten this reply/conversation; explain this moment | Apply locally. Do not rewrite permanent preferences or advance fiction. |
| Use shorter narration from now on; stop this GM habit; always or never do this | Update the matching profile selector, or `boundaries.md` for a content limit, preserving the other accepted settings. Any other lasting ruling, preference, or correction becomes a directive (below). |
| Leave this part of my character alone; I want a different ongoing activity | Update `player.md` / Experience Contract or Change Appetite, or a uniquely owned integration limit in `player_ties.md`. Adapt only dependent unplayed preparation. |
| Let me roll from now on; change tracking or resolution | Change the accepted runtime configuration and its required dependencies; do not invent an event, statistic, resource, or past roll. |
| That scene never happened; undo that accepted fictional result | This is an explicit retcon. Identify the exact affected truth and use the normal fictional owner transaction below. |

A restriction takes effect immediately. Stop or redirect the affected material
while its persisted correction is being prepared; never repeat it while waiting
for a check. Ask one narrow clarification only when scope or a consequential
result is genuinely ambiguous. Do not require a tag or repeat an already clear
authorization. A local instruction expires at its stated boundary and does not
become an inferred global preference. If an unfinished local direction must
survive interruption, retain its explicit scope/expiry with the existing relevant
behavior owner as a temporary instruction, separate from ongoing preferences.

## Record Standing Directives

A lasting OOC ruling, preference, or correction that no profile selector or
content limit covers becomes one row in `directives.md`; never stack prose
rules in `storytelling.md` or a reminder file. Add each row with an `append` op
on heading `Standing Directives` holding exactly one `{{next_id:D}}`, such as
`| {{next_id:D}} | global | Do not end replies with a question. | OOC request, revision {{revision}} | active |`.
Scope is `global`, `scene:<scene id>`, or `entity:<note title>`; Source is the
Player's OOC request with its date or revision. When the turn changes no
fiction, commit the row with one `commit-checkpoint` call that repeats the
current scene frame as its checkpoint; it may edit `directives.md` and
`glossary.md` and makes no fictional revision. When the turn also commits
durable fiction, put the row in that turn's one `commit-durable` call instead,
as a change whose kind contains `directive`, owned by `directives.md`. Retire a
row by setting its Status to `retired` (`upsert_row` keyed by its id, never a
deletion); a replacement is a new row that names the id it supersedes.
Directives shape table behavior only: they create no fiction and never override
`AGENTS.md`, safety boundaries, or a locked profile. A lasting correction to
how a recurring term, title, unit, or form of address is rendered is a
`glossary.md` row under `Terms` instead, committed the same way. In a campaign
without `directives.md` or `glossary.md`, the first such commit starts it from
the blank template.

## Persist Configuration Without Inventing Fiction

Pure accepted configuration/experience corrections are Designer maintenance.
Prepare only affected owner sections and dependent readable explanations, with a
short accepted scope/basis in the owning section rather than a transcript. The
locked profile stays the selector authority; update it when a selector changes.
Do not increment fictional continuity, append an RPG event, reopen completed
setup decisions, increment `setup_revision`, or rewrite historical startup
approval/snapshot evidence for a runtime correction.

For coupled maintenance writes, use the existing `tools.file_transaction`
`campaign_lock`, `recover`, and `commit_files` API in one local Python operation.
Hold the lock across recovery, current-owner reads, expected-byte/hash comparisons,
and the complete byte batch. Reject stale input rather than overwriting another
accepted change. Do not include `current_state.yaml`, `session_log.md`, or fictional
owner changes in this configuration batch. A coupled purely mechanical
initialization may include `mechanics_state.json`: for example, enable its existing
empty ledger when the accepted tracking setting now requires it, or initialize
configuration from already authoritative facts without changing those facts.
Preserve existing counters, roll history, resources, conditions, time, and operation
identities. Do not invent quantities, overwrite established values, resolve a roll,
or apply a fictional consequence under the name of initialization. This exception
lets the profile and its required enabled ledger become valid in the same batch.
Use `check_state.check_campaign(root, scope="full")` in the same process as the
`validate_applied` callback and raise on errors so the whole batch rolls back.
This is an explicit maintenance boundary, not a new per-turn check. Preserve
typed recovery failures and follow `docs/file-transactions.md`; never complete
partial writes manually or delete the journal to make the check pass.

A mechanics change that also establishes or alters fictional/mechanical truth
must use the relevant existing mechanics/RPG writer for that truth. Prepare the
complete dependency set first and resume dependent play only when its owners and
full validation agree. If the existing path cannot apply the requested change
coherently, keep the valid prior configuration and explain the concrete missing
dependency; do not claim that the new setting is operating.

## Change The Dice Scale

A stat or difficulty above the configured scale (a roll call refuses it as
`out_of_range`) needs an OOC scale change to `mechanics.resolution` first,
never a hidden "counts as" workaround. Show the Player the odds tables:
`python tools/odds.py campaign` for the current scale, and the same command on
a scratch folder whose `play_profile.yaml` holds only the proposed `mechanics:`
block. Apply the accepted change through the paths above, mapping every
existing value by one stated rule as the `rules.md` Scale Migration describes.

Any change to the die, the bands, the automatic-success margin, the factor
sizes, or the difficulty formula takes the same path, and the Player sees what
it does before deciding. Show the odds before and after on the campaign's real
matchups, not on the whole table: the value and difficulty pairs of the recent
receipts in `campaign/.repog-runtime/rolls.jsonl`, and the player character's
strongest axes against the `rules.md` Tier Caps. Give, for each pair, the chance
of each band before and after, and say plainly when a band becomes unreachable.

Offer "from the next roll" first: earlier receipts and their bands stay as
rolled. Only when the Player asks for the change to reach back, record each
affected earlier roll with one reread row, never by editing its receipt:

```sh
python tools/roll_dice.py --campaign campaign reread --input-file - <<'JSON'
{"roll_id": "dock-feint", "reason": "difficulty formula corrected by OOC request", "new_band": "partial_small_cost"}
JSON
```

A reread is never an open receipt and is never cited. A fictional result that
the new band changes is a retcon (below), committed once through the durable
writer.

## Answer A Language Complaint

When the Player says the prose reads wrong in the play language (a calque, a
foreign word, a stiff construction), acknowledge it in one line, then rewrite
the last reply in the same turn with the phrase gone. Keep the rewrite to the
same events; it changes wording, not fiction. Then record the phrase so it does
not return: as an entry in `narration.narrative_signature.avoid_habits` when the
Player wants it there, or as an example under the language directive in
`directives.md`, a replacement row that names the id it supersedes, or a new
`global` row when there is no language directive yet.

## Amend The Last Beat

"Write it as if I said it there" asks for a retro-edit of the last narrated
beat: the Player adds or changes what their character said or did in it. When
the change is the Player's own action and nothing after it depends on the old
version, amend that beat through one commit: a `commit-durable` when the
amended beat establishes a fact, otherwise a `commit-checkpoint` whose resume
anchor records it. Then show the Player the amended line as it now stands.
Narrate no reaction to the amended line unless the Player asks to continue
from it; a change that alters later results is a retcon (below).

## Keep A Retcon Causally Complete

An explicit retcon is not a style correction or a secondary summary edit. Read
the affected current-state, knowledge, relationship, thread, item, character,
and mechanic owners that actually depend on the named result. Clarify only an
unresolved consequential scope. Preserve unrelated earned truth and record the
correction's basis in the semantic capture; historical events remain history,
not a competing current version.

Apply the coherent current-truth correction through one `rpg_state.py
commit-durable` transaction and any supported mechanic operations. Never edit
only a recap, erase receipts, restore an old snapshot over later independent
events, or narrate a correction that is not persisted in the same turn.
Reconcile dependent prep/projections at the required boundary. If a necessary
dependent change cannot be represented safely, use Designer recovery instead of
a partial retcon.

After a successful correction, refresh only affected source pointers/preparation
and continue from the retained scene anchor. A preference correction does not
decide the character's feelings, erase prior choices, or grant a promised outcome.
