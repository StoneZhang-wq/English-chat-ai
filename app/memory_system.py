import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 英语水平配置
ENGLISH_LEVELS = {
    "minimal": {
        "name": "极简",
        "description": "极简级，最简单的日常用语，适合2句话对话",
        "difficulty": {
            "vocabulary": "最基础词汇（500词以内），如 hello, thank you, yes, no, how are you",
            "vocab_scope": "只使用超高频生活用词，避免抽象或学术词",
            "vocab_avoid": "避免多音节或罕见词（如 sophisticated, comprehensive）",
            "grammar": "仅现在时，最简单的陈述句和疑问句",
            "grammar_structures": "只用主谓或主谓宾；不使用从句",
            "tenses": ["present simple"],
            "idioms": False,
            "idiom_ratio": "0%",
            "slang": False,
            "sentence_length": "3-6词",
            "sentence_length_range": "3-6词",
            "complexity": "最简单的短句，主谓结构",
            "info_density": "每句只表达1个信息点"
        }
    },
    "beginner": {
        "name": "初级（A1）",
        "description": "入门级，基础词汇和简单句型",
        "difficulty": {
            "vocabulary": "基础词汇（1000词以内）",
            "vocab_scope": "高频日常用词，避免抽象名词和复杂动词",
            "vocab_avoid": "避免高阶词（如 elaborate, nuanced）",
            "grammar": "现在时、简单过去时、基本疑问句",
            "grammar_structures": "主谓宾为主，允许简单并列句",
            "tenses": ["present simple", "past simple"],
            "idioms": False,
            "idiom_ratio": "0-5%",
            "slang": False,
            "sentence_length": "5-8词",
            "sentence_length_range": "5-8词",
            "complexity": "简单句，主谓宾结构",
            "info_density": "每句1个信息点，避免多层信息"
        }
    },
    "elementary": {
        "name": "基础（A2）",
        "description": "基础级，日常交流词汇",
        "difficulty": {
            "vocabulary": "日常词汇（2000词以内）",
            "vocab_scope": "日常场景词汇为主，可少量加入生活短语",
            "vocab_avoid": "避免学术词或专业术语",
            "grammar": "现在时、过去时、将来时、现在进行时",
            "grammar_structures": "简单并列句，允许because/and连接",
            "tenses": ["present simple", "past simple", "future simple", "present continuous"],
            "idioms": "少量常见习语（如 'how are you', 'nice to meet you'）",
            "idiom_ratio": "5-10%",
            "slang": False,
            "sentence_length": "8-12词",
            "sentence_length_range": "8-12词",
            "complexity": "简单句和并列句",
            "info_density": "每句1-2个信息点"
        }
    },
    "pre_intermediate": {
        "name": "准中级（A2-B1）",
        "description": "准中级，开始使用复合句",
        "difficulty": {
            "vocabulary": "扩展词汇（3000词以内）",
            "vocab_scope": "生活与学习场景常用词，允许适度抽象词",
            "vocab_avoid": "避免罕见学术词或文学词",
            "grammar": "所有基本时态、条件句、被动语态",
            "grammar_structures": "允许1个从句（because/when/if）",
            "tenses": ["all basic tenses", "present perfect", "past continuous", "conditional"],
            "idioms": "常见习语和短语动词",
            "idiom_ratio": "10-15%",
            "slang": "少量日常俚语",
            "sentence_length": "10-15词",
            "sentence_length_range": "10-15词",
            "complexity": "复合句，从句",
            "info_density": "每句1-2个信息点，允许补充细节"
        }
    },
    "intermediate": {
        "name": "中级（B1-B2）",
        "description": "中级，流利日常交流",
        "difficulty": {
            "vocabulary": "丰富词汇（5000词以内）",
            "vocab_scope": "常用进阶词+语境化表达",
            "vocab_avoid": "避免过度书面或极少见词汇",
            "grammar": "所有时态、虚拟语气、复杂语法结构",
            "grammar_structures": "允许2个从句或非限定性从句",
            "tenses": ["all tenses", "present perfect continuous", "past perfect", "subjunctive"],
            "idioms": "常用习语和表达",
            "idiom_ratio": "15-20%",
            "slang": "日常俚语和口语表达",
            "sentence_length": "12-18词",
            "sentence_length_range": "12-18词",
            "complexity": "复杂复合句，多种从句",
            "info_density": "每句2个信息点，允许对比或解释"
        }
    },
    "upper_intermediate": {
        "name": "中高级（B2）",
        "description": "中高级，复杂话题讨论",
        "difficulty": {
            "vocabulary": "高级词汇（8000词以内）",
            "vocab_scope": "进阶与抽象表达，含部分领域词汇",
            "vocab_avoid": "避免生僻学术词堆砌",
            "grammar": "所有语法结构，包括倒装、强调句",
            "grammar_structures": "允许多重从句与强调结构",
            "tenses": ["all tenses including perfect continuous forms"],
            "idioms": "丰富习语和地道表达",
            "idiom_ratio": "20-25%",
            "slang": "常见俚语和流行语",
            "sentence_length": "15-22词",
            "sentence_length_range": "15-22词",
            "complexity": "复杂句式，多种语法结构混合",
            "info_density": "每句2-3个信息点"
        }
    },
    "advanced": {
        "name": "高级（B2-C1）",
        "description": "高级，接近母语水平",
        "difficulty": {
            "vocabulary": "高级词汇和学术词汇（10000+词）",
            "vocab_scope": "高级抽象表达+部分学术用语",
            "vocab_avoid": "避免极端冷僻或专业术语堆叠",
            "grammar": "所有高级语法，包括修辞手法",
            "grammar_structures": "允许复杂从句、倒装、强调与修辞",
            "tenses": ["all tenses with nuanced usage"],
            "idioms": "大量习语、谚语和地道表达",
            "idiom_ratio": "25-30%",
            "slang": "丰富俚语、网络用语和流行语",
            "sentence_length": "18-25词",
            "sentence_length_range": "18-25词",
            "complexity": "复杂句式，多种修辞手法",
            "info_density": "每句2-3个信息点，允许抽象表达"
        }
    }
}

class DiaryMemorySystem:
    """简化版日记式记忆系统，使用文本摘要存储对话内容"""
    
    def __init__(self, 
                 memory_file=None,
                 max_entries=None,
                 cefr_vocab_file=None,
                 account_name=None):
        # 获取项目根目录（app 的父目录）
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(current_file_dir)
        
        # 账号名称（用于创建独立的记忆文件夹）
        self.account_name = account_name
        
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
                # 如果有账号名称，使用账号专属文件夹；否则使用默认路径
                if self.account_name:
                    # 清理账号名称，移除不安全字符
                    safe_account_name = "".join(c for c in self.account_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_account_name = safe_account_name.replace(' ', '_')
                    if not safe_account_name:
                        safe_account_name = "default"
                    # 账号专属路径：memory/accounts/{account_name}/diary.json
                    self.diary_file = Path(project_dir) / "memory" / "accounts" / safe_account_name / "diary.json"
                else:
                    # 默认路径：项目根目录下的 memory/diary.json
                    self.diary_file = Path(project_dir) / "memory" / "diary.json"
        
        self.max_entries = max_entries or int(os.getenv("MEMORY_MAX_ENTRIES", "50"))
        
        # 确保目录存在
        self.diary_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_temp_file = self.diary_file.parent / "session_temp.json"
        self.user_profile_file = self.diary_file.parent / "user_profile.json"
        
        # CEFR词汇表文件路径
        if cefr_vocab_file:
            self.cefr_vocab_file = Path(cefr_vocab_file)
        else:
            self.cefr_vocab_file = self.diary_file.parent / "cefr_vocabulary.json"
        
        self.diary_data = self.load_diary()
        self.user_profile = self.load_user_profile()
        self.cefr_vocab_data = self.load_cefr_vocabulary()
        
        # 打印调试信息
        print(f"Memory system initialized:")
        print(f"  Diary file: {self.diary_file}")
        print(f"  Session temp: {self.session_temp_file}")
        print(f"  User profile: {self.user_profile_file}")
        print(f"  CEFR vocabulary: {self.cefr_vocab_file}")
        
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
            level_key = self.user_profile["english_level"]
            level_config = ENGLISH_LEVELS.get(level_key)
            if level_config:
                level_display = f"{level_config['name']} - {level_config['description']}"
            else:
                level_display = level_key
            context_parts.append(f"英文水平：{level_display}")
            if self.user_profile.get("english_level_description"):
                context_parts.append(f"英文水平描述：{self.user_profile['english_level_description']}")
        
        if context_parts:
            return "\n".join(context_parts)
        return ""
    
    def load_cefr_vocabulary(self) -> Dict:
        """加载CEFR分级词汇表"""
        try:
            if self.cefr_vocab_file.exists():
                with open(self.cefr_vocab_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    vocab_levels = len(data.get('vocabulary', {}))
                    print(f"CEFR vocabulary loaded: {vocab_levels} levels")
                    return data
            else:
                print(f"CEFR vocabulary file not found: {self.cefr_vocab_file}")
                return {}
        except Exception as e:
            print(f"Error loading CEFR vocabulary: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_cefr_vocab_for_level(self, level: str) -> Dict:
        """根据难度级别获取对应的CEFR词汇、短语和句型
        
        Args:
            level: 难度级别 (minimal/beginner/elementary/pre_intermediate/intermediate/upper_intermediate/advanced)
        
        Returns:
            包含vocabulary, phrases, grammar_patterns的字典
        """
        if not self.cefr_vocab_data:
            return {}
        
        # 映射难度级别到CEFR级别
        level_mapping = {
            "minimal": "A1",
            "beginner": "A1",
            "elementary": "A2",
            "pre_intermediate": "B1",
            "intermediate": "B1",
            "upper_intermediate": "B2",
            "advanced": "C1"
        }
        
        cefr_level = level_mapping.get(level, "A1")
        vocab_data = self.cefr_vocab_data.get("vocabulary", {})
        phrases_data = self.cefr_vocab_data.get("phrases", {})
        patterns_data = self.cefr_vocab_data.get("grammar_patterns", {})
        
        # 获取当前级别及以下级别的词汇（允许使用更简单的词汇）
        result = {
            "vocabulary": [],
            "phrases": [],
            "grammar_patterns": []
        }
        
        # CEFR级别顺序
        cefr_order = ["A1", "A2", "B1", "B2", "C1"]
        target_index = cefr_order.index(cefr_level) if cefr_level in cefr_order else 0
        
        # 收集当前级别及以下级别的词汇（最多包含当前级别和上一级别）
        for i in range(max(0, target_index - 1), target_index + 1):
            level_key = cefr_order[i]
            if level_key in vocab_data:
                result["vocabulary"].extend(vocab_data[level_key])
            if level_key in phrases_data:
                result["phrases"].extend(phrases_data[level_key])
            if level_key in patterns_data:
                result["grammar_patterns"].extend(patterns_data[level_key])
        
        # 限制数量，避免prompt过长
        result["vocabulary"] = result["vocabulary"][:50]  # 最多50个词汇
        result["phrases"] = result["phrases"][:20]  # 最多20个短语
        result["grammar_patterns"] = result["grammar_patterns"][:15]  # 最多15个句型
        
        return result
    
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
        valid_levels = ["minimal", "beginner", "elementary", "pre_intermediate", "intermediate", "upper_intermediate", "advanced"]
        if level not in valid_levels:
            print(f"Invalid english level: {level}, must be one of {valid_levels}")
            return
        
        self.user_profile["english_level"] = level
        if description:
            self.user_profile["english_level_description"] = description
        self.save_user_profile()
        level_name = ENGLISH_LEVELS.get(level, {}).get("name", level)
        print(f"English level updated to: {level_name}")
    
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
    
    def get_difficulty_instructions(self, level_config):
        """根据水平配置生成难度要求"""
        diff = level_config["difficulty"]
        instructions = []
        
        instructions.append(f"【词汇难度】{diff['vocabulary']}")
        if diff.get("vocab_scope"):
            instructions.append(f"【词汇范围】{diff['vocab_scope']}")
        if diff.get("vocab_avoid"):
            instructions.append(f"【用词限制】{diff['vocab_avoid']}")
        instructions.append(f"【语法结构】{diff['grammar']}")
        if diff.get("grammar_structures"):
            instructions.append(f"【句型限制】{diff['grammar_structures']}")
        instructions.append(f"【时态使用】必须自然使用以下时态：{', '.join(diff['tenses'])}")
        # 移除句子长度描述（这是每句话的长度，不是总句数，避免与总句数要求混淆）
        instructions.append(f"【句式复杂度】{diff['complexity']}")
        if diff.get("info_density"):
            instructions.append(f"【信息密度】{diff['info_density']}")
        
        if diff.get('idioms'):
            if diff['idioms'] is True:
                instructions.append("【习语使用】必须包含常用习语和短语动词")
            else:
                instructions.append(f"【习语使用】{diff['idioms']}")
        if diff.get("idiom_ratio"):
            instructions.append(f"【习语比例】约{diff['idiom_ratio']}的句子包含习语或短语动词")
        
        if diff.get('slang'):
            if diff['slang'] is True:
                instructions.append("【俚语使用】必须包含日常俚语和口语表达")
            elif diff['slang']:
                instructions.append(f"【俚语使用】{diff['slang']}")
        
        instructions.append("【硬性要求】不要写超出当前难度的词汇或语法；宁可更简单也不要更复杂")
        
        return "\n".join(instructions)
    
    async def generate_english_dialogue(self, today_chinese_summary: str = "", 
                                        dialogue_length: str = "auto",
                                        difficulty_level: str = None,
                                        custom_sentence_count: int = None):
        """基于今天的中文对话和历史记忆生成英文教学对话
        
        Args:
            today_chinese_summary: 今天的中文对话摘要
            dialogue_length: 对话长度 (short/medium/long/custom/auto)
            difficulty_level: 难度水平 (beginner/elementary/pre_intermediate/intermediate/upper_intermediate/advanced)
                            如果为None，使用用户当前水平
            custom_sentence_count: 自定义句数（2-30）
        """
        import asyncio
        from .app import chatgpt_streamed
        
        # 对话长度映射（长度优先，不受难度影响）
        DIALOGUE_LENGTH_MAP = {
            "short": 8,
            "medium": 14,
            "long": 20
        }
        
        # 获取用户档案和记忆上下文
        user_profile = self.get_user_profile_context()
        memory_context = self.get_memory_context()
        
        # 获取练习记忆（最近的10条），只使用有复习笔记的记录
        practice_memories = self.get_practice_memories(limit=10)
        # 过滤掉没有复习笔记的记录
        practice_memories_with_review = [m for m in practice_memories if m.get("review_notes")]
        practice_memories_context = ""
        if practice_memories_with_review:
            practice_memories_context = "\n\n【历史练习记忆】（用于参考，生成更个性化的对话）：\n"
            for memory in practice_memories_with_review:
                topic = memory.get("dialogue_topic", "未知主题")
                date = memory.get("date", "")
                review_notes = memory.get("review_notes", {})
                
                # 提取词汇信息
                vocabulary = review_notes.get("vocabulary", {})
                difficult_words = vocabulary.get("difficult_words", [])
                key_words = vocabulary.get("key_words", [])
                
                # 提取语法点
                grammar_points = review_notes.get("grammar", [])
                grammar_summary = []
                for g in grammar_points[:3]:  # 只取前3个语法点
                    grammar_summary.append(g.get("point", ""))
                
                # 提取错误纠正
                corrections = review_notes.get("corrections", [])
                corrections_summary = []
                for c in corrections[:2]:  # 只取前2个错误
                    corrections_summary.append(c.get("user_said", ""))
                
                # 提取学习建议
                suggestions = review_notes.get("suggestions", [])
                
                # 构建详细信息
                memory_info = f"- {date} {topic}主题练习\n"
                if difficult_words:
                    memory_info += f"  易错词汇：{', '.join(difficult_words[:5])}\n"
                if key_words:
                    memory_info += f"  重点词汇：{', '.join(key_words[:5])}\n"
                if grammar_summary:
                    memory_info += f"  语法要点：{', '.join(grammar_summary)}\n"
                if corrections_summary:
                    memory_info += f"  常见错误：{', '.join(corrections_summary)}\n"
                if suggestions:
                    memory_info += f"  学习建议：{suggestions[0] if suggestions else ''}\n"
                
                practice_memories_context += memory_info
        
        # 获取用户当前水平
        user_level = self.user_profile.get("english_level", "beginner")
        
        # 确定使用的难度水平
        target_level = difficulty_level if difficulty_level else user_level
        
        # 获取该水平的配置（如果不存在，默认使用beginner）
        if target_level not in ENGLISH_LEVELS:
            target_level = "beginner"
        level_config = ENGLISH_LEVELS.get(target_level, ENGLISH_LEVELS["beginner"])
        
        # 生成难度要求说明
        difficulty_instructions = self.get_difficulty_instructions(level_config)
        
        # 确定对话句数（长度优先）
        if dialogue_length == "auto":
            dialogue_length = "medium"
        
        if dialogue_length == "custom":
            try:
                custom_count = int(custom_sentence_count) if custom_sentence_count is not None else None
            except (TypeError, ValueError):
                custom_count = None
            if custom_count is None or custom_count < 2 or custom_count > 30:
                custom_count = 14
            target_sentences = custom_count
        else:
            target_sentences = DIALOGUE_LENGTH_MAP.get(dialogue_length, DIALOGUE_LENGTH_MAP["medium"])
        
        # 加载CEFR词汇表并生成资料库上下文
        resource_context = ""
        cefr_vocab = self.get_cefr_vocab_for_level(target_level)
        
        if cefr_vocab and (cefr_vocab.get("vocabulary") or cefr_vocab.get("phrases") or cefr_vocab.get("grammar_patterns")):
            vocab_list = cefr_vocab.get("vocabulary", [])
            phrases_list = cefr_vocab.get("phrases", [])
            patterns_list = cefr_vocab.get("grammar_patterns", [])
            
            resource_parts = []
            if vocab_list:
                # 只显示前30个词汇，避免prompt过长
                vocab_display = ", ".join(vocab_list[:30])
                resource_parts.append(f"【推荐词汇】{vocab_display}")
            if phrases_list:
                phrases_display = ", ".join(phrases_list[:15])
                resource_parts.append(f"【常用短语】{phrases_display}")
            if patterns_list:
                patterns_display = ", ".join(patterns_list[:10])
                resource_parts.append(f"【推荐句型】{patterns_display}")
            
            if resource_parts:
                resource_context = "\n".join(resource_parts)
        
        resource_context_block = f"\n\n【CEFR资料库参考】\n{resource_context}" if resource_context else "\n\n【CEFR资料库参考】无（将使用通用词汇）"
        
        # 构建提示词
        topic_instruction = "对话内容要与用户今天聊的话题相关" if today_chinese_summary else "对话内容要基于用户的兴趣、职业和历史对话记录"
        
        prompt = f"""基于以下信息，生成一段适合用户的英文教学对话内容。

【⚠️ 最高优先级：句数限制（不可违反）】
必须生成严格{target_sentences}句对话，这是硬性要求。
- 对话必须正好是{target_sentences}句，不能多也不能少
- 无论难度如何，句数限制优先于所有其他要求
- 如果无法在{target_sentences}句内完成，宁可简化内容也要保证句数

用户信息：
{user_profile if user_profile else "暂无用户信息"}

历史记忆：
{memory_context if memory_context else "暂无历史记忆"}

今天的中文对话摘要：
{today_chinese_summary if today_chinese_summary else "无（将基于历史记忆生成）"}
{practice_memories_context}
{resource_context_block}

目标难度水平：{level_config['name']} - {level_config['description']}

【难度要求】（用于控制每句话的用词和句型，不影响总句数）：
{difficulty_instructions}

【内容要求】：
1. 对话必须贴近日常生活，涉及日常沟通场景（如：工作、学习、娱乐、社交、购物、旅行等）
2. 必须自然使用指定的时态，不要刻意堆砌，要让时态使用符合真实对话场景
3. 对话要实用，能帮助用户在实际场景中应用
4. 根据难度水平包含适量的习语、俚语或地道表达（不要过度使用）
5. 对话要自然流畅，像真实的口语交流，不要像教科书
6. 可以基于用户的历史记忆和兴趣来设计对话主题
7. {topic_instruction}

【格式要求】：
- 每句话一行，用 "A: " 和 "B: " 表示对话双方
- 只返回英文对话内容，不要中文解释
- 确保对话连贯，有逻辑性，有真实感

示例格式：
A: Hi, how are you today?
B: I'm doing great, thanks for asking!
A: That's wonderful to hear.
...

现在生成对话："""
        
        # 调用AI生成
        try:
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
        except Exception as e:
            print(f"Error calling chatgpt_streamed: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        if self.is_error_response(response):
            print(f"Error generating english dialogue: {response}")
            return None
        
        if not response or not response.strip():
            print("Error: Empty response from chatgpt_streamed")
            return None
        
        dialogue_text = response.strip()
        
        # 解析对话文本，提取每句对话
        dialogue_lines = []
        lines = dialogue_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('A: '):
                text = line[3:].strip()
                if text:
                    dialogue_lines.append({"speaker": "A", "text": text})
            elif line.startswith('B: '):
                text = line[3:].strip()
                if text:
                    dialogue_lines.append({"speaker": "B", "text": text})
        
        # 如果没有解析到对话，返回原始文本（兼容旧格式）
        if not dialogue_lines:
            print("Warning: No dialogue lines parsed, returning raw text")
            return dialogue_text
        
        # 生成每句对话的音频
        import uuid
        from .app import TTS_PROVIDER, doubao_text_to_speech, openai_text_to_speech, elevenlabs_text_to_speech, kokoro_text_to_speech
        
        # 创建音频存储目录
        dialogue_id = str(uuid.uuid4())[:8]
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(current_file_dir)
        audio_dir = os.path.join(project_dir, "outputs", "english_dialogue", dialogue_id)
        
        try:
            os.makedirs(audio_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating audio directory: {e}")
            import traceback
            traceback.print_exc()
            # 即使目录创建失败，也继续尝试生成音频
        
        # 为每句对话生成音频
        audio_success_count = 0
        for i, line in enumerate(dialogue_lines):
            try:
                # 根据TTS_ENCODING环境变量确定输出格式
                tts_encoding = os.getenv('TTS_ENCODING', 'mp3')
                if TTS_PROVIDER == 'doubao' and tts_encoding == 'mp3':
                    audio_filename = f"{line['speaker']}_{i}.mp3"
                else:
                    audio_filename = f"{line['speaker']}_{i}.wav"
                audio_path = os.path.join(audio_dir, audio_filename)
                
                # 根据TTS_PROVIDER选择相应的TTS函数
                if TTS_PROVIDER == 'doubao':
                    success = await doubao_text_to_speech(line['text'], audio_path)
                    if not success:
                        print(f"Warning: Doubao TTS failed for line {i}")
                        line['audio_url'] = None
                        continue
                elif TTS_PROVIDER == 'openai':
                    await openai_text_to_speech(line['text'], audio_path)
                elif TTS_PROVIDER == 'elevenlabs':
                    success = await elevenlabs_text_to_speech(line['text'], audio_path)
                    if not success:
                        print(f"Warning: ElevenLabs TTS failed for line {i}")
                        line['audio_url'] = None
                        continue
                elif TTS_PROVIDER == 'kokoro':
                    success = await kokoro_text_to_speech(line['text'], audio_path)
                    if not success:
                        print(f"Warning: Kokoro TTS failed for line {i}")
                        line['audio_url'] = None
                        continue
                elif TTS_PROVIDER == 'sparktts':
                    # Spark-TTS需要特殊处理，这里暂时跳过或使用其他TTS
                    print(f"Warning: Spark-TTS not supported for dialogue cards, skipping line {i}")
                    line['audio_url'] = None
                    continue
                else:
                    # 默认使用豆包TTS
                    print(f"Warning: Unknown TTS_PROVIDER '{TTS_PROVIDER}', using Doubao TTS as fallback")
                    success = await doubao_text_to_speech(line['text'], audio_path)
                    if not success:
                        print(f"Warning: Doubao TTS fallback failed for line {i}")
                        line['audio_url'] = None
                        continue
                
                # 检查文件是否成功创建
                if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                    # 生成音频URL（相对路径，前端可以通过静态文件服务访问）
                    audio_url = f"/audio/english_dialogue/{dialogue_id}/{audio_filename}"
                    line['audio_url'] = audio_url
                    line['audio_path'] = audio_path  # 保存完整路径供后端使用
                    audio_success_count += 1
                    print(f"Generated audio for {line['speaker']} line {i}: {audio_url}")
                else:
                    print(f"Warning: Audio file not created or empty for line {i}")
                    line['audio_url'] = None
            except Exception as e:
                print(f"Error generating audio for line {i}: {e}")
                import traceback
                traceback.print_exc()
                line['audio_url'] = None  # 如果生成失败，设置为None
        
        print(f"Audio generation complete: {audio_success_count}/{len(dialogue_lines)} successful")
        
        # 返回包含音频URL的对话数据（即使部分音频生成失败，也返回对话文本）
        return {
            "dialogue_text": dialogue_text,
            "dialogue_lines": dialogue_lines,
            "dialogue_id": dialogue_id
        }
    
    def save_practice_memory(self, practice_data: Dict) -> bool:
        """保存练习记忆到文件（创建新记录）
        
        Args:
            practice_data: 练习数据字典，包含：
                - id: 练习ID（必需）
                - date: 日期
                - timestamp: 时间戳
                - dialogue_topic: 对话主题
                - review_notes: 复习笔记
                - expansion_materials: 场景拓展资料
        
        Returns:
            bool: 是否保存成功
        """
        try:
            practice_memories_file = os.path.join(str(self.diary_file.parent), "practice_memories.json")
            practice_id = practice_data.get("id")
            
            if not practice_id:
                print("Error: practice_id is required")
                return False
            
            # 读取现有数据
            if os.path.exists(practice_memories_file):
                with open(practice_memories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"practices": []}
            
            practices = data.get("practices", [])
            
            # 添加新的练习记忆
            practices.append(practice_data)
            print(f"Practice memory created: {practice_id}")
            
            data["practices"] = practices
            
            # 保存到文件
            with open(practice_memories_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving practice memory: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_practice_memories(self, limit: int = 10) -> List[Dict]:
        """获取最近的练习记忆
        
        Args:
            limit: 返回的记录数量限制
        
        Returns:
            List[Dict]: 练习记忆列表，按时间倒序
        """
        try:
            practice_memories_file = os.path.join(str(self.diary_file.parent), "practice_memories.json")
            
            if not os.path.exists(practice_memories_file):
                return []
            
            with open(practice_memories_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            practices = data.get("practices", [])
            
            # 按时间戳排序（最新的在前）
            practices.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # 返回最近的limit条记录
            return practices[:limit]
            
        except Exception as e:
            print(f"Error loading practice memories: {e}")
            import traceback
            traceback.print_exc()
            return []