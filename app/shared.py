"""
Shared resources used across the application.
状态按用户(account_name)隔离，与现有账号记忆系统对接。
"""

import os
from dotenv import load_dotenv

load_dotenv()

# WebSocket clients
clients = set()
active_client_status = {}  # Track status of websocket clients

# WebSocket -> account_name 绑定，用于按用户分状态
_ws_to_account = {}

DEFAULT_ACCOUNT = "default"

def _default_user_state():
    """单用户状态的默认结构（与现有账号记忆等对接）"""
    return {
        "conversation_history": [],
        "current_character": os.getenv("CHARACTER_NAME", "english_tutor"),
        "conversation_active": False,
        "continue_conversation": False,
        "learning_stage": "chinese_chat",  # "chinese_chat" 或 "english_learning"
    }

# 按用户 ID(account_name) 存状态
_user_states = {}

def get_user_state(account_name=None):
    """获取指定用户的状态，无则创建默认。account_name 为空时使用 DEFAULT_ACCOUNT。"""
    key = (account_name or DEFAULT_ACCOUNT).strip() or DEFAULT_ACCOUNT
    if key not in _user_states:
        _user_states[key] = _default_user_state()
    return _user_states[key]

def set_websocket_account(websocket, account_name):
    """绑定 WebSocket 与账号，用于该连接后续请求按用户分状态。"""
    _ws_to_account[websocket] = (account_name or "").strip() or DEFAULT_ACCOUNT

def get_websocket_account(websocket):
    """获取 WebSocket 绑定的账号，未绑定返回 DEFAULT_ACCOUNT。"""
    return _ws_to_account.get(websocket, DEFAULT_ACCOUNT)

def remove_websocket_account(websocket):
    """连接断开时移除绑定。"""
    _ws_to_account.pop(websocket, None)

# ---------- 按用户的 state getter/setter（与现有逻辑兼容，account_name 为空时用 default）----------

def get_current_character(account_name=None):
    """Get the current character for the given account."""
    return get_user_state(account_name)["current_character"]

def set_current_character(character, account_name=None):
    """Set the current character for the given account."""
    get_user_state(account_name)["current_character"] = character

def is_conversation_active(account_name=None):
    """Check if a conversation is active for the given account."""
    return get_user_state(account_name)["conversation_active"]

def set_conversation_active(active, account_name=None):
    """Set the conversation active state for the given account."""
    get_user_state(account_name)["conversation_active"] = active

def get_conversation_history(account_name=None):
    """Get conversation history for the given account (返回引用，调用方可 append/clear)。"""
    return get_user_state(account_name)["conversation_history"]

def clear_conversation_history(account_name=None):
    """Clear the conversation history for the given account."""
    get_user_state(account_name)["conversation_history"].clear()

def get_learning_stage(account_name=None):
    """Get learning stage for the given account."""
    return get_user_state(account_name)["learning_stage"]

def set_learning_stage(stage, account_name=None):
    """Set learning stage for the given account."""
    if stage in ["chinese_chat", "english_learning"]:
        get_user_state(account_name)["learning_stage"] = stage
        print(f"Learning stage set to: {stage} (account={account_name or DEFAULT_ACCOUNT})")
    else:
        print(f"Invalid learning stage: {stage}, must be 'chinese_chat' or 'english_learning'")

def get_continue_conversation(account_name=None):
    """Get continue_conversation flag for the given account."""
    return get_user_state(account_name)["continue_conversation"]

def set_continue_conversation(value, account_name=None):
    """Set continue_conversation for the given account."""
    get_user_state(account_name)["continue_conversation"] = value

# ---------- 兼容旧代码：保留 conversation_history 的“当前默认用户”引用 ----------
# 仅用于尚未传入 account_name 的调用处，建议逐步改为显式传 account_name
def _default_conversation_history():
    return get_conversation_history(DEFAULT_ACCOUNT)

def add_client(client):
    """Add a client to the set of connected clients."""
    clients.add(client)
    active_client_status[client] = True

def remove_client(client):
    """Remove a client from the set of connected clients."""
    clients.discard(client)
    remove_websocket_account(client)
    if client in active_client_status:
        del active_client_status[client]

def is_client_active(client):
    """Check if a client is active."""
    return active_client_status.get(client, False)

def set_client_inactive(client):
    """Mark a client as inactive."""
    active_client_status[client] = False

# 记忆系统（与现有账号记忆对接：按 account_name 使用，不依赖全局“当前账号”）
memory_system = None
current_account = None  # 保留用于 get_memory_system(account_name=None) 时的回退
_last_memory_init_error = None

def get_memory_system(account_name=None):
    """获取记忆系统实例（单例模式，但基于账号）。传入 account_name 时使用该账号，与按用户分状态对接。"""
    global memory_system, current_account, _last_memory_init_error

    if account_name is None:
        account_name = current_account

    if account_name and account_name != current_account:
        memory_system = None
        current_account = account_name

    if memory_system is None:
        _last_memory_init_error = None
        try:
            from .memory_system import DiaryMemorySystem
            memory_system = DiaryMemorySystem(account_name=account_name)
            current_account = account_name
            print(f"Memory system initialized successfully for account: {account_name or 'default'}")
        except Exception as e:
            _last_memory_init_error = str(e)
            print(f"Error initializing memory system: {e}")
            import traceback
            traceback.print_exc()
            memory_system = None
            current_account = None
    return memory_system

def get_last_memory_init_error():
    """返回上次记忆系统初始化失败时的错误信息（供登录接口返回给用户）"""
    global _last_memory_init_error
    return _last_memory_init_error

def get_current_account():
    """获取当前账号名称（全局回退值，建议各请求显式传 account_name）"""
    global current_account
    return current_account

def set_current_account(account_name):
    """设置当前账号（会重新初始化记忆系统），用于登录等场景。"""
    global memory_system, current_account
    if account_name != current_account:
        memory_system = None
        current_account = account_name
