#!/usr/bin/env python3
"""
sr — StarRocks 个人账号 CLI（读写）。

连接配置从 .env 文件读取（不要入 git）。查找顺序：
  1. --env <path>
  2. ~/.env

需要的 key：
  SR_HOST=...
  SR_USER=...
  SR_PASSWORD=...
  SR_QUERY_PORT=9030      # 可选，默认 9030
  SR_DB=information_schema # 可选，默认 information_schema

shell 里已 export 的同名变量优先生效，便于临时覆盖。
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import pymysql
except ImportError:
    sys.stderr.write("missing dependency: pymysql\n  pip install pymysql\n")
    sys.exit(2)


ENV_KEYS = ("SR_HOST", "SR_QUERY_PORT", "SR_USER", "SR_PASSWORD", "SR_DB")


def parse_env_file(path: Path) -> dict:
    out = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if v and v[0] in ("'", '"') and v[-1] == v[0]:
            v = v[1:-1]
        out[k] = v
    return out


def load_env(explicit: str | None) -> dict:
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.append(Path.home() / ".env")
    loaded_from = None
    for p in candidates:
        if p.is_file():
            env = parse_env_file(p)
            for k in ENV_KEYS:
                if k not in os.environ and k in env:
                    os.environ[k] = env[k]
            loaded_from = p
            break
    missing = [k for k in ("SR_HOST", "SR_USER", "SR_PASSWORD") if not os.environ.get(k)]
    if missing:
        sys.stderr.write(
            f"missing env key(s): {', '.join(missing)}\n"
            f"checked: {', '.join(str(c) for c in candidates)}\n"
            "create a .env file with:\n"
            "  SR_HOST=...\n  SR_USER=...\n  SR_PASSWORD=...\n"
            "  SR_QUERY_PORT=9030  # optional\n"
        )
        sys.exit(2)
    return {
        "host": os.environ["SR_HOST"],
        "port": int(os.environ.get("SR_QUERY_PORT", "9030")),
        "user": os.environ["SR_USER"],
        "password": os.environ["SR_PASSWORD"],
        "default_db": os.environ.get("SR_DB", "information_schema"),
        "loaded_from": loaded_from,
    }


def connect(conn: dict, db: str | None):
    return pymysql.connect(
        host=conn["host"],
        port=conn["port"],
        user=conn["user"],
        password=conn["password"],
        database=db or conn["default_db"],
        charset="utf8mb4",
        connect_timeout=30,
        read_timeout=7200,
        write_timeout=7200,
        init_command="SET SESSION query_timeout = 7200",
    )


def run_query(conn_args, sql: str, db: str | None = None):
    conn = connect(conn_args, db)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description is None:
                return [], (), cur.rowcount
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            return cols, rows, cur.rowcount
    finally:
        conn.close()


def run_exec(conn_args, sql: str, db: str | None = None) -> int:
    conn = connect(conn_args, db)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()


def print_table(cols, rows) -> None:
    if not cols:
        print("(no columns)")
        return
    widths = [len(c) for c in cols]
    str_rows = []
    for r in rows:
        s = [("" if v is None else str(v)) for v in r]
        str_rows.append(s)
        for i, v in enumerate(s):
            widths[i] = max(widths[i], len(v))

    def line(vals):
        return " | ".join(v.ljust(widths[i]) for i, v in enumerate(vals))

    print(line(cols))
    print("-+-".join("-" * w for w in widths))
    for s in str_rows:
        print(line(s))
    print(f"({len(str_rows)} rows)")


def print_json(cols, rows) -> None:
    out = [dict(zip(cols, r)) for r in rows]
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


DESTRUCTIVE_RE = re.compile(
    r"\b(DROP\s+(DATABASE|TABLE|VIEW|INDEX|PARTITION)|"
    r"TRUNCATE\s+TABLE|"
    r"DELETE\s+FROM(?![^;]*\bWHERE\b)|"
    r"ALTER\s+TABLE\s+\S+\s+DROP\s+(COLUMN|PARTITION))\b",
    re.IGNORECASE,
)


def confirm_destructive(sql: str, force: bool) -> bool:
    m = DESTRUCTIVE_RE.search(sql)
    if not m or force:
        return True
    sys.stderr.write(f"!! destructive: {m.group(0)}\n   {sql}\n")
    try:
        ans = input("   type 'yes' to proceed: ").strip()
    except EOFError:
        return False
    return ans == "yes"


def parse_qual(ref: str) -> tuple[str, str]:
    if "." not in ref:
        sys.stderr.write(f"expected <db>.<table>, got: {ref}\n")
        sys.exit(2)
    db, table = ref.split(".", 1)
    return db.strip("`"), table.strip("`")


def cmd_dbs(args, conn_args) -> None:
    _, rows, _ = run_query(conn_args, "SHOW DATABASES")
    for (name,) in rows:
        print(name)


def cmd_tables(args, conn_args) -> None:
    _, rows, _ = run_query(conn_args, f"SHOW TABLES FROM `{args.db}`")
    for (name,) in rows:
        print(name)


def cmd_show(args, conn_args) -> None:
    db, table = parse_qual(args.target)
    _, rows, _ = run_query(conn_args, f"SHOW CREATE TABLE `{db}`.`{table}`")
    print(rows[0][1])


def cmd_count(args, conn_args) -> None:
    db, table = parse_qual(args.target)
    _, rows, _ = run_query(conn_args, f"SELECT COUNT(*) FROM `{db}`.`{table}`")
    print(rows[0][0])


def cmd_query(args, conn_args) -> None:
    cols, rows, _ = run_query(conn_args, args.sql, db=args.connection_db)
    (print_json if args.json else print_table)(cols, rows)


def cmd_exec(args, conn_args) -> None:
    if args.file:
        text = Path(args.file).expanduser().read_text()
        sqls = [s.strip() for s in text.split(";") if s.strip()]
    elif args.sql:
        sqls = [args.sql.strip().rstrip(";")]
    else:
        sys.stderr.write("sr exec: provide SQL string or -f <file>\n")
        sys.exit(2)

    for s in sqls:
        if not confirm_destructive(s, args.force):
            sys.stderr.write("aborted\n")
            sys.exit(1)
        rc = run_exec(conn_args, s, db=args.connection_db)
        preview = s.replace("\n", " ")
        if len(preview) > 120:
            preview = preview[:117] + "..."
        print(f"OK affected_rows={rc}  {preview}")


def main() -> int:
    p = argparse.ArgumentParser(
        prog="sr",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--env", help=".env path override")
    p.add_argument("--db", dest="connection_db",
                   help="连接时 USE 的库（默认 SR_DB 或 information_schema）")
    p.add_argument("--json", action="store_true", help="JSON 输出（query 有效）")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("dbs", help="SHOW DATABASES")
    sp.set_defaults(func=cmd_dbs)

    sp = sub.add_parser("tables", help="SHOW TABLES FROM <db>")
    sp.add_argument("db")
    sp.set_defaults(func=cmd_tables)

    sp = sub.add_parser("show", help="SHOW CREATE TABLE <db>.<table>")
    sp.add_argument("target", metavar="db.table")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("count", help="SELECT COUNT(*) FROM <db>.<table>")
    sp.add_argument("target", metavar="db.table")
    sp.set_defaults(func=cmd_count)

    sp = sub.add_parser("query", help="执行任意 SELECT")
    sp.add_argument("sql")
    sp.set_defaults(func=cmd_query)

    sp = sub.add_parser("exec", help="执行 DDL/DML（直接生效，Claude 应在调用前把 SQL 给用户看）")
    sp.add_argument("sql", nargs="?")
    sp.add_argument("-f", "--file", help="从文件读 SQL（半角分号分条）")
    sp.add_argument("--force", action="store_true",
                    help="跳过 DROP/TRUNCATE/DELETE 交互确认（脚本化用）")
    sp.set_defaults(func=cmd_exec)

    args = p.parse_args()
    conn_args = load_env(args.env)
    args.func(args, conn_args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
