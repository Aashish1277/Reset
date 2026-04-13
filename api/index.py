import os
import random
import string
import uuid
import requests
import json
from datetime import datetime
from flask import Flask, request
import telebot
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- CORE LOGIC RETENTION ---

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
    }

def id_user(user_id):
    try:
        url = f"https://i.instagram.com/api/v1/users/{user_id}/info/"
        headers = {"User-Agent": "Instagram 219.0.0.12.117 Android"}
        r = requests.get(url, headers=headers, timeout=5)
        return r.json()["user"]["username"]
    except:
        return "Unknown"

def reset_instagram_password(reset_link):
    try:
        ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD = generate_device_info()
        
        # Improved Parsing for the link format in your screenshot
        parsed_url = urlparse(reset_link)
        params = parse_qs(parsed_url.query)
        
        uidb36 = params.get('uidb36', [None])[0]
        token_full = params.get('token', [None])[0]
        
        if not uidb36 or not token_full:
            return {"success": False, "error": "Invalid Link Format"}
            
        token = token_full.split(':')[0]

        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data = {
            "source": "one_click_login_email",
            "uidb36": uidb36,
            "device_id": ANDROID_ID,
            "token": token,
            "waterfall_id": WATERFALL_ID
        }
        
        r = requests.post(url, headers=make_headers(user_agent=USER_AGENT), data=data, timeout=8)
        
        if "user_id" not in r.text:
            return {"success": False, "error": "Link expired or Instagram blocked the request."}

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
        
        r2_req = requests.post(url2, headers=make_headers(mid, USER_AGENT), data=data2, timeout=8)
        r2 = r2_req.text
        
        challenge_context_final = r2.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]

        data3 = {
            "is_caa": "False",
            "cni": str(cni),
            "bk_client_context": {"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"},
            "challenge_context": challenge_context_final,
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "enc_new_password1": PASSWORD,
            "enc_new_password2": PASSWORD
        }
        
        requests.post(url2, headers=make_headers(mid, USER_AGENT), data=data3, timeout=8)
        return {"success": True, "password": PASSWORD.split(":")[-1], "user_id": user_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- TELEGRAM HANDLERS ---

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "⸸ SATAN INSTA RESET 𓄋\nSend me the Instagram Reset Link to start.")

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_reset(message):
    bot.send_message(message.chat.id, "🔄 Processing Reset Link... Please wait.")
    result = reset_instagram_password(message.text.strip())
    
    if result.get("success"):
        username = id_user(result.get("user_id"))
        msg = f"𓄅 𝗦𝗔𝗧𝗔𝗡 𝗦𝗘𝗡𝗗 𝗔 𝗠𝗘𝗦𝗦𝗔𝗚𝗘\n\n[+] 𝗨𝗦𝗘𝗥𝗡𝗔𝗠𝗘 : {username}\n[+] 𝗣𝗔𝗦𝗦𝗪𝗢𝗥𝗗: {result.get('password')}\n\n𝗕𝗬 : @xYourKing"
        bot.send_message(message.chat.id, msg)
    else:
        # This part was missing in your original code, which is why it looked stuck
        error_msg = result.get("error", "Unknown Error")
        bot.send_message(message.chat.id, f"❌ Reset Failed\nReason: {error_msg}")

@app.route('/api/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

@app.route('/')
def index():
    return "Bot is active"
