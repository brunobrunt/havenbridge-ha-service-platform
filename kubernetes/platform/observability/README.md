# HavenBridge Observability

This directory contains the monitoring, logging, dashboard, alerting, and
observability configuration for the HavenBridge platform.

The observability phase begins after the core HavenBridge infrastructure,
application, CI, release automation, and continuous deployment pipeline have
been implemented and validated.

At the beginning of this phase, HavenBridge already has:

```text
KVM/libvirt infrastructure
        ↓
Highly available Kubernetes cluster
        ↓
kube-vip
        ↓
Calico
        ↓
MetalLB
        ↓
Traefik + Gateway API
        ↓
NFS-backed persistent storage
        ↓
PostgreSQL
        ↓
FastAPI HavenBridge API
        ↓
GitHub CI
        ↓
Semantic release automation
        ↓
Self-hosted CD runner
        ↓
Kubernetes deployment
```

The purpose of the observability phase is to make the health and behavior of
this platform measurable, searchable, and visible.

---

## Current Observability Status

The observability phase has started.

Current status:

```text
Observability directory created             COMPLETE
Cluster baseline validation                 COMPLETE
Cluster resource preflight                  COMPLETE
Prometheus installation                     NOT STARTED
Grafana installation                        NOT STARTED
HavenBridge application metrics             NOT STARTED
Loki installation                           NOT STARTED
Grafana Alloy installation                  NOT STARTED
Centralized Kubernetes logging              NOT STARTED
Alerting                                    NOT STARTED
Incident simulation                         NOT STARTED
Distributed tracing                         FUTURE
```

No monitoring stack has been installed yet.

This is intentional.

The existing Kubernetes platform was first validated so that any changes
introduced by the observability stack can be compared against a known healthy
baseline.

---

## Purpose

The HavenBridge observability layer will provide visibility into the health,
performance, and behavior of:

- Kubernetes nodes
- Kubernetes control-plane components
- Kubernetes workloads
- HavenBridge API Pods
- PostgreSQL
- Traefik
- Persistent storage
- Cluster networking
- Application requests
- Application failures
- Pod restarts
- Resource consumption
- Release behavior
- Future background workers and services

The goal is to move from:

```text
Something is wrong
        ↓
SSH into a node
        ↓
Run several kubectl commands
        ↓
Search individual logs
        ↓
Try to determine what happened
```

toward:

```text
Something is wrong
        ↓
Open Grafana
        ↓
Inspect metrics
        ↓
Inspect logs
        ↓
Correlate the evidence
        ↓
Identify the likely cause
```

---

## Operational Questions Observability Should Answer

The observability platform should eventually allow HavenBridge operators to
answer questions such as:

```text
Is the Kubernetes cluster healthy?

Are all HavenBridge Pods available?

Which node is using the most CPU?

Which Pod is consuming the most memory?

Has a Pod restarted recently?

Is the HavenBridge API receiving requests?

How many requests are succeeding?

How many requests are failing?

Is application latency increasing?

Is PostgreSQL reachable?

Is PostgreSQL consuming excessive resources?

Is Traefik successfully routing application traffic?

Are application requests returning HTTP 4xx or 5xx errors?

Did a deployment cause an increase in errors?

What happened immediately before an application failure?

Which logs correspond to a particular failure?

Is persistent storage behaving normally?

Are Kubernetes control-plane components healthy?
```

---

## Planned Observability Architecture

The HavenBridge observability architecture will collect both metrics and logs
from the Kubernetes platform and application workloads.

```text
Kubernetes + HavenBridge
        |
        +---- Metrics ----> Prometheus
        |                     |
        |                     v
        |                  Grafana
        |
        +---- Logs -------> Grafana Alloy
                              |
                              v
                            Loki
                              |
                              v
                           Grafana
```

Prometheus and Loki serve different purposes.

```text
Prometheus
    ↓
Metrics
    ↓
Numbers measured over time

Examples:
CPU
memory
request count
latency
error rate
Pod restarts
```

```text
Loki
    ↓
Logs
    ↓
Application and platform messages

Examples:
application errors
database connection failures
Traefik requests
startup messages
exceptions
```

Grafana provides a common interface for exploring both.

```text
Prometheus ──┐
             │
             v
           Grafana
             ^
             │
Loki ────────┘
```

---

## Planned Components

### Prometheus

Prometheus will collect and store time-series metrics.

Examples include:

```text
CPU usage
Memory usage
Filesystem usage
Pod restarts
Pod availability
Deployment replica health
HTTP request counts
HTTP error counts
Application latency
```

Prometheus works by periodically scraping metrics endpoints and storing the
results as time-series data.

Conceptually:

```text
Application / Kubernetes component
        ↓
/metrics endpoint
        ↓
Prometheus scrape
        ↓
Time-series database
        ↓
Queries / alerts / Grafana
```

---

### Prometheus Operator

The planned Kubernetes monitoring stack will use Prometheus Operator
functionality.

Prometheus Operator manages Kubernetes resources associated with Prometheus
monitoring.

Examples include:

```text
Prometheus
ServiceMonitor
PodMonitor
PrometheusRule
Alertmanager
```

This allows monitoring configuration to be managed using Kubernetes resources
rather than manually editing Prometheus configuration files.

---

### kube-state-metrics

kube-state-metrics exposes information about Kubernetes objects.

Examples include:

```text
Deployment desired replicas
Deployment available replicas
Pod status
PersistentVolumeClaim status
StatefulSet status
Node conditions
```

This is different from CPU or memory monitoring.

For example:

```text
node-exporter
    ↓
How much CPU is the machine using?

kube-state-metrics
    ↓
Does Kubernetes think this Deployment has the correct number of replicas?
```

---

### node-exporter

node-exporter exposes operating-system and hardware metrics from Kubernetes
nodes.

Examples include:

```text
CPU usage
Memory usage
Filesystem usage
Disk activity
Network activity
Load average
```

This will allow Grafana dashboards to show the health of:

```text
eph-cp01
eph-cp02
eph-cp03
eph-worker01
eph-worker02
```

---

### Grafana

Grafana will provide dashboards and visualization.

Grafana will initially use Prometheus as a data source.

Later it will also use Loki.

Conceptually:

```text
Prometheus metrics
        ↓
      Grafana
        ↑
Loki logs
```

Grafana dashboards will eventually include:

```text
Kubernetes cluster overview
Node health
Pod health
HavenBridge API health
HavenBridge request activity
PostgreSQL health
Traefik traffic
Storage health
Release/deployment behavior
```

---

### Loki

Loki will provide centralized log storage and querying.

Without centralized logging, troubleshooting often requires:

```bash
kubectl logs <pod>
```

for one Pod at a time.

With Loki, logs from many workloads can be queried centrally.

Conceptually:

```text
havenbridge-api Pod 1 ──┐
havenbridge-api Pod 2 ──┤
PostgreSQL ─────────────┤
Traefik ────────────────┤
Other workloads ────────┘
          ↓
      Grafana Alloy
          ↓
         Loki
          ↓
        Grafana
```

This will make it possible to investigate questions such as:

```text
Show HavenBridge API errors.

Show logs from namespace havenbridge.

Show logs from a particular Pod.

Show database connection failures.

Show logs around the time of a failed deployment.
```

---

### Grafana Alloy

Grafana Alloy will collect logs from Kubernetes workloads and forward them to
Loki.

The basic log flow will be:

```text
Kubernetes container logs
        ↓
Grafana Alloy
        ↓
Loki
        ↓
Grafana
```

Alloy will eventually attach useful Kubernetes metadata to logs so that they
can be searched using information such as:

```text
namespace
Pod
container
application
node
```

---

### Alertmanager

Alertmanager will later receive alerts generated by Prometheus rules.

Example:

```text
Prometheus detects condition
        ↓
Alert rule becomes active
        ↓
Alertmanager
        ↓
Notification
```

Potential HavenBridge alerts include:

```text
HavenBridge API unavailable

Too many HavenBridge API Pod restarts

High node CPU usage

High node memory usage

Persistent storage nearly full

PostgreSQL unavailable

Deployment has unavailable replicas

High HTTP 5xx error rate

Application latency above threshold
```

Alerting will be implemented only after the underlying metrics have first been
validated.

---

## Future Distributed Tracing

Distributed tracing is not part of the first observability implementation.

A later phase may introduce:

```text
OpenTelemetry
        ↓
Grafana Tempo
        ↓
Grafana
```

This could eventually allow one application request to be followed across
multiple HavenBridge services.

The longer-term observability model would then become:

```text
Metrics  → Prometheus
Logs     → Loki
Traces   → Tempo
             ↓
           Grafana
```

---

## Observability and the Future AI Operations Agent

The observability stack will also support the planned HavenBridge AI Operations
Agent.

The agent will eventually be able to use evidence from multiple sources.

Example:

```text
HavenBridge API unavailable
        ↓
Inspect Kubernetes Deployment
        ↓
Inspect Pod readiness
        ↓
Inspect Kubernetes Events
        ↓
Read Prometheus metrics
        ↓
Search Loki logs
        ↓
Read HavenBridge runbooks
        ↓
Correlate evidence
        ↓
Produce incident summary
        ↓
Recommend safe recovery actions
```

This is one reason observability is being implemented before the AI operations
phase.

---

## Implementation Strategy

Observability will be implemented incrementally.

Each major component will be:

```text
Understand
    ↓
Configure
    ↓
Deploy
    ↓
Validate
    ↓
Capture evidence
    ↓
Document
    ↓
Commit to Git
```

The project will not install Prometheus, Grafana, Loki, and Alloy all at once.

Each component must first be understood and validated independently.

---

## Implementation Phases

### O1 — Observability Foundation

Goals:

```text
Create observability repository structure
Document observability architecture
Capture existing cluster baseline
Review available cluster resources
Confirm Helm availability
Confirm no previous monitoring namespace exists
```

Status:

```text
IN PROGRESS
```

---

### O2 — Prometheus Monitoring Stack

Goals:

```text
Add Prometheus Helm repository
Inspect kube-prometheus-stack
Pin the selected chart version
Create HavenBridge-specific Helm values
Create monitoring namespace
Install monitoring stack
Validate Prometheus
Validate node-exporter
Validate kube-state-metrics
Validate Prometheus Operator
Validate Alertmanager components
```

Prometheus will not be installed using unexplained default values.

The selected Helm chart version and HavenBridge configuration will be recorded
in this repository.

---

### O3 — Grafana

Goals:

```text
Validate Grafana deployment
Access Grafana securely
Verify Prometheus data source
Inspect Kubernetes dashboards
Create HavenBridge-specific dashboards
```

Initial dashboards should include:

```text
Cluster overview
Node health
Pod health
Namespace health
HavenBridge workload health
```

---

### O4 — HavenBridge Application Metrics

The FastAPI application will later expose application-specific metrics.

Possible metrics include:

```text
HTTP request count
HTTP response status
HTTP error count
Request duration
Requests in progress
Inquiry creation count
Inquiry status-update count
Database operation failures
```

This will allow Prometheus to observe the application itself rather than only
the Kubernetes infrastructure around it.

---

### O5 — Loki and Grafana Alloy

Goals:

```text
Deploy Loki
Deploy Grafana Alloy
Collect Kubernetes container logs
Attach Kubernetes metadata
Connect Loki to Grafana
Validate log searches
```

Validation should include logs from:

```text
havenbridge-api
PostgreSQL
Traefik
```

---

### O6 — Alerting

Goals:

```text
Define Prometheus alert rules
Validate Alertmanager
Create meaningful HavenBridge alerts
Simulate safe failures
Confirm alerts activate and recover
```

Alerts should be based on observed baseline behavior rather than arbitrary
thresholds wherever possible.

---

### O7 — Combined Operational Dashboards

This phase will combine metrics and logs for troubleshooting.

Example:

```text
Grafana dashboard shows:
HTTP 500 spike
        ↓
Open related logs
        ↓
Loki shows database connection failures
        ↓
Prometheus shows PostgreSQL unavailable
        ↓
Incident cause becomes easier to identify
```

---

### O8 — Incident Simulation and Validation

Controlled failure scenarios may include:

```text
Scale HavenBridge API down
Restart an API Pod
Temporarily break a readiness condition
Generate HTTP errors
Generate application traffic
Observe Pod restart behavior
Simulate PostgreSQL unavailability where safe
```

The purpose is to prove that the observability stack can detect real changes in
platform behavior.

---

## Observability Repository Structure

The observability implementation will live under:

```text
kubernetes/platform/observability/
```

Initial structure:

```text
kubernetes/platform/observability/
├── README.md
└── evidence/
```

As the implementation grows, additional directories may be introduced.

Expected future structure:

```text
kubernetes/platform/observability/
├── README.md
├── prometheus/
├── grafana/
├── loki/
├── alloy/
├── alerting/
├── dashboards/
└── evidence/
```

Directories will be created only when the corresponding implementation begins.

---

## Management Hosts

The HavenBridge project deliberately separates repository management from
Kubernetes administration.

### syrus

`syrus` is used for:

```text
Git repository management
Editing configuration files
Editing README files
Creating observability manifests
Creating Helm values files
Git commits
Git pushes
Local application development
```

Repository:

```text
/home/alabi/projects/havenbridge-ha-service-platform
```

---

### eph-cp01

`eph-cp01` is currently used as the primary Kubernetes administrative host for
manual cluster operations during this phase.

Address:

```text
172.16.10.31
```

It is used for commands such as:

```text
kubectl
helm
```

Examples:

```bash
kubectl get nodes
kubectl get pods -A
helm version
```

The other control-plane nodes are:

```text
eph-cp02
eph-cp03
```

---

### havenbridge-runner01

`havenbridge-runner01` remains the dedicated self-hosted GitHub Actions CD
runner.

It uses a restricted Kubernetes identity and is not used as the general
cluster-administration workstation.

This preserves the least-privilege design of the HavenBridge CD pipeline.

---

## Pre-Installation Cluster Baseline

Before installing observability components, the Kubernetes cluster was
validated from `eph-cp01`.

Command:

```bash
kubectl get nodes -o wide
```

Result:

```text
NAME           STATUS   ROLES           VERSION   INTERNAL-IP
eph-cp01       Ready    control-plane   v1.36.2   172.16.10.31
eph-cp02       Ready    control-plane   v1.36.2   172.16.10.32
eph-cp03       Ready    control-plane   v1.36.2   172.16.10.33
eph-worker01   Ready    worker          v1.36.2   172.16.10.34
eph-worker02   Ready    worker          v1.36.2   172.16.10.35
```

Result:

```text
5/5 Kubernetes nodes Ready
```

---

## Pre-Installation Workload Baseline

Existing workloads were reviewed using:

```bash
kubectl get pods -A
```

The cluster contained healthy workloads for:

```text
Calico
cert-manager
HavenBridge API
PostgreSQL
CoreDNS
NFS CSI
etcd
Kubernetes API server
Kubernetes controller manager
Kubernetes scheduler
kube-proxy
kube-vip
MetalLB
Traefik
```

HavenBridge application state:

```text
havenbridge-api
    2 Pods Running

havenbridge-postgres-0
    1 Pod Running
```

This baseline is important because it records the state of the platform before
Prometheus, Grafana, Loki, or Alloy are introduced.

---

## Helm Baseline

Helm was validated on `eph-cp01`.

Command:

```bash
helm version
```

Result:

```text
Helm v4.2.3
Kubernetes client version v1.36
```

Helm will be used to install and manage major observability components.

---

## Resource Preflight

Before installing Prometheus and Grafana, Kubernetes node capacity was
reviewed.

Command:

```bash
kubectl get nodes \
  -o custom-columns='NAME:.metadata.name,CPU:.status.capacity.cpu,MEMORY:.status.capacity.memory'
```

Result:

```text
NAME           CPU   MEMORY
eph-cp01       2     3916Mi
eph-cp02       2     3916Mi
eph-cp03       2     4009988Ki
eph-worker01   2     7942Mi
eph-worker02   2     7942Mi
```

For easier interpretation:

```text
eph-cp01       2 vCPU   ~4 GiB
eph-cp02       2 vCPU   ~4 GiB
eph-cp03       2 vCPU   ~4 GiB
eph-worker01   2 vCPU   ~8 GiB
eph-worker02   2 vCPU   ~8 GiB
```

Approximate total cluster resources:

```text
CPU:     10 vCPU
Memory:  ~27 GiB
```

Approximate worker-node resources:

```text
CPU:     4 vCPU
Memory:  ~16 GiB
```

The observability stack must therefore be sized for a homelab environment.

The goal is to provide meaningful monitoring without consuming an excessive
portion of the resources needed by HavenBridge itself.

Resource requests and limits will be reviewed before installation rather than
blindly accepting production-sized defaults.

---

## Namespace Preflight

Before beginning the installation, the cluster was checked for existing
monitoring namespaces.

Command:

```bash
kubectl get namespace monitoring observability 2>/dev/null || true
```

Result:

```text
No existing monitoring namespace
No existing observability namespace
```

This confirms that the upcoming deployment will not collide with a previous
HavenBridge monitoring installation.

The namespace to be used for the initial Prometheus/Grafana monitoring stack
will be decided and documented before installation.

---

## Git Baseline

The repository on `syrus` was checked before beginning the observability work.

Command:

```bash
git status -sb
```

Baseline result:

```text
## main...origin/main
```

This confirmed that the observability phase started from the current main
branch.

---

## Planned Prometheus Deployment Approach

The initial Prometheus/Grafana monitoring implementation is expected to use the
Prometheus Community Helm chart:

```text
kube-prometheus-stack
```

The stack provides the major Kubernetes monitoring components required for the
first phase.

Before installation, HavenBridge will:

```text
Add the Prometheus Community Helm repository
        ↓
Refresh Helm repository metadata
        ↓
Inspect available kube-prometheus-stack versions
        ↓
Select and pin an exact chart version
        ↓
Review default values
        ↓
Create HavenBridge-specific values
        ↓
Review resource usage
        ↓
Install
        ↓
Validate every component
```

The project will not intentionally rely on an unspecified `latest` chart
version.

The exact chart version will be recorded here once selected.

---

## Planned Prometheus Installation Files

When the Prometheus implementation begins, configuration will be stored under:

```text
kubernetes/platform/observability/prometheus/
```

Expected files may include:

```text
kubernetes/platform/observability/prometheus/
├── values.yaml
└── README.md
```

The exact structure will be created when O2 begins.

The purpose of `values.yaml` will be to store HavenBridge-specific Helm
configuration instead of passing a long collection of options directly on the
command line.

---

## Storage Considerations

Prometheus and Loki store historical data.

Persistent storage will therefore be considered carefully.

HavenBridge already has:

```text
NFS CSI
        ↓
havenbridge-nfs StorageClass
        ↓
NFS storage hosted by syrus
```

Before persistence is enabled for Prometheus or Loki, the project will decide:

```text
How much data should be retained?

How much storage should be allocated?

Should the existing NFS StorageClass be used?

What happens to monitoring data if syrus is unavailable?

How important is historical monitoring data during disaster recovery?
```

Monitoring persistence will not be enabled without documenting these tradeoffs.

---

## Resource-Sizing Principle

HavenBridge is a homelab platform rather than a large production cluster.

Observability resources will therefore be sized according to actual available
capacity.

The objective is:

```text
Enough resources
    ↓
Prometheus and Grafana remain stable

but

Not so much
    ↓
Observability starves HavenBridge workloads
```

Resource usage will be reviewed after installation using Kubernetes resource
information and later Prometheus itself.

---

## Security Principles

The observability stack should follow the same security principles used
elsewhere in HavenBridge.

These include:

```text
Least privilege
Explicit Kubernetes identities
Avoid unnecessary external exposure
Use Secrets for sensitive values
Document access paths
Separate application and operational responsibilities
```

Grafana should not simply be exposed publicly without considering
authentication and routing.

Any Gateway API, Service, TLS, or authentication configuration used to access
Grafana will be documented before implementation.

---

## Validation Approach

Each observability component must have an explicit validation step.

Examples:

### Prometheus

```text
Prometheus Pod Running
        ↓
Prometheus targets discovered
        ↓
Targets healthy
        ↓
Metrics query succeeds
```

### Grafana

```text
Grafana Pod Running
        ↓
Grafana accessible
        ↓
Prometheus configured as data source
        ↓
Dashboard displays real metrics
```

### Loki

```text
Loki Running
        ↓
Alloy forwarding logs
        ↓
Loki receiving logs
        ↓
Grafana log query returns HavenBridge logs
```

### Alerting

```text
Alert rule configured
        ↓
Controlled condition generated
        ↓
Prometheus rule fires
        ↓
Alertmanager receives alert
        ↓
Condition recovers
        ↓
Alert resolves
```

---

## Evidence

Observability validation evidence will be stored under:

```text
kubernetes/platform/observability/evidence/
```

Evidence will be created incrementally rather than only at the end of the
project.

Expected evidence may include:

```text
cluster-baseline.txt
prometheus-installation-validation.txt
prometheus-target-validation.txt
grafana-validation.txt
havenbridge-metrics-validation.txt
loki-validation.txt
alloy-log-collection-validation.txt
alert-validation.txt
incident-simulation-validation.txt
```

Exact filenames may change as the implementation develops.

---

## Documentation Rule

Every completed observability step should be documented incrementally.

Documentation should capture:

```text
What was implemented
Why it was implemented
Where configuration is stored
Commands used
Configuration decisions
Validation performed
Observed result
Problems encountered
How problems were resolved
```

This README provides the overall observability architecture and implementation
history.

Component-specific details may later be stored in dedicated README files under:

```text
kubernetes/platform/observability/prometheus/
kubernetes/platform/observability/grafana/
kubernetes/platform/observability/loki/
kubernetes/platform/observability/alloy/
```

---

## Observability Phase 4 — HavenBridge Application Metrics

Observability Phase 4 adds application-level metrics and Grafana
visualization to the HavenBridge FastAPI backend.

The goal of this phase is to make application behavior observable beyond
basic Kubernetes Pod and node health.

The application exposes Prometheus metrics through:

```text
/metrics
```

The primary HavenBridge application metric families currently implemented
are:

```text
havenbridge_http_requests_total
havenbridge_http_request_duration_seconds
```

These metrics provide the foundation for monitoring:

```text
request traffic
HTTP response codes
HTTP 4xx errors
HTTP 5xx errors
request latency
route behavior
replica behavior
```

The metrics pipeline is:

```text
HavenBridge FastAPI
        |
        v
/metrics
        |
        v
ServiceMonitor
        |
        v
Prometheus
        |
        v
Grafana
```


### Prometheus Metrics Endpoint

The HavenBridge FastAPI application exposes Prometheus-compatible metrics at:

```text
/metrics
```

The application middleware records request information including:

```text
method
route
status_code
request duration
```

Kubernetes liveness and readiness requests are recorded by the application
metrics but are intentionally excluded from the Grafana application traffic
queries.

The `/metrics` endpoint itself is excluded from request instrumentation to
avoid Prometheus scraping activity inflating the application request metrics.


### HavenBridge Request Counter

The application exposes:

```text
havenbridge_http_requests_total
```

This is a Prometheus Counter.

It increases whenever the HavenBridge API processes an instrumented HTTP
request.

Labels include:

```text
method
route
status_code
```

This single metric is used to calculate several operational views, including:

```text
overall request rate
request rate by route
request rate by replica
HTTP responses by status code
HTTP 4xx percentage
HTTP 5xx rate
HTTP 5xx percentage
```


### HavenBridge Request Duration Histogram

The application also exposes:

```text
havenbridge_http_request_duration_seconds
```

This is a Prometheus Histogram.

It records how long application requests take to complete.

Histogram buckets are used with:

```text
histogram_quantile()
```

to estimate P95 latency.

P95 means that approximately 95 percent of observed requests completed at or
below the displayed latency value.

The dashboard uses this metric to calculate:

```text
overall P95 request latency
P95 latency by route
P95 latency by replica
```


### Prometheus ServiceMonitor

Prometheus scraping is configured through:

```text
kubernetes/platform/observability/prometheus/havenbridge-api-servicemonitor.yaml
```

The ServiceMonitor selects the HavenBridge API Service and scrapes:

```text
path: /metrics
port: http
interval: 30s
scrapeTimeout: 10s
```

The ServiceMonitor uses:

```text
release: havenbridge-monitoring
```

so that it matches the ServiceMonitor selector used by the deployed
kube-prometheus-stack Prometheus instance.


### Prometheus NetworkPolicy Access

Initial Prometheus discovery successfully found both HavenBridge API
endpoints, but the targets were unavailable because the HavenBridge API was
protected by Kubernetes NetworkPolicy ingress isolation.

The source-controlled NetworkPolicy is:

```text
kubernetes/applications/havenbridge/backend/networkpolicy.yaml
```

A dedicated ingress rule was added allowing only Prometheus Pods in the
`observability` namespace to reach HavenBridge API Pods on:

```text
TCP 8000
```

After the NetworkPolicy was applied, both HavenBridge API Prometheus targets
reported:

```text
up = 1
```

This validated both target discovery and network authorization.


### Prometheus Application Metrics Validation

Prometheus successfully stored custom HavenBridge metrics from both API
replicas.

Validated metric families included:

```text
havenbridge_http_requests_total
havenbridge_http_request_duration_seconds_count
```

Observed labels confirmed that metrics could be separated by:

```text
Pod
Service
route
method
HTTP status
```

Result:

```text
PASS
```


### HavenBridge Grafana Application Dashboard

A dedicated application dashboard was created:

```text
HavenBridge API — Application Overview
```

Dashboard description:

```text
Operational overview of the HavenBridge API covering replica health,
request rates, HTTP errors, response codes, route activity, and P95
latency using Prometheus metrics.
```

The dashboard currently contains 11 panels.

| # | Panel | Visualization |
|---|---|---|
| 1 | HavenBridge API Replicas Up | Stat |
| 2 | HavenBridge Application Request Rate | Time series |
| 3 | HavenBridge Request Rate by Route | Time series |
| 4 | HavenBridge HTTP 5xx Error Rate | Time series |
| 5 | HavenBridge HTTP Responses by Status Code | Time series |
| 6 | HavenBridge P95 Request Latency | Time series |
| 7 | HavenBridge Request Rate by Replica | Time series |
| 8 | HavenBridge P95 Latency by Route | Time series |
| 9 | HavenBridge 5xx Error Percentage | Stat |
| 10 | HavenBridge P95 Latency by Replica | Time series |
| 11 | HavenBridge 4xx Error Percentage | Stat |


### Kubernetes Health-Probe Exclusion

Application traffic queries intentionally exclude Kubernetes health checks
using:

```promql
route!~"/health/(live|ready)"
```

Without this filter, automated readiness and liveness requests would be
counted as application traffic and could hide the behavior of real user
requests.


### Controlled Grafana Traffic Validation

Controlled traffic was generated to prove that the dashboard correctly
represented known HTTP behavior.

Successful requests:

```bash
for i in {1..80}; do
  curl -s https://havenbridge.lab/ > /dev/null
done
```

Intentional HTTP 404 requests:

```bash
for i in {1..20}; do
  curl -s https://havenbridge.lab/this-route-does-not-exist > /dev/null
done
```

The controlled traffic contained:

```text
80 HTTP 200 requests
20 HTTP 404 requests
--------------------
100 total requests
```

Expected HTTP 4xx percentage:

```text
20 / 100 * 100 = 20%
```

Grafana displayed:

```text
HavenBridge 4xx Error Percentage = 20%
HavenBridge 5xx Error Percentage = 0%
```

Result:

```text
PASS
```

Unknown routes were represented by the metric label:

```text
unmatched
```

This prevents every invalid URL from becoming a unique Prometheus label and
helps control metric cardinality.


### Grafana Dashboard Source Control

After the 11-panel dashboard was manually built and validated, it was exported
from Grafana.

The Git-controlled dashboard definition is stored at:

```text
kubernetes/platform/observability/grafana/dashboards/havenbridge-api-application-overview.json
```

The full path on `syrus` is:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/observability/grafana/dashboards/havenbridge-api-application-overview.json
```

The exported dashboard uses:

```text
apiVersion: dashboard.grafana.app/v2
kind: Dashboard
```

The JSON was validated with `jq`.

Validated panel count:

```text
11
```

Grafana-instance-specific metadata such as resource versions, timestamps, and
local user identifiers was removed from the Git-controlled copy.


### Grafana Dashboard Provisioning

The dashboard is automatically made available to Grafana through Kubernetes
ConfigMap provisioning.

Kustomize configuration:

```text
kubernetes/platform/observability/grafana/dashboards/kustomization.yaml
```

The Kustomization generates:

```text
ConfigMap:
havenbridge-api-grafana-dashboard
```

in:

```text
namespace: observability
```

with:

```text
grafana_dashboard=1
```

The existing Grafana dashboard sidecar watches for this label.


### Grafana Dashboard Provisioning Flow

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
grafana-sc-dashboard
 |
 v
Grafana
 |
 v
HavenBridge API — Application Overview
```


### Grafana Sidecar Validation

The deployed Grafana Pod contains:

```text
grafana-sc-dashboard
grafana-sc-datasources
grafana
```

The effective dashboard sidecar configuration confirmed:

```text
enabled: true
label: grafana_dashboard
labelValue: 1
searchNamespace: ALL
allowUiUpdates: false
```

The generated ConfigMap passed Kubernetes server-side validation:

```text
configmap/havenbridge-api-grafana-dashboard created (server dry run)
```

The ConfigMap was then deployed successfully:

```text
configmap/havenbridge-api-grafana-dashboard created
```

The deployed ConfigMap contained:

```text
Dashboard title:
HavenBridge API — Application Overview

Panel count:
11
```

The Grafana sidecar logs confirmed:

```text
Writing /tmp/dashboards/havenbridge-api-application-overview.json (ascii)
```

Grafana then returned:

```text
200 OK {"message":"Dashboards config reloaded"}
```

The Grafana web interface was refreshed after provisioning and all 11
dashboard panels remained available.

Result:

```text
PASS
```


### Dashboard Management Model

The HavenBridge dashboard is now managed as code.

Previously:

```text
Grafana UI
    |
    v
manually created dashboard
```

Current model:

```text
Git
 |
 v
dashboard JSON
 |
 v
Kustomize
 |
 v
Kubernetes ConfigMap
 |
 v
Grafana sidecar
 |
 v
Grafana dashboard
```

The Git-controlled JSON should therefore be treated as the authoritative
configuration for permanent dashboard changes.


### Observability Phase 4 Validation Status

Observability Phase 4 has now validated:

```text
FastAPI Prometheus instrumentation                  PASS
/metrics endpoint                                  PASS
ServiceMonitor                                     PASS
Prometheus target discovery                        PASS
NetworkPolicy authorization                        PASS
Both HavenBridge API replicas scraped              PASS
Custom request counter                             PASS
Custom request-duration histogram                  PASS
Grafana 11-panel application dashboard             PASS
Controlled HTTP traffic validation                 PASS
HTTP 4xx percentage validation                     PASS
HTTP 5xx percentage validation                     PASS
Dashboard JSON export                              PASS
Dashboard source control                           PASS
Kustomize ConfigMap generation                     PASS
Grafana sidecar provisioning                       PASS
Grafana provisioning reload                        PASS
All 11 panels present after provisioning           PASS
```

The application metrics and visualization pipeline is operational:

```text
HavenBridge
    |
    v
Application metrics
    |
    v
Prometheus
    |
    v
Grafana
```

## Observability Phase 5 — Centralized Logging

Observability Phase 5 introduces centralized Kubernetes and HavenBridge
application logging.

The goal is to collect logs from workloads across the Kubernetes cluster,
store them centrally, and make them searchable through Grafana.

The logging architecture is:

```text
Kubernetes + HavenBridge
        |
        +---- Metrics ----> Prometheus
        |                     |
        |                     v
        |                  Grafana
        |
        +---- Logs -------> Grafana Alloy
                              |
                              v
                            Loki
                              |
                              v
                           Grafana
```

For the logging path specifically:

```text
Kubernetes Pods
      ↓
Grafana Alloy
      ↓
havenbridge-loki-gateway
      ↓
Monolithic Loki
      ↓
10Gi PersistentVolumeClaim
      ↓
havenbridge-nfs
```

### Grafana Alloy

Grafana Alloy is the log collector.

In simple terms:

```text
Alloy = collects and delivers logs
```

Alloy runs as a Kubernetes DaemonSet so that one Alloy Pod runs on each
Kubernetes node.

Current deployment:

```text
eph-cp01       → Alloy
eph-cp02       → Alloy
eph-cp03       → Alloy
eph-worker01   → Alloy
eph-worker02   → Alloy
```

The three control-plane nodes use a `NoSchedule` taint, so Alloy includes an
explicit toleration allowing the DaemonSet to run on those nodes.

Each Alloy instance receives its node name through:

```text
spec.nodeName
```

and discovers only Pods running on that same node.

This prevents multiple Alloy instances from collecting the same logs.

Alloy uses:

```text
loki.source.kubernetes
```

to read Kubernetes Pod logs through the Kubernetes API.

Useful Kubernetes metadata is converted into Loki labels including:

```text
namespace
pod
container
node
app
cluster
```

The cluster label is:

```text
cluster="everpresence-haven"
```

### Alloy RBAC

The default Alloy Helm chart rendered broader read permissions than required
for the HavenBridge logging use case.

Before installation, the permissions were reduced to read-only access to:

```text
pods
pods/log
namespaces
```

Allowed verbs are:

```text
get
list
watch
```

Alloy does not receive application resource modification permissions such as:

```text
create
update
patch
delete
```

This keeps the log collector aligned with the HavenBridge least-privilege
design.

### Loki

Grafana Loki is the centralized log storage and query backend.

In simple terms:

```text
Loki = stores and searches logs
```

HavenBridge currently deploys Loki in Monolithic mode.

This means the Loki read, write, query, and storage functions run together
instead of being separated into multiple distributed Loki services.

This design is appropriate for the current HavenBridge homelab because the
expected logging volume does not require a distributed Loki architecture.

Current versions:

```text
Loki Helm chart: 18.11.7
Loki version:    3.7.7
```

### Loki Gateway

Alloy sends logs to the Loki gateway rather than directly to the Loki Pod.

The internal ingestion endpoint is:

```text
http://havenbridge-loki-gateway.observability.svc.cluster.local/loki/api/v1/push
```

The flow is:

```text
Alloy
   ↓
havenbridge-loki-gateway
   ↓
Loki
```

The gateway provides a stable Kubernetes Service endpoint for log ingestion.

### Loki Persistent Storage

Loki uses persistent storage so log data is not tied to the lifecycle of the
Loki container.

Current storage configuration:

```text
PVC:           storage-havenbridge-loki-0
Capacity:      10Gi
Access Mode:   ReadWriteOnce
StorageClass:  havenbridge-nfs
Status:        Bound
```

Storage flow:

```text
Loki StatefulSet
      ↓
PVC
      ↓
havenbridge-nfs StorageClass
      ↓
NFS-backed PersistentVolume
```

Loki currently uses:

```text
TSDB
filesystem object storage
schema v13
replication_factor: 1
```

### Loki Validation

Before Alloy was introduced, Loki was validated independently.

The Loki readiness endpoint returned:

```text
HTTP/1.1 200 OK
ready
```

A manual validation log was then pushed to Loki:

```text
HavenBridge Loki manual validation log
```

The log was successfully queried back using LogQL.

This proved that Loki could:

```text
receive logs
store logs
query logs
return logs
```

before introducing the automatic log collector.

### Alloy Installation Validation

The Alloy Helm configuration was validated before installation using:

```text
helm template
        ↓
rendered Kubernetes YAML
        ↓
RBAC inspection
        ↓
Kubernetes server-side dry run
        ↓
Helm installation
```

The final DaemonSet successfully deployed one Alloy Pod on every Kubernetes
node.

All five Alloy Pods reported:

```text
READY:    2/2
STATUS:   Running
RESTARTS: 0
```

### End-to-End Log Pipeline Validation

Alloy logs confirmed that Kubernetes Pod log streams were being opened.

Examples included workloads from:

```text
havenbridge
observability
kube-system
```

The Loki gateway then showed requests such as:

```text
POST /loki/api/v1/push HTTP/1.1
HTTP status: 204
User-Agent: Alloy/v1.19.2
```

HTTP `204` confirms that Loki successfully accepted logs sent by Alloy.

Log pushes were observed from Alloy instances across all five Kubernetes
nodes.

### HavenBridge Application Log Validation

The following LogQL query successfully returned real HavenBridge application
logs:

```text
{namespace="havenbridge"}
```

Returned streams included metadata such as:

```text
app="havenbridge-api"
namespace="havenbridge"
cluster="everpresence-haven"
node="eph-worker01"
node="eph-worker02"
```

Example application logs included:

```text
GET /health/live HTTP/1.1" 200 OK
GET /health/ready HTTP/1.1" 200 OK
GET /metrics HTTP/1.1" 200 OK
```

This validates the complete path:

```text
HavenBridge API
      ↓
container logs
      ↓
Grafana Alloy
      ↓
Loki Gateway
      ↓
Loki
      ↓
LogQL
```

### Observability Platform Log Validation

Logs from the observability namespace were also successfully queried:

```text
{namespace="observability"}
```

Returned workloads included:

```text
Grafana
Loki
Loki Gateway
```

This demonstrates that the logging platform can also observe its own
components.

### Installation Connectivity Incident

During the initial Alloy Helm installation attempt, connectivity to the
Kubernetes API VIP was temporarily lost.

Observed errors included:

```text
http2: client connection lost
connect: no route to host
```

The affected endpoint was:

```text
k8s-api.lab
172.16.10.30:6443
```

The issue was related to Kubernetes API VIP/network connectivity rather than
the Alloy configuration itself.

The installation subsequently completed successfully.

This provides an important troubleshooting distinction:

```text
Application configuration failure
        ≠
Kubernetes control-plane connectivity failure
```

### Current Phase 5 Status

```text
Loki Helm deployment                    PASS
Monolithic Loki                         PASS
10Gi persistent storage                 PASS
havenbridge-nfs storage                 PASS
Loki readiness                          PASS
Manual Loki ingestion                   PASS
Manual LogQL retrieval                  PASS
Alloy DaemonSet                         PASS
Alloy on all five nodes                 PASS
Control-plane toleration                PASS
Least-privilege Alloy RBAC              PASS
Kubernetes Pod discovery                PASS
Pod log streaming                       PASS
Kubernetes metadata labels              PASS
Alloy → Loki Gateway                    PASS
Loki HTTP 204 ingestion                 PASS
HavenBridge application log retrieval   PASS
Observability platform log retrieval    PASS
```
### Phase 5 Completion

Grafana Loki datasource provisioning has now been completed.

Grafana successfully connects to Loki through:

```text
http://havenbridge-loki-gateway.observability.svc.cluster.local/
```

## Observability Phase 6 — Alerting

HavenBridge uses Prometheus alert rules and Alertmanager to detect
application availability, error-rate, and performance problems and
deliver operational notifications.

### Alerting Architecture

```text
HavenBridge metrics
        ↓
Prometheus
        ↓
Alert Rules
        ↓
Alertmanager
        ↓
havenbridge-notifications
        ├── Discord #havenbridge-alerts
        └── Slack   #havenbridge-alerts
```

```

### Alert Rule Files

HavenBridge-specific alert rules are defined in:

```text
kubernetes/platform/observability/prometheus/havenbridge-alerts.yaml
```

Alertmanager notification routing is defined in:

```text
kubernetes/platform/observability/prometheus/havenbridge-alertmanager-config.yaml
```

Discord and Slack webhook URLs are stored in Kubernetes Secrets
and are not committed to Git:

```text
havenbridge-discord-webhook
havenbridge-slack-webhook
```

### HavenBridgeAPIUnavailable

Check the HavenBridge API targets.

If:

```text
every API target is down
```

or:

```text
Prometheus cannot find the API targets at all
```

and the problem lasts at least 2 minutes,

fire:

```text
HavenBridgeAPIUnavailable
```

with severity:

```text
critical
```

The alert expression is:

```promql
sum(up{namespace="havenbridge", service="havenbridge-api"}) == 0
or
absent(up{namespace="havenbridge", service="havenbridge-api"})
```

The `absent()` condition is important because when all API replicas
disappear, Prometheus may have no target metrics rather than targets
reporting `up = 0`.

### HavenBridgeHigh5xxErrorRate

Look at HavenBridge application requests over the last 5 minutes.

Calculate:

```text
HTTP 5xx requests
----------------- × 100
all application requests
```

Health probe traffic is excluded.

If:

```text
5xx error percentage > 5%
```

and there is actual application traffic,

and the condition stays true for at least 2 minutes,

fire:

```text
HavenBridgeHigh5xxErrorRate
```

with severity:

```text
warning
```

The rule uses:

```promql
or vector(0)
```

so that when there are no 5xx responses, the error side can be
treated as zero instead of missing data.

It also verifies that request traffic is greater than zero so an idle
application does not generate a false high-error alert.

### HavenBridgeHighP95Latency

Look at HavenBridge requests over the last 5 minutes.

Find the latency below which 95% of requests completed.

If:

```text
P95 latency > 500 ms
```

and it stays that way for at least 2 minutes,

fire:

```text
HavenBridgeHighP95Latency
```

with severity:

```text
warning
```

The histogram stores duration in seconds, therefore:

```text
0.5 seconds = 500 milliseconds
```

During normal validation, HavenBridge P95 latency was approximately:

```text
4.75 ms
```

### Alert State Lifecycle

Prometheus alerts normally transition through:

```text
inactive
    ↓ condition becomes true
pending
    ↓ condition remains true for 2 minutes
firing
```

After the monitored condition recovers:

```text
firing
    ↓
inactive
```

### Notification Delivery

Alertmanager routes HavenBridge alerts through:

```text
havenbridge-notifications
```

The receiver sends notifications to:

```text
Discord #havenbridge-alerts
Slack   #havenbridge-alerts
```

Both integrations use:

```text
sendResolved: true
```

so operators receive both incident and recovery notifications.

### Alerting Validation

Observability Phase 6 validation included:

- Prometheus rule loading and health validation
- negative and positive 5xx PromQL testing
- controlled HTTP 500 generation
- `inactive → pending → firing` validation
- controlled API outage using `2 → 0` replicas
- HTTP 503 validation during the outage
- Alertmanager receipt of warning and critical alerts
- Discord firing and resolved notification delivery
- Slack firing and resolved notification delivery
- application recovery to `2/2` API replicas
- confirmation that both API scrape targets returned `up = 1`

Detailed validation commands and troubleshooting evidence are stored in:

```text
kubernetes/platform/observability/evidence/havenbridge-alerting-validation.txt
```

### HavenBridge Alerts

| Alert | Severity | Purpose |
|---|---|---|
| `HavenBridgeAPIUnavailable` | critical | Detects when all HavenBridge API targets are unavailable or disappear |
| `HavenBridgeHigh5xxErrorRate` | warning | Detects when HTTP 5xx responses exceed 5% of application traffic |
| `HavenBridgeHighP95Latency` | warning | Detects when P95 request latency exceeds 500 ms |
