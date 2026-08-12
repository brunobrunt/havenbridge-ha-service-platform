# HavenBridge CI/CD

This directory documents the Continuous Integration and Continuous Deployment
architecture used by the HavenBridge platform.

The purpose of the CI/CD pipeline is to automatically validate application
changes, build container images, publish approved images to GitHub Container
Registry and deploy approved releases to the HavenBridge Kubernetes cluster.

## CI/CD Architecture

```text
Developer
   ↓
git push / pull request
   ↓
GitHub
   ↓
┌──────────────────────────────────────┐
│ GitHub-hosted runner                 │
│                                      │
│  CI                                  │
│  ├─ Checkout source                  │
│  ├─ Set up Python                    │
│  ├─ Install dependencies             │
│  ├─ Run tests                        │
│  ├─ Validate Docker build            │
│  └─ Validate Kubernetes manifests    │
└─────────────────┬────────────────────┘
                  ↓
             main approved
                  ↓
             Build image
                  ↓
                GHCR
                  ↓
┌──────────────────────────────────────┐
│ Self-hosted HavenBridge runner       │
│                                      │
│  CD                                  │
│  ├─ Pull/deploy approved version     │
│  ├─ kubectl apply / update image     │
│  ├─ Watch rollout                    │
│  └─ HTTPS health validation          │
└─────────────────┬────────────────────┘
                  ↓
          HavenBridge Kubernetes
```

## What CI Means

Continuous Integration validates application changes before they are accepted
as deployable HavenBridge releases.

The CI portion of the pipeline will run on a GitHub-hosted runner.

Its responsibilities will include:

```text
Checkout source code
        ↓
Set up Python
        ↓
Install dependencies
        ↓
Run application tests
        ↓
Validate Docker build
        ↓
Validate Kubernetes manifests
```

CI answers the question:

> Is this change safe and technically valid enough to continue through the
> delivery pipeline?

## What CD Means

Continuous Deployment handles delivery of an approved application version to
the HavenBridge Kubernetes environment.

Because the HavenBridge Kubernetes cluster runs inside the private homelab,
deployment requires a runner that can reach that environment.

The CD portion will therefore use a HavenBridge self-hosted GitHub Actions
runner.

Its responsibilities will include:

```text
Receive approved release
        ↓
Deploy approved image
        ↓
Update Kubernetes workload
        ↓
Watch Deployment rollout
        ↓
Verify Pods become Ready
        ↓
Validate HTTPS health endpoint
```

CD answers the question:

> Can the approved HavenBridge release be deployed successfully and verified
> in Kubernetes?

## Why Two Runner Types Are Used

“I separated CI and CD runners because CI only needed an isolated build environment, while CD required controlled access to the private Kubernetes network.”

The pipeline separates public CI work from private cluster deployment.

```text
GitHub-hosted runner
        =
Build and validation environment

Self-hosted HavenBridge runner
        =
Private deployment environment
```

The GitHub-hosted runner does not need direct administrative access to the
HavenBridge Kubernetes cluster.

The self-hosted runner will have controlled access to the homelab environment
required for deployment.

This separation reduces the amount of Kubernetes access exposed to the CI
portion of the pipeline.

## Container Registry

HavenBridge container images are stored in GitHub Container Registry.

```text
GitHub Actions
      ↓
Docker build
      ↓
GHCR
      ↓
ghcr.io/brunobrunt/havenbridge-api:<version>
      ↓
Kubernetes
```

The existing manually published image:

```text
ghcr.io/brunobrunt/havenbridge-api:0.1.0
```

provides the starting point.

Phase 6 will automate the process that was previously performed manually.

## Planned Pipeline Stages

The HavenBridge CI/CD implementation will be built incrementally.

### Stage 1 — CI Foundation

```text
Git push / pull request
        ↓
Checkout repository
        ↓
Set up Python
        ↓
Install dependencies
        ↓
Run tests
```

### Stage 2 — Build Validation

```text
CI succeeds
        ↓
Build Docker image
        ↓
Validate image build
```

### Stage 3 — Kubernetes Manifest Validation

```text
Application validation
        ↓
Validate Kubernetes YAML
        ↓
Reject invalid manifests
```

### Stage 4 — GHCR Publication

```text
Approved main branch
        ↓
Build versioned image
        ↓
Authenticate to GHCR
        ↓
Push image
```

### Stage 5 — Kubernetes Deployment

```text
Approved image
        ↓
Self-hosted runner
        ↓
Deploy to HavenBridge
        ↓
kubectl rollout status
```

### Stage 6 — Post-Deployment Validation

```text
Deployment completed
        ↓
Pods Ready
        ↓
Service available
        ↓
HTTPS health check
        ↓
https://havenbridge.lab/health/ready
        ↓
HTTP 200
```

## Final Delivery Goal

The completed Phase 6 delivery path will be:

```text
Code change
   ↓
GitHub
   ↓
Automated CI
   ↓
Tests pass
   ↓
Docker image built
   ↓
Image published to GHCR
   ↓
Automated Kubernetes deployment
   ↓
Rollout succeeds
   ↓
HTTPS health validation succeeds
```

The pipeline will be implemented and validated one stage at a time rather than
introducing the complete deployment automation at once.
