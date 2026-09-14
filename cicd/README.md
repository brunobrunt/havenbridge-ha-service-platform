# HavenBridge CI/CD

This directory documents the Continuous Integration and Continuous Deployment
architecture used by the HavenBridge HA Service Platform.

The CI/CD implementation validates HavenBridge application changes, builds and
publishes versioned container images, creates semantic application releases,
and deploys approved releases to the private HavenBridge Kubernetes cluster.

The current implementation separates:

- Continuous Integration on GitHub-hosted runners.
- Release automation on GitHub-hosted runners.
- Continuous Deployment on a dedicated self-hosted runner.
- Kubernetes authentication through a restricted ServiceAccount and
  namespace-scoped RBAC.
- Human-readable semantic release tags from Git commit provenance.
- Runtime image identification through the immutable container digest.

---

## CI/CD Architecture

```text
Developer
   ↓
git push / pull request
   ↓
GitHub
   ↓
┌───────────────────────────────────────────────┐
│ HavenBridge CI                               │
│ GitHub-hosted runner                         │
│                                               │
│  ├─ Checkout source                          │
│  ├─ Set up Python                            │
│  ├─ Install dependencies                     │
│  ├─ Run FastAPI tests                        │
│  ├─ Validate Docker build                    │
│  └─ Validate Kubernetes manifests            │
└──────────────────────┬────────────────────────┘
                       ↓
                 CI succeeds
                       ↓
┌───────────────────────────────────────────────┐
│ HavenBridge Release                          │
│ GitHub-hosted runner                         │
│                                               │
│  ├─ Determine whether a release is required  │
│  ├─ Calculate semantic version               │
│  ├─ Build release image                      │
│  ├─ Publish semantic tag to GHCR             │
│  ├─ Publish commit-SHA tag to GHCR           │
│  └─ Create/push annotated Git tag            │
└──────────────────────┬────────────────────────┘
                       ↓
              successful release
                       ↓
┌───────────────────────────────────────────────┐
│ HavenBridge CD                               │
│ Self-hosted runner                           │
│ havenbridge-runner01                         │
│                                               │
│  ├─ Verify release commit SHA                │
│  ├─ Resolve semantic release tag             │
│  ├─ Verify Kubernetes access                 │
│  ├─ Deploy semantic-version image            │
│  ├─ Watch Kubernetes rollout                 │
│  └─ Verify deployed image                    │
└──────────────────────┬────────────────────────┘
                       ↓
              HavenBridge Kubernetes
                       ↓
          ghcr.io/.../havenbridge-api:vX.Y.Z
                       ↓
               CRI-O image digest
```

The important design decision is that release provenance and the Kubernetes
deployment reference are related but serve different purposes:

```text
RELEASE_SHA
    =
exact source-code provenance and release verification

RELEASE_TAG
    =
human-readable Kubernetes deployment version

ImageID / sha256 digest
    =
immutable runtime container artifact
```

---

## Repository Location

The CI/CD implementation is maintained under:

```text
/home/alabi/projects/havenbridge-ha-service-platform
```

The primary CI/CD documentation is:

```text
cicd/README.md
```

Key workflow files are:

```text
.github/workflows/ci.yml
.github/workflows/release.yml
.github/workflows/cd.yml
```

The semantic-version calculator is:

```text
cicd/scripts/next-version.sh
```

The self-hosted runner implementation is documented in:

```text
cicd/self-hosted-runner/README.md
```

---

## CI/CD Directory Structure

```text
cicd/
├── README.md
├── github-actions-simple-concepts.txt
├── github-hosted-runners/
│   └── README.md
├── scripts/
│   └── next-version.sh
├── self-hosted-runner/
│   ├── README.md
│   └── evidence/
│       ├── automated-release-no-release-validation.txt
│       └── kubernetes-rbac-validation.txt
└── evidence/
    ├── ci-foundation/
    │   ├── github-actions-ci-validation-results.txt
    │   └── github-actions-ci-validation-steps.txt
    ├── docker-build/
    │   ├── github-actions-docker-build-validation-results.txt
    │   └── github-actions-docker-build-validation-steps.txt
    ├── ghcr-change-detection/
    │   ├── gha-ghcr-change-detection-results.txt
    │   └── gha-ghcr-change-detection-steps.txt
    ├── ghcr-publication/
    │   ├── gha-ghcr-publication-results.txt
    │   └── gha-ghcr-publication-steps.txt
    ├── k8s-manifest-validation/
    │   ├── gha-k8s-manifest-validation-results.txt
    │   └── gha-k8s-manifest-validation-steps.txt
    ├── semver-release/
    │   ├── gha-semver-release-results.txt
    │   └── gha-semver-release-steps.txt
    └── cd-deployment/
        ├── v0.3.0-deployment-validation.txt
        ├── v0.4.0-deployment-validation.txt
        ├── v0.5.0-version-reporting-validation.txt
        ├── v0.6.0-automated-semantic-release-validation.txt
        └── v0.8.0-semantic-tag-deployment-validation.txt
```

---

## What Continuous Integration Means

Continuous Integration validates changes before they are treated as a
deployable HavenBridge application release.

CI answers:

> Is this change technically valid enough to continue through the delivery
> pipeline?

The CI workflow performs application and deployment validation without needing
administrative access to the private Kubernetes cluster.

Typical CI flow:

```text
Checkout source
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

CI is intentionally separated from private-cluster deployment.

---

## What the Release Stage Means

The Release stage turns eligible application changes into an intentional,
versioned HavenBridge application release.

It is responsible for:

```text
Determine whether application release is required
        ↓
Calculate semantic version
        ↓
Build release image
        ↓
Validate release
        ↓
Publish semantic-version image
        ↓
Publish commit-SHA image
        ↓
Create annotated Git tag
        ↓
Push Git tag
```

Release automation does not mean that every repository change becomes an
application release.

Changes such as documentation-only, CI/CD-only, or maintenance commits can
complete without creating a new HavenBridge API version.

---

## What Continuous Deployment Means

Continuous Deployment delivers a successfully created HavenBridge application
release to the private Kubernetes environment.

CD answers:

> Can the released HavenBridge version be deployed successfully and verified
> in Kubernetes?

The CD workflow runs on the self-hosted runner because the Kubernetes API is
inside the private homelab network.

Current deployment flow:

```text
Successful HavenBridge Release
        ↓
Verify release SHA
        ↓
Find semantic Git tag for that release SHA
        ↓
Confirm tag points to the expected commit
        ↓
Self-hosted runner
        ↓
Restricted Kubernetes identity
        ↓
Deploy semantic release image
        ↓
Wait for rollout
        ↓
Verify deployed semantic image
```

---

## Why Two Runner Types Are Used

HavenBridge separates CI/release execution from private-cluster deployment.

```text
GitHub-hosted runner
        =
build, test, validation and release publication

Self-hosted HavenBridge runner
        =
private Kubernetes deployment
```

This design limits how much private Kubernetes access is exposed to the public
CI environment.

A concise explanation is:

> I separated CI and CD runners because CI only needs an isolated build
> environment, while CD requires controlled access to the private Kubernetes
> network.

---

## GitHub Actions Workflows

### HavenBridge CI

Path:

```text
.github/workflows/ci.yml
```

Purpose:

- Test application changes.
- Validate the Docker build.
- Validate Kubernetes manifests.
- Prevent invalid application changes from progressing.

### HavenBridge Release

Path:

```text
.github/workflows/release.yml
```

Purpose:

- Operate on the source revision validated by CI.
- Determine whether the change requires an application release.
- Calculate the next semantic version.
- Build the release image.
- Publish both semantic-version and commit-SHA tags to GHCR.
- Create and push the annotated Git release tag.

The workflow also retains manual execution as a fallback where configured.

### HavenBridge CD

Path:

```text
.github/workflows/cd.yml
```

Purpose:

- React only to a successful HavenBridge Release.
- Verify whether a semantic application release was actually created.
- Validate release provenance.
- Deploy the semantic-version image.
- Wait for the Kubernetes rollout.
- Verify that Kubernetes references the expected release tag.

---

## Container Registry

HavenBridge container images are stored in GitHub Container Registry:

```text
ghcr.io/brunobrunt/havenbridge-api
```

A semantic release is represented by a human-readable image tag such as:

```text
ghcr.io/brunobrunt/havenbridge-api:v0.8.0
```

The same release can also retain a Git commit SHA tag for source-code
traceability.

Example:

```text
Semantic release:
ghcr.io/brunobrunt/havenbridge-api:v0.8.0

Source revision:
ghcr.io/brunobrunt/havenbridge-api:<git-commit-sha>
```

Both tags can identify the same underlying container image.

---

## Container Image Versioning Strategy

HavenBridge combines three identifiers:

1. Semantic version.
2. Git commit SHA.
3. Immutable container digest.

They have different purposes.

```text
Semantic version
v0.8.0
        ↓
human-readable application release

Git commit SHA
<40-character-sha>
        ↓
source-code provenance

Container digest
sha256:<digest>
        ↓
exact immutable runtime artifact
```

The design avoids using `latest` as the primary production-style deployment
reference because `latest` is mutable and does not communicate which release
is intended.

---

## Semantic Versioning

HavenBridge application releases follow:

```text
MAJOR.MINOR.PATCH
```

Example:

```text
v0.8.0
```

### PATCH

A PATCH release represents a backward-compatible bug fix or correction.

Example:

```text
v0.8.0
    ↓
v0.8.1
```

Typical HavenBridge examples include:

- Fixing request validation.
- Correcting API error handling.
- Fixing logging behavior.
- Correcting a small database query issue.

### MINOR

A MINOR release represents new backward-compatible functionality.

Example:

```text
v0.8.1
    ↓
v0.9.0
```

Typical examples include:

- Adding a new API endpoint.
- Adding referral functionality.
- Adding coordinator functionality.
- Adding a new application workflow.

### MAJOR

A MAJOR release represents an incompatible or deliberately breaking change.

Example:

```text
v1.6.4
    ↓
v2.0.0
```

Possible examples include:

- Incompatible API redesign.
- Removal of previously supported behavior.
- Major application architecture changes.
- Breaking integration or data-model changes.

---

## Why HavenBridge Uses 0.x Versions

HavenBridge is still under active development.

Versions such as:

```text
v0.3.0
v0.4.0
v0.5.0
v0.6.0
v0.8.0
```

communicate that the application and delivery platform are still evolving.

A future `v1.0.0` can represent the point at which the HavenBridge application
is considered stable enough for its first major baseline.

---

## A Git Push Does Not Automatically Mean an Application Release

Repository activity and application releases are deliberately separated.

For example:

```text
README update
        ↓
git push
        ↓
CI validation
        ↓
no HavenBridge API release required
```

Likewise, changes limited to CI/CD documentation or workflow maintenance should
not automatically increase the HavenBridge application version.

Semantic versions represent application releases rather than every Git commit.

---

## Semantic Version Calculator

Path:

```text
cicd/scripts/next-version.sh
```

The calculator examines HavenBridge API application history and applies release
rules based on conventional commits.

Current release rules include:

```text
fix:    → PATCH
feat:   → MINOR
feat!:  → MAJOR
```

Non-release changes such as:

```text
docs:
test:
chore:
```

do not create an application release by themselves.

The calculator exposes values to GitHub Actions through `GITHUB_OUTPUT`.

---

## No-Release Guard

The release process includes an explicit no-release path.

```text
HavenBridge CI succeeds
        ↓
HavenBridge Release starts
        ↓
next-version.sh
        ↓
No release-causing application commit
        ↓
release_needed=false
        ↓
No semantic Git tag created
        ↓
No application image deployment required
```

This behavior prevents CI/CD-only and documentation-only changes from creating
false HavenBridge application releases.

Evidence is stored in:

```text
cicd/self-hosted-runner/evidence/automated-release-no-release-validation.txt
```

---

## Build-Once Principle

HavenBridge follows a build-once approach where possible.

```text
Build image
        ↓
Validate image
        ↓
Tag validated image
        ↓
Publish the same image
```

This avoids validating one artifact and independently rebuilding a different
artifact for release.

The release can then receive multiple identifiers:

```text
Container image
    ├── v0.8.0
    └── <git-commit-sha>
```

while the registry/runtime digest identifies the immutable contents.

---

## Git Commit SHA Image Tags

The commit SHA remains an important part of the release model.

A Git SHA provides a direct connection to the source revision:

```text
Git commit
        ↓
40-character SHA
        ↓
release image
        ↓
semantic tag
```

The SHA is retained for provenance even though Kubernetes now uses the semantic
release tag as its visible Deployment image reference.

---

## Semantic Version Tag and Git SHA Together

A release can be represented by both:

```text
ghcr.io/brunobrunt/havenbridge-api:v0.8.0
```

and:

```text
ghcr.io/brunobrunt/havenbridge-api:<git-commit-sha>
```

The semantic tag answers:

> Which HavenBridge release is this?

The Git SHA answers:

> Which exact source revision produced this release?

---

## Image Digest

CRI-O and the container registry identify the exact image artifact using a
content digest.

Example from the validated `v0.8.0` deployment:

```text
Image:
ghcr.io/brunobrunt/havenbridge-api:v0.8.0

ImageID:
ghcr.io/brunobrunt/havenbridge-api@sha256:9830854685b118be4bd9a8a1a2a0048eb5a6a3d32e2a9f8f72f21f8d82e6826c
```

The semantic tag is operationally readable while the digest remains immutable.

---

## Current HavenBridge Tagging Policy

The current strategy is:

```text
Application release
        ↓
Semantic version calculated
        ↓
Release image built
        ↓
Image receives semantic version tag
        +
Image receives Git SHA tag
        ↓
Both published to GHCR
        ↓
CD verifies SHA provenance
        ↓
CD deploys semantic tag
        ↓
CRI-O records immutable digest
```

---

## Release-to-CD Trigger

The CD workflow is triggered by completion of the `HavenBridge Release`
workflow rather than directly by every normal push to `main`.

Conceptually:

```yaml
on:
  workflow_run:
    workflows:
      - HavenBridge Release
    types:
      - completed
```

The CD workflow first determines whether the successful Release run actually
created a semantic-version application release.

If no release tag exists for the release commit, CD finishes without changing
the Kubernetes workload.

This prevents a successful no-op Release run from redeploying the application.

---

## Release Verification Before Deployment

CD receives the release source SHA from the completed Release workflow:

```yaml
RELEASE_SHA: ${{ github.event.workflow_run.head_sha }}
```

It also resolves the semantic release tag associated with that commit.

The release verification stage checks that:

```text
RELEASE_SHA is a valid Git SHA
        ↓
semantic release tag exists
        ↓
tag resolves to RELEASE_SHA
        ↓
release is eligible for deployment
```

This means semantic-tag deployment does not remove source-code provenance.

Instead:

```text
RELEASE_SHA
        =
provenance validation

RELEASE_TAG
        =
deployment reference
```

---

## CD Runner Identity

The deployment job runs on:

```text
havenbridge-runner01
IP: 172.16.10.37
```

The GitHub Actions service runs as:

```text
github-runner
```

The runner uses the custom GitHub Actions label:

```text
havenbridge-cd
```

The runner service is:

```text
actions.runner.brunobrunt-havenbridge-ha-service-platform.havenbridge-runner01.service
```

The service has been validated as enabled and active and has successfully
reported:

```text
Connected to GitHub
Listening for Jobs
```

Detailed implementation:

```text
cicd/self-hosted-runner/README.md
```

---

## Restricted Kubernetes Authentication

The self-hosted runner does not use Kubernetes administrator credentials.

The runner uses:

```text
/home/github-runner/.kube/config
```

Ownership:

```text
github-runner:github-runner
```

Permissions:

```text
600
```

The Kubernetes identity is:

```text
system:serviceaccount:havenbridge:havenbridge-deployer
```

The identity is implemented with:

```text
ServiceAccount
        ↓
Role
        ↓
RoleBinding
```

The manifests are maintained under:

```text
kubernetes/platform/rbac/cd-runner/
```

The Role grants only the deployment permissions required by CD.

The identity can perform required Deployment operations but cannot read
Kubernetes Secrets.

---

## Least-Privilege Validation

The HavenBridge CD identity was validated with both a positive and negative
authorization test.

### Positive Deployment Test

**Host: `havenbridge-runner01`**

```bash
sudo -u github-runner \
  KUBECONFIG=/home/github-runner/.kube/config \
  kubectl get deployment havenbridge-api \
  -n havenbridge
```

Expected and validated behavior:

```text
NAME              READY   UP-TO-DATE   AVAILABLE
havenbridge-api   2/2     2            2
```

### Negative Secret Test

**Host: `havenbridge-runner01`**

```bash
sudo -u github-runner \
  KUBECONFIG=/home/github-runner/.kube/config \
  kubectl get secrets \
  -n havenbridge
```

Validated result:

```text
Error from server (Forbidden)
```

This proves that CD has the deployment permissions it needs without broad
Secret access.

Detailed evidence:

```text
cicd/self-hosted-runner/evidence/kubernetes-rbac-validation.txt
```

A concise explanation is:

> I created a dedicated Kubernetes ServiceAccount for CD. A namespace-scoped
> Role grants only the deployment permissions it needs, and a RoleBinding
> connects the identity to those permissions. I then tested both positive and
> negative authorization cases to prove least privilege.

---

## Why CD Deploys the Semantic Release Tag

Earlier HavenBridge CD releases deployed the commit-SHA-tagged container image
directly.

That approach provided excellent source traceability, but an operator looking
at Kubernetes would see a value such as:

```text
ghcr.io/brunobrunt/havenbridge-api:aeab8e5f81f88689f1c0e00834492500367b5023
```

rather than the application release version.

The current CD implementation keeps SHA-based provenance validation but deploys
the semantic release tag.

For the validated `v0.8.0` release:

```text
RELEASE_TAG:
v0.8.0
```

Kubernetes now displays:

```text
ghcr.io/brunobrunt/havenbridge-api:v0.8.0
```

while CRI-O records:

```text
ghcr.io/brunobrunt/havenbridge-api@sha256:9830854685b118be4bd9a8a1a2a0048eb5a6a3d32e2a9f8f72f21f8d82e6826c
```

The current relationship is:

```text
Git release commit
        ↓
RELEASE_SHA
        ↓
release provenance validation
        ↓
RELEASE_TAG
        ↓
ghcr.io/brunobrunt/havenbridge-api:v0.8.0
        ↓
Kubernetes Deployment
        ↓
CRI-O immutable image digest
```

This provides readable release identification without discarding traceability.

---

## CD Workflow Environment

The CD deployment job uses:

```text
KUBECONFIG=/home/github-runner/.kube/config
NAMESPACE=havenbridge
DEPLOYMENT=havenbridge-api
CONTAINER=havenbridge-api
RELEASE_SHA=<release commit SHA>
RELEASE_TAG=<semantic release tag>
```

`RELEASE_SHA` identifies the exact source revision that produced the release.

`RELEASE_TAG` is the human-readable application release that CD deploys to
Kubernetes.

---

## CD Workflow Step-by-Step

### Step 1 — Verify the Release

**Execution context: GitHub Actions / CD workflow**

The workflow verifies the successful Release run and determines whether a
semantic release was actually created.

A successful no-op Release does not cause a Kubernetes deployment.

### Step 2 — Validate the Release SHA

**Execution context: GitHub Actions / CD workflow**

`RELEASE_SHA` must be a valid 40-character hexadecimal Git SHA.

Invalid values stop deployment.

### Step 3 — Resolve the Semantic Release Tag

**Execution context: GitHub Actions / CD workflow**

The workflow finds the semantic version tag pointing at `RELEASE_SHA`.

Example:

```text
RELEASE_SHA=<release commit>
        ↓
release tag lookup
        ↓
RELEASE_TAG=v0.8.0
```

The tag is then checked to ensure it resolves to the expected release commit.

### Step 4 — Show Runner Identity

**Execution context: `havenbridge-runner01` through GitHub Actions**

The workflow displays:

```text
Runner hostname
Runner operating-system user
Release tag
Release SHA
```

This confirms deployment is executing on the expected self-hosted runner with
the expected release information.

### Step 5 — Verify Kubernetes Access

**Execution context: `havenbridge-runner01` through GitHub Actions**

Equivalent command:

```bash
kubectl get deployment havenbridge-api \
  -n havenbridge
```

This proves the runner can reach the Kubernetes API and authenticate using the
restricted identity.

### Step 6 — Show the Currently Deployed Image

**Execution context: `havenbridge-runner01` through GitHub Actions**

The workflow reads the existing Deployment image before modifying Kubernetes.

This preserves a before-and-after deployment record in the Actions log.

### Step 7 — Construct the Semantic Release Image

**Execution context: `havenbridge-runner01` through GitHub Actions**

Current logic:

```bash
IMAGE="ghcr.io/brunobrunt/havenbridge-api:${RELEASE_TAG}"
```

For `v0.8.0`:

```text
ghcr.io/brunobrunt/havenbridge-api:v0.8.0
```

The release SHA remains available separately for provenance validation.

### Step 8 — Update the Kubernetes Deployment

**Execution context: `havenbridge-runner01` through GitHub Actions**

Equivalent operation:

```bash
kubectl set image \
  deployment/"${DEPLOYMENT}" \
  "${CONTAINER}"="${IMAGE}" \
  -n "${NAMESPACE}"
```

With `v0.8.0`, the effective image is:

```text
ghcr.io/brunobrunt/havenbridge-api:v0.8.0
```

Changing the Pod template causes Kubernetes to create a new rollout.

### Step 9 — Wait for the Rollout

**Execution context: `havenbridge-runner01` through GitHub Actions**

```bash
kubectl rollout status \
  deployment/"${DEPLOYMENT}" \
  -n "${NAMESPACE}" \
  --timeout=180s
```

CD does not report deployment success merely because the Deployment was
patched. The workload must roll out successfully.

### Step 10 — Verify the Deployed Image

**Execution context: `havenbridge-runner01` through GitHub Actions**

Current expected-image logic:

```bash
EXPECTED="ghcr.io/brunobrunt/havenbridge-api:${RELEASE_TAG}"
```

The workflow reads the image currently configured on the Deployment and
compares it with `EXPECTED`.

For `v0.8.0`:

```text
Expected:
ghcr.io/brunobrunt/havenbridge-api:v0.8.0

Actual:
ghcr.io/brunobrunt/havenbridge-api:v0.8.0
```

If the values differ, the CD workflow fails.

---

## CD Security Decisions

The CD workflow intentionally minimizes access.

Key decisions include:

- Deployment occurs only through the dedicated self-hosted runner.
- The runner uses a dedicated Linux account.
- Kubernetes authentication uses a dedicated ServiceAccount.
- RBAC is namespace-scoped.
- Secret listing is intentionally denied.
- The CD workflow does not require Kubernetes administrator credentials.
- Release provenance is verified before deployment.
- No-op releases do not redeploy the application.
- Deployment concurrency prevents overlapping production-style rollouts.

The CD job needs:

```text
RELEASE_SHA
RELEASE_TAG
kubectl
restricted kubeconfig
network access to Kubernetes API
```

---

## Deployment Concurrency

The CD workflow uses the deployment concurrency group:

```text
havenbridge-production-deployment
```

and:

```yaml
cancel-in-progress: false
```

This prevents separate HavenBridge CD runs from modifying the same Deployment
simultaneously.

---

## Historical Release Validation

The release history below is intentionally retained because it documents the
evolution of the HavenBridge pipeline.

### v0.3.0 — First Successful Self-Hosted CD Deployment

`v0.3.0` was the first successful end-to-end self-hosted CD deployment.

Release:

```text
v0.3.0
```

Commit:

```text
e3bacb4f602b2adfb97356f2b75be8731c23d8c7
```

At this stage, CD deployed the commit-SHA-tagged image directly.

Validated flow:

```text
HavenBridge Release
        ↓
GHCR
        ↓
Self-hosted CD runner
        ↓
Kubernetes Deployment
        ↓
successful rollout
```

Evidence:

```text
cicd/evidence/cd-deployment/v0.3.0-deployment-validation.txt
```

### v0.4.0 — Feature, Gateway and PostgreSQL Persistence Validation

For `v0.4.0`, CD still used the commit SHA as the Kubernetes image tag.

Release SHA:

```text
f4c146b97297455432ff37b9641e88806133ec0b
```

Historical deployed image:

```text
ghcr.io/brunobrunt/havenbridge-api:f4c146b97297455432ff37b9641e88806133ec0b
```

Validation included:

```text
CI application tests                    PASS
Docker build                            PASS
Kubernetes manifest validation          PASS
GHCR publication                        PASS
v0.4.0 Release workflow                 PASS
Release-to-CD workflow handoff          PASS
Self-hosted CD deployment               PASS
Exact SHA image verification            PASS
Kubernetes rollout                      PASS
Two API Pods running                    PASS
Gateway validation                      PASS
Deployed PATCH endpoint                 PASS
PostgreSQL persistence verification     PASS
```

The deployed status-update endpoint was validated through the HavenBridge
Gateway and the resulting PostgreSQL state was independently verified.

Evidence:

```text
cicd/evidence/cd-deployment/v0.4.0-deployment-validation.txt
```

### v0.5.0 — Application Version Reporting

`v0.5.0` validated application-version injection and runtime reporting.

The running API successfully reported:

```text
version: 0.5.0
```

Evidence:

```text
cicd/evidence/cd-deployment/v0.5.0-version-reporting-validation.txt
```

### v0.6.0 — Automated Semantic Release Validation

`v0.6.0` validated automatic semantic-version calculation and automatic Git
tag creation.

The release was calculated from a conventional application commit using:

```text
feat:
```

which correctly produced a MINOR release.

Validated release:

```text
Latest release: v0.5.0
Release type:   minor
Next release:   v0.6.0
```

Automatically created tag:

```text
Tag:     v0.6.0
Tagger:  github-actions[bot]
Commit:  9df2c05d4c18ccb97ebb8ee0b039fcad16e90ad6
```

At this historical stage, Kubernetes still deployed the exact commit SHA:

```text
ghcr.io/brunobrunt/havenbridge-api:9df2c05d4c18ccb97ebb8ee0b039fcad16e90ad6
```

That historical behavior is intentionally documented rather than rewritten.

Evidence:

```text
cicd/evidence/cd-deployment/v0.6.0-automated-semantic-release-validation.txt
```

### v0.8.0 — Semantic Tag Kubernetes Deployment

`v0.8.0` validated the current deployment model.

The CD workflow changed from:

```bash
IMAGE="ghcr.io/brunobrunt/havenbridge-api:${RELEASE_SHA}"
```

to:

```bash
IMAGE="ghcr.io/brunobrunt/havenbridge-api:${RELEASE_TAG}"
```

Deployment verification changed from:

```bash
EXPECTED="ghcr.io/brunobrunt/havenbridge-api:${RELEASE_SHA}"
```

to:

```bash
EXPECTED="ghcr.io/brunobrunt/havenbridge-api:${RELEASE_TAG}"
```

The SHA remains part of release verification and provenance.

The semantic tag now becomes the visible Kubernetes Deployment image.

---

## v0.8.0 Kubernetes Validation

### Rollout

**Host: `eph-cp01`**

```bash
kubectl -n havenbridge rollout status deployment/havenbridge-api
```

Validated result:

```text
deployment "havenbridge-api" successfully rolled out
```

### Deployment Availability

**Host: `eph-cp01`**

```bash
kubectl -n havenbridge get deployment havenbridge-api
```

Validated result:

```text
NAME              READY   UP-TO-DATE   AVAILABLE   AGE
havenbridge-api   2/2     2            2           44d
```

### API Pods

**Host: `eph-cp01`**

```bash
kubectl -n havenbridge get pods | grep havenbridge-api
```

Validated result:

```text
havenbridge-api-b99c859b7-kgn7k   1/1   Running   0   63m
havenbridge-api-b99c859b7-vwj9s   1/1   Running   0   63m
```

### Semantic Tag and Runtime Digest

**Host: `eph-cp01`**

```bash
POD=$(kubectl -n havenbridge get pods -o name \
  | grep '^pod/havenbridge-api-' \
  | head -n1)

kubectl -n havenbridge get "${POD}" \
  -o jsonpath='Image: {.spec.containers[?(@.name=="havenbridge-api")].image}{"\n"}ImageID: {.status.containerStatuses[?(@.name=="havenbridge-api")].imageID}{"\n"}'
```

Validated result:

```text
Image: ghcr.io/brunobrunt/havenbridge-api:v0.8.0
ImageID: ghcr.io/brunobrunt/havenbridge-api@sha256:9830854685b118be4bd9a8a1a2a0048eb5a6a3d32e2a9f8f72f21f8d82e6826c
```

Validation conclusion:

```text
Semantic release-tag deployment            PASS
Kubernetes rollout                          PASS
Deployment replicas 2/2                    PASS
Two HavenBridge API Pods Running           PASS
Human-readable Kubernetes image version    PASS
Immutable runtime image digest             PASS
```

Evidence:

```text
cicd/evidence/cd-deployment/v0.8.0-semantic-tag-deployment-validation.txt
```

---

## Current Release and Deployment Model

The current model is:

```text
Application development
        ↓
Conventional commit
        ↓
Push to main
        ↓
HavenBridge CI
        ↓
Tests / build / manifest validation
        ↓
HavenBridge Release
        ↓
next-version.sh
        ↓
Does the API change require a release?
        │
        ├── NO
        │    ↓
        │  successful no-op
        │    ↓
        │  no semantic tag
        │    ↓
        │  no Kubernetes deployment
        │
        └── YES
             ↓
        semantic version calculated
             ↓
        release image built
             ↓
        semantic tag published to GHCR
             +
        commit-SHA tag published to GHCR
             ↓
        annotated Git tag created
             ↓
        HavenBridge Release succeeds
             ↓
        HavenBridge CD
             ↓
        verify RELEASE_SHA provenance
             ↓
        resolve RELEASE_TAG
             ↓
        self-hosted runner
             ↓
        restricted Kubernetes deployer identity
             ↓
        semantic-version image deployment
             ↓
        Kubernetes rollout
             ↓
        Deployment image verification
             ↓
        CRI-O immutable digest
             ↓
        running HavenBridge application
```

---

## Rollback Model

Explicit semantic versions make rollback easier to understand.

Example:

```text
v0.8.1 deployed
        ↓
problem detected
        ↓
identify previous known-good release
        ↓
v0.8.0
        ↓
redeploy approved image
        ↓
verify rollout
        ↓
validate application health
```

A future automated rollback mechanism can build on the same versioning model.

Database schema changes must be considered independently because an application
rollback can be unsafe if the database schema has become incompatible.

---

## Troubleshooting

### CD Workflow Does Not Start

Confirm that `HavenBridge Release` completed and that the CD
`workflow_run` trigger is configured for the correct workflow name.

Also confirm that a real semantic application release was created.

A successful no-op Release is expected to produce no deployment.

### Self-Hosted Runner Is Offline

**Host: `havenbridge-runner01`**

```bash
sudo systemctl status \
  actions.runner.brunobrunt-havenbridge-ha-service-platform.havenbridge-runner01.service
```

**Host: `havenbridge-runner01`**

```bash
sudo systemctl is-enabled \
  actions.runner.brunobrunt-havenbridge-ha-service-platform.havenbridge-runner01.service
```

**Host: `havenbridge-runner01`**

```bash
sudo systemctl is-active \
  actions.runner.brunobrunt-havenbridge-ha-service-platform.havenbridge-runner01.service
```

### Kubernetes Access Fails

**Host: `havenbridge-runner01`**

```bash
sudo -u github-runner \
  KUBECONFIG=/home/github-runner/.kube/config \
  kubectl get deployment havenbridge-api \
  -n havenbridge
```

### Kubernetes Returns Forbidden

Do not solve a `Forbidden` error by granting cluster-admin.

Review the Role:

```text
kubernetes/platform/rbac/cd-runner/role.yaml
```

and add only the minimum permission genuinely required by the deployment
workflow.

### Rollout Fails or Times Out

**Host: `eph-cp01`**

```bash
kubectl get deployment havenbridge-api \
  -n havenbridge
```

**Host: `eph-cp01`**

```bash
kubectl get pods \
  -n havenbridge
```

**Host: `eph-cp01`**

```bash
kubectl describe deployment havenbridge-api \
  -n havenbridge
```

**Host: `eph-cp01`**

```bash
kubectl get events \
  -n havenbridge \
  --sort-by='.lastTimestamp'
```

### Verify the Current Release Tag

**Host: `eph-cp01`**

```bash
kubectl -n havenbridge get deployment havenbridge-api \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="havenbridge-api")].image}{"\n"}'
```

Expected pattern:

```text
ghcr.io/brunobrunt/havenbridge-api:vX.Y.Z
```

### Verify Runtime Digest

**Host: `eph-cp01`**

```bash
POD=$(kubectl -n havenbridge get pods -o name \
  | grep '^pod/havenbridge-api-' \
  | head -n1)

kubectl -n havenbridge get "${POD}" \
  -o jsonpath='Image: {.spec.containers[?(@.name=="havenbridge-api")].image}{"\n"}ImageID: {.status.containerStatuses[?(@.name=="havenbridge-api")].imageID}{"\n"}'
```

---

## Evidence Index

### CI Foundation

```text
cicd/evidence/ci-foundation/github-actions-ci-validation-results.txt
cicd/evidence/ci-foundation/github-actions-ci-validation-steps.txt
```

### Docker Build

```text
cicd/evidence/docker-build/github-actions-docker-build-validation-results.txt
cicd/evidence/docker-build/github-actions-docker-build-validation-steps.txt
```

### Kubernetes Manifest Validation

```text
cicd/evidence/k8s-manifest-validation/gha-k8s-manifest-validation-results.txt
cicd/evidence/k8s-manifest-validation/gha-k8s-manifest-validation-steps.txt
```

### GHCR Publication

```text
cicd/evidence/ghcr-publication/gha-ghcr-publication-results.txt
cicd/evidence/ghcr-publication/gha-ghcr-publication-steps.txt
```

### GHCR Change Detection

```text
cicd/evidence/ghcr-change-detection/gha-ghcr-change-detection-results.txt
cicd/evidence/ghcr-change-detection/gha-ghcr-change-detection-steps.txt
```

### Semantic Release

```text
cicd/evidence/semver-release/gha-semver-release-results.txt
cicd/evidence/semver-release/gha-semver-release-steps.txt
```

### CD Deployments

```text
cicd/evidence/cd-deployment/v0.3.0-deployment-validation.txt
cicd/evidence/cd-deployment/v0.4.0-deployment-validation.txt
cicd/evidence/cd-deployment/v0.5.0-version-reporting-validation.txt
cicd/evidence/cd-deployment/v0.6.0-automated-semantic-release-validation.txt
cicd/evidence/cd-deployment/v0.8.0-semantic-tag-deployment-validation.txt
```

### Self-Hosted Runner and RBAC

```text
cicd/self-hosted-runner/evidence/kubernetes-rbac-validation.txt
cicd/self-hosted-runner/evidence/automated-release-no-release-validation.txt
```

---

## Related CI/CD Documentation

GitHub-hosted runner documentation:

```text
cicd/github-hosted-runners/README.md
```

Self-hosted runner documentation:

```text
cicd/self-hosted-runner/README.md
```

Semantic-version calculator:

```text
cicd/scripts/next-version.sh
```

GitHub Actions workflows:

```text
.github/workflows/ci.yml
.github/workflows/release.yml
.github/workflows/cd.yml
```

Kubernetes CD RBAC:

```text
kubernetes/platform/rbac/cd-runner/
```

---

## Current CI/CD Status

The HavenBridge CI/CD implementation has been validated across CI, release
automation, GHCR publication, restricted self-hosted deployment and Kubernetes
runtime verification.

Current status:

```text
GitHub-hosted CI                           PASS
FastAPI automated tests                   PASS
Docker build validation                   PASS
Kubernetes manifest validation            PASS
GHCR publication                          PASS
Semantic-version calculator               PASS
API-specific release filtering            PASS
Conventional-commit release rules         PASS
No-release negative guard                 PASS
Automatic version calculation             PASS
Automatic Git-tag creation                PASS
Automatic Git-tag push                    PASS
Release-to-CD workflow chaining           PASS
Dedicated self-hosted CD runner           PASS
Restricted Kubernetes kubeconfig          PASS
Namespace-scoped RBAC                     PASS
Positive Deployment authorization         PASS
Negative Secret authorization             PASS
Release SHA provenance validation         PASS
Semantic release-tag deployment           PASS
Kubernetes rollout validation             PASS
Deployment image verification             PASS
Runtime immutable image digest            PASS
Application version reporting             PASS
Released API feature validation           PASS
PostgreSQL persistence validation         PASS
```

Validated release milestones include:

```text
v0.3.0  First successful self-hosted CD deployment
v0.4.0  Gateway/API feature and PostgreSQL persistence validation
v0.5.0  Runtime application-version reporting
v0.6.0  Automated semantic-version and Git-tag creation
v0.8.0  Semantic release-tag Kubernetes deployment
```

---

## Current Operational Deployment Reference

The validated Kubernetes Deployment currently uses:

```text
ghcr.io/brunobrunt/havenbridge-api:v0.8.0
```

The validated runtime image digest is:

```text
sha256:9830854685b118be4bd9a8a1a2a0048eb5a6a3d32e2a9f8f72f21f8d82e6826c
```

This is the intended current model:

```text
Readable release version
        +
Git source provenance
        +
Immutable runtime artifact identity
```

---

## Interview Talking Point

A concise explanation of the current HavenBridge CI/CD design is:

> I separated CI, release automation and deployment into distinct stages.
> GitHub-hosted runners test and build the application and publish versioned
> images to GHCR. A dedicated self-hosted runner performs Kubernetes deployment
> because the cluster is private. The runner authenticates through a restricted
> ServiceAccount and namespace-scoped RBAC rather than administrator
> credentials. Releases retain the Git SHA for provenance, while Kubernetes
> deploys the human-readable semantic release tag. I also verify the resulting
> CRI-O image digest so the running artifact remains traceable to an immutable
> container image.

---

## Summary

HavenBridge now has an evidence-driven CI/CD implementation that demonstrates:

- Automated application validation.
- Container build validation.
- Kubernetes manifest validation.
- GHCR publication.
- Semantic-version calculation.
- Release-aware no-op behavior.
- Automated annotated Git tagging.
- Git SHA source provenance.
- Semantic-tag Kubernetes deployment.
- Restricted self-hosted runner access.
- Least-privilege Kubernetes RBAC.
- Rollout verification.
- Deployment-image verification.
- Immutable runtime digest verification.
- Historical evidence for major CI/CD milestones.

The current release deployment model intentionally separates:

```text
RELEASE_SHA
        ↓
provenance

RELEASE_TAG
        ↓
operator-readable deployment

sha256 digest
        ↓
immutable runtime artifact
```

That separation gives HavenBridge both traceability and operational clarity.
