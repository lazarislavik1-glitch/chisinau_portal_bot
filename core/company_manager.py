# core/company_manager.py

import json
import os
from typing import List, Dict, Any

from config import COMPANIES_FILE

# Структура файла:
# {
#   "sub_code": [
#       {
#           "name": "...",
#           "activity": "...",
#           "advantages": "...",
#           "address": "...",
#           "contacts": "...",
#           "photos": ["file_id1", "file_id2", ...]
#       },
#       ...
#   ],
#   ...
# }


def _ensure_file_exists() -> None:
    """Если файла ещё нет – создаём пустой JSON."""
    if not os.path.exists(COMPANIES_FILE):
        with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)


def load_companies() -> Dict[str, List[Dict[str, Any]]]:
    """Загрузка всех компаний из файла."""
    _ensure_file_exists()
    try:
        with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except json.JSONDecodeError:
        # Если файл повреждён – перезаписываем пустым
        return {}


def save_companies(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Сохранение словаря компаний в файл."""
    with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_companies_by_subcategory(sub_code: str) -> List[Dict[str, Any]]:
    """Получить все компании по коду подкатегории."""
    data = load_companies()
    return data.get(sub_code, [])


def add_company(
    sub_code: str,
    name: str,
    activity: str,
    advantages: str,
    address: str,
    contacts: str,
    photos: List[str] | None = None
) -> None:
    """Добавить новую компанию в указанную подкатегорию."""
    data = load_companies()

    company = {
        "name": name,
        "activity": activity,
        "advantages": advantages,
        "address": address,
        "contacts": contacts,
        "photos": photos or []
    }

    if sub_code not in data:
        data[sub_code] = []

    data[sub_code].append(company)
    save_companies(data)


def delete_company(sub_code: str, index: int) -> bool:
    """
    Удалить компанию по индексу в подкатегории.
    Возвращает True, если удалили успешно.
    """
    data = load_companies()
    companies = data.get(sub_code, [])

    if 0 <= index < len(companies):
        companies.pop(index)
        if companies:
            data[sub_code] = companies
        else:
            # Если подкатегория опустела – удаляем ключ
            data.pop(sub_code, None)
        save_companies(data)
        return True

    return False
