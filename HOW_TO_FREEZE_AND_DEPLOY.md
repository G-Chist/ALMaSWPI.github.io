# Freeze & Deploy Guide

This explains how to update the ES3011 Jupyter notebooks/content, modify the Flask
injections (banner, AI sidebar, tutor), rebuild the static site, and deploy.

## Directory layout

```
ALMaSWPI.github.io/
├── freeze.py                  # Flask app + Frozen-Flask build script
├── .github/workflows/deploy.yml  # CI: auto-builds & deploys on push
├── es3011-content/            # JupyterLite _site/ output (your notebooks)
│   ├── index.html
│   ├── lab/index.html
│   └── …
├── templates/                 # Flask templates for injection
│   ├── banner.html            # top bar injected into Jupyter pages
│   ├── ai_sidebar.html        # "Ask Big Pickle" sidebar
│   └── tutor_bar.html         # AI tutor bar
├── static/                    # Flask static assets (CSS/JS for injections)
│   ├── css/
│   │   ├── banner.css
│   │   ├── ai_sidebar.css
│   │   ├── tutor_bar.css
│   │   └── cell_tutor_links.css
│   ├── ai_sidebar.js
│   ├── tutor_bar.js
│   ├── cell_tutor_links.js
│   ├── system_prompt.txt
│   └── tutor_prompt.txt
├── api-server/                # Standalone Flask API deployable to Vercel
│   ├── app.py
│   └── requirements.txt
└── *.html, css/, js/, …       # ALMaSWPI site (unchanged)
```

## Workflow

### 1. Update Jupyter notebooks

Edit notebooks in `~/JupyterBasedControlEngineeringTextbook/`, then rebuild
JupyterLite and copy the output here:

```bash
# In ~/JupyterBasedControlEngineeringTextbook/
#   jupyter lite build --output-dir _site

# Copy the fresh build into this repo:
cp -r ~/JupyterBasedControlEngineeringTextbook/_site \
      /path/to/ALMaSWPI.github.io/es3011-content
```

### 2. Modify Flask injections

- **`templates/banner.html`** – the red "WPI ES3011" bar at the top of every
  Jupyter page.
- **`templates/ai_sidebar.html`** – the "Ask Big Pickle" sidebar (button +
  panel + chat).
- **`templates/tutor_bar.html`** – the "AI Tutor" bar.

  **Important:** All asset paths (`href`, `src`) in these templates must start
  with `/static/`. The `freeze.py` script automatically rewrites them to
  relative paths at build time so they work from any deployment subpath.

- **`static/css/*.css`** – styles for the injections above.
- **`static/*.js`** – JavaScript for the injections.
- **`static/system_prompt.txt`** – system prompt used by the AI sidebar chat
  API (`/api/chat`).
- **`static/tutor_prompt.txt`** – system prompt for the tutor bar API
  (`/api/tutor-chat`).

### 3. Deploy the AI API to Vercel

The sidebar/tutor need a live API to respond. The standalone app in
`api-server/app.py` is designed for Vercel:

1. Go to **vercel.com → Add New → Project** and import this repo.
2. In **Settings → General → Root Directory**, set `api-server/`.
3. Add **Environment Variable**: `OPENCODE_API_KEY` = your API key.
4. Deploy. Vercel gives you a URL like `https://al-ma-swpi-github-io.vercel.app`.

### 4. Set API_BASE

The frozen site needs to know where the API lives. The JS in the
sidebar/tutor reads `window.API_BASE` to decide which server to call.

**Via GitHub Variables (recommended):**
Go to **Settings → Variables and Secrets → Actions → Variables** → add:
- **Name:** `API_BASE`
- **Value:** `https://al-ma-swpi-github-io.vercel.app` (your Vercel URL)

On the next push to `main`, the CI build will inject
`<script>window.API_BASE="..."</script>` into the frozen HTML.

**Via local build:**
```bash
API_BASE=https://al-ma-swpi-github-io.vercel.app python freeze.py
```

If `API_BASE` is not set, the JS defaults to `/api/chat` (only works when
running `python freeze.py serve` locally).

### 5. Preview locally

```bash
~/JupyterBasedControlEngineeringTextbook/venv/bin/python freeze.py serve
```

Opens a Flask dev server on http://localhost:8000. The `/api/chat` and
`/api/tutor-chat` endpoints require a `.env` file with an `OPENCODE_API_KEY`
in the repo root or `~/JupyterBasedControlEngineeringTextbook/`.

### 6. Build the static site

```bash
~/JupyterBasedControlEngineeringTextbook/venv/bin/python freeze.py
```

Output goes to `_build/`. The freeze:
- Copies ALMaSWPI pages as-is.
- Copies JupyterLite content to `es3011/`.
- Injects the banner, AI sidebar, and tutor bar into every HTML file under
  `es3011/`.
- Rewrites all `/static/…` paths to relative paths (`../../static/…`) so
  they work regardless of GitHub Pages subpath.
- Injects `<script>window.API_BASE="…"</script>` if `API_BASE` was set.

### 7. Deploy

Push to `main`. The workflow at `.github/workflows/deploy.yml` builds and
deploys automatically.

## How the freeze works

`freeze.py` is a Flask app that serves three things:

| Route | Source | Behaviour |
|---|---|---|
| `/` | ALMaSWPI repo root | Served as-is |
| `/es3011/…` | `es3011-content/` | HTML gets banner/AI sidebar injected |
| `/static/…` | `static/` | CSS/JS for the injections |

Frozen-Flask visits every URL via the test client, writes the response to
`_build/`, and the result is a fully static site ready for GitHub Pages.

## AI Chat Architecture

```
Browser (GitHub Pages)
    │
    ├──── window.API_BASE ────┐
    │                         │
    ▼                         ▼
/api/chat (local dev)    https://al-ma-swpi-github-io.vercel.app/api/chat
(freeze.py serve)             │
                         api-server/app.py (Vercel)
                              │
                              ▼
                         opencode.ai (LLM API)
```

When `API_BASE` is set (via GitHub Variable or env), the frozen HTML includes
`<script>window.API_BASE="https://…"</script>`. The JS uses that as the base
URL for API calls. Without it, the JS falls back to `/api/chat` (only works
when `freeze.py serve` is running locally).
