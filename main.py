from telebot import types
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import sys
import sqlite3
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from markups import *
from configs.settings import *
from bot_instance import bot

from bot_logging import *
import handlers.bot_statistics as bot_statistics
import handlers.bot_accounts as bot_accounts
import handlers.bot_settings as bot_settings
import handlers.bot_balances as bot_balances
import handlers.bot_categories as bot_categories
import handlers.bot_admin as bot_admin
from utils.bot_db import *
from utils.bot_admin_db import *
from markups import *
import threading

# Словарь для хранения состояний пользователей
user_states = {}

# ID администратора из настроек
ADMIN_ID = ADMIN_USER_ID  # Должен быть определен в configs/settings.py

introducing_text = ("👋 Добро пожаловать в FinanceBot!\n\n"
        "Для добавления расходов напиши мне:\n"
        "<i>сумма категория [комментарий]</i>\n\n"
        "Добавить транзакцию на конкретный счет:\n"
        "<i>сумма счет категория [комментарий]</i>\n\n"
        "Выберите нужный раздел в меню ниже:")

help_text = ("📝 Как добавить транзакцию:\n\n"
             "сумма категория [комментарий]\n\n"
             "Если хотите добавить транзакцию на конкретный счет, то используйте:\n"
             "сумма счет категория [комментарий]\n\n"
             "<b>Примеры:</b>\n"
             "<i>100 сбербанк еда пицца</i>\n"
             "<i>350 еда пицца</i>\n"
             "<i>60 транспорт автобус</i>\n"
             "<i>50000 доход зарплата</i>")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    is_new = False
    
     # Инициализируем базу данных при первом запуске
    init_db()

    if not get_user(user_id):
        # Добавляем пользователя в базу данных и создаем для него счет по умолчанию
        add_user(user_id, first_name, last_name, username)
        add_account(user_id, "Счёт по умолчанию", 0)

        # делаем этот счет счетом по умолчанию
        new_account_id = get_account_id_by_name(user_id, "Счёт по умолчанию")
        set_default_account(user_id, new_account_id)

    
        is_new = True

    logger.info("Пользователь %s вызвал команду start", username)
    logger.info("Для пользователя %s создан счет по умолчанию", username)
    
    if is_new:
        bot.send_message(user_id, "Для тебя я создал новый счет по умолчанию!\n\n"
                     "На нём пока что ноль рублей.\n" 
                     "Ты можешь ознакомиться подробнее по команде /accounts")
    
    bot.send_message(
        message.chat.id, 
        introducing_text,
        parse_mode="HTML",
        reply_markup=main_menu_markup()
    )
    
# обработка команды menu
@bot.message_handler(commands=['menu'])
def handle_menu(message):
    user_id = message.from_user.id
    logger.info("Пользователь %s вызвал команду menu", user_id)
    bot.send_message(user_id, "👋Выберите интересующий вас раздел:", reply_markup=main_menu_markup())

# обработка команды feedback
@bot.message_handler(commands=['feedback'])
def handle_feedback(message):
    user_id = message.from_user.id
    logger.info("Пользователь %s вызвал команду feedback", user_id)
    
    # Устанавливаем состояние пользователя
    user_states[user_id] = {
        "state": "waiting_for_feedback",
        "data": {}
    }
    
    # Отправляем сообщение с инструкцией
    bot.send_message(
        user_id, 
        "📝 Пожалуйста, напишите ваш отзыв или предложение в следующем сообщении.\n\nЧтобы отменить, отправьте /cancel",
        reply_markup=types.ReplyKeyboardRemove()
    )

# Обработчик для отмены ввода обратной связи
@bot.message_handler(commands=['cancel'])
def handle_cancel(message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id].get("state") == "waiting_for_feedback":
        user_states.pop(user_id, None)
        bot.send_message(
            user_id, 
            "❌ Отправка отзыва отменена."
        )
        handle_menu(message)
    
# Обработчик получения обратной связи
@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id].get("state") == "waiting_for_feedback")
def process_feedback(message):
    user_id = message.from_user.id
    feedback_text = message.text
    
    # Получаем данные о пользователе
    user_info = f"Пользователь: {message.from_user.first_name}"
    if message.from_user.last_name:
        user_info += f" {message.from_user.last_name}"
    if message.from_user.username:
        user_info += f" (@{message.from_user.username})"
    user_info += f"\nID пользователя: {user_id}"
    
    # Формируем сообщение для администратора
    admin_message = f"📨 Новый отзыв!\n\n{user_info}\n\n📝 Отзыв:\n{feedback_text}"
    
    try:
        # Отправляем отзыв администратору
        bot.send_message(ADMIN_ID, admin_message)
        
        # Отправляем подтверждение пользователю
        bot.send_message(
            user_id, 
            "✅ Спасибо за ваш отзыв! Он был передан администратору."
        )
        handle_menu(message)
        
        logger.info(f"Пользователь {user_id} отправил отзыв: {feedback_text}")
    except Exception as e:
        bot.send_message(
            user_id, 
            "❌ Произошла ошибка при отправке отзыва. Пожалуйста, попробуйте позже."
        )
        handle_menu(message)
        logger.error(f"Ошибка при отправке отзыва от пользователя {user_id}: {str(e)}")
    
    # Очищаем состояние пользователя
    user_states.pop(user_id, None)

# обработка команды очистки всех данных о пользователе
@bot.message_handler(commands=['delete_all_information'])
def handle_delete_all_information(message):
    chat_id = message.from_user.id
    
    logger.info("Пользователь %s вызвал команду удаления всех данных", chat_id)
    bot.send_message(chat_id, "Ты уверен, что хочешь удалить все данные?", reply_markup=yes_no_markup("delete_all_information"))


# обработчик выбора пользователя, удалять данные или нет    
@bot.callback_query_handler(func = lambda call: call.data.startswith("delete_all_information_"))
def handle_delete_all_information_yes(call):
    chat_id = call.from_user.id
    
    bot.answer_callback_query(call.id)
    if call.data == "delete_all_information_yes":
        delete_all_information(chat_id)
        logger.info("Пользователь %s подтвердил удаление всех данных", chat_id)
        bot.reply_to(call.message, "Все данные успешно удалены...\n\nЧтобы перейти в меню нажми /start")
    else:
        bot.reply_to(call.message, "Данные все еще сохранены!\n\nЧтобы перейти в меню нажми /start")

# обработка команды help
@bot.message_handler(commands=['help'])
def handle_help(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "👋Выберите интересующий вас раздел:", reply_markup=help_markup())


# Обработка callback_data
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == "main_menu":
         bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=introducing_text,
            reply_markup=main_menu_markup(),
            parse_mode="HTML"
        )
    elif call.data == "help":
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="❓ Помощь\n\nВыберите интересующий вас раздел:",
            reply_markup=help_markup()
        )
    elif call.data == "back_to_main":
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=introducing_text,
            reply_markup=main_menu_markup(),
            parse_mode="HTML"
        )
    elif call.data == "feedback_cmd":
        bot.answer_callback_query(call.id)
        # Устанавливаем состояние пользователя
        user_states[chat_id] = {
            "state": "waiting_for_feedback",
            "data": {}
        }
        
        # Отправляем сообщение с инструкцией
        bot.send_message(
            chat_id, 
            "📝 Пожалуйста, напишите ваш отзыв или предложение в следующем сообщении.\n\nЧтобы отменить, отправьте /cancel",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    # Обработка разделов помощи
    elif call.data == "help_add_expense":
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=help_text,
            reply_markup=help_markup(),
            parse_mode="HTML"
        )

    elif call.data == "help_get_report":
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="📊 Как получить отчёт:\n\nПока что я не умею такого... Но скоро научусь!",
            reply_markup=help_markup()
        )


    # Подтверждаем обработку callback
    bot.answer_callback_query(call.id)


# Обработчик ввода расходов
@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def handle_transaction(message):
    try:
        user_id = message.from_user.id
        parts = message.text.split()
        categories = get_categories(user_id)
        income_categories = list(map(lambda a: a[1], filter(lambda a: not a[3], categories)))
        expense_categories = list(map(lambda a: a[1], filter(lambda a: a[3], categories)))
        is_another_account =  False
        # accounts = list(map(lambda a: a[1], get_accounts(user_id)))
        
        

        if len(parts) < 2:
            bot.reply_to(message, "❗Неверный формат. \n\nИспользуйте:\n"
                                "сумма категория [комментарий] - для расходов\n\n"
                                "❔ Записать транзакцию на конкретный счет:\n"
                                "сумма счет категория [комментарий]")
            return
        


        if get_account_id_by_name(user_id, parts[1]):
            is_another_account = True
            account_id = get_account_id_by_name(user_id, parts[1])
            category = parts[2].lower()
        else:
            account_id = get_default_account_id(user_id)
            if not account_id:
                bot.reply_to(message, "❌ У вас не установлен основной счет. Установите его в /accounts")
                return
            category = parts[1].lower()

        

        if category not in get_categories_name(user_id):
            bot.send_message(user_id, "К сожалению такой категории нет.\nЧтобы добавить перейдите в /categories")
            return

        logger.info("Пользователь %s (ID: %s) записал транзакцию: %s", 
                   message.from_user.username, user_id, message.text)

        
        is_income = category in income_categories

        try:
            amount = float(parts[0])
        except ValueError:
            bot.send_message(user_id, "Сумма должна быть числом")
            return
        
    
        if is_another_account:
            comment = ' '.join(parts[3:]) if len(parts) > 3 else ''
        else:
            comment = ' '.join(parts[2:]) if len(parts) > 2 else ''
        # Получаем основной счет
        


        
       # Добавляем транзакцию
        if add_transaction(user_id, account_id, category, amount, comment):
            # Получаем обновленный баланс счета
            account_info = get_account_info(account_id)
            if account_info:
                account_name, new_balance, _ = account_info
                
                # Формируем сообщение в зависимости от типа транзакции
                if is_income:
                    response = (f"✅ Доход добавлен:\n"
                              f"Сумма: +{amount} руб.\n"
                              f"Комментарий: {comment if comment else 'без комментария'}\n\n"
                              f"💰 Баланс счета\n<i>{account_name}</i>: <b>{new_balance}</b> руб.")
                else:
                    response = (f"✅ Расход добавлен:\n"
                              f"Категория: <i>{category}</i>\n"
                              f"Сумма: <i>-{amount} руб.</i>\n"
                              f"Комментарий: {comment if comment else 'без комментария'}\n\n"
                              f"💰 Баланс счета\n<i>{account_name}</i>: <b>{new_balance}</b> руб.")
                
                additional_text = "\n\nДля того, чтобы вернуться в меню, нажмите /start\nПосмотреть расходы за сегодня /expenses_by_this_day"
                response += additional_text

                bot.send_message(user_id, response, parse_mode="HTML")
            else:
                bot.send_message(user_id, "❌ Ошибка при получении информации о счете")
        else:
            bot.send_message(user_id, "❌ Произошла ошибка при добавлении транзакции")
    
    except Exception as e:
        logger.exception("Ошибка %s при добавлении транзакции", e)
        bot.send_message(user_id, "❌ Произошла ошибка при добавлении транзакции")


def send_reminder(user_id):
    """Отправка напоминания пользователю"""
    try:
        settings = get_reminder_settings(user_id)
        if not settings['enabled']:
            return
        
        # Проверяем, установлен ли часовой пояс
        if not has_timezone(user_id):
            # Предлагаем установить часовой пояс
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                "🌍 Установить часовой пояс", 
                callback_data="set_timezone"
            ))
            
            bot.send_message(
                user_id,
                "⚠️ Для корректной работы напоминаний необходимо установить ваш часовой пояс.\n"
                "Пожалуйста, нажмите на кнопку ниже для настройки:",
                reply_markup=markup
            )
            return
        
        # Проверяем, есть ли траты за сегодня
        today_transactions = get_period_statistics(user_id, period='day')
        if not today_transactions or (not today_transactions['income'] and not today_transactions['expense']):
            bot.send_message(
                user_id,
                "🔔 Напоминание!\n\n"
                "Не забудьте внести траты за сегодня! 😊"
            )
    except Exception as e:
        logger.exception("Ошибка %s при отправке напоминания", str(e))

def check_and_send_reminders():
    """Проверка и отправка напоминаний всем пользователям"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT user_id, reminder_time, timezone_offset
        FROM users 
        WHERE reminders_enabled = TRUE
        ''')
        users = cursor.fetchall()
        
        # Текущее время по UTC
        utc_time = datetime.now(timezone.utc)
        
        for user_id, reminder_time, timezone_offset in users:
            if timezone_offset is None:
                time_now = datetime.now().strftime('%H:%M')
                if time_now == reminder_time:
                    send_reminder(user_id)
            else:
                # Создаем время пользователя с учетом таймзоны
                user_timezone = timezone(timedelta(hours=timezone_offset))
                user_current_time = utc_time.astimezone(user_timezone).strftime('%H:%M')
                
                # Если текущее время по таймзоне пользователя совпадает с временем напоминания
                if user_current_time == reminder_time:
                    send_reminder(user_id)
    except Exception as e:
        logger.exception("Ошибка при проверке и отправке напоминаний: %s", str(e))
    finally:
        cursor.close()
        conn.close()

def reminder_checker():
    """Поток для проверки напоминаний"""
    while True:
        check_and_send_reminders()
        time.sleep(40)  # Проверяем каждую минуту

if __name__ == '__main__':
    # Инициализируем базу данных
    init_db()
    
    # Инициализируем первого администратора
    init_first_admin(ADMIN_ID)
    
    reminder_thread = threading.Thread(target=reminder_checker)
    reminder_thread.daemon = True
    reminder_thread.start()

    print("Бот запущен...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.exception("Ошибка при запуске бота %s", str(e))

        # Перезапускаем бота при ошибке
        bot.stop_polling()
        bot.polling(none_stop=True)