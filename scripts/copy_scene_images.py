"""One-off: 从指定目录复制场景 PNG 到 app/static/images/scenes/。路径请使用纯英文避免编码问题。"""
import os
import sys
import shutil
from pathlib import Path

# 保证从项目根可 import app
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.scene_npc_db import _scenes_images_dir

# 源目录：优先从环境变量 SCENE_IMAGES_SOURCE 读取（建议使用纯英文路径）
# 例：set SCENE_IMAGES_SOURCE=C:\path\to\assets  或  export SCENE_IMAGES_SOURCE=/path/to/assets
_ASSETS_ENV = os.environ.get("SCENE_IMAGES_SOURCE", "").strip()
ASSETS = Path(_ASSETS_ENV) if _ASSETS_ENV else None
SCENES = ["home", "community", "park", "hospital", "bank", "cafe", "restaurant", "fast_food", "snack_shop"]


def main():
    dest = _scenes_images_dir()
    dest.mkdir(parents=True, exist_ok=True)
    print("Target dir (same as backend):", dest)
    if not ASSETS or not ASSETS.is_dir():
        print("Source dir not set or missing. Set env SCENE_IMAGES_SOURCE to folder containing scene PNGs.")
        print("Example (Windows): set SCENE_IMAGES_SOURCE=C:\\Users\\You\\assets")
        print("Example (Unix):    export SCENE_IMAGES_SOURCE=/home/you/assets")
        return
    for name in SCENES:
        src = ASSETS / f"{name}.png"
        if src.is_file():
            shutil.copy2(src, dest / f"{name}.png")
            print("  Copied", name + ".png")
        else:
            print("  Skip (not found):", src)
    pngs = list(dest.glob("*.png"))
    print("PNG count in dir:", len(pngs))


if __name__ == "__main__":
    main()
