# CRIT-003-Port-Connection-Diagnosis

## Description
Diagnose and fix port 3000 connection timeout issues that prevent successful deployment of production services despite ports showing as LISTENING.

## Current Critical Issue
- Port 3000 shows LISTENING status but connections timeout
- Services appear to be running but are unreachable
- Network configuration preventing proper service communication
- WSL2 port forwarding may not be working correctly

## Acceptance Criteria
- [ ] Port 3000 accepts connections without timeout
- [ ] All production service ports (8000-8002, 5432, 6379) accessible
- [ ] WSL2 to Windows port forwarding working correctly
- [ ] No firewall blocking container traffic
- [ ] Service health checks passing
- [ ] End-to-end connectivity verified

## Dependencies
- CRIT-001: Docker Desktop installed
- CRIT-002: Docker daemon verified and running
- WSL2 properly configured

## Risk Assessment
- **HIGH**: WSL2 networking complexity may require advanced troubleshooting
- **HIGH**: Windows firewall blocking container communications
- **MEDIUM**: Port conflicts with existing services
- **MEDIUM**: Docker network configuration issues
- **LOW**: Need to restart services after configuration changes

## Subtasks
- [ ] Analyze current port binding configuration (Est: 5min)
- [ ] Check WSL2 port forwarding settings (Est: 10min)
- [ ] Configure Windows firewall for Docker (Est: 10min)
- [ ] Test container networking and connectivity (Est: 10min)
- [ ] Verify Docker network bridge configuration (Est: 5min)

## Testing Requirements
- [ ] Network tests: All ports accessible from host
- [ ] Integration tests: Container-to-container communication
- [ ] E2E tests: Full service connectivity chain

## Diagnostic Commands
```bash
# 1. Check current port status
netstat -an | findstr "3000\|8000\|8001\|8002\|5432\|6379"
netstat -ano | findstr LISTENING

# 2. Test port connectivity
telnet localhost 3000
curl -v --connect-timeout 5 http://localhost:3000
curl -v --connect-timeout 5 http://localhost:8000

# 3. Check Docker network configuration
docker network ls
docker network inspect bridge
docker network inspect horme-network

# 4. WSL2 networking diagnostics
wsl hostname -I
wsl cat /etc/resolv.conf
```

## WSL2 Port Forwarding Fix
```powershell
# Check WSL2 IP address
wsl hostname -I

# Manual port forwarding (if needed)
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=172.xx.xx.xx

# Check existing port proxies
netsh interface portproxy show all

# Remove port proxy if needed
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0
```

## Windows Firewall Configuration
```powershell
# Create comprehensive firewall rules for Docker
New-NetFirewallRule -DisplayName "Docker WSL2" -Direction Inbound -Protocol TCP -LocalPort 2375,2376 -Action Allow
New-NetFirewallRule -DisplayName "Docker Services" -Direction Inbound -Protocol TCP -LocalPort 3000,8000,8001,8002 -Action Allow
New-NetFirewallRule -DisplayName "Docker Database" -Direction Inbound -Protocol TCP -LocalPort 5432,6379 -Action Allow
New-NetFirewallRule -DisplayName "Docker HTTP" -Direction Inbound -Protocol TCP -LocalPort 80,443 -Action Allow

# Check if rules are active
Get-NetFirewallRule -DisplayName "*Docker*" | Select-Object DisplayName,Enabled,Direction,Action
```

## Docker Network Troubleshooting
```bash
# 1. Create test container on specific port
docker run --rm -d --name test-nginx -p 3000:80 nginx:alpine

# 2. Test connectivity to test container
curl http://localhost:3000

# 3. Check container networking
docker exec test-nginx ip addr show
docker port test-nginx

# 4. Clean up test
docker stop test-nginx
```

## Service-Specific Port Testing
```bash
# Test MCP server port (3000)
curl -v http://localhost:3000/health 2>&1

# Test Nexus Gateway ports (8000-8002)
curl -v http://localhost:8000/health 2>&1
curl -v http://localhost:8001/health 2>&1
curl -v http://localhost:8002/health 2>&1

# Test database connectivity
telnet localhost 5432
telnet localhost 6379
```

## Expected Resolution Steps
1. Identify root cause of connection timeouts
2. Fix WSL2 port forwarding if needed
3. Configure Windows firewall rules
4. Restart Docker services
5. Verify all ports accessible

## Expected Resolution Time
30 minutes maximum

## Definition of Done
- [ ] All service ports accessible without timeout
- [ ] WSL2 port forwarding working correctly
- [ ] Windows firewall properly configured for Docker
- [ ] Docker network bridge functional
- [ ] Test containers can be reached from host
- [ ] Production services ready for deployment

## Next Actions After Completion
1. Proceed to CRIT-004: Build all required Docker images
2. Deploy production services using docker-compose
3. Run comprehensive connectivity tests