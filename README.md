# SQL_SELECT_parser
Python-скрипт для безопасного выполнения SQL-запросов к PostgreSQL.
Проверяет наличие только запроса SELECT, добавляет LIMIT 5 в конец при отсутствии и обрабатывает исключения при ошибках.
Получает данные из базы данных при успешном запросе и выводит данные на экран в удобной табличной форме.
## Требования
* Python 3.10+
* PostgreSQL
  
## Иcпользование скрипта
### 1. Клонирование репозитория
```bash
git clone https://github.com/Dmitry-sorokin57/SQL_SELECT_parser.git
cd SQL_SELECT_parser
```
### 2. Установка зависимостей
   ```bash
   pip install -r requirements.txt
   ```
### 3. Настройка подключения к PostgreSQL
   Скопировать .env.example в .env и указать параметры:
   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password
```
### 4. Запуск скрипта
   ```python main.py```

## Ввод данных
Программа попросит ввести запрос:
```bash
Введите SQL-запрос:
SELECT * FROM students
```
и выведет на экран таблицу:
```bash
| id | name    | age | score |
+----+---------+-----+-------+
| 1  | Dima    | 18  | 73    |
| 2  | Egor    | 20  | 98    |
| 3  | Max     | 19  | 45    |
| 4  | Gevorg  | 21  | 68    |
| 5  | Natalya | 22  | 89    |
+----+---------+-----+-------+
Всего строк: 5
```
