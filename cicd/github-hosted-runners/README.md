# HavenBridge GitHub-Hosted Runners

This directory documents how HavenBridge uses GitHub-hosted runners for
continuous integration and release automation.

Unlike the HavenBridge self-hosted CD runner, these runners are created,
managed and destroyed by GitHub.

## Purpose

HavenBridge uses GitHub-hosted runners for workloads that do not require
direct access to the private Kubernetes environment.

They are currently used for:

* continuous integration;
* FastAPI testing;
* Docker image builds;
* Kubernetes manifest validation;
* GitHub Container Registry publishing;
* semantic-version release builds.

The primary runner specification used by HavenBridge is:

```yaml
runs-on: ubuntu-latest
```

## Current Workflows

The GitHub-hosted runner is currently used by:

```text
.github/workflows/ci.yml
```

and:

```text
.github/workflows/release.yml
```

The continuous deployment workflow is intentionally different:

```text
.github/workflows/cd.yml
```

CD uses the dedicated HavenBridge self-hosted runner because the
deployment workflow requires controlled access to the private Kubernetes
cluster.

## CI Runner Flow

The HavenBridge CI workflow is triggered by pushes and pull requests
targeting the `main` branch.

The execution flow is:

```text
Developer change
        ↓
GitHub
        ↓
HavenBridge CI
        ↓
GitHub-hosted ubuntu-latest runner
        ↓
Checkout repository
        ↓
Detect HavenBridge API changes
        ↓
Set up Python
        ↓
Install dependencies
        ↓
Run FastAPI tests
        ↓
Build Docker image
        ↓
Validate Kubernetes manifests
        ↓
Optionally publish SHA-tagged image to GHCR
        ↓
Runner is discarded by GitHub
```

The runner does not remain running after the workflow job completes.

## Release Runner Flow

The HavenBridge Release workflow is triggered when a semantic-version
Git tag matching:

```text
v*.*.*
```

is pushed to GitHub.

For example:

```text
v0.3.0
```

The release flow is:

```text
Git tag
        ↓
HavenBridge Release
        ↓
GitHub-hosted ubuntu-latest runner
        ↓
Run FastAPI tests
        ↓
Build HavenBridge API image
        ↓
Validate Kubernetes manifests
        ↓
Authenticate to GHCR
        ↓
Publish semantic-version image
        ↓
Publish immutable commit-SHA image
        ↓
Runner is discarded by GitHub
```

For the `v0.3.0` release, the release workflow produced both a
human-readable semantic-version tag and an immutable commit-SHA tag.

Example:

```text
ghcr.io/brunobrunt/havenbridge-api:v0.3.0
```

and:

```text
ghcr.io/brunobrunt/havenbridge-api:e3bacb4f602b2adfb97356f2b75be8731c23d8c7
```

The CD workflow deploys the immutable SHA-tagged image so that the exact
source commit running in Kubernetes can be identified.

## Ephemeral Runner Model

GitHub-hosted runners are ephemeral.

The simplified lifecycle is:

```text
Workflow job queued
        ↓
GitHub provisions runner
        ↓
Job executes
        ↓
Job completes
        ↓
Runner is destroyed
```

HavenBridge does not provision these machines with Terraform or manage
them with Ansible.

GitHub manages:

* runner infrastructure;
* operating-system provisioning;
* runner software;
* runner lifecycle;
* base image maintenance.

This is why there is no Terraform or Ansible implementation under this
directory.

## Why GitHub-Hosted Runners Are Used for CI

CI jobs need to:

* check out source code;
* install application dependencies;
* execute automated tests;
* build container images;
* validate Kubernetes manifests.

These operations do not require direct access to the private HavenBridge
Kubernetes API.

Using GitHub-hosted runners therefore avoids unnecessarily exposing the
private Kubernetes environment to CI jobs.

## Why GitHub-Hosted Runners Are Used for Release

The release workflow must build and publish application images to GitHub
Container Registry.

Because GHCR is publicly reachable from GitHub infrastructure, a
GitHub-hosted runner is appropriate for this work.

The release runner does not require the HavenBridge Kubernetes
kubeconfig.

Its responsibility ends after the approved application image has been
successfully published to GHCR.

## Why CD Uses a Self-Hosted Runner Instead

The HavenBridge Kubernetes cluster exists inside the private homelab
network.

The Kubernetes API is available through:

```text
https://k8s-api.lab:6443
```

The CD workflow therefore requires a runner with controlled network
access to the private environment.

For this reason, CD uses:

```text
havenbridge-runner01
```

with the custom GitHub Actions label:

```text
havenbridge-cd
```

The CD job targets it using:

```yaml
runs-on:
  - self-hosted
  - havenbridge-cd
```

## GitHub-Hosted vs Self-Hosted Runners

| Characteristic         | GitHub-Hosted   | HavenBridge Self-Hosted         |
| ---------------------- | --------------- | ------------------------------- |
| Infrastructure owner   | GitHub          | HavenBridge                     |
| Lifecycle              | Ephemeral       | Persistent                      |
| VM provisioning        | GitHub          | Terraform/libvirt               |
| OS configuration       | GitHub          | cloud-init + Ansible            |
| Runner maintenance     | GitHub          | HavenBridge                     |
| Private cluster access | No              | Yes                             |
| Kubernetes kubeconfig  | No              | Restricted kubeconfig           |
| Primary use            | CI and Release  | CD                              |
| Runner specification   | `ubuntu-latest` | `self-hosted`, `havenbridge-cd` |

## Security Boundary

The separation between GitHub-hosted and self-hosted runners is
intentional.

GitHub-hosted CI and Release jobs do not receive Kubernetes
administrative credentials and do not need direct access to the private
cluster.

The self-hosted CD runner receives only the restricted Kubernetes
identity required for deployment.

The architecture is:

```text
                    GitHub
                       |
          +------------+------------+
          |                         |
          v                         v
    GitHub-hosted              GitHub-hosted
      CI runner                Release runner
          |                         |
          |                         v
          |                       GHCR
          |                         |
          +-------------------------+
                                    |
                                    v
                             HavenBridge CD
                                    |
                                    v
                         havenbridge-runner01
                                    |
                                    v
                            github-runner
                                    |
                                    v
                       restricted kubeconfig
                                    |
                                    v
                        havenbridge-deployer
                                    |
                                    v
                          Kubernetes cluster
```

## Design Decision

HavenBridge intentionally separates build infrastructure from deployment
infrastructure.

CI and Release use ephemeral GitHub-hosted runners because they do not
need private-cluster access.

CD uses a persistent self-hosted runner because deployment requires
controlled connectivity to the internal Kubernetes API.

This limits the number of systems that possess Kubernetes credentials and
creates a clear security boundary between building an application and
deploying it.

## Related Documentation

Self-hosted runner implementation:

```text
cicd/self-hosted-runner/README.md
```

Continuous deployment documentation:

```text
cicd/cd/README.md
```

GitHub Actions workflows:

```text
.github/workflows/ci.yml
.github/workflows/release.yml
.github/workflows/cd.yml
```
