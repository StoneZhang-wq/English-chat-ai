import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class SummaryMemorySystem:
    """简化版日记式记忆系统，使用文本摘要存储对话内容"""
    
    def __init__(self, 
                 memory_file=None,
                 max_entries=None):
        # 获取项目根目录（app 的父目录）
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(current_file_dir)
        
        # 从环境变量读取配置，如果没有则使用默认值（相对于项目根目录）
        if memory_file:
            # 如果提供了路径，使用提供的路径
            self.diary_file = Path(memory_file)
        else:
            # 从环境变量读取，或使用默认路径
            env_memory_file = os.getenv("MEMORY_FILE")
            if env_memory_file:
                # 如果是绝对路径，直接使用；如果是相对路径，相对于项目根目录
                if os.path.isabs(env_memory_file):
                    self.diary_file = Path(env_memory_file)
                else:
                    self.diary_file = Path(project_dir) / env_memory_file
            else:
                # 默认路径：项目根目录下的 memory/diary.json
                self.diary_file = Path(project_dir) / "memory" / "diary.json"
        
        self.max_entries = max_entries or int(os.getenv("MEMORY_MAX_ENTRIES", "50"))
        
        # 确保目录存在
        self.diary_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_temp_file = self.diary_file.parent / "session_temp.json"
        self.user_profile_file = self.diary_file.parent / "user_profile.json"
        self.diary_data = self.load_diary()
        self.user_profile = self.load_user_profile()
        
        # 打印调试信息
        print(f"Memory system initialized:")
        print(f"  Diary file: {self.diary_file}")
        print(f"  Session temp: {self.session_temp_file}")
        print(f"  User profile: {self.user_profile_file}")
        
    def load_diary(self) -> Dict:
        """加载日记文件"""
        if not self.diary_file.exists():
            return {
                "version": "1.0",
                "last_updated": None,
                "entries": []
            }
        
        try:
            with open(self.diary_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading diary: {e}")
            return {
                "version": "1.0",
                "last_updated": None,
                "entries": []
            }
    
    def save_diary(self):
        """保存日记到文件"""
        self.diary_data["last_updated"] = datetime.now().isoformat()
        
        try:
            # 确保目录存在
            self.diary_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.diary_file, "w", encoding="utf-8") as f:
                json.dump(self.diary_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving diary: {e}")
            import traceback
            traceback.print_exc()
    
    def get_memory_context(self) -> str:
        """获取记忆上下文，基于日记摘要和用户档案"""
        # 获取当前日期
        today = datetime.now()
        today_str = today.strftime("%Y年%m月%d日")
        today_iso = today.strftime("%Y-%m-%d")
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]
        
        # 获取用户档案
        user_profile = self.get_user_profile_context()
        
        # 获取最近的日记条目（最近10条）
        recent_entries = self.diary_data.get("entries", [])[-10:]
        
        # 构建上下文
        context_parts = [f"[当前时间信息]\n今天是{today_str}（{weekday}），日期：{today_iso}"]
        
        if user_profile:
            context_parts.append(f"[用户档案信息]\n{user_profile}")
        
        if recent_entries:
            # 按日期分组条目
            entries_by_date = {}
            for entry in recent_entries:
                date_str = entry.get("date", "")
                if date_str:
                    if date_str not in entries_by_date:
                        entries_by_date[date_str] = []
                    entries_by_date[date_str].append(entry)
            
            # 生成摘要列表（带相对时间标签）
            summary_entries = []
            for date_str in sorted(entries_by_date.keys())[-7:]:  # 最近7天的记录
                time_label = self.get_relative_time_label(date_str)
                date_entries = entries_by_date[date_str]
                summaries = [e.get("summary", "") for e in date_entries if e.get("summary")]
                if summaries:
                    # 合并同一天的多个摘要
                    combined_summary = " ".join(summaries)
                    summary_entries.append(f"{time_label}（{date_str}）：{combined_summary}")
            
            if summary_entries:
                context_parts.append(f"[最近的对话记录]\n" + "\n".join(summary_entries))
        
        if len(context_parts) == 1:  # 只有时间信息
            return ""
        
        context = "\n\n".join(context_parts)
        context += f"""

请根据以上记忆与用户对话：
1. 明确知道今天是{today_str}
2. 如果用户提到"昨天"、"今天"、"明天"，要能准确理解
3. 可以主动提及之前的对话内容，如"你昨天提到..."、"你之前说过..."
4. 可以追问后续进展，如"你之前提到的...现在怎么样了？"
5. 保持对话的连贯性和时间感
6. 使用相对时间概念（昨天、前天、上周等）让对话更自然
7. 如果知道用户的姓名、兴趣等信息，要自然地使用这些信息
8. 重要：只能基于以上真实记录的对话内容进行对话，不要虚构或添加不存在的信息
9. 重要：不要说"在日记中提到"，只说"提到"或"说过"即可
10. 重要：回复要简洁自然，像正常朋友聊天一样。每次回复尽量控制在50-100字左右，除非用户明确要求详细解释。保持对话的轻松和自然，不要长篇大论。
"""
        return context
    
    def get_relative_time_label(self, date_str: str) -> str:
        """获取相对时间标签（昨天、今天、明天等）"""
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            days_ago = (today - target_date).days
            
            if days_ago == 0:
                return "今天"
            elif days_ago == 1:
                return "昨天"
            elif days_ago == 2:
                return "前天"
            elif days_ago < 7:
                return f"{days_ago}天前"
            elif days_ago < 30:
                weeks = days_ago // 7
                return f"{weeks}周前"
            else:
                months = days_ago // 30
                return f"{months}个月前"
        except:
            return date_str
    
    def save_to_session_temp(self, message: Dict, character: str = ""):
        """保存消息到临时会话文件"""
        if not self.session_temp_file.exists():
            session_data = {
                "session_start": datetime.now().isoformat(),
                "character": character,
                "messages": []
            }
        else:
            try:
                with open(self.session_temp_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
            except:
                session_data = {
                    "session_start": datetime.now().isoformat(),
                    "character": character,
                    "messages": []
                }
        
        # 更新角色（如果提供了）
        if character:
            session_data["character"] = character
        
        # 添加消息
        session_data["messages"].append(message)
        
        # 保存到文件
        try:
            # 确保目录存在
            self.session_temp_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_temp_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            print(f"Saved message to session temp: {self.session_temp_file} (total messages: {len(session_data['messages'])})")
        except Exception as e:
            print(f"Error saving to session temp file: {e}")
            print(f"  File path: {self.session_temp_file}")
            import traceback
            traceback.print_exc()
    
    def load_session_temp(self) -> Optional[Dict]:
        """加载临时会话文件"""
        if not self.session_temp_file.exists():
            return None
        
        try:
            with open(self.session_temp_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session temp file: {e}")
            return None
    
    def clear_session_temp(self):
        """清空临时会话文件"""
        if self.session_temp_file.exists():
            try:
                self.session_temp_file.unlink()
            except Exception as e:
                print(f"Error clearing session temp file: {e}")
    
    def is_error_response(self, response: str) -> bool:
        """检查响应是否为错误信息"""
        error_indicators = [
            "Error connecting to",
            "Error:",
            "Connection aborted",
            "ConnectionResetError",
            "timeout",
            "网络错误",
            "连接失败"
        ]
        response_lower = response.lower()
        return any(indicator.lower() in response_lower for indicator in error_indicators)
    
    async def generate_diary_summary(self, session_messages: List[Dict], character: str):
        """从会话生成文本摘要（不设字数限制，实事求是）"""
        import asyncio
        from .app import chatgpt_streamed
        
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in session_messages
        ])
        
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        timestamp = today.isoformat()
        session_id = f"{date_str}_{today.strftime('%H-%M-%S')}"
        
        # 简化的摘要生成提示词
        summary_prompt = f"""请将以下对话整理成一段简单的文本摘要，描述用户在这次对话中做了什么、说了什么、表达了什么。

要求：
1. 实事求是，有多少信息就写多少，不设字数限制
2. 如果用户只是简单打招呼，就写"用户简单打招呼"
3. 如果用户说了很多信息，就详细记录
4. 只记录对话中明确提到的内容，不要虚构或添加细节
5. 用自然的中文描述，像在写日记一样

对话内容：
{conversation_text}

只返回摘要文本，不要其他说明。"""
        
        # 将同步函数包装成异步调用
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: chatgpt_streamed(
                summary_prompt,
                "你是一个专业的对话摘要助手，实事求是地总结对话内容，不添加任何细节。",
                "neutral",
                []
            )
        )
        
        # 检查是否为错误响应
        if self.is_error_response(response):
            print(f"Error in diary summary generation: {response}")
            return None
        
        # 清理响应（去除可能的格式标记）
        summary = response.strip()
        if not summary:
            return None
        
        return {
            "date": date_str,
            "timestamp": timestamp,
            "session_id": session_id,
            "character": character,
            "summary": summary
        }
    
    async def generate_diary_summary_from_temp(self, character: str = ""):
        """从临时文件生成摘要"""
        session_data = self.load_session_temp()
        if not session_data or not session_data.get("messages"):
            return None
        
        # 使用临时文件中的消息进行生成
        messages = session_data.get("messages", [])
        if not messages:
            return None
        
        # 使用临时文件中的角色，如果没有则使用传入的角色
        session_character = session_data.get("character") or character
        
        entry = await self.generate_diary_summary(messages, session_character)
        return entry
    
    def add_diary_entry(self, entry: Dict):
        """添加日记条目到日记文件"""
        if not entry:
            return
        
        if "entries" not in self.diary_data:
            self.diary_data["entries"] = []
        
        self.diary_data["entries"].append(entry)
        
        # 限制条目数量（保留最近N条）
        if len(self.diary_data["entries"]) > self.max_entries:
            self.diary_data["entries"] = self.diary_data["entries"][-self.max_entries:]
        
        # 保存到文件
        self.save_diary()
    
    def load_user_profile(self) -> Dict:
        """加载用户档案"""
        if not self.user_profile_file.exists():
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": None,
                "name": None,
                "age": None,
                "occupation": None,
                "interests": [],
                "preferences": {},
                "goals": [],
                "habits": [],
                "english_level": "beginner",  # 新增：beginner/elementary/intermediate/advanced
                "english_level_description": "",  # 新增：英文水平描述
                "other_info": {}
            }
        
        try:
            with open(self.user_profile_file, "r", encoding="utf-8") as f:
                profile = json.load(f)
                # 确保所有必需字段存在
                if "version" not in profile:
                    profile["version"] = "1.0"
                if "created_at" not in profile:
                    profile["created_at"] = datetime.now().isoformat()
                # 确保英文水平字段存在
                if "english_level" not in profile:
                    profile["english_level"] = "beginner"
                if "english_level_description" not in profile:
                    profile["english_level_description"] = ""
                return profile
        except Exception as e:
            print(f"Error loading user profile: {e}")
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
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
                "other_info": {}
            }
    
    def save_user_profile(self):
        """保存用户档案"""
        self.user_profile["last_updated"] = datetime.now().isoformat()
        
        try:
            # 确保目录存在
            self.user_profile_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.user_profile_file, "w", encoding="utf-8") as f:
                json.dump(self.user_profile, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving user profile: {e}")
            import traceback
            traceback.print_exc()
    
    def get_user_profile_context(self) -> str:
        """获取用户档案上下文"""
        if not self.user_profile or not any([
            self.user_profile.get("name"),
            self.user_profile.get("age"),
            self.user_profile.get("occupation"),
            self.user_profile.get("interests"),
            self.user_profile.get("preferences")
        ]):
            return ""
        
        context_parts = []
        
        if self.user_profile.get("name"):
            context_parts.append(f"姓名：{self.user_profile['name']}")
        if self.user_profile.get("age"):
            context_parts.append(f"年龄：{self.user_profile['age']}")
        if self.user_profile.get("occupation"):
            context_parts.append(f"职业：{self.user_profile['occupation']}")
        if self.user_profile.get("interests"):
            interests = ", ".join(self.user_profile["interests"])
            context_parts.append(f"兴趣：{interests}")
        if self.user_profile.get("preferences"):
            prefs = ", ".join([f"{k}: {v}" for k, v in self.user_profile["preferences"].items()])
            context_parts.append(f"偏好：{prefs}")
        if self.user_profile.get("goals"):
            goals = ", ".join(self.user_profile["goals"])
            context_parts.append(f"目标：{goals}")
        if self.user_profile.get("habits"):
            habits = ", ".join(self.user_profile["habits"])
            context_parts.append(f"习惯：{habits}")
        
        # 添加英文水平信息
        if self.user_profile.get("english_level"):
            level_map = {
                "beginner": "初级（A1-A2）",
                "elementary": "基础（A2-B1）",
                "intermediate": "中级（B1-B2）",
                "advanced": "高级（B2-C1）"
            }
            level_display = level_map.get(self.user_profile["english_level"], self.user_profile["english_level"])
            context_parts.append(f"英文水平：{level_display}")
            if self.user_profile.get("english_level_description"):
                context_parts.append(f"英文水平描述：{self.user_profile['english_level_description']}")
        
        if context_parts:
            return "\n".join(context_parts)
        return ""
    
    def is_first_conversation(self) -> bool:
        """判断是否是第一次沟通（检查用户档案是否已有基本信息）"""
        if not self.user_profile:
            return True
        
        # 检查是否有基本信息：姓名、职业、兴趣中的至少一个
        has_basic_info = (
            self.user_profile.get("name") or
            self.user_profile.get("occupation") or
            (self.user_profile.get("interests") and len(self.user_profile["interests"]) > 0)
        )
        
        return not has_basic_info
    
    def update_english_level(self, level: str, description: str = ""):
        """更新用户英文水平"""
        valid_levels = ["beginner", "elementary", "intermediate", "advanced"]
        if level not in valid_levels:
            print(f"Invalid english level: {level}, must be one of {valid_levels}")
            return
        
        self.user_profile["english_level"] = level
        if description:
            self.user_profile["english_level_description"] = description
        self.save_user_profile()
        print(f"English level updated to: {level}")
    
    async def extract_user_info(self, conversation_text: str):
        """从对话中提取用户关键信息（严格模式：只提取明确提到的内容）"""
        import asyncio
        from .app import chatgpt_streamed
        
        extract_prompt = f"""请从以下对话中提取用户明确提到的关键信息，以JSON格式返回。

重要要求：
1. 只提取对话中明确提到的信息，不要推断或添加细节
2. 如果用户说"我叫张磊"，提取name为"张磊"
3. 如果用户说"我喜欢篮球和电影"，提取interests为["篮球", "电影"]
4. 如果信息不明确或未提到，使用null或空数组/对象

对话内容：
{conversation_text}

请提取以下信息（如果对话中明确提到）：
1. 姓名（name）
2. 年龄（age）
3. 职业（occupation）
4. 兴趣（interests，数组）
5. 偏好（preferences，对象，如语言偏好、学习方式等）
6. 目标（goals，数组）
7. 习惯（habits，数组）
8. 其他重要信息（other_info，对象）

返回格式（JSON）：
{{
    "name": "用户姓名或null",
    "age": "年龄或null",
    "occupation": "职业或null",
    "interests": ["兴趣1", "兴趣2"],
    "preferences": {{"key": "value"}},
    "goals": ["目标1", "目标2"],
    "habits": ["习惯1", "习惯2"],
    "other_info": {{"key": "value"}}
}}

只返回JSON，不要其他说明。如果某项信息不存在，使用null或空数组/对象。"""
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: chatgpt_streamed(
                extract_prompt,
                "你是一个专业的信息提取助手，只提取对话中明确提到的信息，不进行推断。",
                "neutral",
                []
            )
        )
        
        # 检查是否为错误响应
        if self.is_error_response(response):
            print(f"Error in user info extraction: {response}")
            return None
        
        # 尝试解析JSON
        try:
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                extracted_info = json.loads(json_str)
                
                # 更新用户档案（合并新信息）
                self.update_user_profile(extracted_info)
                return extracted_info
        except Exception as e:
            print(f"Error parsing extracted user info: {e}")
            print(f"Response: {response[:200]}")
        
        return None
    
    def update_user_profile(self, new_info: Dict):
        """更新用户档案（合并新信息）"""
        if not new_info:
            return
        
        timestamp = datetime.now().isoformat()
        
        # 更新基本信息（只更新空值，不覆盖已有信息）
        if new_info.get("name") and not self.user_profile.get("name"):
            self.user_profile["name"] = new_info["name"]
        if new_info.get("age") and not self.user_profile.get("age"):
            self.user_profile["age"] = new_info["age"]
        if new_info.get("occupation") and not self.user_profile.get("occupation"):
            self.user_profile["occupation"] = new_info["occupation"]
        
        # 合并数组（去重）
        if new_info.get("interests"):
            existing = set(self.user_profile.get("interests", []))
            new_interests = set(new_info["interests"])
            self.user_profile["interests"] = list(existing | new_interests)
        
        if new_info.get("goals"):
            existing = set(self.user_profile.get("goals", []))
            new_goals = set(new_info["goals"])
            self.user_profile["goals"] = list(existing | new_goals)
        
        if new_info.get("habits"):
            existing = set(self.user_profile.get("habits", []))
            new_habits = set(new_info["habits"])
            self.user_profile["habits"] = list(existing | new_habits)
        
        # 合并对象
        if new_info.get("preferences"):
            if "preferences" not in self.user_profile:
                self.user_profile["preferences"] = {}
            self.user_profile["preferences"].update(new_info["preferences"])
        
        if new_info.get("other_info"):
            if "other_info" not in self.user_profile:
                self.user_profile["other_info"] = {}
            self.user_profile["other_info"].update(new_info["other_info"])
        
        # 更新时间戳
        self.user_profile["last_updated"] = timestamp
        
        # 保存
        self.save_user_profile()
    
    async def generate_english_dialogue(self, today_chinese_summary: str = "", dialogue_length: str = "auto"):
        """基于今天的中文对话和历史记忆生成英文教学对话"""
        import asyncio
        from .app import chatgpt_streamed
        
        # 对话长度映射
        DIALOGUE_LENGTH_MAP = {
            "short": {"beginner": 8, "elementary": 10, "intermediate": 12, "advanced": 15},
            "medium": {"beginner": 12, "elementary": 15, "intermediate": 18, "advanced": 20},
            "long": {"beginner": 15, "elementary": 18, "intermediate": 22, "advanced": 25}
        }
        
        # 获取用户档案和记忆上下文
        user_profile = self.get_user_profile_context()
        memory_context = self.get_memory_context()
        
        # 获取英文水平
        english_level = self.user_profile.get("english_level", "beginner")
        english_level_map = {
            "beginner": "初级（A1-A2）",
            "elementary": "基础（A2-B1）",
            "intermediate": "中级（B1-B2）",
            "advanced": "高级（B2-C1）"
        }
        level_description = english_level_map.get(english_level, "初级")
        
        # 确定对话句数
        if dialogue_length == "auto":
            dialogue_length = "medium"  # 默认使用medium
        
        target_sentences = DIALOGUE_LENGTH_MAP.get(dialogue_length, DIALOGUE_LENGTH_MAP["medium"]).get(english_level, 15)
        
        # 构建提示词
        prompt = f"""基于以下信息，生成一段适合用户的英文教学对话内容。

用户信息：
{user_profile if user_profile else "暂无用户信息"}

历史记忆：
{memory_context if memory_context else "暂无历史记忆"}

今天的中文对话摘要：
{today_chinese_summary if today_chinese_summary else "无"}

用户英文水平：{level_description}

要求：
1. 生成一段自然的英文对话（约{target_sentences}句），对话内容要与用户今天聊的话题相关
2. 根据用户的英文水平（{level_description}）调整词汇和语法难度
3. 对话要实用、贴近生活，符合用户的兴趣和职业
4. 只返回英文对话内容，不要中文解释
5. 格式：每句话一行，用 "A: " 和 "B: " 表示对话双方
6. 对话要自然流畅，像真实的口语交流

示例格式：
A: Hi, how are you today?
B: I'm doing great, thanks for asking!
A: That's wonderful to hear.
...

现在生成对话："""
        
        # 调用AI生成
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: chatgpt_streamed(
                prompt,
                "你是一个专业的英语教学助手，能够根据用户的水平和兴趣生成个性化的英文对话。",
                "neutral",
                []
            )
        )
        
        if self.is_error_response(response):
            print(f"Error generating english dialogue: {response}")
            return None
        
        return response.strip()
