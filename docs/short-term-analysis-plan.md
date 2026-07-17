# 短线适配性分析功能计划

## 一、功能目标

用户输入**股票代码或名称**，系统综合分析后给出：
- **适合短线** → 输出持仓策略（入场价、止盈/止损位、仓位建议、持仓周期）
- **不适合短线** → 输出原因（波动不足、流动性差、技术面破位等）

---

## 二、现有架构分析

| 模块 | 现状 | 差距 |
|------|------|------|
| `FinancialAgent` | 只取最新一日价格 + PE/ROE | 缺少多日K线、换手率、量比 |
| `TechnicalAgent` | 硬编码占位，未接入真实数据 | 需实现 MACD/RSI/均线/布林带等 |
| `NewsAgent` | RAG 检索 + LLM 情感分析 | 基本可用，可复用 |
| `RiskAgent` | 硬编码占位 | 需基于真实波动率/换手率计算 |
| `ReportAgent` | 通用投资报告 prompt | 需改为短线专用 prompt |
| `AkShareRepository` | 仅 `stock_zh_a_hist` 取单日 + 财务摘要 | 需新增多日历史K线、个股资金流向等 |
| 前端 | 只有代码输入框 | 需支持名称搜索/联想 |
| State | 无短线判定字段 | 需新增 `short_term_result` |

---

## 三、技术方案

### 3.1 后端改动

#### Task 1：扩展 AkShareRepository — 新增数据源

文件：`app/services/repositories/akshare_repo.py`

新增方法：

| 方法 | akshare 接口 | 用途 |
|------|-------------|------|
| `get_hist_kline(symbol, days=30)` | `stock_zh_a_hist` (返回多日 DataFrame) | 近 30 日 K 线 |
| `get_stock_name(symbol)` | `stock_individual_info_em` | 股票代码 → 名称 |
| `search_by_name(name)` | `stock_zh_a_spot_em` | 名称模糊搜索 → 代码 |
| `get_money_flow(symbol)` | `stock_individual_fund_flow` | 个股资金流向 |

#### Task 2：扩展数据模型

文件：`app/services/models/stock.py`

新增模型：

```python
class KLineBar(BaseModel):
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: float
    turnover: float | None = None     # 换手率

class TechnicalIndicators(BaseModel):
    ma5: float | None = None
    ma10: float | None = None
    ma20: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    rsi: float | None = None
    boll_upper: float | None = None
    boll_lower: float | None = None
    volume_ratio: float | None = None  # 量比

class MoneyFlow(BaseModel):
    main_net_inflow: float | None = None   # 主力净流入
    retail_net_inflow: float | None = None  # 散户净流入

class ShortTermAssessment(BaseModel):
    suitable: bool
    score: float           # 0-100 综合评分
    reasons: list[str]     # 判断依据
    strategy: dict | None = None  # 适合时给出策略
```

#### Task 3：实现真正的 TechnicalAgent

文件：`app/agents/technical.py`

基于 30 日 K 线计算技术指标：

- **MA5 / MA10 / MA20**：多头排列判断趋势
- **MACD**：金叉/死叉信号
- **RSI**：超买(>70)/超卖(<30)区间
- **布林带**：价格是否触及上下轨
- **量比**：放量/缩量判断

> 计算逻辑用纯 Python（pandas），不引入 TA-Lib 等 C 依赖，降低部署复杂度。

#### Task 4：实现真正的 RiskAgent

文件：`app/agents/risk.py`

基于真实数据评估短线风险：

- **波动率**：近 N 日收益率标准差
- **换手率**：过低(<1%)不适合短线
- **流动性**：日均成交额是否充足（建议 > 5000万）
- **涨跌停距离**：当前价距涨跌停的空间

#### Task 5：新增 ShortTermAgent（核心）

文件：`app/agents/short_term.py`（新建）

汇总技术面、资金面、风险面，通过 LLM 做短线适配性判断：

```
输入：technical_analysis + risk_analysis + news_analysis + financial_analysis
输出：ShortTermAssessment（适合/不适合 + 原因 + 策略）
```

Prompt 设计要点：
- 短线核心关注：趋势、量能、波动率、资金流向
- 明确评分维度（技术面 40% + 资金面 20% + 波动/流动性 20% + 新闻情绪 20%）
- 适合时给出：建议入场区间、止盈位、止损位、仓位比例、预期持仓天数
- 不适合时给出：具体原因 + 当前更适合的操作建议（观望/等回调等）

#### Task 6：修改 LangGraph 工作流

文件：`app/graph/workflow.py`

```
当前：financial → [news, technical, risk] → report → END
改为：financial → [news, technical, risk] → short_term → report → END
```

- 在 report 之前插入 `ShortTermAgent` 节点
- report prompt 改为短线专用模板，整合 `ShortTermAssessment` 结果

#### Task 7：扩展 State

文件：`app/graph/state.py`

新增字段：

```python
kline_data: list[dict] | None        # K线历史
indicators: dict | None              # 技术指标
money_flow: dict | None              # 资金流向
short_term_assessment: dict | None   # 短线评估结果
stock_name: str | None               # 股票名称
```

#### Task 8：新增 API 接口

文件：`app/api/v1/routes/short_term.py`（新建）

```python
POST /api/v1/short-term-analyze    # 流式返回短线分析
GET  /api/v1/stock/search?q=茅台   # 股票名称搜索
```

#### Task 9：StockDataService 扩展

文件：`app/services/stock_service.py`

新增方法：

- `get_kline_data(stock_code, days)` — 获取多日 K 线
- `get_technical_indicators(stock_code)` — 计算并返回技术指标
- `get_money_flow(stock_code)` — 获取资金流向
- `search_stock(query)` — 支持代码/名称模糊搜索

### 3.2 前端改动

#### Task 10：新增短线分析页面组件

文件：`frontend/src/components/ShortTerm.vue`（新建）

UI 布局：

```
┌──────────────────────────────────────┐
│  [股票搜索框] 支持代码/名称输入 + 联想 │
│  [开始短线分析]                       │
├──────────────────────────────────────┤
│  分析进度条（各 Agent 节点进度）       │
├──────────────────────────────────────┤
│  综合评分：82 / 100  ✅ 适合短线      │
│                                      │
│  📈 持仓策略                          │
│  ├ 入场区间：15.2 - 15.5             │
│  ├ 止盈位：16.8 (+8.5%)              │
│  ├ 止损位：14.6 (-4%)                │
│  ├ 建议仓位：30%                     │
│  └ 预期持仓：3-5 个交易日             │
│                                      │
│  📊 K线图（ECharts candlestick）      │
│  📰 新闻情绪                          │
│  ⚠️ 风险提示                         │
└──────────────────────────────────────┘
```

#### Task 11：股票搜索组件

文件：`frontend/src/components/StockSearch.vue`（新建）

- 输入框支持代码和名称
- 防抖请求 `/api/v1/stock/search`
- 下拉联想列表，点击选中

#### Task 12：K线图升级

文件：`frontend/src/components/KLine.vue`

- 从静态 mock 改为接入真实 K 线数据
- 使用 ECharts candlestick 图
- 叠加 MA5/MA10/MA20 均线

### 3.3 数据流总览

```
用户输入（代码/名称）
        │
        ▼
  StockDataService
  ├─ 代码解析（名称→代码）
  ├─ 30日K线
  ├─ 财务数据
  ├─ 资金流向
  └─ 新闻检索
        │
        ▼
  LangGraph Workflow
  financial ──→ [news | technical | risk] ──→ short_term ──→ report
        │
        ▼
  流式返回前端
  ├─ 进度事件（各节点完成）
  ├─ 短线判定结果（适合/不适合）
  └─ 完整分析报告
```

---

## 四、容易忽略的细节

1. **名称 → 代码映射**：当前 `NewsAgent` 中硬编码了 5 只股票的映射表，需要改为动态查询 akshare 全市场列表
2. **ST / 退市 / 停牌股过滤**：搜索结果和输入校验时需排除 ST 股和停牌股，这类股票短线风险极高
3. **新股（上市不足 30 日）**：K 线数据不足时，技术指标无法计算，应明确告知用户
4. **数据缓存策略**：K 线和技术指标缓存 TTL 建议 ≤ 5 分钟（盘中）/ 1 小时（盘后），避免用过期数据做短线判断
5. **交易时间感知**：非交易时段获取的是上一交易日数据，报告中应标注数据时效性
6. **免责声明**：短线分析结果页面底部必须添加风险提示——"以上分析仅供参考，不构成投资建议"
7. **LLM 输出稳定性**：`ShortTermAgent` 要求 LLM 输出结构化 JSON 而非自由文本，便于前端解析评分和策略；需做 JSON 解析容错（LLM 可能输出多余文字）
8. **并发与超时**：akshare 接口偶尔响应慢（已设 3s 超时），若多个 Agent 同时请求可能叠加延迟，需设置全局超时兜底
9. **历史回测（可选/后续）**：未来可用历史数据验证模型准确率，当前版本不涉及

---

## 五、实施顺序

| 阶段 | 任务 | 产出 |
|------|------|------|
| **阶段 1** | Task 1 + Task 2 | 数据层就绪（可独立测试） |
| **阶段 2** | Task 3 + Task 4 + Task 9 | 技术指标 + 风险评估 + Service 层 |
| **阶段 3** | Task 5 + Task 6 + Task 7 | LangGraph 工作流改造完成 |
| **阶段 4** | Task 8 | API 接口层 |
| **阶段 5** | Task 10 + Task 11 + Task 12 | 前端 UI |
| **阶段 6** | 联调 + 测试 | 端到端验证 |

---

## 六、技术决策说明

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 技术指标计算 | 纯 pandas | 项目已依赖 pandas，不引入 TA-Lib 等 C 库，降低部署复杂度 |
| 短线评估方式 | LLM 结构化输出 | 复用现有 Ollama + qwen3，灵活性高于规则引擎 |
| 搜索方式 | akshare 全市场快照过滤 | 无需维护本地股票库，数据实时 |
| 前端 K 线图 | ECharts candlestick | 项目已引入 ECharts，直接升级即可 |
