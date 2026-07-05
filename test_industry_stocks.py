#!/usr/bin/env python3
"""
测试行业成分股获取功能
"""
import sys
from pathlib import Path

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent / "skills" / "deep-analysis" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from lib.target.base import IndustryTarget

def test_industry_stocks():
    """测试行业成分股获取"""
    print("=" * 60)
    print("测试行业成分股获取功能")
    print("=" * 60)
    
    # 测试行业列表
    test_industries = ["白酒", "新能源", "医药", "半导体"]
    
    for industry in test_industries:
        print(f"\n测试行业: {industry}")
        print("-" * 40)
        
        try:
            target = IndustryTarget(name=industry, top_n=5)
            tickers = target.to_legacy_tickers()
            
            if tickers:
                print(f"✅ 成功获取 {len(tickers)} 只成分股:")
                for ticker in tickers:
                    print(f"   - {ticker}")
            else:
                print(f"⚠️  未找到成分股")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_industry_stocks()
