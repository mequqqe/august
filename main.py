import random
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

message_counter = 0
correct_answer = None  
# Создайте словарь для отслеживания пользователей, которые уже дали правильные ответы
answered_correctly = {}



# Создаем подключение к базе данных или создаем файл базы данных, если он не существует
conn = sqlite3.connect('user_scores.db')
cursor = conn.cursor()

# Создаем таблицу для хранения информации о пользователях и их успехах
# Измените создание таблицы для хранения информации о пользователях и их успехах
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_scores (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    score INTEGER DEFAULT 0
)
''')


# Сохраняем изменения в базе данных и закрываем соединение
conn.commit()
conn.close()



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

# Функция для генерации математической задачи
def generate_math_problem():
    # Генерируем два случайных числа в диапазоне от 1 до 100
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 100)

    # Выбираем случайную математическую операцию (сложение, вычитание, умножение)
    operation = random.choice(['+', '*'])

    # Генерируем текст задачи
    if operation == '+':
        problem_text = f"{num1} + {num2} = ?"
        answer = num1 + num2
    elif operation == '*':
        problem_text = f"{num1} * {num2} = ?"
        answer = num1 * num2

    return problem_text, answer

# Обработчик входящих сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global message_counter, correct_answer

    # Если пользователь отправил ответ на арифметическую задачу
    if message_counter % 20 != 0 and message.text.isdigit():
        user_answer = int(message.text)

        # Проверяем, не отвечал ли пользователь уже ранее
        if message.from_user.id in answered_correctly:
            bot.send_message(message.chat.id, "Вы уже давали правильный ответ ранее.")
            return

        # Проверяем правильность ответа пользователя
        if user_answer == correct_answer:
            bot.send_message(message.chat.id, "Правильно! Вам начислено 5 баллов.")

            # Обновляем счет пользователя в базе данных
            update_user_score(message.from_user.id, 5)

            # Добавляем пользователя в словарь answered_correctly
            answered_correctly[message.from_user.id] = True

        else:
            bot.send_message(message.chat.id, "Неправильно. Попробуйте еще раз.")
    
    # Увеличиваем счетчик сообщений после каждого сообщения
    message_counter += 1

    # Если достигнуто 20 сообщений, отправляем новую математическую задачу
    if message_counter % 80 == 0:
        problem, correct_answer = generate_math_problem()
        bot.send_message(message.chat.id, problem)




# Функция для обновления счета пользователя в базе данных
def update_user_score(user_id, points):
    conn = sqlite3.connect('user_scores.db')
    cursor = conn.cursor()

    # Проверяем, есть ли пользователь в базе данных
    cursor.execute('SELECT * FROM user_scores WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()

    if user_data is None:
        # Если пользователь не найден, добавляем его в базу данных
        cursor.execute('INSERT INTO user_scores (user_id, username, score) VALUES (?, ?, ?)', (user_id, '', points))
    else:
        # Если пользователь найден, обновляем его счет
        current_score = user_data[2]
        new_score = current_score + points
        cursor.execute('UPDATE user_scores SET score = ? WHERE user_id = ?', (new_score, user_id))

    conn.commit()
    conn.close()

def get_top_users(limit=10):
    conn = sqlite3.connect('user_scores.db')
    cursor = conn.cursor()

    # Извлекаем данные о пользователях и их баллах, сортируем по убыванию баллов
    cursor.execute('SELECT user_id, username, score FROM user_scores ORDER BY score DESC LIMIT ?', (limit,))
    top_users = cursor.fetchall()

    conn.close()

    return top_users



# Обработчик команды /top
@bot.message_handler(commands=['top'])
def top(message):
    # Получите топ-пользователей (по умолчанию 10)
    top_users = get_top_users()

    if top_users:
        top_message = "Топ пользователей, решавших математические задачи:\n"
        for i, (user_id, username, score) in enumerate(top_users, start=1):
            top_message += f"{i}. {username} - {score} баллов\n"

        bot.send_message(message.chat.id, top_message)
    else:
        bot.send_message(message.chat.id, "Пока нет пользователей в топе.")




# Запуск бота
if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Произошла ошибка: {str(e)}. Перезапуск бота через 10 секунд...")
            time.sleep(10)
