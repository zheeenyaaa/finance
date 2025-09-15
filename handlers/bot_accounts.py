from bot_instance import bot

from telebot import types
from bot_logging import *
from markups import *
from utils.bot_db import *

# Словарь для хранения состояний пользователей
user_states = {}
# текст приветствия
accounts_introduce_text = "💸 Тут ты можешь контролировать свои счета:"

@bot.message_handler(commands=["accounts"])
def handle_accounts(message):
    user_id = message.from_user.id
    user_states.pop(user_id, None)
    bot.send_message(message.chat.id, accounts_introduce_text, reply_markup=accounts_markup())

@bot.callback_query_handler(func=lambda call: call.data=="accounts")
def settings_menu(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    user_states.pop(chat_id, None)
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=accounts_introduce_text,
            reply_markup=accounts_markup()
        )
    
# функция показа информации о всех аккаунтах
def unified_show_accounts_list(user_id, message_id, source_type):
    try:
        accounts = get_accounts(user_id)
        
        if not accounts:
            if source_type == "call":
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text="У вас пока нет добавленных счетов.",
                    reply_markup=back_markup("accounts")
                )
                return
            else:
                bot.send_message(user_id, "У вас пока нет добавленных счетов." , reply_markup=back_markup("accounts"))
        current_default = get_default_account_id(user_id)

        # Создаем inline клавиатуру со списком счетов
        markup = types.InlineKeyboardMarkup()
        for account in accounts:
            # Проверяем, что account[0] действительно является числом
            account_id = int(account[0])  # Преобразуем в число сразу при создании кнопки
            
            prefix = "✅ " if account_id == current_default else ""
            markup.add(types.InlineKeyboardButton(
                f"{prefix} {account[1]} — {account[2]} руб.",
                callback_data=f"account_info_{account_id}"  # Используем уже преобразованный ID
            ))

        btn_add = types.InlineKeyboardButton("🏦 Добавить счет", callback_data="add_account")
        btn_back = types.InlineKeyboardButton("🔙 Назад",callback_data="accounts")
        markup.add(btn_add, btn_back)

        
        if source_type == "call":
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text="📋 Ваши счета:\n\nВыберите счет для просмотра подробной информации:",
                reply_markup=markup
            )
        else:
            bot.send_message(user_id,"📋 Ваши счета:\n\nВыберите счет для просмотра подробной информации:" , reply_markup=markup)
    except Exception as e:
        logger.error("Ошибка при получении списка счетов: %s", str(e))

        if source_type == "call":
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text="❌ Произошла ошибка при получении списка счетов.",
                reply_markup=back_markup("accounts")
            )
        else:
            bot.send_message(user_id, "❌ Произошла ошибка при получении списка счетов.", reply_markup=back_markup("accounts"))


# обработчик показа списка аккаунтов
@bot.callback_query_handler(func=lambda call: call.data == "accounts_list")
def show_accounts(call):
    user_id = call.from_user.id
    message_id = call.message.message_id
    bot.answer_callback_query(call.id)
    unified_show_accounts_list(user_id, message_id, source_type="call")

@bot.message_handler(commands=["accounts_list"])
def handle_show_accounts(message):
    user_id = message.from_user.id
    message_id = message.message_id
    unified_show_accounts_list(user_id, message_id, source_type="command")

# функция показа информации об аккаунте
def unified_show_account_info(user_id, message_id, account_id, source_type):
    try:
        account = get_account_info(account_id)
        
        if not account:
            if source_type == "call":
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text="❌ Не удалось получить информацию о счете.",
                    reply_markup=back_markup("accounts")
                )
                return
            else:
                bot.send_message(
                    user_id,
                    text="❌ Не удалось получить информацию о счете.",
                    reply_markup=back_markup("accounts")
                )
        
        name, amount, created_at = account
        
        # # Преобразуем строку даты в datetime объект
        # try:
        #     created_date = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        #     formatted_date = created_date.strftime('%d.%m.%Y %H:%M')
        # except Exception as e:
        #     logger.error("Ошибка при форматировании даты: %s", str(e))
        #     formatted_date = created_at  # Используем оригинальную дату, если не удалось преобразовать
        
        default_account_id = get_default_account_id(user_id)

        text = f"📛<b>{name}</b> \n\n<i>Информация о счете:</i>\n"
        if default_account_id == account_id:
            text += "Это ваш основной счет. По умолчанию с него списываются деньги при записи трат\n\n"

        text += f"💵 Сумма: {amount} руб.\n"        

        if source_type == "call":
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text = text,
                reply_markup=account_markup(user_id, account_id),
                parse_mode="HTML"
            )
        else:
            bot.send_message(
                user_id,
                text,
                reply_markup=account_markup(user_id, account_id),
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error("Ошибка при получении информации о счете: %s", str(e))
        
        if source_type == "call":
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text="❌ Произошла ошибка при получении информации о счете.",
                reply_markup=back_markup("accounts")
            )
        else:
            bot.send_message(
                user_id,
                "❌ Произошла ошибка при получении информации о счете.",
                reply_markup=back_markup("accounts")
            )

# Обработчик просмотра информации о счете
@bot.callback_query_handler(func=lambda call: call.data.startswith("account_info_"))
def show_account_info(call):
    user_id = call.from_user.id
    message_id = call.message.message_id
    account_id_str = call.data.split("_")[2]
    account_id = int(account_id_str)

    user_states.pop(user_id, None)

    bot.answer_callback_query(call.id)
    unified_show_account_info(user_id, message_id, account_id, source_type="call")
    

# Обработчик кнопки "Добавить счет"
@bot.callback_query_handler(func=lambda call: call.data == "add_account")
def handle_add_account(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    # Устанавливаем начальное состояние для пользователя
    user_states[call.message.chat.id] = {
        "state": "waiting_for_account_name",  # Текущее состояние
        "data": {}  # Словарь для хранения собранных данных
    }
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="Введите название счета:",
            reply_markup=cancel_markup("accounts")
        )

# Обработчик ввода названия счета
@bot.message_handler(func=lambda message: 
    user_states.get(message.chat.id, {}).get("state") == "waiting_for_account_name")
def handle_account_name(message):
    chat_id = message.chat.id
    new_name = message.text
    user_id = message.from_user.id
    
    # Проверяем, существует ли уже счет с таким именем у этого пользователя
    accounts = get_accounts(user_id)
    name_exists = False
    
    for acc in accounts:
        if acc[1].lower() == new_name.lower():
            name_exists = True
            break
    
    if name_exists:
        # Имя уже существует, отправляем сообщение об ошибке
        bot.send_message(
            chat_id,
            f"❌ Счет с названием <i>{new_name.lower()}</i> уже существует. Пожалуйста, введите другое название.",
            reply_markup=cancel_markup("accounts_list"),
            parse_mode="HTML"
        )
        # Сохраняем состояние, чтобы пользователь мог повторить попытку
        return
    
    user_states[message.chat.id].update({
        "state": "waiting_for_amount",
        "data": {"account_name": message.text}
    })
    bot.send_message(
        chat_id=chat_id,
        text="Введите сумму на счету:",
        reply_markup=cancel_markup("accounts")
    )

# Обработчик ввода суммы счета
@bot.message_handler(func=lambda message: 
    user_states.get(message.chat.id, {}).get("state") == "waiting_for_amount")
def handle_account_amount(message):
    try:
        amount = float(message.text)
        account_data = user_states[message.chat.id]["data"]
        account_name = account_data["account_name"]

        user_id = message.from_user.id
        message_id = message.message_id
        
        if add_account(message.from_user.id, account_name, amount):
            bot.send_message(
                message.chat.id, 
                f"✅ Отлично!\n\n Счет <b>{account_name}</b> с суммой <i>{amount}</i> руб. успешно добавлен!",
                parse_mode="HTML"
            )
        else:
            bot.send_message(
                message.chat.id, 
                "❌ Произошла ошибка при добавлении счета. Попробуйте позже."
            )
        
        # Очищаем состояние пользователя после завершения сценария
        user_states.pop(message.chat.id, None)
        
        unified_show_accounts_list(user_id, message_id, source_type="command")    
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректную сумму (число)")


# обработка установки аккаунта в качестве основного
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_default_"))
def handle_set_default_account(call):
    """Обработка выбора основного счета"""
    try:
        account_id = int(call.data.split("_")[2])
        user_id = call.from_user.id
        message_id = call.message.message_id
        
        if set_default_account(user_id, account_id):
            # Получаем информацию о выбранном счете
            account_info = get_account_info(account_id)
            if account_info:
                name, amount, _ = account_info
                bot.answer_callback_query(call.id)
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text=f"✅ Основной счет установлен:\n<b>{name}</b> - <i>{amount}</i> руб.",
                    parse_mode="HTML"    
                )

                unified_show_account_info(user_id, message_id,account_id, source_type="command")
         
      
        else:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text="❌ Произошла ошибка при установке основного счета"
            )
            
            unified_show_account_info(user_id, message_id, account_id, source_type="command")
    except Exception as e:
        logger.exception("Ошибка %e при выборе основного счета", e)

# Обработчик выбора счета для изменения
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_account_amount_"))
def handle_account_to_edit(call):
    try:
        account_id = int(call.data.split("_")[3])
        accounts = get_accounts(call.from_user.id)
        account = next(acc for acc in accounts if acc[0] == account_id)
        
        # Сохраняем информацию о выбранном счете
        user_states[call.from_user.id] = {
            "state": "waiting_for_new_amount",
            "data": {"account_id": account_id, "account_name": account[1]}
        }
        
        # Создаем клавиатуру с кнопкой отмены
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "❌ Отмена",
            callback_data=f"account_info_{account_id}"
        ))
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Введите новую сумму для счета <b>{account[1]}</b>:",
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error("Ошибка при выборе счета: %s", str(e))
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка при выборе счета.",
            reply_markup=back_markup("accounts")
        )

# Обработчик ввода новой суммы
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == "waiting_for_new_amount")
def handle_new_amount(message):
    try:
        new_amount = float(message.text)
        account_data = user_states[message.chat.id]["data"]
        account_id = account_data["account_id"]
        account_name = account_data["account_name"]
        
        user_id = message.from_user.id
        message_id = message.message_id
        
        if update_account_amount(account_id, new_amount):
            bot.send_message(
                message.chat.id, 
                f"✅ Сумма счета <i>{account_name}</i> успешно изменена на {new_amount} руб.",
                parse_mode="HTML"
            )
        else:
            bot.send_message(
                message.chat.id, 
                "❌ Произошла ошибка при изменении суммы счета."
            )
        
        # Очищаем состояние и возвращаемся в меню настроек
        user_states.pop(message.chat.id, None)
        unified_show_account_info(user_id, message_id, account_id, source_type="command")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректную сумму (число)")
    except Exception as e:
        logger.error("Ошибка при изменении суммы счета: %s", str(e))
        bot.send_message(message.chat.id, "❌ Произошла ошибка при изменении суммы счета.")
        user_states.pop(message.chat.id, None)
        bot.send_message(
            message.chat.id,
            accounts_introduce_text,
            reply_markup=accounts_markup()
        )

# Обработчик кнопки "Изменить название счета"
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_account_name_"))
def handle_account_name_to_edit(call):
    try:
        account_id = int(call.data.split("_")[3])
        accounts = get_accounts(call.from_user.id)
        account = next(acc for acc in accounts if acc[0] == account_id)
        
        # Сохраняем информацию о выбранном счете
        user_states[call.from_user.id] = {
            "state": "waiting_for_new_name",
            "data": {
                "account_id": account_id, 
                "account_name": account[1],
                "message_id": call.message.message_id
            }
        }
        
        # Создаем клавиатуру с кнопкой отмены

        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Введите новое название для счета <b>{account[1]}</b>:",
            reply_markup=cancel_markup(f"account_info_{account_id}"),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error("Ошибка при выборе счета для изменения названия: %s", str(e))
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка при выборе счета.",
            reply_markup=back_markup("accounts")
        )

# Обработчик ввода нового названия счета
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == "waiting_for_new_name")
def handle_new_name(message):
    try:
        new_name = message.text
        account_data = user_states[message.chat.id]["data"]
        account_id = account_data["account_id"]
        old_account_name = account_data["account_name"]
        
        user_id = message.from_user.id
        
        # Проверяем, существует ли уже счет с таким именем у этого пользователя
        accounts = get_accounts(user_id)
        name_exists = False
        
        for acc in accounts:
            if acc[0] != account_id and acc[1].lower() == new_name.lower():
                name_exists = True
                break
        
        if name_exists:
            # Имя уже существует, отправляем сообщение об ошибке
            bot.send_message(
                message.chat.id,
                f"❌ Счет с названием <i>{new_name.lower()}</i> уже существует. Пожалуйста, введите другое название.",
                reply_markup=cancel_markup(f"account_info_{account_id}"),
                parse_mode="HTML"
            )
            # Сохраняем состояние, чтобы пользователь мог повторить попытку
            return
        
        if update_account_name(account_id, new_name):
            bot.send_message(
                message.chat.id, 
                f"✅ Название счета успешно изменено с <i>{old_account_name}</i> на <i>{new_name}</i>.",
                parse_mode="HTML"
            )
        else:
            bot.send_message(
                message.chat.id, 
                "❌ Произошла ошибка при изменении названия счета."
            )
        
        # Получаем message_id из состояния пользователя для передачи в функцию показа информации о счете
        message_id = account_data.get("message_id")
        
        # Очищаем состояние 
        user_states.pop(message.chat.id, None)
        
        # Показываем информацию о счете с обновленным названием
        unified_show_account_info(user_id, message_id, account_id, source_type="command")
    except Exception as e:
        logger.error("Ошибка при изменении названия счета: %s", str(e))
        bot.send_message(message.chat.id, "❌ Произошла ошибка при изменении названия счета.")
        user_states.pop(message.chat.id, None)
        bot.send_message(
            message.chat.id,
            accounts_introduce_text,
            reply_markup=accounts_markup()
        )

# Добавляем обработчик подтверждения удаления
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete_"))
def confirm_delete_account(call):
    try:
        account_id = int(call.data.split("_")[2])
        account_name = get_account_info(account_id)[0]

        user_id = call.from_user.id

        
        # Создаем клавиатуру подтверждения
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Да, удалить", callback_data=f"delete_yes_{account_id}"),
            types.InlineKeyboardButton("❌ Нет, отмена", callback_data=f"account_info_{account_id}")
        )
        
        bot.answer_callback_query(call.id)

        text = f"Вы уверены, что хотите удалить счет <b>{account_name}</b>?"

        if get_default_account_id(user_id) == account_id:
            text += "\n\nДанный счет является счетом по умолчанию"

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error("Ошибка при подтверждении удаления: %s", str(e))
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка при подтверждении удаления.",
            reply_markup=back_markup("accounts")
        )

# Добавляем обработчик окончательного удаления
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_yes_"))
def delete_account_final(call):
    try:
        account_id = int(call.data.split("_")[2])
        account_name = get_account_info(account_id)[0]
        
        user_id = call.from_user.id
        message_id = call.message.message_id

        all_accounts_user = get_accounts(user_id)
        if len(all_accounts_user) == 1 and all_accounts_user[0][0] == account_id:
            bot.send_message(
                user_id,
                "❗Вы не можете удалить последний счет по умолчанию.\n\nСоздайте новый или измените этот",
                )
                
            unified_show_accounts_list(user_id, message_id, source_type="command")
            return
        
        # Проверяем наличие транзакций
        result = delete_account(account_id)
        
        if not result['success'] and 'transactions_count' in result:
            # Есть связанные транзакции, спрашиваем пользователя
            transactions_count = result['transactions_count']
            
            # Создаем клавиатуру для выбора действия
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Да, удалить всё", callback_data=f"delete_with_transactions_{account_id}"),
                types.InlineKeyboardButton("❌ Нет, отмена", callback_data=f"account_info_{account_id}")
            )
            
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=f"⚠️ Счет <b>{account_name}</b> содержит <b>{transactions_count}</b> транзакций.\n\nУдаление счета приведет к удалению всех связанных транзакций.\n\nВы уверены, что хотите продолжить?",
                reply_markup=markup,
                parse_mode="HTML"
            )
            return
            
        elif result['success']:
            # Транзакций нет, удаляем счет
            if get_default_account_id(user_id) == account_id:                
               # у первого счета пользователя берем его имя
                new_default_account_id, new_default_account_name, _ = get_accounts(user_id)[0]
                
                bot.answer_callback_query(call.id)
                bot.send_message(
                    user_id, 
                    f"❗Вы удаляете счет <b>{account_name}</b>, который является счетом по умолчанию. \n\nСледующим счётом по умолчанию будет установлен <b>{new_default_account_name}</b>",
                    parse_mode="HTML"
                )
                
                try:
                    set_default_account(user_id, new_default_account_id)
                except Exception as e:
                    logger.error(f"Ошибка при установке нового счета по умолчанию: {str(e)}")
                    bot.send_message(user_id, "❌ Произошла ошибка при установке нового счета по умолчанию")
            else:
                bot.answer_callback_query(call.id)
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text=f"✅ Счет <b>{account_name}</b> успешно удален!",
                    parse_mode="HTML")

            unified_show_accounts_list(user_id, message_id, source_type="command")
        else:
            # Произошла ошибка при удалении
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"❌ Произошла ошибка при удалении счета: {result.get('error', 'Неизвестная ошибка')}")
            
            unified_show_accounts_list(user_id, message_id, source_type="command")
    except Exception as e:
        logger.error(f"Ошибка при удалении счета: {str(e)}")

        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка при удалении счета."
        )
        unified_show_accounts_list(user_id, message_id, source_type="command")

# Добавляем обработчик удаления счета вместе с транзакциями
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_with_transactions_"))
def delete_account_with_transactions_handler(call):
    try:
        account_id = int(call.data.split("_")[3])
        account_name = get_account_info(account_id)[0]
        
        user_id = call.from_user.id
        message_id = call.message.message_id
        
        # Удаляем счет вместе с транзакциями
        result = delete_account_with_transactions(account_id)
        
        if result['success']:
            transactions_deleted = result['transactions_deleted']
            
            # Проверяем, был ли это счет по умолчанию
            if get_default_account_id(user_id) == account_id:
                # Получаем список доступных счетов
                accounts = get_accounts(user_id)
                if accounts:
                    # Устанавливаем первый доступный счет как счет по умолчанию
                    new_default_account_id, new_default_account_name, _ = accounts[0]
                    
                    bot.answer_callback_query(call.id)
                    bot.send_message(
                        user_id, 
                        f"❗Вы удалили счет <b>{account_name}</b>, который был счетом по умолчанию.\n\nСчетом по умолчанию теперь будет <b>{new_default_account_name}</b>",
                        parse_mode="HTML"
                    )
                    
                    try:
                        set_default_account(user_id, new_default_account_id)
                    except Exception as e:
                        logger.error(f"Ошибка при установке нового счета по умолчанию: {str(e)}")
                        bot.send_message(user_id, "❌ Произошла ошибка при установке нового счета по умолчанию")
            
            # Отправляем сообщение об успешном удалении
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=f"✅ Счет <b>{account_name}</b> и связанные с ним <b>{transactions_deleted}</b> транзакций успешно удалены!",
                parse_mode="HTML"
            )
            
            # Показываем обновленный список счетов
            unified_show_accounts_list(user_id, message_id, source_type="command")
        else:
            # Если произошла ошибка
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=f"❌ Произошла ошибка при удалении счета: {result.get('error', 'Неизвестная ошибка')}"
            )
            unified_show_accounts_list(user_id, message_id, source_type="command")
    except Exception as e:
        logger.error(f"Ошибка при удалении счета с транзакциями: {str(e)}")
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка при удалении счета и транзакций."
        )
        unified_show_accounts_list(call.from_user.id, call.message.message_id, source_type="command")

