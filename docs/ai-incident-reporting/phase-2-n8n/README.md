
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
