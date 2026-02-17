"""本地文件记忆适配器：读写 memory/accounts/{account}/ 下 JSON 文件"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .base import MemoryAdapter


def _safe_account(account_name: Optional[str]) -> str:
    name = (account_name or "").strip()
    name = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    return name if name else "default"


class FileAdapter(MemoryAdapter):
    def __init__(self, account_name: Optional[str] = None, project_dir: Optional[Path] = None):
        self.account_name = account_name
        if project_dir is None:
            current_file_dir = Path(__file__).resolve().parent.parent
            project_dir = current_file_dir.parent
        self.base_dir = Path(project_dir) / "memory" / "accounts" / _safe_account(account_name)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._diary_file = self.base_dir / "diary.json"
        self._user_profile_file = self.base_dir / "user_profile.json"
        self._session_temp_file = self.base_dir / "session_temp.json"
        self._npc_learn_progress_file = self.base_dir / "npc_learn_progress.json"

    def get_user_id(self) -> str:
        return _safe_account(self.account_name)

    def _read_json(self, path: Path, default: Dict) -> Dict:
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def _write_json(self, path: Path, data: Dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_diary_data(self) -> Dict[str, Any]:
        default = {"version": "1.0", "last_updated": None, "entries": []}
        return self._read_json(self._diary_file, default)

    def save_diary_data(self, data: Dict[str, Any]) -> None:
        self._write_json(self._diary_file, data)

    def load_user_profile(self) -> Dict[str, Any]:
        default = {
            "version": "1.0",
            "created_at": None,
            "last_updated": None,
            "name": None,
            "age": None,
            "occupation": None,
            "interests": [],
            "preferences": {},
            "goals": [],
            "habits": [],
            "english_level": "beginner",
            "english_level_description": "",
            "other_info": {},
        }
        return self._read_json(self._user_profile_file, default)

    def save_user_profile(self, profile: Dict[str, Any]) -> None:
        self._write_json(self._user_profile_file, profile)

    def load_session_temp(self) -> Optional[Dict[str, Any]]:
        if not self._session_temp_file.exists():
            return None
        try:
            with open(self._session_temp_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def save_session_temp(self, data: Dict[str, Any]) -> None:
        self._write_json(self._session_temp_file, data)

    def clear_session_temp(self) -> None:
        if self._session_temp_file.exists():
            try:
                self._session_temp_file.unlink()
            except Exception:
                pass

    def load_npc_learn_progress(self) -> Dict[str, Any]:
        return self._read_json(self._npc_learn_progress_file, {})

    def save_npc_learn_progress(self, data: Dict[str, Any]) -> None:
        self._write_json(self._npc_learn_progress_file, data)
