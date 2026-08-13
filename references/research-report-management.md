# 调研报告文件管理规范

## 核心规则（强制）

**入库的唯一前提：用户明确说"存知识库"、"保存到 raw/research/" 或类似表述。**

未指定 → 报告**不写盘**，只在聊天中给核心结论，改用 `hindsight_retain` 记录核心教训。

## 入库位置（用户指定后）

统一写：

```
~/wiki/raw/research/主题关键词-YYYY-MM-DD.md
```

并 sync 到 Obsidian 主 vault（`/mnt/d/OneDrive/obsidian-david-knowledge/`）：

```bash
rsync -av ~/wiki/raw/research/ "/mnt/d/OneDrive/obsidian-david-knowledge/raw/research/"
```

## 命名规范

格式：`主题关键词-YYYY-MM-DD.md`（日期放末尾）

示例：
- `优美与崇高调研-2026-08-13.md`
- `AI-Agent框架对比-2026-05-14.md`

**禁止：**
- `调研报告.md`（无主题）
- `2026-05-14-主题.md`（日期在前）

## 不进 raw/wiki 的内容

**判断标准：这份文件 3 个月后还有参考价值吗？没有 → 不进 raw/wiki。**

- ❌ 测试报告、实验记录、验证过程
- ❌ 中间产物、进度跟踪、日志文件
- ❌ 我自主生成的调研报告（未经用户指定）
- ❌ 纯过程性描述（"做了什么"而非"学到了什么"）

以上一律改用 `hindsight_retain` 记录核心教训。
