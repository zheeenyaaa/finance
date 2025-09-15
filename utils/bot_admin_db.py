import psycopg2  
import psycopg2.extras 
from configs.settings import DB_CONFIG 
from bot_logging import *

def connect_db():
    """Соединение с базой данных PostgreSQL"""
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )


def get_total_users_count():
    """Получение общего количества пользователей"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        logger.info(f"[SUCCESS] Получено общее количество пользователей: {count}")
        return count
    except Exception as e:
        logger.error(f"Ошибка при получении общего количества пользователей: {str(e)}")
        return 0
    finally:
        cursor.close()
        conn.close()

def get_new_users_today():
    """Получение количества пользователей, зарегистрировавшихся сегодня"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE DATE(created_at) = CURRENT_DATE
        ''')
        count = cursor.fetchone()[0]
        logger.info(f"[SUCCESS] Получено количество новых пользователей за сегодня: {count}")
        return count
    except Exception as e:
        logger.error(f"Ошибка при получении новых пользователей: {str(e)}")
        return 0
    finally:
        cursor.close()
        conn.close()

def get_admin_ids():
    """Получение списка ID администраторов"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT admin_id FROM admins')
        admins = [admin[0] for admin in cursor.fetchall()]
        return admins
    except Exception as e:
        logger.error(f"Ошибка при получении списка администраторов: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()

def is_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT 1 FROM admins WHERE admin_id = %s', (user_id,))
        result = cursor.fetchone() is not None
        return result
    except Exception as e:
        logger.error(f"Ошибка при проверке прав администратора: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def add_admin(admin_id, username):
    """Добавление нового администратора"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO admins (admin_id, username)
        VALUES (%s, %s)
        ON CONFLICT (admin_id) DO NOTHING
        ''', (admin_id, username))
        conn.commit()
        logger.info(f"[SUCCESS] Добавлен новый администратор: {username} (ID: {admin_id})")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при добавлении администратора: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def init_first_admin(admin_id):
    """Инициализация первого администратора при запуске"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Проверяем, есть ли администраторы в системе
        cursor.execute('SELECT COUNT(*) FROM admins')
        count = cursor.fetchone()[0]
        
        # Если администраторов нет, добавляем первого
        if count == 0:
            cursor.execute('''
            INSERT INTO admins (admin_id, username)
            VALUES (%s, 'First Admin')
            ''', (admin_id,))
            conn.commit()
            logger.info(f"[SUCCESS] Инициализирован первый администратор с ID: {admin_id}")
            return True
        return False
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при инициализации первого администратора: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()