"""Validate private World Voices memory and its player-safe projection.

This checker enforces structural boundaries only. It never decides whether a
source should communicate, whether a claim is true, or whether a voice is
convincing; those remain GPT-5.6 responsibilities.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")
ARTIFACT_FAMILIES = {"personal", "public_media", "faction_institutional", "legal_official", "intelligence_covert", "cultural_academic_commercial", "custom"}
PRODUCTION_STATUSES = {"proposed", "approved", "rejected", "retracted", "superseded", "archived"}
DISTRIBUTION_STATUSES = {"scheduled", "in_transit", "delivered", "discovered", "intercepted", "lost", "leaked", "copied", "quoted", "altered", "forged", "archived"}
CLAIM_CLASSES = {"confirmed", "observed", "believed", "inferred", "rumor", "withheld", "deliberate_falsehood", "unknown", "uncertain"}
EPISTEMIC_LAYERS = {
    "confirmed_facts", "direct_evidence", "beliefs", "inferences", "rumors",
    "withheld", "deliberate_falsehoods", "cannot_know_or_imply",
    "uncertainty", "verification_habits",
}
SOURCE_KINDS = {"npc", "faction", "institution", "office", "outlet", "network", "player", "unknown"}
EVENT_KINDS = {"durable_revision", "world_event", "artifact", "player_message", "explicit_request"}
PRIVATE_KEYS = {
    "epistemic_basis", "claim_basis", "claim_class", "fact_id", "fact_ids",
    "actual_provenance", "operation_id", "source_event_ref", "hidden",
    "gm_only", "secret", "protected_name", "unrevealed", "holders",
}
PROJECTION_CATALOG_KEYS = {"projection_version", "generated_revision", "page_size", "visible_count", "pages"}
PROJECTION_PAGE_KEYS = {"page_version", "generated_revision", "page", "documents"}
PROJECTION_SUMMARY_KEYS = {
    "key", "path", "title", "family", "artifact_type", "source_label",
    "authored_time", "authored_order", "received_time", "received_order", "thread_key", "compare_group", "status",
    "unread_hint", "acquisition_summary", "access_scope",
}
PROJECTION_DOCUMENT_KEYS = {
    "document_version", "key", "title", "family", "artifact_type", "source_label",
    "authored_time", "authored_order", "authored_place", "intended_audience", "channel", "skin",
    "body_text", "acquisition_context", "thread_key", "reply_to_key",
    "supersedes_key", "status", "compare_group", "links",
    "access_scope", "received_order",
}


def _finding(severity: str, rule: str, message: str, path: str | Path) -> dict[str, str]:
    return {"severity": severity, "rule": rule, "message": message, "path": str(path)}


def _load(path: Path, findings: list[dict]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(_finding("error", "world_voices_json_invalid", str(exc), path))
        return None


def _safe_relative(root: Path, raw: Any, *, prefix: str, findings: list[dict], label: str, must_exist: bool = True) -> Path | None:
    if not isinstance(raw, str) or not raw.strip() or "\\" in raw:
        findings.append(_finding("error", "world_voices_path_invalid", f"{label} must be a non-empty forward-slash relative path.", raw or label))
        return None
    path = (root / raw).resolve()
    try:
        relative = path.relative_to(root.resolve()).as_posix()
    except ValueError:
        findings.append(_finding("error", "world_voices_path_escape", f"{label} escapes its allowed root.", raw))
        return None
    if not relative.startswith(prefix):
        findings.append(_finding("error", "world_voices_path_scope", f"{label} must remain under {prefix}.", raw))
        return None
    if must_exist and not path.is_file():
        findings.append(_finding("error", "world_voices_file_missing", f"Referenced file does not exist: {raw}", raw))
    return path


def _ids_from_knowledge(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return {
        value.strip().strip("`*_ ")
        for value in re.findall(r"(?mi)^\s*-\s*Fact id:\s*(.+?)\s*$", path.read_text(encoding="utf-8"))
        if value.strip().strip("`*_ ")
    }


def _current_continuity_revision(path: Path) -> int | None:
    if not path.is_file():
        return None
    match = re.search(r"(?m)^continuity_revision:\s*(\d+)\s*$", path.read_text(encoding="utf-8"))
    return int(match.group(1)) if match else None


def _protected_records(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    section = re.search(r"(?ms)^## Protected Proper Nouns\s*$\n(?P<body>.*?)(?=^##\s|\Z)", text)
    if section is None:
        return []
    body = section.group("body")
    headings = list(re.finditer(r"(?m)^###\s+(.+?)\s*$", body))
    records: list[dict[str, str]] = []
    for index, heading in enumerate(headings):
        name = heading.group(1).strip().strip("`*_ ")
        if name.casefold() in {"protected name", "name", "example"}:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        entry = body[heading.end():end]
        fields = {
            key.casefold(): value.strip().strip("`*_ ")
            for key, value in re.findall(r"(?mi)^\s*-\s*([^:]+):\s*(.*?)\s*$", entry)
        }
        records.append({"name": name, **fields})
    return records


def _walk_private_keys(value: Any, path: str, findings: list[dict]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}" if path else key
            if key.casefold() in PRIVATE_KEYS:
                findings.append(_finding("error", "world_voices_projection_private_field", "Private World Voices metadata entered a player projection.", child))
            _walk_private_keys(item, child, findings)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_private_keys(item, f"{path}[{index}]", findings)


def validate_manifest(campaign: Path) -> tuple[list[dict], dict | None]:
    findings: list[dict] = []
    path = campaign / "world_voices" / "index.json"
    if not path.exists():
        return findings, None  # Backwards-compatible: missing means off.
    data = _load(path, findings)
    if not isinstance(data, dict):
        return findings, None
    if data.get("schema_version") != 1:
        findings.append(_finding("error", "world_voices_schema_invalid", "World Voices schema_version must be 1.", path))
    for field in ("revision", "continuity_revision", "operation_sequence"):
        value = data.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            findings.append(_finding("error", "world_voices_revision_invalid", f"{field} must be a non-negative integer.", path))
    operations = data.get("completed_operations")
    artifacts = data.get("artifacts")
    if not isinstance(operations, dict):
        findings.append(_finding("error", "world_voices_operations_invalid", "completed_operations must be an object.", path))
        operations = {}
    if not isinstance(artifacts, dict):
        findings.append(_finding("error", "world_voices_artifacts_invalid", "artifacts must be an object.", path))
        return findings, data
    sequences: list[int] = []
    for operation_id, record in operations.items():
        if not SAFE_ID.fullmatch(operation_id) or not isinstance(record, dict):
            findings.append(_finding("error", "world_voices_operation_invalid", "Completed operation ids and records must be valid.", f"{path}#{operation_id}"))
            continue
        sequence = record.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
            findings.append(_finding("error", "world_voices_operation_sequence_invalid", "Completed operation sequence must be a positive integer.", f"{path}#{operation_id}"))
        else:
            sequences.append(sequence)
    if len(sequences) != len(set(sequences)):
        findings.append(_finding("error", "world_voices_operation_sequence_duplicate", "Completed operation sequences must be unique.", path))
    if sequences and max(sequences) > data.get("operation_sequence", -1):
        findings.append(_finding("error", "world_voices_operation_sequence_stale", "operation_sequence trails a completed operation.", path))
    campaign_revision = _current_continuity_revision(campaign / "current_state.yaml")
    if campaign_revision is not None and data.get("continuity_revision") != campaign_revision:
        findings.append(_finding("error", "world_voices_continuity_stale", "World Voices continuity_revision must match current_state.yaml after a durable change.", path))

    knowledge_ids = _ids_from_knowledge(campaign / "knowledge_boundaries.md")
    protected_records = _protected_records(campaign / "knowledge_boundaries.md")
    distribution_ids: set[str] = set()
    for artifact_id, artifact in artifacts.items():
        where = f"{path}#artifacts.{artifact_id}"
        if not SAFE_ID.fullmatch(artifact_id) or not isinstance(artifact, dict):
            findings.append(_finding("error", "world_voices_artifact_invalid", "Artifact ids and records must be valid.", where))
            continue
        required_text = ("title", "artifact_type", "authored_time", "authored_place", "intended_audience", "intent", "channel", "body_path", "created_by_operation_id")
        for field in required_text:
            if not isinstance(artifact.get(field), str) or not artifact[field].strip():
                findings.append(_finding("error", "world_voices_artifact_field_missing", f"Artifact requires {field}.", where))
        if artifact.get("artifact_id") != artifact_id:
            findings.append(_finding("error", "world_voices_artifact_identity_mismatch", "Artifact record id must match its manifest key.", where))
        for field in ("actual_provenance", "perceived_provenance"):
            if not isinstance(artifact.get(field), str) or not artifact[field].strip():
                findings.append(_finding("error", "world_voices_provenance_missing", f"Artifact requires private {field}.", where))
        version = artifact.get("version")
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            findings.append(_finding("error", "world_voices_version_invalid", "Artifact version must be a positive integer.", where))
        authored_index = artifact.get("authored_time_index")
        if isinstance(authored_index, bool) or not isinstance(authored_index, int) or authored_index < 0:
            findings.append(_finding("error", "world_voices_time_index_invalid", "Artifact authored_time_index must be a non-negative integer.", where))
        links = artifact.get("player_safe_links")
        if not isinstance(links, list) or any(not isinstance(link, dict) or set(link) != {"kind", "label"} or not all(isinstance(value, str) and value.strip() for value in link.values()) for link in links):
            findings.append(_finding("error", "world_voices_links_invalid", "player_safe_links may contain only bounded kind/label objects.", where))
        if artifact.get("family") not in ARTIFACT_FAMILIES:
            findings.append(_finding("error", "world_voices_family_invalid", "Artifact family is outside the extensible registry.", where))
        if artifact.get("production_status") not in PRODUCTION_STATUSES:
            findings.append(_finding("error", "world_voices_status_invalid", "Artifact production_status is invalid.", where))
        author = artifact.get("author")
        if not isinstance(author, dict) or author.get("kind") not in SOURCE_KINDS or not all(isinstance(author.get(k), str) and author[k].strip() for k in ("ref", "label")):
            findings.append(_finding("error", "world_voices_author_invalid", "Artifact author needs kind, ref, and player-safe label.", where))
        elif author.get("kind") == "player" and artifact.get("player_wording_approved") is not True:
            findings.append(_finding("error", "world_voices_player_authorship_unapproved", "Player-authored artifacts require explicit wording approval.", where))
        source_event = artifact.get("source_event")
        if not isinstance(source_event, dict) or source_event.get("kind") not in EVENT_KINDS or not isinstance(source_event.get("ref"), str) or not source_event.get("ref", "").strip():
            findings.append(_finding("error", "world_voices_source_event_invalid", "Artifact needs a supported causal source event.", where))
        elif not SAFE_ID.fullmatch(source_event["ref"]):
            findings.append(_finding("error", "world_voices_source_event_ref_invalid", "Source event ref must be a stable id.", where))
        elif source_event.get("kind") == "artifact" and source_event.get("ref") not in artifacts:
            findings.append(_finding("error", "world_voices_source_artifact_missing", "Source artifact reference does not exist.", where))
        elif source_event.get("kind") == "durable_revision":
            revision_match = re.search(r"(?:^|[-_])(?:rev|revision)[-_]?(\d+)$", source_event["ref"])
            if revision_match is None or int(revision_match.group(1)) > data.get("continuity_revision", -1):
                findings.append(_finding("error", "world_voices_source_revision_invalid", "Durable source refs must end in an existing rev-N or revision-N.", where))
        body_file = _safe_relative(campaign, artifact.get("body_path"), prefix="world_voices/artifacts/", findings=findings, label="body_path")
        if artifact.get("created_by_operation_id") not in operations:
            findings.append(_finding("error", "world_voices_creation_operation_missing", "Artifact creation operation is absent from the permanent ledger.", where))
        created_revision = artifact.get("created_revision")
        if isinstance(created_revision, bool) or not isinstance(created_revision, int) or created_revision < 0 or created_revision > data.get("continuity_revision", -1):
            findings.append(_finding("error", "world_voices_created_revision_invalid", "Artifact created_revision is outside campaign continuity.", where))
        thread_id = artifact.get("thread_id")
        if not isinstance(thread_id, str) or not SAFE_ID.fullmatch(thread_id):
            findings.append(_finding("error", "world_voices_thread_invalid", "thread_id must be a stable id.", where))
        for field in ("root_artifact_id", "reply_to", "supersedes", "superseded_by", "retraction_artifact_id"):
            ref = artifact.get(field)
            if ref is not None and (not isinstance(ref, str) or ref not in artifacts):
                findings.append(_finding("error", "world_voices_artifact_reference_invalid", f"{field} must reference an existing artifact or be null.", where))
        claims = artifact.get("claim_basis")
        if not isinstance(claims, list):
            findings.append(_finding("error", "world_voices_claim_basis_invalid", "claim_basis must be a private list.", where))
        else:
            claim_ids: set[str] = set()
            for index, claim in enumerate(claims):
                cwhere = f"{where}.claim_basis[{index}]"
                if not isinstance(claim, dict) or not SAFE_ID.fullmatch(str(claim.get("claim_id", ""))) or claim.get("classification") not in CLAIM_CLASSES:
                    findings.append(_finding("error", "world_voices_claim_invalid", "Each claim needs a stable id and approved classification.", cwhere))
                    continue
                if claim["claim_id"] in claim_ids:
                    findings.append(_finding("error", "world_voices_claim_duplicate", "Claim ids must be unique within an artifact.", cwhere))
                claim_ids.add(claim["claim_id"])
                fact_id = claim.get("fact_id")
                if fact_id is not None and (not isinstance(fact_id, str) or fact_id not in knowledge_ids):
                    findings.append(_finding("error", "world_voices_fact_reference_invalid", "Claim fact_id must exist in knowledge_boundaries.md.", cwhere))
                if not isinstance(claim.get("basis"), str) or not claim.get("basis", "").strip():
                    findings.append(_finding("error", "world_voices_claim_basis_missing", "Each private claim record needs a bounded basis.", cwhere))
        epistemic = artifact.get("epistemic_basis")
        if not isinstance(epistemic, dict) or set(epistemic) != EPISTEMIC_LAYERS or any(not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value) for value in epistemic.values()):
            findings.append(_finding("error", "world_voices_epistemic_basis_invalid", "Private epistemic_basis must contain the ten bounded perspective layers.", where))
        if body_file is not None and body_file.is_file() and isinstance(author, dict):
            body_text = body_file.read_text(encoding="utf-8")
            claim_fact_ids = {claim.get("fact_id") for claim in claims if isinstance(claim, dict)} if isinstance(claims, list) else set()
            for protected in protected_records:
                if not re.search(rf"(?<!\w){re.escape(protected['name'])}(?!\w)", body_text, re.IGNORECASE):
                    continue
                status = protected.get("status", "").casefold()
                fact_id = protected.get("fact id", "")
                globally_revealed = any(status.startswith(value) for value in ("revealed", "pc-known", "player-known", "confirmed"))
                holder_text = " ".join((protected.get("companions who know", ""), protected.get("npcs or factions who know", ""))).casefold()
                author_known = author.get("kind") == "player" and any(protected.get(field, "").casefold() in {"yes", "true", "known"} for field in ("player knows", "player character knows"))
                author_tokens = [str(author.get(field, "")).strip().casefold() for field in ("ref", "label")]
                author_known = author_known or any(token and token in holder_text for token in author_tokens)
                if not globally_revealed and (not fact_id or fact_id not in claim_fact_ids or not author_known):
                    findings.append(_finding("error", "world_voices_protected_name_unbounded", "Artifact uses a protected name without a matching fact reference and recorded source holder.", where))
        distributions = artifact.get("distributions")
        if not isinstance(distributions, list):
            findings.append(_finding("error", "world_voices_distributions_invalid", "distributions must be a list.", where))
            continue
        for index, distribution in enumerate(distributions):
            dwhere = f"{where}.distributions[{index}]"
            if not isinstance(distribution, dict) or not SAFE_ID.fullmatch(str(distribution.get("distribution_id", ""))):
                findings.append(_finding("error", "world_voices_distribution_invalid", "Distribution needs a stable id.", dwhere))
                continue
            distribution_id = distribution["distribution_id"]
            if distribution_id in distribution_ids:
                findings.append(_finding("error", "world_voices_distribution_duplicate", "Distribution ids must be globally unique.", dwhere))
            distribution_ids.add(distribution_id)
            if distribution.get("status") not in DISTRIBUTION_STATUSES:
                findings.append(_finding("error", "world_voices_distribution_status_invalid", "Distribution status is invalid.", dwhere))
            for field in ("channel", "scheduled_time", "causal_basis", "operation_id"):
                if not isinstance(distribution.get(field), str) or not distribution[field].strip():
                    findings.append(_finding("error", "world_voices_distribution_field_missing", f"Distribution requires {field}.", dwhere))
            scheduled_index = distribution.get("scheduled_time_index")
            completed_index = distribution.get("completed_time_index")
            if isinstance(scheduled_index, bool) or not isinstance(scheduled_index, int) or scheduled_index < 0:
                findings.append(_finding("error", "world_voices_time_index_invalid", "Distribution scheduled_time_index must be a non-negative integer.", dwhere))
            if completed_index is not None and (isinstance(completed_index, bool) or not isinstance(completed_index, int) or completed_index < scheduled_index):
                findings.append(_finding("error", "world_voices_time_index_invalid", "Distribution completed_time_index cannot precede scheduling.", dwhere))
            if not isinstance(distribution.get("recipients"), list) or not distribution["recipients"]:
                findings.append(_finding("error", "world_voices_distribution_recipients_invalid", "Distribution needs one or more recipient refs.", dwhere))
            for flag in ("public", "player_access", "dashboard_eligible"):
                if not isinstance(distribution.get(flag), bool):
                    findings.append(_finding("error", "world_voices_distribution_flag_invalid", f"{flag} must be boolean.", dwhere))
            if distribution.get("dashboard_eligible") and not distribution.get("player_access"):
                findings.append(_finding("error", "world_voices_hidden_dashboard", "A non-player-access distribution cannot be Dashboard eligible.", dwhere))
            if distribution.get("player_access") and distribution.get("status") not in {"delivered", "discovered", "intercepted", "leaked", "copied", "quoted", "archived"}:
                findings.append(_finding("error", "world_voices_delivery_timing_invalid", "Player access cannot precede a completed acquisition channel.", dwhere))
            history = distribution.get("history")
            if not isinstance(history, list) or not history or not isinstance(history[0], dict) or history[0].get("status") != "scheduled":
                findings.append(_finding("error", "world_voices_distribution_history_invalid", "Distribution history must begin with its scheduled record.", dwhere))
            else:
                previous_time_index = -1
                for history_index, event in enumerate(history):
                    if not isinstance(event, dict) or set(event) != {"status", "time", "time_index", "operation_id"} or event.get("status") not in DISTRIBUTION_STATUSES or event.get("operation_id") not in operations or isinstance(event.get("time_index"), bool) or not isinstance(event.get("time_index"), int):
                        findings.append(_finding("error", "world_voices_distribution_history_invalid", "Distribution history contains an invalid lifecycle event.", f"{dwhere}.history[{history_index}]"))
                        continue
                    if event["time_index"] < previous_time_index:
                        findings.append(_finding("error", "world_voices_distribution_history_order", "Distribution history time indices must be monotonic.", f"{dwhere}.history[{history_index}]"))
                    previous_time_index = event["time_index"]
                if isinstance(history[-1], dict) and (history[-1].get("status") != distribution.get("status") or history[-1].get("operation_id") != distribution.get("operation_id")):
                    findings.append(_finding("error", "world_voices_distribution_history_current", "Current distribution status and operation must match the latest history entry.", dwhere))
            if distribution.get("operation_id") not in operations:
                findings.append(_finding("error", "world_voices_distribution_operation_missing", "Distribution operation is absent from the permanent ledger.", dwhere))
            knowledge_revision = distribution.get("knowledge_revision")
            if distribution.get("player_access") and (isinstance(knowledge_revision, bool) or not isinstance(knowledge_revision, int) or knowledge_revision > data.get("continuity_revision", -1)):
                findings.append(_finding("error", "world_voices_knowledge_revision_missing", "Player access requires a matching durable knowledge revision.", dwhere))
    return findings, data


def validate_projection(campaign: Path, *, full: bool = True) -> list[dict]:
    findings: list[dict] = []
    root = campaign / "dashboard"
    catalog_path = root / "assets" / "world_voices" / "catalog.json"
    if not catalog_path.is_file():
        return findings
    catalog = _load(catalog_path, findings)
    if not isinstance(catalog, dict):
        return findings
    _walk_private_keys(catalog, "catalog", findings)
    if set(catalog) != PROJECTION_CATALOG_KEYS or catalog.get("projection_version") != 1:
        findings.append(_finding("error", "world_voices_catalog_contract", "Player catalog has unsupported fields or version.", catalog_path))
    page_size = catalog.get("page_size")
    if isinstance(page_size, bool) or not isinstance(page_size, int) or not 1 <= page_size <= 50:
        findings.append(_finding("error", "world_voices_catalog_page_size", "Catalog page_size must be 1..50.", catalog_path))
    pages = catalog.get("pages")
    if not isinstance(pages, list) or len(pages) > 128:
        findings.append(_finding("error", "world_voices_catalog_pages", "Catalog pages must be a bounded list of at most 128 pages.", catalog_path))
        return findings
    summaries = 0
    document_paths: set[str] = set()
    protected = [record["name"] for record in _protected_records(campaign / "knowledge_boundaries.md") if not any(record.get("status", "").casefold().startswith(value) for value in ("revealed", "pc-known", "player-known", "confirmed"))]
    for page_ref in pages:
        if not isinstance(page_ref, dict) or set(page_ref) != {"path", "count"}:
            findings.append(_finding("error", "world_voices_catalog_page_ref", "Each catalog page reference needs only path and count.", catalog_path))
            continue
        page_path = _safe_relative(root, page_ref.get("path"), prefix="assets/world_voices/pages/", findings=findings, label="page.path")
        if page_path is None or not page_path.is_file():
            continue
        page = _load(page_path, findings)
        if not isinstance(page, dict):
            continue
        _walk_private_keys(page, "page", findings)
        if set(page) != PROJECTION_PAGE_KEYS or page.get("page_version") != 1:
            findings.append(_finding("error", "world_voices_page_contract", "Projection page has unsupported fields or version.", page_path))
        documents = page.get("documents")
        if not isinstance(documents, list) or len(documents) > 50 or page_ref.get("count") != len(documents):
            findings.append(_finding("error", "world_voices_page_size", "Projection page count is invalid.", page_path))
            continue
        summaries += len(documents)
        for summary in documents:
            if not isinstance(summary, dict) or set(summary) != PROJECTION_SUMMARY_KEYS:
                findings.append(_finding("error", "world_voices_summary_contract", "Document summary contains unsupported fields.", page_path))
                continue
            _walk_private_keys(summary, "summary", findings)
            doc_path = summary.get("path")
            if doc_path in document_paths:
                findings.append(_finding("error", "world_voices_projection_duplicate", "Player projection contains a duplicate document path.", page_path))
            document_paths.add(str(doc_path))
            if full:
                resolved = _safe_relative(root, doc_path, prefix="assets/world_voices/documents/", findings=findings, label="document.path")
                if resolved is not None and resolved.is_file():
                    document = _load(resolved, findings)
                    if isinstance(document, dict):
                        _walk_private_keys(document, "document", findings)
                        if set(document) != PROJECTION_DOCUMENT_KEYS or document.get("document_version") != 1:
                            findings.append(_finding("error", "world_voices_document_contract", "Player document contains unsupported fields or version.", resolved))
                        for name in protected:
                            if any(isinstance(value, str) and re.search(rf"(?<!\w){re.escape(name)}(?!\w)", value, re.IGNORECASE) for value in document.values()):
                                findings.append(_finding("error", "world_voices_projection_protected_name", "Player document contains an unrevealed protected name.", resolved))
    if catalog.get("visible_count") != summaries:
        findings.append(_finding("error", "world_voices_catalog_count", "Catalog visible_count must equal its player-safe summaries.", catalog_path))
    return findings


def validate_projection_file(campaign: Path, relative_path: str) -> dict[str, Any]:
    """Validate one browser-requested projection file without scanning archive bodies."""
    campaign = campaign.resolve()
    dashboard = campaign / "dashboard"
    findings: list[dict] = []
    resolved = _safe_relative(
        dashboard,
        relative_path,
        prefix="assets/world_voices/",
        findings=findings,
        label="projection request",
    )
    if resolved is not None and resolved.is_file():
        value = _load(resolved, findings)
        if isinstance(value, dict):
            _walk_private_keys(value, "projection", findings)
            normalized = resolved.relative_to(dashboard).as_posix()
            if normalized.endswith("/catalog.json"):
                if set(value) != PROJECTION_CATALOG_KEYS or value.get("projection_version") != 1:
                    findings.append(_finding("error", "world_voices_catalog_contract", "Requested catalog has an invalid contract.", resolved))
                elif isinstance(value.get("pages"), list):
                    for reference in value["pages"]:
                        if not isinstance(reference, dict) or set(reference) != {"path", "count"}:
                            findings.append(_finding("error", "world_voices_catalog_page_ref", "Requested catalog has an invalid page reference.", resolved))
                        else:
                            _safe_relative(dashboard, reference.get("path"), prefix="assets/world_voices/pages/", findings=findings, label="catalog page")
            elif "/pages/" in normalized:
                if set(value) != PROJECTION_PAGE_KEYS or value.get("page_version") != 1 or not isinstance(value.get("documents"), list) or len(value["documents"]) > 50:
                    findings.append(_finding("error", "world_voices_page_contract", "Requested projection page has an invalid contract.", resolved))
                elif isinstance(value.get("documents"), list):
                    for summary in value["documents"]:
                        if not isinstance(summary, dict) or set(summary) != PROJECTION_SUMMARY_KEYS:
                            findings.append(_finding("error", "world_voices_summary_contract", "Requested page has an invalid summary.", resolved))
                        else:
                            _safe_relative(dashboard, summary.get("path"), prefix="assets/world_voices/documents/", findings=findings, label="summary document")
            elif "/documents/" in normalized:
                if set(value) != PROJECTION_DOCUMENT_KEYS or value.get("document_version") != 1 or not isinstance(value.get("body_text"), str) or len(value["body_text"]) > 120_000:
                    findings.append(_finding("error", "world_voices_document_contract", "Requested player document has an invalid contract.", resolved))
                for record in _protected_records(campaign / "knowledge_boundaries.md"):
                    if any(record.get("status", "").casefold().startswith(item) for item in ("revealed", "pc-known", "player-known", "confirmed")):
                        continue
                    if any(isinstance(item, str) and re.search(rf"(?<!\w){re.escape(record['name'])}(?!\w)", item, re.IGNORECASE) for item in value.values()):
                        findings.append(_finding("error", "world_voices_projection_protected_name", "Requested player document contains an unrevealed protected name.", resolved))
            else:
                findings.append(_finding("error", "world_voices_projection_path", "Requested file is outside the catalog/page/document contract.", resolved))
    errors = sum(item["severity"] == "error" for item in findings)
    return {"ok": errors == 0, "error_count": errors, "findings": findings}


def check_world_voices(campaign: Path, *, projection: str = "full") -> dict[str, Any]:
    campaign = campaign.resolve()
    findings, manifest = validate_manifest(campaign)
    if projection != "none":
        findings.extend(validate_projection(campaign, full=projection == "full"))
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    return {
        "ok": errors == 0,
        "campaign_path": str(campaign),
        "enabled_memory_present": manifest is not None,
        "error_count": errors,
        "warning_count": warnings,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", nargs="?", default="campaign")
    parser.add_argument("--projection", choices=("none", "index", "full"), default="full")
    args = parser.parse_args(argv)
    result = check_world_voices(Path(args.campaign), projection=args.projection)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
