import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import time
from datetime import datetime


def clean_text(text):
    """Очистка текста от спецсимволов"""
    if not text:
        return ""
    return text.replace('"', "'").replace('\n', ' ').strip()


def parse_ria_date(date_str):
    """Парсинг даты формата RIA ('10 февраля 2025')"""
    months = {
        'января': 1, 'февраля': 2, 'марта': 3,
        'апреля': 4, 'мая': 5, 'июня': 6,
        'июля': 7, 'августа': 8, 'сентября': 9,
        'октября': 10, 'ноября': 11, 'декабря': 12
    }
    try:
        parts = date_str.split()
        if len(parts) == 3:
            day, month, year = parts
            return datetime(int(year), months.get(month, 1), int(day))
    except:
        return None
    return None


def parse_news():
    """Основная функция парсинга"""
    url = "https://ria.ru/science/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    result = {
        'data': [],
        'total_count': 0,
        'timestamp': time.time(),
        'status': False
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        news_cards = soup.find_all('div', class_='list-item')[:15]  # Лимит 15 новостей

        for card in news_cards:
            try:
                # Проверка даты
                date_elem = card.find('div', class_='list-item__date')
                news_date = parse_ria_date(date_elem.get_text(strip=True)) if date_elem else None

                if news_date and (news_date.year != 2025 or news_date.month != 2):
                    continue

                # Извлечение данных
                title_elem = card.find('a', class_='list-item__title')
                if not title_elem:
                    continue

                item = {
                    'title': clean_text(title_elem.get_text()),
                    'link': urljoin(url, title_elem.get('href', '')),
                    'date': date_elem.get_text(strip=True) if date_elem else "",
                    'text': clean_text(card.find('div', class_='list-item__content').get_text()[:300])
                    if card.find('div', class_='list-item__content') else ""
                }
                result['data'].append(item)

            except Exception as e:
                print(f"[Ошибка карточки] {str(e)}")
                continue

        result['total_count'] = len(result['data'])
        result['status'] = True

    except requests.RequestException as e:
        print(f"[Ошибка сети] {str(e)}")
    except Exception as e:
        print(f"[Критическая ошибка] {str(e)}")

    # Сохранение результатов
    with open('news_february.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result['status'], result['total_count']


if __name__ == "__main__":
    print("=== Запуск парсера ===")
    success, count = parse_news()
    status = "успешно" if success else "с ошибками"
    print(f"Парсинг завершён {status}. Обработано новостей: {count}")