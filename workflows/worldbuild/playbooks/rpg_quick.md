# RPG Quick Session 0

Load this playbook only after the router has selected `rpg + quick`. Quick
must produce a small playable V2/V3 core in 6–8 content decisions, with every
inferred choice shown as a default. The experience and depth gates do not
count.

# Decision Sequence

Use this order and combine only closely related choices:

1. campaign pitch: universe, tone, player fantasy, and what play must not
   become;
2. one contextual Starter Bundle;
3. boundaries plus agency, consequence, and content stance;
4. player-character concept, defining competence, limitation, and appearance
   direction;
5. starting scale, current pressure or calm affordance, first place, and
   character connection;
6. mechanics/progression/failure plus the required Turn Protocol and semantic
   parallelism summary;
7. narration, options, Dashboard, visual mode, and cost acknowledgement;
8. final summary approval, including all defaults and deferred choices.

Research is conditional. If it is needed, use
`playbooks/research_gate.md` and keep the total within eight decisions by
folding its bounded result into final approval rather than silently accepting
risk.

# Immediate Persistence Map

Do not hold accepted answers only in an in-memory final seed. On the same turn
as each accepted decision, write its semantic owners, update the decision in
`session_zero.md`, then increment `setup_profile.yaml.setup_revision` and sync
the active profile's `source_setup_revision`. Leave a module open if that write
cannot be completed. Do not run a full check after each answer.

| Decision | Immediate authoritative persistence |
| --- | --- |
| 1. Pitch | `campaign_one_pager.md`; premise/summary in `world.md`; campaign id and Pitch progress in setup/session files |
| 2. Starter Bundle | accepted lenses, resolution, narration and breather contract in `play_profile.yaml`; readable fit in `system_fit.md`; resolved lens stance in `world.md` |
| 3. Boundaries | `boundaries.md`, relevant Yes/No/Maybe entries in `palette.md`, and Group Contract progress |
| 4. Character | `player.md`, appearance stance in `appearance_guide.md`, and immediately known ties/limits in `player_ties.md` / `knowledge_boundaries.md` |
| 5. Pressure and place | `issues.md` / `threads.md`, `world.md`, `places/*.md`, `faces_and_places.md`, draft `location_graph.md`, relevant `active_cast.md`, and draft starting state/opening files |
| 6. Mechanics and performance | modules, advancement and performance in `play_profile.yaml`; `system_fit.md`, `rules.md`, `progression.md`; `mechanics_state.json` only for approved stateful modules |
| 7. Narration, Dashboard, visuals | profile narration/dashboard/visual policies, `storytelling.md`, `visual_style.md`, `visual_gallery.md`, and resumable `visual_state.json`; derived Dashboard/Atlas files wait for finalization |
| 8. Final approval | approval/default/deferred record and module statuses in setup/session files; it authorizes finalization but does not first persist earlier answers |

Conditional research status, evidence, open questions, risk, and current-scale
permission go to `research_dossier.md` before dependent truth is locked.

# Starter Bundle Defaults

Offer two to four pitch-specific choices. Each shows:

- intended play feel and proposed setting/play lenses;
- `fictional`, `bands`, or `numeric` resolution grounding;
- mechanics that remain off unless explicitly accepted;
- three short Narrative Signature anchors and up to three avoid habits;
- interiority, at most two sensory priorities, dialogue balance, humor,
  emotional distance, breather frequency, and exit policy;
- tracking and expected speed effect;
- why one option is recommended.

With no stronger signal, use `fictional`, `player_owned`, balanced dialogue,
situational humor, close emotional distance, balanced breathers, and
`player_led_with_established_triggers`. Anchor prose on concrete sensory
evidence, character-specific plain dialogue, and causal consequence before
exposition. Avoid cryptic-default speech, recycled stock gestures/metaphors,
and tension manufactured after clean success.

Read only candidate briefs from `briefs/lenses/INDEX.md`. Fantasy alone does
not imply mana or HP; survival alone does not imply strict consumables. Ask for
explicit approval before enabling a stateful deterministic module.

# Required Quick Core

Infer only enough content for the first playable scale:

- a short campaign promise and World Operating Model;
- three to seven playable truths;
- at least one current issue/thread or a mode-appropriate calm affordance with
  campaign-level pressure elsewhere;
- one starting place with routine, access, reaction point, ordinary activity,
  and location connections;
- only the T1–T3 faces/factions needed for opening play;
- T2/T3 Agency Cards, natural presence, knowledge boundaries, and contrast;
- player concept, permissions/limits or approved bands/numbers, and player
  ties that revise the world;
- an actionable opening with neutral choice space and a resumable scene frame;
- the accepted continuity, advancement, Dashboard, visual, and Turn Protocol
  policies.

Every inferred answer must appear in `setup_profile.yaml.defaulted_packs` or
the defaulted section of `session_zero.md`. “Use defaults” selects Fast and
`selective_structural` for a new workspace only after the displayed timing,
freshness, usage, Dashboard, and visual caveats are acknowledged.

# Quick Performance Card

Present the existing planning estimates as estimates, not guarantees:

- Fast: routine 30–90 seconds, local durable 45–120 seconds, structural
  boundaries 2–4 minutes;
- Balanced: light 1–2 minutes, durable 1.5–3 minutes;
- Maximum Continuity: durable 2–4 minutes, structural 3–6 minutes;
- Dashboard refresh: about +1–2 minutes when triggered;
- image draft/revision: about +1–3+ minutes each;
- accepted gallery/Dashboard placement: about +1–2 minutes.

Add that selective semantic parallelism can shorten eligible setup/research
boundaries but may increase model allowance use. It does not change normal
turn behavior or continuity requirements.

# Quick Finalization

After final approval, load `finalization.md`. Quick has a hard cap of two
read-only proposal workers:

1. world ecology: truths, pressures, factions, world domains;
2. cast and space: NPC/place cards, natural presence, relationships, routes.

The coordinator owns player/profile truth, knowledge classification, stable
ids, current state, opening, presentation, readiness, snapshot, and checks.
If either lane is too small or dependent, run it serially.
