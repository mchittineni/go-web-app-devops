# Part 07 · Automate it with CI/CD

Everything so far, you typed. Now robots do it on every push. This is the part
that turns a hobby project into engineering.

Two initials worth splitting apart:

- **CI** (Continuous Integration) — on every push, check the code: does it
  build, do the tests pass, is it secure?
- **CD** (Continuous Delivery) — if the checks pass, build the image and get it
  ready to deploy.

The instructions live in `.github/workflows/cicd.yaml`. GitHub reads that file
automatically — there is nothing to install.

## The six jobs, in order

| # | Job | What it refuses to let through |
|---|---|---|
| 1 | **build** | Badly formatted code, failing tests, race conditions |
| 2 | **lint** | Suspicious patterns and likely bugs a compiler allows |
| 3 | **security** | Known vulnerabilities, and passwords committed by accident |
| 4 | **manifests** | Kubernetes files that are invalid or insecurely configured |
| 5 | **image** | Builds, scans and cryptographically *signs* the image |
| 6 | **deploy** | Records the new version in Git for Argo CD to pick up |

The order is deliberate: cheap checks fail in seconds, and nothing is published
to a registry until all four earlier gates pass.

## Set up your own copy

You need a Docker Hub account (free) and your own GitHub fork.

### 1. Create a Docker Hub access token

Log in at [hub.docker.com](https://hub.docker.com) → *Account Settings* →
*Personal access tokens* → create one with **Read & Write**. Copy it now; it is
shown once.

!!! warning "Use a token, never your password"

    A token can be scoped and revoked without changing your login, and if it
    leaks it cannot be used to take over your account. Never paste a password
    into a CI system.

### 2. Add the secrets to GitHub

In your fork: *Settings* → *Secrets and variables* → *Actions* →
*New repository secret*. Add two:

| Name | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | The token you just copied |

Secrets are write-only — even you cannot read them back, and they are masked in
logs.

### 3. Push a change and watch

```bash title="terminal — in the project folder"
git checkout -b my-first-change
# edit something in static/home.html, then:
git add .
git commit -m "Change the homepage headline"
git push -u origin my-first-change
```

Open the *Actions* tab on GitHub. You will watch the jobs run in real time.
Click any job to expand its output.

!!! note "A red X is a success"

    A failing pipeline did its job — it caught something before a user did.
    Click the failed job, scroll to the first red line, and read it. CI errors
    are usually far more specific than they look.

## What "signing" means and why you should care

The `image` job does two things beyond building. It generates an **SBOM** — a
complete parts list of everything inside the image — and it **signs** the image
cryptographically.

The signature answers a question you cannot otherwise answer: *was this image
really built by my pipeline from my code, or did someone replace it?* Anyone can
verify it:

```bash title="terminal — optional, needs cosign"
cosign verify docker.io/YOUR_USERNAME/go-web-app:latest \
  --certificate-identity-regexp='.*/go-web-app-devops/.*' \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com
```

No signing key was ever created or stored. The pipeline proves its own identity
to a public transparency log at build time. This is called *keyless signing*,
and it is the current standard for supply-chain security.

## Run the same gates locally

Never guess whether CI will pass. Ask it first:

```bash title="terminal — in the project folder"
make verify
```

!!! success "Checkpoint"

    - Both secrets are saved in your fork.
    - You pushed a branch and watched the Actions tab.
    - An image appeared in your Docker Hub account.
