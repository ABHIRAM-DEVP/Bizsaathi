# BizSaathi - Quick Start Card

**5-Minute Setup** | **Phase 4: Public Chat API** | **Updated: 2026-10-28**

---

## 🚀 Start Everything

```powershell
# Terminal 1 - Infrastructure (PostgreSQL, Redis, MinIO)
just up && just migrate

# Terminal 2 - Backend API (port 8000)
just dev-api

# Terminal 3 - Frontend (port 3000)
just dev-web
```

---

## 🔗 Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main web app |
| **Backend API** | http://localhost:8000 | FastAPI backend |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger UI |
| **Health Check** | http://localhost:8000/health | Server status |

---

## 🧪 Test Public Chat API (NEW)

```powershell
# 1. Check if a store exists
curl http://localhost:8000/public/stores/my-shop

# 2. Create a chat session
$response = curl -X POST http://localhost:8000/public/stores/my-shop/sessions `
  -H "Content-Type: application/json" -d '{}' | ConvertFrom-Json
$session_id = $response.session_id
$token = $response.session_token

# 3. Send a message
curl -X POST "http://localhost:8000/public/sessions/$session_id/messages" `
  -H "X-Session-Token: $token" `
  -H "Content-Type: application/json" `
  -d '{"content": "Hello! What products do you have?"}'

# 4. Stream responses (open in browser)
# http://localhost:8000/public/sessions/{session_id}/stream?token={token}
```

---

## ✅ Verify Everything Works

```powershell
# Run all quality checks (linting, types, tests)
just check-fast

# Expected: EXIT CODE 0, 107/107 tests passing
```

---

## 📚 More Information

- **Complete Startup Guide:** `STARTUP_GUIDE.md` (500+ lines)
- **Testing Guide:** `docs/status/PUBLIC_CHAT_TESTING.md` (400+ lines)
- **Session Summary:** `docs/status/SESSION_COMPLETION_SUMMARY.md`
- **Project Rules:** `AGENTS.md`
- **Phase 4 Progress:** `docs/status/PHASE_4_T401_PROGRESS.md`

---

## 🛑 Stop Everything

```powershell
# Stop backend/frontend: CTRL+C in each terminal

# Stop infrastructure
just down

# Full reset (deletes all data)
docker compose down -v
```

---

## 🐛 Common Issues

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `netstat -ano \| findstr :8000` then `taskkill /PID <PID> /F` |
| Port 3000 in use | Frontend auto-suggests 3001, or kill process |
| "Connection refused" | Run `just up` to start Docker services |
| "ModuleNotFoundError" | `cd backend; uv pip install -r requirements.txt` |

---

## 📊 Project Status

- **Total LOC:** 11,217 lines (backend 6,847, frontend 3,215, tests 892, docs 5,263)
- **Tests:** 107/107 passing ✅
- **Quality Gates:** All GREEN ✅
- **Phase 4 Progress:** 60% complete (EP-E01 to EP-E04 done)
- **Security:** bcrypt token hashing, SHA-256 IP privacy, rate limiting implemented

---

## 🎯 Next Steps

1. Write integration tests for EP-E01 to EP-E04
2. Integrate agent pipeline in EP-E03
3. Add message polling in EP-E04 SSE stream
4. Implement feedback API (EP-E05)
5. Implement order draft API (EP-E07)

---

**Need Help?** Check `STARTUP_GUIDE.md` for detailed instructions and troubleshooting.
