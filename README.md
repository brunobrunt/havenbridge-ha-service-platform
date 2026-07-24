# Ever Presence Haven Platform

A production-like infrastructure and application prototype for Ever Presence Haven.

## Project Components

* Terraform and KVM/libvirt virtual-machine provisioning
* Cloud-init operating-system bootstrap
* Ansible configuration management
* Highly available Kubernetes cluster
* Application deployment with Helm and GitOps
* Monitoring with Prometheus and Grafana

## Kubernetes Cluster Architecture

The platform uses a highly available Kubernetes control plane consisting of three control-plane nodes and two worker nodes.

```text
                  k8s-api.lab:6443
                    172.16.10.30
                           |
                      kube-vip
                           |
          +----------------+----------------+
          |                |                |
      eph-cp01         eph-cp02         eph-cp03
    172.16.10.31     172.16.10.32     172.16.10.33
      API server       API server       API server
      Controller       Controller       Controller
      Scheduler        Scheduler        Scheduler
      etcd member      etcd member      etcd member
          |                |                |
          +----------------+----------------+
                           |
              +------------+------------+
              |                         |
         eph-worker01              eph-worker02
         172.16.10.34              172.16.10.35
```

### Architecture Components

* `k8s-api.lab:6443` is the shared Kubernetes API endpoint.
* `172.16.10.30` is the virtual IP reserved for the Kubernetes API.
* `kube-vip` provides availability for the shared control-plane endpoint.
* `eph-cp01`, `eph-cp02`, and `eph-cp03` run the API server, controller manager, scheduler, and stacked etcd.
* `eph-worker01` and `eph-worker02` run application workloads.
* A future third worker, `eph-worker03`, is reserved at `172.16.10.36`.

## Current Phase

### Phase 1: Terraform Infrastructure — Complete

Terraform, KVM/libvirt, cloud-init, and Ubuntu 24.04 cloud images were used to provision:

* Three control-plane nodes
* Two worker nodes
* Static IP networking
* Dedicated virtual disks
* Cloud-init bootstrap configuration

Detailed Terraform documentation is available in:

[`terraform/libvirt/README.md`](terraform/libvirt/README.md)



### Phase 3: Ansible Configuration Management — In Progress

Ansible inventory and connectivity have been configured for all five nodes.

All nodes successfully passed the preflight validation, including checks for:

* CPU, memory, and disk capacity
* Static IP configuration
* Default gateway
* Swap status
* Cloud-init completion
* QEMU guest agent
* Time synchronization
* DNS resolution

The next step is configuring the operating-system prerequisites required by Kubernetes, followed by containerd, kubeadm, kubelet, and kubectl.

Detailed Ansible documentation is available in:

[`ansible/README.md`](ansible/README.md)

## Planned Kubernetes Stack

* Kubernetes `v1.36`
* Three-node stacked-etcd control plane
* Two initial worker nodes
* `kube-vip` virtual API endpoint
* containerd runtime
* Calico networking
* Metrics Server
* Helm
* GitOps
* Prometheus and Grafana


## Monitoring, Alerting and Application Observability

After the highly available Kubernetes cluster is fully configured and all control-plane and worker nodes are healthy, the project will include a dedicated monitoring and alerting phase.

This phase will demonstrate how the Ever Presence Haven platform can run a containerized application while providing visibility into infrastructure health, application performance and service availability.

### Objectives

The monitoring phase will:

* Deploy Prometheus for Kubernetes and application metrics collection.
* Deploy Grafana for dashboards and visualization.
* Deploy Alertmanager for routing and managing alerts.
* Monitor Kubernetes nodes, Pods, Deployments and cluster components.
* Deploy a web application and its dependent services.
* Configure application-specific metrics and dashboards.
* Create alerts for infrastructure and application failures.
* Document deployment, validation and troubleshooting procedures.

### Proposed Application Workload

A sample Ever Presence Haven web application will be deployed to demonstrate a realistic multi-service workload.

The application may include:

```text
Web frontend
    ↓
Application API
    ↓
Database service
```

Depending on the final application design, additional services such as Redis, an ingress controller or persistent storage may also be included.

The workload will be deployed using Kubernetes resources such as:

* Namespace
* Deployment
* Service
* ConfigMap
* Secret
* PersistentVolumeClaim
* Ingress
* HorizontalPodAutoscaler
* PodDisruptionBudget

### Monitoring Components

The project will use the following observability components:

#### Prometheus

Prometheus will collect metrics from:

* Kubernetes nodes
* kubelet
* Kubernetes API server
* Deployments and Pods
* Container resource usage
* Application endpoints
* Database or dependent services where supported

#### Grafana

Grafana dashboards will display:

* Node CPU, memory and disk usage
* Pod CPU and memory usage
* Pod restarts
* Deployment replica availability
* Kubernetes API health
* Application request rate
* Application response latency
* HTTP error rate
* Application and database availability

#### Alertmanager

Alertmanager will receive alerts from Prometheus and manage notification routing.

Initial alerts may include:

* Kubernetes node unavailable
* Pod repeatedly restarting
* Deployment replicas unavailable
* High node CPU usage
* High node memory usage
* Low disk space
* Application endpoint unavailable
* High HTTP error rate
* High application response latency
* PersistentVolume nearing capacity

### Application Monitoring

The sample application will expose a metrics endpoint that Prometheus can scrape.

Where supported, the application will provide metrics such as:

```text
HTTP request count
HTTP response status
Request duration
Application error count
Active connections
Dependency health
```

A Kubernetes `ServiceMonitor` or `PodMonitor` will be used to tell Prometheus how to discover and scrape the application.

### Alerting Validation

The project will include controlled failure tests to verify that alerts work correctly.

Examples include:

* Scaling the application Deployment to zero replicas
* Stopping or deleting an application Pod
* Simulating an unhealthy application endpoint
* Generating elevated HTTP error responses
* Creating temporary CPU or memory pressure
* Making a dependent service unavailable

The resulting alert will be observed in Prometheus and Alertmanager, and the recovery state will be confirmed after the issue is resolved.

### Deployment Approach

The monitoring stack will be deployed after the Kubernetes cluster is stable.

The preferred implementation will use Helm and the Prometheus Community `kube-prometheus-stack`, which provides:

* Prometheus
* Grafana
* Alertmanager
* kube-state-metrics
* Prometheus Node Exporter
* Prometheus Operator
* Default Kubernetes dashboards
* Default Kubernetes alerting rules

Project-specific Helm values will be stored in the repository so the monitoring configuration remains reproducible.

A proposed repository structure is:

```text
kubernetes/
├── applications/
│   └── everpresence-demo/
│       ├── namespace.yaml
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       ├── servicemonitor.yaml
│       └── prometheusrule.yaml
│
└── monitoring/
    ├── namespace.yaml
    ├── kube-prometheus-stack-values.yaml
    ├── dashboards/
    ├── alerts/
    └── README.md
```

### Success Criteria

This phase will be considered complete when:

* All Kubernetes nodes appear healthy in Prometheus.
* Grafana displays cluster and application dashboards.
* The sample application is reachable through Kubernetes.
* Prometheus successfully scrapes application metrics.
* Alert rules transition correctly between pending, firing and resolved states.
* Alertmanager receives and displays active alerts.
* Application and infrastructure failures can be detected and diagnosed from the monitoring stack.
* Deployment and troubleshooting steps are documented in the repository.

### Project Value

This monitoring phase extends the project beyond Kubernetes installation.

It demonstrates practical experience with:

* Kubernetes administration
* Highly available infrastructure
* Application deployment
* Helm
* Prometheus
* Grafana
* Alertmanager
* Kubernetes observability
* Application performance monitoring
* Alert design and incident troubleshooting
* Infrastructure documentation

The result will be a complete platform engineering project that provisions infrastructure, builds a Kubernetes cluster, deploys an application and provides operational monitoring for both the cluster and the workload.

