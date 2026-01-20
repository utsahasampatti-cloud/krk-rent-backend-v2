# krk-rent-backend (OLX-only, backend-only)

## Local run (requires Postgres + Redis)
1) Create venv + install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Env vars
```bash
export DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/DBNAME"
export REDIS_URL="redis://HOST:6379/0"
```

3) Init DB
Run `app/models.sql` against your database.

4) Start Web
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

5) Start Worker (separate terminal)
```bash
python -m app.worker
```

## API
- GET /health
- POST /search
- GET /feed?user_id=123&limit=10
- POST /state
