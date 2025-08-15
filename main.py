from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import asyncio
import os

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN", "7796252339:AAFadwYkYlsBEsUPPGCgr1WKJr8mkPL2x34")
ADMIN_IDS = {2146073106, 7482893034}
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://indian-mall-bot-24-7.onrender.com/webhook")

# ====== FAQs ======
FAQS = {
    "Delivery Charges": "📦 *Delivery Charges:*\nA minimal delivery fee of ₹30 is applicable to ensure safe and timely delivery of your order.",
    "Delivery Time": (
        "🚀 *Same-Day Delivery Policy*\n"
        "We offer *Same-Day Delivery* in select locations for eligible products.\n\n"
        "🕒 *Order Cut-Off Time:*\n"
        "Orders placed between *8:00 AM* and *10:00 PM* will be delivered on the *same day*.\n"
        "Orders placed after *10:00 PM* will be delivered on the *next day*.\n\n"
        "📦 Subject to product availability and delivery area."
    ),
    "Return Policy": "❌ *No Return | No Replacement | No Refund.*\nPlease read the product description carefully before placing your order.",
    "Contact Support": "📞 *You can contact us via:*\n✉️ Email: support@indianmall.in\n📱 Phone: +91-7796305789, +91-9322410521",
    "Payment Methods": "💳 *We accept a wide range of payment methods:*\nUPI, Debit/Credit Cards, Net Banking,\n150+ UPI Apps, and Partial Cash on Delivery (COD).",
    "What is Partial COD?": "💰 *What is Partial COD?*\n\nPartial COD means you pay a small advance online while placing the order, and the remaining amount in cash when the product is delivered.\n\n🔹 Example: For a ₹500 order, you may pay ₹100 online and ₹400 on delivery.\n\n✅ This ensures safe and genuine orders from customers."
}

# ====== Keyboard ======
faq_keyboard = ReplyKeyboardMarkup(
    keyboard=[[key] for key in FAQS.keys()],
    resize_keyboard=True,
    one_time_keyboard=False
)

# ====== Flask App & Bot ======
app = Flask(__name__)
application = ApplicationBuilder().token(BOT_TOKEN).build()
bot = application.bot

# ====== Helpers ======
async def alert_if_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "Unknown"
    ip_addr = request.remote_addr if request else "Webhook"

    if user_id not in ADMIN_IDS:
        for admin in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin,
                text=f"⚠️ *Unknown User Detected!*\n👤 @{username}\n🆔 {user_id}\n🌐 IP: {ip_addr}",
                parse_mode='Markdown'
            )

# ====== Handlers ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await alert_if_unknown(update, context)
    await update.message.reply_text(
        "🙏 *Welcome to Indian Mall Support Bot!*\n\n🛍️ Your one-stop solution for all shopping queries.\n\n👇 Tap a question below to get started instantly!",
        reply_markup=faq_keyboard,
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await alert_if_unknown(update, context)
    user_message = update.message.text.strip()

    if user_message in FAQS:
        await update.message.reply_text(FAQS[user_message], parse_mode='Markdown')
    else:
        for admin in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin,
                text=f"📩 *New Message Received*\n👤 @{update.effective_user.username}\n🆔 {update.effective_user.id}\n💬 {user_message}",
                parse_mode='Markdown'
            )
        await update.message.reply_text("✅ *Your message has been sent to our support team.*", parse_mode='Markdown')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await alert_if_unknown(update, context)
    for admin in ADMIN_IDS:
        await context.bot.send_photo(
            chat_id=admin,
            photo=update.message.photo[-1].file_id,
            caption=f"📸 Image from @{update.effective_user.username}",
            parse_mode='Markdown'
        )
    await update.message.reply_text("✅ Your photo has been sent to support.", parse_mode='Markdown')

async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: /reply <user_id> <your message>")
        return

    user_id = int(context.args[0])
    message_text = " ".join(context.args[1:])
    try:
        await context.bot.send_message(chat_id=user_id, text=message_text)
        await update.message.reply_text("✅ Message sent successfully.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")

# ====== Flask Routes ======
@app.route('/')
def home():
    return "✅ Indian Mall Bot is live!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        if not data:
            return "no data", 400

        update = Update.de_json(data, bot)
        asyncio.get_event_loop().create_task(application.process_update(update))
        return "ok"
    except Exception as e:
        print(f"[ERROR] Webhook error: {e}")
        return "error", 500

# ====== Register Handlers ======
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("reply", reply_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# ====== Main ======
if __name__ == '__main__':
    async def setup_webhook():
        await bot.delete_webhook()
        await bot.set_webhook(url=WEBHOOK_URL)

    asyncio.run(setup_webhook())
    app.run(host='0.0.0.0', port=8080)
