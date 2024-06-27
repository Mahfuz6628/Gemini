import os
from flask import Flask, request, jsonify
import sqlite3
import google.generativeai as genai

app = Flask(__name__)

# আপনার API কী এখানে সেট করুন
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)

# SQLite ডাটাবেস সেটআপ
def init_db():
    with sqlite3.connect("chatbot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                user_id TEXT,
                message TEXT
            )
        """)
        conn.commit()

@app.route('/ask', methods=['GET'])
def ask():
    query = request.args.get('q')
    user_id = request.args.get('user_id')
    if not query or not user_id:
        return jsonify({"error": "Please provide both query and user_id parameters."}), 400

    with sqlite3.connect("chatbot.db") as conn:
        cursor = conn.cursor()
        
        # পূর্ববর্তী মেসেজগুলো রিট্রিভ করা
        cursor.execute("SELECT message FROM chat_history WHERE user_id = ?", (user_id,))
        history = cursor.fetchall()
        history = [h[0] for h in history]  # টুপল থেকে মেসেজগুলো বের করা

        # নতুন মেসেজ সংরক্ষণ করা
        cursor.execute("INSERT INTO chat_history (user_id, message) VALUES (?, ?)", (user_id, query))
        conn.commit()

    chat_session = model.start_chat(
        history=history
    )

    response = chat_session.send_message(query)
    
    # নতুন উত্তর সংরক্ষণ করা
    with sqlite3.connect("chatbot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_history (user_id, message) VALUES (?, ?)", (user_id, response.text))
        conn.commit()

    return jsonify({"response": response.text})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8080)
