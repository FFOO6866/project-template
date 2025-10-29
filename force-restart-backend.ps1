# Force Restart Backend - PowerShell Script
Write-Host "======================================"
Write-Host "Force Restarting Backend API Server"
Write-Host "======================================"
Write-Host ""

# Step 1: Kill all processes on port 8002
Write-Host "[1/5] Finding processes on port 8002..."
$processes = Get-NetTCPConnection -LocalPort 8002 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($processes) {
    foreach ($pid in $processes) {
        Write-Host "Killing process $pid..."
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "No processes found on port 8002"
}

# Step 2: Wait for processes to die
Write-Host "[2/5] Waiting for cleanup..."
Start-Sleep -Seconds 5

# Step 3: Verify port is free
Write-Host "[3/5] Verifying port 8002 is available..."
$stillRunning = Get-NetTCPConnection -LocalPort 8002 -ErrorAction SilentlyContinue

if ($stillRunning) {
    Write-Host "ERROR: Port 8002 is still in use!"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Port 8002 is now available"

# Step 4: Load environment variables
Write-Host "[4/5] Loading environment variables..."
$envFile = Get-Content .env -ErrorAction Stop
foreach ($line in $envFile) {
    if ($line -notmatch '^#' -and $line -match '=') {
        $parts = $line -split '=', 2
        $key = $parts[0].Trim()
        $value = $parts[1].Trim()
        [Environment]::SetEnvironmentVariable($key, $value, 'Process')
    }
}

# Set database variables
[Environment]::SetEnvironmentVariable('DB_HOST', 'localhost', 'Process')
[Environment]::SetEnvironmentVariable('DB_PORT', '5434', 'Process')
[Environment]::SetEnvironmentVariable('DB_NAME', 'horme_db', 'Process')
[Environment]::SetEnvironmentVariable('DB_USER', 'horme_user', 'Process')

# Step 5: Start backend
Write-Host "[5/5] Starting backend server..."
Write-Host ""
Write-Host "Backend starting on http://0.0.0.0:8002"
Write-Host "Press Ctrl+C to stop"
Write-Host ""

python -m uvicorn src.nexus_backend_api:app --host 0.0.0.0 --port 8002 --reload
