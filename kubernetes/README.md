# Kubernetes Deployment Configuration

This directory contains Kubernetes manifests for deploying Doppelganger Studio to a production cluster.

## Directory Structure

```
kubernetes/
├── namespace.yaml              # Namespace definition
├── configmaps/                 # Configuration data
│   ├── app-config.yaml
│   └── nginx-config.yaml
├── secrets/                    # Sensitive data (not committed)
│   ├── api-keys.yaml.example
│   └── database-credentials.yaml.example
├── deployments/                # Deployment definitions
│   ├── api-deployment.yaml
│   ├── worker-deployment.yaml
│   └── frontend-deployment.yaml
├── services/                   # Service definitions
│   ├── api-service.yaml
│   ├── frontend-service.yaml
│   └── database-service.yaml
├── ingress/                    # Ingress rules
│   └── ingress.yaml
├── volumes/                    # Persistent volumes
│   ├── postgres-pvc.yaml
│   └── redis-pvc.yaml
└── monitoring/                 # Monitoring stack
    ├── prometheus.yaml
    └── grafana.yaml
```

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3 (optional, for cert-manager)
- Docker images built and pushed to registry

## Quick Start

### 1. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 2. Create Secrets

```bash
# Copy example secrets
cp secrets/api-keys.yaml.example secrets/api-keys.yaml
cp secrets/database-credentials.yaml.example secrets/database-credentials.yaml

# Edit with your values
nano secrets/api-keys.yaml
nano secrets/database-credentials.yaml

# Apply secrets
kubectl apply -f secrets/
```

### 3. Create ConfigMaps

```bash
kubectl apply -f configmaps/
```

### 4. Create Persistent Volumes

```bash
kubectl apply -f volumes/
```

### 5. Deploy Services

```bash
kubectl apply -f services/
```

### 6. Deploy Applications

```bash
kubectl apply -f deployments/
```

### 7. Configure Ingress

```bash
kubectl apply -f ingress/
```

### 8. Monitor Deployment

```bash
kubectl get pods -n doppelganger-studio
kubectl logs -f deployment/api -n doppelganger-studio
```

## Scaling

### Scale API Workers

```bash
kubectl scale deployment api --replicas=5 -n doppelganger-studio
```

### Scale Background Workers

```bash
kubectl scale deployment worker --replicas=10 -n doppelganger-studio
```

## Monitoring

Access Grafana dashboards:

```bash
kubectl port-forward svc/grafana 3000:3000 -n doppelganger-studio
```

Then navigate to http://localhost:3000

## Troubleshooting

### Check Pod Status

```bash
kubectl describe pod <pod-name> -n doppelganger-studio
```

### View Logs

```bash
kubectl logs -f <pod-name> -n doppelganger-studio
```

### Execute Commands in Pod

```bash
kubectl exec -it <pod-name> -n doppelganger-studio -- /bin/bash
```

## Production Considerations

- [ ] Enable HTTPS with cert-manager
- [ ] Configure resource limits and requests
- [ ] Set up horizontal pod autoscaling
- [ ] Configure network policies
- [ ] Enable pod security policies
- [ ] Set up backup and disaster recovery
- [ ] Configure log aggregation
- [ ] Enable metrics and tracing
