"""Domain logic: shape Duden word / conjugation / search pages into
compact dicts (stdlib only).

Data source: duden.de public word pages
(https://www.duden.de/rechtschreibung/<word>) — free, no key, no login.

Page structure (server-rendered HTML, verified 2026-11-10):
- lemma in <h1>; word type / frequency in <dl class="tuple"> blocks
  (Wortart, Häufigkeit with a shaft aria-label).
- meanings: <div class="enumeration__text">…</div> inside the
  #bedeutungen division (one per numbered meaning).
- spelling: #rechtschreibung division (Worttrennung line + notes).
- synonyms: links with data-duden-ref-type="lexeme" inside the
  #synonyme division; the dedicated /synonyme/<word> overview page
  only lists alphabetical navigation, so the word page's list is used.
- grammar: first <p> of the #grammatik division
  ("das Haus; Genitiv: des Hauses, Häuser"); verbs link to
  /konjugation/<verb>.
- conjugation page: <ul class="accordion__list content-column"> lists
  in document order — first 6 are Indikativ (Präsens, Präteritum,
  Perfekt, Plusquamperfekt, Futur I, Futur II), then Konjunktiv I/II,
  then the Imperativ list (2 items, no label) and the infinite forms
  (Infinitiv mit zu / Partizip I / Partizip II, one form each).
  Footnote <sup> markers are stripped before parsing.
"""
from __future__ import annotations

import html as _html
import re
from urllib.parse import quote

BASE = "https://www.duden.de"

PERSONS = ["ich", "du", "er/sie/es", "wir", "ihr", "sie"]

TENSES = ["Präsens", "Präteritum", "Perfekt", "Plusquamperfekt",
          "Futur I", "Futur II"]
TENSE_KEYS = ["praesens", "praeteritum", "perfekt", "plusquamperfekt",
              "futur_i", "futur_ii"]

_TAG_RE = re.compile(r"<[^>]+>")
_SUP_RE = re.compile(r"<sup[^>]*>.*?</sup>", re.S)
_WS_RE = re.compile(r"\s+")

_TRANSLIT = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss",
})


def validate_word(word: str) -> str:
    w = (word or "").strip()
    if not w:
        raise ValueError("word must not be empty")
    if len(w) > 80:
        raise ValueError("word too long (max 80 characters)")
    return w


def validate_limit(limit: int) -> int:
    if not 1 <= limit <= 20:
        raise ValueError(f"limit out of range: {limit} (expected 1..20)")
    return limit


def word_slug(word: str) -> str:
    """Duden URL slug: umlauts transliterated (ä→ae …), spaces → _."""
    return word.translate(_TRANSLIT).replace(" ", "_")


def word_url(word: str) -> str:
    return f"{BASE}/rechtschreibung/{word_slug(word)}"


def conjugation_url(verb: str) -> str:
    return f"{BASE}/konjugation/{word_slug(verb)}"


def search_url(query: str) -> str:
    return f"{BASE}/suchen/dudenonline/{quote(query.strip())}"


def _clean(text: str) -> str:
    return _WS_RE.sub(" ", _html.unescape(_TAG_RE.sub(" ", text or ""))).strip()


def _division(html: str, div_id: str) -> str:
    """Raw HTML of the <div class="division" id="<div_id>"> block."""
    m = re.search(rf'id="{re.escape(div_id)}"', html)
    if not m:
        return ""
    start = html.rfind("<div", 0, m.start())
    if start < 0:
        start = m.start()
    nxt = html.find('<div class="division ', start + 10)
    return html[start:] if nxt < 0 else html[start:nxt]


def _first_paragraph(division_html: str) -> str:
    m = re.search(r"<p[^>]*>(.*?)</p>", division_html, re.S)
    return _clean(m.group(1)) if m else ""


def parse_word_page(html: str) -> dict:
    """{lemma, word_type, frequency, meanings, hyphenation, grammar,
    origin, synonyms, conjugation_url, url} — empty strings/lists
    when a section is absent (not every word has every section)."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    lemma = _clean(m.group(1)) if m else ""
    lemma = lemma.replace("­", "").replace(" ,", ",")
    m = re.search(
        r'<dt class="tuple__key">Wortart:.*?</dt>\s*'
        r'<dd class="tuple__val">(.*?)</dd>', html, re.S)
    word_type = _clean(m.group(1)) if m else ""
    m = re.search(
        r'<dt class="tuple__key">Häufigkeit:.*?'
        r'<div class="shaft" aria-label="([^"]+)"', html, re.S)
    frequency = _html.unescape(m.group(1)) if m else ""

    meanings = []
    for raw in re.findall(r'enumeration__text">(.*?)</div>', html, re.S):
        t = _clean(raw)
        if t and t not in meanings:
            meanings.append(t)

    rechtschreibung = _division(html, "rechtschreibung")
    hyphenation = ""
    if rechtschreibung:
        lines = [_clean(ln) for ln in _TAG_RE.sub("\n", rechtschreibung).split("\n")]
        lines = [ln for ln in lines if ln]
        for i, ln in enumerate(lines):
            if ln == "Worttrennung" and i + 1 < len(lines):
                # Duden marks syllable breaks with a soft hyphen or
                # a pipe; normalise both to · for display
                hyphenation = (lines[i + 1].replace("­", "·")
                               .replace("|", "·"))
                break

    grammar = _first_paragraph(_division(html, "grammatik"))
    origin = _first_paragraph(_division(html, "herkunft"))
    syn_div = _division(html, "synonyme")
    synonyms = []
    for raw in re.findall(
            r'data-duden-ref-type="lexeme"[^>]*>([^<]+)</a>', syn_div):
        w = _clean(raw)
        if w and w not in synonyms:
            synonyms.append(w)
    m = re.search(r'href="(/konjugation/[^"]+)"', html)
    conj_url = f"{BASE}{m.group(1)}" if m else ""
    return {
        "lemma": lemma,
        "word_type": word_type,
        "frequency": frequency,
        "meanings": meanings,
        "hyphenation": hyphenation,
        "grammar": grammar,
        "origin": origin,
        "synonyms": synonyms,
        "conjugation_url": conj_url,
    }


def parse_spelling(html: str) -> dict:
    """{hyphenation, notes} from the #rechtschreibung division."""
    word = parse_word_page(html)
    div = _division(html, "rechtschreibung")
    notes = _clean(div)[:1500]
    # drop the leading "Rechtschreibung" heading + info icon
    notes = re.sub(r"^Rechtschreibung\s*ⓘ\s*", "", notes)
    return {"hyphenation": word["hyphenation"], "notes": notes}


def parse_conjugation(html: str) -> dict:
    """{indikativ: {tense_key: {person: form}}, imperative:
    {singular, plural}, infinitiv_mit_zu, partizip_i, partizip_ii}."""
    clean_html = _SUP_RE.sub("", html)
    uls = re.findall(
        r'<ul class="accordion__list content-column">(.*?)</ul>',
        clean_html, re.S)
    tables = []
    for u in uls:
        items = [_clean(li) for li in re.findall(
            r'<li class="accordion__item">(.*?)</li>', u, re.S)]
        items = [it for it in items if it]
        if items:
            tables.append(items)

    indikativ: dict[str, dict[str, str]] = {}
    imperative = {"singular": "", "plural": ""}
    infinitiv_mit_zu = ""
    partizip_i = ""
    partizip_ii = ""
    for items in tables:
        label, forms = items[0], items[1:]
        if label in TENSES and len(forms) == 6:
            key = TENSE_KEYS[TENSES.index(label)]
            if key not in indikativ:
                indikativ[key] = dict(zip(PERSONS, forms))
        elif label == "Infinitiv mit zu" and forms:
            infinitiv_mit_zu = forms[0]
        elif label == "Partizip I" and forms:
            partizip_i = forms[0]
        elif label == "Partizip II" and forms:
            partizip_ii = forms[0]
        elif len(items) == 2 and not imperative["singular"]:
            # the Imperativ list carries no label — its two items are
            # the singular (du) and plural (ihr) forms directly
            imperative = {"singular": items[0], "plural": items[1]}
    if not indikativ and not partizip_ii:
        raise ValueError("no conjugation tables found on this page "
                         "(is it a verb?)")
    return {
        "indikativ": indikativ,
        "imperative": imperative,
        "infinitiv_mit_zu": infinitiv_mit_zu,
        "partizip_i": partizip_i,
        "partizip_ii": partizip_ii,
    }


def parse_search(html: str) -> list[dict]:
    """[{word, url}] — Duden headwords from the search results page."""
    out: list[dict] = []
    seen = set()
    for slug in re.findall(r'href="/rechtschreibung/([^"]+)"', html):
        if slug in seen:
            continue
        seen.add(slug)
        display = slug.replace("_", " ")
        out.append({"word": display,
                    "url": f"{BASE}/rechtschreibung/{slug}"})
    return out
