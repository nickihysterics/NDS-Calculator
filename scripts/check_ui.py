"""Проверка браузерного интерфейса; --screenshots обновляет иллюстрации README."""

import argparse
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--screenshots", action="store_true")
    args = parser.parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1050}, reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((ROOT / "src/ui/index.html").as_uri())
        expect(page.locator("#exportExcel")).to_be_disabled()
        page.get_by_role("button", name="Загрузить пример").click()
        expect(page.locator(".table__row")).to_have_count(3)
        expect(page.locator("#sumGross")).to_have_text("4\u00a0209,00 ₽")
        expect(page.locator("#sumVat")).to_have_text("759,00 ₽")
        if args.screenshots:
            page.screenshot(path=str(ROOT / "docs/screenshots/table.png"), full_page=True)
        page.locator(".field--net").first.fill("100")
        expect(page.locator(".field--gross").first).to_have_value("122,00")
        page.locator(".field--qty").first.fill("2")
        expect(page.locator("#sumGross")).to_have_text("2\u00a0318,00 ₽")
        page.get_by_role("tab", name="Настройки").click()
        page.locator("#vatRate").fill("10")
        expect(page.locator("#vatRateBadge")).to_have_text("10,00%")
        page.locator("#buyerOrg").fill("ООО «Учебный покупатель»")
        page.locator("#sellerOrg").fill("ООО «Демо-поставщик»")
        page.locator("#specLine").fill("Спецификация № 1 от __DATE__ г.")
        page.locator("#specDate").fill("14.09.2026")
        if args.screenshots:
            page.evaluate("window.scrollTo(0, 0)")
            page.screenshot(path=str(ROOT / "docs/screenshots/settings.png"), full_page=False)
        page.get_by_role("tab", name="Таблица", exact=True).click()
        expect(page.locator(".field--gross").first).to_have_value("110,00")
        page.locator(".field--qty").first.fill("0")
        expect(page.locator(".has-error")).to_have_count(1)
        page.locator(".field--qty").first.fill("1")
        expect(page.locator(".has-error")).to_have_count(0)
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.get_by_role("button", name="Очистить таблицу").click()
        expect(page.locator(".table__row")).to_have_count(3)
        page.once("dialog", lambda dialog: dialog.accept())
        page.get_by_role("button", name="Очистить таблицу").click()
        expect(page.locator(".table__row")).to_have_count(1)
        page.get_by_role("button", name="Загрузить пример").click()
        for width in (390, 900, 1440):
            page.set_viewport_size({"width": width, "height": 1050})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), width
        assert not errors, errors
        browser.close()
    print("UI OK: demo, editing, rate, quantity, validation, clear confirmation, 390/900/1440 px")


if __name__ == "__main__":
    main()
