#!/bin/bash
# scripts/db_backup/backup_db.sh
# "God Tier" utility to create atomic, validated PostgreSQL backups with retention and overlap protection.

# 1. Robustness: Exit on error, undefined variables, and pipe failures
set -euo pipefail

# 2. Paths & Environment Check
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Hard requirement: BACKUP_DIR must be set
: "${BACKUP_DIR:?❌ ERROR: BACKUP_DIR must be set (e.g. export BACKUP_DIR=/var/backups/portfolio-db)}"

RETENTION_DAYS="${RETENTION_DAYS:-14}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-portfolio}"
DB_HOST="${DB_HOST:-localhost}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

# Anchor compose file to project root
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_ROOT/docker-compose.yml}"

# 3. Filename & Lock Setup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.dump"
TMP_FILE="$BACKUP_DIR/.backup_${TIMESTAMP}.tmp"
LOCK_FILE="$BACKUP_DIR/.backup.lock"

mkdir -p "$BACKUP_DIR"

# 4. Lock Management (Overlap Protection)
if command -v flock >/dev/null 2>&1; then
    exec 9>"$LOCK_FILE"
    if ! flock -n 9; then
        echo "❌ Another backup is already running (lock: $LOCK_FILE)"
        exit 1
    fi
else
    echo "⚠️  flock not available; skipping overlap protection."
fi

# Cleanup temp file on exit if promotion didn't happen
trap 'rm -f "$TMP_FILE" >/dev/null 2>&1 || true' EXIT

echo "🚀 Starting God-Tier database backup..."
echo "📍 Location: $BACKUP_DIR"

# 5. Common pg_dump arguments
PG_DUMP_ARGS=(-Fc --no-owner --no-privileges)

run_pg_dump() {
    local dest="$1"

    # Prefer Docker Compose if service "db" exists
    if command -v docker >/dev/null 2>&1 && docker compose -f "$COMPOSE_FILE" ps --services | grep -qx "db"; then
        echo "🐳 Docker Compose detected. Running pg_dump inside 'db' container..."
        # Pass password explicitly
        docker compose -f "$COMPOSE_FILE" exec -T db \
            env PGPASSWORD="$DB_PASSWORD" \
            pg_dump "${PG_DUMP_ARGS[@]}" -U "$DB_USER" "$DB_NAME" > "$dest"
        return 0
    fi

    echo "🖥️  Local environment detected. Running pg_dump directly..."
    export PGPASSWORD="$DB_PASSWORD"
    if [ -n "${DATABASE_URL:-}" ]; then
        pg_dump "${PG_DUMP_ARGS[@]}" "$DATABASE_URL" > "$dest"
    else
        pg_dump "${PG_DUMP_ARGS[@]}" -U "$DB_USER" -h "$DB_HOST" "$DB_NAME" > "$dest"
    fi
}

# 6. Execution (to TMP_FILE)
run_pg_dump "$TMP_FILE"

# 7. Validation (Sanity Checks)
if [ ! -s "$TMP_FILE" ]; then
    echo "❌ ERROR: Backup failed: output file is empty."
    exit 1
fi

validate_dump() {
    local file="$1"
    # Local validation
    if command -v pg_restore >/dev/null 2>&1; then
        pg_restore -l "$file" >/dev/null 2>&1
        return $?
    fi
    # Container-based fallback validation
    if command -v docker >/dev/null 2>&1; then
        echo "⚠️  pg_restore not found locally. Validating using a Postgres container..."
        docker run --rm -i postgres:15-alpine pg_restore -l >/dev/null 2>&1 < "$file"
        return $?
    fi
    echo "⚠️  Could not validate dump header: tools missing."
    return 0
}

echo "🔍 Validating dump integrity..."
if ! validate_dump "$TMP_FILE"; then
    echo "❌ ERROR: Backup validation failed. Corrupted header."
    exit 1
fi

# 8. Atomic Promotion
mv -f "$TMP_FILE" "$BACKUP_FILE"
trap - EXIT # Clear trap after successful promotion

echo "✅ Backup successful: $(basename "$BACKUP_FILE")"
ls -lh "$BACKUP_FILE" | awk '{print "📦 Size: " $5}'

# 9. Retention Policy
echo "🧹 Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "backup_*.dump" -type f -mtime +"$RETENTION_DAYS" -print -delete \
    | awk '{print "🗑️  Deleted: " $1}'

echo "✨ Maintenance complete."
