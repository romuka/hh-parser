import asyncio
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
from collections import Counter
from datetime import datetime, timedelta
from tqdm import tqdm
os.makedirs("data", exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

SKILLS_TO_FIND = [
    "python", "sql",
    "r studio", "язык r",
    "postgresql", "clickhouse", "mysql", "mongodb", "oracle",
    "greenplum", "redshift", "trino", "hadoop",
    "power bi", "tableau", "qlik", "superset", "metabase",
    "looker", "datalens",
    "excel", "google sheets", "power query",
    "airflow", "spark", "kafka", "dbt", "git",
    "pandas", "numpy", "scikit", "matplotlib",
    "1с", "битрикс", "jira", "confluence",
    "a/b", "etl", "api", "машинное обучение", "ml"
]

# ---- Шаг 1: собираем карточки со страниц поиска (синхронно) ----
# Страницы поиска идут последовательно — их немного (10-20)
# Асинхронность нужна для парсинга самих вакансий — их сотни

import requests

def collect_vacancy_cards():
    date_from = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    results = []
    page = 0

    while True:
        url = f"https://hh.ru/search/vacancy?text=аналитик+данных&area=1&date_from={date_from}&page={page}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        vacancies = soup.find_all("div", {"class": "vacancy-info--ieHKDTkezpEj0Gsx"})

        if not vacancies:
            print(f"Страниц собрано: {page}. Завершаем сбор карточек.")
            break

        for vacancy in vacancies:
            title_tag = vacancy.find("a", {"data-qa": "serp-item__title"})
            title = title_tag.text.strip() if title_tag else "Не указано"
            link = title_tag["href"] if title_tag else None

            company_tag = vacancy.find("span", {"data-qa": "vacancy-serp__vacancy-employer-text"})
            company = company_tag.text.strip() if company_tag else "Не указано"

            salary_tag = vacancy.find("span", {"data-qa": "vacancy-serp__vacancy-compensation"})
            salary = salary_tag.text.strip() if salary_tag else "Не указана"

            experience_tag = vacancy.find("span", {"data-qa": lambda x: x and x.startswith("vacancy-serp__vacancy-work-experience")})
            experience = experience_tag.text.strip() if experience_tag else "Не указан"

            remote_tag = vacancy.find("span", {"data-qa": "vacancy-label-work-schedule-remote"})
            remote = "Да" if remote_tag else "Нет"

            metro_tags = vacancy.find_all("span", {"data-qa": "address-metro-station-name"})
            metro = ", ".join([m.text.strip() for m in metro_tags]) if metro_tags else "Не указано"

            title_lower = title.lower()
            if "junior" in title_lower or "младший" in title_lower:
                grade = "junior"
            elif "senior" in title_lower or "старший" in title_lower:
                grade = "middle"
            elif "middle" in title_lower or "lead" in title_lower:
                grade = "senior"
            else:
                grade = "не указан"

            results.append({
                "title": title,
                "company": company,
                "salary": salary,
                "link": link,
                "experience": experience,
                "grade": grade,
                "remote": remote,
                "metro": metro
            })

        print(f"Страница {page + 1} — карточек: {len(vacancies)}, всего: {len(results)}")
        page += 1
        time.sleep(2)

    return results

def parse_skills(links):
    results = []
    for link in tqdm(links, desc="Парсим навыки"):
        try:
            response = requests.get(link, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            description_tag = soup.find("div", {"data-qa": "vacancy-description"})
            description = description_tag.text.lower() if description_tag else ""

            matched = [
                skill for skill in SKILLS_TO_FIND
                if re.search(r'\b' + re.escape(skill) + r'\b', description)
            ]
            results.append(", ".join(matched) if matched else "Не найдено")

        except Exception:
            results.append("Ошибка")

        time.sleep(1.5)

    return results

# ---- Главный запуск ----

if __name__ == "__main__":
    # Шаг 1 — собираем карточки
    print("=== Собираем карточки вакансий ===")
    cards = collect_vacancy_cards()

    df = pd.DataFrame(cards)
    df = df.drop_duplicates(subset="link")
    print(f"\nУникальных вакансий: {len(df)}")

    # Фильтруем рекламные ссылки
    valid_links = [
        link for link in df["link"].tolist()
        if link and "adsrv" not in link
    ]
    print(f"Вакансий для парсинга навыков: {len(valid_links)}")

    # Шаг 2 — асинхронно парсим навыки
    print("\n=== Парсим навыки асинхронно ===")
    skills_results = parse_skills(valid_links)

    # Сопоставляем навыки обратно с DataFrame
    skills_map = dict(zip(valid_links, skills_results))
    df["skills_found"] = df["link"].map(skills_map).fillna("Не указаны")

    # Считаем топ навыков
    all_skills = []
    for skills in df["skills_found"]:
        if skills not in ("Не найдено", "Не указаны", "Ошибка"):
            all_skills.extend([s.strip() for s in skills.split(",")])

    from collections import Counter
    skill_counts = Counter(all_skills)
    skills_df = pd.DataFrame(
        skill_counts.most_common(),
        columns=["skill", "count"]
    )

    print("\n--- Топ навыков ---")
    print(skills_df.head(15))

    df.to_csv("data/vacancies.csv", index=False, encoding="utf-8-sig")
    skills_df.to_csv("data/skills_top.csv", index=False, encoding="utf-8-sig")
    print(f"\nГотово! Сохранено {len(df)} вакансий.")