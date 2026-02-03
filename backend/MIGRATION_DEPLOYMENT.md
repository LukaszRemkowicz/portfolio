# Migration Consolidation - Production Deployment Guide

## Overview
This guide documents the safe deployment of consolidated migrations to production. The `astrophotography` app's migrations `0001-0009` have been consolidated into a single `0001_initial.py` to fix `TranslatableModel` inheritance issues in tests.

## ⚠️ CRITICAL: Production Safety

**Production databases have already applied migrations `0001` through `0009`.** We must use `--fake` to mark the new consolidated migration as applied without executing SQL, preventing data loss and schema conflicts.

## Pre-Deployment Checklist

- [ ] **Backup production database** (mandatory)
- [ ] Test consolidation in local environment
- [ ] Test consolidation in staging with production data clone
- [ ] Verify all tests pass locally
- [ ] Review migration changes with team
- [ ] Schedule maintenance window (optional, no downtime expected)

## Changes Made

### Astrophotography App
- **Deleted**: Migrations `0002` through `0009`
- **Modified**: `0001_initial.py` (consolidated from `0001-0009`)
  - Added `TranslatableModel` bases to: `Place`, `AstroImage`, `MainPageLocation`, `MainPageBackgroundImage`
  - Includes `migrate_translations` data migration function
  - Optimized from 80 operations to 35 operations

### Programming App
- **Modified**: `0001_initial.py`
  - Added `TranslatableModel` base to `ProjectImage`

### Core App
- **Modified**: `0001_initial.py`
  - Updated dependency from `astrophotography.0002_consolidated_updates` to `astrophotography.0001_initial`

## Deployment Steps

### Step 1: Backup Database
```bash
# PostgreSQL backup
pg_dump -h <host> -U <user> -d <database> -F c -b -v -f backup_$(date +%Y%m%d_%H%M%S).dump

# Verify backup
pg_restore --list backup_TIMESTAMP.dump | head -20
```

### Step 2: Deploy Code
```bash
# Pull latest code
git pull origin main

# Restart application (if needed)
docker compose restart portfolio-be
# OR
systemctl restart portfolio-backend
```

### Step 3: Fake the Consolidated Migration
```bash
# Enter backend container/environment
docker compose exec portfolio-be bash
# OR
cd /path/to/backend && source venv/bin/activate

# Fake the astrophotography 0001_initial migration
python manage.py migrate astrophotography 0001 --fake

# This marks 0001_initial as applied without running SQL
# Safe because production already has the schema from old migrations
```

### Step 4: Run Remaining Migrations
```bash
# Apply any migrations after 0010 (if they exist)
python manage.py migrate astrophotography

# Apply migrations for other apps
python manage.py migrate
```

### Step 5: Verify Migration State
```bash
# Check all migrations are applied
python manage.py showmigrations astrophotography

# Expected output:
# astrophotography
#  [X] 0001_initial
#  [X] 0010_... (if exists)
#  [X] 0011_... (if exists)

# Verify no unapplied migrations
python manage.py showmigrations | grep "\[ \]"
# Should return empty (no unapplied migrations)
```

### Step 6: Smoke Test
```bash
# Test critical endpoints
curl https://your-domain.com/api/astrophotography/images/ | jq
curl https://your-domain.com/api/programming/projects/ | jq

# Check admin panel
# Navigate to https://admin.your-domain.com
# Verify astrophotography and programming models load correctly
```

## Rollback Procedure

If issues occur:

### 1. Restore Database Backup
```bash
# Stop application
docker compose stop portfolio-be

# Restore database
pg_restore -h <host> -U <user> -d <database> -c backup_TIMESTAMP.dump

# Start application
docker compose start portfolio-be
```

### 2. Revert Code
```bash
# Revert to previous commit
git revert HEAD
git push origin main

# Redeploy
docker compose restart portfolio-be
```

### 3. Verify State
```bash
# Check migration state matches pre-deployment
python manage.py showmigrations astrophotography

# Should show 0001-0009 as applied
```

## Verification Checklist

After deployment:

- [ ] All migrations show `[X]` in `showmigrations`
- [ ] No errors in application logs
- [ ] Astrophotography images load correctly
- [ ] Programming projects load correctly
- [ ] Admin panel functions normally
- [ ] Translation functionality works
- [ ] No 500 errors in monitoring

## Technical Details

### Why --fake is Safe

1. **Schema Unchanged**: The consolidated migration produces the same database schema as the original migrations `0001-0009`
2. **Data Unchanged**: No data migrations are re-run
3. **State-Only Change**: Only the migration history table (`django_migrations`) is updated
4. **Idempotent**: Running `--fake` multiple times has no effect

### Migration Consolidation Benefits

1. **Fixes Test Failures**: Resolves `TypeError: Translatable model does not appear to inherit from TranslatableModel`
2. **Cleaner History**: Reduces 9 migrations to 1
3. **Faster Tests**: Fewer migrations to apply during test database creation
4. **Easier Maintenance**: Single source of truth for initial schema

## Support

If you encounter issues:

1. Check application logs: `docker compose logs -f portfolio-be`
2. Check migration state: `python manage.py showmigrations`
3. Verify database connectivity: `python manage.py dbshell`
4. Contact development team with error details

## Post-Deployment

- [ ] Monitor application for 24 hours
- [ ] Verify backup retention policy
- [ ] Update deployment documentation
- [ ] Notify team of successful deployment
