from flask import Flask, request, jsonify, render_template
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
client = Anthropic()

SYSTEM_PROMPT = """You are FitBot, an expert AI fitness and gym coach.
Help users with workout plans, exercises, nutrition, and fitness goals.
Keep answers practical, motivating, and concise."""

chat_history = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    chat_history.append({"role": "user", "content": user_message})
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=chat_history
    )
    bot_reply = response.content[0].text
    chat_history.append({"role": "assistant", "content": bot_reply})
    return jsonify({"reply": bot_reply})

if __name__ == "__main__":
    app.run(debug=True)