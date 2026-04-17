---
name: starrocks-query
description: 通过自然语言查询公司 StarRocks 数据仓库（加密货币量化数据）。当用户询问行情、K线、订单簿、成交、资金费率、未平仓量 OI、强平、ADL 风险、CoinGlass 衍生指标、ETL 数据质量等需要从数据库取数的问题时使用此 skill。覆盖 Binance、Bitget、Bybit、OKX、Gate、Hyperliquid、CoinGlass、CoinGecko、CoinMarketCap 等交易所/数据源，包含 tick 级（Iceberg 外表）与 1m/1d/5m 聚合数据。本 skill 通过 starrocks MCP server 访问数据库。
---

# StarRocks 量化数据查询 Skill

## 前置条件
本 skill 依赖名为 `starrocks` 的 MCP server。如果 Claude 没有发现以下工具，请用户在 Claude Desktop/Code 设置里配置 MCP server。

可用 MCP 工具：
- `execute_query(sql)` —— 执行只读 SQL，返回结果
- `search_schema(keywords)` —— **用关键词匹配字段名和字段注释**（多个关键词 AND 逻辑），返回命中表的完整 schema。用于不确定目标信息落在哪张表时。
- `describe_table(table)` —— 单表完整 schema以及三条sample数据
- `list_databases()` —— 所有库
- `get_query_context()` —— 指标口径词典 + 全量表清单 + SQL 示例；

## 数据布局（Catalog / Database / 路由规则）

StarRocks 是统一查询入口。底下挂两个 catalog：

| Catalog | 类型 | 数据库 | 装什么 | 查询路径 |
|---|---|---|---|---|
| `default_catalog` | StarRocks 内部表 | `lfdata` | 中低频数据：资金费率、持仓量、K线、聚合指标、强平、ADL 等 | `lfdata.<table>` |
| `iceberg` | Iceberg 外表（NAS/S3 Parquet, zstd） | `udata` | 高频 tick 类数据（逐笔成交、盘口、订单簿、标记价等；） | `iceberg.udata.<table>`（**三段式必须带 catalog 前缀**） |

**路由规则**：能用低频满足就用低频；只有明确要逐笔/盘口/订单簿等明细才走 `iceberg.udata`

**数据链路**
- 高频：Exchange WebSocket → Kafka → Flink ETL → Iceberg (按 `dt` UTC 天分区) → StarRocks Iceberg Catalog
- 中低频：采集服务 → StarRocks 内部表（部分表也带 `dt` 分区）


## 工作流程（每次按此顺序）

### 1. 会话初始化（每个会话第一次查询前做一次）
调用 `get_query_context()` —— 一次性拿到**全量表清单**、指标口径词典、SQL 示例。表清单已覆盖所有库。

后续同一会话内不用重复调用，除非用户问到全新主题。

### 2. 识别用户画像
根据提问方式判断技术水平：
- **技术用户**（用 SQL 术语、字段名、专业指标如 VWAP / taker buy ratio）→ 直接给 SQL + 简短结果解读
- **非技术用户**（大白话如"昨天比特币涨了多少"）→ 用业务语言解释，SQL 折叠在后

### 3. 找表

按顺序，能在前一步搞定就不用进下一步：

1. **`get_query_context()` 表清单**：初始化时已拿到全量表名 + comment，按交易所/产品/数据类型对应，大部分情况够用
2. **`search_schema(keywords)`**：表清单对应不上时，用字段名或业务术语反查——英文命中字段名（`funding_rate` / `taker_buy`），中文命中注释（"资金费率" / "强平"）
3. **`describe_table`**：字段含义/单位/symbol 格式拿不准时，看完整 schema + 3 条 sample

iceberg 外表必须三段式 `iceberg.udata.<table>`。

### 4. 澄清必要信息
**只在真的取不到数的情况下**反问，能合理推断就直接用并在结果里说明假设：
- **时间范围**：用户没说就按"最近 1 天 / 最近 3 天"等合理默认，并在 SQL 注释里写清楚
- **交易所/市场**：默认binance linear,如用户只说"BTC"且没指明 → 默认 `btc-usdt` + `binance_linear`（合约），并告知；明确要现货/其他交易所再切
- **symbol范围**：高频表数据量较大,避免全symbol跨多天查询。

### 5. 生成 SQL —— 硬规则

**绝对禁止**：INSERT / UPDATE / DELETE / DROP / TRUNCATE / ALTER / CREATE / GRANT / REVOKE。MCP server 也会拦，但 Claude 不应主动生成。

**时间字段命名规律**（具体字段名因表而异，不确定时以 `describe_table` 的 comment 和 sample 为准）：
- `dt`：UTC 日期分区键，DATE 或 `YYYY-MM-DD` 字符串，大部分表都有 —— SQL 必带的分区过滤条件
- 以 `_ts` 结尾的 bigint 字段：时间戳数值。**tick 高频表统一纳秒**；K线 / 资金费率 / 其他低频表统一毫秒
- 以 `_tm` / `_time` 结尾的 datetime 字段：业务时间或落库时间，UTC
- `update_time` / `create_time`：通常是 ETL 落库/更新时间，不是业务时间


**必须遵守**：
1. **分区下推**：有 `dt` 字段的表必须带 `dt` 范围过滤
2. **LIMIT**：默认末尾加 `LIMIT 100`。如果忘了加 LIMIT，server 会自动注入。
3. **默认按业务时间戳倒序**：明细查询默认 `ORDER BY <业务时间戳> DESC`（参照上面时间字段速查）；聚合查询按聚合维度排序。让用户最先看到最新数据。
4. **高频表时间窗口尽量限制 1 天内**（`iceberg.udata.*`），超出必须用户二次确认。
5. **Symbol 规范**：内部统一小写中划线 `btc-usdt`；部分表可能同时有 `symbol`（原始如 `BTCUSDT`）和 `symbol_us`（内部 `btc-usdt`）两套字段，JOIN / WHERE 要对齐。不确定时 `describe_table` 看 sample。
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
- `error: db_error` → 字段名错、symbol 大小写错、时间戳单位错；修正一次再跑，**同一错误重试不超过 2 次**
- `db_error: timeout` → 查询超时（MCP 默认限制 30s）；缩小时间范围、加过滤条件，或改用预聚合表；**不要原样重试**
- 0 行结果 → 提醒用户数据缺失或筛选过严
- 金额/统计类结果异常时主动质疑，不要直接展示
- Iceberg 外表漏 `iceberg` 前缀（写成 `udata.xxx`，正确是 `iceberg.udata.xxx`）
- 内部表写 `iceberg.lfdata.xxx` —— Iceberg catalog 下没有 lfdata 库
- 忘加时间范围过滤 —— 全表扫