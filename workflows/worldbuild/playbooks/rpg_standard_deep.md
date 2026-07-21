# RPG Standard And Deep Session 0

Load only after the router selects RPG Standard or Deep. Standard completes
the 17-module core in roughly 17–25 decisions. Deep completes the same core,
then opens only deterministically triggered packs and normally stops at 30–45
decisions.

# Core Pipeline

1. **Campaign Pitch:** universe/genre, emotional tone, player fantasy, dominant
   feel, and what the campaign must not become. Then choose a contextual
   Starter Bundle.
2. **Research Need Gate:** classify canon/real/homebrew/original grounding and
   load `research_gate.md` when outside sources matter.
3. **Group Contract:** boundaries, agency, consequence, clarification stance,
   and one coherent narration card with Narrative Signature, interiority,
   sensory/dialogue, humor, emotional distance, and breather choices.
4. **System Fit:** play modes, mechanics weight, `fictional|bands|numeric`
   grounding, approved deterministic modules, inventory/time/travel/wound/dice
   rigor, advancement, and the required Turn Protocol/performance choice.
5. **Canon Policy:** original or the precise allowed timeline, elements,
   closeness, contradiction, and approval boundaries.
6. **Palette:** Yes/No/Maybe tone, genre, powers, factions, visuals, and
   storytelling habits.
7. **Visual Mode:** independent Dashboard and visual choices, initial tiles,
   map skin when relevant, refresh/placement policy, art direction, and timing
   acknowledgement. Draft visuals never become canon before acceptance.
8. **World Truths:** only playable truths about society, authority, economy,
   travel, powers/technology, belief, danger, history, daily life, and common
   misconceptions. Each truth needs a table consequence.
9. **Scale:** first-session boundary, coarse time, routes/access/traffic, news
   speed, and what remains offstage.
10. **Issues:** active/impending problems, beneficiary, harmed party, visible
    sign, ignored consequence, and dramatic question—never a fixed plot.
11. **Factions:** only initially needed forces, with public mask, stable desire,
    method/capability, face/place, pressure tactic, knowledge boundary, and
    optional owning world domain.
12. **Faces And Places:** playable handles tied to pressure and player ties,
    with independent wants, appearance/spatial continuity, routines,
    availability, natural presence, affordances, and gated knowledge.
13. **Progression:** cadence/closure levels, fitting reward mix, companion
    advancement, power-creep limit, and `explicit_ooc|automatic_fictional|none`.
14. **Player Character:** identity, appearance, personality, background,
    competence/limits, capabilities/counterplay, and approved numeric stats
    only under numeric grounding.
15. **PC Integration:** issues, factions, faces/places, personal pressures,
    relationships, secrets/debts, and backstory limits that revise the world.
16. **Starting Situation:** place, arrival, known/visible context, neutral
    action space, pressure or calm affordance, hidden limits, scene mode, and
    an opening built from routine + disruption + natural presence + arrival.
17. **Continuity:** research/canon/power/knowledge/reveal/creation/relationship/
    distill/advancement ownership and the selected performance cadence.

# Immediate Persistence Map

Every accepted answer is durable in the same Session 0 turn. Write the
semantic owner first, update `session_zero.md`, then increment the setup
revision and sync `play_profile.yaml.source_setup_revision`. Do not postpone
the 17 module answers until final materialization or run full validation after
each question.

| Module | Immediate authoritative persistence |
| --- | --- |
| 1. Pitch | `campaign_one_pager.md`, summary in `world.md`, setup/session progress |
| 2. Research | `research_dossier.md`; accepted source/canon constraints update `boundaries.md` before dependent truth is locked |
| 3. Group Contract | `boundaries.md`, profile narration, `storytelling.md` |
| 4. System Fit | profile mechanics/resolution/performance/advancement, `system_fit.md`, `rules.md`, approved mechanics-state contract |
| 5. Canon | dossier, boundaries, palette, canon summary in `world.md` |
| 6. Palette | `palette.md` and resulting hard boundaries |
| 7. Visual Mode | profile Dashboard/visual/World Voices policy, `visual_style.md`, gallery/state; derived surfaces wait for finalization |
| 8. World Truths | `world_truths.md` and accepted World Operating Model in `world.md` |
| 9. Scale | `world.md`, draft current state, `location_graph.md`, relevant world domains and starting prep |
| 10. Issues | `issues.md`, `threads.md`, gated `secrets_and_clues.md` entries |
| 11. Factions | faction notes, ledger, relationships, knowledge and owning world domains |
| 12. Faces/Places | character/place notes, index, ledger/relationship/knowledge entries, active cast, routes and appearance guidance |
| 13. Progression | `progression.md` and profile advancement policy |
| 14. Player Character | `player.md`, appearance guide and approved mechanical representation |
| 15. PC Integration | `player_ties.md`, relationships, threads and player/PC knowledge |
| 16. Starting Situation | `first_session.md`, `opening_brief.md`, draft scene/current state, relevant cast and prep |
| 17. Continuity | rules/storytelling, authority notes, progression/research state and final runtime performance contract |

Write Deep activation to `setup_profile.yaml.activated_packs` as soon as its
trigger is accepted, then persist each pack answer:

| Deep pack | Immediate owners |
| --- | --- |
| `character_foundation` | `character_foundation.md`, player/ties and personal places/relationships |
| `group` | `group.md`, relevant faction/place notes, relationships and player ties |
| `world_fabric` | world, truths, issues and only relevant faction/place notes |
| `location_network` | location graph, places, travel/world domains and cast availability |
| `faction_information` | faction notes, knowledge, relationships, issues/domains |
| `campaign_architecture` | threads, issues, progression and initial closure/carry-forward promises without fixing a plot |
| `mechanics_progression` | approved profile modules, system/rules/progression, optional mechanics state |
| `source_grounding` | dossier, boundaries, palette and supported world truth |

# Important Module Invariants

- World Operating Model records main cause/effect chains, beneficiaries,
  costs, player-visible channels, deliberate exceptions, and resolved lens
  conflicts.
- T2/T3 NPCs receive the compact Agency Card and, when active, a bounded
  Offscreen Trajectory. Compare each against the two most similar active NPCs;
  when four of six contrast axes overlap, redesign at least two. This is a
  model pass, not a checker.
- Stable NPC identity/routine/decision logic belongs in character notes;
  temporary location/activity/objective in `active_cast.md`; knowledge truth
  in `knowledge_boundaries.md`; world movement in `world_dynamics.md`;
  systemic problems in `issues.md`; player-linked questions in `threads.md`;
  current relationship truth in `relationship_map.md`.
- Numeric grounding alone requires eight 1–5 stats and an approved budget.
  Fictional/banded play uses permissions, limits, leverage, counterplay, or
  broad setting-appropriate bands.
- The opening remains neutral and actionable. `first_session.md` is prep;
  `opening_brief.md` becomes the sole finalized opening. A breather may have no
  immediate pressure when campaign-level pressure exists elsewhere.
- World Voices is an optional communication layer within the bundle/profile,
  not a publication quota. Its Dashboard tile requires both Dashboard and
  World Voices projection permission.

# Turn Protocol

Offer Fast, Balanced, Maximum Continuity, or Custom with the established
timing bands, freshness guarantees, and Dashboard/visual estimates. Fast is
recommended; it defers duplicate secondary propagation, never current truth,
knowledge, mechanics, durable revision events, or advancement gates.

In the same performance decision, show `off`, recommended
`selective_structural`, and `aggressive_structural` semantic parallelism.
Explain that eligible boundaries may finish sooner while using more model
allowance. This is one coherent performance decision, not a new module.

# Deep Activation

Activate packs only from accepted answers:

- persistent crew/company/base -> `group`;
- detailed identity/inner life/change arc -> `character_foundation`;
- substantially original society/law/economy/culture/metaphysics/history ->
  `world_fabric`;
- exploration/travel/routes/sandbox/survival logistics -> `location_network`;
- politics/intrigue/contested information -> `faction_information`;
- explicit multi-arc promises/setup-payoff/climax/endings ->
  `campaign_architecture`;
- tactical resources/stats/conditions/clocks/detailed growth ->
  `mechanics_progression`;
- canon/real-world/hard-science source sensitivity -> `source_grounding`.

Do not activate Group for a solo campaign without a persistent collective or
World Fabric merely because all campaigns have a world. Checkpoint after each
8–10 decisions with locked choices, open packs, defaults, and approximate
remainder. Ask permission before exceeding 45. Route world detail into
existing files; only `character_foundation.md` and `group.md` are optional new
notes when their packs activate.

# Standard/Deep Finalization

After final approval, load `finalization.md`. Use no more than three read-only
proposal workers: world ecology, cast/space, and—only when substantial—systems/
presentation. The coordinator owns all authoritative writes, opening, ids,
knowledge, revision, readiness, snapshot, and final checks.
