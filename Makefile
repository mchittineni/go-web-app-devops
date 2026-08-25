# go-web-app — developer entrypoints.
# Every target here is also what CI runs, so "it passes locally" means
# something.

SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

APP         := go-web-app
IMAGE       ?= $(APP)
VERSION     ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo dev)
COMMIT      ?= $(shell git rev-parse HEAD 2>/dev/null || echo unknown)
LDFLAGS     := -s -w -X main.version=$(VERSION) -X main.commit=$(COMMIT)
CHART       := helm/go-web-app-chart
PLATFORMS   ?= linux/amd64,linux/arm64

.PHONY: help
help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

## --- Application ----------------------------------------------------------

.PHONY: run
run: ## Run the server locally on :8080
	go run .

.PHONY: build
build: ## Build the binary into bin/
	CGO_ENABLED=0 go build -trimpath -ldflags="$(LDFLAGS)" -o bin/$(APP) .

.PHONY: pages
pages: ## Regenerate the static HTML from the shared shell
	python3 hack/gen_pages.py

.PHONY: fmt
fmt: ## Format the code
	gofmt -w .

.PHONY: vet
vet: ## Run go vet
	go vet ./...

.PHONY: lint
lint: ## Run golangci-lint (matches CI)
	golangci-lint run

.PHONY: test
test: ## Run tests with the race detector
	go test -race -shuffle=on -covermode=atomic -coverprofile=coverage.out ./...
	@go tool cover -func=coverage.out | tail -n 1

.PHONY: cover
cover: test ## Open the HTML coverage report
	go tool cover -html=coverage.out -o coverage.html
	@echo "wrote coverage.html"

.PHONY: bench
bench: ## Run benchmarks
	go test -bench=. -benchmem -run=^$$ ./...

## --- Security -------------------------------------------------------------

.PHONY: vuln
vuln: ## Scan for known vulnerabilities (matches CI)
	go run golang.org/x/vuln/cmd/govulncheck@latest ./...

.PHONY: scan
scan: ## Trivy scan of the repo and the built image
	trivy fs --scanners vuln,secret,misconfig --severity CRITICAL,HIGH .
	trivy image --severity CRITICAL,HIGH --ignore-unfixed $(IMAGE):$(VERSION)

## --- Container ------------------------------------------------------------

.PHONY: docker
docker: ## Build the image for the local platform
	docker build \
	  --build-arg VERSION=$(VERSION) \
	  --build-arg COMMIT=$(COMMIT) \
	  -t $(IMAGE):$(VERSION) -t $(IMAGE):latest .

.PHONY: docker-multi
docker-multi: ## Build the multi-arch image (requires buildx)
	docker buildx build --platform=$(PLATFORMS) \
	  --build-arg VERSION=$(VERSION) \
	  --build-arg COMMIT=$(COMMIT) \
	  -t $(IMAGE):$(VERSION) .

.PHONY: docker-run
docker-run: docker ## Run the image on :8080
	docker run --rm -p 8080:8080 \
	  --read-only --cap-drop=ALL --security-opt=no-new-privileges \
	  $(IMAGE):$(VERSION)

## --- Kubernetes -----------------------------------------------------------

.PHONY: helm-lint
helm-lint: ## Lint the chart
	helm lint $(CHART) --strict

.PHONY: helm-template
helm-template: ## Render the chart to stdout
	helm template $(APP) $(CHART)

.PHONY: helm-validate
helm-validate: helm-lint ## Render and validate against Kubernetes schemas
	helm template $(APP) $(CHART) | kubeconform -strict -summary -ignore-missing-schemas
	kubeconform -strict -summary k8s/manifests/

.PHONY: helm-install
helm-install: ## Install or upgrade the release
	helm upgrade --install $(APP) $(CHART) --atomic --timeout 3m

.PHONY: helm-test
helm-test: ## Run the chart's connection test
	helm test $(APP)

.PHONY: k8s-apply
k8s-apply: ## Apply the raw manifests
	kubectl apply -f k8s/manifests/

## --- Documentation --------------------------------------------------------

.PHONY: docs-install
docs-install: ## Install the docs site dependencies
	pip install -r requirements-docs.txt

.PHONY: docs
docs: ## Serve the docs site locally with live reload on :8000
	mkdocs serve

.PHONY: docs-build
docs-build: ## Build the docs site exactly as CI does
	mkdocs build --strict

## --- Housekeeping ---------------------------------------------------------

.PHONY: verify
verify: fmt vet lint test helm-validate ## Everything CI checks, in one go

.PHONY: clean
clean: ## Remove build artefacts
	rm -rf bin dist site coverage.out coverage.html
