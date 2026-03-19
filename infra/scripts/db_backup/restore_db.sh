#!/bin/bash
# scripts/db_backup/restore_db.sh
# Utility to restore a database backup to the 'db' service in Docker Compose.
# WARNING: This overwrites the existing database!

set -euo pipefail

# 1. Paths & Environment
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

source "$PROJECT_ROOT/infra/scripts/utils.sh"

# Default configuration (can be overridden by env vars)
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-$(get_db_name)}"
TARGET_DB="${TARGET_DB:-db}"
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_ROOT/docker-compose.yml}"

# Validating COMPOSE_FILE: If it's a directory, look for docker-compose.yml inside
if [ -d "$COMPOSE_FILE" ]; then
    COMPOSE_FILE="${COMPOSE_FILE%/}/docker-compose.yml"
fi

# 2. Argument Parsing (Backup File)
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_backup_file>"
    echo "Available backups in ${BACKUP_DIR:-/var/backups/portfolio}:"
    find "${BACKUP_DIR:-/var/backups/portfolio}" -maxdepth 3 \( -name '*.dump' -o -name '*.sql' -o -name '*.sql.gz' \) -type f 2>/dev/null | sort | sed 's/^/  /'
    exit 1
fi

BACKUP_FILE="$1"

# Verify file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# 3. Confirmation Prompt
echo "⚠️  DANGER: This operation will OVERWRITE the database '$DB_NAME' in service '$TARGET_DB'."
echo "    Target: Docker Compose service '$TARGET_DB' (from $COMPOSE_FILE)"
echo "    Source: $(basename "$BACKUP_FILE")"
echo ""
read -p "Are you sure you want to proceed? (Type 'yes' to confirm): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Restore cancelled."
    exit 1
fi

# 4. Copy to Container
echo "🐳 Copying backup to '$TARGET_DB' container..."
# Ensure the container is running
if ! docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q "^${TARGET_DB}\$"; then
    echo "⚙️  Starting '$TARGET_DB' service..."
    docker compose -f "$COMPOSE_FILE" up -d "$TARGET_DB"
    echo "⏳ Waiting for database to be ready..."
    sleep 5
fi

CONTAINER_BACKUP_PATH="/tmp/restore_$(date +%s).dump"
docker compose -f "$COMPOSE_FILE" cp "$BACKUP_FILE" "${TARGET_DB}:$CONTAINER_BACKUP_PATH"

# 5. Restore Execution
echo "🔄 Restoring database..."

# Function to detect format and restore
restore_cmd() {
    # Check if it's a custom format dump (starts with PGDMP signature) or assume SQL
    # We'll use pg_restore -l to test validity and format.
    # If pg_restore accepts it, use pg_restore. Otherwise, try psql.

    if docker compose -f "$COMPOSE_FILE" exec -T "$TARGET_DB" pg_restore -l "$CONTAINER_BACKUP_PATH" >/dev/null 2>&1; then
        echo "  - Format: Custom (.dump)"

        # WIPE existing data to avoid foreign key conflicts during drop
        echo "  - 🧨 Wiping 'public' schema to ensure clean slate..."
        docker compose -f "$COMPOSE_FILE" exec -T "$TARGET_DB" \
            psql -U "$DB_USER" -d "$DB_NAME" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

        # Restore without --clean (since we just wiped it)
        docker compose -f "$COMPOSE_FILE" exec -T "$TARGET_DB" \
            pg_restore -U "$DB_USER" -d "$DB_NAME" \
            --no-owner --no-privileges \
            "$CONTAINER_BACKUP_PATH" || echo "⚠️ pg_restore completed with some warnings/ignored errors."
    else
        echo "  - Format: Plain SQL"
        # For plain SQL, we might need to drop/create the DB manually or rely on the script
        # But commonly plain SQL dumps include DROP/CREATE if generated that way.
        # If not, we run it against the existing DB.
        docker compose -f "$COMPOSE_FILE" exec -T "$TARGET_DB" \
            psql -U "$DB_USER" -d "$DB_NAME" -f "$CONTAINER_BACKUP_PATH"
    fi
}

if restore_cmd; then
    echo "✅ Restore completed successfully."
else
    echo "❌ Restore failed."
    # Cleanup even on failure
    docker compose -f "$COMPOSE_FILE" exec -T "$TARGET_DB" rm -f "$CONTAINER_BACKUP_PATH"
    exit 1
fi

# 6. Cleanup
docker compose -f "$COMPOSE_FILE" exec -T "$TARGET_DB" rm -f "$CONTAINER_BACKUP_PATH"
echo "✨ All done."
