"""Address-based edit operations for RPG owner files.

The GM decides what changed and writes the new text. These operations only
place that text at a declared address: a key path in `current_state.yaml`, a
Markdown heading, or a Markdown table row. The GM therefore never has to quote
the old text back, and deleting or replacing a section costs as little as
appending one.

The module is deliberately semantic-free: it never decides what a fact means,
which owner holds it, or whether a change is plausible. It only refuses
ambiguous or impossible addresses, so a mistyped heading fails loudly instead
of writing in the wrong place.
"""

from __future__ import annotations

import json
import re
from typing import Any


YAML_OPS = frozenset({"set", "list_add", "list_remove", "list_set"})
MARKDOWN_OPS = frozenset(
    {"append", "replace_section", "remove_section", "insert_section", "upsert_row", "delete_row", "replace"}
)
MAX_OPS = 64
MAX_OP_TEXT = 60_000

# Fields the RPG writer owns. A typed edit may never touch them; the writer
# also re-checks the persistence block after every candidate is built.
PROTECTED_YAML_KEYS = frozenset({"continuity_revision", "persistence"})
YAML_RESERVED_WORDS = frozenset({"true", "false", "yes", "no", "on", "off", "null", "y", "n"})

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE_RE = re.compile(r"^[ \t]*(```|~~~)")
TABLE_SEPARATOR_RE = re.compile(r"^\|?[ \t]*:?-{3,}:?[ \t]*(\|[ \t]*:?-{3,}:?[ \t]*)*\|?[ \t]*$")
PLACEHOLDER_RE = re.compile(r"\{\{\s*(revision|next_id:([A-Za-z][A-Za-z0-9_]{0,31}))\s*\}\}")
REVISION_STAMP_RE = re.compile(r"(?m)^(As of revision:[ \t]*)(\d+)([ \t]*)$")


class OwnerOpError(Exception):
    """A typed edit that cannot be applied exactly as declared."""

    def __init__(self, category: str, reason: str) -> None:
        super().__init__(reason)
        self.category = category


def _text(value: Any, label: str, *, allow_empty: bool = False, one_line: bool = False) -> str:
    if not isinstance(value, str):
        raise OwnerOpError("input_invalid", f"{label} must be text")
    if not allow_empty and not value.strip():
        raise OwnerOpError("input_invalid", f"{label} must be non-empty text")
    if one_line and ("\n" in value or "\r" in value):
        raise OwnerOpError("input_invalid", f"{label} must be one line")
    if len(value) > MAX_OP_TEXT:
        raise OwnerOpError("input_invalid", f"{label} exceeds {MAX_OP_TEXT} characters")
    return value


def _newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


# ---------------------------------------------------------------------------
# Placeholders
# ---------------------------------------------------------------------------


class PlaceholderContext:
    """Resolve `{{revision}}` and `{{next_id:PREFIX}}` deterministically.

    `next_id` scans the target file for `PREFIX-<number>` and allocates the next
    free number. Allocations made earlier in the same payload are remembered,
    so two new facts in one commit never share an id.
    """

    def __init__(self, revision: int) -> None:
        self.revision = revision
        self._allocated: dict[tuple[str, str], tuple[int, int]] = {}

    def resolve(self, value: str, *, path: str, file_text: str) -> str:
        def substitute(match: re.Match[str]) -> str:
            if match.group(1) == "revision":
                return str(self.revision)
            prefix = match.group(2)
            key = (path, prefix)
            if key not in self._allocated:
                found = re.findall(rf"\b{re.escape(prefix)}-(\d+)\b", file_text)
                # Keep the file's zero padding (PC-021 -> PC-022).
                width = max((len(number) for number in found), default=1)
                self._allocated[key] = (max((int(number) for number in found), default=0), width)
            number, width = self._allocated[key]
            self._allocated[key] = (number + 1, width)
            return f"{prefix}-{str(number + 1).zfill(width)}"

        return PLACEHOLDER_RE.sub(substitute, value)

    def resolve_any(self, value: Any, *, path: str, file_text: str) -> Any:
        if isinstance(value, str):
            return self.resolve(value, path=path, file_text=file_text)
        if isinstance(value, list):
            return [self.resolve_any(item, path=path, file_text=file_text) for item in value]
        if isinstance(value, dict):
            return {key: self.resolve_any(item, path=path, file_text=file_text) for key, item in value.items()}
        return value


# ---------------------------------------------------------------------------
# YAML: the restricted shape used by current_state.yaml
# ---------------------------------------------------------------------------


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_content(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def _key_match(line: str, key: str, indent: int) -> bool:
    return _indent(line) == indent and re.match(rf"^ *{re.escape(key)}:(?:[ \t]|$)", line.rstrip("\r\n")) is not None


def _block_end(lines: list[str], index: int) -> int:
    """Return the end of the value that belongs to the key on `lines[index]`.

    The value spans following lines that are more indented, and block-sequence
    items written at the key's own indentation. Comments at the key's level or
    shallower belong to the parent, not to this value.
    """

    indent = _indent(lines[index])
    end = index + 1
    cursor = index + 1
    while cursor < len(lines):
        line = lines[cursor]
        if not line.strip():
            cursor += 1
            continue
        line_indent = _indent(line)
        if line_indent > indent or (line_indent == indent and line.lstrip(" ").startswith("- ")):
            cursor += 1
            end = cursor
            continue
        break
    return end


def _locate_key(lines: list[str], key_path: str) -> int:
    parts = key_path.split(".")
    if not key_path or any(not part or not re.fullmatch(r"[A-Za-z0-9_-]+", part) for part in parts):
        raise OwnerOpError("input_invalid", f"key path '{key_path}' must be dot-separated simple keys")
    if parts[0] in PROTECTED_YAML_KEYS:
        raise OwnerOpError("input_invalid", f"'{parts[0]}' is managed by the writer and cannot be edited")
    start, end, indent = 0, len(lines), 0
    found = -1
    for depth, part in enumerate(parts):
        matches = [index for index in range(start, end) if _key_match(lines[index], part, indent)]
        if not matches:
            scope = ".".join(parts[:depth]) or "the top level"
            raise OwnerOpError("candidate_invalid", f"key '{part}' does not exist under {scope}; typed edits never create keys")
        if len(matches) > 1:
            raise OwnerOpError("candidate_invalid", f"key '{'.'.join(parts[: depth + 1])}' appears more than once")
        found = matches[0]
        if depth == len(parts) - 1:
            break
        child_start = found + 1
        child_end = _block_end(lines, found)
        children = [index for index in range(child_start, child_end) if _is_content(lines[index])]
        if not children:
            raise OwnerOpError("candidate_invalid", f"'{'.'.join(parts[: depth + 1])}' has no nested keys")
        start, end, indent = child_start, child_end, _indent(lines[children[0]])
    return found


def _inline_value(line: str) -> str:
    value = line.split(":", 1)[1].strip()
    if value.startswith(("\"", "'")):
        return value
    return value.split(" #", 1)[0].strip()


def _render_scalar(value: Any, label: str) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return json.dumps(value)
    if isinstance(value, str):
        if "\n" in value or "\r" in value:
            raise OwnerOpError("input_invalid", f"{label} must be one line in current_state.yaml")
        # Enum-like tokens (scene modes, phases) stay bare, as the templates write them.
        if re.fullmatch(r"[a-z][a-z0-9_]*", value) and value not in YAML_RESERVED_WORDS:
            return value
        return json.dumps(value, ensure_ascii=False)
    raise OwnerOpError("input_invalid", f"{label} must be text, a number, true, false, or null")


def _decode_item(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith('"'):
        try:
            decoded = json.loads(raw)
            if isinstance(decoded, str):
                return decoded
        except json.JSONDecodeError:
            pass
    if len(raw) >= 2 and raw[0] == raw[-1] == "'":
        return raw[1:-1].replace("''", "'")
    return raw


def _read_list(lines: list[str], index: int, key_path: str) -> list[str]:
    inline = _inline_value(lines[index])
    end = _block_end(lines, index)
    items: list[str] = []
    for line in lines[index + 1 : end]:
        if not _is_content(line):
            continue
        stripped = line.strip()
        if not stripped.startswith("- "):
            raise OwnerOpError("candidate_invalid", f"'{key_path}' is a mapping, not a list")
        items.append(_decode_item(stripped[2:]))
    if inline:
        if items:
            raise OwnerOpError("candidate_invalid", f"'{key_path}' mixes an inline value with list items")
        if inline == "[]":
            return []
        try:
            decoded = json.loads(inline)
        except json.JSONDecodeError as exc:
            raise OwnerOpError("candidate_invalid", f"'{key_path}' is not a list") from exc
        if not isinstance(decoded, list) or not all(isinstance(item, str) for item in decoded):
            raise OwnerOpError("candidate_invalid", f"'{key_path}' is not a list of text items")
        return decoded
    return items


def _write_value(lines: list[str], index: int, rendered: list[str]) -> None:
    end = _block_end(lines, index)
    newline = "\r\n" if lines[index].endswith("\r\n") else "\n"
    # Keep trailing blank lines that separate this key from the next block.
    while end > index + 1 and not lines[end - 1].strip():
        end -= 1
    lines[index:end] = [line + newline for line in rendered]


def _set_key(lines: list[str], key_path: str, value: Any, label: str) -> None:
    index = _locate_key(lines, key_path)
    end = _block_end(lines, index)
    inline = _inline_value(lines[index])
    nested = [line for line in lines[index + 1 : end] if _is_content(line)]
    block_scalar = inline.startswith(("|", ">"))
    if inline.startswith("{") or (nested and not block_scalar and not all(line.strip().startswith("- ") for line in nested)):
        raise OwnerOpError("candidate_invalid", f"'{key_path}' holds nested keys; set its children instead")
    if inline.startswith("[") or (nested and not block_scalar):
        raise OwnerOpError("candidate_invalid", f"'{key_path}' is a list; use list_add, list_remove, or list_set")
    if isinstance(value, (list, dict)):
        raise OwnerOpError("input_invalid", f"{label} must be a scalar; use list_set for lists")
    key = key_path.rsplit(".", 1)[-1]
    prefix = " " * _indent(lines[index])
    _write_value(lines, index, [f"{prefix}{key}: {_render_scalar(value, label)}"])


def _set_list(lines: list[str], key_path: str, items: list[str]) -> None:
    index = _locate_key(lines, key_path)
    key = key_path.rsplit(".", 1)[-1]
    prefix = " " * _indent(lines[index])
    if not items:
        _write_value(lines, index, [f"{prefix}{key}: []"])
        return
    rendered = [f"{prefix}{key}:"]
    rendered.extend(f"{prefix}  - {json.dumps(item, ensure_ascii=False)}" for item in items)
    _write_value(lines, index, rendered)


def _items(value: Any, label: str) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not value:
        raise OwnerOpError("input_invalid", f"{label} must be text or a non-empty array of text")
    items: list[str] = []
    for position, item in enumerate(value):
        text = _text(item, f"{label}[{position}]", one_line=True).strip()
        items.append(text)
    return items


def apply_yaml_ops(text: str, ops: list[dict[str, Any]], *, label: str) -> str:
    lines = text.splitlines(keepends=True)
    for position, op in enumerate(ops):
        op_label = f"{label}.ops[{position}]"
        kind = op["op"]
        if kind == "set":
            if "values" in op:
                values = op["values"]
                if not isinstance(values, dict) or not values:
                    raise OwnerOpError("input_invalid", f"{op_label}.values must be a non-empty object")
                for key_path, value in values.items():
                    _set_key(lines, key_path, value, f"{op_label}.values.{key_path}")
            else:
                _set_key(lines, _text(op.get("key"), f"{op_label}.key", one_line=True), op.get("value"), f"{op_label}.value")
            continue
        key_path = _text(op.get("key"), f"{op_label}.key", one_line=True)
        index = _locate_key(lines, key_path)
        current = _read_list(lines, index, key_path)
        if kind == "list_set":
            raw = op.get("items")
            items = [] if raw == [] else _items(raw, f"{op_label}.items")
            _set_list(lines, key_path, items)
        elif kind == "list_add":
            additions = [item for item in _items(op.get("items"), f"{op_label}.items") if item not in current]
            if additions:
                _set_list(lines, key_path, current + additions)
        elif kind == "list_remove":
            removals = _items(op.get("items"), f"{op_label}.items")
            missing = [item for item in removals if item not in current]
            if missing:
                raise OwnerOpError(
                    "candidate_invalid",
                    f"{op_label}: {missing} not in '{key_path}'; current items: {current}",
                )
            _set_list(lines, key_path, [item for item in current if item not in removals])
    return "".join(lines)


# ---------------------------------------------------------------------------
# Markdown: sections addressed by heading, tables addressed by first cell
# ---------------------------------------------------------------------------


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    found: list[tuple[int, int, str]] = []
    fenced = False
    for index, line in enumerate(lines):
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = HEADING_RE.match(line.rstrip("\r\n"))
        if match:
            found.append((index, len(match.group(1)), match.group(2).strip()))
    return found


def _parse_heading_address(value: Any, label: str) -> tuple[int | None, str]:
    text = _text(value, label, one_line=True).strip()
    match = HEADING_RE.match(text)
    if match:
        return len(match.group(1)), match.group(2).strip()
    return None, text


def _section_end(lines: list[str], headings: list[tuple[int, int, str]], index: int, level: int) -> int:
    for line_index, line_level, _ in headings:
        if line_index > index and line_level <= level:
            return line_index
    return len(lines)


def _find_section(lines: list[str], heading: Any, under: Any, label: str) -> tuple[int, int, int]:
    """Return (heading line, body end, level) for one uniquely addressed heading."""

    headings = _headings(lines)
    scope_start, scope_end = 0, len(lines)
    if under is not None:
        parent_level, parent_text = _parse_heading_address(under, f"{label}.under")
        parents = [
            item for item in headings if item[2] == parent_text and (parent_level is None or item[1] == parent_level)
        ]
        if len(parents) != 1:
            raise OwnerOpError(
                "candidate_invalid",
                f"{label}.under '{parent_text}' matched {len(parents)} headings; expected exactly one",
            )
        parent_index, parent_lvl, _ = parents[0]
        scope_start, scope_end = parent_index + 1, _section_end(lines, headings, parent_index, parent_lvl)
    level, title = _parse_heading_address(heading, f"{label}.heading")
    matches = [
        item
        for item in headings
        if scope_start <= item[0] < scope_end and item[2] == title and (level is None or item[1] == level)
    ]
    if len(matches) != 1:
        nearby = [item[2] for item in headings if scope_start <= item[0] < scope_end][:24]
        hint = "add 'under' or consolidate the duplicates" if matches else f"headings here: {nearby}"
        raise OwnerOpError(
            "candidate_invalid",
            f"{label}.heading '{title}' matched {len(matches)} headings; expected exactly one ({hint})",
        )
    index, found_level, _ = matches[0]
    return index, _section_end(lines, headings, index, found_level), found_level


def _body_lines(value: str, newline: str) -> list[str]:
    body = value.replace("\r\n", "\n").strip("\n")
    return [line + newline for line in body.split("\n")]


def _last_content(lines: list[str], start: int, end: int) -> int:
    """Index just after the last non-blank line in lines[start:end], or start."""

    cursor = end
    while cursor > start and not lines[cursor - 1].strip():
        cursor -= 1
    return cursor


def _ensure_line_break(lines: list[str], index: int, newline: str) -> None:
    if index > 0 and not lines[index - 1].endswith(("\n", "\r")):
        lines[index - 1] += newline


def _append(lines: list[str], op: dict[str, Any], label: str, newline: str) -> None:
    body = _body_lines(_text(op.get("text"), f"{label}.text"), newline)
    if op.get("heading") is None:
        insert_at = _last_content(lines, 0, len(lines))
        _ensure_line_break(lines, insert_at, newline)
        lines[insert_at:insert_at] = ([newline] if insert_at else []) + body
        return
    index, end, _ = _find_section(lines, op.get("heading"), op.get("under"), label)
    insert_at = _last_content(lines, index + 1, end)
    if insert_at == index + 1:
        body = [newline] + body
        if end == index + 1 and end < len(lines):
            body = body + [newline]
    _ensure_line_break(lines, insert_at, newline)
    lines[insert_at:insert_at] = body


def _replace_section(lines: list[str], op: dict[str, Any], label: str, newline: str) -> None:
    index, end, _ = _find_section(lines, op.get("heading"), op.get("under"), label)
    body = _body_lines(_text(op.get("text"), f"{label}.text"), newline)
    trailing = [newline] if end < len(lines) else []
    lines[index + 1 : end] = [newline] + body + trailing


def _remove_section(lines: list[str], op: dict[str, Any], label: str) -> None:
    index, end, _ = _find_section(lines, op.get("heading"), op.get("under"), label)
    del lines[index:end]


def _insert_section(lines: list[str], op: dict[str, Any], label: str, newline: str) -> None:
    level, title = _parse_heading_address(op.get("heading"), f"{label}.heading")
    if level is None:
        raise OwnerOpError("input_invalid", f"{label}.heading must include its # level, e.g. '### {title}'")
    body = _body_lines(_text(op.get("text"), f"{label}.text"), newline)
    headings = _headings(lines)
    scope_start, scope_end = 0, len(lines)
    if op.get("under") is not None:
        parent_index, scope_end, parent_level = _find_section(lines, op.get("under"), None, f"{label}.under")
        scope_start = parent_index + 1
        if level <= parent_level:
            raise OwnerOpError("input_invalid", f"{label}.heading must be deeper than its parent heading")
    duplicates = [item for item in headings if scope_start <= item[0] < scope_end and item[2] == title]
    if duplicates:
        raise OwnerOpError(
            "candidate_invalid",
            f"{label}: a heading '{title}' already exists here; use replace_section instead of stacking another",
        )
    insert_at = _last_content(lines, scope_start, scope_end)
    _ensure_line_break(lines, insert_at, newline)
    block = [newline, f"{'#' * level} {title}{newline}", newline] + body
    # Existing blank lines after the insertion point already separate the new
    # section from whatever follows; add one only when a heading follows directly.
    if insert_at == scope_end and scope_end < len(lines):
        block.append(newline)
    lines[insert_at:insert_at] = block


def _table_bounds(lines: list[str], start: int, end: int, table: int, label: str) -> tuple[int, int]:
    tables: list[tuple[int, int]] = []
    cursor = start
    while cursor < end:
        if lines[cursor].lstrip().startswith("|"):
            first = cursor
            while cursor < end and lines[cursor].lstrip().startswith("|"):
                cursor += 1
            if cursor - first >= 2 and TABLE_SEPARATOR_RE.match(lines[first + 1].strip()):
                tables.append((first, cursor))
        else:
            cursor += 1
    if not isinstance(table, int) or isinstance(table, bool) or not 0 <= table < len(tables):
        raise OwnerOpError("candidate_invalid", f"{label}: table {table} not found ({len(tables)} table(s) in scope)")
    return tables[table]


def _split_row(line: str) -> list[str]:
    row = line.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", row)]


def _row_text(cells: list[str], newline: str) -> str:
    escaped = [re.sub(r"(?<!\\)\|", r"\\|", cell) for cell in cells]
    return "| " + " | ".join(escaped) + " |" + newline


def _table_op(lines: list[str], op: dict[str, Any], label: str, newline: str) -> None:
    if op.get("heading") is not None:
        index, end, _ = _find_section(lines, op.get("heading"), op.get("under"), label)
        start = index + 1
    else:
        start, end = 0, len(lines)
    first, last = _table_bounds(lines, start, end, op.get("table", 0), label)
    columns = len(_split_row(lines[first]))
    # A row is keyed by its first cell, or by its first several cells when one
    # column is not unique (From | Direction | To in a relationship map).
    raw_key = op.get("key")
    key_cells = raw_key if isinstance(raw_key, list) else [raw_key]
    if not key_cells or len(key_cells) > columns:
        raise OwnerOpError("input_invalid", f"{label}.key must name 1 to {columns} leading cells")
    key = [_text(cell, f"{label}.key", one_line=True).strip() for cell in key_cells]
    width = len(key)
    rows = [index for index in range(first + 2, last) if _split_row(lines[index])[:width] == key]
    if len(rows) > 1:
        raise OwnerOpError(
            "candidate_invalid",
            f"{label}: key {key} matches {len(rows)} rows; give more leading cells so it names one row",
        )
    if op["op"] == "delete_row":
        if not rows:
            keys = [_split_row(lines[index])[:width] for index in range(first + 2, last)][:40]
            raise OwnerOpError("candidate_invalid", f"{label}: no row with key {key}; keys: {keys}")
        del lines[rows[0]]
        return
    raw_cells = op.get("cells")
    if not isinstance(raw_cells, list) or len(raw_cells) != columns:
        raise OwnerOpError("input_invalid", f"{label}.cells must list exactly {columns} cells")
    cells = [_text(cell, f"{label}.cells[{position}]", allow_empty=True, one_line=True).strip() for position, cell in enumerate(raw_cells)]
    if cells[:width] != key:
        raise OwnerOpError("input_invalid", f"{label}.cells must start with the key {key}")
    row = _row_text(cells, newline)
    if rows:
        lines[rows[0]] = row
    else:
        _ensure_line_break(lines, last, newline)
        lines.insert(last, row)


def _replace_exact(lines: list[str], op: dict[str, Any], label: str) -> list[str]:
    text = "".join(lines)
    old = _text(op.get("old"), f"{label}.old")
    new = op.get("new")
    if not isinstance(new, str):
        raise OwnerOpError("input_invalid", f"{label}.new must be text")
    count = text.count(old)
    if count != 1:
        raise OwnerOpError("candidate_invalid", f"{label}.old matched {count} times; expected exactly one")
    return text.replace(old, new, 1).splitlines(keepends=True)


def apply_markdown_ops(text: str, ops: list[dict[str, Any]], *, label: str) -> str:
    newline = _newline(text)
    lines = text.splitlines(keepends=True)
    for position, op in enumerate(ops):
        op_label = f"{label}.ops[{position}]"
        kind = op["op"]
        if kind == "append":
            _append(lines, op, op_label, newline)
        elif kind == "replace_section":
            _replace_section(lines, op, op_label, newline)
        elif kind == "remove_section":
            _remove_section(lines, op, op_label)
        elif kind == "insert_section":
            _insert_section(lines, op, op_label, newline)
        elif kind in {"upsert_row", "delete_row"}:
            _table_op(lines, op, op_label, newline)
        elif kind == "replace":
            lines = _replace_exact(lines, op, op_label)
    result = "".join(lines)
    return result if result.endswith(("\n", "\r")) else result + newline


# ---------------------------------------------------------------------------
# Entry points used by the RPG writer
# ---------------------------------------------------------------------------


def parse_ops(value: Any, *, relative: str, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise OwnerOpError("input_invalid", f"{label}.ops must be a non-empty array")
    if len(value) > MAX_OPS:
        raise OwnerOpError("input_invalid", f"{label}.ops exceeds {MAX_OPS}")
    allowed = YAML_OPS if relative.endswith((".yaml", ".yml")) else MARKDOWN_OPS
    if not relative.endswith((".yaml", ".yml", ".md")):
        raise OwnerOpError("input_invalid", f"{label}: typed ops support YAML and Markdown owners only")
    parsed: list[dict[str, Any]] = []
    for position, op in enumerate(value):
        op_label = f"{label}.ops[{position}]"
        if not isinstance(op, dict) or not isinstance(op.get("op"), str):
            raise OwnerOpError("input_invalid", f"{op_label} must be an object with an 'op' name")
        if op["op"] not in allowed:
            raise OwnerOpError(
                "input_invalid",
                f"{op_label}.op '{op['op']}' is not available for {relative}; use one of: {', '.join(sorted(allowed))}",
            )
        parsed.append(op)
    return parsed


def apply_ops(
    text: str,
    ops: list[dict[str, Any]],
    *,
    relative: str,
    label: str,
    placeholders: PlaceholderContext,
) -> str:
    """Apply typed ops to one owner's text after resolving placeholders."""

    resolved = [placeholders.resolve_any(op, path=relative, file_text=text) for op in ops]
    if relative.endswith((".yaml", ".yml")):
        return apply_yaml_ops(text, resolved, label=label)
    return apply_markdown_ops(text, resolved, label=label)


def stamp_revision(text: str, revision: int) -> str:
    """Set a single `As of revision: N` stamp, if the file carries exactly one."""

    matches = list(REVISION_STAMP_RE.finditer(text))
    if len(matches) != 1:
        return text
    match = matches[0]
    return text[: match.start()] + f"{match.group(1)}{revision}{match.group(3)}" + text[match.end() :]


def set_scene_frame(text: str, *, scene_id: str, scene_mode: str, resume_anchor: str) -> str:
    """Copy checkpoint fields into current_state.yaml's scene frame."""

    lines = text.splitlines(keepends=True)
    for key, value in (
        ("scene_frame.scene_id", scene_id),
        ("scene_frame.mode", scene_mode),
        ("scene_frame.resume_anchor", resume_anchor),
    ):
        _set_key(lines, key, value, f"checkpoint -> {key}")
    return "".join(lines)


def stacked_headings(text: str, *, minimum: int = 3) -> list[tuple[str, int]]:
    """Find headings repeated with only numbers or a parenthetical changed.

    A note that grows "Current State (day 22)", "Current State (day 72)", ...
    has stacked layers that contradict each other; it should be replaced in
    place. Normal repeated structure (one heading per entity) does not match,
    because those headings differ in their words.
    """

    counts: dict[str, int] = {}
    labels: dict[str, str] = {}
    for _, level, title in _headings(text.splitlines(keepends=True)):
        normalized = re.sub(r"\([^)]*\)", "", title)
        normalized = re.sub(r"\d+", "#", normalized).strip(" -:—").casefold()
        normalized = re.sub(r"\s+", " ", normalized)
        if not normalized:
            continue
        key = f"{level}:{normalized}"
        counts[key] = counts.get(key, 0) + 1
        labels.setdefault(key, title)
    return [(labels[key], count) for key, count in counts.items() if count >= minimum]
