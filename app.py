import os, asyncio, random, threading, json
from flask import Flask, render_template_string, request, redirect
from telethon import TelegramClient, events

app = Flask(__name__)

# --- CONFIG ---
API_ID = 31537946
API_HASH = '106cc67a66bf705abe0ae56e7d588e76'
DATA_DIR = './sessions'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

# Global storage for the login process
pending_logins = {}

app_state = {"active": False, "logs": [], "sent_users": set()}

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>
        body { font-family: sans-serif; background: #0b0e11; color: white; padding: 20px; }
        .card { background: #181c20; padding: 15px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #333; }
        input { width: 80%; padding: 10px; margin: 10px 0; background: #222; color: white; border: 1px solid #444; }
        .btn { padding: 12px 25px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
        .btn-blue { background: #40a7e3; color: white; }
        .btn-green { background: #28a745; color: white; }
    </style>
</head>
<body>
    <h2>📱 Bot Control Panel</h2>
    
    <div class='card'>
        <h3>Step 1: Login Account</h3>
        <form action='/send_code' method='post'>
            <input type='text' name='phone' placeholder='+91XXXXXXXXXX' required>
            <button class='btn btn-blue'>Send OTP Code</button>
        </form>
        
        {% if phone_awaiting_code %}
        <hr>
        <p style='color: #40a7e3'>Enter code for {{ phone_awaiting_code }}</p>
        <form action='/verify_code' method='post'>
            <input type='hidden' name='phone' value='{{ phone_awaiting_code }}'>
            <input type='text' name='otp' placeholder='12345' required>
            <button class='btn btn-green'>Verify & Login</button>
        </form>
        {% endif %}
    </div>

    <div class='card'>
        <h3>Step 2: Automation</h3>
        <p>Status: <b>{{ "RUNNING" if active else "PAUSED" }}</b></p>
        <a href='/toggle'><button class='btn'>{{ "STOP" if active else "START" }}</button></a>
    </div>

    <div class='card'>
        <h4>Activity Log</h4>
        <div style='font-size: 12px; color: #0f0;'>
            {% for log in logs %} <div>> {{ log }}</div> {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    phone = next(iter(pending_logins), None)
    return render_template_string(HTML_DASHBOARD, phone_awaiting_code=phone, active=app_state["active"], logs=app_state["logs"])

@app.route('/send_code', methods=['POST'])
def send_code():
    phone = request.form['phone']
    client = TelegramClient(f"{DATA_DIR}/{phone}", API_ID, API_HASH)
    
    async def get_code():
        await client.connect()
        send_obj = await client.send_code_request(phone)
        pending_logins[phone] = {"client": client, "hash": send_obj.phone_code_hash}
    
    asyncio.run(get_code())
    return redirect('/')

@app.route('/verify_code', methods=['POST'])
def verify_code():
    phone = request.form['phone']
    otp = request.form['otp']
    data = pending_logins.get(phone)
    
    async def finish():
        await data["client"].sign_in(phone, otp, phone_code_hash=data["hash"])
        app_state["logs"].insert(0, f"✅ Account {phone} Linked!")
        del pending_logins[phone]

    asyncio.run(finish())
    return redirect('/')

@app.route('/toggle')
def toggle():
    app_state["active"] = not app_state["active"]
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
    
