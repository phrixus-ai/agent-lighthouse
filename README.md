<div align="center">

# AgentLighthouse

**Free AI Readiness & Modern Web Compliance Scanner**

[Scan your site live](https://agentlighthouse.burakgider.com) &middot; [API Docs](#api) &middot; MIT License

> Is your website ready for AI agents and modern web standards? Find out in 10 seconds.

</div>

---

## Why Agent Readiness & Modern Web Compliance Matter

AI agents from Google, OpenAI, Anthropic, and Perplexity are actively crawling the web. If your site lacks structured data, semantic HTML, or `llms.txt`, these agents can't understand your content properly.

Meanwhile, **Google's Modern Web Guidance** defines the standards for modern, accessible, and performant websites — native browser APIs over JavaScript libraries, semantic HTML over divs, and user preference respect.

**AgentLighthouse** scans any URL and gives you a **0-100 score** across **40 checks** in 6 categories:

| Category | Weight | What It Checks |
|---|---|---|
| Security | 18pts | SSL, HSTS, CSP, X-Frame-Options, permissions |
| SEO & Metadata | 8pts | Title, description, OG tags, Twitter Card |
| AI & Agent Readiness | 21pts | llms.txt, semantic HTML, AI bot access, headings |
| Structured Data | 14pts | JSON-LD, Schema.org coverage |
| **Modern Web** | **20pts** | Dialog, Popover API, Container Queries, View Transitions, user preference queries, landmarks |
| Performance & Crawling | 19pts | Viewport, charset, canonical, robots.txt, sitemap, compression |

### Score Levels

- **Excellent** — 90+ (your site is fully AI-ready and modern)
- **Good** — 70-89 (minor fixes recommended)
- **Fair** — 50-69 (important gaps found)
- **Poor** — Below 50 (significant work needed)

## Try It Now

**[agentlighthouse.burakgider.com](https://agentlighthouse.burakgider.com)**

No signup, no API key. Paste a URL, get your score.

## API

For CI/CD integration or batch scanning:

```bash
curl -X POST https://agentlighthouse.burakgider.com/api/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

Returns a JSON object with `score`, `level`, `checks[]` array, and per-category breakdown.

### AI-Friendly Endpoints

```
GET /llms.txt        — Machine-readable docs for AI agents
GET /llms-full.txt   — Detailed documentation (Accept: text/markdown)
```

## Modern Web Compliance Checks

Based on [Google Chrome Modern Web Guidance](https://developer.chrome.com/docs/modern-web-guidance):

- **Native Dialog** — `<dialog>` element instead of custom modals
- **Responsive Images** — `<picture>` + srcset for adaptive delivery
- **Container Queries** — `@container` for component-level responsive design
- **Popover API** — Native popover attribute over tooltip libraries
- **View Transitions** — Smooth page transitions API
- **User Preference Queries** — `prefers-reduced-motion` + `prefers-color-scheme`
- **Landmark Elements** — `<main>`, `<nav>`, `<header>`, `<footer>`, `<aside>`, `<article>`
- **Resource Hints** — preload, prefetch, preconnect
- **Time Element** — Machine-readable `<time datetime="...">`
- **Native Disclosure** — `<details>/<summary>` over custom accordions
- **Inline Event Handlers** — CSP-compatible `addEventListener` over inline handlers
- **CSP Meta Tag** — Fallback Content-Security-Policy in `<meta>`

## Built For the Agentic Era

AgentLighthouse is designed for a world where AI agents discover, read, and act on web content:

- Detects `llms.txt` / `llms-full.txt` (the emerging standard for AI-readable docs)
- Validates AI crawler access rules in `robots.txt` (GPTBot, Claude-Web, PerplexityBot)
- Checks semantic HTML structure that agents rely on for comprehension
- Analyzes JSON-LD / Schema.org structured data coverage
- Scans for Google Modern Web Guidance compliance

## Tech Stack

Python 3.11, Flask, BeautifulSoup4, lxml, vanilla JS

## License

MIT &middot; [PHRIXUS](https://github.com/phrixus-ai)

---

<details>
<summary>Self-Host / Developer Setup</summary>

```bash
git clone https://github.com/phrixus-ai/agent-lighthouse.git
cd agent-lighthouse
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env  # optional — for production
python -m webaudit     # → http://localhost:5000
```

| Variable | Default | Description |
|---|---|---|
| `WEBAUDIT_PORT` | `5000` | Flask port |
| `SITE_URL` | (empty) | Production URL for SEO/OG tags |
| `AGENTLIGHTHOUSE_SECRET_KEY` | `dev-key-change-in-production` | Flask secret key |

</details>
