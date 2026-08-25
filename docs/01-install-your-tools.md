# Part 01 · Install your tools

Five tools. Install them all now so nothing interrupts you later. Every command
in this guide is typed into a **terminal**.

## Opening a terminal

- **macOS** — press ++cmd+space++, type "Terminal", press ++enter++.
- **Windows** — install [WSL2](https://learn.microsoft.com/windows/wsl/install)
  and use the Ubuntu terminal. Everything in this guide assumes Linux/macOS
  commands, and WSL2 gives you those on Windows.
- **Linux** — you already know.

## Install the tools

=== "macOS"

    [Homebrew](https://brew.sh) installs everything:

    ```bash title="terminal — anywhere"
    brew install go git helm kubectl
    brew install --cask docker
    ```

=== "Ubuntu / WSL2"

    ```bash title="terminal — anywhere"
    # Git and Docker
    sudo apt update && sudo apt install -y git docker.io
    sudo usermod -aG docker $USER   # then log out and back in

    # Go — check go.dev/dl for the current version first
    curl -LO https://go.dev/dl/go1.27.0.linux-amd64.tar.gz
    sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go1.27.0.linux-amd64.tar.gz
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc && source ~/.bashrc

    # kubectl and Helm
    sudo snap install kubectl --classic
    sudo snap install helm --classic
    ```

## Verify every one of them

Do not skip this. A missing tool produces a confusing error ten minutes later,
and you will blame the wrong thing.

```bash title="terminal — anywhere"
go version
git --version
docker --version
kubectl version --client
helm version --short
```

You should see five version numbers, something like:

```text
go version go1.27.0 darwin/arm64
git version 2.43.0
Docker version 27.4.0, build bde2b89
Client Version: v1.32.0
v3.19.0+g3d8990f
```

!!! warning "If Docker says \"cannot connect to the daemon\""

    Docker has two halves: the `docker` command and a background service called
    the *daemon*. The command is installed but the service is not running.

    - **macOS** — open Docker Desktop from Applications and wait for its whale
      icon to stop animating.
    - **Linux** — run `sudo systemctl start docker`.

!!! note "On version numbers"

    This project needs **Go 1.26 or newer**. Older versions will fail to build
    with a message about the `go.mod` file. The other tools are relaxed — any
    recent version works.

!!! success "Checkpoint"

    All five commands print a version number and none of them print
    "command not found".
