# Part 10 · When it breaks

It will. These are the errors you are most likely to hit, and what they actually
mean.

## The universal debugging move

Whenever a pod misbehaves, run these two commands in this order. The answer is
in one of them almost every time:

```bash title="terminal — your first move, always"
kubectl describe pod <pod-name>   # read the Events at the bottom
kubectl logs <pod-name>           # read what the program said
```

## Pod status meanings

| Status | What it means | What to do |
|---|---|---|
| `ImagePullBackOff`<br>`ErrImagePull` | Kubernetes cannot find or download the image. | Check the `image:` spelling. Using `kind`? Run `kind load docker-image`. Private registry? You need a pull secret. |
| `CrashLoopBackOff` | The program starts, dies, and Kubernetes keeps retrying. | `kubectl logs <pod> --previous` — this shows the crash, which the normal logs will have lost. |
| `Pending` | No node can accept it. | `kubectl describe pod` and read Events. Usually not enough CPU/memory in the cluster. |
| `0/1 Running` | Running, but the readiness probe says no. | It cannot serve `/readyz`. Check the logs and the container port. |
| `OOMKilled` | It used more memory than its limit. | Raise `resources.limits.memory` in `values.yaml`. |

## Other common errors

| Message | Cause and fix |
|---|---|
| `address already in use` | Something else is on port 8080 — often an earlier run you forgot. Find it with `lsof -i :8080` and stop it, or use `LISTEN_ADDR=":9090" go run .` |
| `cannot connect to the Docker daemon` | Docker Desktop is not running. Start it and wait for the whale to settle. |
| `go.mod requires go >= 1.26` | Your Go is too old. Install a newer one and re-check `go version`. |
| `The connection to the server … was refused` | No cluster is running or `kubectl` is pointed at a dead one. Check `kubectl config current-context`. |
| `UPGRADE FAILED: another operation in progress` | A previous Helm command was interrupted. `helm rollback go-web-app`, then retry. |
| My CSS changes do nothing | Either the assets are compiled into the binary (rebuild), or you used an inline `style=` attribute, which the security policy blocks. Use a class in `app.css`. |
| Ingress returns 404 | No ingress controller installed, or `ingressClassName` does not match one. Check `kubectl get ingressclass`. |

## How to ask for help well

Include these four things and you will usually get an answer first try:

1. The exact command you ran.
2. The complete error, copied as text — not a screenshot, not paraphrased.
3. The output of `kubectl describe pod <name>` if it is cluster-related.
4. What you expected to happen instead.

## Clean up everything

```bash title="terminal — tear it all down"
helm uninstall go-web-app
kubectl delete -f k8s/manifests/ --ignore-not-found
kind delete cluster --name devops-demo
docker system prune -a          # reclaims disk from old images
```
