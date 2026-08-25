// Package main implements a small, dependency-free static web application.
//
// The HTML/CSS/JS assets are embedded into the binary with embed.FS, so the
// resulting container image only needs the binary itself — nothing is read
// from the container filesystem at runtime, which lets the pod run with a
// read-only root filesystem.
package main

import (
	"context"
	"embed"
	"errors"
	"fmt"
	"io/fs"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"runtime/debug"
	"strings"
	"syscall"
	"time"
)

//go:embed static
var staticFS embed.FS

// Build metadata, injected at link time:
//
//	go build -ldflags="-X main.version=1.2.3 -X main.commit=$(git rev-parse HEAD)"
var (
	version = "dev"
	commit  = "unknown"
)

// pages maps a public route to the embedded HTML document it serves.
var pages = map[string]string{
	"/home":    "static/home.html",
	"/courses": "static/courses.html",
	"/about":   "static/about.html",
	"/contact": "static/contact.html",
}

const (
	defaultAddr     = ":8080"
	readTimeout     = 10 * time.Second
	writeTimeout    = 30 * time.Second
	idleTimeout     = 120 * time.Second
	headerTimeout   = 5 * time.Second
	shutdownTimeout = 15 * time.Second
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: parseLevel(env("LOG_LEVEL", "info")),
	}))
	slog.SetDefault(logger)

	if err := run(logger); err != nil {
		logger.Error("server exited with error", slog.Any("error", err))
		os.Exit(1)
	}
}

func run(logger *slog.Logger) error {
	srv := &http.Server{
		Addr:              env("LISTEN_ADDR", defaultAddr),
		Handler:           newHandler(logger),
		ReadTimeout:       readTimeout,
		ReadHeaderTimeout: headerTimeout,
		WriteTimeout:      writeTimeout,
		IdleTimeout:       idleTimeout,
		ErrorLog:          slog.NewLogLogger(logger.Handler(), slog.LevelError),
	}

	// Trap SIGINT/SIGTERM so Kubernetes rolling updates drain in-flight
	// requests instead of severing them.
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	errCh := make(chan error, 1)
	go func() {
		logger.Info("server starting",
			slog.String("addr", srv.Addr),
			slog.String("version", version),
			slog.String("commit", commit),
		)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			errCh <- err
		}
		close(errCh)
	}()

	select {
	case err := <-errCh:
		return err
	case <-ctx.Done():
		logger.Info("shutdown signal received, draining connections")
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), shutdownTimeout)
	defer cancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		return fmt.Errorf("graceful shutdown: %w", err)
	}
	logger.Info("server stopped cleanly")
	return nil
}

// newHandler wires the routes and the middleware chain.
func newHandler(logger *slog.Logger) http.Handler {
	mux := http.NewServeMux()

	// Liveness: the process is up and the mux is answering.
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) {
		writeText(w, http.StatusOK, "ok")
	})

	// Readiness: the embedded assets are actually resolvable, so we never
	// take traffic on a binary that would 500 on every page.
	mux.HandleFunc("GET /readyz", func(w http.ResponseWriter, _ *http.Request) {
		if err := checkAssets(); err != nil {
			logger.Error("readiness check failed", slog.Any("error", err))
			writeText(w, http.StatusServiceUnavailable, "unavailable")
			return
		}
		writeText(w, http.StatusOK, "ready")
	})

	// Build metadata, handy for verifying which image is actually running.
	mux.HandleFunc("GET /version", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.WriteHeader(http.StatusOK)
		_, _ = fmt.Fprintf(w, `{"version":%q,"commit":%q}`+"\n", version, commit)
	})

	for route, file := range pages {
		mux.Handle("GET "+route, servePage(file))
	}

	// CSS/JS/images. The FileServer is scoped to the embedded FS, so path
	// traversal cannot escape into the container filesystem.
	mux.Handle("GET /static/", cacheControl("public, max-age=3600, must-revalidate",
		http.FileServerFS(staticFS)))

	// "/" exactly — keep the historical entrypoint working. Deliberately no
	// catch-all "/" pattern: a method-less catch-all matches every method and
	// would suppress ServeMux's own 405 for things like POST /home. Without
	// it the mux returns 404 for unknown paths and 405 for wrong methods.
	mux.Handle("GET /{$}", http.RedirectHandler("/home", http.StatusFound))

	return recoverPanic(logger, requestLogger(logger, securityHeaders(mux)))
}

func servePage(name string) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, err := staticFS.ReadFile(name)
		if err != nil {
			slog.ErrorContext(r.Context(), "embedded page missing",
				slog.String("page", name), slog.Any("error", err))
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Header().Set("Cache-Control", "public, max-age=300, must-revalidate")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(body)
	})
}

// checkAssets verifies every routed page plus the shared assets are present
// in the embedded filesystem.
func checkAssets() error {
	required := make([]string, 0, 2+len(pages))
	required = append(required, "static/app.css", "static/app.js")
	for _, file := range pages {
		required = append(required, file)
	}
	for _, name := range required {
		if _, err := fs.Stat(staticFS, name); err != nil {
			return fmt.Errorf("missing embedded asset %q: %w", name, err)
		}
	}
	return nil
}

// securityHeaders applies a deny-by-default baseline. The CSP has no
// 'unsafe-inline' because all styles and scripts are served as same-origin
// files rather than inlined into the documents.
func securityHeaders(next http.Handler) http.Handler {
	const csp = "default-src 'self'; " +
		"script-src 'self'; " +
		"style-src 'self'; " +
		"img-src 'self' data:; " +
		"font-src 'self'; " +
		"connect-src 'self'; " +
		"object-src 'none'; " +
		"base-uri 'none'; " +
		"frame-ancestors 'none'; " +
		"form-action 'self'; " +
		"upgrade-insecure-requests"

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		h := w.Header()
		h.Set("Content-Security-Policy", csp)
		h.Set("X-Content-Type-Options", "nosniff")
		h.Set("X-Frame-Options", "DENY")
		h.Set("Referrer-Policy", "strict-origin-when-cross-origin")
		h.Set("Cross-Origin-Opener-Policy", "same-origin")
		h.Set("Cross-Origin-Resource-Policy", "same-origin")
		h.Set("Permissions-Policy", "geolocation=(), microphone=(), camera=(), payment=()")
		// Only assert HSTS when the request actually arrived over TLS,
		// so plain-HTTP local development is not poisoned.
		if r.TLS != nil || strings.EqualFold(r.Header.Get("X-Forwarded-Proto"), "https") {
			h.Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
		}
		next.ServeHTTP(w, r)
	})
}

// statusRecorder captures the response status for access logging.
type statusRecorder struct {
	http.ResponseWriter
	status int
	bytes  int
}

func (s *statusRecorder) WriteHeader(code int) {
	s.status = code
	s.ResponseWriter.WriteHeader(code)
}

func (s *statusRecorder) Write(b []byte) (int, error) {
	if s.status == 0 {
		s.status = http.StatusOK
	}
	n, err := s.ResponseWriter.Write(b)
	s.bytes += n
	return n, err
}

func requestLogger(logger *slog.Logger, next http.Handler) http.Handler {
	// Health probes fire every few seconds; logging them buries real traffic.
	quiet := map[string]bool{"/healthz": true, "/readyz": true}

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rec := &statusRecorder{ResponseWriter: w}
		next.ServeHTTP(rec, r)

		if quiet[r.URL.Path] && rec.status < http.StatusBadRequest {
			return
		}
		logger.LogAttrs(r.Context(), slog.LevelInfo, "http request",
			slog.String("method", r.Method),
			slog.String("path", r.URL.Path),
			slog.Int("status", rec.status),
			slog.Int("bytes", rec.bytes),
			// Milliseconds, not slog.Duration: the latter serialises as raw
			// nanoseconds in JSON, which no log backend graphs usefully.
			slog.Float64("duration_ms", float64(time.Since(start).Microseconds())/1000),
			slog.String("remote_ip", clientIP(r)),
			slog.String("user_agent", r.UserAgent()),
		)
	})
}

func recoverPanic(logger *slog.Logger, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				logger.Error("recovered from panic",
					slog.Any("panic", rec),
					slog.String("path", r.URL.Path),
					slog.String("stack", string(debug.Stack())),
				)
				// Generic message: never leak a stack trace to the client.
				http.Error(w, "internal server error", http.StatusInternalServerError)
			}
		}()
		next.ServeHTTP(w, r)
	})
}

func cacheControl(value string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", value)
		next.ServeHTTP(w, r)
	})
}

func clientIP(r *http.Request) string {
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return host
}

func writeText(w http.ResponseWriter, code int, msg string) {
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.WriteHeader(code)
	_, _ = fmt.Fprintln(w, msg)
}

func env(key, fallback string) string {
	if v, ok := os.LookupEnv(key); ok && v != "" {
		return v
	}
	return fallback
}

func parseLevel(s string) slog.Level {
	var l slog.Level
	if err := l.UnmarshalText([]byte(s)); err != nil {
		return slog.LevelInfo
	}
	return l
}
