"""
Shared resources used across the application
"""

import os
from dotenv import load_dotenv

load_dotenv()

# WebSocket clients
clients = set()
active_client_status = {}  # Track status of websocket clients

# Shared state variables
current_character = os.getenv("CHARACTER_NAME", "english_tutor")  # Get from .env
conversation_active = False
conversation_history = []
continue_conversation = False  # Added missing variable
learning_stage = "chinese_chat"  # "chinese_chat" 或 "english_learning"

# Functions to get and set shared state
def get_current_character():
    """Get the current character."""
    global current_character # noqa: F824
    return current_character

def set_current_character(character):
    """Set the current character."""
    global current_character # noqa: F824
    current_character = character

def is_conversation_active():
    """Check if a conversation is active."""
    global conversation_active # noqa: F824
    return conversation_active

def set_conversation_active(active):
    """Set the conversation active state."""
    global conversation_active # noqa: F824
    conversation_active = active

def add_client(client):
    """Add a client to the set of connected clients."""
    clients.add(client)
    active_client_status[client] = True

def remove_client(client):
    """Remove a client from the set of connected clients."""
    clients.discard(client)
    if client in active_client_status:
        del active_client_status[client]

def is_client_active(client):
    """Check if a client is active."""
    return active_client_status.get(client, False)

def set_client_inactive(client):
    """Mark a client as inactive."""
    active_client_status[client] = False

def clear_conversation_history():
    """Clear the conversation history."""
    global conversation_history
    conversation_history = []

# 记忆系统
memory_system = None

def get_memory_system():
    """获取记忆系统实例（单例模式）"""
    global memory_system
    if memory_system is None:
        try:
            from .memory_system import DiaryMemorySystem
            memory_system = DiaryMemorySystem()
            print("Memory system initialized successfully")
        except Exception as e:
            print(f"Error initializing memory system: {e}")
            import traceback
            traceback.print_exc()
            memory_system = None
    return memory_system

# 学习阶段管理
def get_learning_stage():
    """获取当前学习阶段"""
    global learning_stage # noqa: F824
    return learning_stage

def set_learning_stage(stage):
    """设置学习阶段"""
    global learning_stage # noqa: F824
    if stage in ["chinese_chat", "english_learning"]:
        learning_stage = stage
        print(f"Learning stage set to: {stage}")
    else:
        print(f"Invalid learning stage: {stage}, must be 'chinese_chat' or 'english_learning'")