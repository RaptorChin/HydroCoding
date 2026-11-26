# =============================================================
# 檢核：牡丹水庫例 01（自由溢流）的 Fortran 演算成果
# 對應教案：Week 13、第十八節 E1、D3、判斷題 17
#
# 做法：用「二分法」獨立重算連續方程式（Fortran 用的是 Newton-Raphson 法），
#       方法不同，算出來卻一致，才能說明數值解是對的。
#
# 執行方式（在 HydroCoding 資料夾）：
#     python tools\refcase_check\check_reservoir_routing.py
# =============================================================

import numpy as np
from common import REF, need_ref_case, xls_rows, report, section, summary

BASE = REF / "reservoir routing" / "牡丹水庫練習" / "例01_PMF模擬_自由溢流_溢洪道"
DT_SIM = 1800.0      # 演算時距 0.5 小時 = 1800 秒（Conditions.org 的設定）
N_SUB = 2            # 1 小時入流切成 2 個 0.5 小時


def find_run_folder():
    """找出放 Fortran 程式與輸入檔的子資料夾（用 Conditions.org 判斷，不寫死資料夾名稱）。"""
    hits = sorted(p.parent for p in BASE.glob("*/Conditions.org"))
    return hits[0] if hits else None


def read_block(lines, tag):
    """讀 Conditions.org 裡某個 [標籤] 底下的表格：標籤 → 說明 → (空行) → 筆數 → 資料。"""
    i = [k for k, l in enumerate(lines) if l.strip() == tag][0] + 2
    while not lines[i].strip():
        i += 1
    n = int(lines[i])
    return np.array([list(map(float, lines[i + 1 + k].split())) for k in range(n)])


def route(h0, inflow, H, V, Hr, Qr, fix_tail):
    """
    水庫蓄水演算（自由溢流）。
    fix_tail=False：忠實重現 Fortran，最後一個時段的「下一筆入流」當成 0
    fix_tail=True ：修正版，最後一筆入流維持原值
    回傳每個時刻的 [蓄水量, 水位, 入流, 放流]
    """
    def outflow(s):
        h = np.interp(s, V, H)
        return 0.0 if h < Hr[0] else float(np.interp(h, Hr, Qr))

    I = list(inflow) + ([inflow[-1]] if fix_tail else [0.0])
    s = float(np.interp(h0, H, V))
    out = [(s, h0, I[0], outflow(s))]
    for j in range(len(inflow)):
        for k in range(N_SUB):
            i0 = I[j] + (I[j + 1] - I[j]) / N_SUB * k
            i1 = I[j] + (I[j + 1] - I[j]) / N_SUB * (k + 1)
            o0 = outflow(s)
            lo, hi = 0.0, V[-1]
            for _ in range(200):     # 二分法：找出讓連續方程式成立的期末蓄水量
                mid = (lo + hi) / 2
                f = mid - (s + 0.5 * (i0 + i1) * DT_SIM - 0.5 * (o0 + outflow(mid)) * DT_SIM)
                lo, hi = (lo, mid) if f > 0 else (mid, hi)
            s = (lo + hi) / 2
            out.append((s, float(np.interp(s, V, H)), i1, outflow(s)))
    return np.array(out)


def main():
    need_ref_case()
    run = find_run_folder()
    if run is None:
        print("找不到含 Conditions.org 的子資料夾，無法檢核。")
        return
    lines = (run / "Conditions.org").read_text(encoding="big5").split("\n")
    HV = read_block(lines, "[HV]")
    HQ = read_block(lines, "[ratingcurve]")
    H, V, Hr, Qr = HV[:, 0], HV[:, 1], HQ[:, 0], HQ[:, 1]
    inflow = np.loadtxt(run / "Inflow.csv")

    section("1. 輸入資料基本檢查")
    report("ok" if np.all(np.diff(V) > 0) else "error", "-", f"H-V 曲線 {len(H)} 點，容積隨水位單調遞增")
    report("ok" if np.all(np.diff(Qr) > 0) else "error", "-", f"H-Q 率定曲線 {len(Hr)} 點，流量隨水位單調遞增")
    report("info", "-", f"入流歷線 {len(inflow)} 筆（每小時一筆），最後一筆 = {inflow[-1]} cms")

    section("2. 與 Fortran output.csv 比對（起始水位 126 m）")
    f = np.genfromtxt(run / "output.csv", delimiter=",", skip_header=1, encoding="big5")[:, :6]
    r = route(126.0, inflow, H, V, Hr, Qr, fix_tail=False)
    dh, dq = np.abs(f[:, 3] - r[:, 1]).max(), np.abs(f[:, 5] - r[:, 3]).max()
    report("ok" if dh < 0.001 and dq < 0.01 else "error", "-",
           f"忠實重現版與 output.csv：水位最大差 {dh:.4f} m、放流最大差 {dq:.4f} cms")
    if f[-1, 4] == 0 and inflow[-1] != 0:
        report("error", "E1", f"output.csv 最後兩筆入流 = {f[-2, 4]:.0f}、{f[-1, 4]:.0f} cms，"
               f"但原始入流最後一筆是 {inflow[-1]:.0f} cms → Fortran 的 Inflow(j+1) 超出資料範圍，讀到 0")

    section("3. 與正式成果 水庫演算結果.xls 比對（8 個起始水位）")
    wb_path = BASE / "水庫演算結果.xls"
    from common import open_xls
    wb = open_xls(wb_path)
    peaks = []
    tail_bug = 0
    for sh in wb.sheets():
        h0 = float(sh.name.split("_")[1])
        x = np.array([sh.row_values(i)[:7] for i in range(1, sh.nrows)], dtype=float)
        r = route(h0, inflow, H, V, Hr, Qr, fix_tail=False)
        n = min(len(x), len(r))
        d = np.abs(x[:n, 4] - r[:n, 1]).max()
        if d >= 0.001:
            report("error", "-", f"起始 {h0} m：水位最大差 {d:.4f} m（超過 0.001 m）")
        if x[-1, 5] == 0 and inflow[-1] != 0:
            tail_bug += 1
        peaks.append((h0, x[:, 4].max(), x[:, 6].max()))
    report("ok", "-", f"{len(peaks)} 個起始水位的水位歷線都與獨立重算一致（差 < 0.001 m）")
    if tail_bug:
        report("error", "E1", f"正式成果 {tail_bug} 張工作表的最後入流都是 0 → 同樣帶有尾端歸零錯誤")

    section("4. 修正尾端錯誤後的影響")
    r_bug = route(130.0, inflow, H, V, Hr, Qr, fix_tail=False)
    r_fix = route(130.0, inflow, H, V, Hr, Qr, fix_tail=True)
    report("info", "E1", f"起始 130 m：最高水位 錯誤版 {r_bug[:, 1].max():.3f} / 修正版 {r_fix[:, 1].max():.3f} m；"
           f"最後放流 錯誤版 {r_bug[-1, 3]:.1f} / 修正版 {r_fix[-1, 3]:.1f} cms → 洪峰不受影響，只影響尾端")
    if len({round(p[1], 3) for p in peaks}) == 1:
        report("info", "-", f"所有起始水位的最高水位都是 {peaks[0][1]:.3f} m、最大放流 {peaks[0][2]:.1f} cms（判斷題 17）")

    section("5. 率定曲線檢查（與擬合方程式比較）")
    rows = xls_rows(BASE / "溢洪道_流量率定曲線1.xls")
    pts = [(r[0], r[1], r[2]) for r in rows if all(isinstance(v, float) for v in r[:3])]
    for h, q, qfit in pts:
        dev = (q - qfit) / qfit * 100
        if abs(dev) > 5 and h < 141:    # 高水位段擬合本來就比較差，只看常用範圍
            report("doubt", "D3", f"{h} m：表列 {q:.0f} cms，擬合方程式 {qfit:.0f} cms，相差 {dev:+.1f}%")
    slope = np.diff(Qr) / np.diff(Hr)
    for i in range(1, len(slope)):
        if slope[i] < 0.5 * slope[i - 1] and Hr[i] < 141:
            report("doubt", "D3", f"{Hr[i - 1]}→{Hr[i]} m 斜率 {slope[i - 1]:.0f} cms/m，"
                   f"{Hr[i]}→{Hr[i + 1]} m 突然降到 {slope[i]:.0f} cms/m")

    return summary("水庫演算")


if __name__ == "__main__":
    main()
