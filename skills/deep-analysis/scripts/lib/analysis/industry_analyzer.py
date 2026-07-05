"""
行业分析器 - v4.0 新增

功能 1：针对输入的行业，判断哪个行业值得入手

使用示例：
    analyzer = IndustryAnalyzer()
    result = analyzer.analyze("白酒")
    result = analyzer.compare(["白酒", "新能源", "医药"])
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


class IndustryAnalyzer:
    """
    行业分析器
    
    核心功能：
    1. analyze(industry_name) - 分析单个行业
    2. compare(industry_list) - 对比多个行业
    """
    
    def __init__(self):
        self.collector = None
        self.scorer = None
    
    def analyze(self, industry_name: str, top_n: int = 10, 
                 detailed: bool = False) -> Dict:
        """
        分析单个行业
        
        参数：
        - industry_name: 行业名称（如"白酒"）
        - top_n: 分析的龙头股数量
        - detailed: 是否生成详细报告
        
        返回：
        {
            "industry_name": "白酒",
            "overall_score": 75.5,
            "rating": "值得关注",
            "reasons": [...],
            "top_stocks": [...],
            "risks": [...],
            "report_path": "reports/industry_白酒_20260705/index.html"
        }
        """
        print(f"\n{'='*60}")
        print(f"📊 分析行业: {industry_name}")
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
        
        # 4. 生成分析结果
        print(f"\n步骤 3/4: 生成分析...")
        analysis = self._generate_analysis(data, scores)
        
        # 5. 生成报告
        if detailed:
            print(f"\n步骤 4/4: 生成报告...")
            report_path = self._generate_report(data, scores, analysis)
            analysis["report_path"] = report_path
        
        print(f"\n{'='*60}")
        print(f"✅ 分析完成: {industry_name}")
        print(f"   评分: {analysis['overall_score']}")
        print(f"   评级: {analysis['rating']}")
        print(f"{'='*60}\n")
        
        return analysis
    
    def compare(self, industry_list: List[str], top_n: int = 5) -> Dict:
        """
        对比多个行业（快速对比用 TOP 5）
        
        参数：
        - industry_list: 行业名称列表
        - top_n: 每个行业分析的龙头数量
        
        返回：
        {
            "ranking": [
                {"industry": "白酒", "score": 80, "rating": "推荐"},
                {"industry": "新能源", "score": 65, "rating": "观望"},
            ],
            "best_industry": "白酒",
            "comparison_report": "reports/comparison_20260705/index.html"
        }
        """
        print(f"\n{'='*60}")
        print(f"📊 对比行业: {', '.join(industry_list)}")
        print(f"{'='*60}\n")
        
        results = []
        
        for i, industry in enumerate(industry_list, 1):
            print(f"\n[{i}/{len(industry_list)}] 分析: {industry}")
            result = self.analyze(industry, top_n=top_n, detailed=False)
            results.append(result)
        
        # 排序
        ranking = sorted(results, key=lambda x: x["overall_score"], reverse=True)
        
        print(f"\n{'='*60}")
        print(f"🏆 行业排名:")
        for i, item in enumerate(ranking, 1):
            print(f"   {i}. {item['industry_name']} - 评分: {item['overall_score']} ({item['rating']})")
        print(f"{'='*60}\n")
        
        return {
            "ranking": ranking,
            "best_industry": ranking[0]["industry_name"] if ranking else None,
            "best_score": ranking[0]["overall_score"] if ranking else 0
        }
    
    def _generate_analysis(self, data: Dict, scores: Dict) -> Dict:
        """
        生成行业分析结论
        
        提取关键信息：
        - 行业整体评分
        - TOP 3 推荐股票
        - 看多/看空理由
        - 风险提示
        """
        industry_name = data["_industry_name"]
        industry_score = scores.get("industry_score", {})
        industry_panel = scores.get("industry_panel", {})
        stock_scores = scores.get("stock_scores", {})
        
        # 1. 整体评分和评级
        overall_score = industry_score.get("avg_score", 0)
        rating = industry_score.get("consensus", "无法评估")
        
        # 2. 提取推荐股票（TOP 3）
        top_stocks = self._extract_top_stocks(stock_scores, n=3)
        
        # 3. 提取看多理由
        reasons_bullish = self._extract_reasons(industry_panel, signal="bullish")
        
        # 4. 提取看空理由
        reasons_bearish = self._extract_reasons(industry_panel, signal="bearish")
        
        # 5. 风险提示
        risks = self._extract_risks(data)
        
        return {
            "industry_name": industry_name,
            "overall_score": overall_score,
            "rating": rating,
            "top_stocks": top_stocks,
            "reasons_bullish": reasons_bullish,
            "reasons_bearish": reasons_bearish,
            "risks": risks,
            "stock_count": industry_score.get("stock_count", 0)
        }
    
    def _extract_top_stocks(self, stock_scores: Dict, n: int = 3) -> List[Dict]:
        """提取 TOP N 推荐股票"""
        valid_scores = [(ticker, score) for ticker, score in stock_scores.items() if score]
        
        # 按综合评分排序
        sorted_stocks = sorted(
            valid_scores,
            key=lambda x: x[1].get("panel", {}).get("overall_score", 0),
            reverse=True
        )
        
        top_stocks = []
        for ticker, score in sorted_stocks[:n]:
            panel = score.get("panel", {})
            basic = score.get("dimensions", {}).get("0_basic", {}).get("data", {})
            
            top_stocks.append({
                "ticker": ticker,
                "name": basic.get("name", ticker),
                "score": panel.get("overall_score", 0),
                "reason": self._generate_stock_reason(ticker, score)
            })
        
        return top_stocks
    
    def _extract_reasons(self, panel: Dict, signal: str) -> List[str]:
        """提取看多/看空理由"""
        # TODO: 从 industry_panel 中提取真实理由
        # 临时返回示例数据
        if signal == "bullish":
            return [
                "行业估值处于历史低位",
                "龙头股护城河深厚",
                "政策面支持消费复苏"
            ]
        else:
            return [
                "消费复苏不及预期",
                "行业竞争加剧",
                "原材料成本上升"
            ]
    
    def _extract_risks(self, data: Dict) -> List[str]:
        """提取风险提示"""
        # TODO: 从数据中分析风险
        return [
            "行业政策变化风险",
            "市场需求不及预期风险",
            "宏观经济波动风险"
        ]
    
    def _generate_stock_reason(self, ticker: str, score: Dict) -> str:
        """生成单只股票的推荐理由"""
        panel = score.get("panel", {})
        dimensions = score.get("dimensions", {})
        
        # 提取关键维度评分
        basic_score = dimensions.get("0_basic", {}).get("score", 0)
        financial_score = dimensions.get("1_financials", {}).get("score", 0)
        
        reasons = []
        if basic_score >= 70:
            reasons.append("基本面良好")
        if financial_score >= 70:
            reasons.append("财务健康")
        
        return "；".join(reasons) if reasons else "综合评分较高"
    
    def _generate_report(self, data: Dict, scores: Dict, analysis: Dict) -> str:
        """生成行业分析报告"""
        # TODO: 实现报告生成逻辑
        # 临时返回示例路径
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report_dir = Path(f"reports/industry_{data['_industry_name']}_{timestamp}")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / "index.html"
        report_path.write_text("<html><body><h1>行业分析报告</h1></body></html>", encoding="utf-8")
        
        return str(report_path)


def analyze_industry(industry_name: str, top_n: int = 10, detailed: bool = False) -> Dict:
    """
    快捷函数：分析单个行业
    
    使用示例：
    from lib.analysis.industry_analyzer import analyze_industry
    result = analyze_industry("白酒")
    """
    analyzer = IndustryAnalyzer()
    return analyzer.analyze(industry_name, top_n=top_n, detailed=detailed)


def compare_industries(industry_list: List[str]) -> Dict:
    """
    快捷函数：对比多个行业
    
    使用示例：
    from lib.analysis.industry_analyzer import compare_industries
    result = compare_industries(["白酒", "新能源", "医药"])
    """
    analyzer = IndustryAnalyzer()
    return analyzer.compare(industry_list)


if __name__ == "__main__":
    # 测试代码
    print("测试行业分析器...")
    
    analyzer = IndustryAnalyzer()
    
    # 测试单个行业分析
    result = analyzer.analyze("白酒", top_n=5)
    print(f"\n分析结果: {result['industry_name']}")
    print(f"评分: {result['overall_score']}")
    print(f"评级: {result['rating']}")
    
    # 测试行业对比
    # result = analyzer.compare(["白酒", "新能源"])
    # print(f"\n最佳行业: {result['best_industry']}")
