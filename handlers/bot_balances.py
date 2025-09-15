from bot_instance import bot
from bot_logging import *
from utils.bot_db import *
from markups import balance_markup


def unified_handler_get_balance(user_id, message_id, source_type):
    try:
        # Получаем текущую дату
        current_date = datetime.now()
        year = current_date.year
        month = current_date.month
        
        # Получаем баланс
        balance_data = get_month_balance(user_id, year, month)
        month_name = get_month_name(month).lower()

        text = (f"💰 Баланс за {month_name} {year}\n\n"
                    f"➕ Доходы: <i>+{balance_data['income']} руб.</i>\n"
                    f"➖ Расходы: <i>-{balance_data['expenses']} руб.</i>\n\n"
                    f"💵 Сальдо: <b>{balance_data['balance']:+} руб.</b>")
        
        if source_type == "callback":
            bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=text,
            reply_markup=balance_markup(user_id, year, month),
            parse_mode="HTML"
            )
        else:
            bot.send_message(
                user_id, 
                text,
                reply_markup=balance_markup(user_id, year, month),
                parse_mode="HTML"
            )
    except Exception as e:
        logger.exception("Ошибка %s при показе баланса", e)


@bot.message_handler(commands=["balance"])
def handle_view_balance(message):
    chat_id = message.from_user.id
    message_id = message.message_id
    unified_handler_get_balance(chat_id, message_id, source_type="command")


@bot.callback_query_handler(func=lambda call: call.data == "balance")
def show_balance(call):
    """Показ текущего баланса"""
    chat_id = call.from_user.id
    message_id = call.message.message_id
    unified_handler_get_balance(chat_id, message_id, source_type="callback")
    bot.answer_callback_query(call.id)
    

@bot.callback_query_handler(func=lambda call: call.data.startswith("balance_"))
def handle_balance_navigation(call):
    """Обработка навигации по месяцам"""
    try:
        user_id = call.from_user.id
        # Получаем год и месяц из callback_data
        _, year, month = call.data.split("_")
        year = int(year)
        month = int(month)
        
        # Корректируем год и месяц, если месяц вышел за пределы
        if month > 12:
            year += 1
            month = 1
        elif month < 1:
            year -= 1
            month = 12
        
        # Получаем баланс
        balance_data = get_month_balance(call.from_user.id, year, month)
        
        # Форматируем сообщение
        month_name = get_month_name(month)
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"💰 Баланс за {month_name} {year}\n\n"
                 f"➕ Доходы: +{balance_data['income']} руб.\n"
                 f"➖ Расходы: -{balance_data['expenses']} руб.\n"
                 f"💵 Сальдо: {balance_data['balance']:+} руб.",
            reply_markup=balance_markup(user_id, year, month)
        )
    except Exception as e:
        logger.exception("Ошибка %s при навигации по балансу", e)