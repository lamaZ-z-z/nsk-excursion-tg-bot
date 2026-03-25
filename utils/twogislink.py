'''Module with function that finds 2gis url in message'''
import re

def find_2gis_link(text: str) -> str:
    """
    Находит ссылку на 2gis.ru в тексте.
    Возвращает первую найденную ссылку или None.
    """
    # Паттерн для поиска ссылок 2gis.ru
    pattern = r'https://2gis.ru/novosibirsk/[^\s<>"\'(){}|\\^`\[\]]+'
    try:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    except Exception:
        return None
