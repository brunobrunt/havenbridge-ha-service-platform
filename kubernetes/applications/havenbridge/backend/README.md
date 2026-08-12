# HavenBridge Backend Kubernetes Deployment

This directory contains the Kubernetes manifests used to deploy the
HavenBridge FastAPI backend.

## Backend Components

```text
configmap.yaml
deployment.yaml
service.yaml
httproute.yaml
```

## Application ConfigMap

The backend uses the following ConfigMap:

```text
havenbridge-api-config
```

Manifest:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/configmap.yaml
```

The ConfigMap stores non-sensitive application and PostgreSQL connection
settings.

Configured database connection:

```text
POSTGRES_HOST=havenbridge-postgres
POSTGRES_PORT=5432
POSTGRES_DB=havenbridge
POSTGRES_USER=havenbridge_admin
POSTGRES_PASSWORD_FILE=/run/secrets/postgres-password
```

The PostgreSQL password is not stored in the ConfigMap. It remains in the
existing Kubernetes Secret:

```text
Secret: havenbridge-postgres-secret
Key: POSTGRES_PASSWORD
```

The password will be mounted into the API Pod as a read-only file at:

```text
/run/secrets/postgres-password
```

## ConfigMap Validation

The manifest was validated against the Kubernetes API before being applied:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl apply \
    --dry-run=server \
    --filename=-' \
  < /home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/configmap.yaml
```

Validated result:

```text
configmap/havenbridge-api-config created (server dry run)
```

Apply the ConfigMap:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl apply \
    --filename=-' \
  < /home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/configmap.yaml
```

Verify it:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get configmap \
    havenbridge-api-config \
    --namespace havenbridge'
```
### ConfigMap Deployment Status

The ConfigMap was successfully created in the `havenbridge` namespace:

```text
configmap/havenbridge-api-config created


### 🚀 HavenBridge API Deployment

### Why Topology Spread Constraints Are Used

`topologySpreadConstraints` prevents both HavenBridge API replicas from being scheduled on the same worker node.

It tells Kubernetes to spread matching API Pods evenly across nodes identified by:

```yaml
topologyKey: kubernetes.io/hostname
```

This improves availability because if one worker node fails, the API replica on the other worker can continue serving traffic.

```text
API replica 1 → eph-worker01
API replica 2 → eph-worker02
```

`maxSkew: 1` allows a maximum difference of one matching Pod between nodes, while `DoNotSchedule` prevents Kubernetes from placing a Pod when the required distribution cannot be maintained.



The HavenBridge FastAPI backend is deployed using:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/deployment.yaml
```

The Deployment runs the following image:

```text
ghcr.io/brunobrunt/havenbridge-api:0.1.0
```

The initial deployment uses one replica while application startup, database
connectivity, Secret mounting, security controls and health probes are
validated.

### Deployment Validation

The manifest was first validated as YAML:

```bash
python3 -c '
import yaml
path = "/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/deployment.yaml"
with open(path, encoding="utf-8") as file:
    yaml.safe_load(file)
print("deployment.yaml is valid YAML")
'
```

Validated result:

```text
deployment.yaml is valid YAML
```

The manifest was then validated against the Kubernetes API:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl apply \
    --dry-run=server \
    --filename=-' \
  < /home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/deployment.yaml
```

Validated result:

```text
deployment.apps/havenbridge-api created (server dry run)
```

### Apply the Deployment

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl apply \
    --filename=-' \
  < /home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/deployment.yaml
```

### Runtime Security

The API Pod uses a restricted security configuration:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 100
  runAsGroup: 101
  seccompProfile:
    type: RuntimeDefault
```

The container also uses:

```yaml
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: true
```

The image runs as:

```text
uid=100(havenbridge)
gid=101(havenbridge)
```

### PostgreSQL Password Mount

The PostgreSQL password remains in the existing Kubernetes Secret:

```text
Secret: havenbridge-postgres-secret
Key: POSTGRES_PASSWORD
```

The Secret key is mounted as a read-only file inside the API container:

```text
/run/secrets/postgres-password
```

The application reads the password using:

```text
POSTGRES_PASSWORD_FILE=/run/secrets/postgres-password
```

This prevents the database password from being placed directly in the
ConfigMap or Deployment environment variables.


#### Topology Spread Configuration

The HavenBridge API uses topology spread constraints to prefer distributing API replicas across different worker nodes.

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        app.kubernetes.io/name: havenbridge-api
```

##### `DoNotSchedule` versus `ScheduleAnyway`

`DoNotSchedule` is a strict rule. Kubernetes leaves a Pod in `Pending` state when it cannot satisfy the requested Pod distribution.

`ScheduleAnyway` is a preference. Kubernetes tries to spread the Pods evenly but still schedules a Pod when perfect distribution is temporarily impossible.

| Setting          | Behaviour                                                   |
| ---------------- | ----------------------------------------------------------- |
| `DoNotSchedule`  | Blocks scheduling when the spread rule cannot be satisfied  |
| `ScheduleAnyway` | Prefers even spreading but allows scheduling when necessary |

HavenBridge originally used `DoNotSchedule`, but it blocked the temporary extra Pod created during a rolling update. The configuration was changed to `ScheduleAnyway` so Kubernetes can complete rolling updates while still preferring one API replica on each worker node.



## Deployment Troubleshooting

### Named User and `runAsNonRoot`

The first Pod failed with:

```text
CreateContainerConfigError
```

The Pod event reported:

```text
container has runAsNonRoot and image has non-numeric user (havenbridge),
cannot verify user is non-root
```

Although the image user was non-root, Kubernetes could not verify the named
user from the image metadata.

The issue was corrected by explicitly defining the verified UID and GID:

```yaml
runAsUser: 100
runAsGroup: 101
```

Troubleshooting flow:

```text
Image declares USER havenbridge
        ↓
Kubernetes cannot verify the named user is non-root
        ↓
Pod enters CreateContainerConfigError
        ↓
Explicit UID 100 and GID 101 added
        ↓
Container starts successfully
```

### Incorrect Health Probe Path

The container started successfully but remained unready and eventually entered
`CrashLoopBackOff`.

The logs showed:

```text
GET /health HTTP/1.1" 404 Not Found
```

The application does not provide a health endpoint at `/health`. It provides
separate liveness and readiness endpoints.

The probes were corrected to:

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: http

livenessProbe:
  httpGet:
    path: /health/live
    port: http
```

The readiness endpoint verifies that the API is ready to receive traffic,
including its PostgreSQL connectivity.

The liveness endpoint verifies that the FastAPI process is still functioning.

Troubleshooting flow:

```text
Kubernetes probes /health
        ↓
FastAPI returns 404
        ↓
Readiness remains false
        ↓
Liveness probe fails
        ↓
Kubernetes restarts the container
        ↓
Probe paths corrected
        ↓
Both endpoints return 200 OK
```

## Successful Validation

Deployment status:

```text
NAME              READY   UP-TO-DATE   AVAILABLE
havenbridge-api   1/1     1            1
```

Application startup logs:

```text
Starting HavenBridge API in production mode.
Creating missing HavenBridge database tables.
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

Successful health checks:

```text
GET /health/ready HTTP/1.1" 200 OK
GET /health/live HTTP/1.1" 200 OK
```

This confirms:

* The GHCR image was pulled successfully through CRI-O.
* The container runs as a non-root user.
* The PostgreSQL Secret is mounted successfully.
* The API connects to PostgreSQL.
* The application starts in production mode.
* The readiness probe succeeds.
* The liveness probe succeeds.
* The Deployment has one available replica.


## HavenBridge API Service

The HavenBridge API is exposed internally through a Kubernetes `ClusterIP`
Service.

Service manifest:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/service.yaml
```

The Service configuration is:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: havenbridge-api
  namespace: havenbridge
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: havenbridge-api
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: http
```

The Service listens on port `80` and forwards traffic to the named `http`
container port defined in the Deployment:

```yaml
ports:
  - name: http
    containerPort: 8000
    protocol: TCP
```

Traffic flow:

```text
Service port 80
      ↓
targetPort http
      ↓
Container port named http
      ↓
Container port 8000
```

### Service Selector

The Service selects Pods using:

```yaml
selector:
  app.kubernetes.io/name: havenbridge-api
```

This selector matches the Pod label defined under the Deployment's Pod
template:

```yaml
spec:
  template:
    metadata:
      labels:
        app.kubernetes.io/name: havenbridge-api
```

A Service selects Pods rather than selecting the Deployment object directly.

### Manifest Validation

The Service manifest was validated against the Kubernetes API before it was
applied:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl apply \
    --dry-run=server \
    --filename=-' \
  < /home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/service.yaml
```

Validated result:

```text
service/havenbridge-api created (server dry run)
```

### EndpointSlice Validation

The Service EndpointSlice was inspected using:

```bash
kubectl get endpointslice \
  --namespace havenbridge \
  --selector kubernetes.io/service-name=havenbridge-api \
  --output wide
```

Validated result:

```text
NAME                    ADDRESSTYPE   PORTS   ENDPOINTS
havenbridge-api-b97n6   IPv4          8000    10.244.176.217
```

The EndpointSlice address matched the healthy API Pod:

```text
Pod IP:    10.244.176.217
Node:      eph-worker02
Status:    Running
Ready:     1/1
Restarts:  0
```

This confirms that the Service selector successfully discovered the API Pod.

### Internal DNS Validation

The Service was tested using its complete Kubernetes DNS name:

```text
havenbridge-api.havenbridge.svc.cluster.local
```

The test was executed from inside the API Pod:

```bash
kubectl exec \
  deployment/havenbridge-api \
  --namespace havenbridge \
  -- python -c '
import urllib.request

url = "http://havenbridge-api.havenbridge.svc.cluster.local/health/ready"

with urllib.request.urlopen(url, timeout=5) as response:
    print("Status:", response.status)
    print("Body:", response.read().decode())
'
```

Validated result:

```text
Status: 200
Body: {"status":"ready"}
```

This confirms:

* Kubernetes DNS resolved the Service name.
* The Service accepted traffic on port `80`.
* The EndpointSlice forwarded traffic to the API Pod on port `8000`.
* The API readiness endpoint returned HTTP `200`.

### Port-Forward Validation

The ClusterIP Service was also tested temporarily through a local port-forward:

```bash
kubectl port-forward \
  service/havenbridge-api \
  --namespace havenbridge \
  8080:80
```

Traffic flow:

```text
127.0.0.1:8080
      ↓
HavenBridge API Service port 80
      ↓
API Pod port 8000
```

Readiness test:

```bash
curl -i http://127.0.0.1:8080/health/ready
```

Validated result:

```text
HTTP/1.1 200 OK
server: uvicorn
content-type: application/json

{"status":"ready"}
```

Liveness test:

```bash
curl -i http://127.0.0.1:8080/health/live
```

Validated result:

```text
HTTP/1.1 200 OK
server: uvicorn
content-type: application/json
```

The port-forward is temporary and does not permanently expose the Service
outside the Kubernetes cluster. Press `Ctrl+C` in the port-forward terminal
after testing is complete.

## Successful Service Validation

The completed checks confirm:

* The `ClusterIP` Service was created successfully.
* The Service selector matches the API Pod labels.
* An EndpointSlice was created automatically.
* The EndpointSlice contains the correct Pod IP and port.
* Kubernetes internal DNS resolves the Service.
* Readiness requests return HTTP `200`.
* Liveness requests return HTTP `200`.
* Traffic reaches the FastAPI application through Service port `80`.


## Why HavenBridge Uses MetalLB and Traefik

The HavenBridge Kubernetes cluster runs on virtual machines in a home lab. It
does not run in a public cloud such as AWS, Azure or Google Cloud.

In a public cloud, creating a Kubernetes Service with:

```yaml
type: LoadBalancer
```

normally causes the cloud provider to create an external load balancer and
assign an IP address automatically.

A bare-metal or home-lab Kubernetes cluster does not have a cloud provider
available to perform that task. This is why HavenBridge uses MetalLB.

### What MetalLB Does

MetalLB provides external IP addresses for Kubernetes `LoadBalancer` Services
in a bare-metal environment.

For HavenBridge, MetalLB assigned:

```text
172.16.10.40
```

to the Traefik entry point.

This address is reachable from the home-lab network and becomes the external
application address for HavenBridge.

MetalLB’s responsibility is therefore:

```text
Provide a reachable network IP
        ↓
Assign it to a LoadBalancer Service
        ↓
Advertise that IP on the local network
```

MetalLB answers the question:

```text
Which IP address should clients connect to?
```

Without MetalLB, the Traefik Service could remain without an external IP, or
the project would need to rely on less convenient alternatives such as
`NodePort`.

### Why Not Use Only NodePort?

A `NodePort` Service exposes an application using a high port on every
Kubernetes node, for example:

```text
172.16.10.34:31234
```

That approach would require clients to know a worker node IP and an unusual
port number.

MetalLB gives the platform a cleaner address:

```text
172.16.10.40
```

This behaves more like a production load balancer and makes the home-lab
architecture easier to understand and present.

### What Traefik Does

Traefik is the application traffic controller and reverse proxy.

After a request reaches `172.16.10.40`, Traefik examines the request and
determines which Kubernetes Service should receive it.

Traefik can route traffic using information such as:

```text
Hostname
URL path
HTTP protocol
Gateway listener
HTTPRoute rules
```

For example:

```text
http://havenbridge.lab
```

can be routed to:

```text
havenbridge-api Service
```

Traefik answers the question:

```text
Which application should receive this request?
```

### MetalLB and Traefik Have Different Jobs

MetalLB and Traefik are not replacements for each other.

MetalLB operates mainly at the network-address level:

```text
External client
      ↓
172.16.10.40
```

Traefik operates at the HTTP-routing level:

```text
Request for havenbridge.lab
      ↓
Match an HTTPRoute
      ↓
Forward to havenbridge-api Service
```

A simple comparison is:

| Component          | Main responsibility                               |
| ------------------ | ------------------------------------------------- |
| MetalLB            | Provides the externally reachable IP address      |
| Traefik            | Receives and routes HTTP or HTTPS traffic         |
| Gateway API        | Defines the routing configuration Traefik follows |
| Kubernetes Service | Sends traffic to the selected application Pods    |

### What MetalLB Does Not Do

MetalLB does not inspect URLs or route requests based on hostnames.

It does not decide that:

```text
havenbridge.lab
```

should go to the HavenBridge API.

Its main job is to provide and advertise the IP address.

### What Traefik Does Not Do

Traefik does not independently provide a bare-metal external IP address.

It needs a network mechanism that makes its Service reachable outside the
cluster. In HavenBridge, MetalLB provides that mechanism.

### HavenBridge Traffic Flow

The planned external traffic path is:

```text
Client
  ↓
DNS resolves havenbridge.lab
  ↓
172.16.10.40
  ↓
MetalLB-provided LoadBalancer address
  ↓
Traefik Gateway
  ↓
HavenBridge HTTPRoute
  ↓
havenbridge-api ClusterIP Service on port 80
  ↓
EndpointSlice
  ↓
HavenBridge API Pod on port 8000
```

In simple terms:

```text
MetalLB gets traffic into the cluster.
Traefik sends that traffic to the correct application.
```

### GatewayClass Validation

The Traefik GatewayClass was validated with:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get gatewayclass \
    --output wide'
```

Validated result:

```text
NAME      CONTROLLER                      ACCEPTED
traefik   traefik.io/gateway-controller   True
```

This confirms that Traefik is registered as the controller responsible for
processing Gateway API resources that use the `traefik` GatewayClass.

### Gateway Validation

The HavenBridge Gateway was validated with:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl get gateway \
    --all-namespaces \
    --output wide'
```

Validated result:

```text
NAMESPACE   NAME                  CLASS     ADDRESS        PROGRAMMED
traefik     havenbridge-gateway   traefik   172.16.10.40   True
```

The result confirms:

* The Gateway is named `havenbridge-gateway`.
* The Gateway is located in the `traefik` namespace.
* It uses the `traefik` GatewayClass.
* It has the MetalLB-provided address `172.16.10.40`.
* Its configuration has been successfully programmed by Traefik.

The `PROGRAMMED=True` condition means the Traefik controller has accepted and
processed the Gateway configuration.

### Interview Explanation

A concise explanation of the design is:

> HavenBridge runs on a bare-metal Kubernetes home lab, so there is no cloud
> provider to allocate external LoadBalancer addresses. MetalLB fills that gap
> by assigning the application gateway IP `172.16.10.40`. Traefik receives
> traffic on that address and uses Kubernetes Gateway API resources to route
> requests to the correct internal Service. MetalLB provides network
> reachability, while Traefik provides application-level routing.


* **MetalLB:** Provides an external IP address for the Traefik `LoadBalancer` Service in the bare-metal Kubernetes environment.
* **Traefik:** Receives traffic on that external IP and routes it to the correct Kubernetes Service using Gateway API rules.


## HTTPRoute

The `HTTPRoute` defines how external HTTP requests received by the Traefik
Gateway are forwarded to the HavenBridge API Service.

Without an `HTTPRoute`, the Gateway can receive traffic on the MetalLB address
`172.16.10.40`, but Traefik has no rule telling it which Kubernetes Service
should receive requests for `havenbridge.lab`.

The route connects:

```text
havenbridge.lab
        ↓
Traefik Gateway
        ↓
HTTPRoute
        ↓
havenbridge-api Service
        ↓
HavenBridge API Pod
```

In simple terms, the Gateway receives the traffic, while the `HTTPRoute` tells
Traefik where to send it.

## External HTTPRoute Validation

The HavenBridge API `HTTPRoute` was successfully attached to the Traefik
Gateway.

Validated route conditions:

```text
Accepted=True
ResolvedRefs=True
attachedRoutes=1
```

These conditions confirm that:

* Traefik accepted the `HTTPRoute`.
* The referenced `havenbridge-api` Service exists.
* The route is attached to the `web` Gateway listener.

The external API endpoint was tested from Syrus:

```bash
curl -v \
  --connect-timeout 5 \
  http://havenbridge.lab/health/ready
```

Validated response:

```text
HTTP/1.1 200 OK
Content-Type: application/json
Server: uvicorn

{"status":"ready"}
```

DNS validation:

```bash
getent hosts havenbridge.lab
```

Validated result:

```text
172.16.10.40    havenbridge.lab
```

Routing validation:

```bash
ip route get 172.16.10.40
```

Validated result:

```text
172.16.10.40 dev virbr0 src 172.16.10.1
```

The successful external traffic path is:

```text
Syrus
  ↓
havenbridge.lab
  ↓
MetalLB address 172.16.10.40
  ↓
Traefik LoadBalancer Service port 80
  ↓
Traefik Gateway web listener
  ↓
HavenBridge API HTTPRoute
  ↓
havenbridge-api ClusterIP Service port 80
  ↓
EndpointSlice
  ↓
HavenBridge API Pod port 8000
```

The Gateway listener internally uses port `8000`, but external clients connect
to port `80` because the Traefik `LoadBalancer` Service exposes port `80`.

Therefore, the correct external URL is:

```text
http://havenbridge.lab/health/ready
```

and not:

```text
http://havenbridge.lab:8000/health/ready
```


### The successful response confirms the complete production traffic path is still working:

havenbridge.lab
    ↓
MetalLB IP 172.16.10.40
    ↓
Traefik
    ↓
HTTPRoute
    ↓
havenbridge-api Service
    ↓
HavenBridge API Pod
    ↓
HTTP 200 {"status":"ready"}

### Validation Namespace Cleanup

The temporary `platform-validation` namespace and its Nginx resources were removed after the real HavenBridge API route was validated.

After cleanup, the external readiness endpoint was tested again:

```bash
curl -iv http://havenbridge.lab/health/ready
```

Validated result:

```text
HTTP/1.1 200 OK
Server: uvicorn

{"status":"ready"}
```

This confirms that deleting the temporary validation resources did not affect the HavenBridge API, Traefik Gateway, HTTPRoute, MetalLB address, or internal Kubernetes Service.


#### Replica Placement and Rolling-Update Strategy

The HavenBridge API runs two replicas, with one replica placed on each worker node:

```text
havenbridge-api replica 1 → eph-worker01
havenbridge-api replica 2 → eph-worker02
```

This improves application availability because the API can continue running if one worker node becomes unavailable.

The Deployment uses:

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app.kubernetes.io/name: havenbridge-api
```

`DoNotSchedule` enforces the distribution rule and prevents Kubernetes from placing both API replicas on the same worker node.

The rolling-update strategy is:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 0
```

`maxSurge: 0` prevents Kubernetes from creating a temporary third API Pod during an update.

This is necessary because the HavenBridge cluster currently has only two eligible worker nodes. A temporary third Pod cannot satisfy the strict topology spread requirement.

`maxUnavailable: 1` allows Kubernetes to remove one old replica before creating its replacement.

The update flow is:

```text
Two existing API replicas
        ↓
One old replica is removed
        ↓
A replacement replica is scheduled on the available worker
        ↓
The second replica is replaced
        ↓
Final state returns to one replica per worker
```

This configuration was chosen because the previous combination caused a rollout failure:

```yaml
maxUnavailable: 0
maxSurge: 1
whenUnsatisfiable: DoNotSchedule
```

That configuration attempted to create a temporary third Pod, but the scheduler could not place it while maintaining the strict node distribution.

The corrected configuration trades temporary reduced capacity during an update for guaranteed final placement across both worker nodes.

The updated manifest was validated using:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl apply --dry-run=server --filename=-' \
  < /home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/deployment.yaml
```

Validated result:

```text
deployment.apps/havenbridge-api configured (server dry run)
```

The Deployment was then applied:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl apply --filename=-' \
  < /home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/deployment.yaml
```

Validated result:

```text
deployment.apps/havenbridge-api configured
```

Final Pod placement:

```text
NAME                               READY   STATUS    NODE
havenbridge-api-554c86f6d5-6rkkt   1/1     Running   eph-worker01
havenbridge-api-554c86f6d5-cdhd5   1/1     Running   eph-worker02
```

This confirms:
* Two API replicas are running.
* Both replicas are Ready.
* The replicas are distributed across separate worker nodes.
* Strict topology spreading is working.
* The rolling-update configuration no longer creates an unschedulable third Pod.

#### API Pod Failure and Self-Healing Validation

A controlled Pod-failure test was performed to confirm that the HavenBridge API remains available when one replica is deleted.

The API initially had two healthy replicas:

```text
eph-worker01 → 10.244.35.108
eph-worker02 → 10.244.176.224
```

The API Pod running on `eph-worker01` was manually deleted.

Because the Pods are managed by a Kubernetes Deployment with `replicas: 2`,
Kubernetes detected that the actual number of replicas was lower than the
desired number and automatically created a replacement.

Recovered state:

```text
eph-worker01 → 10.244.35.109
eph-worker02 → 10.244.176.224
```

The Pod IP on `eph-worker01` changed because the replacement was a new Pod.

The Service EndpointSlice was also updated automatically:

```text
Before deletion:
10.244.35.108,10.244.176.224

After recovery:
10.244.35.109,10.244.176.224
```

This demonstrates Kubernetes self-healing:

```text
One API Pod is deleted
        ↓
The Deployment detects only one running replica
        ↓
The Service continues using the remaining ready endpoint
        ↓
Kubernetes schedules a replacement Pod
        ↓
The readiness probe succeeds
        ↓
The new Pod is added to the EndpointSlice
        ↓
Two healthy replicas are restored
```

The validation confirmed:

* The remaining API replica continued running during the failure.
* Kubernetes automatically created a replacement Pod.
* The replacement was scheduled on the correct worker node.
* The readiness probe prevented traffic from reaching the replacement before it was ready.
* The EndpointSlice removed the deleted Pod IP.
* The EndpointSlice added the replacement Pod IP.
* The desired state of two ready replicas was restored.

Evidence was saved under:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/pod-failure-validation/
```

Evidence files:

```text
before-pod-deletion.txt
readiness-during-pod-deletion.txt
curl-errors.txt
after-pod-deletion.txt
```


#### PodDisruptionBudget

A PodDisruptionBudget, or PDB, is a Kubernetes policy that limits how many replicas of an application may be voluntarily removed at the same time.

The HavenBridge API uses a `PodDisruptionBudget` to protect application
availability during planned Kubernetes disruptions such as node draining,
maintenance and cluster upgrades.

Manifest:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/pdb.yaml
```

The disruption policy is:

```yaml
spec:
  maxUnavailable: 1
  unhealthyPodEvictionPolicy: AlwaysAllow
  selector:
    matchLabels:
      app.kubernetes.io/name: havenbridge-api
```

`maxUnavailable: 1` means Kubernetes may voluntarily disrupt only one
HavenBridge API replica at a time.

With two replicas, the expected behaviour is:

```text
Two healthy API replicas
        ↓
One voluntary eviction is requested
        ↓
The PodDisruptionBudget allows the eviction
        ↓
At least one healthy API replica remains available
```

The selector matches the HavenBridge API Deployment selector, ensuring that the
budget protects the correct application Pods.

`unhealthyPodEvictionPolicy: AlwaysAllow` permits an unhealthy or permanently
unready Pod to be removed during node maintenance instead of allowing it to
block the drain operation. Healthy Pods remain protected by the disruption
budget.

A PodDisruptionBudget protects against voluntary API-managed evictions. It does
not prevent sudden node failure, hardware failure, application crashes or
direct Pod deletion.

The earlier manual Pod deletion test validated Deployment self-healing and
Service failover. The PodDisruptionBudget will be validated separately using a
controlled `kubectl drain` operation.


##### Cordon, Drain and Uncordon

- **Cordon:** Marks a node as unschedulable, so Kubernetes stops placing new Pods on it. Existing Pods keep running.
- **Drain:** Cordons the node and then evicts eligible existing Pods for maintenance.
- **Uncordon:** Makes the node schedulable again so Kubernetes can place Pods on it.

##### Continuous Availability Test

External readiness requests were sent every second while an API Pod was disrupted:

```bash
EVIDENCE_DIR="/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/pdb-drain-validation"

while true; do
  NOW=$(date '+%Y-%m-%d %H:%M:%S')

  STATUS=$(curl \
    --silent \
    --show-error \
    --output /dev/null \
    --write-out '%{http_code}' \
    --connect-timeout 2 \
    --max-time 3 \
    http://havenbridge.lab/health/ready \
    2>> "$EVIDENCE_DIR/curl-errors.txt" || true)

  printf '%s HTTP %s\n' \
    "$NOW" \
    "${STATUS:-000}"

  sleep 1
done | tee \
  "$EVIDENCE_DIR/readiness-during-drain.txt"
```

This loop records the HTTP status returned by the external readiness endpoint every second.

Validated output:

```text
2026-08-04 10:31:53 HTTP 200
2026-08-04 10:31:54 HTTP 200
2026-08-04 10:31:55 HTTP 200
```

Continuous HTTP `200` responses confirm that the HavenBridge API remained reachable through the remaining healthy replica while Kubernetes handled the disruption.

The results are stored in:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/pdb-drain-validation/readiness-during-drain.txt
```

Any connection errors are stored in:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/pdb-drain-validation/curl-errors.txt
```



##### PodDisruptionBudget Drain Test Results

A controlled maintenance test was performed on `eph-worker01` to validate the
HavenBridge API PodDisruptionBudget.

Before the drain, the application had two healthy replicas:

```text
eph-worker01 → 10.244.35.109
eph-worker02 → 10.244.176.224
```

The PodDisruptionBudget reported:

```text
MAX UNAVAILABLE:      1
ALLOWED DISRUPTIONS:  1
```

This meant Kubernetes was permitted to voluntarily evict one API replica while
requiring at least one healthy replica to remain available.

The targeted drain used:

```bash
kubectl drain eph-worker01 \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --pod-selector=app.kubernetes.io/name=havenbridge-api \
  --grace-period=30 \
  --timeout=180s
```

The `--pod-selector` option limited the test to HavenBridge API Pods and
prevented unrelated workloads from being intentionally evicted during this
validation.

The drain performed the following actions:

```text
eph-worker01 was cordoned
        ↓
The HavenBridge API Pod on eph-worker01 was evicted
        ↓
The API replica on eph-worker02 remained Ready
        ↓
The Deployment created a replacement Pod
        ↓
The replacement remained Pending while eph-worker01 was cordoned
```

During the drain, the cluster state was:

```text
eph-worker01: Ready,SchedulingDisabled

Running API replica:
eph-worker02 → 10.244.176.224

Replacement API replica:
Pending
```

The Service EndpointSlice temporarily contained only the remaining healthy
endpoint:

```text
10.244.176.224:8000
```

The PodDisruptionBudget changed to:

```text
ALLOWED DISRUPTIONS: 0
```

This was expected because only one healthy API replica remained. The PDB would
therefore prevent another voluntary API disruption until the second replica
recovered.

The Pending Pod Events reported:

```text
0/5 nodes are available:
1 node did not match pod topology spread constraints
1 node was unschedulable
3 nodes had untolerated taints
```

This meant:

```text
eph-worker01
  → correct node for the replacement, but cordoned

eph-worker02
  → already running the other API replica

Three control-plane nodes
  → protected by control-plane taints
```

The strict topology-spread policy therefore prevented both API replicas from
being placed on the same worker node.

The worker was returned to service using:

```bash
kubectl uncordon eph-worker01
```

After uncordoning, Kubernetes scheduled the Pending replacement Pod on
`eph-worker01`.

Final recovered state:

```text
eph-worker01 → 10.244.35.110
eph-worker02 → 10.244.176.224
```

Both Pods returned to:

```text
READY:   1/1
STATUS:  Running
```

The PodDisruptionBudget returned to:

```text
MAX UNAVAILABLE:      1
ALLOWED DISRUPTIONS:  1
```

The EndpointSlice automatically returned to two healthy endpoints:

```text
10.244.35.110
10.244.176.224
```

External availability was tested continuously through:

```text
http://havenbridge.lab/health/ready
```

The test recorded:

```text
2,306 successful HTTP 200 responses
```

This confirms that the remaining API replica continued serving external
requests while `eph-worker01` was drained and the replacement replica was
Pending.

The validated recovery flow was:

```text
Two healthy API replicas
        ↓
eph-worker01 is drained
        ↓
PDB permits one API Pod eviction
        ↓
eph-worker02 continues serving traffic
        ↓
Replacement Pod remains Pending
        ↓
eph-worker01 is uncordoned
        ↓
Replacement Pod schedules on eph-worker01
        ↓
Readiness probe succeeds
        ↓
EndpointSlice returns to two endpoints
        ↓
PDB allows one disruption again
```

The test confirms:

* the PodDisruptionBudget permits only one voluntary disruption at a time;
* the remaining API replica continues serving traffic;
* the Service removes the evicted Pod from its EndpointSlice;
* strict topology spreading prevents both replicas from sharing one worker;
* uncordoning restores the worker as a scheduling target;
* Kubernetes automatically restores the desired replica count;
* one API replica is restored on each worker node;
* the EndpointSlice returns to two ready endpoints.

Evidence is stored in:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/pdb-drain-validation/
```

Evidence files include:

```text
before-drain.txt
during-drain.txt
pending-pod-events.txt
after-drain.txt
readiness-during-drain.txt
curl-errors.txt
```

## Kubernetes NetworkPolicy Security

The HavenBridge backend uses Kubernetes `NetworkPolicy` resources to restrict
communication between application workloads.

The objective is a least-privilege network model:

```text
Only explicitly required traffic is allowed.
Unapproved Pod-to-Pod communication is blocked.
```

Before this phase, no NetworkPolicy resources existed in the cluster. The
HavenBridge application Pods were therefore not isolated by Kubernetes
NetworkPolicy.

The NetworkPolicy phase was introduced in stages instead of applying ingress
and egress restrictions simultaneously. This made each change easier to
validate and reduced the risk of accidentally breaking DNS or PostgreSQL
connectivity.

The implementation order was:

```text
Inspect existing labels and traffic paths
        ↓
Restrict Traefik-to-API ingress
        ↓
Validate approved and unauthorized API access
        ↓
Restrict API egress
        ↓
Allow only CoreDNS and PostgreSQL
        ↓
Validate allowed and blocked API egress
        ↓
Restrict PostgreSQL ingress
        ↓
Validate approved API access and blocked unauthorized access
```

The final HavenBridge application traffic model is:

```text
External Client
        |
        v
MetalLB / Traefik
        |
        | TCP/8000 allowed
        v
HavenBridge API
        |
        | TCP/5432 allowed
        v
PostgreSQL
```

The API also requires Kubernetes DNS:

```text
HavenBridge API
        |
        +----> CoreDNS UDP/53
        |
        +----> CoreDNS TCP/53
```

Other tested API egress traffic is blocked.

### Ingress and Egress Perspective

In Kubernetes NetworkPolicy, ingress and egress are interpreted relative to
the selected Pod.

```text
Traffic entering a selected Pod = ingress
Traffic leaving a selected Pod  = egress
```

For the API-to-PostgreSQL connection:

```text
API Pod                         PostgreSQL Pod
--------                        --------------
egress  --------------------->  ingress
```

This means one network connection can be egress from one workload and ingress
to another.

### MetalLB, Traefik and NetworkPolicy Responsibilities

MetalLB, Traefik and NetworkPolicy solve different problems.

```text
MetalLB
= makes the Traefik LoadBalancer IP reachable

Traefik
= receives HTTP traffic and routes it to the correct Kubernetes Service

NetworkPolicy
= controls whether Pod-to-Pod communication is allowed
```

For HavenBridge:

```text
External Client
      |
      v
havenbridge.lab
      |
      v
172.16.10.40
      |
      v
MetalLB
      |
      v
Traefik
      |
      | controlled by API ingress policy
      v
HavenBridge API
      |
      | controlled by API egress policy
      v
PostgreSQL
      ^
      |
      | controlled by PostgreSQL ingress policy
```

MetalLB does not decide whether Traefik may contact the API or whether the API
may contact PostgreSQL. Those permissions are enforced through NetworkPolicy.

### NetworkPolicy Resources

The completed configuration contains three production NetworkPolicies:

```text
allow-traefik-to-havenbridge-api
allow-havenbridge-api-egress
allow-havenbridge-api-to-postgres
```

The policies were verified with:

```bash
kubectl get networkpolicy \
  --namespace havenbridge
```

Observed state:

```text
NAME                                POD-SELECTOR
allow-havenbridge-api-egress        app.kubernetes.io/name=havenbridge-api

allow-havenbridge-api-to-postgres   app.kubernetes.io/instance=havenbridge-postgres,
                                    app.kubernetes.io/name=postgresql

allow-traefik-to-havenbridge-api    app.kubernetes.io/name=havenbridge-api
```

---

### 1. Traefik-to-API Ingress Protection

Manifest:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/networkpolicy.yaml
```

The policy selects the HavenBridge API Pods:

```yaml
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: havenbridge-api
```

This answers:

```text
Which Pods are protected by this NetworkPolicy?
```

The answer is:

```text
HavenBridge API Pods
```

The policy controls ingress only:

```yaml
policyTypes:
  - Ingress
```

The first implementation intentionally restricted only incoming API traffic.
API egress was left unrestricted temporarily so PostgreSQL and DNS
communication could be validated separately.

The allowed source must match both the Traefik namespace and the Traefik Pod
label:

```yaml
ingress:
  - from:
      - namespaceSelector:
          matchLabels:
            kubernetes.io/metadata.name: traefik
        podSelector:
          matchLabels:
            app.kubernetes.io/name: traefik
```

Because the `namespaceSelector` and `podSelector` are in the same peer entry,
both conditions must match:

```text
Namespace must be traefik
        AND
Pod must have app.kubernetes.io/name=traefik
```

The allowed destination port is:

```text
TCP/8000
```

The resulting allowed traffic path is:

```text
Traefik Pod
in the traefik namespace
        |
        | TCP/8000
        v
HavenBridge API Pod
```

Traffic from unrelated Pods is not allowed to reach the selected API Pods.

#### API Ingress Positive Validation

External traffic was tested through the approved application path:

```bash
curl -iv \
  http://havenbridge.lab/health/ready
```

Validated response:

```text
HTTP/1.1 200 OK
Server: uvicorn

{"status":"ready"}
```

The liveness endpoint was also tested:

```bash
curl -iv \
  http://havenbridge.lab/health/live
```

Validated response:

```text
HTTP/1.1 200 OK
Server: uvicorn
```

This confirmed that the approved traffic path remained available:

```text
External client
        ↓
MetalLB
        ↓
Traefik
        ↓
Allowed by NetworkPolicy
        ↓
HavenBridge API Pod on TCP/8000
```

#### API Ingress Negative Validation

A temporary BusyBox Pod was created in the `default` namespace.

Manifest:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/networkpolicy-validation/unauthorized-client-pod.yaml
```

The test Pod attempted direct access to:

```text
http://havenbridge-api.havenbridge.svc.cluster.local/health/ready
```

The test Pod did not satisfy the permitted source requirements:

```text
Namespace was not traefik

and

Pod label was not:
app.kubernetes.io/name=traefik
```

Validated output:

```text
Testing direct access to the HavenBridge API
Connecting to havenbridge-api.havenbridge.svc.cluster.local (10.109.62.24:80)
wget: download timed out

EXPECTED: NetworkPolicy blocked the connection.
```

The DNS name successfully resolved:

```text
havenbridge-api.havenbridge.svc.cluster.local
        ↓
10.109.62.24
```

This proved that Kubernetes DNS and the API Service were functioning.

The HTTP connection itself timed out, proving that the unauthorized Pod was
blocked before it could reach the API backend.

The validated security behaviour is:

```text
Traefik Pod in traefik namespace
        ↓
TCP/8000 allowed
        ↓
HavenBridge API

Unrelated Pod in default namespace
        ↓
Direct connection blocked
        ↓
Connection times out
```

The result was stored at:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/networkpolicy-validation/unauthorized-client-result.txt
```

The temporary Pod was removed after validation:

```bash
ssh -i /home/alabi/.ssh/eph_k8s \
  mino@172.16.10.31 \
  'kubectl delete pod unauthorized-api-client \
    --namespace default \
    --ignore-not-found'
```

This validation confirmed:

* Traefik can reach the HavenBridge API.
* External readiness requests return HTTP `200`.
* External liveness requests return HTTP `200`.
* Kubernetes DNS resolves the API Service.
* An unauthorized Pod cannot connect directly to the API Service.
* Calico is enforcing the API ingress NetworkPolicy.

---

### 2. HavenBridge API Egress Protection

Manifest:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/networkpolicy-egress.yaml
```

The policy selects the HavenBridge API Pods:

```yaml
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: havenbridge-api
```

The policy type is:

```yaml
policyTypes:
  - Egress
```

Once this policy selects the API Pods for egress, outbound traffic must match an
allowed egress rule.

The API requires only two approved internal destinations:

```text
CoreDNS
PostgreSQL
```

#### Kubernetes DNS Egress

The DNS rule selects CoreDNS using both namespace and Pod labels:

```yaml
namespaceSelector:
  matchLabels:
    kubernetes.io/metadata.name: kube-system

podSelector:
  matchLabels:
    k8s-app: kube-dns
```

This means:

```text
Destination namespace must be kube-system
        AND
Destination Pod must have k8s-app=kube-dns
```

Allowed DNS ports:

```text
UDP/53
TCP/53
```

UDP/53 is used for normal DNS queries.

TCP/53 is also allowed because DNS can use TCP when required.

The CoreDNS metrics port:

```text
TCP/9153
```

is intentionally not required by the HavenBridge API and is therefore not
included in the allowed API egress rules.

#### PostgreSQL Egress

PostgreSQL was identified using these Pod labels:

```text
app.kubernetes.io/instance=havenbridge-postgres
app.kubernetes.io/name=postgresql
```

The destination namespace is:

```text
havenbridge
```

Allowed port:

```text
TCP/5432
```

The API egress flow is therefore:

```text
HavenBridge API
      |
      +----> CoreDNS UDP/53      allowed
      |
      +----> CoreDNS TCP/53      allowed
      |
      +----> PostgreSQL TCP/5432 allowed
```

Other tested outbound destinations are blocked.

#### API Egress Positive Validation

After the egress policy was applied, both API replicas remained Ready and
PostgreSQL remained Running.

Validated API placement:

```text
havenbridge-api-554c86f6d5-8dhtp
READY: 1/1
NODE: eph-worker01
IP: 10.244.35.110

havenbridge-api-554c86f6d5-cdhd5
READY: 1/1
NODE: eph-worker02
IP: 10.244.176.224

havenbridge-postgres-0
READY: 1/1
NODE: eph-worker01
IP: 10.244.35.106
```

External readiness continued to return:

```text
HTTP/1.1 200 OK
```

The captured API logs continued to show successful readiness and liveness
requests without relevant DNS or PostgreSQL connection errors.

Positive validation evidence:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/networkpolicy-validation/api-egress-positive-validation.txt
```

#### API Egress Negative Validation

A temporary validation Job attempted to connect to:

```text
http://kube-dns.kube-system.svc.cluster.local:9153/metrics
```

The DNS lookup succeeded:

```text
kube-dns.kube-system.svc.cluster.local
        ↓
10.96.0.10
```

This demonstrated that the allowed DNS rule was working.

The connection to TCP/9153 timed out:

```text
Testing an egress destination that is not allowed

Destination:
http://kube-dns.kube-system.svc.cluster.local:9153/metrics

Connecting to kube-dns.kube-system.svc.cluster.local:9153 (10.96.0.10:9153)
wget: download timed out

EXPECTED: NetworkPolicy blocked TCP port 9153.
```

This demonstrated:

```text
CoreDNS DNS ports 53
        ↓
allowed

CoreDNS metrics port 9153
        ↓
blocked
```

The validation Job was removed after testing.

Evidence:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/networkpolicy-validation/api-egress-negative-validation.txt
```

Validation procedure:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/networkpolicy-validation/api-egress-negative-validation-steps.txt
```

---

### 3. PostgreSQL Ingress Protection

Manifest:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/networkpolicy-postgres-ingress.yaml
```

The PostgreSQL ingress policy selects Pods matching:

```yaml
podSelector:
  matchLabels:
    app.kubernetes.io/instance: havenbridge-postgres
    app.kubernetes.io/name: postgresql
```

The source must match both:

```text
Namespace:
havenbridge

Pod label:
app.kubernetes.io/name=havenbridge-api
```

The allowed destination port is:

```text
TCP/5432
```

The resulting database access rule is:

```text
HavenBridge API
        |
        | TCP/5432
        v
PostgreSQL
```

Unrelated Pods are blocked.

#### API Egress and PostgreSQL Ingress Relationship

The API-to-PostgreSQL connection is protected from both perspectives.

From the API perspective:

```text
API egress policy:

"I am permitted to send traffic to PostgreSQL on TCP/5432."
```

From the PostgreSQL perspective:

```text
PostgreSQL ingress policy:

"I am permitted to receive TCP/5432 traffic from HavenBridge API Pods."
```

Therefore:

```text
API egress allows PostgreSQL
              AND
PostgreSQL ingress allows API
              |
              v
Connection succeeds
```

If either side does not allow the traffic, the connection fails.

#### PostgreSQL Positive Validation

After applying the PostgreSQL ingress NetworkPolicy, the API readiness endpoint
was tested:

```bash
curl -iv \
  http://havenbridge.lab/health/ready
```

Observed response:

```text
HTTP/1.1 200 OK
Server: uvicorn

{"status":"ready"}
```

The HavenBridge workloads remained healthy:

```text
havenbridge-api-554c86f6d5-8dhtp
READY: 1/1
STATUS: Running
NODE: eph-worker01
IP: 10.244.35.110

havenbridge-api-554c86f6d5-cdhd5
READY: 1/1
STATUS: Running
NODE: eph-worker02
IP: 10.244.176.224

havenbridge-postgres-0
READY: 1/1
STATUS: Running
NODE: eph-worker01
IP: 10.244.35.106
```

The successful API readiness response confirmed that approved
API-to-PostgreSQL communication remained functional after database ingress
isolation was enabled.

#### PostgreSQL Negative Validation

A temporary Pod named:

```text
postgres-unauthorized-client
```

was created in:

```text
default
```

It attempted to connect to:

```text
havenbridge-postgres.havenbridge.svc.cluster.local:5432
```

The Pod did not satisfy the approved source requirements:

```text
Namespace was not havenbridge

and

Pod was not labelled:
app.kubernetes.io/name=havenbridge-api
```

Observed result:

```text
Testing unauthorized PostgreSQL access

EXPECTED: PostgreSQL ingress NetworkPolicy blocked the connection.
```

This confirmed that an unrelated workload could not establish a TCP connection
to PostgreSQL on port `5432`.

The temporary Pod was removed:

```bash
kubectl delete pod postgres-unauthorized-client \
  --namespace default \
  --ignore-not-found
```

Cleanup was verified:

```text
=== Default Namespace ===
No resources found in default namespace.
```

Validation procedure:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/networkpolicy-validation/postgres-ingress-validation-steps.txt
```

Validation result:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/networkpolicy-validation/postgres-ingress-validation.txt
```

---

### Final NetworkPolicy Validation

After all tests and cleanup, the three production NetworkPolicies remained
active:

```text
allow-havenbridge-api-egress
allow-havenbridge-api-to-postgres
allow-traefik-to-havenbridge-api
```

The final application state remained healthy:

```text
HavenBridge API replica 1: Running
HavenBridge API replica 2: Running
PostgreSQL:               Running
```

External readiness was tested again:

```bash
curl -iv \
  http://havenbridge.lab/health/ready
```

Final result:

```text
HTTP/1.1 200 OK

{"status":"ready"}
```

The completed NetworkPolicy model is:

```text
External Client
      |
      v
MetalLB
      |
      v
Traefik
      |
      | API ingress policy
      | TCP/8000 allowed
      v
HavenBridge API
      |
      | API egress policy
      | TCP/5432 allowed
      v
PostgreSQL
      ^
      |
      | PostgreSQL ingress policy
      | HavenBridge API Pods allowed
```

Kubernetes DNS is separately permitted:

```text
HavenBridge API
       |
       +----> CoreDNS UDP/53
       |
       +----> CoreDNS TCP/53
```

The validated least-privilege communication model is:

```text
Traefik -> API                 allowed
Unrelated Pod -> API           blocked

API -> CoreDNS:53              allowed
API -> PostgreSQL:5432         allowed
API -> unapproved tested port  blocked

API -> PostgreSQL:5432         allowed
Unrelated Pod -> PostgreSQL    blocked
```

### NetworkPolicy Validation Evidence

Validation evidence is stored under:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/networkpolicy-validation/
```

The evidence includes:

```text
unauthorized-client-pod.yaml
unauthorized-client-result.txt

api-egress-positive-validation.txt
api-egress-negative-test-job.yaml
api-egress-negative-validation.txt
api-egress-negative-validation-steps.txt

postgres-unauthorized-client.yaml
postgres-ingress-validation-steps.txt
postgres-ingress-validation.txt

havenbridge-networkpolicy-ingress-vs-egress.txt
```

The validation steps files document how each test was performed.

The validation result files preserve the observed evidence from the running
cluster.

### NetworkPolicy Phase Status

The planned HavenBridge NetworkPolicy security phase is complete.

Validated controls include:

* restricted Traefik-to-API ingress;
* blocked unauthorized direct API access;
* restricted API DNS egress;
* restricted API-to-PostgreSQL egress;
* blocked unapproved API egress;
* restricted PostgreSQL ingress;
* blocked unauthorized PostgreSQL access;
* successful application operation after network isolation;
* successful cleanup of temporary validation resources.



## Current External Routing and TLS Status

> **Current-state note:** Earlier sections of this README contain HTTP-based
> validation performed before the HavenBridge TLS phase was completed. Those
> results are retained as historical implementation evidence. The current
> external architecture redirects HTTP traffic to HTTPS and serves the
> HavenBridge application through the Traefik `websecure` listener.

### Current Backend Manifests

The HavenBridge backend currently uses:

```text
configmap.yaml
deployment.yaml
service.yaml
httproute.yaml
httproute-http-redirect.yaml
pdb.yaml
networkpolicy.yaml
networkpolicy-egress.yaml
networkpolicy-postgres-ingress.yaml
```

The manifests collectively provide:

```text
Application configuration
        ↓
FastAPI Deployment
        ↓
ClusterIP Service
        ↓
HTTPS Gateway API routing
        ↓
HTTP-to-HTTPS redirect
        ↓
PodDisruptionBudget
        ↓
NetworkPolicy security
```

### Current HTTP Behaviour

Plain HTTP no longer serves the HavenBridge API directly.

Requests arriving through:

```text
http://havenbridge.lab
```

follow this path:

```text
Client
   ↓
havenbridge.lab
   ↓
172.16.10.40
   ↓
MetalLB
   ↓
Traefik Service :80
   ↓
web:8000
   ↓
Gateway HTTP listener
   ↓
havenbridge-http-redirect HTTPRoute
   ↓
301 Moved Permanently
   ↓
HTTPS
```

The redirect was validated as:

```text
HTTP/1.1 301 Moved Permanently
Location: https://havenbridge.lab/health/ready
```

The redirect manifest is:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/httproute-http-redirect.yaml
```

### Current HTTPS Behaviour

HTTPS is now the application-serving path.

```text
https://havenbridge.lab
        ↓
172.16.10.40
        ↓
MetalLB
        ↓
Traefik LoadBalancer Service :443
        ↓
websecure:8443
        ↓
Gateway HTTPS listener
        ↓
TLS termination
        ↓
havenbridge-api HTTPRoute
        ↓
havenbridge-api Service :80
        ↓
EndpointSlice
        ↓
Ready API Pod :8000
        ↓
FastAPI
```

The application HTTPS route is defined in:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/httproute.yaml
```

### TLS Termination

TLS terminates at Traefik.

The client communicates with Traefik using encrypted HTTPS:

```text
Client
   ↕
HTTPS / TLS
   ↕
Traefik
```

Traefik uses the Kubernetes TLS Secret:

```text
havenbridge-tls
```

to present the certificate for:

```text
havenbridge.lab
```

After TLS termination, Traefik routes the request internally to the
`havenbridge-api` Service.

Detailed TLS and private-PKI documentation is maintained at:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/tls/README.md
```

Detailed Traefik and Gateway API documentation is maintained at:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/traefik/README.md
```

### Final End-to-End Validation

The HTTP redirect was validated with:

```text
HTTP/1.1 301 Moved Permanently
Location: https://havenbridge.lab/health/ready
```

Following the redirect produced:

```text
Final URL: https://havenbridge.lab/health/ready
HTTP Code: 200
Redirects: 1
```

Direct HTTPS validation produced:

```text
HTTP/2 200
{"status":"ready"}
```

The final production-style request path is therefore:

```text
HTTP request
     ↓
301 HTTPS redirect
     ↓
HTTPS :443
     ↓
TLS termination at Traefik
     ↓
Gateway API
     ↓
HTTPRoute
     ↓
havenbridge-api Service
     ↓
EndpointSlice
     ↓
Ready API Pod
     ↓
FastAPI
     ↓
HTTP 200
```

### Current Backend Security and Availability

The HavenBridge backend currently combines:

```text
2 API replicas
        +
topology spreading
        +
PodDisruptionBudget
        +
readiness and liveness probes
        +
non-root container execution
        +
read-only root filesystem
        +
NetworkPolicy
        +
HTTPS
        +
HTTP-to-HTTPS redirect
```

Together, these controls provide application availability, workload isolation,
secure external access and controlled Kubernetes networking.

### Validation Evidence

Backend validation evidence is maintained under:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/applications/havenbridge/backend/evidence/
```

TLS validation evidence is maintained under:

```text
/home/alabi/projects/havenbridge-ha-service-platform/kubernetes/platform/evidence/tls-validation/
```
