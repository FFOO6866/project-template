#!/bin/bash
# Automated PostgreSQL backup script for Horme POV production

set -e

# Configuration
BACKUP_DIR="/backups"
DB_HOST="postgres"
DB_PORT="5432"
DB_NAME="${POSTGRES_DB:-horme_db}"
DB_USER="${POSTGRES_USER:-horme_user}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="horme_backup_${TIMESTAMP}.sql"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Retention policy (keep last 30 days)
RETENTION_DAYS=30

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${BACKUP_DIR}/backup.log"
}

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

log "Starting PostgreSQL backup for database: ${DB_NAME}"

# Check if database is accessible
if ! pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}"; then
    log "ERROR: Database is not accessible"
    exit 1
fi

# Create backup
log "Creating backup: ${BACKUP_FILE}"
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    --no-password \
    --verbose \
    --format=custom \
    --compress=9 \
    --file="${BACKUP_PATH}" 2>&1 | tee -a "${BACKUP_DIR}/backup.log"

# Check if backup was successful
if [ $? -eq 0 ] && [ -f "${BACKUP_PATH}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
    log "Backup completed successfully: ${BACKUP_FILE} (${BACKUP_SIZE})"
    
    # Create a symlink to the latest backup
    ln -sf "${BACKUP_FILE}" "${BACKUP_DIR}/latest_backup.sql"
    
    # Compress older backups (older than 1 day)
    find "${BACKUP_DIR}" -name "horme_backup_*.sql" -type f -mtime +1 ! -name "*gz" -exec gzip {} \;
    
    # Clean up old backups
    log "Cleaning up backups older than ${RETENTION_DAYS} days"
    find "${BACKUP_DIR}" -name "horme_backup_*.sql*" -type f -mtime +${RETENTION_DAYS} -delete
    
    # Log backup statistics
    TOTAL_BACKUPS=$(find "${BACKUP_DIR}" -name "horme_backup_*" -type f | wc -l)
    TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
    log "Backup retention: ${TOTAL_BACKUPS} backups, total size: ${TOTAL_SIZE}"
    
else
    log "ERROR: Backup failed"
    exit 1
fi

# Verify backup integrity
log "Verifying backup integrity"
pg_restore --list "${BACKUP_PATH}" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log "Backup verification successful"
else
    log "WARNING: Backup verification failed"
fi

log "Backup process completed"