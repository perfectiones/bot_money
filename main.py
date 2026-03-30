import telebot
from telebot import types
import os
import sqlite3

from dotenv import load_dotenv


# @bot.message_handler(content_types=['text'])
# def message(message):
#     if message.text == 'Добавить траты':
#         connect = sqlite3.connect('database.db')
#         cursor = connect.cursor()
#
#         cursor.execute("""
#                    CREATE TABLE IF NOT EXISTS SALES (
#                    id INTEGER PRIMARY KEY,
#                    name TEXT)
#                """)
#
#         connect.commit()
#
#         user_id = message.chat.id
#         user_name = "slamich"
#
#         cursor.execute("INSERT INTO SALES (id, name) VALUES (?, ?)", (user_id, user_name))
#         connect.commit()
#     elif message.text == 'Показать траты':
#         connect = sqlite3.connect('database.db')
#         cursor = connect.cursor()
#
#         cursor.execute("SELECT * FROM SALES")
#         rows = cursor.fetchall()
#         if rows:
#             text = "📋 Список записей:\n\n"
#             for row in rows:
#                 text += f"ID: {row[0]} | Имя: {row[1]}\n"
#             bot.send_message(message.chat.id, text)
#         else:
#             bot.send_message(message.chat.id, "❌ Записей пока нет!")
#
#         connect.close()
# @bot.message_handler(content_types=["text"])
# def handle_text(message):
#     number = int(message.text) * 2
#     bot.send_message(message.chat.id, f'Вы написали: {number}'  )

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

telegram_token = os.getenv('TOKEN')
bot = telebot.TeleBot(telegram_token)

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🎯 Доходы")
    btn2 = types.KeyboardButton("⛔ Расходы")
    markup.add(btn1, btn2)
    return markup

def income_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📃 Список доходов")
    btn2 = types.KeyboardButton("🤗 Добавить доход")
    btn3 = types.KeyboardButton("⚙️ Редактировать доход")
    btn4 = types.KeyboardButton("🔙 Назад")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

def expense_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📃 Список расходов")
    btn2 = types.KeyboardButton("🤗 Добавить расход")
    btn3 = types.KeyboardButton("⚙️ Редактировать расход")
    btn4 = types.KeyboardButton("🔙 Назад")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🔙 Главное меню:", reply_markup=main_menu())

@bot.message_handler(content_types=['text'])
def message(message):
    # 🎯 Доходы
    if message.text == '🎯 Доходы':
        bot.send_message(message.chat.id, "💰 Меню доходов:", reply_markup=income_menu())

    # ⛔ Расходы
    elif message.text == '⛔ Расходы':
        bot.send_message(message.chat.id, "💸 Меню расходов:", reply_markup=expense_menu())

    # 📃 Список доходов
    elif message.text == '📃 Список доходов':
        connect = sqlite3.connect('database.db')
        cursor = connect.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='SALES'")
        if cursor.fetchone():
            cursor.execute("SELECT * FROM SALES")
            rows = cursor.fetchall()
            text = "📋 Список расходов:\n\n"
            for row in rows:
                text += f"ID: {row[0]} | Название: {row[1]}\n"
            bot.send_message(message.chat.id, text)

    # 🤗 Добавить доход
    elif message.text == '🤗 Добавить доход':
        bot.send_message(message.chat.id, "➕ Введи сумму дохода:")

    # ⚙️ Редактировать доход
    elif message.text == '⚙️ Редактировать доход':
        bot.send_message(message.chat.id, "⚙️ Редактирование доходов...")

    # 📃 Список расходов (из БД)
    elif message.text == '📃 Список расходов':
        connect = sqlite3.connect('database.db')
        cursor = connect.cursor()

        cursor.execute("SELECT * FROM SALES")
        rows = cursor.fetchall()

        if rows:
            text = "📋 Список расходов:\n\n"
            for row in rows:
                text += f"ID: {row[0]} | Имя: {row[1]}\n"
            bot.send_message(message.chat.id, text)
        else:
            bot.send_message(message.chat.id, "❌ Расходов пока нет!")

        connect.close()

    # 🤗 Добавить расход
    elif message.text == '🤗 Добавить расход':
        connect = sqlite3.connect('database.db')
        cursor = connect.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SALES (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        connect.commit()

        user_id = message.chat.id
        user_name = "slamich"

        cursor.execute("INSERT INTO SALES (id, name) VALUES (?, ?)", (user_id, user_name))
        connect.commit()
        connect.close()

        bot.send_message(message.chat.id, "✅ Расход добавлен!")

    # ⚙️ Редактировать расход
    elif message.text == '⚙️ Редактировать расход':
        bot.send_message(message.chat.id, "⚙️ Редактирование расходов...")

    # 🔙 Назад
    elif message.text == '🔙 Назад':
        bot.send_message(message.chat.id, "🔙 Главное меню:", reply_markup=main_menu())



bot.polling(none_stop=True, interval=0)