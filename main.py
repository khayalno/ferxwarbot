import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

users = {}


def menu():
    keyboard = [
        ["📝 ناوم تۆمار بکە"],
        ["📚 خوێندم", "👂 گوێگرم"],
        ["🟢 مۆڵەت"],
        ["🗑️ ناوم بسڕەوە"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "بەخێربێیت 🌷\nتکایە یەکێک لە هەڵبژاردەکان هەڵبژێرە:",
        reply_markup=menu()
    )


async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "📝 ناوم تۆمار بکە":
        context.user_data["registering"] = True
        await update.message.reply_text("✍️ تکایە ناوت بنووسە:")

    elif text == "📚 خوێندم":
        users.setdefault(user_id, {})
        users[user_id]["status"] = "خوێندم"
        await update.message.reply_text("✅ تۆمار کرا: خوێندم")

    elif text == "👂 گوێگرم":
        users.setdefault(user_id, {})
        users[user_id]["status"] = "گوێگرم"
        await update.message.reply_text("✅ تۆمار کرا: گوێگرم")

    elif text == "🟢 مۆڵەت":
        users.setdefault(user_id, {})
        users[user_id]["status"] = "مۆڵەت"
        await update.message.reply_text("✅ مۆڵەتت تۆمار کرا.")

    elif text == "🗑️ ناوم بسڕەوە":
        if user_id in users:
            del users[user_id]
            await update.message.reply_text("🗑️ ناوت سڕایەوە.")
        else:
            await update.message.reply_text("ℹ️ ناوت پێشتر تۆمار نەکراوە.")

    elif context.user_data.get("registering"):
        users[user_id] = {
            "name": text,
            "status": "تۆمارکراو"
        }
        context.user_data["registering"] = False

        await update.message.reply_text(
            f"✅ ناوت بە سەرکەوتوویی تۆمار کرا:\n\n👤 {text}",
            reply_markup=menu()
        )

    else:
        await update.message.reply_text(
            "تکایە یەکێک لە دوگمەکان هەڵبژێرە 👇",
            reply_markup=menu()
        )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    app.run_polling()


if __name__ == "__main__":
    main()
