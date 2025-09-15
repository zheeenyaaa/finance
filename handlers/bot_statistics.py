from bot_instance import bot
from telebot import types
from bot_logging import *
from markups import *
from utils.bot_db import *
from datetime import datetime, timedelta

@bot.callback_query_handler(func=lambda call: call.data == "statistics")
def check_outcomes(call):

    id_chat = call.message.chat.id
    message_id = call.message.message_id
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
            chat_id=id_chat,
            message_id=message_id,
            text="📊Подробнее посмотреть расходы",
            reply_markup=statistics_markup()
        )
@bot.message_handler(commands=['statistics'])
def handle_statistics(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "📊Подробнее посмотреть расходы", reply_markup=statistics_markup())


# показ детальной статистики
@bot.callback_query_handler(func=lambda call: call.data == "detailed_statistics")
def show_detailed_statistics(call):
    """Показ детальной статистики"""
    try:
        user_id = call.from_user.id
        stats = get_detailed_statistics(user_id)
        
        if not stats or (not stats['income'] and not stats['expense']):
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="У вас пока нет транзакций.",
                reply_markup=statistics_markup()
            )
            return
        
        # Формируем сообщение со статистикой
        message = "📊 Детальная статистика:\n\n"
        
        total_income = 0
        total_expenses = 0
        
        # Показываем доходы
        if stats['income']:
            message += "📈 Доходы:\n"
            for category, data in stats['income'].items():
                total_income += data['total']
                message += f"\n{category}: +{data['total']} руб. ({data['count']} транзакций)\n"
                message += "Последние транзакции:\n"
                for trans in data['transactions'][:5]:  # Показываем последние 5 транзакций
                    dt_utc = trans["date"]
                    if has_timezone(user_id):
                        dt_local = dt_utc + timedelta(hours=get_timezone_offset(user_id))
                    else:
                        dt_local = dt_utc + timedelta(hours=3)

                    date = dt_local.strftime('%d.%m.%Y %H:%M')
                    message += f"• {date}: +{trans['amount']} руб."
                    if trans['comment']:
                        message += f" ({trans['comment']})"
                    message += "\n"
            message += "\n"
        
        # Затем показываем расходы по категориям
        if stats['expense']:
            message += "📉 Расходы по категориям:\n"
            for category, data in stats['expense'].items():
                total_expenses += data['total']
                message += f"\n{category}: -{data['total']} руб. ({data['count']} транзакций)\n"
                message += "Последние транзакции:\n"
                for trans in data['transactions'][:5]:  # Показываем последние 5 транзакций
                    dt_utc = trans["date"]
                    if has_timezone(user_id):
                        dt_local = dt_utc + timedelta(hours=get_timezone_offset(user_id))
                    else:
                        dt_local = dt_utc + timedelta(hours=3)
                    date = dt_local.strftime('%d.%m.%Y %H:%M')
                    
                    message += f"• {date}: -{trans['amount']} руб."
                    if trans['comment']:
                        message += f" ({trans['comment']})"
                    message += "\n"
        
        # Добавляем итоги
        message += "\n💰 Итого:\n"
        message += f"📈 Общий доход: +{total_income} руб.\n"
        message += f"📉 Общий расход: -{total_expenses} руб.\n"
        message += f"💵 Баланс: {total_income - total_expenses:+} руб."
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message,
            reply_markup=statistics_markup()
        )
    except Exception as e:
        logger.exception("Ошибка %s при показе детальной статистики", e)
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка при получении статистики",
            reply_markup=statistics_markup()
        )

# функция для обработки команды показа статистики за сегодня
def unified_handle_show_today_statistics(chat_id, message_id, source_type):
    """Показ статистики за сегодня"""
    try:
        stats = get_period_statistics(chat_id, 'day')
        
        if not stats or (not stats['income'] and not stats['expense']):
            if source_type == "call":
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="За сегодня транзакций нет.",
                    reply_markup=statistics_markup()
                )
                
            else:
                bot.send_message(chat_id, "За сегодня транзакций нет.", reply_markup=statistics_markup())
            return
        
        # Формируем сообщение со статистикой
        message = "📊 Статистика за сегодня:\n\n"
        
        total_income = 0
        total_expenses = 0
        
        # Сначала показываем доходы
        if stats['income']:
            message += "📈 Доходы:\n"
            for category, data in stats['income'].items():
                total_income += data['total']
                message += f"\n{category}: +{data['total']} руб. ({data['count']} транзакций)\n"
                message += "Последние транзакции:\n"
                for trans in data['transactions']:
                    dt_utc = trans["date"]
                    if has_timezone(chat_id):
                        dt_local = dt_utc + timedelta(hours=get_timezone_offset(chat_id))
                    else:
                        dt_local = dt_utc + timedelta(hours=3)
                    date = dt_local.strftime('%H:%M')
                    message += f"• {date}: +{trans['amount']} руб."
                    if trans['comment']:
                        message += f" ({trans['comment']})"
                    message += "\n"
            message += "\n"
        
        # Затем показываем расходы по категориям
        if stats['expense']:
            message += "📉 Расходы по категориям:\n"
            for category, data in stats['expense'].items():
                total_expenses += data['total']
                message += f"\n{category}: -{data['total']} руб. ({data['count']} транзакций)\n"
                message += "Последние транзакции:\n"
                for trans in data['transactions']:
                    dt_utc = trans["date"]
                    if has_timezone(chat_id):
                        dt_local = dt_utc + timedelta(hours=get_timezone_offset(chat_id))
                    else:
                        dt_local = dt_utc + timedelta(hours=3)
                    date = dt_local.strftime('%H:%M')
                    message += f"• {date}: -{trans['amount']} руб."
                    if trans['comment']:
                        message += f" ({trans['comment']})"
                    message += "\n"
        
        # Добавляем итоги
        message += "\n💰 Итого за сегодня:\n"
        message += f"📈 Доходы: +{total_income} руб.\n"
        message += f"📉 Расходы: -{total_expenses} руб.\n"
        message += f"💵 Баланс: {total_income - total_expenses:+} руб."
        

        if source_type == "call":
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=message,
                reply_markup=statistics_markup()
            )
        else:
            bot.send_message(chat_id, message, reply_markup=statistics_markup())
    except Exception as e:
        logger.exception("Ошибка %s при показе статистики за сегодня", str(e))
        
        if source_type == "call":
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="❌ Произошла ошибка при получении статистики",
                reply_markup=statistics_markup()
            )
        else:
            bot.send_message(chat_id, "❌ Произошла ошибка при получении статистики", reply_markup=statistics_markup())


@bot.message_handler(commands=["expenses_by_this_day"])
def handle_show_today_statistics(message):
    chat_id = message.from_user.id
    message_id = message.id
    unified_handle_show_today_statistics(chat_id, message_id, source_type="command")

@bot.callback_query_handler(func=lambda call: call.data == "expenses_by_this_day")
def show_today_statistics(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    unified_handle_show_today_statistics(chat_id, message_id, source_type="call")
    bot.answer_callback_query(call.id)
  


@bot.callback_query_handler(func=lambda call: call.data == "expenses_by_this_week")
def show_week_statistics(call):
    """Показ статистики за неделю"""
    try:
        user_id = call.from_user.id
        stats = get_period_statistics(user_id, 'week')
        
        if not stats or (not stats['income'] and not stats['expense']):
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="За последнюю неделю транзакций нет.",
                reply_markup=statistics_markup()
            )
            return
        
        # Формируем сообщение со статистикой
        message = "📊 Статистика за последнюю неделю:\n\n"
        
        total_income = 0
        total_expenses = 0
        
        # Сначала показываем доходы
        if stats['income']:
            message += "📈 Доходы:\n"
            for category, data in stats['income'].items():
                total_income += data['total']
                message += f"\n{category}: +{data['total']} руб. ({data['count']} транзакций)\n"
                message += "Последние транзакции:\n"
                for trans in data['transactions'][:5]:  # Показываем последние 5 транзакций
                    dt_utc = trans["date"]
                    if has_timezone(user_id):
                        dt_local = dt_utc + timedelta(hours=get_timezone_offset(user_id))
                    else:
                        dt_local = dt_utc + timedelta(hours=3)
                    date = dt_local.strftime('%d.%m %H:%M')
                    message += f"• {date}: +{trans['amount']} руб."
                    if trans['comment']:
                        message += f" ({trans['comment']})"
                    message += "\n"
            message += "\n"
        
        # Затем показываем расходы по категориям
        if stats['expense']:
            message += "📉 Расходы по категориям:\n"
            for category, data in stats['expense'].items():
                total_expenses += data['total']
                message += f"\n{category}: -{data['total']} руб. ({data['count']} транзакций)\n"
                message += "Последние транзакции:\n"
                for trans in data['transactions'][:5]:  # Показываем последние 5 транзакций
                    dt_utc = trans["date"]
                    if has_timezone(user_id):
                        dt_local = dt_utc + timedelta(hours=get_timezone_offset(user_id))
                    else:
                        dt_local = dt_utc + timedelta(hours=3)
                    date = dt_local.strftime('%d.%m %H:%M')
                    message += f"• {date}: -{trans['amount']} руб."
                    if trans['comment']:
                        message += f" ({trans['comment']})"
                    message += "\n"
        
        # Добавляем итоги
        message += "\n💰 Итого за неделю:\n"
        message += f"📈 Доходы: +{total_income} руб.\n"
        message += f"📉 Расходы: -{total_expenses} руб.\n"
        message += f"💵 Баланс: {total_income - total_expenses:+} руб."
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message,
            reply_markup=statistics_markup()
        )
    except Exception as e:
        logger.exception("Ошибка %s при показе статистики за неделю", str(e))
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка при получении статистики",
            reply_markup=statistics_markup()
        )