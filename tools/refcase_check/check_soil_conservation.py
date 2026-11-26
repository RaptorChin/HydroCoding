# =============================================================
# 檢核：其他/水保相關EXCEL檔/ 的 4 個檔案
#   水理計算-1.xls（排水溝、涵管）、坡度25x25.xls（坵塊法坡度）、
#   土方計算-新.xls（方格法土方，Lotus 巨集）、工程經費計算.xls
# 對應教案：Week 1–2 延伸、Week 3、Week 10、Week 11、選修 D、
#           第十八節 E7、D5、D6、判斷題 12～16
#
# 執行方式（在 HydroCoding 資料夾）：
#     python tools\refcase_check\check_soil_conservation.py
# =============================================================

import math
import numpy as np
from common import REF, need_ref_case, open_xls, xls_rows, report, section, summary

FOLDER = REF / "其他" / "水保相關EXCEL檔"
N_MANNING = 0.012          # 從表上數值反推出來的粗糙係數
C_GRADED, C_UNGRADED = 0.96, 0.85    # 反推出來的逕流係數（有整地 / 未整地）


def slope_class(S):
    """山坡地土地可利用限度分類標準的坡度分級。"""
    for k, upper in enumerate([5, 15, 30, 40, 55, 100], start=1):
        if S <= upper:
            return k
    return 7


def check_drainage():
    section("1. 水理計算-1.xls：排水溝逐列重算")
    rows = xls_rows(FOLDER / "水理計算-1.xls")
    bad = 0
    elev = []
    for r in rows[3:22]:
        name, I, a1, a2, Q, Qp, QS = r[0], r[1], r[2] or 0, r[3] or 0, r[4], r[5], r[6]
        b, h, A, P, S, V, Qd = r[8], r[10], r[11], r[12], r[14], r[15], r[16]
        Qc = (C_UNGRADED * a1 + C_GRADED * a2) * I / 360
        Ac, Pc = b * h, b + 2 * h
        Vc = (Ac / Pc) ** (2 / 3) * (S / 100) ** 0.5 / N_MANNING
        errs = []
        if abs(Qc - Q) > 0.0006: errs.append(f"Q {Q}→{Qc:.4f}")
        if abs(Ac - A) > 1e-6 or abs(Pc - P) > 1e-6: errs.append("斷面")
        if abs(Vc - V) / V > 0.002: errs.append(f"V {V}→{Vc:.3f}")
        if abs(Vc * Ac - Qd) > 0.0011: errs.append(f"Qd {Qd}→{Vc * Ac:.3f}")
        if abs(Q + Qp - QS) > 0.0002: errs.append("ΣQ")
        if errs:
            bad += 1
            report("error", "-", f"{name}：{'、'.join(errs)}")
        elev.append((name, r[17], r[18], S))
    report("ok" if bad == 0 else "error", "-", f"19 條排水溝的 Q、斷面、V、Qd、ΣQ：{19 - bad} 條一致（C = {C_GRADED}/{C_UNGRADED}、n = {N_MANNING}）")

    total = rows[22]
    s1 = sum((r[2] or 0) for r in rows[3:22]); s2 = sum((r[3] or 0) for r in rows[3:22])
    if abs(total[2] - s1) > 0.001 or abs(total[3] - s2) > 0.001:
        report("error", "E7", f"第 23 列合計：未整地 {total[2]:.4f} ha（實際 {s1:.4f}）、有整地 {total[3]:.4f} ha（實際 {s2:.4f}）")
    same = [e for e in elev if (e[1], e[2]) == (105.6, 105.4)]
    if len(same) > 5:
        slopes = sorted(e[3] for e in same)
        report("doubt", "D5", f"{len(same)} 條溝的溝底高程都是 105.6 → 105.4 m，但坡度從 {slopes[0]:.2f}% 到 {slopes[-1]:.2f}% 都有 → 疑似複製未更新")
    fast = [f"{r[0]} {r[15]} m/s" for r in rows[3:22] if r[15] > 4]
    report("doubt", "-", f"流速超過 4 m/s 的溝：{'、'.join(fast)}（是否超過容許最大流速？判斷題 14）")

    section("2. 水理計算-1.xls：涵管（非滿管）")
    for r in rows[28:]:
        if not str(r[0]).strip():
            continue
        D, h, A, S, V = r[4], r[5], r[6], r[9], r[10]
        rr = D / 2
        th = 2 * math.acos((rr - h) / rr)
        Ac, Pc = rr * rr * (th - math.sin(th)) / 2, rr * th
        Vc = (Ac / Pc) ** (2 / 3) * (S / 100) ** 0.5 / N_MANNING
        ok = abs(Ac - A) < 0.0002 and abs(Vc - V) / V < 0.005
        report("ok" if ok else "error", "-", f"{r[0]}：D = {D} m、水深 {h:.2f} m → A {Ac:.4f}（表 {A:.4f}）、V {Vc:.3f}（表 {V}，差 {(V - Vc) / Vc * 100:+.1f}%，表上中間值有四捨五入）")
    qs = {round(r[3], 4) for r in rows[28:] if str(r[0]).strip()}
    if len(qs) == 1:
        report("doubt", "D5", f"3 段涵管的需求流量都是 {qs.pop()} cms，表上沒有集水面積與降雨強度，看不出來源")


def check_slope():
    section("3. 坡度25x25.xls：坵塊法坡度")
    wb = open_xls(FOLDER / "坡度25x25.xls")
    for name, offset in (("Sheet1", 1), ("Sheet1 (2)", 1), ("Sheet1 (3)", 1)):   # 三張表的 A 欄都是空白或編號
        sh = wb.sheet_by_name(name)
        n, bad = 0, 0
        for r in range(1, sh.nrows):
            v = sh.row_values(r)
            try:
                dh, cnt, L, S, cls = v[offset], v[offset + 1], v[offset + 2], v[offset + 3], v[offset + 5]
                Sc = cnt * math.pi * dh / (8 * L) * 100
            except (TypeError, ValueError, IndexError):
                continue
            if not isinstance(S, float):
                continue
            n += 1
            if abs(Sc - S) > 0.01 or slope_class(Sc) != int(cls):
                bad += 1
                report("error", "-", f"{name} 第 {r + 1} 列：表上 {S}% / {cls} 級，重算 {Sc:.2f}% / {slope_class(Sc)} 級")
        report("ok" if bad == 0 else "error", "-", f"{name}：{n} 格的坡度 S = nπΔh/(8L) 與坡度分級，{n - bad} 格一致")
    sh = wb.sheet_by_name("Sheet1 (3)")
    area = [sh.cell_value(r, 7) for r in range(1, 27)]
    area_fix = [sh.cell_value(r, 8) for r in range(1, 27)]
    aS = [sh.cell_value(r, 9) for r in range(1, 27)]
    h31 = sh.cell_value(30, 7)
    full = [r + 1 for r in range(1, 27) if abs(sh.cell_value(r, 7) - 625) < 1e-6]
    avg = sum(aS) / sum(area_fix)
    report("ok" if abs(avg - sh.cell_value(32, 7)) < 0.001 else "error", "-", f"Sheet1 (3) 平均坡度 = {sum(aS):,.2f} / {sum(area_fix):,.2f} = {avg:.4f}%（表上 {sh.cell_value(32, 7):.4f}%）")
    if abs(h31 - sum(area)) > 1:
        report("doubt", "D6", f"Sheet1 (3) H31 合計 {h31:,.2f} m²，但該欄實際加總 {sum(area):,.2f} m²，"
               f"差 {sum(area) - h31:,.0f} m²；面積 = 625 的完整方格在第 {full} 列（備註「須減去分母」）")


def check_earthwork():
    section("4. 土方計算-新.xls：方格法（重算 Lotus 巨集）")
    sh = open_xls(FOLDER / "土方計算-新.xls").sheet_by_index(1)
    o_rows = [r for r in range(sh.nrows) if str(sh.cell_value(r, 0)).startswith("O.")]
    num = lambda x: float(x) if isinstance(x, float) else np.nan
    O = np.array([[num(sh.cell_value(r, c)) for c in range(1, 52)] for r in o_rows])
    D = np.array([[num(sh.cell_value(r + 1, c)) for c in range(1, 52)] for r in o_rows])
    dh = O - D
    cell_area = 625.0
    # 讀出巨集上次執行時輸入的範圍（B176 行數、B177 列數）
    cols, nrows_ = int(sh.cell_value(175, 1)), int(sh.cell_value(176, 1))
    sub = dh[:nrows_, :cols]
    cut_lotus = fill_lotus = 0.0          # 忠實重現：空白當 0
    cut_full = fill_full = 0.0            # 只算四個角都有資料的方格
    mixed = full = 0
    for i in range(nrows_ - 1):
        for j in range(cols - 1):
            q = sub[i:i + 2, j:j + 2]
            s = np.nansum(q)
            cut_lotus, fill_lotus = (cut_lotus + s, fill_lotus) if s > 0 else (cut_lotus, fill_lotus + s)
            if not np.isnan(q).any():
                full += 1
                mixed += int((q > 0).any() and (q < 0).any())
                cut_full, fill_full = (cut_full + s, fill_full) if s > 0 else (cut_full, fill_full + s)
    listed = {}
    for r in range(sh.nrows):
        t = "".join(str(sh.cell_value(r, c)) for c in range(1, 4))
        if "累計" in t:
            listed[t.strip()[:2]] = float(sh.cell_value(r, 4))   # Lotus 巨集把結果寫成文字，要轉成數字
    k = cell_area / 4
    report("ok" if abs(cut_lotus * k - listed.get("挖土", 0)) < 0.1 else "error", "-",
           f"挖方：Σ高差 {cut_lotus:.1f} m × 625 / 4 = {cut_lotus * k:,.1f} m³（表上 {listed.get('挖土')}）")
    report("ok" if abs(fill_lotus * k - listed.get("填土", 0)) < 0.1 else "error", "-",
           f"填方（空白當 0，忠實重現巨集）：{fill_lotus * k:,.1f} m³（表上 {listed.get('填土')}）")
    report("doubt", "-", f"只算 {full} 個完整方格：挖方 {cut_full * k:,.1f}、填方 {fill_full * k:,.1f} m³；"
           f"其中 {mixed} 格同時有挖有填，格內會互相抵銷（判斷題 12）")


def check_cost():
    section("5. 工程經費計算.xls")
    rows = xls_rows(FOLDER / "工程經費計算.xls")
    items = [r for r in rows[:20] if isinstance(r[2], float)]
    bad = [i + 1 for i, r in enumerate(items) if abs(round(r[2] * r[3]) - r[4]) > 0.5]
    subtotal = sum(r[4] for r in items)
    fee = rows[22][4]
    report("ok" if not bad else "error", "-", f"{len(items)} 個工項 數量 × 單價 = 複價" + ("，全部一致" if not bad else f"，不符：{bad}"))
    report("ok" if abs(subtotal - rows[21][4]) < 0.5 else "error", "-", f"小計 {subtotal:,.0f} 元（表上 {rows[21][4]:,.0f}）")
    report("ok" if abs(round(subtotal * 0.15) - fee) < 1 else "error", "-", f"管理費 15% = {subtotal * 0.15:,.0f} 元（表上 {fee:,.0f}）")
    report("info", "-", f"修正管理費 {rows[24][4]:,.0f} 元，使總經費湊整為 {rows[25][4]:,.0f} 元（判斷題 16）")


def main():
    need_ref_case()
    check_drainage()
    check_slope()
    check_earthwork()
    check_cost()
    return summary("水保相關")


if __name__ == "__main__":
    main()
