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
Player's OOC request with its date or revision. Commit it in the turn's one
`commit-durable` call as a change whose kind contains `directive`, owned by
`directives.md`. Retire a row by setting its Status to `retired` (`upsert_row`
keyed by its id, never a deletion); a replacement is a new row that names the
id it supersedes. Directives shape table behavior only: they create no fiction
and never override `AGENTS.md`, safety boundaries, or a locked profile. A
campaign begun before 0.3.0 first needs the blank `directives.md` from the
plugin's campaign template, copied in Designer Mode.

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
events, or narrate a correction before persistence succeeds. Reconcile dependent
prep/projections at the required boundary. If a necessary dependent change cannot
be represented safely, use Designer recovery instead of a partial retcon.

After a successful correction, refresh only affected source pointers/preparation
and continue from the retained scene anchor. A preference correction does not
decide the character's feelings, erase prior choices, or grant a promised outcome.
