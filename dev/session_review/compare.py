"""Print the 0.4.0 success metrics (spec section 10) for one or two review work dirs.

    python compare.py WORK_A [WORK_B] [--labels A B] [--json]

A work dir holds turns.jsonl and quant.json from extract.py and, when the review
followed the README, check_full.json and campaign_copy/campaign/ (play_profile.yaml
for the bands; .repog-runtime/rolls.jsonl and lint_history.jsonl). An optional interventions.json (the review
workflow writes it: a list of {turn, likely_cause}) feeds the intervention
count. A missing source shows as n/a. Runtime rows count only inside the play
turns' time window, so a work dir cut with --since measures only its own turns.
The "met" column judges the last work dir against the target.

Every dir is measured the same way, so two games compare fairly:
- play turns: every turn of a --since extraction, else from the first turn
  that ran commit-durable;
- narrated turn: a play turn without OOC that has a reply text block of 200 or
  more characters;
- narrated first: committed turns (any that ran an rpg_state commit) whose
  narration came before the first commit. A committed turn with no
  narration-length text counts as not narrated first, as the capsule's
  [order] check reads it (repog_runtime.turn_order); the cell says how many
  there were;
- status lines: short reply lines (300 characters or less) in non-OOC play
  turns that hold an unambiguous backend phrase: a helper, rule or failure
  name (any snake_case word, such as `rpg_state` or `stale_revision`), a
  commit operation (`commit-durable`), a file name with a record, runtime or
  helper extension (`threads.md`, `rolls.jsonl`, `repog.sh`), or one of
  tr.json's meta phrases (spec 6.1, `distill` among them). Record verbs are
  not counted: clerks and logs are ordinary fiction, and first-person
  narration says "I'll write the records" too. Quoted speech is removed
  first; lines marked OOC and dialogue lines opening with a dash or a single
  quote are skipped;
- wait to narration: prompt to the first narration text block, median over
  narrated turns; "~20 s" counts as met up to 25 s;
- reachable bad band: a rolled (not auto) receipt that could land below the
  lowest success band, read as roll_dice reads it (the band a margin of 0
  lands in, and every band above it). A 0.4.0 receipt says so in
  `p_below_success`; an older one is worked out from its dice and margin
  against the campaign copy's bands (play_profile.yaml; the default bands
  without one). The cell also counts the rolls that could reach the worst
  band, the reading of the G2 baseline ("failure reachable in 1/35");
- empty distill with stale findings: a successful, non-repeated commit-distill
  that changed no record beyond the state, the log and archives, while its full
  check still reported a staleness or distill-gate warning not deferred to
  curation;
- standing warnings: the full check's warnings; acknowledged findings are info
  and shown apart (a warning whose message says some of its files are
  acknowledged still stands);
- "bir an": play turns whose reply contains it, over play turns with a reply;
  restating opening: narrated turns whose first sentence shares two or more
  word stems with the prompt and holds a second-person verb as the lint reads
  one (the tr and en packs' `second_person_patterns`, through lang_pack; the
  Turkish past tense is left out, as it reads the same as a genitive). The G2
  baseline counted 48/186 and 42/156. Without the packs' patterns the
  restating share is n/a;
- PC authoring: linted replies (the latest row per prompt) flagged
  `pc_authoring` or `pc_line_rewritten`, judged on the last third as the G2
  baseline is ("10% late"); the share over all replies is shown too;
- records in another language: files listed by an unacknowledged (warning)
  `records_language_mismatch` finding, acknowledged files shown apart (an info
  finding's files, plus the "N more acknowledged by" count of a partly
  acknowledged warning); a full check older than 0.4.0 has no such rule and
  reports 0.
"""

from __future__ import annotations

import argparse
import datetime as dt
import functools
import importlib.util
import json
import re
import statistics
from dataclasses import dataclass
from pathlib import Path

from extract import NARRATION_CHARS, ts

CAMPAIGN = Path("campaign_copy") / "campaign"
RUNTIME = CAMPAIGN / ".repog-runtime"
PLUGIN_TOOLS = Path(__file__).resolve().parents[2] / "plugin" / "tools"
WINDOW_SLACK = dt.timedelta(minutes=10)
PC_AUTHORING_RULES = ("pc_authoring", "pc_line_rewritten")
# roll_dice's bands for a campaign without a resolution block (odds.DEFAULT_BANDS).
DEFAULT_BANDS = ({"at_least": 0, "band": "success"}, {"at_least": -999, "band": "failure"})

# Backend phrases a Player should never see, kept to the unambiguous ones.
# Record verbs ("saving the records", "kaydettim") and words such as
# "revision" are left out: clerks, logs and bounty records are ordinary
# fiction, and first-person narration says "I'll write the records" too.
STATUS_RE = re.compile(
    "|".join(
        [
            # helper, rule and failure names: rpg_state, check_state, stale_revision
            r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b",
            # commit operations: commit-durable, commit-distill
            r"\bcommit-[a-z]+",
            # file names: records, runtime files and the helpers themselves
            r"\b[\w-]+\.(?:md|ya?ml|jsonl?|py|sh)\b",
            # tr.json's meta phrases (spec 6.1), as phrases
            r"\bkayıtlar tamam\b",
            r"\bkaydı tamamla",
            r"\bkayıt daha kaldı",
            r"\bkaydediyorum\b",
            r"\bkaydederken\b",
            r"\btablonun biçimi\b",
            r"\bdistill\b",
        ]
    ),
    re.IGNORECASE,
)
# A partly acknowledged records_language_mismatch warning gives its acknowledged
# files only as a count in its message (spec 9.3, C).
MORE_ACKNOWLEDGED_RE = re.compile(r"\b(\d+) more acknowledged by\b")
STATUS_LINE_CHARS = 300
# Quoted speech, removed before a line is matched; an unclosed quote runs to the line end.
QUOTED_RE = re.compile(r"„[^“”\n]*[“”]?|“[^”\n]*”?|\"[^\"\n]*\"?|«[^»\n]*»?")
# Dialogue lines whose speech has no span to remove: a dash, a closing quote
# used to open, or a single quote (also the Turkish apostrophe, so never a span).
DIALOGUE_LINE_MARKS = ("—", "–", "”", "'", "‘")

BIR_AN_RE = re.compile(r"(?<!\w)bir an(?!\w)")
WORD_RE = re.compile(r"[^\W\d_]{4,}")
SENTENCE_END_RE = re.compile(r"[.!?…](?:\s|$)")
# The packs that define `second_person_patterns` (spec 9.3, L).
SECOND_PERSON_PACKS = ("tr", "en")
STOPWORDS = frozenset(
    "ama için gibi daha sonra şimdi bunu şunu onun onlar benim senin bana sana evet hayır değil kadar "
    "olan olarak diye çünkü sadece hemen artık zaten yine böyle şöyle nasıl neden nerede "
    "that this with from then they them their there what when your have just into about will "
    "would could should were been after before still while over".split()
)


@dataclass
class Cell:
    """One measured value: the text shown and the number checked against the target."""

    text: str
    value: float | None = None


@dataclass
class Review:
    work: Path
    turns: list[dict]
    play: list[dict]
    rolls: list[dict] | None
    lint: list[dict] | None
    check: dict | None
    interventions: list[dict] | None
    bands: list[dict]


# ----------------------------------------------------------------- loading


def read_jsonl(path: Path) -> list[dict] | None:
    if not path.is_file():
        return None
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def read_json(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def play_turns(turns: list[dict], quant: dict) -> list[dict]:
    if quant.get("since"):
        return turns
    start = next((t["idx"] for t in turns if any("commit-durable" in h for h in t.get("helpers") or [])), None)
    return [t for t in turns if start is not None and t["idx"] >= start]


def in_window(rows: list[dict] | None, play: list[dict], turns: list[dict]) -> list[dict] | None:
    """Runtime rows written while the play turns ran (rows without a time stay)."""

    if rows is None or not play:
        return rows
    start, end = ts(play[0].get("prompt_ts")), ts(turns[-1].get("last_ts"))
    if start is None or end is None:
        return rows
    kept = []
    for row in rows:
        stamp = ts(row.get("at"))
        if stamp is None or start <= stamp <= end + WINDOW_SLACK:
            kept.append(row)
    return kept


def distinct_replies(rows: list[dict] | None) -> list[dict] | None:
    """One lint row per reply: a turn that ends twice keeps its latest row
    (presentation_lint.distinct_history)."""

    if rows is None:
        return None
    kept, seen = [], set()
    for row in reversed(rows):
        key = str(row.get("prompt_uuid") or "")
        if key:
            if key in seen:
                continue
            seen.add(key)
        kept.append(row)
    return kept[::-1]


@functools.lru_cache(maxsize=None)
def plugin_module(name: str):
    """A plugin tool module, loaded by path (the dev tools are not a package)."""

    spec = importlib.util.spec_from_file_location(f"repog_review_{name}", PLUGIN_TOOLS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def campaign_bands(work: Path) -> list[dict]:
    """The campaign copy's resolution bands, parsed by the plugin's own odds module.

    The default bands when the copy has no play_profile.yaml or no resolution
    block, or when the block cannot be read.
    """

    profile = work / CAMPAIGN / "play_profile.yaml"
    if not profile.is_file():
        return list(DEFAULT_BANDS)
    try:
        resolution = plugin_module("odds").load_resolution(profile.read_text(encoding="utf-8"))
    except Exception:  # a dev report must still print the other metrics
        return list(DEFAULT_BANDS)
    return list(resolution["bands"]) if resolution else list(DEFAULT_BANDS)


def load_review(work: Path) -> Review:
    turns = read_jsonl(work / "turns.jsonl") or []
    quant = read_json(work / "quant.json") or {}
    play = play_turns(turns, quant)
    check = read_json(work / "check_full.json")
    interventions = read_json(work / "interventions.json")
    if isinstance(interventions, dict):
        interventions = interventions.get("interventions")
    return Review(
        work=work,
        turns=turns,
        play=play,
        rolls=in_window(read_jsonl(work / RUNTIME / "rolls.jsonl"), play, turns),
        lint=in_window(distinct_replies(read_jsonl(work / RUNTIME / "lint_history.jsonl")), play, turns),
        check=check if isinstance(check, dict) else None,
        interventions=interventions if isinstance(interventions, list) else None,
        bands=campaign_bands(work),
    )


# ------------------------------------------------------------- text checks


def tr_lower(text: str) -> str:
    return text.replace("I", "ı").replace("İ", "i").lower()


def narration_text(turn: dict) -> str | None:
    return next((text for text in turn.get("texts") or [] if len(text) >= NARRATION_CHARS), None)


def narrated(review: Review) -> list[dict]:
    return [t for t in review.play if not t.get("ooc") and narration_text(t)]


def status_lines(turn: dict) -> list[str]:
    found = []
    for text in turn.get("texts") or []:
        for line in text.splitlines():
            line = line.strip().lstrip("*_> ")
            if not line or len(line) > STATUS_LINE_CHARS or "OOC" in line.upper():
                continue
            if line.startswith(DIALOGUE_LINE_MARKS):
                continue
            if STATUS_RE.search(QUOTED_RE.sub(" ", line).strip()):
                found.append(line)
    return found


@functools.lru_cache(maxsize=1)
def second_person_rules() -> tuple:
    """(fold, ((pack, patterns), ...)): the packs' second-person verbs, read as
    the lint reads them; no rules when lang_pack or the patterns are missing."""

    try:
        lang_pack = plugin_module("lang_pack")
        packs = [lang_pack.load_pack(code) for code in SECOND_PERSON_PACKS]
        rules = tuple((pack, tuple(lang_pack.compile_patterns(pack, "second_person_patterns"))) for pack in packs)
        return lang_pack.fold, tuple((pack, patterns) for pack, patterns in rules if patterns)
    except Exception:  # a dev report must still print the other metrics
        return None, ()


def second_person(text: str) -> bool:
    fold, rules = second_person_rules()
    return any(pattern.search(fold(text, pack)) for pack, patterns in rules for pattern in patterns)


def stems(text: str) -> set[str]:
    return {word[:5] for word in WORD_RE.findall(tr_lower(text)) if word not in STOPWORDS}


def opening_sentence(text: str) -> str:
    body = text.strip().lstrip("*_>#\"'“”«—–- ")
    end = SENTENCE_END_RE.search(body)
    return body[: end.end()] if end and end.end() <= 300 else body[:300]


def restates(prompt: str, narration: str) -> bool:
    asked = stems(prompt)
    if len(asked) < 2:
        return False
    first = opening_sentence(narration)
    return len(stems(first) & asked) >= 2 and second_person(first)


# --------------------------------------------------------------- receipts


def is_rolled_receipt(row: dict) -> bool:
    return row.get("kind", "roll") != "reread" and isinstance(row.get("roll_id"), str) and not row.get("auto")


def worst_margin(row: dict) -> int | None:
    """The margin with every die at 1, for a plain NdS receipt."""

    match = re.fullmatch(r"(\d+)d(\d+)", str(row.get("die") or ""))
    dice, margin = row.get("dice"), row.get("margin")
    if not match or not isinstance(dice, list) or not isinstance(margin, int):
        return None
    if len(dice) != int(match.group(1)) or not all(isinstance(face, int) for face in dice):
        return None
    return margin - sum(dice) + len(dice)


def lowest_success(bands) -> int:
    """The index of the lowest success band, as roll_dice.success_bands reads it.

    It is the band a margin of 0 lands in; the last band catches every lower
    margin, so it is a success only on a one-band scale.
    """

    index = next((i for i, band in enumerate(bands) if band["at_least"] <= 0), len(bands) - 1)
    return min(index, max(len(bands) - 2, 0))


def bad_band_reachable(row: dict, bands=DEFAULT_BANDS) -> bool | None:
    """Whether the roll could land below the lowest success band; None when unknown."""

    chance = row.get("p_below_success")
    if isinstance(chance, (int, float)) and not isinstance(chance, bool):
        return chance > 0
    if row.get("certain") is True:
        return False
    worst = worst_margin(row)
    if worst is None:
        return None
    lowest = lowest_success(bands)
    return lowest < len(bands) - 1 and worst < bands[lowest]["at_least"]


def worst_band_reachable(row: dict, bands=DEFAULT_BANDS) -> bool | None:
    """Whether the roll could land in the scale's worst band; None when unknown."""

    worst = worst_margin(row)
    if worst is not None:
        return len(bands) > 1 and worst < bands[-2]["at_least"]
    reachable = row.get("reachable_bands")
    if isinstance(reachable, list) and reachable:
        return bands[-1]["band"] in reachable
    return None


# ----------------------------------------------------------------- metrics


def percent(part: float, whole: float) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "n/a"


def ratio(part: int, whole: int) -> Cell:
    return Cell(f"{part}/{whole} ({percent(part, whole)})", part / whole if whole else None)


NA = Cell("n/a")


def m_narrated_first(review: Review) -> Cell:
    if not review.turns:
        return NA
    committed = [t for t in review.play if t.get("order") not in (None, "no_commit")]
    cell = ratio(sum(t["order"] == "narrate_first" for t in committed), len(committed))
    unnarrated = sum(t["order"] == "commit_no_long_text" for t in committed)
    return Cell(cell.text + (f", {unnarrated} without narration" if unnarrated else ""), cell.value)


def m_status_lines(review: Review) -> Cell:
    if not review.turns:
        return NA
    count = sum(len(status_lines(t)) for t in review.play if not t.get("ooc"))
    return Cell(str(count), count)


def m_narration_wait(review: Review) -> Cell:
    waits = [t["narration_wait_s"] for t in narrated(review) if t.get("narration_wait_s") is not None]
    if not waits:
        return NA
    value = statistics.median(waits)
    return Cell(f"{value:.0f} s", value)


def _known(flags) -> list[bool]:
    return [flag for flag in flags if flag is not None]


def m_bad_band_rolls(review: Review) -> Cell:
    if review.rolls is None:
        return NA
    rolled = [row for row in review.rolls if is_rolled_receipt(row)]
    bad = _known(bad_band_reachable(row, review.bands) for row in rolled)
    worst = _known(worst_band_reachable(row, review.bands) for row in rolled)
    auto = sum(1 for row in review.rolls if row.get("auto") and row.get("kind", "roll") != "reread")
    cell = ratio(sum(bad), len(bad))
    extras = [f"worst band {sum(worst)}/{len(worst)}"] if worst else []
    extras += [f"{len(rolled) - len(bad)} unknown"] if len(bad) < len(rolled) else []
    extras += [f"{auto} auto"] if auto else []
    return Cell(cell.text + (f", {', '.join(extras)}" if extras else ""), cell.value)


def m_empty_distills(review: Review) -> Cell:
    if not review.turns:
        return NA
    distills = [d for t in review.play for d in t.get("distills") or [] if d.get("ok") and not d.get("idempotent")]
    empty = sum(1 for d in distills if not d.get("changed_records") and d.get("stale_rules"))
    return Cell(f"{empty}/{len(distills)}", empty)


def is_acknowledged(finding: dict) -> bool:
    """A finding a directive acknowledged: the full check turns it into info and names the directive.

    A warning that only says some of its files are acknowledged still stands.
    """

    return finding.get("severity") == "info" and bool(
        finding.get("acknowledged_by") or "acknowledged by" in str(finding.get("message") or "")
    )


def m_standing_warnings(review: Review) -> Cell:
    if review.check is None:
        return NA
    findings = [f for f in review.check.get("findings") or [] if isinstance(f, dict)]
    count = review.check.get("warning_count")
    if not isinstance(count, int):
        count = sum(1 for f in findings if f.get("severity") == "warning")
    acknowledged = sum(1 for f in findings if is_acknowledged(f))
    return Cell(f"{count}" + (f" ({acknowledged} acknowledged)" if acknowledged else ""), count)


def m_bir_an_restating(review: Review) -> Cell:
    replied = [t for t in review.play if t.get("texts")]
    turns = narrated(review)
    if not turns:
        return NA
    bir_an = sum(1 for t in replied if BIR_AN_RE.search(tr_lower("\n".join(t["texts"]))))
    bir_an_text = f"{percent(bir_an, len(replied))} of {len(replied)}"
    if not second_person_rules()[1]:
        return Cell(f"{bir_an_text} / n/a")
    restating = sum(1 for t in turns if restates(t.get("prompt") or "", narration_text(t)))
    return Cell(
        f"{bir_an_text} / {percent(restating, len(turns))} of {len(turns)}",
        max(bir_an / len(replied), restating / len(turns)),
    )


def _pc_flagged(row: dict) -> bool:
    counts = row.get("counts") or {}
    return any(counts.get(rule) for rule in PC_AUTHORING_RULES)


def m_pc_authoring(review: Review) -> Cell:
    if not review.lint:
        return NA
    rows = review.lint
    late = rows[len(rows) - len(rows) // 3 :] if len(rows) >= 3 else rows
    flagged = sum(1 for row in rows if _pc_flagged(row))
    flagged_late = sum(1 for row in late if _pc_flagged(row))
    return Cell(
        f"{percent(flagged_late, len(late))} late, {percent(flagged, len(rows))} of {len(rows)}",
        flagged_late / len(late),
    )


def m_model_interventions(review: Review) -> Cell:
    if review.interventions is None:
        ooc = sum(1 for t in review.play if t.get("ooc"))
        return Cell(f"n/a (OOC play turns: {ooc})") if review.turns else NA
    turns = {t["idx"] for t in review.turns}
    count = sum(
        1
        for item in review.interventions
        if isinstance(item, dict)
        and item.get("likely_cause") == "model_error"
        and (not isinstance(item.get("turn"), int) or item["turn"] in turns)
    )
    return Cell(str(count), count)


def m_failed_commits(review: Review) -> Cell:
    if not review.turns:
        return NA
    calls = sum(int(t.get("commit_calls") or 0) for t in review.play)
    return ratio(sum(int(t.get("commit_failures") or 0) for t in review.play), calls)


def _finding_files(finding: dict) -> set[str]:
    listed = finding.get("paths") or finding.get("files")
    if isinstance(listed, list):
        return {str(path) for path in listed}
    named = re.findall(r"[\w./\\-]+\.(?:md|ya?ml|json)\b", str(finding.get("message") or ""))
    return set(named or [str(finding.get("path") or "?")])


def language_mismatch_files(check: dict) -> tuple[set[str], int]:
    """The files unacknowledged `records_language_mismatch` findings list, and
    how many files directives acknowledged.

    An acknowledged finding is info and lists its files; a partly acknowledged
    warning lists only its open files and gives the rest as "N more
    acknowledged by" in its message.
    """

    open_files: set[str] = set()
    acknowledged: set[str] = set()
    counted = 0
    for finding in check.get("findings") or []:
        if not isinstance(finding, dict) or finding.get("rule") != "records_language_mismatch":
            continue
        if finding.get("severity", "warning") == "info":
            acknowledged |= _finding_files(finding)
            continue
        open_files |= _finding_files(finding)
        more = MORE_ACKNOWLEDGED_RE.search(str(finding.get("message") or ""))
        counted += int(more.group(1)) if more else 0
    return open_files, len(acknowledged) + counted


def m_records_language(review: Review) -> Cell:
    if review.check is None:
        return NA
    open_files, acknowledged = language_mismatch_files(review.check)
    count = len(open_files)
    return Cell(f"{count} files" + (f" ({acknowledged} acknowledged)" if acknowledged else ""), count)


METRICS = [
    ("narrated_first", "Committed turns narrated first", "90%+", m_narrated_first, lambda v: v >= 0.9),
    ("status_lines", "Status lines the Player saw", "0", m_status_lines, lambda v: v == 0),
    ("narration_wait", "Median wait to narration", "~20 s", m_narration_wait, lambda v: v <= 25),
    ("bad_band_rolls", "Rolls with a reachable bad band", "every roll made", m_bad_band_rolls, lambda v: v >= 1),
    ("empty_distills", "Empty distills with stale findings", "0", m_empty_distills, lambda v: v == 0),
    ("standing_warnings", "Standing warnings", "0 unacknowledged", m_standing_warnings, lambda v: v == 0),
    ("bir_an_restating", '"bir an" / restating openings', "under 10%", m_bir_an_restating, lambda v: v < 0.10),
    ("pc_authoring", "PC authoring (lint)", "under 3%", m_pc_authoring, lambda v: v < 0.03),
    ("model_interventions", "Model-error interventions", "under 10", m_model_interventions, lambda v: v < 10),
    ("failed_commits", "Failed commit calls", "under 5%", m_failed_commits, lambda v: v < 0.05),
    ("records_language", "Records in another language", "none", m_records_language, lambda v: v == 0),
]


def measure(work: Path) -> dict[str, Cell]:
    review = load_review(Path(work))
    return {key: function(review) for key, _, _, function, _ in METRICS}


def met(cell: Cell, check) -> bool | None:
    return None if cell.value is None else bool(check(cell.value))


# ------------------------------------------------------------------- output


def table(labels: list[str], results: list[dict[str, Cell]]) -> str:
    head = ["Metric", *labels, "Target", f"Met ({labels[-1]})"]
    lines = ["| " + " | ".join(head) + " |", "|" + " --- |" * len(head)]
    for key, label, target, _, check in METRICS:
        verdict = met(results[-1][key], check)
        mark = "n/a" if verdict is None else ("yes" if verdict else "no")
        lines.append("| " + " | ".join([label, *(r[key].text for r in results), target, mark]) + " |")
    return "\n".join(lines)


def as_json(labels: list[str], results: list[dict[str, Cell]]) -> dict:
    return {
        "dirs": labels,
        "metrics": [
            {
                "key": key,
                "label": label,
                "target": target,
                "values": [
                    {"text": r[key].text, "value": r[key].value, "met": met(r[key], check)} for r in results
                ],
            }
            for key, label, target, _, check in METRICS
        ],
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("work", nargs="+", help="one or two work dirs from extract.py")
    parser.add_argument("--labels", nargs="+", help="column names (default: the dir names)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a Markdown table")
    args = parser.parse_args(argv)
    if len(args.work) > 2:
        parser.error("compare takes one or two work dirs")
    labels = args.labels or [Path(work).resolve().name for work in args.work]
    if len(labels) != len(args.work):
        parser.error("give one label per work dir")
    results = [measure(Path(work)) for work in args.work]
    if args.json:
        print(json.dumps(as_json(labels, results), ensure_ascii=False, indent=1))
    else:
        print(table(labels, results))


if __name__ == "__main__":
    main()
