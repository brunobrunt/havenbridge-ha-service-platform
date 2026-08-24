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


## Container Image Versioning Strategy

HavenBridge uses a deliberate container image versioning strategy so that
every published application image can be traced back to its source code and
stable application releases can be identified using human-readable version
numbers.

The strategy combines:

- Semantic Versioning for intentional application releases.
- Git commit SHA tags for exact source-code traceability.

This avoids relying only on mutable tags such as `latest`.


### Why Container Image Versioning Matters

As the HavenBridge application grows, new functionality, bug fixes, API
changes, database changes, and operational improvements will be introduced.

Without proper image versioning, it would become difficult to answer
questions such as:

    Which version of the HavenBridge API is currently deployed?

    Which Git commit created the running container image?

    Which image introduced a problem?

    Which previous version should be used for rollback?

For example, a deployment using:

    ghcr.io/brunobrunt/havenbridge-api:latest

does not clearly identify the application version represented by `latest`.

The meaning of `latest` can change whenever another image is published.

A version such as:

    ghcr.io/brunobrunt/havenbridge-api:v0.3.0

is easier for a human to understand.

A Git SHA tag such as:

    ghcr.io/brunobrunt/havenbridge-api:<git-commit-sha>

provides exact source-code traceability.

HavenBridge therefore plans to use both.


### Semantic Versioning

HavenBridge application releases will follow Semantic Versioning:

    MAJOR.MINOR.PATCH

Example:

    v0.3.2

Meaning:

    0 = MAJOR
    3 = MINOR
    2 = PATCH


### PATCH Version

A PATCH version represents a backward-compatible bug fix or small correction.

Example:

    v0.3.0
        ↓
    v0.3.1

Possible HavenBridge examples:

    fix inquiry validation bug
    correct API error handling
    repair logging behavior
    fix a small database query issue

The application gains no major new capability.


### MINOR Version

A MINOR version represents new backward-compatible functionality.

Example:

    v0.3.1
        ↓
    v0.4.0

Possible HavenBridge examples:

    add referral functionality
    add coordinator functionality
    add a notification feature
    introduce a new API endpoint
    add a new application workflow

Existing supported functionality should continue to work.


### MAJOR Version

A MAJOR version represents a significant incompatible or breaking change.

Example:

    v1.6.4
        ↓
    v2.0.0

Possible HavenBridge examples:

    redesign the public API in an incompatible way
    remove previously supported API behavior
    introduce a major application architecture change
    introduce breaking data or integration changes

Major versions should therefore be changed deliberately.


### Why HavenBridge Currently Uses 0.x Versions

HavenBridge is still under active application development.

During this stage, versions may look like:

    v0.1.0
    v0.2.0
    v0.3.0
    v0.3.1
    v0.4.0

The `0` major version communicates that the application is still evolving.

An example development history could be:

    v0.1.0
        Initial working HavenBridge API

    v0.2.0
        Add new service inquiry functionality

    v0.2.1
        Fix inquiry validation issue

    v0.3.0
        Add coordinator workflow

    v0.4.0
        Add referral functionality

    v1.0.0
        First application release considered stable

The actual version changes will be based on the application changes that are
implemented rather than automatically incrementing a version after every
Git push.


### A Git Push Does Not Automatically Mean a New Semantic Version

Not every repository change represents a new application release.

For example:

    README update
        ↓
    git push

should not automatically cause:

    v0.3.0
        ↓
    v0.3.1

Likewise, a CI workflow documentation change does not necessarily represent a
new HavenBridge API release.

Semantic versions will therefore represent intentional application releases,
not every Git commit.


### Git Commit SHA Image Tags

Every Git commit already has a unique identifier.

Example:

    d277fb9...

GitHub Actions exposes the commit SHA that triggered a workflow.

HavenBridge can use that value as a container image tag.

Conceptually:

    Git commit
        ↓
    d277fb9...
        ↓
    CI tests the source
        ↓
    Docker image is built
        ↓
    image receives SHA tag

Example:

    ghcr.io/brunobrunt/havenbridge-api:<git-commit-sha>

This creates a direct relationship:

    Git source code
        ↓
    Git commit SHA
        ↓
    Docker image
        ↓
    Kubernetes deployment

If a running image has a particular SHA tag, the exact source code used to
create it can be located in Git.


### Semantic Version Tag and Git SHA Tag Together

An intentional HavenBridge release can have multiple tags pointing to the
same container image.

Example:

                         ┌── v0.4.0
                         │
    Container Image ─────┤
                         │
                         └── <git-commit-sha>

The registry could therefore contain:

    ghcr.io/brunobrunt/havenbridge-api:v0.4.0

and:

    ghcr.io/brunobrunt/havenbridge-api:<git-commit-sha>

Both tags can reference the exact same image digest.

The semantic version provides:

    human-readable release identification

The Git SHA provides:

    exact source-code traceability


### Image Digest

Container registries also identify images using an immutable content digest.

Conceptually:

    Human release name
        ↓
    v0.4.0

    Source traceability
        ↓
    Git SHA

    Exact container artifact
        ↓
    Image digest

Example concept:

    v0.4.0
        ↓
    <git-commit-sha>
        ↓
    sha256:<image-digest>

The digest identifies the exact image contents.

This becomes especially useful when proving exactly which artifact was
deployed.


### HavenBridge Tagging Policy

The planned HavenBridge policy is:

    Development / CI build
        ↓
    Git SHA identifies the source revision

    Intentional application release
        ↓
    Semantic Version tag
        +
    Git SHA tag

Example:

    ghcr.io/brunobrunt/havenbridge-api:v0.5.0

and:

    ghcr.io/brunobrunt/havenbridge-api:<git-commit-sha>

Both identify the same application image.


### Why `latest` Will Not Be the Primary Deployment Version

The `latest` tag is mutable.

For example:

    Monday:
    latest → image A

    Friday:
    latest → image B

A Kubernetes manifest containing:

    image: ghcr.io/brunobrunt/havenbridge-api:latest

therefore does not clearly communicate which application release was intended.

HavenBridge will prefer explicit image versions.

For example:

    image: ghcr.io/brunobrunt/havenbridge-api:v0.5.0

or an immutable image reference when appropriate.

This improves:

    deployment traceability
    troubleshooting
    rollback
    auditability
    operational understanding


### Planned Git Release Tags

Semantic application releases can later be represented by Git tags.

Example:

    git tag v0.5.0
    git push origin v0.5.0

A future GitHub Actions release workflow can respond to a Git tag matching:

    v*.*.*

Conceptually:

    Git tag v0.5.0
        ↓
    GitHub Actions
        ↓
    Run tests
        ↓
    Build image
        ↓
    Validate Kubernetes manifests
        ↓
    Authenticate to GHCR
        ↓
    Publish image
        ↓
    havenbridge-api:v0.5.0
        +
    havenbridge-api:<git-commit-sha>


### Current CI Versus Future Release Workflow

The current workflow validates every relevant development change.

Current flow:

    git push / pull request
        ↓
    GitHub Actions
        ↓
    FastAPI tests
        ↓
    Docker build validation
        ↓
    Kubernetes manifest validation

The future release flow will add:

    approved application version
        ↓
    Git release tag
        ↓
    GitHub Actions
        ↓
    validated container image
        ↓
    GHCR publication

This separates:

    CI validation

from:

    intentional application release publication


### Build Once Principle

HavenBridge should avoid building one image for testing and then independently
building another image for publication when the same validated artifact can be
used.

The preferred principle is:

    Build once
        ↓
    Validate
        ↓
    Tag the validated image
        ↓
    Publish that image

For the current GitHub Actions job, the Docker image is initially created as:

    havenbridge-api:ci

Because the Docker build, validation, and future GHCR publication steps run
inside the same job, they run on the same GitHub-hosted runner.

The already-built image therefore remains available to later steps in that
job.

A later step can tag that same image for GHCR instead of rebuilding it.


### Planned GHCR Image Flow

The planned publication flow is:

    Source code
        ↓
    Git commit
        ↓
    GitHub Actions
        ↓
    pytest
        ↓
    6 tests pass
        ↓
    Docker build
        ↓
    havenbridge-api:ci
        ↓
    Kubeconform
        ↓
    9 Kubernetes resources valid
        ↓
    GHCR authentication
        ↓
    Tag validated image
        ↓
    ghcr.io/brunobrunt/havenbridge-api:<git-commit-sha>
        ↓
    Push to GHCR

For an intentional semantic release, the same image can additionally receive:

    ghcr.io/brunobrunt/havenbridge-api:v0.x.x


### Kubernetes Deployment Versioning

The deployed Kubernetes workload should eventually reference an explicit
approved application version.

Example:

    containers:
      - name: havenbridge-api
        image: ghcr.io/brunobrunt/havenbridge-api:v0.5.0

This makes the desired application version visible directly in the
Kubernetes Deployment definition.

The running system can then be reasoned about as:

    Git release
        ↓
    v0.5.0
        ↓
    GHCR image
        ↓
    Kubernetes Deployment
        ↓
    HavenBridge API Pods


### Rollback Example

Suppose:

    v0.5.0

is deployed successfully.

Later:

    v0.6.0

is released but introduces an application problem.

Because releases are explicitly versioned, HavenBridge can identify the
previous known-good version:

    v0.5.0

Conceptually:

    v0.6.0
    problem detected
        ↓
    identify previous known-good version
        ↓
    v0.5.0
        ↓
    redeploy
        ↓
    verify rollout
        ↓
    verify HTTPS health

This is significantly safer and easier to understand than trying to determine
which historical image an old `latest` tag represented.


### Versioning and Database Changes

Application versioning becomes particularly important when future HavenBridge
versions introduce database schema changes.

For example:

    v0.6.0
        ↓
    application change
        +
    database migration

A rollback may then require consideration of both:

    application image compatibility

and:

    database schema compatibility

Database migration strategy will therefore be handled deliberately when
HavenBridge reaches that application maturity stage.


### Current Implementation Status

Implemented:

    GitHub Actions CI
    FastAPI automated tests
    Docker image build validation
    Kubernetes manifest validation
    GHCR package write permission

Planned next:

    GHCR authentication
    Git SHA image tagging
    GHCR image publication
    publication validation

Planned later:

    semantic Git release tags
    automated semantic release publication
    Kubernetes deployment automation
    rollback automation


### Interview Talking Point

A concise explanation of the HavenBridge image versioning strategy is:

    "I designed the container release strategy to combine Semantic Versioning
    with Git commit SHA tags. Semantic versions such as v0.4.0 identify
    intentional application releases, while SHA tags provide exact
    source-code traceability. I avoid relying on latest as the deployment
    version because it is mutable. The CI pipeline follows a build-once
    approach so the image that passes validation is the same artifact that is
    later tagged and published to GHCR."


## Semantic Version Release Automation

HavenBridge uses a separate GitHub Actions Release workflow for intentional
application releases.

Workflow:

```text
.github/workflows/release.yml
```

Earlier HavenBridge releases used a manual semantic-version process:

```text
Human selects semantic version
        ↓
Create annotated Git tag
        ↓
Push Git tag to GitHub
        ↓
HavenBridge Release workflow
```

For example:

```bash
git tag -a v0.5.0 \
  -m "HavenBridge v0.5.0 - automatic application version reporting"

git push origin v0.5.0
```

This manual process was useful while the Git tag, Release workflow, GHCR image,
and CD relationship were being learned and validated.

The release process is now being changed so that semantic-version calculation
and Git-tag creation are automated.

The Release workflow is started intentionally with:

```yaml
on:
  workflow_dispatch:
```

This keeps a human release-approval point while removing the need to manually
calculate, create, and push the next semantic version.

The new release flow is:

```text
Application change committed
        ↓
Push to main
        ↓
HavenBridge CI
        ↓
CI succeeds
        ↓
Human starts HavenBridge Release
        ↓
Calculate next semantic version
        ↓
Run API tests
        ↓
Build release image
        ↓
Validate Kubernetes manifests
        ↓
Push release image to GHCR
        ↓
Create annotated Git tag automatically
        ↓
Push Git tag automatically
        ↓
Release workflow succeeds
        ↓
Existing HavenBridge CD workflow
```

The human decides **when** to release.

The automation determines **what the next application version should be**.

### Semantic Version Calculator

The version-calculation logic is stored separately from the GitHub Actions
workflow:

```text
cicd/scripts/next-version.sh
```

The Release workflow calls it with:

```yaml
- name: Determine next semantic version
  id: version
  run: bash "$GITHUB_WORKSPACE/cicd/scripts/next-version.sh"
```

The script examines committed Git history after the latest semantic-version
tag.

Important:

```text
The script examines COMMITTED Git history only.

It does not inspect uncommitted or unstaged working-directory changes.
```

The current release rules are:

```text
feat:   → MINOR
fix:    → PATCH
feat!:  → MAJOR
```

Examples:

```text
Latest release: v0.5.0

feat: add referral workflow
        ↓
Next release: v0.6.0
```

```text
Latest release: v0.6.0

fix: correct inquiry validation
        ↓
Next release: v0.6.1
```

Commits such as:

```text
docs:
test:
chore:
```

do not create an application release by themselves.

### API-Specific Version Calculation

HavenBridge contains application, Kubernetes, Terraform, Ansible, CI/CD, and
other platform code.

The semantic-version calculator therefore limits release-causing Git history
to:

```text
applications/havenbridge-api
```

This prevents an unrelated infrastructure change such as:

```text
feat: improve Terraform runner provisioning
```

from incorrectly increasing the HavenBridge API version.

An application change such as:

```text
feat: add referral endpoint
```

remains eligible for a semantic-version increase when it changes files under:

```text
applications/havenbridge-api
```

### Full Git History

The Release workflow checks out the complete Git history:

```yaml
- name: Checkout repository
  uses: actions/checkout@v7
  with:
    fetch-depth: 0
```

This is required because the version calculator needs access to previous Git
tags and commits.

Conceptually:

```text
Latest semantic tag
        ↓
Committed API changes after that tag
        ↓
Release rule
        ↓
Next semantic version
```

### Calculated Release Values

The version calculator writes values to GitHub Actions `GITHUB_OUTPUT`.

For a minor release, the values could be:

```text
bump=minor
tag=v0.6.0
app_version=0.6.0
```

The Release workflow can then reuse them as:

```text
steps.version.outputs.bump
steps.version.outputs.tag
steps.version.outputs.app_version
```

For example, the calculated application version is supplied to the Docker
build:

```yaml
APP_VERSION="${{ steps.version.outputs.app_version }}"
```

while the calculated semantic Git/Docker tag is available as:

```yaml
${{ steps.version.outputs.tag }}
```

### Automatic Git Tag Creation

After the release image has passed its tests and validation and has been
published, GitHub Actions creates the annotated source-code tag:

```bash
TAG="${{ steps.version.outputs.tag }}"

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

git tag -a "${TAG}" \
  -m "HavenBridge ${TAG}"

git push origin "${TAG}"
```

This replaces the previous manual commands:

```text
git tag -a v0.x.x ...
git push origin v0.x.x
```

The Release workflow requires:

```yaml
permissions:
  contents: write
  packages: write
```

`packages: write` permits GHCR publication.

`contents: write` permits the workflow to push the automatically created Git
tag back to the repository.

### Git Tag and Container Image Tag

The two tags serve different purposes:

```text
Git tag
v0.6.0
    ↓
Marks the released source-code commit
```

```text
Container image tag
ghcr.io/brunobrunt/havenbridge-api:v0.6.0
    ↓
Identifies the released container image
```

The release image also retains a commit-SHA tag for exact source-code
traceability.

### No Release-Causing Commit

If no committed HavenBridge API change matches the release rules, the version
calculator stops the release:

```text
No release-causing commit found. Release stopped.
```

This behavior has been validated locally.

It prevents documentation-only, infrastructure-only, or other non-release
changes from accidentally creating a new HavenBridge API version.

### Current Validation Status

The automated semantic-version implementation has been prepared locally.

Validated locally:

```text
Semantic-version script Bash syntax        PASS
No release-causing commit detection        PASS
No-release exit behavior                   PASS
API-specific Git-history filtering         PASS
```

The first complete GitHub Actions validation of automatic version calculation,
GHCR publication, automatic Git-tag creation, and Release-to-CD deployment is
still pending.

The earlier manually created semantic releases remain valid historical
release evidence.


## Continuous Deployment Implementation

HavenBridge now has a working continuous deployment workflow that
deploys approved application releases from GitHub Container Registry
into the private Kubernetes cluster.

Workflow:

```text
.github/workflows/cd.yml
```

Unlike CI and Release, CD does not execute on a GitHub-hosted runner.

It targets the dedicated self-hosted runner:

```text
havenbridge-runner01
```

using:

```yaml
runs-on:
  - self-hosted
  - havenbridge-cd
```

This is required because the Kubernetes API exists inside the private
HavenBridge homelab network.

## Release-to-CD Trigger

The CD workflow is not triggered directly by every push to `main`.

Instead, it waits for the `HavenBridge Release` workflow to finish:

```yaml
on:
  workflow_run:
    workflows:
      - HavenBridge Release
    types:
      - completed
```

The deployment job runs only when the Release workflow succeeded:

```yaml
if: ${{ github.event.workflow_run.conclusion == 'success' }}
```

The resulting flow is:

```text
Application changes
        ↓
Push to main
        ↓
HavenBridge CI
        ↓
Tests + build + manifest validation
        ↓
Manual release decision
        ↓
Semantic Git tag
        ↓
HavenBridge Release
        ↓
Release image published to GHCR
        ↓
Release workflow succeeds
        ↓
HavenBridge CD
        ↓
Self-hosted runner
        ↓
Kubernetes deployment
```

This prevents a failed release from reaching the Kubernetes environment.

## CD Runner Identity

The deployment job executes on:

```text
havenbridge-runner01
IP: 172.16.10.37
```

The GitHub Actions service runs under the dedicated Linux account:

```text
github-runner
```

The runner is registered with GitHub using the custom label:

```text
havenbridge-cd
```

and runs persistently as the systemd service:

```text
actions.runner.brunobrunt-havenbridge-ha-service-platform.havenbridge-runner01.service
```

The service was validated as:

```text
enabled
active
```

and successfully reported:

```text
Connected to GitHub
Listening for Jobs
```

Detailed runner implementation is documented at:

```text
cicd/self-hosted-runner/README.md
```

## Restricted Kubernetes Authentication

The GitHub Actions runner does not use Kubernetes administrator
credentials.

The runner uses the restricted kubeconfig:

```text
/home/github-runner/.kube/config
```

The kubeconfig is owned by:

```text
github-runner:github-runner
```

with permissions:

```text
600
```

It authenticates to Kubernetes as:

```text
system:serviceaccount:havenbridge:havenbridge-deployer
```

The Kubernetes identity is implemented using:

```text
ServiceAccount
        ↓
Role
        ↓
RoleBinding
```

under:

```text
kubernetes/platform/rbac/cd-runner/
```

The restricted Role allows the deployment identity to:

* get Deployments;
* list Deployments;
* watch Deployments;
* patch the `havenbridge-api` Deployment.

The identity cannot read Kubernetes Secrets.

## Least-Privilege Validation

The positive authorization test was executed from
`havenbridge-runner01` as the actual GitHub Actions Linux account:

```bash
sudo -u github-runner \
  KUBECONFIG=/home/github-runner/.kube/config \
  kubectl get deployment havenbridge-api \
  -n havenbridge
```

Result:

```text
NAME              READY   UP-TO-DATE   AVAILABLE
havenbridge-api   2/2     2            2
```

The Deployment request was allowed.

A negative authorization test was then performed:

```bash
sudo -u github-runner \
  KUBECONFIG=/home/github-runner/.kube/config \
  kubectl get secrets \
  -n havenbridge
```

Result:

```text
Error from server (Forbidden)
```

The request was intentionally denied.

I created a dedicated Kubernetes ServiceAccount for CD. A
namespace-scoped Role grants only the deployment permissions it needs,
and a RoleBinding connects the identity to those permissions. I then
tested both positive and negative authorization cases to prove least
privilege.

Detailed RBAC validation evidence is stored at:

```text
cicd/self-hosted-runner/evidence/kubernetes-rbac-validation.txt
```

## Why CD Deploys the Commit-SHA Image

The Release workflow publishes both a semantic-version image and an
immutable commit-SHA image.

For `v0.3.0`:

```text
Human-readable release:

ghcr.io/brunobrunt/havenbridge-api:v0.3.0
```

and:

```text
Exact source commit:

ghcr.io/brunobrunt/havenbridge-api:e3bacb4f602b2adfb97356f2b75be8731c23d8c7
```

Both images represent the same release source state.

The CD workflow deploys the commit-SHA-tagged image because the SHA
provides an exact connection between:

```text
Git commit
    ↓
container image
    ↓
Kubernetes Deployment
```

The semantic version remains the human-readable release identifier.

A future enhancement may deploy by immutable container image digest for
even stronger artifact-level immutability.

## CD Workflow Environment

The CD workflow defines the deployment target using:

```text
KUBECONFIG=/home/github-runner/.kube/config
NAMESPACE=havenbridge
DEPLOYMENT=havenbridge-api
CONTAINER=havenbridge-api
RELEASE_SHA=<release commit SHA>
```

The release SHA is obtained from the completed Release workflow using:

```yaml
RELEASE_SHA: ${{ github.event.workflow_run.head_sha }}
```

This ensures CD deploys the exact commit that produced the successful
release.

## CD Workflow Step-by-Step

### Step 1 — Show Runner Identity

The workflow displays:

```text
Runner hostname
Runner operating-system user
Release commit SHA
```

This confirms that the deployment job is executing on the expected
self-hosted runner.

### Step 2 — Validate the Release SHA

The workflow verifies that `RELEASE_SHA` is a valid 40-character
hexadecimal Git SHA.

Invalid values cause the deployment to stop.

### Step 3 — Verify Kubernetes Access

The runner executes:

```bash
kubectl get deployment havenbridge-api \
  -n havenbridge
```

This proves that the runner can:

* reach the Kubernetes API;
* authenticate with the restricted kubeconfig;
* access the HavenBridge Deployment.

### Step 4 — Show the Currently Deployed Image

Before changing Kubernetes, the workflow reads the current container
image from the Deployment.

Before the first automated CD rollout, HavenBridge used:

```text
ghcr.io/brunobrunt/havenbridge-api:0.1.0
```

This provides a clear before-and-after deployment record.

### Step 5 — Construct the Release Image

The workflow constructs:

```text
ghcr.io/brunobrunt/havenbridge-api:${RELEASE_SHA}
```

For `v0.3.0`, this became:

```text
ghcr.io/brunobrunt/havenbridge-api:e3bacb4f602b2adfb97356f2b75be8731c23d8c7
```

### Step 6 — Update the Kubernetes Deployment

The equivalent deployment command is:

```bash
kubectl set image \
  deployment/havenbridge-api \
  havenbridge-api=ghcr.io/brunobrunt/havenbridge-api:<RELEASE_SHA> \
  -n havenbridge
```

Updating the Deployment Pod template causes Kubernetes to create a new
rollout.

### Step 7 — Wait for the Rollout

The workflow waits for Kubernetes using:

```bash
kubectl rollout status \
  deployment/havenbridge-api \
  -n havenbridge \
  --timeout=180s
```

CD therefore does not report success merely because the Deployment was
patched.

The new workload must successfully roll out.

### Step 8 — Verify the Deployed Image

After rollout, the workflow reads the Deployment image again and
compares it with the expected release SHA image.

If the expected and actual values differ, the CD workflow fails.

## CD Security Decisions

The CD workflow intentionally uses:

```yaml
permissions: {}
```

because it does not require broad `GITHUB_TOKEN` permissions.

Kubernetes authentication is provided locally on the self-hosted runner
through the restricted kubeconfig.

The workflow also intentionally does not check out the repository source
code.

The deployment job needs only:

* the release SHA;
* `kubectl`;
* the restricted kubeconfig;
* network access to the Kubernetes API.

This reduces the amount of code executed on the trusted deployment
runner.

## Deployment Concurrency

The workflow uses:

```text
havenbridge-production-deployment
```

as its concurrency group.

It also uses:

```yaml
cancel-in-progress: false
```

This prevents multiple HavenBridge deployments from modifying the same
Deployment simultaneously.

## First Successful End-to-End CD Deployment

The first successful self-hosted HavenBridge CD deployment used:

```text
Release: v0.3.0

Commit:
e3bacb4f602b2adfb97356f2b75be8731c23d8c7
```

The Release workflow completed successfully and published both the
semantic-version image and commit-SHA image to GHCR.

The following CD steps passed:

```text
Show CD runner identity        PASS
Validate release SHA           PASS
Verify Kubernetes access       PASS
Show currently deployed image  PASS
Deploy released API image      PASS
Wait for rollout               PASS
Verify deployed image          PASS
```

## Cluster-Side Image Validation

After GitHub Actions completed, the deployment was independently checked
from `havenbridge-runner01`:

```bash
sudo -u github-runner \
  KUBECONFIG=/home/github-runner/.kube/config \
  kubectl get deployment havenbridge-api \
  -n havenbridge \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="havenbridge-api")].image}{"\n"}'
```

Result:

```text
ghcr.io/brunobrunt/havenbridge-api:e3bacb4f602b2adfb97356f2b75be8731c23d8c7
```

This confirmed that Kubernetes was configured with the exact image
produced from the `v0.3.0` release commit.

## Kubernetes Rollout Validation

The rollout was independently verified using:

```bash
sudo -u github-runner \
  KUBECONFIG=/home/github-runner/.kube/config \
  kubectl rollout status deployment/havenbridge-api \
  -n havenbridge
```

Result:

```text
deployment "havenbridge-api" successfully rolled out
```

The first Release → GHCR → self-hosted CD runner → Kubernetes deployment
therefore completed successfully end to end.

## CD Deployment Evidence

Detailed evidence for the first successful deployment is stored at:

```text
cicd/evidence/cd-deployment/v0.3.0-deployment-validation.txt
```


## Second Successful End-to-End CD Deployment: v0.4.0

HavenBridge `v0.4.0` provided a second complete validation of the
Release → GHCR → self-hosted CD → Kubernetes delivery path.

Unlike `v0.3.0`, which primarily established and validated the CD
infrastructure, `v0.4.0` contained a real application feature:

```text
PATCH /api/v1/inquiries/{inquiry_id}/status
```

The release used:

```text
Release:
v0.4.0

Commit:
f4c146b97297455432ff37b9641e88806133ec0b

Commit message:
feat: add service inquiry status updates
```

Before the release tag was created, the normal HavenBridge CI workflow
completed successfully for the application commit.

The CI workflow validated:

```text
Detect HavenBridge API changes        PASS
Run HavenBridge API tests             PASS
Build HavenBridge API Docker image    PASS
Validate Kubernetes manifests         PASS
Log in to GHCR                        PASS
Tag image for GHCR                    PASS
Push image to GHCR                    PASS
```

The annotated Git tag:

```text
v0.4.0
```

then triggered the `HavenBridge Release` workflow.

After the Release workflow completed successfully, the
`HavenBridge CD` workflow started automatically.

The release-to-CD relationship is:

```text
v0.4.0 Git tag
        ↓
HavenBridge Release
        ↓
Release succeeds
        ↓
HavenBridge CD
        ↓
Self-hosted runner
        ↓
Kubernetes
```

CD is not triggered independently by the tag. It waits for the Release
workflow to complete successfully.

### How the CD Workflow Changes the Kubernetes Image

The image change is performed by this operation in `.github/workflows/cd.yml`:

```bash
IMAGE="ghcr.io/brunobrunt/havenbridge-api:${RELEASE_SHA}"

kubectl set image \
  deployment/"${DEPLOYMENT}" \
  "${CONTAINER}"="${IMAGE}" \
  -n "${NAMESPACE}"
```

For `v0.4.0`, the release SHA was:

```text
f4c146b97297455432ff37b9641e88806133ec0b
```

Therefore the image deployed by CD was:

```text
ghcr.io/brunobrunt/havenbridge-api:f4c146b97297455432ff37b9641e88806133ec0b
```

`kubectl set image` is the command that changes the Deployment Pod
template.

Conceptually:

```text
kubectl set image
        ↓
Deployment Pod template changes
        ↓
Kubernetes detects the new template
        ↓
New ReplicaSet is created
        ↓
New Pods start with the new image
        ↓
Old Pods are replaced
```

The next CD command:

```bash
kubectl rollout status \
  deployment/"${DEPLOYMENT}" \
  -n "${NAMESPACE}" \
  --timeout=180s
```

does not change the image. It waits for Kubernetes to complete the new
rollout successfully.

A later command such as:

```bash
kubectl get deployment havenbridge-api \
  -n havenbridge \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="havenbridge-api")].image}{"\n"}'
```

also does not change the image.

It only reads the Deployment and shows which image is currently
configured.

The distinction is:

```text
kubectl set image       = CHANGE the Deployment image
kubectl rollout status  = WAIT for / VERIFY the rollout
kubectl get             = READ / VERIFY the configured image
```

### Cluster-Side v0.4.0 Image Validation

The deployed image was independently checked from the Kubernetes
environment.

Command:

```bash
kubectl get deployment havenbridge-api \
  -n havenbridge \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="havenbridge-api")].image}{"\n"}'
```

Result:

```text
ghcr.io/brunobrunt/havenbridge-api:f4c146b97297455432ff37b9641e88806133ec0b
```

This proved that Kubernetes was configured with the exact image produced
from the `v0.4.0` release commit.

### Kubernetes Rollout Validation for v0.4.0

Command:

```bash
kubectl rollout status \
  deployment/havenbridge-api \
  -n havenbridge \
  --timeout=180s
```

Result:

```text
deployment "havenbridge-api" successfully rolled out
```

Two HavenBridge API Pods were confirmed running:

```text
havenbridge-api-5c8bf7fcd7-c8ggj   1/1   Running   eph-worker01
havenbridge-api-5c8bf7fcd7-wt5xc   1/1   Running   eph-worker02
```

This also confirmed that the API replicas were distributed across the
two worker nodes.

### Gateway Validation for v0.4.0

From `syrus`, the API was reachable using:

```bash
curl -k -i https://havenbridge.lab/
```

Result:

```text
HTTP/2 200
```

On `eph-cp01`, `havenbridge.lab` did not resolve locally.

The application Gateway path was therefore tested without changing DNS
by using:

```bash
curl -k -i \
  --resolve havenbridge.lab:443:172.16.10.40 \
  https://havenbridge.lab/
```

Result:

```text
HTTP/2 200
```

This validated the application path through:

```text
eph-cp01
    ↓
172.16.10.40
    ↓
Traefik / Gateway API
    ↓
HTTPRoute
    ↓
havenbridge-api Service
    ↓
HavenBridge API Pods
```

The missing `havenbridge.lab` name resolution on `eph-cp01` is a
separate lab DNS/hosts follow-up and did not prevent application
validation.

### Deployed PATCH Feature Validation

The new `v0.4.0` status-update endpoint was tested against the
Kubernetes-deployed application:

```bash
curl -k -i \
  --resolve havenbridge.lab:443:172.16.10.40 \
  -X PATCH \
  https://havenbridge.lab/api/v1/inquiries/1/status \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "closed"
  }'
```

Result:

```text
HTTP/2 200
```

The API response confirmed:

```text
id:
1

requester_name:
Version 0.4 Test

status:
closed

updated_at:
2026-08-21T16:14:48.550344Z
```

### PostgreSQL Persistence Validation

The persisted value was then verified independently inside PostgreSQL.

PostgreSQL access:

```bash
kubectl exec -it \
  -n havenbridge \
  havenbridge-postgres-0 \
  -c postgresql \
  -- psql \
  -U havenbridge_admin \
  -d havenbridge
```

Query:

```sql
SELECT
    id,
    requester_name,
    status,
    created_at,
    updated_at
FROM service_inquiries
WHERE id = 1;
```

Result:

```text
id             = 1
requester_name = Version 0.4 Test
status         = closed
updated_at     = 2026-08-21 16:14:48.550344+00
```

This proved that the new status was not only returned by the API but was
also committed successfully to PostgreSQL.

### v0.4.0 End-to-End Result

The complete validated path was:

```text
Application feature
        ↓
Commit f4c146b...
        ↓
Normal CI
        ↓
Annotated tag v0.4.0
        ↓
HavenBridge Release
        ↓
GHCR
        ↓
HavenBridge CD
        ↓
havenbridge-runner01
        ↓
kubectl set image
        ↓
Kubernetes rollout
        ↓
Gateway validation
        ↓
PATCH feature validation
        ↓
PostgreSQL persistence validation
```

Validation summary:

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
Gateway HTTP/2 access                   PASS
Deployed PATCH endpoint                 PASS
PostgreSQL persistence verification     PASS
```

Final result:

```text
PASS
```

Detailed evidence is stored at:

```text
cicd/evidence/cd-deployment/v0.4.0-deployment-validation.txt
```

Two non-blocking follow-up items were identified during this validation:

1. `eph-cp01` does not currently resolve `havenbridge.lab`; the Gateway
   remained reachable when the host-to-IP mapping was supplied with
   `curl --resolve`.

2. The API root response currently reports `"version":"0.1.0"` even
   though the deployed release is `v0.4.0`. Application version reporting
   should later be aligned with the actual deployed release.


## CD Troubleshooting

### CD Workflow Does Not Start

Confirm that `HavenBridge Release` completed successfully.

The CD workflow is triggered by Release completion and not directly by a
normal push to `main`.

### Self-Hosted Runner Is Offline

On `havenbridge-runner01`:

```bash
sudo systemctl status \
  actions.runner.brunobrunt-havenbridge-ha-service-platform.havenbridge-runner01.service
```

Confirm automatic startup:

```bash
sudo systemctl is-enabled \
  actions.runner.brunobrunt-havenbridge-ha-service-platform.havenbridge-runner01.service
```

Confirm that it is currently running:

```bash
sudo systemctl is-active \
  actions.runner.brunobrunt-havenbridge-ha-service-platform.havenbridge-runner01.service
```

### Kubernetes Access Fails

Test using the exact identity used by GitHub Actions:

```bash
sudo -u github-runner \
  KUBECONFIG=/home/github-runner/.kube/config \
  kubectl get deployment havenbridge-api \
  -n havenbridge
```

### Kubernetes Returns Forbidden

Do not solve a `Forbidden` error by giving the runner cluster-admin
privileges.

Review:

```text
kubernetes/platform/rbac/cd-runner/role.yaml
```

and add only the minimum permission genuinely required by CD.

### Rollout Fails or Times Out

Check the Deployment:

```bash
kubectl get deployment havenbridge-api \
  -n havenbridge
```

Check the Pods:

```bash
kubectl get pods \
  -n havenbridge
```

Describe the Deployment:

```bash
kubectl describe deployment havenbridge-api \
  -n havenbridge
```

Review recent Kubernetes events:

```bash
kubectl get events \
  -n havenbridge \
  --sort-by='.lastTimestamp'
```

## Current Release and Deployment Model

The current HavenBridge release model keeps a deliberate human approval gate
while automating semantic-version selection and Git-tag creation.

```text
Develop
    ↓
Conventional Commit
    ↓
Push to main
    ↓
HavenBridge CI
    ↓
CI succeeds
    ↓
Human approves release
by running HavenBridge Release
    ↓
next-version.sh examines committed API changes
    ↓
Semantic version calculated automatically
    ↓
Release tests and validation
    ↓
Release image published to GHCR
    ↓
Annotated Git tag created automatically
    ↓
Git tag pushed automatically
    ↓
Release workflow succeeds
    ↓
HavenBridge CD
    ↓
Self-hosted runner
    ↓
Kubernetes
```

The human release decision remains intentional.

The following manual work is no longer required:

```text
Manually calculate v0.x.x
Manually run git tag -a
Manually run git push origin <tag>
```

Release automation now performs those operations.

The first complete GitHub Actions end-to-end validation of this automated
release model is still pending.

## Automated Semantic Versioning Implementation Status

HavenBridge has now implemented automated semantic-version calculation and
automatic Git-tag creation.

The earlier manual process was:

```text
Human selects release version
        ↓
Human creates annotated Git tag
        ↓
Human pushes Git tag
        ↓
Release workflow
        ↓
CD deployment
```

The new implementation is:

```text
Conventional application commit
        ↓
HavenBridge CI
        ↓
Human starts HavenBridge Release
        ↓
next-version.sh examines committed API changes
        ↓
Release type determined automatically
        ↓
Semantic version calculated automatically
        ↓
Release image built and validated
        ↓
Semantic-version image pushed to GHCR
        ↓
Annotated Git tag created automatically
        ↓
Git tag pushed automatically
        ↓
Existing CD workflow deploys the release
```

The current release rules are:

```text
feat:   → MINOR
fix:    → PATCH
feat!:  → MAJOR
```

For example:

```text
v0.5.0
    +
feat: add referral workflow
    ↓
v0.6.0
```

The version-calculation logic is maintained in:

```text
cicd/scripts/next-version.sh
```

The GitHub Actions orchestration is maintained in:

```text
.github/workflows/release.yml
```

The human release gate is intentionally retained for now.

This means HavenBridge currently automates:

```text
Version calculation
Git tag creation
Git tag push
Container-image tagging
Container-image publication
Release-to-CD handoff
```

while a human still decides when the Release workflow should run.

A later enhancement may remove the manual `workflow_dispatch` approval point
and allow eligible commits to initiate releases automatically after suitable
branch, pull-request, and release controls are established.

The automated semantic-version implementation is complete locally but has not
yet completed its first full GitHub Actions end-to-end validation.

That validation will confirm:

```text
Automatic semantic-version calculation
        ↓
Automatic GHCR publication
        ↓
Automatic Git-tag creation
        ↓
Successful Release workflow
        ↓
Automatic HavenBridge CD
        ↓
Kubernetes rollout
        ↓
Application reports the calculated version
```


## Related CI/CD Documentation

GitHub-hosted runners:

```text
cicd/github-hosted-runners/README.md
```

Self-hosted runner:

```text
cicd/self-hosted-runner/README.md
```

Self-hosted runner RBAC evidence:

```text
cicd/self-hosted-runner/evidence/kubernetes-rbac-validation.txt
```

CD deployment evidence:

```text
cicd/evidence/cd-deployment/v0.3.0-deployment-validation.txt
cicd/evidence/cd-deployment/v0.4.0-deployment-validation.txt
```

GitHub Actions workflows:

```text
.github/workflows/ci.yml
.github/workflows/release.yml
.github/workflows/cd.yml
```

Semantic-version calculator:

```text
cicd/scripts/next-version.sh
```

The semantic-version calculator examines committed HavenBridge API changes
after the latest release tag and determines the next release version using
the current HavenBridge release rules:

```text
feat:   → MINOR
fix:    → PATCH
feat!:  → MAJOR
```

The calculated values are passed back to:

```text
.github/workflows/release.yml
```

through GitHub Actions `GITHUB_OUTPUT`.


## Current CD Status

The HavenBridge Release + self-hosted continuous deployment implementation is
complete and validated.

The existing release and CD architecture has successfully deployed multiple
semantic-version releases through the self-hosted runner into the Kubernetes
cluster.

Completed milestones include:

* GitHub-hosted CI validated.
* GHCR publication validated.
* Semantic-version Release workflow validated using the original manual Git-tag release gate.
* Dedicated self-hosted CD runner provisioned.
* GitHub Actions runner registered.
* Runner systemd service enabled and running.
* Dedicated `github-runner` Linux account configured.
* Restricted Kubernetes kubeconfig installed.
* Dedicated `havenbridge-deployer` ServiceAccount configured.
* Namespace-scoped Role and RoleBinding configured.
* Positive Deployment authorization test passed.
* Negative Secret authorization test passed.
* Release-to-CD workflow chaining validated.
* Commit-SHA image deployment validated.
* Kubernetes rollout validation passed.
* Exact deployed-image verification passed.
* First end-to-end release `v0.3.0` successfully deployed.
* Second end-to-end release `v0.4.0` successfully deployed.
* Real `PATCH /api/v1/inquiries/{inquiry_id}/status` application change validated through the Gateway.
* PostgreSQL persistence of the deployed `v0.4.0` status update independently verified.
* Release `v0.5.0` successfully deployed.
* Automatic application-version injection validated with the running API reporting `"version": "0.5.0"`.

### Semantic-Version Automation Status

HavenBridge is now extending the validated Release + CD architecture with
automatic semantic-version calculation and automatic Git-tag creation.

Current implementation status:

```text
Semantic-version calculator             Implemented
API-specific Git-history filtering       Implemented
Conventional-commit release rules        Implemented
Automatic version calculation            Locally validated
No-release detection                     Locally validated
Automatic Git-tag creation               Implemented in Release workflow
Automatic Git-tag push                   Implemented in Release workflow
Human workflow_dispatch release gate     Retained intentionally
Full GitHub Actions validation            Pending
Automatic Release-to-CD validation       Pending
```

The new implementation therefore does not replace the already validated CD
pipeline.

Instead, it replaces the manual version-selection and Git-tag creation steps
that previously occurred before the Release workflow.

Previous release entry:

```text
Human chooses v0.x.x
        ↓
git tag -a v0.x.x
        ↓
git push origin v0.x.x
        ↓
Release
        ↓
CD
```

New release entry:

```text
Human starts HavenBridge Release
        ↓
next-version.sh
        ↓
Version calculated automatically
        ↓
Release validation and GHCR publication
        ↓
Git tag created and pushed automatically
        ↓
Existing HavenBridge CD
```

The Release + CD pipeline remains validated.

The new automated semantic-version entry process is implemented but will not
be marked fully validated until its first successful end-to-end GitHub Actions
release and Kubernetes deployment.
