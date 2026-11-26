# =============================================================
# 檢核：降雨頻率分析_20231008.xlsx
# 對應教案：Week 6–7、第十八節 E5、D1、判斷題 5、19
#
# 做法：用 scipy 的「精確」機率分布獨立計算各重現期雨量，
#       跟 Excel 的快取值比對。不是把 Excel 公式照抄一遍，
#       因為照抄只能證明抄對，不能證明 Excel 對。
#
# 執行方式（在 HydroCoding 資料夾）：
#     python tools\refcase_check\check_frequency.py
# =============================================================

import numpy as np
from scipy import stats
from common import REF, need_ref_case, xlsx_rows, cell, is_num, report, section, summary

FILE = REF / "hydrological analysis" / "降雨頻率分析_20231008.xlsx"
T = np.array([2, 5, 10, 25, 50, 100, 200])          # 要比對的重現期
EXCEL_ROW = {2: 5, 5: 6, 10: 7, 25: 10, 50: 11, 100: 12, 200: 13}   # Fq_Comp. 工作表裡各重現期所在的列


def main():
    need_ref_case()
    comp = xlsx_rows(FILE, "Fq_Comp.", max_row=60, max_col=40)
    compF = xlsx_rows(FILE, "Fq_Comp.", formulas=True, max_row=60, max_col=40)
    rain = xlsx_rows(FILE, "Rain", max_row=40, max_col=20)

    # Fq_Comp. 的 F 欄是分析用的樣本（從 Rain 工作表 R 欄帶過來的流域平均雨量）
    x = np.array([r[5] for r in comp[2:] if len(r) > 5 and is_num(r[5])])
    n = len(x)

    section("1. 基本統計量")
    mu, sd = x.mean(), x.std(ddof=1)            # ddof=1：樣本標準差，與 Excel STDEV 相同
    g1 = stats.skew(x, bias=True)               # 未修正偏態
    G1 = stats.skew(x, bias=False)              # 修正後偏態（與 Excel SKEW 相同）
    ex = {k: cell(comp, a) for k, a in [("n", "C3"), ("mu", "C4"), ("sd", "C5"), ("cs", "C6"), ("hazen", "C7"), ("bobee", "C8")]}
    report("ok" if ex["n"] == n else "error", "-", f"樣本數 {n}（Excel {ex['n']}）")
    report("ok" if abs(mu - ex["mu"]) < 1e-6 else "error", "-", f"平均 {mu:.4f}（Excel {ex['mu']:.4f}）")
    report("ok" if abs(sd - ex["sd"]) < 1e-6 else "error", "-", f"標準差 {sd:.4f}（Excel {ex['sd']:.4f}，用 ddof=1）")
    report("ok" if abs(G1 - ex["cs"]) < 1e-6 else "error", "-",
           f"偏態 Excel SKEW = {ex['cs']:.5f}，等於修正後 G1 = {G1:.5f}（未修正 g1 = {g1:.5f}）")

    section("2. 偏態係數修正")
    hazen = G1 * (1 + 8.5 / n)
    report("ok" if abs(hazen - ex["hazen"]) < 1e-6 else "error", "-", f"Hazen 修正 C7 = {ex['hazen']:.5f}（重算 {hazen:.5f}）")
    double = G1 * np.sqrt(n * (n - 1)) / (n - 2) * (1 + 8.5 / n)
    if abs(ex["bobee"] - double) < 1e-6:
        report("error", "E5", f"「Bobée 修正」C8 = {ex['bobee']:.5f}，公式是 SKEW × √(n(n−1))/(n−2) × (1+8.5/n)。"
               f"SKEW 已經是 G1，又乘一次 √(n(n−1))/(n−2) → 重複修正（只做 Hazen 應為 {hazen:.5f}）")
    used = [cell(xlsx_rows(FILE, "Fq-Result", formulas=True, max_row=3, max_col=9), a) for a in ["D2", "E2", "F2", "G2", "H2"]]
    report("info", "E5", f"Fq-Result 成果表引用的欄位：{used} → 沒有用到 AD、AF（重複修正的欄位）")

    section("3. 各分布重現期雨量：scipy 精確解 vs Excel")
    p = 1 - 1 / T
    z = stats.norm.ppf(p)
    y = np.log(x)
    sy2 = np.log(1 + (sd / mu) ** 2)
    mine = {
        "NORMAL": ("Y", stats.norm.ppf(p, mu, sd), 0.001),
        "LOG-NORMAL II": ("Z", np.exp(np.log(mu) - sy2 / 2 + z * np.sqrt(sy2)), 0.001),
        "PEARSON III": ("AE", stats.pearson3.ppf(p, G1, loc=mu, scale=sd), 0.5),
        "LOG-PEARSON III": ("AG", np.exp(stats.pearson3.ppf(p, stats.skew(y, bias=False), loc=y.mean(), scale=y.std(ddof=1))), 0.5),
        "GUMBEL（動差法 n→∞）": ("AH", mu + sd * (-np.sqrt(6) / np.pi * (0.5772157 + np.log(np.log(T / (T - 1))))), 0.001),
    }
    for name, (col, v, tol) in mine.items():
        e = np.array([cell(comp, f"{col}{EXCEL_ROW[t]}") for t in T])
        diff = np.max(np.abs(v - e) / e) * 100
        note = "（Excel 用 Wilson-Hilferty 近似）" if tol > 0.01 else ""
        report("ok" if diff <= tol else "error", "-", f"{name:20s} 最大差 {diff:.3f}% {note}｜100 年：Python {v[5]:.1f}、Excel {e[5]:.1f} mm")

    section("4. 測站資料來源")
    L = np.array([[v for v in r[11:14]] for r in rain[2:31]], dtype=float)      # L、M、N 欄 = 三站
    w = np.array([cell(rain, a) for a in ["B17", "C17", "D17"]], dtype=float)
    corr = np.corrcoef(L.T)
    tidy = np.mean(np.abs(L * w * 10 - np.round(L * w * 10)) < 1e-6)            # 乘權重後是否剛好是一位小數
    if corr.min() > 0.9999:
        report("doubt", "D1", f"三站（{rain[1][2]}、{rain[1][3]}、{rain[1][4]}）逐年雨量相關係數最小值 {corr.min():.5f}，"
               f"乘權重後 {tidy * 100:.0f}% 剛好是一位小數 → 是從流域平均反推的值，不是觀測值")
    coord = [cell(rain, a) for a in ["C9", "C10", "D9", "D10"]]
    if all(v is None for v in coord):
        report("info", "-", "Rain 工作表的 X_TWD97、Y_TWD97 只有欄位標題，座標值是空白")

    return summary("頻率分析")


if __name__ == "__main__":
    main()
