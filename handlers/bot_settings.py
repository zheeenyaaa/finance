from bot_instance import bot
from telebot import types
from bot_logging import *
from utils.bot_db import *
from markups import *
import re
from datetime import datetime
 
settings_introduce_text = "⚙️Настройки:"
reminders_introduce_text = ("🔔 Настройки напоминаний\n\n"
                 "Бот будет напоминать вам о необходимости внести траты за день.\n"
                 "Выберите, хотите ли вы получать напоминания и в какое время:")

user_states = {}

@bot.callback_query_handler(func = lambda call:call.data == "settings")
def settings_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    user_states.pop(chat_id, None)

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=settings_introduce_text,
        reply_markup=settings_markup()
    )

@bot.message_handler(commands=['settings'])
def handle_settings(message):
    user_id = message.from_user.id
    bot.send_message(user_id, settings_introduce_text, reply_markup=settings_markup())


@bot.callback_query_handler(func=lambda call: call.data == "reminders")
def show_reminders_settings(call):
    """Показ настроек напоминаний"""
    user_states.pop(call.from_user.id, None)

    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=reminders_introduce_text,
            reply_markup=reminders_markup(call.from_user.id)
        )
    except Exception as e:
        logger.exception("Ошибка при показе настроек напоминаний")

@bot.callback_query_handler(func=lambda call: call.data in ["reminder_on", "reminder_off"])
def toggle_reminders(call):
    """Включение/выключение напоминаний"""
    try:
        user_id = call.from_user.id
        enabled = call.data == "reminder_on"
        
        # Если включаем напоминания, проверим наличие таймзоны
        if enabled and not has_timezone(user_id):
            # Таймзона не установлена, запрашиваем у пользователя
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, "⚠️ Для корректной работы напоминаний необходимо установить ваш часовой пояс.\n"
                                     "Пожалуйста, нажмите на кнопку ниже для настройки:",
                                     reply_markup=types.InlineKeyboardMarkup().add(
                                        types.InlineKeyboardButton("🌍 Установить часовой пояс", callback_data="set_timezone")
                                     ))
            return
        
        if set_reminders_enabled(user_id, enabled):
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=reminders_introduce_text,
                reply_markup=reminders_markup(user_id)
            )
    except Exception as e:
        logger.exception("Ошибка при изменении статуса напоминаний")

@bot.callback_query_handler(func=lambda call: call.data == "set_reminder_time")
def show_time_input(call):
    """Запрос ввода времени у пользователя"""
    try:
        user_id = call.from_user.id
        
        # Проверяем, установлен ли часовой пояс
        if not has_timezone(user_id):
            # Если нет, просим установить сначала часовой пояс
            bot.edit_message_text(chat_id = user_id, message_id = call.message.message_id, text = "⚠️ Для корректной работы напоминаний необходимо установить ваш часовой пояс.\n"
                                     "Пожалуйста, нажмите на кнопку ниже для настройки:",
                                     reply_markup=types.InlineKeyboardMarkup().add(
                                        types.InlineKeyboardButton("🌍 Установить часовой пояс", callback_data="set_timezone")
                                     ))
            bot.answer_callback_query(call.id)
            return
            
        # Устанавливаем состояние ожидания ввода времени
        user_states[user_id] = {
            "state": "waiting_for_reminder_time",
            "message_id": call.message.message_id
        }
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="⏰ Введите время для напоминаний в формате ЧЧ:ММ\n"
                 "Например: 21:00\n\n"
                 "🔙 Для отмены нажмите кнопку 'Назад'",
            reply_markup=back_markup("reminders")
        )
    except Exception as e:
        logger.exception("Ошибка при запросе ввода времени")


# Добавляем обработчик ввода времени
@bot.message_handler(func=lambda message: 
    user_states.get(message.chat.id, {}).get("state") == "waiting_for_reminder_time")
def handle_time_input(message):
    """Обработка введенного времени"""
    try:
        # Проверяем формат времени
        try:
            time_str = message.text.strip()
            # Проверяем формат ЧЧ:ММ
            if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_str):
                raise ValueError("Неверный формат времени")
            
            # Устанавливаем время напоминания
            if set_reminder_time(message.from_user.id, time_str):
                # Очищаем состояние
                user_states.pop(message.chat.id, None)
                
                # Отправляем сообщение об успешной установке
                bot.send_message(
                    message.chat.id,
                    f"✅ Время напоминания установлено: {time_str}"
                )
                bot.send_message(message.chat.id, reminders_introduce_text, reply_markup=reminders_markup(message.from_user.id)) 
            else:
                bot.send_message(
                    message.chat.id,
                    "❌ Произошла ошибка при установке времени",
                    reply_markup=reminders_markup(message.from_user.id)
                )
        except ValueError:
            bot.send_message(
                message.chat.id,
                "❌ Неверный формат времени. Используйте формат ЧЧ:ММ\n"
                "Например: 21:00"
            )
            return
    except Exception as e:
        logger.exception("Ошибка при обработке ввода времени")
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при установке времени",
            reply_markup=reminders_markup(message.from_user.id)
        )
        user_states.pop(message.chat.id, None)


@bot.callback_query_handler(func=lambda call: call.data == "set_timezone")
def show_timezone_input(call):
    """Запрос текущего времени у пользователя"""
    try:
        # Устанавливаем состояние ожидания ввода времени
        user_states[call.from_user.id] = {
            "state": "waiting_for_current_time",
            "message_id": call.message.message_id
        }
        
        # Получаем текущее UTC время
        utc_time_str = datetime.now().strftime('%H:%M')
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⏰ Настройка часового пояса\n\n"
                 f"Сейчас UTC+3 время: {utc_time_str}\n\n"
                 f"Пожалуйста, введите ваше текущее время в формате ЧЧ:ММ\n"
                 f"Например: 21:00\n\n",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 Назад", callback_data="settings")
            )
        )
    except Exception as e:
        logger.exception("Ошибка %e при запросе текущего времени", e)

@bot.message_handler(func=lambda message: 
    user_states.get(message.chat.id, {}).get("state") == "waiting_for_current_time")
def handle_current_time_input(message):
    """Обработка введенного текущего времени"""
    try:
        # Проверяем формат времени
        try:
            user_time_str = message.text.strip()
            # Проверяем формат ЧЧ:ММ
            if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', user_time_str):
                raise ValueError("Неверный формат времени")
            
            # Получаем текущее UTC время
            utc_time_str = datetime.now().strftime('%H:%M')
            
            # Вычисляем разницу в часах
            user_time = datetime.strptime(user_time_str, '%H:%M')
            utc_time = datetime.strptime(utc_time_str, '%H:%M')
            
            # Вычисляем разницу в часах
            time_diff = (user_time - utc_time).total_seconds() / 3600
            
            # Округляем до ближайшего целого часа
            timezone_offset = round(time_diff) + 3
            
            # Проверяем, что смещение в разумных пределах (-12 до +14)
            if not -12 <= timezone_offset <= 14:
                raise ValueError("Неправильное смещение часового пояса")
            
            # Устанавливаем часовой пояс
            if set_timezone_offset(message.from_user.id, timezone_offset):
                # Очищаем состояние
                user_states.pop(message.chat.id, None)
                
                # Отправляем сообщение об успешной установке
                bot.send_message(message.chat.id, f"✅ Часовой пояс установлен: UTC{'+' if timezone_offset >= 0 else ''}{timezone_offset}")
               
            else:
                bot.send_message(
                    message.chat.id, "❌ Произошла ошибка при установке часового пояса")
     
            bot.send_message(message.chat.id, settings_introduce_text, reply_markup=settings_markup())
        except ValueError as e:
            bot.send_message(
                message.chat.id,
                "❌ Неверный формат времени. Используйте формат ЧЧ:ММ\n"
                "Например: 21:00"
            )
            return
    except Exception as e:
        logger.exception("Ошибка при обработке ввода времени")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при установке часового пояса")
        bot.send_message(message.chat.id, settings_introduce_text, reply_markup=settings_markup())
        user_states.pop(message.chat.id, None)


# @bot.callback_query_handler(func=lambda call: call.data == "set_default_account")
# def show_default_account_selection(call):
#     """Показ списка счетов для выбора основного"""
#     try:
#         accounts = get_accounts(call.from_user.id)
#         if not accounts:
#             bot.answer_callback_query(call.id)
#             bot.edit_message_text(
#                 chat_id=call.message.chat.id,
#                 message_id=call.message.message_id,
#                 text="❌ У вас нет добавленных счетов",
#                 reply_markup=settings_markup()
#             )
#             bot.send_message(call.from_user.id, settings_introduce_text, reply_markup="settings")
#             return
        
#         # Получаем текущий основной счет
#         current_default = get_default_account_id(call.from_user.id)
        
#         # Создаем клавиатуру со списком счетов
#         markup = types.InlineKeyboardMarkup()
#         for account in accounts:
#             account_id, name, amount = account
#             # Добавляем галочку к текущему основному счету
#             prefix = "✅ " if account_id == current_default else ""
#             markup.add(types.InlineKeyboardButton(
#                 f"{prefix}{name} - {amount} руб.",
#                 callback_data=f"select_default_{account_id}"
#             ))
        
#         markup.add(types.InlineKeyboardButton(
#             "🔙 Назад",
#             callback_data="settings"
#         ))
        
#         bot.answer_callback_query(call.id)
#         bot.edit_message_text(
#             chat_id=call.message.chat.id,
#             message_id=call.message.message_id,
#             text="💳 Выберите основной счет:\n\n"
#                  "С этого счета будут списываться деньги по умолчанию при добавлении трат.",
#             reply_markup=markup
#         )
#     except Exception as e:
#         logger.exception("Ошибка при показе списка счетов")

# @bot.callback_query_handler(func=lambda call: call.data.startswith("select_default_"))
# def handle_default_account_selection(call):
#     """Обработка выбора основного счета"""
#     try:
#         account_id = int(call.data.split("_")[2])
#         user_id = call.from_user.id
        
#         if set_default_account(user_id, account_id):
#             # Получаем информацию о выбранном счете
#             account_info = get_account_info(account_id)
#             if account_info:
#                 name, amount, _ = account_info
#                 bot.answer_callback_query(call.id)
#                 bot.edit_message_text(
#                     chat_id=call.message.chat.id,
#                     message_id=call.message.message_id,
#                     text=f"✅ Основной счет установлен:\n{name} - {amount} руб."
#                 )

         
#                 bot.send_message(user_id, settings_introduce_text, reply_markup=settings_markup())
              
#         else:
#             bot.answer_callback_query(call.id)
#             bot.edit_message_text(
#                 chat_id=call.message.chat.id,
#                 message_id=call.message.message_id,
#                 text="❌ Произошла ошибка при установке основного счета",
#                 reply_markup=settings_markup()
#             )
#     except Exception as e:
#         logger.exception("Ошибка %e при выборе основного счета", e)