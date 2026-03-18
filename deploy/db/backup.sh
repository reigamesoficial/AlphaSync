#!/bin/bash
# =============================================================================
# AlphaSync — Script de backup do PostgreSQL (VPS 3)
# Uso: ./backup.sh
# Cron sugerido: 0 2 * * * /opt/alphasync/deploy/db/backup.sh
# =============================================================================

set -euo pipefail

BACKUP_DIR="./backups"
CONTAINER="alphasync_db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/alphasync_${TIMESTAMP}.sql.gz"
KEEP_DAYS=7

# Carregar variáveis
source .env 2>/dev/null || true

DB_USER="${POSTGRES_USER:-alphasync}"
DB_NAME="${POSTGRES_DB:-alphasync}"

echo "[$(date -Iseconds)] Iniciando backup: ${BACKUP_FILE}"

mkdir -p "${BACKUP_DIR}"

# Dump comprimido
docker exec "${CONTAINER}" pg_dump -U "${DB_USER}" "${DB_NAME}" \
  --no-owner --no-acl --clean --if-exists \
  | gzip > "${BACKUP_FILE}"

SIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)
echo "[$(date -Iseconds)] Backup concluído: ${BACKUP_FILE} (${SIZE})"

# Remover backups antigos
find "${BACKUP_DIR}" -name "alphasync_*.sql.gz" -mtime +${KEEP_DAYS} -delete
echo "[$(date -Iseconds)] Backups mais antigos que ${KEEP_DAYS} dias removidos."
