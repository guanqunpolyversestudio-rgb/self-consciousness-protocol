# Render Deploy Notes

This backend can be deployed to Render as a single-instance FastAPI service with a persistent disk.

## What is already in the repo

- `render.yaml` at the repo root
- `backend/.python-version`
- `backend/Dockerfile` remains available for non-Render use
- shared DB path can be overridden with `SC_BACKEND_DB_PATH`

## Local startup remains unchanged

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

or:

```bash
cd backend
.venv/bin/python run.py
```

## Render assumptions

- single instance only
- SQLite stays on a persistent disk
- `SC_BACKEND_DB_PATH` points to the mounted disk path
- `WAVESPEED_API_KEY` is configured as a Render secret env var

## Manual steps still required

1. Log into Render.
2. Connect the Git repo.
3. Create the web service from `render.yaml`.
4. Confirm the service can use a persistent disk.
5. Set the secret `WAVESPEED_API_KEY` in Render.
6. Deploy.

## Current tradeoff

This is the simplest cloud setup for the current codebase.

Because the shared backend still uses SQLite:

- keep one instance
- do not scale horizontally
- move to Postgres later if multi-instance public traffic becomes necessary
