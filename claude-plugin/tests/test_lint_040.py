"""Presentation lint 0.4.0: the age rule, rolling caps, gesture families, case slips, echo and PC-line rules,
name exclusions, OOC turns, the stored record's privacy, and the habit and distill reports."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import presentation_lint
from lang_pack import available_codes, load_pack
from presentation_lint import (
    LINT_HISTORY,
    LINT_LAST,
    REPORT_TEXT_MAX,
    SNIPPET_CHARS,
    lint_reply,
    report_summary,
    run_hook,
    top_habits,
)
from repog_runtime import read_jsonl


@pytest.fixture(autouse=True)
def _isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Campaign discovery must only find what a test sets up."""

    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)


def _lint(text: str, *, code: str, prompt: str = "", descriptions=(), history=(), pack=None, **context) -> dict:
    context.setdefault("play_language", code)
    pack = pack if pack is not None else load_pack(code)
    return lint_reply(prompt, [text], list(descriptions), pack=pack, context=context, history=list(history))


def _counts(text: str, *, code: str, **kwargs) -> dict[str, int]:
    return _lint(text, code=code, **kwargs)["counts"]


def _tallies(*values: dict[str, int]) -> list[dict]:
    """Earlier reply records holding only the rolling-rule tallies."""

    return [{"tallies": dict(value)} for value in values]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    _write(path, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def _runtime(campaign: Path) -> Path:
    return campaign / ".repog-runtime"


# Pads an age and a romance term apart: two more sentences and well over 220 characters.
FAR_TR = (
    " Gemi sabah erkenden limandan ayrıldı ve rüzgâr güneyden sertçe esiyordu."
    " Tayfalar halatları çekti, kaptan dümende bekledi, ufukta küçük adalar birer birer belirdi."
    " Akşam olunca güvertede fenerler yakıldı ve martılar direklerin çevresinde dönmeyi bıraktı."
)
FAR_EN = (
    " The ship left the harbor early in the morning and the wind blew hard from the south."
    " The crew hauled on the lines, the captain held the wheel, and small islands rose one by one."
    " When evening came the lanterns were lit on deck and the gulls stopped circling the masts."
)


# ---------------------------------------------------------------------------
# minor_sexual_proximity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "reply"),
    [
        ("tr", "On beş yaşındayken Kerem'e âşık olmuştu. Gemi limana yanaştı."),
        ("tr", "On beşimdeyken onu ilk kez öptüm, dedi kadın."),
        ("tr", "15 yaşında bir çocuktu. Ertesi yaz evlendiler."),
        ("tr", "On beş yaşında bir kızdı ve ilk kez âşık oldu."),
        ("tr", "On beşimde ilk sevgilim oldu."),
        ("tr", "Yaşı henüz on altıydı; nişanlısı onu bekliyordu."),
        ("en", "At fifteen she fell in love with the ferryman's son."),
        ("en", "She was a 15-year-old deckhand. He kissed her at the rail."),
        ("en", "He was fifteen years old when he became her lover."),
        ("en", "Aged 15, he courted the miller's daughter."),
        # First person, possessives, digits and the "-ydı" forms.
        ("tr", "On beş yaşımdayken ilk kez âşık oldum."),
        ("tr", "On dört yaşımda evlendim."),
        ("tr", "On beş yaşımızda sevgili olduk."),
        ("tr", "Henüz on altısındaydı ama nişanlısı vardı."),
        ("tr", "15'imdeyken bir sevgilim vardı."),
        ("tr", "On beş yaşını doldurmadan evlendirildi."),
        ("tr", "Şubatta on dördündeydi ve sevgilisine bir kolye aldı."),
        ("tr", "Yaşı on beşti ama sevgilisi vardı."),
        ("tr", "Sevgilisi on beş yaşındaydı."),
        # "She was N" followed by a clause, and "at N" with no clock word.
        ("en", "She was fifteen when she married the captain."),
        ("en", "I was fourteen when I fell in love with him."),
        ("en", "He was only sixteen and already her lover."),
        ("en", "At eleven she kissed the stable boy behind the mill."),
    ],
)
def test_minor_sexual_proximity_flags_an_under_18_age_near_a_romance_term(code: str, reply: str) -> None:
    result = _lint(reply, code=code)
    assert result["counts"]["minor_sexual_proximity"] == 1
    assert result["summary"].startswith("Last reply: age under 18 near a romance or sex term (")
    assert result["summary"].endswith("no relationship may begin before 18.")


@pytest.mark.parametrize(
    ("code", "reply"),
    [
        # Durations are not ages.
        ("tr", "On beş yıl önce sevgilisini denizde kaybetmişti."),
        ("tr", "On beş günde limana vardılar; sevgilisi onu bekliyordu."),
        ("en", "Fifteen years ago he kissed his wife goodbye at the quay."),
        # Adults.
        ("tr", "Yirmi yaşındayken sevgilisiyle limanda tanıştı."),
        ("en", "At twenty she fell in love with the ferryman's son."),
        # A distance, not an age.
        ("en", "At fifteen paces the duelists turned; later the winner kissed his bride."),
        # An age with no romance term near it.
        ("tr", "On beş yaşındayken gemiye çırak olarak girdi." + FAR_TR + " Yıllar sonra evlendi."),
        ("en", "At fifteen she signed on as a deckhand." + FAR_EN + " Years later she married the harbor master."),
    ],
)
def test_minor_sexual_proximity_ignores_durations_adults_and_distant_terms(code: str, reply: str) -> None:
    assert "minor_sexual_proximity" not in _counts(reply, code=code)


def test_the_age_rule_leads_the_summary_and_reads_ooc_notes_too() -> None:
    reply = "Saving the scene and the campaign state now.\n\nOn beş yaşındayken Kerem'e âşık olmuştu."
    result = _lint(reply, code="tr")
    assert result["findings"][0]["rule"] == "minor_sexual_proximity" and "out_of_language" in result["counts"]
    assert result["summary"].startswith("Last reply: age under 18 near a romance or sex term")
    # An out-of-character turn lints its prose only, yet the age rule reads everything the Player saw.
    ooc = "(OOC: At fifteen she had a lover, if you want that in her backstory.)\n\nMarta mends the nets in silence."
    assert _counts(ooc, code="en", prompt="OOC: tell me about Marta's past")["minor_sexual_proximity"] == 1


@pytest.mark.parametrize(
    ("code", "minor", "adult", "duration"),
    [
        (
            "de",
            "Mit fünfzehn Jahren verliebte sie sich in den Fährmann.",
            "Mit zwanzig Jahren verliebte sie sich in den Fährmann.",
            "Vor fünfzehn Jahren küsste er seine Frau zum Abschied.",
        ),
        (
            "es",
            "A los quince años se enamoró del barquero.",
            "A los veinte años se enamoró del barquero.",
            "Hace quince años besó a su esposa en el muelle.",
        ),
        (
            "fr",
            "À quinze ans, elle tomba amoureuse du passeur.",
            "À vingt ans, elle tomba amoureuse du passeur.",
            "Il y a quinze ans, il embrassa sa femme sur le quai.",
        ),
    ],
)
def test_the_other_packs_carry_age_patterns_and_romance_terms(code: str, minor: str, adult: str, duration: str) -> None:
    assert _counts(minor, code=code)["minor_sexual_proximity"] == 1
    assert "minor_sexual_proximity" not in _counts(adult, code=code)
    assert "minor_sexual_proximity" not in _counts(duration, code=code)


def test_every_shipped_pack_names_the_age_group_and_romance_terms() -> None:
    for code in available_codes():
        pack = load_pack(code)
        assert pack["age_patterns"] and pack["romance_terms"], code
        assert all("(?P<age>" in pattern for pattern in pack["age_patterns"]), code


# A live campaign's retcon: the relationship began at nineteen, after a span of work from fifteen.
VERA_TR = (
    "35. gün akşam: Delmora'yla geçmişini ve neden ayrıldığını Tolon'a itiraf etti: on beşinden yirmi iki "
    "yaşına, yedi yıl Demir Kilit'teydi; Delmora onu önce himayesine alıp yetiştirdi, Vera ancak on "
    "dokuz yaşında sevgilisi oldu."
)
VERA_KNOWLEDGE_TR = (
    "Tolon, Vera'nın on beşinden yirmi iki yaşına, yedi yıl Demir Kilit'te çalıştığını, Delmora'nın önce "
    "yetiştirmesi, on dokuz yaşından itibaren de sevgilisi olduğunu biliyor."
)
VERA_EN = "She worked there from fifteen to twenty-two; she became his lover only at nineteen."
CLOSEST_ADULT = [
    ("tr", VERA_TR),
    ("tr", VERA_KNOWLEDGE_TR),
    ("en", VERA_EN),
    ("en", "She signed on at fifteen and sailed until twenty-two; she became his lover only at nineteen."),
    ("tr", "On beş yaşında gemiye katıldı. Vera, on dokuz yaşında, Delmora'nın sevgilisi oldu."),
    ("en", "She joined the crew at fifteen. At nineteen, she became his lover."),
]
CLOSEST_MINOR = [
    ("tr", "Yirmi iki yaşında gemiden ayrıldı; ilk sevgilisi on beş yaşındayken olmuştu."),
    ("en", "At twenty-two she left the ship; she had taken her first lover at fifteen."),
    ("tr", "On beş yaşında bir korsanla sevgili oldu, yirmi yaşında da ayrıldılar."),
    ("en", "At fifteen she took a lover; at twenty she married."),
    # A span that starts under 18 is one expression, read from its first age.
    ("tr", "On beşinden yirmi iki yaşına kadar Delmora'nın sevgilisiydi."),
    ("en", "From fifteen to twenty-two she was his lover."),
]
NOT_THE_AGE_RULE = [
    # Days of the month and clock times.
    ("tr", "Ayın on beşinde evlendiler."),
    ("tr", "Şubatın on dördünde sevgilisine bir kolye aldı."),
    ("tr", "Ayın onunda evlendiler ve limana döndüler."),
    ("en", "At 11 p.m. she kissed him goodnight at the door."),
    ("en", "At 2 a.m. the lovers finally slept."),
    ("en", "At 12 noon the bride arrived at the chapel."),
    ("en", "Married at twenty-five. At 9 a.m. every day she trains."),
    ("en", "The tavern opens from ten to twelve; lovers meet there."),
    # "yaşı" before a longer number, and its idioms.
    ("tr", "Yaşı on sekizi çoktan geçmişti; sevgilisiyle limanda buluştu."),
    ("tr", "Yaşı bir hayli ilerlemiş olan kral, genç karısını öptü."),
    ("tr", "Yaşı bir yana, hâlâ sevgilisini bekliyor."),
    ("tr", "Evlendiklerinde kocasının yaşı iki katıydı."),
    # Idioms, "dear", a child's endearment and family kisses.
    ("tr", '"Tanrı aşkına, o daha on yaşında bir çocuk!" diye bağırdı Nami.'),
    ("tr", "Aşk olsun, on iki yaşındaki çırağı mı dövdün?"),
    ("tr", "Sevgili kızım, bugün on beş yaşına girdin."),
    ("tr", "Babası öldüğünde on iki yaşındaydı; sevgili annesi onu tek başına büyüttü."),
    ("tr", "Kardeşi Elif on iki yaşında. Sevgili kardeşini korumak için her şeyi yapar."),
    ("tr", "Annesi on yaşındaki oğlunu alnından öptü."),
    ("en", "Happy birthday, sweetheart, you are ten years old today."),
    ("en", "His mother kissed him goodbye when he was ten."),
    ("en", "She kissed her ten-year-old son goodnight."),
]


@pytest.mark.parametrize(("code", "reply"), CLOSEST_MINOR)
def test_the_age_rule_flags_a_term_whose_closest_age_is_under_18(code: str, reply: str) -> None:
    assert _counts(reply, code=code)["minor_sexual_proximity"] == 1


@pytest.mark.parametrize(("code", "reply"), CLOSEST_ADULT)
def test_an_adult_age_closer_to_the_term_than_the_childhood_age_wins(code: str, reply: str) -> None:
    assert "minor_sexual_proximity" not in _counts(reply, code=code)


@pytest.mark.parametrize(("code", "reply"), NOT_THE_AGE_RULE)
def test_dates_clock_times_idioms_and_family_kisses_are_not_the_age_rule(code: str, reply: str) -> None:
    assert "minor_sexual_proximity" not in _counts(reply, code=code)


@pytest.mark.parametrize(
    ("code", "minor", "duration"),
    [
        ("fr", "Elle avait quinze ans quand elle tomba amoureuse du passeur.", "Il y avait quinze ans qu'ils étaient amants."),
        ("de", "Die fünfzehnjährige Anna verliebte sich in den Fährmann.", "Nach einer fünfzehnjährigen Liebesaffäre trennten sie sich."),
        ("es", "Una chica de quince años se enamoró del barquero.", "Tras un noviazgo de quince años, se casaron en el puerto."),
    ],
)
def test_other_packs_read_a_duration_as_no_age(code: str, minor: str, duration: str) -> None:
    assert _counts(minor, code=code)["minor_sexual_proximity"] == 1
    assert "minor_sexual_proximity" not in _counts(duration, code=code)


@pytest.mark.parametrize(
    ("code", "reply", "flagged"),
    [(code, reply, True) for code, reply in CLOSEST_MINOR]
    + [(code, reply, False) for code, reply in CLOSEST_ADULT + NOT_THE_AGE_RULE]
    + [("en", "Orphaned at twelve on the docks. Her first kiss came then.", True), ("tr", "On beşimdeyken onu ilk kez öptüm.", True)],
)
def test_the_lint_and_the_full_check_read_the_age_rule_alike(code: str, reply: str, flagged: bool) -> None:
    check_content = pytest.importorskip("check_content")
    assert ("minor_sexual_proximity" in _counts(reply, code=code)) is flagged
    assert (check_content.minor_proximity(reply) is not None) is flagged


# ---------------------------------------------------------------------------
# Rolling caps: "bir an" and negated descriptions
# ---------------------------------------------------------------------------


def test_bir_an_is_capped_at_three_in_the_last_ten_replies() -> None:
    reply = "Bir an durdu ve kapıya baktı."
    assert "avoid_phrase" not in _counts(reply, code="tr", history=_tallies({"phrase:bir an": 1}, {"phrase:bir an": 1}))
    result = _lint(reply, code="tr", history=_tallies({"phrase:bir an": 2}, {"phrase:bir an": 1}))
    assert result["counts"]["avoid_phrase"] == 1 and result["tallies"] == {"phrase:bir an": 1}
    assert '1x "bir an" (4 in last 3, cap 3 per 10 replies)' in result["summary"]
    # Only the nine replies before this one count.
    old = _tallies({"phrase:bir an": 3}, *([{}] * 9))
    assert "avoid_phrase" not in _counts(reply, code="tr", history=old)
    # A reply without the phrase is never reported, however often it came before.
    assert "avoid_phrase" not in _counts("Halvar kapıya baktı.", code="tr", history=_tallies({"phrase:bir an": 5}))


def test_a_rolling_cap_reads_the_same_way_for_an_english_pack_phrase() -> None:
    pack = copy.deepcopy(load_pack("en"))
    pack["avoid_phrases"] = [{"phrase": "a moment", "max_per_reply": 1, "rolling_max": 3, "note": ""}]
    reply = "For a moment the harbor was quiet."
    assert "avoid_phrase" not in _counts(reply, code="en", pack=pack, history=_tallies({"phrase:a moment": 1}, {}))
    result = _lint(reply, code="en", pack=pack, history=_tallies(*([{"phrase:a moment": 1}] * 3)))
    assert result["counts"]["avoid_phrase"] == 1
    assert '"a moment" (4 in last 4, cap 3 per 10 replies)' in result["summary"]


@pytest.mark.parametrize(
    ("code", "reply"),
    [
        ("tr", "Kılıcını çekmiyor ama elini kabzadan da ayırmıyor."),
        ("tr", "Sana bakmıyor, kapıya bile ama dikkatle dinliyor."),
        ("en", "Her voice did not shake, and she kept her eyes on the door."),
    ],
)
def test_one_negated_description_counts_toward_a_rolling_rate(code: str, reply: str) -> None:
    alone = _lint(reply, code=code)
    assert "negated_description" not in alone["counts"] and alone["tallies"] == {"negated": 1}
    assert "negated_description" not in _counts(reply, code=code, history=_tallies({"negated": 1}, {}))
    flagged = _lint(reply, code=code, history=_tallies({"negated": 1}, {}, {"negated": 2}))
    assert flagged["counts"]["negated_description"] == 1
    assert "1 negated description (in 3 of last 4 replies)" in flagged["summary"]


# ---------------------------------------------------------------------------
# Spelled day ordinals
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "reply"),
    [("tr", "Beşinci gün liman göründü."), ("en", "On the fifth day the harbor came into view.")],
)
def test_a_spelled_day_ordinal_leaks_only_near_the_tracked_day(code: str, reply: str) -> None:
    for day in (3, 5, 7):
        assert _counts(reply, code=code, day=day) == {"tracker_leak": 1}
    for day in (2, 8, 40):
        assert "tracker_leak" not in _counts(reply, code=code, day=day)
    assert "tracker_leak" not in _counts(reply, code=code)  # no tracked day


@pytest.mark.parametrize(
    ("code", "reply"),
    [("tr", "On beşinci gün liman göründü."), ("en", "On the twenty-fifth day the harbor came into view.")],
)
def test_a_compound_day_ordinal_leaks_on_any_day(code: str, reply: str) -> None:
    assert _counts(reply, code=code, day=90) == {"tracker_leak": 1}


def test_a_frequency_is_not_a_day_ordinal() -> None:
    assert "tracker_leak" not in _counts("Every second day the ferry crossed the strait.", code="en", day=2)


# ---------------------------------------------------------------------------
# Backend phrases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "reply",
    [
        "Kayıtlar tamam, devam edelim.",
        "Şimdi kaydı tamamlıyorum.",
        "Bir kayıt daha kaldı.",
        "Sahneyi kaydederken Halvar bekledi.",
        "Tablonun biçimi bozulmuş.",
        "Şimdi distill.",
    ],
)
def test_turkish_backend_phrases_are_meta_leaks(reply: str) -> None:
    assert _counts(reply, code="tr")["meta_leak"] == 1


def test_a_ships_log_entry_is_not_a_meta_leak() -> None:
    assert "meta_leak" not in _counts("Kaptan seyir defterine kısa bir kayıt düştü ve kalemi bıraktı.", code="tr")
    assert "meta_leak" not in _counts("The captain made a short entry in the ship's log and set down the pen.", code="en")
    assert _counts("I am updating the session log now.", code="en")["meta_leak"] == 1


# ---------------------------------------------------------------------------
# Calques
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("reply", "shown"),
    [
        ("Gülüşü gözlerine ulaşmıyordu.", "gözlerine ulaşmıyordu"),
        ("Gülümsemesi gözlerine çıkmıyordu.", "gözlerine çıkmıyordu"),
        ("Yüzündeki ifade gülümsemeye en yakın şeydi.", "gülümsemeye en yakın şeydi"),
        ("Limana taze et geldi.", "taze et"),
        ("Yeni etler gemiye bindi.", "Yeni etler"),
        ("Ev para vermez, dedi kumarbaz.", "Ev para vermez"),
        ("Sözleri havada asılı kaldı.", "havada asılı kaldı"),
        ("Gülümseme boşa gitti.", "Gülümseme boşa gitti"),
        ("Kapı kapandı. Hiçbir şey olmuyor.", "Hiçbir şey olmuyor"),
        ("Korku değil, öfke vardı yüzünde.", "Korku değil, öfke"),
    ],
)
def test_new_turkish_calques_are_reported_as_written(reply: str, shown: str) -> None:
    result = _lint(reply, code="tr")
    assert result["counts"]["calque"] == 1
    assert f'calque "{shown}"' in result["summary"]


@pytest.mark.parametrize(
    ("code", "reply"),
    [
        # A live false positive: idiomatic Turkish.
        ("tr", "Ne eksik ne fazla konuştu."),
        # "X değil, Y" inside a sentence, and "hiçbir şey olmuyor" that is no transition.
        ("tr", "Kapıyı açtı ama içeride korku değil, merak vardı."),
        ("tr", "Kapıda bekledi; hiçbir şey olmuyordu ki şaşırsın."),
        # Fresh meat that is meat, the nearest object, and a thought tag after "değil,".
        ("tr", "Pazarda taze et ve balık satılıyordu; Sanji tezgâhları tek tek geziyordu."),
        ("tr", "Kasaptan taze et aldı ve gemiye döndü."),
        ("tr", "Kapıya en yakın şey bir sandalyeydi; Zoro onu kaptı."),
        ("tr", "Pek de kötü değil, diye düşünüyor Sanji."),
        # English is the source language of these calques.
        ("en", "Her smile did not reach her eyes, and the fresh meat stood by the rail."),
    ],
)
def test_calques_skip_idioms_and_mid_sentence_forms(code: str, reply: str) -> None:
    assert "calque" not in _counts(reply, code=code)


# ---------------------------------------------------------------------------
# Gesture families
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "reply", "family", "label"),
    [
        ("tr", "Halvar'ın dudağının kenarı kıvrıldı ve kapıyı kapattı.", "lip_corner", "lip corner curls"),
        ("tr", "Ayla kaşlarını kaldırdı.", "eyebrow_raise", "eyebrow raise"),
        ("tr", "Edric yara izine dokundu.", "scar_touch", "touching a scar"),
        ("tr", "Ayla bir şey demiyor, kapıyı açıyor.", "says_nothing", "says nothing"),
        ("en", "The corner of her mouth twitched.", "lip_corner", "mouth corner twitches"),
        ("en", "She raised an eyebrow and set the cup down.", "eyebrow_raise", "eyebrow raise"),
        ("en", "He touched the scar on his jaw.", "scar_touch", "touching a scar"),
        ("en", "Marta said nothing and went back to the nets.", "says_nothing", "says nothing"),
    ],
)
def test_a_gesture_family_flags_in_three_of_the_last_ten_replies(code: str, reply: str, family: str, label: str) -> None:
    key = f"gesture:{family}"
    alone = _lint(reply, code=code)
    assert alone["tallies"] == {key: 1} and "gesture_repeat" not in alone["counts"] and alone["gesture_families"] == []
    assert "gesture_repeat" not in _counts(reply, code=code, history=_tallies({key: 1}, {}))
    result = _lint(reply, code=code, history=_tallies({key: 1}, {}, {key: 2}))
    assert result["counts"]["gesture_repeat"] == 1 and result["gesture_families"] == [family]
    assert f"gesture repeated: {label} (3 of last 4)" in result["summary"]
    # Only the nine replies before this one count.
    old = _tallies({key: 1}, {key: 1}, *([{}] * 9))
    assert "gesture_repeat" not in _counts(reply, code=code, history=old)


@pytest.mark.parametrize(
    ("code", "reply"),
    [
        ("tr", "Kaşığı kaldırdı ve çorbayı içti."),  # a spoon, not an eyebrow
        ("tr", '"Kaşlarını kaldırıp durma," dedi Halvar.'),  # speech
        ("en", '"Don\'t raise an eyebrow at me," she said.'),
        ("en", "She raised the lantern and the cup."),
    ],
)
def test_gesture_families_skip_speech_and_look_alike_words(code: str, reply: str) -> None:
    result = _lint(reply, code=code, history=_tallies(*([{"gesture:eyebrow_raise": 1}] * 5)))
    assert result["tallies"] == {} and "gesture_repeat" not in result["counts"]


# ---------------------------------------------------------------------------
# Case slips
# ---------------------------------------------------------------------------


def test_a_dotless_capital_i_opening_a_turkish_sentence() -> None:
    result = _lint("Ilk ışık surlara vurdu. Ikinci kapı açıktı.", code="tr")
    assert result["counts"]["dotless_capital"] == 2
    assert 'capital I for İ: "Ilk" (write "İlk")' in result["summary"]
    # Words Turkish spells with I are fine.
    assert "dotless_capital" not in _counts("Işık soldu. Islak taşlar parladı.", code="tr")
    # A name the campaign knows is a name, with or without its ending.
    named = "Ilse kapıyı açtı. Ilse'ninki daha uzundu."
    assert _counts(named, code="tr")["dotless_capital"] == 2
    assert "dotless_capital" not in _counts(named, code="tr", names=["Ilse"])
    # English writes I.
    assert "dotless_capital" not in _counts("Inside, Ilka waited by the fire. Ivo said little.", code="en")


def test_a_dotless_capital_i_is_read_against_the_few_words_that_start_with_i() -> None:
    # Back-vowel words too: Turkish word-initial i does not follow vowel harmony.
    slips = "Insanlar meydanda toplandı. Inanmıyorum, dedi. Ilaç işe yaradı. Imparator geldi."
    result = _lint(slips, code="tr")
    assert result["counts"]["dotless_capital"] == 4
    assert 'capital I for İ: "Insanlar" (write "İnsanlar")' in result["summary"]
    # Words that really start with ı, and a name the reply also writes inside a sentence.
    assert "dotless_capital" not in _counts("Işık soldu. Islak taşlar parladı. Irmak taştı. Isırgan her yeri sardı.", code="tr")
    assert "dotless_capital" not in _counts("Ivankov kapıyı açtı. Kapıda Ivankov bekliyordu.", code="tr")
    # English writes I whatever follows.
    assert "dotless_capital" not in _counts("Instead, Iris waited. Ideas came slowly.", code="en")


@pytest.mark.parametrize(
    ("code", "reply"),
    [("tr", "İlse kapıyı açtı. İlse'nin eli titriyordu."), ("en", "İlse opened the door. İlse's hands shook.")],
)
def test_a_name_written_with_the_other_capital_i(code: str, reply: str) -> None:
    result = _lint(reply, code=code, names=["Ilse"], cast_names=["Ilse"])
    assert result["counts"]["name_case_mismatch"] == 2
    assert '"İlse" written for "Ilse"' in result["summary"]
    right = reply.replace("İlse", "Ilse")
    assert _counts(right, code=code, names=["Ilse"], cast_names=["Ilse"]) == {}
    # The other way round: the card writes İ.
    assert _counts("Ilkay geldi.", code=code, names=["İlkay"])["name_case_mismatch"] == 1
    assert "name_case_mismatch" not in _counts("İlkay geldi.", code=code, names=["İlkay"])


# ---------------------------------------------------------------------------
# Short English lines
# ---------------------------------------------------------------------------


def test_a_short_english_line_in_a_turkish_reply() -> None:
    reply = "Halvar kapıyı açtı ve avluya çıktı.\n\nNow the distill.\n\nAyla bekliyor."
    result = _lint(reply, code="tr")
    assert result["counts"]["foreign_short_line"] == 1
    assert 'short English line: "Now the distill."' in result["summary"]
    # Turkish short lines and a lone English word are not.
    assert "foreign_short_line" not in _counts("Halvar kapıyı açtı.\n\nŞimdi gidelim.\n\nTamam, OK.", code="tr")
    # An English reply is in its own language.
    assert "foreign_short_line" not in _counts("Halvar opened the gate.\n\nNow the distill.", code="en")


# ---------------------------------------------------------------------------
# Names left out of detection and phrase counts
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "line", "name"),
    [("tr", "Kara Kanadı'nın Gölgesi bekliyor.", "Kara Kanadı'nın Gölgesi"), ("en", "Harbor Warden Vell waits.", "Harbor Warden Vell")],
)
def test_names_are_not_repeated_phrases(code: str, line: str, name: str) -> None:
    def history(**context) -> list[dict]:
        records = [_lint(line, code=code, **context) for _ in range(2)]
        return [{"fingerprint": record["fingerprint"], "trigrams": record["trigrams"]} for record in records]

    assert _counts(line, code=code, history=history())["repetition"] == 1
    assert "repetition" not in _counts(line, code=code, history=history(names=[name]), names=[name])


def test_names_are_not_another_language() -> None:
    names = ["The Lady of the Lake", "Knight of the Rose"]
    # The lower-case words that join a name's capitalized words belong to it, with any ending after it.
    cases = (("Halvar, Lady of the Lake'in kapısında bekledi.", "out_of_language"), ("Lady of the Lake.", "foreign_short_line"))
    for reply, rule in cases:
        assert _counts(reply, code="tr")[rule] == 1
        assert rule not in _counts(reply, code="tr", names=names)
    # Tool descriptions too.
    description = ["Lady of the Lake notu"]
    assert _counts("Halvar kapıyı açtı.", code="tr", descriptions=description)["out_of_language"] == 1
    assert "out_of_language" not in _counts("Halvar kapıyı açtı.", code="tr", descriptions=description, names=names)
    # An English reply naming Turkish places.
    line = "Deniz ve Kum, Taş ile Su."
    assert _counts(line, code="en")["out_of_language"] == 1
    assert "out_of_language" not in _counts(line, code="en", names=["Deniz ve Kum", "Taş ile Su"])
    # Joining words belong to a name only between two of its words.
    assert _counts("Halvar of the Lake.", code="tr", names=names)["foreign_short_line"] == 1


# ---------------------------------------------------------------------------
# Out-of-character turns
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "prompt", "note", "prose", "leak", "in_fiction"),
    [
        (
            "tr",
            "OOC: zarı tekrar atma lütfen",
            "(OOC: Tamam, sahneyi kaydederken zarı yeniden atmıyorum.)",
            "Halvar kapıyı açtı ve avluya çıktı.",
            " Kayıtlar tamam.",
            "Kapıyı açıyorum.",
        ),
        (
            "en",
            "OOC: no reroll please",
            "(OOC: Sure, no reroll; the session log stays as it is.)",
            "Marta opens the door and steps into the yard.",
            " The session log is updated.",
            "I open the door.",
        ),
    ],
)
def test_an_ooc_turn_lints_the_prose_outside_the_ooc_note(
    code: str, prompt: str, note: str, prose: str, leak: str, in_fiction: str
) -> None:
    reply = f"{note}\n\n{prose}"
    assert "meta_leak" not in _counts(reply, code=code, prompt=prompt)
    assert _counts(reply + leak, code=code, prompt=prompt)["meta_leak"] == 1
    # An in-fiction turn reads everything the Player saw.
    assert _counts(reply, code=code, prompt=in_fiction)["meta_leak"] == 1


@pytest.mark.parametrize(
    ("code", "reply"),
    [
        ("tr", "Halvar kapıyı açtı (OOC: bugün 92. gün) ve avluya çıktı."),
        ("en", "Marta opens the door (OOC: day 92) and steps into the yard."),
    ],
)
def test_an_ooc_parenthetical_is_not_prose(code: str, reply: str) -> None:
    assert "tracker_leak" not in _counts(reply, code=code, day=92)
    assert _counts(reply.replace("(OOC: ", "(").replace(")", ""), code=code, day=92)["tracker_leak"] == 1


# ---------------------------------------------------------------------------
# NPC echoes and paraphrased restatements
# ---------------------------------------------------------------------------


PROMPT_ECHO = {"tr": "Halvar'a fenerin kimde olduğunu soruyorum.", "en": "I ask Marta who took the lantern."}


@pytest.mark.parametrize(
    ("code", "reply"),
    [
        ("tr", 'Halvar bir süre sustu. "Fener mi?" diye tekrarlıyor, gözlerini kısarak.'),
        ("tr", 'Halvar "fener" sözünü yavaşça yineliyor.'),
        ("en", 'Marta pauses. "The lantern?" she repeats, frowning.'),
        ("en", 'Marta echoes the word "lantern" under her breath.'),
        # The quotative "diye" marks its clause's words as speech, quoted or not.
        ("tr", "Fener mi, diye tekrarlıyor Halvar ve gözlerini kısıyor."),
        # Past-tense narration echoes too.
        ("en", '"The lantern," she echoed, and set the cup down.'),
    ],
)
def test_an_npc_echoing_the_players_words(code: str, reply: str) -> None:
    result = _lint(reply, code=code, prompt=PROMPT_ECHO[code])
    assert result["counts"]["npc_echo"] == 1
    assert "NPC repeats the Player's words" in result["summary"]


@pytest.mark.parametrize(
    ("code", "prompt", "reply"),
    [
        ("en", "I walk into the cave and call out for Nami.", "Your voice echoes through the cave, and something answers from the dark."),
        ("en", "I strike the door again and again.", "Repeated blows splinter the door at last."),
        ("tr", "Kapıyı yumrukluyorum.", "Yumruklarının sesi koridorda tekrarlanıyor, kapı sarsılıyor ama açılmıyor."),
        ("tr", "Halvar'a fenerin kimde olduğunu soruyorum.", "Kapının gıcırtısı koridorda yineliyor; fener sönmüş."),
    ],
)
def test_an_echo_verb_without_speech_is_no_npc_echo(code: str, prompt: str, reply: str) -> None:
    assert "npc_echo" not in _counts(reply, code=code, prompt=prompt)


@pytest.mark.parametrize(
    ("code", "prompt", "reply", "quoted"),
    [
        (
            "tr",
            "Bana haritayı ver, diyorum.",
            "Liman sessizdi, rüzgar sertti ve gemiler iskelede sallanıyordu; kaptan halatları tek tek kontrol etti. "
            "Kadın 'haritayı mı' diye tekrarlıyor.",
            "Kadın 'haritayı mı' diye tekrarlıyor",
        ),
        (
            "en",
            "I ask Marta who took the lantern.",
            "The harbor was quiet, the wind was hard and the boats rocked at the pier; the captain checked every line. "
            '"The lantern?" she repeats.',
            '"The lantern?" she repeats',
        ),
    ],
)
def test_the_npc_echo_note_quotes_the_echo(code: str, prompt: str, reply: str, quoted: str) -> None:
    assert f"NPC repeats the Player's words: \"{quoted}\"" in _lint(reply, code=code, prompt=prompt)["summary"]


@pytest.mark.parametrize(
    ("code", "reply"),
    [
        # The NPC the Player addressed is named, not echoed.
        ("tr", "Çan sesi Halvar'ın arkasında yineliyor; avlu boş."),
        ("en", "Marta pauses. The bell repeats its call over the harbor."),
        # An echo verb with none of the prompt's words near it.
        ("tr", "Rüzgâr aynı ıslığı yineliyor; avlu boş, karanlık ve soğuk, kuyunun başında kimse yok. Halvar fenerin camını sildi."),
        ("en", "The gulls repeat their cries over the empty quay, and far off, by the gate, someone lights a lantern."),
    ],
)
def test_an_echo_verb_needs_a_prompt_content_word_near_it(code: str, reply: str) -> None:
    assert "npc_echo" not in _counts(reply, code=code, prompt=PROMPT_ECHO[code])


PROMPT_ACT = {"tr": "Kapıyı açıp avluya bakıyorum.", "en": "I open the door and look into the courtyard."}


@pytest.mark.parametrize(
    ("code", "reply"),
    [
        ("tr", "Kapıyı yavaşça itip avluya çıkıyorsun. Gece serindi ve fenerler sönmüştü."),
        ("en", "You push the heavy door and step into the courtyard. The night is cold."),
    ],
)
def test_an_opening_that_retells_the_players_action(code: str, reply: str) -> None:
    result = _lint(reply, code=code, prompt=PROMPT_ACT[code])
    assert result["counts"]["restatement"] == 1
    assert "opening retells the Player's action" in result["summary"]


@pytest.mark.parametrize(
    ("code", "reply"),
    [
        # No second-person verb.
        ("tr", "Avlu karanlıktı; fenerler çoktan sönmüştü ve kuyunun başında kimse yoktu."),
        ("en", "The courtyard is cold and empty; the lanterns have burned out."),
        # A second-person verb sharing one stem with the prompt.
        ("tr", "Soğuğu hemen yüzünde hissediyorsun; avlu karanlık."),
        ("en", "You feel the cold at once. The courtyard is empty."),
    ],
)
def test_a_first_sentence_needs_two_prompt_stems_and_a_second_person_verb(code: str, reply: str) -> None:
    assert "restatement" not in _counts(reply, code=code, prompt=PROMPT_ACT[code])


# ---------------------------------------------------------------------------
# The player character's lines
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "prompt", "reply", "kind"),
    [
        ("tr", "Halvar'ın yanından ayrılıp kapıya yürüyorum.", '"Bunu sonra konuşuruz," diyorsun. Halvar başını salladı.', "fabricated"),
        ("tr", '"Yarın gel," diyorum Halvar\'a.', '"Bunu sonra konuşuruz," diyorsun. Halvar başını salladı.', "rewritten"),
        ("en", "I leave Marta and walk to the door.", '"We talk later," you say. Marta nods.', "fabricated"),
        ("en", 'I tell Marta, "Come back tomorrow."', '"We talk later," you say. Marta nods.', "rewritten"),
    ],
)
def test_a_pc_line_the_player_never_wrote(code: str, prompt: str, reply: str, kind: str) -> None:
    result = _lint(reply, code=code, prompt=prompt)
    assert result["counts"]["pc_line_rewritten"] == 1
    assert f"PC line {kind}:" in result["summary"]
    finding = next(finding for finding in result["findings"] if finding["rule"] == "pc_line_rewritten")
    assert finding["evidence"][1].startswith("Player: ")


@pytest.mark.parametrize(
    ("code", "prompt", "reply"),
    [
        ("tr", '"Yarın gel," diyorum Halvar\'a.', 'Halvar başını salladı. "Yarın gel," diyorsun ona tekrar.'),
        ("tr", "Halvar'a yarın gelmesini söylüyorum.", 'Halvar başını salladı. "Yarın gel," diyorsun.'),
        ("en", 'I tell Marta, "Come back tomorrow."', 'Marta nods slowly. "Come back tomorrow," you say again.'),
        # An NPC's line is not the player character's.
        ("en", "I leave Marta and walk to the door.", 'Marta looks up. "We talk later," she says.'),
    ],
)
def test_a_pc_line_in_the_players_own_words_passes(code: str, prompt: str, reply: str) -> None:
    assert "pc_line_rewritten" not in _counts(reply, code=code, prompt=prompt)


# ---------------------------------------------------------------------------
# Tool descriptions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "description"),
    [
        ("tr", "Edric notunu güncelle"),
        ("tr", "Gizli geçidi kaydet"),
        ("tr", "Kapının sırrını sakla"),
        ("en", "Update Edric's note"),
        ("en", "Record the secret passage"),
    ],
)
def test_a_tool_description_with_a_cast_name_or_a_secret_word(code: str, description: str) -> None:
    reply = {"tr": "Halvar kapıyı açtı.", "en": "Marta opens the door."}[code]
    result = _lint(reply, code=code, descriptions=[description], cast_names=["Edric"])
    assert result["counts"]["tool_description_leak"] == 1
    # The note stays generic: the description may hold a protected name.
    assert "1 tool description with a cast name or a secret word" in result["summary"]
    assert description not in result["summary"]


@pytest.mark.parametrize(("code", "description"), [("tr", "Read the secret notes"), ("tr", "Open the hidden ledger"), ("en", "Gizli geçidi kaydet")])
def test_english_secret_words_count_in_any_play_language(code: str, description: str) -> None:
    # Tool descriptions are often English; a Turkish game reads English secret words too.
    reply = {"tr": "Halvar kapıyı açtı.", "en": "Marta opens the door."}[code]
    expected = 0 if code == "en" else 1
    assert _counts(reply, code=code, descriptions=[description]).get("tool_description_leak", 0) == expected


@pytest.mark.parametrize(("code", "description"), [("tr", "Sahneyi kaydet"), ("tr", "Save the scene"), ("en", "Save the scene"), ("en", "Update the edric field")])
def test_a_plain_tool_description_passes(code: str, description: str) -> None:
    reply = {"tr": "Halvar kapıyı açtı.", "en": "Marta opens the door."}[code]
    assert "tool_description_leak" not in _counts(reply, code=code, descriptions=[description], cast_names=["Edric"])


# ---------------------------------------------------------------------------
# The hook: the current turn only, counts and short snippets only
# ---------------------------------------------------------------------------


def _user(text: str, uuid: str) -> dict:
    return {"type": "user", "uuid": uuid, "timestamp": "2026-11-04T10:00:00Z", "message": {"role": "user", "content": text}}


def _assistant(text: str) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


def _event(project: Path, transcript: Path) -> dict:
    return {"session_id": "s-1", "transcript_path": str(transcript), "cwd": str(project), "hook_event_name": "Stop"}


def test_the_hook_stores_the_prompt_language_and_never_the_text(campaign: Path, tmp_path: Path) -> None:
    prompt = "Halvar'a kapıyı kimin kilitlediğini ve neden bu gece kimsenin çıkmadığını soruyorum."
    earlier = "Kayıtlar tamam. Bir an durdu. Bir an baktı. Bir an bekledi. Bir an sustu."
    reply = (
        "Halvar kapının önünde durdu ve sana döndü; dudağının kenarı kıvrıldı. Avludaki fenerin ışığı yüzüne "
        "vuruyordu ve uzaktan bir köpeğin havlaması duyuldu, sonra her şey yeniden sessizleşti. Kayıt daha kaldı."
    )
    transcript = tmp_path / "session.jsonl"
    rows = [_user("Avluya çıkıyorum.", "u-0"), _assistant(earlier), _user(prompt, "u-1"), _assistant(reply)]
    transcript.write_bytes("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode("utf-8"))
    record = run_hook(_event(tmp_path, transcript))
    assert record is not None
    # Only the current turn is linted: the earlier reply's "bir an" run is not counted.
    assert record["counts"] == {"meta_leak": 1}
    history = read_jsonl(_runtime(campaign) / LINT_HISTORY)
    assert len(history) == 1
    stored = history[0]
    assert stored["prompt_language"] == "tr" and "prompt_sample" not in stored
    assert stored["tallies"] == {"gesture:lip_corner": 1}
    text = json.dumps(stored, ensure_ascii=False)
    for piece in (prompt, "Halvar", "fenerin", "kilitlediğini"):
        assert piece not in text
    last = json.loads((_runtime(campaign) / LINT_LAST).read_text(encoding="utf-8"))
    assert all(len(snippet) <= SNIPPET_CHARS for finding in last["findings"] for snippet in finding["evidence"])
    assert reply not in json.dumps(last, ensure_ascii=False)


def test_the_module_documents_what_the_hook_reads_and_stores() -> None:
    doc = " ".join(presentation_lint.__doc__.split())
    assert "reads only the current session's last turn, locally" in doc
    assert "it never stores the prompt or the reply" in doc


def _transcript(tmp_path: Path, prompt: str, reply: str, name: str = "session.jsonl") -> Path:
    path = tmp_path / name
    rows = [_user(prompt, f"u-{name}"), _assistant(reply)]
    path.write_bytes("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode("utf-8"))
    return path


@pytest.mark.parametrize(
    ("prompt", "note", "prose"),
    [
        ("OOC: tell me about Marta's past", "(OOC: At fifteen she had a lover, if you want that in her backstory.)", "Marta mends the nets in silence."),
        (
            "OOC: Ayla'nın geçmişini anlatır mısın?",
            "(OOC: On beş yaşındayken Kerem'e âşık olmuştu, istersen geçmişine ekleriz.)",
            "Ayla ağları onarıyor.",
        ),
    ],
)
def test_a_short_ooc_answer_keeps_its_age_finding(campaign: Path, tmp_path: Path, prompt: str, note: str, prose: str) -> None:
    record = run_hook(_event(tmp_path, _transcript(tmp_path, prompt, f"{note}\n\n{prose}")))
    assert record is not None and record["counts"] == {"minor_sexual_proximity": 1}
    assert record["summary"].startswith("Last reply: age under 18 near a romance or sex term")
    (stored,) = read_jsonl(_runtime(campaign) / LINT_HISTORY)
    assert stored["counts"] == {"minor_sexual_proximity": 1}
    assert stored["tallies"] == {} and stored["fingerprint"] == [] and stored["trigrams"] == []
    # A short out-of-character answer with no age finding is still not recorded.
    quiet = note.replace("fifteen", "twenty").replace("On beş", "Yirmi")
    assert run_hook(_event(tmp_path, _transcript(tmp_path, prompt, f"{quiet}\n\n{prose}", "quiet.jsonl"))) is None
    assert len(read_jsonl(_runtime(campaign) / LINT_HISTORY)) == 1


@pytest.mark.parametrize(
    ("stored", "prompt", "expected"),
    [
        ("tr", "OOC: can you remind me what the dice rules are and how the bands work again?", "tr"),
        ("tr", "I walk down to the harbor and look for the old ship and its captain.", "tr"),
        ("en", "Limana inip eski gemiyi ve kaptanını arıyorum, sonra da meyhaneye gidiyorum.", "en"),
    ],
)
def test_one_prompt_in_another_language_does_not_switch_the_pack(stored: str, prompt: str, expected: str) -> None:
    earlier = [{"prompt_language": stored}] * 5
    assert presentation_lint.resolve_language("auto", prompt, earlier, "")[:2] == (expected, "prompts")
    # With no earlier prompts, or when most of them agree with it, the prompt decides.
    assert presentation_lint.resolve_language("auto", prompt, [], "")[0] != stored
    other = presentation_lint.resolve_language("auto", prompt, [], "")[0]
    assert presentation_lint.resolve_language("auto", prompt, [{"prompt_language": other}] * 3 + earlier[:2], "")[0] == other


def test_the_hook_drops_prompt_samples_a_0_3_0_history_kept(campaign: Path, tmp_path: Path) -> None:
    sample = "Gizli planımı Halvar'a anlatıyorum ve kapıyı kilitliyorum."
    old = [
        {"prompt_uuid": f"p{index}", "prompt_sample": sample, "language": "tr", "counts": {}, "fingerprint": [], "trigrams": []}
        for index in range(3)
    ]
    _write_jsonl(_runtime(campaign) / LINT_HISTORY, old)
    record = run_hook(_event(tmp_path, _transcript(tmp_path, "Evet.", "Halvar başını kaldırdı.")))
    assert record is not None and (record["language"], record["language_source"]) == ("tr", "prompts")
    raw = (_runtime(campaign) / LINT_HISTORY).read_text(encoding="utf-8")
    assert "prompt_sample" not in raw and "Gizli" not in raw and "Halvar" not in raw
    history = read_jsonl(_runtime(campaign) / LINT_HISTORY)
    assert len(history) == 4 and [row["prompt_language"] for row in history[:3]] == ["tr"] * 3
    # Later runs append as before.
    run_hook(_event(tmp_path, _transcript(tmp_path, "Hayır.", "Halvar kapıyı kapattı.", "next.jsonl")))
    assert len(read_jsonl(_runtime(campaign) / LINT_HISTORY)) == 5


# ---------------------------------------------------------------------------
# top_habits and report_summary
# ---------------------------------------------------------------------------


def _row(uuid: str, counts: dict[str, int], families: tuple[str, ...] = ()) -> dict:
    """A reply record as the hook stores it, without the n-gram hashes."""

    return {"prompt_uuid": uuid, "language": "tr", "counts": counts, "gesture_families": list(families)}


HABIT_ROWS = [
    _row("p1", {"avoid_phrase": 2, "gesture_repeat": 1}, ("lip_corner",)),
    _row("p2", {"avoid_phrase": 1, "restatement": 1}),
    _row("p3", {"gesture_repeat": 2}, ("lip_corner", "eyebrow_raise")),
    _row("p4", {"restatement": 1, "calque": 1}),
    _row("p5", {}),
]


def test_top_habits_counts_replies_per_rule_and_per_gesture_family(campaign: Path) -> None:
    assert top_habits(campaign) == []
    _write_jsonl(_runtime(campaign) / LINT_HISTORY, HABIT_ROWS)
    _write(
        _runtime(campaign) / LINT_LAST,
        json.dumps({"findings": [{"rule": "avoid_phrase", "count": 1, "evidence": ['"bir an" x1 (4 in last 3)']}]}),
    )
    habits = top_habits(campaign)
    assert habits == [
        {"rule": "avoid_phrase", "label": "stock phrases", "count": 2, "example": '"bir an" x1 (4 in last 3)'},
        {"rule": "restatement", "label": "restating openings", "count": 2, "example": ""},
        {"rule": "gesture_repeat:lip_corner", "label": "lip corner curls", "count": 2, "example": "dudağının kenarı kıvrıldı"},
    ]
    assert [(habit["rule"], habit["count"]) for habit in top_habits(campaign, last=2)] == [("restatement", 1), ("calque", 1)]
    assert [habit["rule"] for habit in top_habits(campaign, limit=5)][3:] == ["calque", "gesture_repeat:eyebrow_raise"]
    assert top_habits(campaign, limit=0) == []


def test_report_summary_for_the_distill_result(campaign: Path) -> None:
    assert report_summary(campaign) == {"replies": 0, "rules": {}, "top": [], "text": "No linted replies yet."}
    _write_jsonl(_runtime(campaign) / LINT_HISTORY, HABIT_ROWS)
    summary = report_summary(campaign)
    assert summary["replies"] == 5 and summary["top"] == top_habits(campaign)
    assert summary["rules"] == {"avoid_phrase": 2, "restatement": 2, "calque": 1, "gesture_repeat": 2}
    assert summary["text"] == (
        "Presentation lint, last 5 replies: 1 clean; "
        "most flagged: stock phrases (2), restating openings (2), lip corner curls (2)."
    )
    assert report_summary(campaign, last=1)["text"] == "Presentation lint, last 1 reply: 1 clean."


def test_report_summary_leads_with_the_age_rule_and_stays_short(campaign: Path) -> None:
    rows = HABIT_ROWS + [_row("p6", {"minor_sexual_proximity": 1, "calque": 1})]
    _write_jsonl(_runtime(campaign) / LINT_HISTORY, rows)
    _write(_runtime(campaign) / LINT_LAST, json.dumps({"summary": "Last reply: " + "x" * 900 + "."}))
    summary = report_summary(campaign)
    assert summary["text"].startswith(
        "Presentation lint, 1 reply put an age under 18 near a romance or sex term; check every age; last 6 replies"
    )
    assert list(summary["rules"])[0] == "minor_sexual_proximity"
    assert len(summary["text"]) <= REPORT_TEXT_MAX and summary["text"].endswith("…")


def test_protected_name_evidence_never_becomes_a_habit_example(campaign: Path) -> None:
    rows = [_row("p1", {"secret_leak": 1, "tool_description_leak": 1, "calque": 1}), _row("p2", {"secret_leak": 1})]
    _write_jsonl(_runtime(campaign) / LINT_HISTORY, rows)
    findings = [
        {"rule": "secret_leak", "count": 1, "evidence": ["…the heir is Prince Varo of the hidden line…"]},
        {"rule": "tool_description_leak", "count": 1, "evidence": ["[tool] Note Prince Varo's claim"]},
        {"rule": "calque", "count": 1, "evidence": ["sesi düzdü"]},
    ]
    _write(_runtime(campaign) / LINT_LAST, json.dumps({"findings": findings}))
    habits = {habit["rule"]: habit for habit in top_habits(campaign, limit=5)}
    assert habits["secret_leak"]["example"] == "" and habits["tool_description_leak"]["example"] == ""
    assert habits["calque"]["example"] == "sesi düzdü"
    assert "Varo" not in json.dumps(report_summary(campaign), ensure_ascii=False)
