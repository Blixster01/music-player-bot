"""
db.py — простая «БД» для избранных треков.

Хранилище: JSON-файл на диске.
Структура:
{
    "<api_token>": ["mediaId1", "mediaId2", ...],
    ...
}

Использование:
    from db import get_favorites, add_favorite, remove_favorite, set_favorites
"""

import json
import os
from typing import List

DB_PATH = os.getenv("DB_PATH", "favorites.json")


# ── internal helpers ──────────────────────────────────────────────────────────

def _load() -> dict:
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(data: dict) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── public API ────────────────────────────────────────────────────────────────

def get_favorites(token: str) -> List[str]:
    """Вернуть список mediaId для данного токена."""
    return _load().get(token, [])


def set_favorites(token: str, media_ids: List[str]) -> None:
    """Полностью перезаписать список избранного."""
    data = _load()
    data[token] = list(media_ids)
    _save(data)


def add_favorite(token: str, media_id: str) -> List[str]:
    """Добавить трек в избранное. Возвращает актуальный список."""
    data = _load()
    favorites = data.get(token, [])
    if media_id not in favorites:
        favorites.append(media_id)
        data[token] = favorites
        _save(data)
    return favorites


def remove_favorite(token: str, media_id: str) -> List[str]:
    """Удалить трек из избранного. Возвращает актуальный список."""
    data = _load()
    favorites = data.get(token, [])
    if media_id in favorites:
        favorites.remove(media_id)
        data[token] = favorites
        _save(data)
    return favorites


def clear_favorites(token: str) -> None:
    """Очистить всё избранное для токена."""
    data = _load()
    data.pop(token, None)
    _save(data)
