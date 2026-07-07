# Why RePoG Fits Codex

RePoG is not a chatbot prompt. It is a repository-shaped RPG workspace.

That makes Codex a natural fit: Codex can read durable repo instructions, edit
Markdown campaign memory, run small validation tools, and keep a long session
grounded in files instead of relying only on the current chat window.

## The Core Pattern

RePoG uses the same workspace pattern that makes agentic coding useful:

- durable instructions live in `AGENTS.md`;
- task workflows live in `workflows/`;
- reusable startup prompts live in `briefs/`;
- campaign memory lives in Markdown and YAML files;
- small Python tools check invariants without becoming a full game engine.

For RPG play, this means the GM can improvise naturally while still maintaining
continuity across long campaigns.

## Why A Repo Instead Of A Chat Prompt

Long AI roleplay tends to fail when important details exist only in the chat
history. RePoG gives those details stable homes:

- `knowledge_boundaries.md` separates GM-only truth from player, companion,
  NPC, and faction knowledge.
- `creation_ledger.md` records named NPCs, places, and factions as they appear.
- `relationship_map.md` keeps compact links between people, places, factions,
  debts, and consequences.
- `progression.md` and `arc_closure.md` make rewards and upgrades explicit at
  the right narrative moments.
- `next_act_prep.md` carries old consequences into the next major act.

The agent does not need to remember everything perfectly. It needs to read and
maintain the right files.

## What Codex Demonstrates Well Here

RePoG is a useful Codex example because it combines several Codex strengths:

- repo-local instructions through `AGENTS.md`;
- workflow-following across multi-step creative tasks;
- editing many small text files safely;
- running local checks before and after changes;
- extending the same workspace pattern toward images or other assets when the
  agentic tool supports them;
- previewing a local player dashboard through the same file-backed workflow;
- turning a folder of plain files into a specialized interactive environment.

The result is not just a game. It is a demonstration of how agentic coding tools
can run a non-code workflow when the workflow is shaped like a repository.

## Open-Source Agent Workflow Value

RePoG can help people experiment with:

- long-running agent memory patterns;
- human-readable state instead of opaque vector memory;
- agent behavior encoded as repo-local workflows;
- validation tools that support creative work without replacing it;
- portable workspace conventions for Codex and other agentic coding tools.

This is why RePoG is currently Codex-first, but not Codex-only. Codex is the
best tested target today; the broader project is about agentic workspaces as a
medium for persistent, creative systems.
