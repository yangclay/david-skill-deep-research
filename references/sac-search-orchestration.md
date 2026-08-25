# SaC 搜索编排（Search as Code Orchestration）

> 基于 Perplexity SaC 架构 + ODS 开源方法，2026-08-13 实测验证
> **核心思想：搜索是可编程的。用 execute_code 写一段 Python 编排完整搜索 pipeline（fanout → search → extract → rerank → dedupe），只把压缩后的 top-N 结果带回上下文。**

## 调用原则（内联优先，需要逻辑才用脚本）

| 类型 | 处理方式 | 例子 |
|------|---------|------|
| **纯 API 调用**（一次请求拿结果） | **直接内联 execute_code**，不写脚本 | Tavily/SerpAPI 单次查询、curl 抓单页 |
| **有状态逻辑**（覆盖率判断/多引擎组合） | **内联 execute_code**（四段式管道见下） | 按子问题特性选引擎 |
| **Python 库封装**（Scrapling/crawl4ai） | 用 py 脚本（库本身是 Python，无法内联为 API） | 反爬、全站抓取 |
| **复合逻辑**（相关性打分） | 内联 + Jina rerank | 统一重排 |

**判断标准**：这个调用有没有"多步逻辑、库依赖"？
- 没有 → 内联 execute_code（一次 urllib/curl 搞定，不产生脚本文件）
- 有 → 用 scripts/ 里的对应脚本

## API 限流速查表（2026-08 官方核实）

**所有 API 目前都是免费的，真正约束是速率限制（RPM）和 Hermes 的 20 RPM 总限流。**

| API | 免费额度 | **速率限制** | 安全间隔 | 用途 |
|-----|---------|------------|---------|------|
| **Tavily** | 1000 credits/月（basic=1，advanced=2） | **dev: 100 RPM**；research: 20 RPM | ≥1s | 核心子问题深度搜索（**只用 advanced+include_answer**；2026-08-24 对拍：basic 模式与 DDG top-5 完全同源，烧 credits 纯浪费） |
| **SerpAPI** | 250 searches/月 | **free: 50/小时** | 串行 | 中文生态/多引擎 |
| **Exa** | $20 注册 + $10/月（≈1400 次/月） | **/search: 10 QPS**（600 RPM） | 不用管 | 语义相似/论文 |
| **Searlo** | 3000 credits（一次性，90 天有效） | Pro: 300 req/min | 不用管 | Google SERP 主力（易腐品先烧；实测支持中文/site:/gl/hl，与 Serper 同源） |
| **Serper** | 2500 次（注册一次性赠送，不过期） | **50 QPS**，1-2s 响应 | 不用管 | Google SERP 接棒（Searlo 耗尽/到期后转正；num=20 单次翻倍 + tbs 时间窗） |
| **TinyFish** | Search/Fetch 永久免费 | **Search: 30 RPM**，Fetch: 150 URLs/min | ≥2s | 免费质量层（2026-08-24 对拍：英文 top5 与 Serper 完全一致、中文 4/5 重叠，实为 Google 同源质量；30 RPM 慢、无 num/tbs 进阶参数；实时内容最优：reuters/techcrunch > DDG reddit/youtube） |
| **Jina Rerank** | 1000 万 token（非商用） | **100 RPM，100K TPM，2 并发** | ≥0.6s + ≤2 并发 | 相关性重排 |
| **web_search**（内置 DDG） | 无限免费 | 无公布限流 | 不用管 | 兜底（质量不足，2026-08-24 降级） |

**调度铁律：**
1. **Hermes execute_code 总限流 20 RPM（Agnes）**——所有 API 调用 + 工具调用共享，`time.sleep(3)` 不可省
2. **同一 API 绝不并发**（Tavily/SerpAPI 单线程串行）
3. **Jina rerank 一次调研只调 1-2 次**——全部结果合并后一次性重排，不是每个查询重排
4. **质量优先**（2026-08-24 全引擎对拍定案）：默认第一层 = Searlo（易腐先烧）→ 耗尽后 TinyFish（免费 Google 质量，日常）+ Serper（进阶参数场景：num=20/tbs/批量 fanout 高并发）；DDG 兜底；TinyFish 兼任实时内容首选
5. **Tavily 只用 advanced**（2026-08-24 对拍：basic 模式与 DDG top-5 完全同源，烧 credits 纯浪费；价值只在 advanced+include_answer 的 AI 答案）

## 五段式管道（引擎选择是"决策"不是"顺序"）

```
Step 2a: 引擎选择（按子问题特性决策）
  ├─ 核心子问题（高信息增益，要 AI 答案）→ Tavily advanced
  ├─ 一般子问题（默认）              → Searlo 先烧（易腐）→ 耗尽后 TinyFish 日常 / Serper 进阶（真 Google SERP）；DDG 仅兜底
  ├─ Google SERP（要真 Google 排名/英文深度覆盖）→ Searlo（credits 到期前先烧）→ Serper（2500 接棒；num=20 单次翻倍 + tbs 时间窗）
  ├─ 应用/趋势/当代艺术/体验类          → Tavily（实测 2026-08-13：web_search top-10 假命中）
  ├─ 中文生态（知乎/公众号/小红书/B站） → Searlo site: 先烧（2026-08-24 实测：中文+site:+gl/hl 全透传，与 Serper 结果同源）→ Serper site: 接棒；百度系内容才 SerpAPI 百度
  ├─ 语义相似（找相关/论文）           → Exa
  ├─ 学术专项                         → Scholar / arXiv
  └─ 覆盖率检查：不足 → 升级到下一成本层

Step 2b: 统一 rerank（所有引擎结果汇合）
  → Jina 打分 → 过滤 <0.3 → 按分数排序

Step 2b.5: 规则 filter（补 Jina 向量相似度的语义盲区）
  ├─ snippet 过短（<20 字符）→ 剔除（导航页）
  ├─ SEO 农场模式（TOP10/排行榜/必看/十大/汉语言文学学习类账号文）→ 降为 C 级
  ├─ 文库/聚合类（wenku.baidu/news.qq/百家号）→ 降为 C 级（非一手，2026-08-13 实测漏网）
  ├─ 子问题关键词缺失 → 降权
  └─ 登录页/404（login/signin/404）→ 剔除
  → 不用 LLM 做相关性 filter（写报告的 LLM 已天然判断，独立 LLM 层是税）

Step 2c: 内容形态工具（按需）
  ├─ 验证原文   → web-fetch.sh / 内联 curl
  ├─ 反爬页面   → scrape-stealth.py
  └─ 全站抓取   → crawl_site.py

Step 2d: dedupe + top-N 压缩输出

Step 2e: parse_field 结构化字段提取（对 top-3 抓原文 → 抽结构化字段）
```

**关键区别（vs 早期 smart-search）：** smart-search 是固定顺序逐层升级（不管子问题特性），五段式让模型根据子问题特性选引擎组合——核心问题用 Tavily，一般问题走 Google SERP 质量层（Searlo→Serper），中文用 Serper site:。**按需组合，不是全量堆叠。**

## 工具选择矩阵（按功能和使用场景调用，不是"源不足才用"）

| 场景 | 首选 | 说明 |
|------|------|------|
| **SaC 批量 fanout + rerank**（深度调研核心） | `execute_code` + Searlo/Serper + Jina | 一次编排多查询，Jina 重排，只回 top-N |
| **核心子问题深度搜索**（要 AI 答案） | 内联 Tavily API（`search_depth=advanced` + `include_answer`） | 见下方"Tavily 内联模板" |
| **一般子问题搜索**（默认） | Searlo → Serper（内联 REST） | 质量优先；credits 耗尽降 web_search(DDG) 兜底 |
| **应用/趋势/当代艺术/体验类** | 内联 Tavily API | 实测 web_search 命中率低（2026-08-13 优美与崇高） |
| **快速抓单页** | `web-fetch.sh` 或内联 curl | 干净解析，无 JS 渲染需求 |
| **反爬/Cloudflare 页面** | `scrape-stealth.py --mode http/stealth` | http/stealth/dynamic 三模式全通 |
| **全站/多页抓取** | `crawl_site.py`（crawl4ai） | single/multi/sitemap 三模式 |
| **中文生态**（知乎/公众号/天眼查） | 内联 SerpAPI 百度 + site: 过滤 | tool-reference.md 站点表 |
| **语义相似/论文检索** | Exa（原生工具） | 语义搜索 |
| **学术论文** | google-scholar-search / arxiv-scholar-search | 学术专项 |
| **GitHub 开源项目对比** | GitHub API | 按 stars 排序 |

**核心原则**：能内联就内联（一次 urllib/curl 调用），只有库依赖（Scrapling/crawl4ai）才用脚本。

## 完整编排模板（五段式）

```python
# === SaC 编排：引擎决策 → fanout → search → rerank → dedupe ===
from hermes_tools import web_search, terminal
import json, time, urllib.request

def get_key(name):
    for p in ["/home/clay/.hermes/profiles/david/.env", "/home/clay/.hermes/.env"]:
        try:
            for line in open(p):
                if line.strip().startswith(f"{name}="):
                    return line.strip().split("=", 1)[1]
        except Exception:
            pass
    return None

MAIN_QUERY = "<主问题描述>"

# === Step 2a: 引擎选择（按子问题特性决策）===
# 每个子问题标注引擎：核心→tavily，一般→web_search，中文→serpapi，语义→exa
queries = [
    ("子问题1", "tavily",   ["query 1a", "query 1b 变体"]),   # 核心：Tavily 要 AI 答案
    ("子问题2", "searlo", ["english query 2a"]),                # 一般：Searlo 先烧（质量优先默认层）
    ("子问题3", "serper", ["site:zhihu.com 中文查询", "查询 site:mp.weixin.qq.com"]),  # 中文/Google SERP：Serper
]

raw = []
for sub, engine, qs in queries:
    for q in qs:
        time.sleep(3)  # 铁律：Agnes 20 RPM，不可省
        try:
            if engine == "serper":  # Google SERP + 中文 site: 主力（2500 次，50 QPS）
                payload = json.dumps({"q": q, "gl": "cn", "hl": "zh-cn", "num": 20}).encode()
                req = urllib.request.Request("https://google.serper.dev/search", data=payload,
                    headers={"X-API-KEY": get_key("SERPER_API_KEY"),
                             "Content-Type": "application/json"}, method="POST")
                d = json.loads(urllib.request.urlopen(req, timeout=15).read())
                items = [{"title": x.get("title",""), "url": x.get("link",""),
                          "description": x.get("snippet","")} for x in d.get("organic",[])]
            elif engine == "searlo":  # Google SERP 默认第一层（3000 credits 90 天到期，先烧）
                # 坑（2026-08-24 实测）：Searlo 拦 urllib 默认 UA（HTTP 403）——必须走 curl
                from urllib.parse import quote
                q_enc = quote(q, safe='')
                sresp = terminal(f"curl -s --max-time 15 'https://api.searlo.tech/api/v1/search/web?q={q_enc}&limit=10&gl=us' -H 'x-api-key: {get_key(\"SEARLO_API_KEY\")}'", timeout=20).get("output","")
                d = json.loads(sresp)
                items = [{"title": x.get("title",""), "url": x.get("link",""),
                          "description": x.get("snippet","")} for x in (d.get("results") or d.get("organic") or [])]
            elif engine == "web_search":
                r = web_search(q, limit=5)
                items = r.get("data", {}).get("web", [])
            elif engine == "tavily":
                payload = json.dumps({"api_key": get_key("TAVILY_API_KEY"), "query": q,
                    "max_results": 5, "search_depth": "advanced",
                    "include_answer": True}).encode()
                req = urllib.request.Request("https://api.tavily.com/search", data=payload,
                    headers={"Content-Type": "application/json"}, method="POST")
                d = json.loads(urllib.request.urlopen(req, timeout=20).read())
                items = [{"title": x.get("title",""), "url": x.get("url",""),
                          "description": x.get("content","")} for x in d.get("results",[])]
                if d.get("answer"):
                    raw.append({"_sub": sub, "title": "[AI 摘要]", "url": "",
                                "description": d["answer"][:300], "_engine": "tavily_answer"})
            elif engine == "serpapi_baidu":
                from urllib.parse import quote
                import re
                q_enc = quote(q, safe='')  # 中文/空格必须 URL 编码
                url = f"https://serpapi.com/search?q={q_enc}&api_key={get_key('SERPAPI_API_KEY')}&engine=baidu"
                # 用 curl 而非 urllib（urllib 到 serpapi.com 易超时）；timeout 45s（百度结果偶发慢）
                sresp = terminal(f"curl -s --max-time 45 -A 'Mozilla/5.0' '{url}'", timeout=50).get("output","")
                # 关键坑：SerpAPI 百度结果 snippet 可能含控制字符，json.loads 严格模式会报
                # "Invalid control character" → 必须先用正则清理 \x00-\x1f\x7f 再解析
                clean = re.sub(r'[\x00-\x1f\x7f]', '', sresp)
                d = json.loads(clean)
                items = [{"title": x.get("title",""), "url": x.get("link",""),
                          "description": x.get("snippet","")} for x in d.get("organic_results",[])]
            else:  # exa 等
                items = []
            for item in items:
                item["_sub"] = sub
                item["_engine"] = engine
                raw.append(item)
        except Exception as e:
            print(f"[{engine}] FAIL: {q[:40]} → {e}")

print(f"RAW: {len(raw)} 条（含引擎标注）")

# === Step 2b: 统一 rerank（Jina，一次调用全部结果）===
docs = [f"{x.get('title','')} {x.get('description','')}" for x in raw]
payload = json.dumps({"model": "jina-reranker-v2-base-multilingual",
                      "query": MAIN_QUERY, "documents": docs, "top_n": 10})
with open("/tmp/jina_payload.json", "w") as f:
    f.write(payload)
cmd = f"""curl -s -X POST 'https://api.jina.ai/v1/rerank' \
  -H "Authorization: Bearer ${JINA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @/tmp/jina_payload.json"""
out = terminal(cmd, timeout=30).get("output", "")
scores = {}
try:
    scores = {x["index"]: x["relevance_score"] for x in json.loads(out).get("results", [])}
except Exception:
    print("RERANK FAILED, fallback to raw order")

# === Step 2d: filter + dedupe + top-N ===
RELEVANCE_THRESHOLD = 0.3
top = []
seen_urls, seen_domains = set(), set()
for i, item in sorted(enumerate(raw), key=lambda t: -scores.get(t[0], 0)):
    url = item.get("url", "")
    domain = url.split("/")[2] if "//" in url else ""
    if scores.get(i, 0) < RELEVANCE_THRESHOLD and scores:
        continue
    if url in seen_urls or domain in seen_domains:
        continue
    seen_urls.add(url)
    seen_domains.add(domain)
    top.append({"score": round(scores.get(i, 0), 3), "title": item.get("title","")[:70],
                "url": url, "desc": item.get("description","")[:200],
                "sub": item.get("_sub",""), "engine": item.get("_engine","")})
    if len(top) >= 10:
        break

print(json.dumps(top, ensure_ascii=False, indent=1))
```

## 使用说明

1. **每次执行前**：把 `MAIN_QUERY` 和 `queries`（含引擎标注）换成实际调研问题
2. **引擎标注**：核心 → `tavily`，一般 → `searlo`（先烧）→ `serper`，中文 → `serper` site:，百度系 → `serpapi_baidu`，语义 → `exa`，兜底 → `web_search`
3. **查询数量**：控制在 ≤15 个（execute_code 5 分钟超时 + 50 次工具调用上限）
4. **rerank 失败兜底**：Jina 挂了就按原始顺序返回（脚本内 try/except）
5. **相关性阈值**：0.3 默认，结果太少降到 0.2，太多升到 0.4
6. **铁律（不可省）**：
   - `time.sleep(3)` —— Agnes 20 RPM 总限流
   - Jina 必须用 curl + `-d @file`（内联会转义失败）
   - key 必须脚本内读文件（execute_code 环境不自动加载 .env）
   - 同一 API 绝不并发

## 后续：chunking（可选）

rerank 后如需深度提取内容，对 top-3 结果用 `web-fetch.sh` 或 `scrape-stealth.py`（反爬时）抓取：

```bash
bash scripts/web-fetch.sh <url> 8000
# 或反爬
PYTHONPATH=$HOME/.local/lib/python3.12/site-packages /usr/bin/python3 scripts/scrape-stealth.py <url> --max-chars 8000
```

## parse_field：结构化字段提取（Step 2e）

> 对应 Perplexity SaC 第六原语 `parse_field`。rerank + dedupe 后，对 top-3 结果抓原文，提取**结构化字段**，让报告是"字段化的证据"而非"堆砌的摘要"。

### 为什么需要

Jina rerank 只给相关性分数，不告诉你"这条结果的哪个字段回答了子问题"。报告里"概念定义/历史演变/关键数字"如果直接堆摘要，就丢失字段结构，结论无法精确追溯。

### 怎么做（内联，不写脚本）

对每个 top-3 结果：
1. **抓原文**：`web-fetch.sh`（干净页）或 `scrape-stealth.py`（反爬）
2. **抽字段**（按调研主题定义字段名）
3. **字段 → 结论映射**：每条核心结论必须能指向"哪个来源的哪个字段"

### 字段模板（按主题替换字段名）

```python
# 对 top-3 抓原文后，用规则/正则提取字段（不是 LLM，省 token）
fields = {
    "定义": "",      # 概念/术语的精确定义 + 出处 URL
    "时间": "",      # 动态事实的时间戳
    "关键数字": "",  # 可量化的数据点 + 出处 URL
    "观点A": "",     # 立场 1 + 出处 URL
    "观点B": "",     # 立场 2（冲突时）+ 出处 URL
    "出处": "",      # 每个字段的来源 URL（必填）
}
```

**铁律**：字段值必须可追溯到来源 URL；缺出处的字段不进报告。字段化后的结论直接填入报告的"核心结论"与"来源列表"，保证结论↔来源一一对应。
