import os, asyncio, random, threading, json
from flask import Flask, render_template_string, request, redirect
from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins

app = Flask(__name__)

# --- SETTINGS ---
API_ID = 31537946
API_HASH = '106cc67a66bf705abe0ae56e7d588e76'
MY_GROUP = 'global_chattinghub'
# Path for persistent storage (Change to './' if not using Render Disk)
DATA_DIR = './sessions/' 
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

# --- DATABASE ---
DB_FILE = os.path.join(DATA_DIR, 'bot_data.json')
def load_db():
    if os.path.exists(DB_FILE):
        return json.load(open(DB_FILE))
    return {"messages": ["Hello!", "Hey, let's chat!"], "sent_users": [], "active": False}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- HTML DASHBOARD ---
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0b0e11; color: #fff; padding: 15px; }
        .card { background: #181c20; padding: 20px; border-radius: 15px; margin-bottom: 15px; border: 1px solid #333; }
        .btn { padding: 12px; border: none; border-radius: 8px; color: #fff; font-weight: bold; width: 100%; cursor: pointer; margin: 5px 0; }
        .btn-start { background: #28a745; } .btn-pause { background: #dc3545; } .btn-add { background: #40a7e3; }
        input, textarea { width: 95%; padding: 10px; margin: 10px 0; background: #222; border: 1px solid #444; color: #fff; border-radius: 5px; }
        .log-box { background: #000; padding: 10px; height: 200px; overflow-y: auto; font-size: 12px; color: #0f0; border: 1px solid #444; }
        .msg-item { background: #222; padding: 5px; margin: 5px; border-radius: 5px; display: flex; justify-content: space-between; }
    </style>
</head>
<body>
    <h2>🚀 TG Master Panel</h2>
    
    <div class='card'>
        <h3>Status: <span style='color:{{ "green" if db.active else "red" }}'>{{ "RUNNING" if db.active else "PAUSED" }}</span></h3>
        <form action='/toggle' method='post'>
            <button class='btn {{ "btn-pause" if db.active else "btn-start" }}'>
                {{ "PAUSE BOT" if db.active else "START BOT" }}
            </button>
        </form>
    </div>

    <div class='card'>
        <h4>Add New Account</h4>
        <form action='/add_account' method='post'>
            <input type='text' name='phone' placeholder='+91XXXXXXXXXX' required>
            <button class='btn btn-add'>Request Login Code</button>
        </form>
        <p><small>Check Render Terminal/Logs to enter the code.</small></p>
    </div>

    <div class='card'>
        <h4>Message Templates</h4>
        {% for m in db.messages %}
        <div class='msg-item'>{{ m }} <a href='/del_msg/{{ loop.index0 }}' style='color:red'>[X]</a></div>
        {% endfor %}
        <form action='/add_msg' method='post'>
            <input type='text' name='new_msg' placeholder='Type new message...'>
            <button class='btn btn-add'>Add Message</button>
        </form>
    </div>
</body>
</html>
"""

# --- BOT LOGIC ---
async def start_automation():
    while True:
        if not db["active"]:
            await asyncio.sleep(5)
            continue
            
        sessions = [f.replace('.session','') for f in os.listdir(DATA_DIR) if f.endswith('.session')]
        if not sessions: 
            await asyncio.sleep(10)
            continue

        # Main Listener Account (First one in list)
        listener_phone = sessions[0]
        client = TelegramClient(os.path.join(DATA_DIR, listener_phone), API_ID, API_HASH)
        
        try:
            await client.start()
            @client.on(events.NewMessage(incoming=True))
            async def handler(event):
                if not db["active"] or not event.is_group: return
                
                sender = await event.get_sender()
                if not sender or sender.bot: return
                if sender.id in db["sent_users"]: return # Already messaged check

                # Filter: Don't message if sender is Admin or in My Group
                try:
                    # Quick check if user is admin
                    perms = await client.get_permissions(event.chat_id, sender.id)
                    if perms.is_admin: return
                except: pass

                # Pick random sender account
                acc = random.choice(sessions)
                msg = random.choice(db["messages"])
                
                async with TelegramClient(os.path.join(DATA_DIR, acc), API_ID, API_HASH) as s_client:
                    try:
                        await s_client.send_message(sender.id, msg)
                        db["sent_users"].append(sender.id)
                        save_db(db)
                        await asyncio.sleep(random.randint(60, 120))
                    except: pass

            await client.run_until_disconnected()
        except:
            await asyncio.sleep(10)

# --- ROUTES ---
@app.route('/')
def index(): return render_template_string(HTML, db=db)

@app.route('/toggle', methods=['POST'])
def toggle():
    db["active"] = not db["active"]
    save_db(db)
    return redirect('/')

@app.route('/add_msg', methods=['POST'])
def add_msg():
    db["messages"].append(request.form['new_msg'])
    save_db(db)
    return redirect('/')

@app.route('/add_account', methods=['POST'])
def add_account():
    phone = request.form['phone']
    # This runs the login in a thread so you can enter the code in Render Logs
    def login():
        c = TelegramClient(os.path.join(DATA_DIR, phone), API_ID, API_HASH)
        c.start(phone)
    threading.Thread(target=login).start()
    return "Check Render Logs/Terminal to enter the code! <a href='/'>Back</a>"

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(start_automation())).start()
    app.run(host='0.0.0.0', port=10000)
    
