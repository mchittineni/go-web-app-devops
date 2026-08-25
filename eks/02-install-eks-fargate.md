# Create an EKS cluster

Complete `01-prereq.md` first.

> **Cost warning:** an EKS cluster bills per hour for the control plane plus
> the compute behind it, whether or not anything is deployed. Delete the
> cluster when you finish the exercise.

## Option A — declarative cluster config (recommended)

A config file is reviewable, diffable and reproducible; a long
`eksctl create cluster` command line is none of those.

```yaml
# cluster.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: demo-cluster
  region: us-east-1
  # Pin the control plane version. Track EKS release notes for the current
  # supported versions before bumping.
  version: "1.32"

# Required for IRSA / Pod Identity so workloads get scoped AWS permissions
# instead of borrowing the node role.
iam:
  withOIDC: true

# Fargate removes node management entirely. Note that Fargate pods cannot use
# DaemonSets, host networking, or privileged containers — which suits this
# app fine, since it needs none of them.
fargateProfiles:
  - name: default
    selectors:
      - namespace: default
      - namespace: kube-system

addons:
  - name: vpc-cni
  - name: coredns
  - name: kube-proxy

cloudWatch:
  clusterLogging:
    enableTypes: ["api", "audit", "authenticator"]
```

```bash
eksctl create cluster -f cluster.yaml
```

## Option B — one-liner (quickest, least reproducible)

```bash
eksctl create cluster \
  --name demo-cluster \
  --region us-east-1 \
  --version 1.32 \
  --fargate \
  --with-oidc
```

## Verify

```bash
aws eks update-kubeconfig --name demo-cluster --region us-east-1
kubectl get nodes
kubectl get pods -A
```

## Deploy this app

```bash
helm upgrade --install go-web-app ./helm/go-web-app-chart \
  --set ingress.enabled=true \
  --set autoscaling.enabled=true \
  --atomic --timeout 5m
```

## Delete the cluster

Do this as soon as you are done — it is the single largest cost in the
tutorial.

```bash
eksctl delete cluster --name demo-cluster --region us-east-1 --wait
```

Then confirm nothing was orphaned (load balancers and EBS volumes outlive a
failed delete and keep billing):

```bash
aws elbv2 describe-load-balancers --region us-east-1 \
  --query 'LoadBalancers[].LoadBalancerName'
aws ec2 describe-volumes --region us-east-1 \
  --filters Name=status,Values=available --query 'Volumes[].VolumeId'
```
