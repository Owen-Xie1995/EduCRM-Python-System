"""將畫面上的學生清單匯出成 Excel。"""
from openpyxl import Workbook

HEADERS = ["學號", "姓名", "性別", "電話", "家長", "狀態", "欠款", "時間"]


def export_students(path, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = '學生清單'
    sheet.append(HEADERS)
    for row in rows:
        sheet.append(row)
        # 姓名、電話等輸入保留為文字，避免被 Excel 當成公式。
        for cell in sheet[sheet.max_row]:
            if isinstance(cell.value, str):
                cell.data_type = 's'
    workbook.save(path)
