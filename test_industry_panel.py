#!/usr/bin/env python3
"""
测试行业分析的真实专家投票功能
"""

import sys
from pathlib import Path

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent / "skills" / "deep-analysis" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

def test_industry_panel():
    """测试行业级 panel 生成"""
    print("🧪 测试行业分析的真实专家投票功能\n")
    
    # 导入模块
    try:
        from lib.analysis.industry_analyzer import IndustryAnalyzer, get_industry_category, get_investor_weight_adjustment
        print("✅ 模块导入成功\n")
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return
    
    # 测试行业分类识别
    print("📋 测试行业分类识别:")
    test_industries = ["白酒", "新能源", "半导体", "医药", "军工", "银行", "房地产"]
    for industry in test_industries:
        category = get_industry_category(industry)
        weights = get_investor_weight_adjustment(industry)
        print(f"   {industry} → {category} (权重调整: {weights})")
    
    print("\n" + "="*60)
    
    # 测试行业分析
    print("📊 测试行业分析（真实专家投票）:\n")
    
    analyzer = IndustryAnalyzer()
    
    # 分析白酒行业
    print("正在分析：白酒行业")
    print("(这将对成分股进行评分，然后聚合生成行业级专家投票)\n")
    
    try:
        result = analyzer.analyze("白酒", top_n=5, detailed=True)
        
        print("\n" + "="*60)
        print("✅ 分析完成！\n")
        
        print(f"行业: {result['industry_name']}")
        print(f"评分: {result['overall_score']}")
        print(f"评级: {result['rating']}")
        print(f"\n看多理由:")
        for reason in result['reasons_bullish']:
            print(f"  • {reason}")
        print(f"\n看空理由:")
        for reason in result['reasons_bearish']:
            print(f"  • {reason}")
        
        if 'report_path' in result:
            print(f"\n📄 报告已生成: {result['report_path']}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_industry_panel()
