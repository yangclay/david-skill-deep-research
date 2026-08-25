# 中文调研专项指南

适用场景：调研中国境内的企业、机构、产品、事件，尤其是消费投诉、口碑调查、中文生态（知乎/公众号/百度系）类任务。

## 搜索策略优先级

### 第一轮：通用搜索（SaC 引擎决策自动完成）

Searlo → Serper（Google SERP 质量层）为主力，DDG 仅兜底（2026-08-24 质量优先定案）。但如果结果中**中文内容 < 30%** 或 **核心问题无直接回答**，进入第二轮。

### 第二轮：中文平台专项补充

按主题类型选择平台组合：

**企业/机构背景调查：**
- 天眼查 / 企查查 — 公司注册信息、股东结构、法律诉讼、行政处罚
- 百度地图 — 实体门店/办公地点是否存在
- 百度搜索 `site:aiqicha.baidu.com` — 企业信息

**消费者口碑/投诉：**
- 黑猫投诉 `site:tousu.sina.com.cn`
- 百度贴吧 — 品牌/产品贴吧，真实用户吐槽
- 知乎 `site:zhihu.com` — 深度分析和体验帖

**社交媒体/短视频：**
- 抖音 `site:douyin.com` — 短视频体验分享（内容抓取困难，但标题+摘要有价值）
- 小红书 `site:xiaohongshu.com` 或 `site:xhslink.com` — 种草/避雷
- B站 `site:bilibili.com` — 深度评测视频

**中文内容深度抓取：**
- SerpAPI 百度引擎 — 中文内容自动触发（SaC 引擎决策）
- 微信公众号 `site:mp.weixin.qq.com` — 深度文章
- 知乎文章 `site:zhuanlan.zhihu.com` — 专栏分析

## 软文/推广文识别

中文互联网的"排行榜""推荐""TOP10"文章**大量是付费软文**。识别特征：

1. **SEO 优化痕迹** — 标题堆砌关键词（实测案例：中文美学检索 top 结果多为百度教育/文库/百科，标题模板化如"优美与崇高的区别"，内容为拼凑抄写）
2. **格式化模板** — 统一的"优势/特色/推荐理由"结构，无真实体验细节
3. **无负面内容** — 全是好评，无缺点或风险提示
4. **联系方式突出** — 文末有电话/微信/咨询入口
5. **发布平台** — 搜狐号、百家号、小众教育网站（而非知乎、豆瓣等UGC平台）

**处理方式：**
- 软文可信度标记为 C（存疑）
- 报告中明确标注"推广文/软文性质"
- 不作为正面口碑的唯一证据
- 寻找独立第三方评价（知乎、贴吧、投诉平台）

## 中文调研实测要点（2026-08-13 优美与崇高）

中文调研与英文调研差异显著，以下是 v3.1 全链路实测（优美与崇高）沉淀的真实经验：

**1. 百度系结果按 source family 聚类（G-001 实测触发）**
- 中文 9 条结果中 cp.baidu / easylearn / wenku / baike 为同家族，独立中文源实际仅 ~3 个
- 处理：追溯引用链，按 source family 计数，不得视为独立证据

**2. 百度教育/文库/百科按 SEO 农场降权（G-012 实测触发）**
- 中文 top 结果多为百度教育/文库/百科，标题模板化（"优美与崇高的区别"），内容拼凑抄写
- 处理：标记 C 级可信度并降权，优先中国社会科学网等学术机构

**3. 中文权威来源优先**
- 学术机构（中国社会科学网等）> 权威媒体 > 百科 > 百度系教育内容
- 中文优质来源（学术论文）覆盖不足是常见缺口 → 可补知网/学术搜索

**4. SerpAPI 百度引擎实测坑**
- 中文/空格必须 URL 编码（`quote(q, safe='')`）
- 结果 snippet 可能含控制字符 → 必须正则清理 `[\x00-\x1f\x7f]` 再 json.loads
- 用 curl 而非 urllib（urllib 到 serpapi.com 易超时），timeout 45s

## 抓取限制

- 抖音视频页面：`web_fetch` 通常无法抓取正文（JS渲染），但搜索结果的标题+摘要已包含关键信息
- 微信公众号文章：部分有反爬，可尝试 `scrape-stealth.py`
- 百度搜索结果：需用 SerpAPI 百度引擎（SaC 引擎决策处理）
- 天眼查/企查查：需登录才能查看详情，但搜索结果摘要通常包含注册状态

## 案例参考

- `~/wiki/raw/research/优美与崇高调研-2026-08-13.md` — 中文语境调研标准模板（触发 G-001 伪独立来源 + G-012 SEO 农场，2026-08-13 v3.1 实测）
- `~/wiki/raw/research/AI营销Agent工具对比-2026-08-13.md` — 工具对比调研模板（WorkBuddy/n8n/Zapier/Coze，2026-08-13 v3.1 实测）


---

# 中文搜索 site: 过滤技巧（补充）

### 中文搜索 site: 过滤技巧

- site:zhihu.com — 知乎
- site:mp.weixin.qq.com — 微信公众号
- site:juejin.cn — 掘金
- site:csdn.net — CSDN
- site:bilibili.com — B站
- site:xiaohongshu.com — 小红书
- site:douyin.com — 抖音
- 企业信息：天眼查/企查查
- 消费维权：site:tousu.sina.com.cn 黑猫投诉

# 深度调研参考材料

从 SKILL.md 中提取的补充内容。核心七步法在 SKILL.md 中。

---

## 自适应搜索策略

SaC 五段式管道已内建引擎决策和覆盖率判断（见 `sac-search-orchestration.md`）。以下规则用于**首轮搜索后仍有缺口时的补充搜索**。

### 补充搜索决策树（首轮完成后评估）

```
首轮结果评估
  ├─ 覆盖率不足 / 核心子问题无可靠证据？ → 换引擎补搜（Tavily advanced / SerpAPI）
  ├─ 中文内容密度 > 40%？ → SerpAPI 百度已自动覆盖
  ├─ 发现 PDF / DOI / arXiv 链接？ → 触发 arxiv-scholar-search
  ├─ 发现 scholar.google.com 链接？ → 触发 google-scholar-search
  ├─ 新闻时间戳 > 6 个月？ → 提示是否需要最新动态
  ├─ 核心结论无来源或存疑？ → 单独抓原文验证（web-fetch.sh）
  ├─ web-fetch 返回 403/空内容？ → scrape-stealth.py 或 TinyFish Fetch
  ├─ 关键数据点多个来源矛盾？ → 溯因推理（abductive-reasoning）
  └─ 需要开源工具对比？ → GitHub API 补充
```

### 补充搜索选择

| 目标 | 补充工具 |
|------|----------|
| 学术论文 | Google Scholar + arXiv |
| 开源工具对比 | GitHub API |
| 社区讨论 | HN Algolia + Reddit JSON |
| 反爬/Cloudflare 页面 | Scrapling 或 TinyFish Fetch |
| 验证码墙/强反爬（微信/知乎/小红书/Turnstile） | cloak-fetch.py（CloakBrowser，hermes-agent venv python3） |
| 多页爬取/全站抓取 | crawl4ai |
| 语义相似内容 | Exa |
| 动态/实时内容 | TinyFish Search |

### 中文生态覆盖

- **知乎全链**：搜索用 Searlo `site:zhihu.com`（先烧）→ Serper 接棒 → SerpAPI 百度兜底；**抓正文用 cloak-fetch.py**（CloakBrowser 绕验证码墙，`PYTHONPATH=$HOME/.local/lib/python3.12/site-packages /usr/bin/python3 scripts/cloak-fetch.py <url>`）——搜索+抓取两段拼成完整知乎通道
- **微信公众号**：Serper `site:mp.weixin.qq.com` 搜索得 URL 后 web-fetch 抓正文；反爬时 wechat-article-reader skill（CloakBrowser）
- **知乎 / 掘金 / B站**：Serper `site:zhihu.com / site:juejin.cn / site:bilibili.com`
- **百度系内容（文库/百科/贴吧/黑猫）**：SerpAPI 百度引擎（专属场景，月 250 次额度留给它）
- **Hacker News**：`curl -s "https://hn.algolia.com/api/v1/search?query=关键词&tags=story&hitsPerPage=5"`
- **Reddit**：`curl -s -H "User-Agent: research-bot" "https://www.reddit.com/search.json?q=关键词&limit=5&sort=relevance"`

---

## Kanban 研究任务模板

通过 kanban 分配研究任务时，必须在 body 中包含技术问题处理要求：

```
### ⚠️ 技术问题处理要求（强制）

遇到技术障碍 → 诊断原因 → 选择替代方案 → 继续搜索 → 记录解决方法。
禁止"搜索不到就算了"。

常见障碍：
- 反爬/Cloudflare → scrape-stealth.py
- 验证码墙/强反爬（微信/Turnstile/中文平台） → cloak-fetch.py（CloakBrowser）
- SPA/JS 渲染 → scrape-stealth.py --mode dynamic
- web_fetch 403 → scrape-stealth.py
- 搜索被限 → 切换引擎
- 结果不足 → 补充搜索
```

---

## Token 消耗控制

- SaC 引擎决策自动处理分层，不需要手动选引擎
- 搜索结果写文件，不全部塞进 context
- 先综合再展示，给用户看去重后的精华

---

## 搜索引擎全景

| 引擎 | 覆盖 | 免费额度 | 用途 |
|------|------|----------|------|
| Tavily research | 内置 | 1000 credits/月（research 20 RPM） | 深度综合调研 |
| Tavily search | 内置 | 1000 credits/月（dev 100 RPM） | AI 原生快速搜索 |
| Searlo | REST | 3000 credits（一次性 90 天，先烧） | Google SERP 主力 |
| Serper | REST | 2500 次（注册一次性赠送，50 QPS） | Google SERP 接棒 + 中文 site: 主力 |
| DuckDuckGo | 内置 | ♾️ | 兜底 |
| Exa | 原生 | $20 注册 + $10/月（≈1400 次/月） | 语义搜索 |
| SerpAPI | REST | 250 searches/月（50/h） | 多引擎 |
| Google Scholar | Skill | ♾️ | 学术 |
| arXiv | Skill | ♾️ | 预印本 |
| Scrapling | 本地 | ♾️ | 反爬 |
| crawl4ai | 本地 | ♾️ | 全站抓取 |
| TinyFish Search | REST | ♾️（30 RPM） | 实时搜索 |
| TinyFish Fetch | REST | ♾️（150 URLs/min） | 浏览器渲染抓取 |

> ⚠️ 数据以 sac-search-orchestration.md 的限流速查表为准（2026-08 官方核实）

---

## 辅助脚本

### Searlo 搜索
```bash
curl -s "https://api.searlo.tech/api/v1/search/web?q=查询词&limit=5&gl=us" \
  -H "x-api-key: $SEARLO_API_KEY" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for r in d.get('organic',[])[:5]:
    print(r.get('title',''))
    print(r.get('link',''))
    print(r.get('snippet','')[:200])
    print()
"
```

### Tavily 增强搜索（内联）
```python
# 见 sac-search-orchestration.md 的 Tavily 内联模板
# search_depth=advanced + include_answer=True
```

### 检查 Tavily 配额
```bash
curl -s -X POST "https://api.tavily.com/usage" -H "Content-Type: application/json" \
  -d '{"api_key":"'"$TAVILY_API_KEY"'"}' | python3 -c "
import sys,json; d=json.load(sys.stdin)
used=d.get('account',{}).get('plan_usage',0)
limit=d.get('account',{}).get('plan_limit',1000)
print(f'Tavily: {used}/{limit} ({used/limit*100:.0f}% used)')
"
```

### Web 页面抓取
```bash
bash scripts/web-fetch.sh <url> [max_chars]
# 或内联 curl（无脚本依赖）
curl -s --max-time 15 -A "Mozilla/5.0" "<url>"
```

---

## Pitfall：搜索关键词不全导致遗漏主流工具

工具/项目类调研，仅靠搜索引擎可能遗漏大项目。

**防御措施**：
1. GitHub API 交叉验证（按 stars 排序搜 topic）
2. 多关键词搜索（同一领域 3+ 种关键词组合）
3. 竞品发现（找到一个工具后搜 "alternatives"）


---

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

## Position in SaC engine decision pipeline

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
export TINYFISH_API_KEY="<从 ~/.hermes/.env 读取>"  # 不要硬编码密钥

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
