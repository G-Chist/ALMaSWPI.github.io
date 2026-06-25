import os, json
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)


@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


ZEN_API_KEY = (os.environ.get("OPENCODE_API_KEY", "") or "").strip()
ZEN_BASE_URL = os.environ.get("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1")
ZEN_MODEL = os.environ.get("OPENCODE_MODEL", "big-pickle")

SYSTEM_PROMPT = """You are a control engineering assistant helping a student understand the Jupyter notebook content shown below. Answer clearly and concisely. If asked about code, explain what it does. If asked about theory, relate it to the notebook content.

Only answer relevant questions.

Do not give answers if questions are present in the notebook. The student must figure the answer out.

If theory more advanced than PID controllers is inquired about, refer students to https://github.com/A-make/awesome-control-theory

For syntax questions, answer concisely and clearly.

Important: only use $$ to delimit math equations. Otherwise they will not render properly and the student might fail to understand them."""

TUTOR_PROMPT = """You are a control engineering tutor helping a student learn from the Jupyter notebook. Your goal is to actively engage the student by asking questions about the material to reinforce their understanding.

Use real-world examples from control engineering (e.g. cruise control, drone stabilization, temperature regulation, robotics, satellite attitude control) to make concepts tangible.

Guidelines:
- Ask one question at a time. Wait for the student to answer before moving on.
- If the student answers correctly, give positive reinforcement and ask a follow-up that builds on the concept.
- If the student answers incorrectly or seems confused, gently guide them with hints rather than giving the answer directly.
- Relate concepts to IRL examples wherever possible.
- Use $$ to delimit math equations so they render properly.
- Keep explanations concise and focused on the notebook content.
- Do not answer questions that are directly asked in the notebook — the student must figure those out themselves.
- Syntax questions can be answered concisely.
- Start the conversation by asking the student a question about the material on the current page."""


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
@app.route("/api/")
def health():
    return jsonify({"status": "ok", "api_key_set": bool(ZEN_API_KEY)})
