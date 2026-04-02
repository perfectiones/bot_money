import telebot
from telebot import types
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

# ========== НАСТРОЙКА ==========
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

telegram_token = os.getenv('TOKEN')
bot = telebot.TeleBot(telegram_token)

# Словарь для хранения состояний пользователей
user_states = {}


# ========== КЛАВИАТУРЫ ==========
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
    btn3 = types.KeyboardButton("✏️ Редактировать доход")
    btn4 = types.KeyboardButton("🗑 Удалить доход")
    btn5 = types.KeyboardButton("🔙 Назад")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup


def expense_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📃 Список расходов")
    btn2 = types.KeyboardButton("🤗 Добавить расход")
    btn3 = types.KeyboardButton("✏️ Редактировать расход")
    btn4 = types.KeyboardButton("🗑 Удалить расход")
    btn5 = types.KeyboardButton("🔙 Назад")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup


def cancel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("❌ Отмена")
    markup.add(btn)
    return markup


# ========== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()

    # Таблица доходов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Income (
            id INTEGER,
            name TEXT,
            amount REAL,
            valid_from TEXT,
            valid_to TEXT
        )
    ''')

    # Таблица расходов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Expense (
            id INTEGER,
            name TEXT,
            amount REAL,
            valid_from TEXT,
            valid_to TEXT
        )
    ''')

    conn.commit()
    conn.close()


init_db()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def format_transaction(row):
    return f"ID: {row[0]} | 📝 {row[1]} | 💰 {row[2]}₽ | 📅 {row[3]} → {row[4]}"


# ========== СТАРТ ==========
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🔙 Главное меню:", reply_markup=main_menu())


# ========== ОСНОВНОЙ ОБРАБОТЧИК ==========
@bot.message_handler(content_types=['text'])
def message(message):
    user_id = message.chat.id
    text = message.text

    # ===== 1. ОТМЕНА =====
    if text == "❌ Отмена":
        if user_id in user_states:
            del user_states[user_id]
        bot.send_message(user_id, "❌ Операция отменена", reply_markup=main_menu())
        return

    # ===== 2. ОБРАБОТКА СОСТОЯНИЙ =====
    if user_id in user_states:
        state = user_states[user_id]
        step = state.get('step')

        # ---------- УДАЛЕНИЕ (ввод ID) ----------
        if step == 'waiting_delete_id':
            try:
                record_id = int(text)
                conn = sqlite3.connect('finance.db')
                cursor = conn.cursor()

                table = 'Income' if state['type'] == 'income' else 'Expense'
                cursor.execute(f"DELETE FROM {table} WHERE rowid = ? AND id = ?", (record_id, user_id))
                conn.commit()

                if cursor.rowcount > 0:
                    bot.send_message(user_id, f"✅ Запись ID {record_id} удалена!",
                                     reply_markup=income_menu() if state['type'] == 'income' else expense_menu())
                else:
                    bot.send_message(user_id, f"❌ Запись ID {record_id} не найдена")

                conn.close()
                del user_states[user_id]

            except ValueError:
                bot.send_message(user_id, "❌ Введи число (ID)")
            except Exception as e:
                bot.send_message(user_id, f"❌ Ошибка: {e}")
                del user_states[user_id]
            return

        # ---------- РЕДАКТИРОВАНИЕ (ввод ID) ----------
        elif step == 'waiting_edit_id':
            try:
                record_id = int(text)
                conn = sqlite3.connect('finance.db')
                cursor = conn.cursor()

                table = 'Income' if state['type'] == 'income' else 'Expense'
                cursor.execute(
                    f"SELECT rowid, name, amount, valid_from, valid_to FROM {table} WHERE rowid = ? AND id = ?",
                    (record_id, user_id))
                row = cursor.fetchone()
                conn.close()

                if row:
                    user_states[user_id] = {
                        'step': 'waiting_name',
                        'type': state['type'],
                        'action': 'edit',
                        'data': {
                            'old_id': record_id,
                            'old_name': row[1],
                            'old_amount': row[2],
                            'old_date_from': row[3],
                            'old_date_to': row[4]
                        }
                    }
                    bot.send_message(user_id, f"📝 Текущее название: {row[1]}\nВведи НОВОЕ НАЗВАНИЕ (или 'пропустить'):",
                                     reply_markup=cancel_menu())
                else:
                    bot.send_message(user_id, "❌ Запись не найдена")
                    del user_states[user_id]
            except ValueError:
                bot.send_message(user_id, "❌ Введи число (ID)")
            return

        # ---------- ДОБАВЛЕНИЕ / РЕДАКТИРОВАНИЕ: НАЗВАНИЕ ----------
        elif step == 'waiting_name':
            if text.lower() != 'пропустить' or state.get('action') != 'edit':
                state['data']['name'] = text
            state['step'] = 'waiting_amount'
            bot.send_message(user_id, "💰 Введи СУММУ (только число):", reply_markup=cancel_menu())
            return

        # ---------- ДОБАВЛЕНИЕ / РЕДАКТИРОВАНИЕ: СУММА ----------
        elif step == 'waiting_amount':
            try:
                if text.lower() != 'пропустить' or state.get('action') != 'edit':
                    state['data']['amount'] = float(text)
                state['step'] = 'waiting_date_from'
                bot.send_message(user_id, "📅 Введи ДАТУ ОТ (ГГГГ-ММ-ДД) или 'сегодня':", reply_markup=cancel_menu())
            except ValueError:
                bot.send_message(user_id, "❌ Введи число! Например: 50000")
            return

        # ---------- ДОБАВЛЕНИЕ / РЕДАКТИРОВАНИЕ: ДАТА ОТ ----------
        elif step == 'waiting_date_from':
            if text.lower() == 'сегодня':
                state['data']['date_from'] = datetime.now().strftime('%Y-%m-%d')
            elif text.lower() == 'долго':
                state['data']['date_from'] = '2100-12-31'
            else:
                state['data']['date_from'] = text

            if state.get('action') == 'edit':
                state['step'] = 'waiting_new_amount'
                bot.send_message(user_id,
                                 f"💰 Текущая сумма: {state['data']['old_amount']}\nВведи НОВУЮ СУММУ (или 'пропустить'):",
                                 reply_markup=cancel_menu())
            else:
                state['step'] = 'waiting_date_to'
                bot.send_message(user_id, "📅 Введи ДАТУ ДО (ГГГГ-ММ-ДД) или 'долго':", reply_markup=cancel_menu())
            return

        # ---------- ДОБАВЛЕНИЕ: ДАТА ДО ----------
        elif step == 'waiting_date_to':
            if text.lower() == 'долго':
                state['data']['date_to'] = '2100-12-31'
            else:
                state['data']['date_to'] = text

            # Сохраняем в БД
            conn = sqlite3.connect('finance.db')
            cursor = conn.cursor()

            table = 'Income' if state['type'] == 'income' else 'Expense'
            cursor.execute(f'''
                INSERT INTO {table} (id, name, amount, valid_from, valid_to)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, state['data']['name'], state['data']['amount'], state['data']['date_from'],
                  state['data']['date_to']))

            conn.commit()
            conn.close()

            bot.send_message(user_id,
                             f"✅ Добавлено!\n📝 {state['data']['name']}\n💰 {state['data']['amount']}₽\n📅 {state['data']['date_from']} → {state['data']['date_to']}",
                             reply_markup=income_menu() if state['type'] == 'income' else expense_menu())
            del user_states[user_id]
            return

        # ---------- РЕДАКТИРОВАНИЕ: НОВАЯ СУММА ----------
        elif step == 'waiting_new_amount':
            if text.lower() != 'пропустить':
                try:
                    state['data']['new_amount'] = float(text)
                except ValueError:
                    bot.send_message(user_id, "❌ Введи число или 'пропустить'")
                    return

            state['step'] = 'waiting_new_date_from'
            bot.send_message(user_id,
                             f"📅 Текущая дата ОТ: {state['data']['old_date_from']}\nВведи НОВУЮ ДАТУ (ГГГГ-ММ-ДД) или 'пропустить':",
                             reply_markup=cancel_menu())
            return

        # ---------- РЕДАКТИРОВАНИЕ: НОВАЯ ДАТА ОТ ----------
        elif step == 'waiting_new_date_from':
            if text.lower() != 'пропустить':
                if text.lower() == 'сегодня':
                    state['data']['new_date_from'] = datetime.now().strftime('%Y-%m-%d')
                elif text.lower() == 'долго':
                    state['data']['new_date_from'] = '2100-12-31'
                else:
                    state['data']['new_date_from'] = text

            state['step'] = 'waiting_new_date_to'
            bot.send_message(user_id,
                             f"📅 Текущая дата ДО: {state['data']['old_date_to']}\nВведи НОВУЮ ДАТУ (ГГГГ-ММ-ДД) или 'пропустить':",
                             reply_markup=cancel_menu())
            return

        # ---------- РЕДАКТИРОВАНИЕ: НОВАЯ ДАТА ДО ----------
        elif step == 'waiting_new_date_to':
            if text.lower() != 'пропустить':
                if text.lower() == 'долго':
                    state['data']['new_date_to'] = '2100-12-31'
                else:
                    state['data']['new_date_to'] = text

            # Обновляем в БД
            conn = sqlite3.connect('finance.db')
            cursor = conn.cursor()

            table = 'Income' if state['type'] == 'income' else 'Expense'

            updates = []
            params = []

            if 'new_amount' in state['data']:
                updates.append("amount = ?")
                params.append(state['data']['new_amount'])
            if 'new_date_from' in state['data']:
                updates.append("valid_from = ?")
                params.append(state['data']['new_date_from'])
            if 'new_date_to' in state['data']:
                updates.append("valid_to = ?")
                params.append(state['data']['new_date_to'])

            params.append(state['data']['old_id'])
            params.append(user_id)

            cursor.execute(f'''
                UPDATE {table}
                SET {', '.join(updates)}
                WHERE rowid = ? AND id = ?
            ''', params)

            conn.commit()
            conn.close()

            bot.send_message(user_id, "✅ Запись обновлена!",
                             reply_markup=income_menu() if state['type'] == 'income' else expense_menu())
            del user_states[user_id]
            return

    # ===== 3. ОБЫЧНЫЕ КОМАНДЫ =====

    # 🎯 Доходы
    if text == '🎯 Доходы':
        bot.send_message(user_id, "💰 Меню доходов:", reply_markup=income_menu())

    # ⛔ Расходы
    elif text == '⛔ Расходы':
        bot.send_message(user_id, "💸 Меню расходов:", reply_markup=expense_menu())

    # 📃 Список доходов
    elif text == '📃 Список доходов':
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rowid, name, amount, valid_from, valid_to FROM Income WHERE id = ? ORDER BY valid_from DESC",
            (user_id,))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            msg = "📋 *Список доходов:*\n\n"
            for row in rows:
                date_from_db = datetime.strptime(row[-1], '%Y-%m-%d')
                current_date = datetime.now()
                # print(date_from_db > current_date)
                msg += format_transaction(
                    row) + " ✅" if date_from_db > current_date else " ❌" + "\n\n"
            bot.send_message(user_id, msg, parse_mode='Markdown')
        else:
            bot.send_message(user_id, "📭 Нет доходов. Добавьте первый!")

    # 🤗 Добавить доход
    elif text == '🤗 Добавить доход':
        user_states[user_id] = {
            'step': 'waiting_name',
            'type': 'income',
            'action': 'add',
            'data': {}
        }
        bot.send_message(user_id, "📝 Введи НАЗВАНИЕ дохода (например: Зарплата):", reply_markup=cancel_menu())

    # ✏️ Редактировать доход
    elif text == '✏️ Редактировать доход':
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, name, amount FROM Income WHERE id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            msg = "✏️ *Выбери ID для редактирования:*\n\n"
            for row in rows:
                msg += f"ID: {row[0]} | {row[1]} | {row[2]}₽\n"
            bot.send_message(user_id, msg, parse_mode='Markdown')
            bot.send_message(user_id, "Введи ID дохода, который хочешь редактировать:", reply_markup=cancel_menu())
            user_states[user_id] = {'step': 'waiting_edit_id', 'type': 'income', 'data': {}}
        else:
            bot.send_message(user_id, "📭 Нет доходов для редактирования")

    # 🗑 Удалить доход
    elif text == '🗑 Удалить доход':
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, name, amount FROM Income WHERE id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            msg = "🗑 *Выбери ID для удаления:*\n\n"
            for row in rows:
                msg += f"ID: {row[0]} | {row[1]} | {row[2]}₽\n"
            bot.send_message(user_id, msg, parse_mode='Markdown')
            bot.send_message(user_id, "Введи ID дохода, который хочешь удалить:", reply_markup=cancel_menu())
            user_states[user_id] = {'step': 'waiting_delete_id', 'type': 'income', 'data': {}}
        else:
            bot.send_message(user_id, "📭 Нет доходов для удаления")

    # 📃 Список расходов
    elif text == '📃 Список расходов':
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rowid, name, amount, valid_from, valid_to FROM Expense WHERE id = ? ORDER BY valid_from DESC",
            (user_id,))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            msg = "📋 *Список расходов:*\n\n"
            for row in rows:
                date_from_db = datetime.strptime(row[-1], '%Y-%m-%d')
                current_date = datetime.now()
                # print(date_from_db > current_date)
                msg += format_transaction(row) + "✅" if date_from_db > current_date else "❌" + "\n\n"

            bot.send_message(user_id, msg, parse_mode='Markdown')
        else:
            bot.send_message(user_id, "📭 Нет расходов. Добавьте первый!")

    # 🤗 Добавить расход
    elif text == '🤗 Добавить расход':
        user_states[user_id] = {
            'step': 'waiting_name',
            'type': 'expense',
            'action': 'add',
            'data': {}
        }
        bot.send_message(user_id, "📝 Введи НАЗВАНИЕ расхода (например: Продукты):", reply_markup=cancel_menu())

    # ✏️ Редактировать расход
    elif text == '✏️ Редактировать расход':
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, name, amount FROM Expense WHERE id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            msg = "✏️ *Выбери ID для редактирования:*\n\n"
            for row in rows:
                msg += f"ID: {row[0]} | {row[1]} | {row[2]}₽\n"
            bot.send_message(user_id, msg, parse_mode='Markdown')
            bot.send_message(user_id, "Введи ID расхода, который хочешь редактировать:", reply_markup=cancel_menu())
            user_states[user_id] = {'step': 'waiting_edit_id', 'type': 'expense', 'data': {}}
        else:
            bot.send_message(user_id, "📭 Нет расходов для редактирования")

    # 🗑 Удалить расход
    elif text == '🗑 Удалить расход':
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, name, amount FROM Expense WHERE id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            msg = "🗑 *Выбери ID для удаления:*\n\n"
            for row in rows:
                msg += f"ID: {row[0]} | {row[1]} | {row[2]}₽\n"
            bot.send_message(user_id, msg, parse_mode='Markdown')
            bot.send_message(user_id, "Введи ID расхода, который хочешь удалить:", reply_markup=cancel_menu())
            user_states[user_id] = {'step': 'waiting_delete_id', 'type': 'expense', 'data': {}}
        else:
            bot.send_message(user_id, "📭 Нет расходов для удаления")

    # 🔙 Назад
    elif text == '🔙 Назад':
        if user_id in user_states:
            del user_states[user_id]
        bot.send_message(user_id, "🔙 Главное меню:", reply_markup=main_menu())

    else:
        bot.send_message(user_id, "Используйте кнопки меню", reply_markup=main_menu())


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🚀 Бот запущен...")
    bot.polling(none_stop=True, interval=0)
