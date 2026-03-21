import json
import os
import time
import threading
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, CallbackContext

APPROVAL_FILE = Path("pending_approval.json")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def load_approval():
    if APPROVAL_FILE.exists():
        try:
            return json.loads(APPROVAL_FILE.read_text())
        except:
            return None
    return None

def save_approval(data):
    APPROVAL_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def delete_approval():
    if APPROVAL_FILE.exists():
        APPROVAL_FILE.unlink()

def start_command(update: Update, context: CallbackContext):
    global CHAT_ID
    CHAT_ID = str(update.effective_chat.id)
    os.environ["TELEGRAM_CHAT_ID"] = CHAT_ID
    env_path = Path(".env")
    lines = []
    if env_path.exists():
        lines = env_path.read_text().splitlines()
    found = False
    new_lines = []
    for line in lines:
        if line.startswith("TELEGRAM_CHAT_ID="):
            new_lines.append("TELEGRAM_CHAT_ID=" + CHAT_ID)
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append("TELEGRAM_CHAT_ID=" + CHAT_ID)
    env_path.write_text("\n".join(new_lines) + "\n")
    update.message.reply_text("THEIA Guard baglandi!\nChat ID: " + CHAT_ID)

def approval_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    approval = load_approval()
    if approval and approval.get("status") == "sent":
        if data == "approve":
            approval["status"] = "approved"
            icon = "ONAYLANDI"
        else:
            approval["status"] = "denied"
            icon = "REDDEDILDI"
        save_approval(approval)
        query.answer(icon)
        query.edit_message_text(
            query.message.text + "\n\n" + icon,
            parse_mode="Markdown"
        )
    else:
        query.answer("Bu istek zaten islenmis.")

def check_and_send_approval(bot):
    global CHAT_ID
    if not CHAT_ID:
        return
    approval = load_approval()
    if approval and approval.get("status") == "pending":
        risk = approval.get("risk_level", "unknown")
        command = approval.get("command", "unknown")
        risk_icons = {"medium": "SARI - Orta Risk", "high": "KIRMIZI - Yuksek Risk"}
        icon = risk_icons.get(risk, "Risk: " + risk.upper())
        text = "THEIA GUARD ONAY TALEBI\n" + "=" * 30 + "\n"
        text += "Risk: " + icon + "\n"
        text += "Komut: `" + command + "`\n"
        text += "\nBu komutu onayliyor musunuz?"
        keyboard = [[
            InlineKeyboardButton("Onayla", callback_data="approve"),
            InlineKeyboardButton("Reddet", callback_data="deny")
        ]]
        markup = InlineKeyboardMarkup(keyboard)
        try:
            bot.send_message(
                chat_id=int(CHAT_ID),
                text=text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
            approval["status"] = "sent"
            save_approval(approval)
        except Exception as e:
            print("Telegram hatasi: " + str(e))

def polling_loop(updater):
    while True:
        try:
            check_and_send_approval(updater.bot)
        except Exception as e:
            print("Polling hatasi: " + str(e))
        time.sleep(2)

def main():
    global CHAT_ID
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    os.environ["TELEGRAM_BOT_TOKEN"] = token
                elif line.startswith("TELEGRAM_CHAT_ID="):
                    CHAT_ID = line.split("=", 1)[1].strip()
                    os.environ["TELEGRAM_CHAT_ID"] = CHAT_ID
    if not token:
        print("HATA: TELEGRAM_BOT_TOKEN bulunamadi!")
        print("Telegram\'da @BotFather -> /newbot")
        print("Sonra: export TELEGRAM_BOT_TOKEN=token_degerin")
        return
    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CallbackQueryHandler(approval_callback))
    updater.start_polling()
    print("THEIA Guard Telegram Bot aktif!")
    print("Chat ID: " + str(CHAT_ID if CHAT_ID else "Henuz baglanmadi"))
    print("Telegram\'da /start yazin")
    polling_thread = threading.Thread(target=polling_loop, args=(updater,), daemon=True)
    polling_thread.start()
    updater.idle()

if __name__ == "__main__":
    main()
