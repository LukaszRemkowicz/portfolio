# Log Collector

Standalone Python application for deterministic log snapshot collection.

## Purpose

This package is a separate library/runtime responsible only for collecting logs
from configured sources and writing snapshot files.

It does not know anything about the core application's monitoring analysis or
email flow. Its integration boundary is the manifest plus the written snapshot
files.

It is intended for a dedicated collector image or other trusted infra runtime
that has Docker daemon access.

The collector currently writes:

- writes `backend.log`, `frontend.log`
- writes `nginx_access.log`, `nginx_runtime.log`
- writes `traefik_access.log`, `traefik_runtime.log`
- writes `fail2ban.log` when the host fail2ban log is mounted and available
- `collected_at.txt`

It also:

- archives the previous snapshot set
- prunes old archives
- keeps raw Docker API errors in a separate tool log

The collector supports two source types:

- `docker` for application/container stdout-stderr logs
- `file` for host-mounted access and error logs such as nginx and Traefik

## Manifest boundary

The collector is manifest-driven.

Bundled manifest:

- `collector/src/log_collector/log_sources.json`

The manifest defines:

- logical source key
- output filename
- source type
- whether the source is required
- service/container overrides for Docker-backed sources
- path overrides for file-backed sources

This is the collector's connector boundary. Source naming, output naming, and
most source-definition changes should happen in the manifest rather than in the
collector workflow code.

## Docker Usage

The collector is designed to run as a dedicated Docker image or other trusted
runtime that has Docker daemon access.

The image is built from:

- `docker/collector/Dockerfile`

The collector does **not** shell out to `docker logs`. It talks to Docker
through the Python Docker SDK and therefore still needs daemon access at
runtime.

For file-backed sources, the collector must also be able to read the mounted
access-log files directly.

Typical Docker runtime requirements:

- mount a Docker socket into the collector container
- set `DOCKER_HOST` when needed
- mount the output directory for `DOCKER_LOGS_DIR`
- provide `COMPOSE_PROJECT_NAME` so the collector can resolve Docker service containers
- mount host log files when file-backed sources are enabled

Recommended local run:

```bash
docker compose -f docker-compose.collector.yml build
ENVIRONMENT=dev \
COLLECTOR_COMPOSE_PROJECT_NAME=portfolio-dev \
docker compose -f docker-compose.collector.yml run --rm log-collector
```

The repo includes a small dedicated compose file:

- `docker-compose.collector.yml`

For production cron usage, the repo also includes:

- `collector/portfolio-log-collector.cron`

That cron runs the collector container against the production snapshot
directory and the same nginx/Traefik host log directories used by the
producing services.

It mounts:

- `DOCKER_LOGS_DIR` defaults to `/app/docker-logs`
- `LOG_SNAPSHOT_HOST_DIR` defaults to `/var/log/portfolio/docker-logs`
- `/var/run/docker.sock` gives the collector Docker daemon access
- `${NGINX_LOG_DIR:-/var/log/portfolio/nginx/prod}` is mounted read-only at `/var/log/nginx`
- `${TRAEFIK_LOG_DIR:-/var/log/portfolio/traefik}` is mounted read-only at `/var/log/traefik`
- `${FAIL2BAN_LOG_SOURCE:-/var/log/fail2ban.log}` is mounted read-only at `/var/log/fail2ban.log`
- compose owns the default runtime values for production collection
- local runs can override those defaults through host environment variables

If you still prefer a one-shot Docker command, the equivalent runtime is:

```bash
docker run --rm \
  -e DOCKER_HOST=unix:///var/run/docker.sock \
  -e DOCKER_LOGS_DIR=/app/docker-logs \
  -e ENVIRONMENT=prod \
  -e COLLECTOR_COMPOSE_PROJECT_NAME=portfolio-prod \
  -v /var/log/portfolio/docker-logs:/app/docker-logs \
  -v /var/log/portfolio/nginx/prod:/var/log/nginx:ro \
  -v /var/log/portfolio/traefik:/var/log/traefik:ro \
  -v /var/log/fail2ban.log:/var/log/fail2ban.log:ro \
  -v /var/run/docker.sock:/var/run/docker.sock \
  portfolio-log-collector:dev
```

## Runtime contract

Required environment variables:

- `DOCKER_LOGS_DIR`
- `COLLECTOR_COMPOSE_PROJECT_NAME`

Optional environment variables:

- `ENVIRONMENT`
- `COMPOSE_PROJECT_NAME`
- `COMPOSE_FILE`
- `LOG_TAIL`
- `LOG_SINCE`
- `ARCHIVE_RETENTION_DAYS`
- `DOCKER_TOOL_LOG`
- `LOG_SOURCES_MANIFEST`
- `BACKEND_SERVICE`
- `FRONTEND_SERVICE`
- `NGINX_SERVICE`
- `TRAEFIK_SERVICE`
- `TRAEFIK_PROJECT_NAME`
- `TRAEFIK_CONTAINER_NAME`
- `NGINX_ACCESS_LOG_PATH`
- `NGINX_ERROR_LOG_PATH`
- `TRAEFIK_ACCESS_LOG_PATH`
- `FAIL2BAN_LOG_PATH`

`LOG_SNAPSHOT_HOST_DIR` is not an app setting. It is only a compose/runtime
helper for choosing the host bind-mount source that backs `DOCKER_LOGS_DIR`
inside the container, which defaults to `/app/docker-logs`.

`COLLECTOR_COMPOSE_PROJECT_NAME` is also a compose/runtime helper. It becomes
`COMPOSE_PROJECT_NAME` inside the collector container so the app can resolve
the right Docker Compose service containers without depending on a checked-out
compose file.

`FAIL2BAN_LOG_SOURCE` is a compose/runtime helper for the host-side source file
that is mounted into the collector at `/var/log/fail2ban.log`. The collector
app still reads that mounted path through the manifest default.

## Usage

```bash
cd collector
python -m pip install -e ".[test]"
portfolio-log-collector
```

Or directly:

```bash
PYTHONPATH=src python -m log_collector.main
```

Direct Python execution still requires Docker daemon access if you want the
collector to resolve containers and fetch logs. File-backed sources also require
read access to the configured log paths.

## Production Playbook

### 1. Rebuild the collector image

```bash
docker compose -f docker-compose.collector.yml build
```

### 2. Run one manual collection

This verifies the collector can resolve configured sources, read the required
log inputs, and write the snapshot set into the configured output directory.

```bash
docker compose -f docker-compose.collector.yml run --rm -e COLLECTOR_COMPOSE_PROJECT_NAME=portfolio-prod log-collector
```

### 3. Verify snapshot output

Confirm the latest snapshot files exist:

```bash
ls -lh /var/log/portfolio/docker-logs
```

Expected files:

- `backend.log`
- `frontend.log`
- `nginx_access.log`
- `nginx_runtime.log`
- `traefik_access.log`
- `traefik_runtime.log`
- `fail2ban.log`
- `collected_at.txt`

The collector compose runtime mounts the host fail2ban log directly at
`/var/log/fail2ban.log`, so the manifest default can keep the same path inside
the container as on the host.

The default collector/runtime mapping is:

- host snapshot directory: `/var/log/portfolio/docker-logs`
- collector container path: `/app/docker-logs`
- backend container path: `/app/docker-logs`
- host nginx log directory: `${NGINX_LOG_DIR:-/var/log/portfolio/nginx/prod}`
- collector nginx path: `/var/log/nginx`
- host Traefik log directory: `${TRAEFIK_LOG_DIR:-/var/log/portfolio/traefik}`
- collector Traefik path: `/var/log/traefik`

That keeps `DOCKER_LOGS_DIR` consistent inside both containers while still
storing the snapshot files outside the repo on the host and reading raw nginx
and Traefik logs from the same host directories their services already use.

Confirm archive rotation works after a second run:

```bash
find /var/log/portfolio/docker-logs/archive -maxdepth 1 -type d | sort
```

### 4. Install the cron job

The repo template lives at:

- `collector/portfolio-log-collector.cron`

Install it on the server:

```bash
sudo cp collector/portfolio-log-collector.cron /etc/cron.d/portfolio-log-collector
sudo chmod 644 /etc/cron.d/portfolio-log-collector
```

The cron runs through `doppler run --config prod` so the collector resolves the
same environment-backed log directory settings as the production services.

### 5. Verify cron pickup

```bash
systemctl status cron
cat /etc/cron.d/portfolio-log-collector
```

Cron output is appended to:

- `/var/log/portfolio/log-collector.log`

## Testing

```bash
PYTHONPATH=collector/src pytest collector/tests
```

If the package is installed in editable mode with the `test` extra, the same test
suite can also be run from inside the `collector/` directory with:

```bash
pytest tests
```
