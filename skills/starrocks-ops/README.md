# starrocks-ops 安装指南

用**你本人的** StarRocks 账号跑 SQL（读写/DDL）的 Skill。

## 为什么不走 MCP
MCP 是**只读**共享账号，权限覆盖的是团队共享数据，遇到下列情况走本 skill：
- 任何写操作（DDL / DML）
- 访问个人账号能看但共享账号看不到的内部库
- 需要更长超时 / 更大返回量 / 本地落盘输出

---

## 安装（3 步）

### 1. 装 Skill

```bash
git clone https://github.com/UnicodeDigital/claude-skills.git /tmp/claude-skills
mkdir -p ~/.claude/skills
cp -r /tmp/claude-skills/skills/starrocks-ops ~/.claude/skills/
rm -rf /tmp/claude-skills
```

### 2. 装依赖

```bash
pip install pymysql
```

### 3. 写 `~/.env`

```bash
cat > ~/.env <<'EOF'
SR_HOST=127.0.0.1
SR_QUERY_PORT=9030
SR_USER=your_user
SR_PASSWORD=your_password
SR_DB=lfdata
EOF
chmod 600 ~/.env
```

必需配置：`SR_HOST` / `SR_USER` / `SR_PASSWORD`。其他可选。

---

## 用

Claude Code 里直接说话，Claude 会自动走 skill：

> 帮我在 `test` 库创建个t1表
> 帮我在test库的t1表写入几条测试数据


## 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `missing env key(s): SR_HOST` | 没找到 `~/.env` | 按第 3 步创建 |
| `No module named 'pymysql'` | 依赖没装 | `pip install pymysql` |
| `Access denied ... privilege` | 账号无权限 | 联系 DBA 授权，不要换账号绕 |
| `Can't connect to 127.0.0.1:9030` | SSH 隧道断了 | 重起隧道 |
| `exec "A; B"` 只跑 A | pymysql 单语句 | 改用 `-f file.sql` |
