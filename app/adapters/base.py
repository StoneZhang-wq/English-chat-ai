"""记忆存储适配器抽象：diary、user_profile、session_temp 的读写"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class MemoryAdapter(ABC):
    """记忆后端抽象接口。实现：FileAdapter（本地 JSON）、SupabaseAdapter（Supabase）。"""

    @abstractmethod
    def get_user_id(self) -> str:
        """当前账户对应的存储 ID（安全名称）。"""
        pass

    # ---------- diary ----------
    @abstractmethod
    def load_diary_data(self) -> Dict[str, Any]:
        """返回与 diary.json 同结构：{ version, last_updated, entries: [...] }"""
        pass

    @abstractmethod
    def save_diary_data(self, data: Dict[str, Any]) -> None:
        """保存整份 diary 数据。"""
        pass

    # ---------- user_profile ----------
    @abstractmethod
    def load_user_profile(self) -> Dict[str, Any]:
        """返回与 user_profile.json 同结构的 dict。"""
        pass

    @abstractmethod
    def save_user_profile(self, profile: Dict[str, Any]) -> None:
        """保存整份 user_profile。"""
        pass

    # ---------- session_temp（仅当次会话临时，Supabase 后端用内存不落库）----------
    @abstractmethod
    def load_session_temp(self) -> Optional[Dict[str, Any]]:
        """返回 session_temp 内容，无则 None。"""
        pass

    @abstractmethod
    def save_session_temp(self, data: Dict[str, Any]) -> None:
        """保存 session_temp。"""
        pass

    @abstractmethod
    def clear_session_temp(self) -> None:
        """清空 session_temp。"""
        pass

    # ---------- npc_learn_progress（各场景下已学完的 NPC，用于解锁与判断）----------
    @abstractmethod
    def load_npc_learn_progress(self) -> Dict[str, Any]:
        """返回 { small_scene_id: [npc_id, ...], ... }，与 npc_learn_progress.json 同结构。"""
        pass

    @abstractmethod
    def save_npc_learn_progress(self, data: Dict[str, Any]) -> None:
        """保存 npc_learn_progress。"""
        pass
