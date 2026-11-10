# duden-mcp 📖

mcp-name: io.github.mohammad-abbasi-sh/duden-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **[duden.de](https://www.duden.de)** — جست‌وجو در فرهنگ لغت دودن از duden.de (رایگان، بدون کلید): معانی واژه، مترادف‌ها، املا با جداسازی هجاها، نکات دستوری و صرف کامل فعل. بدون کلید، بدون ورود.

> ساختهٔ محمد عباسی، بخشی از «کارخانهٔ MCP آلمان». وابسته به duden.de نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی MCP کلاینت اضافه کنید (stdio):

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

یا به‌صورت محلی اجرا کنید: `python -m duden_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `duden_lookup_word` | جست‌وجوی واژهٔ آلمانی در دودن: معانی، نوع کلمه و دستور زبان |
| `duden_synonyms` | مترادف‌های یک واژهٔ آلمانی |
| `duden_spelling` | املا و جداسازی هجاهای یک واژهٔ آلمانی |
| `duden_grammar` | نکات دستوری یک واژهٔ آلمانی |
| `duden_conjugate` | جدول کامل صرف یک فعل آلمانی |
| `duden_search` | جست‌وجوی سرخط‌های دودن |
| `duden_health` | بررسی دسترس‌پذیری (ok / blocked / error) — یک درخواست مؤدبانه |

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## لایسنس

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
