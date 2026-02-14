"""
将 oral_training_db.json 中每条记录的 content 按难度调整为规范长度：
- Simple: 4 轮 = 8 条
- Intermediate: 8 轮 = 16 条
- Difficult: 12 轮 = 24 条
超出则截断；不足则用第 1 轮（2 条）重复填满。规范见 .cursor/rules/oral-training-db.mdc。
"""
import json
import os
from pathlib import Path

# 使用基于脚本位置的绝对路径，避免 cwd 导致读写错误
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "oral_training_db.json"
TARGET_LEN = {"Simple": 8, "Intermediate": 16, "Difficult": 24}


def main():
    with open(str(DB_PATH), "r", encoding="utf-8") as f:
        data = json.load(f)

    for rec in data:
        diff = rec.get("difficulty", "Simple")
        target = TARGET_LEN.get(diff, 8)
        content = rec.get("content", [])
        if len(content) > target:
            rec["content"] = content[:target]
            continue
        if len(content) == target:
            continue
        if len(content) < 2:
            continue
        # 用第一轮（2 条）重复填满
        pair = content[:2]
        new_content = []
        while len(new_content) < target:
            new_content.extend(pair)
        rec["content"] = new_content[:target]

    with open(str(DB_PATH), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Done. Content lengths expanded to", TARGET_LEN)


if __name__ == "__main__":
    main()
