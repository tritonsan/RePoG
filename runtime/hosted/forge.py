from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import boto3
from jsonschema import Draft202012Validator

from .model import MODEL_ID, client
from .persistence import _safe_extract
from .budget import Usage, estimate_micro_usd

ALLOWED_PREFIXES = ("campaign/",)
CONTEXT_FILES = (
    "AGENTS.md", "workflows/worldbuild/WORKFLOW.md",
    "workflows/worldbuild/playbooks/rpg_quick.md", "workflows/worldbuild/playbooks/finalization.md",
    "campaign/session_zero.yaml", "campaign/current_state.yaml", "campaign/play_profile.yaml",
    "campaign/agent_roster.json", "campaign/agent_seat_state.json",
)


def _pack(workspace: Path) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in workspace.rglob("*"):
            if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts:
                archive.write(path, path.relative_to(workspace).as_posix())
    return output.getvalue()


def quick_forge(bucket: str, session_id: str, prompt: str) -> dict[str, Any]:
    s3 = boto3.client("s3")
    source = s3.get_object(Bucket=bucket, Key=f"sessions/{session_id}/workspace.zip")["Body"].read()
    with tempfile.TemporaryDirectory(prefix="repog-forge-") as temporary:
        workspace = Path(temporary) / "workspace"
        workspace.mkdir()
        with zipfile.ZipFile(io.BytesIO(source)) as archive:
            _safe_extract(archive, workspace)
        context: dict[str, str] = {}
        for relative in CONTEXT_FILES:
            path = workspace / relative
            if path.exists():
                context[relative] = path.read_text(encoding="utf-8")[:18_000]
        response = client().responses.create(
            model=MODEL_ID,
            store=False,
            max_output_tokens=6000,
            input=[
                {"role": "developer", "content": "Create a playable RePoG Quick campaign by editing only campaign/ files. Follow the supplied workflow exactly. WebMCP opt-in is already explicit: configure exactly one Tier 3 companion as the ready Agent Seat. Return complete replacement file contents, never patches, and never write outside campaign/. The result must pass tools/check_state.py campaign --scope full."},
                {"role": "user", "content": json.dumps({"request": prompt, "files": context}, ensure_ascii=False)},
            ],
            text={"format": {"type": "json_schema", "name": "repog_quick_forge", "strict": True, "schema": {
                "type": "object", "additionalProperties": False, "required": ["files", "summary", "manifest", "initial_turn"],
                "properties": {"summary": {"type": "string", "maxLength": 1000}, "manifest": {"type": "object", "additionalProperties": True}, "initial_turn": {"type": "object", "additionalProperties": True}, "files": {"type": "array", "minItems": 1, "maxItems": 30, "items": {"type": "object", "additionalProperties": False, "required": ["path", "content"], "properties": {"path": {"type": "string", "maxLength": 180}, "content": {"type": "string", "maxLength": 50000}}}}},
            }}},
        )
        result = json.loads(response.output_text)
        for item in result["files"]:
            relative = str(item["path"]).replace("\\", "/")
            if not relative.startswith(ALLOWED_PREFIXES) or ".." in Path(relative).parts:
                raise RuntimeError("forge_path_forbidden")
            destination = (workspace / relative).resolve()
            if workspace.resolve() not in destination.parents:
                raise RuntimeError("forge_path_forbidden")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(str(item["content"]), encoding="utf-8")
        check = subprocess.run([os.environ.get("PYTHON_EXECUTABLE", "python"), str(workspace / "tools" / "check_state.py"), str(workspace / "campaign"), "--scope", "full"], cwd=workspace, capture_output=True, text=True, timeout=60, check=False)
        if check.returncode != 0:
            raise RuntimeError("quick_forge_validation_failed")
        contract_root = workspace / "contracts" / "agent-seat" / "v1"
        for value, schema_name in ((result["manifest"], "agent-session-pack.schema.json"), (result["initial_turn"], "agent-turn-brief.schema.json")):
            schema = json.loads((contract_root / schema_name).read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema).iter_errors(value))
            if errors:
                raise RuntimeError("quick_forge_agent_contract_invalid")
        s3.put_object(Bucket=bucket, Key=f"sessions/{session_id}/workspace.zip", Body=_pack(workspace), ServerSideEncryption="AES256", Metadata={"forge": "quick-validated"})
        usage = getattr(response, "usage", None)
        actual = estimate_micro_usd(Usage(
            input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            cached_input_tokens=int(getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        ))
        return {"ok": True, "status": "ready", "summary": result["summary"], "_actual_micro_usd": actual, "_manifest": result["manifest"], "_initial_turn": result["initial_turn"]}
