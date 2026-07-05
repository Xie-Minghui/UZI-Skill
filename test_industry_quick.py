#!/usr/bin/env python3
"""
快速测试行业分析功能（跳过耗时的数据采集）
"""
import sys
from pathlib import Path

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent / "skills" / "deep-analysis" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

def test_industry_analysis():
    """快速测试行业分析"""
    print("=" * 60)
    print("快速测试行业分析功能")
    print("=" * 60)
    
    try:
        # 直接调用分析函数
        from lib.analysis.industry_analyzer import analyze_industry
        
        print("\n开始分析行业: 白酒")
        print("（这将跳过耗时的数据采集，使用缓存数据）\n")
        
        # 设置环境变量，启用 resume 模式
        import os
        os.environ["UZI_NO_RESUME"] = "0"  # 允许使用缓存
        
        result = analyze_industry(
            "白酒",
            top_n=5,
            detailed=False  # 不生成详细报告
        )
        
        print("\n" + "=" * 60)
        print("✅ 分析完成")
        print("=" * 60)
        print(f"行业: {result['industry_name']}")
        print(f"评分: {result['overall_score']}")
        print(f"评级: {result['rating']}")
        print(f"TOP 3 股票: {[s['ticker'] for s in result.get('top_stocks', [])]}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_industry_analysis()
