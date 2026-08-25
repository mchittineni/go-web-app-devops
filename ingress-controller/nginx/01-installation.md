# Install the NGINX Ingress Controller

The manifest below is **pinned to a release**. Never install from a moving
`main`/`master` URL: the controller ships breaking changes between minors, and
an unpinned apply means your ingress layer changes without a commit.

## On AWS (creates a Network Load Balancer)

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.15.1/deploy/static/provider/aws/deploy.yaml
```

## On a local cluster (kind, minikube, Docker Desktop)

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.15.1/deploy/static/provider/cloud/deploy.yaml
```

## Wait for it to become ready

```bash
kubectl wait --namespace ingress-nginx \
  --for=condition=Ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s
```

## Confirm the IngressClass exists

The chart sets `ingress.className: nginx`, which must match a real
IngressClass or the Ingress will be silently ignored.

```bash
kubectl get ingressclass
```

## Get the external address

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

## Upgrading

Check the release notes for the target version first — the controller has
removed annotations and tightened defaults across minor releases.

<https://github.com/kubernetes/ingress-nginx/releases>

Then re-apply the new pinned URL and watch the rollout:

```bash
kubectl rollout status -n ingress-nginx deployment/ingress-nginx-controller
```

## Note on Gateway API

Ingress is now feature-frozen upstream; new work goes into the
[Gateway API](https://gateway-api.sigs.k8s.io/). Ingress remains fully
supported and is the right choice for this project, but for a greenfield
platform evaluate Gateway API first.
