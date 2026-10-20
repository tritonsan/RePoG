"""Presentation lint: the pure rules over tr, en and de replies, campaign context, the Stop hook and the CLI."""

from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

import presentation_lint
from lang_pack import load_pack
from presentation_lint import (
    FINGERPRINT_MAX,
    LINT_HISTORY,
    LINT_LAST,
    SUMMARY_MAX,
    campaign_avoid_phrases,
    distinct_history,
    glossary_variants,
    lint_reply,
    protected_names,
    report,
    resolve_language,
    run_hook,
)
from repog_runtime import read_jsonl


TOOLS = Path(presentation_lint.__file__).resolve().parent
TEMPLATES = TOOLS.parent / "templates" / "campaign"
SCRIPT = TOOLS / "presentation_lint.py"

CLEAN = {
    "tr": (
        "Halvar'a kapıyı kimin kilitlediğini soruyorum.",
        "Halvar kapının önünde durdu ve sana döndü. Avludaki fenerin ışığı yüzüne vuruyordu. "
        '"Bu gece kimse dışarı çıkmayacak," dedi alçak sesle. Uzaktan bir köpeğin havlaması duyuldu.',
    ),
    "en": (
        "I head down to the cellar with Marta.",
        "Cold air rises from the cellar. The stairs are slick with old rain, and somewhere below a drip "
        'keeps time. Marta lifts her lantern higher. "Watch the fourth step," she says. "It gave way last winter."',
    ),
    "de": (
        "Ich frage den Schmied nach dem Schwert.",
        "Der Schmied legt den Hammer auf den Amboss und wischt sich die Hände an der Schürze ab. Draußen "
        'schlägt die Glocke zur Mittagszeit. "Komm morgen wieder," sagt er ruhig. "Dann ist das Eisen kalt."',
    ),
}
PROMPT_TR = "Halvar'a kapıyı kimin kilitlediğini ve neden bu gece kimsenin çıkmadığını soruyorum."

KNOWLEDGE = """# Knowledge Boundaries

## Protected Proper Nouns

### Protected Name

- Fact id:
- Status: GM-only, foreshadowable, PC-known, companion-known, NPC-known, or
  revealed.

### Kül Varisi / Ashen Heir (F-007)

- Fact id: F-007
- Status: GM-only
- NPCs or factions who know: Edric; the Guild

### Ayla

- Fact id: F-002
- Status: revealed at revision 12
- NPCs or factions who know: none

## Player And Character Knowledge

### Not A Protected Entry

- Status: GM-only
"""

GLOSSARY = """# Glossary

<!--
e.g. | span of time | bell | hour, minute | Clock minutes are anachronistic. |
-->

| Notes | Variants | Term | Preferred |
| --- | --- | --- | --- |
| Spoken alone. | harbourmaster, port lord; Warden | harbor master | Harbor Warden |
| | — | bell | bell |
"""


@pytest.fixture(autouse=True)
def _isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Campaign discovery must only find what a test sets up."""

    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)


def _write(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _write(path, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def _lint(texts, *, code: str, prompt: str = "", descriptions=(), history=(), **context) -> dict:
    context.setdefault("play_language", code)
    texts = [texts] if isinstance(texts, str) else list(texts)
    return lint_reply(prompt, texts, list(descriptions), pack=load_pack(code), context=context, history=list(history))


def _rules(result: dict) -> dict[str, dict]:
    return {finding["rule"]: finding for finding in result["findings"]}


def _history(replies: list[str], code: str) -> list[dict]:
    """Earlier reply records shaped as the hook stores them."""

    records = []
    for reply in replies:
        result = _lint(reply, code=code)
        records.append({"fingerprint": result["fingerprint"], "trigrams": result["trigrams"]})
    return records


# ---------------------------------------------------------------------------
# Pure rules
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("code", sorted(CLEAN))
def test_clean_reply_yields_an_empty_summary(code: str) -> None:
    prompt, reply = CLEAN[code]
    result = _lint(reply, code=code, prompt=prompt, day=92, revision=412, player_name="Mira")
    assert result["findings"] == [] and result["counts"] == {} and result["summary"] == ""
    assert result["language"] == code and result["words"] > 20
    assert result["fingerprint"] and result["trigrams"]


def test_turkish_reply_flags_an_english_status_line_and_tool_description() -> None:
    texts = [
        "Halvar kapının önünde durdu ve sana döndü, fenerin ışığı yüzüne vuruyordu.",
        "Saving the scene and the campaign state now.",
    ]
    result = _lint(texts, code="tr", descriptions=["Commit the durable turn to the campaign", "Sahneyi kaydet"])
    finding = _rules(result)["out_of_language"]
    assert finding["count"] == 2
    assert finding["evidence"] == [
        "Saving the scene and the campaign state now.",
        "[tool] Commit the durable turn to the campaign",
    ]
    assert result["summary"].startswith('Last reply: 1 English line: "Saving the scene')
    assert '1 English tool description: "Commit the durable turn' in result["summary"]


def test_turkish_case_endings_after_names_do_not_read_as_english() -> None:
    reply = (
        "Edric'in kılıcı Halvar'ın elinde, Mira'nın gözü Edric'i izliyor. "
        "Halvar'a ve Edric'e baktın, sonra Mira'ya döndün."
    )
    assert "out_of_language" not in _rules(_lint(reply, code="tr"))


@pytest.mark.parametrize(
    "sentence",
    [
        # A title that is a Spanish function word ("ser"), twice.
        "Turnuvanın galibi Ser Aldric Venn, Ser Tomas Hale'i ilk turda yenmişti.",
        # Turkish "her" is a Turkish function word too, so only "an" is left for English.
        "Kervancılar yükleri almaya her an gelebilir.",
        # Two Spanish-looking words ("el", "para") in a sentence of ten.
        "Pazarın ortasında uzun pazarlık: tuz, deri, kumaş, el değiştiren para.",
        # One Spanish-looking word twice ("al al").
        "Koşarak yanına gelen çocuğun yanakları al al olmuş.",
        # A short quoted foreign phrase.
        'Kapıdaki yazıda "for the king" vardı.',
    ],
)
def test_out_of_language_ignores_names_shared_words_and_short_quotes(sentence: str) -> None:
    assert "out_of_language" not in _rules(_lint(sentence, code="tr"))


def test_out_of_language_reads_short_tool_descriptions_and_needs_a_pack() -> None:
    result = _lint("Halvar kapıyı kapattı.", code="tr", descriptions=["Saving the scene", "Sahnenin son durumunu kaydediyorum"])
    assert _rules(result)["out_of_language"]["evidence"] == ["[tool] Saving the scene"]
    german = _lint("Der Schmied nickt.", code="de", descriptions=["Speichere die Szene", "Rolling the dice"])
    assert _rules(german)["out_of_language"]["evidence"] == ["[tool] Rolling the dice"]
    # Without a pack for the play language there is nothing to compare against.
    unknown = _lint("This is plainly an English sentence about the harbor and the gulls.", code="pt")
    assert "out_of_language" not in _rules(unknown)


def test_prose_hides_ooc_blocks_and_markdown_structure_in_place() -> None:
    text = (
        "Halvar kapıyı açtı.\n"
        "(OOC: Zar 5, başarı.)\n"
        "Avlu boştu.\n\n"
        "*(OOC: İki not var.\n\nİkincisi şu.)*\n\n"
        "Rüzgâr esti.\n\n"
        "**OOC:** Taslak aşağıda.\n\n"
        "Bu da taslağın parçası.\n\n"
        "---\n\n"
        "## Başlık\n"
        "- madde\n"
        "> alıntı\n"
        "| a | b |\n"
        "Gece çöktü.\n\n"
        "---\n\n"
        "[OOC] Son not."
    )
    prose = presentation_lint._prose(text)
    assert len(prose) == len(text)
    assert [line.strip() for line in prose.splitlines() if line.strip()] == [
        "Halvar kapıyı açtı.",
        "Avlu boştu.",
        "Rüzgâr esti.",
        "Gece çöktü.",
    ]


def test_german_reply_flags_an_english_line_a_day_number_and_pc_speech() -> None:
    reply = (
        "Der Schmied sieht dich lange an. Du sagst, dass du morgen wiederkommst. Am Tag 92 regnet es. "
        "I will now save the scene and update the campaign file."
    )
    rules = _rules(_lint(reply, code="de", day=92))
    assert rules["out_of_language"]["evidence"] == ["I will now save the scene and update the campaign file."]
    assert rules["tracker_leak"]["count"] == 1
    assert rules["pc_authoring"]["count"] == 1


def test_tracker_day_as_digits_and_as_a_spelled_turkish_ordinal() -> None:
    reply = (
        "Altı yüz doksan ikinci gün sabahı avlu sessizdi. 692. gün de böyle başlamıştı; "
        'Halvar "Kayıtta 1412 yazıyor," dedi.'
    )
    result = _lint(reply, code="tr", day=692, revision=1412)
    finding = _rules(result)["tracker_leak"]
    assert finding["count"] == 3  # spelled ordinal, "692. gün", the bare revision (in speech too)
    assert "Altı yüz doksan ikinci gün" in finding["evidence"][0] and "692. gün" in finding["evidence"][1]
    assert 'tracker number in prose: "Altı yüz doksan ikinci gün"' in result["summary"]


def test_ordinary_numbers_are_not_tracker_leaks() -> None:
    # Small counts that happen to equal the day or revision are coincidences.
    result = _lint("Kapıda 3 muhafız, avluda 12 at bekliyordu ve avlu sessizdi.", code="tr", day=3, revision=12)
    assert "tracker_leak" not in _rules(result)
    # A large value inside a longer number ("1.692 gümüş") is not the day either.
    result = _lint("Kesende 1.692 gümüş ve 692,5 okka tuz vardı.", code="tr", day=692, revision=692)
    assert "tracker_leak" not in _rules(result)
    result = _lint("You count 1,692 coins and 12 arrows.", code="en", day=692, revision=12)
    assert "tracker_leak" not in _rules(result)


def test_tracker_numbers_in_an_ooc_plan_are_not_prose() -> None:
    reply = (
        "(OOC) Atlama taslağı aşağıda; onaylarsan kaydederim.\n\n"
        "## Gün 692 → 735\n\n"
        "- 700. gün: Tobin yola çıkıyor.\n"
        "| 710. gün | Kervan gelir |\n\n"
        "Yedi yüz yirminci gün civarında ilk kar düşüyor.\n\n"
        "---\n\n"
        "Kış erken geldi. Doksan ikinci gün sabahı avlu sessizdi."
    )
    finding = _rules(_lint(reply, code="tr", day=692))["tracker_leak"]
    assert finding["count"] == 1 and "Doksan ikinci gün" in finding["evidence"][0]

    note = "*(OOC: Haklısın, \"doksan ikinci gün\" benim kayıt numaram.)*\n\nHalvar kapıyı açtı."
    assert "tracker_leak" not in _rules(_lint(note, code="tr", day=92))


def test_avoid_phrase_over_its_cap_counts_whole_words_only() -> None:
    reply = "Bir an durdu. Halvar bir an sana baktı, sonra BİR AN daha bekledi. Bir anahtar çıkardı."
    result = _lint(reply, code="tr")
    assert _rules(result)["avoid_phrase"] == {"rule": "avoid_phrase", "count": 3, "evidence": ['"bir an" x3 (cap 1)']}
    assert '3x "bir an" (cap 1)' in result["summary"]
    assert "avoid_phrase" not in _rules(_lint("Bir an durdu. Bir anahtar çıkardı.", code="tr"))


def test_malformed_context_lists_are_ignored() -> None:
    # A lone string is not a list of phrases: its letters must not become phrases.
    result = _lint(
        "A lantern hung by a door.",
        code="en",
        avoid_phrases="a door",
        protected_names="Ayla",
        glossary_variants={"variant": "door"},
    )
    assert result["findings"] == []


def test_quote_spans_pair_openers_with_their_closers_on_one_line() -> None:
    text = 'Bir “açık kaldı ve "kapalı" bitti. „Hallo“ «salut» 「やあ」\n"satır\nsonu"'
    spans = presentation_lint._quote_spans(text)
    assert [text[start:end] for start, end in spans] == ['"kapalı"', "„Hallo“", "«salut»", "「やあ」"]


def test_a_pathological_reply_stays_fast() -> None:
    started = time.perf_counter()
    _lint([" “" * 30_000, '"' * 50_000, "kelime " * 50_000], code="tr", prompt="kelime " * 2_000)
    assert time.perf_counter() - started < 1.0


def test_campaign_avoid_phrases_default_to_a_cap_of_zero() -> None:
    avoid = ["smiled thinly", {"phrase": "lantern hissed", "max_per_reply": 1}]
    result = _lint("The lantern hissed. Marta smiled thinly.", code="en", avoid_phrases=avoid)
    assert _rules(result)["avoid_phrase"] == {"rule": "avoid_phrase", "count": 1, "evidence": ['"smiled thinly" x1 (cap 0)']}


@pytest.mark.parametrize(
    ("code", "prompt", "reply", "echo"),
    [
        (  # the Player's line repeated as the opening quote
            "tr",
            '"Farkındayım, Tobin. Önemli değil." diyorum.',
            '"Farkındayım, Tobin. Önemli değil." Tobin başını eğdi ve tezgâhın altına bir şey sakladı.',
            '"Farkındayım, Tobin. Önemli değil."',
        ),
        (  # the quote corrected and re-punctuated, a case ending added
            "tr",
            '"Kara ormanın ötesine gitsin lordum" diyorum.',
            '"Kara Orman\'ın ötesine gitsin, lordum." Lord Arren başını bir kez salladı.',
            "\"Kara Orman'ın ötesine gitsin, lordum.\"",
        ),
        (  # the action restated with the person ending swapped
            "tr",
            "Halvar'a kapıyı kimin kilitlediğini soruyorum.",
            "Halvar'a kapıyı kimin kilitlediğini soruyorsun. Halvar omuz silkti, anahtarı göstermedi.",
            "Halvar'a kapıyı kimin kilitlediğini soruyorsun",
        ),
        (
            "en",
            "I open the heavy cellar door slowly and look down the dark stairs for the missing courier.",
            "You open the heavy cellar door slowly and look down the dark stairs. Water drips somewhere below.",
            "open the heavy cellar door slowly and look down the dark stairs",
        ),
        (
            "en",
            '"We leave at dawn, all of us," I tell Marta.',
            '"We leave at dawn, all of us." Marta does not argue. She starts packing the salt fish.',
            '"We leave at dawn, all of us."',
        ),
        (
            "de",
            "Ich frage den Schmied, ob er das Schwert bis morgen schärfen kann.",
            "Du fragst den Schmied, ob er das Schwert bis morgen schärfen kann. Er wischt sich die Hände ab.",
            "fragst den Schmied, ob er das Schwert bis morgen schärfen kann",
        ),
        (
            "de",
            '"Ich komme morgen wieder", sage ich.',
            "„Ich komme morgen wieder.“ Der Schmied nickt und legt den Hammer beiseite.",
            "„Ich komme morgen wieder.“",
        ),
        # Three quoted words: too short for a run, still the Player's line.
        ("tr", '"Gidelim hemen buradan" diyorum.', '"Gidelim hemen buradan." Halvar atını çevirdi.', '"Gidelim hemen buradan."'),
        ("en", '"Not tonight, Marta," I say.', '"Not tonight, Marta." She shrugs and goes back to her loom.', '"Not tonight, Marta."'),
        ("de", '"Nicht heute Nacht", sage ich.', "„Nicht heute Nacht.“ Der Schmied zuckt mit den Schultern.", "„Nicht heute Nacht.“"),
    ],
)
def test_restatement_flags_an_opening_that_echoes_the_players_words(code: str, prompt: str, reply: str, echo: str) -> None:
    result = _lint(reply, code=code, prompt=prompt, player_name="Mira")
    finding = _rules(result)["restatement"]
    assert finding["count"] == 1
    assert echo in finding["evidence"][0] and finding["evidence"][1].startswith("Player: ")
    assert "opening restates the Player's words: " in result["summary"]


@pytest.mark.parametrize(
    ("code", "prompt", "reply"),
    [
        # The same people, place and night, in the GM's own words.
        ("tr", PROMPT_TR, CLEAN["tr"][1]),
        (
            "tr",
            "Ilse'ye Varro'nun kampında kaç adam olduğunu ve gece nöbeti kimin tuttuğunu soruyorum.",
            'Ilse parmaklarıyla saydı. "Otuz kadar adam var. Gece nöbetini dağlı okçular tutuyor, '
            'kampın iki ucunda ateş yakıyorlar." Varro\'nun çadırı nehre yakındı.',
        ),
        (
            "en",
            "I ask Marta about the missing courier and the letter he carried.",
            'Marta sets down her cup. "The courier? He left before dawn, and he took nothing with him '
            'but that letter." She looks at the cold hearth.',
        ),
        (  # a shared multi-word name is not an echo
            "en",
            "I walk to the Old Harbor Gate and wait there.",
            "The Old Harbor Gate stands open. Gulls wheel over the empty quay, and a cart creaks past.",
        ),
        ("de", "Ich frage den Schmied nach dem Schwert.", CLEAN["de"][1]),
        (
            "de",
            "Ich gehe mit Anna zum Markt und kaufe Brot für die Reise.",
            "Der Markt ist schon halb leer. Anna zeigt auf einen Stand, an dem noch Brot liegt, "
            "und der Bäcker winkt euch heran.",
        ),
        # Three words in a row are too few to call an echo.
        ("en", "I open the door.", "You open the door. It creaks."),
        # An NPC echoing a short part of the question is fine.
        (
            "tr",
            '"Kapıyı kim kilitledi?" diye soruyorum.',
            '"Kapıyı kim kilitledi, öyle mi?" Halvar güldü. "Sen kilitledin."',
        ),
    ],
)
def test_restatement_ignores_topical_overlap(code: str, prompt: str, reply: str) -> None:
    assert "restatement" not in _rules(_lint(reply, code=code, prompt=prompt, player_name="Mira"))


def test_restatement_reads_the_opening_of_the_prose_only() -> None:
    prompt = "Halvar'a kapıyı kimin kilitlediğini soruyorum."
    after_ooc = "(OOC) Zar gerekmedi.\n\n---\n\nHalvar'a kapıyı kimin kilitlediğini soruyorsun. Halvar susuyor."
    assert _rules(_lint(after_ooc, code="tr", prompt=prompt))["restatement"]["count"] == 1
    only_ooc = "(OOC) Halvar'a kapıyı kimin kilitlediğini sorduğunu not ettim; zar gerekmedi."
    assert "restatement" not in _rules(_lint(only_ooc, code="tr", prompt=prompt))
    late = "Avlu sessizdi. " * 25 + "Halvar'a kapıyı kimin kilitlediğini soruyorsun."
    assert "restatement" not in _rules(_lint(late, code="tr", prompt=prompt))


def test_protected_name_leak_versus_a_revealed_name() -> None:
    names = [
        {"name": "Kül Varisi", "holders": ["Edric"], "status": "GM-only", "fact_id": "F-007"},
        {"name": "Ayla", "holders": [], "status": "revealed", "fact_id": "F-002"},
    ]
    leak = _lint("Kül Varisi'nin adı fısıltıyla geçti. Ayla kapıda bekliyordu.", code="tr", protected_names=names)
    finding = _rules(leak)["secret_leak"]
    assert finding["count"] == 1 and "Kül Varisi'nin" in finding["evidence"][0]
    # The summary reaches the GM's context: fact id and status, never the name.
    assert "1 protected name in the reply (F-007, GM-only)" in leak["summary"] and "Kül" not in leak["summary"]

    revealed = _lint("Ayla kapıda bekliyordu, elinde bir fener vardı.", code="tr", protected_names=names)
    assert "secret_leak" not in _rules(revealed)

    in_tool = _lint("Ayla kapıda bekliyordu.", code="tr", protected_names=names, descriptions=["Kül Varisi notunu güncelle"])
    assert _rules(in_tool)["secret_leak"]["evidence"] == ["[tool] Kül Varisi notunu güncelle"]


def test_repetition_across_recent_replies() -> None:
    earlier = [
        "Halvar kapıyı kapattı. Gözlerini senden ayırmadı ve elini kılıcının kabzasına koydu.",
        "Avluda rüzgar esiyordu. Edric gözlerini senden ayırmadı, sonra elini kılıcının kabzasına koydu.",
        "Ayla güldü ve uzaklaştı. Kapı gıcırdadı.",
    ]
    current = "Edric yine gözlerini senden ayırmadı. Bir süre sonra elini kılıcının kabzasına koydu ve bekledi."
    result = _lint(current, code="tr", history=_history(earlier, "tr"))
    finding = _rules(result)["repetition"]
    assert finding["count"] == 2
    assert finding["evidence"] == [
        '"elini kılıcının kabzasına koydu" (3 of last 4)',
        '"gözlerini senden ayırmadı" (3 of last 4)',
    ]
    assert 'repeated from earlier replies: "elini kılıcının kabzasına koydu"' in result["summary"]
    # One earlier reply with the phrase makes two of the window, not three.
    assert "repetition" not in _rules(_lint(current, code="tr", history=_history(earlier[1:], "tr")))


@pytest.mark.parametrize(
    ("code", "earlier", "current", "phrase"),
    [
        (
            "en",
            ["The lamp guttered low. Marta waited by the door.", "Rain on the roof; the lamp guttered low again."],
            "Somewhere above, the lamp guttered low as the wind rose.",
            "the lamp guttered low",
        ),
        (
            "de",
            [
                "Der alte Schmied legte den schweren Hammer beiseite.",
                "Dann legte der alte Schmied den schweren Hammer beiseite und sah auf.",
            ],
            "Wieder legte der alte Schmied den schweren Hammer beiseite.",
            "den schweren hammer beiseite",
        ),
    ],
)
def test_repetition_in_english_and_german(code: str, earlier: list[str], current: str, phrase: str) -> None:
    finding = _rules(_lint(current, code=code, history=_history(earlier, code)))["repetition"]
    assert any(item.startswith(f'"{phrase}" (3 of last 3)') for item in finding["evidence"])


@pytest.mark.parametrize(
    ("code", "earlier", "current"),
    [
        (  # a place name with the same case ending
            "tr",
            ["Kızıl Tepe'nin surları karanlıktı.", "Akşam Kızıl Tepe'nin kapısı kapandı."],
            "Sabah Kızıl Tepe'nin avlusunda kimse yoktu.",
        ),
        (  # two names joined by a function word
            "tr",
            ["Ilse ile Varro avluda bekliyordu.", "Sabah Ilse ile Varro dereye indi."],
            "Akşam Ilse ile Varro sofrayı kurdu.",
        ),
        (
            "en",
            ["They rode for the Old Harbor Gate at noon.", "Rain fell on the Old Harbor Gate all night."],
            "By dusk the Old Harbor Gate was shut.",
        ),
        (  # an out-of-character stat list
            "tr",
            ["(OOC) Puanlar:\n- Kılıç ve silah: 5\n- Güç ve dayanıklılık: 4", "- Kılıç ve silah: 5\n- Güç ve dayanıklılık: 4"],
            "Puanlar:\n\n- Kılıç ve silah: 5\n- Güç ve dayanıklılık: 4\n\nAvlu sessizdi.",
        ),
    ],
)
def test_repetition_ignores_names_and_ooc_lists(code: str, earlier: list[str], current: str) -> None:
    assert "repetition" not in _rules(_lint(current, code=code, history=_history(earlier, code)))


def test_glossary_variant_instead_of_the_preferred_form() -> None:
    variants = [
        {"variant": "harbourmaster", "preferred": "Harbor Warden"},
        {"variant": "Warden", "preferred": "Harbor Warden"},
    ]
    result = _lint("The harbourmaster waves you through. Later the Harbor Warden nods.", code="en", glossary_variants=variants)
    finding = _rules(result)["glossary_variant"]
    assert finding == {
        "rule": "glossary_variant",
        "count": 1,
        "evidence": ['"harbourmaster" x1 (preferred: "Harbor Warden")'],
    }
    assert '"harbourmaster" instead of "Harbor Warden"' in result["summary"]
    clean = _lint("The Harbor Warden lifts a hand.", code="en", glossary_variants=variants)
    assert "glossary_variant" not in _rules(clean)


def test_negated_descriptions_count_from_two_and_skip_quoted_speech() -> None:
    assert "negated_description" not in _rules(_lint("Her voice did not waver. She set the cup down.", code="en"))
    two = _lint(
        'Her voice did not waver. It wasn\'t fear, it was something colder. "Not now, but soon," she said.', code="en"
    )
    assert _rules(two)["negated_description"]["count"] == 2
    assert "2 negated descriptions" in two["summary"]
    turkish = _lint("Sesi titremiyordu. Bakmıyordu, ama her şeyi görüyordu.", code="tr")
    assert _rules(turkish)["negated_description"]["count"] == 2


def test_calque_reports_the_better_form() -> None:
    result = _lint("Halvar'ın sesi düzdü. Kapıya yürüdü.", code="tr")
    assert _rules(result)["calque"]["evidence"] == ['"sesi düzdü" -> "sakin, tekdüze bir sesle konuştu"']
    assert 'calque "sesi düzdü"' in result["summary"]


def test_meta_leak_paths_code_identifiers_and_backend_words_outside_quotes() -> None:
    reply = (
        "I updated `campaign/characters/halvar.md` and bumped the revision. The durable_turns_since_distill "
        'counter is fine. "We must commit to the climb," Marta says. See tools/rpg_state.py.'
    )
    result = _lint(reply, code="en")
    finding = _rules(result)["meta_leak"]
    # The code span, the identifier, and the path. In English play "revision" and
    # "commit" are ordinary words; only the pack's backend collocations count.
    assert finding["count"] == 3
    assert 'backend terms shown: "campaign/characters/halvar.md"' in result["summary"]
    assert "meta_leak" not in _rules(_lint('"We must commit to the climb," Marta says.', code="en"))
    assert "meta_leak" not in _rules(_lint("The smith's helper would not commit to her persistence.", code="en"))
    assert _rules(_lint("The durable commit went through; the session log is updated.", code="en"))["meta_leak"]["count"] == 2

    turkish = _lint("Sahneyi kaydediyorum; revizyon tamam.", code="tr")
    assert _rules(turkish)["meta_leak"]["count"] == 2


def test_pc_authoring_in_narration_but_not_in_quoted_speech() -> None:
    assert _rules(_lint("Sen de başını salladın ve kapıya yürüdün.", code="tr"))["pc_authoring"]["count"] == 1
    assert "pc_authoring" not in _rules(_lint('"Sen dedin ki gidelim," diye hatırlattı Halvar.', code="tr"))
    assert _rules(_lint("You nod and step through the gate.", code="en"))["pc_authoring"]["count"] == 1
    # The evidence shows the reply as written, quoted words included.
    finding = _rules(_lint('"Olur," dedin. Halvar güldü.', code="tr"))["pc_authoring"]
    assert finding["evidence"] == ['"Olur," dedin. Halvar güldü.']
    assert "pc_authoring" not in _rules(_lint("*(OOC: Bunu sen dedin, ben not ettim.)*\n\nHalvar güldü.", code="tr"))


def test_fingerprint_is_bounded_sorted_and_deterministic() -> None:
    rng = random.Random(7)
    vocabulary = ["river", "lantern", "stone", "harbor", "rope", "salt", "gull", "tide", "plank", "anchor", "sail", "barrel"]
    sentences = [" ".join(rng.choice(vocabulary) for _ in range(12)).capitalize() + "." for _ in range(80)]
    first = _lint(" ".join(sentences), code="en")
    fingerprint = first["fingerprint"]
    assert len(fingerprint) == FINGERPRINT_MAX and len(first["trigrams"]) <= FINGERPRINT_MAX
    assert fingerprint == sorted(set(fingerprint))
    assert all(re.fullmatch(r"[0-9a-f]{8}", value) for value in fingerprint)
    assert _lint(" ".join(sentences), code="en")["fingerprint"] == fingerprint


def test_summary_stays_within_its_limit() -> None:
    notes = [f"note {index} " + "x" * 120 for index in range(5)]
    summary = presentation_lint._summary(notes)
    assert len(summary) <= SUMMARY_MAX and summary.startswith("Last reply: note 0") and summary.endswith(" more.")

    reply = (
        "Bir an durdu, bir an bekledi, bir an daha baktı. Sesi düzdü ve yüzünde hiçbir şey yoktu. "
        "Doksan ikinci gün sabahı `campaign/characters/halvar_usta_notu.md` güncellendi; revizyon tamam. "
        "Sen de başını salladın. Sesi titremiyordu. Bakmıyordu, ama biliyordu. Kül Varisi geldi. "
        "Saving the scene and the campaign state now, then updating every file."
    )
    names = [{"name": "Kül Varisi", "holders": [], "status": "GM-only", "fact_id": "F-007"}]
    result = _lint(reply, code="tr", day=92, protected_names=names, descriptions=["Commit the durable turn now"])
    assert len(result["findings"]) >= 8
    assert len(result["summary"]) <= SUMMARY_MAX
    assert result["summary"].startswith("Last reply: 1 protected name in the reply (F-007")
    for finding in result["findings"]:
        assert len(finding["evidence"]) <= 3 and all(len(item) <= 80 for item in finding["evidence"])


# ---------------------------------------------------------------------------
# Campaign context
# ---------------------------------------------------------------------------


def test_protected_names_parse_entries_and_skip_the_placeholder() -> None:
    assert protected_names(KNOWLEDGE) == [
        {"name": "Kül Varisi", "holders": ["Edric", "the Guild"], "status": "GM-only", "fact_id": "F-007"},
        {"name": "Ashen Heir", "holders": ["Edric", "the Guild"], "status": "GM-only", "fact_id": "F-007"},
        {"name": "Ayla", "holders": [], "status": "revealed at revision 12", "fact_id": "F-002"},
    ]
    assert protected_names((TEMPLATES / "knowledge_boundaries.md").read_text(encoding="utf-8")) == []


def test_glossary_variants_find_columns_by_header_name() -> None:
    assert glossary_variants((TEMPLATES / "glossary.md").read_text(encoding="utf-8")) == []
    assert glossary_variants(GLOSSARY) == [
        {"variant": "harbourmaster", "preferred": "Harbor Warden"},
        {"variant": "port lord", "preferred": "Harbor Warden"},
        {"variant": "Warden", "preferred": "Harbor Warden"},
    ]


def test_campaign_avoid_phrases_from_style_state_and_profile(campaign: Path) -> None:
    _write(campaign / "style_state.json", json.dumps({"avoid_phrases": ["smiled thinly", ""]}))
    profile = (campaign / "play_profile.yaml").read_text(encoding="utf-8") + (
        "narration:\n  language: auto\n  narrative_signature:\n    anchors: []\n    avoid_habits:\n"
        '      - stock pauses like "bir an" and “a beat”\n'
        "      - ending every reply with a question  # the Player's words\n"
        "    interiority_policy: player_owned\n"
    )
    _write(campaign / "play_profile.yaml", profile)
    assert campaign_avoid_phrases(campaign) == ["smiled thinly", "bir an", "a beat", "ending every reply with a question"]


def test_resolve_language_prefers_the_setting_then_prompts_then_the_reply() -> None:
    assert resolve_language("tr-TR", "Hello there", [], "") == ("tr", "setting", None)
    assert resolve_language("auto", "Evet.", [], "Halvar başını kaldırdı.") == ("", "none", None)
    earlier = [{"prompt_sample": "Kapıyı açıp avluya çıkıyorum ve Halvar'ı arıyorum."}] * 3
    code, source, confidence = resolve_language("auto", "Evet.", earlier, "")
    assert (code, source) == ("tr", "prompts") and confidence and confidence > 0
    code, source, _ = resolve_language("auto", "Ok.", [], "The smith set down his hammer and looked at you for a long time.")
    assert (code, source) == ("en", "reply")


def test_distinct_history_keeps_the_latest_record_per_prompt() -> None:
    records = [{"prompt_uuid": "a", "n": 1}, {"prompt_uuid": "b", "n": 2}, {"prompt_uuid": "a", "n": 3}, {"n": 4}, "x"]
    assert distinct_history(records) == [{"prompt_uuid": "b", "n": 2}, {"prompt_uuid": "a", "n": 3}, {"n": 4}]
    assert distinct_history(records, exclude="a") == [{"prompt_uuid": "b", "n": 2}, {"n": 4}]


# ---------------------------------------------------------------------------
# Hook
# ---------------------------------------------------------------------------


def _user(text: str, uuid: str) -> dict:
    return {"type": "user", "uuid": uuid, "timestamp": "2026-10-20T10:00:00Z", "message": {"role": "user", "content": text}}


def _assistant(*blocks: dict) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}}


def _text(text: str) -> dict:
    return {"type": "text", "text": text}


def _tool(description: str) -> dict:
    return {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "sh repog.sh", "description": description}}


def _tool_result() -> dict:
    return {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}}


def _transcript_bytes(rows: list[dict]) -> bytes:
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode("utf-8")


def _event(project: Path, transcript: Path, **extra) -> dict:
    return {
        "session_id": "s-1",
        "transcript_path": str(transcript),
        "cwd": str(project),
        "hook_event_name": "Stop",
        "stop_hook_active": False,
        **extra,
    }


def _runtime(campaign: Path) -> Path:
    return campaign / ".repog-runtime"


def test_run_hook_lints_the_turn_and_stores_the_record(campaign: Path, tmp_path: Path) -> None:
    transcript = tmp_path / "session.jsonl"
    transcript.write_bytes(
        _transcript_bytes(
            [
                _user("Önceki istem.", "u-0"),
                _assistant(_text("Önceki cevap.")),
                _user(PROMPT_TR, "u-1"),
                _assistant(_text("Halvar bir an durdu."), _tool("Commit the durable turn to the campaign")),
                _tool_result(),
                _assistant(_text("Avlu sessizdi ve fenerin ışığı titriyordu; bir an kimse konuşmadı.")),
            ]
        )
    )
    final = "Saving the scene and the campaign state now."  # not yet in the transcript
    record = run_hook(_event(tmp_path, transcript, last_assistant_message=final))

    assert record is not None
    assert json.loads((_runtime(campaign) / LINT_LAST).read_text(encoding="utf-8")) == record
    assert record["language"] == "tr" and record["language_source"] == "prompts" and record["language_confidence"] > 0
    assert record["prompt_uuid"] == "u-1" and record["session_id"] == "s-1"
    assert record["counts"] == {"out_of_language": 2, "avoid_phrase": 2}
    assert record["summary"].startswith('Last reply: 1 English line: "Saving the scene')
    history = read_jsonl(_runtime(campaign) / LINT_HISTORY)
    assert len(history) == 1
    assert history[0]["prompt_uuid"] == "u-1" and history[0]["prompt_sample"] == PROMPT_TR
    assert history[0]["fingerprint"] and history[0]["counts"] == record["counts"]
    assert b"\r" not in (_runtime(campaign) / LINT_HISTORY).read_bytes()


def test_run_hook_does_not_count_the_final_message_twice(campaign: Path, tmp_path: Path) -> None:
    reply = "Bir an durdu. Halvar bir an sana baktı."
    transcript = tmp_path / "session.jsonl"
    transcript.write_bytes(_transcript_bytes([_user(PROMPT_TR, "u-1"), _assistant(_text(reply))]))
    record = run_hook(_event(tmp_path, transcript, last_assistant_message="  " + reply + "\n"))
    assert record is not None and record["counts"] == {"avoid_phrase": 2}


def test_a_repeated_stop_for_one_prompt_neither_duplicates_nor_matches_itself(campaign: Path, tmp_path: Path) -> None:
    reply = "Edric gözlerini senden ayırmadı ve elini kılıcının kabzasına koydu."
    transcript = tmp_path / "session.jsonl"
    transcript.write_bytes(_transcript_bytes([_user(PROMPT_TR, "u-1"), _assistant(_text(reply))]))
    for _ in range(3):
        record = run_hook(_event(tmp_path, transcript))
        assert record is not None and "repetition" not in record["counts"]
    assert len(read_jsonl(_runtime(campaign) / LINT_HISTORY)) == 3
    assert report(campaign)["replies"] == 1


def test_auto_language_uses_earlier_prompts_from_history(campaign: Path, tmp_path: Path) -> None:
    sample = "Kapıyı açıp avluya çıkıyorum ve Halvar'ı arıyorum."
    _write_jsonl(
        _runtime(campaign) / LINT_HISTORY,
        [{"prompt_uuid": f"p{index}", "prompt_sample": sample, "fingerprint": [], "trigrams": []} for index in range(3)],
    )
    transcript = tmp_path / "session.jsonl"
    transcript.write_bytes(_transcript_bytes([_user("Evet.", "u-9"), _assistant(_text("Halvar başını kaldırdı."))]))
    record = run_hook(_event(tmp_path, transcript))
    assert record is not None and record["language"] == "tr" and record["language_source"] == "prompts"


def test_run_hook_reads_the_campaign_owner_files(campaign: Path, tmp_path: Path) -> None:
    _write(campaign / "knowledge_boundaries.md", KNOWLEDGE)
    _write(campaign / "glossary.md", GLOSSARY)
    _write(campaign / "style_state.json", json.dumps({"avoid_phrases": ["smiled thinly"]}))
    profile = (campaign / "play_profile.yaml").read_text(encoding="utf-8")
    _write(campaign / "play_profile.yaml", profile + "runtime:\n  presentation_lint: on\nnarration:\n  language: en\n")
    transcript = tmp_path / "session.jsonl"
    reply = "The harbourmaster smiled thinly. Far off, a bell rang for the Ashen Heir. Ayla did not look up."
    transcript.write_bytes(_transcript_bytes([_user("I wait at the quay.", "u-1"), _assistant(_text(reply))]))
    record = run_hook(_event(tmp_path, transcript))
    assert record is not None
    assert (record["language"], record["language_source"], record["language_confidence"]) == ("en", "setting", None)
    assert record["counts"] == {"avoid_phrase": 1, "secret_leak": 1, "glossary_variant": 1}
    assert "(F-007, GM-only)" in record["summary"] and "Ashen" not in record["summary"]


def test_run_hook_skips_quietly_and_never_raises(campaign: Path, tmp_path: Path) -> None:
    transcript = tmp_path / "session.jsonl"
    transcript.write_bytes(_transcript_bytes([_user(PROMPT_TR, "u-1"), _assistant(_text("Bir an durdu."))]))
    garbage = tmp_path / "garbage.jsonl"
    garbage.write_bytes(b"\xff\xfe not json\n{]\n\n")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    ooc = tmp_path / "ooc.jsonl"
    ooc.write_bytes(_transcript_bytes([_user("(OOC: bu gece kaç gün geçti?)", "u-2"), _assistant(_text("Day 92."))]))

    assert run_hook(_event(tmp_path, tmp_path / "missing.jsonl")) is None
    assert run_hook(_event(tmp_path, garbage)) is None
    assert run_hook(_event(tmp_path, ooc)) is None
    assert run_hook(_event(elsewhere, transcript)) is None
    assert run_hook({"cwd": str(tmp_path)}) is None
    assert run_hook(None) is None  # type: ignore[arg-type]
    assert run_hook({"cwd": 5, "transcript_path": ["x"]}) is None
    assert not (_runtime(campaign) / LINT_LAST).exists()

    profile = (campaign / "play_profile.yaml").read_text(encoding="utf-8")
    _write(campaign / "play_profile.yaml", profile + "runtime:\n  presentation_lint: off\n")
    assert run_hook(_event(tmp_path, transcript)) is None
    _write(campaign / "play_profile.yaml", profile)

    setup = (campaign / "setup_profile.yaml").read_text(encoding="utf-8")
    _write(campaign / "setup_profile.yaml", setup.replace("experience_mode: rpg", "experience_mode: companion"))
    assert run_hook(_event(tmp_path, transcript)) is None
    _write(campaign / "setup_profile.yaml", setup.replace("ready_for_play: true", "ready_for_play: false"))
    assert run_hook(_event(tmp_path, transcript)) is None
    assert not (_runtime(campaign) / LINT_LAST).exists()

    _write(campaign / "setup_profile.yaml", setup)
    assert run_hook(_event(tmp_path, transcript)) is not None


def test_run_hook_is_fast_on_a_large_transcript(campaign: Path, tmp_path: Path) -> None:
    transcript = tmp_path / "large.jsonl"
    filler = _transcript_bytes([_assistant(_text("Eski bir cevap. " * 60))])
    chunk = filler * (1_048_576 // len(filler))
    tail = _transcript_bytes(
        [_user(PROMPT_TR, "u-1"), _assistant(_text(CLEAN["tr"][1]), _tool("Sahne kaydı")), _tool_result()]
    )
    try:
        with transcript.open("wb") as stream:
            for _ in range(125):
                stream.write(chunk)
            stream.write(tail)
        assert transcript.stat().st_size > 120 * 1_048_576
        started = time.perf_counter()
        record = run_hook(_event(tmp_path, transcript, last_assistant_message="Halvar kapıyı kapattı."))
        elapsed = time.perf_counter() - started
    finally:
        transcript.unlink()
    assert record is not None and record["prompt_uuid"] == "u-1" and record["summary"] == ""
    assert elapsed < 1.0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli(*args: str, stdin: bytes = b"", cwd: Path) -> subprocess.CompletedProcess:
    env = {key: value for key, value in os.environ.items() if key != "CLAUDE_PROJECT_DIR"}
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, cwd=cwd, env=env, timeout=120
    )


def test_cli_hook_reads_stdin_with_a_bom_and_prints_nothing(campaign: Path, tmp_path: Path) -> None:
    transcript = tmp_path / "session.jsonl"
    transcript.write_bytes(_transcript_bytes([_user(PROMPT_TR, "u-1"), _assistant(_text("Bir an durdu. Bir an baktı."))]))
    event = json.dumps(_event(tmp_path, transcript), ensure_ascii=False).encode("utf-8")
    completed = _cli("hook", stdin=b"\xef\xbb\xbf" + event, cwd=tmp_path / "work")
    assert (completed.returncode, completed.stdout, completed.stderr) == (0, b"", b"")
    stored = json.loads((_runtime(campaign) / LINT_LAST).read_text(encoding="utf-8"))
    assert stored["counts"] == {"avoid_phrase": 2} and stored["language"] == "tr"

    for junk in (b"", b"not json", b"[1, 2]", b"\xff\xfe\x00"):
        completed = _cli("hook", stdin=junk, cwd=tmp_path / "work")
        assert (completed.returncode, completed.stdout) == (0, b"")


def test_cli_report_prints_ascii_aggregates(campaign: Path, tmp_path: Path) -> None:
    runtime = _runtime(campaign)
    _write_jsonl(
        runtime / LINT_HISTORY,
        [
            {"prompt_uuid": "a", "at": "2026-10-20T10:00:00Z", "language": "tr", "counts": {"avoid_phrase": 3, "calque": 1}},
            {"prompt_uuid": "b", "at": "2026-10-20T10:05:00Z", "language": "tr", "counts": {}},
            {"prompt_uuid": "b", "at": "2026-10-20T10:06:00Z", "language": "tr", "counts": {"avoid_phrase": 1}},
            {"prompt_uuid": "c", "at": "2026-10-20T10:10:00Z", "language": "en", "counts": {"out_of_language": 2}},
        ],
    )
    _write(runtime / LINT_LAST, json.dumps({"summary": 'Last reply: 1 Türkçe line: "x".'}, ensure_ascii=False))

    completed = _cli("report", str(tmp_path), cwd=tmp_path / "work")
    assert completed.returncode == 0 and all(byte < 128 for byte in completed.stdout)
    result = json.loads(completed.stdout)
    assert (result["replies"], result["clean_replies"]) == (3, 0)
    assert result["rules"]["avoid_phrase"] == {"replies": 2, "total": 4}
    assert result["rules"]["out_of_language"] == {"replies": 1, "total": 2}
    assert result["rules"]["secret_leak"] == {"replies": 0, "total": 0}
    assert result["languages"] == {"en": 1, "tr": 2}
    assert result["latest_summary"] == 'Last reply: 1 Türkçe line: "x".'

    last = json.loads(_cli("report", str(campaign), "--last", "1", cwd=tmp_path / "work").stdout)
    assert last["replies"] == 1 and last["since"] == last["until"] == "2026-10-20T10:10:00Z"
    assert last["rules"]["avoid_phrase"] == {"replies": 0, "total": 0}

    missing = _cli("report", str(tmp_path / "nowhere"), cwd=tmp_path / "work")
    assert missing.returncode == 2 and json.loads(missing.stdout)["failure_category"] == "campaign_missing"


def test_campaign_avoid_stems_match_inflected_words() -> None:
    reply = "Parmakları kılıcın kabzasına kenetlenmişti. Kapı tıkırdadı."
    finding = _rules(_lint(reply, code="tr", avoid_phrases=["kenetlen", "tıkırd"]))["avoid_phrase"]
    assert finding["count"] == 2
    # A short entry stays a whole-word phrase, so it cannot match inside longer words.
    assert "avoid_phrase" not in _rules(_lint("Kalan anahtarlar masadaydı.", code="tr", avoid_phrases=["kal"]))


def test_backend_words_that_are_native_vocabulary_are_not_leaks() -> None:
    german = "Die Revision des Plans dauerte lange, und das Schema an der Wand war alt."
    assert "meta_leak" not in _rules(_lint(german, code="de"))
    assert _rules(_lint("Sahne bitti; commit tamam.", code="tr"))["meta_leak"]["count"] == 1
