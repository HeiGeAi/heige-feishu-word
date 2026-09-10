# 飞书云文档视觉能力研究

研究日期：2026-09-10。产品版本和客户端能力可能继续变化。

## 设计判断

高质量汇报需要让读者迅速找到结论、理解差异、核查依据并采取行动。视觉系统应建立在真实业务关系上。原生正文承担可编辑与搜索，图表承担比较与解释，图后保留数据表、结论和来源。

本轮采用三层输出：

1. `document.xml`：原生正文、语义分栏、表格、SVG 画板。开篇画板表达视觉主题。
2. `preview.html`：离线设计预览，适合选模板和审阅内容。原生飞书字体和块间距以客户端为准。
3. `document.enhanced.xml`：将开篇画板换为可选的 HTML 概览。正文与图表仍保持原生块。HTML 可用性取决于租户和客户端。

顶部 SVG 是正文中的开篇画板，不能称为飞书原生封面资源。

## 能力矩阵

| 能力 | 当前官方接口 | 视觉边界 | 本项目策略 |
| :--- | :--- | :--- | :--- |
| 原生正文 | 标题、段落、富文本、列表、复选项 | 客户端字体和字号体系，不能注入网页 CSS | 保留可读、可搜索和可编辑的正文 |
| 分栏 | grid / column，列宽比例之和为 1 | 移动端布局不能由本地网页结果推断 | 使用短两栏，不把长段落压成三栏 |
| 高亮块 | callout，语义背景与边框颜色 | 子块只支持段落、列表、复选项、行内文本 | 只突出结论、风险和关键提醒 |
| 表格 | table / colgroup / th / td | 背景为预设色名，支持合并、垂直对齐 | 中性表头、精确数据和行动矩阵 |
| SVG 画板 | whiteboard type=svg | 可识别图元转成节点；字体重排，部分特性可能降级 | 用稳定的形状、路径和文本，云端导出后再看 |
| Mermaid | whiteboard type=mermaid | 服务端布局，图例和文本需实际验收 | 此版本不引入新的 Mermaid 运行时 |
| Sheet 图表 | 独立 sheets 图表命令 | 真正绑定数据范围，具有 chart ID | 与当前 SVG 数据快照明确区分 |
| 原生封面 | docs +resource-update | 独立资源和裁切偏移 | 此版本不修改原生封面 |
| HTML5 块 | html5-block + reference_map | 单文件，上限 500KB，高度 auto / viewport | 可选响应式概览；保持原生正文兜底 |

## 图表选择

| 读者的问题 | 组件 | 编码规则 |
| :--- | :--- | :--- |
| 哪个更高，差多少 | 横向条形图 | 共同零基线，负数保留，直接显示数值 |
| 随时间怎样变化 | 折线图 | 保留用户时间顺序，清晰数轴与原始读数 |
| 整体由什么组成 | 环形图 | 非负、合计大于零；原值与百分比并列 |
| 哪一段转化损失大 | 漏斗图 | 顺序非递增，矩形宽度与数值成正比 |
| 距离目标还有多远 | 完成度条 | 0 至 100 的固定基线，明确百分比口径 |
| 何时完成，当前在哪 | 时间轴 | 日期、状态与下一步同时呈现 |
| 怎样取舍 | 决策矩阵 | 同一维度比较，附建议与理由 |

避免截断纵轴的柱状图、3D 饼图、无共同口径的双轴、用装饰性渐变暗示数值差异。空白数据不补造成零；超出布局容量明确报错，要求拆图或调整单位。

## 六套视觉语法

| 主题 | 开篇与节奏 | 适合任务 |
| :--- | :--- | :--- |
| atelier-bone | 象牙纸、细金线、大字号与留白 | 管理层迅速决定下一步 |
| grid-bureau | 蓝色重点、编号侧栏、基线与等宽读数 | 周期经营与精确比较 |
| nocturne-teal | 深黑画板、电青状态点、网格 | 技术项目进展与风险同步 |
| broadsheet | 报头双线、衬线、证据分栏 | 研究、洞察和事实边界 |
| moxi-void | 墨团、宣纸、朱砂落款、宽留白 | 决策讨论与方案权衡 |
| soundwave-wrapped | 粉色开场、电黄高光、波形 | 发布、活动和传播复盘 |

主题 HEX 用于 SVG 与 HTML。原生段落使用单独的色名映射。原生文档不会因此变成任意深色整页皮肤。原生画板字体重排为客户端字体，HTML 字体使用本地 CJK 兜底，不依赖外部字体下载。

## 官方资料

- [Docx XML 语法](https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-xml.md)
- [SVG / Mermaid 画板工作流](https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-whiteboard.md)
- [HTML5 与扩展块](https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-xml-extended-blocks.md)
- [HTML5 资源处理源码](https://github.com/larksuite/cli/blob/dbc1559411d74ef2f208259054a0712241ec9e38/shortcuts/doc/html5_block_resources.go)
- [Sheet 图表接口](https://github.com/larksuite/cli/blob/main/skills/lark-sheets/references/lark-sheets-chart.md)
- [原生封面资源](https://github.com/larksuite/cli/blob/main/skills/lark-doc/references/lark-doc-resource-cover.md)
- [飞书流程图与 UML 帮助](https://www.feishu.cn/hc/zh-CN/articles/980918978289)
- [HeiGe-Design 原创设定集](https://github.com/HeiGeAi/HeiGe-Design)

能力研究与实测结果分开记录。云端通过创建接口不等于像素级保真；XML 回读、画板导出、网页交互、实体手机和 PDF 导出应分别验收。后两项没有执行时应明确写未验证。
