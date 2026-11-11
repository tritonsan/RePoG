"""Entry point for the plugin's hook scripts.

Each subcommand reads one hook event (JSON on standard input), does its work,
and prints only what Claude Code expects. It never raises and never blocks:
a failing hook must not cost the Player a prompt or a reply.

    prompt         UserPromptSubmit: apply settled staged curation, then emit
                   the scene capsule as hidden `additionalContext`.
    stop           Stop (async): record the turn's reply order, run the
                   presentation lint over the reply, and remember its names.
    session-start  SessionStart: mark the capsule for a full refresh; after a
                   compaction or a resume, also print the accepted style
                   samples and the locked persistence order.
    pretool        PreToolUse: confine the repog-curator agent to its one
                   staging file.

JSON output is ASCII (`ensure_ascii`), so no console code page can corrupt a
name in the capsule. The SessionStart notice is plain UTF-8 text, printed
after the shell script's reminder line.

The Stop hook reads only the current session's last turn, locally, and
stores positions and flags (`order_last.json`), never the reply's text.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable


# Claude Code caps injected context at 10,000 characters; stay under it.
MAX_CONTEXT = 9_500
# SessionStart sources whose context lost the play so far: the style samples
# and the locked order are printed again for them.
RESUME_SOURCES = frozenset({"compact", "resume"})
# Style samples beside the full capsule after a compaction: both together stay
# well under the 10,000 characters a hook may add to the context.
COMPACT_SAMPLE_CHARS = 800
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


def _print_text(text: str) -> None:
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    sys.stdout.flush()


def _utc_now() -> str:
    import datetime as dt

    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _ready_campaign(event: dict[str, Any]) -> tuple[Path | None, dict[str, str]]:
    import repog_runtime

    campaign = repog_runtime.find_campaign(event.get("cwd"))
    if campaign is None or not repog_runtime.is_ready_rpg(campaign):
        return None, {}
    return campaign, repog_runtime.runtime_settings(campaign)


def _record_curation(campaign: Path, result: dict[str, Any]) -> None:
    """Keep the outcome of a curation run where the next capsule can show it.

    Without this, a proposal rejected as stale would vanish silently and the
    GM would never learn the note still needs folding.
    """

    if not any(result.get(key) for key in ("applied", "rejected", "deferred")):
        return
    import curation
    import repog_runtime

    repog_runtime.write_json_atomic(
        curation.curation_dir(campaign) / curation.RESULT_FILE,
        {
            "at": _utc_now(),
            "applied": result.get("applied", []),
            "rejected": result.get("rejected", []),
            "deferred": result.get("deferred", []),
        },
    )


def prompt(event: dict[str, Any]) -> None:
    campaign, settings = _ready_campaign(event)
    if campaign is None:
        return
    if settings.get("boundary_curator") == "background":
        try:
            import curation
            import rpg_state

            if curation.list_staged(campaign):
                _record_curation(campaign, rpg_state.commit_curation(campaign))
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


def _last_turn(event: dict[str, Any]) -> dict[str, Any] | None:
    """The transcript's last turn, or None when the event names no readable transcript."""

    import repog_runtime

    transcript = event.get("transcript_path")
    if not isinstance(transcript, str) or not transcript:
        return None
    try:
        return repog_runtime.last_turn(transcript)
    except Exception:
        return None


def _reply_text(event: dict[str, Any], turn: dict[str, Any] | None) -> str:
    """Everything the Player saw in the reply that just ended."""

    texts = list(turn["assistant_texts"]) if turn else []
    last = event.get("last_assistant_message")
    # The transcript may not hold the final message yet when Stop fires.
    if isinstance(last, str) and last.strip() and (not texts or texts[-1].strip() != last.strip()):
        texts.append(last)
    return "\n".join(texts)


def _recorded(path: Path, prompt_uuid: Any, session_id: str) -> bool:
    """True when `order_last.json` already holds this session's record of this Player turn."""

    import repog_runtime

    record = repog_runtime.read_json(path, None)
    return (
        isinstance(prompt_uuid, str)
        and bool(prompt_uuid)
        and isinstance(record, dict)
        and record.get("prompt_uuid") == prompt_uuid
        and record.get("session_id") == session_id
    )


def _record_order(campaign: Path, event: dict[str, Any], settings: dict[str, str], turn: dict[str, Any] | None) -> None:
    """Write `order_last.json`: how the turn ordered its commit and how much of it was sent.

    The next capsule shows a short `[order]` reminder when a turn saved a
    result but sent almost nothing, or ended without visible text: the Player
    has not seen that scene. Stores flags and a word count only, once per
    Player turn: a Stop also ends a turn the Player did not start (a
    background task's notice, a slash command), whose transcript turn is the
    Player's turn already recorded, now followed by blocks the Player's turn
    never had.
    """

    if turn is None:
        return
    import repog_runtime

    path = campaign / repog_runtime.RUNTIME_DIR / repog_runtime.ORDER_FILE
    session_id = event.get("session_id") if isinstance(event.get("session_id"), str) else ""
    if _recorded(path, turn.get("prompt_uuid"), session_id):
        return
    order = repog_runtime.turn_order(turn, event.get("last_assistant_message"))
    repog_runtime.write_json_atomic(
        path,
        {
            "at": _utc_now(),
            "prompt_uuid": turn.get("prompt_uuid", ""),
            "session_id": session_id,
            "expected": settings.get("persistence_order") or repog_runtime.RUNTIME_DEFAULTS["persistence_order"],
            "observed": order["observed"],
            "final_text": order["final_text"],
            "reply_words": order["reply_words"],
        },
    )


def stop(event: dict[str, Any]) -> None:
    campaign, settings = _ready_campaign(event)
    if campaign is None:
        return
    turn = _last_turn(event)
    try:
        _record_order(campaign, event, settings, turn)
    except Exception:
        pass  # the record is advisory; the lint and the names still run
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

        text = _reply_text(event, turn)
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
    try:
        scene_capsule.reset(campaign, session_id if isinstance(session_id, str) and session_id else None)
    except OSError:
        pass  # an unwritable runtime folder only means the next capsule may be a delta
    if event.get("source") in RESUME_SOURCES and repog_runtime.is_ready_rpg(campaign):
        # A compaction summary or a resumed session keeps no accepted style
        # sample, and may carry an order rule of its own.
        settings = repog_runtime.runtime_settings(campaign)
        _print_text(scene_capsule.resume_notice(campaign, settings, COMPACT_SAMPLE_CHARS))
        # A compaction lands when the Player's prompt arrives, after that
        # prompt's capsule was built as a delta of sections the summary has
        # now dropped. The full capsule goes out here, so the first reply
        # after a compaction has the cast, directives, language card, and
        # call shapes; it is recorded, so the next prompt gets a delta.
        if settings.get("scene_capsule") == "on":
            try:
                capsule = scene_capsule.build_capsule(
                    campaign,
                    "",
                    session_id=session_id if isinstance(session_id, str) and session_id else "default",
                    settings=settings,
                )
            except Exception:  # the capsule is advisory: the next prompt brings one anyway
                capsule = ""
            if capsule:
                _print_text(capsule)


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
