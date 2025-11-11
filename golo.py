import telebot
from telebot import types
import os

# Укажите свой токен бота
BOTTOKEN = '8556636254:AAFqNK8XggnW7rCsRg_Fs45IzAcVLg6014o'

# Укажите ваш Telegram ID для приема отзывов
CREATOR_ID = '5067637273'  # замените на ваш реальный id

bot = telebot.TeleBot(BOTTOKEN)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    # Приветствие пользователя
    photo_path = 'C:/122.jpg'  # Укажите путь к вашей картинке

    # Создаем inline-клавиатуру
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text="РАСПИСАНИЕ", url="https://p11505.edu35.ru/gmraspisanie/izmeneniya")
    btn2 = types.InlineKeyboardButton(text="СДО", url="https://sdo.p11505.edu35.ru")
    btn3 = types.InlineKeyboardButton(text="ЭЛ ЖУРНАЛ", url="https://ssuz.vip.edu35.ru/auth/login-page")
    btn4 = types.InlineKeyboardButton(text="Обратная связь", callback_data="feedback")
    markup.row(btn1)
    markup.row(btn3, btn2)
    markup.row(btn4)

    # Отправляем сообщение с inline-клавиатурой и фотографией
    with open(photo_path, 'rb') as photo_file:
        bot.send_photo(message.chat.id, photo_file, caption=f'''
Привет, {message.from_user.first_name}! 
Это бот-помощник для студентов Череповецкого химико-технологического колледжа 
Приятного использования!
''', reply_markup=markup)

# Обработчик нажатия на кнопку "Обратная связь"
@bot.callback_query_handler(func=lambda call: call.data == 'feedback')
def feedback_button_pressed(call):
    # Просим пользователя оставить отзыв
    bot.send_message(call.message.chat.id, '''
Отправьте ваше пожелание или предложение в виде обычного сообщения.
Оно будет передано создателям бота.
''')

# Обработчик отзыва
@bot.message_handler(func=lambda m: True)
def collect_feedback(message):
    # Передаем отзыв создателю бота
    bot.send_message(CREATOR_ID, f'''Новый отзыв от пользователя {message.from_user.username}: 
{message.text}''')
    # Сообщаем пользователю, что отзыв отправлен
    bot.send_message(message.chat.id, 'Спасибо за ваш отзыв!')

# Запуск бота
bot.polling(none_stop=True)