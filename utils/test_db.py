
import psycopg2
try:
    connection = psycopg2.connect(
        user="admin",
        password="frgewrjh324932y4",
        host="91.222.236.126",
        port=5432,
        dbname="my_first_db"
    )
    print("Подключение успешно!")
    
    # Создаем курсор для выполнения SQL-запросов
    cursor = connection.cursor()
    
    # Пример запроса
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print("Текущее время:", result)

    # Закрываем курсор и соединение
    cursor.close()
    connection.close()
    print("Соединение закрыто.")

except Exception as e:
    print(f"Ошибка подключения: {e}")