# 01 — North Star And Authority

## Purpose

Fix what is being created, what experience it promises, and who may author which
truth. Do not design the world, cast, or first act yet.

## Play Language First

Before the first content decision, settle the play language: the language the
Player writes in, unless they ask for another. Confirm it in one line in that
language; it is not a content decision and does not count. Record it with
`session_zero_state.py campaign set-language --language <code>` (or
`set-depth --language` at the depth choice). The helper refuses a new Stage 1
decision and Stage 1 completion while it is unset or `auto`.

From then on, write every record's content in that language: descriptions,
summaries, facts, names, Notes cells, `## Now` and History lines, Depth and
Agency Card values, thread text. Keep the structure exactly as the templates
write it: file names, YAML keys, headings, `- Label:` names, table headers,
enum values, and ids.

## Decision Order

Use the manifest decision ids in this order:

1. `01_campaign_frame_and_reach` — source/world anchor, starting slice, and
   `contained | regional | long_journey | episodic` reach.
2. `01_player_fantasy_tone_and_non_goals` — desired play, tone, and what the
   campaign must not become.
3. `01_content_boundaries` — run `../playbooks/content_boundaries.md`: the
   notice, the two fixed rows, the per-row settings, the limits the GM states,
   and an optional stop word. Limits remain editable in play without cost.
4. `01_agency_authorship_and_consequence` — Player-character authorship and the
   accepted consequence ceiling.
5. `01_creation_authority` — approval-first, bounded inference, or broad
   world-side preparation within locked boundaries.
6. `01_primary_topology_intent` — choose `exploration_survival`,
   `political_intrigue`, `personal_drama`, or `mixed`. For `mixed`, name its
   primary non-mixed topology now.

Ask one decision per message. Do not let a bundle silently answer another item.
Record each with the fields in `decisions.md`; `stage-owners --stage-id
01_north_star_authority` lists this stage's owner files and value contracts.
For schema-v10+, reuse the short premise captured before the explicit depth
choice. The intake made no decision/count/revision change; record its answer
through this stage's normal boundary without asking it again. It does not imply
research, authorship, or creation permission.
Complete only its still-unresolved frame/experience choices; do not ask for the
same premise again. Keep an early later-stage answer in the existing decision
summary until its dependency permits the corresponding owner write.

## Trigger Scan

After each accepted answer, record only exact manifest trigger tags supported by
that answer. A `long_journey` may tag `reach.long_journey`; it does not itself
invent routes, companions, or factions.

## Materialization Boundary

Write every critical owner in the acceptance turn. Before completing the stage,
materialize the compact campaign promise, setup progress, authority rules, and
topology intent. Record unresolved research as a Stage 2 dependency, not a world
fact. Store Player-authorship and consequence authority in `boundaries.md`; do
not create the playable `player.md` card before Stage 5. `complete-stage`
refuses while the play language is unset, a fixed content row is missing, or
the Sexual content or Harm to children setting is not one of its options.

## Do Not

- research after presenting source-dependent options;
- infer a hard boundary, source permission, mechanic, or protected PC fact;
- create named cast, locations, issues, or a first-act plot.
