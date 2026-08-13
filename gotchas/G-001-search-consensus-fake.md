id: G-001
title: Search-result consensus can be fake
trigger:
  - 多个搜索结果都声称同一个数字
  - 不同网站引用同一数据
  - 搜索结果高度相似
failure:
  - Agent 将 8 个网页视为 8 个独立证据
  - 输出 "8 sources report 42%"
  - 未追溯引用链
root_cause:
  - 这些网页实际上全部转载同一个原始报道
  - 未检查引用链
  - 未识别 syndicated content
symptom:
  - apparent_cross_source_agreement = high
  - actual_source_independence = low
  - 多个 URL 指向同一篇文章
detection:
  - 检查引用链：多个来源是否指向同一原始文章？
  - 检查发布时间：是否为同一时间批量发布？
  - 检查措辞相似度：是否为同一原文复制？
  - **关键指标**：报告中是否标注了"原始来源"或"trace back to"？
correct_action:
  - 将来源聚类到原始 source
  - 按 source family 计数
  - 输出 "8 pages trace back to 1 primary report"
  - **必须显式引用** G-001
bad_example:
  - "中文 9 条结果都支持同一说法，视为 9 个独立来源"
  - → 错误：未追溯引用链（2026-08-13 优美与崇高实测）
good_example:
  - "中文 9 条中百度系（cp.baidu/easylearn/wenku/baike）为同家族，独立中文源实际仅 ~3 个"
  - → 正确：已追溯并标注 source family（2026-08-13 优美与崇高实测）
eval: 2
created: 2026-08-12
status: active
behavior_check:
  - 报告是否检查了引用链？
  - 报告是否标注了原始来源？
  - 报告是否有 "trace back to" 或 "original source" 表述？
  - 报告是否显式引用了 G-001？
  - 如果引用了 G-001，说明已执行此 gotcha
