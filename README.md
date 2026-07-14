# heige-feishu-word

把 Agent 整理好的结构化内容，确定性地编译为飞书云文档 XML 与可编辑 SVG 画板。

`heige-feishu-word` 面向企业文档交付场景。它用统一的 Document Body 隔离不同 Agent 的输出差异，让 Codex、Claude Code、OpenCode、Hermes 等工具可以围绕同一份内容契约工作。

> 当前版本：`v0.1.0-alpha`。已经实现本地校验与编译，飞书发布、PDF 导出和消息投递仍属于后续集成层。请勿把当前版本直接用于无人值守的生产发布。

## 为什么需要它

普通 Agent 能写出内容，却不一定能稳定交付一份可读、可编辑、可核验的飞书文档。这个项目把交付过程拆成两个边界：

1. Agent 负责理解业务材料，并生成结构化 Document Body。
2. 编译器负责严格校验 Body，并生成稳定的飞书 XML、SVG 画板和产物清单。

不支持的字段和组件会明确报错，不会静默丢失内容。

## 当前能力

* 校验 `Document Body v0.1`。
* 支持 `callout`、`metrics`、`table`、`grid`、`whiteboard_workflow`、`actions` 六类组件。
* 生成飞书云文档 XML。
* 生成固定 `1600 × 900`、不含脚本和远程资源的 SVG 画板。
* 生成带 SHA-256 的 `manifest.json`。
* 原子化写入构建目录，失败时不留下半成品。
* 纯 Python 标准库实现，运行时无第三方依赖。

当前尚未实现素材导入、飞书账号认证、云文档发布、PDF 导出和多 Agent 薄适配层。相关设计保留在 `docs/` 中，实际能力以测试和源码为准。

## 快速开始

要求 Python 3.9 或更高版本。

```bash
git clone https://github.com/HeiGeAi/heige-feishu-word.git
cd heige-feishu-word
python3 -m pip install --upgrade pip
python3 -m pip install .
```

校验标准样本：

```bash
heige-feishu-word validate examples/standard-sample/body.json
```

编译产物：

```bash
heige-feishu-word compile examples/standard-sample/body.json --output build/standard-sample
```

输出目录包含：

```text
build/standard-sample/
├── source.body.json
├── document.xml
├── manifest.json
└── boards/
    └── delivery-workflow.svg
```

项目使用标准 `pyproject.toml` 构建。安装前请使用较新的 `pip`，系统自带的旧版本可能无法正确识别包元数据。如果需要 editable install：

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

## Document Body 示例

```json
{
  "schema_version": "0.1",
  "meta": {
    "title": "企业 AI 文档交付引擎 MVP 决策简报",
    "subtitle": "用统一 Body 连接 Agent、飞书文档与可编辑画板"
  },
  "theme": "editorial-forest",
  "sections": [
    {
      "id": "decision",
      "type": "callout",
      "title": "管理结论",
      "tone": "success",
      "body": "建议进入 MVP 试点。"
    }
  ],
  "assets": []
}
```

完整样本位于 [`examples/standard-sample/body.json`](examples/standard-sample/body.json)。

## 在 Agent 中调用

任何能够执行本地命令的 Agent 都可以使用同一套接口：

```bash
heige-feishu-word validate /absolute/path/to/body.json
heige-feishu-word compile /absolute/path/to/body.json --output /absolute/path/to/output
```

建议让 Agent 只生成 Body，不直接拼接飞书 XML。这样可以把内容推理和确定性渲染分开，也便于做版本控制、自动测试和失败重试。

## 开发与测试

无需安装项目即可运行测试：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

项目遵循以下安全边界：

* 不提交 Token、app secret、cookie、真实 open_id 或客户材料。
* 公开样本只使用合成数据。
* SVG 禁止脚本、图片节点、滤镜、遮罩和远程字体。
* 未支持的输入必须失败，不得静默降级。

## 路线图

* `executive-brief` 双页管理简报主题。
* 飞书云文档发布与回读。
* 原生画板创建与几何质量检查。
* PDF 导出、页数与文字层检查。
* Codex、Claude Code、OpenCode、Hermes 薄适配层。
* 素材清单、附件上传和真实文件投递。

## 参与贡献

提交问题或代码前，请阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)。安全问题请按 [`SECURITY.md`](SECURITY.md) 中的方式报告。

## 许可证

[MIT License](LICENSE)
