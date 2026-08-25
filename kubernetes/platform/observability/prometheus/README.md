# HavenBridge Prometheus Monitoring

This directory contains the HavenBridge-specific Prometheus monitoring
configuration.

## File Purpose

| File | Purpose |
|---|---|
| `README.md` | Explains how Prometheus is configured, installed, validated, and maintained in HavenBridge. |
| `values.yaml` | Contains the HavenBridge-specific Helm settings that override the default `kube-prometheus-stack` configuration. |

Additional files may be added later as the monitoring implementation grows.

Examples may include:

| File | Purpose |
|---|---|
| `servicemonitor.yaml` | Tells Prometheus how to discover and scrape metrics from a HavenBridge application or service. |
| `prometheus-rules.yaml` | Defines Prometheus alerting or recording rules. |
| `grafana-dashboard*.json` | Stores reusable Grafana dashboard definitions if dashboards are managed in Git. |
| `evidence/*.txt` | Records installation and validation results for the monitoring implementation. |

## Helm Chart Selection

The HavenBridge monitoring stack uses the Prometheus Community
`kube-prometheus-stack` Helm chart.

Selected chart:

```text
Chart:       kube-prometheus-stack
Version:     88.5.4
App Version: v0.93.1
```

An exact chart version is pinned so that future installations remain
predictable and are not silently changed by newer upstream releases.


## HavenBridge Resource Configuration

The upstream chart does not define resource settings for several components by
default.

HavenBridge therefore defines explicit resource requests and limits appropriate
for the available homelab capacity.

Current configuration:

```text
Prometheus
  replicas:        1
  retention:       10 days
  CPU request:     250m
  memory request:  512Mi
  CPU limit:       1000m
  memory limit:    2Gi

Grafana
  CPU request:     100m
  memory request:  128Mi
  CPU limit:       500m
  memory limit:    512Mi

Alertmanager
  replicas:        1
  retention:       120h
  CPU request:     100m
  memory request:  128Mi
  CPU limit:       250m
  memory limit:    256Mi

kube-state-metrics
  CPU request:     10m
  memory request:  32Mi
  CPU limit:       100m
  memory limit:    64Mi

node-exporter
  CPU request:     100m
  memory request:  30Mi
  CPU limit:       200m
  memory limit:    50Mi
```

These values are starting points and may be adjusted later using actual
observed resource consumption.


## Initial Storage Decision

The only current Kubernetes StorageClass is:

```text
havenbridge-nfs
```

It is backed by the NFS CSI driver and is currently used by PostgreSQL.

Prometheus persistent TSDB storage has intentionally not been configured during
the initial monitoring deployment.

Grafana persistence has also not been enabled.

The first monitoring deployment will therefore focus on validating:

```text
Prometheus target discovery
Metrics collection
Kubernetes monitoring
Grafana dashboards
Alertmanager availability
node-exporter metrics
kube-state-metrics
```

Persistent observability storage will be evaluated separately after the
monitoring stack is operational.


## Helm Template Validation

Before installing the monitoring stack, the HavenBridge-specific
`values.yaml` file was rendered against `kube-prometheus-stack` chart version
`88.5.4`.

The Git-controlled configuration is stored at:

```text
kubernetes/platform/observability/prometheus/values.yaml
```

A temporary copy was transferred to `eph-cp01` for Helm validation.

The chart was rendered without applying any resources to Kubernetes:

```bash
helm template havenbridge-monitoring \
  prometheus-community/kube-prometheus-stack \
  --version 88.5.4 \
  --namespace observability \
  -f /tmp/havenbridge-kube-prometheus-stack-values.yaml \
  > /tmp/havenbridge-kube-prometheus-stack-rendered.yaml
```

The render completed successfully.

Rendered manifest size:

```text
6,878 lines
```

Major Kubernetes resources generated included:

```text
1  Alertmanager
1  Prometheus
1  DaemonSet
3  Deployments
11 Services
13 ServiceMonitors
35 PrometheusRules
32 ConfigMaps
7  ServiceAccounts
```

The rendered output was also inspected to confirm that the HavenBridge resource
overrides were actually applied.

Validation confirmed:

```text
Prometheus resources               PASS
Prometheus 10-day retention        PASS
Grafana resources                  PASS
Alertmanager resources             PASS
kube-state-metrics resources       PASS
node-exporter resources            PASS
Helm chart rendering               PASS
```

No Kubernetes resources were created during this validation.

Final result:

```text
HELM TEMPLATE VALIDATION PASSED
```
