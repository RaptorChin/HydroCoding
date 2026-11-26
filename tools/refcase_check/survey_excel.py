# =============================================================
# 掃描 ref case 裡所有 Excel 檔：每個檔有哪些工作表、每張表多大、前幾列長什麼樣子
#
# 用途：拿到一大堆陌生的舊檔時，先「看一遍目錄」，決定要深入看哪幾個。
#       這是 Week 3「認識資料」的資料夾版本。
# 輸出位置：tools\refcase_check\output\excel_survey.txt（這個資料夾不會進 git）
#
# 執行方式（在 HydroCoding 資料夾）：
#     python tools\refcase_check\survey_excel.py
# =============================================================

from common import REF, OUTPUT_DIR, need_ref_case, open_xls, section

PREVIEW_ROWS = 8        # 每張工作表預覽幾列
PREVIEW_COLS = 12       # 每列預覽幾欄


def short(v):
    if isinstance(v, float):
        v = round(v, 4)
    return str(v).strip().replace("\n", " ")[:20]


def survey_xls(path, out):
    wb = open_xls(path)
    for sh in wb.sheets():
        out.append(f"  [工作表] {sh.name}（{sh.nrows} 列 × {sh.ncols} 欄）")
        shown = 0
        for r in range(sh.nrows):
            vals = [short(sh.cell_value(r, c)) for c in range(min(sh.ncols, PREVIEW_COLS)) if str(sh.cell_value(r, c)).strip()]
            if vals:
                out.append("      " + " | ".join(vals)[:180])
                shown += 1
            if shown >= PREVIEW_ROWS:
                break


def survey_xlsx(path, out):
    import openpyxl
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    for ws in wb.worksheets:
        out.append(f"  [工作表] {ws.title}（約 {ws.max_row} 列 × {ws.max_column} 欄）")
        shown = 0
        for row in ws.iter_rows(max_row=60, max_col=PREVIEW_COLS, values_only=True):
            vals = [short(v) for v in row if v is not None and str(v).strip()]
            if vals:
                out.append("      " + " | ".join(vals)[:180])
                shown += 1
            if shown >= PREVIEW_ROWS:
                break


def main():
    need_ref_case()
    OUTPUT_DIR.mkdir(exist_ok=True)
    files = sorted(p for p in REF.rglob("*") if p.suffix.lower() in (".xls", ".xlsx", ".xlsm") and not p.name.startswith("~$"))
    out, failed = [], []
    for p in files:
        out.append(f"\n##### {p.relative_to(REF)}")
        try:
            (survey_xls if p.suffix.lower() == ".xls" else survey_xlsx)(p, out)
        except Exception as e:
            out.append(f"  無法讀取：{e}")
            failed.append(f"{p.relative_to(REF)}：{e}")
    target = OUTPUT_DIR / "excel_survey.txt"
    target.write_text("\n".join(out), encoding="utf-8")
    section("掃描結果")
    print(f"  共 {len(files)} 個 Excel 檔，結果存在 {target}")
    for f in failed:
        print(f"  無法讀取：{f}")
    return 0


if __name__ == "__main__":
    main()
