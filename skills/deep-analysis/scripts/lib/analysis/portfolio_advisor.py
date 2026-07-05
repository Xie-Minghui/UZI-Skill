"""
组合顾问 - v4.0 新增

功能 3：针对自己的股票组合，给出购买或卖出和仓位建议

使用示例：
    advisor = PortfolioAdvisor()
    result = advisor.analyze_from_file("holdings.csv")
    result = advisor.analyze_from_list([
        {"ticker": "600519.SH", "shares": 100, "avg_cost": 1800},
        {"ticker": "000858.SZ", "shares": 200, "avg_cost": 120}
    ])
"""

from typing import Dict, List, Optional
from pathlib import Path
import json
import sys
import csv

# 添加父目录到 sys.path
HERE = Path(__file__).parent.parent
sys.path.insert(0, str(HERE))

from target.base import PortfolioTarget, create_target
from pipeline.collect_adapter import DataCollector
from pipeline.score_adapter import ScoreEngine


class PortfolioAdvisor:
    """
    组合顾问
    
    核心功能：
    1. analyze(holdings) - 分析组合，给出建议
    2. analyze_from_file(file_path) - 从 CSV 文件分析
    3. analyze_interactive() - 交互式输入
    
    输入格式（CSV）：
    ticker,shares,avg_cost
    600519.SH,100,1800
    000858.SZ,200,120
    
    返回格式：
    {
        "portfolio_health": 72,
        "holdings_analysis": [
            {
                "ticker": "600519.SH",
                "current_shares": 100,
                "current_cost": 1800,
                "current_price": 2100,
                "profit_loss": "+16.7%",
                "suggest": "hold",
                "target_position": "25%",
                "reason": "估值合理，继续持有"
            },
            ...
        ],
        "risks": [...],
        "report_path": "reports/portfolio_20240705/index.html"
    }
    """
    
    def __init__(self):
        self.collector = None
        self.scorer = None
    
    def analyze(self, holdings: List[Dict], 
                 detailed: bool = False) -> Dict:
        """
        分析用户组合，给出建议
        
        参数：
        - holdings: 持仓列表
          [
              {"ticker": "600519.SH", "shares": 100, "avg_cost": 1800},
              ...
          ]
        - detailed: 是否生成详细报告
        
        返回：分析结果
        """
        print(f"\n{'='*60}")
        print(f"💼 分析组合: {len(holdings)} 只持仓")
        print(f"{'='*60}\n")
        
        # 1. 创建 PortfolioTarget
        target = create_target(
            "portfolio", 
            "my_portfolio",
            holdings=holdings
        )
        
        # 2. 数据采集
        print(f"步骤 1/4: 数据采集...")
        self.collector = DataCollector(target)
        data = self.collector.collect()
        
        # 3. 评分
        print(f"\n步骤 2/4: 评分...")
        self.scorer = ScoreEngine(target)
        scores = self.scorer.score(data)
        
        # 4. 生成买入/卖出建议
        print(f"\n步骤 3/4: 生成建议...")
        advice = self._generate_advice(holdings, data, scores)
        
        # 5. 生成报告（如果需要）
        report_path = None
        if detailed:
            print(f"\n步骤 4/4: 生成报告...")
            report_path = self._generate_report(holdings, advice)
            advice["report_path"] = report_path
        
        print(f"\n{'='*60}")
        print(f"✅ 分析完成")
        print(f"   组合健康度: {advice['portfolio_health']}")
        print(f"   建议操作: 买入 {advice['buy_count']} / 卖出 {advice['sell_count']} / 持有 {advice['hold_count']}")
        print(f"{'='*60}\n")
        
        return advice
    
    def analyze_from_file(self, file_path: str) -> Dict:
        """
        从 CSV 文件分析组合
        
        使用示例：
        advisor = PortfolioAdvisor()
        result = advisor.analyze_from_file("holdings.csv")
        """
        print(f"📂 读取文件: {file_path}")
        
        holdings = self._parse_csv(file_path)
        
        if not holdings:
            print(f"❌ 文件为空或格式错误")
            return {}
        
        return self.analyze(holdings, detailed=True)
    
    def analyze_interactive(self) -> Dict:
        """
        交互式输入持仓
        
        使用示例：
        advisor = PortfolioAdvisor()
        result = advisor.analyze_interactive()
        """
        print(f"\n{'='*60}")
        print(f"💼 交互式输入持仓")
        print(f"{'='*60}\n")
        
        holdings = []
        
        print("请输入持仓信息（输入空行结束）:")
        
        while True:
            print(f"\n持仓 #{len(holdings) + 1}:")
            
            ticker = input("  股票代码 (如 600519.SH): ").strip()
            if not ticker:
                break
            
            try:
                shares = int(input("  持股数量: ").strip())
                avg_cost = float(input("  平均成本: ").strip())
            except ValueError:
                print("  ❌ 输入错误，跳过")
                continue
            
            holdings.append({
                "ticker": ticker,
                "shares": shares,
                "avg_cost": avg_cost
            })
            
            more = input("\n  继续添加? (y/n): ").strip().lower()
            if more != 'y':
                break
        
        if not holdings:
            print(f"\n❌ 未输入持仓")
            return {}
        
        print(f"\n✅ 已输入 {len(holdings)} 只持仓")
        
        return self.analyze(holdings, detailed=True)
    
    def _parse_csv(self, file_path: str) -> List[Dict]:
        """
        解析 CSV 文件
        
        支持格式：
        1. 标准格式 (ticker,shares,avg_cost)
        2. 中文格式 (股票代码,持股数量,平均成本)
        3. 无表头格式（自动检测）
        """
        holdings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                # 读取第一行，判断是否有表头
                first_row = next(reader, None)
                
                if first_row is None:
                    return []
                
                # 判断是否有表头
                if self._is_header(first_row):
                    # 有表头：读取剩余行
                    for row in reader:
                        holding = self._parse_row(row, first_row)
                        if holding:
                            holdings.append(holding)
                else:
                    # 无表头：第一行也是数据
                    holding = self._parse_row(first_row, None)
                    if holding:
                        holdings.append(holding)
                    
                    for row in reader:
                        holding = self._parse_row(row, None)
                        if holding:
                            holdings.append(holding)
        
        except FileNotFoundError:
            print(f"  ❌ 文件不存在: {file_path}")
            return []
        except Exception as e:
            print(f"  ❌ 解析失败: {e}")
            return []
        
        return holdings
    
    def _is_header(self, row: List[str]) -> bool:
        """判断是否为表头"""
        header_keywords = ['ticker', '股票', '代码', 'shares', '持股', '数量', 'avg_cost', '平均', '成本']
        
        row_lower = [cell.lower() for cell in row]
        
        for keyword in header_keywords:
            for cell in row_lower:
                if keyword in cell:
                    return True
        
        return False
    
    def _parse_row(self, row: List[str], headers: Optional[List[str]]) -> Dict:
        """解析单行数据"""
        try:
            # 自动检测字段位置
            if headers:
                # 有表头：按表头解析
                ticker_idx = next(i for i, h in enumerate(headers) if 'ticker' in h.lower() or '代码' in h)
                shares_idx = next(i for i, h in enumerate(headers) if 'shares' in h.lower() or '数量' in h)
                cost_idx = next(i for i, h in enumerate(headers) if 'cost' in h.lower() or '成本' in h)
            else:
                # 无表头：假设顺序为 ticker, shares, avg_cost
                ticker_idx = 0
                shares_idx = 1
                cost_idx = 2
            
            ticker = row[ticker_idx].strip()
            shares = int(row[shares_idx].strip())
            avg_cost = float(row[cost_idx].strip())
            
            return {
                "ticker": ticker,
                "shares": shares,
                "avg_cost": avg_cost
            }
        
        except (IndexError, ValueError) as e:
            print(f"  ⚠️ 跳过无效行: {row} ({e})")
            return None
    
    def _generate_advice(self, holdings: List[Dict], 
                          data: Dict, scores: Dict) -> Dict:
        """
        生成买入/卖出建议
        
        分析维度：
        1. 当前价 vs 成本价 → 盈亏
        2. 综合评分 → 未来预期
        3. 持仓比例 → 仓位合理性
        4. 行业分布 → 分散度
        """
        holdings_data = data.get("stocks_data", {})
        holdings_scores = scores.get("holdings_scores", {})
        portfolio_score = scores.get("portfolio_score", {})
        
        holdings_analysis = []
        buy_count = 0
        sell_count = 0
        hold_count = 0
        
        for holding in holdings:
            ticker = holding["ticker"]
            shares = holding["shares"]
            avg_cost = holding["avg_cost"]
            
            # 获取当前价和评分
            current_price = self._get_current_price(ticker, holdings_data)
            score = holdings_scores.get(ticker, {})
            
            # 计算盈亏
            profit_loss_pct = self._calculate_profit_loss(current_price, avg_cost)
            
            # 生成建议
            suggest = self._suggest_action(ticker, holding, score, current_price)
            
            # 目标仓位
            target_position = self._calculate_target_position(ticker, score)
            
            # 理由
            reason = self._generate_reason(ticker, holding, score, suggest)
            
            holdings_analysis.append({
                "ticker": ticker,
                "name": self._get_stock_name(ticker, holdings_data),
                "current_shares": shares,
                "current_cost": avg_cost,
                "current_price": current_price,
                "profit_loss": profit_loss_pct,
                "score": score.get("panel", {}).get("overall_score", 0),
                "suggest": suggest,
                "target_position": target_position,
                "reason": reason
            })
            
            # 统计
            if suggest == "buy":
                buy_count += 1
            elif suggest == "sell":
                sell_count += 1
            else:
                hold_count += 1
        
        # 组合健康度
        portfolio_health = portfolio_score.get("health_score", 0)
        
        # 风险提示
        risks = self._extract_risks(holdings_analysis)
        
        return {
            "portfolio_health": portfolio_health,
            "holdings_analysis": holdings_analysis,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "hold_count": hold_count,
            "risks": risks
        }
    
    def _get_current_price(self, ticker: str, holdings_data: Dict) -> Optional[float]:
        """获取当前价"""
        stock_data = holdings_data.get(ticker, {})
        
        if not stock_data:
            return None
        
        basic = stock_data.get("0_basic", {}).get("data", {})
        current_price = basic.get("price")
        
        return current_price
    
    def _get_stock_name(self, ticker: str, holdings_data: Dict) -> str:
        """获取股票名称"""
        stock_data = holdings_data.get(ticker, {})
        
        if not stock_data:
            return ticker
        
        basic = stock_data.get("0_basic", {}).get("data", {})
        name = basic.get("name")
        
        return name if name else ticker
    
    def _calculate_profit_loss(self, current_price: Optional[float], 
                                avg_cost: float) -> str:
        """计算盈亏百分比"""
        if not current_price:
            return "N/A"
        
        pct = (current_price - avg_cost) / avg_cost * 100
        
        if pct >= 0:
            return f"+{pct:.1f}%"
        else:
            return f"{pct:.1f}%"
    
    def _suggest_action(self, ticker: str, holding: Dict, 
                        score: Dict, current_price: Optional[float]) -> str:
        """
        生成操作建议
        
        逻辑：
        - 评分 >= 80 + 盈利 → hold
        - 评分 >= 80 + 亏损 → buy (加仓)
        - 评分 < 50 → sell
        - 50 <= 评分 < 80 → hold
        """
        overall_score = score.get("panel", {}).get("overall_score", 0)
        
        if current_price and avg_cost in holding:
            profit_loss = (current_price - holding["avg_cost"]) / holding["avg_cost"]
        else:
            profit_loss = 0
        
        # 建议逻辑
        if overall_score >= 80:
            if profit_loss > 0.2:  # 盈利 > 20%
                return "hold"  # 止盈
            else:
                return "buy"  # 加仓
        elif overall_score < 50:
            if profit_loss > 0:  # 盈利
                return "sell"  # 止盈
            else:
                return "sell"  # 止损
        else:
            return "hold"  # 观望
    
    def _calculate_target_position(self, ticker: str, score: Dict) -> str:
        """计算目标仓位"""
        overall_score = score.get("panel", {}).get("overall_score", 0)
        
        # 简单逻辑：评分越高，仓位越重
        if overall_score >= 80:
            return "30-40%"
        elif overall_score >= 65:
            return "20-30%"
        elif overall_score >= 50:
            return "10-20%"
        else:
            return "0% (清仓)"
    
    def _generate_reason(self, ticker: str, holding: Dict, 
                         score: Dict, suggest: str) -> str:
        """生成建议理由"""
        panel = score.get("panel", {})
        overall_score = panel.get("overall_score", 0)
        
        reasons = []
        
        # 基于评分
        if overall_score >= 80:
            reasons.append("综合评分高")
        elif overall_score < 50:
            reasons.append("综合评分低")
        
        # 基于评委共识
        consensus = panel.get("consensus", "")
        if consensus:
            reasons.append(f"评委共识: {consensus}")
        
        # 基于操作建议
        if suggest == "buy":
            reasons.append("建议加仓")
        elif suggest == "sell":
            reasons.append("建议减仓")
        
        return "；".join(reasons) if reasons else "综合评估"
    
    def _extract_risks(self, holdings_analysis: List[Dict]) -> List[str]:
        """提取组合风险"""
        risks = []
        
        # 检查集中度风险
        if len(holdings_analysis) > 0:
            # TODO: 计算持仓集中度
            risks.append("持仓集中度风险")
        
        # 检查行业分布
        # TODO: 分析行业分布
        risks.append("行业分布风险")
        
        return risks
    
    def _generate_report(self, holdings: List[Dict], 
                         advice: Dict) -> str:
        """生成组合诊断报告"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report_dir = Path(f"reports/portfolio_{timestamp}")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / "index.html"
        
        # 临时：生成简单 HTML
        html_content = f"""
        <html>
        <head><title>组合诊断报告</title></head>
        <body>
            <h1>组合诊断报告</h1>
            <h2>组合健康度: {advice['portfolio_health']}</h2>
            <h3>持仓分析:</h3>
            <table border="1">
                <tr>
                    <th>股票</th>
                    <th>评分</th>
                    <th>建议</th>
                    <th>理由</th>
                </tr>
        """
        
        for item in advice["holdings_analysis"]:
            html_content += f"""
                <tr>
                    <td>{item['name']} ({item['ticker']})</td>
                    <td>{item['score']}</td>
                    <td>{item['suggest']}</td>
                    <td>{item['reason']}</td>
                </tr>
            """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        report_path.write_text(html_content, encoding="utf-8")
        
        return str(report_path)


def analyze_portfolio(file_path: str) -> Dict:
    """
    快捷函数：分析组合
    
    使用示例：
    from lib.analysis.portfolio_advisor import analyze_portfolio
    result = analyze_portfolio("holdings.csv")
    """
    advisor = PortfolioAdvisor()
    return advisor.analyze_from_file(file_path)


def analyze_portfolio_interactive() -> Dict:
    """
    快捷函数：交互式分析组合
    
    使用示例：
    from lib.analysis.portfolio_advisor import analyze_portfolio_interactive
    result = analyze_portfolio_interactive()
    """
    advisor = PortfolioAdvisor()
    return advisor.analyze_interactive()


if __name__ == "__main__":
    # 测试代码
    print("测试组合顾问...")
    
    advisor = PortfolioAdvisor()
    
    # 测试从文件分析
    # result = advisor.analyze_from_file("holdings.csv")
    # print(f"\n分析结果: 组合健康度 {result['portfolio_health']}")
    
    # 测试交互式
    # result = advisor.analyze_interactive()
    
    print("\n测试完成")
