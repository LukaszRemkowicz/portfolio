# GitHub Secrets Configuration

This file documents the required GitHub secrets for the CI/CD pipeline.

## Required Secrets

### Dependency Security
- `SAFETY_API_KEY` - Safety CLI API key used by the `Dependency Security Checks` job in `ci-cd.yml`

### GitHub Project Automation
- `ADD_TO_PROJECT_PAT` - personal access token used by `actions/add-to-project` to add new repository issues to the GitHub Project. For a classic PAT, include `project` scope; for private repositories also include `repo` scope. For a fine-grained PAT, grant Projects read/write plus Issues read access for this repository.

### Supabase Maintenance
Used by `.github/workflows/supabase-maintenance.yml` (database keep-alive ping and monthly encrypted backup to R2). Same values as Doppler `portfolio/prd`.
- `SUPABASE_DB_HOST`, `SUPABASE_DB_PORT`, `SUPABASE_DB_NAME`, `SUPABASE_DB_USER`, `SUPABASE_DB_PASSWORD` - Supabase Postgres connection (session pooler)
- `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` - R2 credentials for uploading to `portfolio-originals/backups/supabase/`
- `BACKUP_PASSPHRASE` - passphrase for the symmetric GPG encryption of the dump

### Built-in Token
- `GITHUB_TOKEN` - automatically provided by GitHub Actions

## Required Variables

### Container Publish
- `IMAGE_NAMESPACE` - GHCR image namespace used by `release.yml` (`<registry>/<IMAGE_NAMESPACE>/production-be`, and `production-nginx` for the VPS rollback path)

### GitHub Project Automation
- `ADD_TO_PROJECT_URL` - GitHub Project URL that should receive new issues. This is the Project board URL from the browser address bar, for example `https://github.com/users/LukaszRemkowicz/projects/1`, not the repository URL `https://github.com/LukaszRemkowicz/portfolio`.

## Setup Instructions

### GitHub Project Automation
```bash
# Go to GitHub repository Settings > Secrets and variables > Actions
# Add this repository variable. Use the GitHub Project board URL from your browser,
# not the repository URL.
ADD_TO_PROJECT_URL=https://github.com/users/LukaszRemkowicz/projects/<project-url-number>

# Add this repository secret:
ADD_TO_PROJECT_PAT=your-token-with-project-access
```

The workflow runs for issues that are opened, reopened, or transferred into this repository. Existing issues are not backfilled automatically by this workflow.

## Current CI/CD Workflow

### What's Included:
- ✅ **Pre-commit hooks** - No secrets needed
- ✅ **PR checks** - No secrets needed
- ✅ **CodeQL security** - No secrets needed
- ✅ **Backend tests** - No secrets needed
- ✅ **Docker build & test** - No secrets needed
- ✅ **Production image publish to GHCR** - Uses built-in `GITHUB_TOKEN` plus repo vars/secrets above
- ✅ **Supabase maintenance** - Needs the Supabase Maintenance secrets above

### What's NOT Included:
- ❌ **Docker Hub push** - Removed (was using public images)
- ❌ **Production deployment** - Manual: the operator runs `infra/scripts/run_admin.sh` (Django migrations), applies new `supabase/migrations/*.sql` grants and runs `supabase/deploy-api.sh` (Edge Function) when a release needs them. The frontend deploys from the `portfolio-fe` repo.

## Security Notes

- Never commit secrets to the repository
- Repository secrets are limited to the ones listed above (Safety, the project PAT and the Supabase maintenance database, R2 and backup secrets); everything else uses `GITHUB_TOKEN`
- `GITHUB_TOKEN` is automatically provided and scoped
- All workflows run in isolated environments

## Deployment

Production deployment is manual and does not use GitHub secrets: see the Release & Deployment section of the root [README](../README.md) and [supabase_api.md](../infra/docs/project/supabase_api.md) (`run_admin.sh`, Supabase grants, `supabase/deploy-api.sh`; secrets come from Doppler).

The former VPS deploy (`deploy_production.sh`) is stopped since 2026-11-17 and kept only as a rollback path: [infra/scripts/README.md](../infra/scripts/README.md).

## Branch Protection Rules

To enable branch protection for the main branch:

1. Go to **Settings** → **Branches** → **Add rule**
2. Set **Branch name pattern** to `main`
3. Enable these settings:
   - ✅ **Require a pull request before merging**
   - ✅ **Require status checks to pass before merging**
   - ✅ **Require branches to be up to date before merging**
   - ✅ **Restrict pushes that create files**
   - ✅ **Include administrators**

4. In **Status checks that are required** (jobs as defined in `.github/workflows/ci-cd.yml`; check the exact names in the workflow and in the repository's branch protection settings):
   - ✅ **Branch Protection Check** (`branch-protection.yml`)
   - ✅ **CI Gate** (aggregates Backend Quality, Backend Tests, Supabase API Function, Trivy, Dependency Security Checks and the image build checks; fails if any of them failed)

5. **Allow force pushes**: ❌ (disabled)
6. **Allow deletions**: ❌ (disabled)

### Allowed branches to merge to main:
- `dev` - Main development branch
- `hotfix/*` - Emergency fixes
- `release/*` - Release branches

### Workflow:
```
feature/* → dev → main
hotfix/* → main (direct)
release/* → main (direct)
```
