#!/usr/bin/env python3
"""
测试行业分析功能（使用示例数据）
"""

import sys
import os

# 添加路径
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

SCRIPTS_DIR = os.path.join(ROOT, "skills", "deep-analysis", "scripts")
if os.path.exists(SCRIPTS_DIR):
    sys.path.insert(0, SCRIPTS_DIR)
else:
    SCRIPTS_DIR = os.path.join(ROOT, "scripts")
    sys.path.insert(0, SCRIPTS_DIR)

print(f"🔍 测试行业分析功能...")
print(f"   根目录: {ROOT}")
print(f"   脚本目录: {SCRIPTS_DIR}")
print()

# 测试 1: 创建 IndustryAnalyzer
print("📊 测试 1: 创建 IndustryAnalyzer...")
try:
    from lib.analysis.industry_analyzer import IndustryAnalyzer
    analyzer = IndustryAnalyzer()
    print(f"   ✅ IndustryAnalyzer 创建成功")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 2: 分析行业（使用示例数据）
print()
print("📊 测试 2: 分析行业 '白酒'（示例数据）...")
try:
    result = analyzer.analyze("白酒", top_n=5, detailed=False)
    
    print(f"   ✅ 分析完成")
    print(f"      行业名称: {result['industry_name']}")
    print(f"      综合评分: {result['overall_score']}")
    print(f"      评级: {result['rating']}")
    print(f"      推荐股票数量: {len(result['top_stocks'])}")
    
    print()
    print("   📊 推荐股票:")
    for i, stock in enumerate(result['top_stocks'], 1):
        print(f"      {i}. {stock['name']} ({stock['ticker']}) - 评分: {stock['score']}")
        print(f"         理由: {stock['reason']}")
    
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("✅ 行业分析测试通过！")
print("=" * 60)
print()
print("📋 下一步:")
print("   1. 测试股票筛选功能")
print("   2. 测试组合诊断功能")
print("   3. 测试智能投顾功能")
print()
