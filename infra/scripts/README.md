# Infrastructure Scripts Runbook

Shell scripts for local tooling and database backups. Production runs on Supabase and Cloudflare; see [supabase_api.md](../docs/project/supabase_api.md) and the Release & Deployment section of the root [README](../../README.md).

## Tooling

- `infra/scripts/run_admin.sh [tag]` -> runs the released `production-be` image locally against Supabase (migrations, admin on http://localhost:8000/admin/)
- `infra/scripts/run_local_api.sh` -> runs the Edge Function locally on :8001 against the dev compose Postgres
- `supabase/deploy-api.sh` -> deploys the Edge Function (`doppler run --project portfolio --config prd -- supabase/deploy-api.sh`)
- `.github/workflows/supabase-maintenance.yml` -> database keep-alive ping and monthly encrypted backup to R2
- `db_backup/` -> backup, restore, restore validation for the local Docker database
- `utils.sh` -> shared utility functions used across the scripts

Details: [supabase_api.md](../docs/project/supabase_api.md).

## Backup scripts

Validate a dump in a temporary Postgres container:

```bash
./infra/scripts/db_backup/test_restore.sh /path/to/backup.dump
```

Restore a dump into the current local Docker DB:

```bash
./infra/scripts/db_backup/restore_db.sh /path/to/backup.dump
```

See [db_backup/MAINTENANCE.md](db_backup/MAINTENANCE.md).
