---
title: Start here
---

# Zero to Kubernetes

You have never written Go, built a container, or touched a cluster. By the end
of this guide you will have done all three — and shipped a website that deploys
itself.

| | |
|---|---|
| **Prior knowledge** | None. You can type commands. |
| **Time** | ~3 hours, spread over parts |
| **Cost** | Free through Part 07 |
| **Project** | `go-web-app-devops` |

## The map: what you are actually building

Before any commands, spend four minutes here. Almost everyone who gets lost
later got lost because they skipped this page and started copying commands
without knowing what they were for.

There is **one website** in this project. It is small on purpose: four pages
about learning DevOps. The website is not the point. The point is everything
that happens between "I changed a file" and "the change is live on the
internet."

That journey has six stages, and each stage is one tool:

```mermaid
flowchart LR
    A["<b>Go</b><br/><small>your code</small>"] --> B["<b>Docker</b><br/><small>one image</small>"]
    B --> C["<b>Kubernetes</b><br/><small>runs copies</small>"]
    C --> D["<b>Helm</b><br/><small>reusable recipe</small>"]
    D --> E["<b>GitHub Actions</b><br/><small>checks + builds</small>"]
    E --> F["<b>Argo CD</b><br/><small>keeps cluster = Git</small>"]
    F --> G(["live website"])
```

### What each word means, in one sentence

| Word | The one-sentence version | Why this project uses it |
|---|---|---|
| **Go** | A programming language that compiles your source into one single executable file. | That single file has no dependencies, which makes every later step simpler. |
| **Docker** | Packs your program plus everything it needs into a sealed box called an *image*. | The image runs identically on your laptop and on a server. "Works on my machine" stops being a problem. |
| **Kubernetes** | Runs your images across many machines, restarts them when they die, and replaces them one at a time when you update. | It is how you get a site that stays up while you deploy to it. |
| **Helm** | A template engine for Kubernetes files, so one recipe serves dev, staging and production. | Stops you copy-pasting near-identical YAML files and letting them drift apart. |
| **GitHub Actions** | Robots that run your tests and build your image every time you push code. | Catches your mistake before a user does. |
| **Argo CD** | Watches your Git repository and makes the cluster match it. | Git becomes the single record of what is deployed. No one deploys by hand. |

!!! note "The one idea to hold on to"

    Every tool here exists to remove a human from a step where humans make
    mistakes. Go removes "did you install the right library?" Docker removes
    "it worked on my laptop." Kubernetes removes "who restarts it at 3am?"
    Argo CD removes "who ran the deploy, and what did they actually deploy?"

!!! success "Checkpoint"

    You can say out loud, without looking, what Docker does and what Kubernetes
    does — and why they are two different things. That is enough. Everything
    else you will learn by doing.

## The path

<div class="gwa-grid" markdown>

<a class="gwa-card" href="01-install-your-tools/"><span class="n">PART 01</span><strong>Install your tools</strong><span class="d">Five tools, then verify every one</span></a>

<a class="gwa-card" href="02-run-the-website/"><span class="n">PART 02</span><strong>Run the website</strong><span class="d">Three commands to your first win</span></a>

<a class="gwa-card" href="03-read-the-code/"><span class="n">PART 03</span><strong>Read the code</strong><span class="d">The only four ideas you need</span></a>

<a class="gwa-card" href="04-build-a-container/"><span class="n">PART 04</span><strong>Build a container</strong><span class="d">Why the image is 11MB, not 900MB</span></a>

<a class="gwa-card" href="05-your-first-cluster/"><span class="n">PART 05</span><strong>Your first cluster</strong><span class="d">Free, local, and self-healing</span></a>

<a class="gwa-card" href="06-package-with-helm/"><span class="n">PART 06</span><strong>Package with Helm</strong><span class="d">One recipe, many environments</span></a>

<a class="gwa-card" href="07-automate-with-cicd/"><span class="n">PART 07</span><strong>Automate with CI/CD</strong><span class="d">Robots do it on every push</span></a>

<a class="gwa-card" href="08-deploy-to-the-cloud/"><span class="n">PART 08</span><strong>Deploy to the cloud</strong><span class="d">Real AWS — costs real money</span></a>

<a class="gwa-card" href="09-gitops-with-argocd/"><span class="n">PART 09</span><strong>GitOps with Argo CD</strong><span class="d">Closing the loop</span></a>

<a class="gwa-card" href="10-when-it-breaks/"><span class="n">PART 10</span><strong>When it breaks</strong><span class="d">Every error you will hit</span></a>

</div>

Stuck on a word? The [glossary](glossary.md) has all 28 of them.
