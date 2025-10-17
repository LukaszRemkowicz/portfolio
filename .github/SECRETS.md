# GitHub Secrets Configuration

This file documents the required GitHub secrets for the CI/CD pipeline.

## Required Secrets

### None Required! 🎉
The current CI/CD pipeline uses only `GITHUB_TOKEN` which is automatically provided by GitHub.

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

### What's NOT Included:
- ❌ **Docker Hub push** - Removed (was using public images)
- ❌ **Production deployment** - Uses `deploy.sh` script instead
- ❌ **Release automation** - Removed (unnecessary for portfolio)

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

No GitHub secrets needed for deployment!

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
