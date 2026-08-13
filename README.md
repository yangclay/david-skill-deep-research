# Deep Research Skill

> **深度调研技能：多源验证、可追溯、反幻觉。** 当问题需要跨来源调查、拆解子问题、验证关键结论、处理来源冲突时使用。

[![Version](https://img.shields.io/badge/version-v3.1.0-blue)](https://github.com/yangclay/david-skill-deep-research)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](https://github.com/yangclay/david-skill-deep-research/blob/master/LICENSE)

用于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的生产级深度调研技能（Agent Skill）。

## 为什么需要它

AI 调研最常见的失败模式不是"搜不到"，而是**搜到了但不可信**：

| 失败模式 | 表现 |
|----------|------|
| 伪独立来源 | 8 个网页声称同一数字，实际全部转载同一个原始报道 |
| SEO 内容农场 | 中文 top 结果多为百度教育/文库/百科等拼凑内容 |
| 时效性过时 | 用 2023 年的信息回答 2026 年的问题 |
| Citation 支撑失败 | 引用了但原文并不支持结论 |
| 冲突静默 | 不同来源矛盾时静默选一个 |

本技能用 **SaC（Search-as-Code）五段式管道 + 5 个核心 Gotcha** 系统性解决这些问题。

## 工作流

```
Step 1 拆解 → Step 2 SaC 编排 → Step 3 Gap Analysis → Step 4 验证 → Step 5 报告
                ↓                                                              ↓
           引擎选择 → Jina rerank → 规则 filter → dedupe → parse_field   Step 6 独立验证
                                                                           Step 7 策略反馈
```

核心：**搜索是可编程的**。用 `execute_code` 编排完整搜索管道（fanout → search → rerank → dedupe），只把压缩后的 top-N 结果带回上下文。

## 安装

### 方式一：clone 到 Hermes profile（推荐）

```bash
git clone https://github.com/yangclay/david-skill-deep-research.git \
  ~/.hermes/profiles/<profile>/skills/deep-research
```

### 方式二：直接复制

将 `SKILL.md` + `references/` + `scripts/` + `gotchas/` + `evals/` 复制到 `~/.hermes/profiles/<profile>/skills/deep-research/`。

### 依赖

- Python 3.12（scripts 依赖 `~/.local/lib/python3.12/site-packages`）
- API keys 存于 `.env`：Tavily / SerpAPI / Exa / Searlo / TinyFish / Jina（全部免费额度）

## 技能结构

```
deep-research/
├── SKILL.md                        # 核心定义（7 步工作流 + ReAct/CodeAct 双模式）
├── references/
│   ├── sac-search-orchestration.md # SaC 五段式管道模板（核心，Step 2 用）
│   ├── source-evaluation.md        # 来源可信度 A/B/C/D 分级
│   ├── reporting.md                # 报告输出规范
│   ├── failure-handling.md         # F1-F7 故障处理
│   ├── tool-reference.md           # 中文调研专项 + 工具参考
│   ├── research-report-management.md # 入库规则（仅用户明确指定时写盘）
│   └── deep-research-user-patterns.md # 差距分析模式识别
├── scripts/
│   ├── web-fetch.sh                # curl 抓单页
│   ├── scrape-stealth.py           # 反爬三模式（http/stealth/dynamic）
│   └── crawl_site.py               # 全站抓取（crawl4ai）
├── gotchas/                        # 5 个核心 Gotcha（G-001/012/013/014/017）
└── evals/                          # 5 个行为化测试用例
```

## 特性

- **SaC 五段式管道**：引擎选择是决策不是顺序——核心问题用 Tavily，一般问题停免费层，中文用 SerpAPI 百度
- **Jina 统一重排**：所有引擎结果汇合后一次打分，过滤 <0.3，杜绝低质量来源混入
- **Gap Analysis 循环控制**：质量够就停（省 token 省 RPM），有缺口定向补搜（最多 3 轮）
- **确定性独立验证**：Step 6 用规则复核（来源可追溯/A 级 ≥2 独立源/冲突可见），禁用同质 LLM 自评
- **Gotcha 显式检测**：报告末尾必须引用 G-001/G-012/G-013/G-014/G-017 状态
- **入库规则**：仅用户明确说"存知识库"才写盘，否则 `hindsight_retain` 记录教训

## 验证记录

- 2026-08-13 v3.1 全链路实测：优美与崇高（中文语境，触发 G-001/G-012）、AI 营销 Agent 工具对比（n8n vs Zapier 90% 成本差距）
- 5 个 evals 覆盖：LLM 定价时效性、AI 营销工具利益冲突、项目管理软件 SEO 过滤、财报来源验证、企业 AI 采用率统计溯源

## License

MIT
