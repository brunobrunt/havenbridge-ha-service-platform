# Ansible Configuration Management

This directory contains the Ansible configuration used to prepare and configure the HavenBridge Community Services Kubernetes cluster.

Terraform creates the virtual machines. Ansible connects to those machines over SSH and configures the operating system, container runtime, Kubernetes packages, shared API endpoint, kube-vip, and kubeadm settings.

## Cluster Nodes

| Node           | Role          | IP address     |
| -------------- | ------------- | -------------- |
| `eph-cp01`     | Control plane | `172.16.10.31` |
| `eph-cp02`     | Control plane | `172.16.10.32` |
| `eph-cp03`     | Control plane | `172.16.10.33` |
| `eph-worker01` | Worker        | `172.16.10.34` |
| `eph-worker02` | Worker        | `172.16.10.35` |

The shared Kubernetes API endpoint is:

```text
k8s-api.lab:6443
172.16.10.30
```

## Directory Structure

```text
ansible/
├── ansible.cfg
├── inventory/
│   ├── hosts.yml
│   └── group_vars/
│       └── all.yml
├── playbooks/
│   ├── preflight.yml
│   ├── prepare_nodes.yml
│   ├── install_crio.yml
│   ├── install_kubernetes_packages.yml
│   ├── configure_cluster_endpoint.yml
│   ├── prepare_kube_vip.yml
│   └── prepare_kubeadm_init.yml
├── roles/
│   ├── kubernetes_prerequisites/
│   ├── crio/
│   ├── kubernetes_packages/
│   ├── cluster_endpoint/
│   ├── kube_vip/
│   └── kubeadm_init/
└── README.md
```

## Ansible Concepts

### Playbook

A playbook decides which hosts and roles Ansible should run.

Example:

```yaml
- name: Install CRI-O
  hosts: all
  become: true

  roles:
    - crio
```

### Role

A role is a reusable collection of tasks and files used to configure one specific service or part of a system.

Examples in this project:

```text
crio
kubernetes_packages
kube_vip
kubeadm_init
```

### Task

A task is one individual action performed by Ansible.

A task may:

* Install a package
* Create a file
* Start a service
* Run a command
* Validate a configuration

### Handler

A handler is a special task that runs only when another task notifies it.

Handlers are commonly used to restart a service or refresh a package cache after a configuration file changes.

```text
Task    = performs an action
Handler = reacts to a change
```

### Inventory

The inventory defines the hosts Ansible manages and organizes them into groups.

This project uses:

```text
control_plane
workers
```

### Variables

Shared variables are stored in:

```text
inventory/group_vars/all.yml
```

Examples include:

```yaml
kubernetes_minor_version: "v1.36"
kubernetes_version: "v1.36.2"
crio_version: "v1.36"
control_plane_vip: "172.16.10.30"
pod_network_cidr: "10.244.0.0/16"
service_network_cidr: "10.96.0.0/12"
```

## Ansible Ad Hoc Commands

An ad hoc command performs a single action without creating a playbook.

Example:

```bash
ansible eph-cp01 -b -m command -a "systemctl is-active crio"
```

Command flags:

```text
-b = become root using sudo
-m = choose the Ansible module
-a = provide arguments to the module
```

The command above means:

```text
Connect to eph-cp01
Use sudo
Use the command module
Run systemctl is-active crio
```

## Configuration Workflow

### 1. Inventory and Connectivity

Display the inventory:

```bash
ansible-inventory --graph
```

Test connectivity:

```bash
ansible all -m ping
```

Ansible ping verifies:

* SSH connectivity
* SSH-key authentication
* Python availability
* Ansible module execution

### 2. Preflight Validation

Playbook:

```text
playbooks/preflight.yml
```

Run:

```bash
ansible-playbook playbooks/preflight.yml
```

The preflight playbook checks:

* Ubuntu version
* CPU capacity
* Memory capacity
* Disk capacity
* Static IP addresses
* Default gateway
* Swap status
* Cloud-init completion
* QEMU guest agent
* Time synchronization
* DNS resolution

All five nodes passed the preflight checks.

### 3. Kubernetes Operating-System Prerequisites

Playbook:

```text
playbooks/prepare_nodes.yml
```

Run:

```bash
ansible-playbook playbooks/prepare_nodes.yml
```

This playbook:

* Keeps swap disabled
* Loads the `overlay` kernel module
* Loads the `br_netfilter` kernel module
* Enables IPv4 forwarding
* Enables bridged traffic processing

The required sysctl settings are:

```text
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
```

### 4.CRI-O Container Runtime

CRI-O is the container runtime used by the Kubernetes nodes in this project.

Kubernetes does not run application containers by itself. It asks a container runtime such as CRI-O to:

* Download container images
* Create Pod sandboxes
* Start and stop containers
* Report container status
* Provide container logs
* Manage container storage and networking integration

CRI-O communicates with Kubernetes through the Container Runtime Interface, commonly called CRI.

### Installation Playbook

The CRI-O installation playbook is:

```text
playbooks/install_crio.yml
```

Run it from the Ansible directory:

```bash
ansible-playbook playbooks/install_crio.yml
```

The playbook calls the `crio` role:

```text
roles/crio/
├── tasks/
│   └── main.yml
└── handlers/
    └── main.yml
```

The role performs the following actions:

1. Installs repository requirements.
2. Adds the official CRI-O repository.
3. Installs CRI-O.
4. Enables and starts the CRI-O service.
5. Installs `crictl`.
6. Configures `crictl` to communicate with CRI-O.
7. Configures the Kubernetes pause image.
8. Validates the CRI-O service and socket.

### CRI-O Version

This project uses the CRI-O minor version that matches Kubernetes:

```text
Kubernetes: v1.36
CRI-O:      v1.36
```

Keeping the Kubernetes and CRI-O minor versions aligned helps maintain compatibility.

The version is defined in:

```text
inventory/group_vars/all.yml
```

Example:

```yaml
kubernetes_minor_version: "v1.36"
crio_version: "v1.36"
crictl_version: "v1.36.0"
```

### CRI-O Service

Check the CRI-O service on all nodes:

```bash
ansible all -b -m command -a "systemctl is-active crio"
```

Expected output from every node:

```text
active
```

Check whether CRI-O starts automatically after reboot:

```bash
ansible all -b -m command -a "systemctl is-enabled crio"
```

Expected:

```text
enabled
```

### CRI-O Socket

Kubernetes communicates with CRI-O through this Unix socket:

```text
/run/crio/crio.sock
```

The Ansible variable contains the full socket address:

```yaml
crio_socket: "unix:///run/crio/crio.sock"
```

This socket is used by:

* `kubeadm`
* `kubelet`
* `crictl`

Check that the socket exists:

```bash
ansible all -b -m stat -a "path=/run/crio/crio.sock"
```

Look for:

```text
"exists": true
"issock": true
```

### crictl

`crictl` is a command-line tool used to inspect and troubleshoot CRI-compatible container runtimes.

It is similar to using Docker commands, but it communicates directly with CRI-O.

The configuration file is:

```text
/etc/crictl.yaml
```

Its contents should resemble:

```yaml
runtime-endpoint: unix:///run/crio/crio.sock
image-endpoint: unix:///run/crio/crio.sock
timeout: 10
debug: false
```

Test communication with CRI-O:

```bash
ansible all -b -m command -a "crictl info"
```

List downloaded images:

```bash
ansible eph-cp01 -b -m command -a "crictl images"
```

List running containers:

```bash
ansible eph-cp01 -b -m command -a "crictl ps"
```

### Pause Image

The pause image creates the shared network environment for each Kubernetes Pod.

Application containers inside the same Pod share the network namespace created by the pause container.

The project configures CRI-O to use:

```text
registry.k8s.io/pause:3.10.2
```

The setting is stored in:

```text
/etc/crio/crio.conf.d/10-pause-image.conf
```

Expected contents:

```toml
[crio.image]
pause_image = "registry.k8s.io/pause:3.10.2"
```

Verify the pause-image configuration on all nodes:

```bash
ansible all -b -m command -a \
  "cat /etc/crio/crio.conf.d/10-pause-image.conf"
```

This command:

* Targets all five Kubernetes nodes.
* Uses `sudo` through the `-b` option.
* Reads the custom CRI-O configuration file.
* Confirms that every node uses the same pause image as kubeadm.

Using the same pause-image version in CRI-O and kubeadm prevents the sandbox-image mismatch warning during kubeadm preflight validation.

### Validate CRI-O Versions

Check the CRI-O version:

```bash
ansible all -b -m command -a "crio --version"
```

Check the `crictl` version:

```bash
ansible all -b -m command -a "crictl --version"
```

Expected versions should match the variables defined in:

```text
inventory/group_vars/all.yml
```

### Test on One Node First

Before applying major CRI-O changes to every node, test on the first control-plane node:

```bash
ansible-playbook playbooks/install_crio.yml --limit eph-cp01
```

After the test succeeds, apply the role to all nodes:

```bash
ansible-playbook playbooks/install_crio.yml
```

### Idempotency

Run the CRI-O playbook a second time:

```bash
ansible-playbook playbooks/install_crio.yml
```

The second run should ideally show:

```text
changed=0
unreachable=0
failed=0
```

This confirms that the CRI-O role is idempotent and does not make unnecessary changes when the desired configuration is already present.

### Useful CRI-O Validation Commands

```bash
ansible all -b -m command -a "systemctl is-active crio"

ansible all -b -m command -a "systemctl is-enabled crio"

ansible all -b -m command -a "crio --version"

ansible all -b -m command -a "crictl --version"

ansible all -b -m command -a "crictl info"

ansible all -b -m command -a \
  "cat /etc/crio/crio.conf.d/10-pause-image.conf"
```

Playbook:

```text
playbooks/install_crio.yml
```

Run:

```bash
ansible-playbook playbooks/install_crio.yml
```

CRI-O is the container runtime used by Kubernetes.

Its CRI socket is:

```text
unix:///run/crio/crio.sock
```

Validation commands:

```bash
ansible all -b -m command -a "systemctl is-active crio"
ansible all -b -m command -a "crio --version"
ansible all -b -m command -a "crictl info"
```

### 5. Kubernetes Packages

Playbook:

```text
playbooks/install_kubernetes_packages.yml
```

Run:

```bash
ansible-playbook playbooks/install_kubernetes_packages.yml
```

The role installs:

```text
kubeadm
kubelet
kubectl
```

Purpose of each package:

```text
kubeadm = initializes or joins a Kubernetes cluster
kubelet = runs Kubernetes workloads on each node
kubectl = manages the Kubernetes cluster
```

The installed version is:

```text
v1.36.2
```

The packages are placed on hold to prevent uncontrolled automatic upgrades.

Verify:

```bash
ansible all -b -m command -a "kubeadm version -o short"
ansible all -b -m command -a "kubelet --version"
ansible all -b -m command -a "kubectl version --client=true"
```

### 6. Shared Kubernetes API Endpoint

Playbook:

```text
playbooks/configure_cluster_endpoint.yml
```

Run:

```bash
ansible-playbook playbooks/configure_cluster_endpoint.yml
```

This adds the following entry to `/etc/hosts` on every node:

```text
172.16.10.30 k8s-api.lab
```

The shared endpoint is:

```text
k8s-api.lab:6443
```

The real control-plane addresses remain:

```text
eph-cp01: 172.16.10.31
eph-cp02: 172.16.10.32
eph-cp03: 172.16.10.33
```

### 7. kube-vip Preparation

Playbook:

```text
playbooks/prepare_kube_vip.yml
```

Run:

```bash
ansible-playbook playbooks/prepare_kube_vip.yml
```

kube-vip provides the virtual IP:

```text
172.16.10.30
```

The kube-vip manifest is stored at:

```text
/etc/kubernetes/manifests/kube-vip.yaml
```

It runs as a static Pod.

A static Pod is started directly by kubelet from a YAML file. It does not require the Kubernetes API server to already exist.

This allows kube-vip to advertise the shared API address while the cluster is being initialized.

### 8. kubeadm Configuration

Playbook:

```text
playbooks/prepare_kubeadm_init.yml
```

Run:

```bash
ansible-playbook playbooks/prepare_kubeadm_init.yml
```

The generated kubeadm configuration is stored at:

```text
/etc/kubernetes/kubeadm-init.yaml
```

Important settings include:

```text
Kubernetes version: v1.36.2
Local API endpoint: 172.16.10.31:6443
Shared API endpoint: k8s-api.lab:6443
CRI socket: unix:///run/crio/crio.sock
Pod network: 10.244.0.0/16
Service network: 10.96.0.0/12
```

The configuration is validated using:

```bash
kubeadm config validate \
  --config /etc/kubernetes/kubeadm-init.yaml
```
### kubeadm Preflight Validation

Before initializing the first control-plane node, run kubeadm’s preflight checks:

```bash
ansible eph-cp01 -b -m command -a \
  "kubeadm init phase preflight --config /etc/kubernetes/kubeadm-init.yaml"
```

This command checks whether `eph-cp01` is ready for cluster initialization.

It validates items such as:

* CPU and memory
* Swap status
* Required ports
* CRI-O connectivity
* Kubernetes configuration
* Required system files
* Network prerequisites

This command does not create the cluster. It only checks for problems that could cause `kubeadm init` to fail.

```text
kubeadm init phase preflight = check readiness
kubeadm init                 = create the control plane
```


## Pre-pulling Kubernetes Images

Before initializing the first control-plane node, the required Kubernetes images are downloaded in advance:

```bash
ansible eph-cp01 -b -m command -a \
  "kubeadm config images pull --config /etc/kubernetes/kubeadm-init.yaml"
```

This step is optional because `kubeadm init` can download the images automatically.

Pre-pulling provides several benefits:

* Confirms that CRI-O is working
* Confirms that the Kubernetes registry is reachable
* Detects DNS or internet-access problems early
* Prevents image-download delays during initialization
* Separates image-download errors from cluster-bootstrap errors

```text
kubeadm config images pull = download Kubernetes images
kubeadm init               = create the control plane
```

The following images were downloaded:

```text
kube-apiserver
kube-controller-manager
kube-scheduler
kube-proxy
CoreDNS
pause
etcd
```
## Rotate and Store kubeadm Join Credentials

After `kubeadm init`, kubeadm generates temporary credentials used to join additional control-plane and worker nodes.

These credentials must be treated as secrets.

Do not commit them to GitHub, paste them into documentation, or share them publicly.

### Understand the Tokens

List the current kubeadm tokens:

```bash
sudo kubeadm token list
```

A token with these usages:

```text
authentication,signing
```

is used by new nodes during `kubeadm join`.

A token with a description similar to:

```text
Proxy for managing TTL for the kubeadm-certs secret
```

manages the temporary lifetime of the uploaded control-plane certificates.

The uploaded certificates normally remain available for approximately two hours.

### Delete an Exposed Join Token

When a join token has been displayed publicly or shared accidentally, delete it.

Use the first six characters of the token:

```bash
sudo kubeadm token delete <TOKEN_ID>
```

Example format:

```text
abcdef
```

Verify that it was removed:

```bash
sudo kubeadm token list
```

### Generate a New Certificate Key

Additional control-plane nodes require access to the shared Kubernetes certificates.

Generate a new certificate key and re-upload the certificates:

```bash
sudo kubeadm init phase upload-certs --upload-certs
```

The command prints a long hexadecimal certificate key.

Keep this key private. It can decrypt sensitive control-plane certificate data.

### Generate a New Control-Plane Join Command

Use the new certificate key to create a temporary control-plane join command:

```bash
sudo kubeadm token create \
  --ttl 2h \
  --print-join-command \
  --certificate-key <NEW_CERTIFICATE_KEY>
```

This command is used on:

```text
eph-cp02
eph-cp03
```

The generated command includes:

```text
--control-plane
--certificate-key
```

These options tell kubeadm that the joining node will become another Kubernetes control-plane node.

### Generate a Worker Join Command

Create a separate join command for the worker nodes:

```bash
sudo kubeadm token create \
  --ttl 2h \
  --print-join-command
```

This command is used on:

```text
eph-worker01
eph-worker02
```

Worker nodes do not require:

```text
--control-plane
--certificate-key
```

### Store Join Commands Securely

Store the generated control-plane and worker join commands in a root-only file on `eph-cp01`:

```bash
sudo vim /root/kubeadm-join-commands.txt
```

After pasting the commands, restrict access:

```bash
sudo chmod 600 /root/kubeadm-join-commands.txt
```

Permissions `600` mean:

```text
root can read and write
all other users have no access
```

View the file only when joining nodes:

```bash
sudo cat /root/kubeadm-join-commands.txt
```

Do not add this file to Git.

### Credential Lifetime

The join token and uploaded certificate data are temporary.

For this project, the replacement credentials are created with:

```text
TTL: 2 hours
```

The additional control-plane nodes should be joined within this period.

When the credentials expire, generate new ones using:

```bash
sudo kubeadm init phase upload-certs --upload-certs
```

and:

```bash
sudo kubeadm token create \
  --ttl 2h \
  --print-join-command
```

### Security Summary

```text
Join token       = allows a node to request cluster membership
Certificate key  = decrypts uploaded control-plane certificates
Join command     = contains temporary cluster credentials
```

Never commit or publicly share:

* kubeadm join tokens
* discovery-token hashes combined with valid tokens
* certificate keys
* `/root/kubeadm-join-commands.txt`
* kubeadm initialization output containing credentials


## Calico Networking Plan

Calico will provide Kubernetes Pod networking and network policies.

The planned networks are:

```text
Node network:     172.16.10.0/24
Kubernetes VIP:   172.16.10.30
Pod network:      10.244.0.0/16
Service network:  10.96.0.0/12
```

Calico will use VXLAN encapsulation.

VXLAN wraps Pod traffic inside normal node-to-node traffic, allowing Pods on different Kubernetes nodes to communicate.

```text
Pod traffic
    ↓
Wrapped inside node traffic
    ↓
Travels across 172.16.10.0/24
    ↓
Unwrapped on the destination node
```

## Idempotency

Ansible playbooks should be safe to run more than once.

The first run may report:

```text
changed=3
```

The second run should ideally report:

```text
changed=0
failed=0
unreachable=0
```

This confirms that the system is already in the desired state and Ansible does not make unnecessary changes.

## YAML Validation

Before running a new playbook:

```bash
ansible-playbook --syntax-check playbooks/PLAYBOOK_NAME.yml
```

List the targeted hosts:

```bash
ansible-playbook playbooks/PLAYBOOK_NAME.yml --list-hosts
```

Check for incorrect YAML asterisk markers:

```bash
grep -RIn '^[[:space:]]*\* ' roles playbooks \
  || echo "No invalid YAML asterisk markers found"
```

YAML list items must begin with:

```yaml
- name: Example task
```

not:

```yaml
* name: Example task
```

## Security Notes

Do not commit:

* SSH private keys
* Kubernetes join tokens
* Certificate keys
* `admin.conf`
* `super-admin.conf`
* kubeadm initialization output containing credentials

Temporary kubeadm output should remain protected and outside Git.

## Current Status

Completed:

* Ansible inventory
* Connectivity testing
* Node preflight validation
* Kubernetes operating-system prerequisites
* CRI-O installation
* Kubernetes package installation
* Shared API endpoint configuration
* kube-vip manifest preparation
* kubeadm initialization configuration
* Kubernetes image pre-pull

Next:

1. Run kubeadm preflight validation
2. Initialize `eph-cp01`
3. Configure kubectl
4. Install Calico
5. Join `eph-cp02` and `eph-cp03`
6. Join `eph-worker01` and `eph-worker02`
7. Validate high availability and Pod networking

