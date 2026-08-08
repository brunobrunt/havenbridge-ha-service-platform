# HavenBridge GitHub Container Registry Runbook

This runbook documents how the HavenBridge API container image is prepared,
tagged, authenticated, published and validated using GitHub Container Registry.

## Registry Details

```text
Registry: ghcr.io
GitHub account: brunobrunt
Repository: havenbridge-ha-service-platform
Local image: havenbridge-api:0.1.0
Registry image: ghcr.io/brunobrunt/havenbridge-api:0.1.0
```

## Authenticate Docker to GHCR

A GitHub personal access token was created with the `write:packages` scope.

The token must never be stored in the repository, Dockerfile, README or shell
history.

Run on `syrus`:

```bash
read -rsp "GitHub Container Registry token: " CR_PAT
echo
```

Authenticate Docker:

```bash
printf '%s' "$CR_PAT" |
docker login ghcr.io \
  --username brunobrunt \
  --password-stdin
```

Expected:

```text
Login Succeeded
```

Remove the token from the current shell variable:

```bash
unset CR_PAT
```

## Authentication Status

Completed:

* [x] GitHub Container Registry token created
* [x] Docker authenticated to `ghcr.io`
* [x] Token removed from the active shell variable

Do not record the actual token in this runbook.

## Docker Credential Warning

Docker reported that the registry credential is stored in:

```text
/home/alabi/.docker/config.json
```

This file must not be added to the HavenBridge Git repository.

A Docker credential helper can be configured later to avoid storing registry
credentials directly in Docker's configuration file.


## Add GitHub Container Registry Metadata

The Dockerfile was updated with Open Container Initiative metadata so GitHub
Container Registry can associate the image with its source repository.

Dockerfile:

```text

LABEL org.opencontainers.image.source="https://github.com/brunobrunt/havenbridge-ha-service-platform" \
      org.opencontainers.image.description="FastAPI backend for the HavenBridge service inquiry and referral tracking platform"


## Verify OCI Image Labels

Confirm that the rebuilt image contains the GitHub Container Registry metadata:

```bash
docker inspect  havenbridge-api:0.1.0  --format '{{range $key, $value := .Config.Labels}}{{printf "%s=%s\n" $key $value}}{{end}}'

##  confirm the non-root user is still configured:
docker run   --rm   --entrypoint id   havenbridge-api:0.1.0
uid=100(havenbridge) gid=101(havenbridge) groups=101(havenbridge)


## Revalidate the Non-Root Container User

After rebuilding the image with OCI metadata, confirm that the image still runs
as the dedicated non-root user:

```bash
docker run \
  --rm \
  --entrypoint id \
  havenbridge-api:0.1.0

## GHCR Package Page

The published HavenBridge API package is available at:

```text
https://github.com/users/brunobrunt/packages/container/package/havenbridge-api

## Validate the GHCR Image from Kubernetes

An initial attempt to use `ctr` directly on `eph-worker01` failed because the
`ctr` command was not installed or available in the worker's command path.

Kubernetes was therefore used to perform the registry pull test.

Create a temporary Pod:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl run ghcr-pull-test \
    --namespace havenbridge \
    --image=ghcr.io/brunobrunt/havenbridge-api:0.1.0 \
    --image-pull-policy=Always \
    --restart=Never \
    --command \
    -- id'

ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl logs \
    ghcr-pull-test \
    --namespace havenbridge'

## output
uid=100(havenbridge) gid=101(havenbridge) groups=101(havenbridge)

Kubernetes can pull the public GHCR image
No Kubernetes imagePullSecret is required
The image starts successfully on a worker node
The image continues to run as a non-root user

## Confirm the Kubernetes Container Runtime

The HavenBridge Kubernetes nodes use CRI-O rather than containerd.

Runtime validation:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get nodes \
    --output custom-columns="NODE:.metadata.name,RUNTIME:.status.nodeInfo.containerRuntimeVersion"'
```

Validated result:

```text
NODE           RUNTIME
eph-cp01       cri-o://1.36.2
eph-cp02       cri-o://1.36.2
eph-cp03       cri-o://1.36.2
eph-worker01   cri-o://1.36.2
eph-worker02   cri-o://1.36.2
```

The runtime service was confirmed on `eph-worker01`:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.34 \
  'sudo systemctl status crio --no-pager'
```

Validated state:

```text
crio.service
Active: active (running)
Enabled: yes
```

The Kubernetes-compatible runtime troubleshooting client is also installed:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.34 \
  'command -v crictl &&
   sudo crictl --version'
```

Validated result:

```text
/usr/local/bin/crictl
crictl version v1.36.0
```

`ctr` is a containerd-specific tool and is not required for this CRI-O-based
cluster.

The correct runtime path is:

```text
Kubernetes
    ↓
kubelet
    ↓
Container Runtime Interface
    ↓
CRI-O
    ↓
OCI runtime
    ↓
Linux container
```

Container images are cached separately on each Kubernetes node. The
`ghcr-pull-test` Pod ran on `eph-worker02`, so the HavenBridge image should
appear in the CRI-O image list on that worker rather than automatically
appearing on `eph-cp01`.

