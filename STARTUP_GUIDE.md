# BizSaathi - Local Development Startup Guide

Complete guide for running BizSaathi backend and frontend locally for development and testing.

## Prerequisites Verification

Before starting, verify you have:

```powershell
# Check Python version (requires 3.12)
python --version
# Should show: Python 3.12.x

# Check Node.js version (requires 18+)
node --version
# Should show: v18.x.x or higher

# Check Docker (for PostgreSQL, Redis, MinIO)
docker --version
# Should show: Docker version 20.x or higher

# Check uv package manager
uv --version
# If not installed: pip install uv

# Check just task runner (optional, but recommended)
just --version
# If not installed: follow https://github.com/casey/just#installation
```

---

## Step 1: Start Infrastructure Services

BizSaathi requires PostgreSQL and Redis running locally via Docker Compose. MinIO is optional.

```powershell
# From project root (d:\PROJECTS\BizSaathi)

# First time only: create a local, ignored configuration file and set unique credentials.
Copy-Item .env.example .env
# Edit .env; do not commit or share it. Use strong, unique values for database,
# JWT, and object-storage secrets. MinIO is optional unless you enable its profile.

# Start all infrastructure services
just up

# Alternative without just:
docker compose up -d

# Verify services are running
docker compose ps
```

**Expected output:**
```
NAME                    SERVICE      STATUS       PORTS
bizsaathi-postgres-1    postgres     running      127.0.0.1:5433->5432/tcp
bizsaathi-redis-1       redis        running      127.0.0.1:6379->6379/tcp
```
Host ports may differ if changed in `.env`. Compose binds development ports to loopback; do not change them to `0.0.0.0` on a network-accessible machine.

**Service URLs (for debugging):**
- PostgreSQL: `localhost:5433` (username and password are the unique local values in `.env`)
- Redis: `localhost:6379`
- MinIO Console: http://localhost:9001 (optional storage profile; credentials are configured in `.env`)
- MinIO API: http://localhost:9000 (optional storage profile)

---

## Step 2: Database Setup

Run Alembic migrations to create all tables.

```powershell
# From project root

# Apply all migrations
just migrate

# Alternative without just:
cd backend
uv run alembic upgrade head
cd ..
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001_initial_schema
INFO  [alembic.runtime.migration] Running upgrade 0001_initial_schema -> 0002_phase2_tables
INFO  [alembic.runtime.migration] Running upgrade 0002_phase2_tables -> 5aa6ba177a21, phase4_customer_and_orders
```

**What this creates:**
- Phase 1: businesses, users, products, customers (12 tables)
- Phase 2: content_templates, content_versions, etc. (6 tables)
- Phase 4: public_sessions, conversations, messages, customer_orders (9 tables)

---

## Step 3: Start Backend API

The FastAPI backend runs on port 8000 with auto-reload for development.

```powershell
# From project root

# Start backend with auto-reload
just dev-api

# Alternative without just:
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['d:\\PROJECTS\\BizSaathi\\backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Backend is ready when you see:**
```
✓ Backend running on http://localhost:8000
```

**Important URLs:**

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Interactive API documentation (Swagger UI) |
| http://localhost:8000/redoc | Alternative API docs (ReDoc) |
| http://localhost:8000/health | Health check endpoint |
| http://localhost:8000/api/v1/* | Protected endpoints (require auth) |
| http://localhost:8000/public/* | Public endpoints (no auth) |

---

## Step 4: Start Frontend (Next.js)

The Next.js frontend runs on port 3000 with hot module reloading.

```powershell
# Open a NEW terminal (keep backend running in the first terminal)
# From project root

# Start frontend development server
just dev-web

# Alternative without just:
cd frontend
npm run dev
```

**Expected output:**
```
> frontend@0.1.0 dev
> next dev

   ▲ Next.js 16.x.x
   - Local:        http://localhost:3000
   - Environments: .env.local

 ✓ Starting...
 ✓ Ready in 2.3s
```

**Frontend is ready when you see:**
```
✓ Compiled / in 1234ms
```

**Frontend URLs:**

| URL | Description |
|-----|-------------|
| http://localhost:3000 | Home page |
| http://localhost:3000/login | Login page |
| http://localhost:3000/dashboard | Business dashboard (after login) |
| http://localhost:3000/products | Product management |
| http://localhost:3000/customers | Customer management |
| http://localhost:3000/content | Content templates |

---

## Step 5: Testing the Public Chat API (Phase 4)

Now that both backend and frontend are running, test the newly implemented Public Chat API endpoints.

### Test Sequence

#### 1. Get Public Store Information (EP-E01)

```powershell
# Get store info by slug
curl http://localhost:8000/public/stores/my-shop
```

**Expected response (if store exists):**
```json
{
  "business": {
    "id": 1,
    "name": "My Shop",
    "slug": "my-shop",
    "description": "...",
    "created_at": "2026-10-20T10:00:00Z"
  },
  "products": [
    {
      "id": 1,
      "name": "Product 1",
      "price": "99.99",
      "is_active": true
    }
  ]
}
```

**Note:** If you get `404 Store not found`, you need to create a business first (see "Creating Test Data" section below).

#### 2. Create Chat Session (EP-E02)

```powershell
# Create a new session for store
curl -X POST http://localhost:8000/public/stores/my-shop/sessions `
  -H "Content-Type: application/json" `
  -d '{}'
```

**Expected response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_token": "abc123def456...",
  "expires_at": "2026-10-29T10:00:00Z"
}
```

**Save these values for next steps!**

#### 3. Send Message (EP-E03)

```powershell
# Replace with your actual session_id and token
$session_id = "550e8400-e29b-41d4-a716-446655440000"
$token = "abc123def456..."

curl -X POST "http://localhost:8000/public/sessions/$session_id/messages" `
  -H "Content-Type: application/json" `
  -H "X-Session-Token: $token" `
  -d '{"content": "Hello! What products do you have?", "attachments": []}'
```

**Expected response:**
```json
{
  "status": "accepted",
  "message_id": "msg_123456"
}
```

#### 4. Stream Responses (EP-E04)

Open in your browser or use a tool that supports Server-Sent Events:

```
http://localhost:8000/public/sessions/{session_id}/stream?token={your_token}
```

**Expected SSE stream:**
```
event: heartbeat
data: {"timestamp": "2026-10-28T15:30:00Z"}

event: heartbeat
data: {"timestamp": "2026-10-28T15:30:15Z"}

...

event: closed
data: {'reason': 'demo_timeout'}
```

**Note:** Currently returns heartbeat every 15 seconds. Full message polling and agent responses will be implemented in future iterations.

---

## Creating Test Data

If you're starting fresh, you'll need to create a business and products first.

### Option 1: Using the API (requires authentication)

```powershell
# 1. Create a user and business (requires POST /api/v1/auth/register or seed data)
# 2. Login to get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email": "owner@example.com", "password": "password123"}'

# 3. Use the token to create products
curl -X POST http://localhost:8000/api/v1/products `
  -H "Authorization: Bearer YOUR_JWT_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"name": "Test Product", "price": 99.99, "is_active": true}'
```

### Option 2: Direct Database Insert (for development)

```sql
-- Connect to PostgreSQL
-- psql -U postgres -d bizsaathi -h localhost

-- Create a business
INSERT INTO businesses (name, slug, owner_email, created_at, updated_at)
VALUES ('Test Shop', 'test-shop', 'test@example.com', NOW(), NOW())
RETURNING id;

-- Create a product (replace business_id with the ID from above)
INSERT INTO products (business_id, name, price, stock_quantity, is_active, created_at, updated_at)
VALUES (1, 'Sample Product', 99.99, 100, true, NOW(), NOW());
```

### Option 3: Run Database Seeds (if available)

```powershell
# Check if seed script exists
cd backend
uv run python -m app.seeds.demo_data
```

---

## Verification Checklist

Before proceeding with development, verify all systems are operational:

- [ ] **Infrastructure running:** `docker compose ps` shows 3 services healthy
- [ ] **Database migrated:** `just migrate` completed without errors
- [ ] **Backend running:** http://localhost:8000/health returns `{"status": "healthy"}`
- [ ] **Frontend running:** http://localhost:3000 loads without errors
- [ ] **API docs accessible:** http://localhost:8000/docs shows Swagger UI
- [ ] **Public store API works:** GET `/public/stores/{slug}` returns 200 or 404
- [ ] **Session creation works:** POST `/stores/{slug}/sessions` returns token
- [ ] **Message sending works:** POST `/sessions/{id}/messages` returns 202
- [ ] **SSE streaming works:** GET `/sessions/{id}/stream` opens SSE connection

---

## Common Issues & Solutions

### Issue: "Connection refused" when starting backend

**Solution:**
```powershell
# Check if PostgreSQL is running
docker compose ps
# If not running, start it
just up
```

### Issue: "Port 8000 already in use"

**Solution:**
```powershell
# Find and kill the process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Or change the port
cd backend
uv run uvicorn app.main:app --reload --port 8001
```

### Issue: "Port 3000 already in use"

**Solution:**
```powershell
# Frontend will automatically suggest port 3001
# Or kill the process
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F
```

### Issue: "ModuleNotFoundError" in backend

**Solution:**
```powershell
# Reinstall dependencies
cd backend
uv pip install -r requirements.txt
```

### Issue: "npm install" fails in frontend

**Solution:**
```powershell
# Clear npm cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: Migration fails with "relation already exists"

**Solution:**
```powershell
# Check current migration state
cd backend
uv run alembic current

# If needed, reset database (WARNING: destroys all data)
docker compose down -v
just up
just migrate
```

---

## Running Tests

### Backend Tests

```powershell
# Run all tests
just check-fast

# Run only unit tests
cd backend
uv run pytest tests/unit -v

# Run only integration tests
uv run pytest tests/integration -v

# Run with coverage
uv run pytest --cov=app --cov-report=html
```

### Frontend Tests

```powershell
cd frontend

# Run unit tests
npm run test

# Run E2E tests (requires backend running)
npm run test:e2e
```

---

## Stopping Services

### Stop Backend/Frontend
- Press `CTRL+C` in each terminal window

### Stop Infrastructure
```powershell
# Stop but keep data
just down

# Alternative
docker compose down

# Stop AND delete all data (full reset)
docker compose down -v
```

---

## Development Workflow

Recommended workflow for daily development:

```powershell
# Morning startup (5 minutes)
1. just up                    # Start Docker services
2. just migrate              # Apply any new migrations
3. just dev-api              # Terminal 1: Start backend
4. just dev-web              # Terminal 2: Start frontend

# During development
- Backend auto-reloads on .py file changes
- Frontend hot-reloads on .tsx/.ts file changes
- Check http://localhost:8000/docs for API changes

# Before committing
5. just check-fast           # Run linters, types, unit tests (2-3 min)
6. just check                # Full test suite including integration (5-10 min)

# End of day
7. CTRL+C in both terminals
8. just down                 # Stop Docker services
```

---

## Next Steps

Now that your environment is running:

1. **Explore the API:** Visit http://localhost:8000/docs
2. **Test Public Chat:** Follow the "Testing the Public Chat API" section above
3. **Create test data:** Use one of the methods in "Creating Test Data"
4. **Review Phase 4 status:** See `docs/status/PHASE_4_T401_PROGRESS.md`
5. **Check remaining tasks:** See `docs/tasks/` directory

---

## Quick Reference

| Component | URL | Credentials |
|-----------|-----|-------------|
| Frontend | http://localhost:3000 | (varies by seed data) |
| Backend API | http://localhost:8000 | (JWT required for protected routes) |
| API Docs | http://localhost:8000/docs | - |
| PostgreSQL | localhost:5433 | Unique credentials configured in ignored `.env` |
| Redis | localhost:6379 | (no password) |
| MinIO Console | http://localhost:9001 | Optional; unique credentials configured in ignored `.env` |

---

## Support

For issues or questions:
- Check `AGENTS.md` for project contract
- Review `docs/` directory for detailed documentation
- Check `docs/12-assumptions-risks-deps.md` for dependency versions
- See `docs/adr/` for architectural decisions

---

**Last Updated:** 2026-10-28  
**Phase:** Phase 4 - Public Customer Chat API  
**Status:** Backend GREEN (107/107 tests passing, all gates passing)
