# Workflow

RePoG Lite Audit

# Purpose

Use this workflow when checking a Lite campaign for continuity, player-facing
leakage, missing memory, stale threads, file health, or readiness for play.

Audit asks whether the campaign can support natural play, not whether every
narrative fact is schema-normalized.

# Audit Checklist

Check:

- `session_zero.md` exists and tracks the Session 0 module decisions;
- `research_dossier.md` exists and records research status, mode, source scope,
  canon/realism policy, hard boundaries, and open source questions;
- existing canon and specific real-world campaigns do not lock major world
  truths, powers, institutions, or factions while research is still
  `needed_pending` unless the Designer explicitly accepted that risk;
- fully original campaigns do not import external canon through research; they
  use adjacent research only as grounding and keep unresolved rules as
  Designer questions;
- `campaign_one_pager.md` is player-safe and does not reveal GM-only secrets;
- `system_fit.md` explains the expected play activity mix and mechanics
  weight;
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
- scenario, arc, or campaign closures have an advancement status of `due`,
  `offered`, `chosen`, `deferred`, or `applied`;
- normal fiction does not continue past a `due` or `offered` advancement gate;
- reward budget is driven by achievement quality first and play volume second;
- GM-awarded perks are fiction-derived, limited, and not exchangeable for a
  different reward;
- major arc closure changes world state, access, reputation, faction status, or
  identity in addition to raw character power;
- companion or allied NPC advancement is considered when an NPC meaningfully
  participated or changed;
- `current_state.yaml` is readable and small;
- `storytelling.md` exists and defines option prompting, reveal policy, and
  pacing defaults;
- `storytelling.md` defines challenge density, routine competence, clean
  success, consequence severity, and breather scene preferences;
- `opening_brief.md` exists and gives location, arrival context, player-known
  context, neutral action space, and hidden information boundaries;
- `creation_ledger.md` contains every T1+ named NPC, location, and faction;
- T2+ ledger entries have matching notes under `characters/`, `places/`, or
  `factions/`;
- T2+ NPC notes include table hook, default posture, mundane agenda, plain
  speech sample, compact appearance card, stat block, power band, weak
  stats/blind spots, and key info separated from personality;
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
  way;
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
- dashboard NPCs, clues, threads, visuals, map nodes, and inventory are all
  player-known or character-perceivable;
- no obvious mojibake or placeholder names remain;
- player-facing examples do not overuse cryptic, aphoristic, or market-style
  dialogue;
- ordinary NPCs have ordinary needs and speech when the scene calls for it;
- low-risk competent actions are not routinely turned into tests,
  complications, suspicion, or hard consequences;
- the opening or next scene gives the player something actionable.

# When Tools Exist

Use Lite tools when available:

- `tools/check_player_facing.py` for leakage;
- `tools/check_state.py` for state sanity;
- `tools/check_dashboard.py` for local dashboard state;
- `tools/snapshot.py` before larger repairs.

If the tools are not implemented yet, perform a manual audit and report that
the mechanical check layer is pending. Separate link checking and dice tools
are intentionally deferred until play proves they are needed.

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
