"""Расчёт спецификации без зависимости от Qt и файловой системы.

Цена-источник округляется до копеек, затем вычисляется вторая цена.
Суммы строки считаются от округлённых цен и количества. Все операции
используют Decimal и ROUND_HALF_UP; входные итоги никогда не считаются доверенными.
"""

from decimal import ROUND_HALF_UP, Decimal

from constants import DEFAULT_VAT_RATE
from utils import parse_decimal, quantize_money

MAX_PRICE = Decimal("1000000000")
MAX_QUANTITY = Decimal("1000000")
MAX_ROWS = 1000
# Удерживаем суммы в диапазоне, где Excel сохраняет копейки (15 значащих цифр).
MAX_TOTAL = Decimal("1000000000000")


def number(value, label, maximum, default=None):
    """Разбирает ограниченное неотрицательное число или выдаёт понятную ошибку."""
    if value is None or str(value).strip() == "":
        return default
    parsed = parse_decimal(value)
    if parsed is None or not 0 <= parsed <= maximum:
        raise ValueError(f"{label}: введите число от 0 до {maximum}.")
    return parsed


def normalize_rows(data):
    """Возвращает ставку и строки с согласованными ценами, количеством и суммами."""
    if not isinstance(data, dict) or not isinstance(data.get("rows"), list):
        raise ValueError("Ожидается объект со списком rows.")
    raw_rows = data["rows"]
    if len(raw_rows) > MAX_ROWS:
        raise ValueError(f"Допускается не более {MAX_ROWS} строк.")
    rate = number(data.get("vatRate"), "Ставка НДС", Decimal(100), DEFAULT_VAT_RATE)
    rate = rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    factor = 1 + rate / 100
    rows = []
    for index, raw in enumerate(raw_rows, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"Строка {index}: ожидается объект.")
        name = str(raw.get("name") or "").strip()
        if not name and all(
            raw.get(key) in (None, "") for key in ("net", "gross", "sum_net", "sum_gross")
        ):
            continue
        if not name:
            raise ValueError(f"Строка {index}: укажите наименование товара.")
        qty = number(raw.get("qty"), f"Строка {index}, количество", MAX_QUANTITY, Decimal(1))
        qty = qty.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        if qty <= 0:
            raise ValueError(f"Строка {index}: количество должно быть не меньше 0,001.")
        net = number(raw.get("net"), f"Строка {index}, цена без НДС", MAX_PRICE)
        gross = number(raw.get("gross"), f"Строка {index}, цена с НДС", MAX_PRICE)
        # Таблицы, в которых указана только сумма, тоже можно импортировать.
        if net is None and gross is None:
            sum_gross = number(raw.get("sum_gross"), "Сумма с НДС", MAX_PRICE * MAX_QUANTITY)
            sum_net = number(raw.get("sum_net"), "Сумма без НДС", MAX_PRICE * MAX_QUANTITY)
            if sum_gross is not None:
                gross = sum_gross / qty
            elif sum_net is not None:
                net = sum_net / qty
        source = raw.get("source", "gross")
        if net is not None and (source == "net" or gross is None):
            net = quantize_money(net)
            gross = quantize_money(net * factor)
            source = "net"
        elif gross is not None:
            gross = quantize_money(gross)
            net = quantize_money(gross / factor)
            source = "gross"
        else:
            raise ValueError(f"Строка {index}: укажите цену с НДС или без НДС.")
        if max(net, gross) > MAX_PRICE:
            raise ValueError(f"Строка {index}: цена превышает {MAX_PRICE}.")
        sum_net = quantize_money(net * qty)
        sum_gross = quantize_money(gross * qty)
        rows.append(
            {
                "name": name,
                "net": net,
                "gross": gross,
                "vat": gross - net,
                "qty": qty,
                "unit": str(raw.get("unit") or "шт").strip(),
                "gost": str(raw.get("gost") or "").strip(),
                "sum_net": sum_net,
                "sum_gross": sum_gross,
                "sum_vat": sum_gross - sum_net,
                "source": source,
            }
        )
    if sum((row["sum_gross"] for row in rows), Decimal(0)) > MAX_TOTAL:
        raise ValueError("Общая сумма с НДС не должна превышать 1 000 000 000 000 рублей.")
    return rate, rows
