import os
import json
import telebot
from telebot import types
from datetime import datetime

TOKEN = "8876884764:AAHnyG_wr5BYy5X9kYsjFOpJ9k3kWB9K8zA"
BOT_USERNAME = "listferxwazbot"

bot = telebot.TeleBot(TOKEN)
DB_FILE = "lists_db_v5.json"

def setup_bot_commands():
    try:
        commands = [
            types.BotCommand("startlist", "دەستپێکردن و دروستکردنی لیستی نوێ"),
            types.BotCommand("closelist", "داخستنی لیستی ئێستا"),
            types.BotCommand("start", "زانیاری و ڕێنیشاندەری بۆت")
        ]
        bot.set_my_commands(commands)
    except Exception:
        pass

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for chat_id in data:
                    data[chat_id]['completed'] = set(str(x) for x in data[chat_id].get('completed', []))
                    for s in data[chat_id].get('students', []):
                        s['id'] = str(s['id'])
                    for l in data[chat_id].get('listeners', []):
                        l['id'] = str(l['id'])
                    for v in data[chat_id].get('leaves', []):
                        v['id'] = str(v['id'])
                return data
        except Exception:
            return {}
    return {}

def save_db():
    try:
        data_to_save = {}
        for chat_id, content in lists_db.items():
            data_to_save[str(chat_id)] = {
                'greg_date': content.get('greg_date', ''),
                'raw_date': content.get('raw_date', ''),
                'teacher': content.get('teacher', ''),
                'assistant': content.get('assistant', ''),
                'students': [{'id': str(s['id']), 'name': s['name']} for s in content.get('students', [])],
                'completed': list(str(x) for x in content.get('completed', set())),
                'listeners': [{'id': str(l['id']), 'name': l['name']} for l in content.get('listeners', [])],
                'leaves': [{'id': str(v['id']), 'name': v['name']} for v in content.get('leaves', [])],
                'is_closed': content.get('is_closed', False),
                'message_id': content.get('message_id', None)
            }
        
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

lists_db = load_db()

def safe_answer_cb(call_id, text=None, show_alert=False):
    try:
        bot.answer_callback_query(call_id, text=text, show_alert=show_alert)
    except Exception:
        pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type == 'private':
        welcome_text = """👋 السَّلَاْمُ عَلَیْکُم

🤖 من بۆتی لیستی ناونوسینی فێرخوازانم.
📌 بە دوگمە و ئایکۆن کار دەکەم بە تەواوی."""
        
        markup = types.InlineKeyboardMarkup()
        add_btn = types.InlineKeyboardButton(
            text="➕ زیادکردن بۆ گروپ", 
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
        )
        markup.add(add_btn)
        bot.reply_to(message, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['startlist'])
def handle_startlist(message):
    if message.chat.type in ['group', 'supergroup']:
        chat_id = str(message.chat.id)
        if chat_id in lists_db:
            lists_db[chat_id]['is_closed'] = False
        msg = bot.reply_to(message, "👨‍🏫 تکایە ناوی مامۆستا بنووسە:")
        bot.register_next_step_handler(msg, ask_assistant_name)

@bot.message_handler(commands=['closelist'])
def handle_closelist(message):
    if message.chat.type in ['group', 'supergroup']:
        chat_id = str(message.chat.id)
        user_id = message.from_user.id
        
        try:
            chat_member = bot.get_chat_member(int(chat_id), int(user_id))
            if chat_member.status not in ['administrator', 'creator']:
                bot.reply_to(message, "🚫 تەنها ئەدمین دەتوانێت لیستەکە داخات.")
                return
        except Exception:
            return

        if chat_id in lists_db:
            lists_db[chat_id]['is_closed'] = True
            save_db()
            send_updated_list(chat_id, message_id=lists_db[chat_id].get('message_id'))
            bot.reply_to(message, "✅ لیستەکە داخرا.")
        else:
            bot.reply_to(message, "⚠️ هیچ لیستێکی چالاک بوونی نییە.")

def ask_assistant_name(message):
    teacher_name = message.text.strip()
    msg = bot.reply_to(message, f"👤 مامۆستا: {teacher_name}\n\nئێستا ناوی یاریدەدەر بنووسە:")
    bot.register_next_step_handler(msg, lambda m: create_final_list(m, teacher_name))

def create_final_list(message, teacher_name):
    assistant_name = message.text.strip()
    chat_id = str(message.chat.id)

    now = datetime.now()
    greg_date = f"{now.day}/{now.month}/{now.year}"

    lists_db[chat_id] = {
        'greg_date': greg_date,
        'raw_date': now.strftime("%d-%m-%Y"),
        'teacher': teacher_name,
        'assistant': assistant_name,
        'students': [],
        'completed': set(),
        'listeners': [],
        'leaves': [],
        'is_closed': False,
        'message_id': None
    }
    
    save_db()
    send_updated_list(chat_id)

def generate_list_text(chat_id):
    data = lists_db[str(chat_id)]
    
    text = f"""بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ
📅 بەرواری زاینی: {data['greg_date']}
ـــــــــــــــــــــــــــــــــــــــــ

👨‍🏫 ناوی مامۆستا: {data['teacher']}
👤 ناوی یاریدەدەر: {data['assistant']}

📋 لیستی فێرخوازان:\n"""
    
    if not data['students']:
        text += "▫️ (هیچ تۆمار نەکراوە)\n"
    else:
        for idx, student in enumerate(data['students'], 1):
            status = " ✅" if str(student['id']) in data['completed'] else ""
            text += f"{idx}. {student['name']}{status}\n"

    text += "\n👂 گوێگر\nــــــــــــــــــــ\n"
    if not data['listeners']:
        text += "▫️ (هیچ تۆمار نەکراوە)\n"
    else:
        for listener in data['listeners']:
            text += f"• {listener['name']}\n"

    text += "\n🟣 مۆڵەت\nــــــــــــــــــــ\n"
    if not data['leaves']:
        text += "▫️ (هیچ تۆمار نەکراوە)\n"
    else:
        for leave in data['leaves']:
            text += f"• {leave['name']}\n"

    text += """\n— — — — — — — — —
پێغەمبەر ﷺ فەرموویەتی:ـ
«مَن يُرِدِ اللهُ بِهِ خَيْرًا يُفَقِّهْهُ فِي الدِّينِ»"""

    if data.get('is_closed', False):
        text += "\n\n🔒 **[ ئەم لیستە داخرا و ناو نووسین ڕاوەستا ]**"

    return text

def build_keyboard(is_closed=False):
    if is_closed:
        return None
        
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_register = types.InlineKeyboardButton("📝 ناوم تۆمار بکە", callback_data="act_register")
    btn_delete = types.InlineKeyboardButton("🗑️ ناوم بسڕەوە", callback_data="act_delete")
    btn_read = types.InlineKeyboardButton("📖 خوێندم", callback_data="act_read")
    btn_listen = types.InlineKeyboardButton("👂 گوێگر", callback_data="act_listen")
    btn_leave = types.InlineKeyboardButton("🟣 مۆڵەت", callback_data="act_leave")
    btn_send_private = types.InlineKeyboardButton("📩 ناردنی لیست بۆ تایبەتی ئەدمین", callback_data="act_send_private")
    
    markup.add(btn_register, btn_delete)
    markup.add(btn_read, btn_listen, btn_leave)
    markup.add(btn_send_private)
    return markup

def send_updated_list(chat_id, message_id=None):
    chat_id = str(chat_id)
    if chat_id not in lists_db:
        return
    data = lists_db[chat_id]
    text = generate_list_text(chat_id)
    markup = build_keyboard(data.get('is_closed', False))
    
    target_msg_id = message_id or data.get('message_id')
    
    if target_msg_id:
        try:
            bot.edit_message_text(
                text, 
                chat_id=int(chat_id), 
                message_id=int(target_msg_id), 
                reply_markup=markup, 
                parse_mode="Markdown"
            )
            return
        except Exception:
            try:
                bot.delete_message(int(chat_id), int(target_msg_id))
            except Exception:
                pass

    try:
        msg = bot.send_message(int(chat_id), text, reply_markup=markup, parse_mode="Markdown")
        lists_db[chat_id]['message_id'] = msg.message_id
        save_db()
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    chat_id = str(call.message.chat.id)
    user_id = str(call.from_user.id)
    user_name = call.from_user.first_name

    if chat_id not in lists_db:
        safe_answer_cb(call.id, "⚠️ لیستێک بوونی نییە، /startlist بنووسە.", show_alert=True)
        return

    data = lists_db[chat_id]

    if data.get('is_closed', False):
        safe_answer_cb(call.id, "🔒 ئەم لیستە داخراوە.", show_alert=True)
        return

    def remove_user_from_all():
        data['students'] = [s for s in data['students'] if str(s['id']) != user_id]
        data['completed'].discard(user_id)
        data['listeners'] = [l for l in data['listeners'] if str(l['id']) != user_id]
        data['leaves'] = [l for l in data['leaves'] if str(l['id']) != user_id]

    action = call.data

    if action == "act_register":
        remove_user_from_all()
        data['students'].append({'id': user_id, 'name': user_name})
        save_db()
        safe_answer_cb(call.id, "ناوی تۆ تۆمار کرا.")

    elif action == "act_delete":
        remove_user_from_all()
        save_db()
        safe_answer_cb(call.id, "ناوت سڕایەوە.")

    elif action == "act_read":
        is_student = any(str(s['id']) == user_id for s in data['students'])
        if not is_student:
            safe_answer_cb(call.id, "⚠️ سەرەتا ناوم تۆمار بکە داگرە.", show_alert=True)
            return
        
        if user_id in data['completed']:
            data['completed'].remove(user_id)
            safe_answer_cb(call.id, "هێمای ✅ لادرا.")
        else:
            data['completed'].add(user_id)
            safe_answer_cb(call.id, "نیشانەی ✅ جێگیر کرا.")
        save_db()

    elif action == "act_listen":
        remove_user_from_all()
        data['listeners'].append({'id': user_id, 'name': user_name})
        save_db()
        safe_answer_cb(call.id, "گوێگربوون تۆمار کرا.")

    elif action == "act_leave":
        remove_user_from_all()
        data['leaves'].append({'id': user_id, 'name': user_name})
        save_db()
        safe_answer_cb(call.id, "مۆڵەت تۆمار کرا.")

    elif action == "act_send_private":
        try:
            chat_member = bot.get_chat_member(int(chat_id), int(user_id))
            if chat_member.status not in ['administrator', 'creator']:
                safe_answer_cb(call.id, "🚫 تەنها ئەدمین دەتوانێت.", show_alert=True)
                return
        except Exception:
            safe_answer_cb(call.id, "⚠️ هەڵە لە پشکنین.", show_alert=True)
            return

        list_text = generate_list_text(chat_id)
        try:
            bot.send_message(int(user_id), f"📥 **لیستی ئەمرۆ:**\n\n{list_text}", parse_mode="Markdown")
            safe_answer_cb(call.id, "✅ بۆ چاتی تایبەتیت ڕەوانە کرا.")
        except Exception:
            safe_answer_cb(call.id, "⚠️ سەرەتا بۆتەکە لە تایبەتی /start بکە.", show_alert=True)
        return

    msg_id = data.get('message_id', call.message.message_id)
    send_updated_list(chat_id, message_id=msg_id)

setup_bot_commands()
print("🤖 بۆتەکە بە سەرکەوتوویی کەوتە کار...")
bot.infinity_polling(none_stop=True)
