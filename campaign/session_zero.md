# Session Zero

Campaign id: `new_campaign`

Use this file as the campaign creation decision log. It is not a transcript.
Keep each module short, current, and useful at the table.

## Session 0 Profile

- Experience: pending (rpg | companion)
- Depth: pending
- Activated Deep packs: none
- Decisions completed: 0
- Question target: pending
- Last checkpoint: 0
- Locked decisions: none
- Defaulted decisions: none
- Deferred decisions: none
- Defaults reviewed at final summary/preparation approval: no
- RPG design direction approved revision: pending
- RPG integrated materialized preparation review: pending
- RPG preparation approved revision: pending
- Deep extension beyond 45 approved: no
- Starter Bundle: pending, route-split, or legacy-single-decision
- Accepted setting lenses: none
- Accepted play lenses: none
- Runtime profile: pending (`play_profile.yaml` for RPG,
  `companion_profile.yaml` for Companion)
- Expected routine turn: pending
- Expected durable turn: pending
- Expected structural / boundary turn: pending
- Semantic parallelism: selective_structural (default; structural boundaries
  only, when supported)
- Maximum parallel workers: 2 (safe default; RPG Standard/Deep may choose 3)
- Parallelism tradeoff: potentially shorter structural waits with higher model
  usage; unsupported tools use the same serial workflow
- Dashboard refresh cost: approximately +1–2 minutes when run
- Companion View cost: no ordinary-message refresh; a small local update only
  when already-shared visible truth changes
- Image generation cost: approximately +1–3+ minutes per draft
- Performance estimate acknowledged: no
- Legacy Standard/Deep/Companion final confirmation: pending
- Current RPG preparation approval: pending

The experience and depth gates are routing questions and do not count in the
content-decision total. Triggered research execution/evidence review and any
explicit source-scope or unavailable-source risk permission are also budget-
exempt, but each unresolved permission still receives its own turn and setup
revision. Deep checkpoints and extension permission are control turns. The
first accepted completion of a decision increments `questions_completed`;
revising that completed decision increments `setup_revision` only.

A recorded decision is a consequential Player choice. Operational fields the
coordinator materializes to honor that choice are not decisions and never
increase the count. A value mechanically entailed by an accepted answer is not
an inferred default either; only a coordinator choice among plausible ordinary
alternatives receives a stable label here.

Current RPG reciprocity routes use two revision-bound approvals. Schema-v6+
Quick records design approval at slot 8, reviews actual materialized
preparation at slot 9, and records preparation approval at slot 10. Schema-v7
Standard/Deep uses modules 19, 20, and 21 for the same boundaries. Preparation
is materialized while not ready; design changes clear both approvals and
preparation-only changes clear preparation approval. Schema-v7 Deep resolves
all activated packs before module-19 approval.

Schema-v8 Deep instead records decisions, stage extensions, output digests,
and both approvals in `session_zero_state.json`. Its decision count is a
fatigue signal rather than a readiness quota, and this file only displays the
managed summary below.

Quick and schema-v7 Standard/Deep use a factual integrated review followed by a
separate readiness go/no-go. Schema-v8 Deep combines those functions in its
second and final Player approval: show the audited preparation once and ask the
Player to request a correction or `lock and start`. No route may introduce new
campaign truth during readiness approval.

## RPG Quick Decision Slot Status

Use this block only for schema-v6+ `rpg + quick`. Standard/Deep use their
schema-appropriate status block; Companion uses its own block. A revised
completed slot keeps its completed count and receives a newer setup revision.

- 1. Campaign Promise And Player Fantasy: open
- 2. Character Identity, Current Desire, And Why Now: open
- 3. Competence, Limitation, And Social Position: open
- 4. Agency, Authorship, And Boundaries: open
- 5. Play And System Contract: open
- 6. Presentation Contract: open
- 7. Character–World Relationship Pattern: open
- 8. Reciprocity Design Review: open
- 9. Integrated Preparation Review: open
- 10. Preparation Approval: open

### Quick Approval References

- Design direction approved revision: null
- Preparation materialized while ready_for_play false: no
- Integrated preparation reviewed player-safe: no
- Preparation approved revision: null
- Approval invalidation notes:

## RPG Standard / Deep Reciprocity Module Status

Use this block only for schema-v7 `rpg + standard|deep`. Quick uses its 10-slot
block; schema-v1–v6 Standard/Deep and legacy Quick use the legacy Module Status
block. A revised completed module keeps its completed count and receives a
newer setup revision.

- 1. Campaign Promise And Player Fantasy: open
- 2. Research Need And Source Boundary: open
- 3. Agency, Authorship, And Content Boundaries: open
- 4. Character Identity, Current Desire, And Why Now: open
- 5. Competence, Limitation, Social Position, And Change Appetite: open
- 6. Play And System Contract: open
- 7. Presentation And Visual Contract: open
- 8. Canon Policy: open
- 9. Palette: open
- 10. World Truths And Operating Model: open
- 11. Scale, Everyday Life, Access, And Routes: open
- 12. Independent Issues And World Dynamics: open
- 13. Factions And Institutions: open
- 14. Faces, Places, And Independent Relationships: open
- 15. Progression And Rewards: open
- 16. Character–World Reciprocity Pass: open
- 17. Starting Situation Design: open
- 18. Continuity, Ownership, And Preparation Contract: open
- 19. Reciprocity Design Review: open
- 20. Integrated Materialized Preparation Review: open
- 21. Preparation Approval: open

### Standard / Deep Approval References

- Design direction approved revision: null
- Activated Deep packs resolved before design approval: not-applicable | no |
  yes
- Preparation materialized while ready_for_play false: no
- Integrated preparation reviewed player-safe: no
- Integrated preparation accepted revision: null
- Preparation approved revision: null
- Approval invalidation notes:

## RPG Deep v8 Stage Summary

- Flow: `rpg_deep_v8`
- Setup revision: 0
- Current stage: North Star And Authority (`01_north_star_authority`)
- Decisions recorded: 0

### Deep v8 Stages

| Stage | Status | Decisions |
| --- | --- | ---: |
| North Star And Authority | active | 0 |
| Research, Canon, And Grounding | not_started | 0 |
| Character Core | not_started | 0 |
| Thin World Kernel | not_started | 0 |
| Character Realization And Mechanics | not_started | 0 |
| Living World Ecology | not_started | 0 |
| Runtime Experience Contract | not_started | 0 |
| Reciprocity And Campaign Horizon | not_started | 0 |
| First Act Preparation | not_started | 0 |

### Deep v8 Extensions

- `character_interior`: not_applicable
- `world_fabric`: not_applicable
- `mechanics_detail`: not_applicable
- `location_network`: not_applicable
- `faction_information`: not_applicable
- `group`: not_applicable
- `character_embedding`: not_applicable
- `advancement_detail`: not_applicable
- `campaign_architecture`: not_applicable

### Defaults And Deferrals

- None

### Deep v8 Gates

- `research_scope_locked`: pending
- `stages_1_8_complete`: pending
- `first_act_design_complete`: pending
- `design_direction_approved`: pending
- `preparation_materialized`: pending
- `cross_read_passed`: pending
- `integrated_review_accepted`: pending
- `preparation_approved`: pending
- `draft_preflight_passed`: pending
- `ready_and_snapshotted`: pending

## Companion Module Status

Use this section only when Experience is `companion`. Leave both RPG status
blocks as inactive templates; only this selected block participates in
Companion readiness. For RPG, this block is inactive and the schema-selected
RPG status block participates in readiness.

- Premise And World: open
- Identity And Appearance: open
- Home, Work, Education, And Economics: open
- Routine, Hobbies, And Obligations: open
- Values And Moral Lines: open
- Psychology And Contradictions: open
- Voice And Messaging Habits: open
- Backstory And Turning Points: open
- Social Circle: open
- Life Problems, Projects, And Goals: open
- Initial User Relationship: open
- Relational Evidence, Conflict, Boundaries, And Repair: open
- Concealment, Topic Disclosure, Deception, And Help: open
- Time, Initiative, User Memory, Performance, And Privacy: open
- AI Transparency, Portrait, Companion View, And Final Confirmation: open

### Companion Runtime Summary

- Primary companion id:
- Starter Bundle:
- Setting: real_city_fictional_private | fictional_world
- Public city/time grounding:
- Private people and places: fictional
- Starting relationship:
- Allowed relationship scope:
- Adult and boundary gates confirmed:
- Channel: async_text
- Conversation language:
- Response length:
- Initiative:
- Humor:
- Advice/list/question habits:
- Life density: grounded
- Offline progression: reconcile_on_next_message
- Autonomy: causal
- User memory: off | ask_before_save | contextual_low_risk
- Sensitive memory: explicit_consent_only
- Disclosure logic:
- Direct deception: no_direct_lies | character_consistent_opt_in
- Boundary reference:
- Layered transparency confirmed:
- Direct identity answer confirmed:
- Portrait: off | optional_manual | setup_once
- Companion View: off | light
- RPG Dashboard: off
- Exchange persistence: single_begin_exchange
- Semantic parallelism: off | selective_structural | aggressive_structural
- Maximum parallel workers: 1–2 for every Companion depth
- Companion parallelism usage notice acknowledged: no
- Defaulted persona/life decisions:
- Deferred decisions:

### Companion Deep Packs

- companion_persona: inactive
- life_fabric: inactive
- backstory_and_turning_points: inactive
- social_ecology: inactive
- relationship_and_intimacy: inactive
- conversation_voice: inactive
- real_world_grounding: inactive
- long_horizon_development: inactive

## Module Status

Use this block for schema-v1–v6 RPG Standard/Deep and legacy RPG Quick. For
schema-v6+ Quick and schema-v7 Standard/Deep it is a semantic reference only;
readiness follows the route-selected status block above.

- Campaign Pitch: open
- Research Need Gate: open
- Group Contract: open
- System Fit: open
- Canon Policy: open
- Palette: open
- Visual Mode And Art Direction: open
- World Truths: open
- Scale: open
- Current And Impending Issues: open
- Factions: open
- Faces And Places: open
- Progression And Rewards: open
- Player Character: open
- PC Integration: open
- Starting Situation / Session 0.5: open
- Continuity Rules: open

Status terms:

- `locked`: decided and safe to use.
- `open`: still needs a Designer answer.
- `defaulted`: Codex chose a coherent default because the Designer allowed it.
- `defer`: intentionally left for play to discover.
- `inactive`: belongs to the unselected RPG/Companion experience.
- `locked_with_open_questions`: safe at the current scale, with named limits
  that remain unresolved.

## Starter Bundle Decision

After the campaign promise, prepare two to four contextual options. Current
schema-v7 RPG routes use them as support but accept system values in module 6
and presentation values in module 7; schema-v6+ Quick accepts those sides in
slots 5 and 6. One response never silently accepts both. An accepted option
enables only the stateful mechanics and optional Dashboard, visual, or World
Voices layers it states explicitly; anything omitted stays off, and no layer
enables another by implication. Legacy Standard/Deep and Companion may retain
their existing single bundle decision. Each option must state:

- how the campaign should feel;
- proposed setting and play lenses;
- proposed tracking/mechanics, clearly marked as suggestions;
- expected tracking load and approximate speed effect;
- why the option fits the pitch.

- Response: accept | mix | change | default | defer
- Accepted bundle:
- Mixed or changed elements:
- Defaulted assumptions:
- Deferred questions:
- Explicitly approved mechanics:
- Explicitly declined mechanics:
- Resolution grounding: fictional | bands | numeric
- Narrative Signature anchors, maximum 3:
- Narrative habits to avoid, maximum 3:
- Interiority policy: player_owned | shared_when_invited | guided
- Sensory priorities, maximum 2:
- Dialogue balance: dialogue_forward | balanced | narration_forward
- Humor: minimal | situational | frequent
- Emotional distance: close | moderate | detached
- Breather frequency: sparse | balanced | generous
- Breather exit policy: player_led | player_led_with_established_triggers |
  world_led
- World Voices: off | manual | curated | reactive
- World Voices approval: review_each | preapproved_bounded
- World Voices Dashboard: off | delivered_only | delivered_and_public
- Artifact richness: concise | balanced | rich
- Communication speed: slow | mixed | fast | setting_defined

`accept` accepts the displayed bundle, including only mechanics clearly listed
for approval. `mix` combines named parts of displayed bundles. `change` asks
for a replacement set. `default` permits the recommended coherent choice and
records every assumption as defaulted. `defer` postpones only non-critical
details; it cannot bypass safety, research, readiness, or an active Deep-pack
critical decision.

## Legacy 17-Module Decision Detail

The numbered sections below preserve schema-v1–v6 Standard/Deep semantic
prompts. Schema-v7 Standard/Deep records the same durable subjects through its
21-module status block and authoritative compact playbook; these headings do
not change its order or approval boundaries.

## 1. Campaign Pitch

- Universe or genre:
- Tone:
- Player fantasy:
- Core play feel:
- This campaign is not:
- Starter Bundle decision:

## 2. Research Need Gate

See `research_dossier.md`.

- Research mode:
- Setting classification:
- Cast scope: full_canon | canon_world_original_cast | genre_adjacent_original
- Timeline anchor:
- Native register and accepted divergence:
- Research status:
- Web search decision:
- Source scope, bounded to the initial playable scale:
- Open source questions:
- Risk accepted: no
- Current-scale lock permitted: no
- Budget accounting: gate work and explicit scope/risk permission turns do not
  increment questions_completed
- Risk acceptance notes:

## 3. Group Contract

- Content boundaries:
- Tone boundaries:
- Agency expectations:
- Failure and consequence appetite:
- Clarification preference:

## 4. System Fit

- Dominant play modes:
- Mechanics weight:
- Resolution grounding: fictional | bands | numeric
- Stat model, only when numeric:
- Starting level:
- Deterministic checks:
- Deterministic resources/cooldowns/regeneration:
- GM judgment zones:
- Accepted setting lenses: fantasy | realistic | cyberpunk | custom:<slug>
- Accepted play lenses: survival | custom:<slug>
- Lens conflicts and precedence:
- Approved mechanic modules (`mechanics.modules`):
- Inventory tracking: abstract | quantified | encumbrance
- Time tracking: coarse | scene | step
- Travel tracking: abstract | route_time
- Wound tracking: narrative | conditions
- Dice mode: judgment_only | player_rolls | open_gm_rolls | hidden_gm_rolls |
  hybrid
- Turn protocol: fast | balanced | maximum_continuity | custom
- Routine-turn estimate:
- Durable-turn estimate:
- Structural / boundary-turn estimate:
- Cold distill policy: every_durable | scene_checkpoint_or_3_durable |
  scene_checkpoint_or_5_durable | scene_checkpoint_only
- Validation policy:
- Dashboard refresh policy:
- Style review policy:
- Latency notice policy:
- Semantic parallelism: off | selective_structural | aggressive_structural
- Maximum parallel workers: 1–2 in Quick; 1–3 in Standard/Deep
- Performance estimate acknowledged:

Materialize accepted runtime choices in `play_profile.yaml`. Keep
`setup_profile.yaml` limited to interview progress, pack completion, readiness,
and revision metadata.

## 5. Canon Policy

- Canon status:
- Allowed canon elements:
- Restricted canon elements:
- Player action versus canon:
- Ask before durable:

## 6. Palette

See `palette.md`.

## 7. Visual Mode And Art Direction

See `visual_style.md` and `visual_gallery.md`.

- Visual mode:
- Quota stance:
- Generation targets:
- Appearance detail level:
- Art direction:
- Visual canon policy:
- Display policy:
- Dashboard mode: off | on
- Dashboard refresh policy: manual | scene_only |
  scene_and_major_visible_change | every_visible_change
- Dashboard tiles:
- Dashboard map skin: auto | minimal | survey | civic | field | systems
- World Voices policy and likely communication channels:
- Accepted visual placement: gallery_only | dashboard_after_approval
- Dashboard refresh cost acknowledged:
- Image generation and revision cost acknowledged:

## 8. World Truths

See `world_truths.md`.

## 9. Scale

- Initial playable scale:
- First-session onstage area:
- Offscreen until later:
- Power/travel implications:
- Coarse fictional time model:
- Starting location connections and access boundaries:
- Ordinary traffic and news-travel assumptions:

## 10. Current And Impending Issues

See `issues.md`.

## 11. Factions

- Initial faction scope:
- Factions created:
- Factions deferred:
- Independent next moves and evaluation triggers:

## 12. Faces And Places

See `faces_and_places.md`.

- NPC ecology and ordinary work:
- Routine and availability expectations:
- Relationship asymmetries:

## 13. Progression And Rewards

See `progression.md`, `arc_closure.md`, and `next_act_prep.md`.

- Arc dramatic question and closure signals:
- Crew or group social contract:
- Advancement cadence: session | scenario | arc | campaign | none
- Advancement presentation: explicit_ooc | automatic_fictional | none

## 14. Player Character

See `player.md`.

## 15. PC Integration

See `player_ties.md`.

## 16. Starting Situation / Session 0.5

See `opening_brief.md` and `first_session.md`.

- First-session prep status: drafting | materialized | consumed
- Opening status: pending | active | consumed
- Opening scene mode: ambient | focused | crisis | aftermath | transition |
  breather

## 17. Continuity Rules

- Creation capture:
- Relationship capture:
- Active cast ownership:
- Location graph ownership:
- Secret and clue handling:
- Knowledge boundaries:
- Research/source boundaries:
- NPC knowledge limits:
- Power escalation limits:
- Progression and reward cadence:
- Companion advancement:
- Selective hot context:
- Triggered lookups:
- On-demand world domains:
- Source-of-truth ownership map:
- Context revision and source-of-truth precedence:
- Visual generation:
- Visual canon:
- Designer approval triggers:
- Distill expectations:
- Maximum durable turns before cold distill:
- Mandatory structural/boundary triggers:
- Durable event log and recovery policy:

## RPG Reciprocity Design Review

Complete this player-safe design display before the selected route's design
approval—Quick slot 8 or schema-v7 Standard/Deep module 19. It is a coherent
direction, not a claim that preparation is already finished. Deep must have no
unresolved activated pack.

- Character seed: identity, current desire, why now, social position
- Competence and world affordance:
- Limitation, cost, pressure, and counterplay:
- Character-originated anchor or explicit approved isolation:
- World-independent issue/domain/process:
- Playable intersection:
- Place/routine/belonging or arrival pattern:
- Independent NPC/faction relationship and its own agenda:
- Opening causal fit:
- Neutral action-space promise:
- Backstory invention boundaries:
- Player-known design summary:
- Hidden material excluded from review:
- Design direction approved: no
- Design direction approved revision: null

## RPG Integrated Materialized Preparation Review

Complete this only after design approval and after actual opening-scale
preparation has been written while `ready_for_play: false`. Quick performs this
at slot 9; schema-v7 Standard/Deep performs it at module 20. Show player-safe
prepared truth, not placeholders or a second abstract proposal, and ask whether
it is accurate, complete at the promised scale, and faithful to the approved
direction. The following preparation approval is a separate go/no-go on that same
unchanged preparation; it must not show a default or prepared fact for the first
time.

- Prepared character summary and current desire:
- Prepared competence affordance:
- Prepared limitation/counterplay:
- Prepared character-originated anchor or explicit isolation:
- Prepared independent issue/domain/process and next movement:
- Prepared intersection:
- Prepared starting place, routine, access, and arrival:
- Prepared relationship/NPC/faction with independent work and obligation:
- Prepared visible opening situation:
- Naturally present people and why they are present:
- Neutral actions available without accepting a quest:
- Backstory facts used and invention boundaries honored:
- Player-safe defaults and deferrals shown:
- Hidden truths intentionally excluded:
- First-session prep status: materialized
- Opening status: active
- Integrated preparation accepted at route review: no
- Preparation approved at route approval: no
- Preparation approved revision: null
- Requested revisions and resulting world impact:

## Runtime Narration Contract

Store the accepted values in `play_profile.yaml` and mirror explanations in
`storytelling.md`.

- Point of view: first | second | third
- Tense: past | present
- Camera: close | medium | wide
- Prose density: lean | balanced | lush
- Response length: brief | dynamic | expansive
- Option prompting: natural | gentle_choices | tactical_menu
- Challenge density: low | balanced | high
- Clue density: low | balanced | high
- Dialogue style: plain | balanced | heightened
- Pacing: dynamic | deliberate | urgent
- Narrative Signature anchors, maximum 3:
- Narrative habits to avoid, maximum 3:
- Interiority: player_owned | shared_when_invited | guided
- Sensory focus, maximum 2:
- Dialogue balance: dialogue_forward | balanced | narration_forward
- Humor: minimal | situational | frequent
- Emotional distance: close | moderate | detached
- Breather frequency: sparse | balanced | generous
- Breather exit: player_led | player_led_with_established_triggers | world_led

## Open Questions For Play

- Question 1:
- Question 2:
- Question 3:
