"""Offline tests — parse real captured Duden pages (scripts/styles
stripped), no network."""
import json
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from duden_mcp import domain as dom
from duden_mcp import server as srv

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _read(name):
    return (FIX / name).read_text(encoding="utf-8")


class TestValidation(unittest.TestCase):
    def test_word(self):
        self.assertEqual(dom.validate_word("  Haus "), "Haus")
        for bad in ["", "   "]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                dom.validate_word(bad)

    def test_limit(self):
        self.assertEqual(dom.validate_limit(10), 10)
        for bad in (0, 21):
            with self.assertRaises(ValueError, msg=str(bad)):
                dom.validate_limit(bad)

    def test_slug(self):
        self.assertEqual(dom.word_slug("Mädchen"), "Maedchen")
        self.assertEqual(dom.word_slug("Haus halten"), "Haus_halten")
        self.assertEqual(dom.word_slug("grüßen"), "gruessen")
        self.assertEqual(
            dom.word_url("Mädchen"),
            "https://www.duden.de/rechtschreibung/Maedchen")
        self.assertEqual(
            dom.conjugation_url("laufen"),
            "https://www.duden.de/konjugation/laufen")


class TestWordHaus(unittest.TestCase):
    def setUp(self):
        self.out = dom.parse_word_page(_read("word-haus.html"))

    def test_lemma_and_type(self):
        self.assertEqual(self.out["lemma"], "Haus, das")
        self.assertEqual(self.out["word_type"], "Substantiv, Neutrum")

    def test_frequency(self):
        self.assertIn("1000 häufigsten", self.out["frequency"])

    def test_meanings(self):
        self.assertEqual(len(self.out["meanings"]), 11)
        self.assertEqual(self.out["meanings"][0],
                         "Gebäude, das Menschen zum Wohnen dient")
        self.assertIn("Wohnung, Heim, in dem jemand ständig lebt",
                      self.out["meanings"])

    def test_hyphenation_and_grammar(self):
        self.assertEqual(self.out["hyphenation"], "Haus")
        self.assertEqual(self.out["grammar"],
                         "das Haus; Genitiv: des Hauses, Häuser")

    def test_origin_and_synonyms(self):
        self.assertTrue(self.out["origin"].startswith(
            "mittelhochdeutsch, althochdeutsch hūs"))
        self.assertEqual(self.out["synonyms"],
                         ["Anwesen", "Bau", "Bauwerk", "Gebäude"])

    def test_no_conjugation_for_noun(self):
        self.assertEqual(self.out["conjugation_url"], "")


class TestWordLaufen(unittest.TestCase):
    def setUp(self):
        self.out = dom.parse_word_page(_read("word-laufen.html"))

    def test_lemma_and_type(self):
        self.assertEqual(self.out["lemma"], "laufen")
        self.assertEqual(self.out["word_type"], "starkes Verb")

    def test_meanings(self):
        self.assertEqual(len(self.out["meanings"]), 29)
        self.assertTrue(self.out["meanings"][0].startswith(
            "sich in aufrechter Haltung"))

    def test_hyphenation(self):
        self.assertEqual(self.out["hyphenation"], "lau·fen")

    def test_conjugation_url(self):
        self.assertEqual(self.out["conjugation_url"],
                         "https://www.duden.de/konjugation/laufen")

    def test_synonyms(self):
        self.assertEqual(self.out["synonyms"],
                         ["eilen", "fegen", "hetzen", "jagen"])


class TestSpelling(unittest.TestCase):
    def test_haus(self):
        out = dom.parse_spelling(_read("word-haus.html"))
        self.assertEqual(out["hyphenation"], "Haus")
        self.assertIn("Haus halten oder haushalten", out["notes"])
        self.assertNotIn("id=", out["notes"])


class TestConjugation(unittest.TestCase):
    def setUp(self):
        self.out = dom.parse_conjugation(_read("conjugation-laufen.html"))

    def test_praesens(self):
        self.assertEqual(self.out["indikativ"]["praesens"], {
            "ich": "laufe (mich/mir)", "du": "läufst (dich/dir)",
            "er/sie/es": "läuft (sich)", "wir": "laufen (uns)",
            "ihr": "lauft (euch)", "sie": "laufen (sich)"})

    def test_praeteritum(self):
        self.assertEqual(self.out["indikativ"]["praeteritum"]["ich"],
                         "lief (mich/mir)")

    def test_perfekt(self):
        self.assertEqual(self.out["indikativ"]["perfekt"]["ich"],
                         "bin gelaufen / habe (mich/mir) gelaufen")

    def test_participles_and_infinitiv(self):
        self.assertEqual(self.out["partizip_i"], "laufend")
        self.assertEqual(self.out["partizip_ii"], "gelaufen")
        self.assertEqual(self.out["infinitiv_mit_zu"], "zu laufen")

    def test_imperative(self):
        self.assertEqual(self.out["imperative"], {
            "singular": "lauf (dich/dir), laufe (dich/dir)!",
            "plural": "lauft (euch)!"})

    def test_no_footnote_markers(self):
        text = json.dumps(self.out, ensure_ascii=False)
        self.assertNotIn(")1", text)
        self.assertNotIn("1, 2", text)


class TestConjugationSein(unittest.TestCase):
    """Irregular/ambiguous verb: the real sein_Hilfsverb page."""

    def test_sein(self):
        out = dom.parse_conjugation(_read("conjugation-sein.html"))
        self.assertEqual(out["indikativ"]["praesens"], {
            "ich": "bin", "du": "bist", "er/sie/es": "ist",
            "wir": "sind", "ihr": "seid", "sie": "sind"})
        self.assertEqual(out["indikativ"]["praeteritum"]["ich"], "war")
        self.assertEqual(out["partizip_ii"], "gewesen")
        self.assertEqual(out["infinitiv_mit_zu"], "zu sein")

    def test_sein_word_page_links_conjugation(self):
        out = dom.parse_word_page(_read("word-sein.html"))
        self.assertEqual(out["lemma"], "sein")
        self.assertEqual(out["conjugation_url"],
                         "https://www.duden.de/konjugation/sein_Hilfsverb")


class TestSearch(unittest.TestCase):
    def test_haus(self):
        hits = dom.parse_search(_read("search-haus.html"))
        self.assertEqual(len(hits), 12)
        self.assertEqual(hits[0], {
            "word": "Haus",
            "url": "https://www.duden.de/rechtschreibung/Haus"})
        self.assertEqual(hits[1]["word"], "Haus halten")


class TestServerWiring(unittest.TestCase):
    """Tools return the envelope + payload with a mocked fetch."""

    def test_lookup_uses_fixture(self):
        html = _read("word-haus.html")
        with mock.patch("duden_mcp.server._http.fetch_text",
                        return_value=html):
            out = json.loads(srv.duden_lookup_word("Haus"))
        self.assertEqual(out["source"], "duden.de")
        self.assertEqual(out["lemma"], "Haus, das")
        self.assertEqual(len(out["meanings"]), 11)

    def test_lookup_404_fallback_then_error(self):
        def fake_fetch(url):
            raise srv._http.DudenMcpError(
                f"duden.de returned HTTP 404 for {url}")
        with mock.patch("duden_mcp.server._http.fetch_text",
                        side_effect=fake_fetch):
            out = json.loads(srv.duden_lookup_word("Xyzqwe"))
        self.assertIn("error", out)
        self.assertIn("try duden_search", out["error"])

    def test_conjugate_uses_fixture(self):
        html = _read("conjugation-laufen.html")
        with mock.patch("duden_mcp.server._http.fetch_text",
                        return_value=html):
            out = json.loads(srv.duden_conjugate("laufen"))
        self.assertEqual(out["partizip_ii"], "gelaufen")
        self.assertEqual(out["indikativ"]["praesens"]["du"],
                         "läufst (dich/dir)")

    def test_conjugate_falls_back_via_word_page(self):
        """sein: direct /konjugation/sein 404s; the tool resolves the
        suffixed entry through the word page."""
        word_html = _read("word-sein.html")
        conj_html = _read("conjugation-sein.html")

        def fake_fetch(url):
            if url.endswith("/konjugation/sein"):
                raise srv._http.DudenMcpError(
                    "duden.de returned HTTP 404 for " + url)
            if "rechtschreibung/sein" in url:
                return word_html
            if url.endswith("/konjugation/sein_Hilfsverb"):
                return conj_html
            raise AssertionError("unexpected url: " + url)

        with mock.patch("duden_mcp.server._http.fetch_text",
                        side_effect=fake_fetch):
            out = json.loads(srv.duden_conjugate("sein"))
        self.assertNotIn("error", out)
        self.assertEqual(out["partizip_ii"], "gewesen")
        self.assertEqual(out["url"],
                         "https://www.duden.de/konjugation/sein_Hilfsverb")


if __name__ == "__main__":
    unittest.main()
