# RePoG Claude Code Plugin (development project)

`plugin/` is the plugin exactly as Claude Code loads it. Everything else here is
for development and is never shipped.

- `tests/` — pytest suite for the plugin helpers (`python -m pytest tests`).
- `dev/install.py` — sync `plugin/` into the desktop app's installed copy, with a backup.
- `dev/package.py` — build `dist/repog-plugin-<version>.zip` for upload.
- `docs/design/` — design notes per release.
- The marketplace entry lives at the repository root (`tritonsan/RePoG`), pointing
  at `./claude-plugin/plugin`; for local CLI testing use `claude --plugin-dir plugin`.

The plugin started as a fork of the canonical RePoG build (0.2.0). It is now
developed here directly; the canonical repo's `build_plugin.py` is not used.
