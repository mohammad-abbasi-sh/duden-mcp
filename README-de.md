# duden-mcp 📖

mcp-name: io.github.mohammad-abbasi-sh/duden-mcp

Inoffizieller **nur lesender** MCP-Server für **[duden.de](https://www.duden.de)** — Duden-Nachschlagen auf duden.de (kostenlos, kein Schlüssel, kein Login): Bedeutungen, Synonyme, Rechtschreibung mit Worttrennung, Grammatik und vollständige Verbkonjugation. Kein Schlüssel, keine Anmeldung.

> Gebaut von Mohammad Abbasi als Teil der "Germany MCP factory". Nicht mit duden.de verbunden.

## Für KI-Agenten

Zur MCP-Client-Konfiguration hinzufügen (stdio):

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

Oder lokal starten: `python -m duden_mcp.server` (benötigt `mcp<2`, `httpx`).

## Tools

| Tool | Beschreibung |
|------|-------------|
| `duden_lookup_word` | Ein deutsches Wort im Duden nachschlagen: Bedeutungen, Wortart & Grammatik |
| `duden_synonyms` | Synonyme eines deutschen Wortes |
| `duden_spelling` | Rechtschreibung & Worttrennung eines deutschen Wortes |
| `duden_grammar` | Grammatiknotizen zu einem deutschen Wort |
| `duden_conjugate` | Vollständige Konjugationstabelle eines deutschen Verbs |
| `duden_search` | Duden-Stichwörter suchen |
| `duden_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## Lizenz

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
