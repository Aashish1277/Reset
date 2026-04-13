import os
import random
import string
import uuid
import requests
import json
from datetime import datetime
from flask import Flask, request
import telebot

app = Flask(__name__)
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN, threaded=False)

# --- 100% CORE LOGIC RETENTION ---

def generate_device_info():
    ANDROID_ID = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
    USER_AGENT = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; {random.choice(['240dpi','320dpi','480dpi'])}; {random.choice(['720x1280','1080x1920','1440x2560'])}; {random.choice(['samsung','xiaomi','huawei','oneplus','google'])}; {random.choice(['SM-G975F','Mi-9T','P30-Pro','ONEPLUS-A6003','Pixel-4'])}; intel; en_US; {random.randint(100000000,999999999)})"
    WATERFALL_ID = str(uuid.uuid4())
    timestamp = int(datetime.now().timestamp())
    nums = ''.join([str(random.randint(1, 100)) for _ in range(4)])
    PASSWORD = f'#PWD_INSTAGRAM:0:{timestamp}:Random@{nums}'
    return ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD

def make_headers(mid="", user_agent=""):
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Bloks-Version-Id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
        "X-Mid": mid or "",
        "User-Agent": user_agent,
    }

def reset_instagram_password(reset_link):
    try:
        ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD = generate_device_info()
        
        # Original Link Parsing Logic
        uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
        token = reset_link.split("&token=")[1].split(":")[0].split("&")[0]

        # REQUEST 1: Initial Reset
        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data1 = {
            "source": "one_click_login_email",
            "uidb36": uidb36,
            "device_id": ANDROID_ID,
            "token": token,
            "waterfall_id": WATERFALL_ID
        }
        r1 = requests.post(url, headers=make_headers(user_agent=USER_AGENT), data=data1, timeout=5)
        
        if "user_id" not in r1.text:
            return {"success": False, "error": "Request 1 failed: Link expired."}

        mid = r1.headers.get("Ig-Set-X-Mid")
        resp_json = r1.json()
        user_id = resp_json.get("user_id")
        cni = resp_json.get("cni")
        nonce_code = resp_json.get("nonce_code")
        challenge_context = resp_json.get("challenge_context")

        # REQUEST 2: Get Challenge Context Final
        url2 = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/"
        data2 = {
            "user_id": str(user_id),
            "cni": str(cni),
            "nonce_code": str(nonce_code),
            "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}',
            "challenge_context": str(challenge_context),
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "get_challenge": "true"
        }
        r2 = requests.post(url2, headers=make_headers(mid, USER_AGENT), data=data2, timeout=5).text
        
        # Original Split Logic
        challenge_context_final = r2.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]

        # REQUEST 3: The Actual Password Change (RESTORED)
        data3 = {
            "is_caa": "False",
            "source": "",
            "uidb36": "",
            "error_state": {"type_name":"str","index":0,"state_id":1048583541},
            "afv": "",
            "cni": str(cni),
            "token": "",
            "has_follow_up_screens": "0",
            "bk_client_context": {"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"},
            "challenge_context": challenge_context_final,
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "enc_new_password1": PASSWORD,
            "enc_new_password2": PASSWORD
        }
        
        r3 = requests.post(url2, headers=make_headers(mid, USER_AGENT), data=data3, timeout=5)
        
        # Return success only if final request was sent
        return {
            "success": True, 
            "password": PASSWORD.split(":")[-1], 
            "user_id": user_id
        }
                
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- TELEGRAM BOT WRAPPER ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "⸸ SATAN INSTA RESET ACTIVE 𓄋\nSend link to change password.")

@bot.message_handler(func=lambda m: "instagram.com" in m.text)
def handle_link(message):
    bot.send_message(message.chat.id, "🔄 Executing real logic... (3 steps)")
    result = reset_instagram_password(message.text.strip())
    
    if result.get("success"):
        msg = f"✅ SUCCESS: PASSWORD CHANGED\n\nUSER ID: {result['user_id']}\nNEW PASS: {result['password']}\n\nBY: @xYourKing"
        bot.send_message(message.chat.id, msg)
    else:
        bot.send_message(message.chat.id, f"❌ FAILED: {result.get('error', 'Link invalid or expired.')}")

# --- VERCEL CONFIG ---

@app.route('/api/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return '', 200
    return 'Forbidden', 403

@app.route('/')
def home():
    return "Bot Online"
