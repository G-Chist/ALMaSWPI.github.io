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
│   ├── config-utils.js
│   └── …
├── templates/                 # Flask templates for injection
│   ├── banner.html            # top bar injected into Jupyter pages
│   ├── ai_sidebar.html        # "Ask Big Pickle" sidebar
│   ├── tutor_bar.html         # AI tutor bar
│   └── welcome.html           # landing page for /es3011/
├── static/                    # Flask static assets (CSS/JS for injections)
│   ├── css/
│   │   ├── banner.css
│   │   ├── ai_sidebar.css
│   │   ├── tutor_bar.css
│   │   ├── cell_tutor_links.css
│   │   └── welcome.css
│   ├── ai_sidebar.js
│   ├── tutor_bar.js
│   ├── cell_tutor_links.js
│   ├── system_prompt.txt
│   └── tutor_prompt.txt
└── *.html, css/, js/, …       # ALMaSWPI site (unchanged)
```

## Workflow

### 1. Update Jupyter notebooks

Edit notebooks in `~/JupyterBasedControlEngineeringTextbook/`, then rebuild
JupyterLite and copy the output here:

```bash
# In ~/JupyterBasedControlEngineeringTextbook/
# rebuild JupyterLite (if you have jupyterlite installed):
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
- **`templates/welcome.html`** – the ES3011 landing page at `/es3011/`.

  **Important:** All asset paths (`href`, `src`) in these templates must start
  with `/static/`. The `freeze.py` script automatically rewrites them to
  relative paths at build time so they work from any deployment subpath.

- **`static/css/*.css`** – styles for the injections above.
- **`static/*.js`** – JavaScript for the injections.
- **`static/system_prompt.txt`** – system prompt used by the AI sidebar chat
  API (`/api/chat`).
- **`static/tutor_prompt.txt`** – system prompt for the tutor bar API
  (`/api/tutor-chat`).

  **Note:** The `/api/chat` and `/api/tutor-chat` endpoints are **only**
  available when running `python freeze.py serve` (Flask dev server). They are
  **not** included in the frozen static build. The sidebar/tutor UI will open
  in the deployed site but the "Send" button will 404 unless you implement a
  serverless alternative (e.g. a GitHub-backed API).

### 3. Add new Flask routes (advanced)

If you add new routes to `freeze.py`, you must also register a URL generator
so Frozen-Flask knows to visit them. Example for a hypothetical `/glossary/`
page:

```python
@app.route("/glossary/")
def glossary():
    return render_template("glossary.html")

@freezer.register_generator
def glossary():
    yield {}   # no arguments → visits /glossary/
```

For parameterised routes use `{"filename": "..."}` as the existing generators
do.

### 4. Preview locally

```bash
~/JupyterBasedControlEngineeringTextbook/venv/bin/python freeze.py serve
```

Opens a Flask dev server on http://localhost:8000. The `/api/chat` and
`/api/tutor-chat` endpoints require a `.env` file with an `OPENCODE_API_KEY`
in the `~/JupyterBasedControlEngineeringTextbook/` directory to work.

### 5. Build the static site

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

### 6. Deploy

**Via CI (recommended):** Push to `main`. The workflow at
`.github/workflows/deploy.yml` builds and deploys automatically.

**Manually:** Commit `_build/` (or symlink to `docs/`) and point GitHub Pages
at it. Not recommended – `_build/` is gitignored.

## How the freeze works

`freeze.py` is a Flask app that serves three things:

| Route | Source | Behaviour |
|---|---|---|
| `/` | ALMaSWPI repo root | Served as-is |
| `/es3011/…` | `es3011-content/` | HTML gets banner/AI sidebar injected |
| `/static/…` | `static/` | CSS/JS for the injections |

Frozen-Flask visits every URL via the test client, writes the response to
`_build/`, and the result is a fully static site ready for GitHub Pages.
