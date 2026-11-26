# =============================================================
# 檢核：滯洪量體計算V2.xlsm、逕流係數0928.xlsx
# 對應教案：Week 3、Week 9、Week 13、第十八節 E4、D4、判斷題 1、2
#
# 做法：
#   1. 把每張滯洪量體工作表的「標題寫的重現期」跟「實際用的 Horner 參數」對照
#   2. 重算面積加權 CN 與 SCS 有效降雨
#   3. 找出寫死的常數、不一致的面積
#
# 執行方式（在 HydroCoding 資料夾）：
#     python tools\refcase_check\check_detention.py
# =============================================================

import re
from common import REF, need_ref_case, xlsx_rows, cell, is_num, report, section, summary

FOLDER = REF / "detention(Outflow Control)"
DET = FOLDER / "滯洪量體計算V2" / "滯洪量體計算V2.xlsm"
CN_FILE = FOLDER / "逕流係數0928.xlsx"


def scs_pe(P, CN):
    """SCS 曲線號碼法有效降雨（mm）。"""
    S = 25.4 * (1000 / CN - 10)
    return (P - 0.2 * S) ** 2 / (P + 0.8 * S) if P > 0.2 * S else 0.0


def main():
    need_ref_case()

    section("1. Horner 參數參考表（集水區資料 S8:U11）")
    base = xlsx_rows(DET, "集水區資料", max_row=12, max_col=21)
    ref = {}
    for col, T in zip("STU", (2, 5, 10)):
        ref[T] = tuple(cell(base, f"{col}{r}") for r in (8, 9, 10, 11))
        report("info", "-", f"{T} 年：a = {ref[T][0]}、b = {ref[T][1]}、c = {ref[T][2]}、最大一日 {ref[T][3]} mm")
    cn_tab = xlsx_rows(CN_FILE, "HORNER公式參數", max_row=9, max_col=4)
    tab = {int(r[0]): tuple(r[1:4]) for r in cn_tab if is_num(r[0])}
    same = all(tuple(ref[T][:3]) == tab.get(T) for T in (2, 5, 10))
    report("ok" if same else "error", "-", f"與 逕流係數0928.xlsx「HORNER公式參數」（中壢站 LPT3）{'一致' if same else '不一致'}")

    def which_T(params):
        for T, v in ref.items():
            if tuple(params[:3]) == tuple(v[:3]):
                return T
        return None

    section("2. 各工作表：標題的重現期 vs 實際參數")
    sheets = ["拆分區外", "滯洪量體計算後10-前2", "滯洪量體計算2yr", "滯洪量體計算5yr", "滯洪量體計算10yr"]
    for s in sheets:
        v = xlsx_rows(DET, s, max_row=12, max_col=10)
        f = xlsx_rows(DET, s, formulas=True, max_row=12, max_col=10)
        for title_cell, col, side in (("B1", "B", "開發後"), ("F1", "F", "開發前")):
            title = cell(v, title_cell)
            if not title:
                continue
            p = tuple(cell(v, f"{col}{r}") for r in (3, 4, 5, 6))      # a、b、c、最大一日
            area, cn = cell(v, f"{col}7"), cell(v, f"{col}9")
            T_title = int(re.search(r"(\d+)\s*年", str(title)).group(1))
            T_real = which_T(p)
            msg = f"{s}｜{title}：a={p[0]}、b={p[1]}、c={p[2]}、{p[3]} mm、面積 {area:.5f} km²、CN {cn}"
            if T_real == T_title and p[3] == ref[T_title][3]:
                report("ok", "-", msg + " → 與標題一致")
            elif T_real is not None:
                report("error", "E4", msg + f" → 標題寫 {T_title} 年，參數卻是 {T_real} 年的")
            else:
                report("doubt", "E4", msg + f" → 標題寫 {T_title} 年，參數不在參考表內，出處不明")
        if cell(v, "E1") is None and s == "拆分區外":
            pass
        i12 = cell(f, "I12")
        if isinstance(i12, str) and "0.17" in i12:
            report("doubt", "-", f"{s}｜I12 公式 {i12}：時間間距 10 分鐘 = 0.16667 hr，寫成 0.17 會高估 2%（判斷題 1）")
        tot = cell(v, "J2")
        if is_num(tot):
            report("info", "-", f"{s}｜總滯洪量 J2 = {tot:.1f} m³（用 J 欄的 *600 秒計算）")

    v = xlsx_rows(DET, "滯洪量體計算後10-前2", max_row=12, max_col=10)
    a_post, a_pre = cell(v, "B7"), cell(v, "F7")
    if a_post and a_pre and max(a_post, a_pre) / min(a_post, a_pre) > 2:
        report("doubt", "D4", f"滯洪量體計算後10-前2：開發後面積 {a_post * 1e6:,.0f} m²、開發前 {a_pre * 1e6:,.0f} m²，"
               f"相差 {a_post / a_pre:.1f} 倍 → 滯洪量主要來自面積差，不是開發造成的逕流增加")

    section("3. CN 值與有效降雨（逕流係數0928.xlsx）")
    cnv = xlsx_rows(CN_FILE, "CN值", max_row=25, max_col=22)
    for label, rows, listed_ref in (("開發前", (4, 5, 6), "J8"), ("開發後", (12, 13, 14), "J16")):
        cns = [cell(cnv, f"J{r}") for r in rows]
        areas = [cell(cnv, f"K{r}") for r in rows]
        w = sum(c * a for c, a in zip(cns, areas)) / sum(areas)
        listed = cell(cnv, listed_ref)
        report("ok" if abs(w - listed) < 1e-3 else "error", "-",
               f"{label} 加權 CN = {w:.4f}（表上 {listed:.4f}）；鋪面 {areas[0]:,.0f} m²、工業 {areas[1]:,.0f} m²、草地 {areas[2]:,.0f} m²")
    report("info", "-", "開發後鋪面減少、草地增加，CN 下降是合理的（判斷題 2）")
    est = xlsx_rows(CN_FILE, "逕流係數推估一覽表", max_row=8, max_col=14)
    for r in (4, 5, 6):
        P, cn0, cn1 = cell(est, f"C{r}"), cell(est, f"M{r}"), cell(est, f"N{r}")
        pe0, pe1 = scs_pe(P, cn0), scs_pe(P, cn1)
        ok = abs(pe0 - cell(est, f"D{r}")) < 0.01 and abs(pe1 - cell(est, f"E{r}")) < 0.01
        report("ok" if ok else "error", "-", f"{cell(est, f'B{r}')} 年 P = {P} mm：Pe 開發前 {pe0:.2f}、開發後 {pe1:.2f} mm（表上 {cell(est, f'D{r}'):.2f}、{cell(est, f'E{r}'):.2f}）")
    estF = xlsx_rows(CN_FILE, "逕流係數推估一覽表", formulas=True, max_row=8, max_col=14)
    hq = [(cell(est, f"H{r}"), cell(est, f"I{r}")) for r in (4, 5, 6)]
    typed = all(not (isinstance(cell(estF, f"H{r}"), str) and str(cell(estF, f"H{r}")).startswith("=")) for r in (4, 5, 6))
    if typed:
        report("doubt", "D4", f"洪峰流量 H4:I6 是直接打上去的數字，不是公式：2 年 {hq[0]}、5 年 {hq[1]}、10 年 {hq[2]}"
               + ("；2 年與 5 年完全相同" if hq[0] == hq[1] else ""))

    section("4. 各處的基地面積")
    areas = {
        "CN值 K7（土地利用合計）": cell(cnv, "K7"),
        "CN值 B22（左表總計）": cell(cnv, "B22"),
        "CN值 U11（基地）": cell(cnv, "U11"),
        "滯洪量體計算2yr B7": cell(xlsx_rows(DET, "滯洪量體計算2yr", max_row=8, max_col=3), "B7") * 1e6,
        "滯洪量體計算後10-前2 B7": a_post * 1e6,
    }
    if len({round(a, 1) for a in areas.values()}) > 1:
        report("doubt", "D4", "基地面積不一致：" + "、".join(f"{k} = {a:,.2f} m²" for k, a in areas.items()))

    return summary("滯洪池")


if __name__ == "__main__":
    main()
