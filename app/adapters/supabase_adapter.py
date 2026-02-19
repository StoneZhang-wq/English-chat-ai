"""Supabase 记忆适配器：读写 users、user_profile、user_npc_learn_progress。session_temp 仅内存不落库。"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .base import MemoryAdapter

logger = logging.getLogger(__name__)

def _safe_account(account_name: Optional[str]) -> str:
    name = (account_name or "").strip()
    name = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    return name if name else "default"


class SupabaseAdapter(MemoryAdapter):
    def __init__(self, account_name: Optional[str] = None):
        self.account_name = account_name
        self._user_id = _safe_account(account_name)
        self._session_temp: Optional[Dict[str, Any]] = None  # 仅当次会话，不落库
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise ValueError("MEMORY_BACKEND=supabase 时需设置 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY")
        from supabase import create_client
        self._client = create_client(url, key)

    def get_user_id(self) -> str:
        return self._user_id

    def _ensure_user(self) -> None:
        r = self._client.table("users").select("id").eq("id", self._user_id).execute()
        if not (r.data and len(r.data) > 0):
            self._client.table("users").insert({"id": self._user_id, "name": self.account_name or self._user_id, "profile": {}}).execute()

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
        try:
            self._ensure_user()
            r = self._client.table("users").select("profile").eq("id", self._user_id).execute()
            if r.data and len(r.data) > 0 and r.data[0].get("profile") is not None:
                out = {**default, **(r.data[0]["profile"] or {})}
                return out
            return default
        except Exception as e:
            logger.warning("Supabase load_user_profile: %s", e)
            return default

    def save_user_profile(self, profile: Dict[str, Any]) -> None:
        try:
            now = datetime.now(timezone.utc).isoformat()
            self._client.table("users").upsert(
                {"id": self._user_id, "name": profile.get("name") or self._user_id, "profile": profile, "last_updated": now},
                on_conflict="id"
            ).execute()
        except Exception as e:
            logger.exception("Supabase save_user_profile: %s", e)
            raise

    def load_session_temp(self) -> Optional[Dict[str, Any]]:
        return self._session_temp

    def save_session_temp(self, data: Dict[str, Any]) -> None:
        self._session_temp = data

    def clear_session_temp(self) -> None:
        self._session_temp = None

    def load_npc_learn_progress(self) -> Dict[str, Any]:
        try:
            self._ensure_user()
            r = self._client.table("user_npc_learn_progress").select("data").eq("user_id", self._user_id).execute()
            if r.data and len(r.data) > 0 and r.data[0].get("data"):
                d = r.data[0]["data"]
                if isinstance(d, dict):
                    return d
            return {}
        except Exception as e:
            logger.warning("Supabase load_npc_learn_progress: %s", e)
            return {}

    def save_npc_learn_progress(self, data: Dict[str, Any]) -> None:
        try:
            self._ensure_user()
            self._client.table("user_npc_learn_progress").upsert(
                {"user_id": self._user_id, "data": data},
                on_conflict="user_id",
            ).execute()
        except Exception as e:
            logger.exception("Supabase save_npc_learn_progress: %s", e)
            raise
