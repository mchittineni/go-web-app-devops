# Glossary

Every term in this guide, in one place.

Binary
:   A compiled, runnable program. Go produces one file; that file is the binary.

Image
:   A sealed, immutable package containing a program and everything it needs to run.

Container
:   A running instance of an image. One image can produce many containers.

Registry
:   Storage for images, so other machines can download them. Docker Hub is one.

Tag
:   A human-readable label on an image, like `latest`. Tags can be moved to point at different images, which is why production pins digests instead.

Digest
:   A cryptographic fingerprint of an exact image, like `sha256:9f86d0…`. Cannot be reused for different content, so it is unambiguous.

Distroless
:   A base image with no shell or package manager — only what is needed to run one program.

Pod
:   The smallest thing Kubernetes runs: one or more containers that live and die together.

Deployment
:   Instructions to keep N identical pods running and to replace them safely on update.

Service
:   A stable internal network address that spreads traffic across pods.

Ingress
:   A rule routing outside traffic to a Service, usually by hostname and path.

Namespace
:   A way of grouping resources so unrelated things do not collide.

Manifest
:   A YAML file describing something you want Kubernetes to create.

Declarative
:   Describing the desired end state and letting the system reach it, instead of listing the steps yourself.

Probe
:   A periodic health check Kubernetes runs against your container. Liveness triggers restarts; readiness controls traffic.

HPA
:   Horizontal Pod Autoscaler — adds and removes pods based on load.

PDB
:   Pod Disruption Budget — a floor on how many pods must stay up during planned maintenance.

Chart
:   A Helm package: templated Kubernetes manifests plus their default values.

Release
:   One installed instance of a chart in a cluster, with a name and a version history.

CI / CD
:   Continuous Integration (automatically test every change) and Continuous Delivery (automatically prepare it for release).

Pipeline
:   The sequence of automated jobs a change must pass through.

Linter
:   A tool that flags suspicious or risky code the compiler still accepts.

SBOM
:   Software Bill of Materials — a complete parts list of everything inside an artifact, so you can tell instantly whether a new vulnerability affects you.

CVE
:   A publicly catalogued security vulnerability, with an identifier like `CVE-2024-1234`.

Keyless signing
:   Proving an artifact's origin using a short-lived identity from the build system, so there is no long-lived signing key to steal.

GitOps
:   Using Git as the only source of truth for what is deployed, with software continuously reconciling the cluster to match it.

Reconcile
:   Compare desired state to actual state and fix the difference. The core loop of both Kubernetes and Argo CD.

Drift
:   When reality no longer matches what is written down — usually because someone changed something by hand.

## Where to go next

- **Read the repo's own docs.** `README.md` covers the app; `README-DevOps.md`
  covers the pipeline in depth; `SECURITY.md` explains every hardening decision.
- **Break things deliberately.** Set a memory limit of `1Mi` and watch
  `OOMKilled`. Point at a non-existent image and read the error. Deliberate
  failure teaches faster than success.
- **Add something.** A new page is the smallest useful change that travels the
  entire pipeline you just learned.
