import telebot
from telebot import types
import os
import sqlite3
from tabulate import tabulate  # pip install tabulate (если не установлено)

# Токен и ID владельца
BOTTOKEN = '8556636254:AAFqNK8XggnW7rCsRg_Fs45IzAcVLg6014o'
CREATOR_ID = '5067637273'  # ID администратора

bot = telebot.TeleBot(BOTTOKEN)

# Статус возможности отправки отзыва
can_send_feedback = {}

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    global can_send_feedback
    can_send_feedback[message.chat.id] = True  # разрешаем отправлять отзыв
    
    # Подключение к базе данных
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        # Проверяем, существуют ли все нужные столбцы, и добавляем их, если нет
        try:
            c.execute("SELECT chat_title, first_name, last_name FROM users LIMIT 1")
        except sqlite3.OperationalError:
            print("Отсутствуют некоторые столбцы. Добавляю...")
            c.execute("ALTER TABLE users ADD COLUMN chat_title TEXT")
            c.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
            c.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
            conn.commit()
        
        # Создаем таблицу, если она еще не создана
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                unique_number TEXT UNIQUE,
                username TEXT,
                chat_title TEXT,
                first_name TEXT,
                last_name TEXT
            );
        ''')
        conn.commit()
    
        # Проверяем регистрацию пользователя
        c.execute("SELECT unique_number, username, first_name, last_name, chat_title FROM users WHERE telegram_id=?", (message.chat.id,))
        result = c.fetchone()
    
        if result is None:
            # Регистрация нового пользователя
            c.execute("INSERT INTO users (telegram_id, unique_number, username, first_name, last_name, chat_title) VALUES (?, ?, ?, ?, ?, ?)",
                      (message.chat.id, None, message.from_user.username, message.from_user.first_name, message.from_user.last_name, message.chat.title))
            conn.commit()
            unique_number = str(c.lastrowid)
            c.execute("UPDATE users SET unique_number=? WHERE telegram_id=?", (unique_number, message.chat.id))
            conn.commit()
        else:
            # Пользователь уже зарегистрирован
            unique_number, username, first_name, last_name, chat_title = result
    
    # Генерация меню
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text="РАСПИСАНИЕ", url="https://p11505.edu35.ru/gmraspisanie/izmeneniya")
    btn2 = types.InlineKeyboardButton(text="СДО", url="https://sdo.p11505.edu35.ru")
    btn3 = types.InlineKeyboardButton(text="ЭЛ ЖУРНАЛ", url="https://ssuz.vip.edu35.ru/auth/login-page")
    
    # Показываем кнопку обратной связи ТОЛЬКО в личных сообщениях
    if message.chat.type == 'private':
        btn4 = types.InlineKeyboardButton(text="Обратная связь", callback_data="feedback")
        markup.add(btn4)
    
    markup.row(btn1)
    markup.row(btn3, btn2)

    # Приветствие пользователя
    bot.send_message(message.chat.id, f'''
Привет, {message.from_user.first_name}! 
Ваш уникальный номер: {unique_number}
Это бот-помощник для студентов Череповецкого химико-технологического колледжа 
Приятного использования!
''', reply_markup=markup)

# Команда для вывода таблицы пользователей
@bot.message_handler(commands=['qwertyidpol00'])
def show_users_table(message):
    # Доступ только владельцу
    if str(message.chat.id) != CREATOR_ID:
        bot.reply_to(message, "Доступ ограничен.")
        return
    
    # Получаем все записи из базы данных
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        rows = c.fetchall()
    
    # Исключаем None-значения из описания столбцов
    valid_columns = [col[0] for col in c.description if col[0]]
    
    # Формируем примитивную текстовую таблицу
    header = "\n".join(valid_columns)
    output = ""
    for idx, row in enumerate(rows):
        clean_row = map(lambda x: "" if x is None else str(x), row)  # избавляемся от None
        output += f"\n\n{idx+1}. {' '.join(clean_row)}\n"
    
    # Отправляем простым текстом
    bot.send_message(message.chat.id, f"<code>{header}{output}</code>", parse_mode='HTML')

# Обрабатываем нажатие на кнопку "Обратная связь"
@bot.callback_query_handler(func=lambda call: call.data == 'feedback')
def feedback_button_pressed(call):
    can_send_feedback[call.message.chat.id] = True  # разрешаем отправлять отзыв
    bot.send_message(call.message.chat.id, '''
Отправьте ваше пожелание или предложение в виде обычного сообщения.
Оно будет передано создателям бота.
''')

# Обрабатываем отзывы
@bot.message_handler(func=lambda m: True)
def collect_feedback(message):
    if can_send_feedback.get(message.chat.id, False):
        # Отзыв принят
        can_send_feedback[message.chat.id] = False  # запрет повторного отправления
        
        # Извлекаем уникальный номер и юзернейм
        with sqlite3.connect('users.db') as conn:
            c = conn.cursor()
            c.execute("SELECT unique_number, username FROM users WHERE telegram_id=?", (message.chat.id,))
            unique_number, username = c.fetchone()
            
        # Отправляем отзыв владельцу
        bot.send_message(CREATOR_ID, f'''Новый отзыв от пользователя {username}, уникальный номер {unique_number}: 
{message.text}''')
        
        # Подтверждение пользователю
        bot.send_message(message.chat.id, 'Спасибо за ваш отзыв!')
    else:
        # Остальные сообщения игнорируются
        pass

# Запуск бота
bot.polling(none_stop=True)
