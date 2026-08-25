/* =============================================================================
 * go-web-app — progressive enhancement layer
 *
 * Rules this file follows:
 *   - Zero dependencies, zero network requests.
 *   - Every page renders and is fully navigable with this file absent.
 *   - prefers-reduced-motion disables animation rather than reducing it.
 *   - No inline handlers and no eval, so the strict CSP needs no escape hatch.
 * ========================================================================== */
(() => {
  'use strict';

  const root = document.documentElement;
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const $ = (sel, scope = document) => scope.querySelector(sel);
  const $$ = (sel, scope = document) => Array.from(scope.querySelectorAll(sel));

  // Signals to the stylesheet that JS is live, which is what gates the
  // reveal-on-scroll transitions. Set first so nothing flashes.
  root.classList.add('js');

  /* --- Theme ------------------------------------------------------------- */
  const THEME_KEY = 'gwa-theme';

  const readStoredTheme = () => {
    try {
      return localStorage.getItem(THEME_KEY);
    } catch {
      return null; // private mode / blocked storage
    }
  };

  const applyTheme = (theme) => {
    if (theme === 'light' || theme === 'dark') {
      root.dataset.theme = theme;
    } else {
      delete root.dataset.theme;
    }
    const btn = $('[data-theme-toggle]');
    if (!btn) return;
    const effective = theme || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
    btn.textContent = effective === 'light' ? '◓' : '◒';
    btn.setAttribute('aria-label', `Switch to ${effective === 'light' ? 'dark' : 'light'} theme`);
    btn.setAttribute('aria-pressed', String(effective === 'light'));
  };

  applyTheme(readStoredTheme());

  const themeToggle = $('[data-theme-toggle]');
  if (themeToggle) {
    themeToggle.hidden = false;
    themeToggle.addEventListener('click', () => {
      const current = root.dataset.theme
        || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
      const next = current === 'light' ? 'dark' : 'light';
      applyTheme(next);
      try {
        localStorage.setItem(THEME_KEY, next);
      } catch { /* storage unavailable — theme is session-only */ }
    });
  }

  /* --- Active nav link + mobile drawer ---------------------------------- */
  const path = location.pathname.replace(/\/$/, '') || '/home';
  $$('.nav-link, .palette-list a').forEach((link) => {
    if (new URL(link.href, location.origin).pathname === path) {
      link.setAttribute('aria-current', 'page');
    }
  });

  const navToggle = $('[data-nav-toggle]');
  const navList = $('#primary-nav');
  if (navToggle && navList) {
    navToggle.hidden = false;
    const setOpen = (open) => {
      navList.dataset.open = String(open);
      navToggle.setAttribute('aria-expanded', String(open));
      navToggle.textContent = open ? '✕' : '≡';
    };
    // Collapsed only while the drawer breakpoint is active; CSS ignores the
    // attribute on wide screens.
    setOpen(false);
    navToggle.addEventListener('click', () => setOpen(navList.dataset.open !== 'true'));
    navList.addEventListener('click', (e) => {
      if (e.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && navList.dataset.open === 'true') setOpen(false);
    });
  }

  /* --- Sticky header + scroll progress ---------------------------------- */
  const header = $('.site-header');
  const progress = $('.scroll-progress');

  if (header || progress) {
    let queued = false;
    const onScroll = () => {
      if (queued) return;
      queued = true;
      requestAnimationFrame(() => {
        queued = false;
        if (header) header.dataset.stuck = String(scrollY > 8);
        if (progress) {
          const max = document.body.scrollHeight - innerHeight;
          progress.style.setProperty('--progress', max > 0 ? String(scrollY / max) : '0');
        }
      });
    };
    addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* --- Reveal on scroll -------------------------------------------------- */
  const revealTargets = $$('[data-reveal]');
  if (revealTargets.length && 'IntersectionObserver' in window && !reduceMotion.matches) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.dataset.revealed = 'true';
        obs.unobserve(entry.target); // reveal once, then stop paying for it
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    revealTargets.forEach((el) => {
      // Stagger siblings so a grid cascades rather than popping as one block.
      const siblings = Array.from(el.parentElement?.children || []);
      const index = siblings.indexOf(el);
      el.style.setProperty('--reveal-delay', `${Math.min(index, 6) * 70}ms`);
      observer.observe(el);
    });
  } else {
    revealTargets.forEach((el) => { el.dataset.revealed = 'true'; });
  }

  /* --- Cursor spotlight on cards ---------------------------------------- */
  const spotlightCards = $$('.card');
  if (spotlightCards.length && matchMedia('(hover: hover) and (pointer: fine)').matches) {
    let frame = 0;
    spotlightCards.forEach((card) => {
      card.addEventListener('pointermove', (e) => {
        if (frame) return;
        frame = requestAnimationFrame(() => {
          frame = 0;
          const box = card.getBoundingClientRect();
          card.style.setProperty('--mx', `${e.clientX - box.left}px`);
          card.style.setProperty('--my', `${e.clientY - box.top}px`);
        });
      });
    });
  }

  /* --- Terminal typewriter ---------------------------------------------- */
  const terminal = $('[data-typewriter]');
  if (terminal) {
    let lines;
    try {
      lines = JSON.parse(terminal.dataset.typewriter);
    } catch {
      lines = null;
    }

    if (Array.isArray(lines) && lines.length) {
      const render = (upto, partial) => {
        const frag = document.createDocumentFragment();
        lines.slice(0, upto).forEach((line) => {
          frag.append(buildLine(line, line.text));
        });
        if (partial !== null && lines[upto]) {
          const el = buildLine(lines[upto], partial);
          const caret = document.createElement('i');
          caret.className = 'caret';
          caret.textContent = ' ';
          el.append(caret);
          frag.append(el);
        }
        terminal.replaceChildren(frag);
      };

      const buildLine = (line, text) => {
        const el = document.createElement('div');
        if (line.kind === 'cmd') {
          const p = document.createElement('span');
          p.className = 'prompt';
          p.textContent = '$ ';
          el.append(p);
        } else {
          el.className = 'out';
        }
        // textContent, never innerHTML — the data is authored, but this keeps
        // the sink safe if it ever becomes dynamic.
        el.append(document.createTextNode(text));
        return el;
      };

      if (reduceMotion.matches) {
        render(lines.length, null);
      } else {
        let li = 0;
        let ci = 0;
        const tick = () => {
          if (li >= lines.length) {
            render(lines.length, null);
            return;
          }
          const line = lines[li];
          if (ci <= line.text.length) {
            render(li, line.text.slice(0, ci));
            ci += 1;
            setTimeout(tick, line.kind === 'cmd' ? 26 : 6);
          } else {
            li += 1;
            ci = 0;
            setTimeout(tick, line.kind === 'cmd' ? 260 : 90);
          }
        };
        render(0, '');
        setTimeout(tick, 400);
      }
    }
  }

  /* --- Stat counters ---------------------------------------------------- */
  const counters = $$('[data-count-to]');
  if (counters.length) {
    const runCounter = (el) => {
      const target = Number(el.dataset.countTo);
      if (!Number.isFinite(target)) return;
      if (reduceMotion.matches) {
        el.textContent = String(target);
        return;
      }
      const duration = 1100;
      const start = performance.now();
      const step = (now) => {
        const t = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - t, 3);
        el.textContent = String(Math.round(target * eased));
        if (t < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };

    if ('IntersectionObserver' in window) {
      const obs = new IntersectionObserver((entries, o) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          runCounter(entry.target);
          o.unobserve(entry.target);
        });
      }, { threshold: 0.5 });
      counters.forEach((el) => obs.observe(el));
    } else {
      counters.forEach(runCounter);
    }
  }

  /* --- Command palette (Cmd/Ctrl+K) ------------------------------------- */
  const palette = $('#palette');
  if (palette && typeof palette.showModal === 'function') {
    const input = $('.palette-input', palette);
    const list = $('.palette-list', palette);
    const empty = $('.palette-empty', palette);
    const items = $$('li', list);

    $$('[data-palette-open]').forEach((btn) => {
      btn.hidden = false;
      btn.addEventListener('click', () => open());
    });

    const visible = () => items.filter((li) => !li.hidden);

    const highlight = (index) => {
      const shown = visible();
      shown.forEach((li, i) => { li.dataset.active = String(i === index); });
      shown[index]?.querySelector('a')?.scrollIntoView({ block: 'nearest' });
    };

    const filter = () => {
      const q = input.value.trim().toLowerCase();
      items.forEach((li) => {
        li.hidden = q !== '' && !li.textContent.toLowerCase().includes(q);
      });
      const count = visible().length;
      if (empty) empty.hidden = count > 0;
      highlight(count ? 0 : -1);
    };

    const open = () => {
      if (palette.open) return;
      input.value = '';
      filter();
      palette.showModal();
      input.focus();
    };

    input.addEventListener('input', filter);

    palette.addEventListener('keydown', (e) => {
      const shown = visible();
      if (!shown.length) return;
      const current = shown.findIndex((li) => li.dataset.active === 'true');

      if (e.key === 'ArrowDown' || (e.key === 'Tab' && !e.shiftKey)) {
        e.preventDefault();
        highlight((current + 1) % shown.length);
      } else if (e.key === 'ArrowUp' || (e.key === 'Tab' && e.shiftKey)) {
        e.preventDefault();
        highlight((current - 1 + shown.length) % shown.length);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        shown[Math.max(current, 0)]?.querySelector('a')?.click();
      }
    });

    // Click on the backdrop closes; clicks inside the dialog do not.
    palette.addEventListener('click', (e) => {
      if (e.target === palette) palette.close();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key.toLowerCase() === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        palette.open ? palette.close() : open();
      }
      // Bare "/" is a search affordance, but never while typing in a field.
      if (e.key === '/' && !palette.open && !/^(INPUT|TEXTAREA)$/.test(document.activeElement?.tagName || '')) {
        e.preventDefault();
        open();
      }
    });

    filter();
  }

  /* --- Constellation canvas -------------------------------------------- */
  const canvas = $('#constellation');
  if (canvas && !reduceMotion.matches && canvas.getContext) {
    const ctx = canvas.getContext('2d', { alpha: true });
    // Cap DPR: a 3x retina backing store on a full-viewport canvas is the
    // single easiest way to burn a mobile GPU budget.
    const dpr = Math.min(devicePixelRatio || 1, 2);

    let w = 0;
    let h = 0;
    let nodes = [];
    let raf = 0;

    const accent = () => getComputedStyle(root).getPropertyValue('--accent').trim() || '#22d3ee';

    const resize = () => {
      w = innerWidth;
      h = innerHeight;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Density scales with area but is hard-capped, so a 4K monitor does
      // not quietly quadruple the per-frame cost.
      const count = Math.min(Math.round((w * h) / 26000), 72);
      nodes = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.16,
        vy: (Math.random() - 0.5) * 0.16,
        r: Math.random() * 1.3 + 0.6,
      }));
    };

    const LINK_DIST = 132;

    const frame = () => {
      ctx.clearRect(0, 0, w, h);
      const color = accent();

      for (let i = 0; i < nodes.length; i += 1) {
        const a = nodes[i];
        a.x += a.vx;
        a.y += a.vy;
        if (a.x < 0 || a.x > w) a.vx *= -1;
        if (a.y < 0 || a.y > h) a.vy *= -1;

        ctx.beginPath();
        ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.5;
        ctx.fill();

        for (let j = i + 1; j < nodes.length; j += 1) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.hypot(dx, dy);
          if (dist > LINK_DIST) continue;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = color;
          ctx.globalAlpha = (1 - dist / LINK_DIST) * 0.16;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
      ctx.globalAlpha = 1;
      raf = requestAnimationFrame(frame);
    };

    const start = () => { if (!raf) raf = requestAnimationFrame(frame); };
    const stop = () => { cancelAnimationFrame(raf); raf = 0; };

    resize();
    start();

    let resizeTimer = 0;
    addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(resize, 150);
    }, { passive: true });

    // Never animate a background tab.
    document.addEventListener('visibilitychange', () => {
      document.hidden ? stop() : start();
    });
    reduceMotion.addEventListener('change', (e) => {
      if (e.matches) {
        stop();
        ctx.clearRect(0, 0, w, h);
      } else {
        start();
      }
    });
  }
})();
