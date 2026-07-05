#!/usr/bin/env python3
"""
测试修复的逻辑漏洞：
1. 评分字段名错误（overall_score → panel_consensus）
2. 推荐理由逻辑漏洞（评分低但理由说"综合评分较高"）
"""

import sys
from pathlib import Path

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent / "skills" / "deep-analysis" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

def test_logic_fix():
    """测试逻辑漏洞修复"""
    print("🧪 测试逻辑漏洞修复\n")
    
    # 模拟一个评分很低的数据
    mock_score = {
        "panel": {
            "panel_consensus": 35,  # 评分很低
            "investors": []
        },
        "dimensions": {
            "0_basic": {
                "score": 45,  # 基本面评分低
                "data": {"name": "测试股票"}
            },
            "1_financials": {
                "score": 40  # 财务评分低
            },
            "2_kline": {
                "score": 30  # 技术面评分低
            }
        }
    }
    
    print("测试场景：评分很低的情况")
    print("  - panel_consensus: 35")
    print("  - basic_score: 45")
    print("  - financial_score: 40")
    print("  - kline_score: 30\n")
    
    try:
        from lib.analysis.industry_analyzer import IndustryAnalyzer
        
        analyzer = IndustryAnalyzer()
        
        # 测试 _generate_stock_reason()
        reason = analyzer._generate_stock_reason("TEST", mock_score)
        
        print(f"生成的推荐理由: {reason}\n")
        
        if "综合评分较高" in reason:
            print("❌ 逻辑漏洞未修复！评分低但理由说'综合评分较高'")
            return False
        else:
            print("✅ 逻辑漏洞已修复！推荐理由反映真实评分")
            print(f"   理由: {reason}")
            return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_score_field():
    """测试评分字段名是否正确"""
    print("\n" + "="*60)
    print("测试评分字段名\n")
    
    # 模拟 stock_scores
    mock_stock_scores = {
        "TEST.XX": {
            "panel": {
                "panel_consensus": 75  # 正确的字段名
            },
            "dimensions": {
                "0_basic": {
                    "data": {"name": "测试股票"}
                }
            }
        }
    }
    
    try:
        from lib.analysis.industry_analyzer import IndustryAnalyzer
        
        analyzer = IndustryAnalyzer()
        
        # 测试 _extract_top_stocks()
        top_stocks = analyzer._extract_top_stocks(mock_stock_scores, n=1)
        
        if top_stocks:
            score = top_stocks[0].get("score", 0)
            print(f"提取的评分: {score}")
            
            if score == 75:
                print("✅ 评分字段名正确（使用 panel_consensus）")
                return True
            else:
                print(f"❌ 评分字段名错误（获取到的是 {score}，应该是 75）")
                return False
        else:
            print("❌ 未提取到股票")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result1 = test_logic_fix()
    result2 = test_score_field()
    
    print("\n" + "="*60)
    if result1 and result2:
        print("✅ 所有测试通过！逻辑漏洞已修复")
    else:
        print("❌ 部分测试失败，需要进一步检查")
