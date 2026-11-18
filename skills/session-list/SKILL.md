---
name: session-list
description: 用户想看本机开了哪些 Claude Code 会话时使用：列出 / 扫描 / 整理会话，问某个目录下有哪些 session、哪些在运行、哪些可以删、归档了哪些（单独列出已归档的会话、找回或恢复归档的会话），或者要 sessionId、session name、cwd、PID 之类的会话信息。包括终端 CLI 会话和 Claude 桌面版里的会话。即使用户只说“看看我开了哪些 session”“再扫描一下”“哪些会话能删”“我归档了哪些”“归档的会话去哪了”也要用。
---

# 会话清单

用一张固定格式的表，把本机的 Claude Code 会话交代清楚：在不在运行、在哪个目录、聊的是什么、留着还是删。

## 第 1 步：收集（只读）

```bash
python3 -I ~/.claude/skills/session-list/scripts/collect.py [--cwd ~/test] [--history --since 30] > <scratchpad>/sessions.json
```

- 默认范围：运行中的进程 + 桌面版侧边栏里的全部会话（含已归档）
- 用户限定了目录（“test 下的”）才加 `--cwd`；说“全部”就不加
- 用户只问已归档的（“归档了哪些”“归档的会话在哪”）加 `--archived`，只输出已归档的会话；可以和 `--cwd` 一起用
- “全部”指正在用的会话，**不含** `--history`。只有用户问到“以前在终端开过的 / 历史会话”才加，没加时在备注里提一句可以再扫
- 用户说“再看 / 再扫描”：重新跑脚本，不要复用上一次的结果，会话状态变得很快

输出字段：`state`（running / paused / archived / history）、`pids`、`size`、`lastActive`（最后一条对话的时间）、`desktopActivity`、`scratchFiles`、`forkedFrom`、`desktopSummary`、`firstUser`、`recentUser`、`recentAssistant`、`warnings`、`isCurrent`。

字段不够判断时，看某个会话最近的真实对话（已滤掉系统提醒、跨会话同步、任务通知等噪音）：

```bash
python3 -I ~/.claude/skills/session-list/scripts/collect.py --tail <sessionId或前缀> 15
```

## 第 2 步：写简介和建议

**一句话简介**：根据 `desktopSummary`、`firstUser`、`recentUser`、`recentAssistant` 概括“做了什么、做到哪”，一句话，中文。
- fork 出来的会话：`recentUser` 常常为空（它自己的消息多是同步通知或图片），以 `recentAssistant` 和 `desktopSummary` 为准，并写明“X 的 fork”
- 信息不够就用 `--tail` 多看几条，别瞎编
- 留意还没了结的事（“等你给 chat_id”“X 删不删待定”），写进简介

**建议**：从上往下，命中第一条就停，后面写一句理由：
1. `isCurrent` 或正在运行 → **保留**
2. 还有待办或待定事项 → **保留**或**看情况**，写明是什么事
3. `scratchFiles.files > 0` → **先把文件存出来，再删**，列出文件名
4. 已归档且没有新内容的 fork、没有对话记录的空条目 → **可删**
5. `lastActive` 距扫描时刻（`scannedAt`）不到 7×24 小时 → **保留**
6. 以后还可能接着做 → **看情况**。判断标准：对话里说过会再回来（“有新点子再找你”），或者是持续开发的代码项目，或者是工作已同步回主会话的 fork
7. 其余已经做完的一次性问答或任务 → **可删**

时间一律看 `lastActive`，它已经排除了压缩摘要和系统消息。`desktopActivity` 会在重开桌面版时被刷新，不代表有新对话，不要拿它判断。

## 第 3 步：输出

按这个列顺序输出一张表，不要增删列：

| # | sessionId | session name | cwd | PID / 入口 | 记录大小 | 一句话简介 | 建议 | 上次活跃时间 |
|---|---|---|---|---|---|---|---|---|

- sessionId 写完整，用反引号括起来；cwd 用 `cwdShort`
- PID / 入口：运行中写 `56715 CLI` 或 `66971 桌面版`，多个进程都列出；其他状态写 `暂停 · 桌面版`、`已归档 · 桌面版`、`仅记录 · CLI`
- 排序沿用脚本输出：当前会话在最前，然后是运行中、暂停、仅记录、已归档，同组内按上次活跃时间从新到旧
- 上次活跃时间写 `MM-DD HH:MM`

表后先写一行汇总（保留 / 看情况 / 可删各几个），再写有内容的备注：
- `warnings` 里的每一条（同一会话挂在多个进程上、cwd 已不存在、记录在多个项目目录下各有一份）
- 桌面版有暂停会话时，说明一次：桌面版最多同时运行 12 个会话进程，空闲的会被自动暂停，点开就能恢复，上下文不丢
- 有 fork 时说明一次：fork 的记录大小包含从父会话继承来的历史，所以和父会话差不多大
- `scratch/…` 的完整路径前缀：`~/Library/Application Support/Claude/scratch-workspaces/<账号>/<组织>/scratch-日期-xxxx`

## 已归档的会话

- 默认清单里已归档的会话排在最后；只看归档的用 `--archived`，表格格式不变，建议列照第 2 步的规则写。
- 一个都没有时，直接说“没有已归档的会话”，不出空表。
- 表后说明一次在哪里找：侧边栏按分组分块显示时（自建分组、Recents 各占一块），已归档的会话不在侧边栏里，搜索也搜不到；桌面版把它们放在单独的会话页（Sessions page）里。所以最省事的是让我恢复。
- 恢复：用户点名要恢复某个会话时，用 `mcp__ccd_session_mgmt__unarchive_session`（延迟加载，先 ToolSearch），参数是该会话的 `desktopHostId`（`local_…`）。恢复后它回到原来的分组。只恢复用户点名的，不顺手恢复别的。
- 链接：会话名写成 `[标题](#<desktopHostId>)`，用户能直接点开。

## 不要做的

- **只列不删。** 归档和恢复都只在用户点名时做。用户要删会话时，让用户在桌面版侧边栏里右键删除；自己动手删需要先退出桌面版，属于另一件事
- 不要用 `ls ~/.claude/projects/*` 这类 shell 通配：项目目录名以 `-` 开头，会被当成参数
- 不要按 sessionId 过滤 fork 的消息：fork 继承来的历史沿用父会话的 sessionId
- 不要只用 `kill -0` 判断进程是否存活：PID 会被复用，脚本已经核对过命令行
