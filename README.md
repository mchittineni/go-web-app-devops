# Go Web Application

A small website written in Go, using only the standard library. It exists to be
the subject of an end-to-end DevOps project: containerised, scanned, signed,
and deployed to Kubernetes with Helm and Argo CD.

**New to any of this?** Start with the
[**Zero to Kubernetes** guide](https://mchittineni.github.io/go-web-app-devops/)
— a complete beginner's walkthrough from installing Go to a self-healing GitOps
deployment. Source in [docs/](docs/); run it locally with `make docs`.

For the delivery pipeline and cluster setup, see **[README-DevOps.md](README-DevOps.md)**.

![Website](static/images/golang-website.png)

## What is here

| Path | What it is |
|---|---|
| [main.go](main.go) | The whole server: routing, middleware, embedded assets, graceful shutdown |
| [main_test.go](main_test.go) | Route, security-header, probe and shutdown tests |
| [static/](static/) | HTML pages plus the shared `app.css` and `app.js` |
| [hack/gen_pages.py](hack/gen_pages.py) | Regenerates the HTML pages from one shared shell |
| [Dockerfile](Dockerfile) | Multi-stage build onto `distroless/static:nonroot` |
| [k8s/manifests/](k8s/manifests/) | Plain Kubernetes manifests |
| [helm/go-web-app-chart/](helm/go-web-app-chart/) | The Helm chart used for real deployments |
| [.github/workflows/cicd.yaml](.github/workflows/cicd.yaml) | The pipeline |
| [docs/](docs/) | The beginner's guide, published to GitHub Pages |
| [mkdocs.yml](mkdocs.yml) | Docs site configuration |

## Running it

Requires **Go 1.26+**.

```bash
go run .
# or
make run
```

Then open <http://localhost:8080/home>. `/` redirects there.

### Routes

| Route | Purpose |
|---|---|
| `/home`, `/courses`, `/about`, `/contact` | The pages |
| `/static/*` | CSS, JS and images |
| `/healthz` | Liveness — the process is answering |
| `/readyz` | Readiness — also verifies the embedded assets resolve |
| `/version` | Build version and commit |

### Configuration

Everything is optional; the defaults are what production runs.

| Variable | Default | Purpose |
|---|---|---|
| `LISTEN_ADDR` | `:8080` | Address to bind |
| `LOG_LEVEL` | `info` | `debug`, `info`, `warn` or `error` |

## Common tasks

```bash
make help      # list every target
make test      # tests with the race detector + coverage
make lint      # golangci-lint, same config as CI
make vuln      # govulncheck
make docker    # build the container image
make verify    # everything CI checks
```

## How it is built

A few decisions worth knowing before you change something:

- **No dependencies.** `go.mod` has no `require` block and there is no
  `go.sum`. Routing uses `net/http`'s method-aware `ServeMux` patterns
  (`GET /home`), added in Go 1.22.
- **Assets are compiled in.** `//go:embed static` puts the HTML, CSS, JS and
  images inside the binary. Nothing is read from disk at runtime, which is why
  the container can run with `readOnlyRootFilesystem: true` and why the runtime
  image needs nothing but the binary.
- **The pages are generated.** `static/*.html` share one shell (nav, footer,
  command palette) produced by `hack/gen_pages.py`. Edit the generator, run
  `make pages`, and commit both.
- **CSS and JS are separate files, not inline.** The server sends a strict
  `Content-Security-Policy` with no `unsafe-inline`. Inline `<style>` blocks and
  `style="..."` attributes will be blocked by the browser — use a class in
  `app.css` instead. A test asserts the CSP has no unsafe directives.
- **The frontend degrades.** Every page is fully readable and navigable with
  JavaScript disabled. `app.js` only adds the theme toggle, command palette
  (<kbd>⌘K</kbd>), scroll reveals, counters and the background canvas — and it
  turns all of it off under `prefers-reduced-motion`.
- **Shutdown is graceful.** `SIGTERM` drains in-flight requests for up to 15s,
  which is what makes zero-downtime rolling updates actually zero-downtime.

## Credits

Content and original project by
[Abhishek Veeramalla](https://github.com/iam-veeramalla). The full free DevOps
course is on
[YouTube](https://www.youtube.com/playlist?list=PLdpzxOOAlwvIKMhk8WhzN1pYoJ1YU8Csa).
