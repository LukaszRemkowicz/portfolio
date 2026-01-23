#!/bin/bash
# scripts/db_backup/test_restore.sh
# "God Tier" Restore Test utility to verify that database dumps are valid and restorable.
# Supports both Custom format (.dump) and Plain SQL backups.

set -euo pipefail

# 1) Paths & Environment Check
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

if [ -z "${BACKUP_DIR:-}" ]; then
    echo "[ERROR] BACKUP_DIR is not set."
    echo "Please set it via environment variable, e.g.:"
    echo "  export BACKUP_DIR=/var/backups/portfolio-db/"
    exit 1
fi

COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_ROOT/docker-compose.yml}"

# 2) Detect Postgres image from docker compose config
echo "[INFO] Detecting Postgres image from configuration..."
POSTGRES_IMAGE=""
if command -v jq >/dev/null 2>&1; then
    # Use jq for bulletproof parsing of the JSON config
    POSTGRES_IMAGE=$(docker compose -f "$COMPOSE_FILE" config --format json | jq -r '.services.db.image' 2>/dev/null || echo "")
fi

if [ -z "${POSTGRES_IMAGE:-}" ]; then
    # Improved fallback parsing if jq is absent or failing
    POSTGRES_IMAGE=$(docker compose -f "$COMPOSE_FILE" config 2>/dev/null | grep -A 100 "db:" | grep "image:" | head -n 1 | awk '{print $2}' | tr -d '[:space:]' | tr -d '"' || echo "")
fi

if [ -z "${POSTGRES_IMAGE:-}" ]; then
    echo "[WARN] Could not detect image from config. Falling back to postgres:15-alpine"
    POSTGRES_IMAGE="postgres:15-alpine"
else
    echo "[INFO] Using image: $POSTGRES_IMAGE"
fi

# 3) Find latest backup
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/backup_* 2>/dev/null | head -n 1 || true)

if [ -z "$LATEST_BACKUP" ]; then
    echo "[ERROR] No backup files found in $BACKUP_DIR"
    exit 1
fi

echo "[DB] Found latest backup: $(basename "$LATEST_BACKUP")"

# 4) Parameters for temporary test container
TEST_CONTAINER="postgres_restore_test"
TEST_DB="restore_verify_db"

cleanup() {
    echo "[CLEANUP] Removing test container..."
    docker rm -f "$TEST_CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "[DOCKER] Starting temporary container ($POSTGRES_IMAGE)..."
docker run --name "$TEST_CONTAINER" \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB="$TEST_DB" \
    -d "$POSTGRES_IMAGE" > /dev/null

echo "[WAIT] Waiting for Postgres to be ready..."
# Robust wait loop: pg_isready + successful psql connection
MAX_RETRIES=30
COUNT=0
until docker exec "$TEST_CONTAINER" pg_isready -U postgres >/dev/null 2>&1 && \
      docker exec "$TEST_CONTAINER" psql -U postgres -d "$TEST_DB" -t -A -c "SELECT 1;" >/dev/null 2>&1; do
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "[ERROR] Postgres failed to initialize in time."
        exit 1
    fi
    sleep 1
    COUNT=$((COUNT + 1))
done
echo "[WAIT] Postgres is ready and accepting queries."

# 5) Copy backup into container (more reliable than streaming binary via stdin)
echo "[COPY] Copying backup into container..."
docker cp "$LATEST_BACKUP" "$TEST_CONTAINER:/tmp/backup"

# 6) Detect format and restore using container tools (tool parity)
echo "[VALIDATE] Detecting dump format inside container..."
RESTORE_CMD=""

# We use 'sh -c' to ensure we have the correct path for pg_restore
if docker exec "$TEST_CONTAINER" sh -c "pg_restore -l /tmp/backup >/dev/null 2>&1"; then
    echo "[FORMAT] PostgreSQL Custom/Tar format detected."
    RESTORE_CMD="pg_restore -U postgres -d $TEST_DB /tmp/backup"
else
    echo "[FORMAT] Plain SQL format detected."
    RESTORE_CMD="psql -U postgres -d $TEST_DB -f /tmp/backup"
fi

echo "[RESTORE] Running: $RESTORE_CMD"
# We suppress stdout to keep logs clean, but show stderr if it fails
if ! docker exec "$TEST_CONTAINER" sh -c "$RESTORE_CMD" > /dev/null; then
    echo "[ERROR] Restore execution failed!"
    exit 1
fi

echo "[SMOKE] Running verification tests..."

# 7) Verify Mandatory Extensions
echo "[CHECK] Verifying extensions..."
REQUIRED_EXTENSIONS=("plpgsql")
for ext in "${REQUIRED_EXTENSIONS[@]}"; do
    OK=$(docker exec "$TEST_CONTAINER" psql -U postgres -d "$TEST_DB" -t -A -c "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='$ext');")
    if [ "$OK" != "t" ]; then
        echo "  [FAIL] Mandatory extension '$ext' MISSING!"
        exit 1
    fi
    echo "  [PASS] extension '$ext' present"
done

# 8) Verify Critical Tables (using idiomatic to_regclass)
echo "[CHECK] Verifying critical tables..."
TABLES_TO_CHECK=("users_user" "astrophotography_astroimage" "django_migrations")

for table in "${TABLES_TO_CHECK[@]}"; do
    EXISTS=$(docker exec "$TEST_CONTAINER" psql -U postgres -d "$TEST_DB" -t -A -c "SELECT to_regclass('public.\"$table\"') IS NOT NULL;")

    if [ "$EXISTS" = "t" ]; then
        COUNT=$(docker exec "$TEST_CONTAINER" psql -U postgres -d "$TEST_DB" -t -A -c "SELECT count(*) FROM public.\"$table\";")
        echo "  [PASS] table '$table' verified (Rows: $COUNT)"
    else
        echo "  [FAIL] Table '$table' MISSING or not a base table!"
        exit 1
    fi
done

echo "[SUCCESS] Restore verification complete. Your backups are God-Tier!"
