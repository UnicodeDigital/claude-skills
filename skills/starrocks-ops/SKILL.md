---
name: starrocks-ops
description: 用**人账号操作数据库** 建表/改字段/删表、INSERT/UPDATE/DELETE、数据修复，也包含个人权限下的 SELECT / COUNT / SHOW CREATE 等查看。通过 skill 目录下的 `scripts/sr.py` 调用，读取 `~/.env`。
allowed-tools: Bash(python3 *)
---

# StarRocks Ops Skill

## 前置
1. Skill 目录在 `~/.claude/skills/starrocks-ops/`（内含 `scripts/sr.py`）
2. `~/.env` 含 `SR_HOST` / `SR_USER` / `SR_PASSWORD`
3. `pip install pymysql`

脚本报 `missing env key(s): SR_HOST` 或 `No module named 'pymysql'` 时引导用户按 README.md 装好再继续。

## 为什么不走 MCP
团队 `starrocks` MCP 是**只读**共享账号，权限覆盖的是团队共享数据（`lfdata` / `iceberg.udata` 等）。遇到下列情况走本 skill：
- 任何写操作（DDL / DML）
- 访问个人账号能看但共享账号看不到的内部库
- 需要更长超时 / 更大返回量 / 本地落盘输出

## 数据布局（Catalog / 内部表 vs Iceberg 外表）

| Catalog | 类型 | 典型库 | 装什么 | 引用路径 | 写/DDL |
|---|---|---|---|---|---|
| `default_catalog` | StarRocks 内部表（OLAP） | `lfdata` + 个人/业务库 | 中低频聚合、维度、账户/交易相关 | `<db>.<table>` | ✅ 全部 DDL/DML |
| `iceberg` | Iceberg 外表（NAS/S3 Parquet + zstd） | `udata` | 高频 tick（逐笔成交、盘口、订单簿、标记价） | `iceberg.<db>.<table>`（三段式必带 `iceberg` 前缀） | ❌ **只读** |

**`iceberg.*` 从 StarRocks 侧一律只读**：禁止 `CREATE` / `INSERT` / `UPDATE` / `DELETE` / `DROP` / `ALTER` 等任何写入或 DDL。Iceberg 的写入和 DDL 走 **Spark / Flink**（日常数据生产归上游 Flink ETL，一次性建表/改 schema/compaction 走 Spark），StarRocks 只消费。跨 catalog 读 Iceberg 写入内部表（`INSERT INTO default_catalog.x SELECT ... FROM iceberg.y`）是允许的，注意 tick 表一天几十 G。

## CLI 接口

| 子命令 | 用途 |
|---|---|
| `dbs` | SHOW DATABASES |
| `tables <db>` | SHOW TABLES FROM db |
| `show <db>.<table>` | SHOW CREATE TABLE |
| `count <db>.<table>` | SELECT COUNT(*) |
| `query "<SQL>"` | 任意 SELECT，`--json` 可出 JSON |
| `exec "<SQL>"` | 执行 DDL/DML（直接生效） |
| `exec -f file.sql` | 从文件读多条（分号分隔） |

通用 flag：`--env <path>` / `--db <name>` / `--json`

## 安全硬规则

1. 只读子命令（`dbs` / `tables` / `show` / `count` / `query`）可直接执行。**`exec` 子命令会直接生效（DDL: `CREATE` / `ALTER` / `DROP` / `TRUNCATE`；DML: `INSERT` / `UPDATE` / `DELETE`），调用前必须把完整 SQL 发在 chat 里给用户审，用户点头才 `exec`**
2. 破坏性关键字（`DROP TABLE/DATABASE/VIEW/INDEX/PARTITION` / `TRUNCATE` / 无 WHERE 的 `DELETE` / `ALTER ... DROP COLUMN|PARTITION`）CLI 会交互二次确认，不要加 `--force` 绕过
3. 不回显 `SR_PASSWORD`（不要 `cat .env` / `echo $SR_PASSWORD` / `env | grep SR`）
4. 迁移/批量改表后用 `count` 对比源 + 目标，列表给用户
5. 改 schema 前先 `show` 拿当前定义再改，别盲改
6. 跨库操作用三段命名 `db.table`，避免默认库错位
7. 多条语句走 `-f file.sql`；pymysql 单语句，`exec "A; B"` 会静默只跑 A
8. 破坏性操作失败不要自动重试，先给用户看错误

## 建表尺寸规则

起 `CREATE TABLE` 先估数据量再定分区/分桶。**对已有表用 `SHOW DATA FROM <db>.<table>` 看真实磁盘占用**（`COUNT(*)` 不反映大小，行宽差异大的表会误判）；分区级用 `SHOW PARTITIONS FROM <db>.<table>`。新表只能问用户估（"预估总量 / 日增量 / 历史起点"）。

**分桶（BUCKETS）**
- 目标：单 bucket ~200MB
- 规则：`BUCKETS ≈ ceil(单分区数据量 / 200MB)`；不分区的表按全表数据量估
- **最小 8**：即使表很小也不低于 8
- 不要无脑填超大 bucket 数，空 bucket 浪费元数据

**分区（PARTITION BY）**
- 小表/维度表/配置表（总量 < 1G 且缓增）：不分区
- 历史数据多 / 持续写入的时序表：按月分区 `date_trunc('month', <time_col>)`，单分区 ≤ 10G
- 单分区接近 10G → 改按天/按周

| 场景 | 数据量 | PARTITION | BUCKETS |
|---|---|---|---|
| 维度表 | < 10MB | 不分区 | 8（下限） |
| 账户快照表（2 亿行） | ~50G、按月分 | 月分区 | 12–16 |
| 日频 K 线 | 每月 ~1.5G | 月分区 | 8 |
| Tick 成交（Iceberg 外表） | 每天几十 G | 天分区 | - |

## 错误处理
- `Access denied ... privilege` → 账号没权限，让用户联系管理员。
- `Unknown database` → 用 `dbs` 确认库名
- `Table already exists` → 用户决定 DROP 重建还是改 `CREATE IF NOT EXISTS`
- pymysql 超时 → CLI 已设 2h query_timeout；还超说明 SQL 有问题，不要盲目重试

## 和 starrocks-query 的分工
- 常规查数据、调研、团队共享口径 → `starrocks-query`（MCP，只读）
- 改结构 / 搬数据 / 修数据 / 访问个人数据 / MCP 权限够不到的查询 → `starrocks-ops`（CLI）
