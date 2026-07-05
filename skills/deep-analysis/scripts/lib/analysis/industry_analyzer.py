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


# ═══════════════════════════════════════════════════════════
# 行业 - 评委权重调整配置
# ═══════════════════════════════════════════════════════════

# 行业分类映射：将行业映射到对应的评委组权重调整
INDUSTRY_GROUP_WEIGHTS = {
    # 消费类（白酒、食品、家电）→ 增加 E 组中国价值派权重
    "消费": {
        "E": 1.5,  # 中国价值派权重 +50%
        "A": 1.2,  # 经典价值派权重 +20%
        "F": 1.3,  # 游资权重 +30%
    },
    # 科技类（半导体、AI、软件）→ 增加 B 组成长派和 I 组 AI 专家权重
    "科技": {
        "B": 1.5,  # 成长派权重 +50%
        "I": 2.0,  # AI 专家权重 +100%
        "G": 1.3,  # 量化派权重 +30%
    },
    # 新能源（光伏、电动车、储能）→ 增加 B 组成长派权重
    "新能源": {
        "B": 1.5,  # 成长派权重 +50%
        "C": 1.2,  # 宏观派权重 +20%
        "E": 1.2,  # 中国价值派权重 +20%
    },
    # 医药（生物科技、医疗器械、创新药）→ 增加 B 组成长派权重
    "医药": {
        "B": 1.3,  # 成长派权重 +30%
        "A": 1.2,  # 经典价值派权重 +20%
        "C": 1.2,  # 宏观派权重 +20%
    },
    # 军工（国防、航天）→ 增加 C 组宏观派权重
    "军工": {
        "C": 1.5,  # 宏观派权重 +50%
        "A": 1.2,  # 经典价值派权重 +20%
        "E": 1.1,  # 中国价值派权重 +10%
    },
    # 金融（银行、保险、券商）→ 增加 A 组经典价值派权重
    "金融": {
        "A": 1.5,  # 经典价值派权重 +50%
        "E": 1.3,  # 中国价值派权重 +30%
        "G": 1.2,  # 量化派权重 +20%
    },
}

# 行业关键词映射：将行业名称映射到分类
INDUSTRY_KEYWORDS = {
    "消费": ["白酒", "食品", "饮料", "家电", "零售", "消费"],
    "科技": ["半导体", "芯片", "AI", "人工智能", "软件", "云计算", "物联网"],
    "新能源": ["新能源", "光伏", "电动车", "储能", "锂电池", "风电"],
    "医药": ["医药", "生物", "医疗", "器械", "创新药", "CXO"],
    "军工": ["军工", "国防", "航天", "航空", "兵器"],
    "金融": ["银行", "保险", "券商", "金融"],
}


def get_industry_category(industry_name: str) -> str:
    """
    根据行业名称判断行业分类
    
    返回：
    - 匹配的分类（消费/科技/新能源/医药/军工/金融）
    - 如果无法匹配，返回 "通用"
    """
    for category, keywords in INDUSTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in industry_name:
                return category
    return "通用"


def get_investor_weight_adjustment(industry_name: str) -> Dict:
    """
    根据行业名称获取评委权重调整
    
    返回：
    - {group: weight_multiplier} 字典
    - 例如：{"E": 1.5, "A": 1.2} 表示 E 组权重 ×1.5，A 组权重 ×1.2
    """
    category = get_industry_category(industry_name)
    
    if category == "通用":
        return {}  # 无权重调整
    
    return INDUSTRY_GROUP_WEIGHTS.get(category, {})


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
        
        # 按综合评分排序（使用 panel_consensus 字段）
        sorted_stocks = sorted(
            valid_scores,
            key=lambda x: x[1].get("panel", {}).get("panel_consensus", 0),
            reverse=True
        )
        
        top_stocks = []
        for ticker, score in sorted_stocks[:n]:
            panel = score.get("panel", {})
            basic = score.get("dimensions", {}).get("0_basic", {}).get("data", {})
            
            # 使用正确的字段名：panel_consensus
            overall_score = panel.get("panel_consensus", 0)
            
            top_stocks.append({
                "ticker": ticker,
                "name": basic.get("name", ticker),
                "score": overall_score,  # 使用真实评分
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
        """生成单只股票的推荐理由（基于真实评分）"""
        panel = score.get("panel", {})
        dimensions = score.get("dimensions", {})
        
        # 获取综合评分
        overall_score = panel.get("panel_consensus", 0)  # 注意：字段名是 panel_consensus，不是 overall_score
        
        # 提取关键维度评分
        basic_score = dimensions.get("0_basic", {}).get("score", 0)
        financial_score = dimensions.get("1_financials", {}).get("score", 0)
        kline_score = dimensions.get("2_kline", {}).get("score", 0)
        
        # 根据评分生成理由（避免逻辑漏洞）
        reasons = []
        
        # 正面理由（仅当评分较高时）
        if basic_score >= 70:
            reasons.append("基本面良好")
        if financial_score >= 70:
            reasons.append("财务健康")
        if kline_score >= 70:
            reasons.append("技术面强势")
        
        # 如果有正面理由，返回
        if reasons:
            return "；".join(reasons)
        
        # 负面理由（当评分较低时）
        if overall_score < 40:
            reasons.append("综合评分较低")
            if basic_score < 50:
                reasons.append("基本面薄弱")
            if financial_score < 50:
                reasons.append("财务压力大")
            return "；".join(reasons)
        elif overall_score < 60:
            return "综合评分中等，需谨慎关注"
        
        # 默认理由（评分在 60-70 之间，但没有单个维度特别突出）
        return "综合评分中等，建议关注"
    
    def _generate_report(self, data: Dict, scores: Dict, analysis: Dict) -> str:
        """生成行业分析报告"""
        from datetime import datetime
        
        industry_name = data["_industry_name"]
        industry_panel = scores.get("industry_panel", {})
        
        # 读取模板
        template_path = Path(__file__).parent / "industry_report_template.html"
        if not template_path.exists():
            print(f"   ⚠️ 模板文件不存在: {template_path}")
            # 返回简单报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = Path(f"reports/industry_{industry_name}_{timestamp}")
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / "index.html"
            report_path.write_text("<html><body><h1>行业分析报告</h1></body></html>", encoding="utf-8")
            return str(report_path)
        
        template = template_path.read_text(encoding="utf-8")
        
        # 计算评分样式类
        overall_score = analysis.get("overall_score", 0)
        score_class = "score-bullish" if overall_score >= 60 else "score-neutral" if overall_score >= 40 else "score-bearish"
        
        # 准备模板数据（简单变量）
        simple_vars = {
            "industry_name": industry_name,
            "overall_score": str(overall_score),
            "score_class": score_class,
            "rating": analysis.get("rating", "无法评估"),
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stock_count": str(analysis.get("stock_count", 0)),
            "bullish_count": str(industry_panel.get("bullish_count", 0)),
            "bearish_count": str(industry_panel.get("bearish_count", 0)),
            "neutral_count": str(industry_panel.get("neutral_count", 0)),
            "skip_count": str(industry_panel.get("skip_count", 0)),
            "total_investors": str(industry_panel.get("bullish_count", 0) + industry_panel.get("bearish_count", 0) + industry_panel.get("neutral_count", 0) + industry_panel.get("skip_count", 0)),
            "overall_consensus": industry_panel.get("overall_consensus", "无法判断"),
            "key_reason": industry_panel.get("key_reason", ""),
            "top_stocks_count": str(len(analysis.get("top_stocks", [])))
        }
        
        # 1. 替换简单变量
        for key, value in simple_vars.items():
            placeholder = "{{" + key + "}}"
            template = template.replace(placeholder, value)
        
        # 2. 生成投资者网格 HTML
        investor_grid_html = self._render_investor_grid(industry_panel.get("investor_verdicts", []))
        template = template.replace("{{investor_grid_placeholder}}", investor_grid_html)
        
        # 3. 生成 TOP 股票表格 HTML
        top_stocks_html = self._render_top_stocks_table(analysis.get("top_stocks", []))
        template = template.replace("{{top_stocks_table_placeholder}}", top_stocks_html)
        
        # 4. 生成看多理由列表
        reasons_bullish_html = self._render_reasons_list(analysis.get("reasons_bullish", []))
        template = template.replace("{{reasons_bullish_placeholder}}", reasons_bullish_html)
        
        # 5. 生成看空理由列表
        reasons_bearish_html = self._render_reasons_list(analysis.get("reasons_bearish", []))
        template = template.replace("{{reasons_bearish_placeholder}}", reasons_bearish_html)
        
        # 6. 生成风险列表
        risks_html = self._render_reasons_list(analysis.get("risks", []))
        template = template.replace("{{risks_placeholder}}", risks_html)
        
        # 写报告（使用绝对路径）
        from pathlib import Path as _Path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 基于脚本所在目录构建绝对路径
        script_dir = _Path(__file__).parent.parent.parent / "scripts"
        report_dir = script_dir / "reports" / f"industry_{industry_name}_{timestamp}"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / "index.html"
        report_path.write_text(template, encoding="utf-8")
        
        print(f"   📄 报告已生成: {report_path}")
        
        return str(report_path.resolve())  # 返回绝对路径
    
    def _render_investor_grid(self, investor_verdicts: List[Dict]) -> str:
        """渲染投资者网格 HTML"""
        if not investor_verdicts:
            return "<p style='color: #64748b;'>暂无投资者数据</p>"
        
        html = "<div class='investor-grid'>"
        
        for verdict in investor_verdicts:
            signal = verdict.get("signal", "neutral")
            inv_id = verdict.get("investor_id", "")
            score = verdict.get("score", 0)
            
            # 获取投资者名称（从 INVESTORS 配置中）
            inv_name = self._get_investor_name(inv_id)
            
            signal_text = {
                "bullish": "👍 看多",
                "bearish": "👎 看空",
                "neutral": "🤝 中性",
                "skip": "⏭️ 跳过"
            }.get(signal, "未知")
            
            html += f"""
            <div class='investor-card {signal}'>
                <div class='investor-name'>{inv_name}</div>
                <div class='investor-signal {signal}'>{signal_text}</div>
                <div class='investor-score'>{score}</div>
            </div>
            """
        
        html += "</div>"
        return html
    
    def _render_top_stocks_table(self, top_stocks: List[Dict]) -> str:
        """渲染 TOP 股票表格 HTML"""
        if not top_stocks:
            return "<p style='color: #64748b;'>暂无股票数据</p>"
        
        html = """
        <table class='stock-table'>
            <thead>
                <tr>
                    <th>排名</th>
                    <th>股票代码</th>
                    <th>股票名称</th>
                    <th>综合评分</th>
                    <th>推荐理由</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for i, stock in enumerate(top_stocks, 1):
            score = stock.get("score", 0)
            score_color = "#22c55e" if score >= 60 else "#eab308" if score >= 40 else "#ef4444"
            
            html += f"""
                <tr>
                    <td style='color: #f1f5f9; font-weight: bold;'>{i}</td>
                    <td style='color: #3b82f6;'>{stock.get('ticker', '—')}</td>
                    <td style='color: #f1f5f9;'>{stock.get('name', '—')}</td>
                    <td>
                        <span style='color: {score_color}; font-weight: bold;'>{score}</span>
                    </td>
                    <td style='color: #cbd5e1;'>{stock.get('reason', '—')}</td>
                </tr>
            """
        
        html += "</tbody></table>"
        return html
    
    def _render_reasons_list(self, reasons: List[str]) -> str:
        """渲染理由列表 HTML"""
        if not reasons:
            return "<p style='color: #64748b;'>暂无数据</p>"
        
        html = "<ul class='reason-list'>"
        for reason in reasons:
            html += f"<li>{reason}</li>"
        html += "</ul>"
        
        return html
    
    def _get_investor_name(self, investor_id: str) -> str:
        """根据 investor_id 获取投资者名称"""
        # 从 INVESTORS 配置中查找
        try:
            from lib.pipeline.score_fns import INVESTORS
            for inv in INVESTORS:
                if inv["id"] == investor_id:
                    return inv["name"]
        except Exception:
            pass
        
        # 返回 ID 作为备选
        return investor_id


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
