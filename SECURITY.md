# Security

## Reporting a vulnerability

Report privately via
[GitHub Security Advisories](https://github.com/iam-veeramalla/go-web-app-devops/security/advisories/new)
rather than opening a public issue. Please include what you did, what happened,
and the affected version or image digest.

## What is enforced automatically

Every push and pull request runs, and fails on:

- `govulncheck` — known CVEs in the Go standard library and module graph,
  filtered to code paths this binary actually reaches
- `gosec` via golangci-lint — security-focused static analysis
- Trivy — filesystem, config and image scanning at CRITICAL/HIGH
- gitleaks — committed secrets
- `kubeconform` and Trivy config — manifest and Dockerfile misconfiguration

Findings are uploaded to GitHub code scanning as SARIF. Dependabot opens weekly
update PRs for Go modules, GitHub Actions and base images. A scheduled Monday
run re-scans unchanged code, because CVEs get published against code that has
not moved.

## Supply chain

Published images are signed with keyless [Cosign](https://docs.sigstore.dev/)
using the workflow's GitHub OIDC identity, and carry a CycloneDX SBOM
attestation plus SLSA build provenance.

```bash
cosign verify docker.io/<user>/go-web-app:<tag> \
  --certificate-identity-regexp='.*/go-web-app-devops/.*' \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com
```

Deployments are pinned by image digest, not by tag, so a re-pushed tag cannot
change what is running.

## Application posture

The app has no authentication, no database, no user input and no outbound
network calls — it serves static content embedded in the binary. That removes
most of the OWASP Top 10 by construction. What remains is handled as follows:

| Concern | Control |
|---|---|
| XSS | Strict CSP with no `unsafe-inline` / `unsafe-eval`; a test fails the build if either appears. All DOM writes in `app.js` use `textContent`, never `innerHTML` |
| Clickjacking | `X-Frame-Options: DENY` and `frame-ancestors 'none'` |
| MIME sniffing | `X-Content-Type-Options: nosniff` |
| Referrer leakage | `Referrer-Policy: strict-origin-when-cross-origin` |
| Transport | HSTS, asserted only when the request actually arrived over TLS |
| Path traversal | Files are served from an embedded `fs.FS`; there is no container filesystem to escape into |
| Slowloris / resource exhaustion | Explicit `ReadHeaderTimeout`, `ReadTimeout`, `WriteTimeout` and `IdleTimeout` on the server |
| Information disclosure | Panics are recovered, logged server-side, and answered with a generic 500 — stack traces never reach a client |
| Cross-origin isolation | `Cross-Origin-Opener-Policy` and `Cross-Origin-Resource-Policy: same-origin` |

## Runtime posture

See the control table in [README-DevOps.md](README-DevOps.md). In short: no
shell in the image, non-root uid 65532, read-only root filesystem, all
capabilities dropped, no privilege escalation, `RuntimeDefault` seccomp, no
service-account token mounted, and an optional default-deny NetworkPolicy.

## Remediation targets

| Severity | Target |
|---|---|
| Critical (CVSS ≥ 9.0, internet-facing) | 24 hours |
| High (7.0–8.9) | 7 days |
| Medium (4.0–6.9) | 30 days |
| Low (< 4.0) | 90 days |
