# Portfolio Scripts

Administrative scripts for portfolio.

## 🚀 deploy.sh

Automatic deployment script to production server.

### How to use:

#### 1. Configure the script:
```bash
# Edit path in file:
nano scripts/deploy.sh

# Change this line:
PROJECT_DIR="/path/to/portfolio"  # CHANGE TO YOUR PATH!
```

#### 2. Make script executable:
```bash
chmod +x scripts/deploy.sh
```

#### 3. Run manually (test):
```bash
./scripts/deploy.sh
```

#### 4. Add to crontab:
```bash
# Edit crontab:
crontab -e

# Add line (every 10 minutes):
*/10 * * * * /path/to/portfolio/scripts/deploy.sh

# Or every 15 minutes:
*/15 * * * * /path/to/portfolio/scripts/deploy.sh
```

### What the script does:

1. **Checks** if there are new changes in git
2. **Pulls** code from `main` branch
3. **Stops** existing containers
4. **Builds** new Docker images
5. **Starts** new containers
6. **Checks** if everything works
7. **Cleans** old images
8. **Logs** everything to `/var/log/portfolio-deploy.log`

### Logs:

```bash
# View deployment logs:
tail -f /var/log/portfolio-deploy.log

# Last 50 lines:
tail -50 /var/log/portfolio-deploy.log
```

### Troubleshooting:

#### Problem: "Project directory does not exist"
```bash
# Check path in script:
grep "PROJECT_DIR" scripts/deploy.sh

# Change to correct path
```

#### Problem: "Docker is not available"
```bash
# Check if Docker works:
docker --version
docker-compose --version
# or
docker compose version
```

#### Problem: "Cannot pull code"
```bash
# Check GitHub connection:
git fetch origin

# Check permissions:
ls -la .git/
```

### Example usage:

```bash
# 1. Configure:
PROJECT_DIR="/home/user/portfolio"

# 2. Test:
./scripts/deploy.sh

# 3. Cron (every 10 minutes):
*/10 * * * * /home/user/portfolio/scripts/deploy.sh

# 4. Check logs:
tail -f /var/log/portfolio-deploy.log
```

### Security:

- ✅ Script checks if code changed
- ✅ No deployment if no changes
- ✅ Logs all operations
- ✅ Stops on errors (`set -e`)
- ✅ Checks container status

## 🏭 build-production.sh

Script for building production images on demand.

### How to use:

#### 1. Configure the script:
```bash
# Edit path in file:
nano scripts/build-production.sh

# Change this line:
PROJECT_DIR="/path/to/portfolio"  # CHANGE TO YOUR PATH!
```

#### 2. Make script executable:
```bash
chmod +x scripts/build-production.sh
```

#### 3. Run:
```bash
# Full build (frontend + backend):
./scripts/build-production.sh

# Frontend only:
./scripts/build-production.sh --frontend-only

# Backend only:
./scripts/build-production.sh --backend-only

# Without pulling code from git:
./scripts/build-production.sh --no-pull

# Combination:
./scripts/build-production.sh --no-pull --frontend-only

# Help:
./scripts/build-production.sh --help
```

### Options:

- `--no-pull` - Skip git pull
- `--frontend-only` - Build only frontend
- `--backend-only` - Build only backend
- `--help` - Show help

### What the script does:

1. **Pulls** code from `main` branch (optionally)
2. **Builds** Docker images with `prod` target
3. **Creates** tags: `:prod`, `:latest`, `:commit-hash`
4. **Asks** if you want to run containers
5. **Logs** everything to `/var/log/portfolio-build.log`

### Usage examples:

```bash
# Quick build without git pull:
./scripts/build-production.sh --no-pull

# Frontend only:
./scripts/build-production.sh --frontend-only

# Full build with deployment:
./scripts/build-production.sh
# (answer 'y' when asked about running containers)

# Test image:
docker run -p 80:80 portfolio-frontend:prod
docker run -p 8000:8000 portfolio-backend:prod
```

### Logs:

```bash
# View build logs:
tail -f /var/log/portfolio-build.log

# Last 50 lines:
tail -50 /var/log/portfolio-build.log
```

## 📋 Script comparison

| Script | Purpose | Trigger | Git Pull | Run Containers |
|--------|---------|---------|----------|----------------|
| `deploy.sh` | Automatic deployment | Cron | Always | Always |
| `build-production.sh` | Build images | Manual | Optionally | Optionally |

### Requirements:

- Git
- Docker
- Docker Compose
- Project directory permissions
- Internet connection (git pull)
