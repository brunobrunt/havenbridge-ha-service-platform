## PostgreSQL Persistent Storage

HavenBridge uses PostgreSQL as its application database. PostgreSQL runs as a Kubernetes StatefulSet because a database requires stable storage and a predictable Pod identity.

### Why a StatefulSet?

A Deployment is normally used for interchangeable application Pods. PostgreSQL is different because its database files must remain attached to the correct database instance.

The StatefulSet provides:

* A predictable Pod name: `havenbridge-postgres-0`
* A persistent volume claim created from `volumeClaimTemplates`
* Reattachment of the same storage when the PostgreSQL Pod is recreated
* Controlled startup and shutdown of the database Pod

The storage flow is:

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

The active storage resources are:

```text
PVC: postgres-data-havenbridge-postgres-0
PV:  pvc-ff29106d-5d97-424f-b6b3-2432df3a176e
Size: 10 GiB
Access mode: ReadWriteOnce
StorageClass: havenbridge-nfs
Reclaim policy: Retain
```

### Init Container

The PostgreSQL Pod includes an init container named:

```text
prepare-data-directory
```

An init container runs before the main PostgreSQL container.

Its purpose is to:

1. Create the PostgreSQL data directory when necessary.
2. Set the directory owner to PostgreSQL UID and GID `999`.
3. Apply secure `0700` permissions.
4. Exit before PostgreSQL starts.

The main PostgreSQL container runs as a non-root user. The short-lived init container prepares the NFS-mounted directory so PostgreSQL can write to it safely.

The init command was optimized to change only the PostgreSQL data directory:

```bash
chown 999:999 "${DATA_DIRECTORY}"
```

A previous version used recursive ownership changes:

```bash
chown -R 999:999 /var/lib/postgresql
```

The recursive command caused slow Pod startup because it processed every PostgreSQL file across the NFS mount whenever the Pod was recreated.

### Health Probes

The PostgreSQL container uses three health probes:

* The startup probe allows first-time database initialization to finish.
* The readiness probe confirms the `havenbridge` database accepts SQL queries.
* The liveness probe confirms that the PostgreSQL server is responding.

Initial database creation over NFS took longer than the original five-minute startup window. Kubernetes restarted the container before initialization completed, leaving a partially initialized database directory.

The startup probe was increased to:

```yaml
periodSeconds: 5
failureThreshold: 180
```

This provides a maximum startup window of 15 minutes for first-time initialization.

### Persistence Validation

Persistence was validated using a synthetic table:

```sql
CREATE TABLE platform_validation (
    id          BIGSERIAL PRIMARY KEY,
    message     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

A synthetic validation record was inserted:

```text
HavenBridge PostgreSQL persistence validation
```

The PostgreSQL Pod was then deleted. The StatefulSet recreated `havenbridge-postgres-0` and reattached the existing PVC.

After the recreated Pod became ready, the original record was queried successfully:

```text
ID: 1
Message: HavenBridge PostgreSQL persistence validation
Created: 2026-07-27 03:33:14.395938+00
```

This confirms that PostgreSQL data survives Pod deletion and recreation.

### Validation Result

```text
Pod deleted
    ↓
StatefulSet recreated the Pod
    ↓
Existing PVC reattached
    ↓
PostgreSQL reopened the NFS-backed data directory
    ↓
Database record survived
```

PostgreSQL persistent storage validation: **Passed**

