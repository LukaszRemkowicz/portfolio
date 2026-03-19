# infra/scripts/monitoring/README.md

## Monitoring Scripts

Scripts for the **AgentLog** — the daily Docker log collection and analysis pipeline.

---

### `collect-logs.sh`

Collects logs from Docker containers and writes them to a shared directory on the **host** server.
This is **Phase 1** of the AgentLog pipeline. It runs as a daily Ubuntu cron job (no Python, no Celery, no dependencies).

**What it does:**
1. Clears any existing log files in `DOCKER_LOGS_DIR` (no stale data)
2. Collects Docker logs for backend and reverse-proxy containers
3. Writes `backend.log` and `nginx.log` to `DOCKER_LOGS_DIR` when available
4. Writes `collected_at.txt` with an ISO timestamp so the Celery worker can detect stale/missing data

**Environment variables:**

| Variable | Required | Default | Description |
|---|---|---|---|
| `DOCKER_LOGS_DIR` | ✅ Yes | — | Absolute path where log files are written |
| `COMPOSE_FILE` | No | `/home/lukasz/portfolio/docker-compose.prod.yml` | Path to docker compose file |
| `LOG_TAIL` | No | `2000` | Number of log lines to collect per container |
| `BACKEND_SERVICE` | No | `portfolio-be` | Docker Compose service name for backend |
| `NGINX_SERVICE` | No | `nginx` | Docker Compose service name for Nginx |
| `TRAEFIK_SERVICE` | No | `traefik` | Docker Compose service name for Traefik |

**Manual run:**
```bash
DOCKER_LOGS_DIR=/var/log/portfolio/docker-logs /home/lukasz/portfolio/infra/scripts/monitoring/collect-logs.sh
```

---

### `portfolio-collect-logs.cron`

System cron entry that runs `collect-logs.sh` daily at midnight UTC.

**Installation:**
```bash
sudo cp portfolio-collect-logs.cron /etc/cron.d/portfolio-collect-logs
sudo chmod 644 /etc/cron.d/portfolio-collect-logs
```

> **Note:** No `systemctl enable` or `crontab -e` required. Ubuntu's `cron` daemon is enabled by default and automatically picks up any file placed in `/etc/cron.d/` within ~1 minute.
> Verify cron is running: `systemctl status cron`

**Log output:** Appended to `/var/log/portfolio/collect-logs.log`

---

### Server Setup (one-time)

```bash
# Create the log directory and grant access to the lukasz user
sudo mkdir -p /var/log/portfolio/docker-logs
sudo chown lukasz:lukasz /var/log/portfolio
sudo chown lukasz:lukasz /var/log/portfolio/docker-logs

# Make script executable
chmod +x /home/lukasz/portfolio/infra/scripts/monitoring/collect-logs.sh

# Install cron job
sudo cp /home/lukasz/portfolio/infra/scripts/monitoring/portfolio-collect-logs.cron /etc/cron.d/portfolio-collect-logs
sudo chmod 644 /etc/cron.d/portfolio-collect-logs
```
