import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class SummaryMemorySystem:
    """基于结构化事实的记忆系统，只存储真实对话内容，不虚构信息"""
    
    def __init__(self, 
                 memory_file=None,
                 max_facts=None):
        # 获取项目根目录（app 的父目录）
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(current_file_dir)
        
        # 从环境变量读取配置，如果没有则使用默认值（相对于项目根目录）
        if memory_file:
            # 如果提供了路径，使用提供的路径
            self.facts_file = Path(memory_file)
        else:
            # 从环境变量读取，或使用默认路径
            env_memory_file = os.getenv("MEMORY_FILE")
            if env_memory_file:
                # 如果是绝对路径，直接使用；如果是相对路径，相对于项目根目录
                if os.path.isabs(env_memory_file):
                    self.facts_file = Path(env_memory_file)
                else:
                    self.facts_file = Path(project_dir) / env_memory_file
            else:
                # 默认路径：项目根目录下的 memory/facts.json
                self.facts_file = Path(project_dir) / "memory" / "facts.json"
        
        self.max_facts = max_facts or int(os.getenv("MEMORY_MAX_FACTS", "200"))
        
        # 确保目录存在
        self.facts_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_temp_file = self.facts_file.parent / "session_temp.json"
        self.user_profile_file = self.facts_file.parent / "user_profile.json"
        self.facts_data = self.load_facts()
        self.user_profile = self.load_user_profile()
        
        # 打印调试信息
        print(f"Memory system initialized:")
        print(f"  Facts file: {self.facts_file}")
        print(f"  Session temp: {self.session_temp_file}")
        print(f"  User profile: {self.user_profile_file}")
        
    def load_facts(self) -> Dict:
        """加载事实文件"""
        if not self.facts_file.exists():
            return {
                "version": "1.0",
                "last_updated": None,
                "facts": []
            }
        
        try:
            with open(self.facts_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading facts: {e}")
            return {
                "version": "1.0",
                "last_updated": None,
                "facts": []
            }
    
    def save_facts(self):
        """保存事实到文件"""
        self.facts_data["last_updated"] = datetime.now().isoformat()
        
        try:
            # 确保目录存在
            self.facts_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.facts_file, "w", encoding="utf-8") as f:
                json.dump(self.facts_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving facts: {e}")
            import traceback
            traceback.print_exc()
    
    def get_memory_context(self) -> str:
        """获取记忆上下文，基于真实事实和用户档案"""
        # 获取当前日期
        today = datetime.now()
        today_str = today.strftime("%Y年%m月%d日")
        today_iso = today.strftime("%Y-%m-%d")
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]
        
        # 获取用户档案
        user_profile = self.get_user_profile_context()
        
        # 获取最近的事实记录（最近30条）
        recent_facts = self.facts_data.get("facts", [])[-30:]
        
        # 构建上下文
        context_parts = [f"[当前时间信息]\n今天是{today_str}（{weekday}），日期：{today_iso}"]
        
        if user_profile:
            context_parts.append(f"[用户档案信息]\n{user_profile}")
        
        if recent_facts:
            # 按日期分组事实
            facts_by_date = {}
            for fact in recent_facts:
                date_str = fact.get("date", "")
                if date_str:
                    if date_str not in facts_by_date:
                        facts_by_date[date_str] = []
                    facts_by_date[date_str].append(fact)
            
            # 生成事实列表（带相对时间标签）
            fact_entries = []
            for date_str in sorted(facts_by_date.keys())[-10:]:  # 最近10天的记录
                time_label = self.get_relative_time_label(date_str)
                date_facts = facts_by_date[date_str]
                fact_texts = [f.get("content", "") for f in date_facts if f.get("content")]
                if fact_texts:
                    fact_entries.append(f"{time_label}（{date_str}）：{'；'.join(fact_texts[:3])}")  # 每天最多3条
            
            if fact_entries:
                context_parts.append(f"[最近的事实记录]\n" + "\n".join(fact_entries))
        
        if len(context_parts) == 1:  # 只有时间信息
            return ""
        
        context = "\n\n".join(context_parts)
        context += f"""

请根据以上记忆与用户对话：
1. 明确知道今天是{today_str}
2. 如果用户提到"昨天"、"今天"、"明天"，要能准确理解
3. 可以主动提及之前的事实记录，如"你昨天说..."、"你前天提到..."
4. 可以追问后续进展，如"你之前提到的...现在怎么样了？"
5. 保持对话的连贯性和时间感
6. 使用相对时间概念（昨天、前天、上周等）让对话更自然
7. 如果知道用户的姓名、兴趣等信息，要自然地使用这些信息
8. 重要：只能基于以上真实记录的事实进行对话，不要虚构或添加不存在的信息
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
    
    async def extract_facts_from_session(self, session_messages: List[Dict], character: str):
        """从会话中提取结构化事实（只提取对话中明确提到的内容）"""
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
        
        # 严格的事实提取提示词
        extract_prompt = f"""请从以下对话中提取用户明确提到的真实事实，以JSON格式返回。

重要要求：
1. 只提取对话中明确提到的内容，不要添加任何细节或推断
2. 不要虚构或补充不存在的信息
3. 如果用户说"我喜欢篮球"，提取为事实；如果用户说"可能喜欢"，不要提取
4. 每个事实必须是对话中直接表达的

对话内容：
{conversation_text}

请提取以下类型的事实（如果对话中明确提到）：
- user_info: 用户的基本信息（姓名、年龄、职业等）
- interest: 用户的兴趣、爱好
- goal: 用户的目标、计划
- event: 用户提到的事件、活动
- preference: 用户的偏好、习惯

返回格式（JSON数组）：
[
  {{
    "category": "user_info|interest|goal|event|preference",
    "content": "用户说：我喜欢打篮球",
    "extracted_data": {{
      "type": "interest",
      "value": "篮球"
    }}
  }},
  {{
    "category": "user_info",
    "content": "用户说：我叫张磊",
    "extracted_data": {{
      "type": "name",
      "value": "张磊"
    }}
  }}
]

只返回JSON数组，不要其他说明。如果对话中没有明确的事实，返回空数组 []。"""
        
        # 将同步函数包装成异步调用
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: chatgpt_streamed(
                extract_prompt,
                "你是一个专业的事实提取助手，只提取对话中明确提到的真实内容，不添加任何细节。",
                "neutral",
                []
            )
        )
        
        # 检查是否为错误响应
        if self.is_error_response(response):
            print(f"Error in fact extraction: {response}")
            return []
        
        # 尝试解析JSON
        facts = []
        try:
            # 提取JSON部分
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                extracted_facts = json.loads(json_str)
                
                # 验证并格式化事实
                for fact in extracted_facts:
                    if isinstance(fact, dict) and fact.get("content"):
                        facts.append({
                            "id": f"fact_{len(self.facts_data.get('facts', [])) + len(facts) + 1:06d}",
                            "date": date_str,
                            "timestamp": timestamp,
                            "session_id": session_id,
                            "character": character,
                            "category": fact.get("category", "other"),
                            "content": fact.get("content", ""),
                            "extracted_data": fact.get("extracted_data", {})
                        })
        except Exception as e:
            print(f"Error parsing extracted facts: {e}")
            print(f"Response: {response[:500]}")
        
        return facts
    
    async def extract_facts_from_temp(self, character: str = ""):
        """从临时文件提取事实"""
        session_data = self.load_session_temp()
        if not session_data or not session_data.get("messages"):
            return []
        
        # 使用临时文件中的消息进行提取
        messages = session_data.get("messages", [])
        if not messages:
            return []
        
        # 使用临时文件中的角色，如果没有则使用传入的角色
        session_character = session_data.get("character") or character
        
        facts = await self.extract_facts_from_session(messages, session_character)
        return facts
    
    def add_fact(self, fact: Dict):
        """添加事实到事实文件"""
        if "facts" not in self.facts_data:
            self.facts_data["facts"] = []
        
        self.facts_data["facts"].append(fact)
        
        # 限制事实数量（保留最近N条）
        if len(self.facts_data["facts"]) > self.max_facts:
            self.facts_data["facts"] = self.facts_data["facts"][-self.max_facts:]
        
        # 保存到文件
        self.save_facts()
    
    def add_facts(self, facts: List[Dict]):
        """批量添加事实"""
        if not facts:
            return
        
        if "facts" not in self.facts_data:
            self.facts_data["facts"] = []
        
        self.facts_data["facts"].extend(facts)
        
        # 限制事实数量（保留最近N条）
        if len(self.facts_data["facts"]) > self.max_facts:
            self.facts_data["facts"] = self.facts_data["facts"][-self.max_facts:]
        
        # 保存到文件
        self.save_facts()
    
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
        
        if context_parts:
            return "\n".join(context_parts)
        return ""
    
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
