# api/index.py
import os
import sys
import traceback
import random
import string
import uuid
import requests
import json
import asyncio
from datetime import datetime
from flask import Flask, request, Response

# Telegram imports
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Configuration ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN environment variable not set!", file=sys.stderr)
    # We'll still let Flask run, but the bot will fail gracefully when called

# --- Flask App Setup ---
app = Flask(__name__)

# --- Telegram Bot Application Setup ---
# Important: We create a single Application instance that will be reused across requests
# to avoid recreating the event loop each time.
if BOT_TOKEN:
    bot = Bot(token=BOT_TOKEN)
    ptb_app = Application.builder().token(BOT_TOKEN).build()
else:
    bot = None
    ptb_app = None

# --- Instagram Reset Functions (same as before) ---
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
        username = r.json()["user"]["username"]
        return username
    except:
        return None

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
            return {"success": False, "error": f"Reset request failed: {r.text}"}

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
        requests.post(url2, headers=make_headers(mid, USER_AGENT), data=data3)
        new_password = PASSWORD.split(":")[-1]
        
        return {
            "success": True,
            "password": new_password,
            "user_id": user_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Bot Handlers (same as before) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me an Instagram password reset link (the link from the email).\n"
        "I'll reset the password and give you the new credentials."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "uidb36=" in text and "token=" in text:
        await update.message.reply_text("⏳ Processing reset link...")

        # Run the blocking function in a thread to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, reset_instagram_password, text)

        if result.get("success"):
            user_id = result.get("user_id")
            new_password = result.get("password")
            username = id_user(user_id)
            if not username:
                username = "Unknown"

            msg = (
                "✅ *Password Reset Successful!*\n\n"
                f"👤 *Username:* `{username}`\n"
                f"🔑 *New Password:* `{new_password}`\n\n"
                "🔒 Login and change the password immediately."
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            error = result.get("error", "Unknown error")
            await update.message.reply_text(f"❌ Failed: {error}")
    else:
        await update.message.reply_text(
            "❓ That doesn't look like an Instagram reset link.\n"
            "Please send the full link from the email (contains `uidb36` and `token`)."
        )

# Register handlers only once
if ptb_app:
    ptb_app.add_handler(CommandHandler("start", start))
    ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Flask Webhook Route ---
@app.route("/api/index", methods=["POST"])
def webhook():
    if not ptb_app:
        return Response("Bot token not configured", status=500)
    
    try:
        # Parse the incoming update from Telegram
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        
        # Process the update asynchronously
        # Since we're inside a sync Flask route, we need to create a new event loop
        # for this invocation only. Vercel runs each request in a fresh environment.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(ptb_app.process_update(update))
        loop.close()
        
        return Response("ok", status=200)
    except Exception as e:
        # Log the full error to Vercel's logs
        print(f"Error processing update: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return Response("error", status=500)

# A simple GET route for health checks (optional)
@app.route("/api/index", methods=["GET"])
def health():
    return "Bot webhook is running", 200

# Vercel expects a variable named `app` as the entry point.
# This is already defined above. 
