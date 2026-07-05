# UZI-Skill 代码流程图

## 整体架构（Mermaid）

```mermaid
graph TB
    subgraph "用户入口"
        A[用户输入股票代码] --> B[run.py]
        B --> C{选择路径}
    end
    
    subgraph "路径 A - CLI 快速模式"
        C -->|lite/deep| D[直接生成报告]
        D --> E[输出 HTML/图片]
    end
    
    subgraph "路径 B - 全量 Agent 分析"
        C -->|深度分析| F[Stage 1: 数据采集]
        F --> G[22 维数据收集]
        G --> H[规则引擎预打分]
        H --> I[保存 raw_data.json]
        I --> J[Agent 介入点 🔴]
        J --> K[读取 panel.json]
        K --> L[角色扮演 66 评委]
        L --> M[更新 agent_analysis.json]
        M --> N[Stage 2: 报告生成]
        N --> O[自检 self_review.py]
        O --> P{critical > 0?}
        P -->|是| Q[阻止生成 → 返回修复]
        P -->|否| R[生成 HTML 报告]
    end
    
    subgraph "66 位评审团结构"
        L --> S1[A组: 经典价值 6人]
        L --> S2[B组: 成长投资 9人]
        L --> S3[C组: 宏观对冲 7人]
        L --> S4[D组: 技术趋势 4人]
        L --> S5[E组: 中国价投 7人]
        L --> S6[F组: A股游资 24人]
        L --> S7[G组: 量化系统 4人]
        L --> S8[H组: 科技领袖 4人]
        L --> S9[I组: Serenity 1人]
    end
    
    style J fill:#ff6b6b,color:#fff
    style O fill:#4ecdc4,color:#fff
    style P fill:#ffe66d
```

## 详细执行流程图

```mermaid
sequenceDiagram
    participant User as 用户
    participant CLI as run.py
    participant Stage1 as Stage 1<br/>数据采集
    participant Agent as Agent<br/>角色扮演
    participant Stage2 as Stage 2<br/>报告生成
    participant Review as self_review.py
    participant Output as HTML 报告
    
    User->>CLI: 输入股票代码 (如: 贵州茅台)
    CLI->>CLI: preflight 检查<br/>(网络/ticker验证)
    
    alt 快速模式 (--depth lite)
        CLI->>Stage1: 采集 7 维核心数据
        Stage1->>Stage2: 直接生成报告
        Stage2->>Output: 输出 HTML
    else 深度模式 (默认)
        CLI->>Stage1: 采集 22 维数据
        
        loop 22 个 Fetcher 并发执行
            Stage1->>Stage1: fetch_basic.py (基本面)
            Stage1->>Stage1: fetch_kline.py (K线)
            Stage1->>Stage1: fetch_financials.py (财报)
            Stage1->>Stage1: fetch_peers.py (同行)
            Stage1->>Stage1: fetch_sentiment.py (舆情)
            Stage1->>Stage1: ... (其他 17 维)
        end
        
        Stage1->>Stage1: 规则引擎预打分<br/>(investor_evaluator.py)
        Stage1->>Agent: 生成 panel.json 骨架
        
        Note over Agent: 🔴 HARD-GATE<br/>Agent 必须介入
        
        Agent->>Agent: 读取 panel.json
        Agent->>Agent: 逐组角色扮演 66 评委
        
        loop 9 大流派评审
            Agent->>Agent: A组: 巴菲特/格雷厄姆/芒格
            Agent->>Agent: B组: 林奇/木头姐/黄仁勋
            Agent->>Agent: C组: 索罗斯/达里奥
            Agent->>Agent: ... (其他组)
        end
        
        Agent->>Agent: 生成 agent_analysis.json<br/>(dim_commentary + panel_insights)
        Agent->>Stage2: 传递分析结果
        
        Stage2->>Review: 执行 13 条自检
        Review->>Review: 检查 critical issues
        
        alt critical > 0
            Review-->>Agent: 返回修复建议
            Agent->>Agent: 修复问题
        else 通过检查
            Stage2->>Output: 生成完整 HTML 报告
            Stage2->>Output: 生成分享图片
            Output->>User: 返回报告路径
        end
    end
```

## 核心模块依赖图

```mermaid
graph LR
    subgraph "入口层"
        A[run.py]
    end
    
    subgraph "Pipeline 层 (v3.0+)"
        B1[lib/pipeline/run.py<br/>编排入口]
        B2[lib/pipeline/collect.py<br/>并发采集]
        B3[lib/pipeline/score.py<br/>评分]
        B4[lib/pipeline/synthesize.py<br/>综合]
        B5[lib/pipeline/score_fns.py<br/>纯函数]
    end
    
    subgraph "数据采集层 (22 Fetchers)"
        C1[fetch_basic.py]
        C2[fetch_kline.py]
        C3[fetch_financials.py]
        C4[fetch_peers.py]
        C5[fetch_sentiment.py]
        C6[fetch_lhb.py]
        C7[...]
    end
    
    subgraph "评分引擎"
        D1[investor_criteria.py<br/>242 条规则]
        D2[investor_evaluator.py<br/>规则引擎]
        D3[investor_db.py<br/>66 评委数据库]
        D4[stock_features.py<br/>108 标准化特征]
    end
    
    subgraph "报告生成层"
        E1[assemble_report.py]
        E2[lib/report/svg_primitives.py]
        E3[lib/report/dim_viz.py]
        E4[lib/report/institutional.py]
        E5[lib/report/panel_cards.py]
    end
    
    subgraph "自检层"
        F1[self_review.py<br/>13 条检查]
    end
    
    A --> B1
    B1 --> B2
    B2 --> C1
    B2 --> C2
    B2 --> C3
    B2 --> C4
    B2 --> C5
    C1 --> D1
    C2 --> D1
    C3 --> D1
    D1 --> D2
    D2 --> D3
    D2 --> D4
    B3 --> E1
    E1 --> E2
    E1 --> E3
    E1 --> E4
    E1 --> E5
    E1 --> F1
    
    style A fill:#61dafb
    style F1 fill:#ff6b6b,color:#fff
```

## 数据流图

```mermaid
graph TB
    subgraph "输入"
        A[股票代码<br/>600519 / 002273.SZ / AAPL]
    end
    
    subgraph "Stage 1: 数据采集 (脚本)"
        B1[raw_data.json<br/>22 维原始数据]
        B2[panel.json<br/>66 评委骨架分]
        B3[synthesis.json<br/>综合研判]
    end
    
    subgraph "Agent 分析 (AI 介入)"
        C1[agent_analysis.json<br/>Agent 角色扮演结果]
        C1 --> C2[dim_commentary<br/>维度定性评语]
        C1 --> C3[panel_insights<br/>评审团观察]
        C1 --> C4[great_divide<br/>多空辩论]
        C1 --> C5[narrative<br/>核心结论]
    end
    
    subgraph "Stage 2: 报告生成 (脚本)"
        D1[index.html<br/>主报告]
        D2[share_card.png<br/>朋友圈竖图]
        D3[wechat_banner.png<br/>微信群战报]
        D4[summary.txt<br/>文字摘要]
    end
    
    subgraph "自检 Gate"
        E1[self_review.py]
        E1 --> E2{13 条检查}
        E2 -->|critical| E3[阻止生成]
        E2 -->|pass| D1
    end
    
    A --> B1
    B1 --> B2
    B2 --> C1
    C1 --> E1
    E1 --> D1
    D1 --> D2
    D1 --> D3
    D1 --> D4
    
    style C1 fill:#4ecdc4,color:#fff
    style E1 fill:#ff6b6b,color:#fff
```

## 66 评委评审流程

```mermaid
graph TB
    A[开始评审] --> B[读取 raw_data.json]
    B --> C[逐组角色扮演]
    
    C --> D1[A组: 价值派]
    C --> D2[B组: 成长派]
    C --> D3[C组: 宏观派]
    C --> D4[D组: 技术派]
    C --> D5[E组: 中国价投]
    C --> D6[F组: 游资]
    C --> D7[G组: 量化]
    C --> D8[H组: 科技领袖]
    C --> D9[I组: Serenity]
    
    D1 --> E1[巴菲特]
    D1 --> E2[格雷厄姆]
    D1 --> E3[芒格]
    
    D6 --> F1[赵老哥]
    D6 --> F2[章盟主]
    D6 --> F3[炒股养家]
    
    E1 --> G[生成判断]
    E2 --> G
    E3 --> G
    F1 --> G
    F2 --> G
    F3 --> G
    
    G --> H[signal: bullish/bearish/neutral]
    H --> I[score: 0-100]
    I --> J[reasoning + 引用规则]
    
    J --> K[更新 panel.json]
    K --> L[写入 agent_analysis.json]
    
    style A fill:#61dafb
    style G fill:#4ecdc4,color:#fff
```

## 关键技术点

### 1. 角色扮演机制
- Agent 不是简单跑规则，而是**真正站在投资者角度思考**
- 三层评估：真实持仓 → 行业亲和度 → 量化规则
- 可以覆盖规则引擎的得分，但必须给出理由

### 2. 自检 Gate (v2.9+)
- `self_review.py` 执行 13 条自动检查
- Critical 问题 > 0 时，**物理上阻止报告生成**
- 每次新 BUG 修复后都会添加新的检查规则

### 3. 数据源 Fallback
- 40+ 数据源，3 层 Tier
- 主源失败 → 自动切换备源 → Playwright 浏览器兜底
- 确保数据可用性

### 4. 多维度分析
- 22 维数据覆盖：基本面、技术面、舆情、行业、政策等
- 17 种机构级方法：DCF、Comps、LBO、IC Memo 等
- 66 位评委 × 242 条量化规则

## 总结

**UZI-Skill 是单 Agent 系统**，核心创新在于：
1. **角色扮演代替多 Agent**：一个 Agent 模拟 66 个不同投资风格的角色
2. **两段式设计**：脚本负责数据采集/计算，Agent 负责定性分析
3. **强制自检**：通过 HARD-GATE 确保分析质量
4. **可扩展性**：易于添加新的评委和评分规则

这种设计比传统多 Agent 系统更高效，避免了 Agent 间的通信开销，同时保证了分析的一致性。
