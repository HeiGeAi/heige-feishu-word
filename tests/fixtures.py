"""Synthetic Document Body fixtures shared by the behavior tests."""

from copy import deepcopy


STANDARD_BODY = {
    "schema_version": "0.1",
    "meta": {
        "title": "企业 AI 文档交付引擎 MVP 决策简报",
        "subtitle": "统一 Document Body，稳定编译为飞书 XML 与可编辑 SVG。",
        "audience": ["业务负责人", "产品负责人", "技术负责人"],
        "status": "MVP 样本",
        "reading_time": "约 3 分钟",
    },
    "theme": "editorial-forest",
    "sections": [
        {
            "id": "management-decision",
            "type": "callout",
            "title": "管理结论",
            "tone": "success",
            "body": "建议先用统一 Document Body 打通一个标准样本，再扩展模板库。",
        },
        {
            "id": "pilot-metrics",
            "type": "metrics",
            "title": "试点目标",
            "items": [
                {
                    "label": "关键文本回读命中率",
                    "value": "100%",
                    "note": "试点目标",
                },
                {
                    "label": "P0 与 P1 问题",
                    "value": "0",
                    "note": "试点目标",
                },
                {
                    "label": "素材完整率",
                    "value": "100%",
                    "note": "试点目标",
                },
            ],
        },
        {
            "id": "architecture-comparison",
            "type": "table",
            "title": "架构选择",
            "columns": ["方案", "优势", "限制"],
            "rows": [
                ["模型无关编译器", "统一契约，可测试", "需要先定义 Body"],
                ["单 Agent 提示词", "启动快", "难复用，难验收"],
            ],
        },
        {
            "id": "delivery-principles",
            "type": "grid",
            "title": "交付原则",
            "items": [
                {
                    "title": "正文优先",
                    "body": "原生 block 承载正文，画板只表达复杂关系。",
                },
                {
                    "title": "确定性编译",
                    "body": "同一 Body 必须生成可复核的本地产物。",
                },
                {
                    "title": "发布可观察",
                    "body": "外部写入必须保留回执和准确失败边界。",
                },
            ],
        },
        {
            "id": "delivery-workflow",
            "type": "whiteboard_workflow",
            "title": "企业 AI 文档交付链路",
            "steps": [
                {
                    "id": "prepare",
                    "title": "内容预整理",
                    "description": "Agent 提炼结论与证据",
                },
                {
                    "id": "body",
                    "title": "统一 Document Body",
                    "description": "结构化六类 section",
                },
                {
                    "id": "compile",
                    "title": "校验与编译",
                    "description": "生成 XML、SVG 和清单",
                },
                {
                    "id": "publish",
                    "title": "飞书发布与回读",
                    "description": "核对关键文本与画板",
                },
                {
                    "id": "qa",
                    "title": "PDF 质量检查",
                    "description": "检查文件、文字层和页面",
                },
                {
                    "id": "deliver",
                    "title": "消息与文件交付",
                    "description": "返回链接、文件和回执",
                },
            ],
        },
        {
            "id": "next-actions",
            "type": "actions",
            "title": "下一步行动",
            "items": [
                {
                    "owner": "产品负责人",
                    "action": "确认试点范围和验收口径",
                    "due": "第 1 周",
                },
                {
                    "owner": "技术负责人",
                    "action": "实现编译器并保留测试证据",
                    "due": "第 2 周",
                },
            ],
        },
    ],
    "assets": [],
}


def standard_body():
    """Return an isolated copy of the complete six-section sample."""

    return deepcopy(STANDARD_BODY)


def minimal_body(section_type="callout"):
    """Return the smallest Body needed to exercise top-level validation."""

    return {
        "schema_version": "0.1",
        "meta": {"title": "最小测试文档"},
        "theme": "editorial-forest",
        "sections": [
            {
                "id": "only-section",
                "type": section_type,
                "title": "唯一章节",
                "body": "合成测试内容",
            }
        ],
        "assets": [],
    }


def workflow_section():
    """Return an isolated workflow section from the standard sample."""

    body = standard_body()
    return next(
        section
        for section in body["sections"]
        if section["type"] == "whiteboard_workflow"
    )
