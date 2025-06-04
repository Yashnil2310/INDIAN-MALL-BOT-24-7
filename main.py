# 📨 Handle Text Messages + Detect Mobile Number
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    username = update.effective_user.username or update.effective_user.first_name or "there"
    user_id = update.effective_user.id

    # Check for mobile number
    found_numbers = re.findall(r'\b[6-9]\d{9}\b', user_message)
    if found_numbers:
        for number in found_numbers:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📞 *Phone number received from @{username}*\nNumber: {number}\nUser ID: {user_id}",
                parse_mode='Markdown'
            )

    # NEW polite response if message doesn't match FAQ
    response = FAQS.get(
        user_message,
        "✅ *Thank you for sharing your contact details.*\nOur support team will reach out to you as soon as possible. 📞"
    )

    if user_message in FAQS:
        await update.message.reply_text(f"*@{username}*,\n" + response, parse_mode='Markdown')
    else:
        await update.message.reply_text(response, parse_mode='Markdown')
