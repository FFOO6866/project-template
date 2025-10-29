# Docker Compose Production Fix Required

## Issue
The `websocket_logs` volume was added in the wrong location in `docker-compose.production.yml` due to automatic file modifications.

## Current State (INCORRECT)
```yaml
postgres_exporter:
  # ... config ...
  networks:
    - horme_network
  websocket_logs:           # ❌ WRONG LOCATION
    driver: local
    name: horme_websocket_logs
  profiles:
    - monitoring
```

## Required Fix
Move `websocket_logs` to the `volumes:` section at the bottom of the file.

### Steps to Fix

1. Open `docker-compose.production.yml`

2. Find and REMOVE these lines (around line 353-356):
```yaml
  websocket_logs:
    driver: local
    name: horme_websocket_logs
```

3. Add them in the correct location under `volumes:` section (around line 419, after `api_logs:`):
```yaml
volumes:
  postgres_data:
    driver: local
    name: horme_postgres_data
  # ... other volumes ...
  api_logs:
    driver: local
    name: horme_api_logs
  websocket_logs:           # ✅ ADD HERE
    driver: local
    name: horme_websocket_logs
  nginx_logs:
    driver: local
    name: horme_nginx_logs
  uploads:
    driver: local
    name: horme_uploads
```

## Verification

After fixing, verify the configuration:

```bash
# Validate docker-compose file
docker-compose -f docker-compose.production.yml config

# Check for syntax errors
echo $?  # Should output 0 if successful
```

## Alternative: Use Provided Fixed File

If you prefer, you can use this corrected volumes section:

```yaml
volumes:
  postgres_data:
    driver: local
    name: horme_postgres_data
  postgres_backups:
    driver: local
    name: horme_postgres_backups
  postgres_logs:
    driver: local
    name: horme_postgres_logs
  redis_data:
    driver: local
    name: horme_redis_data
  redis_logs:
    driver: local
    name: horme_redis_logs
  neo4j_data:
    driver: local
    name: horme_neo4j_data
  neo4j_logs:
    driver: local
    name: horme_neo4j_logs
  neo4j_import:
    driver: local
    name: horme_neo4j_import
  neo4j_plugins:
    driver: local
    name: horme_neo4j_plugins
  prometheus_data:
    driver: local
    name: horme_prometheus_data
  grafana_data:
    driver: local
    name: horme_grafana_data
  api_logs:
    driver: local
    name: horme_api_logs
  websocket_logs:
    driver: local
    name: horme_websocket_logs
  nginx_logs:
    driver: local
    name: horme_nginx_logs
  uploads:
    driver: local
    name: horme_uploads
```

## After Fixing

1. Validate configuration:
   ```bash
   docker-compose -f docker-compose.production.yml config
   ```

2. Build services:
   ```bash
   docker-compose -f docker-compose.production.yml build
   ```

3. Start services:
   ```bash
   docker-compose -f docker-compose.production.yml up -d
   ```

## Status
⚠️ **MANUAL FIX REQUIRED BEFORE DEPLOYMENT**
