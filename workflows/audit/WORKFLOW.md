# Workflow

RePoG Lite Audit

# Purpose

Use this workflow when checking a Lite campaign for continuity, player-facing
leakage, missing memory, stale threads, file health, or readiness for play.

Audit asks whether the campaign can support natural play, not whether every
narrative fact is schema-normalized.

# Audit Checklist

First route by `setup_profile.yaml.experience_mode`. Legacy missing values mean
RPG. For Companion, run `tools/check_companion.py` and audit the Companion
contract below; do not report missing player character, opening scene, arc,
mechanics, dashboard, or World Voices readiness.

For Companion, check:

- `companion_profile.yaml` is locked at the setup revision and
  `play_profile.yaml` is inactive;
- the primary T3 note is adult, behaviorally specific, internally
  contradictory, voice-distinct, and has a routine, obligation, active life
  thread, goals, social connection or chosen isolation, and causal next move;
- `companion_state.json` uses schema v2; timestamps are timezone-aware,
  operational and semantic sequences are monotonic, current condition resolves
  to notes, backward time is rejected, and the same operation cannot be
  applied twice;
- ordinary replies use one `begin-exchange` state call and only durable
  meaning changes open `commit-semantic`; no separate per-message checker or
  View patch is hidden in the route;
- repeated current-activity questions preserve place/activity until an
  established transition;
- elapsed-time developments stay below the returned ceiling and major changes
  have seeded causes;
- `knowledge_boundaries.md` uses a strict per-topic ledger separating private
  truth, current willingness, already-shared surface, and evidence gates; the
  character does not reveal their whole history at first contact;
- relationship context is qualitative, multi-dimensional, and evidence-based,
  with no inferred user emotions, ordered trust/closeness ladder, point
  thresholds, or dependency pressure;
- `boundaries.md` has a referenced active version; broad relationship scope is
  a maximum permission rather than automatic consent, and direct-deception
  opt-in never applies to AI identity, real safety, consent/boundaries, or
  memory semantics;
- `user_context.md` follows `off`, `ask_before_save`, or
  `contextual_low_risk`, contains no transcript or inferred facts, and has no
  sensitive entry without explicit consent; forget requests remove active
  content; an `off` policy also leaves no durable user-event item in the hot
  attention queue;
- direct human/real/AI questions receive clear fictional-AI disclosure while
  ordinary messages do not repeat it;
- replies do not default to lists, advice, therapeutic paraphrase, or a question
  every time, and use at most one self-originated beat;
- optional portraits use visual approval and return to conversation; the RPG
  Dashboard remains off. If the separate Companion View is light, it validates
  only accepted art and already-shared facts, never private presence,
  relationship evidence, disclosure readiness, user memory, or internal ids.

For a representative Companion audit, use
`tools/companion_acceptance_suite.json`. Deterministic cases run inside
`verify_workspace.py`; sample semantic cases in a fresh conversation and judge
them against their expected behavior after the reply, never as a hidden
per-message checker.

For RPG, check:

- `session_zero.md` exists and tracks the Session 0 module decisions;
- `research_dossier.md` exists and records research status, mode, source scope,
  canon/realism policy, hard boundaries, and open source questions;
- `research_dossier.md` has explicit `Risk accepted` and
  `Current-scale lock permitted` fields; `needed_pending` never begins play,
  and partial/unavailable research locks only under its declared gate;
- fully original campaigns do not import external canon through research; they
  use adjacent research only as grounding and keep unresolved rules as
  Designer questions;
- `campaign_one_pager.md` is player-safe and does not reveal GM-only secrets;
- `system_fit.md` explains the expected play activity mix and mechanics
  weight;
- `setup_profile.yaml` stores only Session 0 progress, activated/defaulted/
  completed packs, and readiness; a ready Deep pack has its required output;
- `play_profile.yaml` is locked to the same setup revision before play and owns
  valid lenses, approved mechanics, narration, advancement, dashboard,
  visual, and performance policy;
- lens combinations are deduplicated, documented conflicts are resolved, and
  no lens silently enables a mechanic such as HP, mana, wounds, or inventory;
- Custom protocols keep authoritative state, knowledge boundaries, durable
  revision events, and hot validation mandatory;
- `palette.md` has Yes / No / Maybe boundaries that do not conflict with
  `boundaries.md`;
- `appearance_guide.md` exists and defines middle-detail appearance rules,
  tiered appearance depth, location description fields, faction visual
  identity, and boundaries against invasive or spoiler-heavy details;
- `world_truths.md` stores playable truths with table impact, not encyclopedia
  lore;
- `issues.md` has at least one current or impending issue with visible signs
  and an open question;
- `faces_and_places.md` links important issues or factions to usable NPC/place
  handles;
- `progression.md` defines closure levels, reward cadence, OOC upgrade
  check-ins, reward pool, balance checks, and companion advancement;
- `arc_closure.md`, when used, records closure reviews and chosen upgrades
  without becoming a transcript;
- `next_act_prep.md` exists and, after scenario/arc/campaign closure, carries
  forward active NPCs, companions, factions, locations, items, conditions,
  secrets, relationships, resources, and unresolved pressures;
- a post-arc opening is not drafted from scratch while `next_act_prep.md` is
  still `needed` or `drafting`;
- `knowledge_boundaries.md` separates GM-only truth, player/PC knowledge,
  companion knowledge, NPC/faction knowledge, protected names, safe wording,
  and reveal triggers;
- player-facing examples do not name protected proper nouns before a naming
  event;
- companions do not speak, plan, or react from information they have not
  learned;
- advancement rewards are tied to player actions and fiction sources, not
  arbitrary gifts;
- only the closure selected by `play_profile.yaml.advancement.cadence` opens an
  advancement gate; `none` does not stop normal play;
- `automatic_fictional` does not force an OOC interruption and pauses only for
  an unresolved Player choice;
- `explicit_ooc` blocks applying a required choice or opening a dependent next
  act, but a Player who defers may remain in aftermath/breather play;
- reward budget is driven by achievement quality first and play volume second;
- GM-awarded perks are fiction-derived, limited, and not exchangeable for a
  different reward;
- major arc closure changes world state, access, reputation, faction status, or
  identity in addition to raw character power;
- companion or allied NPC advancement is considered when an NPC meaningfully
  participated or changed;
- `current_state.yaml` is readable and small;
- no campaign is `ready_for_play` with a placeholder campaign id, blank player
  identity/concept, blank scene location/pressure, unfinished opening brief,
  missing World Operating Model, or missing starting snapshot;
- V2 campaigns remain readable; new or migrated campaigns contain memory
  version 3, a non-negative continuity revision, and a valid scene frame;
- `current_state.yaml.persistence` has a valid last-distilled revision, bounded
  durable-turn counter, and deduplicated pending cold targets;
- every schema-v2 durable revision has a matching append-only event, and each
  recorded distilled revision has a matching distilled-through marker;
- Fast never exceeds five undistilled durable turns and Balanced never exceeds
  three; Maximum Continuity leaves no durable turn pending;
- new Fast/Balanced profiles use `scene_checkpoint_or_5_durable` or
  `scene_checkpoint_or_3_durable`; legacy `scene_or_*` values are accepted only
  through the V1/V2 compatibility path;
- a scene checkpoint updates scene frame, active cast, and resume anchor without
  resetting the durable counter, appending a distilled marker, or forcing a
  full check;
- session/scenario/arc/campaign closure, applicable advancement, research lock,
  continuity conflict, and explicit full-save have no unresolved cold targets;
- every active T2/T3 NPC has one complete, plausible `active_cast.md` row with
  location, activity, objective, availability, reason-here, and next move;
- `location_graph.md` endpoints resolve and directed routes are explicit;
- `relationship_map.md` contains current truth without duplicate current pairs;
- stale prep revision is reported and never overrides current state;
- `session_brief.md` identifies a small active memory set and uses triggered
  lookups rather than treating the entire campaign as hot context;
- `world_dynamics.md`, when present, contains only campaign-relevant domains,
  clear refresh triggers, and notable changes rather than continuous
  simulation;
- hidden world events remain outside Player Mode and the dashboard;
- `mechanics_state.json`, when enabled, validates strict integer resources,
  ability costs/cooldowns, quantified inventory, conditions, clocks, elapsed
  time, continuity revision, monotonic operation sequence, and its unbounded
  operation-id registry;
- `style_state.json`, when present, is valid, bounded, stores categorical
  fingerprints rather than full narration, separates narrator repetition from
  named NPC/companion speech habits, and is not written on soft turns;
- `storytelling.md` exists and defines option prompting, reveal policy, and
  pacing defaults;
- `storytelling.md` defines challenge density, routine competence, clean
  success, consequence severity, and breather scene preferences;
- `opening_brief.md` exists and gives location, arrival context, player-known
  context, neutral action space, and hidden information boundaries;
- `first_session.md` is preparation rather than a duplicate current opening,
  becomes `materialized` after transfer to `opening_brief.md`, and becomes
  `consumed` only after that opening is used in play;
- `creation_ledger.md` contains every T1+ named NPC, location, and faction;
- T2+ ledger entries have matching notes under `characters/`, `places/`, or
  `factions/`;
- T2/T3 NPC notes begin with a complete Agency Card: local role, independent
  project, mundane task, pressure decision principle, mistaken belief/error,
  line not crossed, non-Player obligation, speech rhythm/social tactic,
  routine/availability, next move if ignored, and evaluation trigger/channel;
- T2+ NPC notes include table hook, default posture, mundane agenda, plain
  speech sample, compact appearance card, power/capability grounding, weak
  points, and key info separated from personality;
- eight numeric NPC stats are required only when
  `play_profile.yaml.mechanics.resolution_grounding` is `numeric`;
- recurring NPC notes include routine/availability logic, and useful NPCs do
  not appear without plausible travel from last location, elapsed time, a
  current task, reason-here, and contextual reaction;
- companion notes include stats, key capabilities, weak stats, and current
  growth ceiling;
- major obstacles have relevant stat, difficulty, and clean/partial/failure
  outcome notes;
- important factions include faction power band plus typical member,
  specialist, and elite/leader stat guidance;
- early-stage campaigns do not overfill ordinary NPCs with 4 or 5 stats;
- player outcomes generally respect player stat strengths, weak stats,
  capabilities, and known opposition;
- T2+ NPCs are not all suspicious, cryptic, testing, or polished in the same
  way; new/promoted T2/T3 NPCs pass the model-only six-axis Contrast Pass;
- character notes do not hide important clues only inside personality prose;
- T2+ place notes include baseline routine, reaction point, ordinary NPC
  activity, spatial/visual description, and clue exposure gates;
- `secrets_and_clues.md`, when present, keeps discoveries short and flexible
  instead of locked to one NPC or one required action;
- `session_brief.md`, when present, is short prep rather than a plot script;
- `first_session.md`, when present, describes a starting situation rather than
  a required route;
- important factions link to at least one issue, representative face, or key
  place;
- important factions include a visual identity and hidden visual facts are kept
  separate from player-facing faction appearance;
- important NPCs/places represent an issue, faction, or player tie instead of
  existing only as lore;
- every T1+ ledger entry has at least one compact edge in `relationship_map.md`;
- `relationship_map.md` is a short edge-list, not a long encyclopedia or vector
  store substitute;
- the current location exists in `places/` or is clearly described in `world.md`;
- present named NPCs exist in `characters/` or are intentionally minor;
- inventory and conditions do not contradict recent session memory;
- open threads are playable and not stale bookkeeping;
- character attitudes reflect recent important events;
- faction moves have consequences or visible pressure;
- no player-facing sample text contains file paths, raw ids, tool names, YAML,
  checks, prompts, or implementation language;
- if `dashboard/` exists, it has `index.html`, `dashboard_state.json`, and
  `assets/`;
- dashboard text does not contain GM-only truth, protected names before reveal,
  hidden clues, internal ids, file paths outside `assets/`, prompts, tools,
  scripts, YAML, Markdown, or implementation language;
- dashboard NPCs, clues, threads, visuals, map features, and inventory are all
  player-known or character-perceivable;
- Dashboard V3 uses only approved tile types, has current source revision and
  scene id, contains no draft/missing asset, and never shows fabricated
  placeholder stats or readiness;
- Legacy atlas nodes and Atlas V1 features are unique and inside their declared
  coordinate space; current feature and route endpoints are valid; unknown
  Atlas V1 geometry is omitted; and map/visual references use only relative
  `assets/...` paths;
- `map_atlas.json`, when present, stores geometry and presentation only;
  connection, access, and travel truth still agree with `location_graph.md`;
- compatibility-loaded V2 maps still do not imply undiscovered locations,
  hidden routes, secret factions, or protected names before reveal;
- World Voices artifact bodies and manifest references exist and remain inside
  `world_voices/`; artifact/thread/version links, lifecycle states, revisions,
  and permanent operation sequences are valid;
- every artifact has a causal event or prior artifact, and every distribution
  has recipients, channel, fictional timing, causal basis, and append-only
  history;
- claim fact ids resolve to `knowledge_boundaries.md`, which remains the sole
  current fact/holder authority; the private manifest does not create a second
  truth ledger;
- scheduled, delayed, in-transit, lost, or hidden documents do not enter the
  Dashboard projection; hidden artifacts are absent from player-facing names,
  paths, counts, pages, search, and comparison;
- World Voices catalog pages stay bounded, document paths remain relative
  below `assets/world_voices/`, and player files contain no epistemic basis,
  claim class, fact id, operation id, actual provenance, or GM-only field;
- corrections, retractions, and superseding editions preserve and link the
  original artifact instead of rewriting it;
- protected-name delivery has a matching knowledge revision, and the
  Dashboard contains no name still protected from the player character;
- no campaign marked ready for play has a pending visual review;
- every accepted visual requested for dashboard placement exists under
  `dashboard/assets/`, is referenced by an `assets/...` path, and has passed
  the dashboard check;
- `visual_state.json` has at most one pending transaction; pending work has a
  target, interrupted context, last beat, return anchor, and next step;
- visual generation return anchors are preserved through errors and cleared
  only after atomic acceptance, rejection, or an explicit choice to proceed;
- no obvious mojibake or placeholder names remain;
- player-facing examples do not overuse cryptic, aphoristic, or market-style
  dialogue;
- narration varies length and cadence by scene function and does not recycle
  avoid-listed cliches, gestures, or sensory formulas;
- ordinary NPCs have ordinary needs and speech when the scene calls for it;
- low-risk competent actions are not routinely turned into tests,
  complications, suspicion, or hard consequences;
- scene modes match function, clue/local-noise elements are treated as ceilings
  rather than quotas, and quiet/empty places may still count as living scenes;
- natural breather scenes can persist without a fixed turn limit or fabricated
  escalation and exit according to the selected breather policy;
- the opening or next scene gives the player something actionable.

# Triggered Semantic Review

Do not run semantic narration review on every turn and do not implement it as a
Python checker. At an explicit GM-quality audit, a scheduled representative
sample, or a full-distill sample selected by policy, review the transcript with
the GM Spine and triggered playbooks.

Score 0–2 for intent fidelity, causality, Player authorship, NPC agency,
presence/travel logic, voice contrast, knowledge boundaries, pacing, and
continuation. A sample passes at an average of at least 1.5 with no critical
Player-authorship or knowledge-boundary breach. Report concrete evidence and a
small prompt/note correction; do not auto-rewrite established fiction.

For a reproducible replay, use `tools/gm_replay_suite.json` without an API or
runner engine. Start each scenario in a fresh context; give the acting GM only
its `initial_state`, `setup`, and ordered `turn_sequence`. After the last turn,
give the untouched transcript plus the full scenario to a separate human/model
evaluator, copy and fill its `scoring_record`, and apply the top-level formulas.
Do not expose expected observations during play, mutate campaign state, or turn
this sampled audit into an ordinary per-turn gate.

# When Tools Exist

Use Lite tools when available:

- `tools/check_player_facing.py --campaign campaign` for protected-name
  leakage without broad generic-word false positives;
- `tools/check_state.py campaign --scope hot` for per-durable-turn current
  sanity and `--scope full` at the selected distill boundary;
- `tools/check_dashboard.py` for local dashboard state, asset, revision, tile,
  map, and player-facing safety;
- `tools/check_world_voices.py campaign` for private lifecycle/reference and
  player-projection integrity at full-distill/audit boundaries;
- `tools/check_style.py` for policy-triggered, warning-level categorical
  narration repetition checks, never soft-turn or semantic gating;
- `tools/world_pulse.py` with a stable evaluation id for deterministic
  uncertainty when a relevant domain refresh is due;
- `tools/roll_dice.py` for bounded, reproducible approved dice rolls;
- `tools/resolve_mechanic.py` for approved resource, ability, inventory,
  condition, clock, and time operations;
- `tools/visual_handoff.py` for resumable and rollback-protected visual work;
- `tools/update_dashboard.py` for expected-revision atomic tile patches;
- `tools/serve_dashboard.py --check-only` before loopback serving;
- `tools/verify_workspace.py` for the dependency-free public workspace check;
- `tools/snapshot.py` before larger repairs.

If a campaign predates these contracts, preserve it through the documented
compatibility path and report the migration gap; do not claim a check ran when
its tool or required state is absent.

# Reporting

In Designer Mode, report:

- findings ordered by severity;
- the file that needs attention;
- the player-experience risk;
- the smallest recommended fix.

Avoid defending existing structure. If a piece of machinery does not improve
play feel, say so.

# Player-Facing Use

Do not expose audit details to the Player. If an audit repair affects fiction,
present only the corrected in-world continuity after the repair is complete.
