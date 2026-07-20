# RePoG — Judge Guide

## Project At A Glance

**Category:** Apps for Your Life

**Repository:** https://github.com/tritonsan/RePoG

**License:** Apache-2.0

**Credentials:** none

**Separate API key or hosted RePoG service:** not required

RePoG turns an agentic coding workspace into a persistent creative space for
coherent RPG campaigns and evolving fictional AI companions, backed by local,
inspectable memory.

The product is a ready-to-use workspace rather than a hosted website. Download
the ZIP, open the extracted folder in OpenAI Codex, and begin in natural
language. The selected experience maintains its own local memory while small
deterministic tools guard revisions, privacy, mechanics, and player-facing
projections.

## Fastest Product Test

1. On GitHub, choose **Code -> Download ZIP** and extract the archive.
2. Open the extracted folder in OpenAI Codex.
3. Start a new task and send:

   ```text
   Start RePoG and guide me through setup.
   ```

4. Choose **RPG Campaign** or **AI Companion**, then choose **Quick** for the
   shortest setup path.
5. Answer naturally. RePoG asks one decision at a time and materializes the
   accepted choices into the local campaign workspace.

One workspace holds one experience. To try both modes without overwriting the
first setup, extract a second fresh copy of the repository.

## Suggested RPG Check

Choose **RPG Campaign -> Quick** and provide a short mixed fantasy-survival
pitch. The setup should:

- offer a contextual Starter Bundle rather than a generic questionnaire;
- explain optional tracking cost instead of silently enabling mechanics;
- preserve the selected tone, boundaries, visual policy, and turn protocol;
- create a playable opening with current state, natural NPC presence, and a
  resumable scene anchor.

During play, try a routine action, an uncertain action that justifies a roll,
and a quiet social or recovery moment. The GM should preserve player
authorship, limit characters to believable knowledge, resolve the nearest
causal consequence, and allow the calm scene to remain calm unless an already
established trigger actually arrives.

## Suggested Companion Check

Use a fresh copy and choose **AI Companion -> Quick**. Define a fictional adult
character with a compact concept. The setup should establish identity, voice,
routine, important relationships, boundaries, and consent-based memory without
turning the companion into an RPG NPC sheet.

In conversation, the companion may disagree, refer back to something actually
shared, or mention a small causal development from their fictional life.
Personal disclosure should be gradual and relationship evidence should never
appear as an affection score. A direct identity question must receive a clear
answer that this is an AI portraying a fictional character.

## Build Week Feature Tour

The Build Week product story is organized around these seven pillars:

1. **Adaptive Setup** — RPG/Companion routing, Quick/Standard/Deep depth,
   Starter Bundles, lenses, and runtime profiles.
2. **Causal GM and Continuity** — authorship, knowledge, presence, causal
   response, checkpoints, advancement, and breathing room.
3. **Safe Mechanics and Transactions** — reproducible dice, resources,
   conditions, revisions, idempotency, rollback, and visual return anchors.
4. **Dashboard, Atlas, and Visuals** — adaptive tiles, player-safe multi-scale
   maps, approved images, responsive layouts, and accessible interaction.
5. **World Voices** — one event represented through sources with different
   knowledge, motives, channels, and claims; Compare Accounts never exposes
   objective hidden truth.
6. **AI Companion** — persistent identity, consent-aware memory, qualitative
   relationship development, independent continuity, and a lightweight View.
7. **Reliability and Privacy** — local validation, migrations, stale-write
   protection, private/public projection boundaries, and dependency-free
   verification.

## Local Visual Surfaces

After the matching Session 0 enables a view, the RPG Dashboard can be served
locally with:

```bash
python tools/serve_dashboard.py campaign/dashboard
```

Open `http://localhost:8787/`.

The separate lightweight Companion View can be served with:

```bash
python tools/serve_companion_view.py campaign/companion_view
```

Open `http://localhost:8790/`. Companion mode never loads the RPG Dashboard.
The Companion View accepts only an approved portrait and facts already shared
in conversation; private relationship reasoning, user memory, hidden contacts,
and undisclosed presence are structurally rejected.

## Dependency-Free Verification

From the repository root, run:

```bash
python tools/verify_workspace.py
python tools/verify_workspace.py --json
```

No package installation is required. The current public template verifies with
0 errors and 0 warnings. One informational `location_blank` result is expected
because a fresh workspace has not completed Session 0.

Focused checks are also available:

```bash
python tools/check_state.py campaign --scope full
python tools/check_dashboard.py campaign/dashboard/dashboard_state.json
python tools/check_world_voices.py campaign
python tools/check_companion.py campaign --scope full
python tools/check_companion_view.py campaign/companion_view/companion_view_state.json --campaign campaign
```

## What Changed During Build Week

Commit `7ccfd90` is the pre-existing baseline: a playable RPG workspace with a
basic Session 0, campaign memory, Dashboard V2, and 249 passing tests. The
meaningful Build Week product implementation is recorded in
`7ccfd90..6ae9430`. GPT-5.6 Sol in Codex was used to audit, plan, implement,
review, test, and validate the cross-file transformation. The current
development suite contains 317 passing tests.

The user made the product and tradeoff decisions: preserve natural model
judgment, keep state human-readable and local, avoid a second narrative engine,
protect player agency and privacy, and do not make every reply pay for heavy
persistence. GPT-5.6 Sol helped carry those decisions consistently across
workflows, state contracts, validators, migrations, Python tools, and browser
interfaces.

For the full feature-by-feature evidence ledger, verification notes, and exact
baseline distinction, see [`HACKATHON.md`](HACKATHON.md).
