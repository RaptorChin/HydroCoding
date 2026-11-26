# =============================================================
# ref case 檢核工具：共用函數
#
# 所有檢核程式都會 import 這個檔案，裡面放：
#   1. 路徑設定（ref case 資料夾在哪裡）
#   2. 讀 Excel 的小工具（.xls 用 xlrd，.xlsx/.xlsm 用 openpyxl）
#   3. 回報結果的格式（✅ 一致 / ❌ 錯誤 / ⚠️ 疑點 / ℹ️ 資訊）
#
# 這個檔案本身不用執行。
# =============================================================

import sys
import warnings
from pathlib import Path

# Windows 終端機預設是 cp950 編碼，印出 ✅、³ 這類符號會報錯，這裡統一改成 utf-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# openpyxl 讀舊檔時常會跳出一堆無害的警告，先關掉，讓畫面乾淨
warnings.filterwarnings("ignore")

# ---------- 1. 路徑 ----------
# 這個檔案在 HydroCoding/tools/refcase_check/，往上兩層就是 HydroCoding
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REF = PROJECT_ROOT / "ref case"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def need_ref_case():
    """確認 ref case 資料夾存在，不存在就提示並結束程式。"""
    if not REF.exists():
        print(f"找不到 ref case 資料夾：{REF}")
        print("請確認 ref case 放在 HydroCoding 資料夾底下。")
        sys.exit(1)


# ---------- 2. 讀 Excel ----------
def open_xls(path):
    """開啟舊版 .xls（Excel 97–2003）。需要 xlrd 套件。"""
    try:
        import xlrd
    except ImportError:
        print("缺少 xlrd 套件，無法讀取 .xls 檔。")
        print("請在 HydroCoding 資料夾執行：python -m pip install xlrd")
        sys.exit(1)
    return xlrd.open_workbook(str(path))


def xls_rows(path, sheet=0):
    """把 .xls 某一張工作表讀成「列的清單」，每一列是一個 list。"""
    wb = open_xls(path)
    sh = wb.sheet_by_index(sheet) if isinstance(sheet, int) else wb.sheet_by_name(sheet)
    return [sh.row_values(r) for r in range(sh.nrows)]


def xlsx_rows(path, sheet, formulas=False, max_row=None, max_col=None):
    """
    把 .xlsx / .xlsm 某一張工作表讀成「列的清單」。
    formulas=False：讀 Excel 上次存檔時算好的數值（快取值）
    formulas=True ：讀公式文字

    注意：一律用 read_only 模式。有些舊檔的圖表格式 openpyxl 解析不了，
    一般模式會直接報錯。但 read_only 模式讀「往下填滿的共用公式」時，
    可能只顯示第一格的公式（教案判斷題 4），讀公式時要特別小心。
    """
    import openpyxl
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=not formulas)
    ws = wb[sheet] if isinstance(sheet, str) else wb.worksheets[sheet]
    return [list(r) for r in ws.iter_rows(max_row=max_row, max_col=max_col, values_only=True)]


def cell(rows, ref):
    """用 Excel 的儲存格名稱（例如 "B3"）從 rows 取值。"""
    from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
    col, row = coordinate_from_string(ref)
    r, c = row - 1, column_index_from_string(col) - 1
    if r >= len(rows) or c >= len(rows[r]):
        return None
    return rows[r][c]


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


# ---------- 3. 回報結果 ----------
_results = []

ICON = {"ok": "✅", "error": "❌", "doubt": "⚠️ ", "info": "ℹ️ "}


def report(status, code, message):
    """
    記錄並印出一項檢核結果。
    status：ok（重算一致）、error（確定有錯）、doubt（疑點）、info（資訊）
    code  ：對應教案第十八節的編號，例如 "E1"、"D3"；沒有編號就填 "-"
    """
    _results.append((status, code, message))
    print(f"  {ICON[status]} [{code}] {message}")


def section(title):
    print(f"\n========== {title} ==========")


def summary(script_name):
    """印出這支程式的檢核統計，並回傳「有沒有找到錯誤」。"""
    n = {k: sum(1 for s, _, _ in _results if s == k) for k in ICON}
    print(f"\n----- {script_name} 小結：✅ {n['ok']}　❌ {n['error']}　⚠️ {n['doubt']}　ℹ️ {n['info']} -----")
    return n["error"]
