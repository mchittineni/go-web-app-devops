package main

import (
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestPageRoutes(t *testing.T) {
	t.Parallel()
	srv := newHandler(discardLogger())

	for route := range pages {
		t.Run(route, func(t *testing.T) {
			t.Parallel()
			rr := do(t, srv, http.MethodGet, route)

			if rr.Code != http.StatusOK {
				t.Fatalf("status = %d, want %d", rr.Code, http.StatusOK)
			}
			if got, want := rr.Header().Get("Content-Type"), "text/html; charset=utf-8"; got != want {
				t.Errorf("Content-Type = %q, want %q", got, want)
			}
			body := rr.Body.String()
			if !strings.Contains(body, "<!DOCTYPE html>") {
				t.Error("body is missing a valid HTML5 doctype")
			}
			if !strings.Contains(body, `href="/static/app.css"`) {
				t.Error("body does not link the shared stylesheet")
			}
		})
	}
}

func TestSecurityHeaders(t *testing.T) {
	t.Parallel()
	rr := do(t, newHandler(discardLogger()), http.MethodGet, "/home")

	want := map[string]string{
		"X-Content-Type-Options": "nosniff",
		"X-Frame-Options":        "DENY",
		"Referrer-Policy":        "strict-origin-when-cross-origin",
	}
	for header, value := range want {
		if got := rr.Header().Get(header); got != value {
			t.Errorf("%s = %q, want %q", header, got, value)
		}
	}

	csp := rr.Header().Get("Content-Security-Policy")
	if csp == "" {
		t.Fatal("Content-Security-Policy header is absent")
	}
	// An inline-script escape hatch would defeat the point of the policy.
	if strings.Contains(csp, "unsafe-inline") || strings.Contains(csp, "unsafe-eval") {
		t.Errorf("CSP contains an unsafe directive: %q", csp)
	}
	for _, directive := range []string{"default-src 'self'", "object-src 'none'", "frame-ancestors 'none'"} {
		if !strings.Contains(csp, directive) {
			t.Errorf("CSP is missing %q; got %q", directive, csp)
		}
	}
}

func TestHSTSOnlyOverTLS(t *testing.T) {
	t.Parallel()
	srv := newHandler(discardLogger())

	if got := do(t, srv, http.MethodGet, "/home").Header().Get("Strict-Transport-Security"); got != "" {
		t.Errorf("plain HTTP should not set HSTS, got %q", got)
	}

	req := httptest.NewRequestWithContext(t.Context(), http.MethodGet, "/home", nil)
	req.Header.Set("X-Forwarded-Proto", "https")
	rr := httptest.NewRecorder()
	srv.ServeHTTP(rr, req)

	if got := rr.Header().Get("Strict-Transport-Security"); !strings.Contains(got, "max-age=") {
		t.Errorf("HTTPS request should set HSTS, got %q", got)
	}
}

func TestProbes(t *testing.T) {
	t.Parallel()
	srv := newHandler(discardLogger())

	for _, path := range []string{"/healthz", "/readyz"} {
		if rr := do(t, srv, http.MethodGet, path); rr.Code != http.StatusOK {
			t.Errorf("%s = %d, want %d", path, rr.Code, http.StatusOK)
		}
	}
}

func TestReadinessValidatesEmbeddedAssets(t *testing.T) {
	t.Parallel()
	if err := checkAssets(); err != nil {
		t.Fatalf("embedded assets incomplete: %v", err)
	}
}

func TestVersionEndpoint(t *testing.T) {
	t.Parallel()
	rr := do(t, newHandler(discardLogger()), http.MethodGet, "/version")

	if rr.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d", rr.Code, http.StatusOK)
	}
	var payload struct {
		Version string `json:"version"`
		Commit  string `json:"commit"`
	}
	if err := json.Unmarshal(rr.Body.Bytes(), &payload); err != nil {
		t.Fatalf("response is not valid JSON: %v", err)
	}
	if payload.Version == "" || payload.Commit == "" {
		t.Errorf("version payload is incomplete: %+v", payload)
	}
}

func TestRootRedirectsToHome(t *testing.T) {
	t.Parallel()
	rr := do(t, newHandler(discardLogger()), http.MethodGet, "/")

	if rr.Code != http.StatusFound {
		t.Fatalf("status = %d, want %d", rr.Code, http.StatusFound)
	}
	if got := rr.Header().Get("Location"); got != "/home" {
		t.Errorf("Location = %q, want %q", got, "/home")
	}
}

func TestUnknownPathReturns404(t *testing.T) {
	t.Parallel()
	if rr := do(t, newHandler(discardLogger()), http.MethodGet, "/nope"); rr.Code != http.StatusNotFound {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusNotFound)
	}
}

func TestNonGETMethodIsRejected(t *testing.T) {
	t.Parallel()
	rr := do(t, newHandler(discardLogger()), http.MethodPost, "/home")

	if rr.Code != http.StatusMethodNotAllowed {
		t.Errorf("POST /home = %d, want %d", rr.Code, http.StatusMethodNotAllowed)
	}
}

func TestStaticAssetsAreServed(t *testing.T) {
	t.Parallel()
	srv := newHandler(discardLogger())

	for _, asset := range []string{"/static/app.css", "/static/app.js"} {
		rr := do(t, srv, http.MethodGet, asset)
		if rr.Code != http.StatusOK {
			t.Errorf("%s = %d, want %d", asset, rr.Code, http.StatusOK)
		}
		if rr.Header().Get("Cache-Control") == "" {
			t.Errorf("%s is missing a Cache-Control header", asset)
		}
	}
}

// A traversal attempt must not escape the embedded filesystem.
func TestStaticPathTraversalIsBlocked(t *testing.T) {
	t.Parallel()
	rr := do(t, newHandler(discardLogger()), http.MethodGet, "/static/../../etc/passwd")

	if rr.Code == http.StatusOK && strings.Contains(rr.Body.String(), "root:") {
		t.Fatal("path traversal escaped the embedded filesystem")
	}
}

func TestPanicIsRecovered(t *testing.T) {
	t.Parallel()
	boom := http.HandlerFunc(func(http.ResponseWriter, *http.Request) {
		panic("boom")
	})
	rr := httptest.NewRecorder()
	recoverPanic(discardLogger(), boom).ServeHTTP(rr,
		httptest.NewRequestWithContext(t.Context(), http.MethodGet, "/", nil))

	if rr.Code != http.StatusInternalServerError {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusInternalServerError)
	}
	// A stack trace must never reach the client.
	if strings.Contains(rr.Body.String(), "goroutine") {
		t.Error("response body leaked a stack trace")
	}
}

func TestEnvFallback(t *testing.T) {
	if got := env("GO_WEB_APP_UNSET_KEY", "fallback"); got != "fallback" {
		t.Errorf("env() = %q, want %q", got, "fallback")
	}
	t.Setenv("GO_WEB_APP_TEST_KEY", "set")
	if got := env("GO_WEB_APP_TEST_KEY", "fallback"); got != "set" {
		t.Errorf("env() = %q, want %q", got, "set")
	}
	t.Setenv("GO_WEB_APP_TEST_KEY", "")
	if got := env("GO_WEB_APP_TEST_KEY", "fallback"); got != "fallback" {
		t.Errorf("empty env var should fall back, got %q", got)
	}
}

func TestGracefulShutdown(t *testing.T) {
	srv := &http.Server{Handler: newHandler(discardLogger())}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		t.Fatalf("Shutdown() = %v, want nil", err)
	}
}

func BenchmarkHomePage(b *testing.B) {
	srv := newHandler(discardLogger())
	req := httptest.NewRequestWithContext(b.Context(), http.MethodGet, "/home", nil)

	for b.Loop() {
		srv.ServeHTTP(httptest.NewRecorder(), req)
	}
}

func do(tb testing.TB, h http.Handler, method, target string) *httptest.ResponseRecorder {
	tb.Helper()
	rr := httptest.NewRecorder()
	h.ServeHTTP(rr, httptest.NewRequestWithContext(tb.Context(), method, target, nil))
	return rr
}

// discardLogger keeps test output readable — the handlers log every request.
func discardLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}
