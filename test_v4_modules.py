#!/usr/bin/env python3
"""
v4.0 模块测试脚本

测试所有新增模块是否能正常导入和运行。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

# 添加 scripts 目录到路径（兼容现有代码）
SCRIPTS_DIR = ROOT / "skills" / "deep-analysis" / "scripts"
if not SCRIPTS_DIR.exists():
    # Hermes layout
    SCRIPTS_DIR = ROOT / "scripts"

# 关键：添加 scripts 目录到路径（lib 模块在这里）
sys.path.insert(0, str(SCRIPTS_DIR))

print(f"🔍 测试 v4.0 模块...")
print(f"   根目录: {ROOT}")
print(f"   脚本目录: {SCRIPTS_DIR}")

print(f"🔍 测试 v4.0 模块...")
print(f"   根目录: {ROOT}")
print(f"   脚本目录: {SCRIPTS_DIR}")
print()

# 测试结果
passed = 0
failed = 0

def test_module(name: str, import_path: str, test_func=None):
    """测试单个模块"""
    global passed, failed
    
    print(f"📊 测试: {name}")
    
    try:
        # 导入模块
        exec(f"import {import_path}")
        print(f"   ✅ 导入成功: {import_path}")
        
        # 如果有测试函数，执行它
        if test_func:
            test_func()
            print(f"   ✅ 功能测试通过")
        
        passed += 1
        
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    
    print()

# ─── 测试 1: Target 抽象层 ───
def test_target():
    from lib.target.base import TickerTarget, IndustryTarget, PortfolioTarget
    
    # 测试 TickerTarget
    ticker = TickerTarget(name="600519.SH")
    assert ticker.to_legacy_tickers() == ["600519.SH"]
    assert ticker.get_cache_key() == "600519.SH"
    print(f"      TickerTarget: ✅")
    
    # 测试 IndustryTarget
    industry = IndustryTarget(name="白酒", top_n=5)
    assert industry.target_type == "industry"
    assert industry.top_n == 5
    print(f"      IndustryTarget: ✅")

test_module("Target 抽象层", "lib.target.base", test_target)

# ─── 测试 2: 采集适配器 ───
def test_collect_adapter():
    from lib.pipeline.collect_adapter import DataCollector
    
    # 测试创建采集器
    from lib.target.base import TickerTarget
    target = TickerTarget(name="600519.SH")
    collector = DataCollector(target)
    assert collector.target == target
    print(f"      DataCollector: ✅")

test_module("采集适配器", "lib.pipeline.collect_adapter", test_collect_adapter)

# ─── 测试 3: 评分适配器 ───
def test_score_adapter():
    from lib.pipeline.score_adapter import ScoreEngine
    
    # 测试创建评分器
    from lib.target.base import TickerTarget
    target = TickerTarget(name="600519.SH")
    engine = ScoreEngine(target)
    assert engine.target == target
    print(f"      ScoreEngine: ✅")

test_module("评分适配器", "lib.pipeline.score_adapter", test_score_adapter)

# ─── 测试 4: 行业分析器 ───
def test_industry_analyzer():
    from lib.analysis.industry_analyzer import IndustryAnalyzer
    
    # 测试创建分析器
    analyzer = IndustryAnalyzer()
    assert analyzer.collector is None
    assert analyzer.scorer is None
    print(f"      IndustryAnalyzer: ✅")

test_module("行业分析器", "lib.analysis.industry_analyzer", test_industry_analyzer)

# ─── 测试 5: 股票筛选器 ───
def test_stock_screener():
    from lib.analysis.stock_screener import StockScreener
    
    # 测试创建筛选器
    screener = StockScreener()
    assert screener.collector is None
    assert screener.scorer is None
    print(f"      StockScreener: ✅")

test_module("股票筛选器", "lib.analysis.stock_screener", test_stock_screener)

# ─── 测试 6: 组合顾问 ───
def test_portfolio_advisor():
    from lib.analysis.portfolio_advisor import PortfolioAdvisor
    
    # 测试创建顾问
    advisor = PortfolioAdvisor()
    assert advisor.collector is None
    assert advisor.scorer is None
    print(f"      PortfolioAdvisor: ✅")

test_module("组合顾问", "lib.analysis.portfolio_advisor", test_portfolio_advisor)

# ─── 测试 7: 推荐引擎 ───
def test_recommend_engine():
    from lib.analysis.recommend_engine import RecommendEngine
    
    # 测试创建引擎
    engine = RecommendEngine()
    assert engine.industry_analyzer is not None
    assert engine.stock_screener is not None
    assert engine.portfolio_advisor is not None
    print(f"      RecommendEngine: ✅")

test_module("推荐引擎", "lib.analysis.recommend_engine", test_recommend_engine)

# ─── 总结 ───
print("=" * 60)
print(f"📊 测试结果: {passed} 通过, {failed} 失败")
print("=" * 60)

if failed == 0:
    print("✅ 所有模块测试通过！")
    print()
    print("📋 下一步:")
    print("   1. 测试 run.py 参数解析")
    print("   2. 测试实际数据采集（需要网络）")
    print("   3. 优化行业成分股获取逻辑")
else:
    print("❌ 有模块导入失败，请检查错误信息。")

print()
sys.exit(0 if failed == 0 else 1)
