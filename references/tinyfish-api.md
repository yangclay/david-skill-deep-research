# TinyFish API — Free Search & Fetch for Research

> Researched 2026-05-19. Source: tinyfish.ai, docs.tinyfish.ai, GitHub (tinyfish-io).

## What

Enterprise AI web agent infrastructure. 4 APIs, but only **Search** and **Fetch** are relevant for deep research (both free, 0 credits).

## Search API

- **Endpoint:** `GET https://api.search.tinyfish.ai`
- **Auth:** `X-API-Key` header (`TINYFISH_API_KEY` env var)
- **Cost:** 0 credits/req (free on all plans)
- **Rate limit:** 30 req/min (PAYG), 60/min (Starter), 120/min (Pro)
- **Output:** Structured JSON — `{results: [{position, site_name, title, snippet, url}]}`
- **Differentiator:** Real browser-rendered search. Not cached. Handles dynamic/live pages (pricing, earnings, breaking news). Different from traditional SERP scrapers.

```bash
curl "https://api.search.tinyfish.ai?query=web+automation+tools" \
  -H "X-API-Key: $TINYFISH_API_KEY"
```

```python
from tinyfish import TinyFish
client = TinyFish()
response = client.search.query(query="web automation tools")
for r in response.results:
    print(r.title, "→", r.url)
```

## Fetch API

- **Endpoint:** `POST https://api.fetch.tinyfish.ai`
- **Auth:** `X-API-Key` header
- **Cost:** 0 credits/url (free on all plans)
- **Rate limit:** 150 url/min (PAYG), 300/min (Starter), 600/min (Pro)
- **Input:** `{"urls": ["https://..."]}` — up to 10 URLs per request
- **Output:** Clean text/markdown/JSON/HTML. Renders JS-heavy pages.
- **Differentiator:** Hosted real-browser page rendering. No local browser needed. Simpler than scrape-stealth.py.

```bash
curl -X POST https://api.fetch.tinyfish.ai \
  -H "X-API-Key: $TINYFISH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com"]}'
```

```python
from tinyfish import TinyFish
client = TinyFish()
result = client.fetch.get_contents(urls=["https://example.com"])
print(result.results[0].text)
```

## Position in smart-search pipeline

| Layer | Engine | Cost | TinyFish comparison |
|---|---|---|---|
| 1 | DuckDuckGo | Free | TF Search: browser-rendered, dynamic pages |
| 2 | **TinyFish Search** | Free | New layer — live/dynamic content |
| 3 | Searlo | $0.30/1k | TF Search: 30/min vs Searlo unlimited |
| 4 | SerpAPI | $0.01/req | TF Search: no multi-engine (Google/Baidu/etc) |
| 5 | Tavily | $0.01/req | TF Search: no auto-summarization |

**TinyFish Search unique value:** Browser-rendered results from pages that change too fast for cached SERPs (live pricing, earnings, real-time data). Other engines return cached/indexed results.

**TinyFish Fetch unique value:** Hosted browser rendering — replaces local scrape-stealth.py for cases where web_fetch returns 403 or JS-heavy pages. Zero infrastructure to maintain.

## What TinyFish does NOT replace

- **Searlo/SerpAPI** — multi-engine support (Google, Baidu, Bing, YouTube, etc.)
- **Tavily research** — auto multi-round search + content extraction + synthesis
- **crawl4ai** — multi-page/site-wide crawling
- **Scrapling** — advanced anti-bot with stealth mode

## Agent & Browser APIs (not for research)

- **Agent API:** 1 credit/step. Natural-language web automation (fill forms, navigate, extract). Not needed for search/scrape tasks.
- **Browser API:** 1 credit/4 min. Remote stealth browser sessions. Overkill when Fetch API covers page rendering.

## Setup

```bash
# Get API key: https://agent.tinyfish.ai/api-keys
export TINYFISH_API_KEY="***"

# Python SDK
pip install tinyfish

# CLI
npm install -g @tiny-fish/cli

# Hermes skill exists: tinyfish-io/skills (42 ⭐)
```

## Community

- GitHub: tinyfish-io/tinyfish-cookbook (1972 ⭐, MIT, TypeScript)
- Skills: tinyfish-io/skills (Hermes/Clawdbot integration)
- Docs: docs.tinyfish.ai (has llms.txt for coding agents)
