# Part 02 · Get the code and run the website

The fastest possible win: in three commands you will have the site running on
your own machine.

```bash title="terminal — anywhere"
git clone https://github.com/mchittineni/go-web-app-devops.git
cd go-web-app-devops
go run .
```

You should see a line of JSON appear and then nothing else:

```json
{"time":"2026-08-25T15:34:55Z","level":"INFO","msg":"server starting","addr":":8080","version":"dev","commit":"unknown"}
```

The terminal now looks frozen. It is not — the program is running and waiting
for visitors. Leave it alone and open
[http://localhost:8080/home](http://localhost:8080/home) in your browser.

!!! note "What \"localhost:8080\" means"

    `localhost` means "this computer". `8080` is the *port* — think of it as an
    apartment number, so several programs can accept visitors on one machine
    without collisions. The site is not on the internet; only you can reach it.

To stop the server, click the terminal and press ++ctrl+c++. You will see it
shut down deliberately rather than just vanishing:

```json
{"level":"INFO","msg":"shutdown signal received, draining connections"}
{"level":"INFO","msg":"server stopped cleanly"}
```

That "draining" step matters later. It is what lets Kubernetes replace this
program mid-request without anyone seeing an error.

## What is in the folder

Run `ls` and you will see this. Ignore most of it for now:

| Path | What it is | Part |
|---|---|---|
| `main.go` | The entire web server | 03 |
| `main_test.go` | Automated tests for it | 03 |
| `static/` | The HTML, CSS and JavaScript | 03 |
| `Dockerfile` | Recipe for building the container image | 04 |
| `k8s/manifests/` | Kubernetes files, written out longhand | 05 |
| `helm/` | The same thing as a reusable template | 06 |
| `.github/workflows/` | The robots | 07 |
| `gitops/` | Argo CD setup | 09 |
| `Makefile` | Shortcuts for all of the above | — |

## The Makefile is your cheat sheet

Rather than memorising long commands, run:

```bash title="terminal — in the project folder"
make help
```

Every shortcut it lists is exactly what the automated pipeline runs, so "it
passed on my machine" genuinely means something.

!!! success "Checkpoint"

    - The site loads at `localhost:8080/home` and you can click between all four pages.
    - ++ctrl+c++ stops it and prints "server stopped cleanly".
    - `make help` prints a list of commands.
