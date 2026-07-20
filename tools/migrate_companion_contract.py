"""Migrate a RePoG AI Companion campaign to the V2 runtime contract.

Dry-run is read-only. Apply requires an existing campaign snapshot, writes
atomically, and rolls every touched file back if any write fails. The migration
preserves established fiction; uncertain behavioral or disclosure choices are
reported as ``needs_review`` instead of being invented.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


VIEW_FILES = (
    "index.html",
    "app.js",
    "style.css",
    "assets/README.md",
)


def _clean(value: Any) -> str:
    return str(value or "").strip().strip("'\"`")


def _top(text: str, key: str, default: str = "") -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    return _clean(match.group(1)) if match else default


def _nested(text: str, section: str) -> dict[str, str]:
    lines = text.splitlines()
    start = next((i + 1 for i, line in enumerate(lines) if re.fullmatch(rf"{re.escape(section)}:\s*", line)), None)
    if start is None:
        return {}
    result: dict[str, str] = {}
    for line in lines[start:]:
        if line and not line.startswith((" ", "\t")):
            break
        match = re.match(r"^\s{2}([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if match:
            result[match.group(1)] = _clean(match.group(2))
    return result


def _set_top(text: str, key: str, value: str) -> str:
    pattern = rf"(?m)^{re.escape(key)}:\s*.*$"
    line = f"{key}: {value}"
    if re.search(pattern, text):
        return re.sub(pattern, line, text, count=1)
    return line + "\n" + text


def _section_bounds(lines: list[str], section: str) -> tuple[int, int]:
    header = next((i for i, line in enumerate(lines) if re.fullmatch(rf"{re.escape(section)}:\s*", line)), None)
    if header is None:
        lines.extend(([""] if lines and lines[-1] else []) + [f"{section}:"])
        return len(lines) - 1, len(lines)
    end = len(lines)
    for index in range(header + 1, len(lines)):
        line = lines[index]
        if line and not line.startswith((" ", "\t", "#")):
            end = index
            break
    return header, end


def _set_nested(text: str, section: str, key: str, value: str) -> str:
    trailing = text.endswith("\n")
    lines = text.splitlines()
    header, end = _section_bounds(lines, section)
    pattern = re.compile(rf"^\s{{2}}{re.escape(key)}:\s*.*$")
    for index in range(header + 1, end):
        if pattern.match(lines[index]):
            lines[index] = f"  {key}: {value}"
            return "\n".join(lines) + ("\n" if trailing else "")
    lines.insert(end, f"  {key}: {value}")
    return "\n".join(lines) + ("\n" if trailing else "")


def _remove_nested(text: str, section: str, key: str) -> str:
    trailing = text.endswith("\n")
    lines = text.splitlines()
    header, end = _section_bounds(lines, section)
    pattern = re.compile(rf"^\s{{2}}{re.escape(key)}:\s*.*$")
    lines = [line for index, line in enumerate(lines) if not (header < index < end and pattern.match(line))]
    return "\n".join(lines) + ("\n" if trailing else "")


def _field(text: str, name: str) -> str:
    match = re.search(rf"(?im)^(?:-[ \t]+)?{re.escape(name)}:[ \t]*(.*)$", text)
    return _clean(match.group(1)) if match else ""


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def _iso_anchor(state: dict[str, Any]) -> str:
    presence = state.get("current_presence") if isinstance(state.get("current_presence"), dict) else {}
    return _clean(
        state.get("last_user_contact_at")
        or state.get("last_contact_at")
        or state.get("last_observation_at")
        or presence.get("as_of")
    )


def _migrate_profile(text: str) -> tuple[str, list[str], list[str]]:
    old_schema = _top(text, "schema_version", "1")
    old_memory = _nested(text, "memory").get("user_policy", "")
    old_boundary = _nested(text, "relationship").get("boundary_ref", "")
    result = _set_top(text, "schema_version", "2")
    values = (
        ("identity", "direct_identity_framing", "explicit_ai_fictional_character"),
        ("relationship", "model", "evidence_context"),
        ("relationship", "boundary_ref", old_boundary or "companion_boundaries_v1"),
        ("relationship", "deception_policy", "no_direct_lies"),
        (
            "memory",
            "user_policy",
            "contextual_low_risk" if old_memory in {"", "consent_contextual"} else old_memory,
        ),
        ("memory", "sensitive_policy", "explicit_consent_only"),
        ("memory", "raw_transcript_policy", "never"),
        ("memory", "forget_policy", "remove_active_keep_content_free_tombstone"),
        ("visuals", "companion_view", "off"),
        ("visuals", "dashboard", "off"),
        ("performance", "exchange_persistence", "single_begin_exchange"),
        ("performance", "semantic_persistence", "meaningful_change_only"),
        ("performance", "full_distill", "trigger_or_session_stop"),
        ("performance", "validation", "structural_inside_durable_commit"),
        ("performance", "companion_view_refresh", "visible_change_only"),
    )
    for section, key, value in values:
        result = _set_nested(result, section, key, value)
    result = _remove_nested(result, "performance", "contact_write")
    actions = [] if result == text else [f"upgrade companion_profile schema {old_schema} -> 2 and materialize V2 policies"]
    review: list[str] = []
    if old_schema != "2" and _clean(_nested(text, "relationship").get("allowed_scope", "")) == "":
        review.append("companion_profile.yaml: relationship scope remains undecided")
    return result, actions, review


def _v2_state(old: dict[str, Any], *, boundary_ref: str, public_revision: int) -> tuple[dict[str, Any], list[str]]:
    if old.get("schema_version") == 2:
        return old, []
    review: list[str] = []
    presence_old = old.get("current_presence") if isinstance(old.get("current_presence"), dict) else {}
    presence = {
        "as_of": presence_old.get("as_of"),
        "place_ref": str(presence_old.get("place_ref", "")),
        "activity": str(presence_old.get("activity", "")),
        "with_refs": list(presence_old.get("with_refs", [])) if isinstance(presence_old.get("with_refs"), list) else [],
        "availability": str(presence_old.get("availability", "unknown")),
        "expected_until": presence_old.get("expected_until"),
        "source": str(presence_old.get("source", "migration:v1")),
    }
    legacy = old.get("primary_relationship") if isinstance(old.get("primary_relationship"), dict) else {}
    anchor = _iso_anchor(old)
    evidence: list[dict[str, Any]] = []
    for index, source_ref in enumerate(legacy.get("last_evidence_refs", []) if isinstance(legacy.get("last_evidence_refs"), list) else []):
        if not _clean(source_ref) or not anchor:
            continue
        evidence.append(
            {
                "evidence_id": f"migration_evidence_{index + 1}",
                "dimension": "other",
                "direction": "ambiguous",
                "interpretation": "Migrated qualitative relationship evidence; review its current meaning.",
                "source_ref": str(source_ref),
                "observed_at": anchor,
            }
        )
    old_tension = _clean(legacy.get("tension"))
    tensions: list[dict[str, str]] = []
    if old_tension and old_tension not in {"none", "unestablished", "clear"}:
        tensions.append(
            {
                "tension_id": "migration_legacy_tension",
                "summary": old_tension,
                "source_ref": "migration:v1_primary_relationship",
                "status": "active",
            }
        )
    old_trust = _clean(legacy.get("trust_band"))
    old_closeness = _clean(legacy.get("closeness_band"))
    if old_trust not in {"", "unestablished"} or old_closeness not in {"", "unestablished"}:
        review.append(
            "companion_state.json: legacy trust/closeness labels were not converted into an ordered ladder; review contextual evidence"
        )
    if legacy and not evidence:
        review.append("companion_state.json: relational context needs concrete setup or interaction evidence")
    window = old.get("current_window") if isinstance(old.get("current_window"), dict) else {}
    gap = old.get("last_gap") if isinstance(old.get("last_gap"), dict) else {}
    operations = old.get("recent_operation_ids") if isinstance(old.get("recent_operation_ids"), list) else []
    result = {
        "schema_version": 2,
        "state_revision": int(old.get("state_revision", 0) or 0),
        "continuity_revision": int(old.get("continuity_revision", 0) or 0),
        "public_surface_revision": public_revision,
        "interaction_sequence": int(old.get("interaction_sequence", 0) or 0),
        "semantic_operation_sequence": 0,
        "last_semantic_operation_id": "",
        "semantic_operation_ledger": [],
        "configured_timezone": str(old.get("configured_timezone", "")),
        "configured_utc_offset": str(old.get("configured_utc_offset", "")),
        "last_observation_at": old.get("last_observation_at"),
        "last_user_contact_at": old.get("last_user_contact_at") or old.get("last_contact_at"),
        "current_window": {
            "window_id": str(window.get("window_id", "")),
            "started_at": window.get("started_at"),
            "last_exchange_at": window.get("last_exchange_at"),
        },
        "current_presence": presence,
        "current_condition": {
            "as_of": presence.get("as_of"),
            "energy": "unknown",
            "social_bandwidth": "unknown",
            "emotional_weather": "",
            "active_preoccupation": "",
            "cause_ref": "",
            "reevaluate_after": None,
        },
        "attention_queue": [],
        "pending_transition": old.get("pending_transition"),
        "last_gap": {
            "gap_id": str(gap.get("gap_id", "")),
            "elapsed_minutes": int(gap.get("elapsed_minutes", 0) or 0),
            "band": str(gap.get("band", "same_window")),
            "event_ceiling": int(gap.get("event_ceiling", 0) or 0),
            "reconciled_revision": min(
                int(gap.get("reconciled_revision", 0) or 0),
                int(old.get("continuity_revision", 0) or 0),
            ),
        },
        "relational_context": {
            "companion_posture": _clean(legacy.get("companion_stance")) or "unestablished",
            "reciprocity_pattern": _clean(legacy.get("reciprocity")) or "unestablished",
            "boundary_refs": [boundary_ref] if boundary_ref else [],
            "active_tensions": tensions,
            "recent_evidence": evidence[:8],
            "last_change_evidence_id": evidence[-1]["evidence_id"] if evidence else "",
        },
        "recent_operation_ids": [str(value) for value in operations[-256:] if _clean(value)],
    }
    return result, review


def _boundary_section(profile: str, state: dict[str, Any]) -> str:
    relationship = _nested(profile, "relationship")
    memory = _nested(profile, "memory")
    boundary_ref = relationship.get("boundary_ref") or "companion_boundaries_v1"
    scope = relationship.get("allowed_scope") or "needs_review"
    confirmed = _iso_anchor(state) or "needs_review"
    return f"""## Companion Relationship Boundaries

This is the versioned, user-approved relationship contract for Companion mode.
Narrowing takes effect immediately; broadening requires clear confirmation.

- Boundary set id: {boundary_ref}
- Contract version: 1
- Revision: 0
- Effective relationship scope: {scope}
- Last confirmed at: {confirmed}
- Supersedes:
- User-requested narrowing:
- Interaction limits: needs_review
- Romance and intimacy policy: needs_review
- Disagreement and refusal policy: companion may disagree, refuse, and leave without dependency pressure
- Anti-dependency guard: no guilt, exclusivity demands, isolation pressure, or threats used to retain engagement
- Identity transparency: direct real, human, or AI questions receive a truthful fictional-AI answer
- Memory consent: {memory.get('user_policy') or 'contextual_low_risk'}; sensitive facts require explicit consent
- Direct deception: {relationship.get('deception_policy') or 'no_direct_lies'}; never for identity, real safety, consent/boundaries, or memory semantics
"""


def _migrate_boundaries(text: str, profile: str, state: dict[str, Any]) -> tuple[str, list[str]]:
    if re.search(r"(?im)^##\s+Companion Relationship Boundaries\s*$", text):
        return text, []
    return text.rstrip() + "\n\n" + _boundary_section(profile, state) + "\n", [
        "boundaries.md: confirm migrated relationship limits and any allowed intimacy before continuing"
    ]


def _kernel_value(note: str, *names: str) -> str:
    for name in names:
        value = _field(note, name)
        if value:
            return value
    return "needs_review"


def _migrate_primary_note(text: str, boundary_ref: str) -> tuple[str, list[str]]:
    if re.search(r"(?im)^##\s+Hot Character Kernel\s*$", text):
        return text, []
    kernel = f"""## Hot Character Kernel

- Name and pronouns: {_kernel_value(text, 'Name')} / {_kernel_value(text, 'Pronouns')}
- Core values and decision principle: {_kernel_value(text, 'Core values')}
- Moral boundaries: {_kernel_value(text, 'Moral boundaries')}
- Expertise anchors: {_kernel_value(text, 'Occupation or main pursuit', 'Work or education')}
- Blind spots and uncertainty style: {_kernel_value(text, 'False belief about themself')}
- Contradiction one: {_kernel_value(text, 'Contradiction one')}
- Contradiction two: {_kernel_value(text, 'Contradiction two')}
- Independent goal: {_kernel_value(text, 'Long-term goal', 'Short-term goal')}
- Non-user obligation: {_kernel_value(text, 'Non-user obligation')}
- User-independent social anchor: {_kernel_value(text, 'Closest T3 connection', 'Recurring T2 connections', 'Chosen isolation, if no active connection')}
- Neutral voice: {_kernel_value(text, 'Speech rhythm', 'Ordinary speech sample')}
- Warm voice: needs_review
- Stressed voice: needs_review
- Hurt or defensive voice: needs_review
- Humor and disagreement: {_kernel_value(text, 'Humor', 'Disagreement style')}
- Help-seeking and initiative: {_kernel_value(text, 'How they ask for help', 'Next move if ignored')}
- Disclosure posture and fact refs: {_kernel_value(text, 'Disclosure pace', 'Knowledge-boundary fact ids')}
- Boundary ref: {boundary_ref}
"""
    first_section = re.search(r"(?m)^##\s+", text)
    if first_section:
        result = text[: first_section.start()].rstrip() + "\n\n" + kernel + "\n" + text[first_section.start() :]
    else:
        result = text.rstrip() + "\n\n" + kernel + "\n"
    return result, ["primary companion note: review needs_review fields in the migrated Hot Character Kernel"]


def _find_primary_note(campaign: Path, companion_id: str) -> Path | None:
    target = _slug(companion_id)
    for path in sorted((campaign / "characters").glob("*.md")) if (campaign / "characters").is_dir() else []:
        if path.name.startswith("_"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if _slug(path.stem) == target or _slug(_field(text, "Companion id")) == target:
            return path
    return None


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _has_snapshot(campaign: Path) -> bool:
    root = campaign / "snapshots"
    return root.is_dir() and any(root.glob("*/snapshot_manifest.json"))


def _apply_all(planned: dict[Path, str]) -> None:
    originals = {path: path.read_bytes() if path.is_file() else None for path in planned}
    written: list[Path] = []
    try:
        for path, text in planned.items():
            _atomic_text(path, text)
            written.append(path)
    except Exception:
        for path in reversed(written):
            original = originals[path]
            if original is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_text(path, original.decode("utf-8"))
        raise


def migrate(campaign_path: Path, *, apply: bool = False) -> dict[str, Any]:
    campaign = campaign_path.resolve()
    if not campaign.is_dir():
        return {"ok": False, "error": "campaign_path_not_found", "campaign_path": str(campaign)}
    if apply and not _has_snapshot(campaign):
        return {
            "ok": False,
            "error": "snapshot_required",
            "message": "Create a campaign snapshot before applying this migration.",
            "campaign_path": str(campaign),
        }
    planned: dict[Path, str] = {}
    actions: list[dict[str, str]] = []
    review: list[str] = []
    try:
        profile_path = campaign / "companion_profile.yaml"
        state_path = campaign / "companion_state.json"
        profile_old = profile_path.read_text(encoding="utf-8")
        state_old = json.loads(state_path.read_text(encoding="utf-8"))
        if not isinstance(state_old, dict):
            raise ValueError("companion_state.json must contain an object")
        profile_new, profile_actions, profile_review = _migrate_profile(profile_old)
        boundary_ref = _nested(profile_new, "relationship").get("boundary_ref", "companion_boundaries_v1")

        view_state_path = campaign / "companion_view" / "companion_view_state.json"
        public_revision = 0
        if view_state_path.is_file():
            existing_view = json.loads(view_state_path.read_text(encoding="utf-8"))
            if isinstance(existing_view, dict) and isinstance(existing_view.get("public_surface_revision"), int):
                public_revision = max(0, existing_view["public_surface_revision"])
        state_new, state_review = _v2_state(state_old, boundary_ref=boundary_ref, public_revision=public_revision)
        if profile_new != profile_old:
            planned[profile_path] = profile_new
        if state_new != state_old:
            planned[state_path] = json.dumps(state_new, indent=2, ensure_ascii=False) + "\n"
            actions.append({"path": str(state_path), "action": "upgrade companion_state schema 1 -> 2"})
        actions.extend({"path": str(profile_path), "action": value} for value in profile_actions)
        review.extend(profile_review + state_review)

        boundaries_path = campaign / "boundaries.md"
        boundaries_old = boundaries_path.read_text(encoding="utf-8")
        boundaries_new, boundary_review = _migrate_boundaries(boundaries_old, profile_new, state_new)
        if boundaries_new != boundaries_old:
            planned[boundaries_path] = boundaries_new
            actions.append({"path": str(boundaries_path), "action": "add versioned Companion boundary contract"})
        review.extend(boundary_review)

        user_path = campaign / "user_context.md"
        if user_path.is_file():
            user_old = user_path.read_text(encoding="utf-8")
            user_new = re.sub(
                r"(?im)^-\s+Policy:\s*consent_contextual\s*$",
                "- Policy: contextual_low_risk",
                user_old,
                count=1,
            )
            if user_new != user_old:
                planned[user_path] = user_new
                actions.append({"path": str(user_path), "action": "map consent_contextual memory to contextual_low_risk"})

        companion_id = _top(profile_new, "primary_companion_id")
        note_path = _find_primary_note(campaign, companion_id) if companion_id else None
        if note_path:
            note_old = note_path.read_text(encoding="utf-8")
            note_new, note_review = _migrate_primary_note(note_old, boundary_ref)
            if note_new != note_old:
                planned[note_path] = note_new
                actions.append({"path": str(note_path), "action": "add compact Hot Character Kernel"})
            review.extend(note_review)
        elif companion_id:
            review.append(f"characters/: locate the primary companion note for {companion_id}")

        template_view = Path(__file__).resolve().parent.parent / "campaign" / "companion_view"
        for relative in VIEW_FILES:
            source = template_view / relative
            target = campaign / "companion_view" / relative
            if not target.is_file() and source.is_file():
                planned[target] = source.read_text(encoding="utf-8")
                actions.append({"path": str(target), "action": "add lightweight Companion View runtime"})
        if not view_state_path.is_file():
            view_state = {
                "schema_version": 1,
                "enabled": False,
                "public_surface_revision": state_new["public_surface_revision"],
                "identity": {"name": "", "pronouns": "", "tagline": ""},
                "portrait": None,
                "local_clock": None,
                "last_shared_status": None,
                "shared_cards": [],
            }
            planned[view_state_path] = json.dumps(view_state, indent=2, ensure_ascii=False) + "\n"
            actions.append({"path": str(view_state_path), "action": "add disabled player-safe Companion View projection"})

        knowledge_path = campaign / "knowledge_boundaries.md"
        if _top(profile_new, "profile_status") == "locked" and knowledge_path.is_file():
            knowledge = knowledge_path.read_text(encoding="utf-8")
            section = re.search(r"(?im)^##\s+Companion Disclosure Ledger\s*$", knowledge)
            if not section or not re.search(r"(?im)^-\s+Fact id:\s*[a-z0-9]", knowledge[section.end() :] if section else ""):
                review.append("knowledge_boundaries.md: convert established private topics into explicit V2 disclosure-ledger entries")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "error": "migration_read_failed",
            "message": str(exc),
            "campaign_path": str(campaign),
        }

    if apply:
        try:
            _apply_all(planned)
        except (OSError, UnicodeError) as exc:
            return {
                "ok": False,
                "error": "migration_write_failed",
                "message": str(exc),
                "campaign_path": str(campaign),
            }
    return {
        "ok": True,
        "mode": "apply" if apply else "dry-run",
        "campaign_path": str(campaign),
        "changed": bool(planned),
        "changed_files": [str(path) for path in planned],
        "actions": actions,
        "needs_review": sorted(set(review)),
    }


def _print_human(result: dict[str, Any]) -> None:
    if not result.get("ok"):
        print(f"Migration blocked: {result.get('error')}: {result.get('message', '')}")
        return
    state = "changes planned" if result["changed"] else "already current"
    print(f"Companion contract migration ({result['mode']}): {state}")
    for item in result["actions"]:
        print(f"- {item['action']} ({item['path']})")
    for item in result["needs_review"]:
        print(f"- NEEDS REVIEW: {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_path", help="Path to a RePoG campaign folder.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Report changes without writing (default).")
    mode.add_argument("--apply", action="store_true", help="Apply only after a campaign snapshot exists.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)
    result = migrate(Path(args.campaign_path), apply=args.apply)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        _print_human(result)
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
