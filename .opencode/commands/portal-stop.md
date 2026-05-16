---
description: Stop the portal by killing processes on ports 5173 and 5174. Safe to run any time.
agent: build
---

# /portal-stop

Forcefully terminate uvicorn + vite by killing PIDs on ports 5173/5174.

## Execute

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client stop
```

The lib does:
```
lsof -ti:5173,5174 | xargs kill -9
```

## Final report

If something was killed:
```
✅ stopped: killed PIDs <PID1>, <PID2>, ...
   Ports 5173 + 5174 are now free.
```

If nothing was running:
```
ℹ portal was not running (no PIDs on 5173/5174).
```

This command is **idempotent** — running it twice does no harm. Safe to invoke before `/portal-start` if portal is in a weird state.
