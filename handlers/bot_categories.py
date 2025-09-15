from bot_instance import bot
from telebot import types
from bot_logging import *
from markups import *
from utils.bot_db import *

# Словарь для хранения состояний пользователей
user_states = {}
text_error = "❌ Произошла ошибка"

# пока меню выбора расходов или доходов
def unified_show_categories_menu(user_id, message_id, source_type):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Доходы", callback_data="categories_income"))
        markup.add(types.InlineKeyboardButton("➖ Расходы", callback_data="categories_expense"))
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
        
        user_states.pop(user_id, None)
        text = "📋 Управление категориями\n\nВыберите категории доходов или расходов:"
        

        if source_type == "call":
            bot.edit_message_text(chat_id = user_id,
                            message_id = message_id, 
                            text=text, 
                            reply_markup=markup
                            )
        elif source_type == "command":
            bot.send_message(user_id, text, reply_markup=markup)
    except Exception as e:
        logger.error("Error %s", e)

        if source_type == "call":
            bot.edit_message_text(chat_id = user_id,
                            message_id = message_id, 
                            text=text_error, 
                            reply_markup=markup
                            )
        elif source_type == "command":
            bot.send_message(user_id, text_error, reply_markup=markup)

@bot.message_handler(commands=["categories"])
def handle_show_categories_menu(message):
    user_id = message.from_user.id
    message_id = message.message_id
    unified_show_categories_menu(user_id, message_id, source_type = "command")

@bot.callback_query_handler(func=lambda call: call.data == "categories")
def show_categories_menu(call):
    user_id = call.from_user.id
    message_id = call.message.message_id

    unified_show_categories_menu(user_id, message_id, source_type = "call")
    bot.answer_callback_query(call.id)

# показ категорий: расходов или доходов
def unified_show_categories_expense_and_income(user_id, message_id, source_type):
    """Показ категорий расходов"""
    try:
        categories = get_categories(user_id)
        is_call = source_type.split("_")[0] == "call"
        is_expense_type = source_type.split("_")[1] == "expense"

        user_states.pop(user_id, None)
        
        if is_expense_type:
            message = "📋 Категории расходов\n\n"
        else:
            message = "📋 Категории доходов \n\n" 

        if categories:
            message += "Ваши категории:\n"
            for category_id, name, is_default, is_expense in categories:
                if is_expense_type:
                    if is_expense:
                        message += f"🟢 {name}\n"
                else:
                    if not is_expense:
                        message += f"🟢 {name}\n"
        else:
            message += "У вас пока нет категорий"
        
        if is_call:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=message,
                reply_markup=category_menu_markup(is_expense_type)
            )
        else:
            bot.send_message(user_id, message, reply_markup=category_menu_markup(is_expense_type))
    except Exception as e:
        logger.exception("Ошибка %s при показе меню категорий", e)

        if is_call:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text="❌ Произошла ошибка при получении категорий",
                reply_markup=back_markup("back_to_main")
            )
        else:
            bot.send_message(user_id, "❌ Произошла ошибка при получении категорий", reply_markup=back_markup("back_to_main"))

@bot.message_handler(commands=["categories_expense"])
def handle_show_categories_expense(message):
    user_id = message.from_user.id
    message_id = message.message_id
    unified_show_categories_expense_and_income(user_id, message_id, source_type = "command_expense")

@bot.callback_query_handler(func = lambda call: call.data == "categories_expense")
def show_categories_expense(call):
    user_id = call.from_user.id
    message_id = call.message.message_id
    unified_show_categories_expense_and_income(user_id, message_id, source_type="call_expense")
    bot.answer_callback_query(call.id)
    
@bot.message_handler(commands=["categories_income"])
def handle_show_categories_income(message):
    user_id = message.from_user.id
    message_id = message.message_id
    unified_show_categories_expense_and_income(user_id, message_id, source_type = "command_income")

@bot.callback_query_handler(func = lambda call: call.data == "categories_income")
def show_categories_income(call):
    user_id = call.from_user.id
    message_id = call.message.message_id
    unified_show_categories_expense_and_income(user_id, message_id, source_type="call_income")
    bot.answer_callback_query(call.id)
    

# обработка нажатия кнопкни добавить категорию
@bot.callback_query_handler(func=lambda call: call.data.startswith("add_category_"))
def start_add_category(call):
    """Начало процесса добавления категории"""
    is_expense_type = call.data.split("_")[2] == "expense"
    expense_or_income_type = 'expense' if is_expense_type else 'income'

    try:
        user_id = call.from_user.id
        user_states[user_id] = {"state": f"waiting_for_category_name_{expense_or_income_type}"}
    
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Введите название новой категории:",
            reply_markup=cancel_markup(f"categories_{expense_or_income_type}")
        )
    except Exception as e:
        logger.exception("Ошибка %s при начале добавления категории", e)
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка",
            reply_markup=back_markup(f"categories_{expense_or_income_type}")
        )

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state", "").startswith("waiting_for_category_name"))
def handle_new_category_name(message):
    """Обработка ввода названия новой категории"""    
    try:
        message_id = message.message_id
        user_id = message.chat.id
        is_expense_type = user_states[user_id]["state"].split("_")[-1] == "expense"
        expense_or_income_type = 'expense' if is_expense_type else 'income'
        category_name = message.text.strip().lower()
        
        if add_category(user_id, category_name, is_expense_type):
            bot.send_message(
                chat_id=user_id,
                text=f"✅ Категория <b>{category_name}</b> успешно добавлена",
                parse_mode="HTML"
            )
            unified_show_categories_expense_and_income(user_id, message_id, source_type=f"command_{expense_or_income_type}")
        else:
            bot.send_message(
                chat_id=user_id,
                text="❌ Такая категория уже существует",
            )
            unified_show_categories_expense_and_income(user_id, message_id, source_type=f"command_{expense_or_income_type}")
        
        user_states.pop(user_id, None)
    except Exception as e:
        logger.exception("Ошибка %s при добавлении категории", e)
        bot.send_message(
            chat_id=user_id,
            text="❌ Произошла ошибка при добавлении категории",
            reply_markup=back_markup(f"categories_{'expense' if is_expense_type else 'income'}")
        )
        user_states.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_category_"))
def start_edit_category(call):
    """Начало процесса изменения категории"""
    try:
        user_id = call.from_user.id
        is_expense_type = call.data.split("_")[-1] == "expense"
        expense_or_income_type = "expense" if is_expense_type else "income"
        categories = get_categories(user_id)

        user_states.pop(user_id, None)
        
        if not categories:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="У вас нет категорий для изменения",
                reply_markup=back_markup(f"categories_{expense_or_income_type}")
            )
            return
        
        markup = types.InlineKeyboardMarkup()
        for category_id, name, is_default, is_expense in categories:
            if is_expense_type:
                if is_expense:
                    markup.add(types.InlineKeyboardButton(
                        f"✏️ {name}",
                        callback_data=f"edit_id_category_expense_{category_id}"
                    ))
            else:
                if not is_expense:
                    markup.add(types.InlineKeyboardButton(
                        f"✏️ {name}",
                        callback_data=f"edit_id_category_income_{category_id}"
                    ))
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data=f"categories_{expense_or_income_type}"))
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выберите категорию для изменения:",
            reply_markup=markup
        )
    except Exception as e:
        logger.exception("Ошибка %s при начале изменения категории", e)
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка",
            reply_markup=back_markup(f"categories_{expense_or_income_type}")
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_id_category_"))
def handle_edit_category_selection(call):
    """Обработка выбора категории для изменения"""
    try:
        
        user_id = call.from_user.id
        is_expense_type = call.data.split("_")[-2] == "expense"
        expense_or_income_type = "expense" if is_expense_type else "income"
        category_id = int(call.data.split("_")[-1])
    
        user_states[user_id] = {
            "state": f"waiting_for_new_category_name_{expense_or_income_type}",
            "category_id": category_id
        }
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Введите новое название категории:",
            reply_markup=cancel_markup(f"edit_category_{expense_or_income_type}")
        )
    except Exception as e:
        logger.exception("Ошибка %s при выборе категории для изменения", e)
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка",
            reply_markup=back_markup(f"categories_{expense_or_income_type}")
        )

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state", "").startswith("waiting_for_new_category_name"))
def handle_new_category_name_edit(message):
    """Обработка ввода нового названия категории"""
    try:
        user_id = message.chat.id
        message_id = message.message_id
        state = user_states[user_id]
        category_id = state["category_id"]
        new_name = message.text.strip().lower()

        is_expense_type = user_states[user_id]["state"].split("_")[-1] == "expense"
        expense_or_income_type = "expense" if is_expense_type else "income"
        
        if update_category(user_id, category_id, new_name):
            bot.send_message(
                chat_id=user_id,
                text=f"✅ Название категории успешно изменено на <b>{new_name}</b>",
                parse_mode="HTML"
            )
            unified_show_categories_expense_and_income(user_id, message_id, source_type=f"command_{expense_or_income_type}")
        else:
            bot.send_message(
                chat_id=user_id,
                text="❌ Такая категория уже существует"
            )
            unified_show_categories_expense_and_income(user_id, message_id, source_type=f"command_{expense_or_income_type}")
        
        user_states.pop(user_id, None)
    except Exception as e:
        logger.exception("Ошибка %s при изменении названия категории", e)
        bot.send_message(
            chat_id=user_id,
            text="❌ Произошла ошибка при изменении категории",
            reply_markup=back_markup(f"categories_{expense_or_income_type}")
        )
        user_states.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_category_"))
def start_delete_category(call):
    """Начало процесса удаления категории"""
    try:
        is_expense_type = call.data.split("_")[-1] == "expense"
        expense_or_income_type = "expense" if is_expense_type else "income"
        user_id = call.from_user.id
        categories = get_categories(user_id)
        
        if not categories:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="У вас нет категорий для удаления",
                reply_markup=back_markup(f"categories_{expense_or_income_type}")
            )
            return
        
        markup = types.InlineKeyboardMarkup()
        for category_id, name, is_default, is_expense in categories:
            if is_expense_type:
                if is_expense:
                    markup.add(types.InlineKeyboardButton(
                        f"❌ {name}",
                        callback_data=f"delete_id_category_{expense_or_income_type}_{category_id}"
                    ))
            else:
                if not is_expense:
                    markup.add(types.InlineKeyboardButton(
                        f"❌ {name}",
                        callback_data=f"delete_id_category_{expense_or_income_type}_{category_id}"
                    ))
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data=f"categories_{expense_or_income_type}"))
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выберите категорию для удаления:",
            reply_markup=markup
        )
    except Exception as e:
        logger.exception("Ошибка %s при начале удаления категории", e)
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка",
            reply_markup=back_markup(f"categories_{expense_or_income_type}")
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_id_category_"))
def handle_delete_category(call):
    """Обработка удаления категории"""
    try:
        user_id = call.from_user.id
        message_id = call.message.message_id
        category_id = int(call.data.split("_")[-1])
        is_expense_type = call.data.split("_")[-2] == "expense"
        expense_or_income_type = "expense" if is_expense_type else "income"
        category_name = get_category_name(category_id).lower()
        
        if delete_category(user_id, category_id):
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"✅ Категория <b>{category_name}</b> успешно удалена",
                parse_mode="HTML"
            )
            unified_show_categories_expense_and_income(user_id, message_id, source_type=f"command_{expense_or_income_type}")
        else:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ Нельзя удалить базовую категорию",
                reply_markup=back_markup(f"categories_{expense_or_income_type}")
            )
    except Exception as e:
        logger.exception("Ошибка %s при удалении категории", e)
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка при удалении категории",
            reply_markup=back_markup(f"categories_{expense_or_income_type}")
        ) 