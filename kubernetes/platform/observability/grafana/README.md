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

#### Grafana Pod Containers

The Grafana Pod contains the main Grafana application container and two
supporting sidecar containers.

The running containers were validated with:

```bash
kubectl -n observability get \
  $(kubectl -n observability get pods -o name | grep grafana | head -1) \
  -o jsonpath='{range .spec.containers[*]}{.name}{"\n"}{end}'
```

Observed containers:

```text
grafana-sc-dashboard
grafana-sc-datasources
grafana
```

Their responsibilities are:

```text
grafana
    = the main Grafana application

grafana-sc-dashboard
    = sidecar container that watches for dashboard ConfigMaps

grafana-sc-datasources
    = sidecar container that watches for datasource configuration
```

A sidecar is not a separate Pod in this design.

It is an additional container running alongside the main Grafana container
inside the same Kubernetes Pod.

The relationship can be represented as:

```text
Grafana Pod
│
├── grafana
│     └── main Grafana application
│
├── grafana-sc-dashboard
│     └── discovers dashboard ConfigMaps
│
└── grafana-sc-datasources
      └── discovers datasource configuration
```

For HavenBridge dashboards, the dashboard provisioning flow is:

```text
Dashboard JSON in Git
        ↓
Kustomize
        ↓
ConfigMap
        ↓
label:
grafana_dashboard="1"
        ↓
grafana-sc-dashboard
        ↓
dashboard file made available to Grafana
        ↓
Grafana loads the dashboard
```

This is why HavenBridge dashboard JSON files are included in:

```text
kubernetes/platform/observability/grafana/dashboards/kustomization.yaml
```

The ConfigMap acts as the Kubernetes delivery mechanism for the dashboard
configuration, while the `grafana-sc-dashboard` sidecar handles discovery and
provisioning into Grafana.

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


### Updating a Git-Managed Grafana Dashboard

HavenBridge Grafana dashboards are provisioned from Kubernetes ConfigMaps and
stored permanently in Git.

The repository is therefore the source of truth for dashboard configuration.

The dashboard flow is:

```text
Git dashboard JSON
        ↓
Kustomize
        ↓
Kubernetes ConfigMap
        ↓
grafana-sc-dashboard sidecar
        ↓
Grafana
```

Grafana is configured so provisioned dashboards cannot be permanently modified
directly through the Grafana UI.

When attempting to save a provisioned dashboard, Grafana reports:

```text
This dashboard cannot be saved from the Grafana UI because it has been
provisioned from another source.
```

This behavior is intentional.

It prevents a dashboard edited manually in Grafana from silently becoming
different from the version stored in Git.

The configuration therefore follows this principle:

```text
Grafana UI
    = dashboard development and testing

Git
    = permanent dashboard source of truth
```

#### Future Dashboard Update Workflow

Whenever an existing HavenBridge Grafana dashboard is changed, including:

```text
adding a panel
changing a PromQL query
changing a LogQL query
changing thresholds
changing value mappings
changing descriptions
changing panel visualization settings
changing dashboard layout
```

use the following workflow.

```text
Edit dashboard in Grafana
        ↓
test the change
        ↓
attempt Save
        ↓
Grafana reports dashboard is provisioned
        ↓
Save JSON to file
        ↓
validate exported JSON
        ↓
replace Git-managed dashboard JSON
        ↓
remove Grafana runtime metadata
        ↓
validate repository copy
        ↓
copy dashboard to eph-cp01 temporary apply directory
        ↓
kubectl apply -k
        ↓
ConfigMap updated
        ↓
grafana-sc-dashboard detects change
        ↓
Grafana provisioning reload
        ↓
refresh dashboard
        ↓
verify new configuration persists
```

#### Step 1 — Edit and Test the Dashboard

Use the Grafana UI to create or modify the required panel.

Before exporting, validate that the new panel behaves correctly.

For example, confirm:

```text
query returns expected data
visualization type is correct
title and description are present
thresholds are correct
value mappings are correct
healthy and failure states behave as expected
```

The Grafana UI should be treated as the dashboard development environment.

#### Step 2 — Export the Updated Dashboard

When the dashboard is ready, click:

```text
Save
```

Because the dashboard is provisioned, Grafana will not save it directly.

In the Save dashboard dialog use:

```text
Model:  V2 Resource
Format: JSON
```

Then select:

```text
Save JSON to file
```

Grafana downloads a new dashboard JSON file to `syrus`.

A typical downloaded file looks similar to:

```text
~/Downloads/HavenBridge — Operations Overview-<timestamp>.json
```

The timestamp changes with each export.

#### Step 3 — Identify the New Export

Run on `syrus`:

```bash
ls -lt ~/Downloads/*.json | head
```

The newest HavenBridge Operations Overview JSON file should appear first.

To avoid repeatedly typing the long filename, store it temporarily in a shell
variable.

Example:

```bash
FILE="$HOME/Downloads/HavenBridge — Operations Overview-<timestamp>.json"
```

`FILE` is only a convenience variable for the current shell session.

#### Step 4 — Validate the Export

Confirm that the expected number of panels exists.

Run on `syrus`:

```bash
jq '[.spec.elements[] | select(.kind == "Panel")] | length' "$FILE"
```

When validating a specific newly added panel, its title can also be searched.

Example:

```bash
grep -n 'PostgreSQL' "$FILE"
```

The purpose of these checks is:

```text
confirm correct export
        ↓
confirm expected panels
        ↓
only then modify Git source
```

#### Step 5 — Replace the Git Dashboard JSON

The Git-managed Operations Overview dashboard is:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/observability/grafana/dashboards/havenbridge-operations-overview.json
```

Run on `syrus`:

```bash
cp "$FILE" \
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/observability/grafana/dashboards/havenbridge-operations-overview.json
```

#### Step 6 — Remove Grafana Runtime Metadata

Grafana exports runtime metadata that should not be treated as permanent
repository configuration.

Examples include:

```text
runtime UID values
resource versions
generation numbers
creation timestamps
update timestamps
Grafana session metadata
```

HavenBridge keeps the stable dashboard resource name while removing this
runtime metadata.

Run on `syrus`:

```bash
jq '
  .metadata = {
    "name": .metadata.name
  }
' \
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/observability/grafana/dashboards/havenbridge-operations-overview.json \
> /tmp/havenbridge-operations-overview-clean.json
```

Then replace the repository copy:

```bash
mv /tmp/havenbridge-operations-overview-clean.json \
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/observability/grafana/dashboards/havenbridge-operations-overview.json
```

#### Step 7 — Validate the Repository Copy

For example, verify the dashboard panel count:

```bash
jq '[.spec.elements[] | select(.kind == "Panel")] | length' \
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/observability/grafana/dashboards/havenbridge-operations-overview.json
```

Additional validation can be performed with `grep` when a specific query or
panel change needs to be confirmed.

For example:

```bash
grep -n '\[5m\]' \
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/observability/grafana/dashboards/havenbridge-operations-overview.json
```

#### Step 8 — Copy the Dashboard to the Control Plane

The Git repository on `syrus` remains the source of truth.

The directory on `eph-cp01` is only a temporary Kubernetes apply location.

```text
syrus repository
    = permanent source of truth

/tmp/havenbridge-grafana-dashboards on eph-cp01
    = temporary deployment copy
```

Run on `syrus`:

```bash
scp \
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/observability/grafana/dashboards/havenbridge-operations-overview.json \
mino@172.16.10.31:/tmp/havenbridge-grafana-dashboards/havenbridge-operations-overview.json
```

#### Step 9 — Update the Kubernetes ConfigMap

Run on `eph-cp01`:

```bash
kubectl apply -k /tmp/havenbridge-grafana-dashboards
```

For an existing dashboard, the expected result is similar to:

```text
configmap/havenbridge-api-grafana-dashboard unchanged
configmap/havenbridge-operations-grafana-dashboard configured
```

`configured` indicates that Kubernetes updated the existing Operations
Overview ConfigMap.

#### Step 10 — Validate the Kubernetes Dashboard Copy

The dashboard JSON stored in the ConfigMap can be inspected to confirm that the
expected version reached Kubernetes.

Example panel-count validation on `eph-cp01`:

```bash
kubectl -n observability get configmap \
  havenbridge-operations-grafana-dashboard \
  -o json \
| jq -r '.data["havenbridge-operations-overview.json"]' \
| jq '[.spec.elements[] | select(.kind == "Panel")] | length'
```

#### Step 11 — Grafana Sidecar Reload

The Grafana Pod contains:

```text
grafana
grafana-sc-dashboard
grafana-sc-datasources
```

The `grafana-sc-dashboard` sidecar watches Kubernetes ConfigMaps labelled:

```text
grafana_dashboard=1
```

When the dashboard ConfigMap changes, the sidecar writes the updated dashboard
JSON into Grafana's provisioning directory and requests a provisioning reload.

The sidecar can be validated on `eph-cp01` with:

```bash
GRAFANA_POD=$(kubectl -n observability get pods -o name \
  | grep grafana \
  | head -1)
```

Then:

```bash
kubectl -n observability logs \
  "$GRAFANA_POD" \
  -c grafana-sc-dashboard \
  --since=10m \
  | grep -Ei 'havenbridge|dashboard|configmap'
```

A successful update is expected to include messages similar to:

```text
Writing /tmp/dashboards/havenbridge-operations-overview.json
```

and:

```text
Dashboards config reloaded
```

#### Step 12 — Refresh Grafana

If the browser still contains the previous manually edited version, Grafana may
display:

```text
Dashboard changed

The dashboard has been updated by another session.
```

At this point choose:

```text
Discard local changes
```

The browser-local edits are no longer needed because the new version has
already been exported, stored in Git and loaded through the Kubernetes
ConfigMap.

Refresh the dashboard and verify that the new panel or configuration remains.

If the change survives the refresh, the update is now persistent through the
Git-managed provisioning process.

#### Existing Dashboard Versus New Dashboard

When modifying the existing:

```text
HavenBridge — Operations Overview
```

the existing Kustomize entry does not need to be changed because the same JSON
filename and ConfigMap are being updated.

If an entirely new Grafana dashboard is created, then:

```text
kubernetes/platform/observability/grafana/dashboards/kustomization.yaml
```

must also be updated so Kustomize creates a ConfigMap for the new dashboard.

#### Operational Rule

For HavenBridge:

```text
Do not rely on Grafana UI Save for provisioned dashboards.

Edit and test in Grafana.
Export the JSON.
Validate the export.
Store it in Git.
Apply it through Kustomize.
Allow the Grafana sidecar to reload it.
Verify that the dashboard survives a refresh.
```

This keeps Grafana reproducible and prevents dashboard configuration from
existing only inside the running Grafana instance.


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


## HavenBridge — Operations Overview

The `HavenBridge — Operations Overview` dashboard was created during
Observability Phase 7 to provide a single operational view of HavenBridge
application health, traffic, latency, errors, alerts, Kubernetes workload
behavior and centralized application logs.

This dashboard complements the existing:

```text
HavenBridge API — Application Overview
```

dashboard.

The two dashboards serve different purposes:

```text
HavenBridge API — Application Overview
    = detailed application metrics

HavenBridge — Operations Overview
    = cross-signal operational troubleshooting
```

The Operations Overview dashboard combines:

```text
Prometheus metrics
        +
Prometheus alert state
        +
Loki application logs
        +
Kubernetes workload metrics
        ↓
Grafana
        ↓
HavenBridge — Operations Overview
```

Its purpose is to help an operator quickly answer:

```text
Is the API healthy?
Is application traffic reaching HavenBridge?
Are requests succeeding?
Are 5xx errors increasing?
Is latency abnormal?
Are both API replicas receiving traffic?
Are HavenBridge alerts firing?
What do the application logs show?
Are recent container restarts occurring?
```

### Dashboard Panels

The dashboard currently contains ten operational panels.

---

### Panel 1 — HavenBridge API Replicas Up

**Purpose**

Shows the number of HavenBridge API replicas currently being successfully
scraped by Prometheus.

**Visualization**

```text
Stat
```

**Data source**

```text
Prometheus
```

**PromQL**

```promql
sum(
  up{
    namespace="havenbridge",
    service="havenbridge-api"
  }
) or vector(0)
```

**Query type**

```text
Instant
```

**Unit**

```text
None
```

**Value mappings**

```text
0 → DOWN
1 → DEGRADED
2 → HEALTHY
```

**Thresholds**

```text
Base → Red
1    → Orange
2    → Green
```

**Operational interpretation**

```text
2
= both HavenBridge API replicas are available

1
= HavenBridge is still serving traffic but redundancy is degraded

0
= no HavenBridge API replica is available
```

---

### Panel 2 — HavenBridge Application Request Rate

**Purpose**

Shows the rate of non-health-check requests received by the HavenBridge API
over time.

**Visualization**

```text
Time series
```

**Data source**

```text
Prometheus
```

**PromQL**

```promql
sum(
  rate(
    havenbridge_http_requests_total{
      namespace="havenbridge",
      route!~"/health/(live|ready)"
    }[$__rate_interval]
  )
)
```

**Query type**

```text
Range
```

**Unit**

```text
requests/sec (req/s)
```

**Legend**

```text
Application requests
```

**Thresholds**

No thresholds are required.

This panel is intended to show traffic behavior over time rather than represent
a binary healthy or unhealthy condition.

**Operational interpretation**

An increasing line indicates that application traffic is reaching HavenBridge.

Routine Kubernetes health probes are excluded so the panel represents
application traffic rather than readiness and liveness checks.

---

### Panel 3 — HavenBridge 5xx Error Percentage

**Purpose**

Shows the percentage of HavenBridge application requests returning HTTP 5xx
server responses over the selected evaluation period.

**Visualization**

```text
Stat
```

**Data source**

```text
Prometheus
```

**PromQL**

```promql
100 *
(
  sum(
    rate(
      havenbridge_http_requests_total{
        namespace="havenbridge",
        status_code=~"5..",
        route!~"/health/(live|ready)"
      }[$__rate_interval]
    )
  )
  or vector(0)
)
/
sum(
  rate(
    havenbridge_http_requests_total{
      namespace="havenbridge",
      route!~"/health/(live|ready)"
    }[$__rate_interval]
  )
)
```

**Query type**

```text
Instant
```

**Unit**

```text
Percent (0-100)
```

**Legend**

```text
5xx error percentage
```

**No-value display**

```text
NO TRAFFIC
```

**Thresholds**

```text
Base → Green
5    → Orange
20   → Red
```

The warning threshold aligns with the HavenBridge 5xx alert, which evaluates
whether server errors exceed approximately 5% of application traffic.

**Operational interpretation**

```text
0%
= recent application traffic contains no HTTP 5xx responses

greater than 5%
= server-error rate has crossed the warning threshold

NO TRAFFIC
= there is not enough application traffic to calculate an error percentage
```

`NO TRAFFIC` is intentionally different from `0%`.

No traffic means there are no requests to evaluate, while `0%` means requests
are occurring but none are returning server errors.

---

### Panel 4 — HavenBridge P95 Request Latency

**Purpose**

Shows the P95 request latency for HavenBridge application traffic.

P95 answers:

```text
How quickly did 95% of recent application requests complete?
```

**Visualization**

```text
Stat
```

**Data source**

```text
Prometheus
```

**PromQL**

```promql
1000 * histogram_quantile(
  0.95,
  sum by (le) (
    rate(
      havenbridge_http_request_duration_seconds_bucket{
        namespace="havenbridge",
        route!~"/health/(live|ready)"
      }[$__rate_interval]
    )
  )
)
```

The result is multiplied by `1000` to convert seconds to milliseconds.

**Query type**

```text
Instant
```

**Unit**

```text
milliseconds (ms)
```

**Legend**

```text
P95 latency
```

**No-value display**

```text
NO TRAFFIC
```

**Thresholds**

```text
Base → Green
250  → Orange
500  → Red
```

The `500 ms` threshold aligns with the
`HavenBridgeHighP95Latency` warning alert.

**Operational interpretation**

For example:

```text
P95 = 4.75 ms
```

means approximately 95% of recent application requests completed in
`4.75 ms` or less.

Because this is a Stat visualization, the panel intentionally shows the
current calculated value rather than X and Y graph axes.

---

### Panel 5 — HavenBridge HTTP Responses by Status Code

**Purpose**

Shows HavenBridge API response traffic over time grouped by HTTP status code.

**Visualization**

```text
Time series
```

**Data source**

```text
Prometheus
```

**PromQL**

```promql
sum by (status_code) (
  rate(
    havenbridge_http_requests_total{
      namespace="havenbridge",
      route!~"/health/(live|ready)"
    }[$__rate_interval]
  )
)
```

**Query type**

```text
Range
```

**Unit**

```text
requests/sec (req/s)
```

**Legend**

```text
HTTP {{status_code}}
```

Examples include:

```text
HTTP 200
HTTP 404
HTTP 500
```

**Thresholds**

No thresholds are required.

The purpose of this panel is to compare response-code behavior over time.

**Operational interpretation**

```text
HTTP 200
= successful application request

HTTP 404
= requested application route or resource was not found

HTTP 500
= server-side application failure
```

During controlled validation the panel successfully displayed separate
HTTP `200`, `404` and `500` behavior.

---

### Panel 6 — HavenBridge Request Rate by Replica

**Purpose**

Shows the HavenBridge API request rate handled by each application replica over
time.

**Visualization**

```text
Time series
```

**Data source**

```text
Prometheus
```

**PromQL**

```promql
sum by (pod) (
  rate(
    havenbridge_http_requests_total{
      namespace="havenbridge",
      route!~"/health/(live|ready)"
    }[$__rate_interval]
  )
)
```

**Query type**

```text
Range
```

**Unit**

```text
requests/sec (req/s)
```

**Legend**

```text
{{pod}}
```

**Thresholds**

No thresholds are required.

**Operational interpretation**

Each line represents one HavenBridge API Pod.

The panel helps determine whether application traffic is reaching both API
replicas.

Two lines may occasionally overlap when both replicas are processing similar
request rates.

The legend should therefore also be checked when verifying replica activity.

---

### Panel 7 — Firing HavenBridge Alerts

**Purpose**

Shows the number of HavenBridge-specific Prometheus alerts currently in the
`firing` state.

**Visualization**

```text
Stat
```

**Data source**

```text
Prometheus
```

**PromQL**

```promql
count(
  ALERTS{
    alertname=~"HavenBridge.*",
    alertstate="firing"
  }
) or vector(0)
```

**Query type**

```text
Instant
```

**Unit**

```text
None
```

**Legend**

```text
Firing alerts
```

**Value mapping**

```text
0 → NO ACTIVE ALERTS
```

The zero state is displayed as green.

**Thresholds**

```text
Base → Green
1    → Red
```

**Operational interpretation**

```text
0
= no HavenBridge alert is currently firing

1 or more
= one or more HavenBridge operational alerts require attention
```

During controlled HTTP 500 validation this panel changed from:

```text
NO ACTIVE ALERTS
```

to:

```text
1
```

when `HavenBridgeHigh5xxErrorRate` entered the firing state.

It returned to the healthy state after recovery.

---

### Panel 8 — HavenBridge Application Logs

**Purpose**

Shows recent HavenBridge API application logs collected by Grafana Alloy and
stored in Loki.

Routine health-check and Prometheus metrics requests are filtered so the panel
focuses on useful application activity.

**Visualization**

```text
Logs
```

**Data source**

```text
Loki
```

**LogQL**

```logql
{namespace="havenbridge", app="havenbridge-api"}
  != "/health/live"
  != "/health/ready"
  != "/metrics"
```

**Query type**

```text
Range
```

**Display settings**

```text
Show timestamps: ON
Wrap lines:      ON
Display log level
```

**Unit**

Not applicable.

**Legend**

Not required.

**Thresholds**

Not applicable.

**Operational interpretation**

This panel provides application request context alongside the Prometheus
metrics.

During normal traffic validation it displayed entries such as:

```text
GET / HTTP/1.1 200 OK
```

During controlled error testing it also showed the corresponding application
requests.

---

### Panel 9 — HavenBridge Error Logs

**Purpose**

Shows recent HavenBridge API log entries associated with HTTP 5xx responses,
application errors, exceptions and tracebacks.

**Visualization**

```text
Logs
```

**Data source**

```text
Loki
```

**LogQL**

```logql
{namespace="havenbridge", app="havenbridge-api"}
  |~ "(?i)(error|exception|traceback| 5[0-9][0-9] )"
```

**Query type**

```text
Range
```

**Display settings**

```text
Show timestamps: ON
Wrap lines:      ON
Display log level
```

**Unit**

Not applicable.

**Legend**

Not required.

**Thresholds**

Not applicable.

**Operational interpretation**

During normal healthy operation this panel may display:

```text
No data
```

That is expected when no recent application errors exist.

During controlled HTTP 500 validation the panel populated with the intentional
server-error requests generated through:

```text
/test/500
```

This provides immediate log context when a server-error metric or alert is
observed.

---

### Panel 10 — HavenBridge Recent Pod Restarts

**Purpose**

Shows the number of HavenBridge container restarts detected during the most
recent 15-minute evaluation window.

**Visualization**

```text
Stat
```

**Data source**

```text
Prometheus
```

**PromQL**

```promql
sum(
  increase(
    kube_pod_container_status_restarts_total{
      namespace="havenbridge"
    }[15m]
  )
) or vector(0)
```

**Query type**

```text
Instant
```

**Unit**

```text
None
```

**Legend**

```text
Recent restarts
```

**Decimals**

```text
0
```

**Thresholds**

```text
Base → Green
1    → Orange
3    → Red
```

**Operational interpretation**

The panel intentionally uses a recent time window instead of displaying the
lifetime Kubernetes restart counter.

The original dashboard design used:

```promql
sum(
  kube_pod_container_status_restarts_total{
    namespace="havenbridge"
  }
) or vector(0)
```

That query displayed:

```text
3
```

even though the HavenBridge API Pods were healthy.

Kubernetes inspection showed:

```text
HavenBridge API replicas
    → 0 restarts

PostgreSQL Pod
    → 3 historical restarts accumulated over its lifetime
```

The lifetime counter therefore created a misleading operational signal.

The dashboard was changed to answer:

```text
Have any HavenBridge containers restarted recently?
```

rather than:

```text
Have any HavenBridge containers ever restarted?
```

This makes the panel more useful during active incident investigation.

---

### Why `$__rate_interval` Is Used

Several dashboard PromQL queries use:

```text
$__rate_interval
```

instead of a fixed interval such as:

```text
5m
```

`$__rate_interval` is calculated by Grafana using factors such as:

```text
dashboard time range
panel resolution
Prometheus scrape interval
```

This allows the same dashboard query to remain useful when switching between
ranges such as:

```text
Last 5 minutes
Last 1 hour
Last 6 hours
```

A direct Prometheus command using:

```promql
rate(...[5m])
```

may therefore produce a slightly different numeric value from the value
displayed by Grafana at the same moment.

The two queries are answering the same type of operational question but may be
using different evaluation windows.

---

### Phase 7 Dashboard Validation

The Operations Overview dashboard was validated using three controlled traffic
scenarios.

#### Normal HTTP 200 Traffic

Normal application requests were generated against:

```text
https://havenbridge.lab/
```

Expected and observed behavior included:

```text
API replicas       → HEALTHY
request rate       → increased
HTTP status        → HTTP 200
P95 latency        → low
5xx percentage     → 0%
firing alerts      → NO ACTIVE ALERTS
application logs   → GET / ... 200 OK
error logs         → no error entries
recent restarts    → 0
```

#### Controlled HTTP 404 Traffic

Requests were generated against the nonexistent route:

```text
https://havenbridge.lab/this-route-does-not-exist
```

The dashboard correctly showed:

```text
HTTP 404 status traffic
        +
404 application log entries
        +
0% server-error percentage
        +
no HavenBridge server-error alert
```

This confirmed that a client-side `404` condition is observable without being
incorrectly classified as a server-side `5xx` incident.

#### Controlled HTTP 500 Traffic

The protected observability test endpoint was temporarily enabled:

```text
/test/500
```

Controlled HTTP 500 traffic produced:

```text
HTTP 500 status series
        ↓
5xx percentage increase
        ↓
HavenBridge error-log entries
        ↓
HavenBridgeHigh5xxErrorRate
        ↓
pending
        ↓
firing
        ↓
Firing HavenBridge Alerts = 1
        ↓
Alertmanager
        ↓
Slack + Discord
```

After the controlled test endpoint was disabled and the application recovered:

```text
5xx traffic stopped
        ↓
Prometheus rolling window cleared
        ↓
alert returned to healthy state
        ↓
Firing HavenBridge Alerts = 0
        ↓
Slack + Discord resolved notifications
```

This demonstrated end-to-end correlation across metrics, logs, alert state and
external notification channels.

---

### Dashboard Source Control

The Operations Overview dashboard should be preserved in Git rather than
existing only as a manually edited Grafana object.

The dashboard source file is intended to be:

```text
kubernetes/platform/observability/grafana/dashboards/havenbridge-operations-overview.json
```

The complete dashboard lifecycle is:

```text
Grafana dashboard
        ↓
controlled validation
        ↓
export dashboard JSON
        ↓
store JSON in Git
        ↓
provision through Kubernetes
        ↓
Grafana sidecar loads dashboard
```

This follows the existing HavenBridge dashboard-management principle:

```text
Git
= source of truth

Grafana UI
= visualization and controlled dashboard development
```

Permanent dashboard changes should therefore be exported and committed rather
than remaining only in the live Grafana database.

Detailed Phase 7 validation evidence is stored separately under:

```text
kubernetes/platform/observability/evidence/
```

The next observability phase is:

```text
Observability Phase 8 — Incident Simulation
```

That phase will use the Operations Overview dashboard as a first-stop
investigation interface during realistic controlled HavenBridge failures.


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
