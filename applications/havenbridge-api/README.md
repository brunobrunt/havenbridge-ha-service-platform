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

