# starrocks-query 安装指南

## 1. 获取凭证

- **Server URL**：`http://162.128.159.166:9130/mcp`
- **你的个人 Token**：联系@杜壮壮获取

---

## 2. 添加 MCP Server

### Claude Code（终端）

```bash
claude mcp add --transport http starrocks http://162.128.159.166:9130/mcp --header "Authorization: Bearer <你的-token>"
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

```bash
# 1. Clone 公司 skills 仓库
git clone https://github.com/UnicodeDigital/claude-skills.git /tmp/claude-skills

# 2. 复制 starrocks-query skill
mkdir -p ~/.claude/skills
cp -r /tmp/claude-skills/skills/starrocks-query ~/.claude/skills/

# 3. 清理
rm -rf /tmp/claude-skills
```

---

## 4. 验证

### 检查 MCP 连接

```bash
claude mcp list
```

输出里应该能看到 `starrocks` 及其 URL。

### 使用 Skill

在 Claude Code 中输入 `/starrocks-query` 激活 skill，然后直接提问：

> 昨天 btc-usdt 永续涨了多少？

---

## 常见问题

| 现象 | 原因 | 解决                                      |
|---|---|-----------------------------------------|
| Claude 说找不到 MCP 工具 | MCP 没连上 | 检查配置里的 url 和 token，重启客户端                |
| 401 / unauthorized | Token 错了 | 确认 token 前面有 `Bearer `（注意空格）            |
| SQL 跑了但 0 行 | 数据没到或 symbol 格式不对 | 让 Claude 用 `describe_table` 看 sample 确认 |
| 超时 | SQL 太重 | 缩小时间范围，或让 Claude 改用小表                   |
