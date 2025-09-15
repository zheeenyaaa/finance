from bot_instance import bot
import pandas as pd
from configs.settings import DB_FILE
from datetime import datetime
from bot_logging import *
from configs.tools import get_month_name
import sqlite3


def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Создаем таблицу пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            month_start_day INTEGER DEFAULT 1,
            reminders_enabled INTEGER DEFAULT 0,
            reminder_time TEXT DEFAULT '20:00',
            timezone_offset INTEGER DEFAULT NULL,
            default_account_id INTEGER
        )
        ''')

        # Создаем таблицу счетов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            account_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            account_name TEXT,
            amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')

        # Создаем таблицу категорий
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            is_default INTEGER DEFAULT 0,
            is_expense INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')

        # Создаем таблицу транзакций
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            account_id INTEGER,
            category TEXT,
            amount REAL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (account_id) REFERENCES accounts(account_id)
        )
        ''')
        
        conn.commit()
        logger.info("[SUCCESS] База данных инициализирована")
    except Exception as e:
        logger.error("Ошибка %s при инициализации базы данных", e)
    finally:
        conn.close()



# Функции для работы с пользователями
def add_user(user_id, first_name, last_name, username):
    """Добавление нового пользователя"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO users (user_id, first_name, last_name, username)
        VALUES (?, ?, ?, ?)
        ''', (user_id, first_name, last_name, username))
        conn.commit()
        
        # Добавляем базовые категории для нового пользователя
        default_categories = {
            "еда": {
                "is_expense": 1
            },
            "транспорт": {
                "is_expense": 1
            },
            "жилье": {
                "is_expense": 1
            },
            "красота": {
                "is_expense": 1
            },
            "здоровье": {
                "is_expense": 1
            },
            "быт": {
                "is_expense": 1
            },
            "зарплата": {
                "is_expense": 0
            }
        }
        for category in default_categories:
            cursor.execute('''
            INSERT INTO categories (user_id, name, is_default, is_expense)
            VALUES (?, ?, 1, ?)
            ''', (user_id, category, default_categories[category]["is_expense"]))
        
        conn.commit()
        logger.info("[SUCCESS] Добавлен новый пользователь: %s", user_id)
        return True
    except Exception as e:
        logger.error("Ошибка %s при добавлении пользователя", e)
        return False
    finally:
        conn.close()

def get_user(user_id):
    """Получение информации о пользователе"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    except Exception as e:
        logger.error("Ошибка %s при получении информации о пользователе", e)
        return None
    finally:
        conn.close()

# Функции для работы со счетами
def add_account(user_id, account_name, amount):
    """Добавление нового счета"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO accounts (user_id, account_name, amount)
        VALUES (?, ?, ?)
        ''', (user_id, account_name, amount))
        conn.commit()
        logger.info("[SUCCESS] Создан новый счет: Пользователь=%s, Счет='%s', Сумма=%.2f", user_id, account_name, amount)
        return True
    except Exception as e:
        logger.error("Ошибка %s при добавлении счета", e)
        return False
    finally:
        conn.close()

def get_accounts(user_id):
    """Получение всех счетов пользователя"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT account_id, account_name, amount 
        FROM accounts 
        WHERE user_id = ?
        ''', (user_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.error("Ошибка %s при получении списка счетов", e)
        return []
    finally:
        conn.close()

def get_account_id_by_name(user_id, account_name):
    """Получение ID счета по его имени"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT account_id FROM accounts WHERE user_id = ? and LOWER(account_name) = LOWER(?)', (user_id, account_name))
        result = cursor.fetchone()
        if result:
            logger.info("[SUCCESS] Найден ID счета для имени '%s': %s", account_name, result[0])
            return result[0]
        else:
            logger.warning("Счет с именем '%s' не найден", account_name)
            return False
    except Exception as e:
        logger.error("Ошибка %s при получении ID счета по имени", e)
        return False
    finally:
        conn.close() 


def get_account_info(account_id):
    try:
        logger.info("Получение информации о счете с ID: %s (тип: %s)", account_id, type(account_id))
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(accounts)")
        columns = cursor.fetchall()
        logger.info("Структура таблицы accounts: %s", columns)
        
        cursor.execute('''
            SELECT account_name, amount, created_at 
            FROM accounts 
            WHERE account_id = ?
        ''', (str(account_id),))
        
        account = cursor.fetchone()
        logger.info("Результат запроса: %s", account)
        
        conn.close()
        return account
    except Exception as e:
        logger.error("Ошибка %s при получении информации о счете", e)
        return None
    
def update_account_amount(account_id, new_amount):
    """Обновление суммы на счете"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE accounts 
        SET amount = ? 
        WHERE account_id = ?
        ''', (new_amount, account_id))
        conn.commit()
        logger.info("[SUCCESS] Обновлен баланс счета: ID=%s, Новая сумма=%.2f", account_id, new_amount)
        return True
    except Exception as e:
        logger.error("Ошибка %s при обновлении счета", e)
        return False
    finally:
        conn.close()

def update_account_name(account_id, new_name):
    """Обновление названия счета"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE accounts 
        SET account_name = ? 
        WHERE account_id = ?
        ''', (new_name, account_id))
        conn.commit()
        logger.info(f"[SUCCESS] Обновлено название счета: ID={account_id}, Новое название={new_name}")
        return True
    except Exception as e:
        logger.error("Ошибка %s при обновлении названия счета", e)
        return False
    finally:
        conn.close()

def delete_account(account_id):
    """Удаление счета"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM accounts WHERE account_id = ?', (account_id,))
        conn.commit()
        logger.info("[SUCCESS] Удален счет: ID=%s", account_id)
        return True
    except Exception as e:
        logger.error("Ошибка %s при удалении счета", e)
        return False
    finally:
        conn.close()


def update_account_balance(account_id, amount, is_income):
    """Обновление баланса счета"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT amount FROM accounts WHERE account_id = ?', (account_id,))
        current_balance = cursor.fetchone()[0]
        
        new_balance = current_balance + amount if is_income else current_balance - amount
        
        cursor.execute('''
        UPDATE accounts 
        SET amount = ? 
        WHERE account_id = ?
        ''', (new_balance, account_id))
        
        conn.commit()
        logger.info("[SUCCESS] Обновлен баланс счета: ID=%s, Старый баланс=%.2f, Новый баланс=%.2f", 
                   account_id, current_balance, new_balance)
        return True
    except Exception as e:
        logger.error("Ошибка %s при обновлении баланса счета", e)
        return False
    finally:
        conn.close()

# Функции для работы с транзакциями
def add_transaction(user_id, account_id, category, amount, comment):
    """Добавление новой транзакции"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Проверяем существование категории
        cursor.execute('''
        SELECT 1 FROM categories
        WHERE user_id = ? AND LOWER(name) = LOWER(?)
        ''', (user_id, category))

        if not cursor.fetchone():
            logger.warning("Категория '%s' не найдена у пользователя %s", category, user_id)
            return False
        
        # Добавляем транзакцию
        cursor.execute('''
        INSERT INTO transactions (user_id, account_id, category, amount, comment)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, account_id, category, amount, comment))
        
     
        cursor.execute(
            'SELECT amount FROM accounts WHERE account_id = ?',
            (account_id,)
        )

        current_balance = cursor.fetchone()[0]
        category_id = get_category_id_by_name(user_id, category)
        categories_income = get_income_categories(user_id)
        
        is_income = True if category_id in categories_income else False
       
        new_balance = (
            current_balance + amount if is_income
            else current_balance - amount
        )
        cursor.execute(
            'UPDATE accounts SET amount = ? WHERE account_id = ?',
            (new_balance, account_id)
        )
        
        conn.commit()
        logger.info(
            "[SUCCESS] Добавлена транзакция и обновлен баланс: "
            "Пользователь=%s, Категория=%s, Сумма=%s, Новый баланс=%.2f",
            user_id, category, amount, new_balance
        )
        return True
    except Exception as e:
        conn.rollback()
        logger.error("Ошибка %s при добавлении транзакции", e)
        return False
    finally:
        conn.close()


def get_period_statistics(user_id, period='day'):
    """Получение статистики за период (день/неделя)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        if period == 'day':
            date_condition = "DATE(created_at) = DATE('now')"
        else:  # week
            date_condition = "DATE(created_at) >= DATE('now', '-7 days')"
        
        cursor.execute(f'''
        SELECT 
            category,
            amount,
            created_at,
            comment
        FROM transactions
        WHERE user_id = ? 
        AND {date_condition}
        ORDER BY created_at DESC
        ''', (user_id,))
        
        transactions = cursor.fetchall()
        
        categories = {}
        for category, amount, created_at, comment in transactions:
            if category not in categories:
                categories[category] = {
                    'total': 0,
                    'count': 0,
                    'transactions': []
                }
            
            categories[category]['total'] += amount
            categories[category]['count'] += 1
            categories[category]['transactions'].append({
                'amount': amount,
                'date': created_at,
                'comment': comment
            })
        
        logger.info("[SUCCESS] Получена статистика за период %s: Пользователь=%s", period, user_id)
        return categories
    except Exception as e:
        logger.error("Ошибка %s при получении статистики за период", e)
        return {}
    finally:
        conn.close()

def get_detailed_statistics(user_id):
    """Получение детальной статистики транзакций"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT 
            category,
            amount,
            created_at,
            comment
        FROM transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
        ''', (user_id,))
        
        transactions = cursor.fetchall()
        
        categories = {}
        for category, amount, created_at, comment in transactions:
            if category not in categories:
                categories[category] = {
                    'total': 0,
                    'count': 0,
                    'transactions': []
                }
            
            categories[category]['total'] += amount
            categories[category]['count'] += 1
            categories[category]['transactions'].append({
                'amount': amount,
                'date': created_at,
                'comment': comment
            })
        
        logger.info("[SUCCESS] Получена детальная статистика: Пользователь=%s", user_id)
        return categories
    except Exception as e:
        logger.error("Ошибка %s при получении детальной статистики", e)
        return {}
    finally:
        conn.close()

def get_transactions_by_category(user_id, category):
    """Получение транзакций по категории"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT t.*, a.account_name 
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        WHERE t.user_id = ? AND t.category = ?
        ORDER BY t.created_at DESC
        ''', (user_id, category))
        transactions = cursor.fetchall()
        logger.info("[SUCCESS] Получены транзакции по категории: Пользователь=%s, Категория=%s", user_id, category)
        return transactions
    except Exception as e:
        logger.error("Ошибка %s при получении транзакций по категории", e)
        return []
    finally:
        conn.close()

def get_oldest_transaction_by_user(user_id):
    '''Получение самой ранней транзакции пользователя по ID'''
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT MIN(created_at) FROM transactions WHERE user_id = ?", (user_id, ))
        result = cursor.fetchone()

        return result[0]
    except Exception as e:
        logger.error("Ошибка %s при получении самой ранней транзакции пользователя %s", e, user_id)
        return False
    finally:
        conn.close()

# Функции для работы с днем начала месяца
def set_month_start_day(user_id, day):
    """Установка дня начала месяца для пользователя"""
    if not 1 <= day <= 31:
        return False
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE users 
        SET month_start_day = ? 
        WHERE user_id = ?
        ''', (day, user_id))
        conn.commit()
        logger.info("[SUCCESS] Установлен день начала месяца: Пользователь=%s, День=%d", user_id, day)
        return True
    except Exception as e:
        logger.error("Ошибка %s при установке дня начала месяца", e)
        return False
    finally:
        conn.close()

def get_month_start_day(user_id):
    """Получение дня начала месяца для пользователя"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT month_start_day 
        FROM users 
        WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 1
    except Exception as e:
        logger.error("Ошибка %s при получении дня начала месяца", e)
        return 1
    finally:
        conn.close()


def set_reminders_enabled(user_id, enabled):
    """Включение/выключение напоминаний"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE users 
        SET reminders_enabled = ? 
        WHERE user_id = ?
        ''', (1 if enabled else 0, user_id))
        conn.commit()
        status = "включены" if enabled else "выключены"
        logger.info("[SUCCESS] Напоминания %s: Пользователь=%s", status, user_id)
        return True
    except Exception as e:
        logger.error("Ошибка %s при изменении статуса напоминаний", e)
        return False
    finally:
        conn.close()

def set_reminder_time(user_id, time):
    """Установка времени напоминания"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE users 
        SET reminder_time = ? 
        WHERE user_id = ?
        ''', (time, user_id))
        conn.commit()
        logger.info("[SUCCESS] Установлено время напоминания: Пользователь=%s, Время=%s", user_id, time)
        return True
    except Exception as e:
        logger.error("Ошибка %s при установке времени напоминания", e)
        return False
    finally:
        conn.close()

def get_reminder_settings(user_id):
    """Получение настроек напоминаний"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT reminders_enabled, reminder_time 
        FROM users 
        WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        return {
            'enabled': bool(result[0]) if result else True,
            'time': result[1] if result else '21:00'
        }
    except Exception as e:
        logger.error("Ошибка %s при получении настроек напоминаний", e)
        return {'enabled': True, 'time': '21:00'}
    finally:
        conn.close()

def set_timezone_offset(user_id, offset):
    """Установка смещения часового пояса"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE users 
        SET timezone_offset = ? 
        WHERE user_id = ?
        ''', (offset, user_id))
        conn.commit()
        logger.info("[SUCCESS] Установлен часовой пояс: Пользователь=%s, UTC+%d", user_id, offset)
        return True
    except Exception as e:
        logger.error("Ошибка %s при установке часового пояса", e)
        return False
    finally:
        conn.close()

def get_timezone_offset(user_id):
    """Получение смещения часового пояса"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT timezone_offset 
        FROM users 
        WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        logger.error("Ошибка %s при получении смещения часового пояса", e)
        return None
    finally:
        conn.close()

def has_timezone(user_id):
    """Проверка, установлена ли таймзона у пользователя"""
    timezone = get_timezone_offset(user_id)
    return timezone is not None

def set_default_account(user_id, account_id):
    """Установка основного счета"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE users 
        SET default_account_id = ? 
        WHERE user_id = ?
        ''', (account_id, user_id))
        conn.commit()
        logger.info("[SUCCESS] Установлен основной счет: Пользователь=%s, Счет=%s", user_id, account_id)
        return True
    except Exception as e:
        logger.error("Ошибка %s при установке основного счета", e)
        return False
    finally:
        conn.close()

def get_default_account_id(user_id):
    """Получение основного счета"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT default_account_id 
        FROM users 
        WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        logger.error("Ошибка %s при получении основного счета", e)
        return None
    finally:
        conn.close()

def get_default_account_id_info(user_id):
    """Получение информации об основном счете"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT a.account_id, a.account_name, a.amount
        FROM accounts a
        JOIN users u ON a.account_id = u.default_account_id
        WHERE u.user_id = ?
        ''', (user_id,))
        return cursor.fetchone()
    except Exception as e:
        logger.error("Ошибка %s при получении информации об основном счете", e)
        return None
    finally:
        conn.close()

def get_month_balance(user_id, year, month):
    print(user_id)
    """Получение баланса за месяц"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    logger.info("Получение баланса за %s-%s", year, month)
    try:
        # cursor.execute('SELECT month_start_day FROM users WHERE user_id = ?', (user_id,))
        # month_start_day = 1

        # if month_start_day > 1:
        #     if month == 1:
        #         start_date = f"{year-1}-12-{month_start_day:02d}"
        #         end_date = f"{year}-{month:02d}-{month_start_day-1:02d}"
        #     else:
        #         start_date = f"{year}-{month-1:02d}-{month_start_day:02d}"
        #         end_date = f"{year}-{month:02d}-{month_start_day-1:02d}"
        # else:
        start_date = f"{year}-{month:02d}-01 00:00:00"
        if month == 12:
            end_date = f"{year+1}-01-01 00:00:00"
        else:
            end_date = f"{year}-{month+1:02d}-01 00:00:00"

        try:
            cursor.execute('''
            SELECT amount, category
            FROM transactions
            WHERE user_id = ? 
            AND created_at >= ? 
            AND created_at < ?
            ''', (user_id, start_date, end_date))
            
            transactions = cursor.fetchall()
            print(transactions, 42)
            logger.info("Найденные транзакции: %s", transactions)
        except Exception as e:
            print("error")
       
        
        income = 0
        expenses = 0
        income_categories = get_income_categories(user_id)
       
        for amount, category in transactions:
            if get_category_id_by_name(user_id, category) in income_categories:
                income += amount
            else:
                expenses += amount
        
        balance = income - expenses
        
        logger.info("[SUCCESS] Получен баланс за месяц: Пользователь=%s, Доходы=%.2f, Расходы=%.2f, Баланс=%.2f", 
                   user_id, income, expenses, balance)
        
        return {
            'income': income,
            'expenses': expenses,
            'balance': balance
        }
    except Exception as e:
        logger.error("Ошибка %s при получении баланса за месяц", e)
        return {'income': 0, 'expenses': 0, 'balance': 0}
    finally:
        conn.close()

def delete_all_information(user_id):
    """Удаление всей информации о пользователе из базы данных"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Начинаем транзакцию
        cursor.execute('BEGIN TRANSACTION')
        
        # Получаем список всех счетов пользователя
        cursor.execute('SELECT account_id FROM accounts WHERE user_id = ?', (user_id,))
        accounts = cursor.fetchall()
        
        # Удаляем все транзакции пользователя
        cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
        logger.info("[SUCCESS] Удалены все транзакции пользователя %s", user_id)
        
        # Удаляем все счета пользователя
        cursor.execute('DELETE FROM accounts WHERE user_id = ?', (user_id,))
        logger.info("[SUCCESS] Удалены все счета пользователя %s", user_id)
         
        # удаляем категории
        cursor.execute('DELETE FROM categories WHERE user_id = ?', (user_id,))
        logger.info("[SUCCESS] Удалены категории пользователя %s", user_id)
        
        # Удаляем пользователя
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        logger.info("[SUCCESS] Удален пользователь %s", user_id)

       
        # Подтверждаем транзакцию
        conn.commit()
        logger.info("[SUCCESS] Вся информация о пользователе %s успешно удалена", user_id)
        return True
        
    except Exception as e:
        # В случае ошибки откатываем транзакцию
        conn.rollback()
        logger.error("Ошибка %s при удалении информации о пользователе", e)
        return False
    finally:
        conn.close()

# Функции для работы с категориями
def get_categories(user_id):
    """Получение списка категорий пользователя"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT category_id, name, is_default, is_expense
        FROM categories
        WHERE user_id = ?
        ORDER BY is_default DESC, name ASC
        ''', (user_id,))
        categories = cursor.fetchall()
        logger.info("[SUCCESS] Получены категории пользователя %s", user_id)
        return categories
    except Exception as e:
        logger.error("Ошибка %s при получении категорий", e)
        return []
    finally:
        conn.close()

def get_categories_name(user_id):
    '''Получение списка имен категорий пользователя'''
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT name FROM categories WHERE user_id = ?', (user_id,))
        result = cursor.fetchall()

        categories_name = []
        for res in result:
            categories_name.append(res[0].lower())

        logger.info("[SUCCESS] Получены имена категорий пользователя %s", user_id)
        return categories_name
    except Exception as e:
        logger.error("Ошибка %s при получении имен категорий", e)
        return []
    finally:
        conn.close()

def get_category_name(category_id):
    '''Получение имени категории пользователя'''
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT name FROM categories WHERE category_id = ?', (category_id,))
        result = cursor.fetchone()


        logger.info("[SUCCESS] Получено имя категории по id = %s", category_id)
        return result[0]
    except Exception as e:
        logger.error("Ошибка %s при получении имен категории", e)
        return []
    finally:
        conn.close()

def get_category_id_by_name(user_id, category_name):
    '''Получение id категории пользователя по имени категории'''
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT category_id FROM categories WHERE LOWER(name) = LOWER(?) and user_id = ?', (category_name, user_id))
        result = cursor.fetchone()


        logger.info("[SUCCESS] Получено id категории по имени = %s", category_name)
        return result[0]
    except Exception as e:
        logger.error("Ошибка %s при получении айди категории", e)
        return []
    finally:
        conn.close()

def get_expense_categories(user_id):
    '''Получение id всех категорий расхода пользователя'''
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT category_id FROM categories WHERE is_expense = 1 AND user_id = ?", (user_id))
        result = cursor.fetchall()

        expense_categories_id = []

        for res in result:
            expense_categories_id.append(res[0])

        logger.info("[SUCCESS] Получены все категории расхода пользователя %s", user_id)
        return expense_categories_id
    except Exception as e:
        logger.error("Ошибка %s при получении категорий расхода", e)
        return []
    finally:
        conn.close()


def get_income_categories(user_id):

    '''Получение id всех категорий дохода пользователя'''
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT category_id FROM categories WHERE is_expense = 0 AND user_id = ?", (user_id,))
        result = cursor.fetchall()

        income_categories_id = []

        for res in result:
            income_categories_id.append(res[0])

        logger.info("[SUCCESS] Получены все категории дохода пользователя %s", user_id)
        return income_categories_id
    except Exception as e:
        logger.error("Ошибка %s при получении категорий дохода", e)
        return []
    finally:
        conn.close()


def add_category(user_id, category_name, is_expense):
    """Добавление новой категории"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        #делаем имя категории в нижнем регистре
        category_name = category_name.lower()

        # Проверяем, существует ли уже такая категория
        cursor.execute('''
        SELECT 1 FROM categories
        WHERE user_id = ? AND LOWER(name) = LOWER(?)
        ''', (user_id, category_name))
        if cursor.fetchone():
            logger.warning("Категория '%s' уже существует у пользователя %s", category_name, user_id)
            return False
        
        cursor.execute('''
        INSERT INTO categories (user_id, name, is_expense)
        VALUES (?, ?, ?)
        ''', (user_id, category_name, is_expense))
        conn.commit()
        logger.info("[SUCCESS] Добавлена новая категория '%s' для пользователя %s", category_name, user_id)
        return True
    except Exception as e:
        logger.error("Ошибка %s при добавлении категории", e)
        return False
    finally:
        conn.close()

def delete_category(user_id, category_id):
    """Удаление категории"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Проверяем, является ли категория базовой
        cursor.execute('''
        SELECT is_default FROM categories
        WHERE category_id = ? AND user_id = ?
        ''', (category_id, user_id))
        result = cursor.fetchone()
        
        if not result:
            logger.warning("Категория %s не найдена у пользователя %s", category_id, user_id)
            return False
                
        cursor.execute('''
        DELETE FROM categories
        WHERE category_id = ? AND user_id = ?
        ''', (category_id, user_id))
        conn.commit()
        logger.info("[SUCCESS] Удалена категория %s у пользователя %s", category_id, user_id)
        return True
    except Exception as e:
        logger.error("Ошибка %s при удалении категории", e)
        return False
    finally:
        conn.close()

def update_category(user_id, category_id, new_name):
    """Изменение названия категории"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Проверяем существование категории
        cursor.execute('''
        SELECT 1 FROM categories
        WHERE category_id = ? AND user_id = ?
        ''', (category_id, user_id))
        if not cursor.fetchone():
            logger.warning("Категория %s не найдена у пользователя %s", category_id, user_id)
            return False
        
        # Проверяем, существует ли уже такая категория
        cursor.execute('''
        SELECT 1 FROM categories
        WHERE user_id = ? AND LOWER(name) = LOWER(?) AND category_id != ?
        ''', (user_id, new_name, category_id))
        if cursor.fetchone():
            logger.warning("Категория '%s' уже существует у пользователя %s", new_name, user_id)
            return False
        
        cursor.execute('''
        UPDATE categories
        SET name = ?
        WHERE category_id = ? AND user_id = ?
        ''', (new_name, category_id, user_id))
        conn.commit()
        logger.info("[SUCCESS] Обновлено название категории %s на '%s' у пользователя %s", 
                   category_id, new_name, user_id)
        return True
    except Exception as e:
        logger.error("Ошибка %s при обновлении категории", e)
        return False
    finally:
        conn.close()