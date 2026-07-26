# HavenBridge Kubernetes Platform Services

This directory contains Kubernetes platform components required to expose,
route, secure and persist the HavenBridge application.

## Components

- MetalLB for bare-metal LoadBalancer services
- Traefik Proxy for application traffic
- Kubernetes Gateway API for routing
- Persistent storage for stateful workloads
- TLS and certificate management

## Network Addresses

| Purpose | Address |
|---|---|
| Kubernetes API VIP | `172.16.10.30` |
| Application Gateway IP | `172.16.10.40` |
| Kubernetes API DNS | `k8s-api.lab` |
| Application DNS | `havenbridge.lab` |

The Kubernetes API VIP and application gateway address are intentionally
separate.
