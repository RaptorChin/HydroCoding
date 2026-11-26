# =============================================================
# 檢核：鳶山堰徐昇氏.xlsx（徐昇氏權重、年最大一日／二日暴雨）
# 對應教案：Week 4、Week 10、第十八節 E2、D2、判斷題 6、7
#
# 做法：
#   1. 用各站面積重算權重
#   2. 每一年的流域平均雨量，試著用表內每一組權重重算，看表列值是哪一組算出來的
#   3. 找出缺測年份的處理方式、兩張表之間的矛盾、日期格式錯誤
#
# 執行方式（在 HydroCoding 資料夾）：
#     python tools\refcase_check\check_thiessen_yuanshan.py
# =============================================================

import re
import numpy as np
from common import REF, need_ref_case, xlsx_rows, is_num, report, section, summary

FILE = REF / "hydrological analysis" / "鳶山堰徐昇氏.xlsx"
STATIONS = ["石門", "石門(3)", "十一份", "缺子", "大溪", "八德", "三峽"]
SHEETS = ["最大一日暴雨整理", "最大一日暴雨補遺及校正", "最大二日暴雨", "最大二日暴雨補遺及校正"]

# 「徐昇氏權重」工作表裡的 4 組權重：(說明, 面積所在列, 四捨五入權重所在列)，列號從 1 起算
WEIGHT_BLOCKS = [("全部 7 站", 3, 5), ("102 年後剔除缺子、大溪", 9, 11),
                 ("99 年剔除缺子", 15, 17), ("101 年剔除十一份", 20, 22)]


def year_of(date_text):
    """從「102年8月20日~8月21日」這類文字取出民國年。"""
    m = re.match(r"\s*(\d{2,3})", str(date_text))
    return int(m.group(1)) if m else None


def main():
    need_ref_case()

    section("1. 徐昇氏權重表")
    w_rows = xlsx_rows(FILE, "徐昇氏權重", max_row=22, max_col=10)
    weight_sets = {}
    for name, area_row, round_row in WEIGHT_BLOCKS:
        area = np.array([v if is_num(v) else 0.0 for v in w_rows[area_row - 1][2:9]])
        w = np.array([v if is_num(v) else 0.0 for v in w_rows[round_row - 1][2:9]])
        recalc = np.round(area / area.sum(), 3)
        ok = np.allclose(recalc, w, atol=0.0011)
        report("ok" if ok else "error", "-", f"{name}：面積合計 {area.sum():.3f} km²，權重重算{'一致' if ok else '不一致'}，權重合計 {w.sum():.3f}")
        weight_sets[name] = w

    # 年最大暴雨表第 4 列（D4:J4）也有一組權重
    sheet0 = xlsx_rows(FILE, SHEETS[0], max_row=4, max_col=11)
    old_w = np.array(sheet0[3][3:10], dtype=float)
    weight_sets["年最大暴雨表 D4:J4"] = old_w
    if not np.allclose(old_w, weight_sets["全部 7 站"], atol=0.0011):
        report("doubt", "D2", f"年最大暴雨表用的權重 {old_w.tolist()}，"
               f"與徐昇氏權重表的 {weight_sets['全部 7 站'].tolist()} 不同 → 表內有兩組 7 站權重")

    section("2. 逐年重算流域平均雨量")
    # 缺測的是哪幾站 → 應該改用哪一組權重
    expected_set = {frozenset(["缺子", "大溪"]): "102 年後剔除缺子、大溪",
                    frozenset(["缺子"]): "99 年剔除缺子",
                    frozenset(["十一份"]): "101 年剔除十一份"}
    full_sets = ("全部 7 站", "年最大暴雨表 D4:J4")
    by_year, dates = {}, {}
    for s in SHEETS:
        rows = xlsx_rows(FILE, s, max_row=90, max_col=12)
        n_full, unmatched = 0, []
        for r in rows[4:]:
            date, st, listed, remark = r[2], r[3:10], r[10], (r[11] if len(r) > 11 else None)
            if date is None or not is_num(listed):
                continue
            key = (s.startswith("最大二日"), year_of(date))
            by_year.setdefault(key, []).append((s, listed))
            dates.setdefault(key, []).append((s, str(date).strip()))
            v = np.array([x if is_num(x) else 0.0 for x in st])
            # 「缺測」有兩種寫法：空白，或填 0（其他站都有大雨時，某站接近 0 很不合理）
            others = np.median([x for x in v if x > 5]) if any(x > 5 for x in v) else 0
            missing = [STATIONS[i] for i, x in enumerate(st) if not is_num(x) or (x <= 5 and others > 50)]
            trial = {k: float(np.dot(v, w)) for k, w in weight_sets.items()}
            best = min(trial, key=lambda k: abs(trial[k] - listed))
            if not missing:
                n_full += 1
                continue
            should = expected_set.get(frozenset(missing))
            shown = "、".join(f"{STATIONS[i]}={'空白' if not is_num(x) else x}" for i, x in enumerate(st) if STATIONS[i] in missing)
            label = f"{s}｜{str(date).strip()}（{shown}）"
            note = f"；備註寫「{remark.strip()}」" if isinstance(remark, str) and remark.strip() else ""
            matched = abs(trial[best] - listed) < 0.05
            # 這組權重已經剔除（權重 = 0）的站，才算有正確處理缺測
            removed = {STATIONS[i] for i, w in enumerate(weight_sets[best]) if w == 0}
            extra = [m for m in missing if m not in removed]
            if matched and best in full_sets and should:
                right = trial[should]
                report("error", "E2", f"{label}：表列 {listed:.2f} mm 是用「{best}」權重、把缺測站當 0 算的{note}。"
                       f"改用「{should}」權重應為 {right:.2f} mm（差 {(listed - right) / right * 100:+.0f}%）")
            elif matched and extra:
                report("doubt", "D2", f"{label}：表列 {listed:.2f} mm 是用「{best}」權重算的，"
                       f"{'、'.join(extra)} 的值照算進去{note}。是真的沒下雨，還是缺測？")
            elif matched:
                report("ok", "-", f"{label}：表列 {listed:.2f} mm，已正確改用「{best}」權重")
            else:
                unmatched.append(str(date).strip())
        report("info", "-", f"{s}：資料完整的年份 {n_full} 筆")
        if unmatched:
            report("doubt", "D2", f"{s}：缺測年份 {len(unmatched)} 筆用表內任何一組權重都重算不出表列值"
                   f"（可能另有補遺方法，表內沒有說明）：{'、'.join(unmatched)}")

    section("3. 兩張表之間是否矛盾")
    for (is_2day, yr), items in sorted(by_year.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        vals = {round(v, 2) for _, v in items}
        if len(items) > 1 and len(vals) > 1:
            report("doubt", "D2", f"{'二日' if is_2day else '一日'} 民國 {yr} 年：" +
                   "、".join(f"{s} = {v:.2f}" for s, v in items))

    section("4. 日期")
    # 至少要有「年、月、日的數字」；「日」字省略不算錯
    pattern = re.compile(r"^\s*\d{2,3}\s*年\s*\d{1,2}\s*月\s*\d{1,2}")
    for s in SHEETS:
        for r in xlsx_rows(FILE, s, max_row=90, max_col=11)[4:]:
            if r[2] is not None and is_num(r[10]) and not pattern.match(str(r[2])):
                report("doubt", "D2", f"{s}：日期少了「年」或月日數字不完整「{str(r[2]).strip()}」")
    for (is_2day, yr), items in sorted(dates.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        digits = {re.sub(r"\D", "", d)[len(str(yr)):len(str(yr)) + 4] for _, d in items}   # 年份後的月日數字
        if len(items) > 1 and len(digits) > 1:
            report("doubt", "D2", f"{'二日' if is_2day else '一日'} 民國 {yr} 年，兩張表的日期不同：" +
                   "、".join(f"{s}「{d}」" for s, d in items))

    return summary("鳶山堰徐昇氏")


if __name__ == "__main__":
    main()
