from datetime import datetime, timezone
from types import SimpleNamespace

from openpyxl import load_workbook

from app.routes.reports import export_content_disposition
from app.services.excel_export import build_batch_workbook


def test_export_content_disposition_supports_cyrillic_filename() -> None:
    header = export_content_disposition("report_Выхино-Жулебино_20260514_1454.xlsx")

    header.encode("latin-1")
    assert 'filename="report_-_20260514_1454.xlsx"' in header
    assert "filename*=UTF-8''report_%D0%92%D1%8B%D1%85%D0%B8%D0%BD%D0%BE" in header


def test_batch_workbook_combines_districts_in_one_table() -> None:
    repost_date = datetime(2026, 5, 31, tzinfo=timezone.utc)
    resource = SimpleNamespace(
        category_name="личная страница ЛОМа",
        display_name="Тестовый ресурс",
    )

    def report(network_name: str, repost_url: str) -> SimpleNamespace:
        row = SimpleNamespace(
            repost_date=repost_date,
            resource=resource,
            repost_url=repost_url,
            followers_count=10,
            views_count=5,
        )
        return SimpleNamespace(
            network=SimpleNamespace(name=network_name),
            rows=[row],
            infopovod_title="Тест",
            source_url="https://vk.com/wall-1_2",
        )

    workbook = load_workbook(
        build_batch_workbook(
            [
                report("Капотня", "https://vk.com/wall1_1"),
                report("Кузьминки", "https://vk.com/wall2_2"),
            ]
        )
    )
    sheet = workbook.active

    assert sheet["G3"].value == "Район"
    assert sheet["A4"].value == 1
    assert sheet["G4"].value == "Капотня"
    assert sheet["A5"].value == 2
    assert sheet["G5"].value == "Кузьминки"
