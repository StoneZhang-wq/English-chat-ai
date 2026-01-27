"""
测试知识点数据库系统
"""
import sys
from app.knowledge_db import KnowledgeDatabase

def test_knowledge_db():
    """测试知识点数据库功能"""
    print("=" * 50)
    print("测试知识点数据库系统")
    print("=" * 50)
    
    try:
        # 初始化数据库
        kb = KnowledgeDatabase()
        print("\n[1] 初始化数据库... OK")
        
        # 测试读取总表
        master_df = kb.get_master_knowledge()
        print(f"[2] 读取总表... OK (共 {len(master_df)} 个知识点)")
        print(f"    前3个知识点:")
        for idx, row in master_df.head(3).iterrows():
            print(f"      {row['知识点ID']}: {row['内容']} ({row['英文']}) - {row['场景一级']}/{row['场景二级']}")
        
        # 测试用户初始化
        test_user = "测试用户"
        kb.init_user_progress(test_user)
        print(f"\n[3] 初始化用户 '{test_user}' 的学习记录... OK")
        
        # 测试获取推荐
        recommended = kb.get_recommended_knowledge(
            user_id=test_user,
            user_level="intermediate",
            selected_scene_secondary="金融工作"
        )
        print(f"[4] 获取推荐知识点... OK (推荐 {len(recommended)} 个)")
        if recommended:
            print(f"    前3个推荐:")
            for i, k in enumerate(recommended[:3], 1):
                print(f"      {i}. {k['内容']} ({k['英文']}) - {k['场景一级']}/{k['场景二级']} - {k['难度']}")
        
        # 测试更新学习记录
        if recommended:
            test_knowledge = recommended[0]
            kb.update_learning_progress(
                user_id=test_user,
                knowledge_id=test_knowledge['知识点ID'],
                is_correct=True,
                knowledge_info=test_knowledge
            )
            print(f"\n[5] 更新学习记录... OK (知识点: {test_knowledge['内容']})")
            
            # 验证更新
            progress_df = kb.get_user_learning_progress(test_user)
            if len(progress_df) > 0:
                record = progress_df.iloc[0]
                print(f"    验证: 学习次数={record['学习次数']}, 掌握程度={record['掌握程度']:.2f}")
        
        # 测试场景偏好
        kb.increment_scene_choice(test_user, "工作", "金融工作")
        print(f"\n[6] 更新场景偏好... OK (工作/金融工作)")
        
        preferences_df = kb.get_user_scene_preferences(test_user)
        if len(preferences_df) > 0:
            pref = preferences_df.iloc[0]
            print(f"    验证: 选择次数={pref['选择次数']}, 兴趣度={pref['兴趣度']:.2f}")
        
        print("\n" + "=" * 50)
        print("[OK] 所有测试通过！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_knowledge_db()
