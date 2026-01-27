"""
创建初始知识点总表Excel文件
基于CEFR词汇表，分配到不同场景
"""
import json
import pandas as pd
from datetime import datetime
import os

# 场景映射：一级场景 -> 二级场景列表
SCENE_MAPPING = {
    "工作": ["金融工作", "商务会议", "项目管理", "团队协作", "客户服务"],
    "生活": ["家庭关系", "日常购物", "健康医疗", "饮食烹饪", "家居生活"],
    "社交": ["日常社交", "朋友聚会", "约会恋爱", "网络社交", "社区活动"],
    "学习": ["学校课程", "考试准备", "学术研究", "技能培训", "在线学习"],
    "旅行": ["交通出行", "酒店住宿", "景点游览", "购物消费", "紧急情况"],
    "娱乐": ["电影音乐", "运动健身", "游戏娱乐", "阅读写作", "兴趣爱好"]
}

# 难度映射：CEFR级别 -> 系统难度
LEVEL_MAPPING = {
    "A1": "beginner",
    "A2": "elementary", 
    "B1": "intermediate",
    "B2": "upper_intermediate",
    "C1": "advanced"
}

# 类型映射
TYPE_MAPPING = {
    "vocabulary": "单词",
    "phrases": "词组",
    "grammar_patterns": "语法"
}

def load_cefr_data():
    """加载CEFR词汇表"""
    with open('memory/cefr_vocabulary.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_chinese_translation(english_word, word_type):
    """获取中文翻译（简化映射）"""
    translations = {
        # A1级别常用词
        "hello": "你好", "hi": "你好", "goodbye": "再见", "bye": "再见",
        "yes": "是", "no": "不", "please": "请", "thank you": "谢谢", "thanks": "谢谢", "sorry": "对不起",
        "good": "好的", "bad": "坏的", "big": "大的", "small": "小的", "new": "新的", "old": "旧的",
        "hot": "热的", "cold": "冷的", "happy": "高兴的", "sad": "悲伤的",
        "i": "我", "you": "你", "he": "他", "she": "她", "we": "我们", "they": "他们",
        "this": "这个", "that": "那个", "here": "这里", "there": "那里",
        "what": "什么", "who": "谁", "where": "哪里", "when": "什么时候", "why": "为什么", "how": "怎么",
        "name": "名字", "age": "年龄", "work": "工作", "job": "工作", "friend": "朋友", "family": "家庭",
        "school": "学校", "student": "学生", "teacher": "老师", "class": "班级", "lesson": "课程",
        "food": "食物", "water": "水", "coffee": "咖啡", "tea": "茶", "milk": "牛奶", "bread": "面包", "rice": "米饭",
        "car": "汽车", "bus": "公交车", "train": "火车", "plane": "飞机", "bike": "自行车",
        "house": "房子", "home": "家", "room": "房间", "door": "门", "window": "窗户",
        "table": "桌子", "chair": "椅子", "bed": "床", "book": "书", "pen": "笔",
        "eat": "吃", "drink": "喝", "sleep": "睡觉", "go": "去", "come": "来", "see": "看", "know": "知道",
        "think": "想", "want": "想要", "like": "喜欢", "read": "读", "write": "写", "speak": "说",
        "listen": "听", "watch": "看", "play": "玩", "buy": "买", "sell": "卖", "give": "给", "take": "拿",
        "get": "得到", "put": "放", "make": "做", "do": "做", "have": "有", "be": "是",
        "day": "天", "night": "夜晚", "morning": "早上", "afternoon": "下午", "evening": "晚上",
        "today": "今天", "tomorrow": "明天", "yesterday": "昨天", "week": "周", "month": "月", "year": "年",
        "time": "时间", "hour": "小时", "minute": "分钟", "now": "现在", "then": "然后",
        "before": "之前", "after": "之后",
        # A2级别
        "wonderful": "精彩的", "interesting": "有趣的", "beautiful": "美丽的", "nice": "好的", "great": "伟大的",
        "excellent": "优秀的", "fine": "好的", "okay": "好的", "maybe": "也许", "perhaps": "也许",
        "parent": "父母", "child": "孩子", "brother": "兄弟", "sister": "姐妹", "mother": "母亲", "father": "父亲",
        "son": "儿子", "daughter": "女儿", "study": "学习", "learn": "学习", "teach": "教", "test": "测试", "exam": "考试",
        "breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐", "restaurant": "餐厅", "shop": "商店",
        "store": "商店", "market": "市场", "price": "价格", "money": "钱", "cheap": "便宜的", "expensive": "贵的",
        "weather": "天气", "sunny": "晴朗的", "rainy": "下雨的", "cloudy": "多云的", "windy": "有风的",
        "snow": "雪", "rain": "雨", "sun": "太阳", "cloud": "云", "wind": "风",
        "clothes": "衣服", "shirt": "衬衫", "pants": "裤子", "shoes": "鞋子", "hat": "帽子",
        "dress": "裙子", "jacket": "夹克", "coat": "外套", "wear": "穿", "put on": "穿上",
        "hobby": "爱好", "sport": "运动", "football": "足球", "basketball": "篮球", "swim": "游泳",
        "dance": "跳舞", "sing": "唱歌", "music": "音乐", "movie": "电影", "film": "电影",
        "trip": "旅行", "vacation": "假期", "holiday": "假期", "hotel": "酒店", "airport": "机场",
        "station": "车站", "ticket": "票", "passport": "护照", "luggage": "行李",
        "feel": "感觉", "tired": "累的", "hungry": "饿的", "thirsty": "渴的", "sick": "生病的",
        "healthy": "健康的", "strong": "强壮的", "weak": "弱的", "fast": "快的", "slow": "慢的",
        "easy": "容易的", "difficult": "困难的", "hard": "困难的", "simple": "简单的",
        "important": "重要的", "necessary": "必要的", "possible": "可能的", "impossible": "不可能的",
        "right": "对的", "wrong": "错的", "help": "帮助", "helpful": "有帮助的", "kind": "善良的",
        "friendly": "友好的", "polite": "有礼貌的", "rude": "粗鲁的", "quiet": "安静的", "noisy": "吵闹的",
        "clean": "干净的", "dirty": "脏的",
        # B1级别
        "sophisticated": "复杂的", "comprehensive": "全面的", "elaborate": "详尽的", "significant": "重要的",
        "considerable": "相当大的", "substantial": "大量的", "adequate": "足够的", "sufficient": "充足的",
        "appropriate": "合适的", "suitable": "适合的", "career": "职业", "profession": "职业",
        "occupation": "职业", "colleague": "同事", "boss": "老板", "employee": "员工",
        "meeting": "会议", "project": "项目", "deadline": "截止日期", "schedule": "时间表",
        "education": "教育", "university": "大学", "college": "学院", "degree": "学位",
        "course": "课程", "subject": "科目", "research": "研究", "assignment": "作业",
        "essay": "论文", "presentation": "演示", "experience": "经验", "experienced": "有经验的",
        "skill": "技能", "ability": "能力", "talent": "天赋", "knowledge": "知识",
        "expertise": "专业知识", "qualification": "资格", "certificate": "证书", "diploma": "文凭",
        "opinion": "意见", "viewpoint": "观点", "perspective": "视角", "attitude": "态度",
        "belief": "信念", "agree": "同意", "disagree": "不同意", "discuss": "讨论",
        "debate": "辩论", "argue": "争论", "problem": "问题", "issue": "问题",
        "challenge": "挑战", "difficulty": "困难", "solution": "解决方案", "solve": "解决",
        "resolve": "解决", "handle": "处理", "manage": "管理", "deal with": "处理",
        "decision": "决定", "choose": "选择", "choice": "选择", "option": "选项",
        "alternative": "替代方案", "prefer": "更喜欢", "preference": "偏好", "recommend": "推荐",
        "suggest": "建议", "advise": "建议", "environment": "环境", "pollution": "污染",
        "recycle": "回收", "waste": "浪费", "energy": "能源", "resource": "资源",
        "climate": "气候", "temperature": "温度", "global": "全球的", "local": "本地的",
        "technology": "技术", "computer": "电脑", "internet": "互联网", "website": "网站",
        "email": "电子邮件", "software": "软件", "application": "应用程序", "device": "设备",
        "digital": "数字的", "online": "在线的", "culture": "文化", "tradition": "传统",
        "custom": "习俗", "festival": "节日", "celebrate": "庆祝", "ceremony": "仪式",
        "religion": "宗教", "language": "语言", "communication": "沟通", "interaction": "互动",
        "emotion": "情感", "feeling": "感觉", "mood": "情绪", "excited": "兴奋的",
        "nervous": "紧张的", "anxious": "焦虑的", "confident": "自信的", "proud": "骄傲的",
        "ashamed": "羞愧的", "embarrassed": "尴尬的", "relationship": "关系",
        "romantic": "浪漫的", "marriage": "婚姻", "wedding": "婚礼", "divorce": "离婚",
        "single": "单身的", "married": "已婚的", "engaged": "订婚的", "separated": "分居的",
        "widowed": "丧偶的",
        # B2级别
        "nuanced": "微妙的", "intricate": "复杂的", "complex": "复杂的", "thorough": "彻底的",
        "detailed": "详细的", "extensive": "广泛的", "profound": "深刻的",
        "analyze": "分析", "analysis": "分析", "evaluate": "评估", "evaluation": "评估",
        "assess": "评估", "assessment": "评估", "examine": "检查", "investigate": "调查",
        "strategy": "策略", "approach": "方法", "method": "方法", "technique": "技术",
        "procedure": "程序", "process": "过程", "system": "系统", "framework": "框架",
        "structure": "结构", "organization": "组织", "achieve": "实现", "accomplish": "完成",
        "attain": "达到", "obtain": "获得", "acquire": "获得", "gain": "获得",
        "earn": "赚取", "win": "赢得", "succeed": "成功", "influence": "影响",
        "impact": "影响", "effect": "效果", "affect": "影响", "consequence": "后果",
        "result": "结果", "outcome": "结果", "conclusion": "结论", "summary": "总结",
        "overview": "概述", "contribute": "贡献", "contribution": "贡献", "participate": "参与",
        "participation": "参与", "involve": "涉及", "involvement": "参与", "engage": "参与",
        "engagement": "参与", "commit": "承诺", "commitment": "承诺", "develop": "发展",
        "development": "发展", "improve": "改善", "improvement": "改善", "enhance": "增强",
        "enhancement": "增强", "progress": "进步", "advance": "前进", "advancement": "进步",
        "growth": "增长", "maintain": "维持", "maintenance": "维护", "preserve": "保存",
        "preservation": "保存", "sustain": "维持", "sustainability": "可持续性",
        "support": "支持", "supportive": "支持的", "establish": "建立", "establishment": "建立",
        "found": "建立", "foundation": "基础", "create": "创建", "creation": "创造",
        "build": "建造", "construction": "建设", "design": "设计", "demonstrate": "演示",
        "demonstration": "演示", "illustrate": "说明", "illustration": "说明",
        "explain": "解释", "explanation": "解释", "clarify": "澄清", "clarification": "澄清",
        "define": "定义", "definition": "定义", "persuade": "说服", "persuasion": "说服",
        "convince": "说服", "convincing": "令人信服的", "influential": "有影响力的",
        "motivate": "激励", "motivation": "动机", "inspire": "激励", "inspiration": "灵感",
        "criticize": "批评", "criticism": "批评", "critique": "评论", "critical": "关键的",
        "judge": "判断", "judgment": "判断",
        # C1级别
        "exceptionally": "异常地", "remarkably": "显著地", "substantially": "大量地",
        "considerably": "相当地", "significantly": "显著地", "notably": "显著地",
        "particularly": "特别地", "especially": "特别地", "extremely": "极端地",
        "highly": "高度地", "comprehend": "理解", "comprehension": "理解", "perceive": "感知",
        "perception": "感知", "conceive": "构思", "conception": "概念", "apprehend": "理解",
        "apprehension": "理解", "grasp": "掌握", "understanding": "理解", "articulate": "表达",
        "articulation": "表达", "express": "表达", "expression": "表达", "communicate": "沟通",
        "communication": "沟通", "convey": "传达", "conveyance": "传达", "transmit": "传输",
        "transmission": "传输", "synthesize": "综合", "synthesis": "综合", "integrate": "整合",
        "integration": "整合", "combine": "结合", "combination": "结合", "merge": "合并",
        "merger": "合并", "unite": "联合", "unity": "统一", "differentiate": "区分",
        "differentiation": "区分", "distinguish": "区分", "distinction": "区别",
        "discriminate": "歧视", "discrimination": "歧视", "separate": "分离",
        "separation": "分离", "divide": "分割", "division": "分割", "facilitate": "促进",
        "facilitation": "促进", "enable": "使能够", "enablement": "使能够", "empower": "授权",
        "empowerment": "授权", "authorize": "授权", "authorization": "授权", "permit": "允许",
        "permission": "许可", "optimize": "优化", "optimization": "优化", "maximize": "最大化",
        "maximization": "最大化", "minimize": "最小化", "minimization": "最小化",
        "innovate": "创新", "innovation": "创新", "innovative": "创新的", "creativity": "创造力",
        "creative": "创造性的", "originality": "原创性", "original": "原始的", "novelty": "新颖",
        "novel": "新颖的", "uniqueness": "独特性", "philosophy": "哲学", "philosophical": "哲学的",
        "theory": "理论", "theoretical": "理论的", "concept": "概念", "conceptual": "概念的",
        "principle": "原则", "principles": "原则", "doctrine": "教义", "doctrinal": "教义的",
        "contemporary": "当代的", "modern": "现代的", "current": "当前的", "present": "现在的",
        "recent": "最近的", "latest": "最新的", "up-to-date": "最新的", "state-of-the-art": "最先进的",
        "cutting-edge": "前沿的", "advanced": "先进的", "ambiguous": "模糊的", "ambiguity": "模糊性",
        "vague": "模糊的", "vagueness": "模糊性", "unclear": "不清楚的", "clarity": "清晰",
        "clear": "清楚的", "precise": "精确的", "precision": "精确性", "accurate": "准确的",
        "paradox": "悖论", "paradoxical": "矛盾的", "contradiction": "矛盾", "contradictory": "矛盾的",
        "inconsistency": "不一致", "inconsistent": "不一致的", "coherence": "连贯性",
        "coherent": "连贯的", "logical": "逻辑的", "logic": "逻辑",
        # 词组
        "how are you": "你好吗", "nice to meet you": "很高兴见到你", "what's your name": "你叫什么名字",
        "i'm fine": "我很好", "thank you very much": "非常感谢", "you're welcome": "不客气",
        "excuse me": "打扰一下", "i'm sorry": "对不起", "that's okay": "没关系",
        "see you later": "稍后见", "good morning": "早上好", "good afternoon": "下午好",
        "good evening": "晚上好", "good night": "晚安", "have a nice day": "祝你有美好的一天",
        "how's it going": "怎么样", "what's up": "怎么了", "long time no see": "好久不见",
        "take care": "保重", "have a good time": "玩得开心", "good luck": "祝你好运",
        "congratulations": "恭喜", "well done": "做得好", "that's great": "太好了",
        "i think so": "我也这么认为", "i don't think so": "我不这么认为",
        "that's right": "对的", "that's wrong": "错的", "i agree": "我同意", "i disagree": "我不同意",
        "in my opinion": "在我看来", "i believe that": "我相信", "it seems to me": "在我看来",
        "from my point of view": "从我的角度来看", "as far as i'm concerned": "就我而言",
        "on the one hand": "一方面", "on the other hand": "另一方面", "in addition": "此外",
        "furthermore": "此外", "moreover": "而且", "as a result": "结果", "therefore": "因此",
        "consequently": "因此", "however": "然而", "nevertheless": "尽管如此",
        "it goes without saying": "不用说", "needless to say": "不用说", "to put it simply": "简单来说",
        "in other words": "换句话说", "to sum up": "总结", "all things considered": "综合考虑",
        "taking everything into account": "考虑到一切", "it is worth noting": "值得注意的是",
        "it should be emphasized": "应该强调的是", "it is important to mention": "重要的是要提到",
        "it is imperative that": "必须", "it is crucial to": "关键是", "it is essential that": "必须",
        "it cannot be overstated": "不能过分强调", "it bears emphasizing": "值得强调",
        "to delve deeper into": "深入探讨", "to shed light on": "阐明", "to bring to the fore": "突出",
        "to underscore the significance": "强调重要性", "to highlight the importance": "强调重要性",
        # 语法句型
        "i am...": "我是...", "you are...": "你是...", "he/she is...": "他/她是...",
        "i like...": "我喜欢...", "i don't like...": "我不喜欢...", "can you...?": "你能...吗？",
        "do you...?": "你...吗？", "what is...?": "什么是...？", "where is...?": "哪里是...？",
        "how are...?": "...怎么样？", "i was...": "我过去是...", "i will...": "我将...",
        "i'm going to...": "我打算...", "i have...": "我有...", "i can...": "我能...",
        "i should...": "我应该...", "i want to...": "我想要...", "i need to...": "我需要...",
        "i like to...": "我喜欢...", "i prefer to...": "我更喜欢...", "i have been...": "我一直在...",
        "i had...": "我过去有...", "i would...": "我会...", "if i were...": "如果我是...",
        "i wish i could...": "我希望我能...", "it is important to...": "重要的是...",
        "it seems that...": "似乎...", "i think that...": "我认为...", "i believe that...": "我相信...",
        "in my opinion...": "在我看来...", "having said that...": "话虽如此...",
        "it is worth noting that...": "值得注意的是...", "what strikes me is...": "让我印象深刻的是...",
        "it is evident that...": "很明显...", "one cannot deny that...": "不能否认...",
        "not only... but also...": "不仅...而且...", "neither... nor...": "既不...也不...",
        "whether... or...": "无论...还是...", "despite the fact that...": "尽管...",
        "in spite of...": "尽管...", "it is imperative that...": "必须...",
        "were it not for...": "如果不是...", "had it not been for...": "如果不是...",
        "notwithstanding the fact that...": "尽管...", "inasmuch as...": "由于...",
        "to what extent...": "到什么程度...", "to the extent that...": "到...的程度",
        "insofar as...": "就...而言", "albeit...": "尽管...", "albeit the fact that...": "尽管..."
    }
    
    # 尝试直接匹配（不区分大小写）
    key = english_word.lower().strip()
    if key in translations:
        return translations[key]
    
    # 如果是词组，尝试部分匹配
    if word_type == "词组":
        for trans_key, trans_value in translations.items():
            if trans_key in key or key in trans_key:
                return trans_value
    
    # 默认返回英文
    return english_word

def create_knowledge_base():
    """创建知识点总表"""
    cefr_data = load_cefr_data()
    
    knowledge_items = []
    knowledge_id = 1
    
    # 处理词汇、词组、语法
    for data_type, type_name in TYPE_MAPPING.items():
        if data_type not in cefr_data:
            continue
            
        for cefr_level, items in cefr_data[data_type].items():
            system_level = LEVEL_MAPPING.get(cefr_level, "beginner")
            
            # 根据类型和难度分配到不同场景
            for item in items:
                # 根据内容判断场景（简化版，实际应该用AI或词典）
                scene_primary, scene_secondary = assign_scene(item, data_type, system_level)
                
                # 获取中文翻译
                chinese = get_chinese_translation(item, type_name)
                
                knowledge_items.append({
                    "知识点ID": f"KB{knowledge_id:05d}",
                    "场景一级": scene_primary,
                    "场景二级": scene_secondary,
                    "类型": type_name,
                    "内容": chinese,
                    "英文": item,
                    "难度": system_level,
                    "分类标签": f"{scene_primary},{scene_secondary},{type_name}",
                    "创建时间": datetime.now().strftime("%Y-%m-%d")
                })
                knowledge_id += 1
    
    # 创建DataFrame
    df = pd.DataFrame(knowledge_items)
    
    # 尝试保存为Excel
    excel_path = "knowledge_base.xlsx"
    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='知识点库', index=False)
        print(f"[OK] 知识点总表已创建: {excel_path}")
    except ImportError:
        # 如果openpyxl不可用，保存为CSV（用户可以用Excel打开并另存为xlsx）
        csv_path = "knowledge_base.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')  # utf-8-sig确保Excel能正确识别中文
        print(f"[WARNING] openpyxl未安装，已创建CSV格式: {csv_path}")
        print(f"   提示：可以用Excel打开此CSV文件，然后另存为 knowledge_base.xlsx")
        print(f"   或者运行: pip install openpyxl 后重新运行此脚本")
        excel_path = csv_path
    except Exception as e:
        # 其他错误，也保存为CSV作为备选
        csv_path = "knowledge_base.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"[WARNING] 创建Excel失败: {e}")
        print(f"   已创建CSV格式作为备选: {csv_path}")
        excel_path = csv_path
    
    print(f"   总知识点数: {len(knowledge_items)}")
    print(f"   场景分布:")
    scene_counts = df.groupby(['场景一级', '场景二级']).size()
    for (p, s), count in scene_counts.items():
        print(f"     {p} - {s}: {count}个")
    
    return excel_path

def assign_scene(item, data_type, level):
    """根据内容分配场景"""
    item_lower = item.lower().strip()
    
    # 工作相关 - 更细致的分类
    work_keywords = ["work", "job", "career", "profession", "occupation", "colleague", "boss", 
                     "employee", "meeting", "project", "deadline", "schedule", "business", 
                     "office", "company", "investment", "finance", "risk", "management",
                     "team", "collaboration", "client", "customer", "service"]
    if any(kw in item_lower for kw in work_keywords):
        if any(kw in item_lower for kw in ["finance", "investment", "risk", "money", "bank"]):
            return "工作", "金融工作"
        elif any(kw in item_lower for kw in ["meeting", "conference", "presentation", "discuss"]):
            return "工作", "商务会议"
        elif any(kw in item_lower for kw in ["project", "deadline", "plan", "strategy"]):
            return "工作", "项目管理"
        elif any(kw in item_lower for kw in ["team", "collaboration", "cooperation", "together"]):
            return "工作", "团队协作"
        elif any(kw in item_lower for kw in ["client", "customer", "service", "help"]):
            return "工作", "客户服务"
        else:
            return "工作", "商务会议"  # 默认
    
    # 生活相关
    family_keywords = ["family", "parent", "child", "brother", "sister", "mother", "father",
                       "son", "daughter", "marriage", "wedding", "relationship", "romantic",
                       "divorce", "married", "single"]
    if any(kw in item_lower for kw in family_keywords):
        return "生活", "家庭关系"
    
    shopping_keywords = ["shop", "store", "market", "buy", "sell", "price", "money", "cheap", 
                        "expensive", "purchase", "shopping"]
    if any(kw in item_lower for kw in shopping_keywords):
        return "生活", "日常购物"
    
    health_keywords = ["health", "healthy", "sick", "hospital", "doctor", "medicine", "medical",
                      "tired", "hungry", "thirsty", "feel", "pain"]
    if any(kw in item_lower for kw in health_keywords):
        return "生活", "健康医疗"
    
    food_keywords = ["food", "breakfast", "lunch", "dinner", "eat", "drink", "coffee", "tea",
                    "milk", "bread", "rice", "restaurant", "cook", "kitchen"]
    if any(kw in item_lower for kw in food_keywords):
        return "生活", "饮食烹饪"
    
    home_keywords = ["house", "home", "room", "door", "window", "table", "chair", "bed",
                    "clean", "dirty", "furniture"]
    if any(kw in item_lower for kw in home_keywords):
        return "生活", "家居生活"
    
    # 社交相关
    social_keywords = ["friend", "hello", "hi", "nice to meet", "how are you", "social",
                      "greet", "introduce", "meet"]
    if any(kw in item_lower for kw in social_keywords):
        return "社交", "日常社交"
    
    party_keywords = ["party", "gathering", "together", "celebrate", "congratulations"]
    if any(kw in item_lower for kw in party_keywords):
        return "社交", "朋友聚会"
    
    date_keywords = ["date", "romantic", "love", "dating", "relationship"]
    if any(kw in item_lower for kw in date_keywords):
        return "社交", "约会恋爱"
    
    online_keywords = ["online", "internet", "website", "email", "digital", "computer",
                      "technology", "device", "software", "application"]
    if any(kw in item_lower for kw in online_keywords):
        return "社交", "网络社交"
    
    community_keywords = ["community", "activity", "event", "local", "neighborhood"]
    if any(kw in item_lower for kw in community_keywords):
        return "社交", "社区活动"
    
    # 学习相关
    study_keywords = ["school", "student", "teacher", "study", "learn", "education", "university",
                     "college", "class", "lesson", "course", "subject"]
    if any(kw in item_lower for kw in study_keywords):
        return "学习", "学校课程"
    
    exam_keywords = ["exam", "test", "assignment", "essay", "presentation", "degree",
                    "certificate", "diploma", "qualification"]
    if any(kw in item_lower for kw in exam_keywords):
        return "学习", "考试准备"
    
    research_keywords = ["research", "analysis", "investigate", "examine", "academic",
                       "theory", "concept", "philosophy"]
    if any(kw in item_lower for kw in research_keywords):
        return "学习", "学术研究"
    
    skill_keywords = ["skill", "ability", "talent", "training", "practice", "improve",
                     "develop", "enhance"]
    if any(kw in item_lower for kw in skill_keywords):
        return "学习", "技能培训"
    
    online_learn_keywords = ["online", "digital", "internet", "website", "application"]
    if any(kw in item_lower for kw in online_learn_keywords) and "learn" in item_lower:
        return "学习", "在线学习"
    
    # 旅行相关
    travel_keywords = ["travel", "trip", "vacation", "holiday", "journey"]
    if any(kw in item_lower for kw in travel_keywords):
        return "旅行", "交通出行"
    
    transport_keywords = ["car", "bus", "train", "plane", "airport", "station", "ticket",
                         "passport", "luggage"]
    if any(kw in item_lower for kw in transport_keywords):
        return "旅行", "交通出行"
    
    hotel_keywords = ["hotel", "accommodation", "room", "reservation", "check in", "check out"]
    if any(kw in item_lower for kw in hotel_keywords):
        return "旅行", "酒店住宿"
    
    sightseeing_keywords = ["sightseeing", "tour", "visit", "attraction", "scenic", "view"]
    if any(kw in item_lower for kw in sightseeing_keywords):
        return "旅行", "景点游览"
    
    travel_shopping_keywords = ["shop", "store", "market", "buy", "souvenir"]
    if any(kw in item_lower for kw in travel_shopping_keywords) and "travel" in item_lower:
        return "旅行", "购物消费"
    
    emergency_keywords = ["emergency", "help", "police", "hospital", "lost", "problem"]
    if any(kw in item_lower for kw in emergency_keywords):
        return "旅行", "紧急情况"
    
    # 娱乐相关
    movie_keywords = ["movie", "film", "music", "song", "watch", "listen", "entertainment"]
    if any(kw in item_lower for kw in movie_keywords):
        return "娱乐", "电影音乐"
    
    sport_keywords = ["sport", "football", "basketball", "swim", "dance", "exercise", "fitness",
                     "gym", "workout"]
    if any(kw in item_lower for kw in sport_keywords):
        return "娱乐", "运动健身"
    
    game_keywords = ["game", "play", "fun", "enjoy", "entertainment"]
    if any(kw in item_lower for kw in game_keywords):
        return "娱乐", "游戏娱乐"
    
    reading_keywords = ["read", "book", "write", "article", "story", "novel", "literature"]
    if any(kw in item_lower for kw in reading_keywords):
        return "娱乐", "阅读写作"
    
    hobby_keywords = ["hobby", "interest", "like", "prefer", "enjoy", "favorite"]
    if any(kw in item_lower for kw in hobby_keywords):
        return "娱乐", "兴趣爱好"
    
    # 默认分配（根据难度和类型）
    if level in ["beginner", "elementary"]:
        if data_type == "grammar_patterns":
            return "学习", "学校课程"
        else:
            return "社交", "日常社交"
    elif level == "intermediate":
        return "工作", "商务会议"
    else:
        return "学习", "学术研究"

if __name__ == "__main__":
    create_knowledge_base()
