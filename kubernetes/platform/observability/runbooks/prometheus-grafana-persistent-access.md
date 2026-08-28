# HavenBridge Prometheus and Grafana Persistent Local Access

## Purpose

Prometheus and Grafana are deployed inside the HavenBridge Kubernetes cluster
as `ClusterIP` services.

They are intentionally not exposed directly to the external network using
`NodePort`.

Administrative access from the `syrus` workstation is provided through two
controlled forwarding layers:

1. A Kubernetes `kubectl port-forward` running on `eph-cp01`
2. An SSH local tunnel running on `syrus`

Both forwarding layers are managed by systemd so they can restart
automatically and do not require terminals to remain open.

---

## Why Two Services Are Required

A systemd SSH tunnel on `syrus` does not itself connect directly to a
Kubernetes Service.

For Grafana, the complete traffic path is:

```text
Browser on syrus
http://127.0.0.1:3000
        |
        v
havenbridge-grafana-tunnel.service
systemd service on syrus
        |
        | SSH local forwarding
        v
eph-cp01:127.0.0.1:3000
        |
        v
havenbridge-grafana-portforward.service
systemd service on eph-cp01
        |
        | kubectl port-forward
        v
Grafana Kubernetes Service
        |
        v
Grafana Pod
```

Prometheus follows the same design:

```text
Browser on syrus
http://127.0.0.1:9090
        |
        v
havenbridge-prometheus-tunnel.service
systemd service on syrus
        |
        | SSH local forwarding
        v
eph-cp01:127.0.0.1:9090
        |
        v
havenbridge-prometheus-portforward.service
systemd service on eph-cp01
        |
        | kubectl port-forward
        v
Prometheus Kubernetes Service
        |
        v
Prometheus Pod
```

Both halves must be running.

If the SSH tunnel is running but the Kubernetes port-forward is stopped, the
browser can reach `eph-cp01`, but nothing is listening there to forward the
request into Kubernetes.

This behavior was observed during Grafana validation when manually stopping:

```bash
kubectl port-forward \
  -n observability \
  service/havenbridge-monitoring-grafana \
  3000:80
```

with `CTRL+C`.

The Grafana browser immediately lost connectivity even though the persistent
SSH tunnel on `syrus` remained active.

Restarting the Kubernetes port-forward restored Grafana.

This confirmed the need for persistent services on both systems.

---

# Grafana Persistent Access

## Grafana Kubernetes Service

Grafana is deployed by `kube-prometheus-stack`.

Validation:

```bash
kubectl get svc -n observability | grep grafana
```

Validated service:

```text
havenbridge-monitoring-grafana
Type: ClusterIP
Service port: 80
```

The Grafana application itself listens on port `3000` inside the workload.

The Kubernetes Service maps the Service port to the Grafana container.

---

## Grafana Port-Forward Service on eph-cp01

System:

```text
eph-cp01
```

Systemd unit:

```text
/etc/systemd/system/havenbridge-grafana-portforward.service
```

Purpose:

```text
eph-cp01:127.0.0.1:3000
        |
        v
Grafana Kubernetes Service
```

Service definition:

```ini
[Unit]
Description=HavenBridge Grafana Kubernetes Port Forward
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=mino
Environment=KUBECONFIG=/home/mino/.kube/config

ExecStart=/usr/bin/kubectl port-forward \
  --namespace observability \
  service/havenbridge-monitoring-grafana \
  3000:80 \
  --address 127.0.0.1

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

The port-forward is deliberately bound to:

```text
127.0.0.1
```

instead of:

```text
0.0.0.0
```

This prevents Grafana from being directly exposed on the `eph-cp01` network
interface.

Only local processes on `eph-cp01`, including the SSH connection from
`syrus`, can reach the forwarded port.

Enable and start:

```bash
sudo systemctl daemon-reload

sudo systemctl enable --now \
  havenbridge-grafana-portforward.service
```

Status:

```bash
sudo systemctl status \
  havenbridge-grafana-portforward.service
```

Listener validation:

```bash
ss -lntp | grep 3000
```

Expected:

```text
127.0.0.1:3000
```

Grafana health validation:

```bash
curl -s \
  http://127.0.0.1:3000/api/health \
  | python3 -m json.tool
```

Validated response included:

```text
database: ok
version: 13.2.0
```

Result:

```text
PASS
```

---

## Grafana SSH Tunnel Service on syrus

System:

```text
syrus
```

Systemd unit:

```text
/etc/systemd/system/havenbridge-grafana-tunnel.service
```

Purpose:

```text
syrus:127.0.0.1:3000
        |
        | encrypted SSH tunnel
        v
eph-cp01:127.0.0.1:3000
```

Service definition:

```ini
[Unit]
Description=HavenBridge Grafana SSH Tunnel
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=alabi

ExecStart=/usr/bin/ssh \
  -N \
  -T \
  -o BatchMode=yes \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -i /home/alabi/.ssh/eph_k8s \
  -L 127.0.0.1:3000:127.0.0.1:3000 \
  mino@172.16.10.31

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

The service does not use:

```text
-f
```

because systemd manages the process.

With a manually started SSH tunnel, `-f` moves SSH into the background.

With systemd, SSH should remain attached to systemd so the service manager can:

```text
monitor it
detect failures
restart it
record logs
manage startup and shutdown
```

Important SSH options:

```text
-N
    Do not execute a remote command or shell.

-T
    Do not allocate a pseudo-terminal.

BatchMode=yes
    Prevent interactive password prompts.

ExitOnForwardFailure=yes
    Fail the service if the requested port cannot be created.

ServerAliveInterval=30
    Send an SSH keepalive every 30 seconds.

ServerAliveCountMax=3
    Treat the connection as failed after three unanswered keepalives.
```

Enable and start:

```bash
sudo systemctl daemon-reload

sudo systemctl enable --now \
  havenbridge-grafana-tunnel.service
```

Status:

```bash
systemctl status \
  havenbridge-grafana-tunnel.service
```

Listener validation on `syrus`:

```bash
ss -lntp | grep 3000
```

Validated listener:

```text
127.0.0.1:3000
```

Browser URL:

```text
http://127.0.0.1:3000
```

Result:

```text
PASS
```

---

# Prometheus Persistent Access

## Prometheus Kubernetes Service

Prometheus is exposed inside the cluster using:

```text
havenbridge-monitoring-kub-prometheus
```

The service remains internal to Kubernetes.

Administrative access is provided using localhost forwarding rather than
NodePort.

---

## Prometheus Port-Forward Service on eph-cp01

System:

```text
eph-cp01
```

Systemd unit:

```text
/etc/systemd/system/havenbridge-prometheus-portforward.service
```

Purpose:

```text
eph-cp01:127.0.0.1:9090
        |
        v
Prometheus Kubernetes Service
```

Service definition:

```ini
[Unit]
Description=HavenBridge Prometheus Kubernetes Port Forward
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=mino
Environment=KUBECONFIG=/home/mino/.kube/config

ExecStart=/usr/bin/kubectl port-forward \
  --namespace observability \
  service/havenbridge-monitoring-kub-prometheus \
  9090:9090 \
  --address 127.0.0.1

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload

sudo systemctl enable --now \
  havenbridge-prometheus-portforward.service
```

Listener validation:

```bash
ss -lntp | grep 9090
```

Validated listener:

```text
127.0.0.1:9090
```

Prometheus readiness validation:

```bash
curl -s \
  http://127.0.0.1:9090/-/ready
```

Validated result:

```text
Prometheus Server is Ready.
```

Result:

```text
PASS
```

---

## Prometheus SSH Tunnel Service on syrus

System:

```text
syrus
```

Systemd unit:

```text
/etc/systemd/system/havenbridge-prometheus-tunnel.service
```

Purpose:

```text
syrus:127.0.0.1:9090
        |
        | encrypted SSH tunnel
        v
eph-cp01:127.0.0.1:9090
```

Service definition:

```ini
[Unit]
Description=HavenBridge Prometheus SSH Tunnel
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=alabi

ExecStart=/usr/bin/ssh \
  -N \
  -T \
  -o BatchMode=yes \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -i /home/alabi/.ssh/eph_k8s \
  -L 127.0.0.1:9090:127.0.0.1:9090 \
  mino@172.16.10.31

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload

sudo systemctl enable --now \
  havenbridge-prometheus-tunnel.service
```

Validation:

```bash
systemctl status \
  havenbridge-prometheus-tunnel.service
```

Listener:

```bash
ss -lntp | grep 9090
```

Prometheus test from `syrus`:

```bash
curl -s \
  http://127.0.0.1:9090/-/ready
```

Expected:

```text
Prometheus Server is Ready.
```

Browser URL:

```text
http://127.0.0.1:9090
```

The Prometheus SSH tunnel should only be marked fully validated after the
systemd service and browser access have both been confirmed from `syrus`.

---

# Why NodePort Was Not Used

A NodePort would make Grafana or Prometheus reachable through Kubernetes node
IP addresses.

For example:

```text
172.16.10.31:<NodePort>
172.16.10.32:<NodePort>
172.16.10.33:<NodePort>
172.16.10.34:<NodePort>
172.16.10.35:<NodePort>
```

This was unnecessary for administrative observability access.

Prometheus in particular does not provide authentication by default.

The chosen approach keeps both administrative interfaces bound to localhost:

```text
Grafana:     127.0.0.1:3000
Prometheus:  127.0.0.1:9090
```

Access therefore requires SSH access to the Kubernetes administration host.

This reduces unnecessary network exposure while retaining convenient access
from the `syrus` workstation.

A future controlled application-style exposure could use Traefik, Gateway API,
TLS, and authentication if required.

---

# Troubleshooting

## systemd status=217/USER

During Prometheus persistent-access configuration, the following error was
observed:

```text
status=217/USER
Failed to determine user credentials
```

The Prometheus Kubernetes port-forward service had accidentally been created
on `syrus`.

The unit contained:

```text
User=mino
Environment=KUBECONFIG=/home/mino/.kube/config
```

Those settings belong to `eph-cp01`.

The correct placement is:

```text
syrus
    SSH tunnel services

eph-cp01
    Kubernetes kubectl port-forward services
```

The incorrect unit was removed from `syrus`, systemd was reloaded, and the
service was recreated on `eph-cp01`.

Correct Prometheus validation on `eph-cp01`:

```bash
ss -lntp | grep 9090
```

Result:

```text
127.0.0.1:9090
```

Readiness:

```bash
curl -s http://127.0.0.1:9090/-/ready
```

Result:

```text
Prometheus Server is Ready.
```

---

## Port Already in Use

Before enabling a systemd forwarding service, check the required port:

Grafana:

```bash
ss -lntp | grep 3000
```

Prometheus:

```bash
ss -lntp | grep 9090
```

A manually started SSH tunnel or `kubectl port-forward` may already hold the
port.

Identify the process before terminating it:

```bash
ps -fp <PID>
```

Do not start the systemd service until the expected local port is available.

---

## View Service Logs

Grafana port-forward on `eph-cp01`:

```bash
sudo journalctl \
  -u havenbridge-grafana-portforward.service \
  -n 50 \
  --no-pager
```

Grafana tunnel on `syrus`:

```bash
sudo journalctl \
  -u havenbridge-grafana-tunnel.service \
  -n 50 \
  --no-pager
```

Prometheus port-forward on `eph-cp01`:

```bash
sudo journalctl \
  -u havenbridge-prometheus-portforward.service \
  -n 50 \
  --no-pager
```

Prometheus tunnel on `syrus`:

```bash
sudo journalctl \
  -u havenbridge-prometheus-tunnel.service \
  -n 50 \
  --no-pager
```

---

# Operational Commands

Restart Grafana forwarding:

```bash
sudo systemctl restart \
  havenbridge-grafana-portforward.service
```

Restart Grafana SSH tunnel:

```bash
sudo systemctl restart \
  havenbridge-grafana-tunnel.service
```

Restart Prometheus forwarding:

```bash
sudo systemctl restart \
  havenbridge-prometheus-portforward.service
```

Restart Prometheus SSH tunnel:

```bash
sudo systemctl restart \
  havenbridge-prometheus-tunnel.service
```

Check whether a unit starts automatically at boot:

```bash
systemctl is-enabled <service-name>
```

Check whether it is currently running:

```bash
systemctl is-active <service-name>
```

---

# Current Persistent Access Status

```text
syrus
├── havenbridge-grafana-tunnel.service           PASS
└── havenbridge-prometheus-tunnel.service        PASS

eph-cp01
├── havenbridge-grafana-portforward.service      PASS
└── havenbridge-prometheus-portforward.service   PASS
```

Once the Prometheus tunnel on `syrus` is validated, update:

```text
PENDING FINAL VALIDATION
```

to:

```text
PASS
```

---

# Final Access URLs

From the browser on `syrus`:

Grafana:

```text
http://127.0.0.1:3000
```

Prometheus:

```text
http://127.0.0.1:9090
```

These addresses remain bound to localhost and are intended for HavenBridge
administrative access.
