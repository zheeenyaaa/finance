from telebot import types
from bot_instance import bot
from bot_logging import logger
from utils.bot_admin_db import (
    is_admin, add_admin, get_total_users_count, 
    get_new_users_today, get_admin_ids
)

# Декоратор для проверки прав администратора
def admin_required(func):
    def wrapper(message, *args, **kwargs):
        user_id = message.from_user.id
        if is_admin(user_id):
            return func(message, *args, **kwargs)
        else:
            bot.reply_to(message, "⛔ У вас нет прав для выполнения этой команды.")
    return wrapper

# Обработчик команды для проверки статуса администратора
@bot.message_handler(commands=['admin'])
def handle_admin_check(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        bot.reply_to(message, "👑 Вы являетесь администратором бота.")
    else:
        bot.reply_to(message, "⚠️ Вы не являетесь администратором бота.")

# Обработчик команды для получения общей статистики
@bot.message_handler(commands=['stats'])
@admin_required
def handle_stats(message):
    """Получение общей статистики пользователей"""
    total_users = get_total_users_count()
    new_users_today = get_new_users_today()
    
    stats_text = (
        f"📊 Статистика бота:\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"👥 Новых пользователей: {new_users_today}"
    )
    
    bot.reply_to(message, stats_text)
    logger.info(f"Администратор {message.from_user.id} запросил общую статистику")

# Обработчик команды для добавления нового администратора
@bot.message_handler(commands=['addadmin'])
@admin_required
def handle_add_admin(message):
    """Добавление нового администратора"""
    parts = message.text.split()
    
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Укажите ID пользователя, которого хотите сделать администратором.\n\nПример: /addadmin 123456789")
        return
    
    try:
        new_admin_id = int(parts[1])
        username = parts[2] if len(parts) > 2 else "Unknown"
        
        if add_admin(new_admin_id, username):
            bot.reply_to(message, f"✅ Пользователь с ID {new_admin_id} успешно добавлен как администратор.")
        else:
            bot.reply_to(message, f"❌ Ошибка при добавлении администратора.")
            
    except ValueError:
        bot.reply_to(message, "⚠️ ID пользователя должен быть числом.")
        
    logger.info(f"Администратор {message.from_user.id} попытался добавить нового администратора с ID {parts[1]}")

# Обработчик команды для получения справки о командах администратора
@bot.message_handler(commands=['adminhelp'])
@admin_required
def handle_admin_help(message):
    """Получение справки по административным командам"""
    help_text = (
        "👑 Команды администратора:\n\n"
        "/admin - Проверка статуса администратора\n"
        "/stats - Общая статистика пользователей\n"
        "/today - Статистика пользователей за сегодня\n"
        "/addadmin ID [username] - Добавление нового администратора\n"
        "/adminhelp - Эта справка"
    )
    
    bot.reply_to(message, help_text) 