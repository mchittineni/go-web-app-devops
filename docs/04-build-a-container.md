# Part 04 · Put it in a container

A container is your program plus its entire environment, sealed in a box that
behaves identically everywhere. The recipe for the box is the `Dockerfile`.

## Two words people mix up

- An **image** is the sealed box sitting on a shelf. It does nothing.
- A **container** is a running copy of an image. One image, many containers.

Think class and instance, or recipe and meal.

## Build the image

Make sure Docker Desktop is running, then:

```bash title="terminal — in the project folder"
make docker
```

The first run takes a couple of minutes as it downloads the Go compiler image.
Watch the output — each `=>` line is one step of the recipe. When it finishes:

```bash title="terminal — in the project folder"
docker images go-web-app
```

```text
REPOSITORY   TAG      SIZE
go-web-app   latest   ~11MB
```

## Why it is 11MB and not 900MB

This is the single most instructive thing in the whole project. The `Dockerfile`
has **two stages**:

1. **The build stage** starts from the full Go toolchain — about 800MB of
   compiler, linker and standard library. It compiles your code into one
   executable file.
2. **The runtime stage** starts from scratch and copies in *only that
   executable*. The 800MB of build tools is thrown away.

The runtime base image is called `distroless`, and it contains no shell, no
package manager, and no utilities — nothing but the minimum needed to run a
program. So if an attacker ever finds a way to execute commands in your
container, there are no commands to execute. There is no `bash`, no `curl`,
no `ls`.

!!! note "Why this pattern is everywhere"

    Every megabyte in an image is a megabyte to transfer to every server, and
    every program in it is something that can have a security flaw. Small images
    deploy faster *and* have less to attack. Two-stage builds get you both for
    free.

## Run the container

```bash title="terminal — in the project folder"
make docker-run
```

Visit [localhost:8080/home](http://localhost:8080/home) again. Identical site —
but now it is running inside a sealed, read-only box with no privileges. Stop it
with ++ctrl+c++.

That command applies real restrictions. Each flag removes a capability:

| Flag | What it prevents |
|---|---|
| `--read-only` | Writing anything to disk, ever |
| `--cap-drop=ALL` | All special Linux privileges |
| `--security-opt=no-new-privileges` | Gaining privileges after start |

A normal application would break under all three. This one does not, because of
the embedding trick from [Part 03](03-read-the-code.md).

!!! success "Checkpoint"

    - `docker images` shows your image at roughly 11MB.
    - The site loads from the container.
    - You can explain why the image is small — the two stages.
