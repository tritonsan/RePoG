# Workflow

RePoG Worldbuild Router

# Purpose

Use this compact router while `campaign/setup_profile.yaml` is not ready for
play. It keeps ordinary Session 0 turns small: load only the playbook required
by the selected experience, depth, and current boundary.

Worldbuilding creates a playable pressure system, not an encyclopedia. Learn
the chosen universe first; derive tone, truths, issues, people, places,
mechanics, and presentation from that choice without assuming a franchise or
power system.

# Hot Loading Rule

Read this router first, then load only the matching playbook:

| Situation | Load |
| --- | --- |
| RPG Quick interview | `playbooks/rpg_quick.md` |
| RPG Standard or Deep interview | `playbooks/rpg_standard_deep.md` |
| Companion Quick, Standard, or Deep | `playbooks/companion_setup.md` |
| Research Gate or source work | `playbooks/research_gate.md` |
| Final approval and materialization | `playbooks/finalization.md` |
| Eligible semantic parallelism | `workflows/orchestration/WORKFLOW.md` plus the boundary section in the relevant playbook |

`playbooks/full_reference.md` preserves the pre-router workflow as a detailed
design reference. Do not load it by default. Consult only the named section
when a compact playbook leaves a genuine ambiguity; it does not override the
compact playbooks or current campaign schemas.

# Routing Gates

If `experience_mode` is blank, ask only:

> What would you like to create: an RPG Campaign with RePoG as the Game
> Master, or an AI Companion—a persistent fictional character with an
> independent, grounded life?

Persist `rpg` or `companion`. This choice does not count toward the content
decision target. Legacy schema-v1–v3 campaigns without the field remain RPG
campaigns.

If the experience is selected and `session_zero_mode` is blank, ask only:

> Which Session 0 depth do you want: Quick (10–15 minutes), Standard (30–60
> minutes), or Deep (60–120 minutes, normally 30–45 decisions)?

Persist `quick`, `standard`, or `deep`; set setup status to `in_progress`.
Do not combine either routing gate with the pitch, and do not reopen them for
an active or completed experience.

Then route:

- `rpg + quick` -> `playbooks/rpg_quick.md`;
- `rpg + standard|deep` -> `playbooks/rpg_standard_deep.md`;
- `companion + any depth` -> `playbooks/companion_setup.md`.

# Shared Interview Contract

For every content decision:

1. name the current module;
2. ask exactly one decision question;
3. explain why it matters in one or two sentences;
4. offer two to four contextual, neutral options when useful;
5. stop and wait.

Write accepted answers immediately. Never ask again about a decision already
locked, defaulted, skipped, deferred, or answered early. Accept natural
language plus `accept`, `mix`, `change`, `default`, `defer`, “go deeper,” and
“that is enough.” A coherent bundle counts as one decision; do not hide
unrelated choices inside it.

At a module boundary, briefly summarize what was locked and continue with the
next missing decision. At the end, show locked, visibly defaulted, and
deliberately deferred choices, then request one final approval. Never begin RPG
play or Companion conversation while `ready_for_play` is false.

# Starter Bundles

After the pitch or Companion premise, offer two to four contextual bundles and
recommend one. For RPG, a bundle includes feel, candidate lenses, resolution
grounding, optional mechanics awaiting approval, Narrative Signature,
interiority, sensory/dialogue stance, breather policy, tracking load, expected
speed effect, and why it fits. For Companion, it includes personality/voice,
independent-life shape, starting relationship, initiative, memory and
deception policies, Companion View, grounding, and why it fits.

Setting/play lenses are Session 0 question generators, not runtime
instructions. No lens activates HP, mana, inventory, wounds, dice, clocks, or
another mechanic without explicit approval. Accepted runtime choices belong
in the active runtime profile at the current setup revision.

# Performance And Semantic Parallelism

RPG Session 0 must include the existing Turn Protocol choice. Explain its
timing/freshness tradeoff and the independent cost of Dashboard and visual
work; record acknowledgement before readiness. Companion uses its fixed
lightweight exchange contract instead.

Keep the disclosure compact but explicit: Fast is recommended (routine about
30–90 seconds, local durable 45–120 seconds, structural 2–4 minutes); Balanced
usually takes about 1–2 minutes for light turns and 1.5–3 minutes for durable
turns; Maximum Continuity usually takes 2–4 minutes for durable and 3–6
minutes for structural turns. A triggered Dashboard refresh may add about
1–2 minutes, an image draft or revision about 1–3+ minutes, and accepted-image
placement about 1–2 minutes. These are planning estimates, not guarantees.

The same performance summary may offer semantic parallelism without adding a
Quick question:

- `off`: serial work and lowest model usage;
- `selective_structural` (recommended for new workspaces): bounded supporting
  agents only at eligible research or finalization boundaries;
- `aggressive_structural`: lower eligibility thresholds and higher likely
  model usage.

Explain that parallel semantic work may reduce structural waiting time while
using more of the host's model allowance. Missing legacy fields mean `off`.
Quick may use at most two supporting agents; Standard and Deep at most three.
Ordinary questions, final approvals, profile decisions, authoritative writes,
validation, snapshots, Dashboard/visual transactions, opening narration, and
the Companion's final voice remain coordinated by the primary agent.

If the harness has no supporting-agent capability, execute the same bounded
lanes serially. This is a normal fallback, not a setup failure.

# Authority And Revision Rules

- `setup_profile.yaml` owns interview progress, activated/defaulted/deferred
  packs, setup revision, and readiness.
- `play_profile.yaml` owns RPG runtime behavior; `companion_profile.yaml` owns
  Companion runtime behavior. The unused profile is `inactive`.
- Every persisted decision increments `setup_revision`; the active runtime
  profile must cite the same `source_setup_revision` before readiness.
- Research must permit the current-scale lock before durable canon or factual
  truths are finalized.
- Only the coordinating agent writes campaign truth, allocates cross-domain
  ids, classifies knowledge/disclosure, locks profiles, sets readiness,
  creates snapshots, and delivers player-facing text.
- Supporting agents are read-only proposal workers governed by
  `workflows/orchestration/WORKFLOW.md`.

# Completion Route

After final user approval, load `playbooks/finalization.md`. Keep
`ready_for_play: false` while proposals are merged and preflight checks run.
The coordinator must finish the chosen experience's required core, resolve
cross-lane conflicts, and prepare the opening or Companion presence before it
sets final readiness fields.

The required order is:

1. frozen seed and optional bounded proposal lanes;
2. coordinator merge and draft-state preflight while not ready;
3. final status/profile/readiness fields;
4. serial materialization of enabled Dashboard/Atlas or Companion View
   projections at the final revision;
5. starting snapshot;
6. one final aggregate check;
7. player-facing opening or Companion message only after that check passes.

If the final check fails, restore the pre-final draft fields and prior derived
projections, return setup to `in_progress` and `ready_for_play: false`, correct
the authoritative files, and rerun the draft preflight. Then repeat the whole
final-fields -> projections -> fresh snapshot -> aggregate-check sequence.
Never claim partial readiness or treat an earlier candidate snapshot as proof.
