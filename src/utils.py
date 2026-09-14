"""Утилиты для нормализации данных, чисел и расчета НДС."""

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from constants import HEADER_SYNONYMS


def normalize_header(value):
    """Нормализует значение заголовка для поиска совпадений."""
    if value is None:
        return ""
    text = str(value).strip().lower().replace("ё", "е")
    text = re.sub(r"(руб\.?|рублей|рубль|rur|rub|₽)", "", text)
    return re.sub(r"[^a-z0-9а-я]+", "", text)


def build_synonym_index():
    """Строит индекс синонимов заголовков по убыванию длины."""
    index = []
    for field, synonyms in HEADER_SYNONYMS.items():
        for synonym in synonyms:
            norm = normalize_header(synonym)
            if norm:
                index.append((norm, field))
    index.sort(key=lambda item: len(item[0]), reverse=True)
    return index


SYNONYM_INDEX = build_synonym_index()


def match_field(header):
    """Определяет внутреннее имя поля по заголовку Excel."""
    normalized = normalize_header(header)
    if not normalized:
        return None
    for synonym, field in SYNONYM_INDEX:
        if synonym and synonym in normalized:
            return field
    return None


def parse_decimal(value):
    """Преобразует значение в Decimal, поддерживая пробелы и запятые."""
    if value is None:
        return None
    cleaned = "".join(str(value).split()).replace(",", ".")
    if not cleaned:
        return None
    try:
        result = Decimal(cleaned)
        return result if result.is_finite() else None
    except InvalidOperation:
        return None


def quantize_money(value):
    """Округляет Decimal до 2 знаков по стандарту HALF_UP."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_decimal(value):
    """Форматирует Decimal в строку с пробелами и запятой."""
    if value is None:
        return ""
    quantized = quantize_money(value)
    sign = "-" if quantized < 0 else ""
    quantized = abs(quantized)
    raw = f"{quantized:.2f}"
    int_part, frac_part = raw.split(".")
    int_grouped = f"{int(int_part):,}".replace(",", " ")
    return f"{sign}{int_grouped},{frac_part}"


def format_quantity(value):
    """Форматирует количество с до 3 знаков после запятой."""
    if value is None:
        return ""
    if value == value.to_integral():
        return str(int(value))
    quantized = value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    return f"{quantized}".replace(".", ",")


def decimal_to_float(value):
    """Преобразует Decimal в float, если значение задано."""
    return float(value) if value is not None else None


def calc_vat_included(gross, vat_rate):
    """Считает НДС внутри цены: gross * rate / (100 + rate)."""
    if gross is None or vat_rate is None:
        return None
    denominator = Decimal("100") + vat_rate
    if denominator == 0:
        return None
    return gross * vat_rate / denominator
