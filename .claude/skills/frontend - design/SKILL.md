---
name: zamah-ui-designer
description: Generate production-ready frontend UI for the Zamah Expense Tracker — a Flask + Jinja2 + plain-CSS personal expense app — that matches its existing warm "paper-and-ink" editorial fintech design. Use this skill whenever the user wants to design, build, create, redesign, lay out, or improve any page, screen, view, component, partial, form, card, table, list, modal, or section for Zamah (the expense tracker), even if they don't say "Zamah" or "UI" explicitly — e.g. "design the dashboard", "create the add-expense form", "build a category breakdown card", "redesign the login page", "make the expenses list look better", "lay out the monthly report screen". Trigger on phrasings like "design the ___ page", "create UI for ___", "build a component/partial for ___", "redesign/improve ___". Do NOT use for backend routes, database/SQL work, deployment, or UI for a different (non-Zamah) project.
---

# Zamah UI Designer

Produce frontend UI for the **Zamah Expense Tracker** that looks like it was always part of
the app. The whole value of this skill is *consistency*: Zamah already has a distinctive,
well-made design, so a new page should reuse its tokens, layout shells, and existing classes
rather than introduce a fresh style. A page that technically works but looks foreign is a
failure here.

## Know the project before you design

Zamah is a **Flask 3.1 + SQLite + Jinja2 + plain HTML/CSS/JS** app — there is **no frontend
framework and no build step**. That shapes everything:
- "Component" / "partial" means a **Jinja template** (a page that `{% extends "base.html" %}`,
  or an `{% include %}`-able snippet), not a React/Vue component.
- Styling is **plain CSS using the existing CSS variables** in `static/css/style.css`. No
  Tailwind, no CSS-in-JS, no utility classes.
- Icons are **inline Lucide SVG** (no npm packages).
- JS, if any, stays **vanilla** and goes in `static/js/` or a `{% block scripts %}`.
- Currency is **PKR (₨)**.

Read `references/design-system.md` before writing anything — it has the exact color/spacing/
radius tokens, the `base.html` block contract, the list of reusable classes (`.summary-card`,
`.btn-primary`, `.form-input`, …) to prefer over new ones, the icon approach, and a worked
example. Reusing what's there is the single biggest lever on quality.

If you have access to the repo (e.g. it's cloned or files are attached), skim the live
`static/css/style.css` and the closest existing template too — the live files are the real
source of truth, and matching a sibling page is the fastest route to consistency.

## Deliverable: real project files

The output is files that drop straight into the repo, **not** a standalone HTML mockup. For a
typical request that means:
1. A **Jinja template** at `templates/<name>.html` that extends `base.html` and fills the
   `title` / `content` (and optionally `head` / `scripts`) blocks.
2. The **CSS** for it — appended to `static/css/style.css` under a commented section banner in
   the file's existing style, or a new `static/css/<page>.css` for a large standalone page
   (mirroring how `landing.css` is split out). Always reuse existing variables and classes first.
3. If the page implies a route or template variables, **note the route signature and the
   context keys** the template expects (e.g. "expects `expenses` — a list of dicts with
   `name`, `amount`, `date`") so it's clear how to wire it up. Don't silently invent backend
   behavior; flag what the route needs to pass in.

Wrap real, runnable code in fenced blocks with the file path as a heading so it's obvious what
goes where. Don't paste back the whole of `style.css` — give only the new section to append.

## Response shape

Lead with a short **UI structure brief** (a few lines, not an essay), then the code:

1. **Layout & sections** — what the page is made of, top to bottom, and the key UX decisions
   (what's emphasized, what's primary action, empty/loading states if relevant). Keep it tight.
2. **The Jinja template** — file path + code.
3. **The CSS** — file path + the section to add.
4. **Wiring note** — the route/context the template needs, if any, in a sentence or two.

Keep the brief genuinely brief; the code is the deliverable. Don't over-explain obvious markup.

## Design rules (this is the Zamah look)

These restate `design-system.md` at a glance — read the reference for exact values.

- **Use the CSS variables, never raw hex.** Warm `--paper` background, white `--paper-card`
  cards, ink-scale text, `--accent` forest green, `--accent-2` gold for highlights,
  `--danger` red for destructive things.
- **Serif display headings** (`var(--font-display)`), often with an `<em>` in green for
  emphasis; **DM Sans** body. Small uppercase letter-spaced labels for eyebrows/card labels.
- **Cards**: white, `1px solid var(--border)`, `--radius-md`, ~1.75rem padding. Shadows are
  *soft and rare* (`0 8px 40px rgba(0,0,0,0.06)` is the heaviest in the app) — usually just
  the border. Never heavy/dark shadows.
- **Radii** from the tokens (6/12/20px); pills use `border-radius:999px`.
- **Spacing** on the project's de-facto 8px grid — move in 0.5rem multiples; keep generous
  whitespace and clear hierarchy. Page sections use `max-width:var(--max-width); margin:0 auto`.
- **Responsive** at the existing breakpoints (900 / 700 / 600px) rather than new ones.
- **Format money as `₨ 12,500`** (₨, space, comma thousands).
- **Icons**: inline Lucide SVG, ~18–20px, colored via `currentColor`; `aria-hidden` when
  decorative, labeled when meaningful.

## Consistency rule

Match the existing project design. If you can see the repo or relevant CSS/templates, anchor
to the nearest existing page. If you genuinely can't tell what something should look like —
the request references a screen you can't see, or asks for a pattern with no precedent in the
app — **ask the user for a screenshot or pointer to the closest existing page** rather than
guessing and risking a style that clashes. One good clarifying question beats a foreign-looking
page.

## Accessibility & quality basics

Because these ship as real pages, get the fundamentals right without being asked: semantic
elements (`<button>` for actions, `<a>` for navigation, real `<label>`s tied to inputs),
sensible heading order, visible focus (the project's inputs already show a green focus
border — keep that), alt/aria on meaningful icons, and adequate tap targets. Keep markup
clean and minimal — no wrapper-div soup.

## Avoid

- **Generic / dated UI** — stock blue-gradient SaaS dashboards, heavy drop shadows, clip-art
  icons, default browser styling. Zamah's look is specific; honor it.
- **A foreign style** — Tailwind/utility classes, Bootstrap, inline `style="..."` for things
  that belong in CSS, hardcoded hex instead of variables, a new font.
- **Unstructured code dumps** — no context, no file paths, or one giant blob. Always say what
  file each block belongs to and lead with the short structure brief.
- **Reinventing existing classes** — if `.summary-card` / `.btn-primary` / `.form-input`
  already do the job, use them.
- **Silently inventing backend behavior** — if the template needs data, name what the route
  must pass; don't pretend a route exists or change `app.py`/`db.py` unless asked.