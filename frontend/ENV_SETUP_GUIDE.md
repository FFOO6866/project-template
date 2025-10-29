# Frontend Environment Setup Guide

## Quick Start

### 1. Create Your Local Environment File

```bash
# Copy the example file
cp .env.example .env.local
```

### 2. Configure for Your Environment

Choose the appropriate configuration based on your setup:

#### Option A: Local Development (Backend Running Locally)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001
NEXT_PUBLIC_MCP_URL=http://localhost:3002
```

#### Option B: Docker Development (All Services in Docker)

```env
NEXT_PUBLIC_API_URL=http://api:8000
NEXT_PUBLIC_WEBSOCKET_URL=ws://websocket:8001
NEXT_PUBLIC_MCP_URL=http://mcp:3002
```

#### Option C: Production Deployment

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WEBSOCKET_URL=wss://your-domain.com/ws
NEXT_PUBLIC_MCP_URL=https://mcp.yourdomain.com
NEXT_PUBLIC_DEBUG=false
NEXT_PUBLIC_LOG_LEVEL=error
```

### 3. Start Development Server

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

## Essential Configuration Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API endpoint | `http://localhost:8000` |
| `NEXT_PUBLIC_WEBSOCKET_URL` | WebSocket server for chat | `ws://localhost:8001` |
| `NEXT_PUBLIC_MCP_URL` | MCP server endpoint | `http://localhost:3002` |

### File Upload Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_MAX_FILE_SIZE` | `52428800` | Max upload size in bytes (50MB) |
| `NEXT_PUBLIC_MAX_FILE_SIZE_MB` | `50` | Human-readable size for UI |
| `NEXT_PUBLIC_ALLOWED_FILE_EXTENSIONS` | `pdf,docx,xlsx,...` | Allowed file types |

**Important:** These values must match the backend configuration in `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\.env.example`:
- Backend `MAX_FILE_SIZE` = Frontend `NEXT_PUBLIC_MAX_FILE_SIZE`
- Backend `ALLOWED_EXTENSIONS` = Frontend `NEXT_PUBLIC_ALLOWED_FILE_EXTENSIONS`

### Feature Flags

Enable or disable features without code changes:

```env
NEXT_PUBLIC_ENABLE_CHAT=true              # Chat interface
NEXT_PUBLIC_ENABLE_UPLOAD=true            # File uploads
NEXT_PUBLIC_ENABLE_REPORTS=true           # Analytics/reports
NEXT_PUBLIC_ENABLE_AI_RECOMMENDATIONS=true # AI features
NEXT_PUBLIC_ENABLE_NOTIFICATIONS=true     # Real-time notifications
NEXT_PUBLIC_ENABLE_SEARCH=true            # Search functionality
NEXT_PUBLIC_ENABLE_QUOTATIONS=true        # Quotation generation
```

### Chat Configuration

Fine-tune chat behavior:

```env
NEXT_PUBLIC_CHAT_MAX_MESSAGE_LENGTH=5000        # Max chars per message
NEXT_PUBLIC_CHAT_HISTORY_LIMIT=50               # Messages to load
NEXT_PUBLIC_CHAT_AUTO_RECONNECT=true            # Auto-reconnect on disconnect
NEXT_PUBLIC_CHAT_RECONNECT_DELAY=3000           # Wait 3s before reconnect
NEXT_PUBLIC_CHAT_MAX_RECONNECT_ATTEMPTS=5       # Max reconnect tries
```

## Environment-Specific Setup

### Development Environment

1. **Backend Port Conflicts:** If port 8000 is in use, update to match backend:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8002
   ```

2. **Enable Debug Mode:**
   ```env
   NEXT_PUBLIC_DEBUG=true
   NEXT_PUBLIC_LOG_LEVEL=debug
   ```

3. **Test with Mock Data:** Enable all features:
   ```env
   NEXT_PUBLIC_ENABLE_CHAT=true
   NEXT_PUBLIC_ENABLE_UPLOAD=true
   NEXT_PUBLIC_ENABLE_REPORTS=true
   ```

### Docker Environment

1. **Use Docker Service Names** instead of localhost:
   ```env
   NEXT_PUBLIC_API_URL=http://api:8000
   NEXT_PUBLIC_WEBSOCKET_URL=ws://websocket:8001
   NEXT_PUBLIC_MCP_URL=http://mcp:3002
   ```

2. **Network Configuration:** Docker Compose handles DNS resolution automatically

3. **Build Arguments:** Pass environment variables to Docker build:
   ```dockerfile
   # From Dockerfile
   ARG NEXT_PUBLIC_API_URL
   ARG NEXT_PUBLIC_MCP_URL
   ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
   ENV NEXT_PUBLIC_MCP_URL=$NEXT_PUBLIC_MCP_URL
   ```

### Production Environment

1. **Security Hardening:**
   ```env
   NEXT_PUBLIC_DEBUG=false
   NEXT_PUBLIC_LOG_LEVEL=error
   NEXT_PUBLIC_ENABLE_REACT_QUERY_DEVTOOLS=false
   ```

2. **Use Secure Protocols:**
   ```env
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   NEXT_PUBLIC_WEBSOCKET_URL=wss://your-domain.com/ws  # Note: wss:// not ws://
   ```

3. **Enable Monitoring:**
   ```env
   NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
   NEXT_PUBLIC_ENABLE_ERROR_TRACKING=true
   NEXT_PUBLIC_SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
   ```

## Common Issues and Solutions

### Issue: "Failed to fetch" or "Network Error"

**Cause:** API URL is incorrect or backend is not running

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `NEXT_PUBLIC_API_URL` matches backend port
3. For Docker: use service name `http://api:8000` not `localhost`

### Issue: "WebSocket connection failed"

**Cause:** WebSocket URL is incorrect or WebSocket server is down

**Solution:**
1. Verify WebSocket server is running on port 8001
2. Check `NEXT_PUBLIC_WEBSOCKET_URL` is set correctly
3. For production: ensure using `wss://` not `ws://`
4. Check firewall/proxy settings allow WebSocket connections

### Issue: "File too large" error

**Cause:** Frontend and backend file size limits don't match

**Solution:**
1. Ensure `NEXT_PUBLIC_MAX_FILE_SIZE` matches backend `MAX_FILE_SIZE`
2. Convert MB to bytes: 50MB = 52428800 bytes
3. Update both `.env.local` (frontend) and `.env.production` (backend)

### Issue: "File type not allowed"

**Cause:** File extension not in allowed list

**Solution:**
1. Add extension to `NEXT_PUBLIC_ALLOWED_FILE_EXTENSIONS`
2. Add corresponding MIME type to `NEXT_PUBLIC_ALLOWED_MIME_TYPES`
3. Ensure backend also allows this file type

### Issue: Environment variables not updating

**Cause:** Next.js embeds `NEXT_PUBLIC_*` variables at build time

**Solution:**
1. Restart dev server: `npm run dev`
2. For production builds: rebuild the application
3. Clear `.next` cache: `rm -rf .next && npm run dev`

## Validation Checklist

Before deploying, verify:

- [ ] `.env.local` created from `.env.example`
- [ ] `NEXT_PUBLIC_API_URL` is accessible from browser
- [ ] `NEXT_PUBLIC_WEBSOCKET_URL` is correct protocol (`ws://` or `wss://`)
- [ ] File upload limits match backend configuration
- [ ] Debug mode disabled for production (`NEXT_PUBLIC_DEBUG=false`)
- [ ] Error tracking configured for production (Sentry, etc.)
- [ ] Analytics enabled for production (Google Analytics, etc.)
- [ ] All feature flags set appropriately
- [ ] CORS configured on backend for frontend domain

## Testing Your Configuration

### 1. Test API Connection

```bash
# From browser console
fetch(process.env.NEXT_PUBLIC_API_URL + '/health')
  .then(r => r.json())
  .then(console.log)
```

### 2. Test WebSocket Connection

```bash
# From browser console
const ws = new WebSocket(process.env.NEXT_PUBLIC_WEBSOCKET_URL)
ws.onopen = () => console.log('Connected')
ws.onerror = (e) => console.error('Error:', e)
```

### 3. Verify Environment Variables

```bash
# From browser console
console.log('API URL:', process.env.NEXT_PUBLIC_API_URL)
console.log('WS URL:', process.env.NEXT_PUBLIC_WEBSOCKET_URL)
console.log('Debug:', process.env.NEXT_PUBLIC_DEBUG)
```

## Security Best Practices

### DO:
- ✅ Use `.env.local` for local development
- ✅ Set production variables via deployment platform
- ✅ Use `wss://` (secure WebSocket) in production
- ✅ Disable debug mode in production
- ✅ Use environment-specific values

### DON'T:
- ❌ Commit `.env.local` to version control
- ❌ Put secrets in `NEXT_PUBLIC_*` variables (they're exposed to browser)
- ❌ Use `ws://` (insecure) in production
- ❌ Enable debug mode in production
- ❌ Hardcode URLs in code

## Additional Resources

- **Backend Configuration:** `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\.env.example`
- **Docker Configuration:** `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\docker-compose.production.yml`
- **WebSocket Guide:** `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\frontend\hooks\WEBSOCKET_QUICK_REFERENCE.md`
- **Next.js Environment Variables:** https://nextjs.org/docs/app/building-your-application/configuring/environment-variables

## Support

For issues or questions:
1. Check this guide first
2. Review backend logs: `docker logs horme-api`
3. Review WebSocket logs: `docker logs horme-websocket`
4. Check browser console for errors
5. Verify network connectivity between services
