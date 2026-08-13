---
name: orion-research
description: >
  当问题需要跨来源调查、拆解子问题、验证结论、处理冲突时使用。
  触发词：深度调研、调研、研究、investigate、research。
  特别适用于仅凭模型已有知识无法可靠回答，或来源时效性、
  可追溯性、交叉验证和证据质量会显著影响答案的任务。
  对于简单事实查询、仅总结用户提供的材料，或单一权威来源即可
  回答的问题，使用简单 web_search 即可，不要触发本 skill。
license: MIT
metadata:
  hermes:
    tags: [research, orion-research, multi-source, verification]
    related_skills: [browser-act, web-llm-caller]
  version: 3.1.0
---

# Deep-Research Skill v3.1

## Overview

深度调研技能。基于 **SaC（Search as Code）范式**：用 `execute_code` 写 Python 编排完整搜索 pipeline（fanout → search → extract → rerank → dedupe），只把压缩后的 top-N 结果带回上下文。结合 ODS 开源方法（Query Rephrasing、Chunking、动态搜索决策）。

**核心原则**：搜索是可编程的，不是黑盒 API 调用。多源验证、追溯原始来源、标注时效性、处理冲突。

## When to Use

- 用户说"深度调研"、"研究一下"、"调查"、"investigate"、"research"
- 问题需要跨来源交叉验证（时效性、准确性会影响结论）
- 模型已有知识无法可靠回答，或需要最新数据
- 任务涉及竞争性分析、工具对比、市场研究

## When NOT to Use

- 简单事实查询（直接回答即可）
- 单一权威来源可回答的问题
- 仅总结用户提供的材料
- 使用 `web_search` 更合适的情况

## 模式选择（ReAct vs CodeAct）

**先用 30 秒判断复杂度，不要无脑走 SaC 编排：**

| 判断维度 | ReAct（轻量） | CodeAct（SaC 编排） |
|---------|-------------|-------------------|
| 子问题数 | 1 个 | 2-5 个 |
| 来源要求 | 单一权威可答 | 需跨源交叉验证 |
| 事实类型 | 静态（定义/理论） | 动态（版本/价格/CEO） |
| 冲突风险 | 低 | 高（可能矛盾） |

**ReAct 模式**：直接 `web_search` 2-3 次 + 判断，不写 execute_code、不调 Jina，报告精简版（结论 + 来源 URL）。

**CodeAct 模式**：走完整 SaC 五段式管道（见 references/sac-search-orchestration.md）。

**判断标准**："一次 web_search 就够 + 模型已有知识能兜底" → ReAct；"多源验证 + 时效性 + 冲突处理" → CodeAct。

## 工作流（7 步）

### Step 1: 拆解 + Query Rephrasing

- 将问题拆解为 2-5 个子问题，按信息增益排序
- **差距型调研识别**：问题含"区别/优势/提升/现成方案/本质"信号 → 固定加入子问题"现有方案已经能做什么？X 的真正增量是什么？"（见 references/orion-research-user-patterns.md）
- 每个子问题生成 1-3 个查询变体（同义/英文/加限定词）
- **强制输出（写进报告"调研过程"）**：`原查询 → 变体1 / 变体2` 对照表，不是一句话带过。缺对照表 = 报告不达标
- 输出：子问题列表 + 查询组合（含变体）

### Step 2: SaC 编排搜索（核心）

- 用 `execute_code` 写一段 Python 编排搜索 pipeline
- **五段式管道**（模板见 `references/sac-search-orchestration.md`）：
  - **2a 引擎选择**：按子问题特性决策——核心→Tavily（AI 答案），一般→web_search（免费），应用/趋势/当代艺术→Tavily（实测 web_search 命中率低），中文→SerpAPI 百度，语义→Exa
  - **2b 统一 rerank**：所有引擎结果汇合 → Jina 打分 → 过滤 <0.3 → 排序
  - **2b.5 规则 filter**：snippet 过短/SEO 农场/关键词缺失 → 降权剔除（补 Jina 语义盲区，不用 LLM）
  - **2c 内容形态工具**：验证原文→web-fetch.sh / 反爬→scrape-stealth.py / 全站→crawl_site.py
  - **2d dedupe + top-N**：域名去重，只回压缩结果
  - **2e parse_field**：对 top-3 抓原文抽结构化字段（定义/时间/关键数字/观点），字段可追溯到来源 URL
- **限流铁律**：Agnes 总限流 20 RPM → `time.sleep(3)` 不可省；同一 API 绝不并发；Jina 一次调研只调 1-2 次
- **工具选择矩阵**（按场景灵活调用，不是"源不足才用"）：
  - 核心子问题深度搜索 → 内联 Tavily API（`advanced` + `include_answer`）
  - 一般子问题 → `web_search`（免费）
  - 快速抓单页 → `scripts/web-fetch.sh` 或内联 curl
  - 反爬/Cloudflare → `scripts/scrape-stealth.py --mode http`
  - 全站/多页 → `scripts/crawl_site.py`（crawl4ai）
  - 中文生态/学术/GitHub → 见工具矩阵对应行
- 控制：查询 ≤15 个，`time.sleep(3)` 限流，Jina 必须用 curl + `-d @file`

### Step 3: 动态搜索决策（Gap Analysis）

- 评估 top-N 结果质量：
  - 所有子问题有可靠证据 → 停止，进入 Step 4
  - 存在缺口 → 基于缺口定向补搜（最多 3 轮）
  - **对比类缺口**：差距型调研只有 X 的介绍、缺现有方案对比 → 补搜"X vs Y"/"X alternative"（见 references/orion-research-user-patterns.md）
- **不要盲目搜满固定轮数** — 质量够就停，省 token 省 RPM

🔴 **CHECKPOINT（强制）**：Step 3 结束后，必须显式评估「每个子问题是否有 A/B 级证据支撑」。有缺口 → 回到 Step 2 换引擎补搜；全部有证据 → 才允许进入 Step 4。不得跳过此判断直接写报告。

### Step 4: 验证（不变量 + Gotcha）

| 不变量 | 检查 |
|--------|------|
| 搜索 ≠ 证据 | 结果多不代表证据强 |
| 单源 ≠ 验证 | 一个来源再权威也要标注 |
| 转载 ≠ 独立 | 追溯引用链，按 source family 计数 |
| 冲突必须可见 | 不得静默选择其中一个 |
| 引用 ≠ 支撑 | claim 必须被 citation 原文支持 |
| 时效必须验证 | 动态事实标注时间戳 |

### Step 5: 报告

- 完整报告 = 核心结论（带可信度）+ 证据 + 来源列表（每行含可点击 URL）+ 冲突记录 + 分析过程
- **差距型调研**：核心结论第一条必须是 X 的真正价值（解决的痛点，非功能列表）+ 与现有方案的差距（见 references/orion-research-user-patterns.md）
- 必须包含 **Gotcha 检测** 章节（显式引用 G-001/G-012/G-013/G-014/G-017 状态）
- **入库规则（强制）：写 `~/wiki/raw/research/` 的唯一前提是用户明确说"存知识库"/"保存到 raw/research/"**。未指定 → 报告不写盘、不 sync Obsidian，只在聊天给核心结论，改用 `hindsight_retain` 记录核心教训
- 用户指定入库时 → 写 `~/wiki/raw/research/主题-YYYY-MM-DD.md` 并 sync 到 Obsidian（见 references/research-report-management.md）

### Step 6: 独立验证 pass（确定性，非 LLM 自评）

报告写完 ≠ 完成。用**确定性规则**独立复核（不是作者自己勾 ✅）：

| 检查项 | 通过标准 | 失败处理 |
|--------|---------|---------|
| 来源可追溯 | 来源表每行有可点击 URL | 缺 URL → 报告不达标，回补 |
| 可信度不虚标 | 每个 A 级结论有 ≥2 个独立 source family | A 级无支撑 → 降为 B |
| 冲突可见 | 有矛盾未标注 = 失败 | 回补矛盾记录 |
| Gotcha 真实执行 | 每个 Gotcha 写"做了什么"而非"应该做" | 空洞勾选 → 回补 |

**执行方式**：用 `simple-verifier` skill 或手动逐项核对。**禁用 LLM 自评可信度**——同质 LLM 验证无意义（用户原则）。

### Step 7: 搜索策略反馈（积累"引擎-子问题"经验）

调研结束后，用 `hindsight_retain` 结构化记录（不写文件）：

```
[引擎-子问题匹配] 子问题类型 X → 引擎 Y 有效/无效 → 原因。| Involving: david | 搜索策略反馈
```

**只记录两类**：
1. 某引擎对某类子问题**失效**（如 SerpAPI 百度对学术失效、Tavily 对中文失效）
2. 某引擎对某类子问题**意外有效**（超出预期）

**不记录**：一切正常、按预期工作的调用（无增量信息）。

目的：积累"什么引擎对什么子问题最有效"经验，让下次引擎决策更快更准。

## 反模式（不要这样做）

| 反模式 | 后果 |
|--------|------|
| ❌ 盲搜满固定轮数 | 浪费配额和 token，且不解决真实缺口 |
| ❌ 同 API 并发调用 | 触发 429，全部请求失败 |
| ❌ 跳过 Jina rerank 直接写报告 | 低质量/无关来源混入结论 |
| ❌ 把外部 LLM 回答当搜索源（smart chat） | 黑盒无法验证来源，G-001/G-014 全部失效 |
| ❌ 所有子问题都走 Tavily | 1000 credits/月很快烧光，一般子问题用免费层即可 |
| ❌ 结果全量塞进上下文 | 违反 SaC 核心（只回 top-N 压缩结果） |

## 核心 Gotchas

| Gotcha | 触发条件 | 失败表现 | 检查方法 |
|--------|---------|---------|---------|
| **G-001 伪独立来源** | 多结果声称同一数字 | 将转载视为独立证据 | 追溯引用链，按 source family 计数 |
| **G-012 SEO 内容农场** | 搜索结果含大量营销内容 | 将 SEO 内容视为有效来源 | 识别标题党/模板化内容，优先一手来源 |
| **G-013 时效性过时** | 涉及动态事实（定价、版本、CEO） | 使用过时信息 | 检查发布日期，标注时间戳 |
| **G-014 Citation 支撑失败** | 引用了但未验证 | 假设"Citation = 支持" | 抓取原文验证 entailment |
| **G-017 冲突静默** | 不同来源矛盾 | 未标注冲突 | 分类冲突并给出判断 |

## 输出契约

每次调研交付：
1. 核心结论 3-5 条（每条带可信度 A/B/C/D）
2. 来源列表（每行含可点击 URL + 类型 + 可信度）——缺 URL 判不达标
3. Gotcha 检测章节
4. 矛盾记录（不同来源说法差异 + 判断依据）
5. 聊天中：核心结论 +（若入库）文件路径
6. 入库：仅用户明确指定时写 raw/research/ 并 sync，否则不写盘

## 参考文档

- [SaC 搜索编排模板](references/sac-search-orchestration.md) ← 核心，Step 2 用
- [来源可信度评估](references/source-evaluation.md)
- [报告模板](references/reporting.md)
- [用户调研模式（差距分析）](references/orion-research-user-patterns.md) ← Step 1/3/5 用
- [故障处理 F1-F7](references/failure-handling.md) ← Step 2 工具失败时用
- [中文调研专项 + 工具参考](references/tool-reference.md) ← 中文生态/辅助脚本
