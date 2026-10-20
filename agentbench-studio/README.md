# AgentBench Studio

Author, run, verify and compare AI agent tasks.

- **Author**: a task is a prompt plus weighted checks (`contains`, `not_contains`, `regex`, `json_valid`, `json_schema`, `max_words`, `llm_judge`).
- **Task-quality lint**: `GET /tasks/{id}/lint` flags tasks that cannot tell good answers from bad (no checks, only negative or length checks, invalid regex/schema, judge-only scoring).
- **Run and verify**: one run per model, checks are evaluated automatically; each run stores output, latency, per-check results and a weighted score.
- **Compare**: `/benchmarks` ranks models by mean score, pass rate, median latency and errors, plus a task x model score matrix.

## Run

```bash
cp .env.example .env        # add ANTHROPIC_API_KEY / OPENAI_API_KEY for real models
docker compose up --build
```

Web: http://localhost:3000 - API docs: http://localhost:8000/docs

Models are `provider:model`. `mock:echo` and `mock:empty` work offline; `anthropic:<model>` and `openai:<model>` (any OpenAI-compatible server via `OPENAI_BASE_URL`) need keys. Set `JUDGE_MODEL` for `llm_judge` checks.

## Test

```bash
cd backend && pip install -r requirements.txt && pytest          # checks + lint
cd frontend && npm install && npx playwright install chromium
docker compose up -d && npm run e2e                               # author -> run -> compare in a browser
```

## Layout

```
backend/app   main.py (API) checks.py (checks + lint) runner.py providers.py models.py
frontend/app  / (tasks + authoring)  /tasks/[id] (run + results)  /benchmarks
frontend/e2e  Playwright end-to-end spec
```

## Not included yet

Alembic migrations (tables are created on startup), auth, a durable job queue (runs use FastAPI background tasks), repeated runs per task, and Playwright-driven browser-task checks.
