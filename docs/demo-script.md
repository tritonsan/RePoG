# RePoG Demo Script

This script demonstrates the real first-time flow: download RePoG, create a
clean campaign workspace, open that workspace in Codex, complete Quick Session
0, validate it, open the player dashboard, and play one turn.

## Format And Length

- Full walkthrough: 4–7 minutes with edited waiting time.
- Short trailer: 60–90 seconds, using cuts from the full walkthrough.
- Do not pretend the complete setup happens live in 60 seconds.

The full walkthrough is the source recording. A short trailer can keep only the
workspace command, depth choice, two Session 0 answers, completed files,
dashboard, opening line, and one player action.

## Demo Campaign

Use the original setting **The Saltglass City**. It is visually distinct,
requires no copyrighted setting, and exercises character memory, hidden
knowledge, factions, relationships, locations, and the dashboard.

Campaign id: `saltglass_city`

## 1. Download And Create A Clean Workspace

Download or clone RePoG into a new folder. In a terminal opened at that folder,
show the dry run first:

```powershell
python tools/create_campaign_workspace.py `
  --target "D:\RePoG Games\Saltglass City" `
  --campaign-id saltglass_city `
  --git no `
  --dry-run
```

Briefly show that the resolved target and runtime manifest are reported. Then
create the workspace:

```powershell
python tools/create_campaign_workspace.py `
  --target "D:\RePoG Games\Saltglass City" `
  --campaign-id saltglass_city `
  --git no
```

Use `--git no` in the demo to avoid an identity prompt or unrelated Git
explanation. Mention that `--git ask` is the normal optional choice.

Close the source repository. Open only `D:\RePoG Games\Saltglass City` in
Codex and create a new task there. This distinction matters: the generated
workspace, not the downloaded development repository, is the campaign home.

## 2. First Message

Paste exactly:

```text
Start this RePoG campaign and guide me through Session 0.
```

Expected behavior: Codex asks only whether the player wants Quick, Standard,
or Deep Session 0. If it asks for the pitch in the same message, the depth gate
has not been followed and the take should be restarted after checking that the
generated workspace contains the latest instructions.

## 3. Quick Session 0 Answers

The exact wording of Codex's questions may vary. Answer each decision with the
matching block below. Do not paste all blocks at once; the demo should show one
decision per exchange.

### Decision 1 — Depth

```text
I choose Quick. Let us build a playable opening in eight decisions. Fill any
missing detail with coherent defaults, but show me every assumption clearly in
the final summary.
```

What this demonstrates: the new depth gate, decision target, and visible
defaults.

### Decision 2 — Campaign Pitch

```text
The setting is an original weird nautical fantasy noir: Saltglass City, a
half-sunken port built over black water and glass reefs. The tone should be
atmospheric, mysterious, and human, but not grimdark. My player fantasy is to
play a former storm-diver trying to rebuild a life in the city while
investigating a secret from her past. Play should focus on investigation,
social pressure, dangerous exploration, and difficult personal choices. It
should not turn into an epic heroic saga.
```

### Decision 3 — Boundaries, Agency And Consequences

```text
No graphic torture, sexual violence, or detailed harm to children. Horror and
violence may appear, but keep them atmospheric and restrained. Romance is fine
only if it develops naturally, with intimate scenes kept off-screen. Never make
my character's decisions for me. Failure should not stop the story; it should
create a cost, a lost opportunity, a new debt, or rising pressure. Permanent
death should be possible only after an explicit, high-risk choice.
```

### Decision 4 — Player Character

```text
My character is Mara Venn, a former storm-diver who now works as an independent
investigator. Her defining ability is hearing brief sensory memories trapped
inside pieces of saltglass. The ability does not reveal certain truth: its
fragments require physical contact, and prolonged use risks migraines,
disorientation, and confusion between Mara's memories and someone else's. Mara
is observant, stubborn, and calm under pressure. Her central weakness is that
guilt makes her act alone instead of asking for help. She begins at the
competent level; use concept-appropriate defaults for the numeric details.
```

### Decision 5 — Starting World, Pressure And Place

```text
The game begins at dawn in Lantern Quay: rain-dark stone piers, black water,
pale glass reefs, hanging bells, and ordinary dockworkers preparing for the
early shift. Mara has just returned to the city after years away. A courier has
left her a piece of saltglass wrapped in oilcloth; it carries her dead brother's
voice, but only while the tide is receding. The immediate pressures are harbor
collectors searching for the courier and the closing tidal window. The location
should not exist only to serve the mystery; give it its own work, traffic, and
human routines.
```

### Decision 6 — Mechanics, Failure And Progression

```text
Use light-to-moderate mechanics. Make brief checks when there is meaningful
uncertainty or real resistance, while routine expertise succeeds cleanly. We do
not need the resource and cooldown ledger yet. Failure should never completely
block information or progress; instead, it may cost time, trust, position,
health, or create a debt. Discuss advancement after every major scenario and
arc. Rewards may include access, reputation, relationships, and lasting change
in the city as well as personal power.
```

### Decision 7 — Narration And Visuals

```text
Use second person and present tense. Keep the prose atmospheric but clear;
routine conversations should be brief, while discoveries and emotional turns
may breathe a little more. Do not give me a menu of choices every turn or
constantly end with “What do you do?” Reveal hidden information only through
evidence, perception, consequences, or discovery. NPCs should infer only from
what they know and observe. Use curated visual mode: create only one opening
image of Lantern Quay for the demo. The direction is painterly cinematic
concept art with teal, gold, and black, rain, salt, glass, and lantern light.
No anime and no neon cyberpunk. Only accepted images may appear on the
dashboard.
```

### Decision 8 — Research And Final Defaults

If Codex separates research and final confirmation, answer them in two turns;
Quick may therefore finish in eight decisions plus one confirmation exchange.

Research answer:

```text
This is a fully original world, so no external canon research is needed. Use
general plausibility for maritime and harbor life, but do not turn uncertain
real-world detail into firm claims. Set the research status to `not_needed` for
now.
```

Final confirmation:

```text
I approve the summary. Record every assumption filled by Quick mode as a
visible default. Create at least one opening NPC with an independent objective
and a natural reason to be present, at least one real connection from Lantern
Quay to another location, and one world pressure that can advance without the
player. Do not leak hidden truths into the dashboard or opening narration. Run
the checks, take the starting snapshot, and then begin with a natural opening
scene.
```

### Expected Visual Handoff

Before Codex generates the Lantern Quay draft, it should explain that the next
result may contain only the image, that the draft is not yet canon or on the
dashboard, and that you should reply with acceptance or revisions. The image
appearing alone after that warning is expected; the warning prevents it from
becoming a dead end.

If the draft is suitable, reply:

```text
I accept this image as the visual canon for Lantern Quay. Add the accepted
asset to the dashboard, complete the remaining checks, and then return to the
paused Session 0 transition and begin the opening scene.
```

Codex should not answer only "added to the dashboard." It should complete and
validate the asset update, then bridge directly into the prepared opening. If
the image is not suitable, describe the revision instead; Codex should retain
the same Session 0 return anchor through regeneration.

## 4. What To Show While Codex Finishes

Use quick cuts rather than reading every file. Show:

- `campaign/setup_profile.yaml`: `quick`, completed decisions, visible
  defaults, and `ready_for_play: true`;
- `campaign/current_state.yaml`: current place and continuity revision;
- `campaign/active_cast.md`: an NPC's activity, reason here, and next move;
- `campaign/location_graph.md`: Lantern Quay connected to another real place;
- `campaign/knowledge_boundaries.md`: hidden truth separated from player
  knowledge;
- `campaign/snapshots/`: the starting snapshot;
- `campaign/dashboard/dashboard_state.json`: only player-safe information.

Do not linger on file internals. The point is that the notebook is readable and
the player does not have to maintain it manually.

## 5. Validation And Dashboard

If Codex has not already shown the successful checks, run:

```powershell
python tools/check_state.py campaign
python tools/check_dashboard.py campaign/dashboard/dashboard_state.json
```

Both should report zero errors before recording the final take.

Start the local dashboard:

```powershell
python -m http.server 8787 --directory campaign/dashboard
```

Open `http://localhost:8787/`. Show the current scene, Mara, visible NPCs,
player-known pressure, and the small known map. Confirm visually that no GM-only
name, secret, internal id, file path, or technical explanation appears.

## 6. First Player Action

After Codex presents the opening, type:

```text
Before the tide finishes receding, I take the shard in my bare palm. As I focus
on my brother's voice, I also watch for anyone nearby who might be searching
for the courier.
```

This action is useful because it combines Mara's risky capability with
perception and immediate pressure. The response should stay in Player Mode,
avoid technical vocabulary, and create a consequence only if supported by the
campaign state and established fiction.

After the response, briefly show that continuity revision, current state,
relevant NPC activity, and player-safe dashboard information changed together.

## Critical Recording Checklist

- The source repo and generated campaign workspace are visibly different.
- The first Session 0 question asks only for Quick, Standard, or Deep.
- The demo answers one decision per message.
- Quick defaults are visible rather than silently treated as player choices.
- Before generation, Codex explains that the image will appear alone and says
  how to accept or revise it.
- After acceptance and dashboard placement, Codex resumes Session 0 or play
  instead of ending with a technical confirmation.
- NPC presence has an ordinary in-world reason.
- The location has independent activity and at least one valid connection.
- Hidden information never appears on the dashboard.
- State validation and dashboard validation both have zero errors.
- The opening gives pressure and freedom without revealing the solution.
- The first play response contains no paths, YAML, ids, validators, or mode
  terminology.

## Avoid

- Opening the downloaded development repository and treating it as the final
  campaign workspace.
- Using old `campaigns/<id>` commands in the standalone demo.
- Showing copyrighted worlds.
- Pasting every Session 0 answer at once.
- Spending the video on folder internals or terminal output.
- Claiming the full walkthrough takes 60–90 seconds.
- Presenting RePoG as Codex-only or as a standalone game application.
