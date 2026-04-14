import os
import random
import string
import uuid
import time
import json
import base64
import requests
from datetime import datetime
from hashlib import md5

# Telebot & Flask
import telebot
from flask import Flask, request

# Original imports for logic
from user_agent import generate_user_agent
from bs4 import BeautifulSoup

# --- BOT INITIALIZATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# --- 100% CORE LOGIC RETENTION (UNALTERED) ---

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
        "X-Mid": mid,
        "User-Agent": user_agent,
        "Content-Length": "9481"
    }

def id_user(user_id):
    try:
        url = f"https://i.instagram.com/api/v1/users/{user_id}/info/"
        headers = {"User-Agent": "Instagram 219.0.0.12.117 Android"}
        r = requests.get(url, headers=headers)
        try:
            return r.json()["user"]["username"]
        except:
            return f"ID:{user_id}"
    except:
        return f"ID:{user_id}"

def reset_instagram_password(reset_link):
    try:
        ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD = generate_device_info()
        uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
        token = reset_link.split("&token=")[1].split(":")[0]

        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data = {
            "source": "one_click_login_email",
            "uidb36": uidb36,
            "device_id": ANDROID_ID,
            "token": token,
            "waterfall_id": WATERFALL_ID
        }
        r = requests.post(url, headers=make_headers(user_agent=USER_AGENT), data=data)
        
        if "user_id" not in r.text:
            return {"success": False, "error": f"Error in reset request: {r.text}"}

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
        r2 = requests.post(url2, headers=make_headers(mid, USER_AGENT), data=data2).text
        
        challenge_context_final = r2.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]

        data3 = {
            "is_caa": "False", "source": "", "uidb36": "",
            "error_state": {"type_name":"str","index":0,"state_id":1048583541},
            "afv": "", "cni": str(cni), "token": "", "has_follow_up_screens": "0",
            "bk_client_context": {"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"},
            "challenge_context": challenge_context_final,
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "enc_new_password1": PASSWORD, "enc_new_password2": PASSWORD
        }
        
        requests.post(url2, headers=make_headers(mid, USER_AGENT), data=data3)
        return {"success": True, "password": PASSWORD.split(":")[-1], "user_id": user_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- TELEGRAM WEBHOOK HANDLERS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "⸸ SATAN INSTAGRAM RESET 𓄋\n━━━━━━━━━━━━━━\nSend your Instagram reset link.")

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_link(message):
    bot.send_message(message.chat.id, "⏳ Processing reset... Vercel runtime active.")
    result = reset_instagram_password(message.text.strip())
    
    if result.get("success"):
        username = id_user(result.get("user_id"))
        msg = f'''𓄅 𝗦𝗔𝗧𝗔𝗡 𝗦𝗘𝗡𝗗 𝗔 𝗠𝗘𝗦𝗦𝗔𝗚𝗘\n\n[+] 𝗨𝗦𝗘𝗥𝗡𝗔𝗠𝗘 : {username}\n[+] 𝗣𝗔𝗦𝗦𝗪𝗢𝗥𝗗: {result.get("password")}\n\n𝗕𝗬 : @xYourKing 𝗖𝗛 : @xPythonTool'''
        bot.send_message(message.chat.id, msg)
    else:
        bot.send_message(message.chat.id, f"❌ Failed: {result.get('error')}")

# --- VERCEL ENTRY POINT ---

@app.route('/api/index', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Method Not Allowed', 403

@app.route('/')
def index():
    return "<h1>Bot is Online via Webhook</h1>"
