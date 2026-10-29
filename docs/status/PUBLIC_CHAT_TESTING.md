# Public Chat API - Testing Guide

Quick reference for testing the Phase 4 Public Chat API endpoints (T-401).

## Prerequisites

1. Backend running on http://localhost:8000
2. Database migrated (`just migrate`)
3. At least one business with slug and active products

---

## Test Scenario: Complete Chat Flow

### Step 1: Verify Store Exists

```bash
# PowerShell
curl http://localhost:8000/public/stores/my-shop
```

**Success Response (200):**
```json
{
  "business": {
    "id": 1,
    "name": "My Shop",
    "slug": "my-shop",
    "description": "A sample store",
    "created_at": "2026-10-20T10:00:00Z"
  },
  "products": [
    {
      "id": 1,
      "name": "Product A",
      "price": "99.99",
      "stock_quantity": 50,
      "is_active": true
    }
  ]
}
```

**Failure Response (404):**
```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Store not found"
}
```

---

### Step 2: Create Chat Session

```bash
# PowerShell
curl -X POST http://localhost:8000/public/stores/my-shop/sessions `
  -H "Content-Type: application/json" `
  -d '{}'
```

**Success Response (200):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_token": "gAAAAABnH3K9X...(base64 encoded bcrypt hash)",
  "expires_at": "2026-10-29T10:00:00Z"
}
```

**Important:**
- `session_token` is hashed with bcrypt before storage (secure)
- Session expires in 24 hours
- IP address is SHA-256 hashed before storage (privacy-compliant)

**Save these values:**
```powershell
$session_id = "550e8400-e29b-41d4-a716-446655440000"
$token = "gAAAAABnH3K9X..."
```

---

### Step 3: Send Customer Message

```bash
# PowerShell
curl -X POST "http://localhost:8000/public/sessions/$session_id/messages" `
  -H "Content-Type: application/json" `
  -H "X-Session-Token: $token" `
  -d '{
    "content": "Hello! I am interested in Product A. What is the price?",
    "attachments": []
  }'
```

**Success Response (202 Accepted):**
```json
{
  "status": "accepted",
  "message_id": "msg_a1b2c3d4"
}
```

**Error Responses:**

**401 - Invalid Token:**
```json
{
  "type": "about:blank",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Invalid session token"
}
```

**404 - Session Not Found:**
```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Session not found"
}
```

**410 - Session Expired:**
```json
{
  "type": "about:blank",
  "title": "Gone",
  "status": 410,
  "detail": "Session expired"
}
```

**429 - Rate Limited:**
```json
{
  "type": "about:blank",
  "title": "Too Many Requests",
  "status": 429,
  "detail": "Rate limit exceeded. Try again in X seconds."
}
```

---

### Step 4: Stream Agent Responses (SSE)

Open in browser or use curl with streaming:

```
http://localhost:8000/public/sessions/{session_id}/stream?token={your_token}
```

**Browser Test:**
```html
<!-- Save as test_sse.html and open in browser -->
<!DOCTYPE html>
<html>
<head>
  <title>SSE Test</title>
</head>
<body>
  <h1>Public Chat SSE Stream</h1>
  <div id="output"></div>
  <script>
    const sessionId = 'YOUR_SESSION_ID';
    const token = 'YOUR_TOKEN';
    const url = `http://localhost:8000/public/sessions/${sessionId}/stream?token=${token}`;
    
    const eventSource = new EventSource(url);
    const output = document.getElementById('output');
    
    eventSource.addEventListener('heartbeat', (e) => {
      output.innerHTML += `<p>[Heartbeat] ${e.data}</p>`;
    });
    
    eventSource.addEventListener('message', (e) => {
      output.innerHTML += `<p>[Message] ${e.data}</p>`;
    });
    
    eventSource.addEventListener('closed', (e) => {
      output.innerHTML += `<p>[Closed] ${e.data}</p>`;
      eventSource.close();
    });
    
    eventSource.onerror = (error) => {
      output.innerHTML += `<p style="color:red;">[Error] Connection failed</p>`;
      eventSource.close();
    };
  </script>
</body>
</html>
```

**Expected SSE Events:**

```
event: heartbeat
data: {"timestamp": "2026-10-28T15:30:00Z"}

event: heartbeat
data: {"timestamp": "2026-10-28T15:30:15Z"}

event: heartbeat
data: {"timestamp": "2026-10-28T15:30:30Z"}

...

event: closed
data: {'reason': 'demo_timeout'}
```

**Current Implementation:**
- Heartbeat sent every 15 seconds
- Demo timeout after 5 heartbeats (75 seconds)
- No actual messages yet (agent pipeline integration pending)

---

## Database Verification

After completing the flow, verify data was persisted:

```sql
-- Connect to database
-- psql -U postgres -d bizsaathi -h localhost

-- Check public sessions
SELECT id, business_id, expires_at, ip_hash_sha256, created_at
FROM public_sessions
ORDER BY created_at DESC
LIMIT 5;

-- Check conversations
SELECT id, session_id, created_at
FROM conversations
WHERE session_id = 'YOUR_SESSION_ID';

-- Check messages
SELECT id, conversation_id, sender_type, content, created_at
FROM messages
WHERE conversation_id = (
  SELECT id FROM conversations WHERE session_id = 'YOUR_SESSION_ID'
)
ORDER BY created_at ASC;

-- Verify token is bcrypt hashed (should start with $2b$)
SELECT session_token_hash
FROM public_sessions
WHERE id = 'YOUR_SESSION_ID';
-- Example: $2b$12$abc123...
```

---

## Security Testing

### Test 1: Token Verification (bcrypt)

```powershell
# Valid token - should succeed
curl -X POST "http://localhost:8000/public/sessions/$session_id/messages" `
  -H "X-Session-Token: $token" `
  -H "Content-Type: application/json" `
  -d '{"content": "Test"}'

# Invalid token - should return 401
curl -X POST "http://localhost:8000/public/sessions/$session_id/messages" `
  -H "X-Session-Token: wrong_token_123" `
  -H "Content-Type: application/json" `
  -d '{"content": "Test"}'
```

### Test 2: Session Expiration

```sql
-- Manually expire a session
UPDATE public_sessions
SET expires_at = NOW() - INTERVAL '1 hour'
WHERE id = 'YOUR_SESSION_ID';

-- Now try to send a message - should return 410
```

### Test 3: Rate Limiting

```powershell
# Send 6 requests within 60 seconds (limit is 5/min)
for ($i=1; $i -le 6; $i++) {
  curl -X POST "http://localhost:8000/public/sessions/$session_id/messages" `
    -H "X-Session-Token: $token" `
    -H "Content-Type: application/json" `
    -d "{`"content`": `"Message $i`"}"
  Start-Sleep -Milliseconds 500
}
# 6th request should return 429
```

### Test 4: IP Privacy (SHA-256 hash)

```sql
-- Verify IP is hashed, not stored in plaintext
SELECT ip_hash_sha256 FROM public_sessions WHERE id = 'YOUR_SESSION_ID';
-- Should be 64-character hex string (SHA-256)
-- Example: 5d41402abc4b2a76b9719d911017c592ae9e5c8b91b6a6f6f6f6f6f6f6f6f6f6
```

---

## Performance Testing

### Concurrent Sessions

```powershell
# Create 10 concurrent sessions
1..10 | ForEach-Object -Parallel {
  curl -X POST http://localhost:8000/public/stores/my-shop/sessions `
    -H "Content-Type: application/json" `
    -d '{}'
} -ThrottleLimit 10
```

### Message Throughput

```powershell
# Send 100 messages sequentially
for ($i=1; $i -le 100; $i++) {
  $start = Get-Date
  curl -X POST "http://localhost:8000/public/sessions/$session_id/messages" `
    -H "X-Session-Token: $token" `
    -H "Content-Type: application/json" `
    -d "{`"content`": `"Load test message $i`"}" `
    -s | Out-Null
  $duration = (Get-Date) - $start
  Write-Host "Message $i : $($duration.TotalMilliseconds)ms"
}
```

---

## Troubleshooting

### Issue: "Store not found"

**Solution:**
```sql
-- Verify business exists
SELECT id, name, slug FROM businesses;

-- Create test business if needed
INSERT INTO businesses (name, slug, owner_email, created_at, updated_at)
VALUES ('Test Shop', 'test-shop', 'test@example.com', NOW(), NOW());
```

### Issue: "Session token validation failed"

**Causes:**
1. Token was modified or corrupted
2. Session was deleted from database
3. Token format is incorrect

**Debug:**
```sql
-- Check if session exists
SELECT id, session_token_hash FROM public_sessions WHERE id = 'YOUR_SESSION_ID';

-- Verify token hash format (should start with $2b$)
```

### Issue: SSE stream disconnects immediately

**Causes:**
1. Invalid token in query parameter
2. Session expired
3. CORS issues (if testing from different origin)

**Debug:**
```bash
# Check backend logs for errors
# Look for "Token verification failed" or "Session not found"
```

### Issue: Rate limit not working

**Current Implementation:**
- In-memory dictionary (resets on server restart)
- Per IP address (hashed)
- 5 messages per 60 seconds

**Note:** Production should use Redis for distributed rate limiting.

---

## API Endpoints Summary

| Method | Endpoint | Auth | Status |
|--------|----------|------|--------|
| GET | `/public/stores/{slug}` | None | ✅ COMPLETE |
| POST | `/public/stores/{slug}/sessions` | None | ✅ COMPLETE |
| POST | `/public/sessions/{id}/messages` | X-Session-Token | ✅ COMPLETE (pipeline pending) |
| GET | `/public/sessions/{id}/stream` | Query token | ✅ COMPLETE (message polling pending) |
| PATCH | `/public/sessions/{id}/feedback` | X-Session-Token | 🔲 FUTURE (501) |
| POST | `/public/sessions/{id}/order-draft` | X-Session-Token | 🔲 FUTURE (501) |

---

## Next Steps

1. **Agent Pipeline Integration:** Connect EP-E03 to LangGraph pipeline for actual AI responses
2. **Message Polling in SSE:** Implement database polling in EP-E04 to push new messages to clients
3. **Feedback API (EP-E05):** Allow customers to rate responses
4. **Order Draft API (EP-E07):** Generate order proposals from chat context
5. **Redis Rate Limiting:** Replace in-memory dict with Redis for production
6. **Telemetry:** Add OpenTelemetry tracing for observability

---

**Last Updated:** 2026-10-28  
**Implementation Status:** EP-E01 to EP-E04 complete (4/6 endpoints)  
**Test Coverage:** Integration tests pending (unit tests: 107/107 passing)  
**Security:** Token hashing (bcrypt), IP privacy (SHA-256), rate limiting (in-memory)
