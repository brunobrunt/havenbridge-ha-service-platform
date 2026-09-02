# HavenBridge Grafana Alloy

## What Is Grafana Alloy?

Grafana Alloy is the log collector used by HavenBridge.

Its job is to discover Kubernetes workloads, read their logs, attach useful
metadata, and forward the logs to Loki.

In simple terms:

```text
Kubernetes Pods
      ↓
Grafana Alloy
collects the logs
      ↓
Loki
stores the logs
      ↓
Grafana
displays and searches them
```

A useful analogy is:

```text
Alloy   = delivery truck
Loki    = warehouse
Grafana = control room
```

Alloy moves the logs.

Loki stores them.

Grafana is where operators search and investigate them.


## Why HavenBridge Uses Alloy

Kubernetes applications normally write logs to standard output and standard
error.

Examples include:

```text
FastAPI startup messages
HTTP request information
database errors
application exceptions
Kubernetes component logs
```

Without a collector, those logs remain distributed across individual Pods
and nodes.

Alloy provides a centralized collection path:

```text
Pod logs
   ↓
Alloy
   ↓
Loki
   ↓
Grafana
```


## Alloy Version

HavenBridge pins Alloy to:

```text
Helm repository: grafana
Chart:           alloy
Chart version:   1.12.1
Alloy version:   v1.19.2
```

Pinning the version makes the observability deployment reproducible.


## DaemonSet Deployment

Alloy is configured to run as a Kubernetes DaemonSet.

```text
controller.type: daemonset
```

A DaemonSet attempts to run one Alloy Pod on every Kubernetes node.

For HavenBridge:

```text
eph-cp01       → Alloy
eph-cp02       → Alloy
eph-cp03       → Alloy
eph-worker01   → Alloy
eph-worker02   → Alloy
```

This provides cluster-wide log collection.


## Control-Plane Toleration

The three Kubernetes control-plane nodes have the taint:

```text
node-role.kubernetes.io/control-plane:NoSchedule
```

Without a toleration, Alloy would only run on the worker nodes.

The Alloy configuration therefore includes a toleration allowing it to run
on the control-plane nodes as well.

This allows HavenBridge to collect logs from workloads across all five
Kubernetes nodes.


## Per-Node Log Collection

Each Alloy Pod receives the name of the Kubernetes node on which it is
running through the environment variable:

```text
NODE_NAME
```

Kubernetes populates this value using:

```text
spec.nodeName
```

Alloy uses the node name to discover only Pods running on the same node.

For example:

```text
Alloy on eph-worker01
        ↓
Pods on eph-worker01 only

Alloy on eph-worker02
        ↓
Pods on eph-worker02 only
```

This prevents multiple Alloy Pods from collecting the same Pod logs.


## Kubernetes API Log Collection

HavenBridge uses:

```text
loki.source.kubernetes
```

to read Pod logs through the Kubernetes API.

This design does not require:

```text
privileged containers
host filesystem access
/var/log host mounts
Docker container directory mounts
```

The Alloy Kubernetes ServiceAccount and RBAC permissions allow Alloy to read:

```text
pods
pods/log
namespaces
```

and discover Kubernetes workloads.


## Kubernetes Discovery

Alloy uses:

```text
discovery.kubernetes
```

to discover Kubernetes Pods.

The discovery configuration is restricted using:

```text
spec.nodeName
```

so that each Alloy DaemonSet Pod is responsible only for Pods on its own
Kubernetes node.


## Log Relabeling

Before logs are sent to Loki, Alloy converts Kubernetes metadata into useful
Loki labels.

Initial labels include:

```text
namespace
pod
container
node
app
cluster
```

The HavenBridge cluster label is:

```text
cluster="everpresence-haven"
```

These labels make later LogQL searches much easier.


## Example LogQL Queries

All logs from the HavenBridge namespace:

```text
{namespace="havenbridge"}
```

Logs associated with the HavenBridge API:

```text
{namespace="havenbridge", app="havenbridge-api"}
```

Logs from HavenBridge API Pods:

```text
{namespace="havenbridge", pod=~"havenbridge-api-.*"}
```


## Loki Destination

Alloy forwards collected logs to the Loki gateway:

```text
http://havenbridge-loki-gateway.observability.svc.cluster.local/loki/api/v1/push
```

The complete logging flow is:

```text
Kubernetes Pod
      ↓
Grafana Alloy
      ↓
havenbridge-loki-gateway
      ↓
Monolithic Loki
      ↓
10Gi persistent PVC
      ↓
havenbridge-nfs
```


## Resource Configuration

Each Alloy Pod initially requests:

```text
CPU:     50m
Memory:  128Mi
```

Resource limits:

```text
CPU:     250m
Memory:  256Mi
```

These values are intended as a conservative starting point for the current
HavenBridge homelab.


## RBAC

The Alloy Helm chart creates:

```text
ServiceAccount
ClusterRole
ClusterRoleBinding
```

The permissions required for log collection include read-only access to:

```text
pods
pods/log
namespaces
nodes
```

The goal is to allow Alloy to discover workloads and read their logs without
granting permissions to modify application resources.


## Alloy Configuration Flow

The main Alloy configuration follows this sequence:

```text
NODE_NAME
   ↓
discovery.kubernetes
   ↓
discover Pods on this node
   ↓
discovery.relabel
   ↓
add Kubernetes labels
   ↓
loki.source.kubernetes
   ↓
read Pod logs
   ↓
loki.write
   ↓
havenbridge-loki-gateway
```


## Current Status

Completed Alloy preparation:

```text
Alloy Helm repository added              PASS
Alloy chart version pinned               PASS
DaemonSet deployment selected            PASS
Control-plane taints inspected           PASS
Control-plane toleration configured      PASS
NODE_NAME injection configured           PASS
Kubernetes Pod discovery configured      PASS
Kubernetes API log collection selected   PASS
Loki destination configured              PASS
values.yaml created                      PASS
```

The next step is to render the Alloy Helm chart and inspect the generated
Kubernetes resources before installation.

## Installation and End-to-End Validation

Grafana Alloy was installed using Helm after the configuration had first been
validated with `helm template` and a Kubernetes server-side dry run.

Installed versions:

```text
Helm repository: grafana
Chart:           alloy
Chart version:   1.12.1
Alloy version:   v1.19.2
Namespace:       observability
```

### DaemonSet Validation

Alloy runs as a DaemonSet and successfully scheduled one Pod on every
HavenBridge Kubernetes node.

Validated placement:

```text
eph-cp01       → Alloy Running
eph-cp02       → Alloy Running
eph-cp03       → Alloy Running
eph-worker01   → Alloy Running
eph-worker02   → Alloy Running
```

All five Alloy Pods reported:

```text
READY:    2/2
STATUS:   Running
RESTARTS: 0
```

This confirms that the control-plane toleration works as intended.

The resulting architecture is:

```text
eph-cp01       → Alloy
eph-cp02       → Alloy
eph-cp03       → Alloy
eph-worker01   → Alloy
eph-worker02   → Alloy
                    |
                    v
          havenbridge-loki-gateway
                    |
                    v
                   Loki
```

### Alloy Log Discovery Validation

Alloy logs confirmed that Kubernetes Pod log streams were being discovered
and opened.

Examples included:

```text
observability/havenbridge-monitoring-kube-state-metrics
kube-system/kube-controller-manager-eph-cp02
kube-system/kube-controller-manager-eph-cp03
```

The following Alloy components were also observed loading successfully:

```text
discovery.kubernetes.pods
discovery.relabel.pod_logs
loki.source.kubernetes.pod_logs
loki.write.havenbridge
```

This confirms that Alloy can:

```text
discover Kubernetes Pods
        ↓
attach Kubernetes metadata
        ↓
open Pod log streams
        ↓
forward logs toward Loki
```

### Loki Push Validation

The Loki gateway logs confirmed successful pushes from Alloy.

Observed requests included:

```text
POST /loki/api/v1/push HTTP/1.1
HTTP status: 204
User-Agent: Alloy/v1.19.2
```

HTTP `204` confirms that Loki accepted the log batches.

Pushes were observed from Alloy Pods running on all five Kubernetes nodes.

This validates:

```text
Alloy
   ↓
loki.write
   ↓
havenbridge-loki-gateway
   ↓
Loki ingestion
```

### HavenBridge Application Log Validation

A LogQL query for the HavenBridge namespace successfully returned real
application logs:

```text
{namespace="havenbridge"}
```

Returned metadata included:

```text
app="havenbridge-api"
cluster="everpresence-haven"
container="havenbridge-api"
namespace="havenbridge"
node="eph-worker01"
node="eph-worker02"
service_name="havenbridge-api"
```

Example application log messages included:

```text
GET /health/live HTTP/1.1" 200 OK
GET /health/ready HTTP/1.1" 200 OK
GET /metrics HTTP/1.1" 200 OK
```

This proves that real HavenBridge application logs are being collected and
stored centrally.

### Observability Namespace Validation

The following query also returned logs from the observability platform:

```text
{namespace="observability"}
```

Returned workloads included:

```text
Grafana
Loki
Loki Gateway
```

Loki gateway logs showed continuous HTTP `204` responses for Alloy log pushes.

This demonstrates that the logging platform can also observe its own
components.

### RBAC Least-Privilege Validation

The Alloy Helm chart initially rendered broader read permissions than were
required for the HavenBridge log-only use case.

The chart defaults included access to resources such as:

```text
Secrets
ConfigMaps
Events
PrometheusRules
ServiceMonitors
AlertmanagerConfigs
```

Before installation, the HavenBridge configuration was reduced to read-only
access for:

```text
pods
pods/log
namespaces
```

Permitted verbs are only:

```text
get
list
watch
```

Alloy does not receive:

```text
create
update
patch
delete
```

This keeps the logging collector aligned with the HavenBridge least-privilege
design.

### RBAC Helm Rendering Issue

During RBAC hardening, the configuration initially used:

```text
clusterRules: []
```

With Alloy Helm chart `1.12.1`, this produced invalid rendered YAML because
the chart appends `rules` and `clusterRules` into the same ClusterRole.

The final configuration keeps the required Pod log permission in
`clusterRules` instead:

```text
rules:
  pods
  namespaces

clusterRules:
  pods/log
```

After the change:

```text
helm template result: PASS
Kubernetes server-side dry run: PASS
```

### Kubernetes API VIP Interruption During Installation

During the first real Helm installation attempt, the client temporarily lost
connectivity to the Kubernetes API VIP:

```text
https://k8s-api.lab:6443
172.16.10.30:6443
```

The observed errors included:

```text
http2: client connection lost
connect: no route to host
```

The issue was related to temporary Kubernetes API VIP/network connectivity
rather than Alloy configuration.

The installation subsequently completed successfully and all five Alloy
DaemonSet Pods became healthy.

This distinction is important operationally:

```text
Alloy configuration failure
        ≠
Kubernetes API connectivity failure
```

### Final Alloy Validation Status

```text
Helm chart rendered successfully             PASS
Least-privilege RBAC                         PASS
Kubernetes server-side dry run               PASS
DaemonSet installed                          PASS
All five nodes running Alloy                 PASS
Control-plane toleration                     PASS
Pod discovery                                PASS
Pod log streaming                            PASS
Kubernetes metadata labels                   PASS
Alloy → Loki Gateway                         PASS
Loki HTTP 204 ingestion                      PASS
HavenBridge application logs                 PASS
Observability platform logs                  PASS
LogQL retrieval                              PASS
```


## Grafana Integration Validation

Loki was provisioned as a Grafana datasource after Alloy-to-Loki ingestion
was validated.

Grafana Explore successfully displayed real HavenBridge application logs
collected by Alloy.

Validated flow:

Kubernetes Pod
    ↓
Grafana Alloy
    ↓
Loki
    ↓
Grafana Explore

Result: PASS
