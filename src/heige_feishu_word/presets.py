"""Six complete, synthetic document examples with distinct editorial rhythms.

Every preset is a starting document, including its data and decision narrative.
Callers receive a deep copy so personalizing one document never changes another.
"""

from copy import deepcopy


_DISCLAIMER = (
    "本模板中的组织、业务、数据、结论、负责人和日期均为合成演示内容，"
    "不代表用户真实业务或已经发生的事实。使用前请替换来源、数值、负责人和日期，"
    "并重新核对计算、结论与行动承诺。"
)


def _preset(name, description, theme, title, subtitle, audience, eyebrow, sections):
    return {
        "name": name,
        "description": description,
        "theme": theme,
        "body": {
            "schema_version": "0.2",
            "theme": theme,
            "meta": {
                "title": title,
                "subtitle": subtitle,
                "audience": audience,
                "status": "合成演示 · 可编辑预设",
                "reading_time": "阅读约 4 分钟",
                "eyebrow": eyebrow,
                "disclaimer": _DISCLAIMER,
            },
            "sections": sections,
        },
    }


PRESETS = {
    "executive-brief": _preset(
        "管理层决策简报",
        "先给决策，再看资金与约束。用象牙纸色、资源环图和阶段闸门压缩管理层阅读路径。",
        "atelier-bone",
        "把下一笔投入放在留存",
        "合成演示：澄明工作台第四季度资源配置简报",
        ["经营负责人", "财务负责人", "产品负责人"],
        "管理层简报 · 资源配置",
        [
            {
                "id": "decision", "type": "callout", "title": "今天需要拍板", "tone": "info",
                "body": "建议批准 120 万元季度投入，其中 60 万元用于续费体验。首批仅释放 60 万元，第二批在续费试点完成后评审。请于 9 月 18 日确认预算上限与阶段条件。",
            },
            {
                "id": "numbers", "type": "metrics", "title": "四个决策读数",
                "items": [
                    {"label": "申请预算", "value": "120 万元", "note": "合成场景，覆盖一个季度"},
                    {"label": "留存投入占比", "value": "50%", "note": "60 万元，占总申请的一半"},
                    {"label": "试点续费目标", "value": "82%", "note": "目标值，当前合成基线为 76%"},
                    {"label": "第二批释放额", "value": "60 万元", "note": "条件通过后释放，尚未获批"},
                ],
            },
            {
                "id": "allocation", "type": "chart", "title": "预算向续费体验集中", "kind": "donut",
                "labels": ["续费体验", "新客激活", "数据基础", "预备金"],
                "series": [{"name": "申请金额", "values": [60, 30, 20, 10]}], "unit": "万元",
                "source": "合成演示预算草案，共 120 万元；四项金额相加等于申请总额",
                "insight": "续费体验占 50%，是本轮最大投入项；预备金占约 8.3%，需单独审批使用。",
            },
            {
                "id": "money", "type": "table", "title": "每笔钱换取什么",
                "columns": ["投入项", "季度预算", "验收产物"],
                "rows": [
                    ["续费体验", "60 万元", "续费提醒和价值回顾上线，完成试点复盘"],
                    ["新客激活", "30 万元", "首日引导上线，按注册批次复核激活率"],
                    ["数据基础", "20 万元", "统一续费与激活口径，交付可追溯数据表"],
                    ["预备金", "10 万元", "仅用于已审议变更，逐笔留存用途记录"],
                ],
            },
            {
                "id": "guardrails", "type": "grid", "title": "批准时同时写下边界",
                "items": [
                    {"title": "目标与承诺分开", "body": "82% 是试点目标，不是收益保证。试点只覆盖 200 家合成示例客户，不能直接代表全部客户。"},
                    {"title": "预算与现金分开", "body": "120 万元是投入上限。采购仍按验收节点付款，预备金使用必须重新说明原因。"},
                ],
            },
            {
                "id": "gates", "type": "whiteboard_workflow", "title": "用阶段闸门管理投入",
                "steps": [
                    {"id": "approve", "title": "批准首批", "description": "确认 60 万元首批预算与负责人。"},
                    {"id": "pilot", "title": "交付试点", "description": "完成续费体验改版，记录适用客户范围。"},
                    {"id": "review", "title": "核对证据", "description": "核对续费口径、样本与服务成本变化。"},
                    {"id": "release", "title": "释放第二批", "description": "评审通过后释放余款，未通过则调整方案。"},
                ],
            },
            {
                "id": "alternative", "type": "comparison", "title": "如果不批准本轮申请",
                "options": ["分阶段投入", "维持现状"],
                "criteria": [
                    {"label": "新增预算", "values": ["上限 120 万元，分两批", "不新增专项预算"]},
                    {"label": "续费问题", "values": ["形成可评估试点", "继续由客户成功人工处理"]},
                    {"label": "主要代价", "values": ["挤占部分新功能产能", "无法在本季度验证改版作用"]},
                ],
                "recommendation": "建议分阶段投入。若首批试点无法建立可信的续费基线，则暂停第二批预算评审。",
            },
            {
                "id": "owners", "type": "actions", "title": "会后只追踪三件事",
                "items": [
                    {"owner": "经营负责人（示例）", "action": "确认预算上限与首批批准结果", "due": "2026 年 9 月 18 日"},
                    {"owner": "产品负责人（示例）", "action": "提交试点范围、验收口径与排期", "due": "2026 年 9 月 21 日"},
                    {"owner": "财务负责人（示例）", "action": "建立分批释放和预备金使用台账", "due": "2026 年 9 月 23 日"},
                ],
            },
        ],
    ),
    "operating-review": _preset(
        "经营数据复盘",
        "用趋势、渠道构成与指标口径形成经营闭环。瑞士网格强调数字对齐和可比较性。",
        "grid-bureau",
        "增长继续，渠道需要重配",
        "合成演示：澄明订阅业务上半年经营复盘",
        ["经营团队", "增长团队", "财务团队"],
        "经营复盘 · 半年观察",
        [
            {
                "id": "verdict", "type": "callout", "title": "本期判断", "tone": "success",
                "body": "合成场景中，月度收入从 1 月的 80 万元增至 6 月的 132 万元，增加 65%。6 月自然搜索贡献收入的三分之一。建议先验证该渠道的付费质量，再调整下季度资源。",
            },
            {
                "id": "scorecard", "type": "metrics", "title": "经营读数卡",
                "items": [
                    {"label": "6 月收入", "value": "132 万元", "note": "较 5 月的 120 万元增长 10%"},
                    {"label": "半年累计收入", "value": "622 万元", "note": "六个月合成收入之和"},
                    {"label": "6 月目标完成率", "value": "101.5%", "note": "实际 132 万元，目标 130 万元"},
                    {"label": "自然搜索贡献", "value": "33.3%", "note": "44 万元除以 6 月收入 132 万元"},
                ],
            },
            {
                "id": "trend", "type": "chart", "title": "收入连续六个月增长", "kind": "line",
                "labels": ["1 月", "2 月", "3 月", "4 月", "5 月", "6 月"],
                "series": [{"name": "月度收入", "values": [80, 88, 96, 106, 120, 132]}, {"name": "月度目标", "values": [82, 90, 98, 108, 118, 130]}],
                "unit": "万元", "source": "合成演示月度经营表；金额采用同一收入确认口径，目标在各月开始前设定",
                "insight": "前四个月均低于目标，5 月和 6 月转为高于目标；半年实际 622 万元，目标合计 626 万元。",
            },
            {
                "id": "channels", "type": "chart", "title": "自然搜索贡献最多", "kind": "bar",
                "labels": ["自然搜索", "客户转介绍", "内容合作", "付费投放"],
                "series": [{"name": "6 月收入", "values": [44, 36, 30, 22]}], "unit": "万元",
                "source": "合成演示 6 月渠道表；按首次有效来源唯一归因，四项合计 132 万元",
                "insight": "自然搜索贡献 44 万元，付费投放贡献 22 万元；收入贡献不能直接等同于渠道利润或获客效率。",
            },
            {
                "id": "definitions", "type": "table", "title": "先统一读数口径",
                "columns": ["指标", "本次定义", "核对方式"],
                "rows": [
                    ["月度收入", "当月确认收入，已扣退款", "与月度财务结算表核对"],
                    ["渠道收入", "首次有效来源唯一归因", "分渠道求和后与总收入核对"],
                    ["目标完成率", "实际收入除以当月目标", "132 ÷ 130，保留一位小数"],
                ],
            },
            {
                "id": "diagnosis", "type": "grid", "title": "读数背后的两个问题",
                "items": [
                    {"title": "增长是否带来好客户", "body": "当前图表只有收入，缺少渠道成本、续费和回款周期。补齐这些数据前，不据此扩大投放。"},
                    {"title": "自然搜索能否持续", "body": "需要拆分品牌搜索与非品牌搜索，排查单篇内容带来的短期波动。当前半年趋势不能证明渠道可复制。"},
                ],
            },
            {
                "id": "experiment", "type": "whiteboard_workflow", "title": "下一轮经营验证",
                "steps": [
                    {"id": "segment", "title": "拆分渠道", "description": "按来源和首购月份建立客户批次。"},
                    {"id": "cost", "title": "补齐成本", "description": "纳入投放、人力和优惠成本。"},
                    {"id": "quality", "title": "观察质量", "description": "比较首月使用、退款与后续续费。"},
                    {"id": "allocate", "title": "调整资源", "description": "依据完整证据提出下季度渠道方案。"},
                ],
            },
            {
                "id": "followups", "type": "actions", "title": "下次复盘前补齐证据",
                "items": [
                    {"owner": "数据负责人（示例）", "action": "交付渠道批次与收入归因核对表", "due": "2026 年 7 月 8 日"},
                    {"owner": "增长负责人（示例）", "action": "补齐渠道成本和自然搜索结构", "due": "2026 年 7 月 10 日"},
                    {"owner": "经营负责人（示例）", "action": "基于客户质量决定预算调整幅度", "due": "2026 年 7 月 15 日"},
                ],
            },
        ],
    ),
    "project-pulse": _preset(
        "项目进展战报",
        "深空底与电青状态聚焦交付。把完成度、关键里程碑、依赖和责任人放在同一阅读路径。",
        "nocturne-teal",
        "上线前，先打通最后一环",
        "合成演示：澄明知识台试点项目周报",
        ["项目发起人", "研发团队", "业务验收团队"],
        "项目脉搏 · 第 04 周",
        [
            {
                "id": "pulse", "type": "callout", "title": "当前状态与所需支持", "tone": "warning",
                "body": "核心流程已打通，试点计划仍为 9 月 25 日。权限联调完成度为 60%，是当前主要依赖。需要业务验收团队在 9 月 18 日前确认权限测试名单，否则重新评估试点日期。",
            },
            {
                "id": "delivery", "type": "metrics", "title": "交付读数",
                "items": [
                    {"label": "已验收任务", "value": "29 / 40", "note": "72.5%，任务按条计数，不代表工时完成率"},
                    {"label": "阻断缺陷", "value": "2 项", "note": "均位于权限联调，需在试点前关闭"},
                    {"label": "计划试点团队", "value": "3 个", "note": "合成范围，共 30 名试用者"},
                    {"label": "计划试点日", "value": "9 月 25 日", "note": "条件日期，依赖权限与验收通过"},
                ],
            },
            {
                "id": "completion", "type": "chart", "title": "权限与验收仍在途中", "kind": "progress",
                "labels": ["内容导入", "检索体验", "权限联调", "业务验收"],
                "series": [{"name": "已验收任务比例", "values": [100, 80, 60, 50]}], "unit": "%",
                "source": "合成演示任务表；每个模块 10 项任务，分别已验收 10、8、6、5 项，共 29 项",
                "insight": "内容导入已验收完毕；业务验收为 50%，权限联调为 60%，两者需要共同推进。",
            },
            {
                "id": "milestones", "type": "timeline", "title": "从范围冻结到试点",
                "items": [
                    {"date": "9 月 4 日", "title": "范围冻结", "body": "确认首批三支团队与 40 项验收任务。", "status": "done"},
                    {"date": "9 月 11 日", "title": "主流程演示", "body": "内容导入和检索流程完成内部演示。", "status": "done"},
                    {"date": "9 月 18 日", "title": "权限联调", "body": "名单待确认，两个阻断缺陷尚未关闭。", "status": "risk"},
                    {"date": "9 月 22 日", "title": "业务验收", "body": "验收进行中，优先覆盖权限边界场景。", "status": "active"},
                    {"date": "9 月 25 日", "title": "小范围试点", "body": "仅在阻断缺陷清零、验收通过后启动。", "status": "planned"},
                ],
            },
            {
                "id": "risks", "type": "table", "title": "风险必须有触发条件",
                "columns": ["风险", "触发条件", "应对与负责人"],
                "rows": [
                    ["权限联调延迟", "9 月 18 日名单仍未确认", "项目负责人组织范围调整，重估试点日期"],
                    ["历史内容质量不足", "试点抽查出现关键资料缺失", "内容负责人补齐试点范围资料再复验"],
                    ["验收结论不一致", "同一场景出现冲突判定", "业务负责人确认唯一验收标准"],
                ],
            },
            {
                "id": "handoff", "type": "whiteboard_workflow", "title": "试点前的验收路径",
                "steps": [
                    {"id": "roster", "title": "确认名单", "description": "业务团队确认人员、角色和可见范围。"},
                    {"id": "permissions", "title": "复验权限", "description": "逐项验证授权与越权场景，关闭阻断缺陷。"},
                    {"id": "accept", "title": "业务签收", "description": "按统一清单签收，不以演示代替验收。"},
                    {"id": "pilot", "title": "启动试点", "description": "向三支团队开放，并记录回退条件。"},
                ],
            },
            {
                "id": "scope", "type": "grid", "title": "保持范围清晰",
                "items": [
                    {"title": "本期交付", "body": "完成试点团队的导入、检索、权限与业务验收。试点反馈集中进入一张问题表。"},
                    {"title": "后续再评审", "body": "跨组织共享和移动端专项体验尚未纳入本期验收。试点后依据真实需求再排期。"},
                ],
            },
            {
                "id": "next", "type": "actions", "title": "本周行动",
                "items": [
                    {"owner": "业务负责人（示例）", "action": "确认试点权限名单与统一验收标准", "due": "2026 年 9 月 18 日"},
                    {"owner": "研发负责人（示例）", "action": "关闭两个权限阻断缺陷并提交复验证据", "due": "2026 年 9 月 21 日"},
                    {"owner": "项目负责人（示例）", "action": "根据验收结果确认或调整试点日期", "due": "2026 年 9 月 23 日"},
                ],
            },
        ],
    ),
    "research-digest": _preset(
        "研究洞察速递",
        "报刊式层级先交代问题与证据，再区分观察、解释和局限。适合用户研究与行业信息同步。",
        "broadsheet",
        "用户需要的是可信的答案",
        "合成演示：知识检索访谈与任务测试研究速递",
        ["产品团队", "设计团队", "研究团队"],
        "研究速递 · 证据与边界",
        [
            {
                "id": "question", "type": "prose", "title": "研究问题与样本",
                "paragraphs": [
                    "本例关注一个问题：用户在知识检索中，为什么找到答案后仍然不敢使用？示范研究包含 24 名受访者，每人完成相同的查找、核对和引用任务。",
                    "以下样本、访谈观察和测试结果均为合成内容，用于演示研究文档的证据组织。样本来自三个模拟业务团队，属于便利样本，不构成人群代表性研究。",
                ],
            },
            {
                "id": "finding", "type": "callout", "title": "最值得继续验证的判断", "tone": "info",
                "body": "在这组合成样本中，「找不到来源」被提及最多，共 18 人。建议优先验证来源展示能否降低核对成本。提及频次是问题信号，不能单独证明某项功能会提升使用率。",
            },
            {
                "id": "evidence", "type": "chart", "title": "来源缺失是最常见障碍", "kind": "bar",
                "labels": ["找不到来源", "不确定时效", "术语难理解", "无法直接引用"],
                "series": [{"name": "提及人数", "values": [18, 15, 9, 6]}], "unit": "人",
                "source": "合成演示访谈编码表，样本 24 人；按人去重，同一受访者可提及多类障碍，不能将类别人数相加作为总人数",
                "insight": "18 / 24 人提及来源缺失，15 / 24 人提及时效不明；这是多选频次，不表示因果关系。",
            },
            {
                "id": "traceability", "type": "table", "title": "让结论能追溯到观察",
                "columns": ["观察", "当前解释", "下一步证据"],
                "rows": [
                    ["18 人提及找不到来源", "来源入口可能影响信任判断", "比较有无来源入口时的核对耗时"],
                    ["15 人提及时效不明", "更新时间可能影响答案采纳", "测试日期标签与失效提示的理解情况"],
                    ["6 人提及无法直接引用", "引用操作可能增加额外整理工作", "观察复制后编辑步骤和最终引用正确率"],
                ],
            },
            {
                "id": "limits", "type": "grid", "title": "这些证据还不能回答什么",
                "items": [
                    {"title": "不能推及所有用户", "body": "24 人来自便利样本。岗位、经验和资料类型分布不均，频次不能作为总体发生率。"},
                    {"title": "不能证明功能收益", "body": "研究没有随机分组，也没有长期使用观察。当前只能提出设计假设，不能宣称提升留存或收入。"},
                    {"title": "不能合并多选比例", "body": "同一人可以提及多个障碍。类别比例相加可能超过 100%，因此使用条形图呈现人数。"},
                    {"title": "不能忽略反例", "body": "仍有 6 人未提及来源缺失。下一轮需要理解其已有核对方式和具体任务背景。"},
                ],
            },
            {
                "id": "hypotheses", "type": "comparison", "title": "下一轮先测什么",
                "options": ["来源与时间卡", "一键引用卡"],
                "criteria": [
                    {"label": "主要假设", "values": ["减少寻找来源与确认时效的成本", "减少引用时的整理步骤"]},
                    {"label": "观察指标", "values": ["核对耗时、错误采纳次数", "编辑步骤、引用正确率"]},
                    {"label": "当前证据", "values": ["来源 18 人，时效 15 人，存在重叠", "引用障碍 6 人"]},
                ],
                "recommendation": "先做来源与时间卡的可用性测试，同时保留引用任务作为观察项。判断依据是当前问题覆盖，收益仍需实测。",
            },
            {
                "id": "method", "type": "whiteboard_workflow", "title": "从发现到可验证假设",
                "steps": [
                    {"id": "recruit", "title": "补充样本", "description": "覆盖不同岗位、经验和资料类型。"},
                    {"id": "prototype", "title": "统一任务", "description": "使用相同问题和资料，记录既有操作。"},
                    {"id": "observe", "title": "测试原型", "description": "记录耗时、正确率与受访者解释。"},
                    {"id": "revise", "title": "修订判断", "description": "保留反例，区分观察与设计推断。"},
                ],
            },
            {
                "id": "research-next", "type": "actions", "title": "研究后续",
                "items": [
                    {"owner": "研究负责人（示例）", "action": "整理编码表、反例与样本覆盖缺口", "due": "2026 年 9 月 18 日"},
                    {"owner": "设计负责人（示例）", "action": "制作来源与时间卡原型及任务脚本", "due": "2026 年 9 月 21 日"},
                    {"owner": "产品负责人（示例）", "action": "在下一轮实测后更新功能优先级", "due": "2026 年 9 月 28 日"},
                ],
            },
        ],
    ),
    "decision-memo": _preset(
        "方案决策备忘",
        "水墨留白突出一个待决问题。对照表、成本图和退出条件帮助团队明确取舍。",
        "moxi-void",
        "先接入，再决定是否自建",
        "合成演示：内部知识检索工具选型备忘",
        ["技术负责人", "业务负责人", "采购负责人"],
        "决策备忘 · 可逆选择",
        [
            {
                "id": "context", "type": "prose", "title": "决策范围",
                "paragraphs": [
                    "示例团队希望在 6 周内向 50 名内部用户交付知识检索试点。当前需要在「采购成熟服务」与「自建基础版本」之间选择首期路径。",
                    "本备忘只评估第一年成本、交付速度、权限适配和退出能力。全部金额与工期为合成估算，未取得供应商报价或技术验证结果。",
                ],
            },
            {
                "id": "recommendation", "type": "callout", "title": "建议与成立条件", "tone": "info",
                "body": "建议先开展成熟服务的两周验证，再决定采购。条件是权限、数据导出和关键检索任务全部通过。若任一条件失败，则转入自建范围评审，不直接签订全年合同。",
            },
            {
                "id": "tradeoffs", "type": "comparison", "title": "两条路径的真实取舍",
                "options": ["采购成熟服务", "自建基础版本"],
                "criteria": [
                    {"label": "首期可用时间", "values": ["估算 4 周，取决于集成验证", "估算 10 周，超出 6 周目标"]},
                    {"label": "一年成本", "values": ["估算 36 万元", "估算 54 万元"]},
                    {"label": "权限适配", "values": ["依赖服务能力，必须实测", "可自主实现，需要研发投入"]},
                    {"label": "定制空间", "values": ["受开放接口约束", "可控制交互和数据模型"]},
                    {"label": "退出条件", "values": ["验证全量导出与迁移格式", "持续承担维护和人员交接"]},
                ],
                "recommendation": "首期优先验证采购路径，原因是时间约束更紧。若后续定制需求显著增加，重新比较两年成本和维护能力。",
            },
            {
                "id": "cost", "type": "chart", "title": "采购路径首年估算较低", "kind": "bar",
                "labels": ["服务或开发", "集成迁移", "年度维护"],
                "series": [{"name": "采购成熟服务", "values": [20, 10, 6]}, {"name": "自建基础版本", "values": [36, 8, 10]}],
                "unit": "万元", "source": "合成演示首年成本估算；均包含人力与服务支出，采购合计 36 万元，自建合计 54 万元，未含后续扩容",
                "insight": "采购路径首年估算少 18 万元；这一差额尚未通过报价和工时评审验证，不能直接当作实际节省。",
            },
            {
                "id": "conditions", "type": "table", "title": "把前提写成可检查条件",
                "columns": ["条件", "通过证据", "不通过时"],
                "rows": [
                    ["权限隔离", "全部预设越权场景均被正确拦截", "停止采购评审，复核技术路径"],
                    ["数据可导出", "导出后可以重建文件、来源和权限映射", "不签全年合同，要求补充迁移方案"],
                    ["关键任务可用", "50 条示例任务按统一标准完成人工验收", "记录失败类型，评估修复或缩小范围"],
                    ["成本可承受", "采购与财务确认总成本清单", "重新评估范围、预算与交付目标"],
                ],
            },
            {
                "id": "reversibility", "type": "grid", "title": "为决定保留调整空间",
                "items": [
                    {"title": "先验证关键风险", "body": "两周验证优先覆盖权限、导出和检索任务。展示效果良好不能替代这些条件。"},
                    {"title": "写清重新评估时点", "body": "试点运行一个月后，按真实使用量、人工维护成本和定制需求重新评估。当前建议不自动延伸到长期选型。"},
                ],
            },
            {
                "id": "decision-calendar", "type": "timeline", "title": "决策日程",
                "items": [
                    {"date": "9 月 14 日", "title": "启动验证", "body": "确认任务集、权限场景和成本口径。", "status": "planned"},
                    {"date": "9 月 25 日", "title": "证据评审", "body": "逐项检查条件，记录通过与未通过项。", "status": "planned"},
                    {"date": "9 月 28 日", "title": "选择首期路径", "body": "条件通过则进入采购，否则评审自建范围。", "status": "planned"},
                ],
            },
            {
                "id": "decision-owners", "type": "actions", "title": "谁补齐哪份证据",
                "items": [
                    {"owner": "技术负责人（示例）", "action": "提交权限、导出与任务测试结果", "due": "2026 年 9 月 25 日"},
                    {"owner": "采购负责人（示例）", "action": "取得完整报价与退出条款说明", "due": "2026 年 9 月 25 日"},
                    {"owner": "业务负责人（示例）", "action": "根据评审证据确认首期路径与范围", "due": "2026 年 9 月 28 日"},
                ],
            },
        ],
    ),
    "launch-story": _preset(
        "新品发布与活动复盘",
        "声浪配色制造发布时刻，用漏斗、亮点卡和下一步试验承接热度，避免只展示曝光数字。",
        "soundwave-wrapped",
        "一次发布，让价值被看见",
        "合成演示：澄明工作台春季发布活动复盘",
        ["市场团队", "产品团队", "销售团队"],
        "发布故事 · 从关注到行动",
        [
            {
                "id": "headline", "type": "callout", "title": "本次发布带来了什么", "tone": "success",
                "body": "合成场景中，活动触达 10,000 名可追踪用户，最终带来 240 次有效试用。接下来优先验证注册后的引导体验，观察试用者是否完成关键任务，再决定是否扩大活动投入。",
            },
            {
                "id": "launch-numbers", "type": "metrics", "title": "发布结果四个读数",
                "items": [
                    {"label": "可追踪触达", "value": "10,000 人", "note": "同一用户去重，示例活动完整追踪范围"},
                    {"label": "活动页访问", "value": "3,200 人", "note": "占可追踪触达人数的 32%"},
                    {"label": "活动注册", "value": "800 人", "note": "占活动页访问人数的 25%"},
                    {"label": "有效试用", "value": "240 人", "note": "占注册人数的 30%，占触达人数的 2.4%"},
                ],
            },
            {
                "id": "conversion", "type": "chart", "title": "从触达到有效试用", "kind": "funnel",
                "labels": ["可追踪触达", "活动页访问", "活动注册", "有效试用"],
                "series": [{"name": "去重用户数", "values": [10000, 3200, 800, 240]}], "unit": "人",
                "source": "合成演示活动追踪表；同一追踪批次，后一阶段用户均属于前一阶段，窗口为活动开始后 7 天",
                "insight": "访问到注册转化为 25%，注册到有效试用为 30%；优先验证后者能否通过引导改进，当前漏斗不能解释流失原因。",
            },
            {
                "id": "highlights", "type": "grid", "title": "三个亮点，一句价值",
                "items": [
                    {"title": "答案附带出处", "body": "演示从问题到原始资料的核对过程，让观众看到检索结果如何进入真实工作。"},
                    {"title": "团队共享工作区", "body": "用一个跨部门交接案例展示成员协作、权限与信息更新，减少抽象功能罗列。"},
                    {"title": "可复制的入门任务", "body": "活动页提供完整示范资料与任务清单，让注册者能立即尝试一个有结果的流程。"},
                    {"title": "统一价值表达", "body": "每个演示都回答同一个问题：如何更快找到有出处、能复核、可用于协作的信息。"},
                ],
            },
            {
                "id": "journey", "type": "whiteboard_workflow", "title": "让发布体验接得上使用",
                "steps": [
                    {"id": "story", "title": "真实任务开场", "description": "先呈现一个明确的信息协作难题。"},
                    {"id": "demo", "title": "完成流程演示", "description": "展示问题、操作、结果与核对方式。"},
                    {"id": "try", "title": "复制入门任务", "description": "让观众注册后立即尝试相同流程。"},
                    {"id": "learn", "title": "收集试用反馈", "description": "记录完成情况和卡点，形成后续改进。"},
                ],
            },
            {
                "id": "release-moments", "type": "timeline", "title": "发布节奏与后续窗口",
                "items": [
                    {"date": "4 月 7 日", "title": "任务预告", "body": "以协作难题引出发布主题，开放预约。", "status": "done"},
                    {"date": "4 月 10 日", "title": "产品发布", "body": "发布演示、活动页与可复制入门任务。", "status": "done"},
                    {"date": "4 月 17 日", "title": "追踪窗口结束", "body": "冻结本例 7 天漏斗口径与数据。", "status": "done"},
                    {"date": "4 月 20 日", "title": "试用访谈", "body": "访问完成与未完成任务的两类注册者。", "status": "planned"},
                ],
            },
            {
                "id": "learning", "type": "table", "title": "把热度转成下一轮学习",
                "columns": ["问题", "当前证据", "下一步验证"],
                "rows": [
                    ["为什么注册后没有试用", "800 人注册，240 人完成有效试用", "访谈未完成人群，观察首个任务卡点"],
                    ["哪个亮点带来有效使用", "现有漏斗没有内容版本维度", "补齐演示入口标记，比较后续任务完成"],
                    ["是否值得扩大投放", "尚缺活动总成本与后续留存数据", "补齐成本，观察试用批次的持续使用"],
                ],
            },
            {
                "id": "launch-next", "type": "actions", "title": "下一次发布前完成",
                "items": [
                    {"owner": "产品负责人（示例）", "action": "完成注册后引导的任务观察与改进方案", "due": "2026 年 4 月 24 日"},
                    {"owner": "市场负责人（示例）", "action": "补齐内容入口标记与活动成本表", "due": "2026 年 4 月 24 日"},
                    {"owner": "客户成功负责人（示例）", "action": "整理两类注册者访谈和持续使用信号", "due": "2026 年 4 月 28 日"},
                ],
            },
        ],
    ),
}


def list_presets():
    """Return lightweight catalog records in editorial display order."""
    return [
        {"slug": slug, **{key: value[key] for key in ("name", "description", "theme")}}
        for slug, value in PRESETS.items()
    ]


def get_preset(slug):
    """Return a fresh editable Document Body or explain available preset names."""
    if not isinstance(slug, str) or slug not in PRESETS:
        raise ValueError("unsupported preset: %r; choose %s" % (slug, ", ".join(PRESETS)))
    return deepcopy(PRESETS[slug]["body"])
