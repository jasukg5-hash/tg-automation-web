import os, asyncio, random, threading, zipfile
from flask import Flask, render_template_string, request
from telethon import TelegramClient, events

app = Flask(__name__)

# --- AUTO-UNZIP SESSIONS ---
if os.path.exists('sessions_final.zip'):
    with zipfile.ZipFile('sessions_final.zip', 'r') as zip_ref:
        zip_ref.extractall('.')
    print("✅ Sessions extracted successfully!")

# --- CONFIG ---
API_ID = 31537946
API_HASH = '106cc67a66bf705abe0ae56e7d588e76'
LISTENER_PHONE = '+996227015079' 
# The script will find all .session files automatically
SENDER_ACCOUNTS = [f.replace('.session', '') for f in os.listdir('.') if f.endswith('.session')]

state = {"status": "Idle", "sent": 0, "logs": []}
MESSAGES = ["Hey! How are you?", "Hi, nice to meet you!"]

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>
        body { font-family: sans-serif; background: #0b0e11; color: #e9eaeb; text-align: center; padding: 20px; }
        .card { background: #181c20; padding: 20px; border-radius: 15px; border: 1px solid #333; margin-bottom: 20px; }
        .btn { background: #40a7e3; color: white; padding: 15px; border: none; border-radius: 10px; width: 100%; font-size: 18px; }
        .log-box { background: #000; padding: 10px; height: 300px; overflow-y: auto; text-align: left; font-size: 12px; color: #00ff00; }
    </style>
</head>
<body>
    <h2>TG Automation Web</h2>
    <div class='card'>
        <p>Status: <b>{{ state.status }}</b> | Sent: <b>{{ state.sent }}/200</b></p>
        <form action='/start' method='post'><button class='btn'>START NOW</button></form>
    </div>
    <div class='card'><div class='log-box'>
        {% for log in state.logs %}<div>> {{ log }}</div>{% endfor %}
    </div></div>
</body>
</html>
"""

async def run_bot():
    state["status"] = "Running"
    client = TelegramClient(LISTENER_PHONE, API_ID, API_HASH)
    await client.start()
    
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if not event.is_group or state["sent"] >= 200: return
        sender = await event.get_sender()
        if not sender or sender.bot: return

        # Rotate accounts
        phone = random.choice(SENDER_ACCOUNTS)
        async with TelegramClient(phone, API_ID, API_HASH) as s_client:
            try:
                await s_client.send_message(sender.id, random.choice(MESSAGES))
                state["sent"] += 1
                state["logs"].insert(0, f"Sent to {sender.first_name} via {phone}")
                await asyncio.sleep(random.randint(45, 90))
            except Exception as e:
                state["logs"].insert(0, f"Error: {str(e)}")

    await client.run_until_disconnected()

@app.route('/')
def index(): return render_template_string(HTML, state=state)

@app.route('/start', methods=['POST'])
def start():
    if state["status"] == "Idle":
        threading.Thread(target=lambda: asyncio.run(run_bot())).start()
    return "Started! Refresh home page."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
  
