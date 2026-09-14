"""Создаёт Excel для знакомства с импортом: python scripts/make_example.py."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from calculations import normalize_rows  # noqa: E402
from excel_io import write_excel  # noqa: E402


def main():
    payload = json.loads((ROOT / "examples/products.json").read_text(encoding="utf-8"))
    rate, rows = normalize_rows(payload)
    output = ROOT / ".local" / "examples"
    output.mkdir(parents=True, exist_ok=True)
    path = output / "products.xlsx"
    write_excel(path, rate, rows)
    print(path)


if __name__ == "__main__":
    main()
