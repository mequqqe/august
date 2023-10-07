import telebot
import sqlite3
import time
import threading
from telebot import types
import requests
import re

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
TOKEN = ('6509542841:AAF307o-FhkzH8umFpZV0p2T6NgW2NpyWz8')

CHAT_ID = -1001718975100

bot = telebot.TeleBot(TOKEN)

# Функция для отправки "пинга" каждые 30 минут
def send_ping():
    while True:
        try:
            # Пауза в 30 минут перед отправкой следующего "пинга"
            time.sleep(1800)
        except Exception as e:
            print(f"Произошла ошибка при отправке пинга: {str(e)}")

# Запуск потока для отправки "пинга"
ping_thread = threading.Thread(target=send_ping)
ping_thread.daemon = True
ping_thread.start()

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Обработчик команды /start.
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton("Отправить анонимное сообщение")
    markup.add(item)
    bot.send_message(message.chat.id, "Привет! Я бот для отправки анонимных сообщений. "
                                      "Для отправки сообщения нажмите кнопку ниже.",
                     reply_markup=markup)

# Обработчик кнопки "Отправить анонимное сообщение".
@bot.message_handler(func=lambda message: message.text == "Отправить анонимное сообщение")
def send_anonymous_button(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "Введите текст сообщения для отправки анонимно.")

        # Ставим обработчик для следующего сообщения пользователя.
        bot.register_next_step_handler(message, save_anonymous_message)
    else:
        bot.send_message(message.chat.id, "Эта кнопка работает только в личных сообщениях с ботом.")

# Функция для сохранения анонимного сообщения и отправки в беседу.
def save_anonymous_message(message):
    user_id = message.from_user.id
    message_text = message.text

    # Отправляем анонимное сообщение в указанную беседу, заменяя отправителя на "Аноним".
    bot.send_message(CHAT_ID, "Аноним: " + message_text)

# Обработчик команды /send_anonymous в личных сообщениях с ботом.
@bot.message_handler(commands=['send_anonymous'])
def send_anonymous(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "Введите текст сообщения для отправки анонимно.")

        # Ставим обработчик для следующего сообщения пользователя.
        bot.register_next_step_handler(message, save_anonymous_message)
    else:
        bot.send_message(message.chat.id, "Команда /send_anonymous работает только в личных сообщениях с ботом.")

# Обработчик команды /mention_all в беседах.
@bot.message_handler(commands=['mention_all'], func=lambda message: message.chat.type == 'supergroup')
def mention_all(message):
    chat_id = message.chat.id

    # Получаем количество участников в беседе.
    members_count = bot.get_chat_members_count(chat_id)

    # Формируем строку с упоминаниями всех участников.
    mentions = ""
    for i in range(1, members_count + 1):
        mentions += f"@user{i} "

    # Отправляем упоминания всех участников в беседе.
    bot.send_message(chat_id, mentions + "вас вызывают!")

# Запуск бота
if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Произошла ошибка: {str(e)}. Перезапуск бота через 10 секунд...")
            time.sleep(10)
