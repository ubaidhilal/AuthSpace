# AuthSpace upgraded starter

This is a replacement starter for the supplied React + FastAPI + Google OAuth + Composio MCP app. It adds database-backed users, conversations and messages; conversation-specific agent sessions; ownership checks; structured Server-Sent Events; environment-based CORS/OAuth settings; and a React UI that loads persisted history.

## Project layout

- `backend/app/main.py` — FastAPI app, middleware, startup
- `backend/app/api/auth.py` — Google OAuth and logout
- `backend/app/api/dependencies.py` — JWT cookie authentication and active-user lookup
- `backend/app/api/chat.py` — conversation CRUD and streamed chat
- `backend/app/models/` — SQLAlchemy user/conversation/message models
- `backend/app/services/agent_service.py` — Composio MCP agent creation
- `frontend/src/App.jsx` — React login/chat UI and SSE reader

## 1. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Paste a generated value into `SECRET_KEY`, and generate a different value for `SESSION_SECRET`. Set these values in `.env`:

- `GOOGLE_CLIENT_ID_1`
- `GOOGLE_CLIENT_SECRET_1`
- `GOOGLE_REDIRECT_URI`
- `FRONTEND_URL`
- `COMPOSIO_API_KEY`
- `MODEL`

Google Cloud Console **Authorized redirect URIs** must include exactly the value of `GOOGLE_REDIRECT_URI`. For local use, the default is `http://localhost:8000/google/callback`. For another computer, use a backend host/IP reachable from that computer and register that exact callback URI; use HTTPS for production. Do not use `localhost` in a URL that is intended to reach another computer.

Start the backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The default database is a local SQLite file `authspace.db`. To use PostgreSQL, set for example:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/authspace
```

Create the database first. For production, use Alembic migrations instead of relying on `create_all` at startup.

## 2. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL` to a backend URL reachable from the browser. For LAN access, use the backend computer's LAN IP (not `localhost`) and add the frontend origin to `CORS_ORIGINS` in backend `.env`. Example if frontend is hosted at `http://192.168.1.4:5173`:

```env
VITE_API_BASE_URL=http://192.168.1.10:8000
```

and backend:

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://192.168.1.4:5173
FRONTEND_URL=http://192.168.1.4:5173
GOOGLE_REDIRECT_URI=http://192.168.1.10:8000/google/callback
```

Replace example IPs with your actual addresses. The Google callback URI must be registered in Google Cloud Console. OAuth over plain HTTP is for local development only; use HTTPS for deployment.

## 3. API overview

- `GET /health`
- `GET /me`
- `GET /google/login`
- `GET /google/callback`
- `POST /google/logout`
- `GET /conversations`
- `POST /conversations`
- `GET /conversations/{conversation_id}`
- `DELETE /conversations/{conversation_id}`
- `POST /chat` with `{ "question": "...", "conversation_id": "optional UUID" }`

`/chat` returns SSE events: `token`, `done`, and `error`. The frontend parses those events and refreshes persistent history.

## Important security notes

- `MCP_REQUIRE_APPROVAL=never` is retained as the development default to match the supplied app's behavior. It is **not** sufficient protection for sensitive actions. Configure authorization/approval policies in Composio and your app before enabling email sending, deleting data, or other consequential actions. The starter does not implement a human-in-the-loop approval UI.
- The logout endpoint deletes the browser cookie but does not revoke an already-copied stateless JWT; it remains usable until expiry. If immediate revocation is required, add server-side sessions/token revocation.
- Use HTTPS, `COOKIE_SECURE=true`, a strong secret, database migrations, backups, and production logging before deployment.
- The starter validates that users own conversations, but you should add automated tests, rate limiting, and a robust operational policy before public exposure.
- The database stores Google users keyed by Google's stable `sub`. It does not automatically merge accounts based only on matching email addresses.

## Version compatibility

The Composio and OpenAI Agents SDK APIs can change. If your installed SDK versions differ, pin compatible versions and verify `Composio.sessions.create`, `HostedMCPTool`, and `Runner.run_streamed` against the documentation for those exact versions.
