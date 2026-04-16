# starrocks-query 安装指南

## 1. 获取凭证

- **Server URL**：`http://162.128.159.166:9130/mcp`
- **你的个人 Token**：联系@杜壮壮获取

---

## 2. 添加 MCP Server

### Claude Code（终端）

```bash
claude mcp add starrocks \
  --transport http \
  --url http://162.128.159.166:9130/mcp \
  --header "Authorization: Bearer <你的-token>"
```

添加后 Claude Code 下次启动会自动连接。

### Claude Desktop

打开 Claude Desktop → Settings → Developer → Edit Config，添加starrocks的 mcpServers：

```json
{ 
  "preferences": {...},
  "mcpServers": {
    "starrocks": {
      "transport": {
        "type": "streamable_http",
        "url": "http://162.128.159.166:9130/mcp",
        "headers": {
          "Authorization": "Bearer <你的-token>"
        }
      }
    }
  }
}
```

把 `<你的-token>` 替换为实际 token，保存后重启 Claude Desktop。

---

## 3. 安装 Skill

把 `starrocks-query` 目录放到 Claude 的 skills 目录下（二选一）：

```bash
# 方式一：软链接（推荐，方便后续 git pull 更新）
ln -s /path/to/starrocks-mcp/starrocks-query ~/.claude/skills/starrocks-query

# 方式二：直接拷贝
cp -r /path/to/starrocks-mcp/starrocks-query ~/.claude/skills/starrocks-query
```

> Claude Desktop 和 Claude Code 共用同一个 `~/.claude/skills/` 目录，装一次两边都能用。

---

## 4. 验证

### 检查 MCP 连接

```bash
claude mcp list
```

输出里应该能看到 `starrocks` 及其 URL。

### 试一条查询

打开 Claude Desktop 或在终端启动 `claude`，直接问：

> 昨天 btc-usdt 永续涨了多少？

Claude 会自动调用 MCP 工具查数据库并返回结果。如果报错看下面排障。

---

## 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| Claude 说找不到 MCP 工具 | MCP 没连上 | 检查配置里的 url 和 token，重启客户端 |
| 401 / unauthorized | Token 错了 | 确认 token 前面有 `Bearer `（注意空格） |
| SQL 跑了但 0 行 | 数据没到或 symbol 格式不对 | 让 Claude 用 `describe_table` 看 sample 确认 |
| 超时 | SQL 太重 | 缩小时间范围，或让 Claude 改用聚合表 |
