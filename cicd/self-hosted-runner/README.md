# HavenBridge Self-Hosted CD Runner

This directory documents the dedicated self-hosted GitHub Actions runner
used for HavenBridge continuous deployment.

The runner provides a controlled path between GitHub Actions and the
private HavenBridge Kubernetes environment.

## Runner Overview

| Component | Value |
|---|---|
| Runner hostname | `havenbridge-runner01` |
| Runner IP | `172.16.10.37` |
| Runner Linux account | `github-runner` |
| Kubernetes namespace | `havenbridge` |
| Kubernetes ServiceAccount | `havenbridge-deployer` |
| Kubernetes API | `https://k8s-api.lab:6443` |
| Runner kubeconfig | `/home/github-runner/.kube/config` |

The runner is provisioned separately from the Kubernetes worker and
control-plane nodes so that CI/CD execution does not require placing
GitHub Actions directly on a Kubernetes node.


## Infrastructure Provisioning

The HavenBridge CD runner is provisioned as a dedicated virtual machine
using Terraform and KVM/libvirt on the `syrus` host.

Terraform configuration is stored under:

```text
terraform/libvirt/cd-runner/


## Infrastructure Provisioning

The HavenBridge CD runner is provisioned as a dedicated virtual machine
using Terraform and KVM/libvirt on the `syrus` host.

Terraform configuration is stored under:

```text
terraform/libvirt/cd-runner/
```

The runner VM is defined with the following resources:

| Resource | Value |
|---|---|
| Hostname | `havenbridge-runner01` |
| IP address | `172.16.10.37` |
| MAC address | `52:54:00:10:00:37` |
| vCPU | `2` |
| Memory | `4096 MiB` |
| Disk | `30 GiB` |
| Hypervisor | KVM/libvirt |
| Operating system | Ubuntu 24.04 |

The runner is intentionally deployed as a separate VM rather than on a
Kubernetes control-plane or worker node.

This isolates CI/CD execution from the Kubernetes nodes and gives the
deployment runner its own operating-system and security boundary.

### Terraform File Responsibilities

The Terraform implementation is divided into small files with specific
responsibilities.

`versions.tf`

Defines the supported Terraform version and pins the libvirt provider.

`providers.tf`

Configures Terraform to communicate with the system-wide libvirt daemon
on `syrus`.

`variables.tf`

Defines configurable values such as the storage location, Ubuntu base
image, SSH key, network, gateway, DNS servers, internal domain and
timezone.

`locals.tf`

Defines the fixed characteristics of `havenbridge-runner01`, including
its IP address, MAC address, CPU, memory and disk size.

`storage.tf`

Creates the dedicated libvirt storage pool, Ubuntu 24.04 base image and
the runner's QCOW2 virtual disk.

`cloud-init.tf`

Generates the cloud-init configuration used during the VM's first boot.

`domains.tf`

Defines the actual KVM virtual machine, attaches its disk and cloud-init
ISO, connects it to the libvirt network and configures automatic startup.

`outputs.tf`

Provides useful Terraform outputs such as the runner name, IP address,
SSH command and storage-pool information.

## Cloud-Init Configuration

Cloud-init performs the initial operating-system configuration when the
runner VM boots for the first time.

The templates are stored at:

```text
terraform/libvirt/cd-runner/templates/
```

The `user-data.yaml.tftpl` template performs initial host configuration,
including:

- setting the hostname;
- creating the `mino` administrative user;
- installing the SSH public key;
- disabling SSH password authentication;
- disabling direct root login;
- configuring the `America/Edmonton` timezone;
- installing baseline utilities;
- enabling the QEMU guest agent;
- expanding the root filesystem.

The `network-config.yaml.tftpl` template configures:

```text
IP address: 172.16.10.37/24
Gateway:    172.16.10.1
Interface:  eth0
```

## SSH and Ansible Management

After Terraform and cloud-init provision the VM, ongoing configuration
management is handled by Ansible from `syrus`.

The runner is registered in:

```text
ansible/inventory/hosts.yml
```

under the:

```text
cd_runners
```

inventory group.

The inventory entry defines:

```text
Hostname: havenbridge-runner01
IP:       172.16.10.37
SSH user: mino
```

SSH authentication uses the existing HavenBridge SSH key:

```text
/home/alabi/.ssh/eph_k8s
```

Ansible connectivity was validated from:

```text
/home/alabi/projects/havenbridge-ha-service-platform/ansible/
```

using:

```bash
ansible havenbridge-runner01 -m ping
```

Successful result:

```text
havenbridge-runner01 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

This proves that `syrus` can securely reach and manage the dedicated
CD runner over SSH.

## CD Runner Ansible Configuration

The dedicated runner playbook is:

```text
ansible/playbooks/configure_cd_runner.yml
```

The playbook targets only the:

```text
cd_runners
```

inventory group and applies the:

```text
cd_runner
```

role.

The role is stored at:

```text
ansible/roles/cd_runner/
```

The role prepares `havenbridge-runner01` for continuous deployment by:

- installing Git;
- installing curl, wget and jq;
- installing supporting utilities;
- creating the dedicated `github-runner` Linux account;
- configuring the Kubernetes v1.36 APT repository;
- installing `kubectl`.

The `github-runner` account is separate from the `mino`
administrative account.

This provides a dedicated operating-system identity for GitHub Actions
jobs instead of running deployment jobs as the VM administrator.

## Provisioning Flow

The complete self-hosted runner provisioning and access flow is:

```text
Terraform
    ↓
KVM/libvirt VM
    ↓
Ubuntu 24.04
    ↓
cloud-init
    ↓
Static IP 172.16.10.37
    ↓
SSH connectivity from syrus
    ↓
Ansible
    ↓
github-runner Linux account
    ↓
kubectl
    ↓
/home/github-runner/.kube/config
    ↓
havenbridge-deployer ServiceAccount
    ↓
RoleBinding
    ↓
Namespace-scoped Role
    ↓
HavenBridge deployment operations
```

This separates infrastructure provisioning, operating-system
configuration, and Kubernetes authorization into distinct layers.



## Kubernetes CD Identity

The self-hosted runner does not use Kubernetes cluster-administrator
credentials.

A dedicated ServiceAccount named `havenbridge-deployer` is used in the
`havenbridge` namespace.

The access path is:

```text
GitHub Actions
        ↓
havenbridge-runner01
        ↓
github-runner
        ↓
/home/github-runner/.kube/config
        ↓
havenbridge-deployer ServiceAccount
        ↓
RoleBinding
        ↓
Namespace-scoped Role
        ↓
HavenBridge application resources
```

## Restricted Kubeconfig

The Kubernetes credential used by the runner is stored at:

```text
/home/github-runner/.kube/config
```

The file is owned by:

```text
github-runner:github-runner
```

and protected with file mode:

```text
600
```

The kubeconfig authenticates to Kubernetes as:

```text
system:serviceaccount:havenbridge:havenbridge-deployer
```

## Positive Authorization Validation

The deployment identity was tested directly from
`havenbridge-runner01` using the actual `github-runner` Linux account.

Command:

```bash
sudo -u github-runner \
  KUBECONFIG=/home/github-runner/.kube/config \
  kubectl get deployment havenbridge-api \
  -n havenbridge
```

Successful result:

```text
NAME              READY   UP-TO-DATE   AVAILABLE   AGE
havenbridge-api   2/2     2            2           16d
```

This confirms that the self-hosted runner can reach the Kubernetes API,
authenticate using the dedicated ServiceAccount, and access the
HavenBridge Deployment.

## Negative Authorization Validation

Secret access was intentionally tested:

```bash
sudo -u github-runner \
  KUBECONFIG=/home/github-runner/.kube/config \
  kubectl get secrets \
  -n havenbridge
```

Kubernetes returned `Forbidden`.

This result is expected and proves that the CD identity cannot list
Kubernetes Secrets.

## Least-Privilege Design

I created a dedicated Kubernetes ServiceAccount for CD. A
namespace-scoped Role grants only the deployment permissions it needs,
and a RoleBinding connects the identity to those permissions. I then
tested both positive and negative authorization cases to prove least
privilege.

The CD runner therefore does not require the Kubernetes administrator
kubeconfig or cluster-admin privileges.

## Validation Evidence

Detailed validation output is stored in:

```text
cicd/self-hosted-runner/evidence/kubernetes-rbac-validation.txt
```

No Kubernetes token values or private credentials are stored in the
documentation.

## GitHub Actions Runner Registration

After the virtual machine, operating-system configuration, Kubernetes
access and RBAC validation were completed, `havenbridge-runner01` was
registered with the HavenBridge GitHub repository as a self-hosted
GitHub Actions runner.

The runner was registered with:

```text
Runner name:  havenbridge-runner01
Runner label: havenbridge-cd
Runner group: Default
Work folder:  _work
```

The custom `havenbridge-cd` label allows HavenBridge deployment
workflows to target this runner specifically.

A future GitHub Actions deployment job can therefore use:

```yaml
runs-on: [self-hosted, havenbridge-cd]
```

This prevents the HavenBridge CD job from being sent to unrelated
self-hosted runners.

## GitHub Actions Runner Service

The GitHub Actions runner application is installed under:

```text
/home/github-runner/actions-runner
```

The runner is operated by the dedicated Linux account:

```text
github-runner
```

The administrative `mino` account does not have direct access to the
`github-runner` home directory without privilege elevation.

This preserves separation between the VM administrator and the identity
that executes GitHub Actions jobs.

The GitHub Actions runner was installed as a systemd service:

```text
actions.runner.brunobrunt-havenbridge-ha-service-platform.havenbridge-runner01.service
```

The service was configured to run as:

```text
github-runner
```

and is enabled to start automatically when `havenbridge-runner01`
boots.

Service validation showed:

```text
Loaded: loaded
Enabled: enabled
Active: active (running)
```

The runner successfully connected to GitHub and reported:

```text
Connected to GitHub
Current runner version: 2.336.0
Listening for Jobs
```

The running process was also verified to be owned by the
`github-runner` Linux account.

The final service execution path is:

```text
GitHub Actions
        ↓
havenbridge-runner01
        ↓
systemd
        ↓
GitHub Actions Runner service
        ↓
github-runner Linux account
        ↓
_work/
        ↓
kubectl
        ↓
/home/github-runner/.kube/config
        ↓
havenbridge-deployer ServiceAccount
        ↓
Namespace-scoped Kubernetes RBAC
```

This means the self-hosted runner is now online, persistent across VM
reboots, connected to GitHub and ready to receive HavenBridge CD jobs.



## Current Status

The following self-hosted CD runner milestones are complete:

* GitHub Actions runner software installed.
* Runner registered with the HavenBridge GitHub repository.
* Runner registered as `havenbridge-runner01`.
* Custom `havenbridge-cd` runner label configured.
* GitHub Actions runner installed as a systemd service.
* Runner service enabled for automatic startup.
* Runner service validated as `active (running)`.
* Runner process validated as running under `github-runner`.
* GitHub connectivity validated.
* Runner confirmed as listening for GitHub Actions jobs.

The next phase is to connect the self-hosted runner to the HavenBridge
GitHub Actions continuous deployment workflow.

