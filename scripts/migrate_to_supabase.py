#!/usr/bin/env python3
"""
将 memory/accounts/* 下的用户记忆导入到 Supabase。
需先执行 docs/SUPABASE_SCHEMA.sql 建表。脚本会自动加载项目根目录 .env 中的
  SUPABASE_URL、SUPABASE_SERVICE_ROLE_KEY（也可在运行前用环境变量覆盖）。

导入内容：user_profile、npc_learn_progress（不导入 session_temp；已移除 diary）。

用法（项目根目录）：
  python scripts/migrate_to_supabase.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 加载项目根目录的 .env，便于直接运行脚本时读取 SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("请设置环境变量 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

    from supabase import create_client
    client = create_client(url, key)

    accounts_dir = ROOT / "memory" / "accounts"
    if not accounts_dir.is_dir():
        print(f"未找到目录: {accounts_dir}")
        sys.exit(0)

    for account_dir in sorted(accounts_dir.iterdir()):
        if not account_dir.is_dir():
            continue
        user_id = account_dir.name
        profile_path = account_dir / "user_profile.json"
        npc_path = account_dir / "npc_learn_progress.json"

        profile = {}
        if profile_path.exists():
            try:
                profile = json.loads(profile_path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"  [{user_id}] 读取 user_profile 失败: {e}")
        npc_data = {}
        if npc_path.exists():
            try:
                npc_data = json.loads(npc_path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"  [{user_id}] 读取 npc_learn_progress 失败: {e}")

        try:
            client.table("users").upsert({
                "id": user_id,
                "name": profile.get("name") or user_id,
                "profile": profile,
            }, on_conflict="id").execute()
            client.table("user_npc_learn_progress").upsert({
                "user_id": user_id,
                "data": npc_data,
            }, on_conflict="user_id").execute()
            print(f"  OK: {user_id}")
        except Exception as e:
            print(f"  FAIL: {user_id} -> {e}")

    print("迁移完成。")

if __name__ == "__main__":
    main()
