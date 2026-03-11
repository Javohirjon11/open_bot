import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8620408910"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mysecret123")

VOTE_LINK = "https://openbudget.uz/boards/initiatives/initiative/53/a55ad836-73cb-4b9c-a7d7-88175e63fe4d"

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi. Render Environment Variables ga BOT_TOKEN qo'shing.")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# APP
# =========================
flask_app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()

user_data = {}

menu = ReplyKeyboardMarkup(
    [
        ["🗳 Ovoz berish"],
        ["📸 Screenshot yuborish"]
    ],
    resize_keyboard=True
)

# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    text = f"""
👋 Assalomu alaykum {user.first_name}!

🇺🇿 Open Budget loyihasini qo‘llab-quvvatlaganingiz uchun rahmat.

📱 Ovoz berish operatorlari:

• Uzmobile
• Ucell
• Mobiuz
• Beeline

📌 Jarayon:

1️⃣ 🗳 Ovoz berish tugmasini bosing
2️⃣ 📱 Ovoz bergan telefon raqamingizni kiriting
3️⃣ 📸 Screenshot yuboring
4️⃣ 💳 Karta raqamingizni yuboring

🔎 Admin tekshiradi.

⏳ Natija 1 – 1.5 soat ichida aniqlanadi.

✅ Agar ovozingiz haqiqiy bo‘lsa pul karta hisobingizga tushadi.
"""
    await update.message.reply_text(text, reply_markup=menu)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()

    if text == "🗳 Ovoz berish":
        await update.message.reply_text(
            f"🗳 Quyidagi link orqali ovoz bering:\n\n{VOTE_LINK}"
        )
        await update.message.reply_text(
            "📱 Endi ovoz bergan telefon raqamingizni yuboring.\n\nMasalan:\n+998901234567"
        )
        user_data[user_id] = {
            "step": "phone",
            "photos": []
        }
        return

    if text == "📸 Screenshot yuborish":
        if user_id not in user_data:
            user_data[user_id] = {"photos": []}

        user_data[user_id]["step"] = "screenshot"
        user_data[user_id].setdefault("photos", [])

        await update.message.reply_text(
            "📸 Screenshot yuboring.\nTelefon raqam ko‘rinib turishi kerak."
        )
        return

    if user_id in user_data and user_data[user_id].get("step") == "phone":
        user_data[user_id]["phone"] = text
        user_data[user_id]["step"] = "screenshot"

        await update.message.reply_text(
            "📸 Endi ovoz berganingizni tasdiqlovchi screenshot yuboring."
        )
        return

    if user_id in user_data and user_data[user_id].get("step") == "screenshot":
        card = text.replace(" ", "")

        if len(card) != 16 or not card.isdigit():
            await update.message.reply_text(
                "❌ Karta noto‘g‘ri.\n\n16 xonali karta kiriting."
            )
            return

        phone = user_data[user_id].get("phone", "Kiritilmagan")

        admin_text = f"""
📥 Yangi ovoz

👤 Ism: {user.first_name}
🆔 ID: {user_id}

📱 Telefon: {phone}
💳 Karta: {card}

👤 [Foydalanuvchi bilan bog‘lanish](tg://user?id={user_id})
"""

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="Markdown"
        )

        for photo in user_data[user_id].get("photos", []):
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo)

        await update.message.reply_text(
            "✅ Ma'lumotlar qabul qilindi.\n\n"
            "🔎 Tekshiruvga yuborildi.\n"
            "⏳ Natija 1 – 1.5 soat ichida chiqadi."
        )

        user_data.pop(user_id, None)
        return

    await update.message.reply_text(
        "Iltimos, menyudan tugmani tanlang yoki /start bosing."
    )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photo = update.message.photo[-1].file_id

    if user_id not in user_data:
        user_data[user_id] = {
            "step": "screenshot",
            "photos": []
        }

    user_data[user_id].setdefault("photos", [])
    user_data[user_id]["photos"].append(photo)

    await update.message.reply_text(
        "📸 Screenshot qabul qilindi.\n\n"
        "Yana yuborishingiz mumkin yoki 💳 karta raqamingizni yuboring."
    )


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        user_id = int(context.args[0])
        message = " ".join(context.args[1:]).strip()

        if not message:
            raise ValueError("Xabar bo'sh")

        await context.bot.send_message(
            chat_id=user_id,
            text=f"📩 Admin javobi:\n\n{message}"
        )

        await update.message.reply_text("✅ Xabar yuborildi")

    except Exception:
        await update.message.reply_text(
            "❌ Format:\n/reply USER_ID xabar"
        )

# =========================
# HANDLERLARNI ULASH
# =========================
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("reply", reply))
telegram_app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

# =========================
# ROUTES
# =========================
@flask_app.get("/")
def home():
    return "Bot ishlayapti", 200


@flask_app.get("/set_webhook")
async def set_webhook():
    render_url = os.getenv("RENDER_EXTERNAL_URL")

    if not render_url:
        return "RENDER_EXTERNAL_URL topilmadi", 500

    webhook_url = f"{render_url}/webhook/{WEBHOOK_SECRET}"
    await telegram_app.bot.set_webhook(url=webhook_url)
    return f"Webhook o'rnatildi: {webhook_url}", 200


@flask_app.post(f"/webhook/{WEBHOOK_SECRET}")
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return "OK", 200

# =========================
# STARTUP
# =========================
async def startup():
    await telegram_app.initialize()
    await telegram_app.start()

asyncio.run(startup())

app = flask_app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    flask_app.run(host="0.0.0.0", port=port)
