# =============================================================
# 檢核：管涵溝渠檢核計算書(以最大流量檢核).xlsx
# 對應教案：Week 11、第十八節 E3、判斷題 18
#
# 做法：
#   1. 讀出 5 張工作表各自使用的降雨強度公式參數
#   2. 檢查不同公式是否誤用了同一組參數
#   3. 獨立重算 Sherman 工作表的整條計算鏈（I → Q → 圓管通水能力）
#
# 執行方式（在 HydroCoding 資料夾）：
#     python tools\refcase_check\check_sewer_idf.py
# =============================================================

import math
from common import REF, need_ref_case, xlsx_rows, cell, report, section, summary

FILE = REF / "Sewer Flow Routing" / "管涵溝渠檢核計算書(以最大流量檢核).xlsx"


def pipe_capacity(D, n, S_percent):
    """圓管在各水深下的流量，回傳 (最大流量, 對應水深比)。水深從 1% 到 100%，每 1% 算一次。"""
    r = D / 2
    best = (0, 0)
    for pct in range(1, 101):
        h = D * pct / 100
        phi = math.acos(1 - h / r)                       # 半圓心角
        A = r * r * (phi - 0.5 * math.sin(2 * phi))      # 通水面積
        R = r / 2 * (1 - math.sin(2 * phi) / (2 * phi))  # 水力半徑
        Q = A * (1 / n) * R ** (2 / 3) * (S_percent / 100) ** 0.5
        best = max(best, (Q, pct))
    return best


def main():
    need_ref_case()
    import openpyxl
    names = openpyxl.load_workbook(str(FILE), read_only=True).sheetnames

    section("1. 各公式使用的參數")
    params = {}
    for s in names:
        v = xlsx_rows(FILE, s, max_row=46, max_col=32)
        f = xlsx_rows(FILE, s, formulas=True, max_row=46, max_col=32)
        row19 = [(c, x) for c, x in enumerate(v[18]) if isinstance(x, (int, float))]
        I = cell(v, "H15")
        formula = next((x for x in f[18] if isinstance(x, str) and x.startswith("=ROUND(F19")), "")
        nums = tuple(x for _, x in row19[:-1])            # 最後一個數字是計算結果 I，前面是參數
        params[s] = nums
        report("info", "-", f"{s}：參數 {nums}，公式 {formula}，I = {I} mm/hr")

    section("2. 不同公式是否誤用同一組參數")
    groups = {}
    for s, p in params.items():
        key = tuple(x for x in p if x not in (1, 0.5))    # 去掉指數 1、0.5，只看 a、b
        groups.setdefault(key, []).append(s)
    for key, ss in groups.items():
        if len(ss) > 1:
            report("error", "E3", f"{'、'.join(ss)} 共用同一組參數 {key}")
    for s, p in params.items():
        if s in ("Horner公式", "Farazdaghi公式") and 1 in p:
            report("error", "E3", f"{s} 的指數 = 1 → 數學上等於 Talbot 公式 I = a / (t + b)")
    Is = {s: cell(xlsx_rows(FILE, s, max_row=15, max_col=8), "H15") for s in names}
    report("info", "-", "實際算出的降雨強度：" + "、".join(f"{s.replace('公式', '')} {i}" for s, i in Is.items())
           + f" → 只有 {len(set(Is.values()))} 種不同的值")

    section("3. 獨立重算 Sherman 工作表")
    v = xlsx_rows(FILE, "Sherman公式", max_row=46, max_col=32)
    A, C, t = cell(v, "H11"), cell(v, "H12"), cell(v, "H13")
    D, n, L, z1, z2 = cell(v, "T10") / 1000, cell(v, "T12"), cell(v, "T13"), cell(v, "T14"), cell(v, "T15")
    I = 363.7 / t ** 0.337
    Q0 = C * I * A / 360
    S = (z1 - z2) / L * 100
    Qmax, pct = pipe_capacity(D, n, S)
    reduce = cell(v, "I25")
    report("ok" if abs(I - cell(v, "S19")) < 0.01 else "error", "-", f"I = 363.7 / {t}^0.337 = {I:.2f} mm/hr（表上 {cell(v, 'S19')}）")
    report("ok" if abs(Q0 - cell(v, "S22")) < 0.001 else "error", "-", f"Q0 = C·I·A/360 = {Q0:.4f} cms（表上 {cell(v, 'S22')}）")
    report("ok" if abs(S - cell(v, "T16")) < 0.01 else "error", "-", f"坡度 S = ({z1} − {z2}) / {L} = {S:.2f}%（表上 {cell(v, 'T16')}）")
    report("ok" if abs(Qmax - cell(v, "Q43")) / Qmax < 0.005 and pct == cell(v, "D28") else "error", "-",
           f"圓管 D = {D} m、n = {n}：{pct}% 水深時流量最大 {Qmax:.3f} cms（表上 {cell(v, 'D28')}%、{cell(v, 'Q43')} cms，表上有逐步四捨五入）")
    report("doubt", "-", f"「扣除貯集滯洪池 1 小時洪峰削減量」{reduce} cms 是直接打上去的數字，看不出來源")
    report("doubt", "-", f"管內流速 {cell(v, 'Q40')} m/s（坡度 {S:.2f}%）：是否超過規範容許最大流速？")

    return summary("管涵檢核")


if __name__ == "__main__":
    main()
