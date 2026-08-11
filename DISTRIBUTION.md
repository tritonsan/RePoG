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

## Building A Release Package

Maintainers should build an auditable local package from the committed `HEAD`:

```powershell
python -B tools/build_distribution.py `
  --target "..\RePoG-release" `
  --archive "..\RePoG-release.zip"
```

Use `--dry-run --json` to inspect the source commit, target, and tracked file
count without writing anything. Existing targets and archives are refused.

The builder applies the product allowlist to `git ls-files` and gives
`git archive HEAD` only the selected paths; it never copies the working tree.
This means both untracked material and mistakenly tracked `campaigns/`,
examples, tests, development notes, caches, local secrets, Git metadata, and
non-template files under `campaign/` stay outside the package. It verifies the
extracted workspace, writes `DISTRIBUTION_MANIFEST.json` with SHA-256 hashes,
and only then moves the staged directory into place. The optional ZIP is
generated in stable path order with fixed timestamps.

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
