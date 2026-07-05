"""
股票筛选器 - v4.0 新增

功能 2：输入某个行业，从中挖掘出建议购买的几只股票

使用示例：
    screener = StockScreener()
    result = screener.screen("白酒", criteria="balanced")
    result = screener.screen("新能源", top_n=5, criteria="growth")
"""

from typing import Dict, List, Optional
from pathlib import Path
import json
import sys

# 添加父目录到 sys.path
HERE = Path(__file__).parent.parent
sys.path.insert(0, str(HERE))

from target.base import IndustryTarget, create_target
from pipeline.collect_adapter import DataCollector
from pipeline.score_adapter import ScoreEngine


class StockScreener:
    """
    股票筛选器
    
    核心功能：
    1. screen(industry, criteria) - 从行业中筛选推荐股票
    2. screen_with_filters(industry, filters) - 自定义筛选条件
    
    筛选标准：
    - value: 价值型（低 PE + 高股息 + 护城河）
    - growth: 成长型（高增速 + 高 PEG）
    - balanced: 均衡型（综合评分 TOP 3）
    - aggressive: 激进型（游资偏好 + 技术突破）
    """
    
    def __init__(self):
        self.collector = None
        self.scorer = None
    
    def screen(self, industry_name: str, 
                criteria: str = "balanced",
                top_n: int = 10,
                detailed: bool = False) -> Dict:
        """
        从行业中筛选推荐股票
        
        参数：
        - industry_name: 行业名称
        - criteria: 筛选标准 (value/growth/balanced/aggressive)
        - top_n: 分析的龙头数量
        - detailed: 是否生成详细报告
        
        返回：
        {
            "industry_name": "白酒",
            "criteria": "balanced",
            "recommended": [
                {
                    "ticker": "600519.SH",
                    "name": "贵州茅台",
                    "score": 85,
                    "reason": "护城河深厚，ROE稳定",
                    "target_price": 2200,
                    "position_suggestion": "30%"  # 建议配置比例
                },
                ...
            ],
            "not_recommended": [...],
            "industry_outlook": "中性偏多",
            "report_path": "reports/screen_白酒_balanced_20240705/index.html"
        }
        """
        print(f"\n{'='*60}")
        print(f"🔍 筛选股票: {industry_name} (标准: {criteria})")
        print(f"{'='*60}\n")
        
        # 1. 创建 IndustryTarget
        target = create_target(
            "industry", 
            industry_name,
            top_n=top_n
        )
        
        # 2. 数据采集
        print(f"步骤 1/4: 数据采集...")
        self.collector = DataCollector(target)
        data = self.collector.collect()
        
        # 3. 评分
        print(f"\n步骤 2/4: 评分...")
        self.scorer = ScoreEngine(target)
        scores = self.scorer.score(data)
        
        # 4. 筛选逻辑
        print(f"\n步骤 3/4: 筛选股票 (标准: {criteria})...")
        recommended = self._filter_stocks(data, scores, criteria)
        
        # 5. 生成配置建议
        print(f"\n步骤 4/4: 生成配置建议...")
        portfolio_suggestion = self._generate_portfolio_suggestion(recommended)
        
        # 6. 生成报告（如果需要）
        report_path = None
        if detailed:
            print(f"\n生成详细报告...")
            report_path = self._generate_report(
                industry_name, recommended, portfolio_suggestion
            )
        
        print(f"\n{'='*60}")
        print(f"✅ 筛选完成: {industry_name}")
        print(f"   推荐股票: {len(recommended['recommended'])} 只")
        print(f"   行业展望: {portfolio_suggestion['industry_outlook']}")
        print(f"{'='*60}\n")
        
        return {
            "industry_name": industry_name,
            "criteria": criteria,
            "recommended": recommended["recommended"],
            "not_recommended": recommended["not_recommended"],
            "industry_outlook": portfolio_suggestion["industry_outlook"],
            "portfolio_suggestion": portfolio_suggestion,
            "report_path": report_path
        }
    
    def screen_with_filters(self, industry_name: str, 
                           filters: Dict) -> Dict:
        """
        自定义筛选条件
        
        参数：
        - filters: 筛选条件字典
          {
              "pe_max": 30,
              "roe_min": 15,
              "growth_min": 20,
              "dividend_yield_min": 2
          }
        
        返回：
        筛选结果（同 screen()）
        """
        # TODO: 实现自定义筛选逻辑
        pass
    
    def _filter_stocks(self, data: Dict, scores: Dict, 
                        criteria: str) -> Dict:
        """
        根据标准筛选股票
        
        返回：
        {
            "recommended": [...],  # TOP 3
            "not_recommended": [...]  # 其余
        }
        """
        stocks = scores.get("stock_scores", {})
        
        if criteria == "value":
            # 价值型：低 PE + 高股息 + 护城河
            filtered = self._filter_value(stocks)
        elif criteria == "growth":
            # 成长型：高增速 + 高 PEG
            filtered = self._filter_growth(stocks)
        elif criteria == "balanced":
            # 均衡型：综合评分 TOP 3
            filtered = self._filter_balanced(stocks)
        elif criteria == "aggressive":
            # 激进型：游资偏好 + 技术突破
            filtered = self._filter_aggressive(stocks)
        else:
            # 默认：均衡型
            filtered = self._filter_balanced(stocks)
        
        # 排序并返回 TOP N
        recommended = sorted(
            filtered["recommended"],
            key=lambda x: x["score"],
            reverse=True
        )[:3]  # TOP 3
        
        return {
            "recommended": recommended,
            "not_recommended": filtered["not_recommended"]
        }
    
    def _filter_value(self, stocks: Dict) -> Dict:
        """价值型筛选"""
        recommended = []
        not_recommended = []
        
        for ticker, score in stocks.items():
            if score is None:
                continue
            
            # 提取关键指标
            dimensions = score.get("dimensions", {})
            panel = score.get("panel", {})
            
            basic = dimensions.get("0_basic", {}).get("data", {})
            valuation = dimensions.get("10_valuation", {}).get("data", {})
            
            pe = basic.get("pe")
            pb = basic.get("pb")
            dividend_yield = valuation.get("dividend_yield")
            
            overall_score = panel.get("panel_consensus", 0)
            
            # 价值型标准：
            # 1. PE < 30
            # 2. PB < 3
            # 3. 股息率 > 2%
            # 4. 综合评分 > 60
            is_value = (
                (pe and pe < 30) or True  # 临时：不过滤
            ) and overall_score > 60
            
            stock_info = self._format_stock_info(ticker, score)
            
            if is_value:
                recommended.append(stock_info)
            else:
                not_recommended.append(stock_info)
        
        return {
            "recommended": recommended,
            "not_recommended": not_recommended
        }
    
    def _filter_growth(self, stocks: Dict) -> Dict:
        """成长型筛选"""
        # TODO: 实现成长型筛选逻辑
        # 临时：返回综合评分 TOP 5
        return self._filter_balanced(stocks)
    
    def _filter_balanced(self, stocks: Dict) -> Dict:
        """均衡型筛选（综合评分 TOP 3）"""
        recommended = []
        not_recommended = []
        
        for ticker, score in stocks.items():
            if score is None:
                continue
            
            stock_info = self._format_stock_info(ticker, score)
            overall_score = stock_info["score"]
            
            # 均衡型：综合评分 > 65
            if overall_score >= 65:
                recommended.append(stock_info)
            else:
                not_recommended.append(stock_info)
        
        return {
            "recommended": recommended,
            "not_recommended": not_recommended
        }
    
    def _filter_aggressive(self, stocks: Dict) -> Dict:
        """激进型筛选"""
        # TODO: 实现激进型筛选逻辑
        # 临时：返回综合评分 TOP 3
        return self._filter_balanced(stocks)
    
    def _format_stock_info(self, ticker: str, score: Dict) -> Dict:
        """格式化股票信息"""
        dimensions = score.get("dimensions", {})
        panel = score.get("panel", {})
        
        basic = dimensions.get("0_basic", {}).get("data", {})
        
        return {
            "ticker": ticker,
            "name": basic.get("name", ticker),
            "score": panel.get("panel_consensus", 0),
            "reason": self._generate_reason(ticker, score),
            "target_price": self._calculate_target_price(score),
            "position_suggestion": "20%"  # 临时：固定 20%
        }
    
    def _generate_reason(self, ticker: str, score: Dict) -> str:
        """生成推荐理由"""
        dimensions = score.get("dimensions", {})
        panel = score.get("panel", {})
        
        # 提取关键维度评分
        basic_score = dimensions.get("0_basic", {}).get("score", 0)
        financial_score = dimensions.get("1_financials", {}).get("score", 0)
        moat_score = dimensions.get("14_moat", {}).get("score", 0)
        
        reasons = []
        if basic_score >= 70:
            reasons.append("基本面良好")
        if financial_score >= 70:
            reasons.append("财务健康")
        if moat_score >= 70:
            reasons.append("护城河深厚")
        
        # 提取评委看法
        panel_insights = panel.get("insights", "")
        if panel_insights:
            reasons.append(panel_insights[:50])  # 截取前 50 字符
        
        return "；".join(reasons) if reasons else "综合评分较高"
    
    def _calculate_target_price(self, score: Dict) -> Optional[float]:
        """计算目标价（基于 DCF）"""
        synthesis = score.get("synthesis", {})
        dcf = synthesis.get("dcf", {})
        
        intrinsic_value = dcf.get("intrinsic_value")
        
        if intrinsic_value:
            return round(intrinsic_value, 2)
        else:
            # 无法计算 DCF，返回 None
            return None
    
    def _generate_portfolio_suggestion(self, recommended: Dict) -> Dict:
        """生成组合配置建议"""
        recommended_stocks = recommended.get("recommended", [])
        
        if not recommended_stocks:
            return {
                "industry_outlook": "中性",
                "suggested_positions": [],
                "total_allocation": "0%",
                "risk_warning": "无推荐股票"
            }
        
        # 按评分分配权重
        total_score = sum(s["score"] for s in recommended_stocks)
        
        suggested_positions = []
        for stock in recommended_stocks:
            weight = round((stock["score"] / total_score) * 100)
            suggested_positions.append({
                "ticker": stock["ticker"],
                "name": stock["name"],
                "weight": f"{weight}%",
                "reason": stock["reason"]
            })
        
        # 行业展望（基于评委共识）
        # TODO: 从 industry_panel 中提取
        industry_outlook = "中性偏多"
        
        return {
            "industry_outlook": industry_outlook,
            "suggested_positions": suggested_positions,
            "total_allocation": "100%",
            "risk_warning": self._generate_risk_warning(recommended_stocks)
        }
    
    def _generate_risk_warning(self, recommended_stocks: List[Dict]) -> List[str]:
        """生成风险提示"""
        # TODO: 从数据中提取真实风险
        return [
            "行业政策变化风险",
            "市场需求不及预期风险",
            "个股估值过高风险"
        ]
    
    def _generate_report(self, industry_name: str, 
                        recommended: Dict, 
                        portfolio: Dict) -> str:
        """生成筛选报告"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report_dir = Path(f"reports/screen_{industry_name}_{timestamp}")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / "index.html"
        
        # 临时：生成简单 HTML
        html_content = f"""
        <html>
        <head><title>股票筛选报告 - {industry_name}</title></head>
        <body>
            <h1>股票筛选报告</h1>
            <h2>行业: {industry_name}</h2>
            <h3>推荐股票:</h3>
            <ul>
        """
        
        for stock in recommended.get("recommended", []):
            html_content += f"""
                <li>{stock['name']} ({stock['ticker']}) - 评分: {stock['score']}</li>
            """
        
        html_content += """
            </ul>
        </body>
        </html>
        """
        
        report_path.write_text(html_content, encoding="utf-8")
        
        return str(report_path)


def screen_industry(industry_name: str, criteria: str = "balanced") -> Dict:
    """
    快捷函数：从行业中筛选推荐股票
    
    使用示例：
    from lib.analysis.stock_screener import screen_industry
    result = screen_industry("白酒", criteria="balanced")
    """
    screener = StockScreener()
    return screener.screen(industry_name, criteria=criteria, detailed=True)


if __name__ == "__main__":
    # 测试代码
    print("测试股票筛选器...")
    
    screener = StockScreener()
    
    # 测试筛选
    result = screener.screen("白酒", criteria="balanced", top_n=5)
    print(f"\n筛选结果: {result['industry_name']}")
    print(f"推荐股票: {len(result['recommended'])} 只")
    for stock in result["recommended"]:
        print(f"  - {stock['name']} ({stock['ticker']}) - 评分: {stock['score']}")
