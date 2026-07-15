import os
import re
import sys

try:
    import psycopg2
    from dotenv import load_dotenv
except ImportError:
    print("Ошибка, не установлены пакеты")
    sys.exit(1)

FORBIDDEN_COMMANDS = (
    'DELETE', 'UPDATE', 'DROP', 'ALTER', 'INSERT',
    'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE', 'EXECUTE',
    'CALL', 'COPY', 'MERGE', 'VACUUM', 'COMMENT',
    'LOCK', 'UNLOCK', 'BEGIN', 'COMMIT', 'ROLLBACK'
)


def load_config():
    """Функция для чтения .env файла с конфигурацией"""
    load_dotenv()

    config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }

    required = ['database', 'user']  # Обязательные поля, БД и пользователь
    empty_values = [key for key in required if not config.get(key)]

    if empty_values:
        print(f"Ошибка: не заполнены поля: {', '.join(empty_values)}")
        print("Внесите данные в .env файл для подключения к POSTGRESQL")
        sys.exit(1)

    if not config['host']:
        config['host'] = 'localhost'  # Поле по умолчанию
    if not config['port']:
        config['port'] = '5432'

    return config


def get_db_connection(config):
    """Устанавливает соединение с PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Ошибка подключения к БД: {e}")
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"Ошибка PostgreSQL: {e}")
        sys.exit(1)


def has_dangerous_words(sql):
    """Проверяет наличие запрещенных команд в запросе."""
    sql_clean = re.sub(r"'[^']*'", '', sql)
    sql_clean = re.sub(r'"[^"]*"', '', sql_clean)
    for command in FORBIDDEN_COMMANDS:
        if re.search(rf'\b{command}\b', sql_clean, re.IGNORECASE):
            return True
    return False


def is_select_query(sql):
    """Проверяет, является ли запрос SELECT."""
    # Удаляем лишние комментарии из программы
    sql_clean = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
    sql_clean = sql_clean.strip()
    if not sql_clean:
        return False
    # Проверяем на множественные запросы в одной строке
    if sql_clean.count(';') > 1:
        return False
    # Проверяем, что запрос начинается с select
    if not re.match(r'^SELECT\s+', sql_clean, re.IGNORECASE):
        return False

    # Проверяем на запрещенные слова
    if has_dangerous_words(sql_clean):
        return False
    return True


def has_limit(sql):
    """Проверяет, есть ли в запросе LIMIT."""
    # Удаляем комментарии и пробелы из программы
    sql_clean = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
    if re.search(r'\bLIMIT\s+\d+\b', sql_clean, re.IGNORECASE):
        return True
    return False


def add_limit(sql, limit=5):
    """Добавляет LIMIT к запросу, если его нет."""
    return f"{sql.rstrip(';')} LIMIT {limit};"


def execute_query(conn, sql):
    """Выполняет SQL-запрос и вызывает печать таблицы"""
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            # Имена колонок
            columns = [desc[0] for desc in cur.description] if cur.description else []

            if not rows:
                print("Запрос выполнен успешно, но не вернул данных.")
                return
            print_table(rows, columns)

    except psycopg2.ProgrammingError as e:
        print(f"Ошибка синтаксиса SQL: {e}")
    except psycopg2.Error as e:
        print(f"Ошибка выполнения запроса: {e}")
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")


def print_table(rows, columns):
    """Выводит данные в виде таблицы с форматированием"""
    if not rows or not columns:
        return

    # Вычисляем максимальную ширину колонки
    col_widths = []
    for i, col in enumerate(columns):
        max_width = len(col)
        for row in rows:
            if i < len(row):
                val = str(row[i]) if row[i] is not None else 'NULL'
                max_width = max(max_width, len(val))
        col_widths.append(min(max_width, 50))

    # Вывод информации, где у всех колонок одинаковая ширина
    str_sep = '+' + '+'.join(['-' * (width + 2) for width in col_widths]) + '+'
    header = '|' + '|'.join([f' {columns[i]:<{col_widths[i]}} ' for i in range(len(columns))]) + '|'
    print(str_sep)
    print(header)
    print(str_sep)

    # Таблица с данными
    for row in rows:
        row_str = '|'
        for i, val in enumerate(row):
            if i < len(col_widths):
                val_str = str(val) if val is not None else 'NULL'
                row_str += f' {val_str:<{col_widths[i]}} |'
        print(row_str)

    print(str_sep)
    print(f"Всего строк: {len(rows)}")


def main():
    """Основная функция программы."""
    config = load_config()
    conn = get_db_connection(config)

    try:
        # Запрос пользователя
        sql = input("Введите SQL-запрос: ").strip()
        if not sql:
            print("Ошибка: Запрос не может быть пустым!")
            sys.exit(1)

        # Проверка, что запрос - SELECT
        if not is_select_query(sql):
            print("Ошибка: разрешены только SELECT-запросы")
            sys.exit(1)
        if not has_limit(sql):
            sql = add_limit(sql)
            print("Добавлен LIMIT 5 в конец запроса")
        execute_query(conn, sql)

    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем")
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
    finally:
        try:
            conn.close()
        except:
            pass


if __name__ == "__main__":
    main()
