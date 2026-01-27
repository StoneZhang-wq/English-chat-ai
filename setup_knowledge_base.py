"""
设置知识点数据库
运行前请确保已安装: pip install pandas openpyxl
"""
import sys
import subprocess

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import pandas
        import openpyxl
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install pandas openpyxl")
        return False

if __name__ == "__main__":
    if not check_dependencies():
        sys.exit(1)
    
    # 运行创建脚本
    from create_knowledge_base import create_knowledge_base
    create_knowledge_base()
    print("\n✅ 知识点总表创建完成！")
