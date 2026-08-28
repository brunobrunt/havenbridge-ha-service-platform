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

Observability Phase 4 adds application-level Prometheus metrics to the
HavenBridge FastAPI backend.

The application exposes Prometheus metrics through:

```text
/metrics


## Current Next Step

The current observability phase is:

```text
O1 - Observability Foundation
```

The Kubernetes baseline and resource preflight have been completed.

The next implementation task is:

```text
Prometheus Community Helm repository
        ↓
Inspect kube-prometheus-stack
        ↓
Pin an exact chart version
        ↓
Review configuration
        ↓
Create HavenBridge-specific values.yaml
```

No Prometheus or Grafana workloads have been installed yet.

The next cluster change will occur only after the Helm chart and HavenBridge
configuration have been reviewed.


## Observability Namespace

Before beginning the observability installation, the cluster was checked for
existing monitoring namespaces.

Command:

```bash
kubectl get namespace monitoring observability 2>/dev/null || true



## Observability Phase 4 — HavenBridge Application Metrics

Observability Phase 4 adds application-level Prometheus metrics to the
HavenBridge FastAPI backend.

The application exposes Prometheus metrics through:

```text
/metrics
