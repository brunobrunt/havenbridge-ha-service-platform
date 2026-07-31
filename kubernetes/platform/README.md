# HavenBridge Kubernetes Platform Services

This directory contains Kubernetes platform components required to expose,
route, secure and persist the HavenBridge application.

## Components

- MetalLB for bare-metal LoadBalancer services
- Traefik Proxy for application traffic
- Kubernetes Gateway API for routing
- Persistent storage for stateful workloads
- TLS and certificate management

The Kubernetes API VIP and application gateway address are intentionally
separate.

## Network Addresses

| Purpose                | Address           |
| ---------------------- | ----------------- |
| Kubernetes API VIP     | `172.16.10.30`    |
| Application Gateway IP | `172.16.10.40`    |
| Kubernetes API DNS     | `k8s-api.lab`     |
| Application DNS        | `havenbridge.lab` |

The Kubernetes API VIP and application gateway address are intentionally
separate.

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

PostgreSQL is running in the `havenbridge` namespace as a StatefulSet with
NFS-backed persistent storage.

The HavenBridge FastAPI backend has been implemented and packaged as:

```text
havenbridge-api:0.1.0
```

The Docker image has been validated with the following checks:

* The container starts successfully
* The container runs as the non-root `havenbridge` user
* The API connects successfully to PostgreSQL
* SQLAlchemy creates the required application tables
* The `platform_validation` table exists
* The `service_inquiries` table exists

During local validation, the FastAPI container ran on `syrus` while PostgreSQL
ran inside Kubernetes.

The temporary connection path was:

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

## Platform Availability Note

The Kubernetes control plane is redundant across three virtual machines.

However, all Kubernetes virtual machines and the NFS server currently depend
on the same physical host, `syrus`.

An NFS-service failure may affect PostgreSQL and other NFS-backed workloads
while the Kubernetes control plane remains available.

A complete `syrus` host failure stops both the Kubernetes virtual machines and
the NFS storage service.

Detailed storage failure, recovery and resilience guidance is documented in:

* [NFS Storage Design and Recovery](storage/README.md)

## Operational Runbooks

* [HavenBridge API and PostgreSQL Validation](runbooks/havenbridge-api-postgresql-validation.txt)
* [NFS Storage Design and Recovery](storage/README.md)

