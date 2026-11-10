"""Live tests — hit the real duden.de word / conjugation / search pages.
Cautious: few requests.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set DUDEN_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from duden_mcp import server as srv

pytestmark = pytest.mark.live
SKIP = os.environ.get("DUDEN_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="DUDEN_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_lookup_live(self):
        out = json.loads(srv.duden_lookup_word("Haus"))
        self.assertNotIn("error", out)
        self.assertEqual(out["lemma"], "Haus, das")
        self.assertGreaterEqual(len(out["meanings"]), 5)
        print(f"\nLIVE lookup Haus: {len(out['meanings'])} meanings — "
              f"{out['meanings'][0][:60]}")

    def test_synonyms_live(self):
        out = json.loads(srv.duden_synonyms("Haus"))
        self.assertNotIn("error", out)
        self.assertIn("Gebäude", out["synonyms"])

    def test_spelling_live(self):
        out = json.loads(srv.duden_spelling("laufen"))
        self.assertNotIn("error", out)
        self.assertEqual(out["hyphenation"], "lau·fen")

    def test_grammar_live(self):
        out = json.loads(srv.duden_grammar("Haus"))
        self.assertNotIn("error", out)
        self.assertIn("Genitiv", out["grammar"])

    def test_conjugate_live(self):
        out = json.loads(srv.duden_conjugate("laufen"))
        self.assertNotIn("error", out)
        self.assertEqual(out["partizip_ii"], "gelaufen")
        self.assertEqual(out["indikativ"]["praesens"]["ich"],
                         "laufe (mich/mir)")

    def test_conjugate_ambiguous_verb_live(self):
        # sein: bare /konjugation/sein is 404; the tool resolves the
        # suffixed Hilfsverb entry through the word page.
        out = json.loads(srv.duden_conjugate("sein"))
        self.assertNotIn("error", out)
        self.assertEqual(out["partizip_ii"], "gewesen")
        self.assertEqual(out["indikativ"]["praesens"]["ich"], "bin")

    def test_lookup_ambiguous_word_live(self):
        # sein: bare word page 301-redirects to sein_Hilfsverb.
        out = json.loads(srv.duden_lookup_word("sein"))
        self.assertNotIn("error", out)
        self.assertEqual(out["lemma"], "sein")

    def test_search_live(self):
        out = json.loads(srv.duden_search("Haus", limit=5))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["total_results"], 1)
        self.assertEqual(out["items"][0]["word"], "Haus")

    def test_missing_word_live(self):
        out = json.loads(srv.duden_lookup_word("Xyzqweabc"))
        self.assertIn("error", out)
        self.assertIn("try duden_search", out["error"])
