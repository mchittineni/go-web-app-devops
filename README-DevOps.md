# DevOps: the delivery path

How this application gets from a commit to a running pod, and what each gate
is actually protecting against.

```
commit ──► build & test ──► lint ──► security scans ──► manifest validation
                                                              │
                                                              ▼
                                        multi-arch image build ──► Trivy image scan
                                                              │
                                                              ▼
                                              SBOM ──► keyless Cosign signature
                                                              │
                                                              ▼
                                  commit digest into values.yaml ──► Argo CD syncs
```

CI never holds cluster credentials. Its last action is a commit; Argo CD does
the deploying.

## Toolchain versions

| Component | Version | Where it is pinned |
|---|---|---|
| Go (language) | 1.26 | [go.mod](go.mod) |
| Go (build toolchain) | 1.27 | [Dockerfile](Dockerfile), `GO_VERSION` in the workflow |
| Runtime base image | `distroless/static-debian12:nonroot` | [Dockerfile](Dockerfile) |
| golangci-lint | v2.13.1 | [.golangci.yml](.golangci.yml), workflow |
| Helm | v4.2.4 | workflow |
| Kubernetes | ≥ 1.27 | `kubeVersion` in [Chart.yaml](helm/go-web-app-chart/Chart.yaml) |
| ingress-nginx | controller-v1.15.1 | [installation doc](ingress-controller/nginx/01-installation.md) |
| Argo CD | v3.5.1 | [install doc](gitops/argocd/01-install.md) |

Dependabot ([config](.github/dependabot.yml)) opens weekly PRs for Go modules,
GitHub Actions and base images.

## The container

Two stages. The build stage compiles a static binary; the runtime stage is
`distroless/static` with nothing in it but that binary.

```bash
make docker
make docker-run    # runs it read-only, no capabilities, no privilege escalation
```

Properties worth keeping:

- `CGO_ENABLED=0` — a truly static binary, so the runtime image needs no libc.
- `-trimpath` and `-buildvcs=false` — no build-host paths leak into the binary,
  which is what makes the build reproducible.
- `distroless/static:nonroot` — no shell, no package manager, no busybox. There
  is nothing in the image for an RCE to pivot into.
- Runs as uid **65532**, declared numerically so `runAsNonRoot` admission can
  verify it without resolving `/etc/passwd`.
- Assets are embedded, so no `COPY` of static files and no writable path is
  needed at runtime.
- Built for `linux/amd64` and `linux/arm64`.

## The pipeline

[`.github/workflows/cicd.yaml`](.github/workflows/cicd.yaml). Permissions are
`contents: read` at the top level; each job opts into more only where it needs
it.

| Job | What it enforces |
|---|---|
| **build** | `gofmt` clean, `go.mod` tidy, `go vet`, tests under `-race` with `-shuffle=on`, coverage |
| **lint** | golangci-lint, including `gosec`, `bodyclose`, `errorlint`, `noctx` |
| **security** | `govulncheck` (reachable stdlib + module CVEs), Trivy filesystem scan, gitleaks secret scan; findings uploaded as SARIF to code scanning |
| **manifests** | `helm lint --strict`, chart renders, `kubeconform` against real Kubernetes schemas, Trivy config scan of the Dockerfile and manifests |
| **image** | Multi-arch build, Trivy image scan, CycloneDX SBOM, keyless Cosign signature and SBOM attestation |
| **deploy** | Commits the new tag **and digest** into the chart's values |

Notes on why a few things are the way they are:

- **PRs build but never push.** They build a single architecture and `--load`
  it so the image scan has a real artefact to inspect. buildx cannot `--load`
  a multi-platform result, which is why the platform list is conditional.
- **Trivy runs twice on the filesystem.** `trivy-action` ignores `exit-code`
  when it is emitting SARIF, so reporting and gating cannot be one step.
- **Deploys are pinned by digest.** Tags are mutable; a digest is not. The tag
  is written alongside it only so a human can read the values file.
- **`[skip ci]` on the promotion commit**, plus `paths-ignore` on
  `values.yaml`, so the pipeline cannot trigger itself.

### Required repository secrets

| Secret | Purpose |
|---|---|
| `DOCKERHUB_USERNAME` | Registry namespace and login |
| `DOCKERHUB_TOKEN` | Registry access token — **not** an account password |
| `TOKEN` | Optional PAT for the promotion commit. Falls back to `GITHUB_TOKEN`; needed only if branch protection blocks the default token |

Keyless signing needs no secret — it uses the workflow's OIDC identity, which
is why the `image` job requests `id-token: write`.

### Verifying a published image

```bash
cosign verify docker.io/<user>/go-web-app:<tag> \
  --certificate-identity-regexp='.*/go-web-app-devops/.*' \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com

# And read the attested SBOM
cosign download attestation docker.io/<user>/go-web-app:<tag> \
  | jq -r '.payload' | base64 -d | jq '.predicate'
```

## Kubernetes

Two equivalent paths. The Helm chart is what CI promotes to;
`k8s/manifests/` is the same thing written out longhand for learning.

```bash
# Helm (what production uses)
make helm-install
make helm-test          # runs a real HTTP probe against the service

# Raw manifests
make k8s-apply
```

### What the workload asserts about itself

| Control | Setting | Why |
|---|---|---|
| Probes | `startupProbe`, `livenessProbe` on `/healthz`; `readinessProbe` on `/readyz` | `/readyz` verifies the embedded assets resolve, so a broken build never takes traffic |
| Rollout | `maxUnavailable: 0`, `maxSurge: 1` | New pods must be ready before old ones go |
| Drain | `terminationGracePeriodSeconds: 30` | The app drains for up to 15s on `SIGTERM` |
| Root filesystem | `readOnlyRootFilesystem: true` | Nothing is written at runtime |
| Privileges | `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]` | Restricted PSS baseline |
| Identity | `runAsNonRoot`, uid/gid 65532, `seccompProfile: RuntimeDefault` | Restricted PSS baseline |
| API access | `automountServiceAccountToken: false` | The app never calls the API server, so it gets no token |
| Resources | CPU + memory requests, memory limit only | A CPU limit throttles a bursty HTTP server for no benefit; unbounded memory is what evicts a node |
| Availability | PDB `minAvailable`, `topologySpreadConstraints` | Survives a node drain and a single-node loss |
| Network | Optional NetworkPolicy: ingress from the controller, egress to DNS only | Default-deny for a workload that needs nothing outbound |

The Ingress no longer carries `rewrite-target: /`. The original manifest had
it, but the app serves real paths (`/courses`, `/static/app.css`), so rewriting
everything to `/` breaks asset loading.

### Enabling the optional pieces

```bash
helm upgrade --install go-web-app ./helm/go-web-app-chart \
  --set ingress.enabled=true \
  --set autoscaling.enabled=true \
  --set networkPolicy.enabled=true \
  --atomic --timeout 5m
```

`--atomic` rolls back automatically if the release does not become healthy,
which is what you want in a pipeline.

## GitOps with Argo CD

Install per [gitops/argocd/01-install.md](gitops/argocd/01-install.md), then
apply [gitops/argocd/02-application.yaml](gitops/argocd/02-application.yaml).

`selfHeal: true` reverts manual `kubectl edit`s, and the Application ignores
`/spec/replicas` because the HPA owns that field once autoscaling is on —
otherwise Argo CD and the HPA fight over it forever.

## Cluster setup

- [eks/01-prereq.md](eks/01-prereq.md) — tooling and credentials
- [eks/02-install-eks-fargate.md](eks/02-install-eks-fargate.md) — cluster creation
- [ingress-controller/nginx/01-installation.md](ingress-controller/nginx/01-installation.md) — ingress

**Delete the cluster when you are done.** EKS bills the control plane hourly
whether or not anything is deployed.

## Rollback

```bash
# Helm
helm rollback go-web-app          # previous revision
helm history go-web-app

# Argo CD — revert the promotion commit; the cluster follows Git
git revert <promotion-commit>

# Emergency, out-of-band
kubectl rollout undo deployment/go-web-app
```

Prefer the Git revert. A `kubectl rollout undo` under Argo CD's `selfHeal` will
be reverted back within minutes, because Git still says otherwise.

## The documentation site

A beginner-facing guide lives in [`docs/`](docs/) and publishes to GitHub Pages
at <https://mchittineni.github.io/go-web-app-devops/>.

```bash
make docs-install   # once
make docs           # live preview on :8000
make docs-build     # exactly what CI runs (--strict)
```

[`.github/workflows/docs.yaml`](.github/workflows/docs.yaml) builds it on every
push touching `docs/` or `mkdocs.yml` and deploys from `main`. It uses the Pages
Actions flow, so there is no `gh-pages` branch and no build output in the
repository. `--strict` means a broken internal link or a page missing from the
nav fails the build rather than shipping.

**One-time setup in GitHub:** Settings -> Pages -> Source -> **GitHub Actions**.
Without that, the deploy job fails with a "Pages not enabled" error.

## Reproducing the gates locally

```bash
make verify   # fmt, vet, lint, test, helm lint + schema validation
make vuln     # govulncheck
make scan     # Trivy filesystem + image
```
