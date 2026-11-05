# 02 — Research, Canon, And Grounding

## Purpose

Resolve the evidence and permission boundary before any source-sensitive truth
becomes durable. A fully original campaign still records why research is not
needed.

## Decision Order

1. `02_research_need_and_permission` — classify the grounding and obtain the
   allowed source/retrieval method.
2. `02_source_and_cast_scope` — bound sources to the initial playable scale and,
   when applicable, choose full canon, canon-world/original-cast, or
   genre-adjacent scope.
3. `02_canon_divergence_and_native_register` — state permitted divergence and
   the source register that later presentation may intentionally vary from.
4. `02_current_scale_lock` — separate verified claims, accepted bounded risk,
   and named open questions; explicitly permit or refuse current-scale locking.
   In the same decision settle the NPC power scale, before any cast exists: how
   strong the people at this scale are next to the character, and whether the
   scale is `closed` (one range for the whole campaign) or
   `region_anchored_open` (each region has its own cap; reaching a stronger
   region raises it at an act boundary). Record `npc_power_scale` in the value
   (the helper refuses the decision without it) and write the accepted scale to
   `boundaries.md` / Power Scale.

Record each with the fields in `decisions.md`: `02_research_need_and_permission`
takes `status` and `permission`; `02_current_scale_lock` takes `risk_accepted`,
`current_scale_lock_permitted`, and `npc_power_scale`, and depends on
`02_research_need_and_permission`.

Run the shared `research_gate.md` procedure when research is required. Research
execution and evidence review are control work, not hidden content decisions.

## Gate

Pass `research_scope_locked` only when research is not pending and current-scale
lock permission is explicit. A partial dossier may pass only for the covered
opening scale with its remainder named. `complete-stage` refuses, before
writing, a Stage 2 result this gate could not pass; correct the decision first.

## Materialization Boundary

The dossier and source/canon limits are immediate critical owners. At stage end,
persist evidence, version/date scope, contradictions, native register, character
grammar where relevant, and open questions. Do not copy source claims into world
truth owners yet.

## Do Not

- offer canon-dependent mechanics, institutions, names, powers, or travel rules
  before the gate;
- fill a source silence with remembered or genre-default certainty;
- treat research completion as design or readiness approval.

