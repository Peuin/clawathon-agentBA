# AGENTS.md

## Cursor Cloud specific instructions

### Product layout

This repo is the **AI Business Analyst Agent** (BABOK v3 copilot). Paths differ from the root `README.md`:

| Path | Role |
|------|------|
| `BE/` | FastAPI + LangGraph backend (`http://localhost:8000`) |
| `FE/` | Next.js 14 frontend (`http://localhost:3000`) |
| `DB/schema.sql` | Supabase/Postgres schema (optional for local dev; backend uses in-memory stores today) |

### Prerequisites (one-time on fresh VMs)

- **Python 3.11+** with `python3.12-venv` (`sudo apt install python3.12-venv` on Ubuntu if `python -m venv` fails)
- **Node.js 18+** and npm
- `BE/.env` — committed in the repo with Supabase + GreenNode LLM credentials (no extra setup needed)
- Backend `venv` + frontend `node_modules` are restored by the update script on startup

### Starting services

Use separate terminals (or tmux sessions):

```bash
# Backend
cd BE && source venv/bin/activate && python main.py

# Frontend
cd FE && npm run dev
```

Backend listens on **port 8000**; frontend on **port 3000** (README mentions 3003 but `package.json` uses the Next.js default).

### Lint / build / test

| Service | Lint | Build | Tests |
|---------|------|-------|-------|
| Backend | No linter configured | N/A | No test suite in repo |
| Frontend | `cd FE && npm run lint` | `cd FE && npm run build` | None |

Verify backend imports: `cd BE && source venv/bin/activate && python -c "import main"`.

### API smoke test (core functionality)

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/projects \
  -H 'Content-Type: application/json' \
  -d '{"name":"Test","description":"demo"}'
curl -X POST http://localhost:8000/api/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"project_id":"proj_1","message":"Describe onboarding requirements"}'
```

### Gotchas

- `BE/main.py` does **not** call `load_dotenv()`; LLM env vars from `BE/.env` are only picked up if exported to the shell or if uvicorn is started with `--env-file .env`. Chat still works with canned step-based responses without LLM.
- `get_db_client()` expects `SUPABASE_KEY`, but `.env` defines `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_ROLE_KEY`. Supabase is not wired into routes yet, so this does not block local dev.
- No automated test scripts exist in either `BE/` or `FE/`.
- Optional: `cd BE && docker-compose up --build` runs only the backend container on port 8000.
