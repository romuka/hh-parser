import clickhouse_connect
import pandas as pd

# Подключаемся к ClickHouse
client = clickhouse_connect.get_client(
    host="localhost",
    port=8123,
    username="default",
    password="admin"
)

# Создаём базу данных для нашего проекта
# IF NOT EXISTS — не выдаёт ошибку если база уже существует
client.command("CREATE DATABASE IF NOT EXISTS hh")

# Создаём таблицу для вакансий
# MergeTree — основной движок ClickHouse для аналитических запросов
# ORDER BY — по какому полю сортируются данные внутри таблицы
client.command("""
    CREATE TABLE IF NOT EXISTS hh.vacancies (
        title       String,       -- название вакансии
        company     String,       -- компания
        salary      String,       -- зарплата (текст, т.к. формат разный)
        link        String,       -- ссылка на вакансию
        skills_found String       -- найденные навыки через запятую
    )
    ENGINE = MergeTree()
    ORDER BY title
""")

print("База и таблица созданы")
client.command("TRUNCATE TABLE hh.vacancies")
print("Таблица очищена")
# Читаем CSV который собрали парсером
df = pd.read_csv("data/vacancies.csv", encoding="utf-8-sig")
print(f"Столбцы в CSV: {df.columns.tolist()}")  # добавь эту строку
df = df.fillna("Не указано")

print(f"Загружаем {len(df)} вакансий...")

# Загружаем DataFrame прямо в таблицу одной командой
# database — в какую базу, table — в какую таблицу
client.insert_df(database="hh", table="vacancies", df=df)

print("Данные загружены!")

# Проверяем что всё попало — считаем количество строк
result = client.query("SELECT count() FROM hh.vacancies")
print(f"Строк в таблице: {result.result_rows[0][0]}")

# Делаем тестовый запрос — топ 5 компаний по количеству вакансий
print("\nТоп 5 компаний по количеству вакансий:")
result = client.query("""
    SELECT company, count() as cnt
    FROM hh.vacancies
    GROUP BY company
    ORDER BY cnt DESC
    LIMIT 5
""")

for row in result.result_rows:
    print(f"  {row[0]} — {row[1]}")