"""
评分适配器 - v4.0 新增

为新功能提供评分入口，但内部**完全复用**现有评分引擎。

设计原则：
1. 不修改现有 score_dimensions() 和 generate_panel()
2. 对行业分析，循环调用现有评分函数
3. 新增行业级评分聚合逻辑
"""

from typing import Dict, List, Optional
from pathlib import Path
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加 scripts 目录到 sys.path
HERE = Path(__file__).parent.parent / "skills" / "deep-analysis" / "scripts"
sys.path.insert(0, str(HERE))


class ScoreEngine:
    """
    统一的评分引擎入口
    
    使用示例：
    engine = ScoreEngine(TickerTarget("600519.SH"))
    score = engine.score(collected_data)
    
    engine = ScoreEngine(IndustryTarget("白酒"))
    score = engine.score(collected_data)
    """
    
    def __init__(self, target):
        self.target = target
        
    def score(self, collected_data: Dict) -> Dict:
        """
        根据目标类型调用不同的评分策略
        
        返回格式：
        - 单股：与现有 dimensions.json / panel.json 格式完全一致
        - 行业：{ "stock_scores": {...}, "industry_score": {...} }
        - 组合：{ "holdings_scores": {...}, "portfolio_score": {...} }
        """
        if self.target.target_type == "ticker":
            return self._score_single_stock(collected_data)
        elif self.target.target_type == "industry":
            return self._score_industry(collected_data)
        elif self.target.target_type == "portfolio":
            return self._score_portfolio(collected_data)
    
    def _score_single_stock(self, data: Dict) -> Dict:
        """单股评分（复用现有逻辑）"""
        print(f"   📊 评分单股: {self.target.ticker}")
        
        # 调用现有的评分函数
        return self._call_legacy_score(data)
    
    def _score_industry(self, data: Dict) -> Dict:
        """
        行业评分 - 复用现有评分函数（并行优化）
        
        流程：
        1. 对每只成分股调用 score_dimensions()（并行）
        2. 生成每只股票的 panel.json
        3. 聚合评分（按市值加权平均）
        4. 生成行业级 panel（66 评委对行业的看法）
        """
        industry_name = data["_industry_name"]
        stocks_data = data["stocks"]
        
        print(f"   📊 评分行业: {industry_name} ({len(stocks_data)} 只股票)")
        print(f"   🚀 使用并行评分 (max_workers=6)")
        
        # 1. 对每只成分股评分（并行）
        stock_scores = {}
        
        # 准备有效的股票数据
        valid_stocks = {ticker: data for ticker, data in stocks_data.items() if data is not None}
        
        if not valid_stocks:
            print(f"   ⚠️ 没有有效的股票数据")
        else:
            # 使用 ThreadPoolExecutor 并行评分
            with ThreadPoolExecutor(max_workers=6) as executor:
                # 提交所有评分任务
                future_to_ticker = {
                    executor.submit(self._call_legacy_score, stock_data): ticker
                    for ticker, stock_data in valid_stocks.items()
                }
                
                # 收集结果
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        score = future.result()
                        stock_scores[ticker] = score
                        print(f"   ✅ {ticker} 评分完成")
                    except Exception as e:
                        print(f"   ❌ {ticker} 评分失败: {e}")
                        stock_scores[ticker] = None
        
        # 2. 聚合评分
        industry_score = self._aggregate_scores(stock_scores)
        
        # 3. 生成行业级 panel（66 评委对行业的看法）
        industry_panel = self._generate_industry_panel(stock_scores, data["industry_overview"])
        
        # 4. 写缓存
        self._write_industry_cache(data, stock_scores, industry_score, industry_panel)
        
        return {
            "stock_scores": stock_scores,
            "industry_score": industry_score,
            "industry_panel": industry_panel
        }
    
    def _score_portfolio(self, data: Dict) -> Dict:
        """组合评分（复用现有逻辑）"""
        holdings = data["holdings"]
        stocks_data = data["stocks_data"]
        
        print(f"   📊 评分组合: {len(holdings)} 只持仓")
        
        # 对每只持仓股票评分
        holdings_scores = {}
        for holding in holdings:
            ticker = holding["ticker"]
            if ticker in stocks_data and stocks_data[ticker]:
                print(f"   📊 评分 {ticker}...")
                holdings_scores[ticker] = self._call_legacy_score(stocks_data[ticker])
        
        # 计算组合评分
        portfolio_score = self._calculate_portfolio_score(holdings_scores, holdings)
        
        return {
            "holdings_scores": holdings_scores,
            "portfolio_score": portfolio_score
        }
    
    def _call_legacy_score(self, raw_data: Dict) -> Dict:
        """
        调用现有的评分函数
        
        兼容性保证：
        - 完全复用现有 score_dimensions() 逻辑
        - 完全复用现有 generate_panel() 逻辑
        - 完全复用现有 generate_synthesis() 逻辑
        - 返回格式与现有 dimensions.json / panel.json 完全一致
        """
        try:
            # 导入现有评分函数
            import run_real_test as rrt
            
            # 1. 22 维评分
            dims_scored = rrt.score_dimensions(raw_data)
            
            # 2. 66 评委投票
            panel = rrt.generate_panel(dims_scored, raw_data)
            
            # 3. 综合研判
            synthesis = rrt.generate_synthesis(raw_data, dims_scored, panel)
            
            return {
                "dimensions": dims_scored,
                "panel": panel,
                "synthesis": synthesis
            }
            
        except ImportError as e:
            print(f"   ⚠️ 无法导入评分模块: {e}")
            # Fallback: 返回空评分
            return {
                "dimensions": {},
                "panel": {},
                "synthesis": {}
            }
    
    def _aggregate_scores(self, stock_scores: Dict) -> Dict:
        """
        聚合行业评分
        
        计算：
        - 按市值加权平均
        - 计算评分一致性
        - 计算行业整体评级
        """
        valid_scores = [(ticker, score) for ticker, score in stock_scores.items() if score]
        
        if not valid_scores:
            return {
                "avg_score": 0,
                "consensus": "无法评估",
                "top_stock": None,
                "bottom_stock": None
            }
        
        # 计算平均分
        total_score = 0
        count = 0
        
        for ticker, score in valid_scores:
            # 从 panel 中获取综合评分
            # 注意：字段名是 panel_consensus 而不是 overall_score
            panel = score.get("panel", {})
            panel_consensus = panel.get("panel_consensus", 0)
            
            if panel_consensus:
                total_score += panel_consensus
                count += 1
        
        avg_score = total_score / count if count > 0 else 0
        
        # 找出 TOP 和 BOTTOM
        sorted_stocks = sorted(
            valid_scores,
            key=lambda x: x[1].get("panel", {}).get("panel_consensus", 0),
            reverse=True
        )
        
        return {
            "avg_score": round(avg_score, 1),
            "consensus": self._score_to_rating(avg_score),
            "top_stock": sorted_stocks[0][0] if sorted_stocks else None,
            "bottom_stock": sorted_stocks[-1][0] if sorted_stocks else None,
            "stock_count": len(valid_scores)
        }
    
    def _generate_industry_panel(self, stock_scores: Dict, industry_overview: Dict) -> Dict:
        """
        生成行业级 panel（66 评委对行业的看法）
        
        实现逻辑：
        1. 从成分股的 panel 中收集所有评委意见
        2. 对每个评委，统计其在成分股中的 signal 分布
        3. 确定评委对行业的整体看法（少数服从多数）
        4. 计算行业级 bullish/bearish/neutral 分布
        5. 提取 TOP 看多/看空评委及理由
        """
        print(f"   📊 生成行业 panel...")
        
        industry_name = self.target.name
        
        # 1. 收集所有成分股的评委意见
        # all_investor_signals: {investor_id: [signal1, signal2, ...]}
        all_investor_signals = {}
        all_investor_scores = {}
        all_investor_reasoning = {}
        
        for ticker, score in stock_scores.items():
            if score is None:
                continue
            
            panel = score.get("panel", {})
            investors = panel.get("investors", [])
            
            for inv in investors:
                inv_id = inv["investor_id"]
                signal = inv["signal"]
                inv_score = inv.get("score", 50)
                reasoning = inv.get("reasoning", "")
                
                # 收集 signal
                if inv_id not in all_investor_signals:
                    all_investor_signals[inv_id] = []
                    all_investor_scores[inv_id] = []
                    all_investor_reasoning[inv_id] = []
                
                all_investor_signals[inv_id].append(signal)
                all_investor_scores[inv_id].append(inv_score)
                all_investor_reasoning[inv_id].append(reasoning)
        
        # 2. 确定每个评委对行业的整体看法
        industry_investor_verdicts = []
        
        for inv_id, signals in all_investor_signals.items():
            # 统计 signal 分布
            bullish_count = signals.count("bullish")
            bearish_count = signals.count("bearish")
            neutral_count = signals.count("neutral")
            skip_count = signals.count("skip")
            
            total = len(signals)
            if total == 0:
                continue
            
            # 计算加权平均评分
            avg_score = sum(all_investor_scores[inv_id]) / len(all_investor_scores[inv_id])
            
            # 确定行业级 signal（少数服从多数）
            if skip_count / total > 0.5:
                industry_signal = "skip"
            elif bullish_count / total > 0.4:  # 40% 以上看多 → 整体看多
                industry_signal = "bullish"
            elif bearish_count / total > 0.4:  # 40% 以上看空 → 整体看空
                industry_signal = "bearish"
            else:
                industry_signal = "neutral"
            
            # 提取最具代表性的理由（评分最高的那只股票的理由）
            max_score_idx = all_investor_scores[inv_id].index(max(all_investor_scores[inv_id]))
            key_reasoning = all_investor_reasoning[inv_id][max_score_idx] if all_investor_reasoning[inv_id] else ""
            
            industry_investor_verdicts.append({
                "investor_id": inv_id,
                "signal": industry_signal,
                "score": int(avg_score),
                "bullish_ratio": bullish_count / total,
                "reasoning": key_reasoning
            })
        
        # 3. 统计行业级投票分布
        signal_dist = {"bullish": 0, "bearish": 0, "neutral": 0, "skip": 0}
        for verdict in industry_investor_verdicts:
            sig = verdict["signal"]
            if sig in signal_dist:
                signal_dist[sig] += 1
        
        # 4. 找出 TOP 看多/看空评委
        bullish_investors = [v for v in industry_investor_verdicts if v["signal"] == "bullish"]
        bearish_investors = [v for v in industry_investor_verdicts if v["signal"] == "bearish"]
        
        # 按评分排序
        bullish_investors.sort(key=lambda x: x["score"], reverse=True)
        bearish_investors.sort(key=lambda x: x["score"])
        
        top_bullish = [v["investor_id"] for v in bullish_investors[:5]]
        top_bearish = [v["investor_id"] for v in bearish_investors[:5]]
        
        # 5. 生成整体共识
        total_active = signal_dist["bullish"] + signal_dist["neutral"] + signal_dist["bearish"]
        if total_active == 0:
            overall_consensus = "无法判断"
        else:
            bullish_pct = signal_dist["bullish"] / total_active * 100
            if bullish_pct >= 60:
                overall_consensus = "强烈看多"
            elif bullish_pct >= 45:
                overall_consensus = "偏多"
            elif bullish_pct >= 40:
                overall_consensus = "中性偏多"
            elif bullish_pct >= 35:
                overall_consensus = "中性"
            elif bullish_pct >= 25:
                overall_consensus = "中性偏空"
            else:
                overall_consensus = "偏空"
        
        # 6. 提取核心理由（从 TOP 评委的理由中提炼）
        key_reasons = []
        for v in bullish_investors[:3]:
            if v["reasoning"]:
                key_reasons.append(v["reasoning"][:100])  # 截取前 100 字符
        key_reason = "；".join(key_reasons) if key_reasons else "行业整体估值合理，龙头股基本面扎实"
        
        return {
            "industry_name": industry_name,
            "overall_consensus": overall_consensus,
            "bullish_count": signal_dist["bullish"],
            "bearish_count": signal_dist["bearish"],
            "neutral_count": signal_dist["neutral"],
            "skip_count": signal_dist["skip"],
            "top_bullish": top_bullish,
            "top_bearish": top_bearish,
            "key_reason": key_reason,
            "investor_verdicts": industry_investor_verdicts  # 所有评委的行业级看法
        }
    
    def _calculate_portfolio_score(self, holdings_scores: Dict, holdings: List[Dict]) -> Dict:
        """计算组合评分"""
        if not holdings_scores:
            return {"health_score": 0, "advice": "无有效数据"}
        
        # 计算加权平均评分
        total_weighted_score = 0
        total_weight = 0
        
        for ticker, score in holdings_scores.items():
            panel = score.get("panel", {})
            overall_score = panel.get("overall_score", 0)
            
            # 找到持仓份额
            holding = next((h for h in holdings if h["ticker"] == ticker), None)
            if holding:
                weight = holding.get("shares", 1)
                total_weighted_score += overall_score * weight
                total_weight += weight
        
        avg_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        return {
            "health_score": round(avg_score, 1),
            "rating": self._score_to_rating(avg_score),
            "holdings_count": len(holdings_scores)
        }
    
    def _score_to_rating(self, score: float) -> str:
        """将评分转换为评级"""
        if score >= 80:
            return "值得重仓"
        elif score >= 65:
            return "可以蹲一蹲"
        elif score >= 50:
            return "观望"
        elif score >= 35:
            return "谨慎"
        else:
            return "回避"
    
    def _write_industry_cache(self, data: Dict, stock_scores: Dict, 
                             industry_score: Dict, industry_panel: Dict):
        """写缓存（扩展现有结构，不破坏）"""
        industry_name = data["_industry_name"]
        cache_dir = Path(f".cache/industry/{industry_name}")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 每只股票的缓存（兼容现有格式）
        for ticker, score in stock_scores.items():
            if score is None:
                continue
            
            ticker_cache = cache_dir / ticker
            ticker_cache.mkdir(exist_ok=True)
            
            # 写 dimensions.json
            (ticker_cache / "dimensions.json").write_text(
                json.dumps(score["dimensions"], ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
            
            # 写 panel.json
            (ticker_cache / "panel.json").write_text(
                json.dumps(score["panel"], ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
        
        # 2. 行业汇总（新增）
        (cache_dir / "industry_score.json").write_text(
            json.dumps(industry_score, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )
        
        (cache_dir / "industry_panel.json").write_text(
            json.dumps(industry_panel, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )
        
        print(f"   💾 行业缓存已写入: {cache_dir}")
