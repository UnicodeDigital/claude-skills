---
name: starrocks-query
description: 通过自然语言查询公司 StarRocks 数据仓库（加密货币量化数据）。当用户询问行情、K线、订单簿、成交、资金费率、未平仓量 OI、强平、ADL 风险、CoinGlass 衍生指标、ETL 数据质量等需要从数据库取数的问题时使用此 skill。覆盖 Binance、Bitget、OKX、Hyperliquid、CoinGlass 等交易所/数据源，包含 tick 级（Iceberg 外表）与 1m/1d/5m 聚合数据。本 skill 通过 starrocks MCP server 访问数据库**。
---

# StarRocks 量化数据查询 Skill

## 前置条件
本 skill 依赖名为 `starrocks` 的 MCP server。如果 Claude 没有发现以下工具，请用户在 Claude Desktop/Code 设置里配置 MCP server。

可用 MCP 工具：
- `execute_query(sql)` —— 执行只读 SQL，返回结果
- `search_schema(keywords)` —— 关键词搜表
- `describe_table(table)` —— 单表完整 schema以及三条sample数据
- `list_databases()` —— 所有库
- `list_tables()` —— 全量表清单（含 comment，按 catalog.db 分组）
- `get_query_context()` —— 指标口径词典 + SQL 示例（会话初始化用）

## 数据布局（Catalog / Database / 路由规则）

StarRocks 是统一查询入口。底下挂两个 catalog：

| Catalog | 类型 | 数据库 | 装什么 | 查询路径 |
|---|---|---|---|---|
| `default_catalog` | StarRocks 内部表 | `lfdata` | 中低频数据：资金费率、持仓量、K线、聚合指标、强平、ADL 等 | `lfdata.<table>` |
| `iceberg` | Iceberg 外表（NAS/S3 Parquet, zstd） | `udata` | 高频 tick：trade、bbo (book_ticker)、orderbook、mark_price | `iceberg.udata.<table>`（**三段式必须带 catalog 前缀**） |

**数据链路**
- 高频：Exchange WebSocket → Kafka → Flink ETL → Iceberg (按 `dt` UTC 天分区) → StarRocks Iceberg Catalog
- 中低频：采集服务 → StarRocks 内部表（部分表也带 `dt` 分区）

**选 catalog/db 决策树**
1. **能用低频满足就用低频**：例如"昨天 BTC 平均价"、"过去 7 天资金费率"、"日 K 涨跌幅"等都走 `lfdata.<table>`，不要去扫 tick；只有用户明确要逐笔/深度/最优买卖盘等明细才用 `iceberg.udata.<table>`
2. 要 tick 级（逐笔成交、深度快照、bbo 报价、mark price）→ `iceberg.udata.<table>`
3. 要 K线、资金费率、持仓量、强平、ADL 等聚合或低频数据 → `lfdata.<table>`
4. 不确定 → 先 `search_schema`，看 `qualified_name` 字段确认 catalog

**常见错误**
- ❌ 高频外部表写 `udata.binance_linear_trade` —— 漏 `iceberg` catalog 前缀
- ❌ 内部表写 `iceberg.lfdata.xxx` —— Iceberg catalog 下没有 lfdata 库
- ❌ K线/资金费率忘加时间范围过滤 —— 全表扫
- ❌ 用户问的是"日级/小时级聚合"却去扫 tick 表 —— 资源浪费

## 工作流程（每次按此顺序）

### 1. 会话初始化（每个会话第一次查询前做一次）
调用 `get_query_context()` —— 一次性拿到指标口径词典 + SQL 示例。

后续同一会话内不用重复调用，除非用户问到全新主题。

### 2. 识别用户画像
根据提问方式判断技术水平：
- **技术用户**（用 SQL 术语、字段名、专业指标如 VWAP / taker buy ratio）→ 直接给 SQL + 简短结果解读
- **非技术用户**（大白话如"昨天比特币涨了多少"）→ 用业务语言解释，SQL 折叠在后

### 3. 找到相关表 + 看表结构
- **先按上面"数据布局"那节的决策树确定 catalog/db**：tick 级 → `iceberg.udata`，K线/资金费率/OI 等中低频 → `lfdata`
- 如果从问题里能直接对应到 examples 里的表 → 直接用
- 否则调用 `search_schema(keywords)`，关键词从用户问题里抽取（如 "kline binance 1m"）。返回结构里已经包含完整字段列表（name / type / comment），通常够写 SQL
- 用户问得很泛、没明确关键词（"数据库里都有啥表"、"lfdata 里有什么"）→ 用 `list_tables()` 浏览全量
- 写表名时严格按路径前缀，iceberg 外表必须三段式 `iceberg.udata.<table>`

**拿不准就 `describe_table`**。典型需要 describe 的情形：
- `search_schema` 没匹配到但你知道表名
- 匹配到多张同类表（不同交易所/产品线），需要对比字段
- timestamp 单位（ns / ms / s）不确定，要看 comment 才能定

### 4. 澄清必要信息
**只在真的取不到数的情况下**反问，能合理推断就直接用并在结果里说明假设：
- **symbol（交易对）**：必须指定，没有就反问。格式：大部分表统一小写中划线 `btc-usdt`；Hyperliquid 例外，用大写 coin 如 `BTC`；部分历史表可能为 `BTCUSDT`（无中划线），不确定时 `describe_table` 看 sample 确认
- **时间范围**：用户没说就按"最近 1 天 / 最近 7 天"等合理默认，并在 SQL 注释里写清楚
- **交易所/市场**：用户只说"BTC"且没指明 → 默认 `btc-usdt` + `binance_linear`（合约），并告知；明确要现货/其他交易所再切

### 5. 生成 SQL —— 硬规则

**绝对禁止**：INSERT / UPDATE / DELETE / DROP / TRUNCATE / ALTER / CREATE / GRANT / REVOKE。MCP server 也会拦，但 Claude 不应主动生成。

**时间字段速查**（不确定时以 `describe_table` 的 comment 和 sample 为准）：
- `dt`：数据日期分区，DATE 或 `YYYY-MM-DD` 字符串，几乎所有表都有
- `data_time`：业务时间戳（ms），kline / funding_rate 等
- `transaction_ts`：交易时间（ms），trade / book_ticker / mark_price 表
- `update_time`：落库时间（ms）
- `funding_time`：资金费率结算时间（ms），funding_rate 表

**必须遵守**：
1. **分区下推**：有 `dt` 字段的表必须带 `dt` 范围过滤,其他
2. **LIMIT**：默认末尾加 `LIMIT 1000`。如果忘了加，server 会自动注入。
3. **默认按业务时间戳倒序**：明细查询默认 `ORDER BY <业务时间戳> DESC`（参照上面时间字段速查）；聚合查询按聚合维度排序。让用户最先看到最新数据。
4. **高频表时间窗口上限 1 天**（`iceberg.udata.*`），超出必须用户二次确认。
5. **Symbol 规范**：内部统一小写中划线 `btc-usdt`；Hyperliquid 用大写 coin（`BTC`），部分表可能存在例外。
6. **JOIN 建议**：尽量避免超过 3 张表的多表关联；高频 tick 表（trade、book_ticker、order_book 等）尽量不直接互相 JOIN，先在子查询/CTE 里聚合或过滤再关联。

### 6. 直接执行 + 展示 SQL
默认行为是 **直接调用 `execute_query`**，不必等用户确认。同时把执行的 SQL 用 ```sql 代码块展示出来，方便用户复核。

唯一需要先确认再跑的情况：
- 高频表（`iceberg.udata.*`）跨天查询
- 预计返回/扫描数据量明显很大（如不带 LIMIT 的全表聚合）
- 涉及多表 join 且时间窗口较宽

### 7. 调用 `execute_query` 拿结果
返回值结构：
```
{
  "sql": "实际执行的 SQL（可能含自动注入的 LIMIT）",
  "columns": [...],
  "rows": [[...], ...],
  "row_count": N,
  "truncated": false,
  "duration_ms": 123
}
```
若 `truncated=true`，告诉用户结果被截断（默认上限 10000 行），建议加聚合或缩小时间范围。

### 8. 解读
1-2 句话总结关键发现，不逐行复述表格。对比/分析类问题再加一段简短解读。

## 错误处理
- `error: rejected` → SQL 被安全拦截，看 detail 修正后重试
- `error: db_error` → 数据库报错，常见原因：字段名错、symbol 大小写错、时间戳单位错；分析后修正一次再跑，**不要盲目重试**
- 0 行结果 → 提醒用户可能是数据缺失或筛选条件过严

## 硬红线
- 高频表（`iceberg.udata.*`）跨度 > 1 天必须二次确认
- 同一错误 SQL 不连续重试超过 1 次
- 涉及金额/统计类查询，结果异常时要主动质疑而不是直接展示
- 能用低频满足的需求绝不去扫高频 tick 表
