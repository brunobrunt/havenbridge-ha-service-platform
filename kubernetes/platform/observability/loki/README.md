# HavenBridge Loki

## What Is Loki?

Grafana Loki is the log storage and query backend for the HavenBridge
observability platform.

In simple terms:

```text
Loki receives logs
        ↓
stores them
        ↓
allows them to be searched
        ↓
Grafana displays them
```

A useful analogy is:

```text
Alloy   = delivery truck
Loki    = warehouse
Grafana = control room
```

Loki does not normally collect logs directly from every Kubernetes Pod.

Grafana Alloy will perform the collection and send those logs to Loki.

---

## Why HavenBridge Uses Loki

Prometheus tells us what is happening through metrics.

For example:

```text
HTTP 5xx percentage increased
request latency increased
API replica unavailable
```

Loki helps explain why it happened by storing the application and Kubernetes
logs associated with those events.

The combined observability model is:

```text
Metrics
   ↓
Prometheus
   ↓
Grafana

Logs
   ↓
Grafana Alloy
   ↓
Loki
   ↓
Grafana
```

This allows an operator to move from:

```text
Something is wrong
```

to:

```text
What logs explain the problem?
```

---

## Loki Version

HavenBridge pins the Loki Helm deployment to:

```text
Helm repository: grafana-community
Chart:           loki
Chart version:   18.11.7
Loki version:    3.7.7
```

Pinning the chart version prevents a future Helm repository update from
silently changing the Loki version being deployed.

---

## Deployment Architecture

HavenBridge uses Loki in Monolithic mode.

```text
Grafana Alloy
      |
      v
havenbridge-loki-gateway
      |
      v
havenbridge-loki-0
Monolithic Loki
      |
      v
10Gi PVC
      |
      v
havenbridge-nfs
```

Monolithic mode means the Loki read, write, query, and storage functions are
handled by one Loki process instead of being separated into many
microservices.

This is appropriate for the current HavenBridge homelab because the expected
log volume is small and a distributed Loki architecture would add unnecessary
complexity.

---

## Loki Gateway

The Loki Helm chart deploys:

```text
havenbridge-loki-gateway
```

The gateway is the stable internal entry point used by clients that send or
query logs.

The in-cluster log ingestion endpoint is:

```text
http://havenbridge-loki-gateway.observability.svc.cluster.local/loki/api/v1/push
```

The intended flow is:

```text
Alloy
   ↓
Loki Gateway
   ↓
Loki
```

---

## Loki StatefulSet

The Monolithic Loki process is deployed as a Kubernetes StatefulSet.

Current Pod:

```text
havenbridge-loki-0
```

A StatefulSet is appropriate because Loki uses persistent storage that should
remain associated with the workload across Pod restarts.

---

## Persistent Storage

Loki uses a dynamically provisioned Kubernetes PVC.

Current PVC:

```text
storage-havenbridge-loki-0
```

Configuration:

```text
Capacity:      10Gi
Access mode:   ReadWriteOnce
StorageClass:  havenbridge-nfs
Status:        Bound
```

Storage flow:

```text
Loki StatefulSet
        ↓
volumeClaimTemplate
        ↓
PVC
        ↓
havenbridge-nfs StorageClass
        ↓
NFS-backed PersistentVolume
```

The PVC allows Loki log data to survive a Loki Pod restart.

---

## Loki Storage Configuration

HavenBridge currently uses:

```text
TSDB
+
filesystem object storage
```

Schema:

```text
v13
```

The important configuration is:

```text
store: tsdb
object_store: filesystem
schema: v13
```

The Loki filesystem is backed by the persistent Kubernetes volume rather than
temporary container storage.

---

## Replication Factor

HavenBridge currently runs one Loki replica.

Therefore:

```text
replication_factor: 1
```

A replication factor greater than one would require additional Loki replicas.

---

## Resource Configuration

The initial Loki resource allocation is:

```text
Requests:
  CPU:     100m
  Memory:  256Mi

Limits:
  CPU:     500m
  Memory:  1Gi
```

These values provide a conservative starting point for the HavenBridge
homelab and can be adjusted later based on measured usage.

---

## Memcached Caches

The Loki Helm chart enables large Memcached caches by default.

For the HavenBridge homelab these were intentionally disabled:

```text
chunksCache.enabled: false
resultsCache.enabled: false
```

The default cache allocation would consume significantly more memory than is
needed for the current environment.

---

## Loki Canary

Loki Canary was intentionally disabled.

```text
lokiCanary.enabled: false
```

HavenBridge will validate the real log pipeline using Grafana Alloy rather
than deploying additional synthetic canary Pods.

Because the Helm chart test depends on Loki Canary, the chart test was also
disabled:

```text
test.enabled: false
```

---

## Installation Validation

Before Loki was installed, the Helm chart was rendered using:

```bash
helm template havenbridge-loki \
  grafana-community/loki \
  --version 18.11.7 \
  --namespace observability \
  -f /tmp/havenbridge-loki-values.yaml
```

The rendered configuration confirmed:

```text
Monolithic Loki StatefulSet             PASS
1 Loki replica                          PASS
Loki 3.7.7 image                        PASS
10Gi PVC                                PASS
havenbridge-nfs StorageClass            PASS
TSDB                                    PASS
filesystem object storage               PASS
schema v13                              PASS
replication_factor = 1                  PASS
Loki gateway                            PASS
```

A Kubernetes server-side dry run also completed successfully before the
actual installation.

---

## Installed Resources

The Helm release is:

```text
havenbridge-loki
```

Namespace:

```text
observability
```

Validated workloads:

```text
havenbridge-loki-0                          2/2 Running
havenbridge-loki-gateway-...                2/2 Running
```

Validated PVC:

```text
storage-havenbridge-loki-0   Bound   10Gi   havenbridge-nfs
```

---

## Loki Readiness Validation

Loki readiness was tested directly.

Request:

```bash
curl -i http://127.0.0.1:3100/ready
```

Observed result:

```text
HTTP/1.1 200 OK
ready
```

Result:

```text
PASS
```

---

## Loki Build Validation

The Loki build-information API returned:

```text
version: 3.7.7
branch: release-3.7.x
```

This confirmed that the deployed application version matched the pinned Helm
chart configuration.

---

## Manual Log Ingestion Validation

Before introducing Grafana Alloy, one log entry was manually pushed to Loki.

Test log:

```text
HavenBridge Loki manual validation log
```

Label:

```text
job="havenbridge-loki-validation"
```

The log was successfully stored and queried back from Loki using LogQL.

Observed result:

```text
HavenBridge Loki manual validation log
```

Result:

```text
PASS
```

This proves that Loki can:

```text
receive logs
store logs
query logs
return logs
```

before Alloy is introduced.

---

## Current Status

```text
Loki Helm chart reviewed             PASS
Loki chart version pinned            PASS
Monolithic configuration             PASS
NFS persistent storage               PASS
Helm template validation             PASS
Kubernetes server dry-run            PASS
Loki installation                    PASS
Loki Pods running                    PASS
PVC bound                            PASS
Readiness endpoint                   PASS
Manual log ingestion                 PASS
Manual LogQL retrieval               PASS
```

The next step is to deploy Grafana Alloy so Kubernetes Pod logs are collected
automatically and forwarded to Loki.


## Automatic Log Ingestion Through Grafana Alloy

After manual Loki validation was completed, Grafana Alloy was deployed as the
automatic Kubernetes log collector.

Alloy now runs as a DaemonSet across all five Kubernetes nodes and forwards
logs to:

```text
http://havenbridge-loki-gateway.observability.svc.cluster.local/loki/api/v1/push
```

The validated production-style flow is:

```text
Kubernetes Pods
      ↓
Grafana Alloy
      ↓
havenbridge-loki-gateway
      ↓
Monolithic Loki
      ↓
10Gi PVC
      ↓
havenbridge-nfs
```

### Loki Gateway Ingestion Validation

Loki gateway access logs showed requests from Alloy such as:

```text
POST /loki/api/v1/push HTTP/1.1
HTTP status: 204
User-Agent: Alloy/v1.19.2
```

HTTP `204` confirms successful log ingestion.

### Kubernetes Namespace Discovery

The Loki label API returned logs from multiple Kubernetes namespaces,
including:

```text
calico-system
cert-manager
havenbridge
kube-system
metallb-system
observability
tigera-operator
```

This confirms that Alloy is collecting logs across the Kubernetes cluster.

### HavenBridge Application Log Retrieval

The following LogQL query successfully returned HavenBridge application logs:

```text
{namespace="havenbridge"}
```

Returned streams included:

```text
app="havenbridge-api"
namespace="havenbridge"
cluster="everpresence-haven"
node="eph-worker01"
node="eph-worker02"
```

Example retrieved logs included:

```text
GET /health/live HTTP/1.1" 200 OK
GET /health/ready HTTP/1.1" 200 OK
GET /metrics HTTP/1.1" 200 OK
```

This validates the complete application logging path:

```text
HavenBridge API
      ↓
container stdout/stderr
      ↓
Grafana Alloy
      ↓
Loki Gateway
      ↓
Loki
      ↓
LogQL
```

### Observability Platform Log Retrieval

The following query also successfully returned observability platform logs:

```text
{namespace="observability"}
```

Returned streams included logs from:

```text
Grafana
Loki
Loki Gateway
```

This means the logging platform can also observe its own operation.


## Grafana Datasource Validation

Loki was provisioned automatically as a Grafana datasource.

Datasource:

```text
Name: Loki
Type: loki
UID: loki
Access: proxy
Default: false
