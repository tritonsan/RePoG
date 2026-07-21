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
- Starter Bundle: pending
- Accepted setting lenses: none
- Accepted play lenses: none
- Runtime profile: pending (`play_profile.yaml` for RPG,
  `companion_profile.yaml` for Companion)
- Expected routine turn: pending
- Expected durable turn: pending
- Expected structural / boundary turn: pending
- Semantic parallelism: selective_structural (default; structural boundaries
  only, when supported)
- Maximum parallel workers: 3 (Quick materialization is capped at 2)
- Parallelism tradeoff: potentially shorter structural waits with higher model
  usage; unsupported tools use the same serial workflow
- Dashboard refresh cost: approximately +1–2 minutes when run
- Companion View cost: no ordinary-message refresh; a small local update only
  when already-shared visible truth changes
- Image generation cost: approximately +1–3+ minutes per draft
- Performance estimate acknowledged: no
- Final player confirmation: pending

The experience gate and depth gate are routing questions and do not count in
the content-decision total.

## Companion Module Status

Use this section only when Experience is `companion`. Leave the RPG Module
Status below as an inactive template; only this selected block participates in
Companion readiness. For RPG, this block is an inactive template and only the
RPG Module Status block participates in readiness.

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
- Maximum parallel workers: 1–3
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

After the pitch, offer 2 to 4 contextual bundles and ask the Designer to choose
one bundle as a single decision. Each option must state:

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
- Research status:
- Web search decision:
- Source scope:
- Open source questions:
- Risk accepted: no
- Current-scale lock permitted: no
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
- Maximum parallel workers: 1–3
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
