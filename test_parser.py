import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

url = "https://hh.ru/vacancy/133063268"
response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.text, "html.parser")

description_tag = soup.find("div", {"data-qa": "vacancy-description"})
print("Описание найдено:" , description_tag is not None)