
from configs.settings import DB_CONFIG
from datetime import datetime
from bot_logging import *
from configs.tools import get_month_name
import psycopg2  
import psycopg2.extras  
from decimal import Decimal

def connect_db():
    """Соединение с базой данных PostgreSQL"""
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )


def init_db():
    """Инициализация базы данных"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Создаем таблицу пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            month_start_day INTEGER DEFAULT 1,
            reminders_enabled BOOLEAN DEFAULT TRUE,
            reminder_time TEXT DEFAULT '20:00',
            timezone_offset INTEGER DEFAULT NULL,
            default_account_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Создаем таблицу администраторов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            admin_id BIGINT PRIMARY KEY,
            username TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Создаем таблицу счетов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            account_id SERIAL PRIMARY KEY,
            user_id BIGINT,
            account_name TEXT,
            amount NUMERIC(15, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')

        # Создаем таблицу категорий
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id SERIAL PRIMARY KEY,
            user_id BIGINT,
            name TEXT,
            is_default BOOLEAN DEFAULT FALSE,
            is_expense BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')

        # Создаем таблицу транзакций
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id SERIAL PRIMARY KEY,
            user_id BIGINT,
            account_id INTEGER,
            category TEXT,
            amount NUMERIC(15, 2),
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
       INSERT INTO users (user_id, first_name, last_name, username)
        VALUES (%s, %s, %s, %s)
        ''', (user_id, first_name, last_name, username))
        conn.commit()
        
        # Добавляем базовые категории для нового пользователя
        default_categories = {
            "еда": {
                "is_expense": True
            },
            "транспорт": {
                "is_expense": True
            },
            "жилье": {
                "is_expense": True
            },
            "красота": {
                "is_expense": True
            },
            "здоровье": {
                "is_expense": True
            },
            "быт": {
                "is_expense": True
            },
            "зарплата": {
                "is_expense": False
            }
        }
        for category in default_categories:
            cursor.execute('''
            INSERT INTO categories (user_id, name, is_default, is_expense)
            VALUES (%s, %s, %s, %s)
            ''', (user_id, category, True, default_categories[category]["is_expense"]))
        
        conn.commit()
        logger.info("[SUCCESS] Добавлен новый пользователь: %s", user_id)
        return True
    except Exception as e:
        conn.rollback()
        logger.error("Ошибка %s при добавлении пользователя", e)
        return False
    finally:
        cursor.close()
        conn.close()

def get_user(user_id):
    """Получение информации о пользователе"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
        return cursor.fetchone()
    except Exception as e:
        logger.error("Ошибка %s при получении информации о пользователе", e)
        return None
    finally:
        cursor.close()
        conn.close()

        
# Функции для работы со счетами
def add_account(user_id, account_name, amount):
    """Добавление нового счета"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO accounts (user_id, account_name, amount)
        VALUES (%s, %s, %s) RETURNING account_id
        ''', (user_id, account_name, amount))
        account_id = cursor.fetchone()[0]
        conn.commit()
        logger.info("[SUCCESS] Создан новый счет: Пользователь=%s, Счет='%s', Сумма=%.2f", user_id, account_name, amount)
        return True
    except Exception as e:
        conn.rollback()
        logger.error("Ошибка %s при добавлении счета", e)
        return False
    finally:
        cursor.close()
        conn.close()

def get_accounts(user_id):
    """Получение всех счетов пользователя"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT account_id, account_name, amount 
        FROM accounts 
        WHERE user_id = %s
        ''', (user_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.error("Ошибка %s при получении списка счетов", e)
        return []
    finally:
        cursor.close()
        conn.close()


def get_account_id_by_name(user_id, account_name):
    """Получение ID счета по его имени"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT account_id FROM accounts WHERE user_id = %s AND LOWER(account_name) = LOWER(%s)', 
                       (user_id, account_name))
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
        cursor.close()
        conn.close()


def get_account_info(account_id):
    try:
        logger.info("Получение информации о счете с ID: %s (тип: %s)", account_id, type(account_id))
        
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT account_name, amount, created_at 
            FROM accounts 
            WHERE account_id = %s
        ''', (account_id,))
        
        account = cursor.fetchone()
        logger.info("Результат запроса: %s", account)
        
        cursor.close()
        conn.close()
        return account
    except Exception as e:
        logger.error("Ошибка %s при получении информации о счете", e)
        return None
    
def update_account_amount(account_id, new_amount):
    """Обновление суммы на счете"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE accounts 
        SET amount = %s 
        WHERE account_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE accounts 
        SET account_name = %s 
        WHERE account_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Проверяем наличие транзакций, связанных с этим счетом
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE account_id = %s', (account_id,))
        transactions_count = cursor.fetchone()[0]
        
        if transactions_count > 0:
            # Возвращаем информацию о количестве связанных транзакций
            logger.info(f"Невозможно удалить счет ID={account_id}: связан с {transactions_count} транзакциями")
            return {'success': False, 'transactions_count': transactions_count}
        
        # Если транзакций нет, удаляем счет
        cursor.execute('DELETE FROM accounts WHERE account_id = %s', (account_id,))
        conn.commit()
        logger.info(f"[SUCCESS] Удален счет: ID={account_id}")
        return {'success': True}
    except Exception as e:
        logger.error(f"Ошибка при удалении счета: {str(e)}")
        return {'success': False, 'error': str(e)}
    finally:
        cursor.close()
        conn.close()


def update_account_balance(account_id, amount, is_income):
    """Обновление баланса счета"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT amount FROM accounts WHERE account_id = %s', (account_id,))
        current_balance = cursor.fetchone()[0]
        
        new_balance = current_balance + amount if is_income else current_balance - amount
        
        cursor.execute('''
        UPDATE accounts 
        SET amount = %s 
        WHERE account_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Преобразование amount в Decimal
        amount = Decimal(str(amount))

        # Проверяем существование категории
        cursor.execute('''
        SELECT 1 FROM categories
        WHERE user_id = %s AND LOWER(name) = LOWER(%s)
        ''', (user_id, category))

        if not cursor.fetchone():
            logger.warning("Категория '%s' не найдена у пользователя %s", category, user_id)
            return False
        
        # Добавляем транзакцию
        cursor.execute('''
        INSERT INTO transactions (user_id, account_id, category, amount, comment)
        VALUES (%s, %s, %s, %s, %s)
        ''', (user_id, account_id, category, amount, comment))
        
     
        cursor.execute(
            'SELECT amount FROM accounts WHERE account_id = %s',
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
            'UPDATE accounts SET amount = %s WHERE account_id = %s',
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
    """Получение статистики за период (день/неделя) с разделением на доходы и расходы"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        if period == 'day':
            date_condition = "DATE(created_at) = CURRENT_DATE"
        else:  # week
            date_condition = "DATE(created_at) >= (CURRENT_DATE - INTERVAL '7 days')"
        
        cursor.execute(f'''
        SELECT 
            category,
            amount,
            created_at,
            comment
        FROM transactions
        WHERE user_id = %s 
        AND {date_condition}
        ORDER BY created_at DESC
        ''', (user_id,))
        
        transactions = cursor.fetchall()
        
        # Получаем списки ID категорий доходов и расходов
        income_categories_ids = get_income_categories(user_id)
        expense_categories_ids = get_expense_categories(user_id)
        
        # Создаем структуру с разделением на доходы и расходы
        result = {
            'income': {},  # Категории доходов
            'expense': {}  # Категории расходов
        }
        
        # Обрабатываем каждую транзакцию
        for category, amount, created_at, comment in transactions:
            # Определяем тип категории (доход/расход)
            category_id = get_category_id_by_name(user_id, category)
            
            if category_id in income_categories_ids:
                category_type = 'income'
            else:
                category_type = 'expense'
            
            # Добавляем категорию в соответствующий раздел, если ее еще нет
            if category not in result[category_type]:
                result[category_type][category] = {
                    'total': 0,
                    'count': 0,
                    'transactions': []
                }
            
            # Добавляем информацию о транзакции
            result[category_type][category]['total'] += amount
            result[category_type][category]['count'] += 1
            result[category_type][category]['transactions'].append({
                'amount': amount,
                'date': created_at,
                'comment': comment
            })
        
        logger.info("[SUCCESS] Получена статистика за период %s: Пользователь=%s", period, user_id)
        return result
    except Exception as e:
        logger.error("Ошибка %s при получении статистики за период", e)
        return {'income': {}, 'expense': {}}
    finally:
        cursor.close()
        conn.close()

def get_detailed_statistics(user_id):
    """Получение детальной статистики транзакций с разделением на доходы и расходы"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT 
            category,
            amount,
            created_at,
            comment
        FROM transactions
        WHERE user_id = %s
        ORDER BY created_at DESC
        ''', (user_id,))
        
        transactions = cursor.fetchall()
        
        # Получаем списки ID категорий доходов и расходов
        income_categories_ids = get_income_categories(user_id)
        expense_categories_ids = get_expense_categories(user_id)
        
        # Создаем структуру с разделением на доходы и расходы
        result = {
            'income': {},  # Категории доходов
            'expense': {}  # Категории расходов
        }
        
        # Обрабатываем каждую транзакцию
        for category, amount, created_at, comment in transactions:
            # Определяем тип категории (доход/расход)
            category_id = get_category_id_by_name(user_id, category)
            
            if category_id in income_categories_ids:
                category_type = 'income'
            else:
                category_type = 'expense'
            
            # Добавляем категорию в соответствующий раздел, если ее еще нет
            if category not in result[category_type]:
                result[category_type][category] = {
                    'total': 0,
                    'count': 0,
                    'transactions': []
                }
            
            # Добавляем информацию о транзакции
            result[category_type][category]['total'] += amount
            result[category_type][category]['count'] += 1
            result[category_type][category]['transactions'].append({
                'amount': amount,
                'date': created_at,
                'comment': comment
            })
        
        logger.info("[SUCCESS] Получена детальная статистика (доходы/расходы): Пользователь=%s", user_id)
        return result
    except Exception as e:
        logger.error("Ошибка %s при получении детальной статистики", e)
        return {'income': {}, 'expense': {}}
    finally:
        cursor.close()
        conn.close()

def get_transactions_by_category(user_id, category):
    """Получение транзакций по категории"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT t.*, a.account_name 
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        WHERE t.user_id = %s AND t.category = %s
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
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT MIN(created_at) FROM transactions WHERE user_id = %s", (user_id, ))
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
    
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE users 
        SET month_start_day = %s 
        WHERE user_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT month_start_day 
        FROM users 
        WHERE user_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE users 
        SET reminders_enabled = %s 
        WHERE user_id = %s
        ''', (True if enabled else False, user_id))
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE users 
        SET reminder_time = %s 
        WHERE user_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT reminders_enabled, reminder_time 
        FROM users 
        WHERE user_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE users 
        SET timezone_offset = %s 
        WHERE user_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT timezone_offset 
        FROM users 
        WHERE user_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE users 
        SET default_account_id = %s 
        WHERE user_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT default_account_id 
        FROM users 
        WHERE user_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT a.account_id, a.account_name, a.amount
        FROM accounts a
        JOIN users u ON a.account_id = u.default_account_id
        WHERE u.user_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()

    logger.info("Получение баланса за %s-%s", year, month)
    try:
        # cursor.execute('SELECT month_start_day FROM users WHERE user_id = %s', (user_id,))
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
            WHERE user_id = %s 
            AND created_at >= %s 
            AND created_at < %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Проверяем существование пользователя
        cursor.execute('SELECT COUNT(*) FROM users WHERE user_id = %s', (user_id,))
        if cursor.fetchone()[0] == 0:
            logger.warning(f"Пользователь {user_id} не найден в базе данных")
            return False
            
        # Порядок важен из-за внешних ключей в PostgreSQL
        
        # 1. Удаляем транзакции
        try:
            cursor.execute('DELETE FROM transactions WHERE user_id = %s', (user_id,))
            affected_rows = cursor.rowcount
            logger.info(f"[SUCCESS] Удалены транзакции пользователя {user_id}: {affected_rows} записей")
        except Exception as e:
            logger.error(f"Ошибка при удалении транзакций: {str(e)}")
            raise
        
        # 2. Удаляем счета
        try:
            cursor.execute('DELETE FROM accounts WHERE user_id = %s', (user_id,))
            affected_rows = cursor.rowcount
            logger.info(f"[SUCCESS] Удалены счета пользователя {user_id}: {affected_rows} записей")
        except Exception as e:
            logger.error(f"Ошибка при удалении счетов: {str(e)}")
            raise
        
        # 3. Удаляем категории
        try:
            cursor.execute('DELETE FROM categories WHERE user_id = %s', (user_id,))
            affected_rows = cursor.rowcount
            logger.info(f"[SUCCESS] Удалены категории пользователя {user_id}: {affected_rows} записей")
        except Exception as e:
            logger.error(f"Ошибка при удалении категорий: {str(e)}")
            raise
        
        # 4. Удаляем пользователя
        try:
            cursor.execute('DELETE FROM users WHERE user_id = %s', (user_id,))
            affected_rows = cursor.rowcount
            logger.info(f"[SUCCESS] Удален пользователь {user_id}: {affected_rows} записей")
        except Exception as e:
            logger.error(f"Ошибка при удалении пользователя: {str(e)}")
            raise
        
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
        cursor.close()
        conn.close()

# Функции для работы с категориями
def get_categories(user_id):
    """Получение списка категорий пользователя"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT category_id, name, is_default, is_expense
        FROM categories
        WHERE user_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT name FROM categories WHERE user_id = %s', (user_id,))
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT name FROM categories WHERE category_id = %s', (category_id,))
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT category_id FROM categories WHERE LOWER(name) = LOWER(%s) and user_id = %s', (category_name, user_id))
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
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT category_id FROM categories WHERE is_expense = TRUE AND user_id = %s", (user_id, ))
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
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT category_id FROM categories WHERE is_expense = FALSE AND user_id = %s", (user_id,))
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        #делаем имя категории в нижнем регистре
        category_name = category_name.lower()

        # Проверяем, существует ли уже такая категория
        cursor.execute('''
        SELECT 1 FROM categories
        WHERE user_id = %s AND LOWER(name) = LOWER(%s)
        ''', (user_id, category_name))
        if cursor.fetchone():
            logger.warning("Категория '%s' уже существует у пользователя %s", category_name, user_id)
            return False
        
        cursor.execute('''
        INSERT INTO categories (user_id, name, is_expense)
        VALUES (%s, %s, %s)
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Проверяем, является ли категория базовой
        cursor.execute('''
        SELECT is_default FROM categories
        WHERE category_id = %s AND user_id = %s
        ''', (category_id, user_id))
        result = cursor.fetchone()
        
        if not result:
            logger.warning("Категория %s не найдена у пользователя %s", category_id, user_id)
            return False
                
        cursor.execute('''
        DELETE FROM categories
        WHERE category_id = %s AND user_id = %s
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
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Проверяем существование категории
        cursor.execute('''
        SELECT 1 FROM categories
        WHERE category_id = %s AND user_id = %s
        ''', (category_id, user_id))
        if not cursor.fetchone():
            logger.warning("Категория %s не найдена у пользователя %s", category_id, user_id)
            return False
        
        # Проверяем, существует ли уже такая категория
        cursor.execute('''
        SELECT 1 FROM categories
        WHERE user_id = %s AND LOWER(name) = LOWER(%s) AND category_id != %s
        ''', (user_id, new_name, category_id))
        if cursor.fetchone():
            logger.warning("Категория '%s' уже существует у пользователя %s", new_name, user_id)
            return False
        
        cursor.execute('''
        UPDATE categories
        SET name = %s
        WHERE category_id = %s AND user_id = %s
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

def delete_account_with_transactions(account_id):
    """Удаление счета вместе со всеми связанными транзакциями"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Начинаем транзакцию
        
        # Сначала удаляем все связанные транзакции
        cursor.execute('DELETE FROM transactions WHERE account_id = %s', (account_id,))
        transactions_deleted = cursor.rowcount
        logger.info(f"[SUCCESS] Удалено {transactions_deleted} транзакций, связанных со счетом ID={account_id}")
        
        # Затем удаляем сам счет
        cursor.execute('DELETE FROM accounts WHERE account_id = %s', (account_id,))
        account_deleted = cursor.rowcount
        
        conn.commit()
        logger.info(f"[SUCCESS] Удален счет ID={account_id} вместе с {transactions_deleted} транзакциями")
        
        return {'success': True, 'transactions_deleted': transactions_deleted, 'account_deleted': account_deleted}
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при удалении счета с транзакциями: {str(e)}")
        return {'success': False, 'error': str(e)}
    finally:
        cursor.close()
        conn.close()

