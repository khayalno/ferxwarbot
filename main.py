import telebot
from telebot import types

TOKEN = "8876884764:AAHnyG_wr5BYy5X9kYsjFOpJ9k3kWB9K8zA
bot = telebot.TeleBot(listferxwazbot)

@bot.message_handler(commands=['start', 'startlist'])
def ask_teacher_name(message):
    if message.chat.type in ['group', 'supergroup']:
        msg = bot.send_message(message.chat.id, "فەرموو، ناوی مامۆستا بنووسە:")
        bot.register_next_step_handler(msg, get_teacher_name)
    else:
        bot.send_message(message.chat.id, "تکایە ئەم فەرمانە لەناو گرووپدا بەکاربهێنە.")

def get_teacher_name(message):
    teacher_name = message.text
    msg = bot.send_message(message.chat.id, f"ناوی مامۆستا: {teacher_name}\n\nئێستا پۆل یان بەشەکە بنووسە:")
    bot.register_next_step_handler(msg, get_class_name, teacher_name)

def get_class_name(message, teacher_name):
    class_name = message.text
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("✅ ئامادەیە", callback_data="present")
    btn2 = types.InlineKeyboardButton("❌ ئامادە نییە", callback_data="absent")
    markup.add(btn1, btn2)
    bot.send_message(
        message.chat.id,
        f"📋 **لیستی ئامادەبوون**\n\n👨‍🏫 مامۆستا: {teacher_name}\n📚 پۆل/بەش: {class_name}\n\nتکایە لە خوارەوە ئامادەبوونی خۆت دیاری بکە:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "present":
        bot.answer_callback_query(call.id, "سوپاس، ئامادەبوونت تۆمار کرا ✅")
    elif call.data == "absent":
        bot.answer_callback_query(call.id, "سوپاس، نەبوونت تۆمار کرا ❌")

bot.infinity_polling()
