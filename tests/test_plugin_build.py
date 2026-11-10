"""The Claude Code plugin build and its plugin-only helpers.

Claude Code itself is not started here. The shell checks run where `sh` is
available, and `claude plugin validate` runs only where the CLI is installed.
"""
from __future__ import annotations

import hashlib
import http.client
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

import build_plugin
from verify_workspace import distribution_path_allowed

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "plugin"
SH = shutil.which("sh")


def _load_campaign_helper():
    spec = importlib.util.spec_from_file_location("repog_plugin_campaign", OVERLAY / "tools" / "plugin_campaign.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plugin_campaign = _load_campaign_helper()


def _files(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def _canonical(tree: str) -> dict[str, bytes]:
    return {
        f"{tree}/{relative}": data
        for relative, data in _files(ROOT / tree).items()
        if distribution_path_allowed(f"{tree}/{relative}")
    }


def _frontmatter(path: Path) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    assert match, path
    return {key.strip(): value.strip() for key, _, value in (line.partition(":") for line in match.group(1).splitlines())}


@pytest.fixture(scope="module")
def plugin(tmp_path_factory: pytest.TempPathFactory) -> Path:
    target = tmp_path_factory.mktemp("plugin") / "repog"
    result = build_plugin.build(ROOT, target, worktree=True)
    assert result["ok"] and result["file_count"] == len(_files(target))
    return target


def _sh(script: Path, *args: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    assert SH is not None
    return subprocess.run(
        [SH, str(script), *args],
        cwd=cwd,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _carried(plugin_relative: str, data: bytes) -> bytes:
    """What the plugin holds for a canonical file: the bytes, minus any trimmed passage."""

    return build_plugin.trim_file(plugin_relative, data) if plugin_relative in build_plugin.TRIMS else data


def test_plugin_carries_the_workspace_engine_unchanged(plugin: Path) -> None:
    built = _files(plugin)
    for tree in ("workflows", "briefs", "contracts", "evaluation", "docs", "tools"):
        canonical = _canonical(tree)
        assert canonical, tree
        for relative, data in canonical.items():
            if build_plugin.omitted(relative):
                assert relative not in built, relative
            else:
                assert built.get(relative) == _carried(relative, data), relative
    template = {relative.removeprefix("templates/"): data for relative, data in built.items() if relative.startswith("templates/")}
    assert template == {
        relative: _carried(f"templates/{relative}", data)
        for relative, data in _canonical("campaign").items()
        if not build_plugin.omitted(relative)
    }
    for directory in ("agents", "output-styles"):
        for source in (ROOT / ".claude" / directory).glob("*.md"):
            assert built[f"{directory}/{source.name}"] == source.read_bytes()
    for relative in ("AGENTS.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
        assert built[relative] == (ROOT / relative).read_bytes()
    for relative in ("CLAUDE.md", "START_HERE.md", "OPEN_CAMPAIGN.md", "DISTRIBUTION.md", ".claude", "assets", "campaign"):
        assert not (plugin / relative).exists(), relative


def test_play_skill_embeds_the_shared_contract(plugin: Path) -> None:
    skill = plugin / "skills" / "play" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert (ROOT / "AGENTS.md").read_text(encoding="utf-8").strip("\n") in text
    assert build_plugin.INCLUDE_MARKER not in text
    assert (OVERLAY / "skills" / "play" / "SKILL.md").read_text(encoding="utf-8").count(build_plugin.INCLUDE_MARKER) == 1
    assert _frontmatter(skill)["name"] == "play"
    for reference in build_plugin.ROOT_REFERENCE.findall(text):
        assert (plugin / reference).is_file(), reference


@pytest.mark.xfail(
    strict=True,
    reason="The plugin is maintained as its own project since 0.2.0; this overlay is "
    "frozen at 0.1.1 and its skill no longer fits beside the current AGENTS.md.",
)
def test_play_skill_fits_the_compaction_reattach_budget(plugin: Path) -> None:
    # Claude Code re-attaches only the first 5,000 tokens of an invoked skill
    # after compaction, so the whole contract has to fit well inside that.
    skill = plugin / "skills" / "play" / "SKILL.md"
    assert len(skill.read_bytes()) < 19000


def test_plugin_meets_the_directory_limits(plugin: Path) -> None:
    built = _files(plugin)
    assert build_plugin.check(built) == []
    assert len(built) <= build_plugin.MAX_FILES
    assert all(b"\r\n" not in data for relative, data in built.items() if relative.endswith(".sh"))
    manifest = json.loads(built[".claude-plugin/plugin.json"])
    marketplace = json.loads(built[".claude-plugin/marketplace.json"])
    assert manifest["name"] == marketplace["name"] == marketplace["plugins"][0]["name"] == "repog"
    assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])
    assert manifest["license"] == "Apache-2.0"
    assert b"Apache License" in built["LICENSE"][:200]


def _mutated(built: dict[str, bytes], change) -> list[str]:
    plan = dict(built)
    change(plan)
    return build_plugin.check(plan)


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (lambda plan: plan.update({"CLAUDE.md": b"# Notes\n"}), "CLAUDE.md"),
        (lambda plan: plan.update({"bin/repog": b"#!/bin/sh\n"}), "bin/"),
        (lambda plan: plan.update({"docs/.DS_Store": b"x"}), "operating-system file"),
        (lambda plan: plan.update({"docs/con.md": b"x"}), "not valid on Windows"),
        (lambda plan: plan.update({"docs/Readme.md": b"x", "docs/README.MD": b"y"}), "differ only by case"),
        (lambda plan: plan.update({"tools/big.json": b"x" * build_plugin.MAX_TEXT_BYTES}), "byte limit"),
        (lambda plan: plan.update({"tools/cache.pyc": b"x"}), "compiled Python"),
        (lambda plan: plan.pop("scripts/repog.sh"), "scripts/repog.sh"),
        (lambda plan: plan.update({"README.md": b"# RePoG\n\nToo short.\n"}), "40 words"),
        (lambda plan: plan.update({"skills/extra/SKILL.md": b"---\nname: extra\n---\n\nNo description.\n"}), "frontmatter"),
        (lambda plan: plan.update({"skills/extra/SKILL.md": b"---\nname: extra\ndescription: x\n---\n\nRun ${CLAUDE_PLUGIN_ROOT}/scripts/missing.sh\n"}), "missing scripts/missing.sh"),
        (lambda plan: plan.update({"docs/extra.md": b"Run tools/visual_handoff.py first.\n"}), "still mentions omitted tools/visual_handoff.py"),
    ],
)
def test_directory_check_flags_problems(plugin: Path, change, expected: str) -> None:
    problems = _mutated(_files(plugin), change)
    assert any(expected in problem for problem in problems), problems


def test_marketplace_must_name_this_plugin(plugin: Path) -> None:
    def rename(plan: dict[str, bytes]) -> None:
        marketplace = json.loads(plan[".claude-plugin/marketplace.json"])
        marketplace["plugins"][0]["name"] = "other"
        plan[".claude-plugin/marketplace.json"] = json.dumps(marketplace).encode("utf-8")

    assert any("exactly this plugin" in problem for problem in _mutated(_files(plugin), rename))


def _words(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_plugin_leaves_out_what_claude_code_cannot_use(plugin: Path) -> None:
    built = _files(plugin)
    for entry in build_plugin.OMITTED:
        source = ROOT / entry
        assert source.is_file() or (entry.endswith("/") and any(path.is_file() for path in source.rglob("*"))), (
            f"{entry} is listed as omitted but no longer exists"
        )
    assert not [relative for relative in built if build_plugin.omitted(relative)]
    for destination in build_plugin.TRIMS:
        assert destination in built, destination
    for relative, data in built.items():
        if Path(relative).suffix in build_plugin.DOCUMENT_SUFFIXES:
            assert b"visual_handoff" not in data, relative
    play = _words(plugin / "skills" / "play" / "SKILL.md")
    for statement in ("Claude cannot generate images", "visuals.mode", "visuals.companion_view", "07_agent_seats"):
        assert statement in play, statement
    assert "independent reads in one message" in play
    # The plugin README tells the user what is left out, and the helper launcher cannot start it.
    readme = _words(plugin / "README.md")
    assert "Left out:" in readme and "Companion View" in readme and "agent seats" in readme
    assert not any((plugin / "tools" / f"{name}.py").exists() for name in ("visual_handoff", "agent_seat", "verify_workspace"))


_IMPORT_ALL = """
import importlib.util, sys
from pathlib import Path
tools = Path(sys.argv[1])
sys.path.insert(0, str(tools))
failed = []
for path in sorted(tools.glob("*.py")):
    spec = importlib.util.spec_from_file_location("plugin_tool_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve a class through its module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        failed.append(path.name + ": " + type(exc).__name__ + ": " + str(exc))
print(*failed, sep=chr(10))
"""

_VIEW_PROBE = """
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import check_companion
findings = []
with tempfile.TemporaryDirectory() as scratch:
    check_companion._validate_companion_view(Path(scratch), ready=False, draft_preflight=False, policy=sys.argv[2], state={}, findings=findings)
print(json.dumps([item["rule"] for item in findings]))
"""


def _python(code: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-B", "-c", code, *args], capture_output=True, text=True, encoding="utf-8", check=False)


def test_every_plugin_helper_imports_without_the_omitted_layers(plugin: Path) -> None:
    result = _python(_IMPORT_ALL, str(plugin / "tools"))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ""


def test_companion_view_check_is_optional_only_when_the_layer_is_left_out(plugin: Path) -> None:
    def rules(tools: Path, policy: str) -> list[str]:
        result = _python(_VIEW_PROBE, str(tools), policy)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    assert not (plugin / "tools" / "check_companion_view.py").exists()
    assert rules(plugin / "tools", "off") == []
    assert rules(plugin / "tools", "light") == ["companion_view_checker_missing"]
    # A workspace that carries the layer keeps its strictness when the folder goes missing.
    assert rules(ROOT / "tools", "off") == ["companion_view_state_missing"]


def test_dashboard_serves_without_the_agent_seat_layer(plugin: Path, tmp_path: Path) -> None:
    plugin_campaign.init_campaign(tmp_path, template=plugin / "templates" / "campaign")
    dashboard = tmp_path / "campaign" / "dashboard"
    assert not (plugin / "tools" / "agent_seat.py").exists()
    assert not (dashboard / "agent-table.js").exists() and "agent-table" not in (dashboard / "index.html").read_text(encoding="utf-8")

    script = plugin / "tools" / "serve_dashboard.py"
    checked = subprocess.run([sys.executable, "-B", str(script), str(dashboard), "--check-only"], capture_output=True, text=True, encoding="utf-8", check=False)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert json.loads(checked.stdout)["ok"] is True and "agent_seat" not in json.loads(checked.stdout)

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = subprocess.Popen([sys.executable, "-B", str(script), str(dashboard), "--port", str(port)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        assert server.stdout is not None and json.loads(server.stdout.readline())["ok"] is True

        def request(method: str, path: str, body: str | None = None) -> tuple[int, str]:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            headers = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{port}"} if body else {}
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            payload = response.read().decode("utf-8", "replace")
            connection.close()
            return response.status, payload

        assert request("GET", "/")[0] == 200
        for method, path, body in (("GET", "/api/seat/context", None), ("GET", "/api/seat/next-turn", None), ("POST", "/api/seat/turn", "{}")):
            status, payload = request(method, path, body)
            assert status == 404 and json.loads(payload)["failure_category"] == "route_missing", (method, path, status, payload)
    finally:
        server.terminate()
        server.wait(timeout=10)


def test_plugin_states_adult_use_and_model_safety(plugin: Path) -> None:
    manifest = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads((plugin / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert "18+" in manifest["description"] and "18+" in marketplace["plugins"][0]["description"]
    for document in (plugin / "README.md", plugin / "skills" / "play" / "SKILL.md", plugin / "skills" / "new" / "SKILL.md"):
        text = _words(document)
        assert "18 or older" in text, document
        assert "safety policies" in text, document
    assert "never obliges Claude" in _words(plugin / "skills" / "play" / "SKILL.md")


def test_play_skill_keeps_turns_lean(plugin: Path) -> None:
    # A measured live session spent most of each turn writing scripts, payloads,
    # and per-turn style checks. The skill has to keep those rules in the text
    # that Claude Code re-attaches after compaction.
    play = _words(plugin / "skills" / "play" / "SKILL.md")
    for statement in (
        "A soft turn",
        "writes and runs nothing",
        "one Bash call that builds the payload and commits it",
        "`boundary: ordinary`",
        "short anchor: last speaker, open question, who has control",
        "update `active_cast.md` in that same commit",
        "Run `check_style` only at a full distill",
        "never per turn",
        "never after a `cd` into a scratch folder",
        "in the Player's language without backend terms",
    ):
        assert statement in play, statement
    readme = _words(plugin / "README.md")
    assert "CLAUDE_CODE_EFFORT_LEVEL" in readme and "overrides" in readme


def test_trim_line_and_paragraph_keep_every_other_byte() -> None:
    text = "# Top\r\n\r\nKeep one.\n\r\nDrop me\r\nstill part of it\r\n\r\nKeep two.\r\n- item a\r\n- item b\r\n"
    assert build_plugin._drop_paragraph(text, "Drop me") == "# Top\r\n\r\nKeep one.\n\r\nKeep two.\r\n- item a\r\n- item b\r\n"
    assert build_plugin._drop_line(text, "item a") == text.replace("- item a\r\n", "")
    assert build_plugin._drop_paragraph("Keep.\n\nLast one.\n", "Last") == "Keep.\n"
    # A rewritten paragraph takes the line ending of the one it replaces.
    assert build_plugin._rewrite_paragraph(text, "Drop me", "New one\nNew two.") == (
        "# Top\r\n\r\nKeep one.\n\r\nNew one\r\nNew two.\r\n\r\nKeep two.\r\n- item a\r\n- item b\r\n"
    )


def test_trim_item_takes_its_continuation_lines_and_keeps_its_neighbours() -> None:
    packed = "- keep\n- drop this\n  and its second line\n- keep too\n\nafter\n"
    assert build_plugin._drop_item(packed, "drop this") == "- keep\n- keep too\n\nafter\n"
    spaced = "- keep\n\n- drop this\n  more\n\n- keep too\n"
    assert build_plugin._drop_item(spaced, "drop this") == "- keep\n\n- keep too\n"
    assert build_plugin._drop_item("- only\n", "only") == ""


def test_trim_section_ends_at_the_next_heading_and_skips_code_fences() -> None:
    text = "# A\n\nintro\n\n## Drop\n\nbody\n\n```\n# not a heading\n```\n\n## Next\n\ntail\n"
    assert build_plugin._drop_section(text, "## Drop") == "# A\n\nintro\n\n## Next\n\ntail\n"
    assert build_plugin._drop_section("# A\n\nintro\n\n## Drop\n\nbody\n", "## Drop") == "# A\n\nintro\n"
    assert build_plugin._drop_section("# A\n\n## Drop\n\n# B\n", "## Drop") == "# A\n\n# B\n"


def test_trim_text_ignores_wrapping() -> None:
    text = "Keep this sentence. The visual handoff\r\ntool runs here. Keep that.\r\n"
    assert build_plugin._replace_text(text, "The visual handoff tool runs here.", "") == "Keep this sentence. Keep that.\r\n"
    assert build_plugin._replace_text("a b\r\nc d", "b c", "X") == "a X d"


@pytest.mark.parametrize(
    ("operation", "arguments"),
    [
        (build_plugin._drop_line, ("x",)),
        (build_plugin._drop_item, ("x",)),
        (build_plugin._drop_paragraph, ("x",)),
        (build_plugin._rewrite_paragraph, ("x", "y")),
        (build_plugin._drop_section, ("x",)),
        (build_plugin._replace_text, ("x", "")),
    ],
)
def test_trim_anchor_must_match_exactly_once(operation, arguments) -> None:
    for text in ("nothing here\n", "x\n\nx\n"):
        with pytest.raises(build_plugin.PluginBuildError, match="exactly once"):
            operation(text, *arguments)


def test_archive_holds_the_plugin_with_its_manifest_at_the_root(tmp_path: Path) -> None:
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    result = build_plugin.build(ROOT, tmp_path / "first", worktree=True, archive=first)
    build_plugin.build(ROOT, tmp_path / "second", worktree=True, archive=second)
    assert result["archive"] == str(first.resolve())
    with zipfile.ZipFile(first) as bundle:
        names = bundle.namelist()
        assert ".claude-plugin/plugin.json" in names and names == sorted(names)
        assert {name: bundle.read(name) for name in names} == _files(tmp_path / "first")
        assert bundle.testzip() is None
    # The same files always give the same bytes.
    assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()


def test_archive_refuses_an_existing_file_or_a_place_inside_the_plugin(tmp_path: Path) -> None:
    taken = tmp_path / "taken.zip"
    taken.write_bytes(b"not mine")
    with pytest.raises(build_plugin.PluginBuildError, match="Archive already exists"):
        build_plugin.build(ROOT, tmp_path / "a", worktree=True, archive=taken)
    with pytest.raises(build_plugin.PluginBuildError, match="inside the plugin folder"):
        build_plugin.build(ROOT, tmp_path / "b", worktree=True, archive=tmp_path / "b" / "repog.zip")
    assert taken.read_bytes() == b"not mine"
    assert not (tmp_path / "a").exists() and not (tmp_path / "b").exists()


def test_build_refuses_an_existing_target(tmp_path: Path) -> None:
    with pytest.raises(build_plugin.PluginBuildError, match="already exists"):
        build_plugin.build(ROOT, tmp_path, worktree=True)


def test_plugin_sources_stay_out_of_the_player_package() -> None:
    for relative in ("plugin/skills/play/SKILL.md", "plugin/.claude-plugin/plugin.json", "plugin/tools/plugin_campaign.py"):
        assert not distribution_path_allowed(relative), relative
    assert distribution_path_allowed("tools/build_plugin.py")


def test_committed_head_builds_when_it_holds_the_overlay(tmp_path: Path) -> None:
    listed = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", "HEAD", "plugin"], capture_output=True, text=True, check=False)
    if listed.returncode != 0 or not listed.stdout.strip():
        pytest.skip("HEAD does not contain the plugin overlay yet")
    result = build_plugin.build(ROOT, tmp_path / "repog", dry_run=True)
    assert result["ok"] and result["source_commit"]


def test_init_creates_the_blank_campaign_and_project_files(plugin: Path, tmp_path: Path) -> None:
    template = plugin / "templates" / "campaign"
    result = plugin_campaign.init_campaign(tmp_path, template=template)
    assert result["ok"] and result["created"] == ["campaign/", ".claude/settings.json", "CLAUDE.md"]
    assert _files(tmp_path / "campaign") == _files(template)
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    style = _frontmatter(plugin / "output-styles" / "repog.md")["name"]
    assert settings["autoMemoryEnabled"] is False
    assert settings["outputStyle"] == f"repog:{style}"
    assert "repog:play" in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert not list(tmp_path.glob(".repog-campaign-*"))


def test_init_never_overwrites(plugin: Path, tmp_path: Path) -> None:
    template = plugin / "templates" / "campaign"
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text('{"model": "custom"}\n', encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("Mine.\n", encoding="utf-8")
    result = plugin_campaign.init_campaign(tmp_path, template=template)
    assert result["created"] == ["campaign/"] and result["skipped"] == [".claude/settings.json", "CLAUDE.md"]
    assert (tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8") == '{"model": "custom"}\n'
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "Mine.\n"
    before = _files(tmp_path)
    with pytest.raises(plugin_campaign.CampaignError) as error:
        plugin_campaign.init_campaign(tmp_path, template=template)
    assert error.value.category == "campaign_exists"
    assert _files(tmp_path) == before
    assert not list(tmp_path.glob(".repog-campaign-*"))


@pytest.mark.parametrize("missing", ["project", "template"])
def test_init_reports_missing_inputs(plugin: Path, tmp_path: Path, missing: str) -> None:
    project = tmp_path / "absent" if missing == "project" else tmp_path
    template = tmp_path / "no-template" if missing == "template" else plugin / "templates" / "campaign"
    with pytest.raises(plugin_campaign.CampaignError) as error:
        plugin_campaign.init_campaign(project, template=template)
    assert error.value.category == f"{missing}_missing"
    assert not (tmp_path / "campaign").exists()


@pytest.mark.skipif(SH is None, reason="needs a POSIX sh")
def test_session_start_hook_speaks_only_in_plugin_campaigns(plugin: Path, tmp_path: Path) -> None:
    hook = plugin / "scripts" / "session-start.sh"
    command = json.loads((plugin / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert command == 'sh "${CLAUDE_PLUGIN_ROOT}/scripts/session-start.sh"'

    empty = tmp_path / "empty"
    empty.mkdir()
    quiet = _sh(hook, cwd=empty, env={"CLAUDE_PROJECT_DIR": str(empty)})
    assert quiet.returncode == 0 and quiet.stdout == ""

    campaign = tmp_path / "campaign-folder"
    campaign.mkdir()
    plugin_campaign.init_campaign(campaign, template=plugin / "templates" / "campaign")
    reminder = _sh(hook, cwd=campaign, env={"CLAUDE_PROJECT_DIR": str(campaign)})
    assert reminder.returncode == 0 and "repog:play" in reminder.stdout

    (campaign / "AGENTS.md").write_text("# Standalone\n", encoding="utf-8")
    (campaign / "workflows").mkdir()
    standalone = _sh(hook, cwd=campaign, env={"CLAUDE_PROJECT_DIR": str(campaign)})
    assert standalone.returncode == 0 and standalone.stdout == ""


@pytest.mark.skipif(SH is None, reason="needs a POSIX sh")
def test_launcher_runs_bundled_helpers_only(plugin: Path, tmp_path: Path) -> None:
    launcher = plugin / "scripts" / "repog.sh"
    created = _sh(launcher, "plugin_campaign", "init", ".", cwd=tmp_path)
    assert created.returncode == 0, created.stderr
    assert json.loads(created.stdout)["ok"] is True
    checked = _sh(launcher, "check_state", "campaign", cwd=tmp_path)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    for helper in ("../tools/check_state", "check_state.py", "missing_helper", "visual_handoff", "agent_seat", "verify_workspace", ""):
        refused = _sh(launcher, helper, cwd=tmp_path)
        assert refused.returncode == 2
        assert json.loads(refused.stdout)["failure_category"] == "helper_invalid"


@pytest.mark.skipif(shutil.which("claude") is None, reason="needs the Claude Code CLI")
def test_claude_cli_validates_the_plugin(plugin: Path) -> None:
    for target in (plugin, plugin / ".claude-plugin" / "plugin.json"):
        result = subprocess.run(["claude", "plugin", "validate", "--strict", str(target)], capture_output=True, text=True, encoding="utf-8", check=False)
        assert result.returncode == 0, result.stdout + result.stderr
