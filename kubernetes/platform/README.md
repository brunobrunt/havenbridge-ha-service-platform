# HavenBridge Kubernetes Platform Services

This directory contains Kubernetes platform components required to expose,
route, secure and persist the HavenBridge application.

## Components

The HavenBridge Kubernetes platform currently includes:

- kube-vip for the highly available Kubernetes API virtual IP
- Calico for Kubernetes pod networking and NetworkPolicy enforcement
- MetalLB for bare-metal `LoadBalancer` services
- Traefik Proxy for HTTP and HTTPS application traffic
- Kubernetes Gateway API for application routing
- cert-manager for certificate lifecycle management
- A private HavenBridge certificate authority for internal TLS
- NFS-backed persistent storage for stateful workloads
- PostgreSQL persistent storage integration

Each component solves a different platform requirement:

```text
kube-vip
    ↓
Highly available Kubernetes API endpoint

Calico
    ↓
Pod networking and NetworkPolicy

MetalLB
    ↓
Reachable application LoadBalancer IP

Traefik
    ↓
Application reverse proxy

Gateway API
    ↓
HTTP/HTTPS routing

cert-manager
    ↓
Certificate lifecycle automation

Private PKI
    ↓
TLS trust for havenbridge.lab

NFS CSI
    ↓
Dynamic persistent storage


## Network Addresses

| Purpose                | Address           |
| ---------------------- | ----------------- |
| Kubernetes API VIP     | `172.16.10.30`    |
| Application Gateway IP | `172.16.10.40`    |
| Kubernetes API DNS     | `k8s-api.lab`     |
| Application DNS        | `havenbridge.lab` |

The Kubernetes API VIP and application gateway address are intentionally
separate.


## Application Traffic Architecture

HavenBridge uses MetalLB, Traefik and Kubernetes Gateway API together to expose
the application.

The application hostname is:

```text
havenbridge.lab

## HTTP and HTTPS Traffic
HTTP 80 → web:8000
    redirect behavior
    HTTPS 443 → websecure:8443
    secure request flow

## TLS and Certificate Management
    cert-manager
    private Root CA
    CA ClusterIssuer
    havenbridge-tls Secret
    TLS termination
    links to TLS README


## PostgreSQL Persistent Storage

The HavenBridge PostgreSQL database runs as a Kubernetes StatefulSet and uses
dynamically provisioned NFS-backed persistent storage.

### PostgreSQL Storage Flow

```text
PostgreSQL StatefulSet
        ↓
volumeClaimTemplates
        ↓
PVC created automatically
        ↓
havenbridge-nfs StorageClass
        ↓
NFS-backed PersistentVolume
```

The `volumeClaimTemplates` section of the PostgreSQL StatefulSet automatically
creates a dedicated PersistentVolumeClaim for each PostgreSQL pod.

For the current PostgreSQL instance, Kubernetes created the following claim:

```text
postgres-data-havenbridge-postgres-0
```

The claim uses the `havenbridge-nfs` StorageClass, which dynamically provisions
an NFS-backed PersistentVolume.

The resulting storage relationship is:

```text
Pod: havenbridge-postgres-0
        ↓
PVC: postgres-data-havenbridge-postgres-0
        ↓
PV: pvc-ff29106d-5d97-424f-b6b3-2432df3a176e
        ↓
StorageClass: havenbridge-nfs
        ↓
NFS server storage
```

### Why PostgreSQL Uses a StatefulSet

A StatefulSet manages applications that require stable identities and persistent
storage.

Unlike a Deployment, a StatefulSet gives each pod:

* A predictable and stable name, such as `havenbridge-postgres-0`
* A dedicated PersistentVolumeClaim
* A stable relationship with its persistent storage
* Ordered pod creation, termination and replacement

PostgreSQL uses a StatefulSet because its database files must remain available
even when its pod is restarted, deleted or recreated.

The PostgreSQL data is stored on the PersistentVolume rather than inside the
temporary filesystem of the container. This separates the lifecycle of the
database data from the lifecycle of the PostgreSQL pod.

### Persistence Validation

PostgreSQL persistence was validated using the following process:

1. Confirmed that `postgres-data-havenbridge-postgres-0` was in the `Bound`
   state.
2. Confirmed that the claim was bound to
   `pvc-ff29106d-5d97-424f-b6b3-2432df3a176e`.
3. Connected to the `havenbridge` database as `havenbridge_admin`.
4. Created a `platform_validation` table.
5. Inserted a persistence-validation record.
6. Recorded the UID of the original PostgreSQL pod.
7. Deleted `havenbridge-postgres-0`.
8. Allowed the StatefulSet controller to recreate the pod.
9. Confirmed that the recreated pod had a different UID.
10. Confirmed that the original PVC and PV remained bound.
11. Reconnected to PostgreSQL.
12. Confirmed that the original validation record was still available.

The original and recreated pod UIDs were different:

```text
Original pod UID:
7e0a88ad-efe1-424c-9881-54027b0afe43

Recreated pod UID:
a49f2d15-9773-4e46-a6dd-50b90515c8c3
```

The different UIDs prove that Kubernetes created a new pod rather than merely
restarting the original container.

The validation record remained available after the pod was recreated:

```text
ID: 1
Message: HavenBridge PostgreSQL persistence validation
Created: 2026-07-27 03:33:14.395938+00
```

This confirms the following recovery flow:

```text
PostgreSQL pod deleted
        ↓
StatefulSet creates a replacement pod
        ↓
Replacement pod retains the stable pod name
        ↓
Existing PVC is mounted
        ↓
Existing NFS-backed PV is reused
        ↓
PostgreSQL reads the original database files
        ↓
Previously stored data remains available
```

### Validation Result

The PostgreSQL persistent-storage validation was successful.

The test demonstrated that:

* The PostgreSQL PVC remained in the `Bound` state.
* The PersistentVolume remained unchanged.
* The original PostgreSQL pod was replaced.
* The replacement pod mounted the existing PVC.
* PostgreSQL started successfully after recreation.
* The `platform_validation` table remained available.
* The original database record remained unchanged.

Detailed command output and evidence are available at:

```text
storage/evidence/postgres-persistence-validation.txt
```

## Application Integration Status

The HavenBridge FastAPI backend is now deployed inside the Kubernetes cluster
in the:

```text
ghcr.io/brunobrunt/havenbridge-api:0.1.0
```

The Docker image has been validated with the following checks:
### Initial Local Docker and PostgreSQL Validation

Before the HavenBridge API was deployed into Kubernetes, the Docker image was
validated with the following checks:

- The container started successfully.
- The container ran as the non-root `havenbridge` user.
- The API connected successfully to PostgreSQL.
- SQLAlchemy created the required application tables.
- The `platform_validation` table existed.
- The `service_inquiries` table existed.

During this initial validation, the FastAPI container ran on `syrus` while
PostgreSQL ran inside Kubernetes.

The temporary validation path was:

```text
FastAPI container on syrus
        ↓
SSH tunnel
        ↓
kubectl port-forward
        ↓
PostgreSQL Pod in Kubernetes

```

After the API is deployed inside Kubernetes, it will connect directly to the
internal PostgreSQL Service. The SSH tunnel will no longer be required.


At the Kubernetes workload layer, critical application components use
replication, scheduling controls and PodDisruptionBudgets where appropriate.
However, Kubernetes redundancy cannot eliminate the shared physical failure
domain created by running the virtualized cluster and NFS infrastructure on the
same physical host.


## Platform Availability Note

The Kubernetes control plane is redundant across three virtual machines.

However, all Kubernetes virtual machines and the NFS server currently depend
on the same physical host, `syrus`.

An NFS-service failure may affect PostgreSQL and other NFS-backed workloads
while the Kubernetes control plane remains available.

A complete `syrus` host failure stops both the Kubernetes virtual machines and
the NFS storage service.

At the Kubernetes workload layer, critical application components use
replication, scheduling controls and PodDisruptionBudgets where appropriate.

However, Kubernetes redundancy cannot eliminate the shared physical failure
domain created by running the virtualized cluster and NFS infrastructure on the
same physical host.

Detailed storage failure, recovery and resilience guidance is documented in:

- [NFS Storage Design and Recovery](storage/README.md)


## Platform Documentation

Detailed component documentation is maintained beside each platform component.

### Traffic Routing

- [Traefik and Gateway API](traefik/README.md)

Covers:

```text
MetalLB
Traefik
Entrypoints
GatewayClass
Gateway
Listeners
HTTPRoute
Services
EndpointSlices
HTTP-to-HTTPS redirect
High availability
Troubleshooting
```

### TLS and PKI

- [TLS, cert-manager and Private PKI](tls/README.md)

### Persistent Storage

- [NFS Storage Design and Recovery](storage/README.md)

## Operational Runbooks

- [HavenBridge API and PostgreSQL Validation](runbooks/havenbridge-api-postgresql-validation.txt)
- [NFS Storage Design and Recovery](storage/README.md)

Validation evidence is maintained under:

```text
kubernetes/platform/evidence/
```

including:

```text
kubernetes/platform/evidence/tls-validation/
```

## Documentation Hierarchy

```text
README.md
│
└── kubernetes/platform/README.md
        │
        ├── traefik/README.md
        ├── tls/README.md
        ├── storage/README.md
        └── runbooks/
```

The root README provides the overall project story.

The platform README explains how the Kubernetes platform components fit
together.

The component READMEs provide the detailed implementation, validation,
troubleshooting and interview-preparation material.

## Operational Runbooks

- [HavenBridge API and PostgreSQL Validation](runbooks/havenbridge-api-postgresql-validation.txt)
- [NFS Storage Design and Recovery](storage/README.md)


## Documentation Hierarchy
root → platform → component READMEs
