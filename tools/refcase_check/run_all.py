# =============================================================
# 一次執行所有 ref case 檢核程式，最後列出總表
#
# 執行方式（在 HydroCoding 資料夾）：
#     python tools\refcase_check\run_all.py
#
# 只想跑其中一支，就直接執行那一支，例如：
#     python tools\refcase_check\check_frequency.py
# =============================================================

import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

CHECKS = [
    ("check_reservoir_routing.py", "牡丹水庫例 01 Fortran 演算", "W13"),
    ("check_frequency.py", "降雨頻率分析_20231008.xlsx", "W6–7"),
    ("check_thiessen_yuanshan.py", "鳶山堰徐昇氏.xlsx", "W4、W10"),
    ("check_detention.py", "滯洪量體計算V2.xlsm、逕流係數0928.xlsx", "W3、W9、W13"),
    ("check_sewer_idf.py", "管涵溝渠檢核計算書", "W11"),
    ("check_soil_conservation.py", "水保相關EXCEL檔（4 個檔）", "W1–2、W10、W11"),
    ("check_duplicates.py", "同名檔案、曾文例 05", "W9、W14"),
]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    rows = []
    for script, target, week in CHECKS:
        print(f"\n\n################ {script}：{target} ################")
        p = subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, encoding="utf-8",
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        print(p.stdout)
        if p.returncode != 0:
            print(p.stderr)
        # 每支程式最後都會印「小結：✅ x　❌ y　⚠️ z」，從這一行讀出數字
        m = re.search(r"小結：✅ (\d+)　❌ (\d+)　⚠️ (\d+)", p.stdout)
        rows.append((target, week, tuple(map(int, m.groups())) if m else None, p.returncode))

    print("\n\n==================== 總表 ====================")
    print(f"{'檢核對象':40s} {'週次':14s}  ✅    ❌    ⚠️")
    for target, week, n, rc in rows:
        if n is None or rc != 0:
            print(f"{target:40s} {week:14s}  程式執行失敗，請看上方錯誤訊息")
        else:
            print(f"{target:40s} {week:14s} {n[0]:3d}   {n[1]:3d}   {n[2]:3d}")
    print("\n各項錯誤與疑點的說明，見教案第十八節「ref case 參考成果檢核紀錄」。")


if __name__ == "__main__":
    main()
