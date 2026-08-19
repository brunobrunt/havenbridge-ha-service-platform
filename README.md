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

The completed portfolio story is intended to be:

> I designed and built a highly available Kubernetes service platform for a fictional community-services organization. Terraform provisions the KVM infrastructure, Ansible configures the Linux and Kubernetes nodes, kubeadm builds a three-control-plane cluster, kube-vip provides a shared API endpoint, and Calico provides Pod networking. MetalLB and Traefik Gateway API provide application access, while the NFS CSI driver supplies dynamically provisioned persistent storage. The platform is being extended to host a service inquiry and referral tracking application with PostgreSQL, Prometheus, Grafana, and Alertmanager.

---

## Project Story

The HavenBridge portfolio story is:

> I designed and built a highly available Kubernetes service platform for a
> fictional community-services organization. Terraform provisions the KVM and
> libvirt infrastructure, Ansible configures the Linux and Kubernetes nodes,
> and kubeadm builds a three-control-plane Kubernetes cluster. kube-vip
> provides a shared Kubernetes API endpoint, while Calico provides Pod
> networking and NetworkPolicy enforcement.
>
> MetalLB provides a bare-metal application LoadBalancer address, and Traefik
> with Kubernetes Gateway API provides HTTP and HTTPS application routing.
> cert-manager and a private HavenBridge PKI provide TLS for
> `havenbridge.lab`.
>
> The platform hosts a FastAPI service-inquiry backend running across two
> Kubernetes worker nodes and a PostgreSQL StatefulSet using dynamically
> provisioned NFS-backed persistent storage. The application includes health
> probes, topology-spread controls, a PodDisruptionBudget, least-privilege
> NetworkPolicies, non-root container security and HTTP-to-HTTPS redirection.
>
> The next major platform capability will be CI/CD automation using GitHub
> Actions, followed by observability with Prometheus, Grafana and Alertmanager
> and further application functionality.


---

## Current Project Status

The core HavenBridge Kubernetes platform and the first production-style
application deployment are operational.

### Infrastructure and Kubernetes

Completed:

- KVM/libvirt virtual infrastructure provisioned
- Linux hosts configured through Ansible
- Three-control-plane Kubernetes cluster operational
- Two Kubernetes worker nodes operational
- kube-vip providing the shared Kubernetes API VIP
- Calico providing Pod networking
- Calico NetworkPolicy enforcement validated

### Platform Networking

Completed:

- MetalLB installed and configured
- Application LoadBalancer IP assigned as `172.16.10.40`
- `havenbridge.lab` resolves to `172.16.10.40`
- Traefik deployed with two replicas
- Kubernetes Gateway API enabled
- `havenbridge-gateway` programmed successfully
- HTTP `web` entrypoint configured
- HTTPS `websecure` entrypoint configured

### Persistent Storage and PostgreSQL

Completed:

- NFS-backed dynamic storage provisioning
- `havenbridge-nfs` StorageClass configured
- PostgreSQL deployed using a StatefulSet
- PostgreSQL PVC and PersistentVolume binding validated
- PostgreSQL persistence validated through Pod recreation
- Database data confirmed to survive PostgreSQL Pod replacement

### HavenBridge FastAPI Backend

Completed:

- FastAPI backend implemented
- SQLAlchemy and Psycopg PostgreSQL integration implemented
- Docker image built and validated
- Container confirmed to run as a non-root user
- Image published to GitHub Container Registry as:

```text
ghcr.io/brunobrunt/havenbridge-api:0.1.0
```

- API deployed into the `havenbridge` Kubernetes namespace
- Two API replicas running across separate worker nodes
- Readiness and liveness probes validated
- Kubernetes Service and EndpointSlice routing validated
- PostgreSQL connectivity validated
- `platform_validation` and `service_inquiries` database tables confirmed

### Backend Availability and Security

Completed and validated:

- Deployment self-healing after controlled Pod deletion
- Replica distribution across separate worker nodes
- PodDisruptionBudget
- Controlled node-drain validation
- Continuous application availability during voluntary disruption
- Least-privilege Kubernetes NetworkPolicies
- Traefik-to-API ingress restriction
- API-to-PostgreSQL egress restriction
- PostgreSQL ingress restriction
- Unauthorized Pod traffic blocked

The final allowed application communication model is:

```text
External Client
        ↓
MetalLB
        ↓
Traefik
        ↓
HavenBridge API
        ↓
PostgreSQL
```

Kubernetes DNS is separately permitted for the API through CoreDNS.

### TLS and HTTPS

Completed and validated:

- cert-manager installed
- HavenBridge private Root CA created
- HavenBridge CA ClusterIssuer created
- `havenbridge.lab` server certificate issued
- Kubernetes TLS Secret `havenbridge-tls` created
- Traefik HTTPS listener configured
- TLS termination configured at Traefik
- HTTP-to-HTTPS redirect configured
- End-to-end HTTPS access validated

The final external behavior is:

```text
http://havenbridge.lab
        ↓
301 Moved Permanently
        ↓
https://havenbridge.lab
        ↓
TLS
        ↓
Traefik
        ↓
Gateway API
        ↓
HTTPRoute
        ↓
havenbridge-api Service
        ↓
Ready FastAPI Pod
```

The readiness endpoint has been validated as:

```text
https://havenbridge.lab/health/ready
```

with:

```text
HTTP/2 200
{"status":"ready"}
```

### Current Development Position

Completed major capabilities:

```text
Infrastructure provisioning          ✅
Linux configuration                  ✅
HA Kubernetes control plane          ✅
Calico networking                    ✅
MetalLB                              ✅
Traefik and Gateway API              ✅
NFS persistent storage               ✅
PostgreSQL                           ✅
FastAPI backend                      ✅
GitHub Container Registry            ✅
Kubernetes application deployment    ✅
Application HA controls              ✅
NetworkPolicy security               ✅
Private PKI                          ✅
TLS / HTTPS                          ✅
HTTP → HTTPS redirect                ✅
```

The next major phase is CI/CD deployment automation, followed by observability
with Prometheus, Grafana and Alertmanager.

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

The basic idea was: the Kubernetes API needed one stable address that would not depend on any single control-plane VM.

The five virtual machines run on a Dell Precision 5810 host using KVM and libvirt.

The three control-plane nodes provide a stacked-etcd quorum. kube-vip exposes the shared Kubernetes API endpoint at `172.16.10.30`, while application workloads are scheduled primarily on the two worker nodes.


## End-to-End HavenBridge HTTP and HTTPS Request Flow

HavenBridge now uses HTTPS as the application-serving path.

Plain HTTP remains available only to redirect clients to HTTPS.

The application hostname is:

```text
havenbridge.lab
```

which resolves to:

```text
172.16.10.40
```

The address `172.16.10.40` is provided by MetalLB and assigned to the Traefik
`LoadBalancer` Service.

### HTTP Request Flow

If a client requests:

```text
http://havenbridge.lab/health/ready
```

the request follows this path:

```text
Client
        |
        | HTTP
        v
havenbridge.lab
        |
        | DNS lookup
        v
172.16.10.40
        |
        | TCP/80
        v
MetalLB
        |
        v
Traefik LoadBalancer Service :80
        |
        | targetPort = web
        v
Traefik web entrypoint :8000
        |
        v
Gateway listener: web
        |
        v
havenbridge-http-redirect HTTPRoute
        |
        | 301 Moved Permanently
        v
https://havenbridge.lab/health/ready
```

The HTTP listener therefore does not serve the HavenBridge application
directly.

Its purpose is to move clients to the secure HTTPS endpoint.

The redirect was validated as:

```text
HTTP/1.1 301 Moved Permanently
Location: https://havenbridge.lab/health/ready
```

### HTTPS Request Flow

The secure application path begins when the client connects to:

```text
https://havenbridge.lab/health/ready
```

The complete request flow is:

```text
Client
        |
        | HTTPS
        v
havenbridge.lab
        |
        | DNS lookup
        v
172.16.10.40
        |
        | TCP/443
        v
MetalLB
        |
        v
Traefik LoadBalancer Service :443
        |
        | targetPort = websecure
        v
Traefik websecure entrypoint :8443
        |
        v
Gateway listener: websecure
        |
        | TLS certificate:
        | havenbridge.lab
        |
        | TLS Secret:
        | havenbridge-tls
        v
TLS termination at Traefik
        |
        v
havenbridge-api HTTPRoute
        |
        | backend:
        | havenbridge-api:80
        v
havenbridge-api ClusterIP Service
        |
        | Service port 80
        | targetPort = http
        v
EndpointSlice
        |
        | selects a Ready API endpoint
        v
HavenBridge API Pod
        |
        | container port 8000
        v
FastAPI
        |
        v
PostgreSQL Service
        |
        | TCP/5432
        v
PostgreSQL StatefulSet
        |
        v
NFS-backed persistent storage
```

### Port Mapping

The external and internal Traefik ports are:

```text
HTTP
80 → web:8000

HTTPS
443 → websecure:8443
```

Port `80` and port `443` are the public Service ports used by clients.

Ports `8000` and `8443` are the internal Traefik entrypoint ports.

The HavenBridge API has a separate port mapping:

```text
havenbridge-api Service :80
        ↓
targetPort: http
        ↓
FastAPI container :8000
```

Although both Traefik and FastAPI use an internal port numbered `8000`, these
ports belong to different Pods and perform different jobs.

### What Each Major Layer Does

```text
DNS
= resolves havenbridge.lab to 172.16.10.40

MetalLB
= makes 172.16.10.40 reachable on the bare-metal network

Traefik
= receives HTTP and HTTPS application traffic

Gateway
= defines the HTTP and HTTPS entry points

HTTPRoute
= determines what should happen to a matching request

HTTP redirect route
= redirects HTTP clients to HTTPS

TLS
= encrypts client-to-Traefik communication

havenbridge-api Service
= provides a stable backend destination

EndpointSlice
= tracks the currently Ready API Pod endpoints

FastAPI Pod
= handles the application request

PostgreSQL
= provides persistent application data
```

### TLS Termination

TLS terminates at Traefik.

This means:

```text
Client
        |
        | encrypted HTTPS
        v
Traefik
        |
        | TLS decrypted here
        v
Internal Kubernetes routing
        |
        v
HavenBridge API
```

Traefik presents the certificate for:

```text
havenbridge.lab
```

using the Kubernetes TLS Secret:

```text
havenbridge-tls
```

The certificate was issued through the HavenBridge private PKI managed by
cert-manager.

### Final Validation

HTTP redirection was validated successfully:

```text
HTTP/1.1 301 Moved Permanently
Location: https://havenbridge.lab/health/ready
```

Following the redirect produced:

```text
Final URL: https://havenbridge.lab/health/ready
HTTP Code: 200
Redirects: 1
```

Direct HTTPS validation returned:

```text
HTTP/2 200
{"status":"ready"}
```

The final external application behavior is therefore:

```text
HTTP
 ↓
301 redirect
 ↓
HTTPS
 ↓
TLS
 ↓
Traefik
 ↓
Gateway API
 ↓
HTTPRoute
 ↓
Service
 ↓
EndpointSlice
 ↓
Ready FastAPI Pod
 ↓
PostgreSQL
```

Detailed traffic-routing documentation is available in:

```text
kubernetes/platform/traefik/README.md
```

Detailed TLS, cert-manager and private-PKI documentation is available in:

```text
kubernetes/platform/tls/README.md
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
- [x] Confirmed the initial HTTP-only route returned `HTTP 200` before TLS was introduced.
- [x] Added the Traefik `websecure` HTTPS entrypoint.
- [x] Configured the Gateway HTTPS listener for `havenbridge.lab`.
- [x] Configured TLS termination at Traefik.
- [x] Created a dedicated HTTP-to-HTTPS redirect HTTPRoute.
- [x] Confirmed HTTP returns `301 Moved Permanently`.
- [x] Confirmed the redirect points to `https://havenbridge.lab`.
- [x] Confirmed the HTTPS route returns `HTTP/2 200`.


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

### PostgreSQL

- [x] Deployed PostgreSQL as a Kubernetes StatefulSet.
- [x] Configured PostgreSQL to use the `havenbridge-nfs` StorageClass.
- [x] Confirmed the PostgreSQL PVC is `Bound`.
- [x] Confirmed the dynamically provisioned PersistentVolume is available.
- [x] Confirmed PostgreSQL runs as `havenbridge_admin` against the `havenbridge` database.
- [x] Created and validated the `platform_validation` table.
- [x] Created and validated the `service_inquiries` table.
- [x] Deleted and recreated the PostgreSQL Pod.
- [x] Confirmed the replacement Pod received a new UID.
- [x] Confirmed the existing PVC and PV were reused.
- [x] Confirmed database records survived Pod replacement.

Validated persistence flow:

```text
PostgreSQL StatefulSet
        ↓
volumeClaimTemplates
        ↓
PersistentVolumeClaim
        ↓
havenbridge-nfs StorageClass
        ↓
NFS-backed PersistentVolume
        ↓
database data survives Pod replacement
```

### HavenBridge API and Container Registry

- [x] Implemented the HavenBridge FastAPI backend.
- [x] Integrated SQLAlchemy and Psycopg with PostgreSQL.
- [x] Added readiness and liveness endpoints.
- [x] Built Docker image `havenbridge-api:0.1.0`.
- [x] Confirmed the image runs as the non-root `havenbridge` user.
- [x] Validated the container against PostgreSQL before Kubernetes deployment.
- [x] Published the image to GitHub Container Registry.
- [x] Deployed:

```text
ghcr.io/brunobrunt/havenbridge-api:0.1.0
```

- [x] Deployed the API into the `havenbridge` Kubernetes namespace.
- [x] Created the `havenbridge-api` ClusterIP Service.
- [x] Validated Kubernetes DNS resolution for the Service.
- [x] Validated Service-to-Pod routing through EndpointSlices.
- [x] Confirmed readiness and liveness probes return HTTP `200`.

### Backend High Availability

- [x] Scaled the HavenBridge API to two replicas.
- [x] Distributed the replicas across `eph-worker01` and `eph-worker02`.
- [x] Implemented topology-spread constraints.
- [x] Configured the Deployment rolling-update strategy for the two-worker topology.
- [x] Performed a controlled API Pod deletion.
- [x] Confirmed Kubernetes automatically created a replacement Pod.
- [x] Confirmed EndpointSlices automatically replaced the old Pod endpoint.
- [x] Confirmed the remaining API replica continued serving traffic.
- [x] Created a HavenBridge API PodDisruptionBudget.
- [x] Performed a controlled worker-node drain.
- [x] Confirmed the PDB allowed only one voluntary API disruption.
- [x] Confirmed continuous application availability during the drain.
- [x] Uncordoned the worker and confirmed the second replica recovered.

Validated self-healing flow:

```text
API Pod deleted
        ↓
Deployment detects missing replica
        ↓
remaining Ready Pod continues serving
        ↓
replacement Pod created
        ↓
readiness succeeds
        ↓
EndpointSlice updated
        ↓
two Ready replicas restored
```

### NetworkPolicy Security

- [x] Implemented Traefik-to-API ingress restrictions.
- [x] Confirmed Traefik can reach the API on TCP/8000.
- [x] Confirmed an unauthorized Pod cannot directly reach the API.
- [x] Implemented API egress restrictions.
- [x] Allowed CoreDNS on UDP/53 and TCP/53.
- [x] Allowed API-to-PostgreSQL traffic on TCP/5432.
- [x] Confirmed unapproved API egress is blocked.
- [x] Implemented PostgreSQL ingress restrictions.
- [x] Confirmed HavenBridge API Pods can reach PostgreSQL.
- [x] Confirmed unrelated Pods cannot connect to PostgreSQL.
- [x] Confirmed Calico enforces the final least-privilege communication model.

Final allowed communication:

```text
Traefik
   |
   | TCP/8000
   v
HavenBridge API
   |
   | TCP/5432
   v
PostgreSQL

HavenBridge API
   |
   +----> CoreDNS UDP/53
   |
   +----> CoreDNS TCP/53
```

### TLS, HTTPS and Private PKI

- [x] Installed cert-manager.
- [x] Installed and validated cert-manager CRDs.
- [x] Created the `havenbridge-selfsigned` bootstrap ClusterIssuer.
- [x] Created the HavenBridge private Root CA.
- [x] Validated the Root CA certificate and Secret.
- [x] Created the `havenbridge-ca` ClusterIssuer.
- [x] Confirmed both ClusterIssuers report `READY=True`.
- [x] Issued a server certificate for `havenbridge.lab`.
- [x] Created the `havenbridge-tls` Kubernetes TLS Secret.
- [x] Configured the Traefik `websecure` listener.
- [x] Configured TLS termination using `havenbridge-tls`.
- [x] Confirmed the HTTPS listener reports healthy Gateway conditions.
- [x] Added the API HTTPRoute to the HTTPS listener.
- [x] Installed the HavenBridge Root CA into the Syrus trust store.
- [x] Confirmed HTTPS works without `curl -k`.
- [x] Created the HTTP-to-HTTPS redirect route.
- [x] Confirmed HTTP returns a permanent `301` redirect.
- [x] Confirmed following the redirect reaches HTTPS after exactly one redirect.
- [x] Confirmed the final HTTPS readiness endpoint returns HTTP `200`.

Final validated external flow:

```text
http://havenbridge.lab
        ↓
301 Moved Permanently
        ↓
https://havenbridge.lab
        ↓
TLS
        ↓
Traefik websecure
        ↓
Gateway API
        ↓
HTTPRoute
        ↓
havenbridge-api Service
        ↓
EndpointSlice
        ↓
Ready FastAPI Pod
        ↓
HTTP 200
```

Validated endpoint:

```text
https://havenbridge.lab/health/ready
```

Validated response:

```text
HTTP/2 200
{"status":"ready"}
```


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

**Status: core platform services completed**

Completed:

- [x] Install Helm.
- [x] Install MetalLB.
- [x] Reserve application LoadBalancer IP `172.16.10.40`.
- [x] Install Kubernetes Gateway API CRDs.
- [x] Install Traefik.
- [x] Run two Traefik replicas.
- [x] Create a Traefik PodDisruptionBudget.
- [x] Define the `havenbridge.lab` application hostname.
- [x] Create the `traefik` GatewayClass.
- [x] Create `havenbridge-gateway`.
- [x] Validate hostname-based application routing.
- [x] Configure the Traefik `web` HTTP entrypoint.
- [x] Configure the Traefik `websecure` HTTPS entrypoint.
- [x] Configure NFS-backed shared storage.
- [x] Install the NFS CSI driver.
- [x] Create the default `havenbridge-nfs` StorageClass.
- [x] Validate dynamic PersistentVolume provisioning.
- [x] Validate cross-node data persistence.
- [x] Create the `havenbridge` application namespace.
- [x] Establish ConfigMap and Secret handling.
- [x] Implement application NetworkPolicies.
- [x] Validate allowed and blocked NetworkPolicy traffic.
- [x] Install cert-manager.
- [x] Create a private HavenBridge Root CA.
- [x] Create the HavenBridge CA ClusterIssuer.
- [x] Issue a TLS certificate for `havenbridge.lab`.
- [x] Configure TLS termination at Traefik.
- [x] Configure HTTP-to-HTTPS redirection.
- [x] Validate end-to-end HTTPS access.

Final application ingress architecture:

```text
HTTP :80
   ↓
Traefik web :8000
   ↓
301 redirect
   ↓
HTTPS :443
   ↓
Traefik websecure :8443
   ↓
TLS termination
   ↓
Gateway API
   ↓
HTTPRoute
   ↓
Application Service
```


### Phase 5 — Inquiry and Referral Tracking Application

**Status: core backend deployment completed; frontend and workflow expansion remain**

The first production-style HavenBridge application backend is now running
inside Kubernetes.

Completed:

- [x] Create the `havenbridge` application namespace.
- [x] Deploy PostgreSQL as a Kubernetes StatefulSet.
- [x] Configure PostgreSQL with NFS-backed persistent storage.
- [x] Validate PostgreSQL data persistence through Pod replacement.
- [x] Implement the FastAPI backend.
- [x] Add SQLAlchemy and Psycopg PostgreSQL connectivity.
- [x] Build `havenbridge-api:0.1.0`.
- [x] Confirm the container runs as a non-root user.
- [x] Validate the Dockerized API against PostgreSQL.
- [x] Publish the API image to GitHub Container Registry.
- [x] Deploy the API into Kubernetes.
- [x] Create the `havenbridge-api` ClusterIP Service.
- [x] Configure application ConfigMap and Secret handling.
- [x] Mount the PostgreSQL password as a read-only Secret file.
- [x] Configure readiness and liveness probes.
- [x] Configure CPU and memory resource controls.
- [x] Run two API replicas.
- [x] Distribute API replicas across separate worker nodes.
- [x] Configure topology-spread constraints.
- [x] Configure a PodDisruptionBudget.
- [x] Validate Deployment self-healing through controlled Pod deletion.
- [x] Validate application availability during a controlled worker drain.
- [x] Configure the Gateway API application route.
- [x] Implement least-privilege NetworkPolicies.
- [x] Restrict Traefik-to-API ingress.
- [x] Restrict API egress to CoreDNS and PostgreSQL.
- [x] Restrict PostgreSQL ingress to HavenBridge API Pods.
- [x] Validate unauthorized API and PostgreSQL traffic is blocked.
- [x] Configure HTTPS application access.
- [x] Configure HTTP-to-HTTPS redirection.
- [x] Validate the external readiness endpoint through HTTPS.

The deployed backend image is:

```text
ghcr.io/brunobrunt/havenbridge-api:0.1.0
```

The current application path is:

```text
Client
   ↓
HTTPS
   ↓
Traefik
   ↓
Gateway API
   ↓
HTTPRoute
   ↓
havenbridge-api Service
   ↓
Ready FastAPI Pod
   ↓
PostgreSQL Service
   ↓
PostgreSQL StatefulSet
   ↓
NFS-backed persistent storage
```

Validated readiness endpoint:

```text
https://havenbridge.lab/health/ready
```

Validated response:

```text
HTTP/2 200
{"status":"ready"}
```

#### Current Application Components

```text
PostgreSQL              Implemented and running
Backend API             Implemented and running
Persistent storage      Implemented and validated
HTTPS routing           Implemented and validated
NetworkPolicy           Implemented and validated
Frontend                Planned
Notification/SLA worker Planned
Synthetic seed data     Planned
```

#### Remaining Application Work

The remaining Phase 5 application work is focused on expanding the business
functionality rather than basic Kubernetes deployment.

- [ ] Build the web frontend.
- [ ] Add the notification/SLA worker.
- [ ] Add synthetic demonstration seed data.
- [ ] Expand inquiry and referral CRUD workflows.
- [ ] Add application-specific RBAC where required.
- [ ] Evaluate HorizontalPodAutoscaler configuration where meaningful.

Suggested application states remain:

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

Only synthetic demonstration data will be used.

---


### Phase 6 — CI/CD Automation

**Status: next major phase**

The next major goal is to automate application validation, container-image
creation, publication and Kubernetes deployment.

Planned work:

- [ ] Create a CI workflow for the FastAPI application.
- [ ] Run application tests automatically.
- [ ] Validate the Docker build automatically.
- [ ] Build versioned container images.
- [ ] Authenticate securely to GitHub Container Registry.
- [ ] Push approved images to GHCR.
- [ ] Validate Kubernetes manifests automatically.
- [ ] Automate deployment of approved releases.
- [ ] Validate Kubernetes rollout status.
- [ ] Add deployment verification.
- [ ] Document rollback procedures.
- [ ] Preserve CI/CD validation evidence.

Planned delivery flow:

```text
Developer change
      ↓
Git commit
      ↓
GitHub
      ↓
CI validation
      ↓
Tests
      ↓
Container build
      ↓
GHCR
      ↓
Deployment automation
      ↓
Kubernetes
      ↓
Rollout validation
```

---

### Phase 7 — Observability

**Status: planned**

Planned components:

- [ ] Prometheus.
- [ ] Grafana.
- [ ] Alertmanager.
- [ ] Kubernetes workload metrics.
- [ ] Node-level metrics.
- [ ] HavenBridge API metrics.
- [ ] PostgreSQL monitoring where appropriate.
- [ ] Dashboards.
- [ ] Alert rules.
- [ ] Availability monitoring.
- [ ] Resource-usage monitoring.

Planned architecture:

```text
Applications / Kubernetes / Nodes
             ↓
         Prometheus
             ↓
          Grafana
             ↓
         Dashboards

         Prometheus
             ↓
        Alertmanager
             ↓
           Alerts
```

---

### Phase 8 — Application and Operational Maturity

**Status: planned**

Potential improvements include:

- [ ] Expand inquiry and referral functionality.
- [ ] Introduce structured database migrations.
- [ ] Implement PostgreSQL backup procedures.
- [ ] Test PostgreSQL recovery procedures.
- [ ] Add additional operational runbooks.
- [ ] Perform controlled worker-node failure testing.
- [ ] Perform controlled control-plane failure testing.
- [ ] Validate kube-vip failover.
- [ ] Create and test etcd backup procedures.
- [ ] Test etcd recovery procedures.
- [ ] Review physical-host recovery procedures.
- [ ] Continue security hardening.

---

### Phase 9 — AI-Assisted Kubernetes Operations

**Status: planned after the core platform is completed**

A future HavenBridge phase will introduce a secure, read-only Kubernetes
operations agent.

The initial agent will inspect:

```text
Kubernetes workloads
        ↓
Pod status and readiness
        ↓
Kubernetes Events
        ↓
EndpointSlices
        ↓
Application logs
        ↓
Metrics
        ↓
HavenBridge runbooks
```

The agent will produce:

- evidence-based incident summaries;
- likely root-cause explanations;
- relevant platform evidence;
- recommended troubleshooting steps; and
- safe recovery commands.

The first implementation will remain read-only so the agent can assist with
operations without directly modifying Kubernetes resources.


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

These commands provide a quick validation of the major HavenBridge platform
layers.

Cluster-side `kubectl` commands are normally executed from a Kubernetes
control-plane node such as `eph-cp01`.

### Kubernetes and Calico

```bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl get tigerastatus
kubectl get ippools.crd.projectcalico.org
kubectl get --raw='/readyz?verbose'
```

Expected cluster state:

```text
3 control-plane nodes Ready
2 worker nodes Ready
Calico available
CoreDNS available
Kubernetes API ready
```

Validate the Calico IP pool:

```bash
kubectl get ippools.crd.projectcalico.org \
  default-ipv4-ippool \
  -o jsonpath='{.spec.cidr}{"\n"}{.spec.vxlanMode}{"\n"}{.spec.natOutgoing}{"\n"}'
```

Expected:

```text
10.244.0.0/16
Always
true
```

### MetalLB, Traefik and Gateway API

```bash
kubectl get ipaddresspools.metallb.io \
  --namespace metallb-system

kubectl get l2advertisements.metallb.io \
  --namespace metallb-system

kubectl get pods \
  --namespace metallb-system \
  --output wide

kubectl get pods,service \
  --namespace traefik \
  --output wide

kubectl get gatewayclass

kubectl get gateway havenbridge-gateway \
  --namespace traefik

kubectl get httproute \
  --namespace havenbridge
```

The Traefik LoadBalancer Service should expose:

```text
Application IP:
172.16.10.40

HTTP:
80 → web:8000

HTTPS:
443 → websecure:8443
```

Validate Gateway listener route attachment:

```bash
kubectl get gateway havenbridge-gateway \
  --namespace traefik \
  --output jsonpath='{range .status.listeners[*]}{.name}{"\tAttached Routes: "}{.attachedRoutes}{"\n"}{end}'
```

Expected:

```text
web        Attached Routes: 1
websecure  Attached Routes: 1
```

### HTTP-to-HTTPS Redirect

Run from `syrus`:

```bash
curl -sS \
  -o /dev/null \
  -D - \
  http://havenbridge.lab/health/ready \
  | grep -Ei '^(HTTP/|Location:)'
```

Expected:

```text
HTTP/1.1 301 Moved Permanently
Location: https://havenbridge.lab/health/ready
```

Validate the full redirect:

```bash
curl -sS -L \
  -o /dev/null \
  -w 'Final URL: %{url_effective}\nHTTP Code: %{http_code}\nRedirects: %{num_redirects}\n' \
  http://havenbridge.lab/health/ready
```

Expected:

```text
Final URL: https://havenbridge.lab/health/ready
HTTP Code: 200
Redirects: 1
```

### HTTPS Application Validation

Run from `syrus`:

```bash
curl -i \
  https://havenbridge.lab/health/ready
```

Expected:

```text
HTTP/2 200
{"status":"ready"}
```

The final application path is:

```text
Client
   ↓
HTTPS :443
   ↓
172.16.10.40
   ↓
MetalLB
   ↓
Traefik websecure :8443
   ↓
TLS termination
   ↓
Gateway API
   ↓
HTTPRoute
   ↓
havenbridge-api Service
   ↓
EndpointSlice
   ↓
Ready FastAPI Pod
```

### cert-manager and TLS

```bash
kubectl get pods \
  --namespace cert-manager

kubectl get clusterissuer

kubectl get certificate -A \
  --output wide

kubectl get secret havenbridge-tls \
  --namespace traefik
```

Expected certificate state includes:

```text
havenbridge-selfsigned   Ready
havenbridge-ca           Ready

cert-manager/havenbridge-root-ca   Ready
traefik/havenbridge-tls            Ready
```

The final server certificate is stored in:

```text
Secret:
havenbridge-tls

Namespace:
traefik
```

### HavenBridge API

```bash
kubectl get deployment havenbridge-api \
  --namespace havenbridge

kubectl get pods \
  --namespace havenbridge \
  --selector app.kubernetes.io/name=havenbridge-api \
  --output wide

kubectl get service havenbridge-api \
  --namespace havenbridge

kubectl get endpointslice \
  --namespace havenbridge \
  --selector kubernetes.io/service-name=havenbridge-api \
  --output wide
```

Expected application state:

```text
2 API replicas
Both Ready
Replicas distributed across eph-worker01 and eph-worker02
Service available
EndpointSlice contains Ready API endpoints
```

### PodDisruptionBudget

```bash
kubectl get poddisruptionbudget \
  --namespace havenbridge
```

The HavenBridge API PDB should protect the application from more than one
voluntary disruption at a time.

### NetworkPolicy

```bash
kubectl get networkpolicy \
  --namespace havenbridge
```

Expected production policies:

```text
allow-traefik-to-havenbridge-api
allow-havenbridge-api-egress
allow-havenbridge-api-to-postgres
```

The validated communication model is:

```text
Traefik → API TCP/8000                 allowed
Unrelated Pod → API                    blocked

API → CoreDNS UDP/53                   allowed
API → CoreDNS TCP/53                   allowed
API → PostgreSQL TCP/5432              allowed
Unapproved tested API egress           blocked

HavenBridge API → PostgreSQL TCP/5432  allowed
Unrelated Pod → PostgreSQL             blocked
```

### PostgreSQL and Persistent Storage

```bash
kubectl get pod havenbridge-postgres-0 \
  --namespace havenbridge \
  --output wide

kubectl get pvc \
  --namespace havenbridge

kubectl get pv

kubectl get storageclass havenbridge-nfs
```

The PostgreSQL storage relationship should remain:

```text
havenbridge-postgres-0
        ↓
postgres-data-havenbridge-postgres-0
        ↓
PersistentVolume
        ↓
havenbridge-nfs StorageClass
        ↓
NFS-backed storage
```

The earlier temporary `nfs-writer` and `nfs-reader` Pods were used to prove
cross-node NFS persistence and are not required for normal platform
validation.

Current PostgreSQL persistence is validated through the PostgreSQL StatefulSet,
its PVC and its NFS-backed PersistentVolume.

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

HavenBridge is a portfolio and learning platform. Only synthetic demonstration
data should be used.

### Sensitive Information That Must Never Be Committed

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
TLS private keys
Root CA private keys
database passwords
real application secrets
real client or employee information
```

Use placeholders in documentation:

```text
<TOKEN>
<CERTIFICATE_KEY>
<CA_CERT_HASH>
<SECRET_VALUE>
<PASSWORD>
```

### Implemented Application Security Controls

The HavenBridge backend uses several defense-in-depth controls.

#### Non-Root Container Execution

The FastAPI container runs as:

```text
uid=100(havenbridge)
gid=101(havenbridge)
```

The Kubernetes workload explicitly requires non-root execution.

#### Restricted Container Privileges

The API container uses:

```text
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
seccompProfile: RuntimeDefault
capabilities: drop ALL
```

These controls reduce the privileges available to the application process.

#### Kubernetes Secret Handling

The PostgreSQL password is stored in the Kubernetes Secret:

```text
havenbridge-postgres-secret
```

rather than in the ConfigMap or Git repository.

The password is mounted read-only inside the API container at:

```text
/run/secrets/postgres-password
```

#### NetworkPolicy Enforcement

Calico NetworkPolicies enforce a least-privilege communication model.

Validated allowed traffic:

```text
Traefik
   |
   | TCP/8000
   v
HavenBridge API
   |
   | TCP/5432
   v
PostgreSQL

HavenBridge API
   |
   +----> CoreDNS UDP/53
   |
   +----> CoreDNS TCP/53
```

Validated blocked traffic includes:

```text
Unrelated Pod → HavenBridge API    blocked
Unapproved API egress              blocked
Unrelated Pod → PostgreSQL         blocked
```

#### HTTPS and TLS

User-facing application traffic is protected with HTTPS.

```text
HTTP
   ↓
301 redirect
   ↓
HTTPS
   ↓
TLS
   ↓
Traefik
   ↓
HavenBridge API
```

TLS terminates at Traefik using:

```text
Secret: havenbridge-tls
```

#### Private PKI

The HavenBridge certificate hierarchy is:

```text
SelfSigned ClusterIssuer
        ↓
HavenBridge Root CA
        ↓
HavenBridge CA ClusterIssuer
        ↓
havenbridge.lab Certificate
        ↓
havenbridge-tls Secret
```

The Root CA certificate may be distributed to trusted clients.

The Root CA private key and TLS private keys must remain protected.

### Data Privacy

Only synthetic client and application data should be used for development,
testing and portfolio demonstrations.

Real client, employee, health, disability, referral or personally identifiable
information must not be stored in this public repository.

### Current Security Boundaries

TLS currently protects:

```text
Client → Traefik
```

Traefik terminates TLS before routing requests internally to the HavenBridge
API.

Application-level TLS between Traefik and the backend API is not currently
configured.

Because HavenBridge uses a private CA, clients must explicitly trust the
HavenBridge Root CA.

### NFS Security Limitation

The NFS configuration uses homelab-oriented permissions to support dynamic
Kubernetes provisioning.

The use of:

```text
no_root_squash
```

must be treated as a deliberate lab simplification rather than a production
security recommendation.

### Remaining Security Hardening

Future improvements include:

- Application-specific Kubernetes RBAC where required.
- ResourceQuota and LimitRange policies where appropriate.
- PostgreSQL backup and tested recovery procedures.
- Improved protection and recovery planning for private CA signing material.
- Additional audit and observability controls.
- Continued Kubernetes and container security review.
- Evaluation of internal TLS where the threat model requires encryption beyond
  the Traefik boundary.

---

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

The next active HavenBridge phase is **CI/CD automation using GitHub Actions**.

### 1. GitHub Actions CI/CD

The immediate goal is to automate the application delivery process.

Planned work:

- Create the GitHub Actions workflow.
- Run FastAPI tests automatically.
- Validate the Docker build.
- Build versioned HavenBridge API images.
- Authenticate securely to GitHub Container Registry.
- Push approved images to GHCR.
- Validate Kubernetes manifests.
- Automate deployment to the HavenBridge Kubernetes cluster.
- Validate Deployment rollout status.
- Add post-deployment health checks.
- Document rollback procedures.
- Save CI/CD validation evidence.

Planned delivery flow:

```text
Developer change
        ↓
Git commit
        ↓
GitHub
        ↓
GitHub Actions
        ↓
Application tests
        ↓
Docker build
        ↓
GitHub Container Registry
        ↓
Kubernetes deployment
        ↓
Rollout validation
        ↓
HTTPS health check
```

### 2. Observability

After CI/CD, add platform and application observability using:

```text
Prometheus
Grafana
Alertmanager
```

Planned monitoring includes:

- Kubernetes node and workload metrics.
- HavenBridge API availability.
- API response latency and error rates.
- PostgreSQL health where appropriate.
- Resource utilization.
- Dashboards.
- Alert rules.
- Alert delivery and validation.

### 3. Application and Operational Maturity

After the core CI/CD and observability work, continue expanding the HavenBridge
application and operational capabilities.

Planned work includes:

- Build the HavenBridge web frontend.
- Expand inquiry and referral CRUD workflows.
- Add synthetic demonstration data.
- Add the notification/SLA worker.
- Introduce structured database migrations.
- Implement PostgreSQL backups.
- Test PostgreSQL recovery.
- Create etcd backup and recovery procedures.
- Perform controlled worker-node failure testing.
- Perform controlled control-plane failure testing.
- Validate kube-vip failover.
- Continue Kubernetes and application security hardening.

### 4. AI-Assisted Kubernetes Operations

A later phase will introduce a secure read-only HavenBridge Kubernetes
operations agent.

The initial agent will inspect:

```text
Workloads
   ↓
Pod readiness
   ↓
Kubernetes Events
   ↓
EndpointSlices
   ↓
Application logs
   ↓
Metrics
   ↓
HavenBridge runbooks
```

It will produce evidence-based incident summaries, likely root-cause
explanations, troubleshooting recommendations and safe recovery commands.

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
