
## Stage 0 — Preflight Checks

**Host:** syrus
**Operating system:** Ubuntu 24.04 LTS
**Status:** PASSED
**Purpose:** Verify the workstation is ready for a self-hosted n8n deployment.

### Commands Executed

```bash
# HOST: syrus

docker --version
docker compose version
free -h
df -h /data_all
sudo ss -ltnp '( sport = :5678 )'
```

### Verified Results

| Component | Result | Status |
|---|---|---|
| Docker | 29.9.2 | PASS |
| Docker Compose | v5.7.0 | PASS |
| Total memory | 125 GiB | PASS |
| Available memory | 91 GiB | PASS |
| Available disk space | 1.5 TB | PASS |
| TCP port 5678 | No listener detected | PASS |
| Swap | 0 B configured | Observation |

### ELI10 — Command Explanations

- `docker --version`: Displays the installed Docker client version.
- `docker compose version`: Displays the Docker Compose plugin version.
- `free -h`: Displays memory usage in human-readable units.
- `df -h /data_all`: Checks disk space on the filesystem containing `/data_all`.
- `sudo`: Runs the command with elevated privileges.
- `ss`: Displays network socket information.
- `-l`: Show listening sockets.
- `-t`: Show TCP sockets.
- `-n`: Display numeric addresses and ports.
- `-p`: Display associated processes.
- `'( sport = :5678 )'`: Filter for sockets using local port 5678.

### Findings

1. Docker and Docker Compose are installed.
2. The workstation has sufficient available memory and storage for an initial n8n deployment.
3. No process was listening on TCP port 5678 during the check.
4. Swap is not configured; memory requirements will be considered when selecting an Ollama model.
5. Docker daemon connectivity has not yet been verified.

### Changes Made

No packages, containers, or system configuration were modified during Stage 0.

### Conclusion

Stage 0 preflight checks passed.

**Next:** Stage 1 — Verify Docker daemon access and inspect existing containers before deploying n8n.


## Stage 1 — Docker Engine Verification

**Host:** syrus
**Status:** PASSED
**Purpose:** Verify Docker daemon connectivity and inspect existing containers before installing n8n.

### Commands Executed

```bash
docker info --format '{{.ServerVersion}}'

docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

### Verified Results

| Check | Result |
|---|---|
| Docker Engine version | 29.9.2 |
| Docker daemon connectivity | Successful |
| Running Docker containers | None |
| Existing published container ports | None reported |

### ELI10 — Command Explanations

- `docker info`: Requests information from the Docker engine.
- `--format`: Controls how the output is displayed.
- `{{.ServerVersion}}`: Returns the Docker engine version.
- `docker ps`: Lists running containers.
- `{{.Names}}`: Displays container names.
- `{{.Status}}`: Displays container status.
- `{{.Ports}}`: Displays published or exposed ports.
- `\t`: Inserts a tab between output columns.

### Findings

1. The Docker client successfully connected to the Docker daemon.
2. Docker Engine version 29.9.2 was confirmed.
3. No running Docker containers were found.
4. No existing Docker port mappings were reported.
5. No configuration changes were made during verification.

### Conclusion

Docker is operational and ready for the next deployment preparation checks.

**Next:** Prepare an isolated n8n Docker Compose deployment with persistent storage and local-only access.


## Stage 2 — n8n Deployment

### Step 2.1 — Prepare the Installation Directory

**Host:** syrus

**Directory:** `/home/alabi/projects/ai-learning/n8n-lab`

Commands executed:

```bash
mkdir -p ~/projects/ai-learning/n8n-lab
cd ~/projects/ai-learning/n8n-lab
pwd
ls -la
```

**Verified result:** The directory was created successfully and was initially empty.

### Step 2.2 — Create and Validate Docker Compose Configuration

**Configuration file:** `/home/alabi/projects/ai-learning/n8n-lab/compose.yaml`

The Compose configuration defines:

- One n8n service.
- A Docker-managed persistent volume named `n8n_data`.
- Localhost-only port binding (`127.0.0.1:5678:5678`).
- Edmonton timezone configuration.
- Automatic container restart unless explicitly stopped.
- n8n settings-file permission enforcement and task runners.

Commands executed:

```bash
docker compose config --quiet
echo "Compose validation exit code: $?"
docker compose config --services
```

Verified output:

```text
Compose validation exit code: 0
n8n
```

### ELI10 — Command Explanations

- `docker compose config`: Reads and validates the Compose configuration.
- `--quiet`: Suppresses normal output; errors are still reported.
- `$?`: Displays the exit code of the immediately preceding command.
- `--services`: Lists the service names defined in Compose.

### Findings

1. The installation directory exists and is separate from HavenBridge's Kubernetes infrastructure.
2. Docker Compose accepted the configuration.
3. The `n8n` service was detected.
4. No containers have been started during these steps.
5. The container image version has not yet been pinned.

### Next Step

Pin a tested n8n image version, validate the updated Compose configuration, and then deploy the container.


## Step 2.3 — Deploy and Validate n8n

**Host:** syrus
**Deployment directory:** `/home/alabi/projects/ai-learning/n8n-lab`
**Docker image:** `docker.n8n.io/n8nio/n8n:2.46.7`
**Status:** PASSED

### Architecture

The deployment uses Docker Compose to manage one n8n service with persistent storage.

- Container name: `n8n-lab`
- Compose service: `n8n`
- HTTP port: `5678`
- Host binding: `127.0.0.1`
- Persistent volume: `n8n-lab_n8n_data`
- Timezone: `America/Edmonton`

The localhost binding limits access through the published host port to the local machine.

### Security Configuration

A dedicated `.env` file stores the n8n encryption key.

The file is excluded from Git tracking using `.gitignore`.

The encryption key must not be printed in terminal logs, committed to GitHub, or replaced after credentials have been saved without a planned migration.

An encryption key exposed during initial setup was rotated before the owner account and workflows were established. The original test volume was replaced during that reset.

### Docker Compose Validation

```bash
# HOST: syrus
cd ~/projects/ai-learning/n8n-lab

docker compose config --quiet
echo "Validation exit code: $?"
```

**Verified result:** Exit code `0`.

**ELI10:**

- `cd`: Enter the application directory.
- `docker compose config`: Validate the Compose configuration.
- `--quiet`: Suppress normal configuration output, avoiding unnecessary exposure of environment values.
- `$?`: Return the exit code of the immediately preceding command.
- `0`: Success.

### Deployment and Container Status

```bash
# HOST: syrus
docker compose up -d
docker compose ps
```

**ELI10:**

- `up`: Create or start services described in the Compose file.
- `-d`: Run containers in detached/background mode.
- `ps`: Display containers associated with the Compose project.

**Verified result:** The `n8n-lab` container was running with the pinned image `2.46.7`.

### Application Health Verification

```bash
# HOST: syrus
curl -i http://127.0.0.1:5678/healthz
```

**Verified result:**

```text
HTTP/1.1 200 OK

{"status":"ok"}
```

**ELI10:**

- `curl`: Send an HTTP request.
- `-i`: Include response headers.
- `127.0.0.1`: Connect to the local host.
- `5678`: n8n's published HTTP port.
- `/healthz`: Application health endpoint.

### Persistent Storage Verification

```bash
# HOST: syrus
docker volume ls --filter name=n8n-lab_n8n_data
```

**Verified result:** Docker listed `n8n-lab_n8n_data`.

**ELI10:**

- `docker volume ls`: List Docker-managed volumes.
- `--filter`: Limit the displayed results.
- `name=...`: Select volumes matching the specified name.

The named volume stores n8n application data independently of the container lifecycle.

A volume existing does not by itself prove data persistence; that was separately checked through the owner-account restart test.

## Step 2.4 — Owner Account and Persistence Verification

The n8n owner account was created through the browser interface.

The Community Edition license was activated successfully.

A controlled restart was performed:

```bash
# HOST: syrus
docker compose restart n8n
docker compose ps
```

The first HTTP health check returned a connection reset while n8n was still initializing.

A subsequent health check returned HTTP `200 OK`.

After refreshing the browser, the existing owner account remained accessible without repeating registration.

**Result:** Application restart and owner-account persistence verification PASSED.

**ELI10:**

- `restart`: Restart an existing service container.
- `n8n`: Compose service name, not container name.
- `ps`: Verify the container is running.

## Step 2.5 — Configuration Cleanup

The initial startup logs identified `N8N_RUNNERS_ENABLED` as an obsolete environment setting.

The following line was removed from `compose.yaml`:

```yaml
- N8N_RUNNERS_ENABLED=true
```

The configuration was reapplied and the application restarted successfully.

The subsequent logs confirmed:

```text
Registered runner "JS Task Runner"
```

The deprecated setting warning no longer appeared.

**Result:** Configuration cleanup PASSED.

## Step 2.6 — Known Warnings and Limitations

The following warnings remain:

1. Python task runner could not start because Python 3 is unavailable inside the n8n container.
2. Internal task-runner mode is deprecated.
3. Future default changes are announced for unverified community packages, task timeouts, and compression limits.

These warnings did not prevent the current n8n service from starting.

**Future consideration:** Evaluate external task runners before production deployment or introducing workflows requiring Python Code nodes.

No automated remediation was performed.

## Stage 2 Conclusion

The self-hosted n8n deployment is operational.

Verified capabilities include:

- Docker Compose configuration validation
- Pinned n8n image
- Localhost-only HTTP access
- Persistent Docker storage
- Owner-account creation
- Community license activation
- Successful container restart
- Account persistence
- Healthy HTTP endpoint
- JavaScript task-runner registration

**Next:** Stage 3 — Google Sheets integration for synthetic HavenBridge incident records.
