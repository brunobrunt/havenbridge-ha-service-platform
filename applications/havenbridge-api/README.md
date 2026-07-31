## Local HavenBridge API Startup and Validation

The HavenBridge API runs locally on `syrus`, while PostgreSQL runs inside the Kubernetes cluster.

The local connection flow is:

```text
HavenBridge API on syrus
        ↓
127.0.0.1:15432
        ↓
SSH tunnel through eph-cp01
        ↓
Kubernetes PostgreSQL Service
        ↓
havenbridge-postgres-0
```

### Prerequisites

The following resources must already exist:

* PostgreSQL Pod `havenbridge-postgres-0`
* Kubernetes Service `havenbridge-postgres`
* Local Python virtual environment `.venv`
* Local `.env` file
* Temporary PostgreSQL password file

The backend working directory is:

```text
/home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-api
```

---

## 1. Start the PostgreSQL SSH tunnel

Run this step on `syrus` in a dedicated terminal.

First retrieve the current PostgreSQL Service ClusterIP:

```bash
POSTGRES_CLUSTER_IP="$(
  ssh \
    -i /home/alabi/.ssh/eph_k8s \
    mino@172.16.10.31 \
    "kubectl get service havenbridge-postgres \
      -n havenbridge \
      -o jsonpath='{.spec.clusterIP}'"
)"

echo "PostgreSQL Service IP: ${POSTGRES_CLUSTER_IP}"
```

Expected output resembles:

```text
PostgreSQL Service IP: 10.102.178.240
```

Start the SSH tunnel:

```bash
ssh \
  -N \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=60 \
  -o ServerAliveCountMax=3 \
  -i /home/alabi/.ssh/eph_k8s \
  -L "15432:${POSTGRES_CLUSTER_IP}:5432" \
  mino@172.16.10.31
```

This terminal remains occupied while the tunnel is active. That is normal.

The tunnel maps:

```text
127.0.0.1:15432
        ↓
Kubernetes PostgreSQL Service:5432
```

To verify the tunnel from another terminal:

```bash
ss -ltn |
grep ':15432'
```

Expected output should show a listener on local port `15432`.

To stop the foreground tunnel, return to its terminal and press:

```text
Ctrl+C
```

### Optional background tunnel

The tunnel may instead be started in the background:

```bash
ssh \
  -fN \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=60 \
  -o ServerAliveCountMax=3 \
  -i /home/alabi/.ssh/eph_k8s \
  -L "15432:${POSTGRES_CLUSTER_IP}:5432" \
  mino@172.16.10.31
```

Confirm the background process:

```bash
ps -ef |
grep '[s]sh.*15432'
```

---

## 2. Confirm that PostgreSQL is reachable

Open another terminal on `syrus`.

Change to the backend directory:

```bash
cd /home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-api
```

Activate the existing virtual environment:

```bash
source \
  /home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-api/.venv/bin/activate
```

Confirm the active Python interpreter:

```bash
which python
```

Expected:

```text
/home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-api/.venv/bin/python
```

Confirm that the temporary password file exists:

```bash
ls -l \
  /tmp/havenbridge-api-postgres-password
```

If the password file does not exist, recreate it securely:

```bash
umask 077

ssh \
  -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  "kubectl get secret havenbridge-postgres-secret \
    -n havenbridge \
    -o jsonpath='{.data.POSTGRES_PASSWORD}'" |
base64 --decode \
> /tmp/havenbridge-api-postgres-password

chmod 600 \
  /tmp/havenbridge-api-postgres-password
```

Do not display the password file with `cat`.

Test the SQLAlchemy database connection:

```bash
python -c '
from app.database import database_is_ready

print(f"Database ready: {database_is_ready()}")
'
```

Expected:

```text
Database ready: True
```

This confirms:

```text
Python application
        ↓
SQLAlchemy
        ↓
Psycopg
        ↓
SSH tunnel
        ↓
PostgreSQL
```

Do not start Uvicorn until this command returns `True`.

---

## 3. Start the HavenBridge API

Run this command from:

```text
/home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-api
```

Ensure the virtual environment is active:

```bash
cd /home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-api

source .venv/bin/activate
```

Start Uvicorn:

```bash
python -m uvicorn app.main:app \
  --reload \
  --host 127.0.0.1 \
  --port 8000
```

The command means:

```text
python -m uvicorn
    → run the installed Uvicorn module

app.main
    → load app/main.py

:app
    → use the FastAPI object named app

--reload
    → restart automatically after code changes

--host 127.0.0.1
    → accept connections only from syrus

--port 8000
    → expose the API on local port 8000
```

Expected startup logs include:

```text
Uvicorn running on http://127.0.0.1:8000
Starting HavenBridge API in development mode.
Creating missing HavenBridge database tables.
Application startup complete.
```

Keep this terminal open while testing the API.

### Starting through PyCharm

The PyCharm run configuration should use:

```text
Name:
HavenBridge API

Module:
uvicorn

Parameters:
app.main:app --reload --host 127.0.0.1 --port 8000

Working directory:
/home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-api

Python interpreter:
/home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-api/.venv/bin/python
```

The SSH tunnel must already be running before selecting **Run** in PyCharm.

---

## 4. Confirm that FastAPI created the missing table

During application startup, `main.py` runs:

```python
Base.metadata.create_all(
    bind=get_engine(),
)
```

The flow is:

```text
models.py defines ServiceInquiry
        ↓
ServiceInquiry is registered with Base.metadata
        ↓
FastAPI starts
        ↓
Base.metadata.create_all() runs
        ↓
PostgreSQL creates service_inquiries if missing
```

First check the health endpoint:

```bash
command curl -q -sS \
  -w '\nHTTP status: %{http_code}\n' \
  http://127.0.0.1:8000/health/ready
```

Expected:

```text
{"status":"ready"}
HTTP status: 200
```

Then verify the table directly in PostgreSQL:

```bash
ssh \
  -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  "kubectl exec \
    -n havenbridge \
    havenbridge-postgres-0 \
    -c postgresql \
    -- psql \
      -U havenbridge_admin \
      -d havenbridge \
      -c '\d service_inquiries'"
```

Expected columns include:

```text
id
requester_name
requester_email
service_category
message
status
created_at
updated_at
```

A shorter table-existence test is:

```bash
ssh \
  -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  "kubectl exec \
    -n havenbridge \
    havenbridge-postgres-0 \
    -c postgresql \
    -- psql \
      -U havenbridge_admin \
      -d havenbridge \
      -tAc \"SELECT to_regclass('public.service_inquiries');\""
```

Expected:

```text
service_inquiries
```

If nothing is returned, the table does not yet exist.

---

## 5. Test `POST /api/v1/inquiries`

Run this command from any terminal on `syrus` while Uvicorn is running.

Only synthetic data should be used during development:

```bash
command curl -q -sS \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "requester_name": "Jordan Demo",
    "requester_email": "jordan.demo@example.org",
    "service_category": "Respite care",
    "message": "I am requesting information about available respite care services."
  }' \
  -w '\nHTTP status: %{http_code}\n' \
  http://127.0.0.1:8000/api/v1/inquiries
```

Expected response resembles:

```json
{
  "id": 1,
  "requester_name": "Jordan Demo",
  "requester_email": "jordan.demo@example.org",
  "service_category": "Respite care",
  "message": "I am requesting information about available respite care services.",
  "status": "new",
  "created_at": "2026-07-28T00:00:00Z",
  "updated_at": "2026-07-28T00:00:00Z"
}
```

Expected HTTP status:

```text
HTTP status: 201
```

The request flow is:

```text
curl sends JSON
        ↓
POST /api/v1/inquiries
        ↓
ServiceInquiryCreate validates the JSON
        ↓
create_inquiry() creates a ServiceInquiry object
        ↓
SQLAlchemy inserts the row
        ↓
PostgreSQL stores the inquiry
        ↓
ServiceInquiryResponse returns JSON
```

### Confirm the inquiry using the GET endpoint

```bash
command curl -q -sS \
  http://127.0.0.1:8000/api/v1/inquiries |
python3 -m json.tool
```

### Confirm the row directly in PostgreSQL

```bash
ssh \
  -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  "kubectl exec \
    -n havenbridge \
    havenbridge-postgres-0 \
    -c postgresql \
    -- psql \
      -U havenbridge_admin \
      -d havenbridge \
      -c 'SELECT id, requester_name, requester_email, service_category, status, created_at FROM service_inquiries ORDER BY id;'"
```

---

## Correct startup order

Always use this order during local development:

```text
1. Start the SSH tunnel
2. Confirm Database ready: True
3. Start Uvicorn or the PyCharm run configuration
4. Confirm FastAPI created the missing tables
5. Test POST /api/v1/inquiries
6. Confirm the inquiry using GET or PostgreSQL
```

Starting Uvicorn before the SSH tunnel can cause:

```text
connection to server at "127.0.0.1", port 15432 failed
Connection refused
```

Testing the POST endpoint before table creation can cause:

```text
relation "service_inquiries" does not exist
```
---

## Docker Image Validation

The HavenBridge API has been packaged and validated as the following Docker
image:

```text
havenbridge-api:0.1.0
```

The image was built from:

```text
/home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-api/Dockerfile
```

### Non-root container validation

The image was tested with:

```bash
docker run \
  --rm \
  --entrypoint id \
  havenbridge-api:0.1.0
```

Validated result:

```text
uid=100(havenbridge) gid=101(havenbridge) groups=101(havenbridge)
```

This confirms the application runs as the dedicated non-root `havenbridge`
user rather than as `root`.

### Database configuration

The API requires PostgreSQL credentials during startup because SQLAlchemy
connects to PostgreSQL and creates any missing application tables.

The validated database settings were:

```text
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=15432
POSTGRES_USER=havenbridge_admin
POSTGRES_DB=havenbridge
POSTGRES_PASSWORD_FILE=/run/secrets/postgres-password
```

The PostgreSQL password was mounted into the container as a read-only file.

The password was not included in the Docker image, Dockerfile or Git
repository.

### Local container connection path

During local Docker validation, the API ran on `syrus` while PostgreSQL ran
inside Kubernetes.

The temporary connection path was:

```text
HavenBridge API container
        ↓
host.docker.internal:15432
        ↓
Docker bridge: 172.17.0.1
        ↓
SSH tunnel
        ↓
kubectl port-forward on eph-cp01
        ↓
havenbridge-postgres-0:5432
```

This tunnel is required only while the API runs outside Kubernetes.

After the API is deployed in the `havenbridge` namespace, it will connect
directly to the internal PostgreSQL Kubernetes Service.

### Successful container startup

The validated container logs included:

```text
INFO:     Started server process [1]
INFO:     Waiting for application startup.
Starting HavenBridge API in development mode.
Creating missing HavenBridge database tables.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

This confirms that:

* The Docker container started successfully
* FastAPI completed its startup lifecycle
* The PostgreSQL connection succeeded
* SQLAlchemy created any missing tables
* Uvicorn listened on all container network interfaces

### Database tables confirmed

The following tables were confirmed in PostgreSQL:

```text
public | platform_validation | table | havenbridge_admin
public | service_inquiries   | table | havenbridge_admin
```

The `platform_validation` table was used to validate PostgreSQL persistence.

The `service_inquiries` table is used by the HavenBridge API to store service
inquiry submissions.

### Validation status

* [x] Docker image built successfully
* [x] Image runs as a non-root user
* [x] PostgreSQL password supplied through a read-only file
* [x] Local container connected to PostgreSQL in Kubernetes
* [x] FastAPI startup completed successfully
* [x] SQLAlchemy created the required tables
* [x] `platform_validation` table confirmed
* [x] `service_inquiries` table confirmed
* [x] Docker and PostgreSQL troubleshooting documented

Detailed commands and troubleshooting steps are recorded in:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/runbooks/havenbridge-api-postgresql-validation.txt
```

## Next Application Step

The next step is to:

1. Publish `havenbridge-api:0.1.0` to a container registry
2. Deploy the API as a Kubernetes Deployment
3. Create an internal ClusterIP Service
4. Configure PostgreSQL access through Kubernetes Secrets and ConfigMaps
5. Add readiness and liveness probes
6. Add CPU and memory requests and limits
7. Validate direct in-cluster API-to-PostgreSQL communication
8. Expose the API through Traefik and Gateway API

