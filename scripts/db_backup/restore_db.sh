#!/bin/bash
# scripts/db_backup/restore_db.sh
# Utility to restore a database backup to the 'db' service in Docker Compose.
# WARNING: This overwrites the existing database!

set -euo pipefail

# 1. Paths & Environment
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Default configuration (can be overridden by env vars)
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-portfolio}"
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_ROOT/docker-compose.yml}"

# Validating COMPOSE_FILE: If it's a directory, look for docker-compose.yml inside
if [ -d "$COMPOSE_FILE" ]; then
    COMPOSE_FILE="${COMPOSE_FILE%/}/docker-compose.yml"
fi

# 2. Argument Parsing (Backup File)
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_backup_file>"
    echo "Available backups in ${BACKUP_DIR:-scripts/db_backup}:"
    ls -lh "${BACKUP_DIR:-$PROJECT_ROOT/scripts/db_backup}"/*.dump 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    exit 1
fi

BACKUP_FILE="$1"

# Verify file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# 3. Confirmation Prompt
echo "⚠️  DANGER: This operation will OVERWRITE the database '$DB_NAME' in service 'db'."
echo "    Target: Docker Compose service 'db' (from $COMPOSE_FILE)"
echo "    Source: $(basename "$BACKUP_FILE")"
echo ""
read -p "Are you sure you want to proceed? (Type 'yes' to confirm): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Restore cancelled."
    exit 1
fi

# 4. Copy to Container
echo "🐳 Copying backup to 'db' container..."
# Ensure the container is running
if ! docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q "^db$"; then
    echo "⚙️  Starting 'db' service..."
    docker compose -f "$COMPOSE_FILE" up -d db
    echo "⏳ Waiting for database to be ready..."
    sleep 5
fi

CONTAINER_BACKUP_PATH="/tmp/restore_$(date +%s).dump"
docker compose -f "$COMPOSE_FILE" cp "$BACKUP_FILE" "db:$CONTAINER_BACKUP_PATH"

# 5. Restore Execution
echo "🔄 Restoring database..."

# Function to detect format and restore
restore_cmd() {
    # Check if it's a custom format dump (starts with PGDMP signature) or assume SQL
    # We'll use pg_restore -l to test validity and format.
    # If pg_restore accepts it, use pg_restore. Otherwise, try psql.

    if docker compose -f "$COMPOSE_FILE" exec -T db pg_restore -l "$CONTAINER_BACKUP_PATH" >/dev/null 2>&1; then
        echo "  - Format: Custom (.dump)"

        # WIPE existing data to avoid foreign key conflicts during drop
        echo "  - 🧨 Wiping 'public' schema to ensure clean slate..."
        docker compose -f "$COMPOSE_FILE" exec -T db \
            psql -U "$DB_USER" -d "$DB_NAME" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

        # Restore without --clean (since we just wiped it)
        docker compose -f "$COMPOSE_FILE" exec -T db \
            pg_restore -U "$DB_USER" -d "$DB_NAME" \
            --no-owner --no-privileges \
            "$CONTAINER_BACKUP_PATH"
    else
        echo "  - Format: Plain SQL"
        # For plain SQL, we might need to drop/create the DB manually or rely on the script
        # But commonly plain SQL dumps include DROP/CREATE if generated that way.
        # If not, we run it against the existing DB.
        docker compose -f "$COMPOSE_FILE" exec -T db \
            psql -U "$DB_USER" -d "$DB_NAME" -f "$CONTAINER_BACKUP_PATH"
    fi
}

if restore_cmd; then
    echo "✅ Restore completed successfully."
else
    echo "❌ Restore failed."
    # Cleanup even on failure
    docker compose -f "$COMPOSE_FILE" exec -T db rm -f "$CONTAINER_BACKUP_PATH"
    exit 1
fi

# 6. Cleanup
docker compose -f "$COMPOSE_FILE" exec -T db rm -f "$CONTAINER_BACKUP_PATH"
echo "✨ All done."
