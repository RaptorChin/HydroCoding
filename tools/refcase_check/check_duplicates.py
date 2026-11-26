# =============================================================
# 檢核：ref case 裡「同名但放在不同資料夾」的 Excel 檔，內容是否真的相同
# 對應教案：Week 9、Week 14、第十八節 E6
#
# 為什麼要查：複製資料夾當新題目，最容易忘記換掉裡面的資料。
#             檔名一樣不代表內容一樣，內容一樣也不代表放對地方。
#
# 執行方式（在 HydroCoding 資料夾）：
#     python tools\refcase_check\check_duplicates.py
# =============================================================

import hashlib
from common import REF, need_ref_case, open_xls, xls_rows, report, section, summary


def md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def content(path):
    """把 .xls 的所有工作表內容讀成一個可以比較的資料結構。"""
    wb = open_xls(path)
    return [(s.name, [s.row_values(r) for r in range(s.nrows)]) for s in wb.sheets()]


def main():
    need_ref_case()

    section("1. 同名 .xls 檔的內容比較")
    groups = {}
    for p in REF.rglob("*.xls"):
        if not p.name.startswith("~$"):
            groups.setdefault(p.name, []).append(p)
    same = diff = 0
    for name, paths in sorted(groups.items()):
        if len(paths) < 2:
            continue
        try:
            cs = [content(p) for p in paths]
        except Exception:
            continue
        if all(c == cs[0] for c in cs[1:]):
            same += 1
        else:
            diff += 1
            where = "；".join(str(p.parent.relative_to(REF)) for p in paths[:4]) + ("…" if len(paths) > 4 else "")
            report("info", "-", f"「{name}」有 {len(paths)} 份，內容不完全相同：{where}")
    report("info", "-", f"同名 .xls 共 {same + diff} 組：內容相同 {same} 組、不同 {diff} 組（不同不一定是錯，可能只是多了欄位，要再人工確認）")

    section("2. 曾文水庫例 05 是否誤用牡丹水庫的資料")
    zw = REF / "reservoir routing" / "曾文水庫練習" / "例05_PMF模擬_控制放流_所有出水工"
    md = REF / "reservoir routing" / "牡丹水庫練習" / "例05_PMF模擬_控制放流_溢洪道多流況+排水道"
    copied = []
    for f in ["H-V_淤積50年後.xls", "進水流量歷線.xls", "流量率定曲線5.xls", "例05_水庫演算結果.xls"]:
        a, b = zw / f, md / f
        if a.exists() and b.exists() and md5(a) == md5(b):
            copied.append(f)
    if copied:
        hv = xls_rows(zw / "H-V_淤積50年後.xls")
        h = [r[0] for r in hv if isinstance(r[0], float)]
        report("error", "E6", f"曾文例 05 的 {len(copied)} 個資料檔與牡丹例 05 位元組完全相同：{'、'.join(copied)}；"
               f"H-V 水位範圍 {min(h)}～{max(h)} m，但題目說明的曾文水庫蓄水範圍是 EL.216～236 m")
    zw1 = REF / "reservoir routing" / "曾文水庫練習" / "例01_溢洪道_自由溢流"
    md1 = REF / "reservoir routing" / "牡丹水庫練習" / "例01_PMF模擬_自由溢流_溢洪道"
    if (zw1 / "進水流量歷線.xls").exists() and content(zw1 / "進水流量歷線.xls") == content(md1 / "進水流量歷線.xls"):
        report("doubt", "E6", "曾文例 01 資料夾裡的「進水流量歷線.xls」內容也是牡丹的入流；曾文的入流應該用 Inflow_Morakot_2009.xls")
    hav = xls_rows(zw1 / "H-A-V_2010.xls")
    h = [r[0] for r in hav if isinstance(r[0], float)]
    report("info", "-", f"曾文例 01 的 H-A-V_2010.xls 水位範圍 {min(h)}～{max(h)} m（這才是曾文水庫的資料）")

    return summary("重複檔案")


if __name__ == "__main__":
    main()
