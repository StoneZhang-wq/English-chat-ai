#!/usr/bin/env python3
"""
从 data/dialogues.json 生成 data/scene_npc_index.json，并为缺失的小场景自动复制占位图。
程序启动时会自动调用本脚本，无需人工执行；也可在项目根目录手动运行：
  python scripts/build_scene_npc_index.py
"""
import json
import shutil
import sys
from pathlib import Path

# 与 scene_npc_db 保持一致
IMMERSIVE_SCENE_OVERRIDE = {"hospital": "clinic"}
IMAGE_EXTS = (".jpg", ".png", ".jpeg", ".webp", ".svg")


def to_immersive_scene_id(small_scene_id: str) -> str:
    return IMMERSIVE_SCENE_OVERRIDE.get(small_scene_id, small_scene_id)


def ensure_scene_images(root: Path, has_immersive: set) -> None:
    """为 has_immersive 中每个 small_scene_id 确保存在至少一张图，无则复制 default.svg 为 {id}.svg"""
    scenes_dir = root / "app" / "static" / "images" / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    default_svg = scenes_dir / "default.svg"
    if not default_svg.is_file():
        return
    for sid in has_immersive:
        if not sid:
            continue
        has_any = any((scenes_dir / f"{sid}{ext}").is_file() for ext in IMAGE_EXTS)
        if not has_any:
            target = scenes_dir / f"{sid}.svg"
            try:
                shutil.copy2(default_svg, target)
                print(f"  已为小场景 {sid} 生成占位图: {target.name}")
            except OSError as e:
                print(f"  警告: 复制占位图到 {target} 失败: {e}", file=sys.stderr)


def ensure_big_scene_images(root: Path, big_scenes: list) -> None:
    """为大场景确保存在至少一张图，无则复制 default_big.svg 为 big_{id}.svg"""
    scenes_dir = root / "app" / "static" / "images" / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    default_big = scenes_dir / "default_big.svg"
    if not default_big.is_file():
        return
    for b in big_scenes:
        bid = b.get("id") if isinstance(b, dict) else b
        if not bid:
            continue
        name = f"big_{bid}"
        has_any = any((scenes_dir / f"{name}{ext}").is_file() for ext in IMAGE_EXTS)
        if not has_any:
            target = scenes_dir / f"{name}.svg"
            try:
                shutil.copy2(default_big, target)
                print(f"  已为大场景 {bid} 生成占位图: {target.name}")
            except OSError as e:
                print(f"  警告: 复制大场景占位图到 {target} 失败: {e}", file=sys.stderr)


def ensure_npc_images(root: Path, scene_detail_by_immersive_id: dict) -> None:
    """为每个 NPC 确保存在至少一张图，无则复制 default_npc.svg 为 npc_{character}.svg"""
    scenes_dir = root / "app" / "static" / "images" / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    default_npc = scenes_dir / "default_npc.svg"
    if not default_npc.is_file():
        return
    for detail in scene_detail_by_immersive_id.values():
        for n in detail.get("npcs") or []:
            char = n.get("character") or ""
            if not char:
                continue
            name = f"npc_{char}"
            has_any = any((scenes_dir / f"{name}{ext}").is_file() for ext in IMAGE_EXTS)
            if not has_any:
                target = scenes_dir / f"{name}.svg"
                try:
                    shutil.copy2(default_npc, target)
                    print(f"  已为 NPC {char} 生成占位图: {target.name}")
                except OSError as e:
                    print(f"  警告: 复制 NPC 占位图到 {target} 失败: {e}", file=sys.stderr)


def main(root: Path = None):
    if root is None:
        root = Path(__file__).resolve().parent.parent
    dialogues_path = root / "data" / "dialogues.json"
    index_path = root / "data" / "scene_npc_index.json"

    if not dialogues_path.exists():
        print(f"错误: 未找到 {dialogues_path}", file=sys.stderr)
        sys.exit(1)

    with open(dialogues_path, "r", encoding="utf-8") as f:
        dialogues = json.load(f)

    if not isinstance(dialogues, list):
        print("错误: dialogues.json 应为数组", file=sys.stderr)
        sys.exit(1)

    order_map = {"daily": 1, "food": 2, "travel": 3, "shopping": 4, "work": 5, "social": 6}

    # 有 immersive 的 small_scene_id
    has_immersive = set()
    for d in dialogues:
        if d.get("usage") == "immersive":
            sid = d.get("small_scene")
            if sid:
                has_immersive.add(sid)

    # 大场景
    big_seen = {}
    for d in dialogues:
        bid = d.get("big_scene")
        if not bid:
            continue
        if bid not in big_seen:
            big_seen[bid] = {
                "id": bid,
                "name": d.get("big_scene_name", bid),
                "order": order_map.get(bid, 99),
            }
    big_scenes = sorted(big_seen.values(), key=lambda x: x.get("order", 99))

    # 大场景 -> 小场景列表（含 immersive_scene_id）
    small_by_big = {}
    for d in dialogues:
        bid = d.get("big_scene")
        sid = d.get("small_scene")
        if not bid or not sid:
            continue
        if bid not in small_by_big:
            small_by_big[bid] = {}
        if sid not in small_by_big[bid]:
            immersive_id = d.get("immersive_scene_id", to_immersive_scene_id(sid))
            small_by_big[bid][sid] = {
                "id": immersive_id,
                "small_scene_id": sid,
                "name": d.get("small_scene_name", sid),
                "immersive_scene_id": immersive_id,
                "order": len(small_by_big[bid]) + 1,
            }
    small_scenes_by_big = {}
    for bid, smap in small_by_big.items():
        small_scenes_by_big[bid] = sorted(smap.values(), key=lambda x: (x.get("order", 99), x["id"]))

    # 小场景详情（仅含至少有一个 immersive 的小场景）：title, small_scene_id, npcs
    scene_detail_by_immersive_id = {}
    for d in dialogues:
        sid = d.get("small_scene")
        if not sid or sid not in has_immersive:
            continue
        immersive_id = d.get("immersive_scene_id", to_immersive_scene_id(sid))
        if immersive_id not in scene_detail_by_immersive_id:
            scene_detail_by_immersive_id[immersive_id] = {
                "title": d.get("small_scene_name", sid),
                "small_scene_id": sid,
                "npcs": {},
            }
        # NPC：仅在有 learn 对话时才会出现在小场景里；这里从所有 usage 收集 NPC 名，以 immersive 为准取 title
        if d.get("usage") == "immersive":
            scene_detail_by_immersive_id[immersive_id]["title"] = d.get("small_scene_name", sid)
        nid = d.get("npc")
        if nid and d.get("usage") == "learn":
            if nid not in scene_detail_by_immersive_id[immersive_id]["npcs"]:
                scene_detail_by_immersive_id[immersive_id]["npcs"][nid] = {
                    "id": nid,
                    "label": d.get("npc_name", nid),
                    "character": f"{sid}_{nid}",
                }

    # npcs 转为列表，并只保留有 immersive 对话的 NPC
    for immersive_id, detail in scene_detail_by_immersive_id.items():
        sid = detail["small_scene_id"]
        npcs_with_immersive = set()
        for d in dialogues:
            if d.get("small_scene") == sid and d.get("usage") == "immersive":
                npcs_with_immersive.add(d.get("npc"))
        npcs_with_immersive.discard(None)
        npc_list = []
        for nid, info in detail["npcs"].items():
            if nid in npcs_with_immersive:
                npc_list.append(info)
        detail["npcs"] = npc_list
        if not npc_list:
            # 无有效 NPC 则不暴露该场景
            continue

    # 移除无 npcs 的详情
    scene_detail_by_immersive_id = {
        k: v for k, v in scene_detail_by_immersive_id.items() if v.get("npcs")
    }

    index = {
        "has_immersive": list(has_immersive),
        "big_scenes": big_scenes,
        "small_scenes_by_big": small_scenes_by_big,
        "scene_detail_by_immersive_id": scene_detail_by_immersive_id,
    }

    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    # 为小场景、大场景、NPC 确保存在本地图（无则复制对应 default_*.svg）
    ensure_scene_images(root, has_immersive)
    ensure_big_scene_images(root, big_scenes)
    ensure_npc_images(root, scene_detail_by_immersive_id)

    print(f"已生成索引: {index_path}")
    print(f"  大场景: {len(big_scenes)}, 有沉浸的小场景: {len(has_immersive)}, 场景详情: {len(scene_detail_by_immersive_id)}")


if __name__ == "__main__":
    main()
