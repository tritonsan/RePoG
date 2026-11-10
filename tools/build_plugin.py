"""Build the RePoG plugin for Claude Code from the canonical source.

The plugin carries the same engine as the player workspace: the routed
workflows, briefs, contracts, evaluation protocols, docs, and helpers, with the
blank campaign template under ``templates/campaign``.  Plugin-only files live
in ``plugin/``.  ``skills/play/SKILL.md`` includes ``AGENTS.md`` when the plugin
is built, so the shared contract keeps a single source.

Claude cannot generate images, and Claude Code uses neither browser-agent seats
nor the Companion View, so the plugin leaves out their files and the release
tooling that needs the source checkout (``OMITTED``) and removes the passages
that point at them (``TRIMS``).  Every other engine file is carried byte for
byte.  A trim whose anchor no longer matches fails the build instead of
shipping stale text, and a carried document that still names an omitted file
fails the build too.

Like ``build_distribution.py``, a build reads the committed ``HEAD`` by default.
``--worktree`` reads the working tree instead, for local testing, and
``--archive`` also writes the plugin as a deterministic ZIP with its manifest at
the root.  The result is checked against the automated limits of Anthropic's
plugin directory before anything is written.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import build_distribution

sys.dont_write_bytecode = True

OVERLAY = "plugin"
PLAY_SKILL = "skills/play/SKILL.md"
INCLUDE_MARKER = "<!-- repog:include AGENTS.md -->"
TEMPLATE_ROOT = "templates/campaign"
ENGINE_TREES = {"briefs", "contracts", "docs", "evaluation", "tools", "workflows"}
ENGINE_ROOT_FILES = {"AGENTS.md", "LICENSE", "THIRD_PARTY_NOTICES.md"}
# The player workspace's Claude Code agents and output style ship unchanged.
CLAUDE_LAYER = {"agents": "agents", "output-styles": "output-styles"}

# Canonical files the plugin does not carry.  A trailing slash names a folder.
OMITTED = frozenset(
    {
        # Image generation: Claude cannot make images.
        "tools/visual_handoff.py",
        "workflows/gm/playbooks/visual_handoff.md",
        # Pages and tools for the standalone workspace and its release, which
        # need the source checkout rather than a plugin install.
        "docs/claude-code.md",
        "tools/build_distribution.py",
        "tools/build_plugin.py",
        "tools/verify_workspace.py",
        # Browser-agent seats, a WebMCP layer that Claude Code does not use.
        "tools/agent_seat.py",
        "tools/compile_agent_brief.py",
        "docs/agent-seat.md",
        "contracts/agent-seat/",
        "campaign/agent_seat_state.json",
        "campaign/agent_roster.json",
        "campaign/dashboard/agent-table.css",
        "campaign/dashboard/agent-table.js",
        # The Companion View, a local status page built around a portrait.
        "tools/check_companion_view.py",
        "tools/serve_companion_view.py",
        "campaign/companion_view/",
    }
)
# Omitted files that must not be named by any document the plugin carries.
# Data files and folders stay out of this scan: the authority map still
# describes them as optional stores.
NAMED_SUFFIXES = {".py", ".md", ".css", ".js"}


def omitted(relative: str) -> bool:
    return any(relative == entry or (entry.endswith("/") and relative.startswith(entry)) for entry in OMITTED)


# Passages removed from carried files, keyed by plugin path.  Each operation
# must match exactly once: ("line", needle) drops the line holding needle,
# ("item", needle) the list item that starts on it, ("paragraph", needle) the
# blank-line-delimited block holding it, ("section", heading) a heading and its
# body, ("rewrite", needle, new) replaces that block with new, and
# ("text", old, new) swaps a phrase, ignoring how it is wrapped.
TRIMS: dict[str, tuple[tuple[str, ...], ...]] = {
    "workflows/gm/WORKFLOW.md": (("line", "playbooks/visual_handoff.md"),),
    "workflows/reference/optional-surfaces.md": (
        ("section", "# Visual Generation Handoff"),
        (
            "rewrite",
            "Load only when an enabled Dashboard, Agent Seat, Companion View, or visual",
            "Load only when an enabled Dashboard is triggered. The mode-specific playbook\nowns execution.",
        ),
        ("text", "# Player Dashboard And Companion View", "# Player Dashboard"),
        (
            "rewrite",
            "The Dashboard is RPG-only; Companion mode keeps it off.",
            "The Dashboard is RPG-only; Companion mode keeps it off.",
        ),
        (
            "text",
            "When the Agent Seat layer is active, the same-origin Table surface may additionally submit one "
            "revision-guarded operational intent through `tools/agent_seat.py`; that intent is not campaign truth "
            "and cannot write dashboard tiles or campaign owners.",
            "",
        ),
    ),
    "workflows/audit/WORKFLOW.md": (
        ("line", "tools/visual_handoff.py"),
        (
            "text",
            "Deterministic cases run inside `verify_workspace.py`; sample semantic cases in a fresh conversation",
            "Run its sample semantic cases in a fresh conversation",
        ),
        ("line", "`tools/verify_workspace.py` for the dependency-free public workspace check;"),
    ),
    "workflows/companion/WORKFLOW.md": (("section", "# Visuals"),),
    "workflows/worldbuild/playbooks/full_reference.md": (("paragraph", "If Session 0 generates a visual"),),
    "docs/dashboard.md": (("section", "## Visual Acceptance And Return"),),
    "docs/companion-mode.md": (
        (
            "rewrite",
            "Companion mode never loads the RPG Dashboard or World Voices layer.",
            "Companion mode never loads the RPG Dashboard or World Voices layer.",
        ),
        ("paragraph", "An optional portrait uses the standard draft/approval handoff"),
    ),
    "tools/README.md": (
        ("section", "## Agent Seat"),
        ("paragraph", "Run the dependency-free distributable smoke check with:"),
        ("paragraph", "python tools/verify_workspace.py --json"),
        ("paragraph", "Maintainers can also enforce the public-package boundary"),
        ("paragraph", "python -B tools/build_distribution.py"),
        ("paragraph", "The builder packages `HEAD`, not the mutable working tree"),
        ("paragraph", "The Claude Code plugin edition builds from the same source"),
        ("paragraph", "python -B tools/build_plugin.py --target"),
        ("text", "## Dashboard, Companion View, And Visual Transactions", "## Dashboard"),
        ("line", "python tools/check_companion_view.py"),
        ("line", "python tools/serve_companion_view.py"),
        ("line", "python tools/visual_handoff.py campaign --help"),
        (
            "text",
            "The visual handoff tool allows one pending `begin → attach → accept/revise/cancel` transaction and "
            "preserves its return anchor. Acceptance copies the approved asset into both campaign visual memory "
            "and dashboard assets; gallery, appearance, and requested dashboard placement roll back together on failure.",
            "",
        ),
        ("paragraph", "Companion mode keeps Dashboard V3 off."),
    ),
    "workflows/reference/authority-map.md": (
        ("line", "  agent_seat_state.json"),
        ("line", "  agent_roster.json"),
        ("line", "  companion_view/"),
        ("paragraph", "- `agent_seat_state.json` is the optional RPG Agent Seat operation store."),
        ("paragraph", "- `agent_roster.json` is the optional RPG Agent Seat eligibility manifest."),
        ("item", "- `companion_view/` is the optional lightweight derived Companion surface"),
    ),
    "templates/campaign/dashboard/index.html": (
        ("line", '<link rel="stylesheet" href="agent-table.css">'),
        ("line", '<script src="agent-table.js"></script>'),
    ),
    "templates/campaign/visual_gallery.md": (
        ("paragraph", "Generation alone does not mean acceptance."),
        ("text", "Accepted entries are added by the visual handoff tool.", "Accepted entries are added when a visual is accepted."),
    ),
    "templates/campaign/visual_style.md": (
        (
            "rewrite",
            "Use this file only if the campaign wants optional generated visuals.",
            "Image generation is unavailable in the RePoG plugin for Claude, so this\n"
            "campaign keeps visuals off and leaves the rest of this file unused.",
        ),
        ("paragraph", "Use `tools/visual_handoff.py` for"),
        ("paragraph", "Before generating a draft, run the begin step"),
    ),
}
REQUIRED = (
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "AGENTS.md",
    "LICENSE",
    "README.md",
    PLAY_SKILL,
    "skills/new/SKILL.md",
    "hooks/hooks.json",
    "scripts/repog.sh",
    "scripts/session-start.sh",
    "tools/plugin_campaign.py",
    f"{TEMPLATE_ROOT}/setup_profile.yaml",
)

# Automated limits from https://claude.com/docs/plugins/pre-submission-checklist.
MAX_FILES = 512
MAX_TEXT_BYTES = 256 * 1024
MAX_FILE_BYTES = 5 * 1024 * 1024
UNLIMITED_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp", ".otf", ".ttf", ".woff", ".woff2"}
# Files Claude reads as instructions.  Python helpers are left out of the
# omitted-file scan: a few name an optional sibling on purpose, and the tests
# import every helper to prove none needs an omitted one.
DOCUMENT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".txt", ".sh", ".html", ".js", ".css"}
SYSTEM_NAMES = {".ds_store", "thumbs.db", "desktop.ini", "__macosx"}
WINDOWS_DEVICES = {"con", "prn", "aux", "nul", *(f"com{n}" for n in range(1, 10)), *(f"lpt{n}" for n in range(1, 10))}
ROOT_REFERENCE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)")


class PluginBuildError(RuntimeError):
    pass


def plugin_path(relative: str, policy: Any) -> str | None:
    """Return where a canonical source file goes in the plugin, if anywhere."""

    if relative.startswith(f"{OVERLAY}/"):
        return relative[len(OVERLAY) + 1 :]
    if omitted(relative) or not policy.distribution_path_allowed(relative):
        return None
    parts = relative.split("/")
    if len(parts) == 1:
        return relative if relative in ENGINE_ROOT_FILES else None
    if parts[0] in ENGINE_TREES:
        return relative
    if parts[0] == "campaign":
        return "/".join([TEMPLATE_ROOT, *parts[1:]])
    if parts[0] == ".claude" and len(parts) == 3 and parts[1] in CLAUDE_LAYER:
        return f"{CLAUDE_LAYER[parts[1]]}/{parts[2]}"
    return None


def _source(source: Path, worktree: bool) -> tuple[dict[str, bytes], Any, str | None]:
    """Read every file the plugin needs, with the matching packaging policy."""

    if worktree:
        listed = build_distribution._git(source, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
        paths = sorted(path for path in listed.split("\0") if path and (source / path).is_file())
        policy = build_distribution._load_verifier(source)
        selected = [path for path in paths if plugin_path(path, policy) is not None]
        return {path: (source / path).read_bytes() for path in selected}, policy, None

    commit = build_distribution._git(source, "rev-parse", "HEAD")
    paths = [path for path in build_distribution._git(source, "ls-tree", "-rz", "--name-only", commit).split("\0") if path]
    policy = build_distribution._committed_policy(source, commit)
    selected = [path for path in paths if plugin_path(path, policy) is not None]
    if not selected:
        raise PluginBuildError("No plugin files were selected from HEAD.")
    with tempfile.TemporaryDirectory(prefix="repog-plugin-source-") as scratch:
        archive = Path(scratch) / "head.zip"
        result = subprocess.run(
            ["git", "-c", f"safe.directory={source.as_posix()}", "-C", str(source), "archive", "--format=zip", f"--output={archive}", commit, "--", *selected],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if result.returncode != 0:
            raise PluginBuildError(result.stderr.strip() or "Could not archive canonical HEAD.")
        with zipfile.ZipFile(archive) as bundle:
            files = {name: bundle.read(name) for name in bundle.namelist() if not name.endswith("/")}
    return files, policy, commit


def _anchor(kind: str, anchor: str, hits: list[Any]) -> None:
    if len(hits) != 1:
        raise PluginBuildError(f"trim {kind} {anchor!r} matched {len(hits)} times; it must match exactly once.")


def _lines(text: str) -> list[str]:
    """Split after each newline, so rejoining restores the exact bytes."""

    return re.findall(r"[^\n]*\n|[^\n]+", text)


def _drop_line(text: str, needle: str) -> str:
    lines = _lines(text)
    hits = [index for index, line in enumerate(lines) if needle in line]
    _anchor("line", needle, hits)
    del lines[hits[0]]
    return "".join(lines)


def _drop_paragraph(text: str, needle: str) -> str:
    lines = _lines(text)
    hits = [index for index, line in enumerate(lines) if needle in line]
    _anchor("paragraph", needle, hits)
    start, end = hits[0], hits[0] + 1
    while start > 0 and lines[start - 1].strip():
        start -= 1
    while end < len(lines) and lines[end].strip():
        end += 1
    if end < len(lines):
        end += 1  # the blank line that closed the paragraph
    elif start > 0:
        start -= 1  # the last paragraph takes the blank line that opened it
    del lines[start:end]
    return "".join(lines)


def _drop_item(text: str, needle: str) -> str:
    """Drop a list item: its first line and the indented lines that continue it."""

    lines = _lines(text)
    hits = [index for index, line in enumerate(lines) if needle in line]
    _anchor("item", needle, hits)
    start, end = hits[0], hits[0] + 1
    while end < len(lines) and lines[end].strip() and lines[end][0] in " \t":
        end += 1
    if end < len(lines) and not lines[end].strip() and start > 0 and not lines[start - 1].strip():
        end += 1  # an item that stood alone between blank lines takes one of them
    del lines[start:end]
    return "".join(lines)


def _rewrite_paragraph(text: str, needle: str, new: str) -> str:
    lines = _lines(text)
    hits = [index for index, line in enumerate(lines) if needle in line]
    _anchor("rewrite", needle, hits)
    start, end = hits[0], hits[0] + 1
    while start > 0 and lines[start - 1].strip():
        start -= 1
    while end < len(lines) and lines[end].strip():
        end += 1
    ending = re.search(r"\r?\n$", lines[start])
    newline = ending.group() if ending else "\n"
    lines[start:end] = [new.replace("\n", newline) + newline]
    return "".join(lines)


def _drop_section(text: str, heading: str) -> str:
    lines = _lines(text)
    hits = [index for index, line in enumerate(lines) if line.rstrip() == heading]
    _anchor("section", heading, hits)
    start = hits[0]
    level = len(heading) - len(heading.lstrip("#"))
    end, fenced = len(lines), False
    for index in range(start + 1, len(lines)):
        if lines[index].lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(rf"#{{1,{level}}} ", lines[index]):
            end = index
            break
    if end == len(lines):
        while start > 0 and not lines[start - 1].strip():
            start -= 1  # the last section takes the blank lines before it
    del lines[start:end]
    return "".join(lines)


def _replace_text(text: str, old: str, new: str) -> str:
    pattern = r"\s+".join(re.escape(word) for word in old.split())
    if not new:
        pattern = rf"[ \t]*{pattern}"  # a deleted sentence takes its leading space with it
    matches = list(re.finditer(pattern, text))
    _anchor("text", old[:60], matches)
    return text[: matches[0].start()] + new + text[matches[0].end() :]


_TRIM_OPERATIONS = {
    "line": _drop_line,
    "item": _drop_item,
    "paragraph": _drop_paragraph,
    "rewrite": _rewrite_paragraph,
    "section": _drop_section,
    "text": _replace_text,
}


def trim_file(destination: str, data: bytes) -> bytes:
    """Apply the TRIMS for one plugin path to its bytes; other bytes stay as they were."""

    text = data.decode("utf-8")
    for kind, *arguments in TRIMS[destination]:
        text = _TRIM_OPERATIONS[kind](text, *arguments)
    return text.encode("utf-8")


def assemble(files: dict[str, bytes], policy: Any) -> dict[str, bytes]:
    """Map canonical files to plugin paths, trim them, and expand the play skill."""

    plan: dict[str, bytes] = {}
    origin: dict[str, str] = {}
    for relative in sorted(files):
        destination = plugin_path(relative, policy)
        if destination is None:
            continue
        if destination in plan:
            raise PluginBuildError(f"{relative} and {origin[destination]} both map to {destination}.")
        plan[destination] = files[relative]
        origin[destination] = relative

    for destination in TRIMS:
        if destination not in plan:
            raise PluginBuildError(f"{destination} is trimmed but is not part of the plugin.")
        plan[destination] = trim_file(destination, plan[destination])

    if PLAY_SKILL not in plan or "AGENTS.md" not in plan:
        raise PluginBuildError(f"The plugin needs {PLAY_SKILL} and AGENTS.md.")
    skill = plan[PLAY_SKILL].decode("utf-8").replace("\r\n", "\n")
    if skill.count(INCLUDE_MARKER) != 1:
        raise PluginBuildError(f"{PLAY_SKILL} must contain the AGENTS.md include marker exactly once.")
    contract = plan["AGENTS.md"].decode("utf-8").replace("\r\n", "\n").strip("\n")
    plan[PLAY_SKILL] = skill.replace(INCLUDE_MARKER, contract).encode("utf-8")
    # Shell scripts must keep LF endings, whatever the checkout did.
    for relative in plan:
        if relative.endswith(".sh"):
            plan[relative] = plan[relative].replace(b"\r\n", b"\n")
    return plan


def _frontmatter(text: str) -> dict[str, str] | None:
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        key, separator, value = line.partition(":")
        if separator and key.strip() and not key.startswith((" ", "\t")):
            fields[key.strip()] = value.strip()
    return None


def _readme_words(text: str) -> int:
    words, fenced = 0, False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced:
            words += len(line.split())
    return words


def check(plan: dict[str, bytes]) -> list[str]:
    """Return directory-limit and structure problems; empty means buildable."""

    problems = [f"missing {relative}" for relative in REQUIRED if relative not in plan]
    if len(plan) > MAX_FILES:
        problems.append(f"{len(plan)} files exceed the directory's {MAX_FILES}-file limit")
    if "CLAUDE.md" in plan:
        problems.append("a CLAUDE.md at the plugin root is never loaded; instructions belong in a skill")
    folded: dict[str, str] = {}
    for relative, data in sorted(plan.items()):
        pure = PurePosixPath(relative)
        if pure.parts[0] == "bin":
            problems.append(f"{relative}: a top-level bin/ stops claude.ai and Cowork from installing the plugin")
        for part in pure.parts:
            if part.lower() in SYSTEM_NAMES:
                problems.append(f"{relative}: operating-system file")
            if ":" in part or part.endswith((".", " ")) or part.split(".")[0].lower() in WINDOWS_DEVICES:
                problems.append(f"{relative}: name is not valid on Windows")
        if relative.lower() in folded:
            problems.append(f"{relative} and {folded[relative.lower()]} differ only by case")
        folded[relative.lower()] = relative
        if pure.suffix.lower() in {".pyc", ".pyo"}:
            problems.append(f"{relative}: compiled Python is not allowed")
        limit = MAX_FILE_BYTES if pure.suffix.lower() in UNLIMITED_SUFFIXES else MAX_TEXT_BYTES
        if len(data) >= limit:
            problems.append(f"{relative}: {len(data)} bytes reach the {limit}-byte limit")
        if relative.startswith("skills/") and INCLUDE_MARKER.encode("utf-8") in data:
            problems.append(f"{relative}: unexpanded include marker")
        if pure.suffix.lower() in DOCUMENT_SUFFIXES:
            text = data.decode("utf-8", "replace")
            problems.extend(
                f"{relative}: still mentions omitted {entry}"
                for entry in sorted(OMITTED)
                if PurePosixPath(entry).suffix in NAMED_SUFFIXES and PurePosixPath(entry).name in text
            )
    if problems:
        return problems

    try:
        manifest = json.loads(plan[".claude-plugin/plugin.json"])
        marketplace = json.loads(plan[".claude-plugin/marketplace.json"])
        hooks = json.loads(plan["hooks/hooks.json"])
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"plugin JSON is invalid: {exc}"]
    for field in ("name", "version", "description", "license"):
        if not isinstance(manifest.get(field), str) or not manifest[field]:
            problems.append(f"plugin.json needs a {field}")
    if not isinstance(manifest.get("author"), dict) or not manifest["author"].get("name"):
        problems.append("plugin.json needs author.name")
    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or [entry.get("name") for entry in entries if isinstance(entry, dict)] != [manifest.get("name")]:
        problems.append("marketplace.json must list exactly this plugin")
    elif entries[0].get("source") != "./":
        problems.append("marketplace.json must use the plugin root as its source")
    if not isinstance(hooks.get("hooks"), dict):
        problems.append("hooks/hooks.json needs a top-level hooks object")

    for relative, data in plan.items():
        if relative.startswith(("skills/", "agents/", "output-styles/")) and relative.endswith(".md"):
            fields = _frontmatter(data.decode("utf-8"))
            if not fields or not fields.get("name") or not fields.get("description"):
                problems.append(f"{relative} needs name and description frontmatter")
        if relative.startswith(("skills/", "hooks/")):
            for reference in ROOT_REFERENCE.findall(data.decode("utf-8")):
                if reference.rstrip("/.") not in plan:
                    problems.append(f"{relative} references missing {reference}")
    if _readme_words(plan["README.md"].decode("utf-8")) < 40:
        problems.append("README.md needs at least 40 words outside code blocks")
    return problems


def write_archive(plan: dict[str, bytes], archive: Path) -> None:
    """Write the plugin as a ZIP with its manifest at the root.

    Entries are sorted and carry fixed timestamps, so the same files always give
    the same bytes.
    """

    archive.parent.mkdir(parents=True, exist_ok=True)
    temporary = archive.with_name(f".{archive.name}.tmp")
    temporary.unlink(missing_ok=True)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for relative, data in sorted(plan.items()):
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                bundle.writestr(info, data)
        temporary.replace(archive)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def build(
    source: Path,
    target: Path,
    *,
    worktree: bool = False,
    dry_run: bool = False,
    archive: Path | None = None,
) -> dict[str, Any]:
    source = source.resolve()
    target = target.resolve()
    archive = archive.resolve() if archive else None
    if target.exists():
        raise PluginBuildError(f"Target already exists: {target}")
    if archive is not None:
        if archive.exists():
            raise PluginBuildError(f"Archive already exists: {archive}")
        if archive == target or target in archive.parents:
            raise PluginBuildError(f"Archive must not be inside the plugin folder: {archive}")
    if not (source / ".git").exists():
        raise PluginBuildError(f"Canonical source is not a Git checkout: {source}")
    if Path(build_distribution._git(source, "rev-parse", "--show-toplevel")).resolve() != source:
        raise PluginBuildError("Source must be the canonical Git repository root.")

    files, policy, commit = _source(source, worktree)
    plan = assemble(files, policy)
    problems = check(plan)
    if problems:
        raise PluginBuildError("Plugin failed its checks: " + "; ".join(problems))
    manifest = json.loads(plan[".claude-plugin/plugin.json"])
    summary = {
        "ok": True,
        "dry_run": dry_run,
        "canonical_source": str(source),
        "source_commit": commit,
        "worktree": worktree,
        "target": str(target),
        "archive": str(archive) if archive else None,
        "plugin": manifest["name"],
        "version": manifest["version"],
        "file_count": len(plan),
    }
    if dry_run:
        return summary

    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.staging-", dir=target.parent))
    try:
        for relative, data in sorted(plan.items()):
            path = staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        staging.replace(target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    if archive is not None:
        write_archive(plan, archive)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", required=True, help="New plugin directory to create. Existing targets are refused.")
    parser.add_argument("--worktree", action="store_true", help="Read the working tree instead of committed HEAD.")
    parser.add_argument("--archive", help="Also write a deterministic ZIP of the plugin to this new path.")
    parser.add_argument("--source", default=str(Path(__file__).resolve().parents[1]), help=argparse.SUPPRESS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = build(
            Path(args.source),
            Path(args.target),
            worktree=args.worktree,
            dry_run=args.dry_run,
            archive=Path(args.archive) if args.archive else None,
        )
    except (PluginBuildError, build_distribution.DistributionError, OSError, UnicodeDecodeError, zipfile.BadZipFile) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=True))
        else:
            print(f"Plugin build failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        action = "Would build" if result["dry_run"] else "Built"
        origin = "working tree" if result["worktree"] else result["source_commit"][:12]
        print(f"{action} {result['plugin']} {result['version']} from {origin} -> {result['target']} ({result['file_count']} files)")
        if result["archive"]:
            print(f"Archive: {result['archive']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
