import os
import random
import string
import uuid
import time
import json
import requests
from datetime import datetime
import telebot
from flask import Flask, request

# --- BOT CONFIG ---
BOT_TOKEN = "8467513290:AAGByhKPJ9ToRxkiJVVey4LnSK9AoBfZGEs"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

def generate_device_info():
    ANDROID_ID = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
    USER_AGENT = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; {random.choice(['240dpi','320dpi','480dpi'])}; {random.choice(['720x1280','1080x1920','1440x2560'])}; {random.choice(['samsung','xiaomi','huawei','oneplus','google'])}; {random.choice(['SM-G975F','Mi-9T','P30-Pro','ONEPLUS-A6003','Pixel-4'])}; intel; en_US; {random.randint(100000000,999999999)})"
    WATERFALL_ID = str(uuid.uuid4())
    timestamp = int(datetime.now().timestamp())
    # This creates the new password
    raw_pwd = f"Reset@{random.randint(100,999)}#{random.randint(10,99)}"
    PASSWORD = f'#PWD_INSTAGRAM:0:{timestamp}:{raw_pwd}'
    return ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD, raw_pwd

def make_headers(mid="", user_agent=""):
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Bloks-Version-Id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
        "X-Mid": mid,
        "User-Agent": user_agent,
    }

def reset_instagram_password(reset_link):
    try:
        ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD, raw_pwd = generate_device_info()
        
        # Parse Link
        if "uidb36=" not in reset_link or "&token=" not in reset_link:
            return {"success": False, "error": "Invalid Link Format"}
            
        uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
        token = reset_link.split("&token=")[1].split(":")[0]

        # Step 1: Initial Reset Request
        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data = {"source": "one_click_login_email", "uidb36": uidb36, "device_id": ANDROID_ID, "token": token, "waterfall_id": WATERFALL_ID}
        r1 = requests.post(url, headers=make_headers(user_agent=USER_AGENT), data=data, timeout=10)
        
        if "user_id" not in r1.text:
            return {"success": False, "error": "Link expired or Instagram blocked the request."}

        mid = r1.headers.get("Ig-Set-X-Mid")
        rj = r1.json()
        
        # Step 2: Get Challenge Context
        url2 = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/"
        data2 = {
            "user_id": str(rj.get("user_id")),
            "cni": str(rj.get("cni")),
            "nonce_code": str(rj.get("nonce_code")),
            "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}',
            "challenge_context": str(rj.get("challenge_context")),
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "get_challenge": "true"
        }
        r2 = requests.post(url2, headers=make_headers(mid, USER_AGENT), data=data2, timeout=10)
        
        # Extract final context
        try:
            challenge_final = r2.text.replace('\\', '').split(f'(bk.action.i64.Const, {rj.get("cni")}), "')[1].split('", (bk.action.bool.Const, false)))')[0]
        except:
            return {"success": False, "error": "Could not bypass challenge screen."}

        # Step 3: Final Password Update (THE ACTUAL RESET)
        data3 = {
            "is_caa": "False", "cni": str(rj.get("cni")),
            "bk_client_context": {"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"},
            "challenge_context": challenge_final,
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "enc_new_password1": PASSWORD, "enc_new_password2": PASSWORD
        }
        
        final_resp = requests.post(url2, headers=make_headers(mid, USER_AGENT), data=data3, timeout=10)
        
        # VALIDATION: Check if Instagram actually said OK
        if '"status":"ok"' in final_resp.text:
            return {"success": True, "password": raw_pwd, "user_id": rj.get("user_id")}
        else:
            return {"success": False, "error": "Instagram rejected the new password."}

    except Exception as e:
        return {"success": False, "error": f"System Error: {str(e)}"}

# --- TELEGRAM WEBHOOK ---
@app.route('/api/index', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_link(message):
    wait_msg = bot.send_message(message.chat.id, "⏳ **Validating with Instagram...**\nThis takes ~8 seconds.", parse_mode="Markdown")
    result = reset_instagram_password(message.text.strip())
    
    if result.get("success"):
        msg = f"✅ **RESET SUCCESSFUL**\n\n👤 ID: `{result['user_id']}`\n🔑 Pass: `{result['password']}`\n\nCredit: @b44ner"
        bot.edit_message_text(msg, message.chat.id, wait_msg.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text(f"❌ **FAILED**\nReason: {result.get('error')}", message.chat.id, wait_msg.message_id, parse_mode="Markdown")

@app.route('/')
def index(): return "Bot is Online"
