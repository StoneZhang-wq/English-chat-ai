# 记忆存储适配器：file（本地 JSON）| supabase（Supabase 表）
from .base import MemoryAdapter

def get_memory_adapter(account_name=None, project_dir=None):
    """根据 MEMORY_BACKEND 返回 FileAdapter 或 SupabaseAdapter。"""
    import os
    backend = (os.getenv("MEMORY_BACKEND") or "file").strip().lower()
    if backend == "supabase":
        from .supabase_adapter import SupabaseAdapter
        return SupabaseAdapter(account_name=account_name)
    from .file_adapter import FileAdapter
    return FileAdapter(account_name=account_name, project_dir=project_dir)

__all__ = ["MemoryAdapter", "get_memory_adapter"]
