# =============================================================
# 擷取舊 Excel 檔裡的巨集原始碼，存成文字檔方便閱讀
#   1. 滯洪量體計算V2.xlsm 的 VBA 巨集（需要 oletools 套件）
#   2. 土方計算-新.xls 的 Lotus 1-2-3 巨集（寫在工作表右側的儲存格裡）
# 對應教案：Week 3 VBA 練習、Week 10 方格法土方
#
# 這支不是「檢核」，是讓你不用打開 Excel 就能讀巨集。
# 輸出位置：tools\refcase_check\output\（這個資料夾不會進 git）
#
# 執行方式（在 HydroCoding 資料夾）：
#     python tools\refcase_check\extract_macros.py
# 若要擷取 VBA，先安裝 oletools：
#     python -m pip install oletools
# =============================================================

from common import REF, OUTPUT_DIR, need_ref_case, open_xls, section


def extract_vba(path, out_file):
    try:
        from oletools.olevba import VBA_Parser
    except ImportError:
        print("  缺少 oletools 套件，略過 VBA 擷取。")
        print("  請在 HydroCoding 資料夾執行：python -m pip install oletools")
        return
    vp = VBA_Parser(str(path))
    lines = []
    for _, stream, name, code in vp.extract_macros():
        if code.strip() and "Attribute VB_Name" not in code.strip().split("\n")[-1]:
            lines.append(f"'========== {name}（{stream}）==========\n{code}\n")
    vp.close()
    out_file.write_text("\n".join(lines) or "（沒有找到巨集）", encoding="utf-8")
    print(f"  已存成 {out_file}")


def extract_lotus(path, out_file):
    sh = open_xls(path).sheet_by_index(1)
    lines = []
    for r in range(sh.nrows):
        label, code = str(sh.cell_value(r, 52)).strip(), str(sh.cell_value(r, 53)).strip()
        if label or code:
            lines.append(f"{label:8s}{code}")
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"  已存成 {out_file}（共 {len(lines)} 行）")


def main():
    need_ref_case()
    OUTPUT_DIR.mkdir(exist_ok=True)
    section("1. VBA 巨集：滯洪量體計算V2.xlsm")
    extract_vba(REF / "detention(Outflow Control)" / "滯洪量體計算V2" / "滯洪量體計算V2.xlsm",
                OUTPUT_DIR / "滯洪量體計算V2_VBA.txt")
    section("2. Lotus 1-2-3 巨集：土方計算-新.xls")
    extract_lotus(REF / "其他" / "水保相關EXCEL檔" / "土方計算-新.xls", OUTPUT_DIR / "土方計算_Lotus巨集.txt")
    return 0


if __name__ == "__main__":
    main()
