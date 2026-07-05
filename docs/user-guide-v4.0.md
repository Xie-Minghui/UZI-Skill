# UZI-Skill v4.0 使用指南

## 📂 快速开始

### 安装（不变）

```bash
# Claude Code
/plugin marketplace add wbh604/UZI-Skill
/plugin install stock-deep-analyzer@uzi-skill

# 其他 agent (Codex/Cursor/Gemini)
# 参考 AGENTS.md 对应章节
```

---

## 🎯 v4.0 新增功能概览

| 功能 | 命令 | 说明 |
|------|------|---------|
| **功能 1** | `/analyze-industry` | 分析行业，判断哪个值得入手 |
| **功能 2** | `/screen-industry` | 从行业筛选推荐股票 |
| **功能 3** | `/portfolio-advice` | 诊断组合，给出买卖建议 |
| **功能串联** | `/recommend-portfolio` | 智能投顾（选行业→选股票→配资金） |

---

## 📊 功能 1：行业筛选

### 用途

判断哪个行业值得入手。

### 命令

#### 分析单个行业

```bash
/stock-deep-analyzer:analyze-industry 白酒
/stock-deep-analyzer:analyze-industry 新能源
```

**输出**：
- 行业综合评分（0-100 分）
- 行业评级（值得重仓 / 可以蹲一蹲 / 观望 / 谨慎 / 回避）
- TOP 3 推荐股票
- 看多/看空理由
- 风险提示

#### 对比多个行业

```bash
/stock-deep-analyzer:compare-industries 白酒,新能源,医药
```

**输出**：
- 行业排名（按评分）
- 最佳行业
- 每个行业的简评

---

## 🔍 功能 2：行业选股

### 用途

从指定行业中筛选推荐买入的股票。

### 命令

```bash
/stock-deep-analyzer:screen-industry 白酒 --criteria balanced
/stock-deep-analyzer:screen-industry 新能源 --criteria growth
```

### 筛选标准

| 标准 | 说明 | 适合 |
|------|---------|-------|
| `value` | 价值型（低 PE + 高股息 + 护城河） | 稳健投资者 |
| `growth` | 成长型（高增速 + 高 PEG） | 成长投资者 |
| `balanced` | 均衡型（综合评分 TOP 3）**默认** | 大多数投资者 |
| `aggressive` | 激进型（游资偏好 + 技术突破） | 激进投资者 |

### 输出

- TOP 3 推荐股票（名称、代码、评分、理由）
- 建议配置比例
- 行业展望

---

## 💼 功能 3：组合诊断

### 用途

针对自己的持仓组合，给出买入/卖出/持有建议。

### 命令

#### 方式 1：从 CSV 文件读取

```bash
/stock-deep-analyzer:portfolio-advice --file holdings.csv
```

**CSV 格式**：
```csv
ticker,shares,avg_cost
600519.SH,100,1800
000858.SZ,200,120
```

#### 方式 2：交互式输入

```bash
/stock-deep-analyzer:portfolio-advice
```

然后按提示输入：
```
股票代码: 600519.SH
持股数量: 100
平均成本: 1800
继续添加? (y/n): y
...
```

### 输出

- 组合健康度评分（0-100 分）
- 每只股票的操作建议（买入/卖出/持有）
- 目标仓位
- 盈亏分析
- 风险提示

---

## 🎯 功能串联：智能投顾

### 用途

完整投资决策流程：**选择行业 → 筛选股票 → 配置资金**。

### 命令

```bash
/stock-deep-analyzer:recommend-portfolio 白酒,新能源,医药 --budget 10万 --risk moderate
```

### 参数

| 参数 | 说明 | 默认值 |
|------|---------|--------|
| 行业列表 | 候选行业（逗号分隔） | 必填 |
| `--budget` | 预算（元） | 100000 |
| `--risk` | 风险偏好 | `moderate` |

### 风险偏好

| 偏好 | 说明 | 现金储备 |
|------|---------|---------|
| `conservative` | 保守 | 30% |
| `moderate` | 稳健 **默认** | 20% |
| `aggressive` | 激进 | 10% |

### 输出

- 推荐行业
- TOP 3 推荐股票
- 资金配置方案
- 预期收益和风险
- 完整 HTML 报告

---

## 📋 CSV 格式详解

### 标准格式（有表头）

```csv
ticker,shares,avg_cost
600519.SH,100,1800
000858.SZ,200,120
```

### 中文格式（有表头）

```csv
股票代码,持股数量,平均成本
600519.SH,100,1800
000858.SZ,200,120
```

### 无表头格式

```csv
600519.SH,100,1800
000858.SZ,200,120
```

系统会自动检测是否有表头。

---

## 💡 使用场景

### 场景 1：我想投资，但不知道选哪个行业

**解决**：用 `/compare-industries` 对比多个行业

```
/stock-deep-analyzer:compare-industries 白酒,新能源,医药
```

→ 系统返回行业排名，选择最佳行业

---

### 场景 2：我想投资白酒行业，但不知道选哪只股票

**解决**：用 `/screen-industry` 从行业中筛选

```
/stock-deep-analyzer:screen-industry 白酒 --criteria balanced
```

→ 系统返回 TOP 3 推荐股票和配置建议

---

### 场景 3：我有一笔 10 万元资金，想分散投资

**解决**：用 `/recommend-portfolio` 智能投顾

```
/stock-deep-analyzer:recommend-portfolio 白酒,新能源,医药 --budget 100000 --risk moderate
```

→ 系统自动选择最佳行业，筛选推荐股票，生成资金配置方案

---

### 场景 4：我想检查自己的持仓是否合理

**解决**：用 `/portfolio-advice` 诊断组合

```
/stock-deep-analyzer:portfolio-advice --file holdings.csv
```

→ 系统给出每只股票的操作建议（买入/卖出/持有）和目标仓位

---

## ⚠️ 注意事项

### 1. 行业名称要准确

- ✅ 正确：`白酒`、`新能源汽车`、`半导体`
- ❌ 错误：`酒`、`汽车`、`芯片`

### 2.  CSV 文件要用股票代码

- ✅ 正确：`600519.SH,100,1800`
- ❌ 错误：`贵州茅台,100,1800`

### 3. 建议仅供参考

- 系统建议基于量化评分
- 最终决策需要结合自己的判断

### 4. 及时更新 CSV

- 如果持仓有变化，要更新 CSV 文件
- 或者重新交互式输入

---

## 📖 相关文档

- **设计文档**：`update.md`
- **架构流程图**：`docs/architecture-v4.0.md`
- **实现指南**：`docs/implementation-guide-v4.0.md`
- **原有功能文档**：`README.md`、`AGENTS.md`

---

## 🐛 常见问题

### Q1：如何获取行业成分股？

**A**：系统会自动调用 `akshare` API 获取行业成分股。如果获取失败，会使用示例数据（如白酒行业的贵州茅台、五粮液等）。

---

### Q2：评分逻辑是什么？

**A**：评分基于：
1. 22 维数据采集（基本面、技术面、舆情等）
2. 66 位评委投票（价值派、成长派、宏观派等）
3. 17 种机构级方法（DCF、Comps、LBO 等）

---

### Q3：如何导出报告？

**A**：所有功能都会生成 HTML 报告，保存在 `reports/` 目录。

可以用 `--output-dir` 指定输出目录：

```bash
python run.py --industry 白酒 --output-dir /tmp/reports
```

---

### Q4：分析时间多久？

**A**：取决于模式和行业数量：

| 模式 | 时间 |
|------|------|
| 快速模式（`--depth lite`） | 1-2 分钟 |
| 标准模式（默认） | 5-8 分钟 |
| 深度模式（`--depth deep`） | 15-20 分钟 |
| 对比 3 个行业 | 15-25 分钟 |

---

## 📞 联系和反馈

如有问题或建议，请：
1. 提交 GitHub Issue：https://github.com/Xie-Minghui/UZI-Skill/issues
2. 查看现有文档：`README.md`、`AGENTS.md`、`docs/`

---

**版本**：v4.0  
**最后更新**：2026-07-05  
**作者**：FloatFu-true
