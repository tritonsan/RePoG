"""Validate the structural AI Companion contract without judging prose."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROFILE_STATUSES = {"pending", "locked", "inactive"}
PROFILE_SCHEMAS = {1, 2}
SETTING_MODES = {"real_city_fictional_private", "fictional_world"}
RESPONSE_LENGTHS = {"brief", "dynamic", "expansive"}
INITIATIVE_VALUES = {"reserved", "balanced", "proactive"}
HUMOR_VALUES = {"minimal", "situational", "frequent"}
LIFE_DENSITIES = {"quiet", "grounded", "eventful"}
RELATIONSHIP_SCOPES = {"friendship", "friendship_and_romance", "broad_adult_relationships"}
PORTRAIT_POLICIES = {"off", "optional_manual", "setup_once"}
COMPANION_VIEW_POLICIES = {"off", "light"}
MEMORY_KINDS = {"preference", "durable_event", "promise", "upcoming_date", "callback"}
MEMORY_SOURCES = {"explicit_user_statement", "explicit_user_request_to_remember"}
MEMORY_CONSENTS = {"contextual", "explicit"}
MEMORY_POLICIES = {"off", "ask_before_save", "contextual_low_risk"}
DECEPTION_POLICIES = {"no_direct_lies", "character_consistent_opt_in"}
SEMANTIC_PARALLELISM_POLICIES = {"off", "selective_structural", "aggressive_structural"}
DISCLOSURE_STAGES = {"private", "hinted", "partial", "shared", "corrected"}
DISCLOSURE_POSTURES = {"open", "contextual", "guarded", "refuses_now"}
ACCOUNT_TRUTHFULNESS = {"not_disclosed", "truthful", "incomplete", "false", "corrected"}
PROTECTED_DECEPTION_CATEGORIES = {
    "ai_identity",
    "real_world_safety",
    "consent_boundary",
    "user_memory",
}

HOT_KERNEL_FIELDS = (
    "Name and pronouns",
    "Core values and decision principle",
    "Moral boundaries",
    "Expertise anchors",
    "Blind spots and uncertainty style",
    "Contradiction one",
    "Contradiction two",
    "Independent goal",
    "Non-user obligation",
    "User-independent social anchor",
    "Neutral voice",
    "Warm voice",
    "Stressed voice",
    "Hurt or defensive voice",
    "Humor and disagreement",
    "Help-seeking and initiative",
    "Disclosure posture and fact refs",
    "Boundary ref",
)

PERSONA_FIELDS = (
    "Name",
    "Age",
    "Pronouns",
    "Home base",
    "Occupation or main pursuit",
    "Education and cultural background",
    "Family structure",
    "Economic conditions",
    "First-glance read",
    "Build, posture, and movement",
    "Clothing and aesthetic preferences",
    "Core values",
    "Moral boundaries",
    "Humor",
    "Social courage",
    "Curiosities",
    "Conflict approach",
    "Support style",
    "How trust is built",
    "How closeness is shown",
    "How they ask for help",
    "False belief about themself",
    "Contradiction one",
    "Contradiction two",
    "Speech rhythm",
    "Vocabulary and cultural markers",
    "Message length tendency",
    "Silence, delay, and reply habits",
    "Emotional directness",
    "Ordinary speech sample",
    "Birthplace and upbringing",
    "Formative household dynamics",
    "Education and work history",
    "Important past relationships",
    "Turning points",
    "Earned successes",
    "Home and neighborhood",
    "Work or education",
    "Baseline weekly routine",
    "Responsibilities",
    "Financial or social pressures",
    "Hobbies and personal projects",
    "Favorite public places",
    "Current everyday task",
    "Short-term goal",
    "Long-term goal",
    "Non-user obligation",
    "Active life thread",
    "Next move if ignored",
    "Evaluation trigger",
    "Visible consequence channel",
    "Social obligation that can conflict with availability",
    "Starting stance toward the user",
    "Disagreement style",
    "Boundary-setting style",
    "Repair style",
    "Affection or warmth style",
    "Rivalry or hostility style",
    "What earns trust",
    "What damages trust",
    "Disclosure logic",
    "Disclosure pace",
)

NON_SALIENT_PERSONA_FIELDS = (
    "Jealousy or competition behavior",
    "What they hide or feel shame about",
    "Significant losses",
    "Unresolved past or trauma",
)


def _finding(severity: str, rule: str, message: str, path: Path) -> dict[str, str]:
    return {"severity": severity, "rule": rule, "message": message, "path": str(path)}


def _read(path: Path, findings: list[dict[str, str]]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        findings.append(_finding("error", "companion_read_failed", str(exc), path))
        return ""


def _clean(value: Any) -> str:
    return str(value).strip().strip("'\"`")


def _top_values(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith(" ") or not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match:
            result[match.group(1)] = match.group(2).strip()
    return result


def _block(text: str, key: str) -> str:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if re.match(rf"^{re.escape(key)}:\s*$", line):
            start = index + 1
            break
    if start is None:
        return ""
    selected: list[str] = []
    for line in lines[start:]:
        if line and not line.startswith(" "):
            break
        selected.append(line)
    return "\n".join(selected)


def _nested_values(text: str, key: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in _block(text, key).splitlines():
        match = re.match(r"^\s{2}([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match:
            result[match.group(1)] = match.group(2).strip()
    return result


def _check_misplaced_parallelism_keys(
    text: str,
    path: Path,
    findings: list[dict[str, str]],
) -> None:
    """Keep the delegation contract under the single performance authority."""

    current_top = ""
    reserved = {"semantic_parallelism", "max_parallel_workers"}
    seen: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        top_match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):", line)
        if top_match:
            current_top = top_match.group(1)
        key_match = re.match(r"^(\s*)(semantic_parallelism|max_parallel_workers):", line)
        if key_match is None:
            continue
        indent, key = key_match.groups()
        if key in seen:
            findings.append(
                _finding(
                    "error",
                    "semantic_parallelism_duplicate",
                    f"{key} may appear only once (duplicate at line {line_number}).",
                    path,
                )
            )
        seen.add(key)
        if key in reserved and not (current_top == "performance" and indent == "  "):
            findings.append(
                _finding(
                    "error",
                    "semantic_parallelism_misplaced",
                    f"{key} must appear only as a direct child of performance (line {line_number}).",
                    path,
                )
            )


def _yaml_list(text: str, key: str) -> list[str]:
    inline = re.search(rf"(?m)^{re.escape(key)}:[ \t]*\[(.*?)\][ \t]*$", text)
    if inline:
        return [_clean(item) for item in inline.group(1).split(",") if _clean(item)]
    block = re.search(rf"(?m)^{re.escape(key)}:[ \t]*$", text)
    if not block:
        return []
    tail = text[block.end():]
    end = re.search(r"(?m)^\S", tail)
    body = tail[: end.start()] if end else tail
    return [_clean(match.group(1)) for match in re.finditer(r"(?m)^\s+-\s+(.+?)\s*$", body)]


def _bool(value: Any) -> bool | None:
    normalized = _clean(value).lower()
    if normalized in {"true", "yes"}:
        return True
    if normalized in {"false", "no"}:
        return False
    return None


def _int(value: Any, default: int = -1) -> int:
    try:
        return int(_clean(value))
    except ValueError:
        return default


def _field(text: str, name: str) -> str:
    match = re.search(rf"(?im)^(?:-[ \t]+)?{re.escape(name)}:[ \t]*(.*)$", text)
    return _clean(match.group(1)) if match else ""


def _meaningful(value: str) -> bool:
    normalized = _clean(value).lower()
    return bool(normalized) and normalized not in {
        "replace_me",
        "setup_pending",
        "none yet",
        "none",
        "n/a",
        "tbd",
        "todo",
    }


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _valid_id(value: str) -> bool:
    return re.fullmatch(r"[a-z0-9][a-z0-9_-]*", _clean(value)) is not None


def _timezone_aware(value: str) -> bool:
    if not _meaningful(value):
        return False
    try:
        parsed = datetime.fromisoformat(_clean(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _refs(value: str) -> list[str]:
    normalized = _clean(value).strip("[]")
    if not normalized:
        return []
    return [_clean(item) for item in re.split(r"\s*[,;]\s*", normalized) if _clean(item)]


def _approx_token_count(text: str) -> int:
    """Use a deterministic conservative token approximation without dependencies."""

    return len(re.findall(r"[\w'-]+|[^\w\s]", text, flags=re.UNICODE))


def _note_for_id(directory: Path, entity_id: str) -> Path | None:
    target = _slug(entity_id)
    if not target or not directory.is_dir():
        return None
    for path in directory.glob("*.md"):
        if path.name.startswith("_"):
            continue
        if _slug(path.stem) == target:
            return path
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        declared = _field(text, "Companion id") or _field(text, "Character id")
        if declared and _slug(declared) == target:
            return path
    return None


def _validate_profile(
    campaign: Path,
    *,
    experience_mode: str,
    setup_ready: bool,
    setup_revision: int,
    findings: list[dict[str, str]],
    preflight_ready: bool = False,
) -> dict[str, Any]:
    path = campaign / "companion_profile.yaml"
    if not path.is_file():
        findings.append(_finding("error", "companion_profile_missing", "Companion contract file is missing.", path))
        return {}
    text = _read(path, findings)
    _check_misplaced_parallelism_keys(text, path, findings)
    top = _top_values(text)
    schema = _int(top.get("schema_version"))
    status = _clean(top.get("profile_status", ""))
    source_revision = _int(top.get("source_setup_revision"))
    primary_id = _clean(top.get("primary_companion_id", ""))
    if schema not in PROFILE_SCHEMAS:
        findings.append(_finding("error", "companion_profile_schema_invalid", "companion_profile schema_version must be 1 or 2.", path))
    if status not in PROFILE_STATUSES:
        findings.append(_finding("error", "companion_profile_status_invalid", "profile_status must be pending, locked, or inactive.", path))
    if source_revision < 0:
        findings.append(_finding("error", "companion_profile_revision_invalid", "source_setup_revision must be non-negative.", path))
    if experience_mode == "companion" and setup_ready:
        if status != "locked":
            findings.append(_finding("error", "companion_profile_not_locked", "Ready Companion mode requires profile_status: locked.", path))
    if experience_mode == "rpg" and setup_ready and status != "inactive":
        findings.append(_finding("error", "companion_profile_not_inactive", "Ready RPG mode requires companion_profile profile_status: inactive.", path))
    if (setup_ready or preflight_ready) and source_revision != setup_revision:
        findings.append(_finding("error", "companion_profile_revision_stale", "Companion profile revision does not match setup revision.", path))

    required = experience_mode == "companion" and (setup_ready or preflight_ready)
    identity = _nested_values(text, "identity")
    setting = _nested_values(text, "setting")
    communication = _nested_values(text, "communication")
    life = _nested_values(text, "life")
    relationship = _nested_values(text, "relationship")
    memory = _nested_values(text, "memory")
    visuals = _nested_values(text, "visuals")
    performance = _nested_values(text, "performance")

    parallelism = _clean(performance.get("semantic_parallelism", ""))
    workers_raw = _clean(performance.get("max_parallel_workers", ""))
    acknowledgement_raw = _clean(performance.get("parallelism_notice_acknowledged", ""))
    acknowledgement = _bool(acknowledgement_raw)
    parallelism_configured = bool(parallelism or workers_raw)
    if parallelism_configured:
        if not parallelism or not workers_raw:
            missing = "performance.semantic_parallelism" if not parallelism else "performance.max_parallel_workers"
            findings.append(
                _finding(
                    "error",
                    "semantic_parallelism_incomplete",
                    f"Delegation configuration requires both fields; missing {missing}.",
                    path,
                )
            )
        if parallelism and parallelism not in SEMANTIC_PARALLELISM_POLICIES:
            findings.append(
                _finding(
                    "error",
                    "semantic_parallelism_invalid",
                    "performance.semantic_parallelism must be off, selective_structural, or aggressive_structural.",
                    path,
                )
            )
        if workers_raw and _int(workers_raw) not in {1, 2, 3}:
            findings.append(
                _finding(
                    "error",
                    "max_parallel_workers_invalid",
                    "performance.max_parallel_workers must be an integer from 1 through 3.",
                    path,
                )
            )
    if acknowledgement_raw and acknowledgement is None:
        findings.append(
            _finding(
                "error",
                "companion_parallelism_acknowledgement_invalid",
                "performance.parallelism_notice_acknowledged must be true or false.",
                path,
            )
        )
    elif required and parallelism_configured and acknowledgement is not True:
        findings.append(
            _finding(
                "error",
                "companion_parallelism_unacknowledged",
                "Ready Companion setup requires acknowledgement of the parallelism and model-usage notice.",
                path,
            )
        )

    def enum(section: str, values: dict[str, str], key: str, allowed: set[str], *, needed: bool = required) -> None:
        value = _clean(values.get(key, ""))
        if value and value not in allowed:
            findings.append(_finding("error", "companion_profile_enum_invalid", f"{section}.{key} is invalid: {value}", path))
        elif needed and not value:
            findings.append(_finding("error", "companion_profile_field_missing", f"{section}.{key} is required.", path))

    if _clean(identity.get("framing", "")) not in {"", "layered_transparency"}:
        findings.append(_finding("error", "companion_identity_framing_invalid", "identity.framing must be layered_transparency.", path))
    for key in ("role_exit_on_direct_question", "return_to_character_after_answer"):
        if _bool(identity.get(key, "")) is not True and required:
            findings.append(_finding("error", "companion_identity_gate_missing", f"identity.{key} must be true.", path))
    direct_answer = _clean(identity.get("direct_identity_answer", ""))
    if required and not direct_answer:
        findings.append(_finding("error", "companion_identity_answer_missing", "A direct AI identity answer is required.", path))

    enum("setting", setting, "mode", SETTING_MODES)
    if required:
        for key in ("timezone", "utc_offset"):
            if not _clean(setting.get(key, "")):
                findings.append(_finding("error", "companion_time_config_missing", f"setting.{key} is required.", path))
    if _clean(setting.get("mode", "")) == "real_city_fictional_private":
        for key in ("city_or_region", "country_or_world"):
            if required and not _clean(setting.get(key, "")):
                findings.append(_finding("error", "companion_real_city_missing", f"setting.{key} is required for real-city mode.", path))
        if _bool(setting.get("real_public_geography", "")) is not True:
            findings.append(_finding("error", "companion_real_geography_disabled", "Real-city mode requires real_public_geography: true.", path))
        if _clean(setting.get("private_people_and_places", "")) != "fictional":
            findings.append(_finding("error", "companion_private_world_invalid", "Private people and places must remain fictional.", path))

    enum("communication", communication, "response_length", RESPONSE_LENGTHS)
    enum("communication", communication, "initiative", INITIATIVE_VALUES)
    enum("communication", communication, "humor", HUMOR_VALUES)
    enum("life", life, "density", LIFE_DENSITIES)
    enum("relationship", relationship, "allowed_scope", RELATIONSHIP_SCOPES)
    if schema >= 2:
        enum("relationship", relationship, "deception_policy", DECEPTION_POLICIES)
        enum("memory", memory, "user_policy", MEMORY_POLICIES)
    enum("visuals", visuals, "portrait_policy", PORTRAIT_POLICIES, needed=False)
    if schema >= 2:
        enum("visuals", visuals, "companion_view", COMPANION_VIEW_POLICIES)
    if schema >= 2:
        enum("visuals", visuals, "companion_view", COMPANION_VIEW_POLICIES, needed=False)
    portrait_policy = _clean(visuals.get("portrait_policy", ""))
    accepted_portrait = _clean(visuals.get("accepted_portrait", "")).replace("\\", "/")
    if portrait_policy == "off" and accepted_portrait:
        findings.append(_finding("error", "companion_portrait_policy_conflict", "An off portrait policy cannot reference accepted art.", path))
    if accepted_portrait:
        portrait_path = campaign / accepted_portrait
        if not accepted_portrait.startswith("visuals/characters/") or "/_drafts/" in f"/{accepted_portrait}" or not portrait_path.is_file():
            findings.append(_finding("error", "companion_portrait_missing", "Accepted portrait must exist under visuals/characters and cannot be a draft.", path))
    if required and portrait_policy == "setup_once" and not accepted_portrait:
        findings.append(_finding("error", "companion_portrait_unresolved", "setup_once portrait policy requires an accepted portrait or a switch to off/optional_manual.", path))
    fixed = {
        "communication.channel": (_clean(communication.get("channel", "")), "async_text"),
        "life.offline_progression": (_clean(life.get("offline_progression", "")), "reconcile_on_next_message"),
        "life.autonomy": (_clean(life.get("autonomy", "")), "causal"),
        "relationship.model": (
            _clean(relationship.get("model", "")),
            "evidence_context" if schema >= 2 else "organic_qualitative",
        ),
        "memory.sensitive_policy": (_clean(memory.get("sensitive_policy", "")), "explicit_consent_only"),
        "memory.raw_transcript_policy": (_clean(memory.get("raw_transcript_policy", "")), "never"),
        "visuals.dashboard": (_clean(visuals.get("dashboard", "")), "off"),
    }
    if schema == 1:
        fixed["memory.user_policy"] = (_clean(memory.get("user_policy", "")), "consent_contextual")
    else:
        fixed.update(
            {
                "identity.direct_identity_framing": (
                    _clean(identity.get("direct_identity_framing", "")),
                    "explicit_ai_fictional_character",
                ),
                "memory.forget_policy": (
                    _clean(memory.get("forget_policy", "")),
                    "remove_active_keep_content_free_tombstone",
                ),
                "performance.exchange_persistence": (
                    _clean(performance.get("exchange_persistence", "")),
                    "single_begin_exchange",
                ),
                "performance.semantic_persistence": (
                    _clean(performance.get("semantic_persistence", "")),
                    "meaningful_change_only",
                ),
                "performance.full_distill": (
                    _clean(performance.get("full_distill", "")),
                    "trigger_or_session_stop",
                ),
                "performance.validation": (
                    _clean(performance.get("validation", "")),
                    "structural_inside_durable_commit",
                ),
                "performance.companion_view_refresh": (
                    _clean(performance.get("companion_view_refresh", "")),
                    "visible_change_only",
                ),
            }
        )
    for field_name, (actual, expected) in fixed.items():
        if actual and actual != expected:
            findings.append(_finding("error", "companion_contract_invalid", f"{field_name} must be {expected}.", path))
        elif required and not actual:
            findings.append(_finding("error", "companion_profile_field_missing", f"{field_name} is required.", path))
    if required:
        for key in ("starting_frame",):
            if not _meaningful(relationship.get(key, "")):
                findings.append(_finding("error", "companion_relationship_setup_missing", f"relationship.{key} is required.", path))
        for key in ("primary_companion_is_adult", "boundaries_confirmed", "anti_dependency_guard"):
            if _bool(relationship.get(key, "")) is not True:
                findings.append(_finding("error", "companion_relationship_gate_missing", f"relationship.{key} must be true.", path))
        scope = _clean(relationship.get("allowed_scope", ""))
        if scope in {"friendship_and_romance", "broad_adult_relationships"} and _bool(relationship.get("user_confirmed_adult_for_intimacy", "")) is not True:
            findings.append(_finding("error", "companion_intimacy_adult_gate_missing", "Adult user confirmation is required for romantic/intimate scope.", path))
        if not _meaningful(communication.get("language", "")):
            findings.append(_finding("error", "companion_language_missing", "communication.language is required.", path))
        performance_fields = (
            ("exchange_persistence", "semantic_persistence", "full_distill", "validation")
            if schema >= 2
            else ("contact_write", "semantic_persistence", "full_distill", "validation")
        )
        for key in performance_fields:
            if not _meaningful(performance.get(key, "")):
                findings.append(_finding("error", "companion_performance_missing", f"performance.{key} is required.", path))
        if not _meaningful(primary_id):
            findings.append(_finding("error", "primary_companion_missing", "primary_companion_id is required.", path))
        if schema >= 2 and not _meaningful(relationship.get("boundary_ref", "")):
            findings.append(_finding("error", "companion_boundary_ref_missing", "relationship.boundary_ref is required.", path))
        if schema >= 2 and _clean(performance.get("companion_view_refresh", "")) != "visible_change_only":
            findings.append(_finding("error", "companion_view_refresh_invalid", "performance.companion_view_refresh must be visible_change_only.", path))

    return {
        "status": status,
        "source_setup_revision": source_revision,
        "primary_companion_id": primary_id,
        "setting": setting,
        "relationship": relationship,
        "memory": memory,
        "visuals": visuals,
        "performance": performance,
        "schema_version": schema,
    }


def _validate_persona(
    campaign: Path,
    *,
    primary_id: str,
    ready: bool,
    scope: str,
    relationship: dict[str, str],
    findings: list[dict[str, str]],
) -> Path | None:
    if not _meaningful(primary_id):
        return None
    note = _note_for_id(campaign / "characters", primary_id)
    if note is None:
        findings.append(_finding("error", "primary_companion_note_missing", f"No character note matches {primary_id!r}.", campaign / "characters"))
        return None
    text = _read(note, findings)
    if not ready:
        return note
    if _clean(_field(text, "Tier")).lower() != "t3":
        findings.append(_finding("error", "primary_companion_tier_invalid", "Primary companion must be T3.", note))
    age_match = re.search(r"\d+", _field(text, "Age"))
    if not age_match or int(age_match.group()) < 18:
        findings.append(_finding("error", "primary_companion_not_adult", "Ready primary companions must be explicitly adult.", note))

    kernel = _markdown_section(text, "Hot Character Kernel")
    if not kernel:
        findings.append(_finding("error", "companion_hot_kernel_missing", "Ready Companion mode requires a Hot Character Kernel.", note))
    else:
        for field in HOT_KERNEL_FIELDS:
            if not _meaningful(_field(kernel, field)):
                findings.append(_finding("error", "companion_hot_kernel_field_missing", f"Hot Character Kernel is incomplete: {field}", note))
        if _approx_token_count(kernel) > 700:
            findings.append(_finding("error", "companion_hot_kernel_too_large", "Hot Character Kernel must remain at or below approximately 700 tokens.", note))
        expected_boundary = _clean(relationship.get("boundary_ref", ""))
        actual_boundary = _clean(_field(kernel, "Boundary ref"))
        if expected_boundary and _slug(actual_boundary) != _slug(expected_boundary):
            findings.append(_finding("error", "companion_hot_boundary_ref_mismatch", "Hot Character Kernel boundary ref does not match companion_profile.", note))

    if scope == "hot":
        return note

    for field in PERSONA_FIELDS:
        if not _meaningful(_field(text, field)):
            findings.append(_finding("error", "companion_persona_field_missing", f"Primary companion field is incomplete: {field}", note))
    # These humanizing traits are optional. If present, they may explicitly say
    # that the tendency is not salient rather than inventing mandatory trauma.
    for field in NON_SALIENT_PERSONA_FIELDS:
        value = _field(text, field)
        if value and not _meaningful(value) and _clean(value).lower() not in {"not salient", "no strong pattern", "not established"}:
            findings.append(_finding("warning", "companion_optional_trait_placeholder", f"Optional persona field is still a placeholder: {field}", note))
    social_values = (
        _field(text, "Closest T3 connection"),
        _field(text, "Recurring T2 connections"),
        _field(text, "Named minor T1 connections"),
    )
    isolation = _field(text, "Chosen isolation, if no active connection")
    if not any(_meaningful(value) for value in social_values) and not _meaningful(isolation):
        findings.append(_finding("error", "companion_social_ecology_missing", "Record a social connection or documented chosen isolation.", note))
    scope = _clean(relationship.get("allowed_scope", ""))
    if scope in {"friendship_and_romance", "broad_adult_relationships"} and _clean(_field(text, "Age")) == "":
        findings.append(_finding("error", "companion_intimacy_age_missing", "Romantic scope requires an explicit adult age.", note))
    return note


def _load_state_validator() -> Any:
    path = Path(__file__).with_name("companion_state.py")
    spec = importlib.util.spec_from_file_location("repog_companion_state_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("companion_state.py could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_state(
    campaign: Path,
    *,
    ready: bool,
    primary_id: str,
    profile_setting: dict[str, str],
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    path = campaign / "companion_state.json"
    if not path.is_file():
        findings.append(_finding("error", "companion_state_missing", "Companion state file is missing.", path))
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(_finding("error", "companion_state_invalid", str(exc), path))
        return {}
    if not isinstance(data, dict):
        findings.append(_finding("error", "companion_state_invalid", "Companion state must be a JSON object.", path))
        return {}
    try:
        module = _load_state_validator()
        for item in module.validate_state(data):
            findings.append(_finding(item.get("severity", "error"), item.get("rule", "companion_state_invalid"), item.get("message", "Companion state is invalid."), path))
    except Exception as exc:
        findings.append(_finding("error", "companion_state_checker_failed", str(exc), path))
        return data
    if ready:
        presence = data.get("current_presence", {})
        for key in ("as_of", "place_ref", "activity", "source"):
            if not _meaningful(presence.get(key, "")):
                findings.append(_finding("error", "companion_presence_not_ready", f"current_presence.{key} is required for ready Companion mode.", path))
        if presence.get("availability") == "unknown":
            findings.append(_finding("error", "companion_presence_not_ready", "Ready Companion presence needs a known availability.", path))
        place_ref = _clean(presence.get("place_ref", ""))
        if place_ref and _note_for_id(campaign / "places", place_ref) is None:
            findings.append(_finding("error", "companion_place_ref_missing", f"No place note matches current presence {place_ref!r}.", path))
        for character_ref in presence.get("with_refs", []):
            if _slug(character_ref) == _slug(primary_id):
                findings.append(_finding("error", "companion_presence_self_ref", "with_refs must not include the primary companion themself.", path))
            elif _note_for_id(campaign / "characters", character_ref) is None:
                findings.append(_finding("error", "companion_character_ref_missing", f"No character note matches with_refs entry {character_ref!r}.", path))
        transition = data.get("pending_transition")
        if isinstance(transition, dict):
            transition_place = _clean(transition.get("place_ref", ""))
            if transition_place and _note_for_id(campaign / "places", transition_place) is None:
                findings.append(_finding("error", "companion_transition_place_missing", f"No place note matches pending transition {transition_place!r}.", path))
            for character_ref in transition.get("with_refs", []):
                if _note_for_id(campaign / "characters", character_ref) is None:
                    findings.append(_finding("error", "companion_transition_character_missing", f"No character note matches pending transition contact {character_ref!r}.", path))
        expected_timezone = _clean(profile_setting.get("timezone", ""))
        expected_offset = _clean(profile_setting.get("utc_offset", ""))
        if expected_timezone and _clean(data.get("configured_timezone", "")) != expected_timezone:
            findings.append(_finding("error", "companion_timezone_drift", "State timezone does not match companion_profile.", path))
        if expected_offset and _clean(data.get("configured_utc_offset", "")) != expected_offset:
            findings.append(_finding("error", "companion_offset_drift", "State UTC offset does not match companion_profile.", path))
        if _int(data.get("schema_version"), default=1) >= 2:
            relationship = data.get("relational_context", {})
            if not _meaningful(relationship.get("companion_posture", "")):
                findings.append(_finding("error", "companion_relationship_posture_missing", "Ready Companion relationship needs a companion posture.", path))
            if not _meaningful(relationship.get("reciprocity_pattern", "")):
                findings.append(_finding("error", "companion_relationship_reciprocity_missing", "Ready Companion relationship needs an established reciprocity pattern.", path))
            evidence = relationship.get("recent_evidence", [])
            if not isinstance(evidence, list) or not evidence:
                findings.append(_finding("error", "companion_relationship_evidence_missing", "Ready Companion relationship needs setup or interaction evidence.", path))
            elif _clean(relationship.get("last_change_evidence_id", "")) and _clean(relationship.get("last_change_evidence_id", "")) not in {
                _clean(item.get("evidence_id", "")) for item in evidence if isinstance(item, dict)
            }:
                findings.append(_finding("error", "companion_relationship_change_ref_missing", "last_change_evidence_id must reference recent relationship evidence.", path))
            tensions = relationship.get("active_tensions", [])
            if isinstance(tensions, list) and len(tensions) > 3:
                findings.append(_finding("error", "companion_relationship_tension_limit", "Relational context may retain at most three active tensions.", path))
        else:
            relationship = data.get("primary_relationship", {})
            if not _meaningful(relationship.get("companion_stance", "")):
                findings.append(_finding("error", "companion_relationship_stance_missing", "Ready Companion relationship needs a starting companion stance.", path))
            if not isinstance(relationship.get("last_evidence_refs"), list) or not relationship.get("last_evidence_refs"):
                findings.append(_finding("error", "companion_relationship_evidence_missing", "Ready Companion relationship needs a setup or interaction evidence reference.", path))
    return data


def _markdown_section(text: str, heading: str) -> str:
    match = re.search(rf"(?im)^##\s+{re.escape(heading)}\s*$", text)
    if not match:
        return ""
    rest = text[match.end():]
    next_heading = re.search(r"(?m)^##\s+", rest)
    return rest[: next_heading.start()] if next_heading else rest


def _subsections(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?im)^###\s+(.+?)\s*$", text))
    result: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result.append((match.group(1).strip(), text[match.end():end]))
    return result


def _validate_user_context(
    campaign: Path,
    *,
    ready: bool,
    memory_policy: str,
    profile_schema: int,
    findings: list[dict[str, str]],
) -> None:
    path = campaign / "user_context.md"
    if not path.is_file():
        findings.append(_finding("error", "user_context_missing", "Consent-based user memory file is missing.", path))
        return
    text = _read(path, findings)
    expected_file_policy = memory_policy or ("consent_contextual" if profile_schema == 1 else "contextual_low_risk")
    expected_policy = {
        "Policy": expected_file_policy,
        "Sensitive facts": "explicit consent only",
        "Raw transcript storage": "never",
    }
    for field, expected in expected_policy.items():
        actual = _field(text, field).lower().replace("_", " ")
        if actual != expected.replace("_", " "):
            findings.append(_finding("error", "user_memory_policy_invalid", f"{field} must be {expected}.", path))
    if ready and "### Memory\n\n- Memory id:\n" in text:
        findings.append(_finding("error", "user_memory_template_present", "Remove the example Active Memory before Companion setup completes.", path))
    if ready and "### Follow-Up\n\n- Follow-up id:\n" in text:
        findings.append(_finding("error", "user_followup_template_present", "Remove the example Follow-Up before Companion setup completes.", path))
    active = _markdown_section(text, "Active Memories")
    parts = re.split(r"(?im)^###\s+Memory\s*$", active)[1:]
    active_ids: set[str] = set()
    for index, part in enumerate(parts, start=1):
        memory_id = _field(part, "Memory id")
        content = _field(part, "Content")
        if not memory_id and not content:
            continue
        kind = _field(part, "Kind")
        source = _field(part, "Source")
        consent = _field(part, "Consent")
        sensitive = _field(part, "Sensitive").lower()
        if not _valid_id(memory_id):
            findings.append(_finding("error", "user_memory_id_invalid", f"Memory {index} needs a lowercase stable id.", path))
        elif memory_id in active_ids:
            findings.append(_finding("error", "user_memory_id_duplicate", f"Duplicate active memory id: {memory_id}", path))
        active_ids.add(memory_id)
        if not _meaningful(content):
            findings.append(_finding("error", "user_memory_content_missing", f"Memory {index} has no durable content.", path))
        if kind not in MEMORY_KINDS:
            findings.append(_finding("error", "user_memory_kind_invalid", f"Memory {index} has an invalid kind.", path))
        if source not in MEMORY_SOURCES:
            findings.append(_finding("error", "user_memory_source_invalid", f"Memory {index} lacks an explicit source.", path))
        if consent not in MEMORY_CONSENTS:
            findings.append(_finding("error", "user_memory_consent_invalid", f"Memory {index} has invalid consent.", path))
        if sensitive not in {"yes", "no"}:
            findings.append(_finding("error", "user_memory_sensitive_invalid", f"Memory {index} must mark Sensitive yes or no.", path))
        if sensitive == "yes" and consent != "explicit":
            findings.append(_finding("error", "user_memory_sensitive_without_consent", f"Memory {index} is sensitive but lacks explicit consent.", path))
        if expected_file_policy == "ask_before_save" and consent != "explicit":
            findings.append(_finding("error", "user_memory_save_consent_missing", f"Memory {index} requires explicit save consent under ask_before_save.", path))
        if expected_file_policy == "off":
            findings.append(_finding("error", "user_memory_disabled_but_present", f"Memory {index} is present while durable user memory is off.", path))
        if not _timezone_aware(_field(part, "Recorded at")):
            findings.append(_finding("error", "user_memory_time_invalid", f"Memory {index} needs a timezone-aware Recorded at value.", path))
        last_used = _field(part, "Last used")
        if last_used and _clean(last_used).lower() not in {"never", "not yet"} and not _timezone_aware(last_used):
            findings.append(_finding("error", "user_memory_last_used_invalid", f"Memory {index} has an invalid Last used value.", path))

    followups = _markdown_section(text, "Upcoming Follow-Ups")
    followup_parts = re.split(r"(?im)^###\s+Follow-Up\s*$", followups)[1:]
    followup_ids: set[str] = set()
    for index, part in enumerate(followup_parts, start=1):
        followup_id = _field(part, "Follow-up id")
        content = _field(part, "What the user explicitly shared")
        if not followup_id and not content:
            continue
        if not _valid_id(followup_id):
            findings.append(_finding("error", "user_followup_id_invalid", f"Follow-up {index} needs a lowercase stable id.", path))
        elif followup_id in followup_ids or followup_id in active_ids:
            findings.append(_finding("error", "user_followup_id_duplicate", f"Duplicate user-context id: {followup_id}", path))
        followup_ids.add(followup_id)
        for field in ("What the user explicitly shared", "Due window", "Why a follow-up is welcome"):
            if not _meaningful(_field(part, field)):
                findings.append(_finding("error", "user_followup_field_missing", f"Follow-up {index} is missing {field}.", path))
        consent = _field(part, "Consent")
        sensitive = _field(part, "Sensitive").lower()
        if consent not in MEMORY_CONSENTS:
            findings.append(_finding("error", "user_followup_consent_invalid", f"Follow-up {index} has invalid consent.", path))
        if sensitive not in {"yes", "no"}:
            findings.append(_finding("error", "user_followup_sensitive_invalid", f"Follow-up {index} must mark Sensitive yes or no.", path))
        if sensitive == "yes" and consent != "explicit":
            findings.append(_finding("error", "user_followup_sensitive_without_consent", f"Follow-up {index} is sensitive but lacks explicit consent.", path))
        if expected_file_policy == "ask_before_save" and consent != "explicit":
            findings.append(_finding("error", "user_followup_save_consent_missing", f"Follow-up {index} requires explicit save consent under ask_before_save.", path))
        if _field(part, "Status") not in {"open", "completed", "cancelled"}:
            findings.append(_finding("error", "user_followup_status_invalid", f"Follow-up {index} has an invalid status.", path))
        if expected_file_policy == "off":
            findings.append(_finding("error", "user_memory_disabled_but_present", f"Follow-up {index} is present while durable user memory is off.", path))

    tombstone_header = "| Tombstone id | Forgotten at | Scope |"
    if tombstone_header not in text:
        findings.append(_finding("error", "forget_tombstone_schema_invalid", "Forget tombstones must remain content-free.", path))
        return
    tombstone_ids: set[str] = set()
    tombstones = _markdown_section(text, "Forget Tombstones")
    for line in tombstones.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] == "Tombstone id" or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        tombstone_id, forgotten_at, tombstone_scope = cells
        if not _valid_id(tombstone_id):
            findings.append(_finding("error", "forget_tombstone_id_invalid", f"Tombstone id is invalid: {tombstone_id}", path))
        if tombstone_id in tombstone_ids:
            findings.append(_finding("error", "forget_tombstone_duplicate", f"Duplicate tombstone id: {tombstone_id}", path))
        if tombstone_id in active_ids or tombstone_id in followup_ids:
            findings.append(_finding("error", "forget_tombstone_collision", f"Forgotten id is still active: {tombstone_id}", path))
        tombstone_ids.add(tombstone_id)
        if not _timezone_aware(forgotten_at):
            findings.append(_finding("error", "forget_tombstone_time_invalid", f"Tombstone {tombstone_id} needs a timezone-aware timestamp.", path))
        if not _meaningful(tombstone_scope):
            findings.append(_finding("error", "forget_tombstone_scope_missing", f"Tombstone {tombstone_id} needs a content-free scope label.", path))


def _validate_attention_memory_policy(
    campaign: Path,
    *,
    state: dict[str, Any],
    memory_policy: str,
    findings: list[dict[str, str]],
) -> None:
    """Prevent the hot queue from bypassing an explicitly disabled memory policy."""

    if memory_policy != "off":
        return
    for item in state.get("attention_queue", []) if isinstance(state.get("attention_queue"), list) else []:
        if isinstance(item, dict) and item.get("kind") == "user_event":
            findings.append(
                _finding(
                    "error",
                    "user_memory_disabled_attention_present",
                    "A user-event attention item cannot persist while durable user memory is off.",
                    campaign / "companion_state.json",
                )
            )


def _validate_companion_boundaries(
    campaign: Path,
    *,
    ready: bool,
    relationship: dict[str, str],
    state: dict[str, Any],
    findings: list[dict[str, str]],
) -> None:
    if not ready:
        return
    path = campaign / "boundaries.md"
    text = _read(path, findings) if path.is_file() else ""
    section = _markdown_section(text, "Companion Relationship Boundaries")
    if not section:
        findings.append(_finding("error", "companion_boundaries_missing", "Ready Companion mode needs a versioned Companion Relationship Boundaries section.", path))
        return
    boundary_id = _field(section, "Boundary set id")
    expected_id = _clean(relationship.get("boundary_ref", ""))
    if not _valid_id(boundary_id):
        findings.append(_finding("error", "companion_boundary_id_invalid", "Boundary set id must be a lowercase stable id.", path))
    if expected_id and _slug(boundary_id) != _slug(expected_id):
        findings.append(_finding("error", "companion_boundary_ref_mismatch", "Boundary set id does not match companion_profile relationship.boundary_ref.", path))
    if _int(_field(section, "Contract version"), default=0) < 1:
        findings.append(_finding("error", "companion_boundary_version_invalid", "Companion boundary contract version must be at least 1.", path))
    if _int(_field(section, "Revision"), default=-1) < 0:
        findings.append(_finding("error", "companion_boundary_revision_invalid", "Companion boundary revision must be non-negative.", path))
    scope = _field(section, "Effective relationship scope")
    if scope not in RELATIONSHIP_SCOPES:
        findings.append(_finding("error", "companion_boundary_scope_invalid", "Effective relationship scope is invalid.", path))
    elif scope != _clean(relationship.get("allowed_scope", "")):
        findings.append(_finding("error", "companion_boundary_scope_mismatch", "Effective boundary scope does not match companion_profile.", path))
    narrowing = _field(section, "User-requested narrowing")
    if _meaningful(narrowing):
        if narrowing not in RELATIONSHIP_SCOPES:
            findings.append(_finding("error", "companion_boundary_narrowing_invalid", "User-requested narrowing must use a relationship-scope value or none.", path))
        elif narrowing != scope:
            findings.append(_finding("error", "companion_boundary_narrowing_stale", "An active user-requested narrowing must be the effective relationship scope.", path))
    if not _timezone_aware(_field(section, "Last confirmed at")):
        findings.append(_finding("error", "companion_boundary_confirmation_invalid", "Companion boundaries need a timezone-aware confirmation time.", path))
    for field in (
        "Interaction limits",
        "Romance and intimacy policy",
        "Disagreement and refusal policy",
        "Anti-dependency guard",
        "Identity transparency",
        "Memory consent",
    ):
        if not _meaningful(_field(section, field)):
            findings.append(_finding("error", "companion_boundary_field_missing", f"Companion boundaries are missing {field}.", path))

    relational_context = state.get("relational_context")
    if isinstance(relational_context, dict):
        refs = relational_context.get("boundary_refs", [])
        if not isinstance(refs, list) or boundary_id not in {_clean(value) for value in refs}:
            findings.append(_finding("error", "companion_state_boundary_ref_missing", "State relational_context must reference the active boundary set.", campaign / "companion_state.json"))


def _validate_disclosure_ledger(
    campaign: Path,
    *,
    ready: bool,
    primary_id: str,
    deception_policy: str,
    profile_schema: int,
    findings: list[dict[str, str]],
) -> None:
    if not ready:
        return
    path = campaign / "knowledge_boundaries.md"
    text = _read(path, findings) if path.is_file() else ""
    companion_section = _markdown_section(text, "Companion Knowledge")
    companion_headings = [value.strip() for value in re.findall(r"(?im)^###\s+(.+?)\s*$", companion_section)]
    if not companion_headings or all(_slug(value) in {"companion_name", "primary_companion"} for value in companion_headings):
        findings.append(_finding("error", "companion_knowledge_entry_missing", "Ready Companion mode needs a primary knowledge entry.", path))
    elif primary_id and not any(_slug(primary_id) in _slug(value) or _slug(value) in _slug(primary_id) for value in companion_headings):
        findings.append(_finding("error", "companion_knowledge_ref_mismatch", "Companion Knowledge does not identify the primary companion.", path))

    # Schema-v1 campaigns retain the original loose Reveal Ledger. Migration to
    # profile/state V2 activates the stricter evidence-bound disclosure ledger.
    if profile_schema < 2:
        return
    section = _markdown_section(text, "Companion Disclosure Ledger")
    if not section:
        findings.append(_finding("error", "companion_disclosure_ledger_missing", "Ready Companion V2 mode needs a Companion Disclosure Ledger.", path))
        return
    entries = []
    for heading, body in _subsections(section):
        fact_id = _field(body, "Fact id")
        if not fact_id and _slug(heading) in {"disclosure_fact", "fact"}:
            continue
        if fact_id or any(_meaningful(_field(body, field)) for field in ("Topic", "Private truth", "User-facing account")):
            entries.append((heading, body))
    if not entries:
        findings.append(_finding("error", "companion_disclosure_entry_missing", "Ready Companion V2 mode needs at least one real disclosure fact.", path))
        return

    fact_ids: set[str] = set()
    for heading, body in entries:
        fact_id = _field(body, "Fact id")
        label = fact_id or heading
        if not _valid_id(fact_id):
            findings.append(_finding("error", "companion_disclosure_id_invalid", f"Disclosure entry {heading!r} needs a lowercase stable Fact id.", path))
        elif fact_id in fact_ids:
            findings.append(_finding("error", "companion_disclosure_id_duplicate", f"Duplicate disclosure fact id: {fact_id}", path))
        fact_ids.add(fact_id)
        companion_id = _field(body, "Companion id")
        if _slug(companion_id) != _slug(primary_id):
            findings.append(_finding("error", "companion_disclosure_companion_mismatch", f"Disclosure fact {label} does not identify the primary companion.", path))
        for field in ("Topic", "Private truth", "Reason for posture", "Natural openings"):
            if not _meaningful(_field(body, field)):
                findings.append(_finding("error", "companion_disclosure_field_missing", f"Disclosure fact {label} is missing {field}.", path))
        stage = _field(body, "Stage")
        posture = _field(body, "Posture")
        if stage not in DISCLOSURE_STAGES:
            findings.append(_finding("error", "companion_disclosure_stage_invalid", f"Disclosure fact {label} has an invalid stage.", path))
        if posture not in DISCLOSURE_POSTURES:
            findings.append(_finding("error", "companion_disclosure_posture_invalid", f"Disclosure fact {label} has an invalid posture.", path))
        user_account = _field(body, "User-facing account")
        if stage in {"partial", "shared", "corrected"} and not _meaningful(user_account):
            findings.append(_finding("error", "companion_disclosure_account_missing", f"Disclosure fact {label} needs the account actually given to the user.", path))
        if stage == "private" and _meaningful(user_account):
            findings.append(_finding("error", "companion_private_account_conflict", f"Private disclosure fact {label} cannot claim a user-facing account.", path))
        evidence = _refs(_field(body, "Evidence refs"))
        if not evidence or any(not _meaningful(value) for value in evidence):
            findings.append(_finding("error", "companion_disclosure_evidence_missing", f"Disclosure fact {label} needs at least one contextual evidence ref.", path))
        elif len(evidence) != len(set(evidence)):
            findings.append(_finding("error", "companion_disclosure_evidence_duplicate", f"Disclosure fact {label} repeats an evidence ref.", path))
        if _int(_field(body, "Revision"), default=-1) < 0:
            findings.append(_finding("error", "companion_disclosure_revision_invalid", f"Disclosure fact {label} needs a non-negative revision.", path))

        truthfulness = _field(body, "Account truthfulness")
        direct_lie = _bool(_field(body, "Direct lie permitted"))
        category = _field(body, "Protected category")
        if truthfulness not in ACCOUNT_TRUTHFULNESS:
            findings.append(_finding("error", "companion_disclosure_truthfulness_invalid", f"Disclosure fact {label} has invalid Account truthfulness.", path))
        if direct_lie is None:
            findings.append(_finding("error", "companion_disclosure_lie_flag_invalid", f"Disclosure fact {label} must explicitly set Direct lie permitted yes or no.", path))
        if category not in {"ordinary", *PROTECTED_DECEPTION_CATEGORIES}:
            findings.append(_finding("error", "companion_disclosure_category_invalid", f"Disclosure fact {label} has an invalid Protected category.", path))
        stage_truthfulness = {
            "private": {"not_disclosed"},
            "hinted": {"not_disclosed", "incomplete", "false"},
            "partial": {"incomplete", "truthful", "false"},
            "shared": {"truthful", "false"},
            "corrected": {"corrected", "truthful"},
        }
        if stage in stage_truthfulness and truthfulness not in stage_truthfulness[stage]:
            findings.append(_finding("error", "companion_disclosure_stage_account_conflict", f"Disclosure fact {label} has an account truthfulness inconsistent with stage {stage}.", path))
        if deception_policy == "no_direct_lies" and (direct_lie is True or truthfulness == "false"):
            findings.append(_finding("error", "companion_direct_lie_not_opted_in", f"Disclosure fact {label} permits a direct lie without Session 0 opt-in.", path))
        if category in PROTECTED_DECEPTION_CATEGORIES and (direct_lie is True or truthfulness == "false"):
            findings.append(_finding("error", "companion_protected_deception_forbidden", f"Disclosure fact {label} cannot use deception for protected category {category}.", path))
        if direct_lie is True and truthfulness != "false":
            findings.append(_finding("error", "companion_deception_account_mismatch", f"Disclosure fact {label} permits a lie but does not record a false account.", path))
        if truthfulness == "false":
            if deception_policy != "character_consistent_opt_in" or direct_lie is not True:
                findings.append(_finding("error", "companion_false_account_invalid", f"Disclosure fact {label} has an unauthorized false account.", path))
            if not _meaningful(user_account) or not _meaningful(_field(body, "Deception reason")):
                findings.append(_finding("error", "companion_deception_reason_missing", f"Disclosure fact {label} needs the stable false account and a causal reason.", path))
        if stage == "corrected":
            if truthfulness not in {"corrected", "truthful"} or not _meaningful(_field(body, "Correction note")):
                findings.append(_finding("error", "companion_correction_incomplete", f"Corrected disclosure fact {label} needs a truthful/corrected account and correction note.", path))


def _validate_life_authorities(campaign: Path, *, ready: bool, primary_id: str, findings: list[dict[str, str]]) -> None:
    if not ready:
        return
    dynamics_path = campaign / "world_dynamics.md"
    dynamics = _read(dynamics_path, findings) if dynamics_path.is_file() else ""
    active = _markdown_section(dynamics, "Active Domains")
    domains = [(name, body) for name, body in _subsections(active) if _slug(name) != "domain_name"]
    real_domains = [name for name, _ in domains]
    if not real_domains:
        findings.append(_finding("error", "companion_life_domain_missing", "Ready Companion mode needs at least one active life domain.", dynamics_path))
    domain_ids: set[str] = set()
    for domain_name, body in domains:
        for field in (
            "Domain id",
            "Status",
            "Relevant actors",
            "Current trajectory",
            "Desired outcome (Companion only)",
            "Refresh triggers",
            "Player-visible channels",
            "Next move if ignored",
            "Last evaluated real time (Companion only)",
        ):
            if not _meaningful(_field(body, field)):
                findings.append(_finding("error", "companion_life_domain_field_missing", f"Life domain {domain_name!r} is missing {field}.", dynamics_path))
        domain_id = _slug(_field(body, "Domain id"))
        if domain_id in domain_ids:
            findings.append(_finding("error", "companion_life_domain_duplicate", f"Duplicate life domain id: {domain_id}", dynamics_path))
        domain_ids.add(domain_id)
        if _field(body, "Status").lower() not in {"dormant", "stable", "shifting", "volatile"}:
            findings.append(_finding("error", "companion_life_domain_status_invalid", f"Life domain {domain_name!r} has an invalid status.", dynamics_path))
        timestamp = _field(body, "Last evaluated real time (Companion only)").replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(timestamp)
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError
        except ValueError:
            findings.append(_finding("error", "companion_life_domain_time_invalid", f"Life domain {domain_name!r} needs a timezone-aware last evaluation time.", dynamics_path))

    relationship_path = campaign / "relationship_map.md"
    relationship_text = _read(relationship_path, findings) if relationship_path.is_file() else ""
    rows: list[list[str]] = []
    for line in relationship_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 10 or cells[0] in {"From", "---"} or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    seen: set[tuple[str, str, str]] = set()
    for cells in rows:
        source, direction, target = cells[0], cells[1], cells[2]
        if direction not in {"->", "<->", "→", "↔"}:
            findings.append(_finding("error", "companion_social_direction_invalid", f"Invalid social edge direction: {direction}", relationship_path))
        if any(not _meaningful(cells[index]) for index in (0, 2, 3, 4, 5, 6, 7, 8)):
            findings.append(_finding("error", "companion_social_edge_incomplete", f"Current social edge is incomplete: {source} {direction} {target}.", relationship_path))
        try:
            if int(_clean(cells[9])) < 0:
                raise ValueError
        except ValueError:
            findings.append(_finding("error", "companion_social_revision_invalid", f"Social edge revision is invalid: {source} {direction} {target}.", relationship_path))
        if {_slug(source), _slug(target)} & {"user", "the_user", "player"}:
            findings.append(_finding("error", "companion_primary_relation_duplicated", "The primary user relationship belongs in companion_state.json, not relationship_map.md.", relationship_path))
        if direction in {"<->", "↔"}:
            endpoints = sorted((_slug(source), _slug(target)))
            key = (endpoints[0], "<->", endpoints[1])
        else:
            key = (_slug(source), direction, _slug(target))
        if key in seen:
            findings.append(_finding("error", "companion_social_edge_duplicate", f"Duplicate current social edge: {source} {direction} {target}.", relationship_path))
        seen.add(key)
        for entity in (source, target):
            if _note_for_id(campaign / "characters", entity) is None:
                findings.append(_finding("error", "companion_social_ref_missing", f"Social edge character has no note: {entity}", relationship_path))


def _validate_real_city_research(
    campaign: Path,
    *,
    ready: bool,
    setting: dict[str, str],
    findings: list[dict[str, str]],
) -> None:
    if not ready or _clean(setting.get("mode", "")) != "real_city_fictional_private":
        return
    path = campaign / "research_dossier.md"
    text = _read(path, findings) if path.is_file() else ""
    status_match = re.search(r"(?im)^-\s+Status:[ \t]*`?([a-z_]+)`?[ \t]*$", text)
    status = status_match.group(1) if status_match else ""
    if status not in {"partial_complete", "complete", "unavailable_risk_accepted"}:
        findings.append(_finding("error", "companion_real_city_research_missing", "Real-city Companion setup requires grounded or explicitly risk-accepted research.", path))


def _validate_visual_policy(campaign: Path, *, experience_mode: str, findings: list[dict[str, str]]) -> None:
    if experience_mode != "companion":
        return
    path = campaign / "visual_state.json"
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return  # The shared visual checker reports the parse failure.
    pending = data.get("pending")
    if isinstance(pending, dict):
        placement = _clean(pending.get("placement_target", ""))
        if pending.get("dashboard_placement_requested") is True or placement == "rpg_dashboard_gallery":
            findings.append(_finding("error", "companion_dashboard_visual_forbidden", "Companion portraits cannot request RPG Dashboard placement.", path))
        if placement and placement not in {"none", "companion_view_portrait"}:
            findings.append(_finding("error", "companion_visual_placement_invalid", f"Companion visual placement is invalid: {placement}", path))
    for entry in data.get("history", []) if isinstance(data.get("history"), list) else []:
        if isinstance(entry, dict) and entry.get("dashboard_placement_completed") is True:
            findings.append(_finding("error", "companion_dashboard_visual_forbidden", "Companion visual history cannot claim Dashboard placement.", path))


def _validate_parallelism_notice(
    campaign: Path,
    *,
    required: bool,
    findings: list[dict[str, str]],
) -> None:
    if not required:
        return
    path = campaign / "session_zero.md"
    if not path.is_file():
        findings.append(
            _finding(
                "error",
                "companion_parallelism_summary_missing",
                "Ready Companion setup needs the Session 0 performance summary.",
                path,
            )
        )
        return
    text = _read(path, findings)
    acknowledged = _bool(_field(text, "Companion parallelism usage notice acknowledged"))
    if acknowledged is not True:
        findings.append(
            _finding(
                "error",
                "companion_parallelism_summary_unacknowledged",
                "Session 0 must record acknowledgement of Companion parallelism and model-usage tradeoffs.",
                path,
            )
        )


def _validate_companion_view(
    campaign: Path,
    *,
    ready: bool,
    draft_preflight: bool,
    policy: str,
    state: dict[str, Any],
    findings: list[dict[str, str]],
) -> None:
    state_path = campaign / "companion_view" / "companion_view_state.json"
    checker_path = Path(__file__).with_name("check_companion_view.py")
    if not checker_path.is_file():
        findings.append(_finding("error", "companion_view_checker_missing", "Companion View checker is missing.", checker_path))
        return
    try:
        spec = importlib.util.spec_from_file_location("repog_companion_view_contract", checker_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("checker could not be loaded")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.check_companion_view(state_path, campaign_path=campaign)
    except Exception as exc:
        findings.append(_finding("error", "companion_view_checker_failed", str(exc), checker_path))
        return
    for item in result.get("findings", []):
        findings.append(_finding(item.get("severity", "error"), item.get("rule", "companion_view_invalid"), item.get("message", "Companion View is invalid."), state_path))
    try:
        projection = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    # A draft preflight checks the bundled projection's shape and player-safe
    # contents, but activation is a finalization step after the profile locks.
    expected_enabled = ready and not draft_preflight and policy == "light"
    if projection.get("enabled") is not expected_enabled:
        findings.append(_finding("error", "companion_view_policy_mismatch", f"Companion View enabled must be {str(expected_enabled).lower()} for the current profile/readiness state.", state_path))
    if not draft_preflight and projection.get("public_surface_revision") != state.get("public_surface_revision"):
        findings.append(_finding("error", "companion_view_revision_stale", "Companion View public revision does not match Companion state.", state_path))


def check_companion(
    campaign_path: Path,
    *,
    scope: str = "full",
    preflight_ready: bool = False,
) -> dict[str, Any]:
    campaign = campaign_path.resolve()
    findings: list[dict[str, str]] = []
    if scope not in {"hot", "full"}:
        findings.append(_finding("error", "companion_scope_invalid", "scope must be hot or full.", campaign))
        return _result(campaign, scope, findings)
    setup_path = campaign / "setup_profile.yaml"
    if not setup_path.is_file():
        findings.append(_finding("error", "setup_profile_missing", "setup_profile.yaml is missing.", setup_path))
        return _result(campaign, scope, findings)
    setup_text = _read(setup_path, findings)
    setup = _top_values(setup_text)
    schema = _int(setup.get("schema_version"), default=1)
    experience_mode = _clean(setup.get("experience_mode", ""))
    if schema < 4 and not experience_mode:
        experience_mode = "rpg"
    ready = _bool(setup.get("ready_for_play", "false")) is True
    draft_preflight = bool(preflight_ready and not ready)
    content_ready = bool(ready or draft_preflight)
    setup_revision = _int(setup.get("setup_revision"), default=0)
    profile = _validate_profile(
        campaign,
        experience_mode=experience_mode,
        setup_ready=ready,
        preflight_ready=draft_preflight,
        setup_revision=setup_revision,
        findings=findings,
    )
    _validate_parallelism_notice(
        campaign,
        required=(
            content_ready
            and experience_mode == "companion"
            and bool(
                _clean(profile.get("performance", {}).get("semantic_parallelism", ""))
                or _clean(profile.get("performance", {}).get("max_parallel_workers", ""))
            )
        ),
        findings=findings,
    )
    if (
        content_ready
        and experience_mode == "companion"
        and _clean(setup.get("session_zero_mode", "")) == "deep"
        and _clean(profile.get("setting", {}).get("mode", "")) == "real_city_fictional_private"
        and "real_world_grounding" not in _yaml_list(setup_text, "activated_packs")
    ):
        findings.append(_finding("error", "companion_real_city_pack_missing", "Deep real-city Companion setup must activate real_world_grounding.", setup_path))
    primary_id = str(profile.get("primary_companion_id", ""))
    _validate_persona(
        campaign,
        primary_id=primary_id,
        ready=content_ready and experience_mode == "companion",
        scope=scope,
        relationship=profile.get("relationship", {}),
        findings=findings,
    )
    state = _validate_state(
        campaign,
        ready=content_ready and experience_mode == "companion",
        primary_id=primary_id,
        profile_setting=profile.get("setting", {}),
        findings=findings,
    )
    if scope == "full":
        _validate_user_context(
            campaign,
            ready=content_ready and experience_mode == "companion",
            memory_policy=_clean(profile.get("memory", {}).get("user_policy", "")),
            profile_schema=_int(profile.get("schema_version"), default=1),
            findings=findings,
        )
        _validate_attention_memory_policy(
            campaign,
            state=state,
            memory_policy=_clean(profile.get("memory", {}).get("user_policy", "")),
            findings=findings,
        )
        _validate_companion_boundaries(
            campaign,
            ready=content_ready and experience_mode == "companion",
            relationship=profile.get("relationship", {}),
            state=state,
            findings=findings,
        )
        _validate_disclosure_ledger(
            campaign,
            ready=content_ready and experience_mode == "companion",
            primary_id=primary_id,
            deception_policy=_clean(profile.get("relationship", {}).get("deception_policy", "no_direct_lies")),
            profile_schema=_int(profile.get("schema_version"), default=1),
            findings=findings,
        )
        _validate_life_authorities(
            campaign,
            ready=content_ready and experience_mode == "companion",
            primary_id=primary_id,
            findings=findings,
        )
        _validate_real_city_research(
            campaign,
            ready=content_ready and experience_mode == "companion",
            setting=profile.get("setting", {}),
            findings=findings,
        )
        _validate_visual_policy(campaign, experience_mode=experience_mode, findings=findings)
        if experience_mode == "companion":
            _validate_companion_view(
                campaign,
                ready=ready,
                draft_preflight=draft_preflight,
                policy=_clean(profile.get("visuals", {}).get("companion_view", "off")),
                state=state,
                findings=findings,
            )
    return _result(campaign, scope, findings)


def _result(campaign: Path, scope: str, findings: list[dict[str, str]]) -> dict[str, Any]:
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    return {
        "ok": errors == 0,
        "campaign_path": str(campaign),
        "scope": scope,
        "error_count": errors,
        "warning_count": warnings,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_path")
    parser.add_argument("--scope", choices=("hot", "full"), default="full")
    parser.add_argument(
        "--preflight-ready",
        action="store_true",
        help="Validate draft Companion content as ready without requiring final lock/View activation.",
    )
    args = parser.parse_args(argv)
    result = check_companion(
        Path(args.campaign_path),
        scope=args.scope,
        preflight_ready=args.preflight_ready,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
