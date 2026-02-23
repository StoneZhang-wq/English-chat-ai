#!/usr/bin/env python3
"""
将 data/dialogues - new.json 合并进 data/dialogues.json：
- 以 dialogue_id 为键，new 中有的则替换原表对应条，缺字段的 new 条不参与替换
- new 内重复 dialogue_id 只保留一份
- 原表有而 new 没有的条保留
- new 有而原表没有的条追加到结果
- 去除 new 中的注释（/* */）后再解析
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIALOGUES_PATH = ROOT / "data" / "dialogues.json"
NEW_PATH = ROOT / "data" / "dialogues - new.json"


def strip_json_comments(text: str) -> str:
    """Remove // and /* */ style comments (for JSON with JS comments)."""
    # Remove /* ... */ (multi-line)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Remove // to end of line
    text = re.sub(r'//[^\n]*', '', text)
    return text


def record_key(r):
    return (r.get("small_scene"), r.get("npc"), r.get("usage"))


def is_valid_record(r) -> bool:
    if not isinstance(r, dict):
        return False
    if not r.get("small_scene") or not r.get("npc") or r.get("usage") is None:
        return False
    content = r.get("content")
    if not isinstance(content, list) or len(content) == 0:
        return False
    for item in content:
        if not isinstance(item, dict) or item.get("role") not in ("A", "B"):
            return False
        if item.get("content") is None:
            return False
    return True


def normalize_record(r: dict) -> dict:
    """Ensure required fields and content item shape; return new dict."""
    out = dict(r)
    content = out.get("content") or []
    normalized_content = []
    for item in content:
        if not isinstance(item, dict):
            continue
        role = item.get("role") or "A"
        if role not in ("A", "B"):
            role = "A"
        normalized_content.append({
            "role": role,
            "content": item.get("content") or "",
            "hint": item.get("hint") if item.get("hint") is not None else ""
        })
    out["content"] = normalized_content
    return out


def main():
    if not NEW_PATH.is_file():
        print(f"Not found: {NEW_PATH}", file=sys.stderr)
        sys.exit(1)
    if not DIALOGUES_PATH.is_file():
        print(f"Not found: {DIALOGUES_PATH}", file=sys.stderr)
        sys.exit(1)

    # Load original
    with open(DIALOGUES_PATH, "r", encoding="utf-8") as f:
        original = json.load(f)
    if not isinstance(original, list):
        print("dialogues.json root must be an array", file=sys.stderr)
        sys.exit(1)

    # Load new (strip comments first; file may be multiple arrays ]\n[ concatenated)
    with open(NEW_PATH, "r", encoding="utf-8") as f:
        raw_new = f.read()
    raw_new = strip_json_comments(raw_new)
    # Remove trailing commas before } or ] (invalid in JSON)
    raw_new = re.sub(r',(\s*[}\]])', r'\1', raw_new)
    # Split by ]  [ to get separate array strings, parse each and concatenate
    parts = re.split(r'\]\s*\[', raw_new)
    new_list = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        if not part.startswith('['):
            part = '[' + part
        if not part.endswith(']'):
            part = part + ']'
        try:
            arr = json.loads(part)
        except json.JSONDecodeError as e:
            print(f"dialogues - new.json part {i+1} parse error: {e}", file=sys.stderr)
            sys.exit(1)
        if isinstance(arr, list):
            new_list.extend(arr)
        elif isinstance(arr, dict):
            new_list.append(arr)

    # Dedupe new by dialogue_id (keep last so later-in-file / latest edit wins), filter valid only
    new_by_id = {}
    for r in new_list:
        if not is_valid_record(r):
            continue
        did = r.get("dialogue_id") or (f"{r.get('small_scene')}-{r.get('npc')}-{r.get('dialogue_set')}")
        new_by_id[did] = normalize_record(r)

    # Build result: for each original, replace if dialogue_id in new; then append new ids not in original
    orig_ids = set()
    result = []
    for r in original:
        if not isinstance(r, dict):
            result.append(r)
            continue
        did = r.get("dialogue_id") or (f"{r.get('small_scene')}-{r.get('npc')}-{r.get('dialogue_set')}")
        orig_ids.add(did)
        if did in new_by_id:
            result.append(new_by_id[did])
        else:
            result.append(r)

    # Append new records that don't exist in original (preserve order by new list order for new ids)
    for r in new_list:
        if not is_valid_record(r):
            continue
        did = r.get("dialogue_id") or (f"{r.get('small_scene')}-{r.get('npc')}-{r.get('dialogue_set')}")
        if did not in orig_ids:
            result.append(normalize_record(r))
            orig_ids.add(did)

    # Write back
    with open(DIALOGUES_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Merged: {len(new_by_id)} unique from new (replaced or added), total records: {len(result)}")


if __name__ == "__main__":
    main()
