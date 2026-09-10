# heige-feishu-word

**为飞书白页设计的汇报模板与图表编译器。**

把结构化内容编译成可编辑的飞书正文、紧凑的数据图表和离线预览。六套模板分别服务管理简报、经营复盘、项目同步、研究速递、方案评审与发布提案，用主辅双色、类别色和配套浅底组织信息。

文档从标题、简要信息和核心判断开始，接上 KPI、图表、正文与行动。完整数据和流程说明收在文末，来源留在图旁。读者可以先读主线，再核对依据。

当前开发版本：`v0.2.0a2`。本地编译不需要账号、不联网，运行时只用 Python 标准库。飞书写入由独立的 Lark CLI 完成。

## 六套白页模板

| 模板 | 视觉主题 | 沟通重点 |
| :--- | :--- | :--- |
| `executive-brief` | 海蓝鎏金简报 | 决策建议、预算配置与批准条件 |
| `operating-review` | 蓝橙经营复盘 | 收入趋势、目标偏差与渠道贡献 |
| `project-pulse` | 孔雀琥珀简报 | 完成度、里程碑与交付依赖 |
| `research-digest` | 莓果研究速递 | 核心发现、证据与研究局限 |
| `decision-memo` | 朱砂石青备忘 | 同口径方案比较、成本与退出条件 |
| `launch-story` | 洋红明黄提案 | 发布亮点、转化漏斗与后续行动 |

六套主题均使用白色阅读底，配有八种类别色及对应浅色。章节交替使用主辅色，首项 KPI 以主色实底和白字突出，其他指标采用配套浅底与深色读数；图表和流程阶段也通过颜色建立对应关系。白页可以承载丰富配色，同时让正文与图形保持连续的阅读背景。

颜色表示类别和层级。成功、提醒或风险含义来自显式的 `callout.tone` 与 `timeline.status` 字段，任意 KPI 的颜色都不代表增长、下降或达标。标签、数值、编号标记和折线线型始终保留，读者辨识信息不只依赖颜色。

模板使用明确标注的合成演示数据。正式汇报前请替换数值、口径、来源、日期和负责人，并重新核对图表结论。可直接使用 [六份可编辑 JSON 样例](examples/presets)。

下方为生成的白页离线预览截图。原生飞书字体、块间距和画板转换效果以目标客户端为准。

| 海蓝鎏金简报 | 蓝橙经营复盘 |
| :--- | :--- |
| ![海蓝鎏金简报白页配色预览](assets/previews/executive-brief.png) | ![蓝橙经营复盘白页配色预览](assets/previews/operating-review.png) |
| 孔雀琥珀简报 | 莓果研究速递 |
| ![孔雀琥珀简报白页配色预览](assets/previews/project-pulse.png) | ![莓果研究速递白页配色预览](assets/previews/research-digest.png) |
| 朱砂石青备忘 | 洋红明黄提案 |
| ![朱砂石青备忘白页配色预览](assets/previews/decision-memo.png) | ![洋红明黄提案白页配色预览](assets/previews/launch-story.png) |

## 三分钟开始

Python 3.9 或更高版本。

```bash
git clone https://github.com/HeiGeAi/heige-feishu-word.git
cd heige-feishu-word
python3 -m pip install .

# 查看沟通场景与视觉主题
heige-feishu-word presets
heige-feishu-word themes

# 创建可编辑的结构化示范正文
heige-feishu-word init executive-brief --output my-report.json

# 替换 my-report.json 中的业务内容后编译
heige-feishu-word compile my-report.json --output build/my-report

# 生成六套样本与离线目录
heige-feishu-word gallery --output build/gallery
```

打开 `build/gallery/index.html` 选择样本，或打开 `build/my-report/preview.html` 查看报告。不安装时，可将命令入口 `heige-feishu-word` 替换为 `PYTHONPATH=src python3 -m heige_feishu_word`。

同一份内容可以换主题，以下示例改用孔雀琥珀主题：

```bash
heige-feishu-word compile my-report.json --theme nocturne-teal --output build/my-report-teal
```

主题 ID 保持稳定，`nocturne-teal` 等 ID 现在也对应白页适配版。0.1 输入和 `editorial-forest` 标识继续可用，采用新的白页呈现。

## 图表与组件

支持横向条形、折线、环形、转化漏斗、目标完成度五类数据图表，以及结论高亮、KPI 指标组、原生表格、两栏内容、流程画板、行动清单、段落、里程碑时间轴和方案比较。

单系列条形图按类别着色，多系列条形图与折线图保持同一系列的颜色一致。环形、漏斗和完成度条沿用类别色；流程阶段使用配套浅底、浓色编号和小箭头。颜色不会改变输入顺序、数值大小或图形比例。

每张数据图必须提供来源与解读。正文保留图旁来源和核心判断，完整数据表集中放在飞书文末附录，仍可编辑与搜索。离线预览使用图下可展开的 `details` 保存这些明细，方便边看边核对；这项展开交互不会被宣称为飞书原生组件。

KPI 画板适合一至八项短指标。合法内容超出可读画板容量时，保留为当前章节内的完整原生表格，不截断数据，也不再重复追加同一组指标明细。

图表会检查负数适用范围、零基线、占比、漏斗顺序、百分比范围与文字容量。非法数据和无法容纳的文字会明确报错，不静默删减。下面是一张使用合成数据的条形图：

```json
{
  "schema_version": "0.2",
  "theme": "atelier-bone",
  "meta": {
    "title": "经营复盘",
    "subtitle": "先看变化，再决定下一步",
    "eyebrow": "MONTHLY REVIEW",
    "disclaimer": "合成演示数据，使用前替换。"
  },
  "sections": [{
    "id": "channels",
    "type": "chart",
    "title": "渠道收入比较",
    "kind": "bar",
    "labels": ["产品内转化", "内容渠道", "伙伴推荐"],
    "series": [{"name": "收入", "values": [72, 48, 31]}],
    "unit": "万元",
    "source": "合成演示数据",
    "insight": "产品内转化收入最高，后续需结合成本评估投入。"
  }],
  "assets": []
}
```

此例只有图表，不含 KPI 指标组，因此不会生成 HTML 增强版。

[完整内容契约与产物说明](docs/visual-system/README.md) · [飞书视觉能力研究与官方来源](docs/research/feishu-visual-capabilities.md) · [验收范围与记录](docs/visual-system/validation.md)

## 编译后得到什么

以下以包含指标、环形图和工作流的管理简报为例：

```text
build/my-report/
├── source.body.json
├── document.xml
├── document.enhanced.xml
├── preview.html
├── theme.json
├── manifest.json
├── widgets/
│   └── overview.html
├── boards/
│   ├── numbers.svg
│   ├── allocation.svg
│   └── gates.svg
└── standalone/
    └── allocation.svg
```

- **`document.xml`**：原生标题、段落、表格、复选项与白底 SVG 画板。数据和流程明细位于文末附录。
- **`document.enhanced.xml`**：仅在正文的第一个 `metrics` 能生成 KPI 画板时生成。把这个画板替换为纯指标 HTML，原生标题、metadata、其他画板与明细保持各自位置。`widgets/overview.html` 同条件生成，使用前需验证目标租户与客户端支持。
- **`boards/`**：供文档嵌入的紧凑白底画板。数据图为 1600×600；KPI 高度为 380 或 720，取决于指标行数；工作流高度随内容调整。
- **`standalone/`**：每张数据图另存一份 1600×900 的独立分享版，包含完整标题、来源与解读，适合脱离文档查看。
- **`preview.html`**：白页阅读预览，支持数据展开、图表原尺寸查看、放大、适应宽度和打印。窄屏图块可左右滑动，页面自身保持自适应。
- **`manifest.json`**：记录文件路径、大小与 SHA-256。编译成功后仍标记云端尚未发布。

`meta.eyebrow` 只是一行文档标记，不再触发开篇海报或增强产物。上述 SVG 尺寸是生成文件的坐标尺寸，不能直接视为飞书客户端中的展示高度。

没有 `metrics`，或第一个指标组因视觉容量回退为原生表格时，不生成增强 XML 与 HTML。其他数据图和符合容量的 KPI 画板仍按内容生成。

输出目录仅在旧产物完整且未被用户修改时允许替换；有新增文件、手动修改或软链接时拒绝覆盖。

## 写入飞书

安装并登录 [官方 Lark CLI](https://github.com/larksuite/cli)，在构建目录执行：

```bash
cd build/my-report
lark-cli docs +create --as user --doc-format xml --content @./document.xml
```

若当前构建包含增强版，可在同一目录创建，确保 HTML 相对路径正确：

```bash
lark-cli docs +create --as user --doc-format xml --content @./document.enhanced.xml
```

选择其中一个版本创建。记录返回的文档 URL，检查 `warnings`，随后回读：

```bash
lark-cli docs +fetch --as user --doc '<创建返回的文档URL>' --detail full
```

再查看实际文档并导出画板预览，核对中文字形、数值、折行、连线与块间距。HTML 增强内容需检查 `reference_map` 中的实际 HTML，单独的块占位不代表内容完整。不要为了重试回读而重复创建已经成功的文档。

## 明确的能力边界

原生正文使用飞书的字体、间距与预设色名，例如 `blue`、`orange`、`green`、`purple` 及允许的浅色变体。项目将主辅色与类别色映射到这些色名，以保持相近色系；精确 HEX 色板和构图作用于 SVG 与 HTML。原生 Docx 的预设色名不能保证与图形颜色逐像素相同，也不接受任意网页 CSS 皮肤。

主题的亮 `secondary` 用于图形强调；`palette[1]` 提供同色系更深的第二类别色，适合可读文字和数据系列。二者用途不同，不能把亮辅助色直接当作白底小字颜色。

**SVG 图表是输入快照。修改飞书附录中的数据表不会自动重绘图表。** 更新数据时应修改源 JSON，重新编译并同步相关内容。真正绑定 Sheet 数据源的图表属于独立能力，本版尚未集成。

本版没有内置账号认证、无人值守发布、PDF 导出、外部素材导入、实时 Sheet 连接器或原生封面设置。浏览器窄屏模拟、飞书桌面客户端、实体手机和 PDF 导出需要分别验证。编译、lint 与接口回读通过，也不能代替实际阅读和视觉验收。

## 开发与测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

运行时无第三方依赖。浏览器验收脚本使用可选 Playwright，检查桌面与窄屏、资源、交互和 SVG 文字边界，不属于用户安装依赖。

```bash
# 先安装可选 playwright 与 Chromium，再运行
node scripts/check_browser.cjs build/gallery build/browser-evidence
# 非默认安装位置可通过 PLAYWRIGHT_MODULE 指向 playwright 模块
```

公开样本只含合成数据。不提交 Token、Cookie、app secret、个人 open_id、真实客户材料或私人云端回执。SVG 禁止脚本、远程资源与不受支持的滤镜。更多约定见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [SECURITY.md](SECURITY.md)。

视觉设定适配自 [HeiGe-Design](https://github.com/HeiGeAi/HeiGe-Design)（MIT）：atelier-bone、grid-bureau、nocturne-teal、broadsheet、moxi-void、soundwave-wrapped。此项目将这些设定转化为飞书白页中的主辅色、类别色、配套浅底与排版规则。图表、内容契约与编译代码均在本仓库。

[MIT License](LICENSE)
