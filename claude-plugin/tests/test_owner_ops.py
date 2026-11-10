from __future__ import annotations

import pytest

import owner_ops
from conftest import CURRENT_STATE


def _yaml(ops: list[dict], text: str = CURRENT_STATE) -> str:
    return owner_ops.apply_ops(
        text,
        owner_ops.parse_ops(ops, relative="current_state.yaml", label="m"),
        relative="current_state.yaml",
        label="m",
        placeholders=owner_ops.PlaceholderContext(5),
    )


def _md(text: str, ops: list[dict], *, revision: int = 5) -> str:
    return owner_ops.apply_ops(
        text,
        owner_ops.parse_ops(ops, relative="notes.md", label="m"),
        relative="notes.md",
        label="m",
        placeholders=owner_ops.PlaceholderContext(revision),
    )


def test_set_nested_values_keeps_everything_else() -> None:
    result = _yaml(
        [
            {
                "op": "set",
                "values": {
                    "current_scene.summary": "Mira leaves; the witness \"waits\".",
                    "scene_frame.last_causal_beat.changed_fact": "The witness named Ilse.",
                    "fictional_time.day": 2,
                },
            }
        ]
    )
    assert '  summary: "Mira leaves; the witness \\"waits\\"."\n' in result
    assert '    changed_fact: "The witness named Ilse."\n' in result
    assert "  day: 2\n" in result
    assert "  # A comment that belongs to the player block.\n" in result
    assert result.count("\n") == CURRENT_STATE.count("\n")


def test_set_bare_token_stays_bare_and_reserved_words_are_quoted() -> None:
    result = _yaml([{"op": "set", "values": {"scene_frame.mode": "crisis", "fictional_time.phase": "yes"}}])
    assert "  mode: crisis\n" in result
    assert '  phase: "yes"\n' in result


@pytest.mark.parametrize(
    ("key", "message"),
    [
        ("persistence.durable_turns_since_distill", "managed by the writer"),
        ("continuity_revision", "managed by the writer"),
        ("current_scene.mood", "does not exist"),
        ("scene_frame", "nested keys"),
        ("current_scene.present_npcs", "is a list"),
    ],
)
def test_set_refuses_protected_missing_and_structured_keys(key: str, message: str) -> None:
    with pytest.raises(owner_ops.OwnerOpError, match=message):
        _yaml([{"op": "set", "key": key, "value": "x"}])


def test_list_operations_round_trip() -> None:
    result = _yaml([{"op": "list_add", "key": "current_scene.present_npcs", "items": ["Witness", "Ilse"]}])
    assert '  present_npcs:\n    - "Witness"\n    - "Ilse"\n' in result
    again = _yaml([{"op": "list_add", "key": "current_scene.present_npcs", "items": "Ilse"}], result)
    assert again == result
    removed = _yaml([{"op": "list_remove", "key": "current_scene.present_npcs", "items": ["Witness"]}], result)
    assert '  present_npcs:\n    - "Ilse"\n  immediate_pressure' in removed
    cleared = _yaml([{"op": "list_set", "key": "current_scene.present_npcs", "items": []}], removed)
    assert "  present_npcs: []\n" in cleared


def test_list_remove_of_missing_item_names_current_items() -> None:
    with pytest.raises(owner_ops.OwnerOpError, match=r"current items: \[\]"):
        _yaml([{"op": "list_remove", "key": "current_scene.present_npcs", "items": ["Nobody"]}])


NOTE = """# Note

## Agency Card

- Tier: T2

## Current State

Old state.

## Voice

Short sentences.
"""


def test_append_replace_remove_and_insert_sections() -> None:
    appended = _md(NOTE, [{"op": "append", "heading": "Agency Card", "text": "- Hard boundary: never lies to kin"}])
    assert "- Tier: T2\n- Hard boundary: never lies to kin\n\n## Current State" in appended
    replaced = _md(appended, [{"op": "replace_section", "heading": "## Current State", "text": "New state."}])
    assert "## Current State\n\nNew state.\n\n## Voice" in replaced
    assert "Old state." not in replaced
    removed = _md(replaced, [{"op": "remove_section", "heading": "Voice"}])
    assert "## Voice" not in removed and removed.endswith("New state.\n\n")
    inserted = _md(removed, [{"op": "insert_section", "heading": "## Ties", "text": "Owes Mira a favour."}])
    assert inserted.rstrip().endswith("## Ties\n\nOwes Mira a favour.")


def test_insert_refuses_to_stack_a_duplicate_heading() -> None:
    with pytest.raises(owner_ops.OwnerOpError, match="replace_section"):
        _md(NOTE, [{"op": "insert_section", "heading": "## Current State", "text": "Another layer."}])


def test_ambiguous_or_missing_heading_fails_loudly() -> None:
    doubled = NOTE + "\n## Current State\n\nStacked layer.\n"
    with pytest.raises(owner_ops.OwnerOpError, match="matched 2 headings"):
        _md(doubled, [{"op": "replace_section", "heading": "Current State", "text": "x"}])
    with pytest.raises(owner_ops.OwnerOpError, match="headings here"):
        _md(NOTE, [{"op": "append", "heading": "Secrets", "text": "x"}])


def test_under_disambiguates_nested_headings() -> None:
    text = "# K\n\n## Player\n\n### Notes\n\nA\n\n## NPC\n\n### Notes\n\nB\n"
    result = _md(text, [{"op": "append", "heading": "Notes", "under": "NPC", "text": "C"}])
    assert result.endswith("### Notes\n\nB\nC\n")


def test_headings_inside_code_fences_are_ignored() -> None:
    text = "# K\n\n```\n## Current State\n```\n\n## Current State\n\nReal.\n"
    result = _md(text, [{"op": "replace_section", "heading": "Current State", "text": "Updated."}])
    assert "```\n## Current State\n```" in result and result.endswith("Updated.\n")


TABLE = """# Map

| From | Direction | To | Relation |
| --- | --- | --- | --- |
| Mira | -> | Witness | wary |
| Mira | -> | Courier | hunting |
"""


def test_upsert_row_with_composite_key_and_delete() -> None:
    updated = _md(
        TABLE,
        [{"op": "upsert_row", "key": ["Mira", "->", "Witness"], "cells": ["Mira", "->", "Witness", "trusting | wary"]}],
    )
    assert "| Mira | -> | Witness | trusting \\| wary |\n" in updated
    added = _md(updated, [{"op": "upsert_row", "key": ["Ilse", "->", "Mira"], "cells": ["Ilse", "->", "Mira", "owes"]}])
    assert added.endswith("| Ilse | -> | Mira | owes |\n")
    deleted = _md(added, [{"op": "delete_row", "key": ["Mira", "->", "Courier"]}])
    assert "Courier" not in deleted


def test_upsert_row_rejects_ambiguous_key_and_wrong_width() -> None:
    with pytest.raises(owner_ops.OwnerOpError, match="matches 2 rows"):
        _md(TABLE, [{"op": "upsert_row", "key": "Mira", "cells": ["Mira", "->", "X", "y"]}])
    with pytest.raises(owner_ops.OwnerOpError, match="exactly 4 cells"):
        _md(TABLE, [{"op": "upsert_row", "key": ["Ilse"], "cells": ["Ilse", "->"]}])


def test_placeholders_allocate_padded_ids_once_per_payload() -> None:
    text = "# K\n\n- Fact id: PC-019\n- Fact id: PC-020\n"
    result = _md(
        text,
        [
            {"op": "append", "text": "- Fact id: {{next_id:PC}} (revision {{revision}})"},
            {"op": "append", "text": "- Fact id: {{next_id:PC}}"},
        ],
        revision=12,
    )
    assert "- Fact id: PC-021 (revision 12)\n" in result
    assert result.endswith("- Fact id: PC-022\n")


def test_stamp_and_stacked_heading_detection() -> None:
    assert owner_ops.stamp_revision("# A\n\nAs of revision: 3\n", 9) == "# A\n\nAs of revision: 9\n"
    assert owner_ops.stamp_revision("# A\n", 9) == "# A\n"
    stacked = "# N\n\n## State On Day 289\n\na\n\n## State On Day 389\n\nb\n\n## State On Day 737 (current)\n\nc\n"
    assert owner_ops.stacked_headings(stacked) == [("State On Day 289", 3)]
    distinct = "# N\n\n### Tamsin\n\na\n\n### Tessa\n\nb\n\n### Tom\n\nc\n"
    assert owner_ops.stacked_headings(distinct) == []


def test_yaml_ops_are_refused_for_markdown_and_vice_versa() -> None:
    with pytest.raises(owner_ops.OwnerOpError, match="not available"):
        owner_ops.parse_ops([{"op": "append", "text": "x"}], relative="current_state.yaml", label="m")
    with pytest.raises(owner_ops.OwnerOpError, match="not available"):
        owner_ops.parse_ops([{"op": "set", "key": "a", "value": "b"}], relative="threads.md", label="m")


def test_fold_now_keeps_crlf_line_endings() -> None:
    note = (
        "# N\r\n\r\n## Now\r\n\r\n- Day 1: a.\r\n- Day 2: b.\r\n- Day 3: c.\r\n- Day 4: d.\r\n"
        "\r\n## Agency Card\r\n\r\n- Tier: T2\r\n"
    )
    folded, moved = owner_ops.fold_now(note)
    assert moved == 1 and "\n" not in folded.replace("\r\n", "")
    assert "## Now\r\n\r\n- Day 2: b.\r\n- Day 3: c.\r\n- Day 4: d.\r\n\r\n## History\r\n\r\n- Day 1: a.\r\n\r\n## Agency Card" in folded
    assert owner_ops.fold_now(folded) == (folded, 0)


def test_set_fields_replaces_in_place_and_appends_missing_fields() -> None:
    text = "# T\n\n## Arc Compass\n\n<!--\n- Act status: example\n-->\n\n- Act status: active\n\n## Other\n"
    result = owner_ops.set_fields(text, "Arc Compass", {"Act status": "closed", "Recorded at revision": "4"})
    assert "- Act status: example" in result  # guidance inside a comment is never a field
    assert "- Act status: closed\n- Recorded at revision: 4\n\n## Other\n" in result
    assert owner_ops.section_body(result, "Other") == []
    with pytest.raises(owner_ops.OwnerOpError, match="exactly one"):
        owner_ops.set_fields(text, "Missing", {"A": "b"})


def test_core_status_and_table_rows() -> None:
    note = "# W\n\n## Core\n\n- Status: dead (drowned)\n- Kin: none\n"
    assert owner_ops.core_status(note) == "dead (drowned)"
    assert owner_ops.core_status("# W\n\n- Status: dead\n") == ""
    assert owner_ops.table_rows(TABLE) == (
        ["From", "Direction", "To", "Relation"],
        [["Mira", "->", "Witness", "wary"], ["Mira", "->", "Courier", "hunting"]],
    )
    assert owner_ops.table_rows("# none\n") == ([], [])
