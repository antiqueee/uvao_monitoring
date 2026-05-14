from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.models import Report


def build_report_workbook(report: Report) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Распространение"

    ws.merge_cells("A1:K1")
    ws["A1"] = "Распространение на медиаресурсах АО"
    ws.merge_cells("A2:F2")
    ws["A2"] = "Инфоповод"
    ws.merge_cells("G2:K2")
    ws["G2"] = "Размещение"

    headers = [
        "№ п/п",
        "АО",
        "ИО",
        "Дата",
        "Наименование инфоповода",
        "Ссылка на первоисточник",
        "Категория соц. сетей (окружное или районное сообщество/личная страница ЛОМа/другое(указать категорию))",
        "Наименование канала/сообщества",
        "Ссылка на публикацию",
        "Кол-во подписчиков",
        "Кол-во просмотров",
    ]
    for col, value in enumerate(headers, start=1):
        ws.cell(row=3, column=col, value=value)

    for row_idx, row in enumerate(report.rows, start=4):
        values = [
            row.row_number,
            "ЮВАО",
            "198",
            row.repost_date.strftime("%d.%m.%Y"),
            report.infopovod_title,
            report.source_url,
            row.resource.category_name,
            row.resource.display_name,
            row.repost_url,
            row.followers_count,
            row.views_count,
        ]
        for col, value in enumerate(values, start=1):
            ws.cell(row=row_idx, column=col, value=value)

    pink = PatternFill("solid", fgColor="F4CCCC")
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    for row in ws.iter_rows(min_row=1, max_row=max(ws.max_row, 3), min_col=1, max_col=11):
        for cell in row:
            cell.border = border
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if cell.row <= 3:
                cell.fill = pink
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    widths = [8, 10, 8, 14, 32, 36, 48, 32, 36, 18, 18]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
