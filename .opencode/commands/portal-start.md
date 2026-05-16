---
description: Start the local skills portal (FastAPI:5174 + Vite:5173). Auto-detects portless HTTPS.
agent: build
---

# /portal-start

Start the portal backend + frontend. Idempotent (no-op if already running).

## Execute

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client ensure
```

This:
1. Checks if `/api/health` is already up — if yes, returns immediately
2. Verifies `portal/backend/.venv/bin/python` exists (otherwise prompts user to install)
3. Verifies ports 5173 / 5174 are free (errors if occupied — user must run `/portal-stop` or kill manually)
4. Spawns `./portal/bin/start` in background, redirects logs to `/tmp/portal-uvicorn.log`
5. Polls health up to 20 seconds

## Final report

If success:
```
✅ Skills Portal up:
   API:        http://127.0.0.1:5174/api/health
   Frontend:   http://localhost:5173
   HTTPS:      https://skills-portal.localhost   (if portless installed)
   API docs:   http://127.0.0.1:5174/api/docs
   Logs:       /tmp/portal-uvicorn.log
   Stop:       /portal-stop
```

If failure:
- Print the verbatim PortalError message
- Show last 20 lines of `/tmp/portal-uvicorn.log` if it exists
- Suggest specific fix:
  - "venv missing" → `cd portal/backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
  - "ports occupied" → `lsof -ti:5173,5174 | xargs kill -9` (warn user this kills *anything* on those ports)
