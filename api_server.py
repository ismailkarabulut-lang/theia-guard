from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pathlib import Path
import json

app = Flask(__name__)
CORS(app)

BASE = Path.home() / "Masaüstü" / "theia-guard-core"
LOG = BASE / "theia_guard_log.json"
APPROVAL = BASE / "pending_approval.json"
DASHBOARD = Path.home() / "Masaüstü" / "theia-guard" / "dashboard.html"

def read_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            return []
    return []

@app.route("/")
def index():
    return send_file(DASHBOARD)

@app.route("/api/stats")
def stats():
    entries = read_json(LOG)
    return jsonify({
        "total": len(entries),
        "auto": sum(1 for e in entries if e.get("decision") == "auto_approved"),
        "approved": sum(1 for e in entries if "approved" in e.get("decision","") and e.get("decision") != "auto_approved"),
        "denied": sum(1 for e in entries if "denied" in e.get("decision","")),
        "blocked": sum(1 for e in entries if e.get("decision") == "blocked"),
    })

@app.route("/api/logs")
def logs():
    entries = read_json(LOG)
    return jsonify(list(reversed(entries[-50:])))

@app.route("/api/pending")
def pending():
    data = read_json(APPROVAL)
    if isinstance(data, dict) and data.get("status") == "pending":
        return jsonify(data)
    return jsonify(None)

@app.route("/api/approve", methods=["POST"])
def approve():
    if APPROVAL.exists():
        data = json.loads(APPROVAL.read_text())
        data["status"] = "approved"
        APPROVAL.write_text(json.dumps(data))
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/api/deny", methods=["POST"])
def deny():
    if APPROVAL.exists():
        data = json.loads(APPROVAL.read_text())
        data["status"] = "denied"
        APPROVAL.write_text(json.dumps(data))
        return jsonify({"ok": True})
    return jsonify({"ok": False})
import feedparser

KEYWORDS = ["yapay zeka", "artificial intelligence", "AI", "LLM",
            "ajan", "agent", "ChatGPT", "Claude", "Gemini"]

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=yapay+zeka&hl=tr&gl=TR&ceid=TR:tr",
    "https://news.google.com/rss/search?q=artificial+intelligence&hl=tr&gl=TR&ceid=TR:tr",
]

@app.route("/api/news")
def news():
    results = []
    seen = set()
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:15]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            if link in seen:
                continue
            seen.add(link)
            if any(kw.lower() in title.lower() for kw in KEYWORDS):
                results.append({
                    "title": title,
                    "link": link,
                    "published": entry.get("published", "")
                })
    return jsonify(results[:20])
@app.route("/chat")
def chat_page():
    return send_file(Path.home() / "Masaüstü" / "theia-guard" / "theia_chat.html")
import requests as req
@app.route("/api/chat", methods=["POST"])
def chat_proxy():
    import os
    key = ""
    env_path = Path.home() / "Masaüstü" / "theia-guard" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        return jsonify({"error": "API key bulunamadı"}), 500
    data = request.get_json()
    r = req.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json=data,
        timeout=30
    )
    return jsonify(r.json())
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

