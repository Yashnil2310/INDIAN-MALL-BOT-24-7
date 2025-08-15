from flask import Flask, request
from threading import Thread
import re
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Bot credentials
BOT_TOKEN = "7796252339:AAFadwYkYlsBEsUPPGCgr1WKJr8mkPL2x34"
ADMIN_IDS = {2146073106, 7482893034}  # Multiple Admin IDs

# FAQs
FAQS = {
    "Delivery Charges": "📦 *Delivery Charges:*\nA minimal delivery fee of ₹30 is applicable to ensure safe and timely delivery of your order.",
    "Delivery Time": "🚀 *Same-Day Delivery Policy*  
    We offer *Same-Day Delivery* in select locations for eligible products.  

    🕒 *Order Cut-Off Time:*  
    Orders placed between *8:00 AM* and *10:00 PM* will be delivered on the *same day*.  
    Orders placed after *10:00 PM* will be delivered on the *next day*.  

    📦 Subject to product availability and delivery area.,
    "Return Policy": "❌ *No Return | No Replacement | No Refund.*\nPlease read the product description carefully before placing your order.",
    "Contact Support": "📞 *You can contact us via:*\n✉️ Email: support@indianmall.in\n📱 Phone: +91-7796305789, +91-9322410521",
    "Payment Methods": "💳 *We accept a wide range of payment methods:*\nUPI, Debit/Credit Cards, Net Banking,\n150+ UPI Apps, and Partial Cash on Delivery (COD).",
    "What is Partial COD?": "💰 *What is Partial COD?*\n\nPartial COD means you pay a small advance online while placing the order, and the remaining amount in cash when the product is delivered.\n\n🔹 Example: For a ₹500 order, you may pay ₹100 online and ₹400 on delivery.\n\n✅ This ensures safe and genuine orders from customers."
}

# Keyboard
faq_keyboard = ReplyKeyboardMarkup(
    keyboard=[[key] for key in FAQS.keys()],
    resize_keyboard=True,
    one_time_keyboard=False
)

# Alert function
async def alert_if_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "Unknown"
    ip_addr = request.remote_addr if request else "Polling Mode"

    # Log in console
    print(f"[SECURITY] User: {username} ({user_id}) from IP: {ip_addr}")

    if user_id not in ADMIN_IDS:
        for admin in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin,
                text=f"⚠️ *Unknown User Detected!*\n"
                     f"👤 Username: @{username}\n🆔 ID: {user_id}\n🌐 IP: {ip_addr}",
                parse_mode='Markdown'
            )

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await alert_if_unknown(update, context)

    try:
        with open("NAMASTE.png", "rb") as photo:
            await update.message.reply_photo(photo)
    except:
        pass

    await update.message.reply_text(
        "🙏 *Welcome to Indian Mall Support Bot!*\n\n"
        "🛍️ Your one-stop solution for all shopping queries.\n\n"
        "👇 Tap a question below to get started instantly!",
        reply_markup=faq_keyboard,
        parse_mode='Markdown'
    )

# Text handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await alert_if_unknown(update, context)

    user_message = update.message.text.strip()
    username = update.effective_user.username or update.effective_user.first_name or "there"
    user_id = update.effective_user.id

    found_numbers = re.findall(r'\b[6-9]\d{9}\b', user_message)
    if found_numbers:
        for number in found_numbers:
            for admin in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin,
                    text=f"📞 *Phone number from @{username}*\nNumber: {number}\nUser ID: {user_id}",
                    parse_mode='Markdown'
                )

    if user_message in FAQS:
        response = FAQS[user_message]
        await update.message.reply_text(f"*@{username}*,\n" + response, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "✅ *Thank you for sharing your contact details.*\nOur support team will reach out soon. 📞",
            parse_mode='Markdown'
        )

# Photo handler
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await alert_if_unknown(update, context)

    photo = update.message.photo[-1]
    username = update.effective_user.username or update.effective_user.first_name or "there"

    for admin in ADMIN_IDS:
        await context.bot.send_photo(
            chat_id=admin,
            photo=photo.file_id,
            caption=f"📸 Image received from @{username}\nUser ID: {update.effective_user.id}"
        )

# /reply command
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

# Flask server
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Indian Mall Bot is live!"

def run_web():
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

# Start
if __name__ == '__main__':
    Thread(target=run_web).start()

    tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CommandHandler("reply", reply_command))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    tg_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    tg_app.run_polling()
