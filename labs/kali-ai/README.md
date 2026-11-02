
# Kali-AI Security Learning Lab

> Part of the HavenBridge HA Service Platform
> Status: Phase 0 — Git worktree established
> Environment: On-premises KVM/libvirt homelab

## 1. Project Overview

Kali-AI is a dedicated security learning environment built using
Terraform, KVM/libvirt, Ansible, Linux, and selected security tools.

The purpose is to learn infrastructure automation, reconnaissance,
authorized penetration testing, vulnerability assessment, security
hardening, and eventually AI-assisted incident analysis.

The lab will remain isolated from the production-style HavenBridge
Kubernetes infrastructure.

## 2. Learning Objectives

- Provision Kali Linux using Terraform and libvirt.
- Understand VM images, storage, networking, and cloud-init.
- Configure Linux systems consistently using Ansible.
- Learn basic Linux security and networking commands.
- Practice authorized reconnaissance and vulnerability assessment.
- Document evidence, findings, remediation, and lessons learned.
- Explore read-only AI-assisted security reporting.

## 3. CRAFT Documentation Method

| Element | Meaning | Application |
|---|---|---|
| C — Context | What and why | Explain the goal of each activity |
| R — Role | Who performs it | Identify host, VM, and tool |
| A — Action | What we do | Show exact commands and configurations |
| F — Format | How we document | ELI10 explanations, outputs, diagrams, screenshots |
| T — Tone | How we explain | Clear, beginner-friendly, technically accurate |

Every completed phase will include:
1. Objective
2. Architecture or workflow
3. Prerequisites
4. Host-labelled commands and flag explanations
5. Expected and actual results
6. Screenshot evidence where useful
7. Troubleshooting and lessons learned
8. Git commit and PR reference

## 4. Planned Architecture

```text
syrus (Ubuntu 24.04 LTS)
│
├── KVM / libvirt
│   │
│   └── Dedicated Kali-AI lab network
│       │
│       ├── kali-ai VM
│       │   ├── Kali Linux
│       │   ├── Security tools
│       │   └── Ansible-managed configuration
│       │
│       └── Authorized training targets (future)
│
├── Terraform
│   └── VM, network, and storage provisioning
│
└── Ansible
    └── System configuration and validation
```

Network ranges, VM resources, disk paths, and image details will
be finalized after inspecting the current libvirt environment.

## 5. Safety and Scope

Security testing is restricted to personally owned systems,
deliberately provisioned training targets, or systems for which
explicit authorization has been granted.

The lab must not disrupt HavenBridge workloads.

Initial reconnaissance will use lab targets only.

## 6. Phase Roadmap

| Phase | Description | Status |
|---|---|---|
| 0 | Create Git feature branch and worktree | Completed |
| 1 | Inspect host and download verified Kali image | Planned |
| 2 | Provision network, storage, and VM using Terraform | Planned |
| 3 | Configure Kali using Ansible | Planned |
| 4 | Validate isolation and security baseline | Planned |
| 5 | Learn reconnaissance and network discovery | Planned |
| 6 | Practice authorized vulnerability assessment | Planned |
| 7 | Build AI-assisted reporting workflow | Planned |

## 7. Phase 0 — Git Worktree Setup

### Objective

Create a dedicated development workspace without disturbing
existing HavenBridge feature branches or unfinished changes.

### Host

`syrus` — KVM/libvirt host.

### Command

```bash
# HOST: syrus
cd /home/alabi/projects/havenbridge-ha-service-platform

git worktree add \
  /home/alabi/projects/havenbridge-kali-ai \
  -b feature/kali-ai-lab \
  main
```

### ELI10 Explanation

- `git worktree add`: Creates another working directory for the same repository.
- `/home/alabi/projects/havenbridge-kali-ai`: New folder for Kali-AI development.
- `-b`: Creates a new branch.
- `feature/kali-ai-lab`: Name of the dedicated development branch.
- `main`: Existing branch used as the starting point.

### Verification

```bash
# HOST: syrus
cd /home/alabi/projects/havenbridge-kali-ai

git branch --show-current
git status --short
git worktree list
```

### Observed Results — November 1, 2026

- The new worktree was created successfully.
- Active branch: `feature/kali-ai-lab`.
- Starting commit: `f320dc9`.
- Git working directory was clean.
- Existing HavenBridge worktrees remained intact.

### Lessons Learned

A Git branch represents an independent line of development.

A Git worktree gives that branch its own working directory,
allowing multiple tasks to proceed without repeatedly switching
branches or disturbing uncommitted work.

## 8. Next Phase — Kali Image and Infrastructure Assessment

Before downloading or deploying anything, verify:

- Available CPU, RAM, and storage on `syrus`.
- Current libvirt networks and storage pools.
- Terraform and libvirt provider versions.
- Kali image format, authenticity, and boot compatibility.
- Whether the image supports the intended automated provisioning approach.

Record actual findings in this README before moving to Phase 2.

## 9. Evidence

Screenshots and diagrams will be stored under:

- `assets/screenshots/`
- `assets/diagrams/`

Only verified evidence will be labelled as completed.

## 10. Git Workflow

Feature branch → Local validation → Commit → Push →
Pull request → CI checks → Review → Merge into protected `main`.

No direct development pushes to `main`.
