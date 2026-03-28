import os, asyncio, random, threading, zipfile
from flask import Flask, render_template_string, request
from telethon import TelegramClient, events

app = Flask(__name__)

# --- AUTO-UNZIP & SESSION DETECTION ---
# This looks for your uploaded zip and extracts the "Keys" for your 10+ accounts
if os.path.exists('sessions_final.zip'):
    with zipfile.ZipFile('sessions_final.zip', 'r') as zip_ref:
        zip_ref.extractall('.')
    print("✅ Sessions extracted successfully!")

# Configuration
API_ID = 31537946
API_HASH = '106cc67a66bf705abe0ae56e7d588e76'
LISTENER_PHONE = '+996227015079' 

# This automatically finds all 10+ accounts from the extracted files
SENDER_ACCOUNTS = [f.replace('.session', '') for f in os.listdir('.') if f.endswith('.session') and 'temp' not in f]

state = {"status": "Idle", "sent": 0, "logs": []}
# You can add more messages here
MESSAGES = [
    "Hey! I saw you in the group, let's chat!",
    "Hello! How are you doing today?",
    "Hi there! Nice to meet you.",
    "Hey! I'm also in that Telegram group, thought I'd say hi."
]

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>
        body { font-family: sans-serif; background: #0b0e11; color: #e9eaeb; text-align: center; padding: 10px; }
        .card { background: #181c20; padding: 20px; border-radius: 15px; border: 1px solid #333; margin-bottom: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.5); }
        .btn { background: #40a7e3; color: white; padding: 18px; border: none; border-radius: 12px; width: 100%; font-size: 20px; font-weight: bold; }
        .log-box { background: #000; padding: 10px; height: 350px; overflow-y: auto; text-align: left; font-size: 13px; color: #00ff00; border-radius: 10px; border: 1px solid #444; }
        .status-on { color: #00ff00; }
        .count { font-size: 24px; color: #40a7e3; }
    </style>
</head>
<body>
    <h2>🚀 Motorola Edge 50 Control</h2>
    <div class='card'>
        <p>System Status: <b class='status-on'>{{ state.status }}</b></p>
        <p>Total Sent Today</p>
        <div class='count'>{{ state.sent }} / 200</div>
        <p><small>Using {{ sender_count }} accounts</small></p>
        <form action='/start' method='post'><button class='btn'>START MESSAGING NOW</button></form>
    </div>
    <div class='card'>
        <h4>Live Activity Log</h4>
        <div class='log-box'>
            {% for log in state.logs %}<div>> {{ log }}</div>{% endfor %}
        </div>
    </div>
</body>
</html>
"""

async def run_bot():
    state["status"] = "RUNNING (Listening for members)"
    state["logs"].insert(0, f"System started with {len(SENDER_ACCOUNTS)} accounts.")
    
    # This is your main account that "listens" to groups
    listener = TelegramClient(LISTENER_PHONE, API_ID, API_HASH)
    await listener.start()
    
    @listener.on(events.NewMessage(incoming=True))
    async def handler(event):
        # 1. Check if it's a group and if we reached the 200 limit
        if not event.is_group or state["sent"] >= 200:
            return
            
        # 2. Get the person who just spoke
        sender = await event.get_sender()
        if not sender or sender.bot:
            return

        # 3. Pick one of your 10+ accounts randomly to send the message
        random_account = random.choice(SENDER_ACCOUNTS)
        random_msg = random.choice(MESSAGES)

        # 4. Connect and send
        async with TelegramClient(random_account, API_ID, API_HASH) as sender_client:
            try:
                await sender_client.send_message(sender.id, random_msg)
                state["sent"] += 1
                state["logs"].insert(0, f"✅ Account {random_account[-4:]} messaged {sender.first_name}")
                
                # Wait 45-90 seconds between messages to stay safe from bans
                await asyncio.sleep(random.randint(45, 90))
            except Exception as e:
                state["logs"].insert(0, f"❌ Error with {random_account[-4:]}: {str(e)}")

    await listener.run_until_disconnected()

@app.route('/')
def index():
    return render_template_string(HTML, state=state, sender_count=len(SENDER_ACCOUNTS))

@app.route('/start', methods=['POST'])
def start():
    if state["status"] == "Idle":
        threading.Thread(target=lambda: asyncio.run(run_bot())).start()
    return "<h3>Automation is starting...</h3><p><a href='/'>Click here to go back to Dashboard</a></p>"

if __name__ == "__main__":
    # Render uses port 10000 by default
    app.run(host='0.0.0.0', port=10000)
  
