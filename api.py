"""Standalone Flask API for the ALMaS + ES3011 AI chat sidebar & tutor.
Deploy to PythonAnywhere (or Render, Railway, etc.).

1. Upload this file + prompts to PythonAnywhere
2. Set OPENCODE_API_KEY in the WSGI config or as an env var
3. Point your GitHub Pages site at this API via API_BASE
"""

import os, json
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

HERE = os.path.dirname(os.path.abspath(__file__))

# ── Config ────────────────────────────────────────────────────────────────

def load_env(path=".env"):
    envars = os.environ.copy()
    if os.path.isfile(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip().strip("\"'")
                envars.setdefault(key, val)
    return envars

env = load_env(os.path.join(HERE, ".env"))

ZEN_API_KEY = env.get("OPENCODE_API_KEY", "")
ZEN_BASE_URL = env.get("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1")
ZEN_MODEL = env.get("OPENCODE_MODEL", "big-pickle")

# ── Prompts ───────────────────────────────────────────────────────────────

with open(os.path.join(HERE, "static", "system_prompt.txt")) as f:
    SYSTEM_PROMPT = f.read().strip()
with open(os.path.join(HERE, "static", "tutor_prompt.txt")) as f:
    TUTOR_PROMPT = f.read().strip()

# ── API helpers ───────────────────────────────────────────────────────────

def build_messages(system_prompt, question, context, history):
    system = system_prompt + "\n\n--- Page content ---\n" + context
    messages = [{"role": "system", "content": system}]
    for msg in history:
        if msg.get("role") in ("user", "assistant"):
            messages.append(msg)
    messages.append({"role": "user", "content": question})
    return messages

def call_zen(messages):
    session = requests.Session()
    session.trust_env = False
    r = session.post(
        f"{ZEN_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {ZEN_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"model": ZEN_MODEL, "messages": messages, "stream": False},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ── Routes ────────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def api_chat():
    if not ZEN_API_KEY:
        return jsonify({"error": "OPENCODE_API_KEY not set"}), 500
    try:
        data = request.get_json()
        messages = build_messages(
            SYSTEM_PROMPT,
            data.get("question", ""),
            data.get("context", ""),
            data.get("history", []),
        )
        reply = call_zen(messages)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tutor-chat", methods=["POST"])
def api_tutor_chat():
    if not ZEN_API_KEY:
        return jsonify({"error": "OPENCODE_API_KEY not set"}), 500
    try:
        data = request.get_json()
        messages = build_messages(
            TUTOR_PROMPT,
            data.get("question", ""),
            data.get("context", ""),
            data.get("history", []),
        )
        reply = call_zen(messages)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def health():
    return jsonify({"status": "ok", "api_key_set": bool(ZEN_API_KEY)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
