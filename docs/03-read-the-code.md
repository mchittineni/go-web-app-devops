# Part 03 · Read the code (you only need four ideas)

You do not need to learn Go. You need to recognise four things in `main.go`,
because every later part depends on them.

## Idea 1 — Routes: a URL maps to a function

Somewhere in `main.go` there is a list pairing URLs with files. When a browser
asks for `/courses`, the server sends back `static/courses.html`. That is the
whole website.

| URL | What it returns |
|---|---|
| `/home` `/courses` `/about` `/contact` | The four pages |
| `/static/…` | CSS, JavaScript, images |
| `/healthz` | The word `ok` — "I am alive" |
| `/readyz` | `ready` — "I am alive *and* able to serve pages" |
| `/version` | Which build is running |

## Idea 2 — The HTML lives *inside* the program

One line near the top of `main.go` does something unusual:

```go title="main.go — read only, don't type this"
//go:embed static
var staticFS embed.FS
```

That instruction tells Go: *copy the entire* `static/` *folder into the compiled
program itself.* The finished binary contains the HTML, the CSS, the JavaScript
and the images.

Three consequences you will meet later:

- The container image needs nothing except the binary — no web server, no files to copy.
- The running container can have a **completely read-only filesystem**, because
  nothing is ever read from disk. That removes an entire category of attack.
- If you edit a file in `static/`, you must rebuild for the change to appear.

## Idea 3 — Health endpoints exist for Kubernetes, not for you

`/healthz` and `/readyz` look pointless now. In
[Part 05](05-your-first-cluster.md) Kubernetes will call them every few seconds:

- **Liveness** (`/healthz`): "are you alive?" If this stops answering,
  Kubernetes kills and restarts the container.
- **Readiness** (`/readyz`): "should I send you visitors?" If this says no,
  Kubernetes stops sending traffic but leaves the container running.

The distinction is the difference between a restart and a quiet withdrawal from
the load balancer. Here, `/readyz` actually checks the embedded pages are
present — so a broken build never receives a single visitor.

## Idea 4 — It shuts down on purpose

When Kubernetes wants a container gone it sends a polite signal called
`SIGTERM` and waits. This program catches it, finishes the requests already in
flight (up to 15 seconds), then exits. That is why updating the site causes zero
failed requests.

## Run the tests

Tests are code that checks your code. Run them — this is the same command the
robots run in [Part 07](07-automate-with-cicd.md):

```bash title="terminal — in the project folder"
make test
```

```text
ok  github.com/iam-veeramalla/go-web-app-devops  1.399s  coverage: 66.0% of statements
```

The word `ok` is what you want. "coverage" is the share of lines the tests
actually executed.

## Make your first change

Open `static/home.html` in any editor, change some visible text, save, then:

```bash title="terminal — in the project folder"
go run .
```

Reload the page. Your text is there. You just did the "I changed a file" end of
the journey; the rest of this guide is the other end.

!!! warning "One rule if you edit the pages"

    The server sends a strict security policy that **blocks inline styles and
    scripts**. A `style="…"` attribute or a `<style>` block will be silently
    ignored by the browser. Put styling in `static/app.css` and use a class
    instead. A test will fail the build if this rule is weakened.

!!! success "Checkpoint"

    - `make test` prints `ok`.
    - You changed text in a page and saw it in your browser.
    - You can explain why `/readyz` is different from `/healthz`.
