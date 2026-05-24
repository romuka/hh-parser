import clickhouse_connect
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
# Подключаемся к ClickHouse
client = clickhouse_connect.get_client(
    host="localhost",
    port=8123,
    username="default",
    password=os.getenv("CLICKHOUSE_PASSWORD")
)

# Создаём базу данных для нашего проекта
# IF NOT EXISTS — не выдаёт ошибку если база уже существует
# Удаляем и создаём таблицу заново с актуальной схемой
client.command("DROP TABLE IF EXISTS hh.vacancies")
client.command("""
    CREATE TABLE hh.vacancies (
        title           String,
        company         String,
        salary          String,
        link            String,
        experience      String,
        grade           String,
        remote          String,
        metro           String,
        query           String,
        skills_found    String,
        published_date  String
    )
    ENGINE = MergeTree()
    ORDER BY title
""")
print("Таблица пересоздана")
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