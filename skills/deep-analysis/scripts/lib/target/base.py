"""
Target 抽象层 - v4.0 新增

定义分析目标的抽象基类，支持：
- TickerTarget: 单只股票（向后兼容）
- IndustryTarget: 行业分析
- PortfolioTarget: 组合分析
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class AnalysisTarget(ABC):
    """
    分析目标抽象基类
    
    所有分析目标必须实现：
    1. _get_target_type() - 返回目标类型（子类实现）
    2. to_legacy_tickers() - 转换为现有代码可处理的 ticker 列表
    3. get_cache_key() - 生成缓存路径
    """
    name: str
    
    @abstractmethod
    def _get_target_type(self) -> str:
        """返回目标类型（子类必须实现）"""
        pass
    
    @property
    def target_type(self) -> str:
        """目标类型（自动获取）"""
        return self._get_target_type()
    
    @abstractmethod
    def to_legacy_tickers(self) -> List[str]:
        """
        转换为现有代码可处理的 ticker 列表
        
        用途：
        - 对 TickerTarget：返回 [ticker]
        - 对 IndustryTarget：返回行业 TOP N 成分股
        - 对 PortfolioTarget：返回持仓股票列表
        """
        pass
    
    @abstractmethod
    def get_cache_key(self) -> str:
        """
        生成缓存路径 key
        
        用途：
        - 确保缓存文件不会冲突
        - 复用现有 .cache/ 结构
        """
        pass
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            "target_type": self.target_type,
            "name": self.name,
            "cache_key": self.get_cache_key()
        }


@dataclass
class TickerTarget(AnalysisTarget):
    """
    单只股票目标 - 向后兼容现有逻辑
    
    使用示例：
    target = TickerTarget(name="600519.SH")
    tickers = target.to_legacy_tickers()  # ["600519.SH"]
    """
    ticker: str = ""
    market: str = ""  # A/HK/US
    
    def _get_target_type(self) -> str:
        """返回目标类型"""
        return "ticker"
    
    def __post_init__(self):
        # 如果 ticker 为空，用 name 填充
        if not self.ticker:
            self.ticker = self.name
        
        # 自动检测市场
        if not self.market:
            self.market = self._detect_market()
    
    def _detect_market(self) -> str:
        """自动检测市场"""
        ticker = self.ticker.upper()
        if ".SH" in ticker or ".SZ" in ticker:
            return "A"
        elif ".HK" in ticker or "HK" in ticker:
            return "HK"
        else:
            return "US"
    
    def to_legacy_tickers(self) -> List[str]:
        """返回单只股票列表"""
        return [self.ticker]
    
    def get_cache_key(self) -> str:
        """复用现有缓存结构 .cache/600519.SH/"""
        return self.ticker


@dataclass
class IndustryTarget(AnalysisTarget):
    """
    行业分析目标 - v4.0 新增
    
    使用示例：
    target = IndustryTarget(name="白酒", top_n=10)
    tickers = target.to_legacy_tickers()  # ["600519.SH", "000858.SZ", ...]
    """
    top_n: int = 10  # 分析的龙头股数量
    selection_criteria: str = "market_cap"  # market_cap / liquidity / growth
    industry_code: Optional[str] = None  # 行业代码（可选）
    
    def _get_target_type(self) -> str:
        """返回目标类型"""
        return "industry"
    
    def to_legacy_tickers(self) -> List[str]:
        """
        获取行业成分股（TOP N）
        
        实现逻辑：
        1. 调用 akshare 获取行业成分股
        2. 按 selection_criteria 排序
        3. 返回 TOP N
        """
        stocks = self._fetch_industry_stocks()
        return self._select_top_stocks(stocks, self.top_n)
    
    def _fetch_industry_stocks(self) -> List[Dict]:
        """
        从 akshare 获取行业成分股
        
        实现逻辑：
        1. 调用 akshare.stock_board_industry_name_em() 获取行业列表
        2. 根据行业名称匹配行业代码
        3. 调用 akshare.stock_board_industry_cons_em() 获取成分股
        4. 如果 akshare 调用失败，使用示例数据兜底
        """
        print(f"   📊 获取行业 '{self.name}' 的成分股...")
        
        # 优先使用示例数据（避免网络问题）
        # 如果需要真实数据，可以设置环境变量 UZI_REAL_INDUSTRY_DATA=1
        use_real_data = os.environ.get("UZI_REAL_INDUSTRY_DATA") == "1"
        
        if not use_real_data:
            print(f"   ℹ️  使用示例数据（设置 UZI_REAL_INDUSTRY_DATA=1 启用真实数据）")
            return self._get_example_stocks()
        
        # 尝试获取真实数据
        try:
            import akshare as ak
            
            # 设置超时
            import socket
            socket.setdefaulttimeout(10)
            
            # 方法 1: 使用东方财富行业板块 API
            try:
                # 获取行业板块列表
                industry_df = ak.stock_board_industry_name_em()
                
                # 匹配行业名称（支持模糊匹配）
                matched = industry_df[industry_df['板块名称'].str.contains(self.name, na=False)]
                
                if not matched.empty:
                    # 获取行业代码
                    industry_code = matched.iloc[0]['板块代码']
                    industry_name = matched.iloc[0]['板块名称']
                    print(f"   ✅ 找到行业: {industry_name} (代码: {industry_code})")
                    
                    # 获取该行业的成分股
                    stocks_df = ak.stock_board_industry_cons_em(symbol=industry_code)
                    
                    # 转换为标准格式
                    stocks = []
                    for _, row in stocks_df.iterrows():
                        stocks.append({
                            "ticker": row['代码'],
                            "name": row['名称'],
                            "market_cap": row.get('总市值', 0)
                        })
                    
                    print(f"   ✅ 找到 {len(stocks)} 只股票")
                    return stocks
                else:
                    print(f"   ⚠️  未找到行业 '{self.name}'，尝试概念板块...")
            except Exception as e:
                print(f"   ⚠️  行业板块 API 失败: {e}")
            
            # 方法 2: 使用概念板块 API
            try:
                # 获取概念板块列表
                concept_df = ak.stock_board_concept_name_em()
                
                # 匹配概念名称
                matched = concept_df[concept_df['板块名称'].str.contains(self.name, na=False)]
                
                if not matched.empty:
                    concept_id = matched.iloc[0]['板块代码']
                    concept_name = matched.iloc[0]['板块名称']
                    print(f"   ✅ 找到概念板块: {concept_name} (ID: {concept_id})")
                    
                    # 获取成分股
                    stocks_df = ak.stock_board_concept_cons_em(symbol=concept_id)
                    
                    # 转换为标准格式
                    stocks = []
                    for _, row in stocks_df.iterrows():
                        stocks.append({
                            "ticker": row['代码'],
                            "name": row['名称'],
                            "market_cap": row.get('总市值', 0)
                        })
                    
                    print(f"   ✅ 找到 {len(stocks)} 只股票")
                    return stocks
                else:
                    print(f"   ⚠️  未找到概念板块 '{self.name}'")
            except Exception as e:
                print(f"   ⚠️  概念板块 API 失败: {e}")
            
            # 如果所有 API 都失败，使用示例数据兜底
            print(f"   ⚠️  akshare API 调用失败，使用示例数据兜底")
            
        except ImportError:
            print(f"   ⚠️  akshare 未安装，使用示例数据兜底")
        
        # 兜底方案：使用示例数据
        return self._get_example_stocks()
    
    def _get_example_stocks(self) -> List[Dict]:
        """获取示例数据（兜底方案）"""
        example_stocks = {
            "白酒": [
                {"ticker": "600519.SH", "name": "贵州茅台", "market_cap": 2000000000000},
                {"ticker": "000858.SZ", "name": "五粮液", "market_cap": 500000000000},
                {"ticker": "000568.SZ", "name": "泸州老窖", "market_cap": 300000000000},
                {"ticker": "603369.SH", "name": "今世缘", "market_cap": 100000000000},
                {"ticker": "000799.SZ", "name": "酒鬼酒", "market_cap": 50000000000}
            ],
            "新能源": [
                {"ticker": "300750.SZ", "name": "宁德时代", "market_cap": 1000000000000},
                {"ticker": "002594.SZ", "name": "比亚迪", "market_cap": 800000000000},
                {"ticker": "688981.SH", "name": "中芯国际", "market_cap": 500000000000},
                {"ticker": "601012.SH", "name": "隆基绿能", "market_cap": 300000000000},
                {"ticker": "300274.SZ", "name": "阳光电源", "market_cap": 200000000000}
            ],
            "医药": [
                {"ticker": "600276.SH", "name": "恒瑞医药", "market_cap": 400000000000},
                {"ticker": "000661.SZ", "name": "长春高新", "market_cap": 200000000000},
                {"ticker": "300760.SZ", "name": "迈瑞医疗", "market_cap": 500000000000},
                {"ticker": "688180.SH", "name": "君实生物", "market_cap": 100000000000},
                {"ticker": "002007.SZ", "name": "华兰生物", "market_cap": 80000000000}
            ],
            "半导体": [
                {"ticker": "688981.SH", "name": "中芯国际", "market_cap": 500000000000},
                {"ticker": "603501.SH", "name": "韦尔股份", "market_cap": 200000000000},
                {"ticker": "688008.SH", "name": "澜起科技", "market_cap": 150000000000},
                {"ticker": "002049.SZ", "name": "紫光国微", "market_cap": 120000000000},
                {"ticker": "688012.SH", "name": "中微公司", "market_cap": 100000000000}
            ]
        }
        
        # 返回示例数据（如果行业在列表中）
        if self.name in example_stocks:
            print(f"   ✅ 找到 {len(example_stocks[self.name])} 只示例股票")
            return example_stocks[self.name]
        else:
            print(f"   ⚠️ 行业 '{self.name}' 暂无数据，返回空列表")
            return []
    
    def _select_top_stocks(self, stocks: List[Dict], n: int) -> List[str]:
        """
        按 selection_criteria 选择 TOP N 股票
        
        排序标准：
        - market_cap: 按市值排序（默认）
        - liquidity: 按流动性排序（成交量）
        - growth: 按增速排序
        """
        if not stocks:
            return []
        
        # 根据 selection_criteria 排序
        if self.selection_criteria == "market_cap":
            # 按市值排序
            sorted_stocks = sorted(
                stocks,
                key=lambda x: x.get("market_cap", 0),
                reverse=True
            )
        elif self.selection_criteria == "liquidity":
            # 按流动性排序（ TODO: 需要实现）
            sorted_stocks = stocks
        elif self.selection_criteria == "growth":
            # 按增速排序（ TODO: 需要实现）
            sorted_stocks = stocks
        else:
            # 默认按市值排序
            sorted_stocks = sorted(
                stocks,
                key=lambda x: x.get("market_cap", 0),
                reverse=True
            )
        
        # 返回 TOP N 的 ticker 列表
        return [stock["ticker"] for stock in sorted_stocks[:n]]
    
    def get_cache_key(self) -> str:
        """生成行业缓存路径 .cache/industry/白酒/"""
        return f"industry/{self.name}"


@dataclass
class PortfolioTarget(AnalysisTarget):
    """
    组合分析目标 - v4.0 新增
    
    使用示例：
    target = PortfolioTarget([
        {"ticker": "600519.SH", "shares": 100, "avg_cost": 1800},
        {"ticker": "000858.SZ", "shares": 200, "avg_cost": 120}
    ])
    tickers = target.to_legacy_tickers()  # ["600519.SH", "000858.SZ"]
    """
    holdings: List[Dict] = field(default_factory=list)
    
    def _get_target_type(self) -> str:
        """返回目标类型"""
        return "portfolio"
    
    def to_legacy_tickers(self) -> List[str]:
        """返回持仓股票列表"""
        return [holding["ticker"] for holding in self.holdings]
    
    def get_cache_key(self) -> str:
        """生成组合缓存路径 .cache/portfolio/{timestamp}/"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"portfolio/{timestamp}"
    
    def add_holding(self, ticker: str, shares: int, avg_cost: float):
        """添加持仓"""
        self.holdings.append({
            "ticker": ticker,
            "shares": shares,
            "avg_cost": avg_cost
        })


def create_target(target_type: str, name: str, **kwargs) -> AnalysisTarget:
    """
    工厂函数：创建分析目标
    
    使用示例：
    target = create_target("ticker", "600519.SH")
    target = create_target("industry", "白酒", top_n=10)
    target = create_target("portfolio", "my_portfolio", holdings=[...])
    """
    if target_type == "ticker":
        return TickerTarget(name=name, **kwargs)
    elif target_type == "industry":
        return IndustryTarget(name=name, **kwargs)
    elif target_type == "portfolio":
        return PortfolioTarget(name=name, **kwargs)
    else:
        raise ValueError(f"Unknown target_type: {target_type}")
