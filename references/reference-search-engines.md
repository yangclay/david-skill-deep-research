# 深度调研参考材料

从 SKILL.md 中提取的补充内容。核心七步法在 SKILL.md 中。

---

## 自适应搜索策略

smart-search 已内建逐层升级和提前停止逻辑。以下规则用于 **smart-search 结果不足时的补充搜索**。

### 决策树（smart-search 完成后评估）

```
smart-search 结果
  ├─ 覆盖率 < 85% 且已用完所有层？ → 补充搜索
  ├─ 中文内容密度 > 40%？ → SerpAPI 百度已自动覆盖
  ├─ 发现 PDF / DOI / arXiv 链接？ → 触发 arxiv-scholar-search
  ├─ 发现 scholar.google.com 链接？ → 触发 google-scholar-search
  ├─ 新闻时间戳 > 6 个月？ → 提示是否需要最新动态
  ├─ 核心结论无来源或存疑？ → 单独抓原文验证（web_fetch）
  ├─ web_fetch 返回 403/空内容？ → scrape-stealth.py 或 TinyFish Fetch
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

- smart-search 自动处理分层，不需要手动选引擎
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

### Tavily 增强搜索
```bash
/usr/bin/python3 /home/clay/.hermes/skills/deep-research/scripts/tavily_search_v2.py \
  --query "你的问题" --max-results 5 --verify --cross-verify --format md
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
/usr/bin/python3 /home/clay/.hermes/skills/deep-research/scripts/web-fetch.py <url> [max_chars]
```

---

## Pitfall：搜索关键词不全导致遗漏主流工具

工具/项目类调研，仅靠搜索引擎可能遗漏大项目。

**防御措施**：
1. GitHub API 交叉验证（按 stars 排序搜 topic）
2. 多关键词搜索（同一领域 3+ 种关键词组合）
3. 竞品发现（找到一个工具后搜 "alternatives"）
