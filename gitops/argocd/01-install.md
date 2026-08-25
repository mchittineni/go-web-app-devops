# Install Argo CD

## Install from a pinned release

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.1/manifests/install.yaml
```

`stable` is a moving tag. Pinning a version means an Argo CD upgrade is a
reviewed commit rather than a surprise, and it keeps the CLI and server in
step. Check the [release notes](https://github.com/argoproj/argo-cd/releases)
before bumping.

Wait for it:

```bash
kubectl wait -n argocd --for=condition=available --timeout=300s \
  deployment/argocd-server
```

## Access the UI

Port-forwarding is the safest default — it exposes nothing publicly:

```bash
kubectl port-forward -n argocd svc/argocd-server 8080:443
# then open https://localhost:8080
```

If you need a LoadBalancer instead, be aware this puts the Argo CD API on the
public internet. Change the admin password first and put TLS in front of it.

```bash
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
kubectl get svc argocd-server -n argocd
```

On Windows PowerShell the JSON needs escaping:

```powershell
kubectl patch svc argocd-server -n argocd -p '{\"spec\": {\"type\": \"LoadBalancer\"}}'
```

## Log in

```bash
# Initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d; echo

argocd login localhost:8080 --username admin
```

Then rotate it and delete the bootstrap secret — it is a plaintext credential
sitting in the cluster:

```bash
argocd account update-password
kubectl -n argocd delete secret argocd-initial-admin-secret
```

## Register this application

Apply `02-application.yaml` in this directory, or:

```bash
argocd app create go-web-app \
  --repo https://github.com/iam-veeramalla/go-web-app-devops.git \
  --path helm/go-web-app-chart \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default \
  --sync-policy automated \
  --self-heal --auto-prune
```

CI writes the new image tag and digest into
`helm/go-web-app-chart/values.yaml` on every successful build; Argo CD picks
that commit up and rolls it out. That commit is the deployment record.
