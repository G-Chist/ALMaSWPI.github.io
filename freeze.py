#!/usr/bin/env python3
"""
Freeze the combined ALMaSWPI + ES3011 JupyterLite site into static HTML
using Frozen-Flask, for deployment to GitHub Pages.

Usage:
    python freeze.py              # builds to _build/
    python freeze.py serve        # runs a dev server on port 8000
"""

import os, shutil
from flask import Flask, send_from_directory, abort, Response, request
from flask_frozen import Freezer

HERE = os.path.dirname(os.path.abspath(__file__))

SITE_DIR = os.path.join(HERE, "es3011-content")
TEMPLATES_DIR = os.path.join(HERE, "templates")
STATIC_DIR = os.path.join(HERE, "static")

app = Flask(__name__, static_folder=None)
app.template_folder = TEMPLATES_DIR
app.config['FREEZER_DESTINATION'] = '_build'

ALMAS_DIR = HERE
ES3011_PREFIX = "es3011"

with open(os.path.join(TEMPLATES_DIR, "banner.html")) as f:
    BANNER_HTML = f.read()
with open(os.path.join(TEMPLATES_DIR, "ai_sidebar.html")) as f:
    AI_SIDEBAR_HTML = f.read()
with open(os.path.join(TEMPLATES_DIR, "tutor_bar.html")) as f:
    TUTOR_BAR_HTML = f.read()

SKIP_DIRS = {".git", "_build", "es3011-content", "templates", ".github"}


def relativize(html):
    """Rewrite /static/ paths to be relative to the current page depth.
    This makes injections work regardless of deployment subpath."""
    depth = request.path.strip("/").count("/")
    if depth == 0:
        return html
    prefix = "../" * depth
    html = html.replace('href="/static/', f'href="{prefix}static/')
    html = html.replace('src="/static/', f'src="{prefix}static/')
    return html


def serve_with_banner(filepath):
    if not os.path.isfile(filepath):
        abort(404)
    with open(filepath) as f:
        content = f.read()

    banner = relativize(BANNER_HTML)
    ai = relativize(AI_SIDEBAR_HTML)
    tutor = relativize(TUTOR_BAR_HTML)
    css = relativize('<link rel="stylesheet" href="/static/css/cell_tutor_links.css">')
    js = relativize('<script src="/static/cell_tutor_links.js"></script>')

    i = content.find("<body")
    if i >= 0:
        j = content.index(">", i) + 1
        content = content[:j] + banner + content[j:]
    if "</body>" in content:
        content = content.replace(
            "</body>",
            css + ai + tutor + js + "</body>",
        )
    else:
        content = content.replace(
            "</html>",
            ai + tutor + js + "\n</html>",
        )
    return Response(content, mimetype="text/html")


# ── Flask routes ──────────────────────────────────────────────────────────

@app.route("/static/<path:filename>")
def flask_static(filename):
    return send_from_directory(STATIC_DIR, filename)


@app.route(f"/{ES3011_PREFIX}/")
def es3011_index():
    index_page = os.path.join(SITE_DIR, "index.html")
    return serve_with_banner(index_page)


@app.route(f"/{ES3011_PREFIX}/<path:filename>")
def es3011_files(filename):
    filepath = os.path.join(SITE_DIR, filename)
    if os.path.isdir(filepath):
        idx = os.path.join(filepath, "index.html")
        if os.path.isfile(idx):
            return serve_with_banner(idx)
        abort(404)
    if filename.endswith(".html"):
        return serve_with_banner(filepath)
    return send_from_directory(SITE_DIR, filename)


@app.route("/")
def almas_index():
    return send_from_directory(ALMAS_DIR, "index.html")


@app.route("/<path:filename>")
def almas_files(filename):
    filepath = os.path.join(ALMAS_DIR, filename)
    if os.path.isdir(filepath):
        idx = os.path.join(filepath, "index.html")
        if os.path.isfile(idx):
            return send_from_directory(filepath, "index.html")
        abort(404)
    if not os.path.isfile(filepath):
        abort(404)
    return send_from_directory(ALMAS_DIR, filename)


# ── Freezer ───────────────────────────────────────────────────────────────

freezer = Freezer(app)

SKIP_ALMAS_PREFIXES = tuple(f"{d}/" for d in SKIP_DIRS) + (".gitignore", "freeze.py")


@freezer.register_generator
def almas_files():
    for root, dirs, files in os.walk(ALMAS_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            path = os.path.relpath(os.path.join(root, f), ALMAS_DIR)
            if path.startswith(SKIP_ALMAS_PREFIXES):
                continue
            yield {"filename": path}


@freezer.register_generator
def flask_static():
    for root, dirs, files in os.walk(STATIC_DIR):
        for f in files:
            path = os.path.relpath(os.path.join(root, f), STATIC_DIR)
            yield {"filename": path}


@freezer.register_generator
def es3011_files():
    for root, dirs, files in os.walk(SITE_DIR):
        for f in files:
            path = os.path.relpath(os.path.join(root, f), SITE_DIR)
            yield {"filename": path}


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        app.run(debug=True, port=8000)
    else:
        build_dir = os.path.join(HERE, "_build")
        if os.path.isdir(build_dir):
            shutil.rmtree(build_dir)
        freezer.freeze()
        print(f"\nDone! Static site written to {build_dir}")
        print("Deploy the contents of _build/ to GitHub Pages.")
