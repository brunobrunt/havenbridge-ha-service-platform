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

## # Document the port used by Uvicorn.
## Uvicorn is the web server that runs the FastAPI application and listens for incoming HTTP requests.

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

### Next Application Step
#
#The next step is to:
#
#1. Publish `havenbridge-api:0.1.0` to a container registry
#2. Deploy the API as a Kubernetes Deployment
#3. Create an internal ClusterIP Service
#4. Configure PostgreSQL access through Kubernetes Secrets and ConfigMaps
#5. Add readiness and liveness probes
#6. Add CPU and memory requests and limits
#7. Validate direct in-cluster API-to-PostgreSQL communication
#8. Expose the API through Traefik and Gateway API


## Current Application Direction

The original `havenbridge-api:0.1.0` container-validation milestone has been
completed.

The HavenBridge API is now:

- published through GHCR;
- deployed to Kubernetes;
- exposed through Traefik and Gateway API;
- integrated with PostgreSQL;
- protected with readiness and liveness probes;
- released through semantic Git tags;
- deployed through the self-hosted CD pipeline.

The current application improvement is automatic version reporting so the
running API can report the semantic release version supplied by the release
pipeline.


## PostgreSQL Application Integration

The HavenBridge FastAPI backend connects to PostgreSQL using SQLAlchemy and
Psycopg.

These components have different responsibilities:

```text
FastAPI
   ↓
SQLAlchemy
   ↓
Psycopg
   ↓
PostgreSQL
```

### What FastAPI Does

FastAPI provides the application API endpoints.

For example, a request such as:

```text
POST /api/v1/inquiries
```

is received by FastAPI.

The application then processes the request and may need to create, retrieve or
update information in PostgreSQL.

FastAPI itself is not the PostgreSQL database driver.

### What SQLAlchemy Does

SQLAlchemy provides the higher-level database layer used by the HavenBridge
application.

It allows the application to work with database concepts such as:

- Python database models;
- database tables;
- queries;
- sessions;
- creating records;
- retrieving records; and
- updating records.

For example, the application can represent an inquiry as a Python object and
SQLAlchemy can map that application data to the PostgreSQL table:

```text
service_inquiries
```

The relationship can be pictured as:

```text
Python application object
        ↓
SQLAlchemy
        ↓
PostgreSQL table
```

HavenBridge currently uses PostgreSQL tables including:

```text
platform_validation
service_inquiries
```

### What Psycopg Does

Psycopg is the PostgreSQL driver used by the Python application.

While SQLAlchemy provides the higher-level database interface, Psycopg handles
the lower-level communication with the PostgreSQL server.

A simple way to remember the difference is:

```text
SQLAlchemy
    =
"What database operation does the application want to perform?"

Psycopg
    =
"How does Python actually communicate that operation to PostgreSQL?"

PostgreSQL
    =
"Where is the application data stored?"
```

SQLAlchemy therefore uses the PostgreSQL driver underneath when communicating
with the database.

### HavenBridge Database Request Flow

A database-backed HavenBridge request can be pictured as:

```text
Client
   ↓
FastAPI endpoint
   ↓
Application logic
   ↓
SQLAlchemy
   ↓
Psycopg
   ↓
PostgreSQL connection
   ↓
PostgreSQL
   ↓
Application table
```

Inside Kubernetes, the network portion of that flow becomes:

```text
HavenBridge API Pod
        ↓
SQLAlchemy
        ↓
Psycopg
        ↓
PostgreSQL Service
        ↓
TCP/5432
        ↓
PostgreSQL StatefulSet
```

SQLAlchemy and Psycopg are therefore application components running inside the
FastAPI container.

The PostgreSQL Service, StatefulSet and NetworkPolicies are Kubernetes
resources that provide the infrastructure around that application connection.

### Simple Memory Hook

```text
FastAPI
= receives and processes the API request

SQLAlchemy
= manages the application's database operations

Psycopg
= PostgreSQL driver used to communicate with the database

PostgreSQL
= stores the application data
```

### Interview Explanation

A concise way to explain the design is:

> The HavenBridge FastAPI backend uses SQLAlchemy as its database abstraction
> and ORM layer, while Psycopg acts as the PostgreSQL driver. SQLAlchemy
> manages models, sessions and database operations, while Psycopg provides the
> underlying communication with PostgreSQL.


## Service Inquiry Status Updates

The HavenBridge API supports updating the workflow status of an existing
service inquiry.

This capability is being introduced as part of the v0.4.0 application
release.

### Endpoint

```text
PATCH /api/v1/inquiries/{inquiry_id}/status
```

The endpoint accepts a JSON body containing the new workflow status.

Example:

```bash
curl -s \
  -X PATCH \
  http://127.0.0.1:8000/api/v1/inquiries/1/status \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "referred"
  }'
```

### Approved Workflow Statuses

The currently approved inquiry statuses are:

```text
new
reviewing
referred
closed
```

FastAPI validates these values before attempting a database update.

PostgreSQL independently protects the `service_inquiries.status` column with
the constraint:

```text
ck_service_inquiries_status
```

The validation flow is:

```text
HTTP request
     ↓
Pydantic validation
     ↓
SQLAlchemy
     ↓
PostgreSQL CHECK constraint
```

This means invalid status values remain blocked even when FastAPI is bypassed
and SQL is executed directly against PostgreSQL.

### PostgreSQL Constraint Validation

A direct SQL operation was deliberately attempted using an unsupported status.

PostgreSQL rejected the operation with:

```text
new row for relation "service_inquiries"
violates check constraint "ck_service_inquiries_status"
```

This proved that the database-level status constraint is functioning
independently of FastAPI.

### Successful Status Update Validation

A synthetic inquiry was created through:

```text
POST /api/v1/inquiries
```

The new inquiry initially had:

```text
id     = 1
status = new
```

The status-update endpoint was then used to transition the inquiry through:

```text
new
 ↓
reviewing
 ↓
referred
```

The successful PATCH request returned HTTP `200 OK`.

The persisted row was independently checked inside PostgreSQL using:

```sql
SELECT
    id,
    status,
    created_at,
    updated_at,
    updated_at > created_at AS timestamp_updated
FROM service_inquiries
WHERE id = 1;
```

The validation confirmed:

```text
id                = 1
status            = referred
timestamp_updated = true
```

This proved that the status change was persisted and that `updated_at`
changed when the database record was modified.

### Invalid Status Validation

An unsupported status was deliberately submitted:

```bash
curl -i \
  -X PATCH \
  http://127.0.0.1:8000/api/v1/inquiries/1/status \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "pending"
  }'
```

Result:

```text
HTTP/1.1 422 Unprocessable Entity
```

FastAPI reported that the status must be one of:

```text
new
reviewing
referred
closed
```

This proves that unsupported workflow statuses are rejected before PostgreSQL
is modified.

### Missing Inquiry Validation

A valid status was submitted for an inquiry that does not exist:

```bash
curl -i \
  -X PATCH \
  http://127.0.0.1:8000/api/v1/inquiries/9999/status \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "reviewing"
  }'
```

Result:

```text
HTTP/1.1 404 Not Found
```

The API returned:

```json
{
  "detail": "Service inquiry not found."
}
```

### Automated Test Coverage

Before this feature was implemented, the HavenBridge API test suite contained
six passing tests.

Four tests were added for the status-update capability:

```text
Valid status update                          PASS
Invalid status returns HTTP 422              PASS
Missing inquiry returns HTTP 404             PASS
Updated status remains visible through GET   PASS
```

The complete suite was then executed:

```bash
pytest -q
```

Result:

```text
10 passed
```

The current Starlette test-client deprecation warning does not cause any test
failures and can be handled later as a dependency-maintenance item.

### Python Syntax Validation

The modified Python files were checked with:

```bash
python -m py_compile \
  app/schemas.py \
  app/routers/inquiries.py \
  tests/conftest.py
```

A successful command returned no output.

The difference between the two validation tools is:

```text
py_compile = validates Python syntax
pytest     = validates tested application behavior
```

### Real PostgreSQL Validation Path

Local FastAPI testing on `syrus` reaches PostgreSQL through:

```text
FastAPI on syrus
      ↓
127.0.0.1:25432
      ↓
havenbridge-postgres-ssh-tunnel.service
      ↓
eph-cp01:127.0.0.1:25432
      ↓
havenbridge-postgres-portforward.service
      ↓
havenbridge-postgres-0:5432
      ↓
PostgreSQL database: havenbridge
```

Both forwarding services bind only to `127.0.0.1`, so PostgreSQL is not
directly exposed to the lab network.


### v0.4.0 Release and Kubernetes Validation

The service-inquiry status-update feature was released as:

```text
v0.4.0
```

Release commit:

```text
f4c146b97297455432ff37b9641e88806133ec0b
```

The normal CI workflow first validated the application change.

The `v0.4.0` Git tag then triggered the HavenBridge Release workflow, which
built and published the release images to GHCR.

After the Release workflow completed successfully, the HavenBridge CD workflow
automatically ran on the self-hosted runner.

The CD workflow updated the Kubernetes Deployment to:

```text
ghcr.io/brunobrunt/havenbridge-api:f4c146b97297455432ff37b9641e88806133ec0b
```

The deployed image was verified with:

```bash
kubectl get deployment havenbridge-api \
  -n havenbridge \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="havenbridge-api")].image}{"\n"}'
```

Important:

The `kubectl get deployment` command does not modify the Deployment.

It only reads the image currently configured in the Deployment.

The actual image change was performed earlier by the CD workflow using
`kubectl set image`.

The deployment rollout was verified with:

```bash
kubectl rollout status \
  deployment/havenbridge-api \
  -n havenbridge \
  --timeout=180s
```

Result:

```text
deployment "havenbridge-api" successfully rolled out
```

Two application Pods were confirmed running:

```text
havenbridge-api-5c8bf7fcd7-c8ggj   1/1   Running   eph-worker01
havenbridge-api-5c8bf7fcd7-wt5xc   1/1   Running   eph-worker02
```

### Gateway Validation

The deployed API was successfully reached through the HavenBridge application
Gateway.

On `syrus`:

```bash
curl -k -i https://havenbridge.lab/
```

returned:

```text
HTTP/2 200
```

On `eph-cp01`, `havenbridge.lab` was not locally resolvable, so the Gateway IP
was supplied explicitly:

```bash
curl -k -i \
  --resolve havenbridge.lab:443:172.16.10.40 \
  https://havenbridge.lab/
```

This also returned:

```text
HTTP/2 200
```

This confirmed that the Gateway, Traefik routing, HTTPRoute, Service, and API
Pods were functioning correctly.

The missing `havenbridge.lab` name resolution on `eph-cp01` is a separate lab
DNS/hosts follow-up and did not affect the deployed application.

### Deployed PATCH Validation

The new v0.4.0 endpoint was tested through the Kubernetes Gateway:

```bash
curl -k -i \
  --resolve havenbridge.lab:443:172.16.10.40 \
  -X PATCH \
  https://havenbridge.lab/api/v1/inquiries/1/status \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "closed"
  }'
```

Result:

```text
HTTP/2 200
```

The API response confirmed:

```text
id     = 1
status = closed
```

The database change was then independently verified inside the PostgreSQL Pod:

```bash
kubectl exec -it \
  -n havenbridge \
  havenbridge-postgres-0 \
  -c postgresql \
  -- psql \
  -U havenbridge_admin \
  -d havenbridge
```

Using:

```sql
SELECT
    id,
    requester_name,
    status,
    created_at,
    updated_at
FROM service_inquiries
WHERE id = 1;
```

Result:

```text
id             = 1
requester_name = Version 0.4 Test
status         = closed
updated_at     = 2026-08-21 16:14:48.550344+00
```

This proved the full production-style v0.4.0 path:

```text
Git tag v0.4.0
       ↓
Release workflow
       ↓
GHCR
       ↓
CD workflow
       ↓
Self-hosted runner
       ↓
Kubernetes Deployment
       ↓
Traefik / Gateway API
       ↓
HavenBridge API
       ↓
PATCH status update
       ↓
PostgreSQL persistence
```

### v0.4.0 Final Validation Status

```text
CI application tests                     PASS
Docker build                             PASS
Kubernetes manifest validation           PASS
GHCR publication                         PASS
v0.4.0 Release workflow                  PASS
Release-to-CD workflow handoff           PASS
Self-hosted CD deployment                PASS
Exact SHA image verification             PASS
Kubernetes rollout                       PASS
Two API Pods running                     PASS
Gateway HTTP/2 access                    PASS
Deployed PATCH endpoint                  PASS
PostgreSQL persistence verification      PASS
```

One follow-up item was identified during validation:

```text
At the time of the v0.4.0 deployment validation, GET / reported
application version 0.1.0 while the deployed release was v0.4.0.
```

Application version reporting should be updated in a future change so the API
reports the actual deployed release/version.



## Service Inquiry Lookup by ID

HavenBridge now supports retrieving one service inquiry directly by its
database ID.

Endpoint:

```text
GET /api/v1/inquiries/{inquiry_id}
```

Example:

```text
GET /api/v1/inquiries/1
```

The request flow is:

```text
Client requests inquiry ID
        ↓
FastAPI receives inquiry_id
        ↓
SQLAlchemy searches ServiceInquiry by primary key
        ↓
Record found?
    ├── Yes → return inquiry with HTTP 200
    └── No  → return HTTP 404
```

The route is implemented in:

```text
applications/havenbridge-api/app/routers/inquiries.py
```

The database lookup uses:

```python
inquiry = db.get(ServiceInquiry, inquiry_id)
```

`ServiceInquiry` tells SQLAlchemy which database model to search.

`inquiry_id` contains the primary-key value requested by the client.

For example:

```text
GET /api/v1/inquiries/5
```

results conceptually in:

```text
Look in service_inquiries
        ↓
Find primary key ID 5
        ↓
Return that inquiry
```

If the inquiry does not exist, HavenBridge returns:

```json
{
  "detail": "Service inquiry not found."
}
```

with:

```text
HTTP 404 Not Found
```

### Local Validation

Two automated tests were added in:

```text
applications/havenbridge-api/tests/test_inquiries.py
```

The first test validates successful retrieval:

```text
Create inquiry
        ↓
Read generated ID
        ↓
GET /api/v1/inquiries/{id}
        ↓
HTTP 200
        ↓
Correct inquiry returned
```

The second test validates the missing-record path:

```text
GET /api/v1/inquiries/9999
        ↓
No matching database record
        ↓
HTTP 404
        ↓
"Service inquiry not found."
```

Individual validation results:

```text
test_get_inquiry_returns_requested_record          PASS
test_get_inquiry_returns_404_for_missing_inquiry   PASS
```

The complete HavenBridge API test suite was also executed:

```text
12 passed
1 dependency deprecation warning
```

The warning is produced by the current Starlette/httpx test dependency and
does not represent a failure of the inquiry lookup feature.

### Release Significance

This is a new HavenBridge API capability rather than a documentation,
infrastructure, or CI/CD-only change.

It therefore qualifies as a semantic-version MINOR change under the current
HavenBridge release policy:

```text
feat: → MINOR
```

With the current release at:

```text
v0.5.0
```

the semantic-version automation is expected to calculate:

```text
v0.6.0
```

after this feature is committed using a `feat:` conventional commit.

The version is not created manually. The HavenBridge Release workflow will be
responsible for calculating and creating the release tag during the upcoming
end-to-end validation.



## Python Learning Note — Centralized Application Version Configuration

During the HavenBridge v0.4.0 work, the API version was found to be
hard-coded in two places inside:

```text
applications/havenbridge-api/app/main.py
```

The original code contained:

```python
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)
```

and the root endpoint returned:

```python
return {
    "name": settings.app_name,
    "environment": settings.app_environment,
    "version": "0.1.0",
}
```

This caused a problem after HavenBridge progressed to release `v0.4.0`.

Although Kubernetes was running the `v0.4.0` release image, the API still
reported:

```json
{
  "version": "0.1.0"
}
```

The container version and the version reported by the application had therefore
drifted apart.

### What Was Changed

A central application-version setting was added to:

```text
applications/havenbridge-api/app/config.py
```

using:

```python
app_version: str = "unreleased"
```

The two hard-coded values in `main.py` were then changed to use:

```python
settings.app_version
```

FastAPI configuration now uses:

```python
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)
```

The root endpoint now uses:

```python
return {
    "name": settings.app_name,
    "environment": settings.app_environment,
    "version": settings.app_version,
    "documentation": "/docs",
    "liveness": "/health/live",
    "readiness": "/health/ready",
}
```

### Python Concept: What Is `app_version`?

Inside the `Settings` class:

```python
app_version: str = "unreleased"
```

defines a configuration field.

Breaking the line down:

```text
app_version
    ↓
name of the setting

str
    ↓
Python type hint
    ↓
the value should be a string

"0.4.0"
    ↓
default value
```

Therefore:

```python
app_version: str = "unreleased"
```

can be read as:

> Create a setting named `app_version`. Its value should be a string, and use
> `"0.4.0"` as the default if another value is not supplied.

The application accesses that field through:

```python
settings.app_version
```

This can be thought of as:

```text
settings
   ↓
Settings object
   ↓
app_version
   ↓
"unreleased"

APP_VERSION=0.5.0
        ↓
Pydantic BaseSettings
        ↓
settings.app_version
        ↓
"0.5.0"
```

### Why `settings.app_version` Is Better Than Repeating `"0.4.0"`

Without centralized configuration:

```text
main.py

FastAPI metadata → "0.4.0"

GET / response   → "0.4.0"

other code       → possibly another "0.4.0"
```

Each value would need to be changed independently.

That creates a risk that one location could be forgotten.

With centralized configuration:

```text
config.py

app_version
     ↓
settings.app_version
     ├── FastAPI metadata
     └── GET / response
```

there is one source of application configuration used by multiple parts of the
program.

This is an example of the principle:

```text
Define once
    ↓
Reuse where needed
```

### Important: The Version Is Still a Default Value
### Why the Default Is `unreleased`

The HavenBridge configuration now uses:

```python
app_version: str = "unreleased"
```

still contains a default version in the Python configuration.

If HavenBridge later releases:

```text
v0.5.0
```

and nothing else changes, the application could still report:

```text
0.4.0
```

The next improvement will therefore be to supply the application version from
the release/deployment environment rather than manually changing the Python
source for every release.

### Why `BaseSettings` Helps

The HavenBridge `Settings` class inherits from:

```python
BaseSettings
```

from Pydantic Settings.

This allows configuration fields to be overridden using environment variables.

For example, the Python field:

```python
app_version
```

can receive a value from:

```text
APP_VERSION
```

Conceptually:

```text
APP_VERSION=0.5.0
        ↓
Pydantic Settings
        ↓
settings.app_version
        ↓
"0.5.0"
```

The Python code using:

```python
settings.app_version
```

does not need to change.

For a future major release:

```text
APP_VERSION=1.0.0
        ↓
settings.app_version
        ↓
FastAPI
        ↓
GET /
        ↓
"version": "1.0.0"
```

### Current Versus Target Design

The original design was:

```text
main.py
   ↓
"0.1.0"
   ↓
hard-coded in multiple locations
```

Problem:

```text
Release changes
    ↓
Python version does not automatically change
    ↓
reported version becomes inaccurate
```

The current design is:

```text
config.py
    ↓
app_version = "0.4.0"
    ↓
settings.app_version
    ├── FastAPI metadata
    └── GET / response
```

This centralizes application-version configuration.

The future target design is:

```text
Git release tag
v0.5.0
    ↓
GitHub Actions:
GITHUB_REF_NAME=v0.5.0
    ↓
Bash parameter expansion:
${GITHUB_REF_NAME#v}
    ↓
0.5.0
    ↓
docker build
--build-arg APP_VERSION=0.5.0
    ↓
Dockerfile ARG APP_VERSION
    ↓
Dockerfile ENV APP_VERSION
    ↓
Pydantic BaseSettings
    ↓
settings.app_version
    ├── FastAPI metadata
    └── GET / response
    ↓
"version": "0.5.0"

Later:

```text
Git release
v1.0.0
    ↓
APP_VERSION=1.0.0
    ↓
same Python application code
    ↓
"version": "1.0.0"
```

The important idea is that future releases should not require editing
`main.py` merely to change a version number.

### Python Learning Takeaway

This change introduced several useful Python concepts:

```text
Configuration field
        ↓
app_version: str = "unreleased"

Object attribute access
        ↓
settings.app_version

Reuse
        ↓
one setting used in multiple locations

Environment-driven configuration
        ↓
APP_VERSION can override the default

Separation of concerns
        ↓
config.py stores configuration
main.py uses configuration
```

The key lesson is:

> Application behavior should generally read configuration from a central
> source instead of repeating hard-coded values throughout the program.

### HavenBridge Follow-Up

Current state:

```text
Central app_version setting             IMPLEMENTED
FastAPI uses settings.app_version       IMPLEMENTED
Root endpoint uses settings.app_version IMPLEMENTED
Automatic release-version injection     IMPLEMENTED
```

A future CI/CD improvement will pass the semantic release version into the
container or Kubernetes environment so releases such as:

```text
v0.5.0
v0.6.0
v1.0.0
```

can automatically be reported by the running API without editing Python source
code for each release.
