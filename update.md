# UZI-Skill v4.0 功能扩展设计方案

## 📋 项目概述

基于现有 UZI-Skill v3.9.1 架构，新增三大功能模块，同时保持 100% 向后兼容。

---

## 🎯 新增功能

### 功能 1：行业筛选 (`/analyze-industry`)
**输入**：行业名称或行业列表
**输出**：
- 行业评分和评级
- 行业对比排名
- 推荐买入的行业

**示例**：
```bash
/stock-deep-analyzer:analyze-industry 白酒
/stock-deep-analyzer:compare-industries 白酒,新能源,医药
```

---

### 功能 2：行业选股 (`/screen-industry`)
**输入**：行业名称 + 筛选标准
**输出**：
- TOP N 推荐股票列表
- 每只股票的评分和理由
- 建议配置比例

**示例**：
```bash
/stock-deep-analyzer:screen-industry 白酒 --criteria balanced
/stock-deep-analyzer:screen-industry 新能源 --top-n 5
```

---

### 功能 3：组合诊断 (`/portfolio-advice`)
**输入**：用户持仓组合（CSV 或交互式输入）
**输出**：
- 每只股票的买入/卖出/持有建议
- 仓位调整建议
- 组合健康度评分
- 风险预警

**示例**：
```bash
/stock-deep-analyzer:portfolio-advice --file holdings.csv
/stock-deep-analyzer:portfolio-advice  # 交互式输入
```

---

### 功能串联：智能投顾 (`/recommend-portfolio`)
**输入**：候选行业列表 + 预算 + 风险偏好
**输出**：
1. 筛选最佳行业（功能 1）
2. 从行业中选择推荐股票（功能 2）
3. 生成组合配置方案（功能 3）

**示例**：
```bash
/stock-deep-analyzer:recommend-portfolio 白酒,新能源,医药 --budget 10万 --risk moderate
```

---

## 🏗️ 架构设计

### 核心原则

1. **零破坏**：不修改现有 API 和函数签名
2. **适配器模式**：新代码通过适配器调用老代码
3. **模块化**：每个功能独立，可单独测试和维护
4. **格式兼容**：缓存和数据格式完全兼容 v3.9.1

---

### 目录结构（新增部分）

```
UZI-Skill/
├── run.py                              # ✅ 修改：添加新参数（不修改现有流程）
├── lib/
│   ├── target/                        # 🆕 新增：目标抽象层
│   │   ├── __init__.py
│   │   ├── base.py                   # AnalysisTarget 抽象基类
│   │   ├── ticker_target.py          # 单股目标
│   │   ├── industry_target.py         # 行业目标
│   │   └── portfolio_target.py       # 组合目标
│   │
│   ├── pipeline/
│   │   ├── collect.py                # ✅ 不变：现有采集逻辑
│   │   ├── score.py                  # ✅ 不变：现有评分逻辑
│   │   ├── collect_adapter.py        # 🆕 新增：采集适配器
│   │   ├── score_adapter.py          # 🆕 新增：评分适配器
│   │   └── synthesize.py             # ✅ 不变：现有综合逻辑
│   │
│   ├── analysis/                     # 🆕 新增：分析器模块
│   │   ├── __init__.py
│   │   ├── industry_analyzer.py      # 功能 1 实现
│   │   ├── stock_screener.py        # 功能 2 实现
│   │   ├── portfolio_advisor.py      # 功能 3 实现
│   │   └── recommend_engine.py       # 功能串联引擎
│   │
│   ├── report/                       # 🆕 扩展：报告生成
│   │   ├── ticker_report.py          # ✅ 现有逻辑迁移
│   │   ├── industry_report.py        # 🆕 行业报告
│   │   ├── portfolio_report.py        # 🆕 组合报告
│   │   └── comparison_report.py      # 🆕 对比报告
│   │
│   ├── fetchers/                     # 🆕 新增：行业级 Fetcher
│   │   ├── fetch_industry_overview.py
│   │   ├── fetch_industry_trend.py
│   │   └── fetch_industry_valuation.py
│   │
│   └── utils/
│       ├── cache_manager.py           # 🆕 缓存管理
│       └── portfolio_parser.py       # 🆕 组合解析
│
├── skills/
│   └── deep-analysis/
│       ├── scripts/
│       │   ├── fetch_industry_overview.py    # 🆕 行业概览 Fetcher
│       │   ├── fetch_industry_trend.py       # 🆕 行业趋势 Fetcher
│       │   └── ...                         # 现有 22 个 Fetcher 不变
│       │
│       └── SKILL.md                         # ✅ 修改：添加新功能文档
│
├── commands/                          # 🆕 新增：Slash Commands
│   ├── analyze-industry.md
│   ├── screen-industry.md
│   ├── portfolio-advice.md
│   └── recommend-portfolio.md
│
└── docs/
    ├── architecture-v4.0.md          # 🆕 新架构文档
    └── user-guide-v4.0.md          # 🆕 用户使用指南
```

---

## 🔧 核心模块设计

### 模块 1：Target 抽象层

**文件**：`lib/target/base.py`

**设计目的**：统一表示分析目标（单股/行业/组合）

**关键设计**：
- 不影响现有 `ticker` 参数处理
- 新增 `IndustryTarget` 和 `PortfolioTarget`
- 提供 `to_legacy_tickers()` 方法，转换为现有代码可处理的 ticker 列表

**接口设计**：
```python
@dataclass
class AnalysisTarget(ABC):
    target_type: str  # "ticker" | "industry" | "portfolio"
    name: str
    
    @abstractmethod
    def to_legacy_tickers(self) -> List[str]:
        """转换为现有代码可处理的 ticker 列表"""
    
    @abstractmethod
    def get_cache_key(self) -> str:
        """生成缓存路径（兼容现有 .cache/ 结构）"""
```

---

### 模块 2：采集适配器

**文件**：`lib/pipeline/collect_adapter.py`

**设计目的**：为新功能提供数据采集入口，但内部**完全复用**现有 Fetcher

**关键设计**：
- 不修改现有 `collect.py`
- 对行业/组合分析，循环调用现有 `collect()` 函数
- 新增行业级 Fetcher（`fetch_industry_overview.py` 等）

**数据流**：
```
IndustryTarget
    ↓
collect_adapter.collect_for_target()
    ↓
循环调用现有 collect(ticker)  # 对 TOP N 成分股
    ↓
新增 fetch_industry_overview()   # 行业整体数据
    ↓
返回统一格式（兼容现有 raw_data.json）
```

---

### 模块 3：评分适配器

**文件**：`lib/pipeline/score_adapter.py`

**设计目的**：为新功能提供评分入口，但内部**完全复用**现有评分引擎

**关键设计**：
- 不修改现有 `score_dimensions()` 和 `generate_panel()`
- 对行业分析，循环调用现有评分函数
- 新增行业级评分聚合逻辑

**数据流**：
```
采集到的数据
    ↓
score_adapter.score_for_target()
    ↓
循环调用现有 score_dimensions(raw)  # 对每只股票
    ↓
聚合评分（按市值加权平均）
    ↓
生成行业/组合级 panel.json
```

---

### 模块 4：行业分析器（功能 1）

**文件**：`lib/analysis/industry_analyzer.py`

**核心方法**：
```python
class IndustryAnalyzer:
    def analyze(self, industry_name: str, top_n: int = 10) -> Dict:
        """分析单个行业"""
        
    def compare(self, industry_list: List[str]) -> Dict:
        """对比多个行业，返回排名"""
```

**实现逻辑**：
1. 创建 `IndustryTarget`
2. 调用 `collect_adapter` 采集数据
3. 调用 `score_adapter` 评分
4. 生成行业报告

---

### 模块 5：股票筛选器（功能 2）

**文件**：`lib/analysis/stock_screener.py`

**核心方法**：
```python
class StockScreener:
    def screen(self, industry_name: str, 
               criteria: str = "balanced",
               top_n: int = 10) -> Dict:
        """从行业中筛选推荐股票"""
```

**筛选标准**：
- `value`：价值型（低 PE + 高股息 + 护城河）
- `growth`：成长型（高增速 + 高 PEG）
- `balanced`：均衡型（综合评分 TOP 3）
- `aggressive`：激进型（游资偏好 + 技术突破）

---

### 模块 6：组合顾问（功能 3）

**文件**：`lib/analysis/portfolio_advisor.py`

**核心方法**：
```python
class PortfolioAdvisor:
    def analyze(self, holdings: List[Dict]) -> Dict:
        """分析用户组合，给出建议"""
```

**输入格式**（CSV 或 JSON）：
```csv
ticker,shares,avg_cost
600519.SH,100,1800
000858.SZ,200,120
```

**输出内容**：
- 每只股票的建议（买入/卖出/持有）
- 目标仓位 vs 当前仓位
- 组合健康度评分
- 风险提示

---

### 模块 7：推荐引擎（功能串联）

**文件**：`lib/analysis/recommend_engine.py`

**核心方法**：
```python
class RecommendEngine:
    def recommend(self, 
                  industry_list: List[str],
                  budget: float,
                  risk_tolerance: str) -> Dict:
        """完整投资决策流程"""
```

**执行流程**：
1. 调用 `IndustryAnalyzer.compare()` 筛选最佳行业
2. 调用 `StockScreener.screen()` 从行业选股
3. 调用 `PortfolioAdvisor` 生成配置方案
4. 生成完整报告

---

## 🔄 数据流设计

### 现有功能（不变）

```
用户输入: 600519.SH
    ↓
run.py (现有逻辑)
    ↓
collect(ticker)  # 现有函数
    ↓
score_dimensions(raw)  # 现有函数
    ↓
generate_panel()  # 现有函数
    ↓
assemble_report()  # 现有函数
    ↓
输出 HTML 报告（现有格式）
```

---

### 新功能：行业分析

```
用户输入: --industry 白酒
    ↓
run.py (新参数分支)  # 不修改现有流程
    ↓
IndustryAnalyzer.analyze("白酒")
    ↓
collect_adapter.collect_for_target(IndustryTarget)
    ↓
循环调用 collect(ticker)  # 对 TOP 10 成分股（复用现有函数）
    + 调用 fetch_industry_overview()  # 新增 Fetcher
    ↓
score_adapter.score_for_target()
    ↓
循环调用 score_dimensions(raw)  # 复用现有函数
    + 聚合评分
    ↓
industry_report.assemble()  # 新增报告模板
    ↓
输出行业报告 HTML
```

---

### 新功能：组合诊断

```
用户输入: --portfolio holdings.csv
    ↓
run.py (新参数分支)
    ↓
PortfolioAdvisor.analyze(holdings)
    ↓
循环调用 collect(ticker)  # 对持仓股票（复用现有函数）
    ↓
循环调用 score_dimensions(raw)  # 复用现有函数）
    ↓
生成买入/卖出建议
    ↓
portfolio_report.assemble()  # 新增报告模板
    ↓
输出组合诊断报告
```

---

## 🧪 兼容性保证

### 测试策略

1. **回归测试**：现有 649 个 pytest 必须全过
2. **快照测试**：对比新版本和旧版本生成的报告（MD5 校验）
3. **手动测试**：测试所有现有 Slash Command

### 兼容性检查清单

| 检查项 | 方法 |
|--------|------|
| 现有 CLI 命令不变 | `python run.py 600519.SH` 产生相同结果 |
| 现有 Slash Command 不变 | `/stock-deep-analyzer:analyze-stock` 不变 |
| 缓存格式兼容 | `.cache/<ticker>/` 结构不变 |
| 数据格式兼容 | `raw_data.json` 格式不变（新增字段用 `_` 前缀）|
| 报告格式兼容 | 现有报告模板不变，新增独立模板 |
| Resume 功能不变 | `--resume` 对单股分析仍有效 |

---

## 📝 实施步骤

### Phase 1：基础架构（1-2 天）

1. 创建 `lib/target/` 目录和基类
2. 创建 `lib/pipeline/collect_adapter.py`
3. 创建 `lib/pipeline/score_adapter.py`
4. 编写单元测试（兼容性测试）

### Phase 2：功能 1 - 行业筛选（2-3 天）

1. 实现 `IndustryAnalyzer`
2. 新增 `fetch_industry_overview.py` Fetcher
3. 实现行业报告模板
4. 添加 `--analyze-industry` 参数

### Phase 3：功能 2 - 行业选股（2-3 天）

1. 实现 `StockScreener`
2. 实现筛选逻辑（value/growth/balanced/aggressive）
3. 实现选股报告模板
4. 添加 `--screen-industry` 参数

### Phase 4：功能 3 - 组合诊断（3-4 天）

1. 实现 `PortfolioAdvisor`
2. 实现组合解析（CSV/JSON/交互式）
3. 实现买入/卖出建议逻辑
4. 实现组合报告模板
5. 添加 `--portfolio-advice` 参数

### Phase 5：功能串联（1-2 天）

1. 实现 `RecommendEngine`
2. 串联功能 1 + 功能 2 + 功能 3
3. 添加 `--recommend-portfolio` 参数

### Phase 6：文档和测试（2-3 天）

1. 更新 `SKILL.md`
2. 更新 `README.md`
3. 编写用户使用指南
4. 编写开发者文档
5. 完整回归测试

---

## 🚀 使用方式

### 快速开始

```bash
# 安装（不变）
/plugin marketplace add wbh604/UZI-Skill
/plugin install stock-deep-analyzer@uzi-skill

# 功能 1：行业筛选
/stock-deep-analyzer:analyze-industry 白酒
/stock-deep-analyzer:compare-industries 白酒,新能源,医药

# 功能 2：行业选股
/stock-deep-analyzer:screen-industry 白酒 --criteria balanced
/stock-deep-analyzer:screen-industry 新能源 --top-n 5 --criteria growth

# 功能 3：组合诊断
/stock-deep-analyzer:portfolio-advice --file holdings.csv
/stock-deep-analyzer:portfolio-advice  # 交互式输入

# 功能串联：智能投顾
/stock-deep-analyzer:recommend-portfolio 白酒,新能源,医药 --budget 10万 --risk moderate
```

---

## 📊 预期效果

### 功能 1 输出示例

```json
{
  "industry_name": "白酒",
  "overall_score": 75.5,
  "rating": "值得关注",
  "reasons": [
    "行业估值处于历史低位",
    "龙头股护城河深厚",
    "政策面支持消费复苏"
  ],
  "top_stocks": [
    {"ticker": "600519.SH", "name": "贵州茅台", "score": 85},
    {"ticker": "000858.SZ", "name": "五粮液", "score": 78}
  ],
  "risks": [
    "消费复苏不及预期",
    "行业竞争加剧"
  ]
}
```

### 功能 2 输出示例

```json
{
  "industry_name": "白酒",
  "recommended": [
    {
      "ticker": "600519.SH",
      "name": "贵州茅台",
      "score": 85,
      "reason": "护城河深厚，ROE稳定，估值合理",
      "target_price": 2200,
      "position_suggestion": "30%"
    }
  ],
  "not_recommended": [...],
  "industry_outlook": "中性偏多"
}
```

### 功能 3 输出示例

```json
{
  "portfolio_health": 72,
  "holdings_analysis": [
    {
      "ticker": "600519.SH",
      "current_shares": 100,
      "current_cost": 1800,
      "suggest": "hold",
      "target_position": "25%",
      "reason": "估值合理，继续持有"
    },
    {
      "ticker": "000858.SZ",
      "current_shares": 200,
      "current_cost": 120,
      "suggest": "buy",
      "target_position": "15%",
      "reason": "估值低估，建议加仓"
    }
  ],
  "risks": [...]
}
```

---

## 🎯 总结

本设计方案遵循以下原则：

1. **100% 向后兼容**：现有功能完全不变
2. **最大化复用**：新功能复用现有 22 个 Fetcher 和评分引擎
3. **模块化设计**：每个功能独立，易于测试和维护
4. **可扩展性**：未来可以轻松添加板块分析、跨境对比等功能

预计开发周期：**10-15 天**
预计新增代码：**约 3000-4000 行**（含注释和测试）
