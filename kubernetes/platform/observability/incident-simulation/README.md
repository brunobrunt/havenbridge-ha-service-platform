# HavenBridge Incident Simulation

This directory documents controlled HavenBridge failure scenarios performed
during Observability Phase 8 and the follow-up observability improvements
validated during Observability Phase 9.

The purpose of these simulations is to validate the operational workflow:

```text
Detect
  ↓
Observe
  ↓
Investigate
  ↓
Correlate metrics + logs + Kubernetes state
  ↓
Identify root cause
  ↓
Recover
  ↓
Verify
  ↓
Document
```

Each scenario preserves the failure-injection command, Kubernetes state,
Grafana observations, application behavior, recovery steps and screenshots.

---

## Incident 1 — Degraded HavenBridge API Replica Availability

### Scenario

The HavenBridge API normally runs with two replicas distributed across the two
Kubernetes worker nodes.

Normal state:

```text
havenbridge-api
        ↓
2 replicas
        ↓
eph-worker01
eph-worker02
        ↓
HEALTHY
```

The Deployment was intentionally reduced from two replicas to one.

The goal was to validate whether:

- HavenBridge remained externally available;
- Grafana detected the loss of redundancy;
- the remaining replica continued serving requests;
- HTTP 5xx errors remained absent;
- an incorrect full-outage alert was avoided; and
- the application could be restored cleanly.

---

### Before — Healthy Baseline

Before introducing the failure, the HavenBridge API Deployment reported:

```text
READY       2/2
UP-TO-DATE  2
AVAILABLE   2
```

One API Pod was running on each worker node.

External application validation from `syrus` returned:

```text
HTTP 200
```

The healthy dashboard state is shown below.

![Healthy HavenBridge operational overview](screenshots/incident-01-degraded-api/01-before-healthy-overview.png)

The supporting dashboard panels also showed no active alerts and no recent
container restarts.

![Healthy HavenBridge alerts and logs](screenshots/incident-01-degraded-api/02-before-healthy-alerts-logs.png)

The healthy baseline established:

```text
API replicas       → HEALTHY
HTTP availability  → HTTP 200
5xx errors         → 0%
alerts             → none
recent restarts    → 0
```

---

### Failure Injection

The HavenBridge API Deployment was intentionally scaled from:

```text
2 replicas
```

to:

```text
1 replica
```

On `eph-cp01`:

```bash
kubectl -n havenbridge scale deployment havenbridge-api --replicas=1
```

The Deployment then settled at:

```text
READY       1/1
UP-TO-DATE  1
AVAILABLE   1
```

The application continued responding externally because one healthy API
replica remained available.

---

### During — Grafana Detects Degradation

The Operations Overview dashboard changed the API state from:

```text
HEALTHY
```

to:

```text
DEGRADED
```

![HavenBridge API degraded overview](screenshots/incident-01-degraded-api/03-during-degraded-overview.png)

At the same time:

```text
5xx Error Percentage
    → 0%

P95 Request Latency
    → remained healthy

Application Request Rate
    → application remained capable of serving traffic
```

This demonstrated:

```text
loss of redundancy
        ≠
complete application outage
```

---

### During — Alerts and Application Logs

The lower dashboard panels showed:

```text
Firing HavenBridge Alerts
    → NO ACTIVE ALERTS

HavenBridge Recent Pod Restarts
    → 0
```

![HavenBridge degraded alerts and logs](screenshots/incident-01-degraded-api/04-during-degraded-alerts-logs.png)

The application logs recorded the graceful shutdown of the removed replica.

No full availability alert fired because one healthy replica remained
available.

This was the expected behavior:

```text
1 healthy replica
        ↓
service remains available
        ↓
DEGRADED

not

UNAVAILABLE
```

---

### During — Single Replica Traffic

The `HavenBridge Request Rate by Replica` panel showed only one active API Pod.

![Single HavenBridge API replica serving traffic](screenshots/incident-01-degraded-api/05-during-single-replica-traffic.png)

The operational state was therefore:

```text
Before
    ↓
Replica 1 + Replica 2

During degradation
    ↓
Replica 1 only
```

The remaining replica continued serving HavenBridge traffic.

This confirmed that Kubernetes service routing continued operating correctly
while application redundancy was reduced.

---

### Operational Interpretation

The incident demonstrated three distinct application states:

```text
2 replicas
    ↓
HEALTHY

1 replica
    ↓
DEGRADED

0 replicas
    ↓
UNAVAILABLE
```

A degraded application still has serving capacity, but redundancy has been
lost.

This is operationally significant because an additional failure while only one
replica remains could result in complete HavenBridge API unavailability.

---

### Recovery

The HavenBridge API Deployment was restored to two replicas.

On `eph-cp01`:

```bash
kubectl -n havenbridge scale deployment havenbridge-api --replicas=2
```

The rollout was validated with:

```bash
kubectl -n havenbridge rollout status \
  deployment/havenbridge-api \
  --timeout=180s
```

The recovered Deployment returned to:

```text
READY       2/2
UP-TO-DATE  2
AVAILABLE   2
```

External application validation from `syrus` returned:

```text
HTTP 200
```

---

### After — Healthy State Restored

Grafana returned the application state to:

```text
HEALTHY
```

Normal application traffic was visible again.

![HavenBridge recovered operational overview](screenshots/incident-01-degraded-api/06-after-recovery-overview.png)

The recovered dashboard showed:

```text
API replica health
    → HEALTHY

5xx Error Percentage
    → 0%

P95 latency
    → healthy

application traffic
    → present
```

The lower dashboard panels confirmed both replica activity and a clean
operational state.

![HavenBridge recovery alerts and replica traffic](screenshots/incident-01-degraded-api/07-after-recovery-alerts-replica-traffic.png)

Observed recovery state:

```text
Request Rate by Replica
    → two replicas visible

Firing HavenBridge Alerts
    → NO ACTIVE ALERTS

Application Logs
    → successful HTTP 200 requests

HavenBridge Error Logs
    → no active application errors

HavenBridge Recent Pod Restarts
    → 0
```

---

### Incident Result

```text
Healthy baseline confirmed                    PASS
API scaled from 2 replicas to 1               PASS
Grafana changed HEALTHY → DEGRADED            PASS
Application remained externally available     PASS
HTTP 5xx percentage remained 0%               PASS
No false API-unavailable alert fired          PASS
Single remaining replica remained observable  PASS
Graceful shutdown logs captured               PASS
No recent container restart introduced        PASS
API restored from 1 replica to 2              PASS
Grafana returned DEGRADED → HEALTHY           PASS
External HTTP 200 recovery confirmed          PASS
No active alert after recovery                PASS
```

### Final Outcome

Incident 1 demonstrated that HavenBridge can distinguish a reduction in
application redundancy from a complete service outage.

The remaining API replica continued serving requests while Grafana correctly
reported a degraded state.

After the Deployment was restored to two replicas, HavenBridge returned to the
healthy operational state without HTTP 5xx errors, active alerts or container
restarts.

---


## Incident 2 — Complete HavenBridge API Unavailability

### Scenario

This incident simulated complete HavenBridge API unavailability by scaling the
API Deployment from two replicas to zero.

The purpose was to validate the complete outage path:

```text
2 healthy API replicas
        ↓
scale Deployment to 0
        ↓
no API Pods
        ↓
EndpointSlice has no backend endpoints
        ↓
external request returns HTTP 503
        ↓
Grafana reports DOWN
        ↓
HavenBridgeAPIUnavailable
        ↓
Alertmanager
        ↓
Slack + Discord
        ↓
restore 2 replicas
        ↓
HEALTHY
```

---

### Before — Healthy Baseline

Before failure injection:

```text
Deployment
    READY       2/2
    UP-TO-DATE  2
    AVAILABLE   2

API Pods
    eph-worker01 → Running
    eph-worker02 → Running

External application request
    HTTP 200
```

Grafana showed the normal healthy state.

![Healthy HavenBridge state before outage](screenshots/incident-02-api-unavailable/01-before-healthy-overview.png)

The supporting panels showed no active alerts and no recent container restarts.

![Healthy HavenBridge alerts before outage](screenshots/incident-02-api-unavailable/02-before-healthy-alerts-logs.png)

---

### Failure Injection

On `eph-cp01`:

```bash
kubectl -n havenbridge scale deployment havenbridge-api --replicas=0
```

After Kubernetes completed the scale-down:

```text
READY       0/0
UP-TO-DATE  0
AVAILABLE   0
```

The HavenBridge API EndpointSlice existed, but contained no backend endpoints.

Observed:

```text
NAME                    PORTS     ENDPOINTS
havenbridge-api-b97n6   <unset>   <unset>
```

This meant the Kubernetes Service still existed, but there were no application
Pods available to receive requests.

---

### External Availability Failure

From `syrus`:

```bash
curl -sS -o /dev/null \
  -w 'HTTP %{http_code}\n' \
  https://havenbridge.lab/
```

Observed:

```text
HTTP 503
```

The routing path was:

```text
Client
  ↓
Traefik
  ↓
HTTPRoute
  ↓
havenbridge-api Service
  ↓
EndpointSlice
  ↓
NO API endpoints
  ↓
HTTP 503 Service Unavailable
```

The HTTP 503 was returned by the routing layer because Traefik had no healthy
HavenBridge API backend endpoint to forward the request to.

The request did not reach FastAPI.

---

### During — Complete API Outage

Grafana changed the application state to:

```text
DOWN
```

![HavenBridge API completely unavailable](screenshots/incident-02-api-unavailable/03-during-api-down-overview.png)

The dashboard also showed:

```text
Application Request Rate
    → 0

5xx Error Percentage
    → No data

P95 Request Latency
    → No data

Request Rate by Replica
    → no active replicas
```

`No data` for the application-level metrics was expected.

The HavenBridge request counter and latency histogram are emitted by the
FastAPI processes themselves.

With zero API Pods:

```text
no FastAPI process
        ↓
no application metric target
        ↓
no request counter samples
        ↓
no latency histogram samples
        ↓
No data
```

---

### Why the HTTP 503 Did Not Appear as an API 5xx Metric

Although the external request returned HTTP 503, the request never reached the
HavenBridge API.

Therefore:

```text
Traefik returned HTTP 503
```

but there was no running application process available to increment:

```text
havenbridge_http_requests_total
```

This is different from the controlled `/test/500` scenario.

```text
/test/500
    ↓
request reaches FastAPI
    ↓
FastAPI returns HTTP 500
    ↓
application records the 500 metric
```

During this outage:

```text
request never reaches FastAPI
    ↓
routing layer returns HTTP 503
    ↓
application cannot record the request
```

This explains why the 5xx percentage displayed `No data` rather than an HTTP
503 error percentage.

---

### Alert Transition

Initially the dashboard showed no firing alert while the Prometheus rule's
configured duration had not yet elapsed.

![API down before alert duration completed](screenshots/incident-02-api-unavailable/04-during-api-down-before-alert.png)

The availability rule evaluates:

```text
Check the HavenBridge API targets.

If:
  every API target is down

OR:
  Prometheus cannot find the API targets at all

and the problem lasts at least 2 minutes,

fire:

HavenBridgeAPIUnavailable

with severity:

critical
```

After the outage remained active for the required duration, the dashboard
showed:

```text
Firing HavenBridge Alerts
    → 1
```

![HavenBridge API unavailable alert firing](screenshots/incident-02-api-unavailable/05-during-api-down-alert-firing.png)

The alert was:

```text
HavenBridgeAPIUnavailable
Severity: critical
```

---

### Alertmanager Notification Delivery

Alertmanager successfully delivered the critical firing notification to
Discord.

![Discord HavenBridge API unavailable alert](screenshots/incident-02-api-unavailable/06-during-discord-critical-alert.png)

Slack also received the firing notification.

![Slack HavenBridge API unavailable alert](screenshots/incident-02-api-unavailable/07-during-slack-critical-alert.png)

This validated:

```text
Prometheus
    ↓
HavenBridgeAPIUnavailable
    ↓
Alertmanager
    ├── Discord
    └── Slack
```

---

### Recovery

The HavenBridge API Deployment was restored to two replicas.

On `eph-cp01`:

```bash
kubectl -n havenbridge scale deployment havenbridge-api --replicas=2
```

Recovery was validated with:

```bash
kubectl -n havenbridge rollout status \
  deployment/havenbridge-api \
  --timeout=180s
```

The Deployment returned to:

```text
READY       2/2
UP-TO-DATE  2
AVAILABLE   2
```

The EndpointSlice was repopulated with backend Pod addresses.

External validation from `syrus` returned:

```text
HTTP 200
```

---

### After — API Healthy Before New Traffic

Immediately after the replicas returned, Grafana already detected:

```text
API Replicas Up
    → HEALTHY
```

but several application metrics temporarily displayed:

```text
No data
```

![HavenBridge recovered before new application traffic](screenshots/incident-02-api-unavailable/08-after-recovery-before-traffic-overview.png)

This occurred because the newly started FastAPI processes had not yet handled
enough application traffic for the rate and histogram queries to produce
useful values.

The alert state had also returned to:

```text
NO ACTIVE ALERTS
```

and application startup logs were visible.

![HavenBridge recovery startup logs and alert state](screenshots/incident-02-api-unavailable/09-after-recovery-before-traffic-alerts-logs.png)

---

### Recovery Traffic Validation

Normal application traffic was generated from `syrus`:

```bash
for i in {1..30}; do
  curl -s https://havenbridge.lab/ > /dev/null
done
```

After Prometheus scraped the newly generated metrics:

```text
5xx Error Percentage
    → 0%

P95 Request Latency
    → populated and healthy

HTTP Responses
    → HTTP 200 visible

Request Rate by Replica
    → application traffic visible again
```

![Recovered HavenBridge application metrics](screenshots/incident-02-api-unavailable/10-after-recovery-after-traffic-metrics.png)

The full Operations Overview returned to a healthy operating state.

![HavenBridge healthy after recovery traffic](screenshots/incident-02-api-unavailable/11-after-recovery-after-traffic-overview.png)

Both replicas were visible again and no alert remained active.

![Recovered replica traffic and alert state](screenshots/incident-02-api-unavailable/12-after-recovery-after-traffic-alerts-logs.png)

---

### Firing Alert Panel Behavior

The `Firing HavenBridge Alerts` panel uses an Instant Prometheus query.

It answers:

```text
How many HavenBridge alerts are firing right now?
```

It does not show historical alert state.

During the outage the panel correctly displayed:

```text
1
```

After recovery it returned to:

```text
NO ACTIVE ALERTS
```

The earlier firing state is preserved through the incident screenshots,
Prometheus/Alertmanager evidence and Slack/Discord notification history rather
than by the current-state Stat panel.

---

### Resolved Notifications

Slack received the resolved critical notification after the API recovered.

![Slack HavenBridge API unavailable resolved](screenshots/incident-02-api-unavailable/13-after-recovery-slack-resolved.png)

Discord also received the resolved notification.

![Discord HavenBridge API unavailable resolved](screenshots/incident-02-api-unavailable/14-after-recovery-discord-resolved.png)

The complete alert lifecycle was therefore:

```text
API healthy
    ↓
0 replicas
    ↓
alert pending
    ↓
alert firing
    ↓
Slack + Discord firing
    ↓
2 replicas restored
    ↓
Prometheus detects recovery
    ↓
alert healthy
    ↓
Slack + Discord resolved
```

---

### Incident Result

```text
Healthy 2/2 baseline confirmed                    PASS
Deployment scaled from 2 → 0                      PASS
API Pods removed                                  PASS
EndpointSlice lost backend endpoints              PASS
External HTTP 503 confirmed                       PASS
Grafana changed HEALTHY → DOWN                    PASS
No-data application metric behavior explained     PASS
HavenBridgeAPIUnavailable entered firing state    PASS
Critical alert visible in Grafana                 PASS
Discord firing notification received              PASS
Slack firing notification received                PASS
Deployment restored from 0 → 2                    PASS
EndpointSlice repopulated                         PASS
External HTTP 200 recovery confirmed              PASS
Grafana returned DOWN → HEALTHY                   PASS
Normal application metrics returned               PASS
No active alert remained after recovery           PASS
Slack resolved notification received              PASS
Discord resolved notification received            PASS
```

### Final Outcome

Incident 2 demonstrated complete HavenBridge API outage detection and recovery.

The observability platform successfully distinguished between:

```text
application-generated server errors
```

and:

```text
complete disappearance of the application backend
```

Kubernetes, Traefik, Prometheus, Grafana, Alertmanager, Slack and Discord
provided complementary evidence across the full incident lifecycle.

---

## Incident 3 — PostgreSQL Connectivity Failure

### Objective

This incident simulated a PostgreSQL connectivity failure without stopping the
PostgreSQL Pod, deleting storage, modifying database data, or weakening the
existing NetworkPolicies.

The goal was to observe how HavenBridge behaves when:

```text
PostgreSQL Pod
    = healthy

but

HavenBridge API
    cannot establish a new connection to PostgreSQL
```

This scenario was intentionally different from simply deleting the PostgreSQL
Pod.

The test was designed to isolate the application-to-database connectivity path
and later became the basis for an Observability Phase 9 improvement that added
direct PostgreSQL Service EndpointSlice monitoring, alerting, Grafana
visualization, and preserved validation evidence.

---

### Normal Architecture

The application normally connects through the PostgreSQL Kubernetes Service:

```text
HavenBridge API Pod
        ↓
havenbridge-postgres Service
        ↓
EndpointSlice
        ↓
PostgreSQL Pod
        ↓
Persistent Storage
```

The PostgreSQL Service normally selects the database Pod using:

```text
app.kubernetes.io/instance=havenbridge-postgres
app.kubernetes.io/name=postgresql
```

The PostgreSQL Pod itself remained healthy throughout this incident.

---

### Failure Injection Strategy

A temporary unmatched selector was added to the PostgreSQL Service:

```text
incident=postgres-disconnected
```

Because the PostgreSQL Pod did not contain this label, Kubernetes could no
longer associate the Service with the PostgreSQL Pod.

This produced:

```text
PostgreSQL Pod
    → still Running

PVC
    → untouched

database data
    → untouched

NetworkPolicies
    → unchanged

PostgreSQL Service
    → still exists

EndpointSlice
    → no usable PostgreSQL endpoint
```

This was safer than deleting the PostgreSQL Pod or modifying the database
NetworkPolicies because it disturbed only the Service-to-Pod routing
relationship.

---

### Inject the Failure

Run on `eph-cp01`:

```bash
kubectl -n havenbridge patch service havenbridge-postgres \
  --type=merge \
  -p '{"spec":{"selector":{"incident":"postgres-disconnected"}}}'
```

The equivalent Kubernetes Service shorthand is:

```bash
kubectl -n havenbridge patch svc havenbridge-postgres \
  --type=merge \
  -p '{"spec":{"selector":{"incident":"postgres-disconnected"}}}'
```

The merge operation retained the normal PostgreSQL selectors and added:

```text
incident=postgres-disconnected
```

Since the PostgreSQL Pod did not have this label, the Service stopped resolving
to the database Pod.

---

### Understanding `kubectl patch` in This Incident

This incident used `kubectl patch` rather than replacing the entire PostgreSQL
Service manifest.

`kubectl patch` modifies selected fields on an existing Kubernetes object while
leaving unrelated fields intact.

The general form is:

```bash
kubectl patch <resource> <name> \
  --type=<patch-type> \
  -p '<patch-payload>'
```

The important options are:

| Option | Meaning |
|---|---|
| `patch` | Modify fields on an existing Kubernetes resource |
| `--type` | Select how Kubernetes interprets the patch payload |
| `-p` | Provide the patch payload directly on the command line |
| `--patch` | Long form of `-p` |
| `--patch-file` | Read the patch payload from a file instead |

`-p` means **patch payload**. It does not mean PostgreSQL, Pod, or path.

For example:

```bash
-p '{"spec":{"selector":{"incident":"postgres-disconnected"}}}'
```

is the JSON payload describing the field Kubernetes should modify.

#### Patch Types

The three patch styles most relevant to this project are:

```text
strategic
merge
json
```

They are not interchangeable.

#### Strategic Merge Patch

Example:

```bash
kubectl patch deployment example \
  --type=strategic \
  -p '{"spec":{"replicas":3}}'
```

Strategic Merge Patch understands Kubernetes object structure and can apply
Kubernetes-aware merge behavior to supported built-in resource types.

It is useful when structured fields, especially lists, need Kubernetes-aware
merging.

Strategic Merge Patch is not supported uniformly by every resource type,
particularly CustomResourceDefinitions.

#### JSON Merge Patch

Incident 3 used:

```text
--type=merge
```

with:

```bash
kubectl -n havenbridge patch service havenbridge-postgres \
  --type=merge \
  -p '{"spec":{"selector":{"incident":"postgres-disconnected"}}}'
```

JSON Merge Patch merges the supplied object into the existing Kubernetes
resource.

The patch did not replace the entire Service selector.

Kubernetes retained:

```text
app.kubernetes.io/instance=havenbridge-postgres
app.kubernetes.io/name=postgresql
```

and added:

```text
incident=postgres-disconnected
```

This made `--type=merge` appropriate for the failure injection because the goal
was to add one temporary selector while preserving the rest of the Service.

#### JSON Patch

JSON Patch uses an ordered list of explicit operations.

The Incident 3 recovery used:

```bash
kubectl -n havenbridge patch service havenbridge-postgres \
  --type=json \
  -p='[{"op":"remove","path":"/spec/selector/incident"}]'
```

The JSON Patch payload was:

```json
[
  {
    "op": "remove",
    "path": "/spec/selector/incident"
  }
]
```

The field:

```text
op
```

specifies the operation to perform.

The field:

```text
path
```

specifies the exact location inside the Kubernetes object.

Therefore:

```text
op   = remove
path = /spec/selector/incident
```

means:

```text
remove only spec.selector.incident
```

The original PostgreSQL selectors remain untouched.

This is why JSON Patch was appropriate for recovery: it precisely removed the
temporary incident selector without rebuilding or replacing the rest of the
Service object.

#### JSON Patch Fields

A JSON Patch operation can contain:

| Field | Purpose |
|---|---|
| `op` | Operation to perform |
| `path` | Target JSON path inside the Kubernetes object |
| `value` | New value used by operations such as `add`, `replace`, and `test` |
| `from` | Source path used by `move` and `copy` |

#### JSON Patch Operations

Common JSON Patch operations include:

| Operation | Purpose |
|---|---|
| `add` | Add a new value |
| `remove` | Remove an existing value |
| `replace` | Replace an existing value |
| `move` | Move a value from one JSON path to another |
| `copy` | Copy a value from one JSON path to another |
| `test` | Verify that a value matches an expected value before continuing |

Example `add`:

```json
[
  {
    "op": "add",
    "path": "/metadata/labels/test",
    "value": "true"
  }
]
```

Example `replace`:

```json
[
  {
    "op": "replace",
    "path": "/spec/replicas",
    "value": 3
  }
]
```

Example `remove`:

```json
[
  {
    "op": "remove",
    "path": "/metadata/labels/test"
  }
]
```

`move` and `copy` use a `from` field. For example:

```json
[
  {
    "op": "copy",
    "from": "/metadata/labels/app",
    "path": "/metadata/labels/copied-app"
  }
]
```

For Incident 3, only the precise `remove` operation was required during
recovery.

#### Patch-Type Comparison

```text
--type=strategic
    Kubernetes-aware merging for supported built-in resources

--type=merge
    simple JSON field merge

--type=json
    precise ordered operations against exact JSON paths
```

For this incident:

```text
Failure injection
    → --type=merge
    → add one temporary selector

Recovery
    → --type=json
    → remove exactly that selector
```

#### Previewing a Patch Safely

A patch can be previewed before changing the live resource.

Client-side preview:

```bash
kubectl -n havenbridge patch service havenbridge-postgres \
  --type=merge \
  -p '{"spec":{"selector":{"incident":"postgres-disconnected"}}}' \
  --dry-run=client \
  -o yaml
```

Server-side preview:

```bash
kubectl -n havenbridge patch service havenbridge-postgres \
  --type=merge \
  -p '{"spec":{"selector":{"incident":"postgres-disconnected"}}}' \
  --dry-run=server \
  -o yaml
```

Server-side dry run is especially useful because the Kubernetes API server
validates the proposed object without persisting the change.

Using a targeted patch was appropriate for this incident because it disturbed
the smallest practical part of the PostgreSQL connectivity path while leaving
the Pod, PVC, database data, credentials, and NetworkPolicies unchanged.

---

### Validate the Broken PostgreSQL Endpoint

Run on `eph-cp01`:

```bash
kubectl -n havenbridge get endpointslice \
  -l kubernetes.io/service-name=havenbridge-postgres \
  -o wide
```

During the failure the PostgreSQL EndpointSlice showed:

```text
PORTS       <unset>
ENDPOINTS   <unset>
```

At the same time, the PostgreSQL Pod remained:

```text
1/1 Running
```

This demonstrated an important Kubernetes concept:

```text
healthy Pod
    does not automatically mean
healthy Service connectivity
```

---

### Validate a New API-to-PostgreSQL Connection

A direct TCP connection test was executed from the HavenBridge API Deployment.

Run on `eph-cp01`:

```bash
kubectl -n havenbridge exec deploy/havenbridge-api -- \
  python -c 'import socket; socket.create_connection(("havenbridge-postgres",5432),timeout=5); print("CONNECTED")'
```

The result was:

```text
TimeoutError: timed out
```

This proved that a **new connection** from the HavenBridge API to PostgreSQL
could not be established.

---

### Unexpected Observation — Existing API Requests Still Worked

The HavenBridge readiness endpoint was checked from `syrus`:

```bash
curl -i https://havenbridge.lab/health/ready
```

It still returned:

```text
HTTP 200
{"status":"ready"}
```

The application endpoint was also tested:

```bash
curl --max-time 15 -i \
  https://havenbridge.lab/api/v1/inquiries
```

Surprisingly, this also initially returned:

```text
HTTP 200
```

and existing service-inquiry records.

This behavior was caused by an important application behavior discovered during
the test.

---

### Existing Database Connection Pool

The already-running HavenBridge API Pods had established PostgreSQL connections
before the Service endpoint was removed.

Removing the Service endpoint prevented **new connections**, but it did not
necessarily terminate database TCP connections that were already established.

The observed behavior was therefore:

```text
API Pod already running
        ↓
existing PostgreSQL connection already established
        ↓
Service endpoint removed
        ↓
existing database connection can continue temporarily
        ↓
application request may still succeed
```

This explained why `/api/v1/inquiries` initially continued to work.

---

### Readiness Endpoint and SQLAlchemy Connection-Pool Behaviour

Incident 3 originally appeared to show that the HavenBridge readiness endpoint
did not validate PostgreSQL.

That initial interpretation was incomplete.

The current HavenBridge `/health/ready` endpoint does validate PostgreSQL.

The readiness route calls the database readiness function, obtains a SQLAlchemy
connection, and executes:

```sql
SELECT 1
```

If that operation fails, the endpoint returns HTTP 503.

If it succeeds, the endpoint returns:

```text
HTTP 200
{"status":"ready"}
```

The important behavior exposed by Incident 3 was therefore not the absence of a
database check. It was the interaction between Kubernetes Service routing and
SQLAlchemy connection pooling.

The already-running API Pods had PostgreSQL connections established before the
Service EndpointSlice was broken.

The sequence was:

```text
HavenBridge API Pod starts
        ↓
PostgreSQL connection established
        ↓
connection retained by SQLAlchemy pool
        ↓
PostgreSQL Service selector is broken
        ↓
EndpointSlice loses the PostgreSQL backend
        ↓
new connections through the Service fail
        ↓
existing database TCP connection may remain alive
        ↓
SQLAlchemy may reuse that existing connection
        ↓
SELECT 1 succeeds
        ↓
/health/ready may temporarily continue returning HTTP 200
```

The SQLAlchemy engine also uses connection-pool health checking. A pool health
check can verify whether a checked-out pooled connection is usable, but it does
not require a brand-new TCP connection through the Kubernetes Service for every
readiness request.

This explains why both observations could be true at the same time:

```text
/health/ready
    = HTTP 200
```

while:

```text
new TCP connection to havenbridge-postgres:5432
    = timeout
```

The readiness endpoint answers:

```text
Can this API instance currently obtain a usable SQLAlchemy connection
and execute a PostgreSQL query?
```

The EndpointSlice signal answers:

```text
Does the Kubernetes PostgreSQL Service currently have at least one
Ready backend available for new Service-routed traffic?
```

These are complementary operational signals.

The incident therefore exposed an **observability gap**, not a missing
PostgreSQL readiness check.

---

### Why Readiness Was Not Changed to Force a New TCP Connection

One possible response would have been to force `/health/ready` to establish a
brand-new PostgreSQL TCP connection every time Kubernetes executes its
readiness probe.

That was not selected.

The readiness probe executes frequently. Forcing a completely new database
connection for every readiness request would create unnecessary database
connection churn and would work against the purpose of SQLAlchemy connection
pooling.

The existing readiness endpoint still provides useful application-level
evidence:

```text
Can this API Pod currently obtain a usable SQLAlchemy connection and
execute a PostgreSQL query?
```

The missing signal was different:

```text
Does the PostgreSQL Kubernetes Service currently have a Ready backend
available for new Service-routed connections?
```

That question belongs naturally to Kubernetes and infrastructure monitoring.

The solution was therefore to preserve application connection-pool behavior and
add an independent PostgreSQL Service EndpointSlice signal.

---

### Force a Fresh Application Connection

To prove the effect on a new application process, only one HavenBridge API Pod
was deleted.

The other replica was deliberately left running so the entire application would
not be taken offline.

The Pod deleted during this incident was:

```text
havenbridge-api-d557d8b75-dvh29
```

Run on `eph-cp01`:

```bash
kubectl -n havenbridge delete pod \
  havenbridge-api-d557d8b75-dvh29
```

Kubernetes immediately created a replacement API Pod.

The replacement Pod was:

```text
havenbridge-api-d557d8b75-tfgbv
```

The API Pods were monitored with:

```bash
kubectl -n havenbridge get pods \
  -l app.kubernetes.io/name=havenbridge-api \
  -w
```

The original API replica remained:

```text
1/1 Running
```

while the replacement repeatedly entered:

```text
Running
    ↓
Error
    ↓
CrashLoopBackOff
```

The replacement container eventually accumulated more than 100 restart
attempts before PostgreSQL connectivity was restored.

---

### Application Failure

The replacement API Pod needed to establish a fresh PostgreSQL connection
during application startup.

Because the PostgreSQL Service had no endpoint, the connection timed out.

Grafana application logs showed errors including:

```text
sqlalchemy.exc.OperationalError
psycopg.errors.ConnectionTimeout
connection timeout expired
Application startup failed. Exiting.
```

The failure sequence was:

```text
new API Pod starts
        ↓
FastAPI startup begins
        ↓
SQLAlchemy requests PostgreSQL connection
        ↓
PostgreSQL Service has no endpoint
        ↓
connection timeout
        ↓
application startup fails
        ↓
container exits
        ↓
Kubernetes restarts container
        ↓
CrashLoopBackOff
```

![HavenBridge API degraded during PostgreSQL connectivity failure](screenshots/incident-03-postgresql-connectivity/03-during-api-degraded-overview.png)

---

### Database Connection Failure in Centralized Logs

Grafana and Loki exposed the SQLAlchemy and psycopg connection failure.

This provided application-level evidence that the Kubernetes symptoms were
caused by database connectivity rather than a generic container failure.

![PostgreSQL connection timeout errors](screenshots/incident-03-postgresql-connectivity/04-during-db-connection-errors.png)

---

### CrashLoop and Restart Evidence

The replacement API Pod repeatedly failed startup and was restarted by
Kubernetes.

Example observed state:

```text
havenbridge-api-d557d8b75-92nkr   1/1 Running
havenbridge-api-d557d8b75-tfgbv   0/1 CrashLoopBackOff
```

The surviving API replica allowed HavenBridge to remain partially available.

The overall API state therefore became:

```text
2 replicas expected
        ↓
1 healthy replica
        ↓
1 failing replica
        ↓
DEGRADED
```

![HavenBridge API restart activity during the database incident](screenshots/incident-03-postgresql-connectivity/05-during-crashloop-restarts.png)

---

### Important Observability Gap

During the incident, the Grafana panel:

```text
HavenBridge PostgreSQL Pod Ready
```

continued to report:

```text
HEALTHY
```

The PostgreSQL Pod itself really was healthy.

However:

```text
API → PostgreSQL Service connectivity
```

was broken.

This exposed an important difference between:

```text
database Pod health
```

and:

```text
application-to-database Service connectivity
```

The PostgreSQL Pod readiness metric alone could not detect this failure.

![PostgreSQL remained healthy while application connectivity was broken](screenshots/incident-03-postgresql-connectivity/06-during-postgresql-observability-gap.png)

---

### Why No Critical API Alert Fired During the Original Incident

The existing `HavenBridgeAPIUnavailable` alert is designed to fire when all
HavenBridge API targets are unavailable.

During the original Incident 3 simulation:

```text
one API replica
    → healthy

one API replica
    → CrashLoopBackOff
```

Therefore HavenBridge was degraded, but not completely unavailable.

The alert panel correctly showed:

```text
NO ACTIVE ALERTS
```

That was expected behavior for the API-unavailable alert.

The original incident therefore identified a separate failure mode that needed
its own signal and its own alert.

That follow-up work became Observability Phase 9.

---

## Observability Phase 9 Follow-Up — PostgreSQL Service Reachability Monitoring

### Why the Follow-Up Was Required

Incident 3 established the condition:

```text
PostgreSQL Pod
    = Running and Ready

but

havenbridge-postgres Service
    = no Ready EndpointSlice backend
```

The direct TCP test proved that a new connection could not be established even
while PostgreSQL Pod readiness remained healthy.

The follow-up therefore focused on the question:

```text
Does the havenbridge-postgres Service currently have at least one
Ready EndpointSlice backend?
```

This signal is independent of PostgreSQL Pod readiness and directly represents
the Kubernetes Service routing path needed for new application connections.

---

### kube-state-metrics EndpointSlice Signal

The cluster's kube-state-metrics instance exposes EndpointSlice information
through metrics including:

```text
kube_endpointslice_created
kube_endpointslice_endpoints
kube_endpointslice_info
kube_endpointslice_ports
```

The metric used for this follow-up is:

```text
kube_endpointslice_endpoints
```

The application PostgreSQL Service EndpointSlice is selected with:

```text
endpointslice=~"havenbridge-postgres-[^-]+$"
```

This expression intentionally matches the application PostgreSQL Service
EndpointSlice while excluding the separate PostgreSQL headless Service
EndpointSlice.

The healthy endpoint-count query is:

```promql
sum(
  kube_endpointslice_endpoints{
    namespace="havenbridge",
    endpointslice=~"havenbridge-postgres-[^-]+$",
    ready="true"
  }
) or vector(0)
```

Healthy baseline result:

```text
1
```

During the controlled Service-selector failure:

```text
0
```

The PostgreSQL Pod readiness query is:

```promql
max(
  kube_pod_status_ready{
    namespace="havenbridge",
    pod=~"havenbridge-postgres-.*",
    condition="true"
  }
) or vector(0)
```

Healthy baseline result:

```text
1
```

This allowed the platform to distinguish:

```text
PostgreSQL Pod Ready = 1
```

from:

```text
PostgreSQL Service Ready Endpoints = 0
```

---

### PostgreSQL Service Connectivity Alert

A dedicated Prometheus alert was added:

```text
HavenBridgePostgreSQLConnectivityFailure
```

The alert expression is:

```promql
(
  max(
    kube_pod_status_ready{
      namespace="havenbridge",
      pod=~"havenbridge-postgres-.*",
      condition="true"
    }
  ) == 1
)
and
(
  (
    sum(
      kube_endpointslice_endpoints{
        namespace="havenbridge",
        endpointslice=~"havenbridge-postgres-[^-]+$",
        ready="true"
      }
    )
    or vector(0)
  ) == 0
)
```

The alert means:

```text
PostgreSQL Pod is Ready
        AND
PostgreSQL application Service has zero Ready EndpointSlice backends
```

Configuration:

```text
Alert:
HavenBridgePostgreSQLConnectivityFailure

Severity:
critical

Duration:
2 minutes

Summary:
HavenBridge PostgreSQL Service connectivity has failed
```

The description states that the PostgreSQL Pod is Ready while the application
PostgreSQL Service has had no Ready EndpointSlice backend for at least two
minutes.

The two-minute duration reduces the chance of alerting on a very short
transient EndpointSlice update.

---

### Alert Lifecycle Validation

The new alert was validated through its complete Prometheus state lifecycle.

Healthy baseline:

```text
state = inactive
health = ok
alerts = []
```

After the PostgreSQL Service selector was broken:

```text
state = pending
```

After the condition remained present for two minutes:

```text
state = firing
severity = critical
health = ok
```

Alertmanager then delivered the firing notification to Discord:

```text
HavenBridgePostgreSQLConnectivityFailure - firing
```

This validated the alert path:

```text
Kubernetes EndpointSlice
        ↓
kube-state-metrics
        ↓
Prometheus
        ↓
HavenBridgePostgreSQLConnectivityFailure
        ↓
Alertmanager
        ↓
Discord
```

A Discord firing notification was explicitly validated.

A resolved Discord notification was not required as proof for this phase and
should not be assumed unless separately captured.

---

### Grafana PostgreSQL Service Endpoint Panel

The Git-managed:

```text
HavenBridge — Operations Overview
```

dashboard was extended with:

```text
HavenBridge PostgreSQL Service Endpoint
```

Visualization:

```text
Stat
```

Panel description:

```text
Shows whether the HavenBridge application PostgreSQL Service currently
has at least one Ready EndpointSlice backend available for application
traffic.
```

The panel query is:

```promql
(
  sum(
    kube_endpointslice_endpoints{
      namespace="havenbridge",
      endpointslice=~"havenbridge-postgres-[^-]+$",
      ready="true"
    }
  )
  or vector(0)
) > bool 0
```

The `> bool 0` comparison converts the endpoint count into an operational
boolean:

```text
1
    → HEALTHY

0
    → NO ENDPOINT
```

Panel settings:

```text
Visualization:
    Stat

Query mode:
    Instant

Range:
    false

Legend:
    PostgreSQL Service Endpoint

Calculation:
    Last (not null)

Minimum:
    0

Maximum:
    1

Graph mode:
    none

Text mode:
    value

Threshold mode:
    absolute
```

Value mappings:

```text
1
    → HEALTHY
    → dark green

0
    → NO ENDPOINT
    → dark red
```

The panel was assigned:

```text
panel key:
    panel-13

panel id:
    13
```

Layout:

```text
x      = 0
y      = 48
width  = 12
height = 8
```

---

### Git-Managed Grafana Provisioning

The HavenBridge Operations Overview dashboard is not manually saved in Grafana.

Grafana reports the dashboard as file provisioned, so Git remains the source of
truth.

The dashboard source is:

```text
kubernetes/platform/observability/grafana/dashboards/
havenbridge-operations-overview.json
```

The Kustomize configuration is:

```text
kubernetes/platform/observability/grafana/dashboards/
kustomization.yaml
```

It uses `configMapGenerator` to package the Grafana dashboard JSON into:

```text
havenbridge-operations-grafana-dashboard
```

in namespace:

```text
observability
```

The provisioning path is:

```text
Git-managed dashboard JSON
        ↓
Kustomize configMapGenerator
        ↓
havenbridge-operations-grafana-dashboard ConfigMap
        ↓
Grafana file provisioning
        ↓
HavenBridge — Operations Overview
```

The dashboard was validated locally as JSON with:

```bash
jq empty \
  kubernetes/platform/observability/grafana/dashboards/havenbridge-operations-overview.json
```

The Kustomize render was validated on `eph-cp01`:

```bash
kubectl kustomize /tmp/havenbridge-grafana-dashboards \
  | grep -n -A8 -B3 \
  'HavenBridge PostgreSQL Service Endpoint'
```

A server-side dry run then confirmed that the generated ConfigMaps were valid:

```bash
kubectl apply \
  --dry-run=server \
  -k /tmp/havenbridge-grafana-dashboards
```

Observed result:

```text
configmap/havenbridge-api-grafana-dashboard unchanged (server dry run)
configmap/havenbridge-operations-grafana-dashboard configured (server dry run)
```

The dashboard was then applied through Kustomize:

```bash
kubectl apply \
  -k /tmp/havenbridge-grafana-dashboards
```

#### Why `-k` Was Used Instead of `-f`

The dashboard directory contains a `kustomization.yaml` with
`configMapGenerator`.

The dashboard JSON files themselves are Grafana dashboard definitions. They are
not standalone Kubernetes resource manifests.

Therefore:

```text
kubectl apply -f
```

would mean:

```text
apply this Kubernetes manifest directly
```

while:

```text
kubectl apply -k
```

means:

```text
read kustomization.yaml
        ↓
run Kustomize
        ↓
generate Kubernetes ConfigMaps
        ↓
apply the generated resources
```

Conceptually:

```bash
kubectl apply -k /tmp/havenbridge-grafana-dashboards
```

is equivalent to:

```bash
kubectl kustomize /tmp/havenbridge-grafana-dashboards \
  | kubectl apply -f -
```

This is why `-k` is the correct option for the Git-managed HavenBridge Grafana
dashboard provisioning path.

---

### Live Grafana Validation

After the ConfigMap update was provisioned, the dashboard displayed:

```text
HavenBridge PostgreSQL Pod Ready
    HEALTHY

HavenBridge PostgreSQL Recent Restarts
    NO RECENT RESTARTS

HavenBridge PostgreSQL Service Endpoint
    HEALTHY
```

This confirmed that the new panel was loaded through the Git-managed
provisioning path rather than being stored as an unsupported manual Grafana UI
change.

The new Service Endpoint panel provides the missing operational distinction:

```text
PostgreSQL Pod Ready
    ↓
Is the database Pod healthy?

PostgreSQL Service Endpoint
    ↓
Can the Kubernetes Service currently route to a Ready backend?
```

---

### Recover PostgreSQL Connectivity

The temporary incident selector was removed from the PostgreSQL Service.

Run on `eph-cp01`:

```bash
kubectl -n havenbridge patch service havenbridge-postgres \
  --type=json \
  -p='[{"op":"remove","path":"/spec/selector/incident"}]'
```

This removed only:

```text
incident=postgres-disconnected
```

and preserved the original PostgreSQL Service selectors:

```text
app.kubernetes.io/instance=havenbridge-postgres
app.kubernetes.io/name=postgresql
```

---

### Validate Endpoint Recovery

Run on `eph-cp01`:

```bash
kubectl -n havenbridge get endpointslice \
  -l kubernetes.io/service-name=havenbridge-postgres \
  -o wide
```

During the original Incident 3 recovery, the PostgreSQL endpoint returned:

```text
PORTS       5432
ENDPOINTS   10.244.35.122
```

During the later Phase 9 validation, the current application PostgreSQL
EndpointSlice was observed as:

```text
havenbridge-postgres-2mhcs
Port: 5432
Ready endpoint: 10.244.35.96
```

The difference in Pod IP is expected because Pod addresses can change over time.

The important validation is that the EndpointSlice again contained a Ready
backend.

The restored flow was:

```text
HavenBridge API
        ↓
havenbridge-postgres Service
        ↓
Ready EndpointSlice backend
        ↓
PostgreSQL Pod
```

---

### API Recovery

The replacement API Pod automatically retried after Kubernetes restarted the
container.

Once PostgreSQL connectivity returned, the application successfully completed
startup.

The Pod changed from:

```text
0/1 CrashLoopBackOff
```

to:

```text
1/1 Running
```

The Deployment was validated:

```bash
kubectl -n havenbridge get deployment havenbridge-api
```

Result:

```text
READY   UP-TO-DATE   AVAILABLE
2/2     2            2
```

No manual recreation of the Deployment was required.

Kubernetes recovered the failed replica automatically once its dependency
became available again.

![HavenBridge API recovered after PostgreSQL connectivity restoration](screenshots/incident-03-postgresql-connectivity/07-after-recovery-overview.png)

---

### Successful Application Startup After Recovery

Grafana application logs showed successful startup after database connectivity
was restored.

The logs included:

```text
Started server process
Waiting for application startup
Starting HavenBridge API in production
Application startup complete
Uvicorn running on http://0.0.0.0:8000
```

![Successful application startup after PostgreSQL recovery](screenshots/incident-03-postgresql-connectivity/08-after-recovery-startup-and-restarts.png)

---

### Final Recovery Validation

After recovery:

```text
HavenBridge API Replicas Up
    → HEALTHY

Deployment
    → 2/2

PostgreSQL Pod Ready
    → HEALTHY

PostgreSQL Service Endpoint
    → HEALTHY

Firing HavenBridge Alerts
    → NO ACTIVE ALERTS
```

Prometheus endpoint signal after recovery:

```text
1
```

The combined PostgreSQL connectivity-failure expression returned no matching
series.

The dedicated alert returned to:

```text
state = inactive
alerts = []
health = ok
```

External HavenBridge validation returned:

```text
HTTP 200
```

![HavenBridge healthy after Incident 3 recovery](screenshots/incident-03-postgresql-connectivity/09-after-recovery-healthy-overview.png)

---

### Recent Restart Window Observation

During the original incident the:

```text
HavenBridge Recent Pod Restarts
```

panel continued showing restart activity even after application recovery.

The original query used:

```promql
increase(
  kube_pod_container_status_restarts_total[15m]
)
```

The panel therefore answered:

```text
How many HavenBridge container restarts occurred
during the previous 15 minutes?
```

Recovery does not erase restart history immediately.

For example:

```text
application recovered
        ↓
no more restarts occur
        ↓
old restart events still exist inside [15m]
        ↓
Grafana continues displaying recent restart activity
        ↓
events eventually age out
        ↓
panel returns to 0
```

Prometheus `increase()` may also display fractional values such as:

```text
6.09
```

even when Kubernetes reports an integer restart count.

This occurs because Prometheus extrapolates counter increases around scrape
boundaries.

The Kubernetes restart counter remains the authoritative exact cumulative
container restart count.

---

### Restart Window Improvement

For the HavenBridge Operations Overview dashboard, the restart window was
changed from:

```text
15 minutes
```

to:

```text
5 minutes
```

for both:

```text
HavenBridge Recent Pod Restarts
HavenBridge PostgreSQL Recent Restarts
```

The general HavenBridge restart query now uses:

```promql
sum(
  increase(
    kube_pod_container_status_restarts_total{
      namespace="havenbridge"
    }[5m]
  )
) or vector(0)
```

The PostgreSQL-specific restart query now uses:

```promql
sum(
  increase(
    kube_pod_container_status_restarts_total{
      namespace="havenbridge",
      pod=~"havenbridge-postgres-.*"
    }[5m]
  )
) or vector(0)
```

The five-minute window provides a clearer operational view:

```text
active restart problem
    → visible

application recovers
    ↓
five minutes without additional restarts
    ↓
recent failure evidence ages out
    ↓
panel returns to healthy state
```

The cumulative Kubernetes restart count does not reset.

---

### Final Healthy Dashboard State

After more than five minutes without additional API container restarts:

```text
HavenBridge Recent Pod Restarts
    → 0

HavenBridge PostgreSQL Pod Ready
    → HEALTHY

HavenBridge PostgreSQL Recent Restarts
    → NO RECENT RESTARTS

HavenBridge PostgreSQL Service Endpoint
    → HEALTHY

Firing HavenBridge Alerts
    → NO ACTIVE ALERTS
```

![Final Incident 3 healthy state](screenshots/incident-03-postgresql-connectivity/10-after-recovery-health-and-restarts.png)

---

### Final Observability Model

Incident 3 and its Phase 9 follow-up demonstrated that several health signals
are required to understand the PostgreSQL dependency correctly.

The platform now distinguishes:

```text
PostgreSQL Pod readiness
```

from:

```text
API database-query readiness
```

from:

```text
PostgreSQL Kubernetes Service reachability
```

These answer different questions.

```text
PostgreSQL Pod Ready
    ↓
Is Kubernetes reporting the database Pod as Ready?

/health/ready
    ↓
Can the API currently obtain a usable SQLAlchemy connection
and execute a PostgreSQL query?

PostgreSQL Service Endpoint
    ↓
Does the application PostgreSQL Service currently have at least
one Ready EndpointSlice backend?
```

Together they provide stronger operational evidence than any single signal
alone.

The resulting model is:

```text
PostgreSQL Pod
    ↓
Pod readiness metric
    ↓
Prometheus
         \
          \
HavenBridge API
    ↓      \
/health/ready \
              → Grafana + Alerting
             /
PostgreSQL Service
    ↓       /
EndpointSlice
    ↓     /
kube-state-metrics
    ↓
Prometheus
```

This preserves normal application connection pooling while independently
monitoring the Kubernetes Service path required for new PostgreSQL connections.

---

### Incident 3 Root Cause

The controlled root cause was:

```text
temporary unmatched selector added
to havenbridge-postgres Service
```

which caused:

```text
PostgreSQL Service
        ↓
no matching Pod
        ↓
EndpointSlice becomes empty
        ↓
new PostgreSQL connections fail
        ↓
replacement API Pod cannot start
        ↓
CrashLoopBackOff
        ↓
HavenBridge operates with one API replica
        ↓
DEGRADED
```

---

### Recovery Summary

```text
Remove temporary Service selector
        ↓
PostgreSQL EndpointSlice repopulates
        ↓
new database connections succeed
        ↓
CrashLooping API replica starts
        ↓
Deployment returns to 2/2
        ↓
Prometheus Service Endpoint signal returns to 1
        ↓
HavenBridgePostgreSQLConnectivityFailure returns inactive
        ↓
Grafana returns to HEALTHY
        ↓
restart events age out of five-minute window
        ↓
Recent Pod Restarts returns to 0
```

---

### Operational Lessons

Incident 3 and its Phase 9 follow-up demonstrated several production concepts.

1. A Running and Ready PostgreSQL Pod does not prove that the Kubernetes
   Service can currently route new connections to it.

2. Kubernetes Service health, EndpointSlice state, and Pod health must be
   treated as separate but related observability signals.

3. Existing TCP/database connections can survive after the Kubernetes Service
   routing path is broken.

4. SQLAlchemy connection pooling can therefore allow existing application
   requests and readiness checks to continue temporarily even when fresh
   Service-routed connections fail.

5. Restarting or replacing an application Pod forces a fresh dependency
   connection and may expose an otherwise hidden Service-routing failure.

6. `CrashLoopBackOff` is a symptom. Application logs revealed the actual cause:
   PostgreSQL connection timeout.

7. One surviving API replica prevented a complete HavenBridge outage.

8. The HavenBridge `/health/ready` endpoint does validate PostgreSQL by
   executing a lightweight query. Incident 3 did not prove that the database
   readiness check was missing.

9. Application database readiness and Kubernetes Service reachability answer
   different operational questions and should be monitored together.

10. Forcing a brand-new PostgreSQL TCP connection for every Kubernetes
    readiness probe would create unnecessary connection churn and was not
    required to close this observability gap.

11. `kube_endpointslice_endpoints` provides direct Kubernetes evidence that the
    PostgreSQL application Service has a Ready backend.

12. `HavenBridgePostgreSQLConnectivityFailure` now detects the specific
    condition where PostgreSQL remains Ready but its application Service loses
    all Ready EndpointSlice backends.

13. Alert validation should include the complete lifecycle:

    ```text
    inactive
        ↓
    pending
        ↓
    firing
        ↓
    recovery
        ↓
    inactive
    ```

14. A firing Alertmanager notification to Discord was validated. Resolved
    notification delivery should only be documented when separately captured.

15. Prometheus rolling time windows intentionally preserve recent incident
    evidence after recovery.

16. Kubernetes restart counters are cumulative, while Grafana
    `increase(...[5m])` shows only recent restart activity.

17. Git-provisioned Grafana dashboards should be updated through the dashboard
    JSON and Kubernetes provisioning path rather than saved manually in the
    Grafana UI.

18. `kubectl apply -k` is appropriate for the dashboard directory because
    Kustomize must first generate ConfigMaps from the Grafana JSON files.

19. Targeted `kubectl patch` operations are preferable to destructive changes
    when a controlled incident can be reproduced by modifying only the required
    field.

20. JSON Merge Patch was appropriate for adding the temporary incident selector,
    while JSON Patch was appropriate for precisely removing that selector
    during recovery.

21. Safe incident simulations should disturb the smallest practical component
    and leave persistent storage, application data, credentials, and unrelated
    networking controls untouched.

---

### Validation Evidence

The Phase 9 validation evidence is preserved at:

```text
kubernetes/platform/observability/evidence/
havenbridge-postgresql-service-reachability-validation.txt
```

The evidence records:

```text
healthy baseline
        ↓
EndpointSlice failure injection
        ↓
PostgreSQL Pod remains Ready
        ↓
Service Endpoint signal becomes 0
        ↓
alert pending
        ↓
alert firing
        ↓
Discord firing notification
        ↓
Service selector recovery
        ↓
EndpointSlice returns
        ↓
Service Endpoint signal returns 1
        ↓
alert returns inactive
        ↓
Grafana panel shows HEALTHY
        ↓
external HTTP 200
```

---

### Incident Result

```text
Original Incident 3
-------------------
Incident injection                                  PASS
PostgreSQL Pod preserved                            PASS
Persistent storage safe                             PASS
DB connectivity failure                             PASS
Fresh connection test                               PASS
CrashLoop detected                                  PASS
Degraded API detected                               PASS
Centralized logs detected                           PASS
Service recovery                                    PASS
Endpoint recovery                                   PASS
API returned to 2/2                                 PASS
Grafana returned healthy                            PASS

Observability Phase 9 Follow-Up
-------------------------------
EndpointSlice metric identified                      PASS
Healthy PostgreSQL endpoint baseline = 1             PASS
PostgreSQL Pod Ready baseline = 1                    PASS
Dedicated connectivity alert loaded                  PASS
Alert state inactive → pending                       PASS
Alert state pending → firing                         PASS
Critical severity validated                          PASS
Discord firing notification received                 PASS
Recovery selector removed                            PASS
Original Service selectors restored                  PASS
EndpointSlice Ready backend restored                 PASS
Endpoint signal returned to 1                        PASS
Connectivity expression returned no failure          PASS
Alert returned inactive                              PASS
Alert rule health remained ok                        PASS
HavenBridge API 2/2 Ready                            PASS
External HTTP 200 confirmed                          PASS
Git-managed Grafana panel provisioned                PASS
PostgreSQL Service Endpoint panel = HEALTHY          PASS
```

**Incident 3 — PostgreSQL Connectivity Failure: PASSED**

**Observability Phase 9 — PostgreSQL Service Reachability Monitoring: PASSED**

The PostgreSQL Service-reachability observability gap discovered during
Incident 3 is now closed with:

```text
EndpointSlice monitoring
        +
Prometheus alerting
        +
Alertmanager notification
        +
Discord firing notification
        +
Grafana visualization
        +
Git-managed dashboard provisioning
        +
documented recovery
        +
preserved validation evidence
```
