# 知识点数据库系统使用说明

## 📋 系统概述

本系统采用**映射形式**的数据库设计：
- **总表** (`knowledge_base.xlsx`): 存储所有知识点的基础信息（内容、英文、难度、场景等）
- **用户子表** (`memory/accounts/{用户名}/learning_progress.xlsx`): 只存储用户学习数据，通过知识点ID关联总表

## 🗂️ 数据库结构

### 总表：`knowledge_base.xlsx`
- **Sheet1: 知识点库**
  - 列：知识点ID、场景一级、场景二级、类型、内容、英文、难度、分类标签、创建时间

### 用户子表：`memory/accounts/{用户名}/learning_progress.xlsx`
- **Sheet1: 学习记录**
  - 列：知识点ID、场景一级、场景二级、类型、内容、英文、难度、掌握程度、学习次数、首次学习时间、最后学习时间、是否掌握、错误次数、正确次数、最近正确率
  - **注意**：内容、英文、难度等字段通过知识点ID从总表映射获取，子表只存储学习数据
  
- **Sheet2: 场景偏好**
  - 列：场景一级、场景二级、选择次数、学习次数、掌握知识点数、总知识点数、掌握率、最后学习时间、兴趣度

## 📊 公式设计

### 1. 掌握程度计算公式
```
掌握程度 = 0.5 * 正确率 + 0.3 * 学习次数因子 + 0.2 * 时间衰减因子

其中：
- 正确率 = 正确次数 / (正确次数 + 错误次数)
- 学习次数因子 = min(1.0, 0.2 + 0.3 * log(学习次数+1) / log(21))
- 时间衰减因子 = 基于最后学习时间计算（今天=1.0，逐渐衰减）
```

### 2. 兴趣度计算公式
```
兴趣度 = 0.5 * 选择因子 + 0.3 * 学习因子 + 0.2 * 掌握因子

其中：
- 选择因子 = min(1.0, 0.3 + 0.7 * log(选择次数+1) / log(11))
- 学习因子 = min(1.0, 0.3 + 0.7 * log(学习次数+1) / log(101))
- 掌握因子 = 掌握率
```

## 🎯 推荐逻辑（公式化，不使用AI）

推荐优先级：
1. **用户刚选择的场景二级** → 立即推荐该场景下所有未学习的知识点（最多10个）
2. **兴趣度>0.6 且 掌握率<0.5 的场景** → 推荐8个未学习的知识点
3. **学习过但掌握率<0.4 的场景** → 推荐5个未学习的知识点
4. **从未接触过的场景** → 每个场景推荐5个，最多3个一级场景

**难度过滤**：用户水平可以上升一级（如intermediate可以学upper_intermediate）

## 🚀 使用步骤

### 1. 安装依赖
```bash
pip install pandas openpyxl
```

### 2. 创建知识点总表
```bash
python setup_knowledge_base.py
```
或直接运行：
```bash
python create_knowledge_base.py
```

这将创建 `knowledge_base.xlsx` 文件，包含基于CEFR词汇表的知识点。

### 3. 在代码中使用

#### 初始化数据库
```python
from app.knowledge_db import KnowledgeDatabase

kb = KnowledgeDatabase()
```

#### 获取推荐知识点
```python
# 获取推荐（用户选择场景时）
recommended = kb.get_recommended_knowledge(
    user_id="张三",
    user_level="intermediate",
    selected_scene_secondary="金融工作"  # 用户刚选择的场景
)
```

#### 更新学习记录（练习后）
```python
# 练习后更新
kb.update_learning_progress(
    user_id="张三",
    knowledge_id="KB00001",
    is_correct=True,  # 是否正确
    knowledge_info=None  # 如果为None，会从总表自动获取
)
```

#### 增加场景选择次数（用户选择场景时）
```python
# 用户选择场景时
kb.increment_scene_choice(
    user_id="张三",
    scene_primary="工作",
    scene_secondary="金融工作"
)
```

## 🔗 集成到现有系统

### 1. 在 `generate_english_dialogue` 中使用推荐知识点
- 从推荐系统中获取知识点
- 将推荐的知识点作为词汇和语法参考传递给AI

### 2. 在 `end_practice` 中更新学习记录
- 练习结束后，遍历对话中使用的知识点
- 调用 `update_learning_progress` 更新每个知识点的学习记录

### 3. 在场景选择时更新偏好
- 用户选择场景时，调用 `increment_scene_choice` 增加选择次数

## 📝 注意事项

1. **映射形式**：子表只存储学习数据，基础信息通过ID从总表获取
2. **自动初始化**：首次访问用户子表时会自动创建
3. **数据更新**：每次练习后自动更新学习记录和场景偏好
4. **推荐系统**：完全公式化，不使用AI，性能高效

## 🐛 故障排除

### 问题：找不到知识点总表
**解决**：运行 `python setup_knowledge_base.py` 创建总表

### 问题：ModuleNotFoundError: No module named 'openpyxl'
**解决**：运行 `pip install pandas openpyxl`

### 问题：用户子表不存在
**解决**：系统会自动创建，无需手动操作
