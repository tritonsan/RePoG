"""Create synthetic committed owners for a narrow clean-context reading probe.

Developer-only evidence; requires the repository's pytest fixture dependency.
This exercises transaction primitives, not a complete approved campaign/Distill.
Usage: python -B .../generate_owner_probe.py NEW_OUTPUT_DIRECTORY
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "tools")]
from test_rpg_state import campaign
from test_narrative_transactions import compass, threads, payload, cli_commit


def generate(target):
    target.mkdir(parents=True, exist_ok=False)
    owner = campaign.__wrapped__(target)
    state = (owner / "current_state.yaml").read_text(encoding="utf-8").replace("old_dock", "workshop").replace(
        "Warehouse Questions", "Ece's Workshop").replace("The interview is unresolved.", "The borrowed tool is being returned.").replace(
        "The interview continues.", "Ece is finishing a cabinet.")
    (owner / "current_state.yaml").write_text(state, encoding="utf-8")
    active = threads(compass())
    closed_body = compass(status="closed")
    closed = threads(closed_body)
    (owner / "threads.md").write_text(active, encoding="utf-8")
    (owner / "characters/ece.md").write_text(
        "# Ece Demir\n\nEstablished alias: Demir Usta\n\n"
        "Concrete economical speech, practical decisions, busy with a cabinet order.\n"
        "Relationship authority: relationship_map.md#ece-and-mira\n", encoding="utf-8")
    (owner / "relationship_map.md").write_text(
        "# Relationships\n\n## Ece and Mira\n"
        "Ece trusts Mira's craft. Their old unpaid account remains disputed; Ece will not lend money.\n"
        "Returning the smoothing plane intact before dusk permits the back room tonight only.\n"
        "No permanent key, future night, gift of tools, or settlement of the old account is promised.\n"
        "Ece is willing to discuss a one-month corner rental, paid up front, with tools agreed separately.\n",
        encoding="utf-8")
    initial_knowledge = """# Knowledge Boundaries
## Facts
### Plane return
- Fact id: plane_return
Mira still holds Ece's borrowed plane. Return has not happened.
## Holder Accounts
### Baran
- Account id: baran_report
- Holder ref: baran
- Fact id: plane_return
- Account: Tolga said Mira may have sold the plane; Baran has no direct evidence.
- Stance: suspected
- Source ref: Tolga's report at 14:00
- Learned at: day 1 14:00
- Recorded revision: 0
- Supersedes: none
- Correction ref: none
### Ada
- Account id: ada_uninformed
- Holder ref: ada
- Fact id: plane_return
- Account: Ada has heard neither the sale rumor nor any return outcome.
- Stance: unknown
- Source ref: synthetic setup
- Learned at: unknown
- Recorded revision: 0
- Supersedes: none
- Correction ref: none
"""
    (owner / "knowledge_boundaries.md").write_text(initial_knowledge, encoding="utf-8")
    requests, results = [], []

    def commit(value, command="commit-durable"):
        requests.append({"command": command, "payload": value})
        results.append(cli_commit(owner, value, command))

    close_request = payload("threads.md", active, closed, operation="close-return")
    successor = compass("act_work", previous="act_return", revision=2).replace(
        "What becomes of the borrowed tool?", "Can Mira establish independent work in the workshop corner?"
    ).replace("The tool is returned or its loss is established.",
              "Close when the first paid commission is completed, or Mira abandons this work attempt.")
    archive = "### act_return\n" + closed_body.replace("### Act Scope", "#### Act Scope").replace(
        "### Closure Record", "#### Closure Record")
    activate_request = payload("threads.md", closed, threads(successor, archive), 1, "activate-work")
    corrected = initial_knowledge.replace(
        "Mira still holds Ece's borrowed plane. Return has not happened.",
        "Mira returned the plane intact before dusk. Ece accepted it; the old unpaid account is unchanged."
    ).replace("Account id: baran_report", "Account id: baran_observed").replace(
        "Tolga said Mira may have sold the plane; Baran has no direct evidence.",
        "Baran saw Mira return the plane intact to Ece before dusk."
    ).replace("Stance: suspected", "Stance: confirmed").replace(
        "Source ref: Tolga's report at 14:00", "Source ref: direct observation at the workshop"
    ).replace("Learned at: day 1 14:00", "Learned at: day 1 17:00").replace(
        "Recorded revision: 0\n- Supersedes: none\n- Correction ref: none\n### Ada",
        "Recorded revision: 1\n- Supersedes: baran_report\n- Correction ref: direct witnessed return\n### Ada"
    )
    corrected += "\n## Historical Accounts\nBaran's superseded baran_report: suspected sale from Tolga's 14:00 report; replaced only after direct observation.\n"
    knowledge_request = payload("knowledge_boundaries.md", initial_knowledge, corrected)
    knowledge_request["changes"][0]["id"] = "witnessed-return"
    close_request["changes"].extend(knowledge_request["changes"])
    close_request["mutations"].extend(knowledge_request["mutations"])
    commit(close_request)
    commit(activate_request)
    anchor = "Ece asks Mira whether she wants tea now or after the cabinet work; Mira has not answered."
    commit({"operation_id": "reply-handoff", "expected_continuity_revision": 2,
            "checkpoint": {"scene_id": "dock-interview", "scene_mode": "focused",
                           "resume_anchor": anchor, "active_cast_handoff": "none"},
            "mutations": [{"path": "current_state.yaml", "exact_replacements": [{
                "old": "resume_anchor: The witness waits for the next question.",
                "new": "resume_anchor: " + anchor}]}]}, "commit-checkpoint")
    (owner / "session_brief.md").write_text("""# Session Brief
Prepared from revision: 2
## Triggered Lookups
### Demir Usta
- Lookup id: demir_terms
- Signals: Demir Usta, Ece, money, tools, room, workshop corner
- Owner ref: relationship_map.md#ece-and-mira
- Why now: A return or question about agreed terms.
- Verified at revision: 2
""", encoding="utf-8")
    packet = {
        "purpose": "Read-only restored-owner questions; not gameplay or full campaign validation.",
        "sources": ["current_state.yaml", "session_brief.md", "threads.md", "knowledge_boundaries.md",
                    "relationship_map.md", "characters/ece.md"],
        "questions": [
            "Demir Usta ile para, aletler ve arka oda konusunda hangi şartlar şu anda yürürlükte?",
            "Baran ve Ada rende hakkında ne biliyor; dayanakları aynı mı?",
            "Şu anki act ne zaman kapanabilir; rendenin dönmesi onu kapatmış mı?",
            "Oyuncunun hangi söze karşılık vermesi bekleniyor; seçim yapılmış mı?",
        ],
    }
    (target / "actor_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "mode": "focused_owner_probe", "full_workspace": False,
        "initialization": "Synthetic fixture owner materialization before the first operation.",
        "limitations": "No full setup/Distill or natural-turn capture; transaction primitive and stored-owner reading only.",
        "requests": requests, "results": results,
        "owner_sha256": {str(p.relative_to(owner)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in owner.rglob("*") if p.is_file() and ".repog-transactions" not in p.parts},
    }
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"target": str(target), "operations": len(results), "revision": results[-1]["continuity_revision"]}))


if __name__ == "__main__":
    generate(Path(sys.argv[1]).resolve())
