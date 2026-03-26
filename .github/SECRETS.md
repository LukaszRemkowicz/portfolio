# GitHub Secrets Configuration

This file documents the required GitHub secrets for the CI/CD pipeline.

## Required Secrets

### Container Publish
- `SENTRY_DSN_FE` - frontend production build argument

### Built-in Token
- `GITHUB_TOKEN` - automatically provided by GitHub Actions

## Required Variables

### Container Publish
- `SITE_DOMAIN` - frontend production build argument
- `API_DOMAIN` - frontend production build argument
- `GA_TRACKING_ID` - frontend production build argument
- `ALLOWED_HOSTS` - frontend production build argument
- `PROJECT_OWNER` - frontend production build argument

## Optional Secrets

### Codecov (for code coverage reporting)
- `CODECOV_TOKEN` - Your Codecov token for coverage reporting

## Setup Instructions

### 1. Codecov Token (Optional)
```bash
# Go to GitHub repository settings > Secrets and variables > Actions
# Add this secret if you want code coverage reporting:
CODECOV_TOKEN=your-codecov-token

# To get Codecov token:
# 1. Go to https://codecov.io
# 2. Sign in with GitHub
# 3. Select your repository
# 4. Copy the token from Settings > General
```

## Current CI/CD Workflow

### What's Included:
- ✅ **Pre-commit hooks** - No secrets needed
- ✅ **PR checks** - No secrets needed
- ✅ **CodeQL security** - No secrets needed
- ✅ **Frontend tests** - No secrets needed
- ✅ **Backend tests** - No secrets needed
- ✅ **Docker build & test** - No secrets needed
- ✅ **Production image publish to GHCR** - Uses built-in `GITHUB_TOKEN` plus repo vars/secrets above

### What's NOT Included:
- ❌ **Docker Hub push** - Removed (was using public images)
- ❌ **Production deployment** - Uses `deploy.sh` script instead

## Security Notes

- Never commit secrets to the repository
- Current pipeline is secure without additional secrets
- `GITHUB_TOKEN` is automatically provided and scoped
- All workflows run in isolated environments

## Deployment

For production deployment, use the provided `deploy.sh` script:
```bash
# On your production server:
./scripts/deploy.sh
```

GitHub secrets are not used for VPS deployment itself. GHCR pull credentials for the server should live outside the repo, for example in Doppler.

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

4. In **Status checks that are required**:
   - ✅ **Branch Protection Check**
   - ✅ **Frontend Tests**
   - ✅ **Backend Tests**
   - ✅ **Docker Build & Test**
   - ✅ **Security Scan**
   - ✅ **All Checks Completed**

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
