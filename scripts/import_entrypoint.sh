#!/bin/bash
# DataFlow Product Import Entrypoint Script
# Manages the complete import process with error handling and logging

set -euo pipefail

# Configuration
DATABASE_URL="${DATABASE_URL:-postgresql://horme_user:secure_password_2024@postgres-import:5432/horme_db}"
BATCH_SIZE="${BATCH_SIZE:-1000}"
TEST_MODE="${TEST_MODE:-false}"
EXCEL_FILE="/app/data/ProductData (Top 3 Cats).xlsx"
MAX_RETRIES=3
RETRY_DELAY=10

# Logging setup
LOG_DIR="/app/logs"
REPORT_DIR="/app/reports"
mkdir -p "$LOG_DIR" "$REPORT_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_DIR/import_entrypoint.log"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$LOG_DIR/import_entrypoint.log" >&2
}

# Wait for database to be ready
wait_for_database() {
    log "Waiting for PostgreSQL database to be ready..."
    local retry_count=0
    
    while [ $retry_count -lt 30 ]; do
        if python -c "
import psycopg2
import sys
try:
    conn = psycopg2.connect('$DATABASE_URL')
    conn.close()
    print('Database is ready')
    sys.exit(0)
except Exception as e:
    print(f'Database not ready: {e}')
    sys.exit(1)
        "; then
            log "Database is ready!"
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        log "Database not ready, attempt $retry_count/30. Waiting 10 seconds..."
        sleep 10
    done
    
    log_error "Database failed to become ready after 300 seconds"
    return 1
}

# Check if Excel file exists
check_excel_file() {
    if [ ! -f "$EXCEL_FILE" ]; then
        log_error "Excel file not found: $EXCEL_FILE"
        log "Available files in /app/data:"
        ls -la /app/data/ || true
        return 1
    fi
    
    local file_size=$(stat -c%s "$EXCEL_FILE")
    log "Excel file found: $EXCEL_FILE (${file_size} bytes)"
    return 0
}

# Run DataFlow import with retries
run_dataflow_import() {
    local retry_count=0
    local import_args=""
    
    # Build import arguments
    if [ "$TEST_MODE" = "true" ]; then
        import_args="--test"
        log "Running in TEST MODE (first 100 rows only)"
    fi
    
    import_args="$import_args --batch-size $BATCH_SIZE"
    import_args="$import_args --excel-file $EXCEL_FILE"
    import_args="$import_args --database-url $DATABASE_URL"
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        log "Starting DataFlow import attempt $((retry_count + 1))/$MAX_RETRIES..."
        log "Command: python scripts/dataflow_product_import.py $import_args"
        
        if python scripts/dataflow_product_import.py $import_args; then
            log "DataFlow import completed successfully!"
            return 0
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $MAX_RETRIES ]; then
                log_error "Import attempt $retry_count failed. Retrying in $RETRY_DELAY seconds..."
                sleep $RETRY_DELAY
            else
                log_error "All import attempts failed after $MAX_RETRIES tries"
                return 1
            fi
        fi
    done
}

# Generate final summary
generate_summary() {
    log "Generating import summary..."
    
    # Count files in reports directory
    local report_count=$(find "$REPORT_DIR" -name "*.txt" -o -name "*.json" | wc -l)
    log "Generated $report_count report files in $REPORT_DIR"
    
    # List report files
    if [ $report_count -gt 0 ]; then
        log "Report files:"
        ls -la "$REPORT_DIR"
    fi
    
    # Check log file size
    local log_file="$LOG_DIR/dataflow_import.log"
    if [ -f "$log_file" ]; then
        local log_size=$(stat -c%s "$log_file")
        log "Import log file: $log_file (${log_size} bytes)"
    fi
}

# Main execution
main() {
    log "=========================================="
    log "DataFlow Product Import Starting"
    log "=========================================="
    log "Configuration:"
    log "  Database URL: $DATABASE_URL"
    log "  Batch Size: $BATCH_SIZE"
    log "  Test Mode: $TEST_MODE"
    log "  Excel File: $EXCEL_FILE"
    log "  Max Retries: $MAX_RETRIES"
    log "=========================================="
    
    # Pre-flight checks
    if ! wait_for_database; then
        log_error "Database readiness check failed"
        exit 1
    fi
    
    if ! check_excel_file; then
        log_error "Excel file check failed"
        exit 1
    fi
    
    # Verify Python environment
    log "Verifying Python environment..."
    python -c "
import sys
print(f'Python version: {sys.version}')

try:
    import pandas
    print(f'Pandas version: {pandas.__version__}')
except ImportError as e:
    print(f'Pandas import failed: {e}')
    sys.exit(1)

try:
    from dataflow import DataFlow
    print('DataFlow import successful')
except ImportError as e:
    print(f'DataFlow import failed: {e}')
    sys.exit(1)

try:
    from kailash.workflow.builder import WorkflowBuilder
    from kailash.runtime.local import LocalRuntime
    print('Kailash imports successful')
except ImportError as e:
    print(f'Kailash imports failed: {e}')
    sys.exit(1)

print('All required packages are available')
"
    
    if [ $? -ne 0 ]; then
        log_error "Python environment verification failed"
        exit 1
    fi
    
    # Run the import
    if run_dataflow_import; then
        log "DataFlow import process completed successfully!"
        generate_summary
        
        log "=========================================="
        log "DataFlow Product Import Completed"
        log "Status: SUCCESS"
        log "=========================================="
        
        exit 0
    else
        log_error "DataFlow import process failed!"
        generate_summary
        
        log "=========================================="
        log "DataFlow Product Import Completed"
        log "Status: FAILURE"
        log "=========================================="
        
        exit 1
    fi
}

# Trap signals for clean shutdown
trap 'log "Received shutdown signal, cleaning up..."; exit 130' INT TERM

# Run main function
main "$@"