# Hosted golden artifacts

`black-gull/bootstrap.json` is the reviewed, character-bounded Agent Session
Pack and first Agent Turn Brief used by the public jury table.

`workspace.zip` is deliberately not committed. Build it from the canonical
public RePoG commit with `tools/build_jury_bundle.py`; the script creates a
rootless runtime archive, validates the workspace and bootstrap, and writes
all generated release files below `.site-artifacts/hosted-runtime/`.

The public GitHub repository therefore keeps two products visibly separate:

- the standalone RePoG workspace used by local Codex-compatible tools; and
- the optional `apps/webmcp`, `runtime/hosted`, and `infra/aws` jury stack.
