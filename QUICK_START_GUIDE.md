# 🚀 Quick Start Guide - Get Running in 5 Minutes

## The Problem

The Docker setup is complex with custom builds. Here's the **fastest way** to get the application running:

---

## ✅ Simple Method (Recommended)

### Step 1: Run the Quick Start Script

```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov
quick-start.bat
```

This will:
1. Start PostgreSQL in Docker (port 5434)
2. Start Redis in Docker (port 6381)
3. Start Backend API with Python (port 8002)

**That's it!** The backend will be running at **http://localhost:8002**

---

### Step 2: Test the Backend

Open a browser or use curl:

```bash
curl http://localhost:8002/api/health
```

Expected response:
```json
{"status":"healthy"}
```

---

### Step 3: Access API Documentation

Open: **http://localhost:8002/docs**

This shows all available API endpoints and lets you test them interactively.

---

### Step 4: Start Frontend (Optional)

If you want the full UI:

```bash
cd frontend
npm install  # Only needed first time
npm run dev
```

Then open: **http://localhost:3000**

---

## 🛑 Stop Services

To stop everything:

1. **Stop Backend**: Press `Ctrl+C` in the terminal running `quick-start.bat`

2. **Stop Databases**:
```bash
docker stop horme-postgres horme-redis
```

---

## 📊 What's Running

| Service | Port | URL |
|---------|------|-----|
| Backend API | 8002 | http://localhost:8002 |
| API Docs | 8002 | http://localhost:8002/docs |
| Health Check | 8002 | http://localhost:8002/api/health |
| PostgreSQL | 5434 | localhost:5434 |
| Redis | 6381 | localhost:6381 |
| Frontend | 3000 | http://localhost:3000 (if running) |

---

## 🔑 Admin Login

Once the frontend is running:

- **Email**: `admin@yourdomain.com`
- **Password**: `2Cbs_Ehbz4wLTOVW8vS6KmoRsLOpl7xLJGo0TlG85Q0`

---

## 🐛 Troubleshooting

### "Module not found" errors

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Or use uv (faster):

```bash
pip install uv
uv pip install -r requirements.txt
```

### "Port already in use"

Kill the process using the port:

```bash
# Check what's using port 8002
netstat -ano | findstr :8002

# Kill it (replace PID with actual number)
taskkill /PID <PID> /F
```

### "Cannot connect to database"

Make sure Docker Desktop is running, then:

```bash
docker ps
```

You should see `horme-postgres` and `horme-redis` running.

If not, restart them:

```bash
docker stop horme-postgres horme-redis
quick-start.bat
```

### Frontend shows "Cannot reach backend"

1. Verify backend is running: http://localhost:8002/api/health
2. Check `frontend/.env.local` contains:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8002
   NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001
   ```

---

## 📖 What You Can Do Now

### 1. Test API Endpoints

Visit http://localhost:8002/docs and try:
- **POST /api/auth/login** - Login with admin credentials
- **GET /api/dashboard** - Get dashboard data
- **GET /api/documents** - List documents
- **POST /api/files/upload** - Upload documents

### 2. Check Database

```bash
docker exec -it horme-postgres psql -U horme_user -d horme_db

# Inside PostgreSQL:
\dt  # List tables
SELECT * FROM users;  # See users
\q   # Quit
```

### 3. Monitor Logs

Backend logs appear in the terminal where you ran `quick-start.bat`

Frontend logs appear in the terminal where you ran `npm run dev`

---

## 🎯 Next Steps

1. **Explore API**: http://localhost:8002/docs
2. **Start Frontend**: `cd frontend && npm run dev`
3. **Upload Documents**: Use the frontend UI
4. **Test Chat**: Try the AI assistant feature

---

## 💡 Why This Method Works

- **No complex Docker builds** - Uses standard images
- **Fast startup** - Databases start in seconds
- **Easy debugging** - See all logs directly
- **Hot reload** - Backend reloads on code changes (`--reload` flag)

---

## 🔄 Alternative: Full Docker Method

If you prefer Docker for everything:

1. **Fix the postgres build issue** (remove pgvector requirements)
2. **Use pre-built images** instead of building
3. **Or use docker-compose.test.yml** instead (simpler setup)

For now, the quick-start method above is **fastest and most reliable**.

---

## ✅ Confirmation

If everything is working, you should see:

1. **Terminal**: Backend logs showing "Uvicorn running on http://0.0.0.0:8002"
2. **Browser** (http://localhost:8002/api/health): `{"status":"healthy"}`
3. **Browser** (http://localhost:8002/docs): Interactive API documentation

**You're all set!** 🎉

---

Need help? Check the logs in the terminal or see `START_SERVICES.md` for more details.
