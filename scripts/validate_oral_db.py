# -*- coding: utf-8 -*-
"""
口语训练数据库 v1.1 自动校验（可与生成工具配合使用）。
校验项：1) 轮数/条数  2) hint → core 覆盖（可选）  3) Unit 差异（需人工抽检）
"""
import json
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "oral_training_db.json"
TARGET_LEN = {"Simple": 8, "Intermediate": 16, "Difficult": 24}


def main():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    errors = []
    for rec in data:
        diff = rec.get("difficulty", "")
        content = rec.get("content", [])
        expected = TARGET_LEN.get(diff)
        if expected is not None and len(content) != expected:
            errors.append(f"{rec.get('dialogue_id')}: content 条数 {len(content)}，应为 {expected}")
    if errors:
        for e in errors:
            print(e)
        print(f"\n共 {len(errors)} 条不符合 v1.1 轮数规范。")
        sys.exit(1)
    print(f"轮数校验通过：共 {len(data)} 条记录，Simple=8 条、Intermediate=16 条、Difficult=24 条。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
