A portfolio-grade infrastructure, Kubernetes, application, and observability platform designed around a fictional community-services organization called **HavenBridge Community Services**.

The project provisions a five-node Kubernetes cluster on KVM/libvirt, configures the nodes with Ansible, builds a highly available kubeadm control plane, provides application traffic routing through MetalLB and Traefik Gateway API, and delivers dynamically provisioned NFS-backed persistent storage.

The platform is being developed to host the **HavenBridge Service Inquiry and Referral Tracking Platform**.

> **Privacy rule:** only synthetic demonstration data may be used. Do not store real client, health, disability, employee, referral, or personally identifiable information in this public repository or the homelab.

> **Naming note:** the existing VM names use the `eph-` prefix because they were created earlier in the project. These internal infrastructure identifiers are retained to avoid unnecessary changes to Kubernetes node names, certificates, etcd membership, and automation inventory.

---

## Project Goal

HavenBridge Community Services is a fictional organization representing a provider of services such as home care, respite care, disability support, residential care, community access, family support, and employee resources.

The project translates that operational context into a practical platform-engineering solution:

**HavenBridge Service Inquiry and Referral Tracking Platform**

Authorized staff will eventually be able to:

* Record service inquiries and referrals.
* Select the requested service category.
* Assign an inquiry to a coordinator.
* Track statuses such as `New`, `Assigned`, `Under Review`, `Contacted`, `Awaiting Information`, and `Closed`.
* Identify overdue or unassigned inquiries.
* View basic operational dashboards.
* Receive notifications when requests exceed a defined response period.
* Access approved internal policies or employee resources.

The Kubernetes cluster is not the final product by itself. It is the highly available foundation on which the operational application, database, routing, persistent storage, monitoring, and alerting services will run.

---

## Project Story

The completed portfolio story is intended to be:

> I designed and built a highly available Kubernetes service platform for a fictional community-services organization. Terraform provisions the KVM infrastructure, Ansible configures the Linux and Kubernetes nodes, kubeadm builds a three-control-plane cluster, kube-vip provides a shared API endpoint, and Calico provides Pod networking. MetalLB and Traefik Gateway API provide application access, while the NFS CSI driver supplies dynamically provisioned persistent storage. The platform is being extended to host a service inquiry and referral tracking application with PostgreSQL, Prometheus, Grafana, and Alertmanager.

---

## Current Project Status

Phases 1–4 are complete.

Phase 5 is in progress.

Completed application-layer work:

- PostgreSQL deployed as a Kubernetes StatefulSet
- PostgreSQL persistence validated
- FastAPI backend implemented with SQLAlchemy and Psycopg
- Docker image `havenbridge-api:0.1.0` built successfully
- Image confirmed to run as the non-root `havenbridge` user
- Local Docker container connected successfully to PostgreSQL in Kubernetes
- `platform_validation` and `service_inquiries` tables confirmed

The next step is to publish the API image to a container registry and deploy it
inside Kubernetes.

## Architecture

### Application access architecture

```text
Staff user
    |
    v
havenbridge.lab
172.16.10.40
    |
    v
MetalLB Layer 2 advertisement
    |
    v
Traefik LoadBalancer Service
    |
    v
Gateway: havenbridge-gateway
    |
    v
HTTPRoute
    |
    v
HavenBridge Web Application
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

The backend application Services remain internal Kubernetes `ClusterIP` Services. They do not require separate external IP addresses because Traefik receives external traffic at `172.16.10.40` and routes requests to the appropriate internal Service.

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

The five virtual machines run on a Dell Precision 5810 host using KVM and libvirt.

The three control-plane nodes provide a stacked-etcd quorum. kube-vip exposes the shared Kubernetes API endpoint at `172.16.10.30`, while application workloads are scheduled primarily on the two worker nodes.


## End-to-End HavenBridge HTTP Request Flow

The following flow shows how an external HTTP request travels from a client on
the home-lab network through the Kubernetes platform until it reaches the
HavenBridge FastAPI application.

```text
curl http://havenbridge.lab
        |
        | DNS lookup
        v
havenbridge.lab = 172.16.10.40
        |
        | HTTP defaults to TCP/80
        v
172.16.10.40:80
        |
        | MetalLB makes this LoadBalancer IP reachable
        v
Traefik LoadBalancer Service
        |
        | Service port 80
        v
Traefik web entrypoint
        |
        | internal port 8000
        v
Gateway listener: web
        |
        | hostname = havenbridge.lab
        v
HTTPRoute
        |
        | backend = havenbridge-api:80
        v
havenbridge-api ClusterIP Service
        |
        | Service port 80
        | targetPort = http
        v
EndpointSlice
        |
        | selects a Ready API Pod endpoint
        v
HavenBridge API Pod
        |
        | container port 8000
        v
FastAPI
```

### What Each Layer Does

The request begins with the hostname:

```text
havenbridge.lab
```

which resolves to the MetalLB-provided application address:

```text
172.16.10.40
```

Because the client uses `http://` without specifying a port, it connects to the
standard HTTP port:

```text
TCP/80
```

MetalLB makes `172.16.10.40` reachable on the home-lab network and assigns that
address to the Traefik `LoadBalancer` Service.

Traefik receives the request through its externally exposed HTTP Service port
`80`. Internally, this traffic reaches Traefik's `web` entrypoint on port
`8000`.

The Gateway listener accepts HTTP traffic for:

```text
havenbridge.lab
```

The `HTTPRoute` then determines which Kubernetes backend should receive that
request. For HavenBridge, the selected backend is:

```text
havenbridge-api Service
port 80
```

The `havenbridge-api` Service provides a stable internal endpoint for the API
Pods. Its `targetPort` references the named `http` container port, which maps
to:

```text
containerPort: 8000
```

Kubernetes maintains an `EndpointSlice` containing the Ready HavenBridge API
Pod IP addresses. Only healthy, Ready application endpoints are used for
normal Service traffic.

The final request therefore reaches the FastAPI application running inside one
of the HavenBridge API Pods.

### Component Responsibilities

```text
DNS
    Resolves havenbridge.lab to 172.16.10.40.

MetalLB
    Makes the LoadBalancer address 172.16.10.40 reachable on the
    bare-metal/home-lab network.

Traefik LoadBalancer Service
    Receives external application traffic on standard ports such as
    HTTP/80 and HTTPS/443.

Traefik EntryPoint
    Provides Traefik's internal HTTP or HTTPS listening point.

Gateway
    Defines which hostnames and protocols Traefik accepts.

HTTPRoute
    Defines where accepted HTTP requests should be routed.

Kubernetes Service
    Provides a stable internal network endpoint for the API workload.

EndpointSlice
    Tracks the Ready Pod IP addresses behind the Service.

HavenBridge API Pod
    Runs the FastAPI application.

FastAPI
    Processes the actual HavenBridge application request.
```

One important detail is that Traefik and the HavenBridge API both currently use
an internal port numbered `8000`, but these are completely separate ports on
different Pods:

```text
Traefik Pod :8000
        ≠
HavenBridge API Pod :8000
```

The Gateway, HTTPRoute, Service and EndpointSlice resources connect these
separate parts of the request path.



### Building Analogy

A simple way to remember the HavenBridge request path is to think of the
platform as an office building.

```text
havenbridge.lab
= building name

172.16.10.40
= building street address

MetalLB
= makes that street address reachable

Traefik Service port 80
= public front door

Traefik web entrypoint :8000
= receptionist's internal desk

Gateway listener
= receptionist saying:
  "I accept visitors for havenbridge.lab"

HTTPRoute
= directory telling the receptionist:
  "The HavenBridge API is in this department"

havenbridge-api Service
= department's permanent extension

EndpointSlice
= list of employees currently available to take the request

API Pod
= employee actually handling the request

FastAPI
= the application doing the work
```

The request can therefore be pictured like this:

```text
Visitor asks for HavenBridge
        ↓
Looks up the building name
        ↓
Finds the street address
172.16.10.40
        ↓
Enters through the public front door
Traefik Service
        ↓
Speaks to the receptionist
Traefik entrypoint / Gateway
        ↓
Receptionist checks the directory
HTTPRoute
        ↓
Calls the department's permanent extension
havenbridge-api Service
        ↓
Finds an available employee
EndpointSlice
        ↓
Employee handles the request
API Pod
        ↓
FastAPI performs the application work
```

This analogy maps directly to the Kubernetes architecture, but the actual
networking components still perform their specific technical roles described
in the request-flow section above.





### Persistent storage architecture

```text
Application Pod
    |
    v
PersistentVolumeClaim
    |
    v
StorageClass: havenbridge-nfs
    |
    v
NFS CSI Driver
    |
    v
NFS server: 172.16.10.1
    |
    v
syrus:/data_all/havenbridge-nfs
```

The `havenbridge-nfs` StorageClass supports dynamic provisioning. Applications create a PersistentVolumeClaim without requiring an administrator to create a matching PersistentVolume manually.

The NFS CSI provisioner creates the PersistentVolume and its backing NFS subdirectory automatically.

---

## Current Cluster Topology

| Node           |     IP address | Role                 | vCPU | Memory |   Disk |
| -------------- | -------------: | -------------------- | ---: | -----: | -----: |
| `eph-cp01`     | `172.16.10.31` | Control plane + etcd |    2 |  4 GiB | 40 GiB |
| `eph-cp02`     | `172.16.10.32` | Control plane + etcd |    2 |  4 GiB | 40 GiB |
| `eph-cp03`     | `172.16.10.33` | Control plane + etcd |    2 |  4 GiB | 40 GiB |
| `eph-worker01` | `172.16.10.34` | Worker               |    2 |  8 GiB | 60 GiB |
| `eph-worker02` | `172.16.10.35` | Worker               |    2 |  8 GiB | 60 GiB |
| Reserved       | `172.16.10.36` | Future worker        |  TBD |    TBD |    TBD |

Network and platform configuration:

| Purpose                        | Value                       |
| ------------------------------ | --------------------------- |
| Libvirt node network           | `172.16.10.0/24`            |
| Libvirt gateway and NFS server | `172.16.10.1`               |
| Kubernetes API DNS name        | `k8s-api.lab`               |
| kube-vip virtual IP            | `172.16.10.30/32`           |
| Kubernetes API port            | `6443`                      |
| Application hostname           | `havenbridge.lab`           |
| MetalLB application IP         | `172.16.10.40`              |
| Pod network                    | `10.244.0.0/16`             |
| Service network                | `10.96.0.0/12`              |
| Calico encapsulation           | VXLAN                       |
| NFS export                     | `/data_all/havenbridge-nfs` |
| Default StorageClass           | `havenbridge-nfs`           |
| SSH user                       | `mino`                      |

The application IP and Kubernetes API IP serve different purposes:

| Address        | Purpose                                              |
| -------------- | ---------------------------------------------------- |
| `172.16.10.30` | Shared Kubernetes API endpoint provided by kube-vip  |
| `172.16.10.40` | Application LoadBalancer address provided by MetalLB |

---

## Technology Stack

### Infrastructure

* Ubuntu 24.04 host
* Dell Precision 5810
* KVM, QEMU and libvirt
* QCOW2 virtual disks
* cloud-init
* Terraform
* `dmacvicar/libvirt` provider

### Configuration and Kubernetes

* Ansible
* Ubuntu 24.04.4 LTS guests
* Kubernetes v1.36.2
* kubeadm, kubelet and kubectl
* CRI-O v1.36.2
* kube-vip v1.2.1
* Calico v3.32.1
* Tigera Operator
* Calico API server
* Three-member stacked etcd

### Platform services

* Helm
* MetalLB v0.16.1
* Kubernetes Gateway API
* Traefik Helm chart v41.0.2
* Traefik Proxy v3.7.6
* NFS server
* NFS CSI Driver v4.13.4
* Dynamic PersistentVolume provisioning
* `ReadWriteMany` shared storage

### Planned application and operations

* Python FastAPI backend
* Web frontend
* PostgreSQL
* Notification worker
* ConfigMaps and Secrets
* NetworkPolicies
* Kubernetes RBAC
* TLS
* Prometheus
* Grafana
* Alertmanager
* Application metrics and alert rules

---

## Repository Layout

```text
havenbridge-ha-service-platform/
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
│   │   └── install_nfs_clients.yml
│   └── roles/
└── kubernetes/
    ├── platform/
    │   ├── metallb/
    │   │   ├── values.yaml
    │   │   └── l2-address-pool.yaml
    │   ├── traefik/
    │   │   └── values.yaml
    │   ├── gateway/
    │   │   └── nginx-validation-route.yaml
    │   └── storage/
    │       └── nfs-storageclass.yaml
    ├── applications/
    │   └── havenbridge/
    └── monitoring/
```

`terraform.tfvars`, private keys, kubeconfig files, join commands, tokens, certificate keys, application secrets, real client information, and other sensitive files must never be committed.

---

## Completed Milestones

### Infrastructure

* [x] Created a dedicated libvirt storage pool.
* [x] Imported an Ubuntu cloud image.
* [x] Provisioned five persistent QCOW2 VM disks.
* [x] Generated cloud-init seed images.
* [x] Created three control-plane VMs and two worker VMs.
* [x] Assigned deterministic MAC addresses and static node IPs.
* [x] Enabled QEMU guest agent support.
* [x] Changed the VM CPU model from `qemu64` to `host-passthrough`.
* [x] Confirmed Terraform can update the domains in place without destroying disks.

### Node configuration

* [x] Completed Ansible connectivity and preflight validation.
* [x] Disabled swap.
* [x] Loaded `overlay` and `br_netfilter`.
* [x] Applied Kubernetes networking sysctl settings.
* [x] Installed and configured CRI-O.
* [x] Installed kubeadm, kubelet and kubectl v1.36.2.
* [x] Held Kubernetes packages at the selected version.
* [x] Configured persistent resolution for `k8s-api.lab`.
* [x] Configured the CRI-O pause image expected by kubeadm.
* [x] Installed `nfs-common` on all control-plane and worker nodes.

### Kubernetes cluster

* [x] Initialized `eph-cp01`.
* [x] Configured a three-member stacked-etcd control plane.
* [x] Joined `eph-cp02` and `eph-cp03`.
* [x] Joined `eph-worker01` and `eph-worker02`.
* [x] Deployed kube-vip on all three control-plane nodes.
* [x] Confirmed the shared API endpoint returns `ok`.
* [x] Installed Calico using the Tigera Operator.
* [x] Configured `10.244.0.0/16`, VXLAN, outbound NAT and `NodeInternalIP` detection.
* [x] Deployed the Calico API server.
* [x] Confirmed all TigeraStatus resources are available.
* [x] Confirmed all five Kubernetes nodes are `Ready`.
* [x] Confirmed cluster resources persisted after all VMs were rebooted.

### Application routing

* [x] Installed Helm.
* [x] Installed MetalLB in Layer 2 mode.
* [x] Created the `havenbridge-application-pool`.
* [x] Reserved `172.16.10.40` for application traffic.
* [x] Verified MetalLB ARP advertisement from `eph-worker01`.
* [x] Verified TCP connectivity to port 80.
* [x] Verified an nginx LoadBalancer Service returned `HTTP 200`.
* [x] Installed the standard Kubernetes Gateway API CRDs.
* [x] Installed Traefik with two replicas.
* [x] Created a Traefik PodDisruptionBudget.
* [x] Created the `traefik` GatewayClass.
* [x] Created `havenbridge-gateway`.
* [x] Created a cross-namespace HTTPRoute.
* [x] Confirmed the Gateway reports `Programmed=True`.
* [x] Confirmed the listener reports one attached route.
* [x] Confirmed the route reports `Accepted=True`.
* [x] Confirmed the route reports `ResolvedRefs=True`.
* [x] Configured `havenbridge.lab` to resolve to `172.16.10.40`.
* [x] Confirmed `http://havenbridge.lab` returns `HTTP 200`.

### Persistent storage

* [x] Installed and configured the NFS server on `syrus`.
* [x] Exported `/data_all/havenbridge-nfs` to `172.16.10.0/24`.
* [x] Confirmed the export was visible from control-plane and worker nodes.
* [x] Completed a manual NFS mount and write test.
* [x] Installed NFS CSI Driver v4.13.4.
* [x] Confirmed the CSI controller is healthy.
* [x] Confirmed one CSI node Pod runs on every Kubernetes node.
* [x] Registered `nfs.csi.k8s.io` with Kubernetes.
* [x] Created the default `havenbridge-nfs` StorageClass.
* [x] Enabled dynamic PersistentVolume provisioning.
* [x] Created a `ReadWriteMany` test PVC.
* [x] Confirmed Kubernetes automatically created the matching PV.
* [x] Wrote data from a Pod on `eph-worker01`.
* [x] Deleted the writer Pod without deleting the PVC.
* [x] Mounted the same PVC from a reader Pod on `eph-worker02`.
* [x] Confirmed the original data remained available.

Cross-node persistence evidence:

```text
Written by Pod nfs-writer on node eph-worker01 at Sun Jul 26 18:45:47 UTC 2026
```

The reader Pod running on `eph-worker02` successfully retrieved that file from the original PersistentVolumeClaim.

---

## Project Phases

### Phase 1 — Infrastructure as Code

**Status: completed**

Terraform provisions:

* Libvirt storage.
* Ubuntu cloud image.
* Persistent VM disks.
* Cloud-init media.
* Network interfaces.
* Virtual machine domains.
* CPU and memory configuration.
* Deterministic MAC addresses.

Detailed instructions and troubleshooting:

* [`terraform/libvirt/README.md`](terraform/libvirt/README.md)

### Phase 2 — Configuration and Kubernetes Bootstrap

**Status: completed**

Ansible prepares the operating system, installs CRI-O and Kubernetes packages, configures the shared API endpoint, prepares kube-vip, installs NFS clients, and supports the kubeadm bootstrap process.

Detailed instructions and troubleshooting:

* [`ansible/README.md`](ansible/README.md)

### Phase 3 — Cluster Validation

**Status: core validation completed; failure testing deferred**

Completed:

* [x] Confirmed all five nodes are `Ready`.
* [x] Tested workload scheduling on both workers.
* [x] Tested Kubernetes Service access.
* [x] Tested the kube-vip shared API endpoint.
* [x] Validated the Calico IP pool and VXLAN configuration.
* [x] Validated CoreDNS and application Service routing.
* [x] Validated cluster persistence after VM reboots.

Deferred resilience tests:

* [ ] Add optional worker-role labels.
* [ ] Perform a controlled kube-vip failover test.
* [ ] Simulate one control-plane outage.
* [ ] Confirm API availability during a control-plane outage.
* [ ] Confirm etcd quorum with one member unavailable.
* [ ] Simulate worker-node loss and verify workload rescheduling.
* [ ] Create an etcd backup and recovery runbook.
* [ ] Test etcd restore procedures.

### Phase 4 — Platform Services

**Status: application routing and persistent storage completed**

Completed:

* [x] Install Helm.
* [x] Install MetalLB.
* [x] Reserve an application LoadBalancer IP.
* [x] Install Gateway API CRDs.
* [x] Install Traefik.
* [x] Run two Traefik replicas.
* [x] Define the `havenbridge.lab` application hostname.
* [x] Create a Gateway and HTTPRoute.
* [x] Validate hostname-based application routing.
* [x] Configure NFS-backed shared storage.
* [x] Install the NFS CSI driver.
* [x] Create a default StorageClass.
* [x] Validate dynamic PV provisioning.
* [x] Validate cross-node data persistence.

Remaining platform work:

* [ ] Configure TLS for `havenbridge.lab`.
* [ ] Create application namespaces.
* [ ] Establish ConfigMap and Secret handling.
* [ ] Add NetworkPolicies.
* [ ] Add application-specific RBAC.
* [ ] Define resource quotas and limit ranges where appropriate.

### Phase 5 — Inquiry and Referral Tracking Application

**Status: in progress**

Completed:

- [x] Deploy PostgreSQL
- [x] Validate PostgreSQL persistence
- [x] Implement the FastAPI backend
- [x] Add SQLAlchemy and Psycopg connectivity
- [x] Build `havenbridge-api:0.1.0`
- [x] Confirm the image runs as a non-root user
- [x] Validate the API container against PostgreSQL
- [x] Confirm the application database tables

Remaining:

- [ ] Publish the API image
- [ ] Deploy the API to Kubernetes
- [ ] Create the API Service
- [ ] Configure Kubernetes Secrets and ConfigMaps
- [ ] Add readiness and liveness probes
- [ ] Add resource requests and limits
- [ ] Create the Gateway API route
- [ ] Build the frontend
- [ ] Add the notification worker

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

Planned application components:

```text
Frontend
Backend API
PostgreSQL
Notification/SLA worker
Synthetic seed data
```

Application deployment will include:

* Dedicated namespace.
* PostgreSQL with an NFS-backed PersistentVolumeClaim.
* Backend API Deployment and Service.
* Frontend Deployment and Service.
* Notification worker.
* ConfigMaps.
* Kubernetes Secrets.
* Readiness and liveness probes.
* Resource requests and limits.
* PodDisruptionBudgets where meaningful.
* Gateway API HTTPRoutes.
* NetworkPolicies.
* Application-specific RBAC.
* HorizontalPodAutoscaler where meaningful.

### Phase 6 — Monitoring and Alerting

This phase remains inside the project scope because it provides operational visibility for both the Kubernetes platform and the inquiry application.

Planned components:

* Prometheus
* Grafana
* Alertmanager
* kube-state-metrics
* Node Exporter
* Prometheus Operator
* ServiceMonitor or PodMonitor resources
* PrometheusRule resources
* Application dashboards

Cluster alerts:

* Node unavailable
* Pod crash looping
* Deployment replicas unavailable
* High CPU or memory usage
* Low disk space
* PersistentVolume capacity risk
* Kubernetes API unavailable
* etcd member unhealthy
* NFS server unavailable

Application alerts:

* Application endpoint unavailable
* API error rate above threshold
* High response latency
* PostgreSQL unavailable
* Notification worker failed
* Inquiry unassigned beyond the response target
* Inquiry under review beyond the service-level target

Only synthetic inquiry data will be used during testing.

---

## High-Level Validation Commands

### Kubernetes and Calico

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

### MetalLB and Traefik

```bash
kubectl get ipaddresspools.metallb.io \
  -n metallb-system

kubectl get l2advertisements.metallb.io \
  -n metallb-system

kubectl get pods \
  -n metallb-system \
  -o wide

kubectl get pods,svc \
  -n traefik \
  -o wide

kubectl get gatewayclass
kubectl get gateway -n traefik
kubectl get httproute -A
```

Validate the application route:

```bash
curl -sS \
  --max-time 10 \
  -D - \
  -o /dev/null \
  http://havenbridge.lab/
```

Expected response:

```text
HTTP/1.1 200 OK
Server: nginx/1.30.4
```

### NFS and persistent storage

```bash
kubectl get csidriver nfs.csi.k8s.io
kubectl get storageclass
kubectl get pvc -A
kubectl get pv
```

Validate the persistence test:

```bash
kubectl get pod nfs-reader \
  -n platform-validation \
  -o wide

kubectl exec \
  -n platform-validation \
  nfs-reader \
  -- cat /data/persistence-proof.txt
```

---

## Major Problems Solved

The detailed runbooks contain the complete commands and explanations. Important lessons include:

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

6. **`--list-hosts` does not execute an Ansible playbook.**
   It validates host selection only.

7. **Join tokens and certificate keys are secrets.**
   Exposed credentials were revoked and replaced. No real join credential belongs in this repository.

8. **The Calico API server Pods run in `calico-system`.**
   `calico-apiserver` is a component name, not the namespace used by this operator-managed installation.

9. **Calico's Gateway API resource is not the standard Kubernetes Gateway API.**
   `gatewayapis.operator.tigera.io` belongs to the Tigera Operator. The standard `gateway.networking.k8s.io` CRDs had to be installed separately.

10. **Traefik chart v41 rejected the previous logging key.**
    The values schema uses `log.level` and `accessLog.enabled`, not the older top-level `logs` configuration.

11. **Local Helm rendering initially selected a removed PodDisruptionBudget API version.**
    Supplying `--api-versions policy/v1/PodDisruptionBudget` produced the correct `policy/v1` resource during local validation. The live Helm installation detected the supported API automatically.

12. **A ClusterIP Service normally has no external IP.**
    The application Service remains internal. Traefik owns the MetalLB address and forwards requests to the ClusterIP Service.

13. **`showmount` does not mount an NFS export.**
    It only lists exports available from the server. A client must mount the export before its files become visible.

14. **The same-looking path on two Linux machines is not automatically shared.**
    `/data_all/havenbridge-nfs` exists on `syrus`. Kubernetes nodes access it through an NFS mount, not through a matching local directory.

15. **A StorageClass can create PersistentVolumes dynamically.**
    A manual PV was not required. The PVC requested the `havenbridge-nfs` StorageClass, and the NFS CSI provisioner created the PV automatically.

16. **A container hostname normally identifies the Pod, not the Kubernetes node.**
    The writer Pod used the Downward API field `spec.nodeName` to record that it was running on `eph-worker01`.

17. **Persistent application data must be separated from the Pod lifecycle.**
    The writer Pod was deleted, but its PVC remained. A new Pod on another worker mounted the same volume and retrieved the original data.

---

## Current Availability Boundaries

The project currently provides redundancy across:

* Three Kubernetes control-plane nodes.
* Three etcd members.
* kube-vip static Pods on all control-plane nodes.
* MetalLB speaker Pods on all Kubernetes nodes.
* Two Traefik replicas on separate worker nodes.
* Application Pods that can be recreated or rescheduled.

The NFS server remains a single point of failure because it runs on the physical host `syrus`.

If `syrus` is unavailable:

* The virtual machines are unavailable because they run on that host.
* The NFS export is unavailable.
* NFS-backed application storage cannot be mounted.

The current NFS design was selected because it is simple, resource-efficient, easy to understand, and supports `ReadWriteMany` in the homelab.

A production implementation could replace it with:

* Longhorn
* Rook-Ceph
* A managed cloud block-storage service
* A managed cloud file-storage service
* A dedicated highly available NFS platform

---

The HavenBridge platform provides redundancy between Kubernetes virtual
machines:

- Three control-plane virtual machines
- Three stacked-etcd members
- kube-vip on all control-plane nodes
- MetalLB speakers across the Kubernetes nodes
- Two Traefik replicas on separate worker virtual machines

However, this is not yet physical-host high availability.

The physical host `syrus` currently provides both:

1. The KVM/libvirt environment hosting all Kubernetes virtual machines
2. The NFS server providing persistent storage to the cluster

### NFS service or export failure

If `syrus` remains operational but the NFS service, export, disk mount or NFS
network path fails:

- The Kubernetes control plane may remain available
- Stateless workloads may continue running
- PostgreSQL and other NFS-backed workloads may become unavailable
- Pods may report `FailedMount`, I/O or readiness errors
- Existing PVCs and PVs should be preserved

The recovery approach is to restore `/data_all`, the NFS service, the original
export and the same NFS server address before restarting affected workloads.

### Complete Syrus host failure

If the physical `syrus` host fails:

- All Kubernetes virtual machines stop
- The Kubernetes API becomes unavailable
- etcd quorum becomes unavailable
- MetalLB and Traefik stop
- PostgreSQL and application workloads stop
- The NFS export becomes unavailable
- The entire HavenBridge homelab platform becomes unavailable

Although the cluster has three control-plane virtual machines, all three share
the same physical failure domain.

### Resilience approach

Short-term improvements:

- Protect `syrus` with a UPS
- Monitor host availability, disk health, capacity and NFS availability
- Create scheduled PostgreSQL logical backups with `pg_dump`
- Create scheduled etcd snapshots
- Copy backups to a separate physical device or remote host
- Test backup restoration procedures

Medium-term improvements:

- Move NFS to a dedicated NAS or second Linux host
- Replicate important storage data to a standby system
- Document an active/passive recovery process
- Keep backups independent of the primary NFS host

Long-term improvements:

- Run Kubernetes nodes across separate physical hosts
- Use Longhorn, Rook-Ceph, highly available NFS or managed cloud storage
- Place storage replicas in separate physical failure domains

Running Longhorn or Rook-Ceph only inside virtual machines hosted by `syrus`
would not protect the platform from a complete `syrus` failure.

Detailed recovery procedures are documented in:

- [NFS Storage Design and Recovery](kubernetes/platform/storage/README.md)

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

* Synthetic data only.
* Namespace isolation.
* Kubernetes RBAC.
* NetworkPolicies.
* Secrets mounted only where required.
* TLS for user-facing endpoints.
* PostgreSQL authentication and least privilege.
* Audit-friendly application timestamps.
* Backups and tested recovery procedures.

The NFS export currently uses homelab-oriented permissions to support dynamic provisioning. The directory should not be left world-writable with `0777`, and the use of `no_root_squash` must be treated as a deliberate lab simplification rather than a production recommendation.

---

## Git Workflow

From the repository root:

```bash
git status --short
git diff --check
git add README.md
git diff --cached --check
git diff --cached --stat
git commit -m "Document platform routing and persistent storage"
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

1. Save the storage validation manifests and evidence in the repository.
2. Clean up the temporary writer and reader Pods when the evidence has been recorded.
3. Create the HavenBridge application namespace.
4. Define application ConfigMaps and Secrets.
5. Deploy PostgreSQL with an NFS-backed PersistentVolumeClaim.
6. Validate PostgreSQL data persistence.
7. Build and deploy the FastAPI backend.
8. Build and deploy the web frontend.
9. Replace the nginx validation route with HavenBridge application routes.
10. Add the notification worker.
11. Add NetworkPolicies and application-specific RBAC.
12. Configure TLS.
13. Add Prometheus, Grafana and Alertmanager.
14. Return to the deferred kube-vip, worker-loss, control-plane-loss, and etcd-quorum tests.

---

## Planned Project Presentation Documents

At the completion of the project, supporting presentation and interview material will be created, including:

* Architecture overview.
* Implementation summary.
* Technology decision record.
* Troubleshooting and lessons-learned document.
* Project presentation talking points.
* Likely technical questions and model answers.
* Explanation of why each major technology was selected.
* Five-minute project presentation script.
* Fifteen-minute technical walkthrough.
* Resume-ready project description.

Topics will include:

* Why Terraform was used.
* Why Ansible was used.
* Why three control-plane nodes were selected.
* Why kube-vip was required.
* Why Calico was selected.
* Why MetalLB was needed.
* Why Traefik and Gateway API were used.
* Why backend Services remain ClusterIP.
* Why a StorageClass was required.
* Why NFS was selected for the homelab.
* How dynamic PV provisioning works.
* How PVC data survives Pod deletion.
* The current availability limitations.
* How the design would change in production.

---

The project remains focused on one outcome: building a reliable, explainable, and portfolio-ready platform capable of hosting and operating the HavenBridge Service Inquiry and Referral Tracking Platform.
