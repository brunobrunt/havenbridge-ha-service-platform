# HavenBridge Grafana

## Purpose

Grafana provides the visualization layer for the HavenBridge observability
platform.

It uses metrics collected by Prometheus to provide dashboards for:

- Kubernetes cluster health
- Node health and resource utilization
- Control-plane components
- HavenBridge application workloads
- PostgreSQL and application metrics as they are added
- Future logs and traces

Grafana was deployed as part of the existing `kube-prometheus-stack`
installation rather than as a separate standalone installation.


## Deployment

Grafana is deployed in:

```text
Namespace: observability
```

The Grafana Pod was validated using:

```bash
kubectl get pods -n observability | grep grafana
```

Validated workload:

```text
havenbridge-monitoring-grafana
3/3 Running
```

Grafana is exposed inside Kubernetes through:

```text
Service: havenbridge-monitoring-grafana
Type: ClusterIP
Service Port: 80
```

Validation command:

```bash
kubectl get svc -n observability | grep grafana
```


## Grafana Credentials

Grafana administrator credentials are stored in the Kubernetes Secret:

```text
havenbridge-monitoring-grafana
```

The Secret keys were inspected using:

```bash
kubectl get secret \
  -n observability \
  havenbridge-monitoring-grafana \
  -o json \
  | jq -r '.data | keys[]'
```

Validated keys:

```text
admin-password
admin-user
ldap-toml
```

The administrator username can be retrieved using:

```bash
kubectl get secret \
  -n observability \
  havenbridge-monitoring-grafana \
  -o jsonpath='{.data.admin-user}' \
  | base64 -d
echo
```

The administrator password can be retrieved locally using:

```bash
kubectl get secret \
  -n observability \
  havenbridge-monitoring-grafana \
  -o jsonpath='{.data.admin-password}' \
  | base64 -d
echo
```

The decoded password must not be committed to the repository or included in
project evidence.


## Grafana Health Validation

Grafana health was validated through its HTTP health API.

Command:

```bash
curl -s \
  http://127.0.0.1:3000/api/health \
  | python3 -m json.tool
```

Validated response:

```text
database: ok
version: 13.2.0
```

Result:

```text
PASS
```
## Prometheus Datasource Validation

The `kube-prometheus-stack` Helm deployment automatically provisioned
Prometheus as a Grafana datasource.

The Kubernetes datasource provisioning object was validated with:

```bash
kubectl get configmaps,secrets \
  -n observability \
  -l grafana_datasource=1


## Dashboard Validation

The `kube-prometheus-stack` deployment automatically provisioned Grafana
dashboards through ConfigMaps labeled for the Grafana dashboard sidecar.

Dashboard provisioning was validated with:

```bash
kubectl get configmaps \
  -n observability \
  -l grafana_dashboard=1
```

The total number of provisioned dashboard ConfigMaps was checked with:

```bash
kubectl get configmaps \
  -n observability \
  -l grafana_dashboard=1 \
  --no-headers \
  | wc -l
```

Validated result:

```text
29
```

This confirmed that 29 dashboards were provisioned automatically by the
monitoring stack.

Representative dashboards were then opened in Grafana and validated using
live Prometheus data.


### etcd Dashboard

Dashboard:

```text
etcd
```

The dashboard successfully displayed all three stacked-etcd members:

```text
172.16.10.31:2381
172.16.10.32:2381
172.16.10.33:2381
```

The dashboard reported:

```text
Up: 3
```

Live panels included:

```text
RPC rate
Active streams
Database size
Disk sync duration
Memory
Client traffic
Peer traffic
Raft-related metrics
```

This provided end-to-end validation of the etcd monitoring path:

```text
etcd metrics endpoints
        |
        v
Prometheus
        |
        v
Grafana Prometheus datasource
        |
        v
etcd dashboard
```

Result:

```text
PASS
```


### Kubernetes API Server Dashboard

Dashboard:

```text
Kubernetes / API server
```

The dashboard displayed live metrics from the Kubernetes API servers.

Representative values observed during validation included:

```text
Overall availability: approximately 99.88%
Read availability:    approximately 99.85%
Write availability:   approximately 99.95%
```

Populated panels included:

```text
Availability
Error budget
Read request rate
Write request rate
Read errors
Write errors
Read duration
Write duration
Work queue add rate
Work queue depth
Work queue latency
Memory
CPU
Goroutines
```

Metrics were visible for all three API server endpoints:

```text
172.16.10.31:6443
172.16.10.32:6443
172.16.10.33:6443
```

The dashboard showed active request traffic, low visible error activity,
stable resource usage, and no sustained work queue backlog during the
validation period.

Result:

```text
PASS
```


### Kubernetes Controller Manager Dashboard

Dashboard:

```text
Kubernetes / Controller Manager
```

The dashboard reported:

```text
Up: 3
```

This confirmed that Prometheus was successfully scraping all three
kube-controller-manager metrics endpoints:

```text
172.16.10.31:10257
172.16.10.32:10257
172.16.10.33:10257
```

Populated panels included:

```text
Work Queue Add Rate
Work Queue Depth
Work Queue Latency
Kube API Request Rate
POST Request Latency 99th Quantile
GET Request Latency 99th Quantile
Memory
CPU Usage
Goroutines
```

The dashboard also provided visual confirmation that the earlier
controller-manager metrics remediation was successful.

Result:

```text
PASS
```


### Kubernetes Compute Resources Nodes Overview

Dashboard:

```text
Kubernetes / Compute Resources / Nodes Overview
```

The dashboard successfully represented the complete HavenBridge Kubernetes
cluster.

Observed cluster values included:

```text
Nodes: 5
Pods:  approximately 69 during validation
```

All five nodes were represented:

```text
eph-cp01
eph-cp02
eph-cp03
eph-worker01
eph-worker02
```

Cluster-wide panels included:

```text
Node and Pod Count
CPU Usage
Memory Usage
CPU Utilization per Node
Memory Utilization per Node
```

The dashboard displayed live CPU and memory utilization separately for all
five nodes.

This confirmed the metrics path:

```text
Kubernetes nodes
      |
      v
node-exporter / kube-state-metrics
      |
      v
Prometheus
      |
      v
Grafana
      |
      v
Nodes Overview dashboard
```

Result:

```text
PASS
```


### Node Exporter Nodes Dashboard

Dashboard:

```text
Node Exporter / Nodes
```

The dashboard displayed live operating-system metrics from Kubernetes nodes.

Validated panels included:

```text
CPU Usage
Load Average
Memory Usage
Disk I/O
Filesystem Usage
```

A node-exporter instance such as:

```text
172.16.10.35:9100
```

was successfully selected and displayed live system metrics.

Result:

```text
PASS
```


### Dashboard Validation Summary

Representative dashboard validation produced:

```text
Provisioned dashboards                         29
etcd                                           PASS
Kubernetes / API server                        PASS
Kubernetes / Controller Manager                PASS
Kubernetes / Compute Resources / Nodes Overview PASS
Node Exporter / Nodes                          PASS
```

The validation confirms that the complete metrics visualization path is
operational:

```text
Kubernetes + HavenBridge infrastructure
                |
                v
             Metrics
                |
                v
            Prometheus
                |
                v
        Grafana datasource
                |
                v
          Grafana dashboards
```

Grafana dashboard provisioning and Kubernetes infrastructure visualization are
therefore considered operational.

## HavenBridge API Application Dashboard

A dedicated Grafana application dashboard was created for the HavenBridge
FastAPI backend.

Dashboard name:

```text
HavenBridge API — Application Overview
```

Dashboard description:

```text
Operational overview of the HavenBridge API covering replica health,
request rates, HTTP errors, response codes, route activity, and P95
latency using Prometheus metrics.
```

The dashboard converts the Prometheus application metrics exposed by
HavenBridge into operational views that can be used to understand traffic,
errors, latency, replica behavior, and application availability.

The two primary HavenBridge metric families currently used by the dashboard
are:

```text
havenbridge_http_requests_total
havenbridge_http_request_duration_seconds
```

These metrics contain labels such as:

```text
method
route
status_code
pod
namespace
service
```

Those labels allow the same base metrics to answer several different
operational questions.

For example:

```text
HTTP request counter
        |
        +---- rate() --------------------> overall request rate
        |
        +---- group by route -----------> request rate by route
        |
        +---- group by pod -------------> request rate by replica
        |
        +---- filter status_code=4xx ---> client error percentage
        |
        +---- filter status_code=5xx ---> server error rate/percentage
```

The request-duration histogram is used to calculate P95 latency globally,
by route, and by replica.

Kubernetes liveness and readiness probes are intentionally excluded from
the application traffic panels using:

```promql
route!~"/health/(live|ready)"
```

This prevents automated health checks from being mistaken for real
application traffic.


### Dashboard Panels

The dashboard currently contains 11 panels.

| # | Panel | Visualization | Purpose |
|---|---|---|---|
| 1 | HavenBridge API Replicas Up | Stat | Shows how many HavenBridge API replicas are currently reachable by Prometheus. |
| 2 | HavenBridge Application Request Rate | Time series | Shows the overall application request rate excluding Kubernetes health probes. |
| 3 | HavenBridge Request Rate by Route | Time series | Breaks application traffic down by individual API route. |
| 4 | HavenBridge HTTP 5xx Error Rate | Time series | Shows the rate of HTTP 5xx server errors. |
| 5 | HavenBridge HTTP Responses by Status Code | Time series | Shows request rate grouped by HTTP status code such as 200 and 404. |
| 6 | HavenBridge P95 Request Latency | Time series | Shows the estimated 95th-percentile request latency across the application. |
| 7 | HavenBridge Request Rate by Replica | Time series | Shows how incoming application traffic is distributed between API replicas. |
| 8 | HavenBridge P95 Latency by Route | Time series | Shows P95 request latency independently for each application route. |
| 9 | HavenBridge 5xx Error Percentage | Stat | Shows the percentage of application requests resulting in HTTP 5xx errors. |
| 10 | HavenBridge P95 Latency by Replica | Time series | Shows P95 request latency independently for each HavenBridge API replica. |
| 11 | HavenBridge 4xx Error Percentage | Stat | Shows the percentage of requests resulting in HTTP 4xx client errors. |


### Controlled Traffic Validation

Controlled requests were generated from `syrus` to prove that the dashboard
responded correctly to known traffic patterns.

Successful requests were generated using:

```bash
for i in {1..80}; do
  curl -s https://havenbridge.lab/ > /dev/null
done
```

Intentional HTTP 404 requests were generated using:

```bash
for i in {1..20}; do
  curl -s https://havenbridge.lab/this-route-does-not-exist > /dev/null
done
```

This produced:

```text
80 successful requests
20 intentional 404 requests
------------------------------
100 total requests
```

The expected HTTP 4xx percentage was therefore:

```text
20 / 100 * 100 = 20%
```

Grafana displayed:

```text
HavenBridge 4xx Error Percentage = 20%
HavenBridge 5xx Error Percentage = 0%
```

This proved that the application metrics, Prometheus queries, and Grafana
visualizations were correctly reflecting known traffic.

The route-level dashboard also showed:

```text
/
unmatched
```

The `unmatched` label is intentionally used by the HavenBridge metrics
middleware for unknown URLs rather than storing every invalid URL as a
separate Prometheus route label. This protects Prometheus from excessive
label cardinality.


### Dashboard Export and Source Control

After the dashboard was manually created and validated in Grafana, it was
exported as Grafana dashboard JSON.

The export uses the Grafana V2 dashboard resource format:

```text
apiVersion: dashboard.grafana.app/v2
kind: Dashboard
```

The exported dashboard was validated with `jq`.

Panel count validation returned:

```text
11
```

All panel titles, descriptions, visualization types, PromQL queries, and
dashboard settings were confirmed to be present.

The dashboard JSON is stored in Git at:

```text
kubernetes/platform/observability/grafana/dashboards/havenbridge-api-application-overview.json
```

The full source path on `syrus` is:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/observability/grafana/dashboards/havenbridge-api-application-overview.json
```

Grafana-generated resource metadata was removed from the Git-managed copy.

Fields such as the following were not retained:

```text
resourceVersion
generation
creationTimestamp
deprecatedInternalID
createdBy
updatedBy
updatedTimestamp
```

The stable dashboard resource name was retained:

```json
{
  "name": "adt7sm7"
}
```

This keeps the repository version focused on the dashboard definition rather
than metadata belonging to one running Grafana instance.


### Dashboard Provisioning with Kustomize

A Kustomize configuration was created at:

```text
kubernetes/platform/observability/grafana/dashboards/kustomization.yaml
```

Its purpose is to convert the Git-controlled dashboard JSON into a Kubernetes
ConfigMap without duplicating the entire dashboard JSON inside another YAML
manifest.

The configuration generates:

```text
ConfigMap:
havenbridge-api-grafana-dashboard
```

in:

```text
namespace: observability
```

with the required label:

```text
grafana_dashboard=1
```

The provisioning flow is:

```text
Git
 |
 v
havenbridge-api-application-overview.json
 |
 v
Kustomize
 |
 v
havenbridge-api-grafana-dashboard ConfigMap
 |
 v
grafana-sc-dashboard sidecar
 |
 v
Grafana provisioning directory
 |
 v
HavenBridge API — Application Overview
```


### Existing Grafana Dashboard Sidecar

The live kube-prometheus-stack configuration was inspected before enabling
custom dashboard provisioning.

The effective Helm configuration showed:

```text
sidecar dashboards enabled: true
label: grafana_dashboard
labelValue: 1
searchNamespace: ALL
allowUiUpdates: false
```

The Grafana Pod was also confirmed to contain:

```text
grafana-sc-dashboard
grafana-sc-datasources
grafana
```

Because the dashboard sidecar was already active, no additional dashboard
sidecar component was required.


### Kustomize and Kubernetes Validation

Before creating the ConfigMap, Kustomize rendered the manifests locally on
`eph-cp01`.

The rendered manifest contained:

```yaml
metadata:
  labels:
    grafana_dashboard: "1"
  name: havenbridge-api-grafana-dashboard
  namespace: observability
```

The rendered manifest size was approximately:

```text
52K
```

Server-side validation was performed before applying it:

```bash
kubectl apply \
  --dry-run=server \
  -f /tmp/havenbridge-grafana-dashboard-rendered.yaml
```

Result:

```text
configmap/havenbridge-api-grafana-dashboard created (server dry run)
```

The actual dashboard was then provisioned using:

```bash
kubectl apply -k /tmp/havenbridge-grafana-dashboard
```

Result:

```text
configmap/havenbridge-api-grafana-dashboard created
```


### ConfigMap Validation

The deployed ConfigMap was verified using:

```bash
kubectl -n observability get configmap \
  havenbridge-api-grafana-dashboard \
  --show-labels
```

The expected label was present:

```text
grafana_dashboard=1
```

The dashboard stored inside the ConfigMap was also queried directly.

Validation returned:

```text
title: HavenBridge API — Application Overview
panel_count: 11
```

This proved that all 11 dashboard panels survived the complete transformation:

```text
Grafana export
      ↓
JSON
      ↓
Kustomize
      ↓
ConfigMap
      ↓
Kubernetes
```


### Grafana Sidecar Provisioning Validation

The Grafana dashboard sidecar logs confirmed that the new dashboard was
detected.

Observed log:

```text
Writing /tmp/dashboards/havenbridge-api-application-overview.json (ascii)
```

Grafana was then instructed by the sidecar to reload its provisioned
dashboards.

Observed response:

```text
200 OK {"message":"Dashboards config reloaded"}
```

No Grafana Pod restart was required.

The Grafana web interface was refreshed after provisioning and all 11
HavenBridge application panels remained present.

Result:

```text
PASS
```


### Dashboard Management Model

The dashboard is no longer treated only as a manually created Grafana
resource.

The intended management model is now:

```text
Git
 ↓
Dashboard JSON
 ↓
Kustomize
 ↓
Kubernetes ConfigMap
 ↓
Grafana dashboard sidecar
 ↓
Grafana
```

The Git-controlled dashboard JSON should therefore be treated as the
authoritative copy for permanent dashboard configuration.

The live Grafana dashboard provider currently uses:

```text
allowUiUpdates: false
```

Permanent dashboard changes should therefore be reflected in the repository
rather than existing only as manual changes in the Grafana UI.


### Image Export Note

Grafana reported:

```text
Image renderer plugin not installed
```

when the dashboard image-export feature was opened.

This does not affect:

```text
dashboard rendering
Prometheus queries
dashboard provisioning
Grafana dashboard availability
```

It only affects Grafana's optional ability to render dashboards or panels
as image files.

Installing the image renderer plugin is not required for the current
observability phase.


## Persistent Administrative Access

Grafana remains exposed internally as a Kubernetes `ClusterIP` service.

Persistent administrative access from `syrus` is provided using two
systemd-managed forwarding layers.

```text
Browser on syrus
http://127.0.0.1:3000
        |
        v
havenbridge-grafana-tunnel.service
        |
        | SSH tunnel
        v
eph-cp01:127.0.0.1:3000
        |
        v
havenbridge-grafana-portforward.service
        |
        | kubectl port-forward
        v
Grafana Kubernetes Service
        |
        v
Grafana Pod
```

The two systemd services are:

On `syrus`:

```text
/etc/systemd/system/havenbridge-grafana-tunnel.service
```

On `eph-cp01`:

```text
/etc/systemd/system/havenbridge-grafana-portforward.service
```

Both services are enabled at boot and configured to restart automatically.

Validated browser URL from `syrus`:

```text
http://127.0.0.1:3000
```

The complete persistent-access implementation, service definitions,
validation commands, security reasoning, and troubleshooting steps are
documented in:

```text
kubernetes/platform/observability/runbooks/prometheus-grafana-persistent-access.md
```


## Why Grafana Is Not Exposed with NodePort

Grafana administrative access does not currently need to be reachable
directly from the HavenBridge lab network.

Using a NodePort would expose Grafana through Kubernetes node addresses.

Instead, Grafana remains a `ClusterIP` service and administrative access uses:

```text
localhost
    ↓
SSH tunnel
    ↓
localhost on eph-cp01
    ↓
kubectl port-forward
    ↓
Grafana
```

This reduces unnecessary network exposure.

A future production-style implementation could expose Grafana through
Traefik and Gateway API with TLS and appropriate authentication controls.


## Current Validation Status

```text
Grafana Pod                         PASS
Grafana Service                     PASS
Grafana HTTP health                 PASS
Grafana database health             PASS
Persistent eph-cp01 port-forward    PASS
Persistent syrus SSH tunnel         PASS
Browser access from syrus           PASS
Prometheus datasource               PASS
Kubernetes dashboards               PASS
```


## Next Step

The next Grafana validation step is to verify that the Prometheus datasource
was automatically provisioned by `kube-prometheus-stack`.

A second Prometheus datasource should not be created manually unless the
existing datasource is missing or incorrectly configured.
