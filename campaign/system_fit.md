# System Fit

Campaign id: `new_campaign`

Use this file to decide what the Lite campaign should rely on: model judgment,
simple notes, or explicit checks. Do not turn this into a code plan unless the
Designer asks.

The runtime contract is `play_profile.yaml`. This file explains why those
choices fit the campaign; it must not silently enable a mechanic.

## Accepted Lenses And Starter Bundle

- Accepted setting lenses:
- Accepted play lenses:
- Starter Bundle choice:
- Mixed or changed elements:
- Expected feel:
- Tracking load:
- Expected speed effect:
- Why this fit was accepted:
- Lens conflicts and resolution:
- Resolution grounding: fictional | bands | numeric
- Narrative Signature anchors, maximum 3:
- Narrative habits to avoid, maximum 3:
- Interiority policy: player_owned | shared_when_invited | guided
- Sensory priorities, maximum 2:
- Dialogue balance: dialogue_forward | balanced | narration_forward
- Humor: minimal | situational | frequent
- Emotional distance: close | moderate | detached
- Breather frequency: sparse | balanced | generous
- Breather exit: player_led | player_led_with_established_triggers | world_led

Lens briefs propose questions and defaults only. A resource, inventory,
condition, clock, time, ability, or dice mechanic becomes active only when the
Designer approves it and it appears under `mechanics.modules` in
`play_profile.yaml`.

## Primary Play Activities

- Activity:
- Why it matters:
- How often it appears:

## Conflict Modes

- Combat:
- Social pressure:
- Investigation:
- Exploration:
- Travel:
- Survival:
- Intrigue:
- Heist or stealth:
- Other:

## Mechanics Weight

Loose, moderate, tactical, mostly narrative, or another agreed style.

## Turn Performance Protocol

Choose this explicitly during Session 0. `fast` is recommended for new
campaigns because it preserves authoritative current truth while batching
secondary-note propagation.

- Profile: pending
- Typical routine-turn estimate: pending
- Typical durable-turn estimate: pending
- Structural / boundary-turn estimate: pending
- Cold distill policy: pending (`every_durable` |
  `scene_checkpoint_or_3_durable` | `scene_checkpoint_or_5_durable` |
  `scene_checkpoint_only`)
- Validation policy: pending
- Dashboard refresh policy: pending
- Style review policy: pending
- Latency notices: exceptional_only
- Estimate caveat acknowledged: no

Profiles:

- `fast`: write a compact scene checkpoint at boundaries and full-distill
  after at most five durable turns or another full trigger; use targeted hot
  checks during play.
- `balanced`: write a compact scene checkpoint at boundaries and full-distill
  at a meaningful full trigger or after at most three durable turns; refresh
  the dashboard for player-visible changes.
- `maximum_continuity`: propagate affected notes and run full checks on every
  durable turn.
- `custom`: choose individual policies without disabling authoritative state,
  knowledge-boundary, durable-event, or hot-validation safeguards.

## Stat And Skill Model

- Resolution grounding: fictional | bands | numeric
- Fictional competencies and limits, when fictional:
- Broad bands, when bands:
- Stats, scale, and starting budget, when numeric:
- Custom terms:

## Special Capabilities / Extras

For each setting-appropriate capability category:

- Name:
- Source:
- Rarity:
- Limit:
- Cost or risk:
- Counterplay:
- Social consequence:

## Progression Fit

See `progression.md` for closure levels, reward cadence, OOC upgrade
check-ins, and companion advancement.

- Preferred upgrade rhythm:
- Rewards should mostly increase: power, access, recognition, agency, identity,
  world change, or a mix.
- Progression should avoid:

## Deterministic Checks

Things that should be checked with simple tools or explicit arithmetic.

- 

### Approved Modules

- Approved modules (`play_profile.yaml.mechanics.modules`):
- Explicitly declined suggestions:
- Inventory tracking: abstract | quantified | encumbrance
- Time tracking: coarse | scene | step
- Travel tracking: abstract | route_time
- Wound tracking: narrative | conditions
- Dice mode: judgment_only | player_rolls | open_gm_rolls | hidden_gm_rolls |
  hybrid

Fantasy alone does not imply mana, HP, spell slots, or any other ledger.
Survival alone does not imply quantified inventory. Activate these only after
an explicit approval decision.

### Optional Mechanics Ledger

- Enabled: yes | no
- Actors tracked:
- Bounded resources:
- Ability prerequisites and costs:
- Cooldown units:
- Regeneration triggers:
- Mechanics that must remain GM judgment:

## GM Judgment Zones

Things Codex should decide from fiction, campaign memory, and table feel.

- 

## House Rulings

Short rulings that should be mirrored in `rules.md`.
