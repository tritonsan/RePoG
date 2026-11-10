# Distribution Boundary

## Canonical Source

The Git repository rooted at `public/RePoG` is the only canonical RePoG
product source in the maintainer workspace. Directories outside that Git root,
including `development/public-repog`, `modes/lite`, `One Piece Lite`, local
campaign copies, and demo material, are development, legacy, or user data.
They must never be merged into a public package by copying the parent folder.

The public GitHub repository represents this canonical root directly. GitHub's
**Code -> Download ZIP** archive contains tracked files and excludes `.git`
metadata and ignored local files.

This is the **source archive**: tests, examples, and CI configuration belong in
the canonical repository. It is playable, but intentionally does not pass the
strict filtered-player-package boundary. The CI workflow builds that separate
player ZIP and uploads it as a `RePoG-player-...` run artifact.

## Development Checks

From the canonical source root, use Python 3.10 or later:

```text
python -m pip install -r requirements-dev.txt
python -B -m pytest
```

`pytest.ini` selects only the canonical `tests/` suite. Tests use temporary
campaigns; the blank `campaign/` template is never their writable fixture.
Development dependencies are not player dependencies. `verify_workspace.py`
remains a standard-library-only smoke check.

The retained regression suite covers RPG commits, Companion persistence,
Session 0, migrations, knowledge protection, Atlas, mechanics, Agent Seat,
portable schema conformance, and filtered-package creation. Semantic play
quality is evaluated separately using `evaluation/`; passing Python tests
does not establish immersion or long-campaign narrative quality.

## Building A Release Package

Maintainers should build an auditable local package from the committed `HEAD`:

```powershell
python -B tools/build_distribution.py `
  --target "..\RePoG-release" `
  --archive "..\RePoG-release.zip"
```

Use `--dry-run --json` to inspect the source commit, target, and tracked file
count without writing anything. Existing targets and archives are refused.

The builder reads both the file list and the product allowlist from the same
resolved committed `HEAD`, then gives `git archive` only the selected paths.
It never copies the working tree or reads the mutable index for package
membership. Commit a finished change before building its release.
This means both untracked material and mistakenly tracked `campaigns/`,
examples, tests, development notes, caches, local secrets, Git metadata, and
non-template files under `campaign/` stay outside the package. It verifies the
extracted workspace, writes `DISTRIBUTION_MANIFEST.json` with SHA-256 hashes,
and only then moves the staged directory into place. The optional ZIP is
generated in stable path order with fixed timestamps.

The plugin edition for Claude Code is built from the same source; see
[Building The Claude Code Plugin](#building-the-claude-code-plugin).

The package also carries the Claude Code layer: `CLAUDE.md`,
`.claude/settings.json`, `.claude/launch.json`, and the Markdown files directly
under `.claude/output-styles/` and `.claude/agents/`. Machine-local Claude Code
state, such as `.claude/settings.local.json`, session worktrees, and
`CLAUDE.local.md`, is outside the allowlist and never enters a package.

The package includes all four `contracts/agent-seat/v1/` schemas and the routed
workflow/reference and evaluation files. Pure adapters in
`tools/compile_agent_brief.py` translate portable intents and resolutions;
local Agent Seat storage/HTTP records remain a distinct internal format.
Importing an intent does not submit it or commit fictional truth.

## Building The Claude Code Plugin

Since plugin 0.2.0 the plugin is maintained as its own project, and this build
is frozen at plugin 0.1.1; see the Plugin Edition section of
`docs/claude-code.md`.

`tools/build_plugin.py` assembles the plugin edition. It combines the
plugin-only files in `plugin/` with the engine trees selected by the same
allowlist, places the blank campaign template under `templates/campaign/`, and
expands `AGENTS.md` into the `repog:play` skill. Like the player package, it
reads committed `HEAD` unless `--worktree` is given and refuses an existing
target. Before writing, it checks the result against the plugin directory's
automated limits: file count, file sizes, names, README, license, manifests,
and every bundled path that a skill or hook names.

Claude cannot generate images, and Claude Code uses neither browser-agent seats
nor the Companion View, so the plugin is not a byte copy of the engine.
`OMITTED` and `TRIMS` in `tools/build_plugin.py` list the whole difference:
those three layers, the standalone workspace's Claude Code page, and the
release and packaging tools (which need this source checkout) are left out, and
the sentences that pointed at them are removed. A trim whose anchor no longer
matches fails the build instead of shipping stale text, and so does a carried
document that still names an omitted file. Two engine helpers
(`tools/serve_dashboard.py` and `tools/check_companion.py`) treat the Agent Seat
layer and the Companion View as optional, so the plugin runs without them;
every other shared file is carried unchanged.

```powershell
python -B tools/build_plugin.py --target "..\repog-plugin" --archive "..\repog-plugin-0.1.1.zip"
claude plugin validate --strict "..\repog-plugin"
```

`--archive` also writes the plugin as a ZIP with the manifest at its root. The
entries are sorted and carry fixed timestamps, so the same files always give the
same bytes. Both the target and the archive must be new paths, and the archive
cannot sit inside the plugin folder.

The built folder is meant to be the root of its own repository; its
`.claude-plugin/marketplace.json` lists the plugin at `./`. `plugin/` itself
never enters the player package.

## Automated Artifacts

`.github/workflows/verify.yml` tests Python 3.10 on Windows, macOS, and Linux,
plus Python 3.13 on Linux. Each job verifies the blank workspace, builds two
independent packages with the same `RePoG` root name, compares ZIP SHA-256
hashes, extracts a ZIP, and verifies the extracted package before upload.
Artifacts are workflow-run downloads; this workflow does not publish a GitHub
Release or modify a player's campaign. For manual reproducibility checks, use
the same target directory basename, because that name is the ZIP's root.

## Release Gate

Run the strict boundary check on an extracted package:

```powershell
python -B tools/verify_workspace.py "..\RePoG-release" --distribution
```

Distribution mode rejects Git and hosting metadata, tests, development trees,
Python bytecode and caches, virtual environments, editor state, and vendored
packages without an adjacent license. If a generated manifest is present, all
listed hashes are verified.

`.gitignore` is intentionally included. It contains no repository history or
credentials and protects users who initialize Git in their campaign folder.

## Third-Party Code

Every bundled third-party package must keep its upstream license beside the
vendored files and must be listed in `THIRD_PARTY_NOTICES.md`. Adding or
upgrading a vendor requires updating both the vendored license and that
inventory before release.
