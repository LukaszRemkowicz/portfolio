# Database Maintenance Guide

This document outlines the procedures for database backups and restores for the portfolio project.

## 🛡️ Database Backups

The `scripts/db_backup/backup_db.sh` script is a production-grade utility that creates compressed, timestamped backups using PostgreSQL's custom format (`-Fc`).

### Features
- **Robustness**: Uses `set -euo pipefail` to ensure any failure stops the script.
- **Compression**: Uses `-Fc` format which is natively compressed and allows for parallel restores.
- **Portability**: Adds `--no-owner` and `--no-privileges` to make backups easy to restore across different environments.
- **Retention**: Automatically deletes backups older than a configurable number of days.

### Usage

#### Manual Backup
Run the script from the project root:
```bash
./scripts/db_backup/backup_db.sh
```

#### Environment Variables
| Variable | Description | Default |
| :--- | :--- | :--- |
| `BACKUP_DIR` | Directory to save backups | **REQUIRED** (e.g., `/var/backups/portfolio-db/`) |
| `RETENTION_DAYS` | Number of days to keep backups | `14` |
| `DB_USER` | Database user | `postgres` |
| `DB_NAME` | Database name | `portfolio` |

---

## 🔝 Database Restore

Since we use the PostgreSQL custom format (`-Fc`), you must use `pg_restore` instead of a simple SQL pipe.

### 🐳 Restoring in Docker
1. **Identify the backup file** in `database_data/`.
2. **Run the restore command**:
```bash
# Example for backup_20240123_120000.dump
docker compose exec -T db pg_restore -U postgres -d portfolio --clean --no-owner < database_data/backup_20240123_120000.dump
```
> [!IMPORTANT]
> The `--clean` flag drops existing objects before recreating them. Use with caution.

### 🖥️ Restoring in Local/Production
```bash
pg_restore -U postgres -d portfolio --clean --no-owner < path/to/backup.dump
```

---

## 🧼 Automated Restore Testing

Backups are only useful if they can be restored. The `scripts/db_backup/test_restore.sh` script automates the verification process by spinning up a temporary "clean" Postgres container and attempting a full restore.

### How to Verify Backups
Run this utility to ensure your backups are not just "present" but actually "healthy":
```bash
BACKUP_DIR=path/to/dumps ./scripts/db_backup/test_restore.sh
```
The script performs a **Truly Professional Verification**:
1. **Env Guard**: Fails immediately with help instructions if `BACKUP_DIR` is missing.
2. **Robust Orchestration**: Uses `docker compose config` to detect the exact production DB image.
3. **Tool Parity**: Runs `pg_restore -l` (header validation) **inside the target container** to ensure version compatibility.
4. **Precision SQL**:
   - Checks for **physical tables** only (`relkind='r'`).
   - Uses `format('%I', ...)` for identifier safety and proper quoting.
5. **Extension Assertions**: Hard-verifies that mandatory extensions (e.g., `plpgsql`) are operational.
6. **Multi-Step Smoke Test**: Validates row counts for `users`, `images`, and `migrations`.

---

---

## 🛡️ Professional Secret Management with Doppler

For production and shared local environments, we use **Doppler** to manage environment variables securely. This eliminates the need for manually managing `.env` files and ensures secrets are never committed to version control.

### 💻 Local Development
1. **Install Doppler CLI**: Follow the [official instructions](https://docs.doppler.com/docs/install-cli).
2. **Login & Setup**:
   ```bash
   doppler login
   doppler setup
   ```
3. **Run Services**:
   Instead of `docker compose up`, run:
   ```bash
   # Injects secrets as environment variables into the shell context
   doppler run -- docker compose up
   ```

### 🚀 Production (DigitalOcean Droplet)
1. **Service Token**: Create a [Doppler Service Token](https://docs.doppler.com/docs/service-tokens) for your production config.
2. **Environment Variable**: Set `DOPPLER_TOKEN` on your server's host environment.
3. **Start Production Services**:
   ```bash
   # Injects secrets from Doppler before executing docker compose
   doppler run -- docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

> [!NOTE]
> Since we use shell interpolation in our `docker-compose.yml` (e.g., `${DB_NAME}`), Doppler correctly injects these variables directly into the containers.

### 📦 Integrated Backups & Tests
Our scripts are designed to work seamlessly with Doppler. Use `doppler run` to provide database credentials without manual `.env` files:
```bash
doppler run -- ./scripts/db_backup/backup_db.sh
doppler run -- ./scripts/db_backup/test_restore.sh
```

---

## 📂 Path Logic
- **Configuration**: `BACKUP_DIR` must be set in the environment (e.g., Doppler or `.bashrc`).
- **Standard**: Recommended to use `/var/backups/portfolio-db/` for production.
- **Fail-Fast**: Scripts will terminate immediately if `BACKUP_DIR` is undefined.
