"""
知识点数据库管理模块
- 总表：knowledge_base.xlsx 或 knowledge_base.csv（映射形式，子表通过ID关联）
- 用户子表：memory/accounts/{用户名}/
  - learning_progress.csv: 学习记录（只存储用户学习数据，通过知识点ID关联总表）
  - scene_preferences.csv: 场景偏好（只存储偏好数据）
"""
import pandas as pd
import os
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# 难度等级顺序
LEVEL_ORDER = ['beginner', 'elementary', 'pre_intermediate', 'intermediate', 'upper_intermediate', 'advanced']

# 掌握程度计算权重
MASTERY_WEIGHTS = {
    'accuracy': 0.5,  # 正确率权重
    'times': 0.3,     # 学习次数权重
    'decay': 0.2      # 时间衰减权重
}

# 兴趣度计算权重
INTEREST_WEIGHTS = {
    'choice': 0.5,    # 选择次数权重
    'study': 0.3,     # 学习次数权重
    'mastery': 0.2   # 掌握率权重
}


class KnowledgeDatabase:
    """知识点数据库管理类"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.master_table_path_xlsx = self.base_dir / "knowledge_base.xlsx"
        self.master_table_path_csv = self.base_dir / "knowledge_base.csv"
        self.memory_dir = self.base_dir / "memory" / "accounts"
    
    def _check_openpyxl(self):
        """检查openpyxl是否可用，如果不可用则抛出错误"""
        if not OPENPYXL_AVAILABLE:
            raise ImportError(
                "openpyxl未安装，无法创建或更新用户学习记录文件。\n"
                "请运行: pip install openpyxl\n"
                "或者以管理员权限运行安装命令"
            )
        
    def get_master_knowledge(self) -> pd.DataFrame:
        """读取总表（支持Excel和CSV格式）"""
        # 优先尝试Excel格式
        if self.master_table_path_xlsx.exists():
            try:
                return pd.read_excel(self.master_table_path_xlsx, sheet_name='知识点库')
            except Exception as e:
                print(f"Warning: 读取Excel文件失败: {e}，尝试CSV格式")
        
        # 如果Excel不存在或读取失败，尝试CSV格式
        if self.master_table_path_csv.exists():
            try:
                return pd.read_csv(self.master_table_path_csv, encoding='utf-8-sig')
            except Exception as e:
                print(f"Warning: 读取CSV文件失败: {e}")
        
        # 如果都不存在，抛出错误
        raise FileNotFoundError(
            f"知识点总表不存在。请确保存在以下文件之一：\n"
            f"  - {self.master_table_path_xlsx}\n"
            f"  - {self.master_table_path_csv}\n"
            f"运行 python create_knowledge_base.py 创建总表"
        )
    
    def get_user_learning_progress_path(self, user_id: str) -> Path:
        """获取用户学习记录文件路径"""
        user_dir = self.memory_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir / "learning_progress.xlsx"
    
    def init_user_progress(self, user_id: str):
        """初始化用户学习记录（如果不存在）"""
        self._check_openpyxl()
        
        progress_path = self.get_user_learning_progress_path(user_id)
        
        if not progress_path.exists():
            # 创建空的学习记录表
            learning_df = pd.DataFrame(columns=[
                '知识点ID', '场景一级', '场景二级', '类型', '内容', '英文', '难度',
                '掌握程度', '学习次数', '首次学习时间', '最后学习时间', 
                '是否掌握', '错误次数', '正确次数', '最近正确率'
            ])
            
            # 创建空的场景偏好表
            preference_df = pd.DataFrame(columns=[
                '场景一级', '场景二级', '选择次数', '学习次数', 
                '掌握知识点数', '总知识点数', '掌握率', '最后学习时间', '兴趣度'
            ])
            
            with pd.ExcelWriter(progress_path, engine='openpyxl') as writer:
                learning_df.to_excel(writer, sheet_name='学习记录', index=False)
                preference_df.to_excel(writer, sheet_name='场景偏好', index=False)
    
    def get_user_learning_progress(self, user_id: str) -> pd.DataFrame:
        """读取用户学习记录"""
        progress_path = self.get_user_learning_progress_path(user_id)
        self.init_user_progress(user_id)
        
        if progress_path.exists():
            try:
                return pd.read_excel(progress_path, sheet_name='学习记录')
            except:
                return pd.DataFrame()
        return pd.DataFrame()
    
    def get_user_scene_preferences(self, user_id: str) -> pd.DataFrame:
        """读取用户场景偏好"""
        progress_path = self.get_user_learning_progress_path(user_id)
        self.init_user_progress(user_id)
        
        if progress_path.exists():
            try:
                return pd.read_excel(progress_path, sheet_name='场景偏好')
            except:
                return pd.DataFrame()
        return pd.DataFrame()
    
    def calculate_time_decay(self, last_learned_time: Optional[datetime]) -> float:
        """计算时间衰减因子"""
        if not last_learned_time:
            return 0.0
        
        if isinstance(last_learned_time, str):
            try:
                last_learned_time = datetime.strptime(last_learned_time, "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    last_learned_time = datetime.strptime(last_learned_time, "%Y-%m-%d")
                except:
                    return 0.0
        
        days_ago = (datetime.now() - last_learned_time).days
        
        if days_ago == 0:
            return 1.0
        elif days_ago <= 3:
            return 1.0 - 0.2 * (days_ago / 3)
        elif days_ago <= 7:
            return 0.8 - 0.2 * ((days_ago - 3) / 4)
        elif days_ago <= 14:
            return 0.6 - 0.2 * ((days_ago - 7) / 7)
        elif days_ago <= 30:
            return 0.4 - 0.2 * ((days_ago - 14) / 16)
        elif days_ago <= 60:
            return 0.2 - 0.1 * ((days_ago - 30) / 30)
        else:
            return 0.1
    
    def calculate_mastery(self, accuracy: float, times: int, time_decay: float) -> float:
        """计算掌握程度"""
        # 正确率因子（直接使用）
        accuracy_factor = max(0.0, min(1.0, accuracy))
        
        # 学习次数因子（对数增长）
        # 学习1次=0.2, 3次=0.5, 5次=0.7, 10次=0.9, 20次=1.0
        times_factor = min(1.0, 0.2 + 0.3 * math.log(times + 1) / math.log(21))
        
        # 时间衰减因子
        decay_factor = max(0.0, min(1.0, time_decay))
        
        mastery = (MASTERY_WEIGHTS['accuracy'] * accuracy_factor + 
                   MASTERY_WEIGHTS['times'] * times_factor + 
                   MASTERY_WEIGHTS['decay'] * decay_factor)
        
        return max(0.0, min(1.0, mastery))
    
    def calculate_interest(self, choice_count: int, study_count: int, mastery_rate: float) -> float:
        """计算兴趣度"""
        # 选择因子（对数增长）
        # 选择1次=0.3, 3次=0.6, 5次=0.8, 10次=1.0
        choice_factor = min(1.0, 0.3 + 0.7 * math.log(choice_count + 1) / math.log(11))
        
        # 学习因子（对数增长）
        # 学习5次=0.3, 10次=0.5, 20次=0.7, 50次=0.9, 100次=1.0
        study_factor = min(1.0, 0.3 + 0.7 * math.log(study_count + 1) / math.log(101))
        
        # 掌握因子（直接使用掌握率）
        mastery_factor = max(0.0, min(1.0, mastery_rate))
        
        interest = (INTEREST_WEIGHTS['choice'] * choice_factor + 
                   INTEREST_WEIGHTS['study'] * study_factor + 
                   INTEREST_WEIGHTS['mastery'] * mastery_factor)
        
        return max(0.0, min(1.0, interest))
    
    def update_learning_progress(self, user_id: str, knowledge_id: str, 
                                is_correct: bool, knowledge_info: Optional[Dict] = None):
        """更新学习记录（练习后调用）"""
        self._check_openpyxl()
        progress_path = self.get_user_learning_progress_path(user_id)
        self.init_user_progress(user_id)
        
        # 读取现有记录
        learning_df = self.get_user_learning_progress(user_id)
        
        # 如果知识信息未提供，从总表获取
        if knowledge_info is None:
            master_df = self.get_master_knowledge()
            knowledge_info = master_df[master_df['知识点ID'] == knowledge_id].iloc[0].to_dict()
        
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # 查找是否已有记录
        existing = learning_df[learning_df['知识点ID'] == knowledge_id]
        
        if len(existing) > 0:
            # 更新现有记录
            idx = existing.index[0]
            learning_df.at[idx, '学习次数'] = learning_df.at[idx, '学习次数'] + 1
            learning_df.at[idx, '最后学习时间'] = now_str
            
            if is_correct:
                learning_df.at[idx, '正确次数'] = learning_df.at[idx, '正确次数'] + 1
            else:
                learning_df.at[idx, '错误次数'] = learning_df.at[idx, '错误次数'] + 1
            
            # 计算最近正确率
            total = learning_df.at[idx, '正确次数'] + learning_df.at[idx, '错误次数']
            accuracy = learning_df.at[idx, '正确次数'] / total if total > 0 else 0.0
            learning_df.at[idx, '最近正确率'] = accuracy
            
            # 计算掌握程度
            last_time = learning_df.at[idx, '最后学习时间']
            if isinstance(last_time, str):
                try:
                    last_time = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
                except:
                    last_time = datetime.strptime(last_time, "%Y-%m-%d")
            else:
                last_time = now
            
            time_decay = self.calculate_time_decay(last_time)
            mastery = self.calculate_mastery(accuracy, learning_df.at[idx, '学习次数'], time_decay)
            learning_df.at[idx, '掌握程度'] = mastery
            learning_df.at[idx, '是否掌握'] = mastery >= 0.7  # 掌握阈值0.7
        else:
            # 创建新记录
            new_record = {
                '知识点ID': knowledge_id,
                '场景一级': knowledge_info.get('场景一级', ''),
                '场景二级': knowledge_info.get('场景二级', ''),
                '类型': knowledge_info.get('类型', ''),
                '内容': knowledge_info.get('内容', ''),
                '英文': knowledge_info.get('英文', ''),
                '难度': knowledge_info.get('难度', 'beginner'),
                '掌握程度': 0.0,
                '学习次数': 1,
                '首次学习时间': now_str,
                '最后学习时间': now_str,
                '是否掌握': False,
                '错误次数': 0,
                '正确次数': 0,
                '最近正确率': 0.0
            }
            
            if is_correct:
                new_record['正确次数'] = 1
                new_record['最近正确率'] = 1.0
            else:
                new_record['错误次数'] = 1
                new_record['最近正确率'] = 0.0
            
            # 计算初始掌握程度
            time_decay = self.calculate_time_decay(now)
            mastery = self.calculate_mastery(new_record['最近正确率'], 1, time_decay)
            new_record['掌握程度'] = mastery
            
            learning_df = pd.concat([learning_df, pd.DataFrame([new_record])], ignore_index=True)
        
        # 保存
        preferences_df = self.get_user_scene_preferences(user_id)
        with pd.ExcelWriter(progress_path, engine='openpyxl') as writer:
            learning_df.to_excel(writer, sheet_name='学习记录', index=False)
            preferences_df.to_excel(writer, sheet_name='场景偏好', index=False)
        
        # 更新场景偏好
        self.update_scene_preference(user_id, knowledge_info.get('场景一级', ''), 
                                     knowledge_info.get('场景二级', ''))
    
    def update_scene_preference(self, user_id: str, scene_primary: str, scene_secondary: str):
        """更新场景偏好（学习后自动调用）"""
        self._check_openpyxl()
        progress_path = self.get_user_learning_progress_path(user_id)
        preferences_df = self.get_user_scene_preferences(user_id)
        
        # 查找是否已有记录
        existing = preferences_df[
            (preferences_df['场景一级'] == scene_primary) & 
            (preferences_df['场景二级'] == scene_secondary)
        ]
        
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # 获取总表中该场景的知识点总数
        master_df = self.get_master_knowledge()
        total_count = len(master_df[
            (master_df['场景一级'] == scene_primary) & 
            (master_df['场景二级'] == scene_secondary)
        ])
        
        # 获取用户学习记录
        learning_df = self.get_user_learning_progress(user_id)
        user_learned = learning_df[
            (learning_df['场景一级'] == scene_primary) & 
            (learning_df['场景二级'] == scene_secondary)
        ]
        mastered_count = len(user_learned[user_learned['是否掌握'] == True])
        study_count = len(user_learned)
        mastery_rate = mastered_count / study_count if study_count > 0 else 0.0
        
        if len(existing) > 0:
            # 更新现有记录
            idx = existing.index[0]
            preferences_df.at[idx, '学习次数'] = study_count
            preferences_df.at[idx, '掌握知识点数'] = mastered_count
            preferences_df.at[idx, '总知识点数'] = total_count
            preferences_df.at[idx, '掌握率'] = mastery_rate
            preferences_df.at[idx, '最后学习时间'] = now_str
            
            # 计算兴趣度
            choice_count = preferences_df.at[idx, '选择次数']
            interest = self.calculate_interest(choice_count, study_count, mastery_rate)
            preferences_df.at[idx, '兴趣度'] = interest
        else:
            # 创建新记录
            new_record = {
                '场景一级': scene_primary,
                '场景二级': scene_secondary,
                '选择次数': 0,  # 选择次数需要单独更新
                '学习次数': study_count,
                '掌握知识点数': mastered_count,
                '总知识点数': total_count,
                '掌握率': mastery_rate,
                '最后学习时间': now_str,
                '兴趣度': 0.0
            }
            preferences_df = pd.concat([preferences_df, pd.DataFrame([new_record])], ignore_index=True)
        
        # 保存
        learning_df = self.get_user_learning_progress(user_id)
        with pd.ExcelWriter(progress_path, engine='openpyxl') as writer:
            learning_df.to_excel(writer, sheet_name='学习记录', index=False)
            preferences_df.to_excel(writer, sheet_name='场景偏好', index=False)
    
    def increment_scene_choice(self, user_id: str, scene_primary: str, scene_secondary: str):
        """增加场景选择次数（用户选择场景时调用）"""
        self._check_openpyxl()
        progress_path = self.get_user_learning_progress_path(user_id)
        preferences_df = self.get_user_scene_preferences(user_id)
        
        # 查找是否已有记录
        existing = preferences_df[
            (preferences_df['场景一级'] == scene_primary) & 
            (preferences_df['场景二级'] == scene_secondary)
        ]
        
        if len(existing) > 0:
            idx = existing.index[0]
            preferences_df.at[idx, '选择次数'] = preferences_df.at[idx, '选择次数'] + 1
            
            # 重新计算兴趣度
            choice_count = preferences_df.at[idx, '选择次数']
            study_count = preferences_df.at[idx, '学习次数']
            mastery_rate = preferences_df.at[idx, '掌握率']
            interest = self.calculate_interest(choice_count, study_count, mastery_rate)
            preferences_df.at[idx, '兴趣度'] = interest
        else:
            # 创建新记录
            master_df = self.get_master_knowledge()
            total_count = len(master_df[
                (master_df['场景一级'] == scene_primary) & 
                (master_df['场景二级'] == scene_secondary)
            ])
            
            new_record = {
                '场景一级': scene_primary,
                '场景二级': scene_secondary,
                '选择次数': 1,
                '学习次数': 0,
                '掌握知识点数': 0,
                '总知识点数': total_count,
                '掌握率': 0.0,
                '最后学习时间': '',
                '兴趣度': 0.0
            }
            preferences_df = pd.concat([preferences_df, pd.DataFrame([new_record])], ignore_index=True)
        
        # 保存
        learning_df = self.get_user_learning_progress(user_id)
        with pd.ExcelWriter(progress_path, engine='openpyxl') as writer:
            learning_df.to_excel(writer, sheet_name='学习记录', index=False)
            preferences_df.to_excel(writer, sheet_name='场景偏好', index=False)
    
    def get_recommended_knowledge(self, user_id: str, user_level: str, 
                                 selected_scene_secondary: Optional[str] = None) -> List[Dict]:
        """
        公式化推荐逻辑（不使用AI）
        
        推荐优先级：
        1. 用户刚选择的场景二级 → 立即推荐该场景下所有未学习的知识点（最多10个）
        2. 兴趣度>0.6 且 掌握率<0.5 的场景 → 推荐8个未学习的知识点
        3. 学习过但掌握率<0.4 的场景 → 推荐5个未学习的知识点
        4. 从未接触过的场景 → 每个场景推荐5个，最多3个一级场景
        """
        # 读取数据
        master_df = self.get_master_knowledge()
        learning_df = self.get_user_learning_progress(user_id)
        preferences_df = self.get_user_scene_preferences(user_id)
        
        # 获取已学习的知识点ID
        learned_ids = set(learning_df['知识点ID'].tolist()) if len(learning_df) > 0 else set()
        
        # 难度过滤（可以上升一级）
        user_level_idx = LEVEL_ORDER.index(user_level) if user_level in LEVEL_ORDER else 0
        max_level_idx = min(len(LEVEL_ORDER) - 1, user_level_idx + 1)  # 可以上升一级
        allowed_levels = LEVEL_ORDER[:max_level_idx + 1]
        
        # 过滤未学习且难度匹配的知识点
        unlearned = master_df[
            (~master_df['知识点ID'].isin(learned_ids)) & 
            (master_df['难度'].isin(allowed_levels))
        ].copy()
        
        recommended = []
        
        # 优先级1：用户刚选择的场景（立即推荐）
        if selected_scene_secondary:
            scene_knowledge = unlearned[unlearned['场景二级'] == selected_scene_secondary]
            for _, row in scene_knowledge.head(10).iterrows():
                recommended.append(row.to_dict())
        
        # 优先级2：兴趣度高(>0.6)且掌握率低(<0.5)的场景
        high_interest_low_mastery = preferences_df[
            (preferences_df['兴趣度'] > 0.6) & (preferences_df['掌握率'] < 0.5)
        ]
        for _, scene in high_interest_low_mastery.iterrows():
            scene_knowledge = unlearned[
                (unlearned['场景一级'] == scene['场景一级']) & 
                (unlearned['场景二级'] == scene['场景二级'])
            ]
            for _, row in scene_knowledge.head(8).iterrows():
                if row['知识点ID'] not in [r['知识点ID'] for r in recommended]:
                    recommended.append(row.to_dict())
        
        # 优先级3：学习过但掌握率低(<0.4)的场景
        low_mastery_scenes = preferences_df[
            (preferences_df['学习次数'] > 0) & (preferences_df['掌握率'] < 0.4)
        ]
        for _, scene in low_mastery_scenes.iterrows():
            scene_knowledge = unlearned[
                (unlearned['场景一级'] == scene['场景一级']) & 
                (unlearned['场景二级'] == scene['场景二级'])
            ]
            for _, row in scene_knowledge.head(5).iterrows():
                if row['知识点ID'] not in [r['知识点ID'] for r in recommended]:
                    recommended.append(row.to_dict())
        
        # 优先级4：从未接触过但难度匹配的场景
        unvisited_scenes = preferences_df[preferences_df['学习次数'] == 0]
        if len(unvisited_scenes) == 0:
            # 如果所有场景都接触过，选择学习次数最少的场景
            unvisited_scenes = preferences_df.nsmallest(3, '学习次数')
        
        # 按场景一级分组
        scene_primary_groups = {}
        for _, scene in unvisited_scenes.head(10).iterrows():
            key = scene['场景一级']
            if key not in scene_primary_groups:
                scene_primary_groups[key] = []
            scene_primary_groups[key].append(scene)
        
        # 每个一级场景最多推荐2个二级场景，每个二级场景推荐5个知识点
        for primary, scenes in list(scene_primary_groups.items())[:3]:
            for scene in scenes[:2]:
                scene_knowledge = unlearned[
                    (unlearned['场景一级'] == scene['场景一级']) & 
                    (unlearned['场景二级'] == scene['场景二级'])
                ]
                for _, row in scene_knowledge.head(5).iterrows():
                    if row['知识点ID'] not in [r['知识点ID'] for r in recommended]:
                        recommended.append(row.to_dict())
        
        # 去重并返回（最多20个）
        seen_ids = set()
        unique_recommended = []
        for k in recommended:
            if k['知识点ID'] not in seen_ids:
                seen_ids.add(k['知识点ID'])
                unique_recommended.append(k)
                if len(unique_recommended) >= 20:
                    break
        
        return unique_recommended
