# duden-mcp 📖

mcp-name: io.github.mohammad-abbasi-sh/duden-mcp

Unofficial **read-only** MCP server for **[duden.de](https://www.duden.de)** — Duden dictionary lookup from duden.de (free, no key, no login): word meanings, synonyms, spelling with hyphenation, grammar notes and full verb conjugation. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory". Not affiliated with duden.de.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "duden": {
      "command": "uvx",
      "args": ["duden-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m duden_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `duden_lookup_word` | Look up a German word in Duden: meanings, word type, frequency, hyphenation & grammar — `word` (e.g. Haus, laufen) |
| `duden_synonyms` | Synonyms of a German word from Duden — `word` |
| `duden_spelling` | Spelling of a German word: hyphenation and spelling notes — `word` |
| `duden_grammar` | Grammar notes for a German word: declension/conjugation summary — `word` |
| `duden_conjugate` | Full conjugation table of a German verb: present, past, perfect, participles, imperative — `verb` |
| `duden_search` | Search Duden headwords matching a query — `query`, `limit` 1..20 |
| `duden_health` | Reachability probe (ok / blocked / error) — one polite request |

## Notes

- All data comes from **Duden's public word pages** (free, no key, no login).
- Meanings are the numbered definitions from the word entry; synonyms are the ones listed on the entry (the dedicated `/synonyme/<word>` overview page only lists alphabetical navigation, so it is linked, not parsed).
- Word URLs use Duden's transliterated slug (ä→ae, ö→oe, ü→ue, ß→ss); lookup tries the transliterated form first, then the raw spelling.
- Ambiguous headwords redirect: `sein` → `sein_Hilfsverb`, `haben` → `haben_Hilfsverb` / `haben_Vollverb`. The tools follow Duden's own redirects, and `duden_conjugate` resolves the suffixed conjugation page through the word entry when the bare `/konjugation/<verb>` URL 404s.
- Hyphenation marks syllable breaks with `·` (Duden itself writes a soft hyphen or pipe).
- Conjugation tables include the reflexive pronouns Duden lists (e.g. `laufe (mich/mir)` for `laufen`).

Tests: 37/37 green (28 offline + 9 live, 2026-11-10).

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## License

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
