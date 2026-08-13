# 中文调研专项指南

适用场景：调研中国境内的企业、机构、产品、事件，尤其是消费投诉、骗局识别、口碑调查类任务。

## 搜索策略优先级

### 第一轮：通用搜索（SaC 引擎决策自动完成）

DuckDuckGo + Searlo 覆盖率通常够用。但如果结果中**中文内容 < 30%** 或 **核心问题无直接回答**，进入第二轮。

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

1. **SEO 优化痕迹** — 标题堆砌关键词（"云南昆明十大专门青少年叛逆厌学教育学校排行榜出炉"）
2. **格式化模板** — 统一的"优势/特色/推荐理由"结构，无真实体验细节
3. **无负面内容** — 全是好评，无缺点或风险提示
4. **联系方式突出** — 文末有电话/微信/咨询入口
5. **发布平台** — 搜狐号、百家号、小众教育网站（而非知乎、豆瓣等UGC平台）

**处理方式：**
- 软文可信度标记为 C（存疑）
- 报告中明确标注"推广文/软文性质"
- 不作为正面口碑的唯一证据
- 寻找独立第三方评价（知乎、贴吧、投诉平台）

## 骗局/传销识别模式

调研企业/机构是否涉骗时，搜索关键词组合：

```
"机构名" 骗局
"机构名" 投诉
"机构名" 维权
"机构名" 传销
"机构名" 洗脑
"行业名" 骗局 案例
```

**公安部门总结的"精神传销"三步法（适用于心灵培训/灵修类）：**
1. 倾诉痛苦经历 → 增加情绪沉浸
2. 不断喊口号 → 入心入脑
3. 制造"人托" → 反馈"神奇效果"

**红旗信号：**
- 无正规资质（营业执照、办学许可）
- 仅靠社交媒体/口碑传播，无官方渠道
- 宣传话术模糊（"心灵成长""突破自我""知行合一"）
- 收费不透明或金额巨大
- 要求"拉人头"或发展下线
- 神化创始人/导师

## 抓取限制

- 抖音视频页面：`web_fetch` 通常无法抓取正文（JS渲染），但搜索结果的标题+摘要已包含关键信息
- 微信公众号文章：部分有反爬，可尝试 `scrape-stealth.py`
- 百度搜索结果：需用 SerpAPI 百度引擎（SaC 引擎决策处理）
- 天眼查/企查查：需登录才能查看详情，但搜索结果摘要通常包含注册状态

## 案例参考

- `raw/research/昆明心聊基地调研-2026-05-14_1_1.md` — 企业背景+口碑+骗局识别的标准模板


---

# 中文内容专项（摘自 workflow.md v2）

---\n
### 中文搜索 site: 过滤技巧\n- site:zhihu.com — 知乎\n- site:mp.weixin.qq.com — 微信公众号\n- site:juejin.cn — 掘金\n- site:csdn.net — CSDN\n- site:bilibili.com — B站\n- site:xiaohongshu.com — 小红书\n- site:douyin.com — 抖音\n- 企业信息：天眼查/企查查\n- 消费维权：site:tousu.sina.com.cn 黑猫投诉\n
---\n
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
| 多页爬取/全站抓取 | crawl4ai |
| 语义相似内容 | Exa |
| 动态/实时内容 | TinyFish Search |

### 中文生态覆盖

- **微信公众号**：搜索得到 URL 后 web-fetch 抓正文
- **知乎 / 掘金**：SerpAPI Google `site:zhihu.com` / `site:juejin.cn`
- **B站**：`site:bilibili.com` 搜索视频和简介
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
- SPA/JS 渲染 → scrape-stealth.py --mode dynamic
- web_fetch 403 → scrape-stealth.py
- 搜索被限 → 切换引擎
- 结果不足 → 补充搜索
```

---

## Token 消耗控制

- SaC 引擎决策自动处理分层，不需要手动选引擎
- 搜索结果写文件，不全部塞进 context
- 先综合再展示，给 Clay 看去重后的精华

---

## 搜索引擎全景

| 引擎 | 覆盖 | 免费额度 | 用途 |
|------|------|----------|------|
| Tavily research | 内置 | ~1000/月 | 深度综合调研 |
| Tavily search | 内置 | ~1000/月 | AI 原生快速搜索 |
| Searlo | REST | $0.30/千次 | Google SERP |
| DuckDuckGo | 内置 | ♾️ | 兜底 |
| Exa | 原生 | 1000/月 | 语义搜索 |
| SerpAPI | REST | 100次/月 | 多引擎 |
| Google Scholar | Skill | ♾️ | 学术 |
| arXiv | Skill | ♾️ | 预印本 |
| Scrapling | 本地 | ♾️ | 反爬 |
| crawl4ai | 本地 | ♾️ | 全站抓取 |
| TinyFish Search | REST | ♾️ | 实时搜索 |
| TinyFish Fetch | REST | ♾️ | 浏览器渲染抓取 |

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
bash /home/clay/.hermes/skills/deep-research/scripts/web-fetch.sh <url> [max_chars]
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

# TinyFish API（微信文章抓取）

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
