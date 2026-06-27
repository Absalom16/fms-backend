#!/bin/sh
set -e

echo "=== Waiting for MySQL to be ready ==="
python - <<'EOF'
import time, sys, os, re

url = os.environ.get('DATABASE_URL', '')
m = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/(.+)', url)
if not m:
    print("[warn] Could not parse DATABASE_URL, skipping DB wait")
    sys.exit(0)

user, pwd, host, port, db = m.groups()
port = int(port or 3306)

import pymysql
for attempt in range(40):
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=pwd, database=db, connect_timeout=3)
        conn.close()
        print(f"  DB ready after {attempt + 1} attempt(s).")
        sys.exit(0)
    except Exception as e:
        print(f"  [{attempt + 1}/40] DB not ready ({e}) — retrying in 3s...")
        time.sleep(3)

print("[error] Database did not become ready in time.")
sys.exit(1)
EOF

echo "=== Running seed data ==="
python seed.py

echo "=== Starting Gunicorn ==="
exec gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --access-logfile - wsgi:app
