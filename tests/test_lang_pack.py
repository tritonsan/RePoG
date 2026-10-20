"""Language packs: shipped pack content and the lang_pack helpers."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

import lang_pack
from lang_pack import (
    available_codes,
    compile_patterns,
    count_phrase,
    detect_language,
    find_patterns,
    fold,
    load_guidance,
    load_pack,
    sentence_split,
    stopword_ratios,
    tokens,
    words,
)


SHIPPED = ["de", "en", "es", "fr", "tr"]
KNOWN_KEYS = {
    "code",
    "name",
    "casefold",
    "stopwords",
    "avoid_phrases",
    "negated_description",
    "day_patterns",
    "pc_speech_patterns",
    "meta_words",
    "calques",
    "common_words",
    "card",
}
REGEX_KEYS = ("negated_description", "day_patterns", "pc_speech_patterns")


def _raw(code: str) -> dict:
    return json.loads((lang_pack.PACK_DIR / f"{code}.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Shipped packs
# ---------------------------------------------------------------------------


def test_available_codes_lists_every_shipped_pack() -> None:
    codes = available_codes()
    assert codes == sorted(codes)
    assert set(SHIPPED) <= set(codes)


@pytest.mark.parametrize("code", SHIPPED)
def test_pack_file_shape(code: str) -> None:
    path = lang_pack.PACK_DIR / f"{code}.json"
    data = path.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf") and b"\r" not in data
    raw = _raw(code)
    assert set(raw) <= KNOWN_KEYS
    assert raw["code"] == code and raw["name"].strip()
    assert raw.get("casefold", "default") in {"turkish", "default"}
    pack = load_pack(code)
    folded = [fold(word, pack) for word in raw["stopwords"]]
    assert 80 <= len(folded) <= 200
    assert len(set(folded)) == len(folded), "stopwords must be unique after folding"
    assert all(words(word, pack) == [word] for word in folded), "each stopword is one token"
    for key in REGEX_KEYS:
        for pattern in raw.get(key, []):
            re.compile(pattern)
    assert raw["pc_speech_patterns"] and raw["day_patterns"]
    assert 0 < len(raw["card"]) <= 600


@pytest.mark.parametrize("code", SHIPPED)
def test_optional_lists_are_well_formed(code: str) -> None:
    raw = _raw(code)
    for item in raw.get("avoid_phrases", []):
        assert set(item) <= {"phrase", "max_per_reply", "note"}
        assert item["phrase"].strip() and isinstance(item["max_per_reply"], int) and item["max_per_reply"] >= 0
    for item in raw.get("calques", []):
        assert set(item) == {"bad", "better"} and item["bad"].strip() and item["better"].strip()
    for key in ("meta_words", "common_words"):
        values = raw.get(key, [])
        assert all(isinstance(value, str) and value.strip() for value in values)
        assert len(set(values)) == len(values)


def test_turkish_pack_carries_the_live_session_evidence() -> None:
    pack = load_pack("tr")
    assert pack["casefold"] == "turkish"
    phrases = {item["phrase"] for item in pack["avoid_phrases"]}
    assert {
        "bir an",
        "başka bir şey demedi",
        "başka bir şey söylemedi",
        "başka bir şey eklemedi",
        "cevabını bekliyor",
        "sesi titremiyordu",
    } <= phrases
    bad = {item["bad"] for item in pack["calques"]}
    assert {
        "yüzünde hiçbir şey yoktu",
        "sesi düzdü",
        "gözleri üstünde kaldı",
        "bir şeyi tartıyordu",
        "ne eksik ne fazla",
        "surlarda çok yakışıyorsun",
    } <= bad
    assert {"tam", "kara", "ak", "er", "bay", "han", "bey", "ay", "can", "nur"} <= set(pack["common_words"])
    assert "sen" in pack["card"] and "siz" in pack["card"]
    assert "çeyrek saat" not in json.dumps(_raw("tr"), ensure_ascii=False)


def test_english_pack_seed_content() -> None:
    pack = load_pack("en")
    phrases = {item["phrase"] for item in pack["avoid_phrases"]}
    assert {"a moment", "said nothing else", "did not waver"} <= phrases
    # Only unambiguous collocations: "commit" or "helper" alone is ordinary English.
    assert {"campaign file", "operation id", "continuity revision", "durable commit"} <= set(pack["meta_words"])
    assert not {"commit", "helper", "revision", "persistence"} & set(pack["meta_words"])


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def test_unknown_or_unsafe_codes_get_an_empty_pack() -> None:
    assert load_pack("xx") == {"code": "xx", "stopwords": []}
    assert load_pack("auto") == {"code": "auto", "stopwords": []}
    assert load_pack("../tr") == {"code": "../tr", "stopwords": []}
    assert load_pack("") == {"code": "", "stopwords": []}


def test_region_subtags_and_case_resolve_to_the_primary_language() -> None:
    assert load_pack("tr-TR")["code"] == "tr"
    assert load_pack("EN_gb")["name"] == "English"


def test_load_pack_returns_a_private_copy() -> None:
    first = load_pack("tr")
    first["stopwords"].append("zzz")
    first["avoid_phrases"].append({"phrase": "x", "max_per_reply": 0, "note": ""})
    second = load_pack("tr")
    assert "zzz" not in second["stopwords"]
    assert all(item["phrase"] != "x" for item in second["avoid_phrases"])


def test_broken_packs_never_raise(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "aa.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "bb.json").write_text(
        json.dumps(
            {
                "code": "bb",
                "name": "Bee",
                "stopwords": ["zz", 7, ""],
                "day_patterns": ["(unclosed", "\\bdag\\s+\\d+"],
                "avoid_phrases": [{"phrase": "ok"}, {"max_per_reply": 2}, "loose"],
                "calques": "not a list",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(lang_pack, "PACK_DIR", tmp_path)
    assert load_pack("aa") == {"code": "aa", "stopwords": []}
    assert available_codes() == ["bb"]
    pack = load_pack("bb")
    assert pack["stopwords"] == ["zz"]
    assert pack["avoid_phrases"] == [{"phrase": "ok", "max_per_reply": 1, "note": ""}]
    assert pack["calques"] == []
    assert find_patterns("Dag 4 begins", pack, "day_patterns") == ["dag 4"]
    assert detect_language("zz " * 10) == ("bb", 1.0)
    monkeypatch.undo()
    assert set(SHIPPED) <= set(available_codes())  # caches are per directory, nothing stale


def test_guidance_packs() -> None:
    for code in ("tr", "en"):
        text = load_guidance(code)
        size = len(text.encode("utf-8"))
        assert 1000 <= size <= 2048, (code, size)
        section = text.split("## Sound like this", 1)[1]
        exemplars = [line for line in section.splitlines() if line.startswith("- ")]
        assert 6 <= len(exemplars) <= 10
    assert load_guidance("xx") == "" and load_guidance("../tr") == ""


# ---------------------------------------------------------------------------
# Folding, tokens, phrases
# ---------------------------------------------------------------------------


def test_turkish_fold_keeps_dotted_and_dotless_i_apart() -> None:
    tr = load_pack("tr")
    assert fold("IŞIK", tr) == "ışık"
    assert fold("İçini", tr) == "içini"
    assert fold("KIRMIZI İPEK", tr) == "kırmızı ipek"
    assert fold("hâlâ Kâğıt", tr) == "hala kağıt"
    assert fold("i\u0307çini", tr) == "içini"  # what str.lower() leaves of "İçini"


def test_default_fold() -> None:
    en = load_pack("en")
    assert fold("Island I", en) == "island i"
    assert fold("İstanbul", en) == "istanbul"
    assert fold("Straße", load_pack("de")) == "strasse"
    assert fold("ÉTÉ", load_pack("fr")) == "été"
    assert fold("Text", None) == "text"


def test_tokens_split_on_punctuation_in_any_script() -> None:
    assert tokens("Ali'nin l'homme snake_case well-known 92.") == [
        "Ali",
        "nin",
        "l",
        "homme",
        "snake",
        "case",
        "well",
        "known",
        "92",
    ]
    assert tokens("हिन्दी भाषा") == ["हिन्दी", "भाषा"]  # vowel signs stay inside the word
    assert tokens("Привет, мир!") == ["Привет", "мир"]
    assert tokens("") == []


@pytest.mark.parametrize(
    ("code", "text", "phrase", "expected"),
    [
        ("tr", "Bir an durdu, sonra bir anahtar çıkardı. Bir an daha.", "bir an", 2),
        ("tr", "İçini bir korku kapladı; içini döktü.", "içini", 2),
        ("tr", "IŞIK söndü, ışık yandı.", "ışık", 2),
        ("tr", "Başka bir şey   demedi.", "başka bir şey demedi", 1),
        ("tr", "Yüzünde hiçbir şey yoktu.", "yüzünde hiçbir şey yoktu", 1),
        ("en", "She didn’t waver. He didn't waver.", "didn't waver", 2),
        ("en", "For a moment, a momentary pause.", "a moment", 1),
        ("en", "A moment. A moment. A moment.", "A MOMENT", 3),
        ("de", "Die Straße war leer.", "strasse", 1),
        ("en", "anything", "", 0),
    ],
)
def test_count_phrase(code: str, text: str, phrase: str, expected: int) -> None:
    assert count_phrase(text, phrase, load_pack(code)) == expected


def test_count_phrase_does_not_overlap() -> None:
    assert count_phrase("ne ne ne", "ne ne", load_pack("tr")) == 1


# ---------------------------------------------------------------------------
# Sentences
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            '"Gel." Kapıyı açtı. Bugün 92. gün değil mi? Ama… belki de öyleydi.',
            ['"Gel."', "Kapıyı açtı.", "Bugün 92. gün değil mi?", "Ama… belki de öyleydi."],
        ),
        ('"Stop!" she said. He left. "Wait," she called.', ['"Stop!" she said.', "He left.", '"Wait," she called.']),
        ("—¿Qué haces? —preguntó. —Nada.", ["—¿Qué haces? —preguntó.", "—Nada."]),
        ("« Viens. » Il partit... Puis revint.", ["« Viens. »", "Il partit...", "Puis revint."]),
        ("我们走吧。他说。好！", ["我们走吧。", "他说。", "好！"]),
        ("Status line\nLine two. Next one! Third?", ["Status line", "Line two.", "Next one!", "Third?"]),
        ("It took 3.5 hours.", ["It took 3.5 hours."]),
        ("", []),
    ],
)
def test_sentence_split(text: str, expected: list[str]) -> None:
    assert sentence_split(text) == expected


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------


TURKISH = [
    "Kapıyı yavaşça açtın ve içeride kimsenin olmadığını gördün.",
    "Bu gece burada kalamazsın, dedi yaşlı kadın sert bir sesle.",
    "Hancı sana bakıp başını salladı ama hiçbir şey söylemedi.",
    "Sabah olduğunda köyün üstüne ince bir sis çökmüştü.",
    "Yol boyunca kimseyle karşılaşmadınız, yalnızca uzaktan bir köpek havladı.",
    "O adamın kim olduğunu ben de bilmiyorum, ama öğrenmek istiyorum.",
    "Atlar ahırda huzursuzdu; fırtına yaklaşıyordu ve kimse uyuyamıyordu.",
    "On gün boyunca dağ yolunda yürüdüler ve hiç durmadılar.",
]
ENGLISH = [
    "The innkeeper slung the rag over his shoulder and shook his head.",
    "Rain had stopped, but water still dripped from the eaves into the yard.",
    "She looked away and said that she had seen nothing at all.",
    "If we leave at first light, we will reach the ford by noon.",
    "The guard held his spear across the gate and would not move.",
    "Word in the market is that wolves came down past the mill last night.",
    "I want to ask the miller about the missing grain before dark.",
]
GERMAN = [
    "Er öffnete die Tür und sah in den dunklen Raum.",
    "Ich weiß nicht, ob wir ihm noch trauen können.",
    "Die Wirtin stellte dir einen Becher Bier auf den Tisch.",
    "Draußen regnete es seit Stunden, und niemand wagte sich hinaus.",
    "Wenn du heute Nacht gehst, wirst du allein sein.",
    "Der alte Schmied hatte seit Tagen kein Wort gesprochen.",
    "Sie war schon fort, als der Morgen über dem Fluss graute.",
]
SPANISH = [
    "La posadera te sirvió un vaso de vino y se fue sin decir nada.",
    "No sé si podemos confiar en él, pero no tenemos otra opción.",
]
FRENCH = [
    "Elle ouvrit la porte et regarda dans la pièce sombre sans rien dire.",
    "Je ne sais pas si nous pouvons encore lui faire confiance ce soir.",
]


@pytest.mark.parametrize(
    ("code", "sentence"),
    [("tr", item) for item in TURKISH]
    + [("en", item) for item in ENGLISH]
    + [("de", item) for item in GERMAN]
    + [("es", item) for item in SPANISH]
    + [("fr", item) for item in FRENCH],
)
def test_detect_language_on_short_sentences(code: str, sentence: str) -> None:
    detected, confidence = detect_language(sentence)
    assert detected == code
    assert confidence > 0.1


def test_detect_language_on_unaccented_turkish() -> None:
    assert detect_language("Bu aksam cok yoruldum, simdi biraz uyumak istiyorum ama olmaz.")[0] == "tr"


def test_detect_language_needs_eight_words() -> None:
    assert detect_language("Kısa bir metin bu.") == (None, 0.0)
    assert detect_language("") == (None, 0.0)
    assert detect_language("1 2 3 4 5 6 7 8 9 10 and the") == (None, 0.0)  # digits are not words
    assert detect_language("Kapıyı açtın ve içeri baktın.", min_words=5)[0] == "tr"


def test_detect_language_without_any_hit_or_with_a_tie() -> None:
    assert detect_language("Gümüş kılıç parladı, rüzgâr dağlardan esti, kurtlar uludu.") == (None, 0.0)
    assert detect_language("in in in in in in in in", ["en", "de"]) == (None, 0.0)


def test_confidence_is_best_ratio_minus_second() -> None:
    sentence = "O adamın kim olduğunu ben de bilmiyorum, ama öğrenmek istiyorum."
    ratios = stopword_ratios(sentence)
    ranked = sorted(ratios.values(), reverse=True)
    assert detect_language(sentence) == ("tr", round(ranked[0] - ranked[1], 4))
    assert ratios["es"] > 0  # "o" and "de" are Spanish too; they cancel out


def test_detect_language_respects_candidates() -> None:
    german = GERMAN[0]
    assert detect_language(german, ["de"])[0] == "de"
    assert detect_language(german, ["tr", "fr"]) == (None, 0.0)
    # "in" is the only hit: one shared-looking stopword is not evidence by default.
    assert detect_language(german, ["en", "tr"]) == (None, 0.0)
    assert detect_language(german, ["en", "tr"], min_hits=1)[0] == "en"
    assert detect_language(german, []) == (None, 0.0)
    assert detect_language(german, ["DE-at", "xx"])[0] == "de"


def test_mixed_reply_leans_to_the_majority_language() -> None:
    text = " ".join(TURKISH[:4]) + " Saving the scene now."
    assert detect_language(text)[0] == "tr"


# ---------------------------------------------------------------------------
# Pack patterns
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "key", "text", "expected"),
    [
        ("tr", "day_patterns", "Bugün 92. gün, sabah erken kalktın.", ["92. gün"]),
        ("tr", "day_patterns", "Doksan ikinci gün de yağmurla başladı.", ["doksan ikinci gün"]),
        ("tr", "day_patterns", "Yüz on ikinci günün sabahıydı.", ["yüz on ikinci günün"]),
        ("tr", "day_patterns", "92'nci gün geldi, 3'üncü günü hatırladın.", ["92'nci gün", "3'üncü günü"]),
        ("tr", "day_patterns", "Kırkıncı günün akşamı kapı çalındı.", ["kırkıncı günün"]),
        ("tr", "day_patterns", "Gün 92 · akşam", ["gün 92"]),
        ("tr", "day_patterns", "Üç gün sonra döndüler; yolculuğun ikinci günü yağmur başladı.", []),
        ("tr", "pc_speech_patterns", '"Gidelim," dedin. Başını salladın.', ["dedin", "başını salladın"]),
        ("tr", "pc_speech_patterns", "Hancıya ne istediğini soruyorsun.", ["soruyorsun"]),
        ("tr", "pc_speech_patterns", "Dediniz ki yarın gelecek; sordunuz mu?", ["dediniz", "sordunuz"]),
        ("tr", "pc_speech_patterns", "Hancı sana baktı ve konuştu.", []),
        (
            "tr",
            "negated_description",
            "Sesi titremiyordu ama elleri kıpırdamadı. Korku değildi, öfkeydi.",
            ["sesi titremiyordu", "elleri kıpırdamadı", "değildi, öfkeydi"],
        ),
        (
            "tr",
            "negated_description",
            "Yüzünde hiçbir ifade yoktu; ne öfkeli ne de üzgündü.",
            ["hiçbir ifade yoktu", "ne öfkeli ne de üzgündü"],
        ),
        ("tr", "negated_description", "Bakmadı ama duydu. Gülmüyordu fakat sesi yumuşaktı.", ["bakmadı ama", "gülmüyordu fakat"]),
        ("tr", "negated_description", "Gülümsüyordu ama gözleri yorgundu.", []),
        ("en", "day_patterns", "Day 92, the ninety-second day, the 92nd day.", ["day 92", "ninety-second day", "92nd day"]),
        ("en", "day_patterns", "On the third day the rain came; three days later it stopped.", []),
        ("en", "pc_speech_patterns", '"Let\'s go," you say. You nod.', ["you say", "you nod"]),
        (
            "en",
            "negated_description",
            "Her voice didn’t waver. It wasn't fear. It was anger. Not anger, but grief.",
            ["didn’t waver", "wasn't fear. it was", "not anger, but"],
        ),
        ("de", "day_patterns", "Am 92. Tag, am dreißigsten Tag, Tag 92.", ["92. tag", "dreissigsten tag", "tag 92"]),
        ("de", "pc_speech_patterns", "„Nein“, sagst du. Du nickst.", ["sagst du", "du nickst"]),
        ("de", "negated_description", "Es war nicht Angst, sondern Zorn.", ["nicht angst, sondern"]),
        ("es", "day_patterns", "Era el día 92, el nonagésimo segundo día.", ["día 92", "nonagésimo segundo día"]),
        ("es", "pc_speech_patterns", "—Vamos —dices. Asientes.", ["dices", "asientes"]),
        ("fr", "day_patterns", "Le 92e jour, le quatre-vingt-douzième jour.", ["92e jour", "quatre-vingt-douzième jour"]),
        ("fr", "pc_speech_patterns", "« Allons-y », dis-tu. Vous dites non.", ["dis-tu", "vous dites"]),
    ],
)
def test_pack_patterns(code: str, key: str, text: str, expected: list[str]) -> None:
    assert find_patterns(text, load_pack(code), key) == expected


def test_find_patterns_counts_overlapping_matches_once() -> None:
    tr = load_pack("tr")
    assert find_patterns("Sesi titremiyordu ama.", tr, "negated_description") == ["sesi titremiyordu"]


def test_compile_patterns_skips_invalid_entries() -> None:
    pack = {"code": "x", "stopwords": [], "day_patterns": ["(broken", "\\bday\\b", 3]}
    assert [pattern.pattern for pattern in compile_patterns(pack, "day_patterns")] == ["\\bday\\b"]
    assert compile_patterns(pack, "missing") == []
    assert compile_patterns(None, "day_patterns") == []


def test_calques_are_found_with_count_phrase() -> None:
    tr = load_pack("tr")
    reply = "Yüzünde hiçbir şey yoktu. Sesi düzdü. Gözleri senin üstünde kaldı."
    found = [item["bad"] for item in tr["calques"] if count_phrase(reply, item["bad"], tr)]
    assert found == ["yüzünde hiçbir şey yoktu", "sesi düzdü", "gözleri senin üstünde kaldı"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_detect_and_codes() -> None:
    script = str(Path(lang_pack.__file__))
    detected = subprocess.run(
        [sys.executable, script, "detect"], input=GERMAN[1].encode("utf-8"), capture_output=True, check=True
    )
    assert json.loads(detected.stdout.decode("utf-8"))["language"] == "de"
    codes = subprocess.run([sys.executable, script, "codes"], capture_output=True, check=True)
    assert set(SHIPPED) <= set(json.loads(codes.stdout.decode("utf-8"))["codes"])
