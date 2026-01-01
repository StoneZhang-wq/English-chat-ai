import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class SummaryMemorySystem:
    """带时间戳的总结式记忆系统，支持短期记忆文件"""
    
    def __init__(self, 
                 memory_file=None,
                 max_summaries=None,
                 timeline_summaries=None):
        # 从环境变量读取配置，如果没有则使用默认值
        self.memory_file = Path(memory_file or os.getenv("MEMORY_FILE", "memory/summary_memory.json"))
        self.max_summaries = max_summaries or int(os.getenv("MEMORY_MAX_SUMMARIES", "50"))
        self.timeline_summaries = timeline_summaries or int(os.getenv("MEMORY_TIMELINE_SUMMARIES", "20"))
        
        self.memory_file.parent.mkdir(exist_ok=True)
        self.session_temp_file = self.memory_file.parent / "session_temp.json"
        self.memory_data = self.load_memory()
        
    def load_memory(self) -> Dict:
        """加载记忆文件"""
        if not self.memory_file.exists():
            return {
                "version": "1.0",
                "last_updated": None,
                "summaries": [],
                "consolidated_memory": "",
                "timeline_memory": ""
            }
        
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading memory: {e}")
            return {
                "version": "1.0",
                "last_updated": None,
                "summaries": [],
                "consolidated_memory": "",
                "timeline_memory": ""
            }
    
    def get_memory_context(self) -> str:
        """获取记忆上下文，包含当前日期信息"""
        if not self.memory_data.get("summaries"):
            return ""
        
        # 获取当前日期
        today = datetime.now()
        today_str = today.strftime("%Y年%m月%d日")
        today_iso = today.strftime("%Y-%m-%d")
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]
        
        consolidated = self.memory_data.get("consolidated_memory", "")
        timeline = self.memory_data.get("timeline_memory", "")
        
        if not consolidated and not timeline:
            return ""
        
        context = f"""
[当前时间信息]
今天是{today_str}（{weekday}），日期：{today_iso}

[用户记忆]
{consolidated}

[对话时间线]
{timeline}

请根据以上记忆与用户对话：
1. 明确知道今天是{today_str}
2. 如果用户提到"昨天"、"今天"、"明天"，要能准确理解
3. 可以主动提及之前的对话内容，如"你昨天说..."、"你前天提到..."
4. 可以追问后续进展，如"你之前提到的...现在怎么样了？"
5. 保持对话的连贯性和时间感
6. 使用相对时间概念（昨天、前天、上周等）让对话更自然
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
            with open(self.session_temp_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving to session temp file: {e}")
    
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
    
    async def summarize_session(self, session_messages: List[Dict], character: str):
        """使用AI总结会话（带时间戳）"""
        import asyncio
        from .app import chatgpt_streamed
        
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in session_messages
        ])
        
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        timestamp = today.isoformat()
        
        summary_prompt = f"""请总结以下对话的关键信息，提取：
1. 用户的基本信息（姓名、年龄、职业、兴趣等）
2. 用户表达的需求、目标或问题
3. 重要的对话主题和内容
4. 用户的偏好和习惯
5. 用户提到的计划、承诺或后续行动

对话内容：
{conversation_text}

请用简洁的中文总结（200-300字），格式如下：
总结：[对话的主要内容，包含时间相关的信息，如"用户说昨天做了什么"、"用户计划明天做什么"等]
关键点：
- [关键点1]
- [关键点2]
- [关键点3]

只返回总结内容，不要其他说明。"""
        
        # 将同步函数包装成异步调用
        loop = asyncio.get_event_loop()
        summary_response = await loop.run_in_executor(
            None,
            lambda: chatgpt_streamed(
                summary_prompt,
                "你是一个专业的对话总结助手，擅长提取关键信息，特别注意时间相关的信息。",
                "neutral",
                []
            )
        )
        
        # 解析总结
        summary_content = summary_response.split("总结：")[-1].split("关键点：")[0].strip()
        if not summary_content:
            summary_content = summary_response[:200]
        
        # 提取关键点
        key_points = []
        if "关键点：" in summary_response:
            points_section = summary_response.split("关键点：")[1]
            for line in points_section.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    key_points.append(line[2:].strip())
        
        return {
            "session_id": f"{date_str}_{today.strftime('%H-%M-%S')}",
            "date": date_str,
            "timestamp": timestamp,
            "character": character,
            "summary": summary_content,
            "key_points": key_points
        }
    
    async def summarize_session_from_temp(self, character: str = ""):
        """从临时文件总结会话"""
        # #region agent log
        import json as json_module
        try:
            with open(r"c:\Users\uip84\Desktop\编程项目\EnglishApp\voice-chat-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json_module.dumps({"location":"memory_system.py:232","message":"summarize_session_from_temp_start","data":{"character":character},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"G"})+"\n")
        except: pass
        # #endregion
        session_data = self.load_session_temp()
        # #region agent log
        try:
            with open(r"c:\Users\uip84\Desktop\编程项目\EnglishApp\voice-chat-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json_module.dumps({"location":"memory_system.py:235","message":"after_load_in_summarize","data":{"has_data":session_data is not None,"has_messages":session_data.get("messages") if session_data else False},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"G"})+"\n")
        except: pass
        # #endregion
        if not session_data or not session_data.get("messages"):
            return None
        
        # 使用临时文件中的消息进行总结
        messages = session_data.get("messages", [])
        if not messages:
            return None
        
        # 使用临时文件中的角色，如果没有则使用传入的角色
        session_character = session_data.get("character") or character
        
        # #region agent log
        try:
            with open(r"c:\Users\uip84\Desktop\编程项目\EnglishApp\voice-chat-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json_module.dumps({"location":"memory_system.py:245","message":"before_summarize_session","data":{"messages_count":len(messages)},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H"})+"\n")
        except: pass
        # #endregion
        summary_data = await self.summarize_session(messages, session_character)
        # #region agent log
        try:
            with open(r"c:\Users\uip84\Desktop\编程项目\EnglishApp\voice-chat-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json_module.dumps({"location":"memory_system.py:247","message":"after_summarize_session","data":{"has_summary":summary_data is not None},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"H"})+"\n")
        except: pass
        # #endregion
        
        return summary_data
    
    def add_summary(self, summary_data: Dict):
        """添加总结到记忆文件"""
        if "summaries" not in self.memory_data:
            self.memory_data["summaries"] = []
        
        self.memory_data["summaries"].append(summary_data)
        
        # 限制总结数量（保留最近N条）
        if len(self.memory_data["summaries"]) > self.max_summaries:
            self.memory_data["summaries"] = self.memory_data["summaries"][-self.max_summaries:]
        
        # 更新合并记忆和时间线
        self.update_memory()
        
        # 保存到文件
        self.save_memory()
    
    def update_memory(self):
        """更新合并记忆和时间线（同步版本）"""
        summaries = self.memory_data.get("summaries", [])
        if not summaries:
            self.memory_data["consolidated_memory"] = ""
            self.memory_data["timeline_memory"] = ""
            return
        
        # 更新时间线记忆
        today = datetime.now().date()
        timeline_entries = []
        
        for summary in summaries[-self.timeline_summaries:]:  # 保留最近N条
            date_str = summary.get("date", "")
            summary_text = summary.get("summary", "")
            time_label = self.get_relative_time_label(date_str)
            timeline_entries.append(f"{time_label}（{date_str}）：{summary_text}")
        
        self.memory_data["timeline_memory"] = "\n".join(timeline_entries)
        
        # 更新合并记忆（每10次总结或总结数量达到10的倍数时）
        if len(summaries) % 10 == 0 or len(summaries) == 1:
            # 异步更新合并记忆（在后台执行）
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.update_consolidated_memory())
                else:
                    asyncio.run(self.update_consolidated_memory())
            except:
                # 如果没有事件循环，创建新的事件循环
                asyncio.run(self.update_consolidated_memory())
    
    async def update_consolidated_memory(self):
        """更新合并后的记忆（带时间概念）"""
        summaries = self.memory_data.get("summaries", [])
        if not summaries:
            return
        
        import asyncio
        from .app import chatgpt_streamed
        
        # 构建带时间戳的总结文本
        all_summaries = "\n".join([
            f"{s.get('date', '')}：{s.get('summary', '')}" 
            for s in summaries[-self.timeline_summaries:]
        ])
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        consolidation_prompt = f"""今天是{today_str}。请将以下带时间戳的对话总结合并成一个连贯的用户记忆描述（400-600字），并保留时间概念：

{all_summaries}

要求：
1. 整合所有关键信息
2. 保留时间顺序和相对时间概念（如"昨天"、"前天"、"上周"）
3. 如果用户提到"昨天做了什么"、"计划明天做什么"，要保留这些时间关系
4. 用自然语言描述，像在描述一个老朋友
5. 格式示例："用户是张三，25岁。昨天（12月26日）开始练习英语，虽然觉得难但坚持下来了。今天（12月27日）换了工作做AI相关，更想提高英语水平..."

只返回合并后的记忆描述，不要其他说明。"""
        
        # 将同步函数包装成异步调用
        loop = asyncio.get_event_loop()
        consolidated = await loop.run_in_executor(
            None,
            lambda: chatgpt_streamed(
                consolidation_prompt,
                "你是一个专业的记忆管理助手，擅长整合和更新用户信息，并保留时间概念。",
                "neutral",
                []
            )
        )
        
        self.memory_data["consolidated_memory"] = consolidated.strip()
        self.save_memory()
    
    def save_memory(self):
        """保存记忆到文件"""
        self.memory_data["last_updated"] = datetime.now().isoformat()
        
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")

