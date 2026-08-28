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
