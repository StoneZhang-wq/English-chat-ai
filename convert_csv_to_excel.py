"""
将CSV格式的知识点总表转换为Excel格式
"""
import pandas as pd
import sys

def convert_csv_to_excel():
    """将knowledge_base.csv转换为knowledge_base.xlsx"""
    try:
        # 读取CSV
        print("读取CSV文件...")
        df = pd.read_csv('knowledge_base.csv', encoding='utf-8-sig')
        print(f"成功读取 {len(df)} 个知识点")
        
        # 转换为Excel
        print("转换为Excel格式...")
        df.to_excel('knowledge_base.xlsx', sheet_name='知识点库', index=False)
        print("✅ 转换完成！已创建 knowledge_base.xlsx")
        
        return True
    except ImportError as e:
        print(f"❌ 错误: {e}")
        print("请先安装openpyxl: pip install openpyxl")
        return False
    except FileNotFoundError:
        print("❌ 错误: 找不到 knowledge_base.csv 文件")
        return False
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = convert_csv_to_excel()
    sys.exit(0 if success else 1)
