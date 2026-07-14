# heige-feishu-word 设计说明

## 目标

`heige-feishu-word` 是一个模型无关的飞书云文档交付编译器。它接收 Agent 已整理好的结构化 Document Body，将内容稳定编译为飞书 XML、可编辑 SVG 画板、素材清单和可验证的交付产物。

项目不把业务逻辑写进单一 Agent 的提示词。Claude Code、Codex、OpenCode、Hermes 等平台只保留薄适配层，统一调用同一个 CLI 和同一份 Body 契约。

## 产品边界

### v0.1 负责

1. 校验统一 JSON Body。
2. 生成飞书 XML 富文本。
3. 生成可编辑 SVG 画板。
4. 汇总输入素材并生成 SHA-256 清单。
5. 使用飞书 user 身份创建文档并回读。
6. 导出 PDF 并执行页数、空白页、文字层和文件完整性检查。
7. 使用飞书 bot 身份发送完成通知与真实文件。
8. 提供 Claude Code、Codex、OpenCode、Hermes 的薄 Skill 适配。

### v0.1 不负责

1. 托管式 SaaS。
2. 复杂扫描件 OCR。
3. 任意历史云文档的无损重排。
4. 大规模无人值守批处理。
5. 严格分页的 Slides 输出。该能力保留为后续独立后端。

## 架构

```text
业务材料
  -> Agent 内容预整理
  -> Document Body JSON
  -> 校验器
  -> 飞书 XML 渲染器
  -> SVG 画板渲染器
  -> 本地产物清单
  -> lark-cli 发布
  -> 云文档回读
  -> PDF 导出与 QA
  -> 飞书消息和文件交付
```

核心编译阶段必须是确定性的，且不访问网络。发布、导出和交付是独立阶段，失败时不得删除本地构建产物。

## Document Body v0.1

顶层字段：

```json
{
  "schema_version": "0.1",
  "meta": {
    "title": "文档标题",
    "subtitle": "一句话说明",
    "audience": ["管理者"],
    "status": "MVP 样本",
    "reading_time": "约 3 分钟"
  },
  "theme": "editorial-forest",
  "sections": [],
  "assets": []
}
```

首个里程碑支持以下 section：

1. `callout`：管理结论、风险或提醒。
2. `metrics`：少量关键指标。
3. `table`：精确的行列比较。
4. `grid`：并列卡片或方案原则。
5. `whiteboard_workflow`：流程型 SVG 画板。
6. `actions`：责任明确的行动清单。

所有 section 必须有稳定 `id`。不支持的 section 直接报错，不允许静默忽略。

## 标准样本

第一阶段只交付一个标准样本：《企业 AI 文档交付引擎 MVP 决策简报》。它需要回答：

1. 为什么做。
2. 当前矛盾是什么。
3. 推荐哪种架构。
4. 业务交付链路如何运转。
5. 试点范围、成功指标和风险控制是什么。
6. 下一步由谁负责。

所有数字明确标注为「试点目标」，不能描述成已达成结果。

## 视觉原则

1. 企业管理文档优先，结论先于背景。
2. 原生飞书 block 承担正文，画板只表达流程、架构和复杂关系。
3. 颜色表达语义，不为装饰堆叠颜色。
4. SVG 固定 `1600 x 900`，只使用飞书可解析的原生形状和真实文本。
5. 不使用渐变、滤镜、遮罩、远程字体、脚本或动画。
6. 画板采用 Editorial Forest 与 Raw Grid 的克制组合。

## 质量门槛

标准样本通过条件：

```text
P0 = 0
P1 = 0
P2 <= 2
素材完整率 = 100%
关键文本回读命中率 = 100%
文档和文件可访问率 = 100%
```

必须保留以下证据：

1. 自动化测试输出。
2. SVG 渲染 PNG 和几何检查结果。
3. 飞书文档 URL、document token、revision 和画板 token。
4. 飞书回读 XML。
5. PDF、`pdfinfo`、`pdftotext` 和逐页 PNG。
6. `manifest.json` 与 `qa-report.json`。
7. 完成通知和文件发送的 `message_id`。

## 安全

1. 仓库不提交 Token、app secret、cookie、真实 open_id 或客户材料。
2. 公开样本只使用合成数据。
3. 所有身份显式指定 `--as user` 或 `--as bot`。
4. 发布前执行密钥扫描和暂存文件人工核对。
5. 所有外部写入保留回执，失败时报告准确边界。

