# GitHub Secrets Configuration

This file documents the required GitHub secrets for the CI/CD pipeline.

## Required Secrets

### Container Publish
- `SENTRY_DSN_FE` - frontend production build argument

### GitHub Project Automation
- `ADD_TO_PROJECT_PAT` - personal access token used by `actions/add-to-project` to add new repository issues to the GitHub Project. For a classic PAT, include `project` scope; for private repositories also include `repo` scope. For a fine-grained PAT, grant Projects read/write plus Issues read access for this repository.

### Built-in Token
- `GITHUB_TOKEN` - automatically provided by GitHub Actions

## Required Variables

### Container Publish
- `SITE_DOMAIN` - frontend production build argument
- `API_DOMAIN` - frontend production build argument
- `GA_TRACKING_ID` - frontend production build argument
- `ALLOWED_HOSTS` - frontend production build argument
- `PROJECT_OWNER` - frontend production build argument

### GitHub Project Automation
- `ADD_TO_PROJECT_URL` - GitHub Project URL that should receive new issues. This is the Project board URL from the browser address bar, for example `https://github.com/users/LukaszRemkowicz/projects/1`, not the repository URL `https://github.com/LukaszRemkowicz/portfolio`.

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

### 2. GitHub Project Automation
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
