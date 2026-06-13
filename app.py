from flask import Flask, request, jsonify, render_template
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are FitBot, a professional gym trainer with 10 years of experience.
You speak in a motivating, energetic and friendly tone like a real gym trainer.

When a user first messages you, ask them:
1. Their fitness level (beginner, intermediate, advanced)
2. Their goal (weight loss, muscle gain, endurance, general fitness)
3. Available equipment (gym, home, no equipment)
4. Available time per day (30 mins, 1 hour, etc.)

Then give them a personalized plan with:
- Specific exercises with sets and reps
- Rest times between sets
- Weekly schedule
- Diet and nutrition tips

Use emojis to keep conversation fun and motivating 💪🔥
Always recommend consulting a doctor for any injuries or health issues."""

chat_history = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")

    chat_history.append({
        "role": "user",
        "content": user_message
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *chat_history
        ],
        max_tokens=1024
    )

    bot_reply = response.choices[0].message.content

    chat_history.append({
        "role": "assistant",
        "content": bot_reply
    })

    return jsonify({"reply": bot_reply})

if __name__ == "__main__":
    app.run(debug=True)