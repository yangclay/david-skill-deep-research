# 调研报告文件管理规范

## 核心规则（2026-08-24 反转：对话优先）

**默认：完整结果发对话框（结论+来源 URL+矛盾+可信度），不写盘。**

写盘唯一触发：Clay 看完对话版**主动说**"有价值/存一份/出报告/存知识库"。判断权在用户，agent 不预判。

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
- `AI营销Agent工具对比-2026-08-13.md`

**禁止：**
- `调研报告.md`（无主题）
- `2026-08-13-主题.md`（日期在前）

## 不进 raw/wiki 的内容

**判断标准：这份文件 3 个月后还有参考价值吗？没有 → 不进 raw/wiki。**

- ❌ 测试报告、实验记录、验证过程
- ❌ 中间产物、进度跟踪、日志文件
- ❌ 我自主生成的调研报告（未经用户指定）
- ❌ 纯过程性描述（"做了什么"而非"学到了什么"）

以上一律改用 `hindsight_retain` 记录核心教训。
