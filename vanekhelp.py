import sqlite3
import re
import telebot
from telebot import types

# ==================== ТОКЕН ====================
TOKEN_PART1 = "9272220563:"
TOKEN_PART2 = "AAFFSdWs7gQbsiERPKv3qX5i9sMS3KT4e-k"
bot = telebot.TeleBot(TOKEN_PART1 + TOKEN_PART2)

ADMIN_USERNAME = "lytixx"

# ==================== ПРЕМИУМ ЭМОДЗИ ====================
# ВНИМАНИЕ: Замени "123456789" на реальные ID премиум-эмодзи!
# Узнать ID можно через бота @RawDataBot (отправь ему эмодзи и найди custom_emoji_id).
EMOJI_VPN = '<tg-emoji emoji-id="5426842318395188200">🌐</tg-emoji>'  # Пример ID
EMOJI_STAR = '<tg-emoji emoji-id="5426842318395188200">⭐</tg-emoji>'
EMOJI_FIRE = '<tg-emoji emoji-id="5426842318395188200">🔥</tg-emoji>'

# ==================== БАЗА ====================
conn = sqlite3.connect("vpn_helper.db", check_same_thread=False, timeout=30)
conn.execute("""CREATE TABLE IF NOT EXISTS users(
    tg_id INTEGER PRIMARY KEY, 
    username TEXT, 
    custom_nick TEXT,
    msg_count INTEGER DEFAULT 0
)""")
conn.execute("""CREATE TABLE IF NOT EXISTS custom_links(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    url TEXT
)""")
conn.commit()

# ==================== ССЫЛКИ ====================
LINKS = {
    "channel": "https://t.me/internet_obhod",
    "premium": "https://t.me/vanek_vnp_bot",
    "tutorial": "https://t.me/internet_obhod/394"
}

# ==================== УТИЛИТЫ ====================
def is_admin(tg_id, username):
    if username and username.lower() == ADMIN_USERNAME: return True
    return False

def get_user(tg_id, username):
    user = conn.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
    if not user:
        conn.execute("INSERT INTO users(tg_id, username, custom_nick) VALUES(?, ?, ?)", (tg_id, username, username or "Аноним"))
        conn.commit()
        return get_user(tg_id, username)
    return user

def add_msg_count(tg_id):
    conn.execute("UPDATE users SET msg_count = msg_count + 1 WHERE tg_id=?", (tg_id,))
    conn.commit()

def fmt(num):
    return f"{num:,}".replace(",", " ")

# ==================== КОМАНДЫ ====================

@bot.message_handler(commands=['start'])
def start(m):
    get_user(m.from_user.id, m.from_user.username)
    text = (
        f"{EMOJI_VPN} <b>Привет! Я помощник Vanya VPN.</b>\n\n"
        f"Я помогу тебе найти нужную информацию, обойти блокировки и настроить VPN.\n\n"
        f"Используй команду /tutor или напиши <code>тутор</code>, чтобы получить инструкции.\n"
        f"Если нужны ссылки — просто напиши <code>ссылки</code>."
    )
    bot.reply_to(m, text, parse_mode="HTML")

@bot.message_handler(commands=['tutor'])
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "тутор")
def tutor(m):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📖 Инструкция по установке", url=LINKS["tutorial"]),
        types.InlineKeyboardButton("🌐 Оригинальный канал", url=LINKS["channel"]),
        types.InlineKeyboardButton("💎 Купить Premium", url=LINKS["premium"])
    )
    bot.reply_to(m, f"{EMOJI_FIRE} <b>Выбери нужный раздел:</b>", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["ссылки", "ссылка"])
def send_links(m):
    text = (
        f"{EMOJI_VPN} <b>Полезные ссылки:</b>\n\n"
        f"🔗 <b>Оригинальный канал:</b> {LINKS['channel']}\n"
        f"💎 <b>Premium подписка:</b> {LINKS['premium']}\n"
        f"📖 <b>Туториалы:</b> {LINKS['tutorial']}"
    )
    bot.reply_to(m, text, parse_mode="HTML", disable_web_page_preview=True)

# ==================== СТАТИСТИКА ====================
@bot.message_handler(commands=['stats'])
def stats(m):
    get_user(m.from_user.id, m.from_user.username)
    user = conn.execute("SELECT msg_count FROM users WHERE tg_id=?", (m.from_user.id,)).fetchone()
    bot.reply_to(m, f"{EMOJI_STAR} Твоя статистика:\nСообщений: <b>{user[0]}</b>", parse_mode="HTML")

@bot.message_handler(commands=['top'])
def top(m):
    users = conn.execute("SELECT custom_nick, msg_count FROM users ORDER BY msg_count DESC LIMIT 10").fetchall()
    if not users:
        return bot.reply_to(m, "Статистики пока нет.")
    
    text = f"{EMOJI_FIRE} <b>Топ активных пользователей:</b>\n\n"
    for i, (nick, count) in enumerate(users, 1):
        text += f"{i}. <b>{nick}</b> — {fmt(count)} сообщ.\n"
    bot.reply_to(m, text, parse_mode="HTML")

# ==================== СМЕНА НИКА ====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("+ник"))
def change_nick(m):
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.reply_to(m, "Напиши: <code>+ник Новый Ник</code>", parse_mode="HTML")
    
    new_nick = parts[1].strip()
    if len(new_nick) > 20:
        return bot.reply_to(m, "Ник слишком длинный (макс. 20 символов).")
        
    get_user(m.from_user.id, m.from_user.username)
    conn.execute("UPDATE users SET custom_nick=? WHERE tg_id=?", (new_nick, m.from_user.id))
    conn.commit()
    bot.reply_to(m, f"✅ Ник в топе изменён на: <b>{new_nick}</b>", parse_mode="HTML")

# ==================== РП КОМАНДЫ ====================
RP_ACTIONS = {
    "пожать руку": "🤝 {u1} пожал руку {u2}!",
    "обнять": "🫂 {u1} крепко обнял {u2}!",
    "ударить": "🥊 {u1} ударил {u2}!",
    "поцеловать": "😘 {u1} поцеловал {u2}!"
}

@bot.message_handler(func=lambda m: m.text and any(rp in m.text.lower() for rp in RP_ACTIONS))
def rp_handler(m):
    if not m.reply_to_message:
        return bot.reply_to(m, "Ответь на сообщение человека, чтобы сделать РП.")
    
    action_text = m.text.lower()
    for action, template in RP_ACTIONS.items():
        if action in action_text:
            u1 = m.from_user.first_name
            u2 = m.reply_to_message.from_user.first_name
            bot.reply_to(m, template.format(u1=u1, u2=u2))
            break

# ==================== АДМИНКА ====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("+инфо"))
def add_info(m):
    if not is_admin(m.from_user.id, m.from_user.username):
        return bot.reply_to(m, "❌ Только для админа.")
    
    parts = m.text.split(maxsplit=2)
    if len(parts) < 3:
        return bot.reply_to(m, "Формат: <code>+инфо Название https://ссылка</code>", parse_mode="HTML")
    
    title = parts[1]
    url = parts[2]
    
    if not url.startswith("http"):
        return bot.reply_to(m, "❌ Ссылка должна начинаться с http:// или https://")
        
    conn.execute("INSERT INTO custom_links(title, url) VALUES(?, ?)", (title, url))
    conn.commit()
    
    bot.reply_to(m, f"✅ Добавлена новая ссылка:\n<b>{title}</b> — {url}", parse_mode="HTML")

# ==================== АВТООТВЕТ В КОММЕНТАРИЯХ (ГРУППА) ====================
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_comments(m):
    # Не реагируем на команды и сообщения от ботов
    if m.text and m.text.startswith('/'): return
    if m.from_user.is_bot: return
    
    add_msg_count(m.from_user.id)
    
    # Триггеры для автоответа в комментариях
    triggers = ["впн", "vpn", "ссылка", "как", "помогите", "тутор", "инструкция"]
    text_lower = m.text.lower() if m.text else ""
    
    if any(t in text_lower for t in triggers):
        # Задержка, чтобы бот не спамил и выглядел как живой
        import time
        time.sleep(2)
        
        text = (
            f"{EMOJI_VPN} Привет! Вот полезные ссылки:\n\n"
            f"🌐 <a href='{LINKS['channel']}'>Оригинальный канал</a>\n"
            f"💎 <a href='{LINKS['premium']}'>Premium подписка</a>\n"
            f"📖 <a href='{LINKS['tutorial']}'>Инструкция по установке</a>"
        )
        bot.reply_to(m, text, parse_mode="HTML", disable_web_page_preview=True)

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    print("Vanya VPN Helper запущен...")
    # Для старых версий библиотеки (чтобы не было ошибки threaded)
    bot.polling(none_stop=True)