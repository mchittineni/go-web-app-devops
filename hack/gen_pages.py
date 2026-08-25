#!/usr/bin/env python3
"""Generate the static HTML pages from one shared shell.

Kept as a build-time generator rather than a runtime template engine so the
Go binary stays dependency-free and the served files are plain, cacheable HTML.
"""
from pathlib import Path

OUT = Path("static")

NAV = [
    ("/home", "Home", "Overview and the learning path"),
    ("/courses", "Courses", "Every Zero-to-Hero playlist"),
    ("/about", "About", "Who maintains this"),
    ("/contact", "Contact", "Join the community"),
]

FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'"
    "%3E%3Crect width='32' height='32' rx='7' fill='%2306b6d4'/%3E%3Ctext x='16' y='22'"
    " font-family='monospace' font-size='15' font-weight='bold' text-anchor='middle'"
    " fill='%23041219'%3E%26lt;/%26gt;%3C/text%3E%3C/svg%3E"
)


def nav_items(active: str) -> str:
    out = []
    for href, label, _ in NAV:
        cur = ' aria-current="page"' if href == active else ""
        out.append(
            f'          <li><a class="nav-link" href="{href}"{cur}>{label}</a></li>'
        )
    return "\n".join(out)


def palette_items() -> str:
    out = []
    for href, label, hint in NAV:
        out.append(
            f'          <li>\n'
            f'            <a href="{href}"><span>{label}</span>'
            f'<span class="hint">{hint}</span></a>\n'
            f'          </li>'
        )
    return "\n".join(out)


SHELL = """<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta name="color-scheme" content="dark light">
  <meta name="theme-color" content="#05060a" media="(prefers-color-scheme: dark)">
  <meta name="theme-color" content="#f6f8fc" media="(prefers-color-scheme: light)">
  <link rel="canonical" href="{canonical}">
  <link rel="icon" href="{favicon}">

  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="/static/images/golang-website.png">
  <meta name="twitter:card" content="summary_large_image">

  <link rel="preload" href="/static/app.css" as="style">
  <link rel="stylesheet" href="/static/app.css">
  <script src="/static/app.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>

  <div class="aurora" aria-hidden="true"></div>
  <div class="grid-veil" aria-hidden="true"></div>
  <canvas id="constellation" aria-hidden="true"></canvas>
  <div class="scroll-progress" aria-hidden="true"></div>

  <header class="site-header">
    <div class="shell nav-bar">
      <a class="brand" href="/home">
        <span class="brand-mark" aria-hidden="true"></span>
        <span>go<em>&#183;</em>web<em>&#183;</em>app</span>
      </a>

      <nav aria-label="Primary">
        <ul class="nav-list" id="primary-nav">
{nav}
        </ul>
      </nav>

      <div class="nav-actions">
        <button class="palette-btn" type="button" data-palette-open hidden>
          <span>Jump to&#8230;</span> <kbd>&#8984;K</kbd>
        </button>
        <button class="icon-btn" type="button" data-theme-toggle hidden
                aria-label="Switch colour theme">&#9683;</button>
        <button class="icon-btn nav-toggle" type="button" data-nav-toggle hidden
                aria-expanded="false" aria-controls="primary-nav"
                aria-label="Toggle navigation">&#8801;</button>
      </div>
    </div>
  </header>

  <main id="main" class="shell">
{content}
  </main>

  <footer class="site-footer">
    <div class="shell footer-inner">
      <p>&copy; Abhishek Veeramalla &#183; content free to use</p>
      <p><code>go-web-app</code> &#183; Go 1.26 &#183; Kubernetes-native</p>
      <nav aria-label="Footer">
        <a href="/home">Home</a>
        <a href="/courses">Courses</a>
        <a href="/healthz">Health</a>
        <a href="/version">Version</a>
      </nav>
    </div>
  </footer>

  <dialog class="palette" id="palette" aria-label="Jump to a page">
    <input class="palette-input" type="text" placeholder="Jump to a page&#8230;"
           aria-label="Filter pages" autocomplete="off" spellcheck="false">
    <ul class="palette-list">
{palette}
    </ul>
    <p class="palette-empty" hidden>No matches.</p>
    <div class="palette-foot">
      <span>&#8593;&#8595; navigate</span><span>&#8629; open</span><span>esc close</span>
    </div>
  </dialog>
</body>
</html>
"""

TERMINAL_LINES = (
    '[{"kind":"cmd","text":"git clone go-web-app \\u0026\\u0026 cd go-web-app"},'
    '{"kind":"out","text":"Cloning into \'go-web-app\'... done."},'
    '{"kind":"cmd","text":"docker build -t go-web-app:dev ."},'
    '{"kind":"out","text":"=\\u003e exporting layers  4.1MB  distroless/static"},'
    '{"kind":"cmd","text":"helm upgrade --install web ./helm/go-web-app-chart"},'
    '{"kind":"out","text":"STATUS: deployed   READY 3/3   probes green"},'
    '{"kind":"cmd","text":"echo \\"you just shipped to Kubernetes\\""}]'
)

HOME = """    <section class="hero">
      <p class="eyebrow"><span class="pulse-dot" aria-hidden="true"></span>Free &#183; open source &#183; hands-on</p>
      <h1>Learn DevOps<br><span class="gradient-text">by shipping it.</span></h1>
      <p class="lede">
        This site is the project. A Go binary with embedded assets, containerised
        into a distroless image, scanned and signed in CI, then rolled out to
        Kubernetes through Helm and Argo CD &#8212; every layer you are about to
        learn is running right now to serve this page.
      </p>

      <div class="actions">
        <a class="btn btn-primary" href="/courses">
          Browse the courses <span class="arrow" aria-hidden="true">&#8594;</span>
        </a>
        <a class="btn btn-ghost" href="https://www.youtube.com/playlist?list=PLdpzxOOAlwvIKMhk8WhzN1pYoJ1YU8Csa"
           rel="noopener noreferrer" target="_blank">
          DevOps Zero to Hero <span class="arrow" aria-hidden="true">&#8599;</span>
        </a>
      </div>

      <div class="terminal" data-reveal>
        <div class="terminal-bar" aria-hidden="true">
          <span></span><span></span><span></span><b>zsh &#8212; go-web-app</b>
        </div>
        <pre class="terminal-body" data-typewriter='{terminal}'><span class="prompt">$ </span>git clone go-web-app &amp;&amp; cd go-web-app</pre>
      </div>
    </section>

    <section aria-labelledby="numbers">
      <div class="section-head" data-reveal>
        <span class="kicker" id="numbers">By the numbers</span>
        <h2>A real production path, not a toy tutorial</h2>
      </div>
      <dl class="stats" data-reveal>
        <div class="stat">
          <dt>Playlists</dt>
          <dd><span data-count-to="9">9</span></dd>
        </div>
        <div class="stat">
          <dt>Image size</dt>
          <dd><span data-count-to="4">4</span><span class="unit">MB</span></dd>
        </div>
        <div class="stat">
          <dt>Runtime deps</dt>
          <dd><span data-count-to="0">0</span></dd>
        </div>
        <div class="stat">
          <dt>Course cost</dt>
          <dd>&#36;<span data-count-to="0">0</span></dd>
        </div>
      </dl>
    </section>

    <section aria-labelledby="stack">
      <div class="section-head" data-reveal>
        <span class="kicker" id="stack">The stack under this page</span>
        <h2>Every layer, end to end</h2>
      </div>
      <div class="grid">
        <article class="card" data-reveal>
          <div class="card-icon" aria-hidden="true">&#9881;</div>
          <h3>Go, standard library only</h3>
          <p>
            <code>net/http</code> with a routed <code>ServeMux</code>, structured
            <code>log/slog</code> output, embedded assets and graceful shutdown.
            No framework, no third-party modules.
          </p>
          <div class="tag-row">
            <span class="tag">embed.FS</span><span class="tag">slog</span><span class="tag">graceful</span>
          </div>
        </article>

        <article class="card" data-reveal>
          <div class="card-icon" aria-hidden="true">&#128230;</div>
          <h3>Containers that carry nothing</h3>
          <p>
            A multi-stage build produces a static binary that runs on
            <code>distroless/static</code> as a non-root user, with a read-only
            root filesystem and no shell to exploit.
          </p>
          <div class="tag-row">
            <span class="tag">distroless</span><span class="tag">non-root</span><span class="tag">multi-arch</span>
          </div>
        </article>

        <article class="card" data-reveal>
          <div class="card-icon" aria-hidden="true">&#128737;</div>
          <h3>A supply chain you can verify</h3>
          <p>
            CI lints, tests, runs <code>govulncheck</code> and Trivy, generates an
            SBOM, then signs the image and its provenance with keyless Cosign.
          </p>
          <div class="tag-row">
            <span class="tag">govulncheck</span><span class="tag">SBOM</span><span class="tag">cosign</span>
          </div>
        </article>

        <article class="card" data-reveal>
          <div class="card-icon" aria-hidden="true">&#9784;</div>
          <h3>Kubernetes, declared properly</h3>
          <p>
            Probes, resource requests, a hardened pod security context, an HPA and
            a disruption budget &#8212; templated in Helm and reconciled by Argo CD.
          </p>
          <div class="tag-row">
            <span class="tag">Helm</span><span class="tag">HPA</span><span class="tag">Argo CD</span>
          </div>
        </article>
      </div>
    </section>

    <section aria-labelledby="start">
      <div class="callout" data-reveal>
        <div>
          <h2 id="start">Start where you are</h2>
          <p class="lede flow-tight">
            Nine Zero-to-Hero playlists covering DevOps, AWS, Azure, Terraform,
            Python, Ansible, GitOps, networking and Kubernetes troubleshooting.
            All of it free.
          </p>
        </div>
        <div class="actions flush">
          <a class="btn btn-primary" href="/courses">
            See all courses <span class="arrow" aria-hidden="true">&#8594;</span>
          </a>
          <a class="btn btn-ghost" href="/about">Meet the author</a>
        </div>
      </div>
    </section>
""".replace("{terminal}", TERMINAL_LINES)


def link_rows(items):
    rows = []
    for i, (title, meta, href) in enumerate(items, start=1):
        rows.append(
            f'          <li>\n'
            f'            <a class="link-row" href="{href}" rel="noopener noreferrer" target="_blank">\n'
            f'              <span class="idx" aria-hidden="true">{i:02d}</span>\n'
            f'              <span class="title">{title}</span>\n'
            f'              <span class="meta">{meta}</span>\n'
            f'            </a>\n'
            f'          </li>'
        )
    return "\n".join(rows)


MAIN_COURSES = [
    ("DevOps Zero to Hero", "core path", "https://www.youtube.com/playlist?list=PLdpzxOOAlwvIKMhk8WhzN1pYoJ1YU8Csa"),
    ("AWS Zero to Hero", "cloud", "https://www.youtube.com/playlist?list=PLdpzxOOAlwvLNOxX0RfndiYSt1Le9azze"),
    ("Azure Zero to Hero", "cloud", "https://www.youtube.com/playlist?list=PLdpzxOOAlwvIcxgCUyBHVOcWs0Krjx9xR"),
    ("Terraform Zero to Hero", "infra as code", "https://www.youtube.com/playlist?list=PLdpzxOOAlwvI0O4PeKVV1-yJoX2AqIWuf"),
    ("Python Zero to Hero", "automation", "https://www.youtube.com/playlist?list=PLdpzxOOAlwvKwTyYNJCUwGPvql0TrsPgv"),
]

EXTRA_COURSES = [
    ("Networking Fundamentals", "foundations", "https://www.youtube.com/playlist?list=PLdpzxOOAlwvKv4MFW35XRskZbQbrt6ep-"),
    ("Ansible Zero to Hero", "config mgmt", "https://www.youtube.com/playlist?list=PLdpzxOOAlwvLxd5nmtmORCmhD5jkrNbuE"),
    ("GitOps Zero to Hero", "delivery", "https://www.youtube.com/playlist?list=PLdpzxOOAlwvKu7OZpgj1-MzJFqZ8RBp6f"),
]

TROUBLESHOOT_COURSES = [
    ("Troubleshooting Kubernetes", "day 2 ops", "https://www.youtube.com/playlist?list=PLdpzxOOAlwvIrFBI1farpLS_OSUBXJMLX"),
]

COURSES = """    <section class="hero">
      <p class="eyebrow"><span class="pulse-dot" aria-hidden="true"></span>9 playlists &#183; always free</p>
      <h1>Learn DevOps<br><span class="gradient-text">from the basics.</span></h1>
      <p class="lede">
        DevOps combines software development and IT operations to shorten the
        development life cycle and deliver continuously without giving up quality.
        Start with the core path, then branch into the cloud or tool you need next.
      </p>
    </section>

    <section aria-labelledby="main-tutorials">
      <div class="section-head" data-reveal>
        <span class="kicker" id="main-tutorials">Main tutorials</span>
        <h2>The core learning path</h2>
      </div>
      <ul class="link-list" data-reveal>
{main}
      </ul>
    </section>

    <section aria-labelledby="additional">
      <div class="section-head" data-reveal>
        <span class="kicker" id="additional">Additional tutorials</span>
        <h2>Go deeper on the fundamentals</h2>
      </div>
      <ul class="link-list" data-reveal>
{extra}
      </ul>
    </section>

    <section aria-labelledby="troubleshooting">
      <div class="section-head" data-reveal>
        <span class="kicker" id="troubleshooting">Troubleshooting</span>
        <h2>When production disagrees with you</h2>
      </div>
      <ul class="link-list" data-reveal>
{trouble}
      </ul>
    </section>

    <section>
      <div class="callout" data-reveal>
        <div>
          <h2>Stuck on something?</h2>
          <p class="lede flow-tight">
            Join the members-only Slack channel and ask. Questions from learners
            shape what gets recorded next.
          </p>
        </div>
        <div class="actions flush">
          <a class="btn btn-primary" href="/contact">
            Get in touch <span class="arrow" aria-hidden="true">&#8594;</span>
          </a>
        </div>
      </div>
    </section>
""".replace("{main}", link_rows(MAIN_COURSES)) \
   .replace("{extra}", link_rows(EXTRA_COURSES)) \
   .replace("{trouble}", link_rows(TROUBLESHOOT_COURSES))


ABOUT = """    <section class="hero">
      <p class="eyebrow"><span class="pulse-dot" aria-hidden="true"></span>About the author</p>
      <h1>Hi, I&#8217;m Abhishek.<br><span class="gradient-text">Welcome to the channel.</span></h1>
      <p class="lede">
        I&#8217;m an open source enthusiast and a firm believer in sharing knowledge.
        I have footprints in projects including Argo CD, the Argo CD Operator,
        Argo Rollouts Manager, the GitOps Operator, the F5 Ingress Controller and
        the NGINX Ingress Controller.
      </p>
      <div class="actions">
        <a class="btn btn-primary" href="https://www.youtube.com/playlist?list=PLdpzxOOAlwvIKMhk8WhzN1pYoJ1YU8Csa"
           rel="noopener noreferrer" target="_blank">
          Watch the playlists <span class="arrow" aria-hidden="true">&#8599;</span>
        </a>
        <a class="btn btn-ghost" href="/contact">Say hello</a>
      </div>
    </section>

    <section aria-labelledby="roles">
      <div class="section-head" data-reveal>
        <span class="kicker" id="roles">Open source</span>
        <h2>Where I spend my time</h2>
      </div>
      <p class="lede flow-loose" data-reveal>
        Alongside working at Red Hat as a GitOps product lead, I hold these
        positions in open source communities.
      </p>
      <ul class="timeline" data-reveal>
        <li><strong>Maintainer &#8212; Argo CD Operator</strong><span>Operator lifecycle for Argo CD on Kubernetes and OpenShift.</span></li>
        <li><strong>Creator &#8212; Argo Rollouts Manager</strong><span>Progressive delivery, declared and reconciled.</span></li>
        <li><strong>Maintainer &#8212; Red Hat Developer GitOps Operator</strong><span>The supported GitOps story on OpenShift.</span></li>
        <li><strong>Member &#8212; Argo Project</strong><span>Contributing across the Argo ecosystem.</span></li>
        <li><strong>Member &#8212; Argo SIG Security</strong><span>Hardening the projects everyone deploys.</span></li>
      </ul>
    </section>

    <section aria-labelledby="why">
      <div class="section-head" data-reveal>
        <span class="kicker" id="why">Why this project exists</span>
        <h2>The website is the syllabus</h2>
      </div>
      <div class="grid">
        <article class="card" data-reveal>
          <div class="card-icon" aria-hidden="true">&#127891;</div>
          <h3>Free, forever</h3>
          <p>Complete DevOps training with practical projects, at no cost. The
             playlists stay open and keep getting extended.</p>
        </article>
        <article class="card" data-reveal>
          <div class="card-icon" aria-hidden="true">&#128295;</div>
          <h3>Built in the open</h3>
          <p>This app, its Dockerfile, its CI pipeline and its Helm chart are all
             in the repository. Read them, break them, improve them.</p>
        </article>
        <article class="card" data-reveal>
          <div class="card-icon" aria-hidden="true">&#128101;</div>
          <h3>Learn together</h3>
          <p>Subscribe to keep learning and growing together, and bring your
             questions to the community channel.</p>
        </article>
      </div>
    </section>
"""

CONTACT = """    <section class="hero">
      <p class="eyebrow"><span class="pulse-dot" aria-hidden="true"></span>Community</p>
      <h1>Got a question?<br><span class="gradient-text">Ask in the open.</span></h1>
      <p class="lede">
        For any doubts while learning, join the members-only Slack channel. It is
        the fastest way to get unstuck, and your question usually helps someone
        else who hit the same wall.
      </p>
      <div class="actions">
        <a class="btn btn-primary" href="https://www.youtube.com/abhishekVeeramalla/join"
           rel="noopener noreferrer" target="_blank">
          Join the Slack channel <span class="arrow" aria-hidden="true">&#8599;</span>
        </a>
        <a class="btn btn-ghost" href="/courses">Back to courses</a>
      </div>
    </section>

    <section aria-labelledby="channels">
      <div class="section-head" data-reveal>
        <span class="kicker" id="channels">Where to reach out</span>
        <h2>Pick the channel that fits</h2>
      </div>
      <div class="grid">
        <a class="card" data-reveal href="https://www.youtube.com/abhishekVeeramalla/join"
           rel="noopener noreferrer" target="_blank">
          <div class="card-icon" aria-hidden="true">&#128172;</div>
          <h3>Members Slack <span class="arrow" aria-hidden="true">&#8599;</span></h3>
          <p>Exclusive channel for members. Best for questions while working
             through a playlist.</p>
        </a>
        <a class="card" data-reveal href="https://www.youtube.com/playlist?list=PLdpzxOOAlwvIKMhk8WhzN1pYoJ1YU8Csa"
           rel="noopener noreferrer" target="_blank">
          <div class="card-icon" aria-hidden="true">&#9654;</div>
          <h3>YouTube <span class="arrow" aria-hidden="true">&#8599;</span></h3>
          <p>Comment on the video you are watching &#8212; useful when the question
             is about a specific step.</p>
        </a>
        <a class="card" data-reveal href="https://github.com/iam-veeramalla/go-web-app-devops"
           rel="noopener noreferrer" target="_blank">
          <div class="card-icon" aria-hidden="true">&#128193;</div>
          <h3>GitHub issues <span class="arrow" aria-hidden="true">&#8599;</span></h3>
          <p>For bugs in this project or the manifests, open an issue on the
             repository.</p>
        </a>
      </div>
    </section>

    <section>
      <div class="callout" data-reveal>
        <div>
          <h2>Before you ask</h2>
          <p class="flow-tight">
            Include what you ran, what you expected and what actually happened
            &#8212; plus the output of <code>kubectl describe</code> or
            <code>kubectl logs</code> if it is a cluster problem. It turns a
            day-long thread into a five-minute answer.
          </p>
        </div>
      </div>
    </section>
"""

PAGES = [
    ("home.html", "/home", "Learn DevOps from Basics",
     "Free, hands-on DevOps training. Zero-to-Hero playlists on DevOps, AWS, "
     "Azure, Terraform, Kubernetes and more — taught through a real Go app "
     "shipped to Kubernetes.", HOME),
    ("courses.html", "/courses", "Courses · Learn DevOps from Basics",
     "Nine free Zero-to-Hero playlists covering DevOps, AWS, Azure, Terraform, "
     "Python, Ansible, GitOps, networking and Kubernetes troubleshooting.", COURSES),
    ("about.html", "/about", "About · Learn DevOps from Basics",
     "Abhishek Veeramalla — GitOps product lead at Red Hat, maintainer of the "
     "Argo CD Operator and creator of Argo Rollouts Manager.", ABOUT),
    ("contact.html", "/contact", "Contact · Learn DevOps from Basics",
     "Join the members-only Slack channel, comment on YouTube, or open a GitHub "
     "issue for anything about this project.", CONTACT),
]

for filename, route, title, description, content in PAGES:
    html = SHELL.format(
        title=title,
        description=description,
        canonical=route,
        favicon=FAVICON,
        nav=nav_items(route),
        palette=palette_items(),
        content=content,
    )
    (OUT / filename).write_text(html, encoding="utf-8")
    print(f"{filename:16} {len(html):>6} bytes")
