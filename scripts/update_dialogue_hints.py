#!/usr/bin/env python3
"""
批量把 data/dialogues.json 里角色 B（用户）的 hint 改为「关键词/关键句」格式，
让用户知道该说什么。A 行 hint 保持不变。
"""
import json
import re
from pathlib import Path


def pattern_for(content: str) -> str:
    """根据用户句生成简短句型或关键词，用于 hint 前半部分。"""
    c = content.strip()
    if not c:
        return c
    # 问句：保留句型框架，可变部分用 ... 代替
    if c.endswith("?"):
        # What's for dinner tonight? -> What's for...?
        if re.match(r"What's for \w+", c, re.I):
            return "What's for...?"
        # Where are the plates? / Where's the sugar?
        if c.startswith("Where are"):
            return "Where are...?"
        if c.startswith("Where's ") or c.startswith("Where is "):
            return "Where is/Where's...?"
        # Can I help?
        if re.match(r"Can I help\??", c, re.I):
            return "Can I help?"
        # Are you using ...?
        if c.startswith("Are you using"):
            return "Are you using...?"
        # Did you see ...?
        if c.startswith("Did you see"):
            return "Did you see...?"
        # Do you have ...? / Would you like ...?
        if c.startswith("Do you have"):
            return "Do you have...?"
        if c.startswith("Would you like"):
            return "Would you like...?"
        # How much ...? / How many ...?
        if c.startswith("How much"):
            return "How much...?"
        if c.startswith("How many"):
            return "How many...?"
        # Is this ...? / Are you ...?
        if c.startswith("Is this "):
            return "Is this...?"
        if c.startswith("Are you "):
            return "Are you...?"
        # 其他问句：取首词+...?
        first = c.split()[0] if c.split() else ""
        if first:
            return first + "...?"
    # 短句/回应直接当关键词
    if len(c) <= 25:
        return c
    # 长句取前半+...
    words = c.split()
    if len(words) <= 4:
        return c
    return " ".join(words[:3]) + "..."


def main():
    root = Path(__file__).resolve().parent.parent
    path = root / "data" / "dialogues.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for rec in data:
        for item in rec.get("content", []):
            if item.get("role") != "B":
                continue
            content = item.get("content", "").strip()
            if not content:
                continue
            old_hint = item.get("hint", "")
            # 已是「关键句」形式（含本句或含 ? 的句型）可跳过
            if content in old_hint and "/" in old_hint:
                continue
            pattern = pattern_for(content)
            if pattern == content:
                new_hint = content
            else:
                new_hint = f"{pattern} / {content}"
            item["hint"] = new_hint
            updated += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已更新 {updated} 条 B 行 hint。")


if __name__ == "__main__":
    main()
