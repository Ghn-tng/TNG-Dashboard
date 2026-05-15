import openpyxl

def inspect_gtc_history():
    wb = openpyxl.load_workbook('TNG - Báo cáo Vận Hành.xlsx', data_only=True)
    ws = wb['3. % GTC-BC']
    for r in range(1, 40):
        row_vals = [ws.cell(r, c).value for c in range(1, 10)]
        print(f"Row {r}: {row_vals}")
    wb.close()

if __name__ == "__main__":
    inspect_gtc_history()
