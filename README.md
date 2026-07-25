# Ever Presence Haven Highly Available Service Platform

A portfolio-grade infrastructure and application platform designed around a real operational use case for Ever Presence Haven.

The project provisions a five-node Kubernetes cluster on KVM/libvirt, configures the nodes with Ansible, builds a highly available kubeadm control plane, and prepares the platform to host an internal **Service Inquiry and Referral Tracking Platform**.

> **Privacy rule:** only synthetic demonstration data may be used. Do not store real client, health, disability, employee, referral, or personally identifiable information in this public repository or the homelab.

---

## Project Goal

Ever Presence Haven provides services such as home care, respite care, disability services, residential care, community access, Indigenous support, and employee resources.

The project translates that business context into a practical platform engineering solution:

**Ever Presence Haven Service Inquiry and Referral Tracking Platform**

Authorized staff will eventually be able to:

- Record service inquiries and referrals.
- Select the requested service category.
- Assign an inquiry to a coordinator.
- Track statuses such as `New`, `Assigned`, `Under Review`, `Contacted`, `Awaiting Information`, and `Closed`.
- See overdue or unassigned inquiries.
- View basic operational dashboards.
- Receive notifications when requests exceed a defined response period.
- Access approved internal policies or employee resources.

The Kubernetes cluster is not the final product by itself. It is the highly available foundation on which this operational application will run.

---

## Project Story

The completed portfolio story is intended to be:

> I designed and built a highly available Kubernetes service platform for Ever Presence Haven. Terraform provisions the KVM infrastructure, Ansible configures the Linux and Kubernetes nodes, kubeadm builds a three-control-plane cluster, kube-vip provides a shared API endpoint, Calico provides Pod networking, and the platform is being extended to host a service inquiry and referral tracking application with Prometheus, Grafana, and Alertmanager observability.

---

## Architecture

### Application architecture

```text
Staff user
    |
    v
Ingress Controller
    |
    v
Service Inquiry Web Application
    |
    +-----------------------+
    |                       |
    v                       v
Backend API             Employee Resources
    |
    +-----------------------+
    |                       |
    v                       v
PostgreSQL Database     Notification Worker
                            |
                            v
                     Email / internal alerts
```

### Kubernetes cluster topology

```text
                  k8s-api.lab:6443
                    172.16.10.30
                           |
                      kube-vip
                           |
          +----------------+----------------+
          |                |                |
      eph-cp01         eph-cp02         eph-cp03
    172.16.10.31     172.16.10.32     172.16.10.33
      API server       API server       API server
      Controller       Controller       Controller
      Scheduler        Scheduler        Scheduler
      etcd member      etcd member      etcd member
          |                |                |
          +----------------+----------------+
                           |
              +------------+------------+
              |                         |
         eph-worker01              eph-worker02
         172.16.10.34              172.16.10.35
```

The five virtual machines run on a Dell Precision 5810 host using KVM and libvirt. The three control-plane nodes provide a stacked-etcd quorum, while kube-vip exposes the shared Kubernetes API endpoint at `172.16.10.30`. Application workloads are scheduled primarily on the two worker nodes.

---

## Current Cluster Topology

| Node | IP address | Role | vCPU | Memory | Disk |
|---|---:|---|---:|---:|---:|
| `eph-cp01` | `172.16.10.31` | Control plane + etcd | 2 | 4 GiB | 40 GiB |
| `eph-cp02` | `172.16.10.32` | Control plane + etcd | 2 | 4 GiB | 40 GiB |
| `eph-cp03` | `172.16.10.33` | Control plane + etcd | 2 | 4 GiB | 40 GiB |
| `eph-worker01` | `172.16.10.34` | Worker | 2 | 8 GiB | 60 GiB |
| `eph-worker02` | `172.16.10.35` | Worker | 2 | 8 GiB | 60 GiB |
| Reserved | `172.16.10.36` | Future worker | TBD | TBD | TBD |

Network configuration:

| Purpose | Value |
|---|---|
| Libvirt node network | `172.16.10.0/24` |
| Libvirt gateway | `172.16.10.1` |
| Kubernetes API DNS name | `k8s-api.lab` |
| kube-vip virtual IP | `172.16.10.30/32` |
| Kubernetes API port | `6443` |
| Pod network | `10.244.0.0/16` |
| Service network | `10.96.0.0/12` |
| Calico encapsulation | VXLAN |
| SSH user | `mino` |

---

## Technology Stack

### Infrastructure

- Ubuntu 24.04 host
- KVM, QEMU and libvirt
- QCOW2 virtual disks
- cloud-init
- Terraform
- `dmacvicar/libvirt` provider

### Configuration and Kubernetes

- Ansible
- Ubuntu 24.04.4 LTS guests
- Kubernetes v1.36.2
- kubeadm, kubelet and kubectl
- CRI-O v1.36.2
- kube-vip v1.2.1
- Calico v3.32.1
- Three-member stacked etcd
- Tigera Operator and Calico API server

### Planned application and operations

- Python FastAPI backend
- Web frontend
- PostgreSQL
- Helm
- Ingress controller
- Prometheus
- Grafana
- Alertmanager
- Application metrics and alert rules

---

## Repository Layout

```text
everpresence-haven-platform/
├── README.md
├── terraform/
│   └── libvirt/
│       ├── README.md
│       ├── versions.tf
│       ├── providers.tf
│       ├── variables.tf
│       ├── locals.tf
│       ├── storage.tf
│       ├── cloud-init.tf
│       ├── domains.tf
│       ├── outputs.tf
│       ├── terraform.tfvars
│       ├── templates/
│       │   ├── user-data.yaml.tftpl
│       │   └── network-config.yaml.tftpl
│       └── scripts/
├── ansible/
│   ├── README.md
│   ├── ansible.cfg
│   ├── inventory/
│   │   ├── hosts.yml
│   │   └── group_vars/
│   │       └── all.yml
│   ├── playbooks/
│   └── roles/
└── kubernetes/                     # Planned application/platform manifests
    ├── applications/
    │   └── everpresence-referrals/
    └── monitoring/
```

`terraform.tfvars`, private keys, kubeconfig files, join commands, tokens, certificate keys, application secrets, and real client information must never be committed.

---

## Completed Milestones

### Infrastructure

- [x] Created a dedicated libvirt storage pool.
- [x] Imported an Ubuntu cloud image.
- [x] Provisioned five persistent QCOW2 VM disks.
- [x] Generated cloud-init seed images.
- [x] Created three control-plane VMs and two worker VMs.
- [x] Assigned deterministic MAC addresses and static node IPs.
- [x] Enabled QEMU guest agent support.
- [x] Changed the VM CPU model from `qemu64` to `host-passthrough`.
- [x] Confirmed Terraform can update the domains in place without destroying disks.

### Node configuration

- [x] Completed Ansible connectivity and preflight validation.
- [x] Disabled swap.
- [x] Loaded `overlay` and `br_netfilter`.
- [x] Applied Kubernetes networking sysctl settings.
- [x] Installed and configured CRI-O.
- [x] Installed kubeadm, kubelet and kubectl v1.36.2.
- [x] Held Kubernetes packages at the selected version.
- [x] Configured persistent resolution for `k8s-api.lab`.
- [x] Configured the CRI-O pause image expected by kubeadm.

### Kubernetes

- [x] Initialized `eph-cp01`.
- [x] Configured a three-member stacked-etcd control plane.
- [x] Joined `eph-cp02` and `eph-cp03`.
- [x] Joined `eph-worker01` and `eph-worker02`.
- [x] Deployed kube-vip on all three control-plane nodes.
- [x] Confirmed the shared API endpoint returns `ok`.
- [x] Installed Calico using the Tigera Operator.
- [x] Configured `10.244.0.0/16`, VXLAN, outbound NAT and `NodeInternalIP` detection.
- [x] Deployed the Calico API server.
- [x] Confirmed all TigeraStatus resources are available.
- [x] Confirmed all five Kubernetes nodes are `Ready`.

Current node view before optional worker-role labels:

```text
NAME           STATUS   ROLES           VERSION
eph-cp01       Ready    control-plane   v1.36.2
eph-cp02       Ready    control-plane   v1.36.2
eph-cp03       Ready    control-plane   v1.36.2
eph-worker01   Ready    <none>          v1.36.2
eph-worker02   Ready    <none>          v1.36.2
```

The `<none>` role is normal until the optional `node-role.kubernetes.io/worker` labels are added.

---

## Project Phases

### Phase 1 — Infrastructure as Code

Terraform provisions the libvirt storage, cloud image, node disks, cloud-init media, network interfaces and VM domains.

Detailed instructions and troubleshooting:

- [`terraform/libvirt/README.md`](terraform/libvirt/README.md)

### Phase 2 — Configuration and Kubernetes Bootstrap

Ansible prepares the operating system, installs CRI-O and Kubernetes packages, configures the API endpoint, prepares kube-vip, and supports the kubeadm bootstrap process.

Detailed instructions and troubleshooting:

- [`ansible/README.md`](ansible/README.md)

### Phase 3 — Cluster Validation

Planned validation work:

- [ ] Label worker nodes.
- [ ] Test Pod scheduling on both workers.
- [ ] Test Pod-to-Pod communication.
- [ ] Test Kubernetes DNS and Service discovery.
- [ ] Test the kube-vip shared endpoint.
- [ ] Test kube-vip failover between control planes.
- [ ] Test control-plane API availability during a single-node outage.
- [ ] Test etcd quorum behaviour.
- [ ] Create an etcd backup and recovery runbook.
- [ ] Validate reboot persistence for all nodes.

### Phase 4 — Platform Services

- [ ] Install an ingress controller.
- [ ] Define an internal application DNS name.
- [ ] Configure TLS.
- [ ] Choose a persistent storage approach for the homelab.
- [ ] Create application namespaces.
- [ ] Establish ConfigMap and Secret handling.
- [ ] Add NetworkPolicies.
- [ ] Add application-specific RBAC.

### Phase 5 — Inquiry and Referral Tracking Application

Suggested application states:

```text
New
Assigned
Under Review
Contacted
Awaiting Information
Closed
```

Suggested synthetic data model:

```text
Inquiry ID
Synthetic client name
Service category
Assigned coordinator
Status
Created time
Response deadline
Last updated time
Internal demonstration notes
```

Application components:

```text
Frontend
Backend API
PostgreSQL
Notification/SLA worker
Synthetic seed data
```

Application deployment should include:

- Namespace
- Deployments
- Services
- ConfigMaps
- Secrets
- PersistentVolumeClaims
- Ingress
- PodDisruptionBudgets
- Resource requests and limits
- Readiness and liveness probes
- HorizontalPodAutoscaler where meaningful

### Phase 6 — Monitoring and Alerting

This phase stays inside the original project scope because it provides operational visibility for both the cluster and the inquiry platform.

Planned components:

- Prometheus
- Grafana
- Alertmanager
- kube-state-metrics
- Node Exporter
- Prometheus Operator
- ServiceMonitor or PodMonitor resources
- PrometheusRule resources
- Application dashboards

Cluster alerts:

- Node unavailable
- Pod crash looping
- Deployment replicas unavailable
- High CPU or memory usage
- Low disk space
- PersistentVolume capacity risk
- Kubernetes API unavailable
- etcd member unhealthy

Application alerts:

- Application endpoint unavailable
- API error rate above threshold
- High response latency
- PostgreSQL unavailable
- Notification worker failed
- Inquiry unassigned beyond the response target
- Inquiry under review beyond the service-level target

Only synthetic inquiry data will be used during testing.

---

## High-Level Validation Commands

Run from a configured control-plane node:

```bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl get tigerastatus
kubectl get ippools.crd.projectcalico.org
kubectl get --raw='/readyz?verbose'
curl -skS --max-time 10 https://k8s-api.lab:6443/livez
echo
```

Expected Calico pool values:

```bash
kubectl get ippools.crd.projectcalico.org \
  default-ipv4-ippool \
  -o jsonpath='{.spec.cidr}{"\n"}{.spec.vxlanMode}{"\n"}{.spec.natOutgoing}{"\n"}'
```

Expected output:

```text
10.244.0.0/16
Always
true
```

---

## Major Problems Solved

The detailed runbooks contain the full commands and explanations. Important lessons include:

1. **The default `qemu64` CPU was too old for a modern Calico/Tigera image.**  
   The Tigera Operator failed with `Fatal glibc error: CPU does not support x86-64-v2`. Terraform was updated to use `cpu = { mode = "host-passthrough" }`.

2. **Provider syntax matters.**  
   With the installed libvirt provider, `cpu { ... }` was rejected as an unsupported block. The correct syntax is an object argument: `cpu = { ... }`.

3. **cloud-init regenerated `/etc/hosts`.**  
   The initial user-data set `manage_etc_hosts: true`. The active file was rebuilt during reboot, removing `k8s-api.lab`. Existing nodes were fixed by updating `/etc/cloud/templates/hosts.debian.tmpl`; the Terraform template was changed to `manage_etc_hosts: false` for future builds.

4. **kubeadm does not copy custom kube-vip manifests.**  
   After a new control-plane node joined, the kube-vip Ansible role had to run on that node.

5. **The kube-vip playbook initially targeted only `eph-cp01`.**  
   It was corrected to target the `control_plane` group and use `--limit` for one-node-at-a-time deployment.

6. **`--list-hosts` does not execute a playbook.**  
   It validates host selection only.

7. **Join tokens and certificate keys are secrets.**  
   Exposed credentials were revoked and replaced. No real join credential belongs in this repository.

8. **The Calico API server Pods run in `calico-system`.**  
   `calico-apiserver` is a component name, not the namespace used by this operator-managed installation.

---

## Security and Privacy

Never commit:

```text
~/.ssh/eph_k8s
/etc/kubernetes/admin.conf
/etc/kubernetes/super-admin.conf
/etc/kubernetes/pki/
/root/kubeadm-init-output.txt
/root/kubeadm-join-commands.txt
/root/kubeadm-worker-join-command.txt
terraform.tfvars
*.tfstate containing sensitive values
real application secrets
real client or employee information
```

Use placeholders in documentation:

```text
<TOKEN>
<CERTIFICATE_KEY>
<CA_CERT_HASH>
<SECRET_VALUE>
```

Recommended application controls:

- Synthetic data only.
- Namespace isolation.
- Kubernetes RBAC.
- NetworkPolicies.
- Secrets mounted only where required.
- TLS for user-facing endpoints.
- PostgreSQL authentication and least privilege.
- Audit-friendly application timestamps.
- Backups and tested recovery procedures.

---

## Git Workflow

From the repository root:

```bash
git status --short
git diff --check
git add README.md terraform/libvirt/README.md ansible/README.md
git diff --cached --check
git diff --cached --stat
git commit -m "Document HA Kubernetes platform build and troubleshooting"
git push origin main
```

Before committing, scan staged changes for obvious secrets:

```bash
git diff --cached | grep -Ei \
'BEGIN (OPENSSH|RSA|EC|DSA) PRIVATE KEY|certificate-key|token:|password:' \
&& echo "Review possible secret before committing" \
|| echo "No obvious secrets found"
```

---

## Next Recommended Work

1. Label both worker nodes.
2. Run scheduling, DNS and Pod-network smoke tests.
3. Perform a controlled kube-vip failover test.
4. Document etcd backup and restore.
5. Create the `kubernetes/` directory structure.
6. Deploy an ingress controller and persistent storage.
7. Build the first FastAPI/PostgreSQL inquiry workflow using synthetic data.
8. Add Prometheus, Grafana and Alertmanager after the application is running.

The project remains focused on one outcome: a reliable platform that can host and operate the Ever Presence Haven Service Inquiry and Referral Tracking Platform.
