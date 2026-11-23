# =============================================================
# test_trap.py —— 梯形渠道（AI 版本）的測試程式
#
# 執行方式（在 HydroCoding 資料夾）：
#     python week01\test_trap.py
# =============================================================

from hydraulics_ai import manning_trap


def check(name, actual, expected, tol=0.001):
    """比對程式算出來的值和手算的標準答案"""
    if expected is None:
        print(f"⏸️ 跳過：{name}（還沒填手算答案，程式算出 {actual:.3f}）")
    elif abs(actual - expected) <= tol:
        print(f"✅ 通過：{name}（程式 {actual:.3f}，手算 {expected:.3f}）")
    else:
        print(f"❌ 失敗：{name}（程式 {actual:.3f}，手算 {expected:.3f}）")


# 共同條件：b = 5 m, h = 2 m, n = 0.03, S = 0.001，只改變邊坡比 z

# z = 0 就是矩形，答案應該和第一堂課一樣
check("z = 0（矩形）", manning_trap(5.0, 2.0, 0.03, 0.001, z=0), 11.308)

# z = 1（1:1 邊坡），答案已經由老師手算好
check("z = 1（1:1 邊坡）", manning_trap(5.0, 2.0, 0.03, 0.001, z=1), 17.701)

# z = 2（2:1 邊坡）—— 👉 請你自己手算，把下面的 None 換成你算出來的 Q
expected_z2 = 22.494
check("z = 2（2:1 邊坡）", manning_trap(5.0, 2.0, 0.03, 0.001, z=2), expected_z2)

# z = 1.5（1.5:1 邊坡）—— 👉 自己手算，把下面的 None 換成你算出來的 Q
expected_z1_5 = 20.195
check("z = 1.5（1.5:1 邊坡）", manning_trap(5.0, 2.0, 0.03, 0.001, z=1.5), expected_z1_5)