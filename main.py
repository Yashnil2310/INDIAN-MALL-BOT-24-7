from flask import Flask
from threading import Thread
import re
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Bot credentials
BOT_TOKEN = "7796252339:AAFadwYkYlsBEsUPPGCgr1WKJr8mkPL2x34"

# Admin IDs
ADMIN_IDS = [2146073106, 7482893034]

# FAQs
FAQS = {
    "Delivery Charges": (
        "📦 *Delivery Charges:*\n"
        "A minimal delivery fee of ₹30 is applicable to ensure safe and timely delivery of your order."
    ),
    "Delivery Time": (
        "🚀 *Same-day delivery* is available in select locations for eligible products.\n"
        "Your order will reach you fast and hassle-free!\n"
        "📦 Subject to availability and delivery area."
    ),
    "Return Policy": (
        "❌ *No Return | No Replacement | No Refund.*\n"
        "Please read the product description carefully before placing your order."
    ),
    "Contact Support": (
        "📞 *You can contact us via:*\n"
        "✉️ Email: support@indianmall.in\n"
        "📱 Phone: +91-7796305789, +91-9322410521"
    ),
    "Payment Methods": (
        "💳 *We accept a wide range of payment methods:*\n"
        "UPI, Debit/Credit Cards, Net Banking,\n"
        "150+ UPI Apps, and Partial Cash on Delivery (COD)."
    ),
    "What is Partial COD?": (
        "💰 *What is Partial COD?*\n\n"
        "Partial COD means you pay a small advance online while placing the order, "
        "and the remaining amount in cash when the product is delivered.\n\n"
        "🔹 Example: For a ₹500 order, you may pay ₹100 online and ₹400 on delivery.\n\n"
        "✅ This ensures safe and genuine orders from customers."
    )
}

# Keyboard
faq_keyboard = ReplyKeyboardMarkup(
    keyboard=[[key] for key in FAQS.keys()],
    resize_keyboard=True,
    one_time_keyboard=False
)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("NAMASTE.png", "rb") as photo:
            await update.message.reply_photo(photo)
    except:
        pass

    await update.message.reply_text(
        "🙏 *Welcome to Indian Mall Support Bot!*\n\n"
        "🛍️ Your one-stop solution for all shopping queries — be it delivery, returns, payments, or anything in between.\n\n"
        "💡 *Here’s how I can help you:*\n"
        "• Delivery charges & timelines\n"
        "• Return and refund policies\n"
        "• Payment methods, including Partial COD\n"
        "• How to reach our support team\n\n"
        "👇 *Just tap a question below to get started instantly!*",
        reply_markup=faq_keyboard,
        parse_mode='Markdown'
    )

# Text message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    username = update.effective_user.username or update.effective_user.first_name or "there"
    user_id = update.effective_user.id

    # Check for mobile number
    found_numbers = re.findall(r'\b[6-9]\d{9}\b', user_message)
    if found_numbers:
        for number in found_numbers:
            for admin in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin,
                    text=f"📞 *Phone number received from @{username}*\nNumber: {number}\nUser ID: {user_id}",
                    parse_mode='Markdown'
                )

    # Reply with FAQ or forward message to admins
    if user_message in FAQS:
        response = FAQS[user_message]
        await update.message.reply_text(f"*@{username}*,\n" + response, parse_mode='Markdown')
    else:
        for admin in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin,
                text=f"📩 *New Message Received*\n👤 @{username}\n🆔 {user_id}\n💬 {user_message}",
                parse_mode='Markdown'
            )
        await update.message.reply_text(
            "✅ *Thank you for your message.*\nOur support team will reach out to you shortly. 📞",
            parse_mode='Markdown'
        )

# Image handler
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    user = update.effective_user
    username = user.username or user.first_name or "there"

    for admin in ADMIN_IDS:
        await context.bot.send_photo(
            chat_id=admin,
            photo=photo.file_id,
            caption=f"📸 Image received from @{username}\nUser ID: {user.id}"
        )

    await update.message.reply_text(
        f"✅ *Thanks @{username}!* We’ve received your image.\nOur support team will review it and get back to you shortly. 🛠️",
        parse_mode='Markdown'
    )

# /reply command
async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
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
        await update.message.reply_text(f"❌ Failed to send message: {e}")

# Flask uptime server
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Indian Mall Bot is live!"

def run_web():
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

# Start
if __name__ == '__main__':
    Thread(target=run_web).start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reply", reply_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.run_polling()
