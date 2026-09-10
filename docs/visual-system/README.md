# 视觉系统与内容契约

设计来源：HeiGeAi/HeiGe-Design，MIT。六个主题保留原设定集的核心颜色、版式语法与签名。飞书原生正文不支持所有网页 token，因此分别导出精确主题 token 和原生颜色映射。

## 输入

保留 Document Body 0.1 的六种组件。0.2 新增 `prose`、`chart`、`timeline` 和 `comparison`；两版输入均校验支持的字段，未知字段不静默丢弃。省略主题使用原有 `editorial-forest`，拼错主题明确报错。

`meta` 可选 `eyebrow`、`disclaimer`。填写 `eyebrow` 会生成开篇画板和 HTML 增强概览。免责声明由内容作者提供，编译器不自动编造业务状态或数字属性。

`chart` 必填 `id`、`type`、`title`、`kind`、`labels`、`series`、`source`、`insight`，可选 `unit`。`series` 中包含 `name` 与数值列表 `values`。

```json
{
  "id": "channel-revenue",
  "type": "chart",
  "title": "渠道收入比较",
  "kind": "bar",
  "labels": ["产品内转化", "内容渠道", "伙伴推荐"],
  "series": [{"name": "收入", "values": [72, 48, 31]}],
  "unit": "万元",
  "source": "合成演示数据，使用前替换",
  "insight": "产品内转化收入最高，下一步需联合成本判断投入。"
}
```

图表最多八个标签。条形图最多两组，折线图最多三组，其余单组。折线图至少两点。数据、名称长度、空值、负值规则、NaN 和 Infinity 均校验。`progress` 数值为百分比 0 至 100。环形图与漏斗图禁止负数，漏斗顺序必须非递增。具体文本容量由字段级错误提示。

`prose` 使用 `paragraphs` 字符串列表。`timeline` 使用 `items`，每项含 `date`、`title`、`body`、`status`，状态为 `done`、`active`、`planned`、`risk`。`comparison` 使用两至三个 `options`，`criteria` 中每项包含 `label` 和同长度 `values`，附必填 `recommendation`。

## 产物

每次编译导出原文、XML、SVG、离线预览、主题 token 与带 SHA-256 的清单。默认无网络、无第三方 Python 运行依赖。构建时不会创建飞书文档。

输出目录仅在上次产物未被修改、没有用户新增文件时允许替换。生成先在临时目录完成；发布到最终目录失败会恢复旧目录。用户修改过的输出会明确拒绝覆盖。

## 不应作出的承诺

- SVG 画板是当前输入的数据快照，修改飞书数据表不会重绘图表。
- HTML 预览不能证明原生 Docx 的字体、间距或手机效果。
- 所有场景都适合视觉浓度很高的样式。正式制度、公文、长篇证据材料应优先阅读效率。
- 所有 SVG 特性都可编辑。本项目只使用受约束的图元，仍需云端读回验收。
- 本轮已交付实时 Sheet 集成、原生封面、PDF 导出或自动发布。
