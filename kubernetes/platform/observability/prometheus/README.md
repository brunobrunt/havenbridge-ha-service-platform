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

## Prometheus Installation Validation

The monitoring stack was installed into the dedicated `observability`
namespace using the pinned Helm chart version:

```text
kube-prometheus-stack 88.5.4
```

Helm release:

```text
havenbridge-monitoring
```

Namespace:

```text
observability
```

The Helm release was validated with:

```bash
helm status havenbridge-monitoring \
  -n observability
```

Validated state:

```text
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

The observability workloads were also validated:

```bash
kubectl get pods -n observability -o wide
```

The monitoring stack included:

```text
Prometheus
Grafana
Alertmanager
Prometheus Operator
kube-state-metrics
node-exporter
```

The node-exporter DaemonSet successfully deployed one Pod to each Kubernetes
node.

```text
eph-cp01
eph-cp02
eph-cp03
eph-worker01
eph-worker02
```

Prometheus readiness was validated using:

```bash
curl -s http://127.0.0.1:9090/-/ready
```

Result:

```text
Prometheus Server is Ready.
```

The Prometheus query API was also validated successfully.


## Prometheus Target Validation

Prometheus uses the `up` metric to show whether discovered scrape targets are
reachable.

Conceptually:

```text
up = 1
    ↓
Prometheus discovered the target
and successfully scraped it

up = 0
    ↓
Prometheus discovered the target
but could not successfully scrape it
```

The following query was used to identify failed targets:

```promql
up == 0
```

CLI equivalent:

```bash
curl -sG \
  'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=up == 0' \
  | python3 -m json.tool
```

The initial validation discovered failures for:

```text
kube-proxy                 5 targets
kube-scheduler             3 targets
kube-controller-manager    3 targets
etcd                       3 targets
```

The workloads themselves were healthy.

The failures were caused by the metrics endpoints listening only on localhost,
while Prometheus was attempting to scrape them using the Kubernetes node IP
addresses.


## kube-proxy Metrics Scrape Failure and Remediation

### Problem

Prometheus discovered all five kube-proxy targets but reported:

```text
172.16.10.31:10249   up=0
172.16.10.32:10249   up=0
172.16.10.33:10249   up=0
172.16.10.34:10249   up=0
172.16.10.35:10249   up=0
```

The kube-proxy Pods themselves were confirmed healthy:

```bash
kubectl get pods -n kube-system \
  -l k8s-app=kube-proxy \
  -o wide
```

### Investigation

The kube-proxy ConfigMap was inspected:

```bash
kubectl -n kube-system get configmap kube-proxy \
  -o jsonpath='{.data.config\.conf}' \
  | grep -E 'metricsBindAddress|healthzBindAddress'
```

Initial result:

```text
healthzBindAddress: ""
metricsBindAddress: ""
```

The actual listening socket was then checked:

```bash
sudo ss -lntp | grep 10249
```

Result:

```text
127.0.0.1:10249
```

Local access worked:

```bash
curl -s http://127.0.0.1:10249/metrics | head -20
```

But node-IP access failed:

```bash
curl -sS --connect-timeout 3 \
  http://172.16.10.31:10249/metrics \
  | head -20
```

This proved that kube-proxy metrics were listening only on localhost.

### Root Cause

Prometheus was trying to scrape:

```text
172.16.10.x:10249
```

but kube-proxy was listening on:

```text
127.0.0.1:10249
```

Therefore:

```text
Prometheus
    ↓
node IP :10249
    ↓
no listener
    ↓
scrape failed
    ↓
up=0
```

### Remediation

Before modifying kube-proxy, its ConfigMap was backed up:

```bash
kubectl -n kube-system get configmap kube-proxy \
  -o yaml \
  > /tmp/kube-proxy-config-before-observability.yaml
```

The ConfigMap was edited:

```bash
KUBE_EDITOR=vim kubectl -n kube-system edit configmap kube-proxy
```

The metrics binding was changed from:

```text
metricsBindAddress: ""
```

to:

```text
metricsBindAddress: "0.0.0.0:10249"
```

Before restarting kube-proxy, the DaemonSet rollout strategy was verified:

```bash
kubectl -n kube-system get daemonset kube-proxy \
  -o jsonpath='Strategy: {.spec.updateStrategy.type}{"\n"}MaxUnavailable: {.spec.updateStrategy.rollingUpdate.maxUnavailable}{"\n"}'
```

Result:

```text
Strategy: RollingUpdate
MaxUnavailable: 1
```

The DaemonSet was then restarted safely:

```bash
kubectl -n kube-system rollout restart daemonset/kube-proxy
```

and monitored:

```bash
kubectl -n kube-system rollout status daemonset/kube-proxy \
  --timeout=5m
```

Final listener:

```bash
sudo ss -lntp | grep 10249
```

Result:

```text
*:10249
```

Final Prometheus validation:

```promql
up{job="kube-proxy"}
```

Result:

```text
172.16.10.31:10249   up=1
172.16.10.32:10249   up=1
172.16.10.33:10249   up=1
172.16.10.34:10249   up=1
172.16.10.35:10249   up=1
```

Result:

```text
5/5 PASS
```


## Control-Plane Metrics Scrape Failures

After kube-proxy was fixed, Prometheus still reported failed targets for:

```text
kube-scheduler
kube-controller-manager
etcd
```

Listener inspection on `eph-cp01` showed:

```bash
sudo ss -lntp | grep -E '10257|10259|2381'
```

Initial result:

```text
127.0.0.1:10259    kube-scheduler
127.0.0.1:10257    kube-controller-manager
127.0.0.1:2381     etcd
```

All three components were therefore reachable only from localhost.

These components are kubeadm-managed static Pods defined under:

```text
/etc/kubernetes/manifests/
```

Relevant manifests:

```text
/etc/kubernetes/manifests/kube-scheduler.yaml
/etc/kubernetes/manifests/kube-controller-manager.yaml
/etc/kubernetes/manifests/etcd.yaml
```

Because kubelet watches this directory directly, changing one of these manifests
causes the corresponding static Pod to be recreated automatically.


## kube-scheduler Metrics Scrape Failure and Remediation

The scheduler command was inspected using:

```bash
kubectl -n kube-system get pod kube-scheduler-eph-cp01 \
  -o jsonpath='{.spec.containers[0].command}' \
  | tr ' ' '\n' \
  | grep -- '--bind-address'
```

Initial configuration:

```text
--bind-address=127.0.0.1
```

The static Pod manifest probes were inspected:

```bash
sudo grep -nE \
  'bind-address|livenessProbe|readinessProbe|startupProbe|host:|port:' \
  /etc/kubernetes/manifests/kube-scheduler.yaml
```

The health probes used:

```text
127.0.0.1
```

Backups were created outside the static-Pod manifest directory before changes.

Example:

```text
/root/havenbridge-observability-backups/eph-cp01/
```

The scheduler configuration was changed on each control-plane node from:

```text
--bind-address=127.0.0.1
```

to:

```text
--bind-address=0.0.0.0
```

The health probe addresses were left unchanged.

Each control-plane node was changed and validated individually.

Listener validation:

```bash
sudo ss -lntp | grep 10259
```

Result:

```text
*:10259
```

An unauthenticated test such as:

```bash
curl -ks \
  https://172.16.10.31:10259/metrics \
  | head -20
```

returned:

```text
403 Forbidden
system:anonymous
```

This proved that the network endpoint was reachable but protected by
Kubernetes authentication and authorization.

Prometheus has an appropriate Kubernetes identity and was able to scrape the
metrics successfully.

Final result:

```text
172.16.10.31:10259   up=1
172.16.10.32:10259   up=1
172.16.10.33:10259   up=1
```

Result:

```text
3/3 PASS
```


## kube-controller-manager Metrics Scrape Failure and Remediation

The controller-manager command was inspected using:

```bash
kubectl -n kube-system get pod kube-controller-manager-eph-cp01 \
  -o jsonpath='{.spec.containers[0].command}' \
  | tr ' ' '\n' \
  | grep -- '--bind-address'
```

Initial result:

```text
--bind-address=127.0.0.1
```

The manifest probes were inspected using:

```bash
sudo grep -nE \
  'bind-address|livenessProbe|readinessProbe|startupProbe|host:|port:' \
  /etc/kubernetes/manifests/kube-controller-manager.yaml
```

The bind address was changed one control-plane node at a time from:

```text
--bind-address=127.0.0.1
```

to:

```text
--bind-address=0.0.0.0
```

After each static Pod recreation, the listener was verified:

```bash
sudo ss -lntp | grep 10257
```

Expected result:

```text
*:10257
```

Final Prometheus validation:

```promql
up{job="kube-controller-manager"}
```

Result:

```text
172.16.10.31:10257   up=1
172.16.10.32:10257   up=1
172.16.10.33:10257   up=1
```

Result:

```text
3/3 PASS
```


## etcd Metrics Scrape Failure and Remediation

etcd required more conservative handling because it stores the Kubernetes
cluster state and participates in the three-member stacked-etcd cluster.

The etcd command was inspected using:

```bash
kubectl -n kube-system get pod etcd-eph-cp01 \
  -o jsonpath='{.spec.containers[0].command}' \
  | tr ' ' '\n' \
  | grep -- '--listen-metrics-urls'
```

Initial configuration:

```text
--listen-metrics-urls=http://127.0.0.1:2381
```

The manifest and probe settings were inspected:

```bash
sudo grep -nE \
  'listen-metrics-urls|livenessProbe|readinessProbe|startupProbe|host:|port:' \
  /etc/kubernetes/manifests/etcd.yaml
```

Instead of exposing etcd metrics on every interface using `0.0.0.0`, localhost
was preserved and the specific management IP of each control-plane node was
added.

`eph-cp01`:

```text
--listen-metrics-urls=http://127.0.0.1:2381,http://172.16.10.31:2381
```

`eph-cp02`:

```text
--listen-metrics-urls=http://127.0.0.1:2381,http://172.16.10.32:2381
```

`eph-cp03`:

```text
--listen-metrics-urls=http://127.0.0.1:2381,http://172.16.10.33:2381
```

The members were changed one at a time.

After each change, the etcd static Pod was allowed to fully recreate before
proceeding to the next control-plane node.


## etcd Static Pod Restart Behavior

The etcd static Pods took longer to restart than kube-scheduler and
kube-controller-manager.

The observed sequence was:

```text
Running
   ↓
Terminating
   ↓
Pending
   ↓
Running
```

This additional time is expected because etcd is a stateful distributed
database.

During startup etcd must:

```text
open its persistent data
load its WAL/database state
rejoin the peer cluster
synchronize with other members
establish healthy quorum
pass readiness checks
```

Administrators should therefore allow additional startup time before assuming
an etcd static-Pod change has failed.


## etcd Health Validation

Direct metrics access was validated on each node:

```text
http://172.16.10.31:2381/metrics
http://172.16.10.32:2381/metrics
http://172.16.10.33:2381/metrics
```

Cluster health was checked after the changes:

```bash
kubectl get --raw='/readyz?verbose' \
  | grep -E 'etcd|readyz check passed'
```

Result:

```text
[+]etcd ok
[+]etcd-readiness ok
readyz check passed
```

Final Prometheus result:

```text
172.16.10.31:2381   up=1
172.16.10.32:2381   up=1
172.16.10.33:2381   up=1
```

Result:

```text
3/3 PASS
```


## Final Prometheus Target Health

After completing the remediation, all failed targets were checked again.

PromQL query:

```promql
up == 0
```

CLI equivalent:

```bash
curl -sG \
  'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=up == 0' \
  | python3 -m json.tool
```

Final result:

```text
result: []
```

This means there were no discovered Prometheus targets reporting `up=0`.

Healthy target count:

```promql
count(up == 1)
```

Validated result:

```text
46
```

Final monitoring state:

```text
Healthy targets:    46
Unhealthy targets:   0
```

Prometheus target collection is therefore considered operational.


## Security Considerations for Metrics Endpoints

Several metrics endpoints were intentionally made reachable over the internal
HavenBridge lab network so Prometheus could scrape them.

Ports include:

```text
9100    node-exporter
10249   kube-proxy
10257   kube-controller-manager
10259   kube-scheduler
2381    etcd metrics
```

These endpoints are intended only for internal observability.

They should not be exposed directly to untrusted or public networks.

The kube-scheduler and kube-controller-manager HTTPS metrics endpoints remain
protected by Kubernetes authentication and authorization.

kube-proxy, node-exporter, and etcd metrics endpoints should be protected using
appropriate network-level controls.


## Validation Evidence

The detailed installation and troubleshooting evidence is stored at:

```text
kubernetes/platform/observability/evidence/prometheus-target-validation.txt
```

This evidence includes:

```text
Helm validation
Prometheus readiness
node-exporter validation
kube-proxy troubleshooting
kube-scheduler troubleshooting
kube-controller-manager troubleshooting
etcd troubleshooting
control-plane health validation
final target health
```

Final validation:

```text
Prometheus Helm release             PASS
Prometheus readiness                PASS
node-exporter                       5/5 PASS
kube-proxy                          5/5 PASS
kube-scheduler                      3/3 PASS
kube-controller-manager             3/3 PASS
etcd                                3/3 PASS
Healthy Prometheus targets           46
Unhealthy Prometheus targets          0
```
