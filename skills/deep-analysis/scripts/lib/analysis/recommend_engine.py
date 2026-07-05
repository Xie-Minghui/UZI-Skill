"""
推荐引擎 - v4.0 新增

功能串联：先选择行业再选择股票

完整投资决策流程：
1. 筛选最佳行业（功能 1）
2. 从行业中选择推荐股票（功能 2）
3. 生成组合配置方案（功能 3）

使用示例：
    engine = RecommendEngine()
    result = engine.recommend(
        industry_list=["白酒", "新能源", "医药"],
        budget=100000,
        risk_tolerance="moderate"
    )
"""

from typing import Dict, List, Optional
from pathlib import Path
import json
import sys

# 添加父目录到 sys.path
HERE = Path(__file__).parent.parent
sys.path.insert(0, str(HERE))

from analysis.industry_analyzer import IndustryAnalyzer
from analysis.stock_screener import StockScreener
from analysis.portfolio_advisor import PortfolioAdvisor


class RecommendEngine:
    """
    推荐引擎
    
    核心功能：
    recommend(industry_list, budget, risk_tolerance) - 完整投资决策
    
    返回：
    {
        "selected_industry": "白酒",
        "industry_analysis": {...},
        "recommended_stocks": [...],
        "portfolio": {
            "total_budget": 100000,
            "positions": [...],
            "cash_reserve": 20000
        },
        "expected_return": "15-20%",
        "risk_warning": [...],
        "report_path": "reports/recommend_20240705/index.html"
    }
    """
    
    def __init__(self):
        self.industry_analyzer = IndustryAnalyzer()
        self.stock_screener = StockScreener()
        self.portfolio_advisor = PortfolioAdvisor()
    
    def recommend(self, 
                  industry_list: List[str], 
                  budget: float = 100000, 
                  risk_tolerance: str = "moderate") -> Dict:
        """
        完整投资决策流程
        
        参数：
        - industry_list: 候选行业列表
        - budget: 预算（元）
        - risk_tolerance: 风险承受能力 (conservative/moderate/aggressive)
        
        返回：完整投资建议
        """
        print(f"\n{'='*60}")
        print(f"🎯 智能投顾引擎")
        print(f"   候选行业: {', '.join(industry_list)}")
        print(f"   预算: ¥{budget:,.0f}")
        print(f"   风险偏好: {risk_tolerance}")
        print(f"{'='*60}\n")
        
        # 步骤 1：行业筛选（功能 1）
        print(f"📊 步骤 1/4: 行业筛选...")
        industry_comparison = self.industry_analyzer.compare(industry_list)
        selected_industry = industry_comparison["best_industry"]
        best_score = industry_comparison["best_score"]
        
        print(f"\n✅ 最佳行业: {selected_industry} (评分: {best_score})")
        
        # 步骤 2：个股挖掘（功能 2）
        print(f"\n📊 步骤 2/4: 从 '{selected_industry}' 中筛选个股...")
        criteria = self._map_risk_to_criteria(risk_tolerance)
        stock_recommendation = self.stock_screener.screen(
            selected_industry, 
            criteria=criteria,
            top_n=10,
            detailed=False
        )
        
        recommended_stocks = stock_recommendation["recommended"]
        print(f"\n✅ 推荐股票: {len(recommended_stocks)} 只")
        for i, stock in enumerate(recommended_stocks, 1):
            print(f"   {i}. {stock['name']} ({stock['ticker']}) - 评分: {stock['score']}")
        
        # 步骤 3：生成组合配置
        print(f"\n📊 步骤 3/4: 生成组合配置...")
        portfolio = self._allocate_budget(
            recommended_stocks,
            budget,
            risk_tolerance
        )
        
        print(f"\n✅ 资金配置方案:")
        print(f"   总投资: ¥{portfolio['total_budget']:,.0f}")
        print(f"   股票投资: ¥{portfolio['total_investment']:,.0f}")
        print(f"   现金储备: ¥{portfolio['cash_reserve']:,.0f}")
        
        for position in portfolio["positions"]:
            print(f"   - {position['name']}: ¥{position['amount']:,.0f} ({position['percentage']})")
        
        # 步骤 4：生成完整报告
        print(f"\n📊 步骤 4/4: 生成投资建议报告...")
        report = self._generate_recommendation_report(
            industry_comparison,
            stock_recommendation,
            portfolio,
            risk_tolerance
        )
        
        print(f"\n{'='*60}")
        print(f"✅ 投资建议生成完成")
        print(f"   报告路径: {report['report_path']}")
        print(f"{'='*60}\n")
        
        return report
    
    def quick_recommend(self, 
                        industry_list: List[str],
                        budget: float = 100000) -> Dict:
        """
        快速推荐（简化版）
        
        与 recommend() 的区别：
        - 不生成详细报告
        - 只返回核心建议
        
        返回：
        {
            "selected_industry": "白酒",
            "top_3_stocks": [...],
            "allocation": {...}
        }
        """
        # 简化版：只做行业筛选 + 股票推荐
        industry_comparison = self.industry_analyzer.compare(industry_list)
        selected_industry = industry_comparison["best_industry"]
        
        stock_recommendation = self.stock_screener.screen(
            selected_industry, 
            criteria="balanced",
            top_n=3,
            detailed=False
        )
        
        return {
            "selected_industry": selected_industry,
            "top_3_stocks": stock_recommendation["recommended"],
            "allocation": self._allocate_budget(
                stock_recommendation["recommended"],
                budget,
                "moderate"
            )
        }
    
    def _map_risk_to_criteria(self, risk_tolerance: str) -> str:
        """根据风险偏好选择筛选标准"""
        mapping = {
            "conservative": "value",      # 保守 → 价值型
            "moderate": "balanced",     # 稳健 → 均衡型
            "aggressive": "growth"       # 激进 → 成长型
        }
        return mapping.get(risk_tolerance, "balanced")
    
    def _allocate_budget(self, 
                         recommended_stocks: List[Dict], 
                         budget: float, 
                         risk_tolerance: str) -> Dict:
        """
        分配资金
        
        逻辑：
        1. 根据评分分配权重
        2. 留出现金储备（根据风险偏好）
        3. 计算每只股票的投资金额
        
        现金储备比例：
        - conservative: 30%
        - moderate: 20%
        - aggressive: 10%
        """
        if not recommended_stocks:
            return {
                "total_budget": budget,
                "total_investment": 0,
                "cash_reserve": budget,
                "positions": []
            }
        
        # 1. 计算现金储备
        cash_reserve_pct = {
            "conservative": 0.3,
            "moderate": 0.2,
            "aggressive": 0.1
        }.get(risk_tolerance, 0.2)
        
        cash_reserve = budget * cash_reserve_pct
        total_investment = budget - cash_reserve
        
        # 2. 根据评分分配权重
        total_score = sum(stock["score"] for stock in recommended_stocks)
        
        positions = []
        for stock in recommended_stocks:
            weight = stock["score"] / total_score
            amount = total_investment * weight
            
            positions.append({
                "ticker": stock["ticker"],
                "name": stock["name"],
                "score": stock["score"],
                "weight": round(weight * 100, 1),
                "amount": round(amount, 2),
                "percentage": f"{round(weight * 100, 1)}%",
                "reason": stock["reason"]
            })
        
        return {
            "total_budget": budget,
            "total_investment": total_investment,
            "cash_reserve": cash_reserve,
            "positions": positions,
            "risk_tolerance": risk_tolerance
        }
    
    def _generate_recommendation_report(self, 
                                      industry_cmp: Dict, 
                                      stock_rec: Dict, 
                                      portfolio: Dict,
                                      risk_tolerance: str) -> Dict:
        """
        生成投资建议报告
        
        报告结构：
        1. 行业选择逻辑
        2. 个股推荐理由
        3. 资金配置方案
        4. 预期收益和风险
        5. 操作建议
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report_dir = Path(f"reports/recommend_{timestamp}")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / "index.html"
        
        # 临时：生成简单 HTML
        selected_industry = industry_cmp["best_industry"]
        recommended_stocks = stock_rec["recommended"]
        
        html_content = f"""
        <html>
        <head>
            <title>投资建议报告</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #3498db; color: white; }}
            </style>
        </head>
        <body>
            <h1>🎯 投资建议报告</h1>
            <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <h2>📊 行业选择</h2>
            <p>推荐行业: <strong>{selected_industry}</strong></p>
            <p>选择理由: 综合评分最高</p>
            
            <h2>📊 推荐股票</h2>
            <table>
                <tr>
                    <th>排名</th>
                    <th>股票</th>
                    <th>评分</th>
                    <th>推荐理由</th>
                </tr>
        """
        
        for i, stock in enumerate(recommended_stocks, 1):
            html_content += f"""
                <tr>
                    <td>{i}</td>
                    <td>{stock['name']} ({stock['ticker']})</td>
                    <td>{stock['score']}</td>
                    <td>{stock['reason']}</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <h2>💼 资金配置方案</h2>
        """
        
        for position in portfolio["positions"]:
            html_content += f"""
            <p><strong>{position['name']}</strong>: ¥{position['amount']:,.0f} ({position['percentage']})</p>
            <p>理由: {position['reason']}</p>
            """
        
        html_content += f"""
            <p>现金储备: ¥{portfolio['cash_reserve']:,.0f}</p>
            
            <h2>⚠️ 风险提示</h2>
            <ul>
                <li>行业政策变化风险</li>
                <li>市场需求不及预期风险</li>
                <li>宏观经济波动风险</li>
            </ul>
        </body>
        </html>
        """
        
        report_path.write_text(html_content, encoding="utf-8")
        
        return {
            "selected_industry": selected_industry,
            "industry_analysis": industry_cmp,
            "recommended_stocks": recommended_stocks,
            "portfolio": portfolio,
            "expected_return": "15-20%",  # TODO: 计算预期收益
            "risk_warning": [
                "行业政策变化风险",
                "市场需求不及预期风险",
                "宏观经济波动风险"
            ],
            "report_path": str(report_path)
        }


def recommend_portfolio(industry_list: List[str], 
                        budget: float = 100000,
                        risk_tolerance: str = "moderate") -> Dict:
    """
    快捷函数：完整投资建议
    
    使用示例：
    from lib.analysis.recommend_engine import recommend_portfolio
    result = recommend_portfolio(
        ["白酒", "新能源", "医药"],
        budget=100000,
        risk_tolerance="moderate"
    )
    """
    engine = RecommendEngine()
    return engine.recommend(industry_list, budget, risk_tolerance)


if __name__ == "__main__":
    # 测试代码
    print("测试推荐引擎...")
    
    engine = RecommendEngine()
    
    # 测试完整推荐
    result = engine.recommend(
        industry_list=["白酒", "新能源", "医药"],
        budget=100000,
        risk_tolerance="moderate"
    )
    
    print(f"\n推荐结果:")
    print(f"  最佳行业: {result['selected_industry']}")
    print(f"  推荐股票: {len(result['recommended_stocks'])} 只")
    print(f"  报告路径: {result['report_path']}")
