# Part 06 · Package it with Helm

You now have seven YAML files with values hardcoded in them. Deploying a second
copy for staging would mean copying all seven and editing them. Helm fixes that.

A Helm **chart** is those same files with the changeable parts pulled out into
one `values.yaml`. Two pieces:

- `helm/go-web-app-chart/templates/` — the shapes, with blanks
- `helm/go-web-app-chart/values.yaml` — what fills the blanks

## Look before you leap

`helm template` fills in the blanks and prints the result *without touching the
cluster*. Always do this first:

```bash title="terminal — in the project folder"
helm template go-web-app ./helm/go-web-app-chart | head -40
```

That output is ordinary Kubernetes YAML — exactly the kind of thing you applied
in [Part 05](05-your-first-cluster.md). Helm is a text generator, nothing more
mysterious.

## Install it

First remove the manual version so the two do not collide:

```bash title="terminal — in the project folder"
kubectl delete -f k8s/manifests/
```

Now install via Helm, pointing at your local image:

```bash title="terminal — in the project folder"
helm upgrade --install go-web-app ./helm/go-web-app-chart \
  --set image.repository=go-web-app \
  --set image.tag=latest \
  --atomic --timeout 3m
```

Three flags worth knowing:

| Flag | Why |
|---|---|
| `upgrade --install` | Installs if new, upgrades if it exists. One command for both, so scripts stay simple. |
| `--set x=y` | Overrides one value without editing the file. |
| `--atomic` | **Automatically rolls back** if the release does not become healthy. Never deploy without it. |

## Confirm and test

```bash title="terminal — anywhere"
helm list
kubectl get pods
helm test go-web-app
```

`helm test` launches a throwaway pod that makes a real HTTP request to
`/readyz`. If it passes, the release genuinely works — not just "the pods
started".

## Turn on the optional pieces

The chart ships extra features switched off. Turn them on to see what a
production-shaped deployment includes:

```bash title="terminal — in the project folder"
helm upgrade --install go-web-app ./helm/go-web-app-chart \
  --set image.repository=go-web-app --set image.tag=latest \
  --set autoscaling.enabled=true \
  --set ingress.enabled=true \
  --atomic --timeout 3m
```

| Feature | What it does |
|---|---|
| **Autoscaling** (HPA) | Adds pods when CPU is busy, removes them when quiet |
| **Ingress** | Gives the site a real hostname instead of `port-forward` |
| **Disruption budget** | Stops a node upgrade taking all your pods at once |
| **Network policy** | Blocks all traffic except what the app actually needs |

## Rolling back

```bash title="terminal — anywhere"
helm history go-web-app
helm rollback go-web-app
```

Helm keeps every previous version. Rollback is one command.

!!! success "Checkpoint"

    - `helm list` shows one release, status `deployed`.
    - `helm test` passes.
    - You understand that Helm output is just Kubernetes YAML.
