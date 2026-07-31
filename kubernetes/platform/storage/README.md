# HavenBridge Kubernetes Storage

This directory contains the Kubernetes persistent-storage configuration,
validation resources, evidence and recovery guidance for the HavenBridge
platform.

The current storage layer uses the Kubernetes NFS CSI driver to dynamically
provision PersistentVolumes from an NFS export hosted on `syrus`.

---

## Storage Architecture

```text
PostgreSQL StatefulSet
        ↓
volumeClaimTemplates
        ↓
PersistentVolumeClaim created automatically
        ↓
StorageClass: havenbridge-nfs
        ↓
NFS CSI Driver
        ↓
PersistentVolume created dynamically
        ↓
NFS server: 172.16.10.1
        ↓
syrus:/data_all/havenbridge-nfs
```

The PostgreSQL StatefulSet requests storage through its
`volumeClaimTemplates` section.

Kubernetes automatically creates a PersistentVolumeClaim for the PostgreSQL
Pod. The `havenbridge-nfs` StorageClass then asks the NFS CSI provisioner to
create:

* A PersistentVolume object in Kubernetes
* A backing directory on the NFS server
* A binding between the PersistentVolumeClaim and PersistentVolume

---

## Why NFS Was Selected

NFS was selected for the HavenBridge homelab because it:

* Is simple to operate
* Requires fewer resources than distributed storage platforms
* Supports dynamic volume provisioning
* Supports `ReadWriteMany`
* Allows storage to be mounted from different Kubernetes worker nodes
* Provides a clear way to demonstrate Kubernetes storage concepts
* Is appropriate for a small portfolio and learning environment

The current implementation is not intended to represent fully redundant
production storage.

Production alternatives may include:

* Longhorn
* Rook-Ceph
* Highly available NFS
* Dedicated NAS appliances
* Cloud-managed block or file storage

---

## StorageClass

The HavenBridge StorageClass is:

```text
havenbridge-nfs
```

List all StorageClasses:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get storageclass'
```

Inspect the HavenBridge StorageClass:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl describe storageclass havenbridge-nfs'
```

The StorageClass is responsible for directing storage requests to the NFS CSI
provisioner.

---

## PostgreSQL StatefulSet

PostgreSQL runs as a Kubernetes StatefulSet.

A StatefulSet is similar to a Deployment, but it is designed for applications
that need:

* A stable Pod name
* Stable storage
* Predictable startup and shutdown behaviour
* A persistent identity across Pod replacement

The PostgreSQL Pod uses the stable name:

```text
havenbridge-postgres-0
```

PostgreSQL uses a StatefulSet instead of a Deployment because its data must
remain attached to the same logical database instance even when the Pod is
deleted and recreated.

A Deployment is normally better suited for stateless applications where any
replica can replace another replica without needing a unique storage identity.

---

## PostgreSQL Storage Flow

The PostgreSQL manifest defines a `volumeClaimTemplates` section.

The storage request follows this process:

```text
StatefulSet creates Pod havenbridge-postgres-0
        ↓
StatefulSet creates PVC postgres-data-havenbridge-postgres-0
        ↓
PVC requests the havenbridge-nfs StorageClass
        ↓
NFS CSI provisioner creates a PersistentVolume
        ↓
PVC becomes Bound to the PersistentVolume
        ↓
PersistentVolume mounts into the PostgreSQL Pod
        ↓
PostgreSQL stores its database files on NFS
```

The PostgreSQL PersistentVolumeClaim is:

```text
postgres-data-havenbridge-postgres-0
```

---

## Validate the PostgreSQL PVC

Run from `syrus`:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get pvc \
    postgres-data-havenbridge-postgres-0 \
    --namespace havenbridge'
```

Detailed output:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl describe pvc \
    postgres-data-havenbridge-postgres-0 \
    --namespace havenbridge'
```

Display the PVC status and associated PersistentVolume:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get pvc \
    postgres-data-havenbridge-postgres-0 \
    --namespace havenbridge \
    --output jsonpath='"'"'STATUS={.status.phase}{"\n"}PV={.spec.volumeName}{"\n"}'"'"''
```

Validated result:

```text
STATUS=Bound
PV=pvc-ff29106d-5d97-424f-b6b3-2432df3a176e
```

A `Bound` status confirms that Kubernetes successfully connected the PVC to a
PersistentVolume.

---

## Validate the PersistentVolume

List the HavenBridge PVC and PV:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get pvc \
    --namespace havenbridge;
   kubectl get pv'
```

Inspect the dynamically provisioned PersistentVolume:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl describe pv \
    pvc-ff29106d-5d97-424f-b6b3-2432df3a176e'
```

The PersistentVolume name may change if the PVC is deleted and recreated.

Do not hard-code the PersistentVolume name into automation without first
querying the PVC.

---

## Validate the PostgreSQL Pod

Check the Pod:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get pod \
    havenbridge-postgres-0 \
    --namespace havenbridge \
    --output wide'
```

Describe the Pod:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl describe pod \
    havenbridge-postgres-0 \
    --namespace havenbridge'
```

Check the init container status:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get pod \
    havenbridge-postgres-0 \
    --namespace havenbridge \
    --output jsonpath='"'"'{range .status.initContainerStatuses[*]}{.name}{" reason="}{.state.terminated.reason}{" exitCode="}{.state.terminated.exitCode}{"\n"}{end}'"'"''
```

Validated result:

```text
prepare-data-directory reason=Completed exitCode=0
```

This confirms the PostgreSQL data directory was prepared successfully before
the main PostgreSQL container started.

Check the init-container logs:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl logs \
    havenbridge-postgres-0 \
    --namespace havenbridge \
    --container prepare-data-directory'
```

An empty result with no error is acceptable when the init container completes
successfully without producing log output.

---

## Validate the PostgreSQL Mount

Display the PostgreSQL container volume mounts:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get pod \
    havenbridge-postgres-0 \
    --namespace havenbridge \
    --output jsonpath='"'"'{range .spec.containers[?(@.name=="postgresql")].volumeMounts[*]}{.name}{" -> "}{.mountPath}{"\n"}{end}'"'"''
```

Validated mounts include:

```text
postgres-data -> /var/lib/postgresql
postgres-secret -> /run/secrets
dshm -> /dev/shm
```

The PostgreSQL database files are stored under the volume mounted at:

```text
/var/lib/postgresql
```

---

## Validate PostgreSQL Data

Confirm the database accepts the mounted Kubernetes Secret:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl exec \
    --namespace havenbridge \
    havenbridge-postgres-0 \
    --container postgresql \
    -- sh -c '"'"'PGPASSWORD="$(cat "$POSTGRES_PASSWORD_FILE")" \
    psql \
      --host 127.0.0.1 \
      --username "$POSTGRES_USER" \
      --dbname "$POSTGRES_DB" \
      --command "SELECT current_user, current_database();"'"'"''
```

Validated result:

```text
current_user       | current_database
-------------------+-----------------
havenbridge_admin  | havenbridge
```

List the application tables:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl exec \
    --namespace havenbridge \
    havenbridge-postgres-0 \
    --container postgresql \
    -- sh -c '"'"'PGPASSWORD="$(cat "$POSTGRES_PASSWORD_FILE")" \
    psql \
      --host 127.0.0.1 \
      --username "$POSTGRES_USER" \
      --dbname "$POSTGRES_DB" \
      --command "\dt"'"'"''
```

Validated tables:

```text
public | platform_validation | table | havenbridge_admin
public | service_inquiries   | table | havenbridge_admin
```

---

## Persistence Validation

PostgreSQL persistence was validated by:

1. Creating data in PostgreSQL
2. Confirming the PVC was `Bound`
3. Deleting or replacing the PostgreSQL Pod
4. Allowing the StatefulSet to recreate the Pod
5. Confirming the same PVC was reattached
6. Confirming the database tables and validation data remained available

This proves the PostgreSQL data is stored outside the lifecycle of the Pod.

```text
PostgreSQL Pod deleted
        ↓
StatefulSet creates replacement Pod
        ↓
Existing PVC remains
        ↓
Existing PersistentVolume remains
        ↓
Replacement Pod mounts the same storage
        ↓
Database data remains available
```

---

## Evidence Directory

Storage validation evidence should be stored under:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/storage/evidence/
```

Recommended structure:

```text
evidence/
├── before/
│   ├── pvc-status.txt
│   ├── pv-status.txt
│   ├── postgres-pod-status.txt
│   ├── postgres-tables.txt
│   └── validation-record.txt
│
└── after/
    ├── pvc-status.txt
    ├── pv-status.txt
    ├── postgres-pod-status.txt
    ├── postgres-tables.txt
    └── validation-record.txt
```

The `before` directory should contain evidence collected before Pod deletion or
replacement.

The `after` directory should contain evidence proving the PVC, tables and data
remained available after the replacement Pod started.

Do not place database passwords or Kubernetes Secret values in evidence files.

---

## Physical Failure Domain

The physical host `syrus` currently performs two infrastructure roles:

1. It hosts all Kubernetes virtual machines through KVM/libvirt
2. It provides the NFS storage used by the Kubernetes cluster

The Kubernetes control plane is redundant across three virtual machines, but
all virtual machines depend on the same physical host.

This means the platform currently has virtual-machine-level redundancy but not
physical-host redundancy.

---

## Failure Scenario 1 — NFS Service Failure

This scenario applies when `syrus` remains operational and the Kubernetes
virtual machines remain running, but one of the following fails:

* `nfs-kernel-server`
* The NFS export
* The `/data_all` mount
* The NFS network path
* The underlying NFS storage disk

Possible symptoms include:

* PostgreSQL readiness failures
* `FailedMount` events
* Pods remaining in `ContainerCreating`
* Storage I/O errors
* PostgreSQL becoming unavailable
* New NFS-backed workloads failing to start

The Kubernetes API and stateless workloads may remain operational.

Do not immediately delete:

* PersistentVolumeClaims
* PersistentVolumes
* The PostgreSQL StatefulSet
* The NFS data directory
* PostgreSQL database files

Deleting these resources can turn a recoverable NFS outage into data loss.

---

## NFS Recovery Checks

Run the following commands on `syrus`.

Confirm the host:

```bash
hostname
```

Confirm `/data_all` is mounted:

```bash
findmnt /data_all
```

Check capacity:

```bash
df -h /data_all
```

Check the NFS service:

```bash
sudo systemctl status \
  nfs-kernel-server \
  --no-pager
```

List the active exports:

```bash
sudo exportfs -v
```

Confirm NFS is listening on port `2049`:

```bash
sudo ss -lntup |
grep ':2049'
```

Check the libvirt network:

```bash
sudo virsh net-list --all
```

Restore the NFS service when necessary:

```bash
sudo systemctl restart \
  nfs-kernel-server
```

Reload the exports:

```bash
sudo exportfs -ra
```

Confirm the exports:

```bash
sudo exportfs -v
```

The original storage endpoint should remain:

```text
NFS server: 172.16.10.1
Export: /data_all/havenbridge-nfs
```

Changing the server address or export path may prevent existing volumes from
mounting.

---

## Validate NFS from Kubernetes

Check the NFS export from a Kubernetes node:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'showmount -e 172.16.10.1'
```

Check storage objects:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get pvc -A;
   kubectl get pv'
```

Check HavenBridge Pods:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get pods \
    --namespace havenbridge \
    --output wide'
```

Check recent storage-related events:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get events \
    --namespace havenbridge \
    --sort-by=.lastTimestamp |
   tail -30'
```

After NFS is restored, confirm:

* PVCs remain `Bound`
* PostgreSQL returns to `Running`
* PostgreSQL becomes ready
* Existing database tables remain available
* Existing application data remains available

Restart workloads only after the NFS service is stable and only when Kubernetes
does not recover them automatically.

---

## Failure Scenario 2 — Complete Syrus Host Failure

A complete failure of `syrus` affects both compute and storage:

```text
syrus unavailable
        ↓
All Kubernetes virtual machines unavailable
        ↓
Kubernetes API unavailable
        ↓
etcd quorum unavailable
        ↓
MetalLB and Traefik unavailable
        ↓
PostgreSQL and application Pods unavailable
        ↓
NFS storage unavailable
        ↓
Entire HavenBridge homelab platform offline
```

Three control-plane virtual machines do not provide protection from a failure
of the single physical machine hosting all three virtual machines.

---

## Full Syrus Recovery Order

Recover the platform in this order:

1. Restore power or repair `syrus`
2. Verify the physical disks
3. Verify the `/data_all` filesystem
4. Restore the libvirt network
5. Restore the libvirt storage pools
6. Start and validate NFS
7. Start the three control-plane virtual machines
8. Start the worker virtual machines
9. Validate Kubernetes and etcd
10. Validate Calico and kube-vip
11. Validate MetalLB and Traefik
12. Validate PVCs and PersistentVolumes
13. Validate PostgreSQL
14. Validate the HavenBridge API

---

## Verify Syrus Storage

Run on `syrus`:

```bash
lsblk -f
```

```bash
findmnt /data_all
```

```bash
df -h /data_all
```

Do not run filesystem-repair commands against a mounted filesystem.

If filesystem damage is suspected, stop and follow the appropriate offline
filesystem-recovery procedure.

---

## Verify libvirt

Run on `syrus`:

```bash
sudo virsh net-list --all
```

```bash
sudo virsh pool-list --all
```

```bash
sudo virsh list --all
```

If the default network is inactive:

```bash
sudo virsh net-start default
```

Start the control-plane virtual machines:

```bash
sudo virsh start eph-cp01
```

```bash
sudo virsh start eph-cp02
```

```bash
sudo virsh start eph-cp03
```

Start the worker virtual machines:

```bash
sudo virsh start eph-worker01
```

```bash
sudo virsh start eph-worker02
```

---

## Validate the Recovered Cluster

Run from `syrus`:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get nodes -o wide'
```

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get pods -A'
```

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get pvc -A;
   kubectl get pv'
```

Validate PostgreSQL tables only after the PostgreSQL Pod is healthy:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl exec \
    --namespace havenbridge \
    havenbridge-postgres-0 \
    --container postgresql \
    -- sh -c '"'"'PGPASSWORD="$(cat "$POSTGRES_PASSWORD_FILE")" \
    psql \
      --host 127.0.0.1 \
      --username "$POSTGRES_USER" \
      --dbname "$POSTGRES_DB" \
      --command "\dt"'"'"''
```

---

## Backup Strategy

The current practical resilience strategy is based on reliable backups and
tested recovery.

It should not be presented as full physical high availability.

### PostgreSQL Backups

Use scheduled logical backups with `pg_dump`.

PostgreSQL backups should be copied to:

* A separate physical disk
* A dedicated NAS
* Another Linux host
* Encrypted remote storage
* Secure cloud object storage

A backup stored only under `/data_all` on `syrus` is not independent of the
primary host.

Copying live PostgreSQL database files is not a replacement for a
database-consistent PostgreSQL backup.

### etcd Backups

Create scheduled etcd snapshots.

Store copies outside `syrus`.

etcd snapshots are required to recover Kubernetes cluster state, including:

* Kubernetes objects
* Deployments
* StatefulSets
* Services
* Secrets
* ConfigMaps
* PersistentVolumeClaims
* Custom resources

### Configuration Backups

The following should remain in Git or protected backups:

* Terraform configuration
* Ansible configuration
* Kubernetes manifests
* Helm values
* Runbooks
* Architecture documentation
* Non-secret application configuration

Never commit:

* PostgreSQL passwords
* Private SSH keys
* kubeconfig files
* Kubernetes join tokens
* Certificate keys
* Application credentials
* Unencrypted backup files containing secrets

### NFS Data Backups

Important NFS data should be copied to a separate physical device or remote
host.

A second directory on the same disk is not an independent backup.

RAID can improve disk availability, but RAID is not a backup.

---

## Resilience Roadmap

### Short Term

* Add UPS protection for `syrus`
* Document clean shutdown and startup procedures
* Monitor physical disk health
* Monitor `/data_all` capacity
* Monitor NFS availability
* Monitor port `2049`
* Schedule PostgreSQL logical backups
* Schedule etcd snapshots
* Copy backups away from `syrus`
* Test restoration procedures

### Medium Term

* Move NFS to a dedicated NAS or second Linux host
* Replicate important storage data
* Create an active/passive recovery procedure
* Use a stable NFS DNS name or virtual address for future volumes
* Keep backup storage independent of the primary NFS server

### Long Term

* Run Kubernetes nodes across independent physical hosts
* Use Longhorn, Rook-Ceph, highly available NFS or managed cloud storage
* Distribute storage replicas across separate hosts and physical disks
* Test node, disk and storage-replica failures

Running Longhorn or Rook-Ceph only inside virtual machines hosted on `syrus`
would not protect the platform from a complete `syrus` failure.

Distributed storage provides host-failure protection only when replicas exist
on independent physical hosts and disks.

---

## Security Notes

* Do not commit PostgreSQL passwords
* Do not store plaintext passwords in this README
* Do not include Secret values in evidence files
* Kubernetes Secret data is Base64-encoded, not automatically encrypted
* Protect database backups because they may contain sensitive application data
* Use read-only Secret mounts where possible
* Restrict access to the NFS export
* Use Kubernetes RBAC to limit access to Secrets and storage resources

---

## Related Documentation

Overall project documentation:

```text
/home/alabi/projects/havenbridge-ha-service-platform/README.md
```

Kubernetes platform documentation:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/README.md
```

API and PostgreSQL validation runbook:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/runbooks/havenbridge-api-postgresql-validation.txt
```

FastAPI documentation:

```text
/home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-api/README.md
```

