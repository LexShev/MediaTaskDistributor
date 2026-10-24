#!/bin/bash
set -euo pipefail

RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.dump"
LOG_FILE="/var/log/backup.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $*" | tee -a "$LOG_FILE"
}

mkdir -p "$BACKUP_DIR"

export PGPASSWORD="$DB_PASSWORD"

log "Starting backup of ${DB_NAME}@${DB_HOST}:${DB_PORT}"

pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --clean --create --if-exists \
    -F c \
    -f "$BACKUP_FILE"

log "Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

DELETED=$(find "$BACKUP_DIR" -name "backup_*.dump" -type f -mtime +"$RETENTION_DAYS" -delete -print | wc -l)
log "Cleaned up ${DELETED} backup(s) older than ${RETENTION_DAYS} days"
