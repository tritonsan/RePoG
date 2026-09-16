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
   agentic coding tool.
3. Start a new conversation in that workspace.
4. Send exactly:

```text
Start RePoG and guide me through setup.
```

RePoG first asks whether you want an **RPG Campaign** or an **AI Companion**.
It then asks whether you want Quick, Standard, or Deep setup.

New RPG Quick uses 9 decision slots; Standard uses 20–29 decisions. Both end
with one approval of the actual prepared campaign to lock and start. Decision
slots may take more than one exchange. Existing campaigns retain their
accepted setup version.

RPG Deep uses nine dependency-gated stages: it establishes authority and
research before the character/world loop, then builds the living world,
runtime contract, campaign horizon, and first Act without a fixed plot.

You do not need to copy templates, edit `campaign/`, run an installer, or use
a campaign-creation command. RePoG prepares and maintains the workspace as you
answer and play.

For the feature overview, optional Dashboard and Companion View instructions,
and local verification commands, see [`README.md`](README.md).
