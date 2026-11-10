"""Structural checks for the Claude Code host layer.

Claude Code itself is not started here. These tests tie the bundled host
configuration to the contracts it adapts, so neither side can drift silently.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Callable

import pytest

from file_transaction import TRANSACTION_DIR
from verify_workspace import REQUIRED_FILES, _check_claude_code_layer, distribution_path_allowed

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / ".claude"
READ_ONLY_TOOLS = {"Glob", "Grep", "Read"}
WEB_TOOLS = {"WebFetch", "WebSearch"}


def _frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert match, path
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, text[match.end() :]


def _tools(fields: dict[str, str]) -> set[str]:
    return {entry.strip() for entry in fields.get("tools", "").split(",") if entry.strip()}


def _text_block_after(text: str, heading: str) -> list[str]:
    section = text[text.index(heading) :]
    block = re.search(r"```text\n(.*?)```", section, re.S)
    assert block, heading
    return [line.strip().rstrip(":") for line in block.group(1).splitlines() if line.strip()]


def _prose_lines(text: str) -> list[str]:
    lines, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced:
            lines.append(line.strip())
    return lines


def _json(relative: str) -> dict:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _agents() -> dict[str, tuple[dict[str, str], str]]:
    return {path.stem: _frontmatter(path) for path in sorted((CLAUDE / "agents").glob("*.md"))}


def _section_headings(text: str) -> set[str]:
    return {line for line in text.splitlines() if line.startswith("## ")}


def test_claude_md_imports_the_shared_contract_and_stays_an_adapter() -> None:
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    # A real import, not a reading instruction or a quoted example.
    assert "@AGENTS.md" in _prose_lines(text)
    # Anthropic recommends keeping each CLAUDE.md under about 200 lines.
    assert len(text.splitlines()) < 200
    shared = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert not _section_headings(text) & _section_headings(shared), "CLAUDE.md must not restate AGENTS.md sections"


def test_claude_md_references_resolve() -> None:
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    paths = re.findall(r"`((?:\.claude|campaign|docs|tools|workflows)/[^`\s<>]*)`", text)
    assert paths
    for relative in paths:
        assert (ROOT / relative).exists(), relative
    launch_names = {item["name"] for item in _json(".claude/launch.json")["configurations"]}
    for name in re.findall(r"`(repog-[a-z-]+)`", text):
        assert name in _agents() or name in launch_names, name


def test_settings_select_the_bundled_style_and_disable_auto_memory() -> None:
    settings = _json(".claude/settings.json")
    styles = {_frontmatter(path)[0]["name"]: _frontmatter(path)[0] for path in (CLAUDE / "output-styles").glob("*.md")}
    assert settings["outputStyle"] in styles
    # The style replaces the software-engineering defaults instead of adding to them.
    assert styles[settings["outputStyle"]]["keep-coding-instructions"] == "false"
    # campaign/ is the only consent-governed memory.
    assert settings["autoMemoryEnabled"] is False


def test_permissions_preapprove_only_helpers_and_campaign_edits() -> None:
    permissions = _json(".claude/settings.json")["permissions"]
    helper = re.compile(r"Bash\((?:python3?|py)(?: -B)? tools/\*\)")
    for rule in permissions["allow"]:
        assert helper.fullmatch(rule) or rule == "Edit(/campaign/**)", rule
    assert f"Edit(/campaign/{TRANSACTION_DIR}/**)" in permissions["deny"]
    assert {"Read(./.env)", "Read(./.env.*)"} <= set(permissions["deny"])


def test_lanes_are_read_only_and_return_the_orchestration_result_shape() -> None:
    orchestration = (ROOT / "workflows" / "orchestration" / "WORKFLOW.md").read_text(encoding="utf-8")
    packet_fields = _text_block_after(orchestration, "# Frozen Task Packet")
    result_fields = _text_block_after(orchestration, "# Supporting-Agent Contract")
    agents = _agents()
    assert set(agents) == {"repog-proposal-lane", "repog-research-lane"}
    for name, (fields, body) in agents.items():
        assert fields["name"] == name
        assert fields["omitClaudeMd"] == "true"
        assert _tools(fields) <= READ_ONLY_TOOLS | WEB_TOOLS
        assert _text_block_after(body, "Return exactly one result") == result_fields
    assert _tools(agents["repog-proposal-lane"][0]) == READ_ONLY_TOOLS
    assert _tools(agents["repog-research-lane"][0]) == READ_ONLY_TOOLS | WEB_TOOLS
    proposal_body = agents["repog-proposal-lane"][1]
    for field in packet_fields:
        assert f"`{field}`" in proposal_body, field


def test_previews_start_the_local_servers_without_auto_verify() -> None:
    launch = _json(".claude/launch.json")
    assert launch["autoVerify"] is False
    assert {item["name"] for item in launch["configurations"]} == {"repog-dashboard", "repog-companion-view"}
    for item in launch["configurations"]:
        script, served, *options = item["runtimeArgs"]
        assert (ROOT / script).is_file() and (ROOT / served).is_dir()
        port = item["port"]
        assert options == ["--port", str(port)]
        default = re.search(r'"--port", type=int, default=(\d+)', (ROOT / script).read_text(encoding="utf-8"))
        assert default and int(default.group(1)) == port
        assert item["autoPort"] is False
        assert item["url"] == f"http://127.0.0.1:{port}"


def test_distribution_ships_shared_claude_files_only() -> None:
    shipped = [relative for relative in REQUIRED_FILES if relative.startswith(".claude/")]
    for directory in ("agents", "output-styles"):
        shipped += [path.relative_to(ROOT).as_posix() for path in sorted((CLAUDE / directory).glob("*.md"))]
    assert "CLAUDE.md" in REQUIRED_FILES
    for relative in ["CLAUDE.md", *shipped]:
        assert distribution_path_allowed(relative), relative
    for relative in (
        "CLAUDE.local.md",
        ".claude/settings.local.json",
        ".claude/worktrees/session/AGENTS.md",
        ".claude/agent-memory/repog-proposal-lane/MEMORY.md",
        ".claude/agent-memory-local/repog-proposal-lane/MEMORY.md",
        ".claude/agents/nested/lane.md",
        ".claude/agents/notes.txt",
        ".claude/skills/example/SKILL.md",
    ):
        assert not distribution_path_allowed(relative), relative
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert {".claude/settings.local.json", ".claude/worktrees/", "CLAUDE.local.md"} <= set(ignored)


def test_runtime_instructions_are_host_neutral() -> None:
    sources = [ROOT / "AGENTS.md", ROOT / "CLAUDE.md"]
    for tree in ("workflows", "briefs", "campaign", ".claude"):
        sources += sorted(path for path in (ROOT / tree).rglob("*") if path.suffix in {".md", ".yaml"})
    for source in sources:
        assert not re.search(r"\bCodex\b", source.read_text(encoding="utf-8")), source.relative_to(ROOT)


def _copy_layer(target: Path) -> Path:
    shutil.copytree(CLAUDE, target / ".claude", ignore=shutil.ignore_patterns("settings.local.json", "worktrees"))
    (target / "tools").mkdir()
    for item in _json(".claude/launch.json")["configurations"]:
        shutil.copy2(ROOT / item["runtimeArgs"][0], target / item["runtimeArgs"][0])
    return target


def _edit_json(relative: str, change: Callable[[dict], None]) -> Callable[[Path], None]:
    def apply(workspace: Path) -> None:
        path = workspace / relative
        value = json.loads(path.read_text(encoding="utf-8"))
        change(value)
        path.write_text(json.dumps(value), encoding="utf-8")

    return apply


def _edit_lane_tools(tools: str) -> Callable[[Path], None]:
    def apply(workspace: Path) -> None:
        path = workspace / ".claude" / "agents" / "repog-proposal-lane.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(re.sub(r"(?m)^tools:.*\n", tools, text), encoding="utf-8")

    return apply


@pytest.mark.parametrize(
    ("rule", "mutate"),
    [
        ("claude_auto_memory_enabled", _edit_json(".claude/settings.json", lambda s: s.update(autoMemoryEnabled=True))),
        ("claude_auto_memory_enabled", _edit_json(".claude/settings.json", lambda s: s.pop("autoMemoryEnabled"))),
        ("claude_output_style_missing", _edit_json(".claude/settings.json", lambda s: s.update(outputStyle="default"))),
        ("claude_preview_autoverify_enabled", _edit_json(".claude/launch.json", lambda s: s.update(autoVerify=True))),
        ("claude_preview_target_missing", lambda w: (w / "tools" / "serve_dashboard.py").unlink()),
        ("claude_config_invalid", lambda w: (w / ".claude" / "settings.json").write_text("{", encoding="utf-8")),
        ("claude_agent_not_read_only", _edit_lane_tools("tools: Read, Grep, Glob, Bash\n")),
        ("claude_agent_not_read_only", _edit_lane_tools("tools: Read, Agent(repog-research-lane)\n")),
        ("claude_agent_tools_missing", _edit_lane_tools("")),
    ],
)
def test_layout_check_flags_claude_layer_drift(tmp_path: Path, rule: str, mutate: Callable[[Path], None]) -> None:
    workspace = _copy_layer(tmp_path)
    assert _check_claude_code_layer(workspace) == []
    mutate(workspace)
    findings = _check_claude_code_layer(workspace)
    assert rule in {item["rule"] for item in findings}
    assert {item["check"] for item in findings} == {"layout"}


def test_layout_check_leaves_designer_agents_alone(tmp_path: Path) -> None:
    workspace = _copy_layer(tmp_path)
    (workspace / ".claude" / "agents" / "designer-helper.md").write_text(
        "---\nname: designer-helper\ndescription: A maintainer's own agent.\ntools: Read, Edit, Bash\n---\n\nHelp.\n",
        encoding="utf-8",
    )
    assert _check_claude_code_layer(workspace) == []
