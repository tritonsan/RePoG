# RePoG Workspace

RePoG turns an agentic coding workspace into either a long-form solo tabletop
RPG Game Master or a persistent AI Companion with a coherent fictional life.
This repository is the ready-to-use workspace: download the ZIP, open the
extracted folder, and start a new conversation.

## Full Walkthrough

This walkthrough shows the earlier public RPG flow. The current workspace also
includes World Voices, Atlas V1, the rebuilt GM contract, and AI Companion
mode.

[![Watch the RePoG demo](https://img.youtube.com/vi/jpXtyfrd5k0/maxresdefault.jpg)](https://youtu.be/jpXtyfrd5k0)

▶ **[Watch the full RePoG demo on YouTube](https://youtu.be/jpXtyfrd5k0)**

## What RePoG Includes

RePoG combines seven connected systems while keeping the workspace local,
readable, and usable as a downloaded folder:

1. **Adaptive setup:** separate RPG Campaign and AI Companion routes; Quick,
   Standard, and Deep depth; contextual Starter Bundles; composable lenses;
   research gates; and compact runtime profiles.
2. **Causal GM and continuity:** player-authorship protection, bounded
   character knowledge, natural NPC presence, independent trajectories,
   resumable scene frames, conditional persistence, advancement, and playable
   breathing room.
3. **Safe mechanics and transactions:** reproducible dice, strict resource and
   condition changes, revisions, monotonic operation identity, replay
   protection, atomic visual approval, rollback, and return to the interrupted
   scene.
4. **Dashboard, Atlas, and visuals:** adaptive player-safe tiles,
   revision-aware refreshes, responsive and accessible interaction, multi-scale
   setting-neutral maps, and approved visual continuity.
5. **World Voices:** letters, newspapers, reports, rumors, and institutional
   documents whose authors remain bounded by their own knowledge, motives, and
   communication channels. An artifact can exist without making its claims
   objective truth.
6. **AI Companion:** a separate lightweight experience with persistent
   identity, routines, social context, conservative elapsed-time development,
   gradual disclosure, consent-aware user memory, qualitative relationship
   evidence, and a privacy-safe Companion View.
7. **Reliability and privacy:** migrations, stale-write rejection, protected
   projections, browser smoke coverage, dependency-free verification, and 317
   passing development tests.

The public distribution does not embed or require a separate model API call.
It uses the capabilities already available in the agentic tool where the
workspace is opened, while deterministic local helpers protect hard state and
continuity rules.

## Start

<details>
<summary><strong>Show the four-step installation guide</strong></summary>

The interface language and exact layout may differ from the recordings, but the
four steps are the same.

### 1. Download the workspace

On GitHub, select **Code → Download ZIP**.

![Select Code and Download ZIP on GitHub](assets/getting-started/01-download-zip.gif)

The current repository file list may look simpler than the recording because
the public download has since been reduced to the clean player workspace.

### 2. Extract the ZIP

Extract the archive into a new folder. You may rename that folder for your
campaign.

![Extract the downloaded RePoG ZIP](assets/getting-started/02-extract-workspace.gif)

### 3. Open the folder

In Codex, select **Open Folder** and choose the extracted workspace. The same
folder can also be opened in Claude Code or another agentic coding tool.

![Open the extracted RePoG folder in Codex](assets/getting-started/03-open-in-codex.gif)

### 4. Start Session 0

Start a new conversation in the opened workspace and send:

```text
Start RePoG and guide me through setup.
```

![Start a new conversation in the RePoG workspace](assets/getting-started/04-start-conversation.gif)

Choose RPG Campaign or AI Companion, then choose Quick, Standard, or Deep
Session 0 and answer naturally. After your pitch, RePoG offers a small Starter
Bundle of experience-specific approaches;
you can accept one, mix them, change them, use the recommended default, or
defer a non-critical choice.

</details>

The included `campaign/` folder is blank campaign memory. The agent fills and
maintains it while you focus on the character, world, and choices. You do not
need to copy templates, run an installer, clone a development repository, or
understand the file structure before playing.

## Choose An Experience

- **RPG Campaign:** RePoG acts as Game Master, maintains a living world, and
  supports scenes, NPCs, optional mechanics, arc closure, visuals, and the
  player-safe Dashboard.
- **AI Companion:** RePoG performs one persistent adult fictional character
  with a grounded independent life, social ecology, private knowledge,
  qualitative relationship development, and natural asynchronous messages.

The Companion does not pretend to be a real human. It stays in character in
ordinary conversation, but a direct identity question receives a clear answer
that it is an AI portraying a fictional companion. It never runs a hidden
background process, exposes a love meter, or silently stores sensitive user
facts.

## Session 0 Depth

- **Quick:** RPG uses 6–8 decisions; Companion uses exactly 7. Roughly 10–15
  minutes.
- **Standard:** RPG uses 17 core modules; Companion uses 15. Roughly 30–60
  minutes.
- **Deep:** adaptive detail packs, normally 30–45 decisions and 60–120 minutes.

All modes use the same continuity model. Quick records visible defaults;
Standard gives a balanced setup; Deep opens only the detail packages relevant
to the chosen campaign.

## AI Companion Continuity

Companion setup defines identity, appearance, voice, values, contradictions,
backstory, home, work or education, finances, routine, hobbies,
responsibilities, family and friends, active problems, projects, and short- and
long-term goals. Close social contacts use the same T1–T3 memory tiers as RPG
NPCs, while casual background people remain lightweight.

The character's life advances only from established causes. On the next user
message, one deterministic local exchange call measures elapsed wall time,
advances the contact clock, and supplies a conservative ceiling: short gaps
usually preserve the same activity, ordinary gaps allow at most a small
grounded update, and long gaps receive a compressed recap rather than a
cascade of dramatic events. A second write is needed only when the reply
creates a durable change. Retried operations are idempotent, backward time is
rejected, and asking what the character is doing twice does not randomly
teleport them elsewhere.

The relationship remains qualitative and evidence-based; it is not a meter or
an ordered intimacy ladder. The companion can disagree, refuse, have
boundaries, reveal each private topic gradually, remember an explicitly shared
upcoming event, or bring up one development from their own life. User feelings
are never inferred as facts. Raw transcripts are not the memory model; Session
0 can disable user memory, ask before every save, or allow low-risk contextual
memory, while sensitive context always requires explicit consent.

Companion mode never loads the RPG Dashboard. It can optionally create a much
lighter separate Companion View containing only an accepted portrait and
facts already shared in conversation. Private whereabouts, relationship
evidence, disclosure readiness, user memory, hidden contacts, and internal
state never appear there. The View refreshes only when its visible truth
changes, so ordinary replies do not pay a dashboard cost. See
[`docs/companion-mode.md`](docs/companion-mode.md) for the runtime, privacy,
disclosure, and migration contract.

## RPG Lenses And Optional Mechanics

RPG Session 0 can combine setting lenses (`fantasy`, `realistic`, `cyberpunk`) with
the `survival` play lens. Lenses shape questions and coherent defaults; they do
not silently turn on HP, mana, inventory accounting, dice, wounds, or other
rules. RePoG explains the tracking cost first, and only the mechanic modules
you approve become part of the campaign.

The resulting `play_profile.yaml` keeps the accepted lenses, mechanics,
narrative signature, player-authorship boundary, resolution grounding,
breather preference, advancement cadence, dashboard policy, visual policy,
map-skin preference, optional World Voices policy, and turn-speed preference in
one compact runtime contract.
This lets a mixed fantasy-survival campaign keep both identities without making
every fantasy campaign track rations or spell points.

## RPG Turn Speed And Continuity

RPG Session 0 also asks how much maintenance each turn should perform:

- **Fast (recommended):** saves current truth immediately, uses a small scene
  checkpoint when needed, and reserves full distillation for five durable
  turns or a true structural boundary.
- **Balanced:** reconciles secondary notes at important beats or after three
  durable turns.
- **Maximum Continuity:** updates every affected note and runs full checks on
  every durable turn.
- **Custom:** lets you tune the cadence without disabling core continuity
  safeguards.

The setup interview shows typical wait ranges and separately explains the
extra time for dashboard refreshes and generated images. These are planning
estimates rather than guarantees.

### Selective structural parallelism

New workspaces also use **Selective Structural** parallelism when the active
agentic tool supports sub-agents. RePoG may split independent proposal work at
Session 0 completion, multi-domain research, a large full distill, or a major
arc closure, then let the coordinating agent merge and validate it once. This
can shorten those exceptional waits, but it may use more model allowance.

Ordinary RPG turns and Companion messages stay single-agent so their intent,
voice, and immediate continuity remain coherent. Supporting agents never
write campaign state or speak to the player. Tools without sub-agent support
run the same work serially, with no missing features. Existing campaigns keep
parallelism off until it is explicitly migrated or selected.

See [Selective Structural Parallelism](docs/semantic-parallelism.md) for the
exact boundaries, provisional timing ranges, and repeatable benchmark method.

## What RePoG Keeps Coherent

- current scene, fictional time, character state, inventory, and pressure;
- NPC location, activity, availability, natural presence, and independent next
  move;
- playable routes, access, traffic, and player-known locations;
- current relationships, debts, trust, tension, and information asymmetry;
- factions and offscreen world movement only when fiction triggers them;
- secrets and knowledge boundaries;
- progression, companion development, arc closure, and next-act preparation;
- accepted visuals and the optional player-safe dashboard.
- causally justified letters, notices, reports, rumors, and contradictory
  in-world accounts when optional World Voices is enabled.

During play, these notes and checks remain behind the curtain. The player
speaks in natural language and receives the living world, not technical state.

## RPG GM Flow And Breathing Room

RePoG resolves each turn from the player's stated intent and method, the
world's real resistance, what involved characters can actually know, and the
nearest causal consequence. The GM does not speak for the player character or
decide their private feelings unless the selected narration contract explicitly
invites shared interiority.

The pacing model also makes room for recovery, ordinary conversation,
maintenance, companion time, small exploration, and quiet personal choices.
A calm scene does not receive a surprise threat merely because the GM wants to
move on. The player may remain there, leave through a natural affordance, or
encounter an already-established world event when its real trigger becomes
due.

If you request a generated visual, RePoG first preserves the interrupted
question or fictional beat. A visual is not treated as campaign canon or added
to the dashboard until you accept it; after acceptance, revision, or
cancellation, play returns to the preserved point.

## Optional Companion View

When Companion Session 0 selected `light`, open its separate read-only view
with:

```bash
python tools/serve_companion_view.py campaign/companion_view
```

Then visit `http://localhost:8790/`. This is not the RPG Dashboard: its initial
HTML, CSS, and JavaScript total about 13 KB, it uses no map or RPG polling
surface, and ordinary replies do not refresh it. It contains only accepted art
and facts already shared in conversation. Precise private presence,
relationship evidence, disclosure readiness, hidden contacts, user memory,
and internal continuity fields are structurally rejected.

## Optional RPG World Voices

World Voices lets the setting communicate through persistent letters,
newspapers, notices, faction documents, legal records, intelligence, rumors,
and other setting-appropriate artifacts. Different people and institutions may
describe the same event differently because each source is limited by what it
could observe, learn, infer, conceal, distort, or deliberately misrepresent.
A document can exist in the world without making its claims objective truth.

The feature is off by default and remains trigger-driven: ordinary turns do no
document work or archive scan. When enabled in Session 0, the campaign chooses
review policy, communication speed, artifact richness, and whether legitimately
acquired documents appear in the read-only Dashboard. The Player replies,
publishes, shares, leaks, or questions documents through natural conversation;
drafted character wording always waits for approval. See
[`docs/world-voices.md`](docs/world-voices.md).

## Optional RPG Dashboard

After Session 0, open the local player dashboard with:

```bash
python tools/serve_dashboard.py campaign/dashboard
```

Then visit `http://localhost:8787/`. The dashboard is read-only and contains
only player-known information. Dashboard V3 uses campaign-specific tiles, so a
mechanics-light game does not show invented stats or resources. Revision-aware
updates reject stale data instead of silently replacing newer state. Its
optional Atlas V1 map supports regions, cities, interiors, and abstract
networks with local, setting-neutral skins; it does not require a map service,
API key, or generated background image. See
[`docs/dashboard.md`](docs/dashboard.md).

## Optional Checks

```bash
python tools/verify_workspace.py
python tools/check_state.py campaign --scope hot
python tools/check_state.py campaign --scope full
python tools/check_companion.py campaign --scope full
python tools/companion_state.py campaign begin-exchange --operation-id exchange-0001 --expected-state-revision 0
python tools/check_companion_view.py campaign/companion_view/companion_view_state.json --campaign campaign
python tools/check_dashboard.py campaign/dashboard/dashboard_state.json
python tools/check_world_voices.py campaign
python tools/snapshot.py campaign --label before_scene
```

`verify_workspace.py` is the dependency-free all-in-one smoke check for the
downloaded workspace. Add `--json` for agent-readable output. The individual
commands remain useful when diagnosing one area. These are guardrails, not a
second game engine.

## Workspace Contents

- `AGENTS.md`: durable GM and continuity rules.
- `CLAUDE.md`: compatibility bridge for Claude Code.
- `OPEN_CAMPAIGN.md`: first-conversation instructions.
- `workflows/`: worldbuilding, RPG GM, Companion conversation, distill, and
  audit procedures.
- `briefs/`: Session 0 interview guidance and composable genre lenses.
- `campaign/`: this RPG or Companion's readable memory, optional RPG
  Dashboard, and independent optional light Companion View.
- `tools/`: small local checks, snapshots, mechanics, and style helpers.

RePoG is licensed under the Apache License, Version 2.0. See [`LICENSE`](LICENSE).
