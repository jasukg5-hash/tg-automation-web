import os, asyncio, random, threading, json
from flask import Flask, render_template_string, request, redirect
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

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
        return json.load(open(DB_FILE))
    return {"msgs": ["Hi! How are you?"], "sent": [], "active": False, "targets": ["english_practice_group"]}

db = load_db()
def save_db():
    with open(DB_FILE, 'w') as f: json.dump(db, f)

# Temp storage for login process
pending = {}

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
        input, textarea { width: 90%; padding: 10px; margin: 10px 0; background: #222; color: white; border: 1px solid #444; }
    </style>
</head>
<body>
    <div class='card'>
        <h2>Status: <span style='color:{{ "green" if db.active else "red" }}'>{{ "RUNNING" if db.active else "PAUSED" }}</span></h2>
        <a href='/toggle'><button class='btn {{ "btn-red" if db.active else "btn-green" }}'>{{ "PAUSE BOT" if db.active else "START BOT" }}</button></a>
    </div>

    <div class='card'>
        <h3>1. Add Account</h3>
        <form action='/send_code' method='post'>
            <input type='text' name='phone' placeholder='+91XXXXXXXXXX' required>
            <button class='btn btn-blue'>Send Code</button>
        </form>
        {% if phone_wait %}
        <hr>
        <p>Enter code for {{ phone_wait }}:</p>
        <form action='/verify_code' method='post'>
            <input type='hidden' name='phone' value='{{ phone_wait }}'>
            <input type='text' name='otp' placeholder='12345' required>
            <button class='btn btn-green'>Verify & Save</button>
        </form>
        {% endif %}
    </div>

    <div class='card'>
        <h3>2. Edit Messages</h3>
        {% for m in db.msgs %}
        <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
            <span>{{ m }}</span> <a href='/del_msg/{{ loop.index0 }}' style='color:red;'>[X]</a>
        </div>
        {% endfor %}
        <form action='/add_msg' method='post'>
            <input type='text' name='msg' placeholder='New message...' required>
            <button class='btn btn-blue'>Add Message</button>
        </form>
    </div>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def index():
    phone = next(iter(pending), None)
    return render_template_string(HTML, db=db, phone_wait=phone)

@app.route('/send_code', methods=['POST'])
def send_code():
    phone = request.form['phone']
    client = TelegramClient(f"{DATA_DIR}/{phone}", API_ID, API_HASH)
    async def go():
        await client.connect()
        h = await client.send_code_request(phone)
        pending[phone] = {"c": client, "h": h.phone_code_hash}
    asyncio.run(go())
    return redirect('/')

@app.route('/verify_code', methods=['POST'])
def verify_code():
    phone, otp = request.form['phone'], request.form['otp']
    async def go():
        data = pending.get(phone)
        await data["c"].sign_in(phone, otp, phone_code_hash=data["h"])
        del pending[phone]
    try:
        asyncio.run(go())
    except Exception as e:
        return f"Error: {e}. Try again."
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

# --- BACKGROUND BOT ---
async def bot_task():
    while True:
        if not db["active"]:
            await asyncio.sleep(5)
            continue
        
        sessions = [f.replace('.session','') for f in os.listdir(DATA_DIR) if f.endswith('.session')]
        if not sessions:
            await asyncio.sleep(10)
            continue
            
        # Use first account as listener
        listener = TelegramClient(f"{DATA_DIR}/{sessions[0]}", API_ID, API_HASH)
        await listener.start()
        
        @listener.on(events.NewMessage(incoming=True))
        async def handler(event):
            if not db["active"] or not event.is_group: return
            
            sender = await event.get_sender()
            if not sender or sender.bot or sender.id in db["sent"]: return
            
            # Logic to skip admins and your group members goes here
            acc = random.choice(sessions)
            async with TelegramClient(f"{DATA_DIR}/{acc}", API_ID, API_HASH) as s:
                try:
                    await s.send_message(sender.id, random.choice(db["msgs"]))
                    db["sent"].append(sender.id)
                    save_db()
                    await asyncio.sleep(60)
                except: pass

        await listener.run_until_disconnected()

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(bot_task())).start()
    app.run(host='0.0.0.0', port=10000)
    
