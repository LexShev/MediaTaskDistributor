"""Нормализация строковых полей для сопоставления.

Каталог Кинопоиска и Oplan3 заполнялись независимо, поэтому порядок стран и
режиссёров может отличаться, названия содержат маркеры сезонов/серий, а год
может обозначать либо год производства, либо год премьеры (расходится на +-1).
Все сравнения выполняются над нормализованными значениями.
"""

import re

# --- Регулярные выражения --------------------------------------------------
_PUNCT_RE = re.compile(r'[^\w\s]', re.UNICODE)
_WS_RE = re.compile(r'\s+', re.UNICODE)

# Маркеры сезон/серия/эпизод/часть, после которых начинается нумерация, а не
# часть оригинального названия.
_SEASON_MARKER_RE = re.compile(
    r'\b(сезон\w*|сер(?:ия|ии|ий)\w*|эпизод\w*|эп\.?|part|season)\b',
    re.IGNORECASE,
)
_TRAILING_NUM_RE = re.compile(r'[№#]\s*\d+\s*$')
# Порядковые номера сезонов/серий вида "3-й", "2-я", "1-е".
_ORDINAL_RE = re.compile(r'\b\d+\s*[-–—]\s*[а-яё]{1,2}\b', re.IGNORECASE)
_YEAR_RE = re.compile(r'(\d{4})')

_ROMAN_TO_ARABIC = {
    'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5',
    'vi': '6', 'vii': '7', 'viii': '8', 'ix': '9', 'x': '10',
    'xi': '11', 'xii': '12', 'xiii': '13', 'xiv': '14', 'xv': '15',
}

# Короткие/служебные токены, бесполезные для блокировки кандидатов.
_STOP_TOKENS = {'the', 'a', 'of', 'and', 'и', 'в', 'на', 'с', 'по', 'из', 'не', 'или'}

# Канонизация стран: ключ -> каноническое имя.
_COUNTRY_SYNONYMS = {
    'сша': 'сша',
    'соединенные штаты': 'сша',
    'соединенные штаты америки': 'сша',
    'америка': 'сша',
    'великобритания': 'великобритания',
    'англия': 'великобритания',
    'соединенное королевство': 'великобритания',
    'россия': 'россия',
    'рф': 'россия',
    'ссср': 'ссср',
    'советский союз': 'ссср',
    'южная корея': 'южная корея',
    'корея южная': 'южная корея',
    'северная корея': 'северная корея',
    'корея северная': 'северная корея',
    'фрг': 'германия',
    'гдр': 'германия',
}


def _to_text(value) -> str:
    if value is None:
        return ''
    return str(value)


def normalize_title(value) -> str:
    """Приводит название к сопоставимому виду."""
    text = _to_text(value).lower()
    text = text.replace('ё', 'е')
    # Убираем кавычки-апострофы до общей чистки, чтобы не склеивать слова.
    text = re.sub(r"[`'’ʼ\"]", '', text)
    # Отрезаем хвост начиная с маркера сезона/серии/эпизода.
    match = _SEASON_MARKER_RE.search(text)
    if match:
        head = text[:match.start()].strip()
        # Номер перед маркером ("... 8 сезон", "... №3 серия").
        head = re.sub(r'\s*[№#]?\s*\d+\s*$', '', head).strip()
        if head:
            text = head
    text = _TRAILING_NUM_RE.sub('', text)
    text = _ORDINAL_RE.sub(' ', text)
    text = _PUNCT_RE.sub(' ', text)
    text = _WS_RE.sub(' ', text).strip()

    # Унифицируем римские цифры-нумерацию в конце названия.
    tokens = text.split()
    if tokens and tokens[-1] in _ROMAN_TO_ARABIC:
        tokens[-1] = _ROMAN_TO_ARABIC[tokens[-1]]
    return ' '.join(tokens)


def significant_tokens(normalized_title: str) -> list:
    """Токены названия для блокировки кандидатов (без коротких и служебных)."""
    return [
        token for token in normalized_title.split()
        if len(token) > 2 and token not in _STOP_TOKENS
    ]


def normalize_countries(value) -> set:
    """Приводит страны к множеству канонических названий (порядок не важен)."""
    if value is None:
        return set()
    if isinstance(value, (list, tuple, set)):
        parts = [str(item) for item in value]
    else:
        parts = re.split(r'[,;/]', _to_text(value))

    result = set()
    for part in parts:
        country = _WS_RE.sub(' ', _to_text(part).lower().replace('ё', 'е')).strip()
        if not country:
            continue
        country = _PUNCT_RE.sub(' ', country).strip()
        result.add(_COUNTRY_SYNONYMS.get(country, country))
    return result


def normalize_persons(value) -> set:
    """Множество токенов ФИО персон (порядок и формат не важны)."""
    return person_tokens(director_names(value))


def person_tokens(names) -> set:
    """Токены ФИО из списка нормализованных имён."""
    tokens = set()
    for name in names:
        tokens.update(token for token in name.split() if len(token) > 1)
    return tokens


def clean_year(value):
    """Извлекает год из числа/строки. Диапазоны '2019-2020' -> 2019."""
    text = _to_text(value)
    match = _YEAR_RE.search(text)
    if not match:
        return None
    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return None


def parse_years(value) -> set:
    """Все годы из строки/числа. Диапазон '1968 - 1971' -> {1968, 1971}."""
    years = set()
    for match in _YEAR_RE.finditer(_to_text(value)):
        try:
            years.add(int(match.group(1)))
        except (TypeError, ValueError):
            continue
    return years


def director_names(value) -> list:
    """Нормализованные полные ФИО режиссёров (порядок сохраняется)."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        parts = [str(item) for item in value]
    else:
        parts = re.split(r'[,;]', _to_text(value))

    names = []
    for part in parts:
        text = _to_text(part).lower().replace('ё', 'е')
        text = _PUNCT_RE.sub(' ', text)
        text = _WS_RE.sub(' ', text).strip()
        if text:
            names.append(text)
    return names


def parse_kinopoisk_id(value):
    """kinopoisk_id приходит из Mongo строкой; нечисловые отбрасываем."""
    text = _to_text(value).strip()
    if text.isdigit():
        return int(text)
    return None


def years_match(query_year, candidate_year) -> bool:
    if query_year is None or candidate_year is None:
        return False
    return abs(query_year - candidate_year) <= 1
