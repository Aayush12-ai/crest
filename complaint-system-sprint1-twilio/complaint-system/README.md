# Enterprise Complaint Management System

## Sprint 1 — Ingest API

### Prerequisites (WSL2)
```bash
# Install Docker Desktop for Windows, enable WSL2 integration
# Then inside WSL2 terminal:
docker --version   # should print Docker version
docker compose version
```

### First-time setup
```bash
# 1. Copy env template and fill in your values
cp .env.example .env
# Open .env and change the passwords if you want (defaults work for dev)

# 2. Start everything
docker compose up -d

# 3. Watch logs until you see "Application startup complete"
docker compose logs -f ingest
```

### Test it
```bash
# Health check
curl http://localhost:8001/health

# Submit a complaint (uses the seeded test user)
curl -X POST http://localhost:8001/complaint \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "channel": "whatsapp",
    "message": "My payment failed but money was deducted"
  }'

# Send the exact same request again — should return SAME complaint_id (idempotency)
```

### Browse the API docs
Open http://localhost:8001/docs — FastAPI auto-generates interactive Swagger UI.

### Peek inside the database
```bash
docker exec -it cms_postgres psql -U cms_user complaints_db

# Inside psql:
SELECT complaint_id, channel, status, created_at FROM complaints;
SELECT * FROM audit_log;
\q
```

### Useful commands
```bash
docker compose ps              # see what's running
docker compose logs -f ingest  # tail ingest logs
docker compose restart ingest  # restart just ingest (after code change)
docker compose down            # stop everything
docker compose down -v         # stop + wipe database volumes (fresh start)
```

## Project Structure
```
complaint-system/
├── docker-compose.yml          ← starts all services
├── .env.example                ← copy to .env
├── .gitignore
├── scripts/
│   └── init.sql                ← database schema (auto-runs on first start)
└── services/
    └── ingest/
        ├── Dockerfile
        ├── requirements.txt
        ├── main.py             ← FastAPI app, routes
        ├── database.py         ← SQLAlchemy async engine
        ├── models.py           ← ORM table definitions
        └── schemas.py          ← Pydantic request/response shapes
```
