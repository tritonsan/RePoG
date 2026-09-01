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


def _safe_extract(archive: zipfile.ZipFile, target: Path) -> None:
    root = target.resolve()
    for member in archive.infolist():
        destination = (target / member.filename).resolve()
        if root != destination and root not in destination.parents:
            raise RuntimeError("workspace_archive_invalid")
    archive.extractall(target)


def initialize_workspace(bucket: str, session_id: str) -> None:
    boto3.client("s3").copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": "golden/workspace.zip"}, Key=f"sessions/{session_id}/workspace.zip", MetadataDirective="COPY")


def apply(bucket: str, session_id: str, persistence: dict[str, Any]) -> None:
    mode = persistence.get("mode", "none")
    if mode == "none":
        return
    command = {"durable": "commit-durable", "checkpoint": "commit-checkpoint"}.get(str(mode))
    if not command:
        raise RuntimeError("persistence_mode_invalid")
    client = boto3.client("s3")
    source = client.get_object(Bucket=bucket, Key=f"sessions/{session_id}/workspace.zip")["Body"].read()
    with tempfile.TemporaryDirectory(prefix="repog-") as temporary:
        workspace = Path(temporary) / "workspace"
        workspace.mkdir()
        with zipfile.ZipFile(io.BytesIO(source)) as archive:
            _safe_extract(archive, workspace)
        tool = workspace / "tools" / "rpg_state.py"
        campaign = workspace / "campaign"
        result = subprocess.run([os.environ.get("PYTHON_EXECUTABLE", "python"), str(tool), str(campaign), command, "--input-json", json.dumps(persistence.get("request", {}))], cwd=workspace, capture_output=True, text=True, timeout=60, check=False)
        if result.returncode != 0:
            raise RuntimeError("durable_commit_failed")
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in workspace.rglob("*"):
                if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts:
                    archive.write(path, path.relative_to(workspace).as_posix())
        client.put_object(Bucket=bucket, Key=f"sessions/{session_id}/workspace.zip", Body=output.getvalue(), ServerSideEncryption="AES256", Metadata={"commit-mode": str(mode)})
