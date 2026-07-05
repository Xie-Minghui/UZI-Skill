"""
采集适配器 - v4.0 新增

为新功能提供数据采集入口，但内部**完全复用**现有 Fetcher。

设计原则：
1. 不修改现有 collect.py
2. 对行业/组合分析，循环调用现有 collect() 函数
3. 新增行业级 Fetcher（fetch_industry_overview.py 等）
"""

from typing import Dict, List, Optional
from pathlib import Path
import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加 scripts 目录到 sys.path
# collect_adapter.py 位于 scripts/lib/pipeline/
# 所以 scripts 目录是 Path(__file__).parent.parent.parent
HERE = Path(__file__).parent.parent  # scripts/lib
SCRIPTS_DIR = HERE.parent  # scripts
sys.path.insert(0, str(SCRIPTS_DIR))

# 调试信息
print(f"   [collect_adapter] SCRIPTS_DIR: {SCRIPTS_DIR}")
print(f"   [collect_adapter] Python path: {sys.path[:3]}...")


class DataCollector:
    """
    统一的数据采集入口
    
    使用示例：
    collector = DataCollector(TickerTarget("600519.SH"))
    data = collector.collect()
    
    collector = DataCollector(IndustryTarget("白酒"))
    data = collector.collect()
    """
    
    def __init__(self, target):
        self.target = target
        
    def collect(self) -> Dict:
        """
        根据目标类型调用不同的采集策略
        
        返回格式：
        - 单股：与现有 raw_data.json 格式完全一致
        - 行业：{ "_type": "industry", "stocks": {...}, "industry_overview": {...} }
        - 组合：{ "_type": "portfolio", "holdings": [...], "stocks_data": {...} }
        """
        if self.target.target_type == "ticker":
            return self._collect_single_stock()
        elif self.target.target_type == "industry":
            return self._collect_industry()
        elif self.target.target_type == "portfolio":
            return self._collect_portfolio()
    
    def _collect_single_stock(self) -> Dict:
        """单股采集（复用现有逻辑）"""
        ticker = self.target.ticker
        print(f"   📊 采集单股数据: {ticker}")
        
        # 调用现有的采集函数
        return self._call_legacy_collect(ticker)
    
    def _collect_industry(self) -> Dict:
        """
        行业数据采集 - 复用现有 Fetcher
        
        流程：
        1. 获取行业成分股（TOP N）
        2. 并发采集每只股票的数据（调用现有 collect()）
        3. 采集行业整体数据（新增 Fetcher）
        4. 聚合行业级指标
        """
        industry_name = self.target.name
        top_n = self.target.top_n
        
        print(f"   📊 采集行业数据: {industry_name} (TOP {top_n})")
        
        # 1. 获取行业成分股
        components = self.target.to_legacy_tickers()
        
        if not components:
            print(f"   ⚠️ 行业 '{industry_name}' 无成分股，使用默认股票列表")
            # TODO: 实现真实的行业成分股获取逻辑
            components = ["600519.SH", "000858.SZ", "000568.SZ"]  # 临时：白酒行业示例
        
        # 2. 并发采集成分股数据
        stocks_data = {}
        
        # 复用现有并发逻辑（max_workers=6）
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_ticker = {
                executor.submit(self._call_legacy_collect, ticker): ticker
                for ticker in components
            }
            
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    data = future.result()
                    stocks_data[ticker] = data
                    print(f"   ✅ {ticker} 采集完成")
                except Exception as e:
                    print(f"   ❌ {ticker} 采集失败: {e}")
                    stocks_data[ticker] = None
        
        # 3. 采集行业整体数据（新增）
        industry_overview = self._fetch_industry_overview(industry_name)
        
        # 4. 聚合行业级指标
        aggregated = self._aggregate_industry_data(stocks_data)
        
        return {
            "_type": "industry",
            "_industry_name": industry_name,
            "_top_n": top_n,
            "stocks": stocks_data,
            "industry_overview": industry_overview,
            "aggregated": aggregated
        }
    
    def _collect_portfolio(self) -> Dict:
        """组合数据采集（复用现有逻辑）"""
        holdings = self.target.holdings
        
        print(f"   📊 采集组合数据: {len(holdings)} 只持仓")
        
        # 对每只持仓股票调用现有 collect()
        stocks_data = {}
        for holding in holdings:
            ticker = holding["ticker"]
            print(f"   📊 采集 {ticker}...")
            stocks_data[ticker] = self._call_legacy_collect(ticker)
        
        return {
            "_type": "portfolio",
            "holdings": holdings,
            "stocks_data": stocks_data
        }
    
    def _call_legacy_collect(self, ticker: str) -> Dict:
        """
        调用现有的采集函数
        
        兼容性保证：
        - 完全复用现有 collect() 逻辑
        - 返回格式与 raw_data.json 完全一致
        """
        # 直接使用 legacy collect_raw_data（更稳定）
        try:
            import run_real_test as rrt
            result = rrt.collect_raw_data(ticker)
            print(f"   ✅ 采集完成: {ticker}")
            
            # 确保返回的数据包含 ticker 字段
            if result and isinstance(result, dict):
                if 'ticker' not in result:
                    result['ticker'] = ticker
                return result
            else:
                print(f"   ⚠️  采集返回空数据: {ticker}")
                return {}
        except Exception as e:
            print(f"   ❌ 采集失败 {ticker}: {e}")
            traceback.print_exc()
            return {}
    
    def _fetch_industry_overview(self, industry_name: str) -> Dict:
        """
        采集行业整体数据 - 新增 Fetcher
        
        返回：
        - 行业指数表现
        - 行业 PE/PB 分位
        - 行业增速
        - 政策支持度
        - 机构配置比例
        """
        print(f"   📊 采集行业概览: {industry_name}")
        
        # TODO: 实现真实的行业数据采集
        # 临时返回示例数据
        return {
            "industry_name": industry_name,
            "index_performance": {
                "1d": "+2.5%",
                "1w": "+5.2%",
                "1m": "+12.8%",
                "ytd": "+25.3%"
            },
            "valuation": {
                "pe_percentile": "45%",  # PE 处于历史 45% 分位
                "pb_percentile": "52%",
                "overall": "合理"
            },
            "growth": {
                "revenue_growth": "18.5%",
                "profit_growth": "22.3%",
                "outlook": "加速"
            },
            "policy": {
                "support_level": "高",
                "recent_policies": ["消费刺激政策", "内需扩大政策"]
            }
        }
    
    def _aggregate_industry_data(self, stocks_data: Dict) -> Dict:
        """
        聚合行业数据
        
        计算：
        - 行业平均 PE/PB
        - 成分股评分一致性
        - 行业热度
        """
        valid_data = [v for v in stocks_data.values() if v]
        
        if not valid_data:
            return {}
        
        # 计算平均值
        pe_values = []
        pb_values = []
        
        for data in valid_data:
            basic = data.get("0_basic", {}).get("data", {})
            pe = basic.get("pe")
            pb = basic.get("pb")
            if pe:
                pe_values.append(pe)
            if pb:
                pb_values.append(pb)
        
        return {
            "stock_count": len(valid_data),
            "avg_pe": sum(pe_values) / len(pe_values) if pe_values else None,
            "avg_pb": sum(pb_values) / len(pb_values) if pb_values else None,
            "consensus": "待评分引擎计算"
        }
