import os, asyncio, random, threading
from flask import Flask, render_template_string, request
from telethon import TelegramClient, events

app = Flask(__name__)

# --- CONFIG ---
API_ID = 31537946
API_HASH = '106cc67a66bf705abe0ae56e7d588e76'
TARGET_GROUPS = ['english_practice_group', 'global_chattinghub'] # Add your targets here

state = {"status": "Idle", "sent": 0, "logs": [], "temp_client": None}

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>
        body { font-family: sans-serif; background: #0b0e11; color: #e9eaeb; text-align: center; padding: 10px; }
        .card { background: #181c20; padding: 20px; border-radius: 15px; border: 1px solid #333; margin-bottom: 20px; }
        .btn { background: #40a7e3; color: white; padding: 15px; border: none; border-radius: 10px; width: 100%; margin-top: 10px; }
        input { width: 90%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #444; background: #222; color: white; }
    </style>
</head>
<body>
    <h2>Account Manager</h2>
    <div class='card'>
        <p>Status: {{ state.status }} | Sent: {{ state.sent }}</p>
        <form action='/login' method='post'>
            <input type='text' name='phone' placeholder='+91XXXXXXXXXX' required>
            <button class='btn'>Login New Account</button>
        </form>
        <hr>
        <form action='/start' method='post'><button class='btn' style='background:#28a745'>START AUTOMATION</button></form>
    </div>
    <div class='card'>
        <div style='text-align:left; font-size:12px; height:200px; overflow-y:auto;'>
            {% for log in state.logs %}<div>> {{ log }}</div>{% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML, state=state)

@app.route('/login', methods=['POST'])
def login():
    phone = request.form['phone']
    # This creates a session file directly on the server
    client = TelegramClient(phone, API_ID, API_HASH)
    state["logs"].insert(0, f"Logging in {phone}... Check Telegram for code.")
    # In a real web app, you'd handle the code input here. 
    # For now, we will use the Render Terminal to enter the code.
    threading.Thread(target=lambda: asyncio.run(client.start(phone))).start()
    return "Check your Render Logs to enter the code! <a href='/'>Back</a>"

@app.route('/start', methods=['POST'])
def start():
    # Logic to rotate through saved .session files and message group members
    state["status"] = "Running"
    return "Bot Started! <a href='/'>Back</a>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
    
