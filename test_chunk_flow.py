#!/usr/bin/env python3
"""
验证语块流程：场景与推荐语块是否可用。
- 默认使用文件后端（data/*.json），无需 MySQL。
- 若设置 CHUNK_BACKEND=mysql，则使用 MySQL（需自行建表并导入数据）。
用法：python test_chunk_flow.py
"""
import os
import sys

# 项目根目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    if os.environ.get("CHUNK_BACKEND", "").strip().lower() == "mysql":
        try:
            from app.chunk_db import ChunkDatabase
            db = ChunkDatabase(".")
        except ImportError as e:
            print("导入 MySQL 后端失败:", e)
            print("请先安装 pymysql: pip install pymysql")
            return 1
    else:
        from app.chunk_file import ChunkDatabaseFile
        db = ChunkDatabaseFile(".")

    print("1. 可用场景 get_available_scenes() ...")
    try:
        scenes = db.get_available_scenes()
    except Exception as e:
        print("   失败:", e)
        if os.environ.get("CHUNK_BACKEND") == "mysql":
            print("   请确认 MySQL 已启动并已建表、导入语块数据")
        else:
            print("   请确认存在 data/scenes.json")
        return 1
    print(f"   共 {len(scenes)} 个三级场景")
    for s in scenes[:5]:
        print(f"   - {s.get('first_scene')} / {s.get('second_scene')} / {s.get('third_scene')} (label_id={s.get('label_id')})")
    if len(scenes) > 5:
        print(f"   ... 等共 {len(scenes)} 个")

    print("\n2. 一级「日常」下 3 个二级选项 get_second_level_options('日常', 3) ...")
    try:
        opts = db.get_second_level_options("日常", 3)
    except Exception as e:
        print("   失败:", e)
        return 1
    print(f"   共 {len(opts)} 个二级选项")
    for o in opts:
        print(f"   - {o}")

    print("\n3. 推荐语块 get_recommended_chunks(first_scene='日常', second_scene='日常对话', user_id='test_user', limit=5) ...")
    try:
        chunks = db.get_recommended_chunks(
            first_scene="日常",
            second_scene="日常对话",
            user_id="test_user",
            limit=5,
        )
    except Exception as e:
        print("   失败:", e)
        return 1
    print(f"   共 {len(chunks)} 条")
    for c in chunks:
        print(f"   - {c.get('chunk')} (category={c.get('category')})")

    print("\n验证完成：流程可用。")
    return 0


if __name__ == "__main__":
    exit(main())
