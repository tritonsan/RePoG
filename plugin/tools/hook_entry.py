"""Entry point for the plugin's hook scripts.

Each subcommand reads one hook event (JSON on standard input), does its work,
and prints only what Claude Code expects. It never raises and never blocks:
a failing hook must not cost the Player a prompt or a reply.

    prompt         UserPromptSubmit: apply settled staged curation, then emit
                   the scene capsule as hidden `additionalContext`.
    stop           Stop (async): run the presentation lint over the reply.
    session-start  SessionStart: mark the capsule for a full refresh.
    pretool        PreToolUse: confine the repog-curator agent to its one
                   staging file.

Output is ASCII JSON (`ensure_ascii`), so no console code page can corrupt a
name in the capsule.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable


# Claude Code caps injected context at 10,000 characters; stay under it.
MAX_CONTEXT = 9_500
CURATOR_AGENT = "repog-curator"
CURATOR_DENIAL = (
    "The RePoG curator may write only its one staging file under "
    "campaign/.repog-runtime/curation/; it reads everything else."
)


def _event() -> dict[str, Any]:
    try:
        raw = sys.stdin.buffer.read()
        value = json.loads(raw.decode("utf-8-sig") or "{}")
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _emit(value: dict[str, Any]) -> None:
    sys.stdout.buffer.write((json.dumps(value, ensure_ascii=True) + "\n").encode("ascii"))
    sys.stdout.flush()


def _ready_campaign(event: dict[str, Any]) -> tuple[Path | None, dict[str, str]]:
    import repog_runtime

    campaign = repog_runtime.find_campaign(event.get("cwd"))
    if campaign is None or not repog_runtime.is_ready_rpg(campaign):
        return None, {}
    return campaign, repog_runtime.runtime_settings(campaign)


def prompt(event: dict[str, Any]) -> None:
    campaign, settings = _ready_campaign(event)
    if campaign is None:
        return
    if settings.get("boundary_curator") == "background":
        try:
            import curation
            import rpg_state

            if curation.list_staged(campaign):
                rpg_state.commit_curation(campaign)
        except Exception:
            pass  # a waiting proposal is retried on the next prompt
    if settings.get("scene_capsule") != "on":
        return
    import scene_capsule

    text = scene_capsule.run_hook(event)
    if text:
        _emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": text[:MAX_CONTEXT],
                }
            }
        )


def _reply_text(event: dict[str, Any]) -> str:
    """Everything the Player saw in the reply that just ended."""

    import repog_runtime

    transcript = event.get("transcript_path")
    turn = repog_runtime.last_turn(transcript) if isinstance(transcript, str) and transcript else None
    texts = list(turn["assistant_texts"]) if turn else []
    last = event.get("last_assistant_message")
    # The transcript may not hold the final message yet when Stop fires.
    if isinstance(last, str) and last.strip() and (not texts or texts[-1].strip() != last.strip()):
        texts.append(last)
    return "\n".join(texts)


def stop(event: dict[str, Any]) -> None:
    campaign, settings = _ready_campaign(event)
    if campaign is None:
        return
    if settings.get("presentation_lint") == "on":
        try:
            import presentation_lint

            presentation_lint.run_hook(event)
        except Exception:
            pass
    session_id = event.get("session_id")
    if settings.get("scene_capsule") == "on" and isinstance(session_id, str) and session_id:
        # Names in this reply join the next capsule's cast even when the
        # Player's next message does not repeat them.
        import scene_capsule

        text = _reply_text(event)
        if text:
            names = scene_capsule.names_in_text(campaign, text, settings=settings)
            scene_capsule.remember_names(campaign, session_id, names)


def session_start(event: dict[str, Any]) -> None:
    import repog_runtime

    campaign = repog_runtime.find_campaign(event.get("cwd"))
    if campaign is None:
        return
    import scene_capsule

    session_id = event.get("session_id")
    scene_capsule.reset(campaign, session_id if isinstance(session_id, str) and session_id else None)


def pretool(event: dict[str, Any]) -> None:
    agent_type = str(event.get("agent_type") or "")
    if CURATOR_AGENT not in agent_type:
        return
    allowed = False
    if event.get("tool_name") == "Write":
        import curation
        import repog_runtime

        campaign = repog_runtime.find_campaign(event.get("cwd"))
        tool_input = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
        path = tool_input.get("file_path")
        allowed = campaign is not None and isinstance(path, str) and curation.is_staging_path(campaign, path)
    if not allowed:
        _emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": CURATOR_DENIAL,
                }
            }
        )


HANDLERS: dict[str, Callable[[dict[str, Any]], None]] = {
    "prompt": prompt,
    "stop": stop,
    "session-start": session_start,
    "pretool": pretool,
}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    handler = HANDLERS.get(args[0]) if args else None
    if handler is None:
        return 0
    try:
        handler(_event())
    except Exception:
        pass  # hooks stay silent on failure; the turn goes on
    return 0


if __name__ == "__main__":
    sys.exit(main())
