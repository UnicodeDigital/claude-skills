#!/usr/bin/env python3
"""收集本机 Claude Code 会话信息（只读），输出 JSON 供整理成表格。

数据来源：
  ~/.claude/sessions/<pid>.json            运行中进程的注册信息（含 name、cwd、入口）
  ~/Library/Application Support/Claude/claude-code-sessions/*/*/local_<hostId>.json
                                            桌面版侧边栏里的会话（含归档状态、标题）
  ~/.claude/projects/<编码后的cwd>/<sessionId>.jsonl
                                            对话记录

用法：
  collect.py                       运行中 + 桌面版侧边栏里的全部会话
  collect.py --cwd ~/test          只要 cwd 在某目录下（含子目录）的
  collect.py --archived            只要桌面版里已归档的（可与 --cwd 同用）
  collect.py --history --since 30  另外加上 30 天内有记录、但既没运行也不在桌面版里的 CLI 历史会话
  collect.py --tail <sessionId或前缀> [N] [宽度]   打印该会话最近 N 条真正的对话（默认 10 条，每条截到 300 字，宽度 0 不截）
"""
import argparse, glob, json, os, subprocess, sys, time
from datetime import datetime

HOME = os.path.expanduser('~')
REG_DIR = os.path.join(HOME, '.claude', 'sessions')
PROJ_DIR = os.path.join(HOME, '.claude', 'projects')
DESK_DIR = os.path.join(HOME, 'Library', 'Application Support', 'Claude', 'claude-code-sessions')
SCRATCH_MARK = '/Library/Application Support/Claude/scratch-workspaces/'

TAIL_BYTES = 4 * 1024 * 1024
HEAD_BYTES = 1 * 1024 * 1024
SKIP_PREFIX = ('<', '[', 'This session is being continued', 'Another Claude session',
               'Base directory for this skill', 'Caveat:')
NOISE = ('<system-reminder', '<cross-session-message', '<task-notification', '<command-',
         '<local-command', '<agent-message', 'Base directory for this skill',
         'This session is being continued', 'Another Claude session', '[Request interrupted',
         '[Image', 'Caveat:')


def pid_command(pid):
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError, OSError):
        return None
    try:
        return subprocess.run(['ps', '-o', 'command=', '-p', str(pid)],
                              capture_output=True, text=True).stdout.strip() or None
    except Exception:
        return None


def ancestor_pids():
    """当前进程的所有祖先 PID，用来认出“调用这个脚本的会话”。"""
    seen, pid = set(), os.getpid()
    while pid > 1 and pid not in seen:
        seen.add(pid)
        try:
            pid = int(subprocess.run(['ps', '-o', 'ppid=', '-p', str(pid)],
                                     capture_output=True, text=True).stdout.strip() or 0)
        except ValueError:
            break
    return seen


def load_registry():
    """运行中的进程。PID 可能被复用，所以还要核对命令行里有 claude。"""
    out = []
    for p in glob.glob(os.path.join(REG_DIR, '*.json')):
        try:
            o = json.load(open(p))
        except Exception:
            continue
        cmd = pid_command(o.get('pid', -1))
        if not cmd or 'claude' not in cmd.lower():
            continue
        out.append(o)
    return out


def load_desktop():
    out = []
    for p in glob.glob(os.path.join(DESK_DIR, '*', '*', 'local_*.json')):
        try:
            out.append(json.load(open(p)))
        except Exception:
            pass
    return out


def find_transcript(sid):
    """不用 shell glob：项目目录名以 '-' 开头，交给 ls 会被当成参数。"""
    hits = []
    try:
        dirs = os.listdir(PROJ_DIR)
    except FileNotFoundError:
        return []
    for d in dirs:
        f = os.path.join(PROJ_DIR, d, sid + '.jsonl')
        if os.path.isfile(f):
            hits.append(f)
    return hits


def read_lines(path, head):
    size = os.path.getsize(path)
    with open(path, 'rb') as fh:
        if head:
            data = fh.read(HEAD_BYTES)
        else:
            fh.seek(max(0, size - TAIL_BYTES))
            data = fh.read()
    lines = data.decode('utf-8', 'ignore').splitlines()
    # 截断处的首行/末行可能不完整，json 解析失败会被跳过
    for l in lines:
        try:
            yield json.loads(l)
        except Exception:
            continue


def text_of(o):
    m = o.get('message')
    c = m.get('content') if isinstance(m, dict) else None
    if isinstance(c, str):
        return c.strip()
    if isinstance(c, list):
        if any(isinstance(x, dict) and x.get('type') == 'tool_result' for x in c):
            return ''
        return ' '.join(x.get('text', '') for x in c
                        if isinstance(x, dict) and x.get('type') == 'text').strip()
    return ''


def scan_transcript(path):
    """首尾各读一段：fork 的记录开头是继承来的父会话历史，里面的 sessionId 也是父会话的，
    所以不要按 sessionId 过滤，而是按时间戳排序取最近的消息。"""
    info = {'first_user': [], 'recent_user': [], 'recent_assistant': [],
            'last_msg_at': None, 'title': None}
    for o in read_lines(path, head=True):
        if o.get('type') == 'user' and not o.get('isMeta') and not o.get('isSidechain'):
            t = text_of(o)
            if t and not t.startswith(SKIP_PREFIX):
                info['first_user'].append(t.replace('\n', ' ')[:160])
                if len(info['first_user']) >= 3:
                    break
    us, as_ = [], []
    for o in read_lines(path, head=False):
        ty = o.get('type')
        if ty in ('custom-title', 'ai-title'):
            info['title'] = o.get('customTitle') or o.get('aiTitle') or info['title']
        if ty not in ('user', 'assistant') or o.get('isSidechain'):
            continue
        ts = o.get('timestamp') or ''
        t = text_of(o)
        # 压缩摘要、系统提醒、跨会话同步等不是对话，不算活跃
        if not t or o.get('isMeta') or o.get('isCompactSummary') or t.lstrip().startswith(NOISE):
            continue
        if ty == 'user':
            us.append((ts, t.replace('\n', ' ')[:200]))
        else:
            as_.append((ts, t.replace('\n', ' ')[:240]))
        if ts and (info['last_msg_at'] is None or ts > info['last_msg_at']):
            info['last_msg_at'] = ts
    us.sort(); as_.sort()
    info['recent_user'] = [t for _, t in us[-5:]]
    info['recent_assistant'] = [t for _, t in as_[-2:]]
    return info


def fmt_size(n):
    for unit in ('B', 'K', 'M', 'G'):
        if n < 1024 or unit == 'G':
            return f'{n:.0f}{unit}' if unit in ('B', 'K') else f'{n:.1f}{unit}'
        n /= 1024


def to_local(ms_or_iso):
    if ms_or_iso is None:
        return None
    if isinstance(ms_or_iso, (int, float)):
        return datetime.fromtimestamp(ms_or_iso / 1000)
    try:
        return datetime.fromisoformat(ms_or_iso.replace('Z', '+00:00')).astimezone().replace(tzinfo=None)
    except Exception:
        return None


def short_cwd(cwd):
    if not cwd:
        return cwd
    if SCRATCH_MARK in cwd:
        return 'scratch/…' + cwd.rsplit('scratch-', 1)[-1][-17:]
    return cwd.replace(HOME, '~', 1) if cwd.startswith(HOME) else cwd


def tail_dialog(sid, n, width=300):
    """打印某个会话最近 n 条真正的对话（去掉系统提醒、跨会话同步、任务通知、技能正文、压缩摘要）。"""
    tps = find_transcript(sid)
    if not tps:  # 允许只给前缀，比如 a68ceac5
        tps = [os.path.join(PROJ_DIR, d, f) for d in os.listdir(PROJ_DIR)
               if os.path.isdir(os.path.join(PROJ_DIR, d))
               for f in os.listdir(os.path.join(PROJ_DIR, d)) if f.startswith(sid) and f.endswith('.jsonl')]
    if not tps:
        sys.exit(f'找不到会话 {sid} 的对话记录')
    rows = []
    for o in read_lines(max(tps, key=os.path.getsize), head=False):
        ty = o.get('type')
        if ty not in ('user', 'assistant') or o.get('isSidechain') or o.get('isMeta'):
            continue
        t = text_of(o)
        if not t or o.get('isCompactSummary') or t.lstrip().startswith(NOISE):
            continue
        rows.append((o.get('timestamp') or '', '用户' if ty == 'user' else 'Claude', t.replace('\n', ' ')))
    rows.sort()
    for ts, who, t in rows[-n:]:
        lt = to_local(ts)
        print(f"[{lt.strftime('%m-%d %H:%M') if lt else '?'}] {who}: "
              + (t if width <= 0 or len(t) <= width else t[:width] + '…'))


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == '--tail':
        a = sys.argv[2:]
        tail_dialog(a[0], int(a[1]) if len(a) > 1 else 10, int(a[2]) if len(a) > 2 else 300)
        return
    ap = argparse.ArgumentParser()
    ap.add_argument('--cwd', help='只保留 cwd 在此目录下（含子目录）的会话')
    ap.add_argument('--history', action='store_true', help='加上不在运行、也不在桌面版里的 CLI 历史会话')
    ap.add_argument('--since', type=int, default=30, help='--history 时只看最近 N 天（默认 30）')
    ap.add_argument('--archived', action='store_true', help='只列桌面版里已归档的会话')
    args = ap.parse_args()

    reg = load_registry()
    anc = ancestor_pids()
    me = next((o['sessionId'] for o in reg if o.get('pid') in anc), '')
    desk = load_desktop()
    host2cli = {d.get('sessionId'): d.get('cliSessionId') for d in desk}

    S = {}  # cli sessionId -> record

    def rec(sid):
        return S.setdefault(sid, {'sessionId': sid, 'pids': [], 'entry': set(), 'name': None,
                                  'cwd': None, 'desktop': None, 'state': None})

    for o in reg:
        r = rec(o['sessionId'])
        r['pids'].append({'pid': o['pid'], 'entry': 'CLI' if o.get('entrypoint') == 'cli' else '桌面版',
                          'status': o.get('status'), 'tmux': o.get('tmux')})
        r['name'] = r['name'] or o.get('name')
        r['cwd'] = o.get('cwd')
    for d in desk:
        sid = d.get('cliSessionId')
        if not sid:
            continue
        r = rec(sid)
        r['desktop'] = {'hostId': d.get('sessionId'), 'archived': bool(d.get('isArchived')),
                        'title': d.get('title'),
                        'lastActivity': d.get('lastActivityAt') or d.get('createdAt'),
                        'summary': (d.get('postTurnSummary') or {}).get('status_detail'),
                        'forkedFrom': host2cli.get(d.get('forkedFromSessionId'))}
        r['cwd'] = r['cwd'] or d.get('cwd')
    if args.history:
        cutoff = time.time() - args.since * 86400
        for d in os.listdir(PROJ_DIR):
            for f in glob.glob(os.path.join(PROJ_DIR, glob.escape(d), '*.jsonl')):
                if os.path.getmtime(f) >= cutoff:
                    rec(os.path.basename(f)[:-6])

    out = []
    for sid, r in S.items():
        tps = find_transcript(sid)
        tp = max(tps, key=os.path.getsize) if tps else None
        info = scan_transcript(tp) if tp else {}
        if r['cwd'] is None and tp:
            for o in read_lines(tp, head=False):
                if o.get('cwd'):
                    r['cwd'] = o['cwd']
        if r['pids']:
            state = 'running'
        elif r['desktop'] and r['desktop']['archived']:
            state = 'archived'
        elif r['desktop']:
            state = 'paused'   # 在桌面版侧边栏里，但没有进程（未打开过或被桌面版暂停）
        else:
            state = 'history'  # 只有对话记录
        name = r['name'] or (r['desktop'] or {}).get('title') or info.get('title')
        # 上次活跃 = 最后一条对话消息的时间。桌面版的 lastActivityAt 在重开会话、导入时也会被刷新，
        # 不代表有新对话，只作为没有消息时的兜底，并单独输出
        desk_act = to_local((r['desktop'] or {}).get('lastActivity'))
        last = to_local(info.get('last_msg_at')) or desk_act or \
            (datetime.fromtimestamp(os.path.getmtime(tp)) if tp else None)
        scratch = None
        if r['cwd'] and SCRATCH_MARK in r['cwd']:
            files = [os.path.join(dp, f) for dp, _, fs in os.walk(r['cwd']) for f in fs] if os.path.isdir(r['cwd']) else []
            scratch = {'files': len(files), 'size': fmt_size(sum(os.path.getsize(f) for f in files)),
                       'names': [os.path.basename(f) for f in files[:8]]}
        warn = []
        if len(r['pids']) > 1:
            warn.append(f"同一会话挂在 {len(r['pids'])} 个进程上，可能互相覆盖记录")
        if len(tps) > 1:
            warn.append('对话记录在多个项目目录下各有一份：' + ', '.join(os.path.basename(os.path.dirname(x)) for x in tps))
        if r['cwd'] and not os.path.isdir(r['cwd']):
            warn.append('cwd 目录已不存在，桌面版打开时会自动 fork')
        out.append({
            'sessionId': sid,
            'isCurrent': sid == me,
            'name': name,
            'cwd': r['cwd'],
            'cwdShort': short_cwd(r['cwd']),
            'state': state,
            'pids': r['pids'],
            'transcript': tp,
            'size': fmt_size(os.path.getsize(tp)) if tp else None,
            'lastActive': last.strftime('%Y-%m-%d %H:%M') if last else None,
            'desktopActivity': desk_act.strftime('%Y-%m-%d %H:%M') if desk_act else None,
            'scratchFiles': scratch,
            'forkedFrom': (r['desktop'] or {}).get('forkedFrom'),
            'desktopHostId': (r['desktop'] or {}).get('hostId'),  # 桌面版日志和侧边栏配置里用的是这个 ID
            'desktopSummary': (r['desktop'] or {}).get('summary'),
            # fork 的开头是继承来的父会话历史，对概括这个 fork 没有帮助
            'firstUser': [] if (r['desktop'] or {}).get('forkedFrom') else info.get('first_user', []),
            'recentUser': info.get('recent_user', []),
            'recentAssistant': info.get('recent_assistant', []),
            'warnings': warn,
        })

    if args.archived:
        out = [x for x in out if x['state'] == 'archived']
    if args.cwd:
        pre = os.path.realpath(os.path.expanduser(args.cwd)).rstrip('/')
        out = [x for x in out if x['cwd'] and (x['cwd'] == pre or x['cwd'].startswith(pre + '/'))]

    order = {'running': 0, 'paused': 1, 'history': 2, 'archived': 3}
    out.sort(key=lambda x: (not x['isCurrent'], order[x['state']], -(datetime.strptime(x['lastActive'], '%Y-%m-%d %H:%M').timestamp() if x['lastActive'] else 0)))
    json.dump({'scannedAt': datetime.now().strftime('%Y-%m-%d %H:%M'),
               'desktopRunCap': 12, 'sessions': out}, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
