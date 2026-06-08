# Start This Project

Use these steps on another laptop.

## 1. Install Frontend

```bash
npm install
```

## 2. Create Environment File

```bash
cp .env.example .env
```

Default `.env` values:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000
TEMPORAL_WORKFLOWS_URL=http://localhost:8233/namespaces/default/workflows
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
FRONTEND_ORIGIN_REGEX=http://(localhost|127\.0\.0\.1|0\.0\.0\.0):[0-9]+
```

## 3. Install Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## 4. Start Backend

Open terminal 1:

```bash
source .venv/bin/activate
python3 run_fastapi.py
```

Backend URL:

```bash
http://127.0.0.1:8000
```

## 5. Start Frontend

Open terminal 2:

```bash
npm run dev
```

Frontend URL is usually:

```bash
http://localhost:5173
```

## 6. Check Backend

Open these in browser:

```bash
http://127.0.0.1:8000/
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api/runbooks
```

## If Backend Not Reachable

Run:

```bash
python3 run_fastapi.py
```

Then refresh the frontend page.
