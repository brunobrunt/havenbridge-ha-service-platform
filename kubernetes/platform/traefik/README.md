# HavenBridge Traefik and Gateway API

## Purpose

This document explains how Traefik, Kubernetes Gateway API, MetalLB, HTTPRoute, TLS, Services, EndpointSlices, and HavenBridge application Pods work together to expose the HavenBridge API.

The goal of this README is not only to document the configuration, but also to serve as a learning and interview-preparation guide.

The HavenBridge ingress architecture provides:

* A stable application IP using MetalLB.
* HTTP and HTTPS entrypoints using Traefik.
* Kubernetes-native routing using Gateway API.
* TLS termination at Traefik.
* HTTP-to-HTTPS redirection.
* Routing from the Gateway to the HavenBridge API Service.
* Load balancing across healthy HavenBridge API Pods.
* High availability using multiple Traefik replicas.
* Pod anti-affinity and a PodDisruptionBudget for Traefik.

The final application URL is:

```text
https://havenbridge.lab
```

The application LoadBalancer IP is:

```text
172.16.10.40
```

---

## What Is Traefik?

Traefik is a reverse proxy and application traffic router.

In the HavenBridge platform, Traefik sits between external clients and Kubernetes application workloads.

Instead of exposing individual application Pods directly to users, external traffic first reaches Traefik.

Traefik then determines where the request should go.

Conceptually:

```text
Client
   ↓
Traefik
   ↓
Routing rules
   ↓
Kubernetes Service
   ↓
Application Pod
```

Traefik therefore provides a controlled entry point into the Kubernetes cluster.

Traefik is not the HavenBridge application itself.

It is infrastructure responsible for receiving and routing application traffic.

---

## Why HavenBridge Uses Traefik

HavenBridge uses Traefik because the platform requires a production-style method of exposing applications from a bare-metal Kubernetes cluster.

The cluster does not run in a cloud provider such as AWS, Azure, or Google Cloud.

Therefore there is no cloud-managed load balancer or application gateway available automatically.

The solution combines several components:

```text
MetalLB
   ↓
Traefik
   ↓
Gateway API
   ↓
HTTPRoute
   ↓
Kubernetes Service
   ↓
Application Pods
```

Each component solves a different problem.

MetalLB provides a reachable LoadBalancer IP.

Traefik receives traffic delivered to that IP.

Gateway API defines the traffic entry points.

HTTPRoute determines which backend receives the request.

The Kubernetes Service provides a stable backend destination.

EndpointSlices identify the currently Ready application Pods.

---

## Where Traefik Fits in the Architecture

The HavenBridge application traffic path is:

```text
Client
   ↓
havenbridge.lab
   ↓
DNS
   ↓
172.16.10.40
   ↓
MetalLB
   ↓
Traefik LoadBalancer Service
   ↓
Traefik entrypoint
   ↓
Gateway listener
   ↓
HTTPRoute
   ↓
havenbridge-api Service
   ↓
EndpointSlice
   ↓
Ready HavenBridge API Pod
   ↓
FastAPI
```

Traefik therefore sits at the boundary between:

```text
External client traffic
```

and:

```text
Internal Kubernetes application routing
```

---

## Traefik Deployment Architecture

Traefik is deployed in the:

```text
traefik
```

namespace.

It is managed using Helm.

The HavenBridge configuration currently runs:

```text
Traefik replicas: 2
```

This avoids having only one Traefik Pod handling application traffic.

The Helm configuration also uses required Pod anti-affinity so the two Traefik replicas should not be scheduled onto the same Kubernetes node.

Conceptually:

```text
eph-worker01
   └── Traefik Pod

eph-worker02
   └── Traefik Pod
```

This improves availability because failure of one worker does not automatically eliminate every Traefik instance.

The Traefik Deployment also has a PodDisruptionBudget configured with:

```text
minAvailable: 1
```

This helps Kubernetes preserve at least one Traefik replica during voluntary disruptions such as node drains.

---

## Traefik Helm Installation

Traefik is managed as a Helm release named:

```text
traefik
```

in the namespace:

```text
traefik
```

The validated chart version is:

```text
41.0.2
```

The deployed Traefik image reported during the Helm upgrade was:

```text
docker.io/traefik:v3.7.6
```

The HavenBridge Helm values are stored in:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/traefik/values.yaml
```

This file is important because it is the source of truth for the Traefik configuration.

The live Gateway contains Helm ownership metadata such as:

```text
app.kubernetes.io/managed-by=Helm
meta.helm.sh/release-name=traefik
```

Because the Gateway is Helm-managed, it should not normally be modified directly with:

```text
kubectl edit gateway
```

A direct manual change could later be overwritten by a Helm upgrade.

The correct workflow is:

```text
Edit values.yaml in Git
        ↓
Helm dry-run
        ↓
Inspect rendered configuration
        ↓
Helm upgrade
        ↓
Validate live Gateway
```

---

## Understanding values.yaml

The Traefik values file controls the major ingress-platform settings.

Important sections include:

```text
deployment
providers
gatewayClass
gateway
service
ports
accessLog
api
podDisruptionBudget
affinity
```

The current architecture enables Kubernetes Gateway API and disables the older Kubernetes Ingress and Traefik CRD routing providers.

Conceptually:

```text
providers.kubernetesGateway.enabled = true

providers.kubernetesIngress.enabled = false

providers.kubernetesCRD.enabled = false
```

This is intentional.

HavenBridge uses:

```text
Gateway
HTTPRoute
```

rather than traditional:

```text
Ingress
```

resources.

---

## Traefik Service and MetalLB

The Traefik Service is configured as:

```text
type: LoadBalancer
```

In a cloud environment, a cloud provider might automatically assign a load balancer IP.

HavenBridge is a bare-metal homelab, so MetalLB performs that role.

Traefik requests the application address:

```text
172.16.10.40
```

using annotations in the Helm values.

The relevant architecture is:

```text
MetalLB address pool
        ↓
172.16.10.40
        ↓
Traefik LoadBalancer Service
```

The configured application pool is:

```text
havenbridge-application-pool
```

The Kubernetes API VIP and application LoadBalancer IP are intentionally separate.

```text
Kubernetes API VIP
172.16.10.30

Application Gateway IP
172.16.10.40
```

This separates cluster-management traffic from application traffic.

---

## Understanding web and websecure

Traefik uses named entrypoints.

HavenBridge currently uses:

```text
web
```

for HTTP and:

```text
websecure
```

for HTTPS.

These names are labels for Traefik network entrypoints.

They are not themselves TCP port numbers.

The full mapping is:

```text
HTTP
80 → web:8000
```

and:

```text
HTTPS
443 → websecure:8443
```

This distinction is important.

Port 80 and port 443 are the external Service ports clients use.

Ports 8000 and 8443 are the internal Traefik container ports.

---

## HTTP Port Mapping

The HTTP path is:

```text
Client
   ↓
TCP/80
   ↓
Traefik LoadBalancer Service
   ↓
Service port 80
   ↓
targetPort: web
   ↓
Traefik entrypoint web
   ↓
containerPort 8000
```

The relevant Helm configuration is conceptually:

```yaml
ports:
  web:
    port: 8000
    exposedPort: 80
```

Therefore:

```text
80
```

is what the client sees.

```text
8000
```

is what Traefik listens on internally.

---

## HTTPS Port Mapping

HTTPS follows the same pattern.

```text
Client
   ↓
TCP/443
   ↓
Traefik LoadBalancer Service
   ↓
Service port 443
   ↓
targetPort: websecure
   ↓
Traefik entrypoint websecure
   ↓
containerPort 8443
```

The corresponding Helm configuration is conceptually:

```yaml
ports:
  websecure:
    port: 8443
    exposedPort: 443
```

Therefore:

```text
443 → websecure:8443
```

is the HavenBridge HTTPS port mapping.

---

## What Is an Entrypoint?

A Traefik entrypoint is a named network listener.

An entrypoint answers the question:

> On which internal network port should Traefik accept this type of traffic?

For HavenBridge:

```text
web
= HTTP entrypoint
= internal port 8000
```

and:

```text
websecure
= HTTPS entrypoint
= internal port 8443
```

The entrypoint is not the same thing as a Gateway listener.

The entrypoint belongs to Traefik.

The Gateway listener belongs to Kubernetes Gateway API.

They work together.

Conceptually:

```text
Traefik entrypoint
        ↓
provides network listener
        ↓
Gateway listener
        ↓
defines Kubernetes routing behavior
```

---

## Gateway API Overview

Kubernetes Gateway API provides standardized resources for configuring application traffic.

HavenBridge primarily uses:

```text
GatewayClass
Gateway
HTTPRoute
```

The relationship is:

```text
GatewayClass
      ↓
Gateway
      ↓
Listener
      ↓
HTTPRoute
      ↓
Service
```

Gateway API separates infrastructure ownership from application routing more clearly than the traditional Ingress model.

---

## GatewayClass

The GatewayClass used by HavenBridge is:

```text
traefik
```

Its controller is:

```text
traefik.io/gateway-controller
```

The GatewayClass tells Kubernetes:

> Gateways using this class should be implemented by the Traefik Gateway controller.

Conceptually:

```text
GatewayClass: traefik
        ↓
Traefik controller
        ↓
implements Gateway resources
```

---

## Gateway

The HavenBridge Gateway is:

```text
Name: havenbridge-gateway
Namespace: traefik
GatewayClass: traefik
```

The Gateway represents the application traffic entry point.

Its current address is:

```text
172.16.10.40
```

The Gateway currently contains two listeners:

```text
web
websecure
```

The Gateway itself has been validated with:

```text
Accepted=True
Programmed=True
```

This means the Gateway controller accepted the configuration and successfully programmed it.

---

## Gateway Listeners

A listener defines which traffic a Gateway accepts.

The HavenBridge Gateway has two.

### HTTP listener

```text
Name: web
Hostname: havenbridge.lab
Protocol: HTTP
Port: 8000
```

### HTTPS listener

```text
Name: websecure
Hostname: havenbridge.lab
Protocol: HTTPS
Port: 8443
TLS Mode: Terminate
Certificate Secret: havenbridge-tls
```

Both listeners permit HTTPRoutes from application namespaces using:

```text
namespacePolicy:
  from: All
```

This is required because the Gateway is in:

```text
traefik
```

while the application HTTPRoutes are in:

```text
havenbridge
```

---

## HTTPRoute

An HTTPRoute tells the Gateway where matching HTTP requests should go.

The primary HavenBridge API route is stored at:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/httproute.yaml
```

It routes:

```text
havenbridge.lab
```

to:

```text
Service: havenbridge-api
Port: 80
```

The backend Service then forwards traffic to the API container port.

The final application route is attached to:

```text
sectionName: websecure
```

This means normal application traffic is served through HTTPS.

A second HTTPRoute handles HTTP redirection.

It is stored at:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/httproute-http-redirect.yaml
```

That route is attached to:

```text
sectionName: web
```

and returns a permanent HTTPS redirect.

---

## How Gateway and HTTPRoute Work Together

The Gateway defines:

> What traffic may enter?

The HTTPRoute defines:

> Where should that traffic go?

For HTTPS:

```text
Gateway listener
websecure
        ↓
accepts HTTPS for havenbridge.lab
        ↓
HTTPRoute
havenbridge-api
        ↓
Service
havenbridge-api:80
```

For HTTP:

```text
Gateway listener
web
        ↓
HTTPRoute
havenbridge-http-redirect
        ↓
301 redirect
        ↓
HTTPS
```

---

## HTTP Request Flow

Plain HTTP is no longer used to serve application traffic directly.

The final HTTP flow is:

```text
http://havenbridge.lab/health/ready
        ↓
DNS resolves havenbridge.lab
        ↓
172.16.10.40
        ↓
TCP/80
        ↓
Traefik LoadBalancer Service
        ↓
web:8000
        ↓
Gateway listener: web
        ↓
havenbridge-http-redirect HTTPRoute
        ↓
301 Moved Permanently
        ↓
Location:
https://havenbridge.lab/health/ready
```

The client is then expected to reconnect using HTTPS.

---

## HTTPS Request Flow

The secure application path is:

```text
https://havenbridge.lab/health/ready
        ↓
DNS
        ↓
172.16.10.40
        ↓
TCP/443
        ↓
Traefik LoadBalancer Service
        ↓
websecure:8443
        ↓
Gateway listener: websecure
        ↓
TLS handshake
        ↓
Traefik presents havenbridge.lab certificate
        ↓
TLS termination
        ↓
havenbridge-api HTTPRoute
        ↓
havenbridge-api Service :80
        ↓
EndpointSlice
        ↓
Ready HavenBridge API Pod :8000
        ↓
FastAPI
        ↓
HTTP/2 200
        ↓
{"status":"ready"}
```

---

## TLS Termination

TLS termination occurs at Traefik.

The Gateway HTTPS listener is configured with:

```text
mode: Terminate
```

and references:

```text
Secret: havenbridge-tls
```

The TLS handshake therefore occurs between:

```text
Client
   ↕ encrypted TLS
Traefik
```

Traefik presents the server certificate and proves possession of its corresponding private key.

After TLS is terminated, Traefik performs internal routing toward the HavenBridge API Service.

The current design therefore uses:

```text
Client → Traefik
HTTPS/TLS encrypted
```

followed by:

```text
Traefik → backend application
internal Kubernetes traffic
```

End-to-end backend TLS may be considered in a future security-hardening phase if required.

---

## HTTP to HTTPS Redirect

HavenBridge permanently redirects HTTP traffic to HTTPS.

The redirect route uses:

```text
RequestRedirect
scheme: https
statusCode: 301
```

The behavior has been validated as:

```text
HTTP/1.1 301 Moved Permanently

Location:
https://havenbridge.lab/health/ready
```

Following that redirect results in:

```text
Final URL:
https://havenbridge.lab/health/ready

HTTP Code:
200

Redirects:
1
```

Therefore:

```text
http://havenbridge.lab
```

is not the final application-serving path.

It exists to guide clients toward:

```text
https://havenbridge.lab
```

API clients should ideally use the HTTPS endpoint directly instead of depending on redirects for write operations.

---

## Complete HavenBridge Request Flow

The complete secure application path is:

```text
Client
        ↓
havenbridge.lab
        ↓
DNS
        ↓
172.16.10.40
        ↓
MetalLB
        ↓
Traefik LoadBalancer Service
        ↓
External :443
        ↓
websecure:8443
        ↓
Gateway HTTPS listener
        ↓
TLS termination
        ↓
havenbridge-tls Secret
        ↓
HTTPRoute
        ↓
havenbridge-api Service :80
        ↓
EndpointSlice
        ↓
Ready API Pod :8000
        ↓
FastAPI
```

The HTTP and HTTPS paths can also be represented as:

```text
HTTP :80
   ↓
web:8000
   ↓
HTTP redirect
   ↓
301 HTTPS redirect


HTTPS :443
   ↓
websecure:8443
   ↓
HTTPRoute
   ↓
havenbridge-api Service
   ↓
API Pods
```

During the HTTPS implementation phase, both listeners temporarily converged on the same application route for validation:

```text
web -----------\
                \
                 > HTTPRoute → Service → API
                /
websecure -----/
```

After HTTPS was proven healthy, the final architecture separated their responsibilities:

```text
web
 ↓
redirect only

websecure
 ↓
application routing
```

---

## Building Analogy

A simple way to remember the architecture is to think of HavenBridge as an office building.

```text
havenbridge.lab
= building name

172.16.10.40
= building street address

MetalLB
= makes the street address reachable

Traefik Service port 80
= normal public front door

Traefik Service port 443
= secure public front door

Traefik web entrypoint :8000
= receptionist's normal internal desk

Traefik websecure entrypoint :8443
= receptionist's secure internal desk

Gateway listener
= receptionist saying:
  "I accept visitors for havenbridge.lab"

HTTPRoute
= directory telling the receptionist:
  "The HavenBridge API is in this department"

havenbridge-api Service
= department's permanent extension

EndpointSlice
= list of employees currently available

API Pod
= employee actually handling the request

FastAPI
= application doing the work
```

For HTTP traffic:

```text
Visitor enters normal door
        ↓
receptionist says:
"For security, please use the secure entrance."
        ↓
301 redirect
```

For HTTPS:

```text
Visitor enters secure door
        ↓
receptionist presents official ID
        ↓
certificate validated
        ↓
directory identifies HavenBridge department
        ↓
available employee handles request
```

---

## Service, EndpointSlice, and Pod Selection

Traefik does not route directly to arbitrary Pod IP addresses defined manually.

The route references:

```text
havenbridge-api Service
```

The Service provides a stable backend abstraction.

Conceptually:

```text
HTTPRoute
   ↓
Service
   ↓
EndpointSlice
   ↓
Ready Pods
```

The HavenBridge API Service listens on:

```text
port 80
```

and maps to the named application target port:

```text
http
```

which corresponds to the FastAPI container port:

```text
8000
```

EndpointSlices contain the current backend endpoints for the Service.

If a Pod is replaced and receives a new Pod IP, the Service and EndpointSlice mechanism updates without requiring the HTTPRoute to change.

This is one of the reasons Services are critical Kubernetes abstractions.

---

## High Availability

Traefik currently runs with:

```text
2 replicas
```

This prevents the application ingress layer from depending on a single Traefik Pod.

Combined with Kubernetes scheduling controls:

```text
2 Traefik Pods
        ↓
separate worker nodes
        ↓
MetalLB Service
        ↓
traffic can continue if one replica fails
```

This does not make the entire platform immune to every failure.

For example, complete loss of the underlying physical host may still affect multiple virtual machines depending on the homelab infrastructure architecture.

However, at the Kubernetes workload level, Traefik is configured to avoid a single-Pod ingress failure.

---

## Pod Anti-Affinity

The Traefik Helm values use required Pod anti-affinity based on:

```text
kubernetes.io/hostname
```

The intention is:

```text
Traefik Pod A
must not share node with
Traefik Pod B
```

when eligible nodes are available.

This reduces the likelihood that one worker-node failure removes every Traefik replica.

---

## PodDisruptionBudget

Traefik has a PodDisruptionBudget configured with:

```text
minAvailable: 1
```

This protects Traefik during voluntary disruptions such as:

```text
kubectl drain
```

The goal is to prevent Kubernetes from voluntarily evicting every Traefik replica at the same time.

A PDB does not prevent hardware failure.

It controls voluntary Kubernetes disruptions.

---

## Security Considerations

Several security measures are present in the Traefik design.

### HTTPS

Application traffic is encrypted between clients and Traefik.

### HTTP redirect

Plain HTTP clients are redirected to HTTPS.

### Private PKI

The HavenBridge TLS certificate is issued by the private HavenBridge Root CA.

### TLS Secret

Traefik references:

```text
havenbridge-tls
```

from the `traefik` namespace.

### Dashboard disabled

The Traefik dashboard is not publicly exposed.

The Helm configuration uses:

```text
dashboard: false
insecure: false
```

### Provider reduction

Only the required Kubernetes Gateway provider is enabled.

Unused routing providers are disabled.

### NetworkPolicy

Application-level NetworkPolicies restrict which traffic can reach the HavenBridge backend.

Traefik is allowed to reach the HavenBridge API container port, while arbitrary Pods are not.

Security therefore exists in layers:

```text
TLS
   ↓
Gateway routing
   ↓
NetworkPolicy
   ↓
Pod security
   ↓
Application controls
```

---

## Failure Scenarios

### Traefik Pod Failure

If one Traefik Pod fails:

```text
Traefik Pod A ❌

Traefik Pod B ✅
```

the surviving replica can continue handling traffic.

### Worker Failure

Pod anti-affinity is intended to place Traefik replicas on different worker nodes.

Failure of one worker should therefore leave another Traefik replica available if the rest of the cluster is healthy.

### MetalLB Failure

If MetalLB cannot advertise:

```text
172.16.10.40
```

clients may not be able to reach the Traefik LoadBalancer Service even if Traefik Pods are healthy.

### Gateway Misconfiguration

A Gateway can exist but fail to become healthy.

Important conditions include:

```text
Accepted
Programmed
ResolvedRefs
```

### HTTPRoute Failure

If the HTTPRoute references:

* the wrong Gateway,
* the wrong listener,
* the wrong Service,
* or the wrong Service port,

traffic may fail even when Traefik itself is healthy.

### Missing TLS Secret

If the HTTPS listener references a missing or invalid TLS Secret, the listener may fail:

```text
ResolvedRefs=False
```

or fail to serve the expected certificate.

### DNS Failure

If:

```text
havenbridge.lab
```

does not resolve to:

```text
172.16.10.40
```

clients will not reach the correct application gateway.

---

## Troubleshooting

Troubleshooting should follow the traffic path instead of randomly checking components.

Recommended order:

```text
DNS
 ↓
MetalLB IP
 ↓
Traefik Service
 ↓
Traefik Pods
 ↓
Gateway
 ↓
Listener
 ↓
HTTPRoute
 ↓
Service
 ↓
EndpointSlice
 ↓
API Pod
 ↓
FastAPI
```

### Verify DNS

```bash
getent hosts havenbridge.lab
```

Expected:

```text
172.16.10.40
```

### Verify Traefik Service

```bash
kubectl get service traefik \
  --namespace traefik \
  --output wide
```

### Verify Traefik Pods

```bash
kubectl get pods \
  --namespace traefik \
  --output wide
```

### Verify Gateway

```bash
kubectl get gateway havenbridge-gateway \
  --namespace traefik
```

### Inspect Gateway status

```bash
kubectl describe gateway havenbridge-gateway \
  --namespace traefik
```

### Show only listener attachment counts

```bash
kubectl get gateway havenbridge-gateway \
  --namespace traefik \
  --output jsonpath='{range .status.listeners[*]}{.name}{"\tAttached Routes: "}{.attachedRoutes}{"\n"}{end}'
```

Expected:

```text
web        Attached Routes: 1
websecure  Attached Routes: 1
```

### Inspect HTTPRoutes

```bash
kubectl get httproute \
  --namespace havenbridge
```

### Inspect API Service

```bash
kubectl get service havenbridge-api \
  --namespace havenbridge
```

### Inspect EndpointSlices

```bash
kubectl get endpointslice \
  --namespace havenbridge
```

### Validate HTTP redirect

```bash
curl -s -o /dev/null -D - \
  http://havenbridge.lab/health/ready \
  | grep -Ei '^(HTTP/|Location:)'
```

Expected:

```text
HTTP/1.1 301 Moved Permanently
Location: https://havenbridge.lab/health/ready
```

### Validate HTTPS

```bash
curl -i https://havenbridge.lab/health/ready
```

Expected:

```text
HTTP/2 200
{"status":"ready"}
```

---

## Validation Commands

### Traefik port mapping

```bash
kubectl get service traefik \
  --namespace traefik \
  --output jsonpath='{range .spec.ports[*]}{.name}{"\tservicePort="}{.port}{"\ttargetPort="}{.targetPort}{"\n"}{end}'
```

Expected:

```text
web        servicePort=80    targetPort=web
websecure  servicePort=443   targetPort=websecure
```

### Traefik container ports

```bash
kubectl get deployment traefik \
  --namespace traefik \
  --output jsonpath='{range .spec.template.spec.containers[0].ports[*]}{.name}{"\tcontainerPort="}{.containerPort}{"\n"}{end}'
```

Expected:

```text
web        containerPort=8000
websecure  containerPort=8443
```

### Gateway conditions

```bash
kubectl describe gateway havenbridge-gateway \
  --namespace traefik
```

Expected:

```text
Accepted=True
Programmed=True
```

Both listeners should also report healthy conditions.

---

## Operational Commands

### View Helm release

```bash
helm list \
  --namespace traefik
```

### View installed values

```bash
helm get values traefik \
  --namespace traefik
```

### View Helm release status

```bash
helm status traefik \
  --namespace traefik
```

### View Traefik logs

```bash
kubectl logs \
  --namespace traefik \
  deployment/traefik
```

### Check Gateway API resources

```bash
kubectl get gatewayclass
kubectl get gateway -A
kubectl get httproute -A
```

---

## Current Limitations

### Private CA trust

The certificate for:

```text
havenbridge.lab
```

is issued by a private HavenBridge CA.

Clients must explicitly trust the HavenBridge Root CA.

This is suitable for a private homelab but differs from a public production application where a publicly trusted CA such as Let's Encrypt or an enterprise PKI may be used.

### Backend traffic

TLS currently terminates at Traefik.

Traffic from Traefik toward the backend API is not currently configured as TLS-encrypted application traffic.

### Physical failure domain

The Kubernetes control plane and worker VMs depend on the underlying homelab physical infrastructure.

Kubernetes workload redundancy cannot protect against every failure of the physical host.

### Gateway API CRD lifecycle

During the Traefik Helm upgrade, the chart emitted a deprecation warning indicating that Gateway API CRDs will no longer be shipped automatically with a future major chart version.

Therefore Gateway API CRDs should eventually have an independent installation and upgrade lifecycle rather than relying on the Traefik chart.

This should be addressed before a future major Traefik upgrade.

---

## Interview Talking Points

### Explain why Traefik was used

A strong answer:

> I used Traefik as the Kubernetes application gateway and reverse proxy. Because the cluster is bare-metal, MetalLB provides the external LoadBalancer IP while Traefik receives HTTP and HTTPS traffic. Kubernetes Gateway API resources then define how traffic is routed to the HavenBridge backend.

### Explain the difference between MetalLB and Traefik

> MetalLB makes a LoadBalancer IP reachable on the bare-metal network. Traefik accepts application traffic on that IP and performs Layer 7 routing. MetalLB provides reachability; Traefik provides application routing.

### Explain Gateway vs HTTPRoute

> The Gateway defines the traffic entry points, such as the HTTP and HTTPS listeners. HTTPRoute defines how matching requests are routed from those listeners to application Services.

### Explain web vs websecure

> `web` is the Traefik HTTP entrypoint on internal port 8000 and is exposed externally as port 80. `websecure` is the HTTPS entrypoint on internal port 8443 and is exposed externally as port 443.

### Explain TLS termination

> TLS terminates at Traefik. The client establishes an encrypted connection to Traefik, Traefik presents the HavenBridge server certificate, decrypts the request, and then routes it to the backend Service.

### Explain the request path

> A client resolves `havenbridge.lab` to `172.16.10.40`. MetalLB makes that LoadBalancer IP reachable. The request reaches the Traefik Service, then the appropriate Gateway listener. The HTTPRoute chooses the HavenBridge API Service, the Service uses its EndpointSlice to select a Ready backend Pod, and the FastAPI application handles the request.

### Explain the HTTP-to-HTTPS redirect

> The HTTP listener does not serve the application directly. It has its own HTTPRoute that returns a permanent 301 redirect to HTTPS. The HTTPS listener then performs TLS termination and routes traffic to the API.

### Explain the availability design

> Traefik runs with two replicas, required Pod anti-affinity across Kubernetes hostnames, and a PodDisruptionBudget with `minAvailable: 1`. This reduces the risk that a single Pod or voluntary node disruption removes the ingress layer.

---

## Related Files

### Traefik Helm configuration

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/traefik/values.yaml
```

### Traefik documentation

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/traefik/README.md
```

### TLS manifests

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/tls/selfsigned-clusterissuer.yaml

/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/tls/havenbridge-root-ca-certificate.yaml

/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/tls/havenbridge-ca-clusterissuer.yaml

/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/tls/havenbridge-certificate.yaml
```

### TLS documentation

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/tls/README.md
```

### Backend HTTPS route

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/httproute.yaml
```

### HTTP-to-HTTPS redirect route

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/httproute-http-redirect.yaml
```

### Backend documentation

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/README.md
```

### TLS validation evidence

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/evidence/tls-validation/
```

### Platform documentation

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/README.md
```

### Project documentation

```text
/home/alabi/projects/havenbridge-ha-service-platform/README.md
```
