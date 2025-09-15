from telebot import types
from bot_instance import *
from utils.bot_db import get_reminder_settings, get_default_account_id, get_oldest_transaction_by_user
from datetime import datetime
from configs.tools import get_month_name


def main_menu_markup():
    """Клавиатура основного меню"""
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("💸 Мои счета", callback_data="accounts")
    # btn2 = types.InlineKeyboardButton("📊 Получить таблицу", callback_data="get_table")
    btn2 = types.InlineKeyboardButton("🏦 Баланс", callback_data="balance")
    btn3 = types.InlineKeyboardButton("📋 Категории", callback_data="categories")
    btn4 = types.InlineKeyboardButton("💰 Статистика", callback_data="statistics")
    btn5 = types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
    btn6 = types.InlineKeyboardButton("❓ Помощь", callback_data="help")
    # btn7 = types.InlineKeyboardButton("✍️ Обратная связь", callback_data="feedback")
    markup.add(btn1)
    markup.add(btn2)
    markup.add(btn3)
    markup.add(btn5)
    markup.add(btn4)
    markup.add(btn6)
    # markup.add(btn7)


    return markup

def accounts_markup():
    markup = types.InlineKeyboardMarkup()
    # btn1 = types.InlineKeyboardButton("🏦 Добавить счет", callback_data="add_account")
    btn2 = types.InlineKeyboardButton("📜 Список счетов", callback_data="accounts_list")
    # btn3 = types.InlineKeyboardButton("🖋 Изменить счет", callback_data="change_account")
    # btn4 = types.InlineKeyboardButton("🗑 Удалить счет", callback_data="delete_accounts_list")
    btn5 = types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    
    # markup.add(btn1)
    markup.add(btn2)
    # markup.add(btn3)
    # markup.add(btn4)
    markup.add(btn5)

    return markup

def settings_markup():
    markup = types.InlineKeyboardMarkup()
    # btn1 = types.InlineKeyboardButton("📅 Указать дату отсчета месяца", callback_data="settings_start_day_of_month")
    btn2 = types.InlineKeyboardButton("🔔 Напоминания", callback_data="reminders")
    btn3 = types.InlineKeyboardButton("🌍 Часовой пояс", callback_data="set_timezone")
    # btn4 = types.InlineKeyboardButton("💳 Основной счет", callback_data="set_default_account")
    btn5 = types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")

    # markup.add(btn1)
    markup.add(btn2)
    markup.add(btn3)
    # markup.add(btn4)
    markup.add(btn5)
    return markup

def month_start_markup():
    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = []
    for day in range(1, 32):
        buttons.append(types.InlineKeyboardButton(
            str(day),
            callback_data=f"month_start_{day}"
        ))
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton(
        "🔙 Назад",
        callback_data="back_to_main"
    ))
    return markup

def reminders_markup(user_id):
    """Клавиатура настроек напоминаний"""
    settings = get_reminder_settings(user_id)
    markup = types.InlineKeyboardMarkup()
    
    # Кнопки включения/выключения
    enabled_btn = types.InlineKeyboardButton(
        "✅ Включено" if settings['enabled'] else "Включить",
        callback_data="reminder_on"
    )
    disabled_btn = types.InlineKeyboardButton(
        "✅ Выключено" if not settings['enabled'] else "Выключить",
        callback_data="reminder_off"
    )
    
    # Кнопка установки времени
    time_btn = types.InlineKeyboardButton(
        f"⏰ Время: {settings['time']}",
        callback_data="set_reminder_time"
    )
    
    # Кнопка возврата
    back_btn = types.InlineKeyboardButton(
        "🔙 Назад",
        callback_data="settings"
    )
    
    markup.add(enabled_btn, disabled_btn)
    markup.add(time_btn)
    markup.add(back_btn)
    return markup

def balance_markup(user_id, year, month):
    """Клавиатура для просмотра баланса"""
    markup = types.InlineKeyboardMarkup()
    
    # Получаем текущую дату
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    # Получаем саммю раннюю транзакцию пользователя
    oldest_transaction = get_oldest_transaction_by_user(user_id)
    # Проверяем, есть ли у пользователя транзакции
    if oldest_transaction:
        # oldest_transaction_date = oldest_transaction.split(" ")[0]
        if isinstance(oldest_transaction, str):
            oldest_transaction_date = datetime.strptime(oldest_transaction, "%Y-%m-%d").date()
        else:
            # Если это уже объект datetime, просто получаем date
            oldest_transaction_date = oldest_transaction.date()

        oldest_year = oldest_transaction_date.year
        oldest_month = oldest_transaction_date.month
    else:
        # Если транзакций нет, используем текущую дату
        oldest_year = current_year
        oldest_month = current_month


    buttons = []

    if not(current_year == oldest_year and current_month == oldest_month):
        # Добавляем кнопки навигации по месяцам
        if not(oldest_month == month and year == oldest_year):
            if month == 1:
                buttons.append(types.InlineKeyboardButton(
                    f"⬅️ {get_month_name(12)}",
                    callback_data=f"balance_{year}_{month-1}"
                ))
            elif month > 1:
                buttons.append(types.InlineKeyboardButton(
                    f"⬅️ {get_month_name(month-1)}",
                    callback_data=f"balance_{year}_{month-1}"
                ))
        
    if month == 12:
        next_month = 1
    else:
        next_month = month + 1

    if not (year == current_year and month == current_month):
        buttons.append(types.InlineKeyboardButton(
            f"{get_month_name(next_month)}➡️",
            callback_data=f"balance_{year}_{month+1}"
        ))
    

    if buttons:
        markup.add(*buttons)
    
    markup.add(types.InlineKeyboardButton(
        "🔙 Назад в меню",
        callback_data="back_to_main"
    ))
    
    return markup

def account_markup(user_id, account_id):
    markup = types.InlineKeyboardMarkup()
    
    is_default = get_default_account_id(user_id) == account_id

    prefix = "🏦" if is_default else "✅"
    text = "Счет уже основной" if is_default else "Сделать основным"

    call_with_id = f"select_default_{account_id}"
    markup.add(types.InlineKeyboardButton(
        f"{prefix} {text}",
        callback_data=f"{'none' if is_default else call_with_id}"
    ))

    markup.add(types.InlineKeyboardButton(
        "✏️ Изменить сумму",
        callback_data=f"edit_account_amount_{account_id}"
    ))
    markup.add(types.InlineKeyboardButton(
        "📇 Изменить название",
        callback_data=f"edit_account_name_{account_id}"
    ))
    markup.add(types.InlineKeyboardButton(
        "❌ Удалить счет",
        callback_data=f"confirm_delete_{account_id}"
    ))
    markup.add(types.InlineKeyboardButton(
        "🔙 К списку счетов",
        callback_data="accounts_list"
    ))
    
    return markup


def statistics_markup():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🗓 Транзакции за сегодня", callback_data = "expenses_by_this_day")
    btn2 = types.InlineKeyboardButton("📆 Транзакции за неделю", callback_data = "expenses_by_this_week")
    btn3 = types.InlineKeyboardButton("📊 Подробная статистика", callback_data = "detailed_statistics")
    btn4 = types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")

    markup.add(btn1)
    markup.add(btn2)
    markup.add(btn3)
    markup.add(btn4)
    return markup

def help_markup():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📝 Как добавить транзакцию", callback_data="help_add_expense")
    btn2 = types.InlineKeyboardButton("📊 Как получить отчёт", callback_data="help_get_report")
    btn3 = types.InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")
    markup.add(btn1)
    markup.add(btn2)
    markup.add(btn3)
    return markup

def category_menu_markup(is_expense_type):
    markup = types.InlineKeyboardMarkup()
    expense_or_income_type = "expense" if is_expense_type else "income"

    markup.add(types.InlineKeyboardButton("➕ Добавить категорию", callback_data=f"add_category_{expense_or_income_type}"))
    markup.add(types.InlineKeyboardButton("✏️ Изменить категорию", callback_data=f"edit_category_{expense_or_income_type}"))
    markup.add(types.InlineKeyboardButton("❌ Удалить категорию", callback_data=f"delete_category_{expense_or_income_type}"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="categories"))

    return markup
    

def back_markup(cb_data):
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("🔙 Назад", callback_data=cb_data)
    markup.add(btn_back)
    return markup

def cancel_markup(cb_data):
    markup = types.InlineKeyboardMarkup()
    btn_cancel = types.InlineKeyboardButton("✖️ Отмена", callback_data=cb_data)
    markup.add(btn_cancel)

    return markup

def yes_no_markup(cb_data):
    '''Создает клавиатуру с двумя inline кнопками "Да" и "Нет"
    Callback которых добавлен как cb_data+"_yes" для кнопки Да
    И cb_data+"_no" для кнопки Нет
    '''
    markup = types.InlineKeyboardMarkup()
    btn_yes = types.InlineKeyboardButton("✅ Да", callback_data=cb_data+"_yes")
    btn_no = types.InlineKeyboardButton("❌ Нет", callback_data=cb_data+"_no")

    markup.add(btn_yes, btn_no)
    return markup
