from app.routes.reports import export_content_disposition


def test_export_content_disposition_supports_cyrillic_filename() -> None:
    header = export_content_disposition("report_Выхино-Жулебино_20260514_1454.xlsx")

    header.encode("latin-1")
    assert 'filename="report_-_20260514_1454.xlsx"' in header
    assert "filename*=UTF-8''report_%D0%92%D1%8B%D1%85%D0%B8%D0%BD%D0%BE" in header
