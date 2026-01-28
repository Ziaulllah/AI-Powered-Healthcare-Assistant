




import os
import uuid
import requests
from flask import Flask, request, jsonify, render_template

# ─────────────────────────────────────────────
# Force Flask to THIS project only
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

# ─────────────────────────────────────────────
# Gemini Config
# ─────────────────────────────────────────────
API_KEY = "AIzaSyBqEXVetJqQkDU4z17nP5zhpBWvLSKwcJY"  # ⚠️ regenerate your key
MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = (
    "You are a strict medical assistant chatbot. "
    "You only answer medical and health-related questions. "
    "If a question is unrelated to health or medicine, politely refuse and respond: "
    "'I'm sorry, I can only answer medical or health-related questions.'"
)

# ─────────────────────────────────────────────
# In-Memory Chat Store
# ─────────────────────────────────────────────
chats = {}  # chat_id -> {title, messages[]}

# ─────────────────────────────────────────────
# Gemini Call
# ─────────────────────────────────────────────
def call_gemini(messages):
    payload = {
        "contents": [{"parts": [{"text": SYSTEM_PROMPT}]}]
    }

    for msg in messages:
        payload["contents"].append({
            "parts": [{"text": f"{msg['sender'].capitalize()}: {msg['text']}"}]
        })

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"Error connecting to Gemini: {str(e)}"

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

# ✅ Create new chat ONLY via button
@app.route("/new-chat", methods=["POST"])
def new_chat():
    chat_id = str(uuid.uuid4())
    chats[chat_id] = {
        "title": "Medical Chat",
        "messages": []
    }
    return jsonify({"chatId": chat_id})

# ❌ NO auto-create here
@app.route("/chat/<chat_id>", methods=["POST"])
def chat(chat_id):
    if chat_id not in chats:
        return jsonify({"error": "Chat does not exist. Click 'New Chat' first."}), 404

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Message required"}), 400

    user_msg = {"sender": "user", "text": data["message"]}
    chats[chat_id]["messages"].append(user_msg)

    bot_reply = call_gemini(chats[chat_id]["messages"])
    chats[chat_id]["messages"].append({"sender": "bot", "text": bot_reply})

    return jsonify({"response": bot_reply})

# Load a specific chat
@app.route("/chat/<chat_id>", methods=["GET"])
def get_chat(chat_id):
    return jsonify({
        "messages": chats.get(chat_id, {}).get("messages", [])
    })

# List chats (sidebar)
@app.route("/chats", methods=["GET"])
def list_chats():
    return jsonify({
        "chats": [
            {"id": cid, "title": data["title"]}
            for cid, data in chats.items()
        ]
    })

# Reset chat
@app.route("/reset", methods=["POST"])
def reset():
    data = request.get_json()
    chat_id = data.get("chatId") if data else None

    if chat_id in chats:
        chats[chat_id]["messages"] = []

    return jsonify({"message": "Chat reset"})

# ─────────────────────────────────────────────
# Run Server
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5057,
        debug=True,
        use_reloader=False
    )
