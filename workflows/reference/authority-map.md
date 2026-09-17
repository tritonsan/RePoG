# Campaign Authority Reference

Read only the section needed to identify a changed fact's owner. This is a cold
reference, never a per-turn load list. AGENTS.md owns cross-mode invariants.

For a difficult lookup, holder-specific account, memory compression, or
resumability question, load the relevant section of
`workflows/reference/continuity-memory.md`. Its optional fields extend existing
owners; they do not activate another memory store or require a legacy migration.

## Campaign Memory

This distribution is a single-campaign, standalone workspace. Its active
campaign root is always `campaign/`; do not create or select a parallel
campaign root.

A fresh template contains RPG and Companion artifacts as well as optional
derived views. Presence alone does not activate an experience, make an
artifact authoritative for the current task, or place it in the hot context.
Use `setup_profile.yaml`, the active profile, and the routed workflow to
determine what applies.

```text
campaign/
  setup_profile.yaml
  session_zero_state.json
  play_profile.yaml
  companion_profile.yaml
  companion_state.json
  agent_seat_state.json
  agent_roster.json
  user_context.md
  companion_view/
  session_zero.md
  campaign_one_pager.md
  research_dossier.md
  world.md
  boundaries.md
  system_fit.md
  palette.md
  world_truths.md
  issues.md
  faces_and_places.md
  visual_style.md
  visual_gallery.md
  progression.md
  arc_closure.md
  next_act_prep.md
  knowledge_boundaries.md
  storytelling.md
  appearance_guide.md
  opening_brief.md
  first_session.md
  character_foundation.md
  player.md
  player_ties.md
  current_state.yaml
  active_cast.md
  location_graph.md
  map_atlas.json
  world_voices/
  world_dynamics.md
  style_state.json
  mechanics_state.json
  visual_state.json
  creation_ledger.md
  relationship_map.md
  secrets_and_clues.md
  session_brief.md
  threads.md
  session_log.md
  rules.md
  characters/
  places/
  factions/
  snapshots/
  visuals/
  dashboard/
```

The storage model is intentionally bounded and role-separated:

### Profiles and Activation

- `setup_profile.yaml` is the setup routing and high-level readiness authority.
  It owns workspace/setup status and revision, the RPG/Companion experience
  choice, Session 0 depth, compatibility accounting, and the readiness gate.
  Schema-v8 Deep derives decision progress from `session_zero_state.json` and
  leaves legacy pack lifecycle lists empty. It does not define runtime behavior
  after materialization.
- `session_zero_state.json` is the canonical schema-v8 RPG Deep interview state.
  It owns the current stage, accepted/defaulted/deferred decision ledger,
  stage-local extensions, output evidence, fatigue checkpoints, and
  revision/digest-bound gates. It is dormant outside schema-v8 RPG Deep.
- `play_profile.yaml` is the materialized RPG runtime configuration when its
  status is `locked`. It owns setup provenance; lenses; approved mechanics,
  resolution, and tracking; narration selectors and Narrative Signature;
  advancement; dashboard, World Voices, and visual policy; and turn-performance
  and structural-parallelism choices. It is inactive in a Companion workspace.
- `companion_profile.yaml` is the materialized Companion runtime configuration
  when its status is `locked`. It owns setup provenance; primary companion
  selection; identity transparency; setting and communication; causal-life,
  relationship-permission, consent, deception, and user-memory policies;
  portrait, Companion View, and dashboard choices; and exchange-persistence
  and structural-performance choices. It is inactive in an RPG workspace.

At runtime, `setup_profile.yaml.experience_mode` and `ready_for_play`, together
with the selected profile's `profile_status`, determine which runtime profile
is active. A `pending` or `inactive` profile is not runtime authority. A locked
profile owns accepted selector values; related Markdown may elaborate them but
must not silently contradict or replace them. Resolve a conflict in Designer
Mode rather than guessing.

### Mode-Specific Runtime Stores

- `agent_seat_state.json` is the optional RPG Agent Seat operation store. It
  owns one browser-agent participant binding, the currently offered safe
  perspective, durable session/beat/seat revisions, at most one pending turn
  intent, its character-visible resolution, bounded prior-turn history, and
  bounded operation identity. A submitted
  intent is a proposal, not fictional truth: it never advances
  `continuity_revision` or writes campaign owners. The GM resolves it together
  with the human intent, persists any resulting world change through the
  ordinary RPG transaction, then records only the character-visible outcome
  here through `tools/agent_seat.py`. This store must never contain GM-only
  facts or another participant's private projection.

- `agent_roster.json` is the optional RPG Agent Seat eligibility manifest. It
  owns only character references, candidate/readiness state, bounded authority,
  and preparation revision. Character notes, relationship memory, and
  `knowledge_boundaries.md` remain authoritative for fictional and epistemic
  truth; the roster must never duplicate their fact text.

- `companion_state.json` is the bounded current-state and operation ledger when
  the Companion runtime is active. It owns state, continuity, and public-surface
  revisions; interaction and semantic-operation identity; the current
  conversation window, presence, condition, attention, and pending transition;
  elapsed-gap reconciliation; and evidence-bounded relational context. It does
  not advance in the background, store durable user memory, infer user
  interiority, or override the locked Companion profile.
- `user_context.md` owns consent-governed durable user memories, follow-ups,
  and content-free forget tombstones. The locked `companion_profile.yaml` owns
  the memory policy; the policy section here is a readable mirror and must not
  override it. Store no raw transcript, inferred profile, or fact the user did
  not explicitly share. Sensitive facts always require explicit consent.
- `world_voices/index.json` is the private artifact registry. It owns artifact
  identity and lifecycle, threads and version links, private epistemic basis,
  claim positions, recipient and channel distribution, revisions, and
  permanent operation identity; `world_voices/artifacts/` owns the Markdown
  bodies. Artifact claims do not become world truth or current holder state:
  `knowledge_boundaries.md` remains authoritative. Neither source is directly
  player-facing; acquired documents require a separate player-safe projection.

### Materialized Campaign Definition and Preparation

- `session_zero.md` is the human-readable Session 0 index and decision summary,
  not a transcript. Its schema-v8 Deep section is rendered from
  `session_zero_state.json`; never hand-edit that projection as state. Other
  routes retain their existing module/slot summary behavior. The locked runtime
  profile owns materialized selector values.
- `campaign_one_pager.md` is the compact, spoiler-safe player-facing
  projection of the campaign promise, tone, play focus, character fit,
  boundaries, and known starting context. It is an alignment surface, not an
  authority for hidden truth or runtime configuration.
- `character_foundation.md` owns the world-independent Character Core during
  schema-v8 RPG Deep Stage 3. It may hold accepted identity, desire, test line,
  protected authorship, and an activated interior extension, but it is not the
  playable character card. Stage 5 materializes the world-specific result in
  `player.md`; other routes may leave the foundation template unused.
- `research_dossier.md` owns research status, mode, source scope, canon or
  realism policy, source-grounded constraints, named uncertainty, risk
  acceptance, and current-scale lock permission. It is an evidence and
  constraint authority, not a second store of playable world truth; materialize
  accepted facts in `world_truths.md`, and never promote pending uncertainty
  silently.
- `world.md` is the compact GM-facing overview and index of the materialized
  campaign promise, world operating model, scale, frame, and major conflicts.
  It may summarize specialized files but must not silently override the
  detailed authority each specialized file owns.
- `boundaries.md` owns campaign-specific canon, tone, power, content,
  improvisation, approval, and player-facing limits, plus the versioned
  Companion relationship boundary contract when Companion mode is active. It
  may narrow campaign behavior but cannot weaken repository-wide invariants.
- `system_fit.md` is the human-readable rationale and summary for accepted
  lenses, play activities, mechanics weight, resolution model, performance
  protocol, and deterministic-check boundaries. The locked RPG profile owns
  runtime selectors; this file cannot enable a mechanic or override that
  profile.
- `palette.md` owns the campaign's Yes / No / Maybe inclusion stance for
  elements, themes, tropes, motifs, powers, factions, problems, and
  storytelling habits. It guides creative selection but does not override
  harder limits in `boundaries.md` or unresolved source constraints.
- `world_truths.md` owns accepted playable setting facts and their table
  impact once the research gate permits them to be locked at the current
  scale. A stored truth is not automatically player- or character-known;
  `knowledge_boundaries.md` owns holders, safe wording, and reveal conditions.
- `issues.md` owns the durable definition and status of current, impending,
  dormant, or resolved systemic problems, including who benefits, who suffers,
  visible signs, and the broad escalation implied by inaction. It provides
  pressure rather than a fixed plot and does not own the live scene, a dramatic
  question, stable faction identity, or the latest evaluated offscreen move.
- `faces_and_places.md` is the GM-facing index that connects issues, factions,
  and player ties to playable NPC and location handles, affordances, and note
  paths. Detailed notes own stable identity and routine;
  `knowledge_boundaries.md` owns fact holders and reveals. Do not turn this
  index into a duplicate character, place, or knowledge store.
- `visual_style.md` is the human-readable visual policy and art-direction
  expansion. It owns quota stance, generation targets, prompting boundaries,
  art direction, continuity guidance, and visual-canon and display rules. The
  locked active profile owns whether visuals and their destination are enabled;
  this file cannot enable generation or replace `visual_state.json`.
- `visual_gallery.md` owns the compact cross-entity index and status of draft,
  accepted, deprecated, or replacement-needed visuals, plus concise accepted
  visual-canon notes. Generation or a draft row does not establish acceptance;
  the visual handoff must complete, and the accepted asset and owning entity
  note must agree with the gallery.
- `progression.md` is the policy and calibration reference for closure levels,
  reward categories, fiction binding, observable player-preference signals,
  balance checks, and companion or ally advancement. The locked RPG profile
  owns advancement cadence and presentation. This file does not open a live
  advancement gate or choose a player-authored upgrade.
- `arc_closure.md` owns the current closure and progression state, including
  the sole live advancement/interlude gate, and records closure reviews,
  offers, chosen or applied upgrades, companion or ally changes, and world
  responses. Its presentation value must mirror the locked RPG profile;
  historical closure entries do not create a second live gate.
- `next_act_prep.md` is the transient GM-facing staging document between a
  closure and the next major act. It owns carry-forward classification, prep
  status, the proposed next-act frame, and inputs for the next
  `opening_brief.md`. It references current player, relationship, knowledge,
  and thread truth without replacing those authorities; after materialization
  it becomes used transition history rather than a second current opening.
- `knowledge_boundaries.md` is the sole current authority for tracked fact
  identities, truth and reveal status, current holders, suspicions and explicit
  unknowns, protected names, safe wording, reveal conditions, and Companion
  disclosure state. Optional Holder Accounts preserve one current received
  account per actor–fact pair, including evidence source, fictional learning
  time, and correction reference. They describe a holder's belief, not another
  world truth; correcting one holder does not update uninformed actors.
  Character and faction notes may own stable epistemic or
  disclosure habits but must not maintain a second copy of current knowledge.
- `storytelling.md` elaborates the locked RPG narration selectors with
  campaign-specific examples and guidance for option prompting, pacing,
  exposition, dialogue, openings, challenge density, and foreshadowing. It
  must not change profile values, knowledge ownership, or repository-wide
  authorship and causal guardrails.
- `appearance_guide.md` owns campaign-wide appearance detail tiers, card
  structure, visual-continuity fields, and boundaries against invasive or
  spoiler-heavy description. It does not own a specific entity's appearance;
  the entity note and any accepted visual canon do, subject to
  `knowledge_boundaries.md`.
- `opening_brief.md` owns the next finalized player-facing opening only while
  its status is `active`, including opening type and mode, arrival context,
  player-known facts, visible situation, ongoing local process, neutral action
  space, pressure, reveal limits, and the checked draft. While `pending` it is
  preparation; once `consumed` it is historical evidence and
  `current_state.yaml` owns the live scene.
- `first_session.md` owns provisional Session 0.5 drafting inputs while its
  status is `drafting`. After those inputs are transferred to an active
  `opening_brief.md`, mark it `materialized` and stop maintaining parallel
  opening wording; after narration mark both files `consumed`. It never owns a
  second current opening or a required plot route.
- `player.md` owns the accepted stable RPG player-character definition:
  identity and concept, appearance, established personality and background,
  starting tier, capabilities, limits, and approved backstory. It must not
  invent or alter player-authored interiority or history. `current_state.yaml`
  owns immediate condition and goal; enabled deterministic mechanics own their
  quantified values.
- `player_ties.md` owns accepted RPG character integration: desired personal
  story, stable tie premises, linked issues, factions, faces, and places,
  personal pressures, and explicit backstory or do-not-use limits. It cannot
  invent an unapproved tie or secret history. `relationship_map.md` owns
  current relationship truth and `threads.md` owns live dramatic questions.

### Current State, World Motion, and Transactions

- `current_state.yaml` is the compact structured hot-state authority when the
  RPG runtime is active. It owns campaign and continuity status, fictional
  time, the player's current condition, goal, capabilities, and enabled stats,
  the current scene, immediate inventory, conditions, clocks, and threats.
  Its scene frame owns the resumable scene id and mode, ongoing process,
  disruption, last causal beat, bounded pending consequences, and resume
  anchor. A material unresolved reply or turn handoff may be retained in that
  existing anchor through a pure checkpoint; it is not a transcript or a new
  fictional revision. Its `persistence` block owns distill progress,
  durable-turn count, and pending cold targets. It does not replace stable
  character or world notes, or durable history.
- `active_cast.md` is the RPG scene-chain hot tracker. It owns temporary
  location, activity, immediate objective, availability, presence reason,
  next move, and last-seen revision only for NPCs who are present, nearby,
  travelling with the player character, or likely to act in the current chain.
  Character notes own stable identity, baseline routine, and their own personal
  offscreen trajectory. A shared domain process belongs in `world_dynamics.md`;
  the character note references it instead of running a second trajectory for
  the same process. Do not use this file as a whole-world roster or a duplicate
  faction or domain clock.
- `location_graph.md` owns current gameable route edges, direction, travel,
  access, visibility, ordinary traffic, conditions, and revision. Place notes
  own stable place identity and `current_state.yaml` owns the current
  location. Its `Player-known` field is a route-local projection that must
  agree with `knowledge_boundaries.md`, not an independent reveal authority.
- `map_atlas.json` is inactive unless a stable map is configured. It owns
  authored coordinate space, geometry, scale, projection, feature placement,
  and presentation provenance only. It does not own travel, access, current
  location, or reveal state; any dashboard map is a player-safe projection
  compiled from `location_graph.md`, approved atlas geometry, and current
  knowledge.
- `world_dynamics.md` owns the current trajectory, trigger and evaluation
  state, and notable evaluated events only for explicitly tracked,
  campaign-relevant offscreen domains. Character and faction notes own stable
  motive, method, and capability. A character's separate personal trajectory
  may stay in its character note; the same movement must not be evaluated in
  both places. On transfer to a shared domain, retain only a `Domain trajectory
  ref` for that process in the character note and archive the former personal
  evaluation. `current_state.yaml` and
  `companion_state.json` own immediate state. Evaluate domains only on a due
  causal trigger. This file is not a continuous simulation, and elapsed time
  alone does not force a result.
- `style_state.json` is the bounded recent-history ledger for narration
  variation. It owns beat, scene, and speaker references, short avoid-phrase
  entries, and categorical fingerprints for dramatic beat, GM move, ending,
  sensory channel, complication, social tactic, and metaphor family. It stores
  neither full prose nor stable narration policy and must not override the
  locked RPG profile or `storytelling.md`.
- `mechanics_state.json` is authoritative only for stateful deterministic
  modules explicitly enabled in the locked RPG profile and while its own
  `enabled` flag is true. Within those modules it owns revisioned resources,
  abilities and cooldowns, quantified inventory, conditions, clocks, elapsed
  time, and operation identity. It cannot enable a mechanic by itself.
  `current_state.yaml` may mirror immediately relevant narrative values, but
  the two files must not contradict each other.
- `visual_state.json` owns at most one resumable visual draft/acceptance
  transaction, its revision and return anchor, and its transaction history.
  It does not make a draft accepted or canonical and does not replace
  `visual_gallery.md` or the accepted visual asset.

### Durable Indexes, Entity Notes, History, and Rulings

- `creation_ledger.md` is the compact production index for every T1+ named NPC,
  location, or faction introduced during setup or play. It owns existence,
  type, tier, first appearance, note path, status, and promotion tracking.
  Entity notes own stable detail and established aliases; a T1 stub without a
  note keeps its established alias with its identity. Derived lookup signals
  reference these owners rather than introducing aliases. Any player-known or
  knowledge summary in the ledger must agree with `knowledge_boundaries.md`.
- `relationship_map.md` owns one current qualitative edge per directed
  relationship, including status, trust, debt or tension, knowledge asymmetry,
  and revision. Entity notes own stable relationship behavior and
  `session_log.md` owns historical changes. In Companion mode this map covers
  the companion's social world, not the primary companion-to-user relationship,
  whose evidence-bounded context belongs in `companion_state.json`. Any
  `Player-known` value must agree with `knowledge_boundaries.md`.
- `secrets_and_clues.md` owns compact discovery candidates and their flexible
  possible delivery channels; it must not bind a clue to one NPC, object, or
  required action without a fictional reason. Fact identity, current
  truth/reveal status, holders, and protected wording remain authoritative in
  `knowledge_boundaries.md`; duplicated status fields here are mirrors.
- `session_brief.md` is an optional, revision-bound GM prep and triggered-lookup
  index for observable player focus, possible scenes, useful entities, and
  likely references. It is neither a plot script nor a current-state authority;
  reference owning files instead of copying their live facts. Optional lookup
  entries bind established names/aliases or causal signals to an owner path and
  heading/id, an applicability condition, and a verified revision. An older
  revision makes applicability unverified; it need not erase useful pointers.
  Load the owner, then refresh or discard only affected entries when their
  dependencies change. The active Act id/Compass and closure references point
  to `threads.md`; they never become a second live Compass.
- `threads.md` owns the status of player-relevant dramatic questions, open
  consequences, promises, debts, mysteries, threats, and opportunities. In
  Companion mode it holds only established shared callbacks, plans, and open
  conversational loops without forcing an arc or climax. It references rather
  than duplicates systemic issues, offscreen trajectories, live scene state,
  or consent-governed user memory.
- `session_log.md` is append-only chronological continuity and recovery
  evidence. It records durable revisions, scene checkpoints, and distill
  markers without becoming current truth or a transcript. When history and a
  current owning file conflict, preserve the old entry and append the
  correction rather than rewriting history. Ordinary Companion contact enters
  this log only when durable meaning changed.
- `rules.md` owns human-readable table procedures, recurring rulings,
  campaign-specific mechanics, and any approved dice procedure. The locked RPG
  profile selects resolution grounding and enabled modules, and
  `mechanics_state.json` owns enabled quantified state; this file cannot
  activate or silently replace either contract.
- `characters/`, `places/`, and `factions/` own readable per-entity stable
  identity, baseline agency and routine, capabilities and limits, appearance,
  behavior, and reference links. A character note may own that NPC's personal
  offscreen trajectory; a trajectory already owned by a shared world domain
  stays a reference here. Do not duplicate another owner's current location,
  knowledge, relationship, domain trajectory, or event history. The primary
  Companion note additionally owns the stable fictional character and bounded
  Hot Character Kernel, not current condition, user memory, or relationship
  context.

### Assets, Derived Views, and Recovery

- `visuals/` is the campaign asset store. Unaccepted generations remain under
  `_drafts/`; accepted assets belong in the matching typed directory. File
  presence alone does not establish acceptance or canon—`visual_gallery.md`
  and the owning entity note record that status.
- `snapshots/` stores explicit reversible campaign copies and their manifests
  for recovery or comparison. A snapshot is never active campaign truth and
  must not be selected merely because it is newer; inspect or restore one only
  during an explicit recovery, migration, or comparison task.
- `dashboard/` is the optional derived RPG player board when enabled by the
  locked RPG profile. Its state owns only projection revision, refresh status,
  and currently displayed player-safe tiles and assets. It is never campaign
  truth; stale output must be rebuilt from owning authorities rather than used
  to update them.
- `companion_view/` is the optional lightweight derived Companion surface when
  enabled by the locked Companion profile. Its state owns only the public
  projection revision and currently displayed identity, accepted portrait,
  local clock, previously shared status, and player-safe shared cards. It must
  not expose private facts, user memory, internal relational context, scores,
  or labels, and it is never a source of truth.

Example rows, placeholder values, allowed-value menus, comments, and blank
template sections are scaffolding, not accepted campaign truth. Remove or
materialize them through the owning setup or runtime workflow before treating
the affected artifact as ready.

This inventory is an authority map, not a load list or a fixed required-file
checklist. The active workflow and deterministic validation determine which
artifacts must be materialized. Do not read or update an inactive or optional
store merely because the fresh template contains it.

If the selected workflow requires an owning artifact and it is missing,
corrupt, or irreconcilably conflicts with another owner, enter Designer Mode
and use the documented validation, migration, or recovery path before
continuing runtime. Do not silently substitute a mirror, projection, prep file,
history entry, or snapshot.

Across this map, a summary, mirror, index, prep note, history entry, or
projection never outranks its owning artifact and never writes truth back into
it. Rebuild stale derived material from the owner. Resolve owner conflicts by
role and explicit repair, not by modification time, file detail, or whichever
copy is easier to load.
