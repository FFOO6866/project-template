# Cloud-Agnostic Deployment Guide

This guide provides instructions for deploying the Horme POV system to various cloud providers using Docker containers and Kubernetes.

## 🐳 Docker-Based Architecture

All services are containerized and can run on any platform that supports Docker:
- **Nexus Gateway**: Multi-channel API gateway (REST/WebSocket/MCP)
- **DataFlow Service**: Database operations with auto-generated nodes
- **MCP Server**: Model Context Protocol for AI agents
- **Classification Service**: ML-powered product classification
- **PostgreSQL**: Primary database with vector extensions
- **Redis**: Caching and session management

## 📦 Local Development with Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## ☸️ Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3 (optional but recommended)

### 1. Create Namespace and Secrets

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets
kubectl create secret generic horme-secrets \
  --from-literal=database-url="postgresql://user:pass@postgres:5432/db" \
  --from-literal=redis-url="redis://:pass@redis:6379/0" \
  --from-literal=jwt-secret="your-secret-key" \
  -n horme-prod
```

### 2. Deploy Infrastructure

```bash
# Deploy PostgreSQL and Redis
kubectl apply -f k8s/infrastructure.yaml

# Wait for infrastructure to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n horme-prod --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n horme-prod --timeout=300s
```

### 3. Deploy Application Services

```bash
# Deploy all services
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n horme-prod
kubectl get svc -n horme-prod
```

## 🌩️ Cloud-Specific Deployment

### AWS (EKS)

```bash
# Create EKS cluster
eksctl create cluster --name horme-prod --region us-east-1 --nodes 3 --node-type t3.large

# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller/crds"
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system --set clusterName=horme-prod

# Deploy application
kubectl apply -f k8s/

# Create ALB Ingress
kubectl apply -f k8s/aws/alb-ingress.yaml
```

### Google Cloud (GKE)

```bash
# Create GKE cluster
gcloud container clusters create horme-prod \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2

# Get credentials
gcloud container clusters get-credentials horme-prod --zone us-central1-a

# Deploy application
kubectl apply -f k8s/

# Create Cloud Load Balancer
kubectl apply -f k8s/gcp/cloud-lb.yaml
```

### Azure (AKS)

```bash
# Create resource group
az group create --name horme-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group horme-rg \
  --name horme-prod \
  --node-count 3 \
  --node-vm-size Standard_DS2_v2

# Get credentials
az aks get-credentials --resource-group horme-rg --name horme-prod

# Deploy application
kubectl apply -f k8s/

# Create Azure Load Balancer
kubectl apply -f k8s/azure/azure-lb.yaml
```

## 🔧 Configuration Management

### Environment Variables

All services support configuration through environment variables:

```yaml
# Common variables
- ENVIRONMENT: production/staging/development
- LOG_LEVEL: DEBUG/INFO/WARNING/ERROR
- DATABASE_URL: PostgreSQL connection string
- REDIS_URL: Redis connection string

# Service-specific
- NEXUS_PORT: API port (default: 8000)
- MCP_PORT: MCP server port (default: 3000)
- OPENAI_API_KEY: For classification service
```

### ConfigMaps and Secrets

```bash
# Create ConfigMap
kubectl create configmap app-config \
  --from-file=config/production.yaml \
  -n horme-prod

# Update secrets
kubectl create secret generic api-keys \
  --from-literal=openai-key="sk-..." \
  --dry-run=client -o yaml | kubectl apply -f -
```

## 📊 Monitoring and Logging

### Prometheus + Grafana

```bash
# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

### ELK Stack for Logs

```bash
# Install Elasticsearch
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch -n logging

# Install Kibana
helm install kibana elastic/kibana -n logging

# Install Fluentd
kubectl apply -f k8s/logging/fluentd-daemonset.yaml
```

## 🚀 CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Kubernetes
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and push Docker images
      run: |
        docker build -t ${{ secrets.REGISTRY }}/nexus-gateway:${{ github.sha }} -f docker/Dockerfile.nexus-gateway .
        docker push ${{ secrets.REGISTRY }}/nexus-gateway:${{ github.sha }}
    
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/nexus-gateway nexus-gateway=${{ secrets.REGISTRY }}/nexus-gateway:${{ github.sha }} -n horme-prod
```

## 🔒 Security Best Practices

1. **Network Policies**: Restrict inter-pod communication
2. **RBAC**: Use service accounts with minimal permissions
3. **Secrets Management**: Use external secret managers (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault)
4. **Image Scanning**: Scan containers for vulnerabilities
5. **TLS Everywhere**: Use TLS for all communications

## 🆘 Troubleshooting

### Common Issues

```bash
# Check pod logs
kubectl logs -f deployment/nexus-gateway -n horme-prod

# Describe pod for events
kubectl describe pod <pod-name> -n horme-prod

# Check service endpoints
kubectl get endpoints -n horme-prod

# Test service connectivity
kubectl exec -it <pod-name> -n horme-prod -- curl http://nexus-gateway:8000/health
```

### Health Checks

All services expose health endpoints:
- `/health` - Liveness probe
- `/ready` - Readiness probe
- `/metrics` - Prometheus metrics

## 📈 Scaling

### Horizontal Pod Autoscaling

```yaml
# HPA is configured for all services
kubectl get hpa -n horme-prod

# Manual scaling
kubectl scale deployment/nexus-gateway --replicas=5 -n horme-prod
```

### Vertical Pod Autoscaling

```bash
# Install VPA
kubectl apply -f https://github.com/kubernetes/autoscaler/releases/latest/download/vertical-pod-autoscaler.yaml

# Apply VPA policies
kubectl apply -f k8s/vpa/
```

## 🔄 Updates and Rollbacks

```bash
# Rolling update
kubectl set image deployment/nexus-gateway nexus-gateway=horme/nexus-gateway:v2.0 -n horme-prod

# Check rollout status
kubectl rollout status deployment/nexus-gateway -n horme-prod

# Rollback if needed
kubectl rollout undo deployment/nexus-gateway -n horme-prod
```

## 📝 Summary

This cloud-agnostic deployment guide ensures your application can run on any cloud provider or on-premises infrastructure. The containerized architecture provides:

- **Portability**: Run anywhere Docker/Kubernetes is supported
- **Scalability**: Auto-scaling based on load
- **Resilience**: Health checks and automatic restarts
- **Observability**: Built-in monitoring and logging
- **Security**: Defense in depth with multiple layers

For provider-specific optimizations, refer to the respective cloud documentation.