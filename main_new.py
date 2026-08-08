import os
import sqlite3
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

DB = "bot.db"


# =========================
# Database
# =========================

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            chat_id INTEGER PRIMARY KEY,
            teacher TEXT DEFAULT '',
            assistant TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            chat_id INTEGER,
            user_id INTEGER,
            name TEXT,
            status TEXT DEFAULT 'registered',
            PRIMARY KEY (chat_id, user_id)
        )
    """)

    conn.commit()
    conn.close()


def get_group(chat_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT teacher, assistant FROM groups WHERE chat_id=?",
        (chat_id,)
    )

    row = cur.fetchone()
    conn.close()

    if row:
        return row[0], row[1]

    return "", ""


def save_group(chat_id, teacher="", assistant=""):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO groups(chat_id, teacher, assistant)
        VALUES (?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
        teacher=excluded.teacher,
        assistant=excluded.assistant
    """, (chat_id, teacher, assistant))

    conn.commit()
    conn.close()


# =========================
# Keyboard
# =========================

def menu():
    keyboard = [
        ["📝 ناوم تۆمار بکە"],
        ["🗑️ ناوم بسڕەوە"],
        ["📖 خوێندم", "👂 گوێگر"],
        ["🕊️ مۆڵەت"],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


# =========================
# Private /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.type != "private":
        return

    user = update.effective_user
    name = user.first_name or "بەکارهێنەر"

    text = f"""👋 السَّلَاْمُ عَلَیْکُم وَرَحْمَةُ اللّٰهِ وَبَرَکَاْتُه

🌷 بەخێربێیت {name}

🤖 من بۆتی «لیستی ناونوسینی فێرخواز»م.

📌 ئیشم ئەوەیە:
• دروستکردنی لیستی خوێندن
• ڕیزبەندی خوێنەر و گوێگر
• بە زمانی کوردی
• کار لە گروپ دەکەم

👇 بۆ دەستپێکردن:
بۆتەکە زیاد بکە بۆ گروپەکەت.

پاشان لە ناو گروپەکە:
startlist
بنووسە.
"""

    await update.message.reply_text(
        text,
        reply_markup=menu()
    )


# =========================
# Check Admin
# =========================

async def is_admin(update: Update):

    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"]:
        return False

    member = await chat.get_member(user.id)

    return member.status in ["administrator", "creator"]


# =========================
# Create daily list
# =========================

async def startlist(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text(
            "❌ ئەم فەرمانە تەنها لە گروپ کار دەکات."
        )
        return

    if not await is_admin(update):
        await update.message.reply_text(
            "❌ تەنها ئەدمینی گروپ دەتوانێت لیست دروست بکات."
        )
        return

    chat_id = update.effective_chat.id

    save_group(chat_id)

    today = datetime.now()

    text = f"""بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ

📅 بەرواری زاینی:
{today.day}/{today.month}/{today.year}

👨‍🏫 ناوی مامۆستا:
ـ

👤 ناوی یاریدەدەر:
ـ

━━━━━━━━━━━━━━

📋 لیستی فێرخوازان

هیچ فێرخوازێک هێشتا تۆمار نەکراوە.

━━━━━━━━━━━━━━

📖 خوێندم
ــــــــــــــــــــ

👂 گوێگر
ــــــــــــــــــــ

🕊️ مۆڵەت
ــــــــــــــــــــ

━━━━━━━━━━━━━━

پێغەمبەر ﷺ فەرموویەتی:ـ

«مَن يُرِدِ اللهُ بِهِ خَيْرًا يُفَقِّهْهُ فِي الدِّينِ»

واتە: هەرکەسێک خودای گەورە خێری بۆی بوێت، شارەزای دەکات لە دین.
"""

    await update.message.reply_text(text)


# =========================
# Student actions
# =========================

async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text
    user = update.effective_user

    if not user:
        return

    user_id = user.id
    name = user.first_name or "بەکارهێنەر"

    # Private chat
    if update.effective_chat.type == "private":

        if text == "📝 ناوم تۆمار بکە":
            await update.message.reply_text(
                "ℹ️ ناوت لە گروپەکە خۆکارانە تۆمار دەکرێت.\n"
                "تکایە بۆ گروپەکە بچۆ و دوگمەکە بەکاربهێنە."
            )

        else:
            await update.message.reply_text(
                "ئەم دوگمەیە لە ناو گروپەکە بەکاردێت."
            )

        return

    # Group only
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    chat_id = update.effective_chat.id

    # Register
    if text == "📝 ناوم تۆمار بکە":

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        cur.execute("""
            INSERT OR REPLACE INTO students
            (chat_id, user_id, name, status)
            VALUES (?, ?, ?, ?)
        """, (chat_id, user_id, name, "registered"))

        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"✅ {name} بە سەرکەوتوویی تۆمار کرا."
        )

    # Delete
    elif text == "🗑️ ناوم بسڕەوە":

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM students WHERE chat_id=? AND user_id=?",
            (chat_id, user_id)
        )

        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"🗑️ {name} لە لیستەکە سڕایەوە."
        )

    # Read
    elif text == "📖 خوێندم":

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        cur.execute("""
            UPDATE students
            SET status='read'
            WHERE chat_id=? AND user_id=?
        """, (chat_id, user_id))

        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"✅ {name} ـەکە بە خوێندراو تۆمار کرا."
        )

    # Listener
    elif text == "👂 گوێگر":

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        cur.execute("""
            INSERT OR REPLACE INTO students
            (chat_id, user_id, name, status)
            VALUES (?, ?, ?, ?)
        """, (chat_id, user_id, name, "listener"))

        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"👂 {name} لە بەشی گوێگر تۆمار کرا."
        )

    # Permission / Leave
    elif text == "🕊️ مۆڵەت":

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        cur.execute("""
            INSERT OR REPLACE INTO students
            (chat_id, user_id, name, status)
            VALUES (?, ?, ?, ?)
        """, (chat_id, user_id, name, "leave"))

        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"🕊️ {name} لە بەشی مۆڵەت تۆمار کرا."
        )


# =========================
# Main
# =========================

def main():

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("startlist", startlist))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            messages
        )
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
