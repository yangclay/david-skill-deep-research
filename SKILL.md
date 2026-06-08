---
name: deep-research
description: "深度调研：问题分解 → 多引擎搜索 → 去重汇总 → 可信度评估 → 综合报告。触发条件：Clay 要求深度调研、对比分析、全面了解、市场调查，或技术问题 ≥2 个未知变量。"
---

# 深度调研（Deep Research）

问题分解 → 多引擎搜索 → 去重 → 可信度评估 → 结构化报告。

## 使用时机

- Clay 说"深度调研"、"调研一下"、"全面了解"、"对比分析"
- 技术问题 ≥ 2 个未知变量
- 需要多源信息综合的分析任务
- 不是单条快速搜索（那直接用 web_search 或 tavily__tavily_search）

---

## ⚠️ 文件命名规则（最优先）

**报告文件名必须包含调研主题关键词，禁止使用默认的"调研报告"作为文件名！**

格式：`主题关键词-YYYY-MM-DD.md`（日期放末尾）

示例：
- "AI 剪片工具对比" → `AI剪片工具对比-2026-05-14.md`
- "LLM Wiki 与知识库最佳实践" → `LLM-Wiki知识库最佳实践-2026-05-05.md`
- "智能家居协议对比" → `智能家居协议对比-2026-05-14.md`

**禁止：**
- `调研报告.md`（默认名称，无主题）❌
- `2026-05-14-主题.md`（日期在前）❌

存放位置：由调用者（agent AGENTS.md）指定。默认 `raw/research/主题-YYYY-MM-DD.md`。

**执行方式：** 在 Step 0（问题分解）时就确定文件名，不要等到 Step 7 才想名字。

---

## 七步调研法

### Step 0：问题分解（Query Decomposition）— 必做

收到主题后，先拆解为子问题再搜索。**这是提升覆盖率最有效的单一步骤。**

1. **理解真实意图**：Clay 说的 ≠ Clay 要的，还原真实需求
2. **拆解为 3-5 个子问题**：
   - 层次分解：大主题 → 子主题 → 具体问题
   - 横向扩展：同一问题从不同角度切入（用户/开发者/竞品/技术）
   - 纵向挖掘：顺着回答链继续问"为什么"和"然后呢"
3. **Query 扩展**：
   - 同义词（"AI" → "artificial intelligence", "机器学习", "深度学习"）
   - 口语→术语（"把视频变短" → "video clipping"）
   - 加限定词（时间、地区、领域）
4. **信息增益排序**（类比决策树分裂）：
   - 拆解完子问题后，评估每个子问题的**信息增益**——"搜完这个子问题，能多大程度减少整体不确定性？"
   - 按信息增益降序排列，优先搜索增益最大的子问题
   - 如果某个子问题搜完后对核心结论没有影响（类比 Permutation Importance ≈ 0），跳过剩余搜索
   - **判断方法**：问自己"如果去掉这个子问题的答案，最终结论会变吗？" → 不会则跳过
5. **输出**：排序后的子问题列表，每个子问题对应 1-2 个搜索 query + 预估信息增益（高/中/低）

> 示例："AI 剪片工具" →
> - 子问题1（高增益）：商业 AI 剪片工具有哪些？价格和功能对比 ← 直接决定推荐
> - 子问题2（高增益）：开源 AI 剪片工具有哪些？（GitHub） ← 决定是否有免费方案
> - 子问题3（中增益）：中文生态有没有本土方案？（知乎/公众号） ← 补充本土化视角
> - 子问题4（低增益）：自部署方案 vs SaaS，各适合什么场景？ ← 细节，可能跳过

🔴 **CHECKPOINT**：展示子问题列表给 Clay，确认搜索方向后再进入 Step 1。

### Step 1：判断调研深度

| 级别 | 信号 | smart-search 参数 |
|---|---|---|
| 快速 | 简单问题、单一方向 | （默认覆盖率 85%） |
| **标准**（默认） | 多角度分析 |  |
| 深度 | 全面调研、工具对比 |  + 辅助工具补充 |
| 极限（--exhaustive） | 不计代价，先告知 Clay | 全部子问题 + Tavily research（最后手段） |

### Step 2：搜索（smart-search 驱动）

**所有搜索统一用 smart-search，不要手动调各个 API。**

```bash
# 单查询（自动逐层升级：DuckDuckGo → Searlo → SerpAPI → Tavily，覆盖率≥85%停止）
python3 /home/clay/.hermes/skills/deep-research/scripts/smart-search.py "查询词"

# 多子问题搜索（共享结果池，避免重复调用）
python3 /home/clay/.hermes/skills/deep-research/scripts/smart-search.py --queries "子问题1" "子问题2" "子问题3"

# Markdown 输出
python3 /home/clay/.hermes/skills/deep-research/scripts/smart-search.py "查询词" --format md
```

**机制说明**：
- **SQLite 缓存**（7天 TTL）：同一查询不重复搜
- **逐层升级**：DuckDuckGo（免费）→ Searlo（$0.30/千次）→ SerpAPI 百度（100次/月）→ Tavily（$0.01/次）
- **85% 覆盖率提前停止**：不追求完美，够了就停
- **子问题共享结果池**：所有子问题共用搜索结果，覆盖够就跳过剩余
- **多视角交叉验证（Bagging 思维）**：对核心子问题，从至少 2 个独立视角搜索（如"用户评价"和"技术评测"），交叉比对结论——一致则可信度高，矛盾则标注争议。这比单视角搜 10 条结果更能降低来源偏差
- **触发条件**：深度/极限调研的核心子问题；快速调研不触发

**特殊场景补充**（smart-search 覆盖不够时）：

- 技术工具/开源项目 → GitHub API
- 语义相似内容 → Exa
- 学术论文 → `google-scholar-search` / `arxiv-scholar-search`
- 社区讨论 → HN Algolia / Reddit JSON
- 反爬/Cloudflare/SPA 页面 → Scrapling（scrape-stealth.py）
- 反爬 + 需要交互/登录态 → browser-act（`skill_view(name='browser-act')`）
- 多页爬取/全站抓取 → crawl4ai（crawl_site.py）
- 抓取原文 → `web_fetch`（内置）
- 微信文章 → curl + MicroMessenger UA（详见 `references/tinyfish-api.md` 或 `research` skill 的 `references/web-fetch-patterns.md`）

**缓存管理**：
```bash
python3 smart-search.py --cache-stats   # 查看缓存统计
python3 smart-search.py --cache-clear   # 清理过期缓存
```

---

**补充搜索工具：**


**Scrapling 反爬抓取**（web_fetch 被拦截时的替代）
- 路径：`scripts/scrape-stealth.py`
- 模式：http（默认，快速）/ stealth（绕 Cloudflare）/ dynamic（JS SPA）
- 用法：
  ```bash
  # 基础抓取（替代 web_fetch）
  python3 scripts/scrape-stealth.py https://example.com

  # 绕过 Cloudflare
  python3 scripts/scrape-stealth.py https://protected.com --mode stealth

  # JS 渲染 SPA
  python3 scripts/scrape-stealth.py https://spa-site.com --mode dynamic

  # 限制长度
  python3 scripts/scrape-stealth.py https://example.com --max-chars 8000
  ```
- 适用场景：web_fetch 返回 403/空内容/Cloudflare challenge、SPA 动态渲染页面
- 自动降级：http → stealth → dynamic，无需手动选模式
- 依赖：`pip install scrapling[all]`（venv: `workspace-shared/venvs/deep-research/`，已装好）
- 浏览器：使用系统 Chrome（`/usr/bin/google-chrome`），无需额外下载。脚本 shebang 指向共享 venv。

**crawl4ai 多页爬取**（需要爬取整个站点或多个页面时）
- 路径：`scripts/crawl_site.py`
- 依赖：crawl4ai venv `~/.hermes/tools/crawl4ai-venv/bin/python`
- 三种模式：
  ```bash
  # 单页抓取（替代 web_fetch，输出更干净）
  ~/.hermes/tools/crawl4ai-venv/bin/python scripts/crawl_site.py https://example.com --mode single

  # 多页爬取：自动跟踪同域链接，最多 N 页
  ~/.hermes/tools/crawl4ai-venv/bin/python scripts/crawl_site.py https://docs.example.com --mode multi --max-pages 10

  # Sitemap 模式：从 /sitemap.xml 发现 URL 并批量抓取
  ~/.hermes/tools/crawl4ai-venv/bin/python scripts/crawl_site.py https://blog.example.com --mode sitemap --max-pages 50

  # JS 渲染（SPA 页面）
  ~/.hermes/tools/crawl4ai-venv/bin/python scripts/crawl_site.py https://spa-site.com --mode multi --js

  # JSON 输出（方便程序处理）
  ~/.hermes/tools/crawl4ai-venv/bin/python scripts/crawl_site.py https://example.com --mode multi --json -o /tmp/crawl_result.json
  ```
- 适用场景：需要爬取整个文档站、博客全站、产品列表页等多页内容
- 与 Scrapling 的区别：Scrapling 是单页反爬专家，crawl4ai 是多页爬取 + JS 渲染
- 浏览器：首次使用需安装 Chromium（`~/.hermes/tools/crawl4ai-venv/bin/python -m playwright install chromium`）

**TinyFish Search & Fetch（免费，浏览器渲染）**
- 完整文档：`references/tinyfish-api.md`
- **Search API**：`GET https://api.search.tinyfish.ai` — 真浏览器渲染的实时搜索，返回结构化 JSON。免费（0 credits），限速 30 req/min。适合动态/实时内容（价格变动、财报、突发新闻）
- **Fetch API**：`POST https://api.fetch.tinyfish.ai` — 真浏览器渲染页面，返回干净 markdown/JSON/HTML。免费（0 credits），限速 150 url/min。可替代 scrape-stealth.py（托管服务，无需本地浏览器）
- 环境变量：`TINYFISH_API_KEY`（https://agent.tinyfish.ai/api-keys）
- 安装：`pip install tinyfish`（SDK）或 `npm install -g @tiny-fish/cli`（CLI）
- **适用场景**：web_fetch 返回 403/JS 重页面 → TinyFish Fetch；需要实时动态搜索结果 → TinyFish Search
- **不适用**：需要多引擎（Google/Baidu/Bing）→ 用 SerpAPI；需要自动综合 → 用 Tavily

**Tavily 搜索（AI 原生）**
- `tavily__tavily_research` — 一次调用 = 自动多轮搜索 + 内容抓取 + 综合报告。深度调研必用，但注意每月限额（~1000次），省着用。
- `tavily__tavily_search` — 快速搜索，参数：query, search_depth(basic/advanced), max_results, include_domains, exclude_domains, time_range

**Exa 语义搜索**
- `Exa`（OpenClaw 原生支持，EXA_API_KEY）— 找相似内容、相关论文、主题探索

**GitHub 代码仓库搜索（技术工具专项）**
GitHub API 搜索代码仓库，支持星标排序、主题过滤。环境变量：`GITHUB_TOKEN`（5000次/小时，无需 key 只能 60次）。

```bash
# 搜索仓库（按星标排序）
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/search/repositories?q=关键词&sort=stars&per_page=10"

# 解析结果
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/search/repositories?q=AI+CLI+tool&sort=stars&per_page=5" \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
for r in d['items'][:5]:
    print(r['full_name'], '⭐', r['stargazers_count'])
    print(r.get('description',''))
    print(r['html_url'])
    print()
"
```

**适用场景**：找开源工具、对比同类项目、查项目活跃度、看 README 了解功能。

**ClawHub / Stack Overflow 工具发现**
- **ClawHub**（skill 发现）：
  ```bash
  clawhub search "关键词"        # 搜索 skill
  clawhub list                   # 列出已安装
  clawhub install skill-name     # 安装
  ```
  需要 `clawhub` CLI（npm i -g clawhub）
- **Stack Overflow**：搜索技术问题/报错
  ```bash
  # SerpAPI Google 搜 Stack Overflow
  curl -s "https://serpapi.com/search?q=关键词+site:stackoverflow.com&api_key=$SERPAPI_API_KEY&num=10"
  # 或 DuckDuckGo
  curl -s "https://api.duckduckgo.com/?q=关键词+site:stackoverflow.com&format=json" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for r in d.get('RelatedTopics',[])[:5]:
    if 'stackoverflow' in r.get('URL',''):
        print(r.get('Text',''))
        print(r.get('URL',''))
        print()
"
  ```

**SerpAPI 统一搜索（补充中文/商业/新闻）**
[SerpAPI](https://serpapi.com) 统一封装 15+ 搜索引擎，一次调用切换引擎。环境变量：`SERPAPI_API_KEY`。

```bash
# Google（默认，中英文兼顾）
curl -s "https://serpapi.com/search?q=搜索词&api_key=$SERPAPI_API_KEY&engine=google&num=10"

# 百度（中文内容优先）
curl -s "https://serpapi.com/search?q=搜索词&api_key=$SERPAPI_API_KEY&engine=baidu&num=10"

# Bing
curl -s "https://serpapi.com/search?q=搜索词&api_key=$SERPAPI_API_KEY&engine=bing&num=10"

# YouTube（视频内容）
curl -s "https://serpapi.com/search?q=搜索词&api_key=$SERPAPI_API_KEY&engine=youtube&num=5"

# 解析结果（jq）
curl -s "..." | python3 -c "
import sys,json
d=json.load(sys.stdin)
for r in d.get('organic_results',[])[:5]:
    print(r.get('title'))
    print(r.get('link'))
    print(r.get('snippet',''))
    print()
"
```

**引擎选择原则**：
- 默认 Google（综合最好）
- 中文内容为主 → 百度
- 新闻/突发 → Google News 或 Bing
- 视频调研 → YouTube
- 俄语内容 → Yandex
- 韩语内容 → Naver

**学术搜索（论文相关时启用）**
- `google-scholar-search` skill — Google 学术
- `arxiv-scholar-search` skill — arXiv 预印本

**兜底**
- `web_search`（DuckDuckGo，内置）— 无限免费

### Step 3：中文内容专项

中文内容在英文搜索源覆盖率低，需要专项补充。

> **完整中文调研指南**（企业背景调查、软文识别、骗局模式、平台选择）见 `references/chinese-research-patterns.md`。

1. **SerpAPI 百度引擎**：中文内容为主时直接用 `engine=baidu`
2. **Google 加 `site:` 过滤**：
   - `site:zhihu.com` — 知乎
   - `site:mp.weixin.qq.com` — 微信公众号
   - `site:juejin.cn` — 掘金
   - `site:csdn.net` — CSDN
   - `site:bilibili.com` — B站（视频）
   - `site:xiaohongshu.com` — 小红书（种草/口碑）
   - `site:douyin.com` — 抖音（短视频体验）
   - `site:tousu.sina.com.cn` — 黑猫投诉（消费维权）
3. **企业信息查询**：天眼查/企查查（公司注册、法律诉讼、行政处罚）
4. **微信/知乎文章内容抓取**：搜索结果得到 URL 后，用 `web-fetch` 直接抓正文（微信公众号文章反爬，需试），知乎文章可直接抓
5. 学术搜索加 `language:zh` 参数
6. **小红书内容**：搜索 `site:xhslink.com` 或直接搜索关键词+小红书，用 web-fetch 抓取
7. DuckDuckGo 加中文关键词

### Step 4：去重汇总

```
收集所有搜索结果
  → URL exact dedup（相同 URL 只保留一个）
    → Domain 去重（同域名多条 → 保留最权威一篇）
      → 标题/摘要相似度检查（>80% 重复则合并）
        → 按相关性排序
```

### Step 5：可信度评估

每条重要结论标注等级：

| 等级 | 标签 | 含义 | 判断标准 |
|---|---|---|---|
| A | ✅ 高度可信 | 可直接引用 | ≥2 个独立来源证实 + 官方/学术来源 |
| B | ⚠️ 基本可信 | 可参考 | 单源但来源权威 + 逻辑自洽 |
| C | ❓ 存疑 | 需验证 | 有矛盾或来源不明确 |
| D | ⚡ 不可信 | 不建议引用 | 与已知事实矛盾或来源明显偏颇 |

**判断要素**：来源类型 + 时效性 + 是否有利益相关 + 交叉验证通过 + 可追溯到原始来源

### Step 6：矛盾信息处理

- **事实矛盾**：查证原始来源，标注可信度更高的一方
- **观点分歧**：并列呈现，注明各方立场和背景
- **信息过时**：标注时间，优先用最新来源

### Step 7：生成报告

**调研报告 = 一本书。** 不是摘要，是完整的研究记录。

报告包含：
1. 核心结论（3-5 条，带可信度）
2. 完整的调研过程（所有子问题的搜索结果、关键来源全文引用、数据对比）
3. 来源列表（每条来源的 URL、类型、可信度）
4. 矛盾记录（不同来源的说法差异、如何判断的）
5. 分析过程（为什么得出这个结论，推理链是什么）

**⚠️ 文件命名必须包含主题，禁止使用默认的"调研报告"作为文件名！**

报告写入路径由调用者（agent AGENTS.md）指定。默认 `raw/research/主题-YYYY-MM-DD.md`。

**命名规则：**
- 从调研主题中提取 3-5 个关键词，**日期放末尾**
- 用连字符 `-` 连接关键词
- 格式：`主题关键词-YYYY-MM-DD.md`（不是 `YYYY-MM-DD-主题.md`）
- 示例：
  - 调研主题"AI 剪片工具对比" → `AI剪片工具对比-2026-05-14.md`
  - 调研主题"LLM Wiki 与知识库最佳实践" → `LLM-Wiki知识库最佳实践-2026-05-05.md`
  - 调研主题"智能家居协议对比" → `智能家居协议对比-2026-05-14.md`

**⚠️ 调研报告存放位置：** 由调用者（agent AGENTS.md）指定。默认 `raw/research/`。

**⚠️ sources/ 必须是完整调研报告原文，不是摘要！**
- 完整的调研过程、所有搜索结果、详细分析 → ✅
- 只有结论和要点 → ❌ 这是摘要，丢失了调研细节

**报告模板：**

```markdown
# [调研主题]

> 调研时间：YYYY-MM-DD HH:MM
> 调研深度：快速/标准/深度/极限
> 使用搜索源：Tavily, Exa, Scholar, ...
> 搜索关键词：关键词1, 关键词2, ...

---

## 核心结论

1. **结论一** — 一句话概括 + 理由 [可信度: A/B/C/D]
2. **结论二** — ...
3. **结论三** — ...

---

## 调研过程

### 子问题 1：[问题描述]

**搜索 query：** "query1" "query2"
**信息增益：** 高/中/低

**来源 1：[来源标题]**
> "关键原文引用（完整段落，不是一句话摘录）"
> — URL: https://... | 类型: 学术/官方/媒体/社区 | 可信度: A/B/C

**来源 2：[来源标题]**
> "关键原文引用"
> — URL: https://... | 类型: ... | 可信度: ...

**分析：** 综合以上来源，[分析过程和判断依据]

---

### 子问题 2：[问题描述]

[同上结构]

---

## 数据对比

| 维度 | 来源A说法 | 来源B说法 | 来源C说法 | 判断 |
|---|---|---|---|---|
| [维度1] | ... | ... | ... | 采纳X，因为... |
| [维度2] | ... | ... | ... | 存疑，需进一步验证 |

---

## 矛盾与争议

### 矛盾 1：[描述]
- 来源 A 说：... [可信度: X]
- 来源 B 说：... [可信度: X]
- 判断：采纳 X，因为...

### 未解决的争议
- [描述] — 当前证据不足以判断，需要...

---

## 来源列表

| # | 来源 | 类型 | 可信度 | URL |
|---|---|---|---|---|
| 1 | 标题 | Tavily/Scholar/Exa/Serper/... | A/B/C | 链接 |
| 2 | ... | ... | ... | ... |

---

## 建议下一步

1. 基于调研结果的具体行动建议
2. 需要进一步验证的点
3. 风险提示（如有）
```

**关键区别：**
- 旧模板：只有结论和分析（像导读）
- 新模板：有完整的调研过程、来源原文引用、数据对比、矛盾记录（像书的原文）
- 每个子问题都记录了搜索 query、来源全文引用、分析过程
- 矛盾信息单独记录，不隐藏

**交付方式**：
1. 报告写入调用者指定的路径（默认 `raw/research/主题-YYYY-MM-DD.md`）
2. 报告必须是**完整的调研内容**（含详细分析、来源列表、可信度评估），不是摘要
3. 在聊天中给调用者 **核心结论**（3-5 条），不是完整报告
4. 告诉调用者完整报告的文件路径
5. 有需要决策的点，明确指出并给推荐

**注意：** 知识条目提取由 knowledge worker 负责，researcher 不做提取工作。

### Step 8：迭代补强（Boosting 思维）— 深度/极限调研必做

**核心思想：** Boosting 的策略是"每次聚焦上次犯的错"。调研也一样——第一轮报告必然有薄弱点，第二轮专门补强。

**触发条件：** 深度或极限调研；快速调研跳过。

**执行步骤：**
1. **识别薄弱点**——扫描第一轮报告，标记：
   - 只有单一来源支撑的结论（可信度可能被高估）
   - 标记为 C/D 可信度的结论（证据不足）
   - 子问题之间逻辑矛盾的地方
   - Clay 最关心的核心结论如果证据不够扎实
2. **定向补搜**——只针对薄弱点搜索，不重搜已经扎实的部分
3. **更新报告**——将补强结果合并进报告，提升薄弱点的可信度

**类比：** 就像 Gradient Boosting 在残差（上次的错误）上训练下一棵树，迭代补强在"调研的残差"（上次的证据缺口）上做专项搜索。

**停止条件：**
- 所有核心结论达到 B 级以上可信度 → 停止
- 已迭代 2 轮仍有 C/D 结论 → 标注为"需要人工判断"，告知 Clay
- Token 预算达到 70% → 停止迭代，告知 Clay 当前质量边界

---

## Scope 边界

**本 skill 做什么**：问题分解 → 多引擎搜索 → 去重汇总 → 可信度评估 → 结构化报告

**本 skill 不做什么**：
- 不做知识条目编译（→ knowledge-writer）
- 不做知识库索引（→ knowledge-base）
- 不做书籍内容提取（→ book-extractor）
- 不做 Obsidian 同步（→ obsidian-vault）

**不要 delegate_task 给其他 agent 做搜索**——搜索是 researcher 的核心职责，自己完成。

---

## 自适应搜索策略、搜索引擎全景、辅助脚本

详见 `references/reference-search-engines.md`

---

## Kanban 研究任务模板

详见 `references/reference-search-engines.md` 中的模板部分。

---

## Token 消耗控制

- smart-search 自动处理分层，不需要手动选引擎
- 搜索结果写文件，不全部塞进 context
- 先综合再展示，给 Clay 看去重后的精华

---

## 故障处理（if-then fallback）

| # | 故障 | 触发条件 | 一线修复 | 仍失败兜底 |
|---|------|---------|---------|-----------|
| F1 | smart-search 零结果 | `smart-search.py` 返回空 JSON | 换同义词重搜（中英文各一次） | 降级到 `web_search`（DuckDuckGo 内置）+ 手动 `curl` 已知权威来源 |
| F2 | Tavily 配额耗尽 | `tavily__tavily_research` 返回 429/quota error | 切到 SerpAPI Google + smart-search 组合 | 在报告标注"⚠️ Tavily 不可用，覆盖度可能不足"，继续用免费源完成 |
| F3 | web_fetch 被拦截 | 返回 403 / 空内容 / Cloudflare challenge | 用 `scripts/scrape-stealth.py --mode stealth` 重试 | 用 TinyFish Fetch（`references/tinyfish-api.md`）或标注"来源不可抓取，仅用摘要" |
| F4 | Context window 溢出 | 搜索结果总量 > 70% context budget | 只保留去重后 top-20 来源的摘要（非全文），全文写入中间文件 | 分批处理：先处理子问题 1-3，写中间文件；再处理 4-5，合并 |
| F5 | 核心结论全为 C/D 可信度 | Step 5 评估后无 A/B 级结论 | 针对 C/D 结论做 Step 8 迭代补搜（换 query、加 site: 过滤） | 在报告显式标注"⚠️ 核心结论证据不足，需人工判断"，不编造可信度 |
| F6 | 质量自评 < 18/30 | Step 7 后 rubric 总分不达标 | 回溯最弱维度（通常是覆盖度或来源质量），补搜 2-3 轮 | 告知 Clay "当前质量待提升"，给出已完成的部分报告 + 建议补充方向 |
| F7 | 来源严重矛盾 | ≥2 个权威来源对同一事实说法相反 | 查原始出处（论文/官方文档/一手数据），标注哪方更可信 | 并列呈现双方说法 + 矛盾原因分析，标注"需人工裁决" |

**执行原则**：
- F1-F3 是搜索层故障，自动修复不中断
- F4-F5 是质量层故障，修复后继续
- F6-F7 是交付层故障，必须告知 Clay

---

## 引用验证

重要结论必须验证：抓取原文 → 对比摘要 → 确认/否定

---

## 调研质量 Checklist

每次调研完成后检查：
- [ ] 问题已分解为 3-5 个子问题
- [ ] 搜索覆盖 ≥ 2 种来源类型
- [ ] 核心子问题有 ≥ 2 个独立视角搜索
- [ ] 去重完成（URL + Domain + 内容相似度）
- [ ] 重要结论标注可信度等级（A/B/C/D）
- [ ] 深度/极限调研已完成迭代补强（Step 8）
- [ ] 报告已写入调用者指定的路径
- [ ] 在聊天中给了 Clay 核心结论 + 文件路径
- [ ] GitHub 交叉验证（工具/项目类调研）

## 质量自评 Rubric（交付前必做）

报告写完后，按 6 个维度自评（1-5 分）：

| 维度 | 1分 | 3分 | 5分 |
|------|-----|-----|-----|
| **覆盖度** | 只覆盖一个角度 | 主要角度有遗漏 | 全覆盖 |
| **来源质量** | 1-2个来源 | 3-5个来源 | ≥5个多类型 |
| **信息密度** | 大量概述 | 有分析不够深 | 详细分析+原文引用 |
| **可信度标注** | 无来源支撑 | 有来源未标注等级 | 全部 A/B/C/D |
| **矛盾处理** | 忽略矛盾 | 记录未分析 | 来源对比+判断依据 |
| **可操作性** | 无建议 | 建议太泛 | 具体可执行 |

**质量底线**：任何维度 < 3 → 不交付。总分 < 18/30 → 标注"质量待提升"。

🛑 **CHECKPOINT**：质量自评未达标（总分 < 18 或任一维度 < 3）→ 不交付，回溯补搜或告知 Clay 质量边界。

## 反例与黑名单：调研中不要做的事

### 已知领域陷阱（核心反例）

Clay 说"调研一下 X"，agent 觉得自己已经知道答案就跳过七步法。

| 条件 | 行为 |
|------|------|
| Clay 没说"调研" + 有相关知识 | 直接回答 |
| Clay 说了"调研"/"深度调研" | **必须走七步法** |

调研的价值不只是"找到答案"，而是多源验证 + 交叉对比 + 发现盲区。

### 搜索阶段反例

| # | 不要做 | 为什么 | 应该做 |
|---|--------|--------|--------|
| R1 | 用单引擎搜一次就下结论 | 单源覆盖率低，来源偏差大 | ≥2 个独立视角交叉验证（Bagging 思维） |
| R2 | 搜到第一个结果就停止 | 可能错过更好的来源 | 子问题全部搜完，按信息增益排序 |
| R3 | 手动逐个调搜索引擎 API | 容易遗漏、浪费 token | 统一用 `smart-search.py` 自动分层 |
| R4 | 把搜索结果全部塞进 context | context 溢出，后面的子问题无空间 | 结果写中间文件，只取去重后 top-20 摘要 |

### 报告阶段反例

| # | 不要做 | 为什么 | 应该做 |
|---|--------|--------|--------|
| R5 | 只写结论不写来源 | Clay 无法验证，报告无可信度 | 每条结论附来源 URL + 可信度等级 |
| R6 | 忽略矛盾信息 | 隐藏分歧 = 信息损失 | 并列呈现 + 标注哪方更可信及理由 |
| R7 | 用"据多方报道"等模糊措辞 | 无法追溯，可能是编造 | 列出具体来源编号 |
| R8 | 报告只有摘要没有过程 | 丢失调研细节，无法复现 | 完整记录子问题、搜索 query、原文引用 |
| R9 | 给 Clay 读完整报告 | context 浪费，Clay 要的是结论 | 聊天中给核心结论(3-5条) + 文件路径 |

### 交付阶段反例

| # | 不要做 | 为什么 | 应该做 |
|---|--------|--------|--------|
| R10 | 质量自评 < 18/30 仍交付 | 低质量报告浪费 Clay 时间 | 回溯补搜或标注"质量待提升" |
| R11 | 编造可信度等级 | 虚假信心导致错误决策 | 证据不足时标 C/D 或"需人工判断" |
| R12 | 文件名用"调研报告.md" | 无法区分多次调研 | `主题关键词-YYYY-MM-DD.md` |

调研的价值不只是"找到答案"，而是多源验证 + 交叉对比 + 发现盲区。
