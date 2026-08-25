# syntax=docker/dockerfile:1.9

# =============================================================================
# Build stage
#
# Pinned to a specific Go minor release so a new upstream release cannot
# silently change the toolchain under CI. BuildKit cache mounts keep the
# module and build caches warm between runs without baking them into a layer.
# =============================================================================
FROM --platform=$BUILDPLATFORM golang:1.27-bookworm AS build

WORKDIR /src

# Dependency manifests first: this layer only invalidates when they change.
# go.sum is optional today (the app has zero external modules) but is copied
# so adding a dependency does not require editing the Dockerfile.
COPY go.mod go.su[m] ./
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download && go mod verify

COPY . .

# TARGETOS/TARGETARCH are supplied by buildx for each platform in the matrix.
ARG TARGETOS
ARG TARGETARCH
ARG VERSION=dev
ARG COMMIT=unknown

# CGO off + -trimpath + stripped symbols produce a fully static, reproducible
# binary with no absolute paths from the build host embedded in it.
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build \
      -trimpath \
      -buildvcs=false \
      -ldflags="-s -w -X main.version=${VERSION} -X main.commit=${COMMIT}" \
      -o /out/go-web-app .

# =============================================================================
# Runtime stage
#
# distroless/static-debian12 contains no shell, no package manager and no libc
# beyond the static essentials (CA certificates, tzdata, /etc/passwd). The
# :nonroot variant runs as uid/gid 65532. The HTML/CSS/JS are compiled into
# the binary via embed.FS, so nothing needs to be copied here and the pod can
# run with readOnlyRootFilesystem: true.
# =============================================================================
FROM gcr.io/distroless/static-debian12:nonroot AS runtime

ARG VERSION=dev
ARG COMMIT=unknown

# OCI annotations: consumed by registries, `docker inspect`, and Trivy/Syft.
LABEL org.opencontainers.image.title="go-web-app" \
      org.opencontainers.image.description="Static Go web application used to teach end-to-end DevOps." \
      org.opencontainers.image.source="https://github.com/iam-veeramalla/go-web-app-devops" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${COMMIT}" \
      org.opencontainers.image.base.name="gcr.io/distroless/static-debian12:nonroot"

COPY --from=build --chown=65532:65532 /out/go-web-app /usr/local/bin/go-web-app

# 65532 is distroless' "nonroot" user; named numerically so Kubernetes
# runAsNonRoot admission can verify it without resolving /etc/passwd.
USER 65532:65532

EXPOSE 8080

ENV LISTEN_ADDR=":8080" \
    LOG_LEVEL="info"

# No shell in the image, so this must be the exec form.
ENTRYPOINT ["/usr/local/bin/go-web-app"]
