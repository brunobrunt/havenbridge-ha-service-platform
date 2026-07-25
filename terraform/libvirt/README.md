# HavenBridge Community Services Kubernetes Platform

## Infrastructure Provisioning with Terraform, KVM/libvirt and Cloud-init

**Project status:** In progress
**Project owner:** Adeola Alabi
**Host system:** Dell Precision 5810
**Host operating system:** Ubuntu 24.04 LTS
**Primary objective:** Build a production-like Kubernetes platform for the HavenBridge Community Services Connect prototype.

---

## 1. Project Overview

This project provisions and configures a highly available Kubernetes lab environment for a proposed HavenBridge Community Services service-inquiry and staff-coordination application.

The infrastructure will use:

* Terraform for virtual-machine provisioning
* KVM/QEMU as the hypervisor
* libvirt for virtual-machine management
* Ubuntu 24.04 cloud images
* Cloud-init for first-boot configuration
* Ansible for operating-system and Kubernetes preparation
* kubeadm for Kubernetes cluster creation
* kube-vip or HAProxy for the highly available Kubernetes API endpoint
* Calico for Kubernetes networking
* Helm for application packaging
* GitHub Actions and Argo CD for CI/CD and GitOps
* Prometheus, Grafana and Alertmanager for monitoring

The environment will initially run entirely on one physical Dell Precision 5810 server.

Although the Kubernetes control plane will be highly available at the virtual-machine level, the project is described as a **production-like HA lab** because all virtual machines depend on one physical host.

---

## 2. Business Context

The proposed application is called:

## HavenBridge Community Services Connect

The prototype is intended to demonstrate a centralized platform for:

* Receiving service inquiries
* Assigning inquiries to employees
* Tracking follow-up activities
* Identifying overdue inquiries
* Measuring response times
* Viewing service-demand reports
* Providing access to approved employee resources

The prototype will use fictional demonstration data only.

It will not store real health information, client records, employee records or other sensitive personal information.

---

## 3. Learning Objectives

This project is also being used to develop practical experience with Terraform and infrastructure as code.

The learning objectives include:

1. Understanding Terraform providers.
2. Declaring infrastructure using HCL.
3. Using variables and local values.
4. Creating multiple similar resources with `for_each`.
5. Managing KVM virtual machines through libvirt.
6. Creating and cloning QCOW2 disks.
7. Configuring virtual machines with cloud-init.
8. Managing Terraform state.
9. Understanding Terraform plans and applies.
10. Testing infrastructure idempotency.
11. Destroying and recreating infrastructure safely.
12. Documenting infrastructure decisions and troubleshooting steps.

---

## 4. Physical Host Specifications

The infrastructure runs on the following host:

| Component              | Specification         |
| ---------------------- | --------------------- |
| Hostname               | `syrus`               |
| Hardware               | Dell Precision 5810   |
| Operating system       | Ubuntu 24.04 LTS      |
| Processor              | Intel Xeon E5-1650 v3 |
| Physical cores         | 6                     |
| Logical CPUs           | 12                    |
| Memory                 | 125 GiB               |
| Primary filesystem     | `/dev/sda2`           |
| Primary free space     | Approximately 192 GiB |
| VM data filesystem     | `/data_all`           |
| VM data free space     | Approximately 1.7 TiB |
| Hypervisor             | KVM/QEMU              |
| libvirt version        | 10.0.0                |
| QEMU version           | 8.2.2                 |
| Virtualization support | Intel VT-x            |

The host has sufficient memory and storage for the planned five-node Kubernetes environment.

CPU allocation must be managed carefully because the host has 12 logical processors.

---

## 5. Planned Virtual Machines

The initial Kubernetes environment will contain five virtual machines.

| Virtual machine | Role                     |     IP address | vCPU |  RAM |  Disk |
| --------------- | ------------------------ | -------------: | ---: | ---: | ----: |
| `eph-cp01`      | Kubernetes control plane | `172.16.10.31` |    2 | 4 GB | 40 GB |
| `eph-cp02`      | Kubernetes control plane | `172.16.10.32` |    2 | 4 GB | 40 GB |
| `eph-cp03`      | Kubernetes control plane | `172.16.10.33` |    2 | 4 GB | 40 GB |
| `eph-worker01`  | Kubernetes worker        | `172.16.10.34` |    2 | 8 GB | 60 GB |
| `eph-worker02`  | Kubernetes worker        | `172.16.10.35` |    2 | 8 GB | 60 GB |

Reserved Kubernetes API virtual address:

| Purpose            |        Address |
| ------------------ | -------------: |
| Kubernetes API VIP | `172.16.10.30` |

The Kubernetes API VIP will later be managed with kube-vip or another load-balancing solution.

---

## 6. Network Design

The project uses the existing libvirt `default` network.

| Network property     | Value                         |
| -------------------- | ----------------------------- |
| Network name         | `default`                     |
| Bridge               | `virbr0`                      |
| Network              | `172.16.10.0/24`              |
| Gateway              | `172.16.10.1`                 |
| DHCP range           | `172.16.10.100–172.16.10.254` |
| Static project range | `172.16.10.30–172.16.10.35`   |

The project addresses are outside the DHCP range, reducing the risk of address conflicts.

The following addresses were tested and found to be available:

```text
172.16.10.30
172.16.10.31
172.16.10.32
172.16.10.33
172.16.10.34
172.16.10.35
```

---

## 7. Storage Design

Virtual-machine disks will be stored under:

```text
/data_all/libvirt/eph-k8s
```

This filesystem was selected because it has approximately 1.7 TiB of available space.

The planned maximum virtual disk capacity is:

```text
3 control-plane disks × 40 GB = 120 GB
2 worker disks × 60 GB        = 120 GB
Total virtual capacity        = 240 GB
```

QCOW2 disks use thin provisioning.

This means a virtual disk configured for 60 GB does not consume 60 GB immediately. Its physical usage grows as data is written.

---

## 8. Ubuntu Base Image

The project uses the official Ubuntu 24.04 cloud image:

```text
/home/alabi/images/ubuntu/ubuntu-24.04-server-cloudimg-amd64.img
```

Image information:

| Property                 | Value                 |
| ------------------------ | --------------------- |
| Format                   | QCOW2                 |
| Download size            | Approximately 593 MiB |
| Initial virtual capacity | 3.5 GiB               |
| Corruption status        | False                 |
| Checksum validation      | Successful            |

Checksum result:

```text
ubuntu-24.04-server-cloudimg-amd64.img: OK
```

### Why the 3.5 GiB capacity is not a limitation

The 3.5 GiB value belongs only to the reusable base image.

Terraform will create larger VM disks from this image:

```text
Ubuntu base image: 3.5 GiB
        |
        +-- eph-cp01: 40 GB
        +-- eph-cp02: 40 GB
        +-- eph-cp03: 40 GB
        +-- eph-worker01: 60 GB
        +-- eph-worker02: 60 GB
```

Cloud-init will expand the root partition and filesystem during the first boot.

---

## 9. Why a Cloud Image Is Used

An Ubuntu installation ISO could be used, but it would require either:

* Installing Ubuntu manually on all five VMs, or
* Building an Ubuntu Autoinstall configuration

The cloud image already contains an installed Ubuntu system and supports cloud-init.

The selected workflow is:

```text
Terraform creates the virtual machine
        |
        v
Terraform creates a disk from the Ubuntu cloud image
        |
        v
Cloud-init configures the operating system
        |
        v
The VM becomes available through SSH
        |
        v
Ansible installs Kubernetes prerequisites
```

This approach is faster, repeatable and better suited to infrastructure automation.

---

## 10. SSH Access

A dedicated SSH key was created for the project:

```text
Private key: /home/alabi/.ssh/eph_k8s
Public key:  /home/alabi/.ssh/eph_k8s.pub
```

The private key must never be:

* Committed to Git
* Included in Terraform files
* Copied into cloud-init
* Shared publicly

Only the public key is installed on the virtual machines.

Public-key fingerprint:

```text
SHA256:C7iu6Jma06msyF8cWIErurkBspCirvrOpXLOc1ChpNY
```

The fingerprint is a short identifier calculated from the full public key. It is not a different SSH key.

---

## 11. Infrastructure Responsibility Model

Each tool has a specific responsibility.

### Terraform

Terraform will create:

* The libvirt storage pool
* VM disks
* Cloud-init seed disks
* VM CPU and memory assignments
* VM network interfaces
* KVM domains

### Cloud-init

Cloud-init will perform the initial operating-system setup:

* Configure the hostname
* Create the administrative user
* Install the SSH public key
* Configure static networking
* Install basic packages
* Start the QEMU guest agent
* Disable swap
* Expand the root filesystem

### Ansible

Ansible will later configure:

* Containerd
* Kubernetes package repositories
* kubeadm
* kubelet
* kubectl
* Kernel modules
* Required sysctl settings
* Node validation

### kubeadm

kubeadm will:

* Initialize the first control plane
* Join additional control-plane nodes
* Join worker nodes
* Generate Kubernetes certificates
* Configure the cluster control plane

---

## 12. Terraform Project Structure

Planned directory structure:

```text
havenbridge-ha-service-platform/
└── terraform/
    └── libvirt/
        ├── versions.tf
        ├── providers.tf
        ├── variables.tf
        ├── locals.tf
        ├── storage.tf
        ├── cloud-init.tf
        ├── domains.tf
        ├── outputs.tf
        ├── terraform.tfvars
        ├── terraform.tfvars.example
        ├── templates/
        │   ├── user-data.yaml.tftpl
        │   └── network-config.yaml.tftpl
        ├── scripts/
        ├── .gitignore
        └── README.md
```

Terraform reads all files ending in `.tf` within the current directory and combines them into one configuration.

The files are separated for human readability rather than because Terraform requires these particular filenames.

---

## 13. Purpose of Each Terraform File

### `versions.tf`

Defines:

* The required Terraform version
* The required providers
* Provider version constraints

### `providers.tf`

Configures Terraform’s connection to libvirt:

```text
qemu:///system
```

### `variables.tf`

Declares configurable input values.

Examples include:

* Base-image path
* Storage-pool path
* SSH public-key path
* Network gateway
* DNS servers

### `terraform.tfvars`

Provides the actual local values for declared variables.

This file is excluded from Git because it may contain host-specific paths or sensitive environment values.

### `locals.tf`

Defines internal reusable values, including the five-node VM inventory.

### `storage.tf`

Defines:

* The libvirt storage pool
* The reusable base-image volume
* Individual VM disks
* Disk capacities

### `cloud-init.tf`

Generates the cloud-init seed disk for each VM.

### `domains.tf`

Defines the actual KVM virtual machines.

A libvirt virtual machine is called a domain.

### `outputs.tf`

Displays useful information after provisioning, including:

* VM names
* IP addresses
* SSH commands
* Control-plane addresses
* Worker addresses

### `templates/user-data.yaml.tftpl`

Contains the cloud-init operating-system configuration.

### `templates/network-config.yaml.tftpl`

Contains the static-network configuration for each VM.

### `.gitignore`

Prevents local Terraform data and sensitive files from being committed.

### `README.md`

Documents the project, learning process, architecture, commands, decisions and troubleshooting history.

---

## 14. Important Terraform Concepts

### Provider

A provider is a plugin that allows Terraform to communicate with an external platform.

This project uses the libvirt provider so Terraform can manage KVM virtual machines.

### Resource

A resource is an infrastructure object managed by Terraform.

Examples include:

* A storage pool
* A QCOW2 disk
* A cloud-init disk
* A virtual machine

### Variable

A variable is an input that can change between environments.

### Local value

A local value is an internal reusable value calculated or organized within the Terraform project.

### State

Terraform state records which real infrastructure objects correspond to the resources declared in the configuration.

The state file must be protected and should not be committed publicly.

### Plan

`terraform plan` compares:

* The desired configuration
* The Terraform state
* The real infrastructure

It then reports what Terraform intends to create, modify or destroy.

### Apply

`terraform apply` performs the changes described in the Terraform plan.

### Destroy

`terraform destroy` removes infrastructure managed by the current Terraform state.

### Idempotency

An idempotent configuration produces no additional changes when the infrastructure already matches the declared configuration.

A successful idempotency check should report:

```text
No changes. Your infrastructure matches the configuration.
```

---

## 15. Current Prerequisites

The following tools are required:

* Terraform
* Git
* KVM/QEMU
* libvirt
* `virsh`
* `qemu-img`
* `cloud-localds`
* `jq`
* `wget`
* `curl`

Current verified components:

```text
KVM/QEMU:             Installed
libvirt:              Running
virsh non-root access: Working
Default network:      Active
Ubuntu cloud image:   Downloaded
Image checksum:       Valid
SSH public key:       Created
Project IP range:     Available
```

---

## 16. Current Progress

### Completed

* [x] Confirmed host CPU, memory and storage capacity
* [x] Confirmed Intel virtualization support
* [x] Confirmed libvirt is active
* [x] Confirmed the `default` libvirt network is active
* [x] Confirmed non-root libvirt access
* [x] Removed the obsolete `ISO's` storage-pool definition
* [x] Selected `/data_all` for VM storage
* [x] Confirmed proposed static IP addresses are available
* [x] Installed supporting cloud-image utilities
* [x] Downloaded the Ubuntu 24.04 cloud image
* [x] Verified the Ubuntu image checksum
* [x] Confirmed the image is QCOW2 and not corrupt
* [x] Created a dedicated project SSH key

### In progress

* [ ] Create the Terraform project directory
* [ ] Configure `versions.tf`
* [ ] Configure `providers.tf`
* [ ] Run the first `terraform init`

### Planned

* [ ] Define input variables
* [ ] Define the five-node VM inventory
* [ ] Create the libvirt storage pool
* [ ] Import the Ubuntu base image
* [ ] Create VM disks
* [ ] Create cloud-init templates
* [ ] Create the five KVM domains
* [ ] Run `terraform validate`
* [ ] Run `terraform plan`
* [ ] Run `terraform apply`
* [ ] Validate network and SSH access
* [ ] Confirm disk expansion
* [ ] Test Terraform idempotency
* [ ] Test infrastructure destruction and recreation
* [ ] Configure the VMs using Ansible
* [ ] Build the Kubernetes cluster using kubeadm

---

## 17. Troubleshooting Log

### Obsolete libvirt storage pool

#### Symptom

libvirt reported:

```text
Failed to autostart storage pool 'ISO's'
```

The pool pointed to:

```text
/home/alabi/Downloads/ISO's
```

The directory no longer existed.

#### Resolution

Autostart was disabled and the obsolete pool definition was removed.

The active pools are now:

```text
default
Downloads
ISO
```

### Historical XATTR warnings

libvirt previously reported security-label timestamp warnings for older Kubernetes QCOW2 disks.

The warnings were historical and did not reappear during the latest libvirt restart.

No extended attributes were manually deleted.

### `cloud-localds --version`

The command:

```bash
cloud-localds --version
```

returned an unsupported-option message.

This does not mean the application is missing. `cloud-localds` does not provide a `--version` option.

Installation can be confirmed with:

```bash
command -v cloud-localds
dpkg-query -W cloud-image-utils
```

---

## 18. Security Considerations

* Do not commit private SSH keys.
* Do not commit Terraform state files.
* Do not place real passwords in Terraform source files.
* Do not use real HavenBridge Community Services client information.
* Do not store sensitive health or employee data in the prototype.
* Use fictional demonstration data.
* Restrict VM access to the private lab network.
* Apply Kubernetes RBAC and NetworkPolicies later.
* Use encrypted application connections.
* Scan container images before deployment.

---

## 19. Planned Validation Tests

After provisioning, each VM must pass the following checks:

* VM is running
* Expected hostname is configured
* Expected static IP is configured
* Default route points to `172.16.10.1`
* DNS resolution works
* Internet access works
* SSH public-key login works
* Password-based SSH login is disabled
* QEMU guest agent is running
* Swap is disabled
* Root disk has expanded to the expected size
* All nodes can communicate with one another
* Terraform reports no unexpected drift

---

## 20. Planned Terraform Workflow

The normal Terraform workflow will be:

```bash
terraform fmt
terraform init
terraform validate
terraform plan
terraform apply
terraform output
terraform plan
```

Purpose of each command:

| Command              | Purpose                                                   |
| -------------------- | --------------------------------------------------------- |
| `terraform fmt`      | Formats Terraform configuration consistently              |
| `terraform init`     | Downloads providers and initializes the working directory |
| `terraform validate` | Checks the syntax and internal consistency                |
| `terraform plan`     | Shows proposed infrastructure changes                     |
| `terraform apply`    | Creates or changes the infrastructure                     |
| `terraform output`   | Displays declared output values                           |
| `terraform destroy`  | Removes managed infrastructure                            |

---

## 21. Future Project Phases

### Phase 1: Infrastructure provisioning

Provision five Ubuntu virtual machines with Terraform and cloud-init.

### Phase 2: Operating-system configuration

Use Ansible to prepare all nodes for Kubernetes.

### Phase 3: Kubernetes cluster creation

Create:

* Three control-plane nodes
* Two worker nodes
* Highly available API endpoint
* Calico networking

### Phase 4: Platform services

Deploy:

* NGINX Ingress Controller
* cert-manager
* Prometheus
* Grafana
* Alertmanager
* Loki
* Argo CD

### Phase 5: Application deployment

Deploy the HavenBridge Community Services Connect prototype.

### Phase 6: Security and reliability

Implement:

* RBAC
* NetworkPolicies
* TLS
* Image scanning
* Backup and recovery
* Node-failure testing
* Upgrade testing

---

## 22. Project Documentation Policy

This README will be updated after each project milestone.

Each update should record:

1. What was implemented.
2. Why it was needed.
3. Commands that were executed.
4. Expected results.
5. Actual results.
6. Problems encountered.
7. How the problems were resolved.
8. What remains to be completed.

This approach makes the repository useful as both a technical portfolio and a Terraform learning resource.


## Terraform Provider Initialization

### Purpose

The first Terraform configuration stage declares the Terraform CLI requirements and the libvirt provider used to manage KVM infrastructure.

No virtual machines or storage resources are created during this stage.

### `versions.tf`

The `versions.tf` file contains:

```hcl
terraform {
  required_version = ">= 1.0.0, < 2.0.0"

  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "~> 0.9.8"
    }
  }
}
```

This configuration establishes:

* The supported Terraform CLI range.
* The source of the libvirt provider.
* The acceptable libvirt provider release range.

The constraint `~> 0.9.8` permits compatible `0.9.x` releases beginning with `0.9.8`, but it does not permit version `0.10.0` or later.

### `providers.tf`

The `providers.tf` file contains:

```hcl
provider "libvirt" {
  uri = "qemu:///system"
}
```

This configures Terraform to connect to the host’s system-wide libvirt service.

The same connection can be tested outside Terraform with:

```bash
virsh -c qemu:///system list --all
```

### Terraform initialization

The working directory is initialized with:

```bash
terraform init
```
##### The Libvirt provider is used to interact with libvirt to manage virtual machines, networks, storage pools, and other resources.

Initialization performs the following actions:

1. Reads the Terraform and provider requirements.
2. Downloads the selected libvirt provider.
3. Creates the local `.terraform` working directory.
4. Creates `.terraform.lock.hcl`.
5. Records provider version and checksum information.

The `.terraform` directory is excluded from Git because it can be recreated.

The `.terraform.lock.hcl` file is committed because it records the exact provider selection and supports repeatable initialization.

### Validation

The provider configuration is checked with:

```bash
terraform providers
terraform validate
```

Expected validation result:

```text
Success! The configuration is valid.
```
## Successful Infrastructure Deployment

Terraform successfully provisioned the initial HavenBridge Community Services Kubernetes lab environment.

### Deployed virtual machines

| Node           | Role          |     IP address | vCPU | Memory |   Disk |
| -------------- | ------------- | -------------: | ---: | -----: | -----: |
| `eph-cp01`     | Control plane | `172.16.10.31` |    2 |  4 GiB | 40 GiB |
| `eph-cp02`     | Control plane | `172.16.10.32` |    2 |  4 GiB | 40 GiB |
| `eph-cp03`     | Control plane | `172.16.10.33` |    2 |  4 GiB | 40 GiB |
| `eph-worker01` | Worker        | `172.16.10.34` |    2 |  8 GiB | 60 GiB |
| `eph-worker02` | Worker        | `172.16.10.35` |    2 |  8 GiB | 60 GiB |

A third worker is reserved for future horizontal scaling:

```text
eph-worker03
172.16.10.36
```

### Terraform-managed resources

Terraform currently tracks 22 resources:

```text
1 libvirt storage pool
6 QCOW2 storage volumes
5 generated cloud-init disks
5 uploaded cloud-init ISO volumes
5 KVM virtual machines
```

The resource count was verified with:

```bash
terraform state list | wc -l
```

Result:

```text
22
```

### Cloud-init validation

Cloud-init completed successfully on all five nodes.

The following items were verified:

* Correct hostnames
* Correct static IP addresses
* Correct control-plane and worker roles
* SSH key authentication
* QEMU guest agent running
* Root filesystem expansion
* Default gateway configuration
* Cloud-init completion without errors

Example validation results from `eph-cp01`:

```text
Hostname: eph-cp01
IP: 172.16.10.31
Cloud-init: done
Guest agent: active
Node role: control-plane
Root filesystem: approximately 38 GiB usable
```

Worker nodes received approximately 58 GiB of usable root filesystem capacity from their 60 GiB virtual disks.

### Idempotency

After deployment, Terraform reported:

```text
No changes. Your infrastructure matches the configuration.
```

This confirms that the Terraform configuration, state file and real libvirt infrastructure are synchronized.

### Git milestone

The initial Terraform infrastructure was committed to Git with:

```text
Provision Kubernetes lab infrastructure with Terraform
```

The repository uses the `main` branch.

