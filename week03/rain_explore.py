# =============================================================
# Week 3 / Project 2：雨量資料 QC 工具 —— 第 1 課：認識資料
# 目的：拿到一份陌生的雨量資料時，先「看清楚它長什麼樣子」
# 新學的東西：
#   1. pd.read_excel()：讀取 Excel
#   2. DataFrame 的基本查看：shape、head、tail、dtypes
#   3. describe()：一行指令看出最小值、最大值、平均值
#   4. isna()：找出空白的格子
#   5. 篩選：df[條件]，就像 Excel 的「篩選」功能
#   6. sort_values()：排序
#
# 執行方式（在 HydroCoding 資料夾）：
#     python week03\rain_explore.py
# =============================================================

import pandas as pd

# 讓中文欄位在終端機裡對齊（純粹是顯示用的設定）
pd.set_option("display.unicode.east_asian_width", True)

# ---------- 1. 讀取 Excel ----------
df = pd.read_excel("week03/雨量_練習站A_2024.xlsx")

# ---------- 2. 先看「外觀」：有幾列幾欄？前後幾筆長什麼樣子？ ----------
print("========== 1. 資料大小 ==========")
print(f"共 {df.shape[0]} 列、{df.shape[1]} 欄")   # shape = (列數, 欄數)

print("\n========== 2. 前 5 筆 ==========")
print(df.head())          # head()：看最前面 5 筆，像 Excel 打開時看到的第一頁

print("\n========== 3. 最後 5 筆 ==========")
print(df.tail())          # tail()：看最後 5 筆

print("\n========== 4. 每一欄的資料型態 ==========")
print(df.dtypes)          # str = 文字、float64 = 有小數點的數字

# ---------- 3. 一行看出整欄的統計摘要 ----------
print("\n========== 5. 雨量的統計摘要 ==========")
print(df["雨量(mm)"].describe())
# count = 有值的筆數、mean = 平均、std = 標準差
# min = 最小值、25% / 50% / 75% = 四分位數、max = 最大值

# ---------- 4. 找空白（缺值） ----------
print("\n========== 6. 每一欄有幾個空白 ==========")
print(df.isna().sum())    # isna() 會把每一格變成 True（空白）或 False，sum() 再數有幾個 True

# ---------- 5. 篩選：只看符合條件的列 ----------
# df[條件] 就像 Excel 的「篩選」，只留下條件為 True 的那幾列
print("\n========== 7. 雨量是空白的列 ==========")
print(df[df["雨量(mm)"].isna()])

print("\n========== 8. 雨量小於 0 的列 ==========")
print(df[df["雨量(mm)"] < 0])

# ---------- 6. 排序：找出最大的幾筆 ----------
print("\n========== 9. 時雨量最大的 10 筆 ==========")
print(df.sort_values("雨量(mm)", ascending=False).head(10))
# ascending=False 表示「由大到小」排序（ascending 是「遞增」的意思）
