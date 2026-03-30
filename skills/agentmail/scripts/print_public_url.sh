#!/usr/bin/env bash
set -euo pipefail
json="$(curl -fsS http://127.0.0.1:4041/api/tunnels)"
python3 - <<'PY' "$json"
import json,sys
obj=json.loads(sys.argv[1])
for t in obj.get('tunnels',[]):
    if t.get('name')=='agentmail' and t.get('public_url','').startswith('https://'):
        print(t['public_url'].rstrip('/') + '/agentmail/webhook')
        raise SystemExit(0)
print('agentmail tunnel not found on 127.0.0.1:4041', file=sys.stderr)
raise SystemExit(1)
PY
