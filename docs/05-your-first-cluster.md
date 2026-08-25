# Part 05 · Your first Kubernetes cluster

Kubernetes runs containers for you. You describe what you want in a file; it
makes reality match, and keeps it matching.

## Get a cluster on your laptop, free

=== "Docker Desktop (easiest)"

    Open Docker Desktop → Settings → Kubernetes → tick **Enable Kubernetes** →
    Apply. Wait a few minutes.

=== "kind"

    `kind` runs a cluster inside Docker.

    ```bash title="terminal — anywhere"
    brew install kind          # or: go install sigs.k8s.io/kind@latest
    kind create cluster --name devops-demo
    ```

Either way, confirm it works:

```bash title="terminal — anywhere"
kubectl get nodes
```

```text
NAME                        STATUS   ROLES           AGE   VERSION
devops-demo-control-plane   Ready    control-plane   1m    v1.32.0
```

`Ready` is what you need. `kubectl` is your remote control for the cluster.

## The five nouns of Kubernetes

Learn these five and you can read almost any Kubernetes file:

| Noun | What it is | Analogy |
|---|---|---|
| **Pod** | One running copy of your container. The smallest unit. | One employee |
| **Deployment** | "Always keep 3 pods of this image running." Replaces them one at a time on update. | The staffing plan |
| **Service** | One stable internal address that load-balances across the pods. | The department phone number |
| **Ingress** | Lets traffic from outside the cluster reach a Service. | The front door |
| **Namespace** | A folder to keep unrelated things apart. | A floor of the building |

Pods are *disposable*. They die, get replaced, and change address. That is why a
Service exists: it is the address that never changes.

## Point the manifests at your image

Open `k8s/manifests/deployment.yaml` and find the `image:` line. It says
`<docker-user-name>/go-web-app:latest` — a placeholder. Change it to just:

```yaml title="k8s/manifests/deployment.yaml — edit this line"
image: go-web-app:latest
imagePullPolicy: IfNotPresent
```

If you used `kind`, it cannot see your local images unless you load them:

```bash title="terminal — only if using kind"
kind load docker-image go-web-app:latest --name devops-demo
```

## Deploy

```bash title="terminal — in the project folder"
kubectl apply -f k8s/manifests/
```

That one command created seven things. Watch the pods start:

```bash title="terminal — anywhere"
kubectl get pods --watch
```

```text
NAME                          READY   STATUS    RESTARTS   AGE
go-web-app-7d9f8b6c4-4xk2p    1/1     Running   0          20s
go-web-app-7d9f8b6c4-8mn5q    1/1     Running   0          20s
go-web-app-7d9f8b6c4-qz7wt    1/1     Running   0          20s
```

Three pods, because the Deployment asked for three. Press ++ctrl+c++ to stop
watching.

## Visit it

The Service is internal to the cluster, so build a temporary tunnel from your
laptop into it:

```bash title="terminal — leave this running"
kubectl port-forward svc/go-web-app 8080:80
```

Open [localhost:8080/home](http://localhost:8080/home). Your site is now served
by Kubernetes.

## Now break it on purpose

This is the most convincing thing you will do today. In a second terminal,
delete a pod:

```bash title="terminal — a second terminal"
kubectl get pods
kubectl delete pod <paste-one-pod-name-here>
kubectl get pods
```

A new pod is already starting. You asked for three; Kubernetes will keep three,
forever, without being asked again. Your website never went down, because the
other two kept serving.

!!! note "This is the whole idea"

    You never told Kubernetes *how* to recover. You told it the desired state —
    three pods — and it continuously works to make reality match. That is called
    **declarative** configuration, and it is the concept underneath Kubernetes,
    Helm, Terraform and Argo CD alike.

## Useful commands while you are here

| Command | Use it when |
|---|---|
| `kubectl get pods` | What is running? |
| `kubectl describe pod <name>` | Why won't this pod start? *Read the Events at the bottom.* |
| `kubectl logs <name>` | What is the program printing? |
| `kubectl logs <name> --previous` | Why did it crash before restarting? |
| `kubectl get events --sort-by=.lastTimestamp` | What just happened in the cluster? |
| `kubectl delete -f k8s/manifests/` | Remove everything you created |

!!! success "Checkpoint"

    - Three pods show `1/1 Running`.
    - The site loads through `port-forward`.
    - You deleted a pod and watched a replacement appear.
