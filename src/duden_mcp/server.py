"""MCP server: unofficial read-only access to the Duden dictionary
(duden.de). No key, no login. NOTE: Duden word pages are
server-rendered HTML — meanings come from enumeration__text divs,
synonyms from lexeme links in the #synonyme division, grammar from
the #grammatik paragraph, conjugation from /konjugation/<verb>
accordion lists; the dedicated /synonyme/<word> overview page only
lists alphabetical navigation, so the word page's synonym list is
used. Word URLs use Duden's transliterated slug (ä→ae, ö→oe, ü→ue,
ß→ss); lookup tries the transliterated slug first, then the raw
word, and suggests duden_search on a 404."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for the Duden dictionary via its \
public word pages (no key, no login): look up a German word \
(meanings, word type, frequency, hyphenation, grammar), get its \
synonyms, check its spelling, read grammar notes, conjugate a verb \
in full, or search Duden headwords. NOTE: word URLs use Duden's \
transliterated slug (ä→ae, ö→oe, ü→ue, ß→ss); the lookup tool tries \
the transliterated form first and the raw spelling second. Built by \
Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · \
https://mabbasi.ir — Germany MCP factory.\
"""

_SOURCE = "duden.de"
_DISCLAIMER = "Unofficial read-only data from duden.de; verify on the site before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


mcp = FastMCP("duden-mcp", instructions=INSTRUCTIONS)


def _fetch_word_page(word: str) -> tuple[str, str]:
    """Fetch a Duden word page; try the transliterated slug, then the
    raw word. Returns (html, url). Raises on a genuine miss."""
    slug_url = _dom.word_url(word)
    try:
        return _http.fetch_text(slug_url), slug_url
    except _http.DudenMcpError as e:
        if "HTTP 404" not in str(e):
            raise
    raw_url = f"{_dom.BASE}/rechtschreibung/{quote(word)}"
    if raw_url == slug_url:
        raise _http.DudenMcpError(
            f"duden.de returned HTTP 404 for {slug_url} "
            f"(word not found: {word!r} — try duden_search)")
    try:
        return _http.fetch_text(raw_url), raw_url
    except _http.DudenMcpError as e2:
        if "HTTP 404" in str(e2):
            raise _http.DudenMcpError(
                f"duden.de returned HTTP 404 for {slug_url} "
                f"(word not found: {word!r} — try duden_search)") from e2
        raise


@mcp.tool()
def duden_lookup_word(word: str) -> str:
    """Look up a German word in Duden: meanings, word type,
    frequency, hyphenation, grammar summary and origin.
    word: e.g. Haus, laufen, Mädchen."""
    try:
        w = _dom.validate_word(word)
        html, url = _fetch_word_page(w)
        out = _dom.parse_word_page(html)
        if not out["lemma"] and not out["meanings"]:
            raise ValueError(f"no dictionary entry found for {w!r} "
                             "(the page has no lemma or meanings)")
    except (_http.DudenMcpError, ValueError) as e:
        return _err(e)
    return _ok({"word": w, "url": url, **out})


@mcp.tool()
def duden_synonyms(word: str) -> str:
    """Synonyms of a German word from Duden (the synonyms listed on
    its word entry). word: e.g. Haus."""
    try:
        w = _dom.validate_word(word)
        html, url = _fetch_word_page(w)
        out = _dom.parse_word_page(html)
    except (_http.DudenMcpError, ValueError) as e:
        return _err(e)
    return _ok({"word": w, "url": url,
                "synonyms": out["synonyms"],
                "count": len(out["synonyms"]),
                "overview_url": f"{_dom.BASE}/synonyme/{_dom.word_slug(w)}",
                "note": "Synonyms as listed on the word entry; the "
                        "full overview page is linked above."})


@mcp.tool()
def duden_spelling(word: str) -> str:
    """Spelling of a German word: hyphenation (syllable breaks shown
    as ·) and spelling notes from Duden. word: e.g. laufen."""
    try:
        w = _dom.validate_word(word)
        html, url = _fetch_word_page(w)
        out = _dom.parse_spelling(html)
    except (_http.DudenMcpError, ValueError) as e:
        return _err(e)
    return _ok({"word": w, "url": url, **out})


@mcp.tool()
def duden_grammar(word: str) -> str:
    """Grammar notes for a German word: declension/conjugation
    summary from Duden (for verbs, a link to the full conjugation
    table). word: e.g. Haus, laufen."""
    try:
        w = _dom.validate_word(word)
        html, url = _fetch_word_page(w)
        out = _dom.parse_word_page(html)
    except (_http.DudenMcpError, ValueError) as e:
        return _err(e)
    return _ok({"word": w, "url": url,
                "word_type": out["word_type"],
                "grammar": out["grammar"],
                "conjugation_url": out["conjugation_url"]})


@mcp.tool()
def duden_conjugate(verb: str) -> str:
    """Full conjugation table of a German verb from Duden: Indikativ
    (Präsens, Präteritum, Perfekt, Plusquamperfekt, Futur I/II),
    Imperativ, Infinitiv mit zu, Partizip I/II.
    verb: e.g. laufen, sein, haben."""
    try:
        v = _dom.validate_word(verb)
        url = _dom.conjugation_url(v)
        try:
            html = _http.fetch_text(url)
        except _http.DudenMcpError as e:
            if "HTTP 404" not in str(e):
                raise
            # Ambiguous verbs (sein/haben/werden) have suffixed
            # entries (sein_Hilfsverb, haben_Vollverb …): resolve the
            # conjugation link through the word page, which follows
            # Duden's own redirect to the canonical entry.
            whtml, _wurl = _fetch_word_page(v)
            conj = _dom.parse_word_page(whtml)["conjugation_url"]
            if not conj:
                raise _http.DudenMcpError(
                    f"duden.de returned HTTP 404 for {url} "
                    f"(no conjugation table for {v!r} — is it a verb?)"
                ) from e
            url = conj
            html = _http.fetch_text(url)
        out = _dom.parse_conjugation(html)
    except (_http.DudenMcpError, ValueError) as e:
        return _err(e)
    return _ok({"verb": v, "url": url, **out})


@mcp.tool()
def duden_search(query: str, limit: int = 10) -> str:
    """Search Duden headwords matching a query (useful when the exact
    spelling is unknown). query: e.g. Haus. limit: 1..20 (default 10)."""
    try:
        lim = _dom.validate_limit(limit)
        q = (query or "").strip()
        if not q:
            raise ValueError("query must not be empty")
        hits = _dom.parse_search(_http.fetch_text(_dom.search_url(q)))
    except (_http.DudenMcpError, ValueError) as e:
        return _err(e)
    return _ok({"query": q, "total_results": len(hits),
                "count": min(lim, len(hits)), "items": hits[:lim]})


@mcp.tool()
def duden_health() -> str:
    """Check whether duden.de is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
