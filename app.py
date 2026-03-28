import os, asyncio, random, threading, json
from flask import Flask, render_template_string, request, redirect
from telethon.sync import TelegramClient
from telethon import events

app = Flask(__name__)

# --- CONFIG ---
API_ID = 31537946
API_HASH = '106cc67a66bf705abe0ae56e7d588e76'
DATA_DIR = './sessions'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

# --- DATABASE SETUP ---
DB_FILE = os.path.join(DATA_DIR, 'bot_config.json')
def load_db():
    if os.path.exists(DB_FILE):
        try: return json.load(open(DB_FILE))
        except: pass
    return {"msgs": ["Hi! Saw you in the group."], "sent": [], "active": False, "targets": []}

db = load_db()
def save_db():
    with open(DB_FILE, 'w') as f: json.dump(db, f)

# Global for the verify step
phone_awaiting = None

# --- HTML INTERFACE ---
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>
        body { font-family: sans-serif; background: #0b0e11; color: white; padding: 15px; }
        .card { background: #181c20; padding: 15px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #333; }
        .btn { padding: 12px; border: none; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 5px; }
        .btn-blue { background: #40a7e3; color: white; }
        .btn-green { background: #28a745; color: white; }
        .btn-red { background: #dc3545; color: white; }
        input { width: 90%; padding: 10px; margin: 10px 0; background: #222; color: white; border: 1px solid #444; }
    </style>
</head>
<body>
    <div class='card'>
        <h2>Status: <span style='color:{{ "green" if db.active else "red" }}'>{{ "RUNNING" if db.active else "PAUSED" }}</span></h2>
        <a href='/toggle'><button class='btn {{ "btn-red" if db.active else "btn-green" }}'>{{ "PAUSE" if db.active else "START" }}</button></a>
    </div>

    <div class='card'>
        <h3>Add Account</h3>
        <form action='/send_code' method='post'>
            <input type='text' name='phone' placeholder='+91XXXXXXXXXX' required>
            <button class='btn btn-blue'>Send OTP</button>
        </form>
        {% if phone_wait %}
        <hr>
        <p>Enter OTP for {{ phone_wait }}:</p>
        <form action='/verify_code' method='post'>
            <input type='hidden' name='phone' value='{{ phone_wait }}'>
            <input type='text' name='otp' placeholder='12345' required>
            <button class='btn btn-green'>Verify & Save</button>
        </form>
        {% endif %}
    </div>

    <div class='card'>
        <h3>Messages</h3>
        {% for m in db.msgs %}
        <div style='margin-bottom:8px;'>• {{ m }} <a href='/del_msg/{{ loop.index0 }}' style='color:red;'>[X]</a></div>
        {% endfor %}
        <form action='/add_msg' method='post'>
            <input type='text' name='msg' placeholder='Add message...' required>
            <button class='btn btn-blue'>Add</button>
        </form>
    </div>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def index():
    global phone_awaiting
    return render_template_string(HTML, db=db, phone_wait=phone_awaiting)

@app.route('/send_code', methods=['POST'])
def send_code():
    global phone_awaiting
    phone = request.form['phone']
    client = TelegramClient(f"{DATA_DIR}/{phone}", API_ID, API_HASH)
    client.connect()
    client.send_code_request(phone)
    client.disconnect()
    phone_awaiting = phone
    return redirect('/')

@app.route('/verify_code', methods=['POST'])
def verify_code():
    global phone_awaiting
    phone, otp = request.form['phone'], request.form['otp']
    client = TelegramClient(f"{DATA_DIR}/{phone}", API_ID, API_HASH)
    try:
        client.connect()
        client.sign_in(phone, otp)
        client.disconnect()
        phone_awaiting = None
    except Exception as e:
        return f"Verify Error: {e}. <a href='/'>Go Back</a>"
    return redirect('/')

@app.route('/add_msg', methods=['POST'])
def add_msg():
    db["msgs"].append(request.form['msg'])
    save_db()
    return redirect('/')

@app.route('/del_msg/<int:idx>')
def del_msg(idx):
    db["msgs"].pop(idx)
    save_db()
    return redirect('/')

@app.route('/toggle')
def toggle():
    db["active"] = not db["active"]
    save_db()
    return redirect('/')

# --- BACKGROUND AUTOMATION ---
def start_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def run():
        while True:
            if not db["active"]:
                await asyncio.sleep(10)
                continue

            sessions = [f.replace('.session','') for f in os.listdir(DATA_DIR) if f.endswith('.session')]
            if not sessions:
                await asyncio.sleep(10)
                continue

            # listener uses the first logged-in account
            client = TelegramClient(f"{DATA_DIR}/{sessions[0]}", API_ID, API_HASH)
            await client.start()

            @client.on(events.NewMessage(incoming=True))
            async def handler(event):
                if not db["active"] or not event.is_group: return
                
                # Check target groups
                chat = await event.get_chat()
                sender = await event.get_sender()
                
                # SMART FILTERS:
                # 1. No bots/admins
                # 2. No repeat messaging
                # 3. Not in your own hub
                if not sender or sender.bot or sender.id in db["sent"]: return
                if getattr(chat, 'username', '') == 'global_chattinghub': return

                try:
                    p = await client.get_permissions(event.chat_id, sender.id)
                    if p.is_admin: return
                except: pass

                # Choose random sender account
                acc = random.choice(sessions)
                async with TelegramClient(f"{DATA_DIR}/{acc}", API_ID, API_HASH) as s:
                    try:
                        await s.send_message(sender.id, random.choice(db["msgs"]))
                        db["sent"].append(sender.id)
                        save_db()
                        await asyncio.sleep(random.randint(60, 120))
                    except: pass

            await client.run_until_disconnected()

    loop.run_until_complete(run())

if __name__ == "__main__":
    threading.Thread(target=start_bot_thread, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
    
