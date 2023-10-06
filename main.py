import telebot
import sqlite3
import time
import threading
from telebot import types

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
bot = telebot.TeleBot('6509542841:AAF307o-FhkzH8umFpZV0p2T6NgW2NpyWz8')

reminders = []

# Функция для создания подключения к БД для каждого потока
def get_db_connection():
    return sqlite3.connect('reminders.db')

# Функция для создания таблицы, если она не существует
def create_table_if_not_exists():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            interval INTEGER,  -- интервал в минутах или часах
            interval_type TEXT  -- "minutes" или "hours"
        )
    ''')
    conn.commit()
    conn.close()

# Запускаем функцию создания таблицы один раз при старте приложения
create_table_if_not_exists()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Чтобы добавить напоминание, отправьте /add_reminder")

@bot.message_handler(commands=['add_reminder'])
def add_reminder(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(types.KeyboardButton('Минуты'))
    markup.add(types.KeyboardButton('Часы'))
    bot.send_message(chat_id, "Выберите единицу измерения интервала:", reply_markup=markup)
    bot.register_next_step_handler(message, get_interval_unit)

def get_interval_unit(message):
    chat_id = message.chat.id
    interval_unit = message.text.lower()  # Преобразуем текст в нижний регистр
    if interval_unit not in ('минуты', 'часы'):
        bot.send_message(chat_id, "Пожалуйста, выберите один из вариантов: 'Минуты' или 'Часы'.")
        return
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(chat_id, f"Введите интервал в {interval_unit}:", reply_markup=markup)
    bot.register_next_step_handler(message, lambda message: get_interval(message, interval_unit))

def get_interval(message, interval_unit):
    chat_id = message.chat.id
    user_id = message.from_user.id
    interval_str = message.text

    try:
        interval = int(interval_str)
        if interval <= 0:
            bot.send_message(chat_id, "Интервал должен быть положительным числом больше нуля.")
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        # Сохраняем напоминание в БД
        cursor.execute('INSERT INTO reminders (user_id, text, interval, interval_type) VALUES (?, ?, ?, ?)',
                       (user_id, '', interval, 'minutes' if interval_unit == 'минуты' else 'hours'))
        conn.commit()
        conn.close()
        bot.send_message(chat_id, f"Интервал {interval} {interval_unit} добавлен. Теперь введите текст напоминания.")
        bot.register_next_step_handler(message, get_text)
    except ValueError:
        bot.send_message(chat_id, "Некорректный формат интервала. Введите число (например, 2 для каждых двух часов).")
    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {str(e)}")

def get_text(message):
    chat_id = message.chat.id
    text = message.text

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reminders WHERE user_id = ? AND text = ""', (message.from_user.id,))
    reminder = cursor.fetchone()

    if reminder is not None:
        # Обновляем запись в БД с текстом напоминания
        cursor.execute('UPDATE reminders SET text = ? WHERE id = ?', (text, reminder[0]))
        conn.commit()
        conn.close()
        bot.send_message(chat_id, "Напоминание добавлено.")
    else:
        bot.send_message(chat_id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")

@bot.message_handler(commands=['list_reminders'])
def list_reminders(message):
    chat_id = message.chat.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reminders WHERE user_id = ? AND text != ""', (message.from_user.id,))
    reminders = cursor.fetchall()
    conn.close()

    if not reminders:
        bot.send_message(chat_id, "У вас нет активных напоминаний.")
    else:
        reminder_list = "Ваши активные напоминания:\n"
        for idx, reminder in enumerate(reminders, start=1):
            interval = reminder[2]
            interval_type = reminder[3]
            text = reminder[1]
            reminder_list += f"{idx}. Каждые {interval} {interval_type}: {text}\n"
        bot.send_message(chat_id, reminder_list)

@bot.message_handler(commands=['delete_reminder'])
def delete_reminder(message):
    chat_id = message.chat.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reminders WHERE user_id = ? AND text != ""', (message.from_user.id,))
    reminders = cursor.fetchall()
    conn.close()

    if not reminders:
        bot.send_message(chat_id, "У вас нет активных напоминаний для удаления.")
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        for idx, reminder in enumerate(reminders, start=1):
            text = reminder[1]
            markup.add(types.KeyboardButton(str(idx)))
        markup.add(types.KeyboardButton('Отмена'))
        bot.send_message(chat_id, "Выберите номер напоминания для удаления или нажмите 'Отмена':", reply_markup=markup)
        bot.register_next_step_handler(message, confirm_delete)

def confirm_delete(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    selected_option = message.text
    if selected_option == 'Отмена':
        bot.send_message(chat_id, "Удаление отменено.")
    else:
        try:
            selected_idx = int(selected_option) - 1
            if selected_idx >= 0 and selected_idx < len(reminders):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('DELETE FROM reminders WHERE id = ?', (reminders[selected_idx][0],))
                conn.commit()
                conn.close()
                bot.send_message(chat_id, "Напоминание удалено.")
            else:
                bot.send_message(chat_id, "Некорректный выбор. Пожалуйста, выберите номер напоминания для удаления.")
        except ValueError:
            bot.send_message(chat_id, "Некорректный выбор. Пожалуйста, выберите номер напоминания для удаления.")
        except Exception as e:
            bot.send_message(chat_id, f"Произошла ошибка: {str(e)}")

# Функция для отправки напоминаний
def send_reminders():
    while True:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reminders')
        reminders = cursor.fetchall()
        conn.close()

        current_time = time.localtime()
        for reminder in reminders:
            user_id, text, interval, interval_type = reminder[1], reminder[2], reminder[3], reminder[4]
            
            # Проверяем тип чата
            chat_type = bot.get_chat(user_id).type
            if chat_type == 'private':  # Чат является личным
                if interval_type == 'minutes':
                    if current_time.tm_min % interval == 0:
                        bot.send_message(user_id, f"Напоминание: {text}")
                elif interval_type == 'hours':
                    if current_time.tm_hour % interval == 0 and current_time.tm_min == 0:
                        bot.send_message(user_id, f"Напоминание: {text}")

        time.sleep(60)   # Проверяем каждую минуту

if __name__ == "__main__":
    # Запускаем функцию для отправки напоминаний в отдельном потоке
    t = threading.Thread(target=send_reminders)
    t.start()

    # Запустим бота
    bot.polling()
