import os
import asyncio
from threading import Thread
from fastapi import APIRouter
from pydantic import BaseModel
from .shared import clients, continue_conversation, conversation_history
from .app import (
    analyze_mood,
    chatgpt_streamed,
    sanitize_response,
    process_and_play,
    execute_screenshot_and_analyze,
    open_file,
    init_ollama_model,
    init_openai_model,
    init_xai_model,
    init_anthropic_model,
    init_openai_tts_voice,
    init_elevenlabs_tts_voice,
    init_set_tts,
    init_set_provider,
    init_set_asr,
    init_kokoro_tts_voice,
    init_voice_speed,
    send_message_to_clients,
)
import json
from .transcription import transcribe_audio
import json
import logging
import requests

# ANSI escape codes for colors
PINK = '\033[95m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
NEON_GREEN = '\033[92m'
RESET_COLOR = '\033[0m'

# Define the CharacterModel
class CharacterModel(BaseModel):
    character: str

router = APIRouter()
characters_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "characters")

# Maximum character length for audio generation
MAX_CHAR_LENGTH = int(os.getenv('MAX_CHAR_LENGTH', 500))

# Global variable to store the current transcription model
FASTER_WHISPER_LOCAL = os.getenv("FASTER_WHISPER_LOCAL", "true").lower() == "true"
current_transcription_model = "gpt-4o-mini-transcribe"
use_local_whisper = FASTER_WHISPER_LOCAL  # Initialize based on environment

# Function to update the transcription model
def set_transcription_model(model_name):
    global current_transcription_model, use_local_whisper
    if model_name == "local_whisper":
        use_local_whisper = True
    else:
        current_transcription_model = model_name
        use_local_whisper = False
    print(f"Transcription set to: {'Local Whisper' if use_local_whisper else current_transcription_model}")
    return {"status": "success", "message": f"Transcription model set to: {'Local Whisper' if use_local_whisper else current_transcription_model}"}

async def record_audio_and_transcribe():
    """Record audio and transcribe it using the selected method"""
    
    # Create a custom callback that works with our clients set
    async def status_callback(status_data):
        message = json.dumps(status_data) if isinstance(status_data, dict) else status_data
        # Use the existing send_message_to_clients function from shared
        await send_message_to_clients(message)
        
    # Use our new unified transcription module
    user_input = await transcribe_audio(
        transcription_model=current_transcription_model,
        use_local=use_local_whisper,
        send_status_callback=status_callback
    )
    
    return user_input

# We can keep this as a utility function but it's not used directly with transcription
async def send_message_to_all_clients(message):
    for client_websocket in clients:
        try:
            await client_websocket.send_text(message)
        except Exception as e:
            print(f"Error sending message to client: {e}")

async def auto_summarize_session(memory_system, character: str):
    """自动生成会话摘要（在后台执行，不阻塞主流程）"""
    try:
        print(f"Auto-summarizing session for {character}...")
        summary_data = await memory_system.summarize_session_from_temp(character)
        
        if summary_data:
            # 添加摘要到记忆系统
            memory_system.add_summary(summary_data)
            
            # 如果提取了用户信息，更新用户档案
            if summary_data.get("extracted_user_info"):
                memory_system.update_user_profile(summary_data["extracted_user_info"])
            
            # 不清空临时文件，继续累积消息（直到手动结束或达到更大阈值）
            print(f"Auto-summary generated and saved for {character}")
        else:
            print("No messages to summarize")
    except Exception as e:
        print(f"Error in auto_summarize_session: {e}")
        import traceback
        traceback.print_exc()

async def process_text(user_input):
    # Import with alias to avoid potential shadowing issues
    from .shared import get_current_character as get_character, conversation_history, get_memory_system, get_learning_stage, set_learning_stage
    
    current_character = get_character()
    learning_stage = get_learning_stage()
    character_folder = os.path.join('characters', current_character)
    character_prompt_file = os.path.join(character_folder, f"{current_character}.txt")
    character_audio_file = os.path.join(character_folder, f"{current_character}.wav")

    base_system_message = open_file(character_prompt_file)
    
    # 加载记忆系统并获取记忆上下文
    memory_system = get_memory_system()
    memory_context = ""
    if memory_system:
        memory_context = memory_system.get_memory_context()
        # 将记忆上下文注入系统提示
        if memory_context:
            base_system_message = f"{base_system_message}\n\n{memory_context}"
    
    # 根据学习阶段调整系统提示
    if learning_stage == "chinese_chat":
        # 中文阶段：只确认用户想学什么场景，不要啰嗦，不要一次问很多
        base_system_message += """

【重要：中文沟通阶段】
- 你只用中文回复，且必须使用中文专用表达（本阶段不涉及英文）。
- 你的唯一职责：确认用户想学什么场景或主题（如：餐厅点餐、机场、酒店、办公室等）。确认清楚即可。
- 每次只问一件事或只做一句确认，回复控制在 20 字以内（例如：「好的，那就练餐厅点餐。」「你想练机场还是酒店？」）。
- 禁止长段介绍、禁止一次提多个问题、禁止追问兴趣/职业/目标等。用户说想练哪个场景就确认哪个场景。
- 如果用户说"开始学英语"、"开始英文学习"等，表示要进入英文学习阶段。
"""
        
        # 检测触发词，切换到英文学习阶段
        trigger_phrases = ["开始学英语", "开始英文学习", "开始英语学习", "start english", "开始学英文"]
        if any(phrase in user_input for phrase in trigger_phrases):
            set_learning_stage("english_learning")
            # 发送提示消息
            await send_message_to_clients({
                "action": "ai_message",
                "text": "好的，让我为你生成一段个性化的英文对话！"
            })
    
    elif learning_stage == "english_learning":
        # 英文学习阶段
        english_level = "beginner"
        if memory_system:
            english_level = memory_system.user_profile.get("english_level", "beginner")
        
        level_map = {
            "beginner": "初级（A1-A2）",
            "elementary": "基础（A2-B1）",
            "intermediate": "中级（B1-B2）",
            "advanced": "高级（B2-C1）"
        }
        level_display = level_map.get(english_level, "初级")
        
        base_system_message += f"""

【重要：英文学习阶段】
- 你必须用英文回复用户
- 根据用户的英文水平（{level_display}）调整回复难度
- 基于用户的兴趣、职业和今天的对话内容进行教学
- 回复要简洁，控制在50-100字
- 可以纠正用户的语法错误，但要友好
"""
    
    # 添加强制简洁要求（优先级最高，覆盖所有其他风格要求）
    base_system_message += """

【重要：回复风格要求】
- 回复要像正常朋友聊天一样，简洁自然
- 若当前为中文沟通阶段：每次回复控制在 20 字以内，只做场景确认，不啰嗦
- 若为英文学习阶段：每次回复控制在 30-80 字左右（2-3 句话）
- 不要使用过多的比喻、修饰词或诗意语言，直接回答问题，不要绕弯子
- 除非用户明确要求详细解释，否则保持简短
- 这个要求优先于所有其他风格要求
"""
    
    mood = analyze_mood(user_input)
    mood_prompt = adjust_prompt(mood)
    
    # 确保用户输入已经在对话历史中（如果不在则添加）
    # 注意：如果从/api/voice/upload或/api/text/send调用，用户输入已经添加了
    if not conversation_history or conversation_history[-1].get("role") != "user" or conversation_history[-1].get("content") != user_input:
        # 只有在确实不存在时才添加，避免重复
        pass  # 不在这里添加，因为已经在upload或send端点添加了
    
    # 保存用户消息到临时会话文件（带时间戳）
    if memory_system:
        try:
            from datetime import datetime
            user_message = {
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            }
            memory_system.save_to_session_temp(user_message, current_character)
            print(f"Saved user message to session temp: {memory_system.session_temp_file}")
        except Exception as e:
            print(f"Error saving user message to session temp: {e}")
            import traceback
            traceback.print_exc()

    # 使用异步版本的LLM调用，避免阻塞事件循环
    from .app import chatgpt_streamed_async
    chatbot_response = await chatgpt_streamed_async(user_input, base_system_message, mood_prompt, conversation_history)
    sanitized_response = sanitize_response(chatbot_response)
    # Limit the response length to the MAX_CHAR_LENGTH for audio generation
    if len(sanitized_response) > MAX_CHAR_LENGTH:
        sanitized_response = sanitized_response[:MAX_CHAR_LENGTH] + "..."
    prompt2 = sanitized_response

    conversation_history.append({"role": "assistant", "content": chatbot_response})
    
    # 保存AI回复到临时会话文件（带时间戳）
    if memory_system:
        try:
            from datetime import datetime
            ai_message = {
                "role": "assistant",
                "content": chatbot_response,
                "timestamp": datetime.now().isoformat()
            }
            memory_system.save_to_session_temp(ai_message, current_character)
            # 注意：摘要生成改为手动触发，通过 /api/conversation/end API
        except Exception as e:
            print(f"Error saving to session temp: {e}")
            import traceback
            traceback.print_exc()
    
    # 先发送AI消息到客户端显示文字（立即执行，无阻塞）
    # 注意：直接传递字典，send_message_to_clients会自动处理JSON编码
    await send_message_to_clients({
        "action": "ai_message",
        "text": chatbot_response,
        "character": current_character
    })
    
    # 让出控制权，确保WebSocket消息已经真正发送到网络
    # 这确保消息发送完成后再创建音频任务
    await asyncio.sleep(0)  # 让出控制权，确保消息发送完成
    
    # 再异步执行 process_and_play（语音处理/播放）
    # 不阻塞主流程，文字已经显示，音频在后台处理
    asyncio.create_task(process_and_play(prompt2, character_audio_file))
    
    # 继续执行保存历史等操作（不等待音频播放完成）
    # Check if this is a story or game character
    is_story_character = current_character.startswith("story_") or current_character.startswith("game_")
    
    if is_story_character:
        # Save to character-specific history file
        save_character_specific_history(conversation_history, current_character)
        print(f"Saved character-specific history for {current_character}")
    # 不再保存全局历史文件（conversation_history.txt 已移除）
        
    return chatbot_response

quit_phrases = ["quit", "Quit", "Quit.", "Exit.", "exit", "Exit"]
screenshot_phrases = [
    "what's on my screen", 
    "take a screenshot", 
    "show me my screen", 
    "analyze my screen", 
    "what do you see on my screen", 
    "screen capture", 
    "screenshot"
]

@router.post("/start_conversation")
async def start_conversation():
    global continue_conversation # noqa: F824
    
    # Set flag to continue conversation
    continue_conversation = True
    
    # Import with alias to avoid potential shadowing issues
    from .shared import conversation_history, get_current_character as get_character, set_conversation_active
    
    # Get the current character
    current_character = get_character()
    print(f"Starting conversation with character: {current_character}")
    
    # Set conversation_active to True
    set_conversation_active(True)
    
    # Determine if character is story/game character
    is_story_character = current_character.startswith("story_") or current_character.startswith("game_")
    
    # Handle history based on character type
    if is_story_character:
        # For story/game characters: preserve existing history or load from character-specific file
        print(f"Using character-specific history for {current_character}")
        loaded_history = load_character_specific_history(current_character)
        if loaded_history:
            # Clear existing history and load from file
            conversation_history.clear()
            conversation_history.extend(loaded_history)
            print(f"Loaded {len(loaded_history)} messages from character-specific history")
        else:
            # If no history exists, make sure in-memory history is cleared too
            conversation_history.clear()
            print("No previous character-specific history found, starting fresh")
    else:
        # For standard characters: make sure we're starting with an empty history
        print(f"Clearing conversation history for standard character: {current_character}")
        conversation_history.clear()
        
        # Load history from file - only for existing global history
        history_file = "conversation_history.txt"
        if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
            print("Loading history from global file")
            temp_history = []
            with open(history_file, "r", encoding="utf-8") as file:
                current_role = None
                current_content = ""
                
                for line in file:
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                        
                    if line.startswith("User:"):
                        # Save previous message if exists
                        if current_role:
                            temp_history.append({"role": current_role, "content": current_content.strip()})
                        
                        # Start new user message
                        current_role = "user"
                        current_content = line[5:].strip()
                    elif line.startswith("Assistant:"):
                        # Save previous message if exists
                        if current_role:
                            temp_history.append({"role": current_role, "content": current_content.strip()})
                        
                        # Start new assistant message
                        current_role = "assistant"
                        current_content = line[10:].strip()
                    else:
                        # Continue previous message
                        current_content += "\n" + line
                
                # Add the last message
                if current_role:
                    temp_history.append({"role": current_role, "content": current_content.strip()})
            
            # Add loaded messages to conversation history
            conversation_history.extend(temp_history)
            print(f"Loaded {len(temp_history)} messages from global history")
    
    print(f"Starting conversation with character {current_character}, history size: {len(conversation_history)}")
    
    # Wait for speech
    # print("Waiting for speech...")
    await send_message_to_clients({"type": "waiting"})
    
    # Start conversation thread
    Thread(target=asyncio.run, args=(conversation_loop(),)).start()
    
    return {"status": "started"}

@router.post("/stop_conversation")
async def stop_conversation():
    global continue_conversation # noqa: F824
    continue_conversation = False
    return {"message": "Conversation stopped"}

async def conversation_loop():
    global continue_conversation # noqa: F824
    
    # Import with alias to avoid potential shadowing issues
    from .shared import get_current_character as get_character
    
    while continue_conversation:
        user_input = await record_audio_and_transcribe() 
        
        # Check if user_input is None and handle it
        if user_input is None:
            print("Warning: Received None input from transcription")
            continue
            
        conversation_history.append({"role": "user", "content": user_input})
        
        # Get current character to check if it's a story/game character
        current_character = get_character()
        is_story_character = current_character.startswith("story_") or current_character.startswith("game_")
        
        # Save history based on character type
        if is_story_character:
            save_character_specific_history(conversation_history, current_character)
            print(f"Saved user input to character-specific history for {current_character}")
        # 不再保存全局历史文件（conversation_history.txt 已移除）
            
        await send_message_to_clients(f"You: {user_input}")
        print(CYAN + f"You: {user_input}" + RESET_COLOR)

        # Check for quit phrases with word boundary check
        words = user_input.lower().split()
        if any(phrase.lower().rstrip('.') == word for phrase in quit_phrases for word in words):
            print("Quitting the conversation...")
            await stop_conversation()
            break

        # Check for screenshot phrases - match only if the full phrase exists in input
        if any(phrase in user_input.lower() for phrase in screenshot_phrases):
            await execute_screenshot_and_analyze()
            continue

        try:
            chatbot_response = await process_text(user_input)
        except Exception as e:
            chatbot_response = f"An error occurred: {e}"
            print(chatbot_response)

        current_character = get_character()
        await send_message_to_clients(chatbot_response)
        # await send_message_to_clients(f"{current_character.capitalize()}: {chatbot_response}") # to use for character names
        # print(f"{current_character.capitalize()}: {chatbot_response}")

def set_env_variable(key: str, value: str):
    os.environ[key] = value
    if key == "OLLAMA_MODEL":
        init_ollama_model(value)  # Reinitialize Ollama model
    if key == "OPENAI_MODEL":
        init_openai_model(value)  # Reinitialize OpenAI model
    if key == "XAI_MODEL":
        init_xai_model(value)  # Reinitialize XAI model
    if key == "ANTHROPIC_MODEL":
        init_anthropic_model(value)  # Reinitialize Anthropic model
    if key == "OPENAI_TTS_VOICE":
        init_openai_tts_voice(value)  # Reinitialize OpenAI TTS voice
    if key == "ELEVENLABS_TTS_VOICE":
        init_elevenlabs_tts_voice(value)  # Reinitialize Elevenlabs TTS voice
    if key == "KOKORO_TTS_VOICE":
        init_kokoro_tts_voice(value)  # Reinitialize Kokoro TTS voice
    if key == "VOICE_SPEED":
        init_voice_speed(value)  # Reinitialize Voice Speed for all TTS providers
    if key == "API_PROVIDER":
        from .app import init_set_api_provider
        success = init_set_api_provider(value)  # 全局API供应商开关
        if not success:
            print(f"Warning: 设置API_PROVIDER失败，值 '{value}' 不支持")
    if key == "TTS_PROVIDER":
        init_set_tts(value)      # Reinitialize TTS Providers (已废弃，请使用API_PROVIDER)
    if key == "MODEL_PROVIDER":
        init_set_provider(value)  # Reinitialize Model Providers (已废弃，请使用API_PROVIDER)
    if key == "ASR_PROVIDER":
        init_set_asr(value)  # Reinitialize ASR Providers (已废弃，请使用API_PROVIDER)


def adjust_prompt(mood):
    """Load mood-specific prompts from the character's prompts.json file."""
    # Import with alias to avoid potential shadowing issues
    from .shared import get_current_character as get_character
    
    # Get the current character
    current_character = get_character()
    
    # Look for character-specific prompts first
    character_prompts_path = os.path.join(characters_folder, current_character, 'prompts.json')
    
    # Control output verbosity using the DEBUG flag from enhanced_logic.py
    try:
        # Import DEBUG flag if it exists
        try:
            from .enhanced_logic import DEBUG
        except ImportError:
            DEBUG = False  # Default to False if not available
            
        # Try to load character-specific prompts
        if os.path.exists(character_prompts_path):
            with open(character_prompts_path, 'r', encoding='utf-8') as f:
                mood_prompts = json.load(f)
                if DEBUG:
                    print(f"Loaded mood prompts for character: {current_character}")
        else:
            # Fall back to global prompts
            prompts_path = os.path.join(characters_folder, 'prompts.json')
            with open(prompts_path, 'r', encoding='utf-8') as f:
                mood_prompts = json.load(f)
                if DEBUG:
                    print(f"Using global prompts.json - character-specific prompts not found")
    except FileNotFoundError:
        print(f"Error loading prompts: character or global prompts.json not found. Using default prompts.")
        mood_prompts = {
            "happy": "RESPOND WITH JOY AND ENTHUSIASM.",
            "sad": "RESPOND WITH KINDNESS AND COMFORT.",
            "flirty": "RESPOND WITH A TOUCH OF MYSTERY AND CHARM.",
            "angry": "RESPOND CALMLY AND WISELY.",
            "neutral": "KEEP RESPONSES SHORT AND NATURAL.",
            "fearful": "RESPOND WITH REASSURANCE.",
            "surprised": "RESPOND WITH AMAZEMENT.",
            "disgusted": "RESPOND WITH UNDERSTANDING.",
            "joyful": "RESPOND WITH EXUBERANCE."
        }
    except Exception as e:
        print(f"Error loading prompts: {e}")
        mood_prompts = {}

    # Get the mood prompt but don't print it in normal logging
    mood_prompt = mood_prompts.get(mood, "")
    
    # Debug output only if DEBUG is enabled
    if 'DEBUG' in locals() and DEBUG:
        print(f"Selected prompt for {current_character} ({mood}): {mood_prompt[:100]}...")
    
    return mood_prompt

async def fetch_ollama_models():
    """Fetch available models from Ollama API"""
    try:
        ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            models_data = response.json()
            # Extract just the model names from the response
            models = [model['name'] for model in models_data.get('models', [])]
            
            # If models list is empty (older Ollama versions format), try alternate path
            if not models and 'models' not in models_data:
                models = [model['name'] for model in models_data]
                
            return {"models": models}
        else:
            logging.warning(f"Failed to fetch Ollama models: {response.status_code}")
            return {"models": ["llama3.2"], "error": f"Failed to fetch models: {response.status_code}"}
    except Exception as e:
        logging.error(f"Error fetching Ollama models: {e}")
        return {"models": ["llama3.2"], "error": f"Error connecting to Ollama: {str(e)}"}

# save_conversation_history 函数已移除（conversation_history.txt 功能已移除）

def is_client_active(client):
    """Check if a client is still active"""
    # This is a placeholder - implement connection checking as needed
    return True

def load_character_prompt(character_name):
    """
    Load the character prompt from the character's text file.
    
    Args:
        character_name (str): The name of the character folder.
        
    Returns:
        str: The character prompt text.
    """
    try:
        character_file_path = os.path.join(characters_folder, character_name, f"{character_name}.txt")
        if not os.path.exists(character_file_path):
            print(f"Character file not found: {character_file_path}")
            # Return a default prompt for the assistant character
            return "You are a helpful AI assistant."
            
        with open(character_file_path, 'r', encoding='utf-8') as file:
            character_prompt = file.read()
            
        print(f"Loaded character prompt for {character_name}: {len(character_prompt)} chars")
        return character_prompt
    except Exception as e:
        print(f"Error loading character prompt: {e}")
        # Return a default prompt for the assistant character
        return "You are a helpful AI assistant."

def save_character_specific_history(history, character_name):
    """
    Save conversation history to a character-specific file for story/game characters.
    Only to be used for characters with names starting with story_ or game_
    
    Args:
        history: The conversation history to save
        character_name: The name of the character
        
    Returns:
        dict: Status of the operation
    """
    try:
        # Only process for story/game characters
        if not character_name.startswith("story_") and not character_name.startswith("game_"):
            print(f"Not a story/game character: {character_name}, skipping history save (global history removed)")
            return {"status": "skipped", "message": "Global history file removed"}
            
        # Create character-specific history file path
        character_dir = os.path.join(characters_folder, character_name)
        history_file = os.path.join(character_dir, "conversation_history.txt")
        
        print(f"Saving character-specific history for {character_name}")
        
        with open(history_file, "w", encoding="utf-8") as file:
            for message in history:
                role = message["role"].capitalize()
                content = message["content"]
                file.write(f"{role}: {content}\n\n")  # Extra newline for readability
                
        print(f"Saved {len(history)} messages to character-specific history file")
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error saving character-specific history: {e}")
        return {"status": "error", "message": str(e)}

def load_character_specific_history(character_name):
    """
    Load conversation history from a character-specific file for story/game characters.
    Only to be used for characters with names starting with story_ or game_
    
    Args:
        character_name: The name of the character
        
    Returns:
        list: The conversation history or an empty list if not found
    """
    try:
        # Only process for story/game characters
        if not character_name.startswith("story_") and not character_name.startswith("game_"):
            print(f"Not a story/game character: {character_name}, using global history instead")
            return []
            
        # Create character-specific history file path
        character_dir = os.path.join(characters_folder, character_name)
        history_file = os.path.join(character_dir, "conversation_history.txt")
        
        # Check if file exists
        if not os.path.exists(history_file) or os.path.getsize(history_file) == 0:
            print(f"No character-specific history found for {character_name}")
            return []
            
        print(f"Loading character-specific history for {character_name}")
        
        temp_history = []
        with open(history_file, "r", encoding="utf-8") as file:
            current_role = None
            current_content = ""
            
            for line in file:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                    
                if line.startswith("User:"):
                    # Save previous message if exists
                    if current_role:
                        temp_history.append({"role": current_role, "content": current_content.strip()})
                    
                    # Start new user message
                    current_role = "user"
                    current_content = line[5:].strip()
                elif line.startswith("Assistant:"):
                    # Save previous message if exists
                    if current_role:
                        temp_history.append({"role": current_role, "content": current_content.strip()})
                    
                    # Start new assistant message
                    current_role = "assistant"
                    current_content = line[10:].strip()
                else:
                    # Continue previous message
                    current_content += "\n" + line
            
            # Add the last message
            if current_role:
                temp_history.append({"role": current_role, "content": current_content.strip()})
                
        print(f"Loaded {len(temp_history)} messages from character-specific history file")
        return temp_history
    except Exception as e:
        logging.error(f"Error loading character-specific history: {e}")
        return []

@router.post("/set_character")
async def set_api_character(character: CharacterModel):
    """Set the current character."""
    # Import with alias to avoid potential shadowing issues
    from .shared import set_current_character, get_current_character, conversation_history
    
    previous_character = get_current_character()
    new_character = character.character
    
    print(f"Switching character: {previous_character} -> {new_character}")
    
    # Always save the previous character's history if needed
    is_previous_story_character = previous_character and (
        previous_character.startswith("story_") or previous_character.startswith("game_")
    )
    
    if is_previous_story_character and conversation_history:
        # Save the current history to character-specific file before switching
        save_character_specific_history(conversation_history, previous_character)
        print(f"Saved history for previous character: {previous_character}")
    
    # Set the new character
    set_current_character(new_character)
    
    # Always clear the global history when switching characters
    conversation_history.clear()
    print(f"Cleared in-memory conversation history")
    
    # Delete the global history file and create a new empty one
    history_file = "conversation_history.txt"
    if os.path.exists(history_file):
        os.remove(history_file)
        print(f"Deleted global history file")
    
    # Create empty history file
    with open(history_file, "w", encoding="utf-8") as f:
        pass
    print(f"Created empty global history file")
    
    return {"status": "success", "message": f"Character set to {new_character}"}