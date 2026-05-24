import requests
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

def parse_sections(soup):
    description_tag = soup.find("div", {"data-qa": "vacancy-description"})
    if not description_tag:
        return {}, ""

    sections = {}
    current_section = "other"
    current_text = []

    for element in description_tag.children:
        if element.name == "p":
            strong = element.find("strong")
            if strong and len(element.text.strip()) < 100:
                if current_text:
                    sections[current_section] = " ".join(current_text).strip()
                current_section = strong.text.strip().lower()
                current_text = []
        elif element.name == "ul":
            for li in element.find_all("li"):
                current_text.append(li.text.strip())

    if current_text:
        sections[current_section] = " ".join(current_text).strip()

    full_text = description_tag.text.lower()
    return sections, full_text

def collect_vacancy_cards():
    date_from = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

    QUERIES = [
        "аналитик данных",
        "data analyst",
        "аналитик BI",
        "python аналитик",
    ]

    all_results = []

    for query in QUERIES:
        print(f"\n=== Собираем: {query} ===")
        page = 0
        query_results = []

        while True:
            url = f"https://hh.ru/search/vacancy?text={query}&area=1&date_from={date_from}&page={page}"
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            vacancies = soup.find_all("div", {"class": "vacancy-info--ieHKDTkezpEj0Gsx"})

            if not vacancies:
                print(f"Страниц собрано: {page}. Завершаем.")
                break

            for vacancy in vacancies:
                title_tag = vacancy.find("a", {"data-qa": "serp-item__title"})
                title = title_tag.text.strip() if title_tag else "Не указано"
                link = title_tag["href"].split("?")[0] if title_tag else None

                company_tag = vacancy.find("span", {"data-qa": "vacancy-serp__vacancy-employer-text"})
                company = company_tag.text.strip() if company_tag else "Не указано"

                salary_tag = vacancy.find("span", {"data-qa": "vacancy-serp__vacancy-compensation"})
                salary = salary_tag.text.strip() if salary_tag else "Не указана"

                experience_tag = vacancy.find("span", {"data-qa": lambda x: x and x.startswith("vacancy-serp__vacancy-work-experience")})
                experience = experience_tag.text.strip() if experience_tag else "Не указан"

                remote_tag = vacancy.find("span", {"data-qa": "vacancy-label-work-schedule-remote"})
                remote = "Да" if remote_tag else "Нет"

                metro_tags = vacancy.find_all("span", {"data-qa": "address-metro-station-name"})
                metro = ", ".join([m.text.strip() for m in metro_tags if m.text.strip()]) if metro_tags else "Не указано"

                title_lower = title.lower()
                if "junior" in title_lower or "младший" in title_lower:
                    grade = "junior"
                elif "lead" in title_lower or "лид" in title_lower:
                    grade = "lead"
                elif "senior" in title_lower or "старший" in title_lower:
                    grade = "senior"
                elif "middle" in title_lower:
                    grade = "middle"
                else:
                    grade = "не указан"

                # skills и published_date пока пустые — заполним в parse_skills
                query_results.append({
                    "title": title,
                    "company": company,
                    "salary": salary,
                    "link": link,
                    "experience": experience,
                    "grade": grade,
                    "remote": remote,
                    "metro": metro,
                    "query": query
                })

            print(f"Страница {page + 1} — карточек: {len(vacancies)}, всего по запросу: {len(query_results)}")
            page += 1
            time.sleep(2)

        all_results.extend(query_results)
        print(f"Итого по запросу '{query}': {len(query_results)}")

    return all_results

def parse_skills(links):
    results = []
    for link in tqdm(links, desc="Парсим навыки"):
        try:
            response = requests.get(link, headers=headers, timeout=10)
            vac_soup = BeautifulSoup(response.text, "html.parser")

            # Парсим секции
            sections, full_text = parse_sections(vac_soup)

            # Ищем навыки только в секции требований
            requirements_text = next(
                (v for k, v in sections.items()
                 if any(w in k for w in ["ожидани", "требовани", "ждем", "requirements", "skills"])),
                ""
            ).lower()

            search_text = requirements_text if requirements_text else full_text

            matched = [
                skill for skill in SKILLS_TO_FIND
                if re.search(r'\b' + re.escape(skill) + r'\b', search_text)
            ]
            skills = ", ".join(matched) if matched else "Не найдено"

            # Дата публикации
            published_date = "Не указана"
            for div in vac_soup.find_all("div"):
                if "Вакансия опубликована" in div.text:
                    span = div.find("span")
                    if span:
                        published_date = span.text.strip()
                        break

            results.append({
                "skills": skills,
                "published_date": published_date
            })

        except Exception as e:
            print(f"Ошибка: {e}")
            results.append({
                "skills": "Ошибка",
                "published_date": "Ошибка"
            })

        time.sleep(1.5)

    return results

if __name__ == "__main__":
    print("=== Собираем карточки вакансий ===")
    cards = collect_vacancy_cards()

    df = pd.DataFrame(cards)
    df = df.drop_duplicates(subset="link")
    print(f"\nУникальных вакансий: {len(df)}")

    valid_links = [
        link for link in df["link"].tolist()
        if link and "adsrv" not in link
    ]
    print(f"Вакансий для парсинга навыков: {len(valid_links)}")

    print("\n=== Парсим навыки ===")
    skills_results = parse_skills(valid_links)

    # Сопоставляем результаты с DataFrame
    skills_map = {link: r["skills"] for link, r in zip(valid_links, skills_results)}
    date_map = {link: r["published_date"] for link, r in zip(valid_links, skills_results)}

    df["skills_found"] = df["link"].map(skills_map).fillna("Не указаны")
    df["published_date"] = df["link"].map(date_map).fillna("Не указана")

    # Считаем топ навыков
    all_skills = []
    for skills in df["skills_found"]:
        if pd.notna(skills) and skills not in ("Не найдено", "Не указаны", "Ошибка", ""):
            all_skills.extend([s.strip() for s in skills.split(",")])

    skill_counts = Counter(all_skills)
    skills_df = pd.DataFrame(skill_counts.most_common(), columns=["skill", "count"])

    print("\n--- Топ навыков ---")
    print(skills_df.head(15))

    df.to_csv("data/vacancies.csv", index=False, encoding="utf-8-sig")
    skills_df.to_csv("data/skills_top.csv", index=False, encoding="utf-8-sig")
    print(f"\nГотово! Сохранено {len(df)} вакансий.")