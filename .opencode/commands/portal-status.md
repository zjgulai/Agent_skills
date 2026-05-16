---
description: Show portal port status, PID, last index build time, and skill count.
agent: build
---

# /portal-status

Read-only diagnostic snapshot of the portal.

## Execute

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client status
```

## Output format

If portal is up:
```
=== Skills Portal status ===
  API:           ✅ up  (http://127.0.0.1:5174)
  Vite (5173):   ✅ up
  PIDs:          [<pid>, <pid>, ...]
  Skill count:   <N>
  Last index:    <iso timestamp>
  Logs:          /tmp/portal-uvicorn.log
```

If portal is down:
```
=== Skills Portal status ===
  API:           ❌ down
  Vite (5173):   ❌ down
  PIDs:          (none)
  Skill count:   ?

To start:  /portal-start
```

If partially up (one port but not the other):
```
=== Skills Portal status (DEGRADED) ===
  API (5174):    ✅ up
  Vite (5173):   ❌ down

This is unusual. Recommend:  /portal-stop && /portal-start
```

Read-only. No writes.
