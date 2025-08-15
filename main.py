from quart import Quart, request, Response
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os
from datetime import datetime
import logging

# ====== LOGGING ======
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("indian-mall-bot")

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN", "7796252339:AAFadwYkYlsBEsUPPGCgr1WKJr8mkPL2x34")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://indian-mall-bot-24-7.onrender.com/webhook")
ADMIN_IDS = set(map(int, os.getenv("ADMIN_IDS", "2146073106,7482893034").split(",")))

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
    "What is Partial COD?": (
        "💰 *What is Partial COD?*\n\n"
        "Partial COD means you pay a small advance online while placing the order, and the remaining amount in cash when the product is delivered.\n\n"
        "🔹 Example: For a ₹500 order, you may pay ₹100 online and ₹400 on delivery.\n\n"
        "✅ This ensures safe and genuine orders from customers."
    ),
}

# ====== Keyboard ======
faq_keyboard = ReplyKeyboardMarkup(
    keyboard=[[key] for key in FAQS.keys()],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# ====== Quart App & PTB Application ======
app = Quart(__name__)
application = ApplicationBuilder().token(BOT_TOKEN).build()
bot = application.bot

# ====== Helpers ======
async def alert_if_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE, source="handler"):
    """Notify admins when a non-admin user interacts."""
    try:
        user = update.effective_user
        if not user:
            return
        user_id = user.id
        username = user.username or user.first_name or "Unknown"
        ip_addr = "Webhook" if source == "webhook" else "Handler"
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if user_id not in ADMIN_IDS:
            log.info(f"[{source.upper()}] Unknown user detected: {username} ({user_id})")
            for admin in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin,
                    text=(
                        "⚠️ *Unknown User Detected!*\n"
                        f"👤 User: @{username}\n"
                        f"🆔 ID: {user_id}\n"
                        f"🌐 IP: {ip_addr}\n"
                        f"🕒 Time: {time_now}"
                    ),
                    parse_mode="Markdown",
                )
    except Exception as e:
        log.exception(f"alert_if_unknown failed: {e}")

# ====== Handlers ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await alert_if_unknown(update, context)
    try:
        try:
            with open("NAMASTE.png", "rb") as photo:
                await update.message.reply_photo(photo)
        except FileNotFoundError:
            pass

        await update.message.reply_text(
            "🙏 *Welcome to Indian Mall Support Bot!*\n\n"
            "🛍️ Your one-stop solution for all shopping queries.\n\n"
            "👇 Tap a question below to get started instantly!",
            reply_markup=faq_keyboard,
            parse_mode="Markdown",
        )
    except Exception as e:
        log.exception(f"/start handler error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await alert_if_unknown(update, context)
    try:
        msg = (update.message.text or "").strip()
        if msg in FAQS:
            await update.message.reply_text(FAQS[msg], parse_mode="Markdown")
        else:
            uname = update.effective_user.username or update.effective_user.first_name or "User"
            uid = update.effective_user.id
            for admin in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin,
                    text=(
                        "📩 *New Message Received*\n"
                        f"👤 @{uname}\n"
                        f"🆔 {uid}\n"
                        f"💬 {msg}"
                    ),
                    parse_mode="Markdown",
                )
            await update.message.reply_text(
                "✅ *Your message has been sent to our support team.*",
                parse_mode="Markdown",
            )
    except Exception as e:
        log.exception(f"text handler error: {e}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await alert_if_unknown(update, context)
    try:
        uname = update.effective_user.username or update.effective_user.first_name or "User"
        photo_id = update.message.photo[-1].file_id
        for admin in ADMIN_IDS:
            await context.bot.send_photo(
                chat_id=admin,
                photo=photo_id,
                caption=f"📸 Image from @{uname}",
                parse_mode="Markdown",
            )
        await update.message.reply_text(
            "✅ Your photo has been sent to support.",
            parse_mode="Markdown",
        )
    except Exception as e:
        log.exception(f"photo handler error: {e}")

async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ You are not authorized.")
            return

        if len(context.args) < 2:
            await update.message.reply_text("⚠️ Usage: /reply <user_id> <your message>")
            return

        user_id = int(context.args[0])
        message_text = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=user_id, text=message_text)
        await update.message.reply_text("✅ Message sent successfully.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")
        log.exception(f"/reply error: {e}")

# ====== Register Handlers ======
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("reply", reply_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# ====== Quart Routes ======
@app.route("/", methods=["GET", "HEAD"])
async def home():
    return Response("✅ Indian Mall Bot is live!", status=200)

@app.route("/webhook", methods=["POST"])
async def telegram_webhook():
    try:
        data = await request.get_json(force=True)
        if not data:
            return Response("no data", status=400)

        update = Update.de_json(data, bot)

        # Direct admin notify without PTB context
        user = update.effective_user
        if user and user.id not in ADMIN_IDS:
            username = user.username or user.first_name or "Unknown"
            time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.info(f"[WEBHOOK] Unknown user detected: {username} ({user.id})")
            for admin in ADMIN_IDS:
                await bot.send_message(
                    chat_id=admin,
                    text=(
                        "⚠️ *Unknown User Detected!*\n"
                        f"👤 User: @{username}\n"
                        f"🆔 ID: {user.id}\n"
                        f"🌐 IP: Webhook\n"
                        f"🕒 Time: {time_now}"
                    ),
                    parse_mode="Markdown",
                )

        await application.process_update(update)
        return Response("ok", status=200)

    except Exception as e:
        log.exception(f"[ERROR] Webhook error: {e}")
        return Response("error", status=500)

# ====== Lifecycle ======
@app.before_serving
async def startup():
    log.info("Starting PTB application and setting webhook...")
    await application.initialize()
    await application.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=WEBHOOK_URL)
    log.info(f"Webhook set to: {WEBHOOK_URL}")

@app.after_serving
async def shutdown():
    log.info("Shutting down PTB application...")
    await application.stop()
    await application.shutdown()
    log.info("Shutdown complete.")

# ====== Entrypoint ======
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
