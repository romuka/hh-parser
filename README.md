# HH.ru vacancy parser — аналитика рынка труда

Парсер вакансий с hh.ru с загрузкой данных в ClickHouse и визуализацией в Jupyter.

## Что делает проект

- Собирает вакансии по запросу с hh.ru за последние 2 недели
- Извлекает навыки из описаний вакансий
- Загружает данные в ClickHouse
- Строит аналитические дашборды в Jupyter

## Стек

- **Python** — requests, BeautifulSoup, pandas, tqdm
- **ClickHouse** — хранение и аналитические запросы
- **Docker** — запуск ClickHouse локально
- **Jupyter + matplotlib** — визуализация

## Результаты анализа (790 вакансий, Москва, май 2026)

Топ навыков которые требуют работодатели:

| Навык | Вакансий |
|-------|----------|
| SQL | 408 |
| Excel | 295 |
| Python | 233 |
| 1С | 124 |
| API | 115 |
| Power BI | 99 |
| PostgreSQL | 82 |
| ClickHouse | 54 |

## Как запустить

### 1. Клонируй репозиторий
```bash
git clone https://github.com/твой_ник/hh_parser.git
cd hh_parser
```

### 2. Создай виртуальное окружение
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Запусти ClickHouse в Docker
```bash
docker run -d --name clickhouse-hh \
  -p 8123:8123 -p 9000:9000 \
  -e CLICKHOUSE_PASSWORD=admin \
  clickhouse/clickhouse-server
```

### 4. Запусти парсер
```bash
python parser.py
```

### 5. Загрузи данные в ClickHouse
```bash
python clickhouse_loader.py
```

### 6. Открой аналитику
```bash
jupyter notebook
```

Открой `analysis.ipynb` и запусти все ячейки.

## Структура проекта

```
hh_parser/
├── parser.py             # сбор вакансий с hh.ru
├── clickhouse_loader.py  # загрузка в ClickHouse
├── analysis.ipynb        # визуализация и аналитика
├── data/
│   ├── vacancies.csv     # собранные вакансии
│   └── skills_top.csv    # топ навыков
└── requirements.txt      # зависимости
```