# GitHub Secrets Configuration

This file documents the required GitHub secrets for the CI/CD pipeline.

## Required Secrets

### Docker Hub
- `DOCKER_USERNAME` - Your Docker Hub username
- `DOCKER_PASSWORD` - Your Docker Hub access token (not password)

### Production Deployment
- `PROD_HOST` - Production server hostname/IP
- `PROD_USERNAME` - SSH username for production server
- `PROD_SSH_KEY` - Private SSH key for production server access

## Setup Instructions

### 1. Docker Hub Secrets
```bash
# Go to GitHub repository settings > Secrets and variables > Actions
# Add these secrets:
DOCKER_USERNAME=your-dockerhub-username
DOCKER_PASSWORD=your-dockerhub-access-token
```

### 2. Production Server Secrets
```bash
# Add these secrets for deployment:
PROD_HOST=your-production-server.com
PROD_USERNAME=deploy
PROD_SSH_KEY=your-private-ssh-key
```

### 3. Generate Docker Hub Access Token
1. Go to Docker Hub > Account Settings > Security
2. Create a new access token
3. Use this token as `DOCKER_PASSWORD` (not your login password)

### 4. Generate SSH Key for Production
```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -C "github-actions-deploy"

# Add public key to production server
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@production-server

# Use private key content as PROD_SSH_KEY secret
cat ~/.ssh/id_ed25519
```

## Security Notes

- Never commit secrets to the repository
- Use environment-specific secrets
- Rotate secrets regularly
- Use least-privilege access for production secrets
- Consider using GitHub Environments for production secrets

## Optional: GitHub Environments

For better security, create GitHub Environments:
1. Go to repository settings > Environments
2. Create `production` environment
3. Add production secrets to the environment
4. Require manual approval for production deployments
