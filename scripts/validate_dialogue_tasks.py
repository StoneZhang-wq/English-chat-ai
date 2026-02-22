#!/usr/bin/env python3
"""
校验 data/dialogues.json 中 user_goal / user_goal_a 是否与角色约定一致。

约定：A = NPC，B = 学习者
- user_goal  应描述 B（学习者）要完成的任务
- user_goal_a 应描述 A（NPC）要完成的任务

若某条中任务描述反了（如 user_goal 里写的是 NPC 的事），本脚本会标出供人工核对。
"""
import json
import sys
from pathlib import Path

# 常见 NPC 角色关键词（出现在 user_goal 里且无「学习者」时可能写反）
NPC_ROLE_KEYWORDS = (
    "快递员", "外卖员", "服务员", "咖啡师", "收银员", "店员", "医生", "护士",
    "保安", "路人", "邻居", "家人", "室友", "迎宾", "点餐员", "配餐员",
    "柜员", "大堂经理", "挂号", "收费员", "导购", "理发师", "前台", "同事",
    "领导", "下属", "面试官", "顾客"
)

# 学习者相关关键词（user_goal 里应有；user_goal_a 里若作为「要完成者」则可能反了）
LEARNER_KEYWORD = "学习者"


def load_dialogues(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def check_one(idx: int, d: dict) -> list[str]:
    issues = []
    ug = (d.get("user_goal") or "").strip()
    uga = (d.get("user_goal_a") or "").strip()
    small = d.get("small_scene", "")
    npc = d.get("npc", "")
    usage = d.get("usage", "")

    # user_goal 应为 B（学习者）的任务：通常含「学习者」
    if ug and LEARNER_KEYWORD not in ug:
        for kw in NPC_ROLE_KEYWORDS:
            if kw in ug and "作为" in ug:
                issues.append(f"user_goal 可能写成了 A 的任务（含「{kw}」且无「学习者」）")
                break

    # user_goal_a 应为 A（NPC）的任务：不应以「学习者」为主语做任务
    if uga and LEARNER_KEYWORD in uga:
        if "要完成" in uga or "完成" in uga:
            issues.append("user_goal_a 中出现了「学习者」且带任务描述，可能写成了 B 的任务")

    # 可选：首句是否为 A（NPC）先开口
    content = d.get("content") or []
    if content and content[0].get("role") == "B":
        issues.append("首句为 B 开口，建议通常由 A（NPC）先开口")

    return issues


def main():
    root = Path(__file__).resolve().parent.parent
    path = root / "data" / "dialogues.json"
    if not path.is_file():
        print(f"未找到 {path}", file=sys.stderr)
        sys.exit(1)

    dialogues = load_dialogues(path)
    print(f"共 {len(dialogues)} 条对话，开始校验任务字段…\n")

    total_issues = 0
    for idx, d in enumerate(dialogues):
        issues = check_one(idx, d)
        if not issues:
            continue
        total_issues += 1
        ident = d.get("dialogue_id") or d.get("small_scene", "") + "-" + (d.get("npc") or "")
        print(f"[{idx}] {ident} (usage={d.get('usage')})")
        for i in issues:
            print(f"  - {i}")
        print()

    if total_issues == 0:
        print("未发现明显任务写反或首句异常。")
    else:
        print(f"共 {total_issues} 条存在疑似问题，请人工核对后按需修改 data/dialogues.json。")
    sys.exit(0 if total_issues == 0 else 0)  # 仍退出 0，仅作提示


if __name__ == "__main__":
    main()
