# =============================================================
# test_hydraulics.py —— 自動對答案程式（測試程式）
# 目的：把「手算對答案」這個動作交給電腦，每次改完程式跑一次就知道有沒有改壞
#
# 執行方式（在 HydroCoding 資料夾）：
#     python week01\test_hydraulics.py
# =============================================================

from hydraulics import manning_rect

passed = 0   # 通過幾題
failed = 0   # 失敗幾題


def check(name, actual, expected, tol=0.001):
    """
    比對「程式算出來的值」和「手算的標準答案」
        name     這一題的名稱
        actual   程式算出來的值
        expected 手算的標準答案
        tol      容許誤差（手算答案通常只到小數 3 位，所以容許 0.001 的差距）
    """
    global passed, failed   # 表示要修改函數外面的 passed、failed（先知道有這種寫法就好）
    if abs(actual - expected) <= tol:
        print(f"✅ 通過：{name}（程式 {actual:.3f}，手算 {expected:.3f}）")
        passed += 1          # passed = passed + 1 的簡寫
    else:
        print(f"❌ 失敗：{name}（程式 {actual:.3f}，手算 {expected:.3f}）")
        failed += 1


def check_error(name, b, h, n, slope):
    """確認不合理的輸入「一定會被擋下來」"""
    global passed, failed
    try:
        manning_rect(b, h, n, slope)
        print(f"❌ 失敗：{name}（應該被擋下，但程式照算了）")
        failed += 1
    except ValueError:
        print(f"✅ 通過：{name}（有被擋下）")
        passed += 1


# ---------- 第一類：計算結果要等於手算答案 ----------
print("===== 計算結果檢查 =====")
check("第一堂課範例 b=5, h=2", manning_rect(5.0, 2.0, 0.03, 0.001), 11.308)
check("第二堂課練習 b=3, h=1.5", manning_rect(3.0, 1.5, 0.025, 0.002), 6.645)
check("Q-H 表格 b=5, h=3", manning_rect(5.0, 3.0, 0.03, 0.001), 19.443)

# ---------- 第二類：不合理的輸入要被擋下 ----------
print("\n===== 輸入檢核檢查 =====")
check_error("水深 h = 0", 5.0, 0.0, 0.03, 0.001)
check_error("水深 h = -1", 5.0, -1.0, 0.03, 0.001)
check_error("粗糙係數 n = 0", 5.0, 2.0, 0.0, 0.001)
check_error("粗糙係數 n = 3（打錯小數點）", 5.0, 2.0, 3.0, 0.001)
check_error("坡度 = 0", 5.0, 2.0, 0.03, 0.0)

# ---------- 總結 ----------
print(f"\n總計：通過 {passed} 題，失敗 {failed} 題")
if failed == 0:
    print("🎉 全部通過，程式沒有被改壞")
else:
    print("⚠️ 有測試失敗，請檢查最近修改過的地方")
