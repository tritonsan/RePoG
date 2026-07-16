"""Verify a clean RePoG player workspace using only the Python standard library.

This is the single public smoke-check entry point.  It checks the distributable
layout, parses every bundled Python helper, runs the campaign validator, and
validates the optional dashboard state.  It does not modify campaign files.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


REQUIRED_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "OPEN_CAMPAIGN.md",
    "README.md",
    "START_HERE.md",
    "LICENSE",
    "campaign/setup_profile.yaml",
    "campaign/play_profile.yaml",
    "campaign/current_state.yaml",
    "campaign/visual_state.json",
    "campaign/dashboard/dashboard_state.json",
    "campaign/dashboard/index.html",
    "tools/check_state.py",
    "tools/check_dashboard.py",
    "tools/resolve_mechanic.py",
    "tools/roll_dice.py",
    "tools/serve_dashboard.py",
    "tools/update_dashboard.py",
    "tools/visual_handoff.py",
    "workflows/audit/WORKFLOW.md",
    "workflows/distill/WORKFLOW.md",
    "workflows/gm/WORKFLOW.md",
    "workflows/worldbuild/WORKFLOW.md",
)

REQUIRED_DIRS = (
    "briefs",
    "briefs/lenses",
    "campaign",
    "campaign/dashboard",
    "docs",
    "tools",
    "workflows",
)

REQUIRED_LENSES = ("INDEX.md", "fantasy.md", "realistic.md", "cyberpunk.md", "survival.md")


def _finding(
    severity: str,
    rule: str,
    message: str,
    path: Path | str | None = None,
    *,
    check: str,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "rule": rule,
        "message": message,
        "path": str(path) if path is not None else None,
        "check": check,
    }


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalise_findings(items: Any, *, check: str) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return [
            _finding(
                "error",
                "invalid_check_result",
                "A bundled checker returned findings in an unsupported format.",
                check=check,
            )
        ]
    normalised: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            normalised.append(
                _finding(
                    "error",
                    "invalid_check_finding",
                    "A bundled checker returned a non-object finding.",
                    check=check,
                )
            )
            continue
        normalised.append(
            {
                "severity": str(item.get("severity", "error")),
                "rule": str(item.get("rule", "unknown")),
                "message": str(item.get("message", "")),
                "path": item.get("path"),
                "check": check,
            }
        )
    return normalised


def _check_layout(workspace: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for relative in REQUIRED_FILES:
        path = workspace / relative
        if not path.is_file():
            findings.append(
                _finding("error", "workspace_file_missing", f"Missing workspace file: {relative}", path, check="layout")
            )
    for relative in REQUIRED_DIRS:
        path = workspace / relative
        if not path.is_dir():
            findings.append(
                _finding("error", "workspace_directory_missing", f"Missing workspace directory: {relative}", path, check="layout")
            )
    for filename in REQUIRED_LENSES:
        path = workspace / "briefs" / "lenses" / filename
        if not path.is_file():
            findings.append(
                _finding("error", "lens_brief_missing", f"Missing bundled lens brief: {filename}", path, check="layout")
            )
    return findings


def _check_python_sources(workspace: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    tools_dir = workspace / "tools"
    if not tools_dir.is_dir():
        return findings
    for path in sorted(tools_dir.glob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            findings.append(_finding("error", "python_source_invalid", str(exc), path, check="python"))
    return findings


def _campaign_check(workspace: Path, campaign: Path, scope: str) -> list[dict[str, Any]]:
    check_path = workspace / "tools" / "check_state.py"
    if not check_path.is_file():
        return []
    try:
        module = _load_module("repog_verify_check_state", check_path)
        result = module.check_campaign(campaign, scope=scope)
    except Exception as exc:  # A broken public checker is itself a verification failure.
        return [_finding("error", "campaign_check_failed", str(exc), check_path, check="campaign")]
    if not isinstance(result, dict):
        return [_finding("error", "campaign_check_invalid", "Campaign checker returned a non-object result.", check_path, check="campaign")]
    return _normalise_findings(result.get("findings"), check="campaign")


def _dashboard_check(workspace: Path, campaign: Path) -> list[dict[str, Any]]:
    check_path = workspace / "tools" / "check_dashboard.py"
    state_path = campaign / "dashboard" / "dashboard_state.json"
    if not check_path.is_file() or not state_path.is_file():
        return []
    try:
        module = _load_module("repog_verify_check_dashboard", check_path)
        result = module.check_dashboard(state_path, campaign_path=campaign)
    except Exception as exc:
        return [_finding("error", "dashboard_check_failed", str(exc), check_path, check="dashboard")]
    if not isinstance(result, dict):
        return [_finding("error", "dashboard_check_invalid", "Dashboard checker returned a non-object result.", check_path, check="dashboard")]
    return _normalise_findings(result.get("findings"), check="dashboard")


def verify_workspace(workspace: Path, *, campaign: Path | None = None, scope: str = "full") -> dict[str, Any]:
    """Return a structured, read-only verification report."""

    workspace = workspace.resolve()
    campaign_path = (campaign or workspace / "campaign").resolve()
    grouped = {
        "layout": _check_layout(workspace),
        "python": _check_python_sources(workspace),
        "campaign": _campaign_check(workspace, campaign_path, scope),
        "dashboard": _dashboard_check(workspace, campaign_path),
    }
    checks: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for check_id, check_findings in grouped.items():
        findings.extend(check_findings)
        errors = sum(item["severity"] == "error" for item in check_findings)
        warnings = sum(item["severity"] == "warning" for item in check_findings)
        infos = sum(item["severity"] == "info" for item in check_findings)
        checks.append(
            {
                "id": check_id,
                "ok": errors == 0,
                "error_count": errors,
                "warning_count": warnings,
                "info_count": infos,
            }
        )
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    infos = sum(item["severity"] == "info" for item in findings)
    return {
        "ok": errors == 0,
        "workspace_path": str(workspace),
        "campaign_path": str(campaign_path),
        "scope": scope,
        "error_count": errors,
        "warning_count": warnings,
        "info_count": infos,
        "checks": checks,
        "findings": findings,
    }


def _print_human(result: dict[str, Any]) -> None:
    print("RePoG workspace verification")
    print(f"Workspace: {result['workspace_path']}")
    for check in result["checks"]:
        status = "PASS" if check["ok"] else "FAIL"
        detail = f"{check['error_count']} errors, {check['warning_count']} warnings"
        print(f"[{status}] {check['id']}: {detail}")
    for item in result["findings"]:
        severity = str(item["severity"]).upper()
        location = f" ({item['path']})" if item.get("path") else ""
        print(f"- {severity} [{item['check']}/{item['rule']}] {item['message']}{location}")
    print(
        f"Result: {'PASS' if result['ok'] else 'FAIL'} "
        f"({result['error_count']} errors, {result['warning_count']} warnings, {result['info_count']} info)"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "workspace",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1]),
        help="Workspace root. Defaults to the parent of this tools directory.",
    )
    parser.add_argument("--campaign", help="Campaign directory. Defaults to <workspace>/campaign.")
    parser.add_argument("--scope", choices=("hot", "full"), default="full")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of the human summary.")
    args = parser.parse_args(argv)
    result = verify_workspace(
        Path(args.workspace),
        campaign=Path(args.campaign) if args.campaign else None,
        scope=args.scope,
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        _print_human(result)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
