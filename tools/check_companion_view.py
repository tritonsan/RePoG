"""Validate the small, player-safe Companion View projection."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


MAX_STATE_BYTES = 8 * 1024
MAX_STATIC_BYTES = 75 * 1024
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
REQUIRED_STATIC = ("index.html", "app.js", "style.css")
ALLOWED_TOP_KEYS = {
    "schema_version",
    "enabled",
    "public_surface_revision",
    "identity",
    "portrait",
    "local_clock",
    "last_shared_status",
    "shared_cards",
}
FORBIDDEN_KEY_PARTS = {
    "trust",
    "closeness",
    "tension",
    "disclosure",
    "secret",
    "hidden",
    "private",
    "memory",
    "usercontext",
    "userprofile",
    "operationid",
    "factid",
    "internalid",
    "relationshipscore",
    "protected",
}
TECHNICAL_TEXT = re.compile(
    r"(?i)(?:\btrust (?:level|band|score|meter)\b|\bcloseness (?:level|band|score|meter)\b|"
    r"\btension (?:level|band|score|meter)\b|\bdisclosure (?:stage|state|readiness)\b|"
    r"\buser (?:memory|profile)\b|\binternal id\b|\b(?:fact|operation)[_-]?id\b|"
    r"\bknowledge_boundaries\b|\bcompanion_state\b|\bcompanion_profile\b)"
)
RAW_INTERNAL_ID = re.compile(r"(?<![\w])(?:[a-z][a-z0-9]*_){1,}[a-z0-9]+(?![\w])")
ABSOLUTE_OR_EXTERNAL = re.compile(r"(?i)^(?:[a-z]:[\\/]|/|https?://|file://|data:)")
SAFE_CARD_TYPES = {"plan", "callback", "keepsake"}


def _finding(severity: str, rule: str, message: str, path: str | Path) -> dict[str, str]:
    return {"severity": severity, "rule": rule, "message": message, "path": str(path)}


def _result(state_path: Path, findings: list[dict[str, str]], *, static_bytes: int = 0) -> dict[str, Any]:
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    return {
        "ok": errors == 0,
        "state": str(state_path),
        "error_count": errors,
        "warning_count": warnings,
        "static_bytes": static_bytes,
        "findings": findings,
    }


def _strict_int(value: Any, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _text(
    value: Any,
    *,
    label: str,
    path: str,
    findings: list[dict[str, str]],
    required: bool = False,
    maximum: int = 280,
) -> str:
    if not isinstance(value, str):
        findings.append(_finding("error", "companion_view_text_invalid", f"{label} must be text.", path))
        return ""
    clean = value.strip()
    if required and not clean:
        findings.append(_finding("error", "companion_view_text_missing", f"{label} cannot be blank.", path))
    if len(clean) > maximum:
        findings.append(_finding("error", "companion_view_text_too_long", f"{label} exceeds {maximum} characters.", path))
    if TECHNICAL_TEXT.search(clean) or RAW_INTERNAL_ID.search(clean):
        findings.append(_finding("error", "companion_view_internal_leak", f"{label} contains internal relationship or memory language.", path))
    return clean


def _unknown_keys(value: dict[str, Any], allowed: set[str], path: str, findings: list[dict[str, str]]) -> None:
    for key in value:
        if key not in allowed:
            findings.append(_finding("error", "companion_view_field_forbidden", f"Field is not part of the public projection: {key}", f"{path}.{key}"))


def _walk_forbidden_keys(value: Any, path: str, findings: list[dict[str, str]]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if any(part in normalized for part in FORBIDDEN_KEY_PARTS):
                findings.append(_finding("error", "companion_view_private_field", "Relationship meters, disclosure state, user memory, and protected fields cannot enter Companion View.", f"{path}.{key}"))
            _walk_forbidden_keys(item, f"{path}.{key}", findings)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_forbidden_keys(item, f"{path}[{index}]", findings)


def _parse_time(value: Any, path: str, findings: list[dict[str, str]]) -> None:
    if not isinstance(value, str) or not value.strip():
        findings.append(_finding("error", "companion_view_time_invalid", "shared_at must be an ISO-8601 timestamp.", path))
        return
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        findings.append(_finding("error", "companion_view_time_invalid", "shared_at must be an ISO-8601 timestamp.", path))
        return
    if parsed.tzinfo is None:
        findings.append(_finding("error", "companion_view_time_naive", "shared_at must include a timezone.", path))


def _protected_names(campaign: Path) -> list[str]:
    path = campaign / "knowledge_boundaries.md"
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    section = re.search(r"(?ms)^## Protected Proper Nouns\s*$\n(?P<body>.*?)(?=^##\s|\Z)", text)
    if section is None:
        return []
    body = section.group("body")
    headings = list(re.finditer(r"(?m)^###\s+(.+?)\s*$", body))
    protected: list[str] = []
    for index, heading in enumerate(headings):
        name = heading.group(1).strip().strip("`*_ ")
        if name.casefold() in {"protected name", "name", "example"}:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        entry = body[heading.end() : end]
        match = re.search(r"(?mi)^\s*-\s*Status:\s*(.+?)\s*$", entry)
        status = match.group(1).strip().strip("`*_ ").casefold() if match else ""
        if not any(re.match(rf"^{re.escape(safe)}\b", status) for safe in ("revealed", "pc-known", "player-known", "confirmed")):
            protected.append(name)
    return sorted(set(protected), key=str.casefold)


def _walk_protected(value: Any, path: str, names: list[str], findings: list[dict[str, str]]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _walk_protected(item, f"{path}.{key}", names, findings)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_protected(item, f"{path}[{index}]", names, findings)
    elif isinstance(value, str):
        for name in names:
            if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", value, re.IGNORECASE):
                findings.append(_finding("error", "companion_view_protected_content", "Companion View contains an unrevealed protected name.", path))


def _safe_asset(view: Path, value: Any, findings: list[dict[str, str]], *, require_assets: bool) -> str:
    if not isinstance(value, str):
        findings.append(_finding("error", "companion_view_asset_invalid", "Portrait asset must be text.", "portrait.asset"))
        return ""
    clean = value.strip().replace("\\", "/")
    if not clean or ABSOLUTE_OR_EXTERNAL.search(clean) or not clean.startswith("assets/"):
        findings.append(_finding("error", "companion_view_asset_unsafe", "Portrait must use a relative assets/... path.", "portrait.asset"))
        return ""
    parts = Path(clean).parts
    if ".." in parts or any(part.casefold() in {"draft", "drafts", "_drafts"} for part in parts):
        findings.append(_finding("error", "companion_view_asset_unsafe", "Draft and escaping paths are not allowed.", "portrait.asset"))
        return ""
    if Path(clean).suffix.casefold() not in IMAGE_SUFFIXES:
        findings.append(_finding("error", "companion_view_asset_type", "Portrait must be PNG, JPEG, WebP, or GIF.", "portrait.asset"))
        return ""
    candidate = view / Path(clean)
    if any(part.is_symlink() for part in [candidate, *candidate.parents] if part != view.parent):
        findings.append(_finding("error", "companion_view_asset_symlink", "Symlinked portrait assets are not served.", "portrait.asset"))
        return ""
    resolved = candidate.resolve()
    try:
        resolved.relative_to(view.resolve())
    except ValueError:
        findings.append(_finding("error", "companion_view_asset_unsafe", "Portrait path escapes Companion View.", "portrait.asset"))
        return ""
    if require_assets and not resolved.is_file():
        findings.append(_finding("error", "companion_view_asset_missing", "Referenced portrait asset does not exist.", "portrait.asset"))
    return clean


def check_companion_view_data(
    data: Any,
    state_path: Path,
    *,
    campaign_path: Path | None = None,
    require_assets: bool = True,
) -> dict[str, Any]:
    state_path = state_path.resolve()
    view = state_path.parent
    campaign = (campaign_path or view.parent).resolve()
    findings: list[dict[str, str]] = []
    if not isinstance(data, dict):
        findings.append(_finding("error", "companion_view_state_invalid", "Projection must contain a JSON object.", state_path))
        return _result(state_path, findings)
    _unknown_keys(data, ALLOWED_TOP_KEYS, "state", findings)
    _walk_forbidden_keys(data, "state", findings)
    if data.get("schema_version") != 1:
        findings.append(_finding("error", "companion_view_schema_invalid", "schema_version must be 1.", "schema_version"))
    if not isinstance(data.get("enabled"), bool):
        findings.append(_finding("error", "companion_view_enabled_invalid", "enabled must be true or false.", "enabled"))
    if not _strict_int(data.get("public_surface_revision")):
        findings.append(_finding("error", "companion_view_revision_invalid", "public_surface_revision must be a non-negative integer.", "public_surface_revision"))

    identity = data.get("identity")
    if not isinstance(identity, dict):
        findings.append(_finding("error", "companion_view_identity_invalid", "identity must be an object.", "identity"))
    else:
        _unknown_keys(identity, {"name", "pronouns", "tagline"}, "identity", findings)
        name = _text(identity.get("name"), label="Public name", path="identity.name", findings=findings, required=data.get("enabled") is True, maximum=80)
        _text(identity.get("pronouns"), label="Pronouns", path="identity.pronouns", findings=findings, maximum=80)
        _text(identity.get("tagline"), label="Tagline", path="identity.tagline", findings=findings, maximum=180)
        if data.get("enabled") is False and name:
            findings.append(_finding("warning", "companion_view_inactive_identity", "The view is disabled but still contains a public identity.", "identity.name"))

    portrait = data.get("portrait")
    if portrait is not None:
        if not isinstance(portrait, dict):
            findings.append(_finding("error", "companion_view_portrait_invalid", "portrait must be null or an object.", "portrait"))
        else:
            _unknown_keys(portrait, {"asset", "alt"}, "portrait", findings)
            asset = _safe_asset(view, portrait.get("asset"), findings, require_assets=require_assets)
            alt = _text(portrait.get("alt"), label="Portrait alternative text", path="portrait.alt", findings=findings, required=True, maximum=280)
            generic = {"portrait", "image", "companion portrait", "companion image"}
            if alt.casefold() in generic or (asset and alt.casefold() == Path(asset).stem.casefold()):
                findings.append(_finding("error", "companion_view_alt_not_meaningful", "Portrait alt text must describe the visible character, not the file or image type.", "portrait.alt"))

    clock = data.get("local_clock")
    if clock is not None:
        if not isinstance(clock, dict):
            findings.append(_finding("error", "companion_view_clock_invalid", "local_clock must be null or an object.", "local_clock"))
        else:
            _unknown_keys(clock, {"label", "timezone"}, "local_clock", findings)
            _text(clock.get("label"), label="Clock label", path="local_clock.label", findings=findings, required=True, maximum=80)
            timezone = _text(clock.get("timezone"), label="IANA timezone", path="local_clock.timezone", findings=findings, required=True, maximum=80)
            if timezone:
                try:
                    ZoneInfo(timezone)
                except (ZoneInfoNotFoundError, ValueError):
                    findings.append(_finding("error", "companion_view_timezone_invalid", "local_clock.timezone must be a known IANA timezone.", "local_clock.timezone"))

    status = data.get("last_shared_status")
    if status is not None:
        if not isinstance(status, dict):
            findings.append(_finding("error", "companion_view_status_invalid", "last_shared_status must be null or an object.", "last_shared_status"))
        else:
            _unknown_keys(status, {"text", "shared_at"}, "last_shared_status", findings)
            _text(status.get("text"), label="Last shared status", path="last_shared_status.text", findings=findings, required=True, maximum=280)
            _parse_time(status.get("shared_at"), "last_shared_status.shared_at", findings)

    cards = data.get("shared_cards")
    if not isinstance(cards, list):
        findings.append(_finding("error", "companion_view_cards_invalid", "shared_cards must be a list.", "shared_cards"))
    else:
        if len(cards) > 3:
            findings.append(_finding("error", "companion_view_cards_excess", "Companion View may show at most three shared cards.", "shared_cards"))
        for index, card in enumerate(cards):
            path = f"shared_cards[{index}]"
            if not isinstance(card, dict):
                findings.append(_finding("error", "companion_view_card_invalid", "Shared cards must be objects.", path))
                continue
            _unknown_keys(card, {"type", "title", "text"}, path, findings)
            if card.get("type") not in SAFE_CARD_TYPES:
                findings.append(_finding("error", "companion_view_card_type", "Card type must be plan, callback, or keepsake.", f"{path}.type"))
            _text(card.get("title"), label="Card title", path=f"{path}.title", findings=findings, required=True, maximum=80)
            _text(card.get("text"), label="Card text", path=f"{path}.text", findings=findings, required=True, maximum=240)

    _walk_protected(data, "state", _protected_names(campaign), findings)
    return _result(state_path, findings)


def check_companion_view(
    state_path: Path,
    *,
    campaign_path: Path | None = None,
    require_assets: bool = True,
) -> dict[str, Any]:
    state_path = state_path.resolve()
    view = state_path.parent
    findings: list[dict[str, str]] = []
    static_bytes = 0
    if not state_path.is_file():
        findings.append(_finding("error", "companion_view_state_missing", f"Missing {state_path}", state_path))
        return _result(state_path, findings)
    try:
        state_size = state_path.stat().st_size
    except OSError as exc:
        findings.append(_finding("error", "companion_view_state_unreadable", str(exc), state_path))
        return _result(state_path, findings)
    if state_size > MAX_STATE_BYTES:
        findings.append(_finding("error", "companion_view_state_too_large", f"Projection is {state_size} bytes; maximum is {MAX_STATE_BYTES}.", state_path))
    for name in REQUIRED_STATIC:
        path = view / name
        if not path.is_file():
            findings.append(_finding("error", "companion_view_static_missing", f"Missing {name}.", path))
            continue
        if path.is_symlink():
            findings.append(_finding("error", "companion_view_static_symlink", f"{name} cannot be a symlink.", path))
            continue
        static_bytes += path.stat().st_size
    if static_bytes > MAX_STATIC_BYTES:
        findings.append(_finding("error", "companion_view_static_too_large", f"Initial static files total {static_bytes} bytes; maximum is {MAX_STATIC_BYTES}.", view))
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        findings.append(_finding("error", "companion_view_state_unreadable", str(exc), state_path))
        return _result(state_path, findings, static_bytes=static_bytes)
    content = check_companion_view_data(data, state_path, campaign_path=campaign_path, require_assets=require_assets)
    findings.extend(content["findings"])
    return _result(state_path, findings, static_bytes=static_bytes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", nargs="?", default="campaign/companion_view/companion_view_state.json")
    parser.add_argument("--campaign", help="Campaign folder used for protected-name checks.")
    parser.add_argument("--no-require-assets", action="store_true")
    args = parser.parse_args(argv)
    result = check_companion_view(
        Path(args.state),
        campaign_path=Path(args.campaign).resolve() if args.campaign else None,
        require_assets=not args.no_require_assets,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
