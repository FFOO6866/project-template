# Frontend Quick Start Guide

## 1. Create Your Environment File (30 seconds)

```bash
# Copy the template
cp .env.example .env.local
```

## 2. Configure for Your Setup

Edit `.env.local` and choose your configuration:

### Local Development (Backend on localhost)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001
NEXT_PUBLIC_MCP_URL=http://localhost:3002
```

### Docker Development (All services in containers)
```env
NEXT_PUBLIC_API_URL=http://api:8000
NEXT_PUBLIC_WEBSOCKET_URL=ws://websocket:8001
NEXT_PUBLIC_MCP_URL=http://mcp:3002
```

## 3. Validate Your Configuration (10 seconds)

```bash
npm run validate-env
```

Expected output:
```
✅ All checks passed! Environment is properly configured.
```

## 4. Start Development (10 seconds)

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Common Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production (validates first) |
| `npm run start` | Start production server |
| `npm run validate-env` | Validate environment configuration |
| `npm run lint` | Run linter |

## Environment Files

| File | Purpose | Commit to Git? |
|------|---------|----------------|
| `.env.example` | Template with all variables | ✅ Yes |
| `.env.local` | Your local configuration | ❌ No (gitignored) |
| `.env.production` | Production configuration | ❌ No (set via platform) |

## Quick Troubleshooting

### Problem: "API URL is required"
**Solution:** Set `NEXT_PUBLIC_API_URL` in `.env.local`

### Problem: "Failed to fetch"
**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify `NEXT_PUBLIC_API_URL` matches backend port
3. For Docker: use `http://api:8000` not `http://localhost:8000`

### Problem: "WebSocket connection failed"
**Solution:**
1. Check WebSocket server is running on port 8001
2. Verify `NEXT_PUBLIC_WEBSOCKET_URL` is correct
3. For production: use `wss://` not `ws://`

### Problem: Environment variables not updating
**Solution:**
1. Restart dev server: `npm run dev`
2. Clear cache: `rm -rf .next && npm run dev`

## Feature Flags (Optional)

Disable features you don't need:

```env
NEXT_PUBLIC_ENABLE_CHAT=false              # Disable chat
NEXT_PUBLIC_ENABLE_UPLOAD=false            # Disable file upload
NEXT_PUBLIC_ENABLE_AI_RECOMMENDATIONS=false # Disable AI features
```

## File Upload Configuration (Optional)

Customize file upload limits (must match backend):

```env
NEXT_PUBLIC_MAX_FILE_SIZE=104857600        # 100MB in bytes
NEXT_PUBLIC_MAX_FILE_SIZE_MB=100           # 100MB for UI display
```

## Production Deployment

For production, ensure:

1. **Use secure protocols:**
   ```env
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   NEXT_PUBLIC_WEBSOCKET_URL=wss://your-domain.com/ws
   ```

2. **Disable debug mode:**
   ```env
   NEXT_PUBLIC_DEBUG=false
   NEXT_PUBLIC_LOG_LEVEL=error
   ```

3. **Enable monitoring:**
   ```env
   NEXT_PUBLIC_ENABLE_ERROR_TRACKING=true
   NEXT_PUBLIC_SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
   ```

## Need More Help?

- **Complete Guide:** See `ENV_SETUP_GUIDE.md`
- **All Variables:** See `.env.example` with detailed comments
- **Implementation Details:** See `ENVIRONMENT_CONFIGURATION_COMPLETE.md`
- **WebSocket Setup:** See `hooks/WEBSOCKET_QUICK_REFERENCE.md`

## Validation Script Output Explained

| Symbol | Meaning |
|--------|---------|
| ✅ | Check passed |
| ❌ | Error - must fix |
| ⚠️  | Warning - review recommended |
| ℹ️  | Information |

## Backend Configuration

Ensure backend is configured properly:
- **File:** `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\.env.example`
- **Ports:** API=8000, WebSocket=8001, MCP=3002
- **CORS:** Must include frontend URL (http://localhost:3000)

## Success Checklist

- [ ] `.env.local` created from `.env.example`
- [ ] Environment variables configured for your setup
- [ ] Validation passes: `npm run validate-env` shows ✅
- [ ] Backend is running and accessible
- [ ] Dev server starts: `npm run dev` succeeds
- [ ] Frontend loads at http://localhost:3000
- [ ] API connection works (check browser console)
- [ ] WebSocket connection works (check browser console)

---

**Time to first run:** ~1 minute

**Questions?** Check the detailed guides in the frontend folder.
