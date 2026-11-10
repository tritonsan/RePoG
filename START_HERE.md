# Start Here

This extracted folder is already a ready-to-use RePoG workspace.

Use Python 3.10 or later, available to your agentic tool as `python` or
`python3`. The player helpers require no third-party packages. A filtered
player ZIP is attached as an artifact to each successful
[Verify and package run](https://github.com/tritonsan/RePoG/actions/workflows/verify.yml).
GitHub's **Code → Download ZIP** also works, but includes source-only tests and
maintainer files.

1. If the workspace is still inside a ZIP archive, extract it into a new
   folder first.
2. Open the extracted folder in Codex, Claude Code, or another compatible
   agentic coding tool. In Claude Code, accept the folder-trust prompt; see
   [`docs/claude-code.md`](docs/claude-code.md).
3. Start a new conversation in that workspace.
4. Send exactly:

```text
Start RePoG and guide me through setup.
```

RePoG first asks whether you want an **RPG Campaign** or an **AI Companion**.
For a new RPG, it takes your short campaign idea first, then helps you explicitly
choose Quick, Standard, or Deep. If you already supplied either answer, it keeps
it instead of asking again. Companion keeps its existing depth-first setup.

Quick emphasizes essential choices and reviewing the GM's preparation; Standard
designs the consequential alternatives together. Their internal completion maps
are not quotas of questions. Both include design approval, then one approval of
the actual prepared campaign to lock and start. Existing campaigns retain their
accepted setup version. You can leave unneeded details open, pause, correct a
choice, or ask to stop expanding without granting an unstated permission.

RPG Deep uses nine dependency-gated stages: it establishes authority and
research before the character/world loop, then builds the living world,
runtime contract, campaign horizon, and first Act without a fixed plot.

You do not need to copy templates, edit `campaign/`, run an installer, or use
a campaign-creation command. RePoG prepares and maintains the workspace as you
answer and play.

For the feature overview, optional Dashboard and Companion View instructions,
and local verification commands, see [`README.md`](README.md).
