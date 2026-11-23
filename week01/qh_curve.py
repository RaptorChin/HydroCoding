# =============================================================
# Week 1 / Project 1：Manning 水理計算器 —— 第 4 版
# 目的：批次計算不同水深的流量，畫出 Q-H 曲線（水位流量率定曲線）
# 新學的東西：
#   1. import：從工具箱（hydraulics.py）拿出函數來用
#   2. list（清單）與 for 迴圈：重複做同一件事很多次
#   3. matplotlib：畫圖
#   4. （第 4 版新增）不會變的參數在迴圈外只檢查一次
#   5. （第 4 版新增）pandas：把結果輸出成 Excel
# =============================================================

import matplotlib.pyplot as plt          # 畫圖工具，習慣簡稱為 plt
import pandas as pd                      # 表格資料工具，習慣簡稱為 pd
from hydraulics import check_channel, manning_rect   # 從自己寫的工具箱拿出兩支工具

# ---------- 1. 固定的渠道條件 ----------
b = 3.0        # 渠寬 (m)
n = 0.03       # Manning 粗糙係數
slope = 0.001  # 渠底坡度

# ---------- 2. 準備一串水深：0.1, 0.2, 0.3, ... , 3.0 m ----------
depths = []                    # 建立一個空的清單（像一個空的 Excel 欄位）
for i in range(1, 31):         # i 會依序等於 1, 2, 3, ..., 30（不含 31）
    depths.append(i * 0.1)     # 把 i × 0.1 放進清單的最後面

# ---------- 3. 每一個水深都算一次流量 ----------
check_channel(b, n, slope)     # 渠道條件不會隨水深改變，在迴圈「外面」檢查一次就好

flows = []                     # 用來裝計算結果的空清單
for h in depths:               # 從 depths 清單裡，一次拿一個水深出來
    Q = manning_rect(b, h, n, slope, check=False)   # 上面檢查過了，這裡不再重複檢查
    flows.append(Q)

# ---------- 4. 印出表格 ----------
print("  水深 h (m) | 流量 Q (m³/s)")
print("-------------+--------------")
for h, Q in zip(depths, flows):   # zip：把兩個清單像拉鍊一樣一對一配對
    print(f"  {h:10.1f} | {Q:12.3f}")

# ---------- 5. 輸出 Excel ----------
# DataFrame 就像一張 Excel 工作表：左邊是欄位名稱，右邊是那一欄的資料
df = pd.DataFrame({
    "水深 h (m)": depths,
    "流量 Q (m³/s)": flows,
})
df["水深 h (m)"] = df["水深 h (m)"].round(2)       # 水深四捨五入到小數 2 位
df["流量 Q (m³/s)"] = df["流量 Q (m³/s)"].round(3)  # 流量四捨五入到小數 3 位

df.to_excel("week01/QH曲線.xlsx", index=False)   # index=False：不要輸出最左邊的列編號
print("\nExcel 已存成 week01/QH曲線.xlsx")

# ---------- 6. 畫 Q-H 曲線 ----------
# 設定中文字型（Windows 內建的「微軟正黑體」），否則中文會變成方塊
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]
plt.rcParams["axes.unicode_minus"] = False

plt.figure(figsize=(7, 5))                       # 開一張 7 × 5 英吋的圖紙
plt.plot(flows, depths, marker="o", markersize=3)  # 橫軸 Q、縱軸 h（率定曲線慣例）
plt.xlabel("流量 Q (m³/s)")
plt.ylabel("水深 h (m)")
plt.title(f"矩形渠道 Q-H 曲線（b = {b} m, n = {n}, S = {slope}）")
plt.grid(True, linestyle="--", alpha=0.5)        # 加上虛線格線

plt.savefig("week01/QH曲線.png", dpi=150)          # 存成圖片檔
print("圖片已存成 week01/QH曲線.png")
plt.show()                                       # 跳出視窗顯示圖（關掉視窗程式才會結束）
