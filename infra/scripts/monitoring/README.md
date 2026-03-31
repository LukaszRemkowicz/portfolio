# 📈 Monitoring Scripts

Scripts for the `AgentLog` daily Docker log collection and analysis pipeline.

## 🧭 Overview

This folder covers the host-side part of monitoring:

- `collect-logs.sh` collects recent container logs into a shared directory
- `portfolio-collect-logs.cron` schedules the collection job on the server
- the backend monitoring app later reads those files and produces analysis output

## 📄 `collect-logs.sh`

Collects logs from Docker containers and writes them to a shared directory on the host server.
This is Phase 1 of the AgentLog pipeline. It runs as a cron job and does not depend on Django or Celery being started from the script itself.

### ✅ What it does

1. Ensures `DOCKER_LOGS_DIR` exists.
2. Archives the previous snapshot set into `DOCKER_LOGS_DIR/archive/` when present.
3. Prunes archived snapshot directories older than the retention window.
3. Resolves the active Compose project name.
4. Collects timestamped logs for backend, frontend, nginx, and Traefik containers when available.
5. Writes `collected_at.txt` with a UTC ISO timestamp so the backend can detect stale or missing data.

### 🔐 Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DOCKER_LOGS_DIR` | Yes | None | Absolute path where log files are written |
| `COMPOSE_FILE` | Yes | None | Compose file used to infer the environment and Compose project |
| `ENVIRONMENT` | No | Inferred from `COMPOSE_FILE` | Environment name used for project resolution |
| `LOG_TAIL` | No | `5000` | Number of log lines to collect per container |
| `LOG_SINCE` | No | `24h` | Time window passed to `docker logs --since` |
| `ARCHIVE_RETENTION_DAYS` | No | `30` | Number of days to keep archived snapshot directories |
| `DOCKER_TOOL_LOG` | No | `${DOCKER_LOGS_DIR}/docker-tool-errors.log` | File where raw Docker stderr output is written |
| `BACKEND_SERVICE` | No | `be` | Compose service name for backend |
| `FRONTEND_SERVICE` | No | `fe` | Compose service name for frontend SSR |
| `NGINX_SERVICE` | No | `nginx` | Compose service name for nginx |
| `TRAEFIK_SERVICE` | No | `traefik` | Compose service name for Traefik |
| `TRAEFIK_PROJECT_NAME` | No | `portfolio-traefik` | Compose project name for the standalone Traefik stack |
| `TRAEFIK_CONTAINER_NAME` | No | `traefik` | Exact container name fallback for Traefik |

### 📝 Output files

The script writes these files into `DOCKER_LOGS_DIR`:

- `backend.log`
- `frontend.log`
- `nginx.log`
- `traefik.log`
- `collected_at.txt`

If a service is not running, the script logs a warning and writes an empty file for that service instead of failing the whole collection. Traefik is resolved from its standalone `portfolio-traefik` stack by default. Raw Docker stderr is written to `docker-tool-errors.log` so the cron log stays limited to collector messages.

### Archive layout

Before each new collection run, the script archives the previous snapshot set into:

- `DOCKER_LOGS_DIR/archive/YYYY-MM-DD_HHMMSS/`

Example:

- `/var/log/portfolio/docker-logs/backend.log`
- `/var/log/portfolio/docker-logs/archive/2026-03-31_000000/backend.log`

The top-level files remain the latest snapshot consumed by the monitoring pipeline.
Archived snapshot directories older than `ARCHIVE_RETENTION_DAYS` are removed automatically.

### ▶️ Manual run

```bash
DOCKER_LOGS_DIR=/var/log/portfolio/docker-logs \
COMPOSE_FILE=/home/lukasz/portfolio/docker-compose.prod.yml \
/home/lukasz/portfolio/infra/scripts/monitoring/collect-logs.sh
```

## ⏰ `portfolio-collect-logs.cron`

System cron entry that runs `collect-logs.sh` daily at midnight UTC.

### ⚙️ Installation

```bash
sudo cp portfolio-collect-logs.cron /etc/cron.d/portfolio-collect-logs
sudo chmod 644 /etc/cron.d/portfolio-collect-logs
```

> **Note:** No `systemctl enable` or `crontab -e` is required. Ubuntu's `cron` daemon picks up files from `/etc/cron.d/` automatically.

Useful check:

```bash
systemctl status cron
```

### 🪵 Cron log output

Job output is appended to:

- `/var/log/portfolio/collect-logs.log`

Useful archive inspection commands:

```bash
ls -la /var/log/portfolio/docker-logs/archive
find /var/log/portfolio/docker-logs/archive -maxdepth 1 -type d | sort
tail -n 50 /var/log/portfolio/docker-logs/archive/2026-03-31_000000/backend.log
```

## 🛠️ Server Setup

```bash
# Create the log directory and grant access to the deploy user
sudo mkdir -p /var/log/portfolio/docker-logs
sudo chown lukasz:lukasz /var/log/portfolio
sudo chown lukasz:lukasz /var/log/portfolio/docker-logs

# Make script executable
chmod +x /home/lukasz/portfolio/infra/scripts/monitoring/collect-logs.sh

# Install cron job
sudo cp /home/lukasz/portfolio/infra/scripts/monitoring/portfolio-collect-logs.cron /etc/cron.d/portfolio-collect-logs
sudo chmod 644 /etc/cron.d/portfolio-collect-logs
```

## 🔗 Related docs

- Infra runbook: [infra/scripts/README.md](../README.md)
- Root project README: [README.md](../../../README.md)
