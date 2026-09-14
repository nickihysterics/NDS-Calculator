import json
from decimal import Decimal
from pathlib import Path

import pytest

from calculations import normalize_rows
from utils import format_decimal, match_field, parse_decimal

CASES = json.loads(Path(__file__).with_name("calculation_cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_shared_rounding_contract(case):
    _, rows = normalize_rows({"vatRate": case["rate"], "rows": [{"name": "Пример", **case["raw"]}]})
    row = rows[0]
    assert [str(row[key]) for key in ("net", "gross", "vat", "sum_net", "sum_gross")] == case[
        "expected"
    ]
    assert row["net"] + row["vat"] == row["gross"]
    assert row["sum_net"] + row["sum_vat"] == row["sum_gross"]


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", "garbage", "1,2,3"])
def test_invalid_numbers(value):
    assert parse_decimal(value) is None
    with pytest.raises(ValueError):
        normalize_rows({"rows": [{"name": "Товар", "gross": value}]})


@pytest.mark.parametrize(
    "raw",
    [
        {"qty": "0"},
        {"qty": "-1"},
        {"qty": "0.0001"},
        {"gross": "-5"},
        {"gross": "1000000001"},
        {"name": ""},
    ],
)
def test_invalid_rows(raw):
    with pytest.raises(ValueError):
        normalize_rows({"rows": [{"name": "Товар", "gross": "122", **raw}]})


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"rows": "bad"},
        {"rows": [None]},
        {"rows": [{}] * 1001},
        {"rows": [], "vatRate": "-100"},
        {"rows": [], "vatRate": "101"},
    ],
)
def test_payload_validation(payload):
    with pytest.raises(ValueError):
        normalize_rows(payload)


def test_totals_are_recalculated_after_edit():
    _, rows = normalize_rows(
        {
            "vatRate": "22",
            "rows": [
                {
                    "name": "Товар",
                    "net": "100",
                    "gross": "999",
                    "source": "net",
                    "qty": "3",
                    "sum_net": "5",
                    "sum_gross": "6",
                }
            ],
        }
    )
    assert rows[0]["sum_gross"] == Decimal("366.00")
    assert rows[0]["sum_net"] == Decimal("300.00")


def test_sum_only_import():
    _, rows = normalize_rows({"rows": [{"name": "Товар", "qty": "2", "sum_gross": "244"}]})
    assert rows[0]["net"] == Decimal("100.00")
    assert rows[0]["sum_gross"] == Decimal("244.00")


def test_empty_row_and_default_quantity():
    rate, rows = normalize_rows({"rows": [{}, {"name": "Товар", "gross": "122"}]})
    assert rate == 22
    assert len(rows) == 1
    assert rows[0]["qty"] == 1


def test_russian_format_and_headers():
    assert format_decimal(parse_decimal("1\u202f234,565")) == "1 234,57"
    assert match_field("Общая стоимость товара с НДС, руб.") == "sum_gross"
    assert match_field("Цена без НДС, руб.") == "net"
    assert match_field("Количество") == "qty"


def test_document_total_limit_protects_excel_precision():
    with pytest.raises(ValueError, match="Общая сумма"):
        normalize_rows({"rows": [{"name": "Товар", "gross": "1000000000", "qty": "1001"}]})
