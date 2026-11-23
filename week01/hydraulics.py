# =============================================================
# hydraulics.py —— 水理計算「工具箱」
# 這個檔案只放函數（工具），不直接執行計算。
# 其他程式可以用 from hydraulics import manning_rect 把工具拿去用。
#
# 檢核分兩級：
#   ❌ 錯誤（直接擋下）：物理上不可能，或幾乎可以確定是打錯字
#   ⚠️ 警告（照算但提醒）：不常見但有可能，請工程師自己確認
# =============================================================


def check_channel(b, n, slope):
    """
    檢查「渠道條件」：渠寬、粗糙係數、坡度
    這三個參數在批次計算不同水深時都不會變，所以只需要檢查一次。
    """
    # ---------- 第一級：錯誤，直接擋下 ----------
    if b <= 0:
        raise ValueError(f"渠寬 b 必須大於 0，目前輸入 b = {b}")
    if n <= 0 or n > 0.5:
        raise ValueError(f"粗糙係數 n 應介於 0～0.5，目前輸入 n = {n}（是否打錯小數點？）")
    if slope <= 0:
        raise ValueError(f"坡度 slope 必須大於 0，目前輸入 slope = {slope}")

    # ---------- 第二級：警告，照算但提醒 ----------
    if n < 0.010 or n > 0.20:
        print(f"⚠️ 警告：n = {n} 不在常見範圍 0.010～0.20，請確認渠道材質")
    if slope > 0.10:
        print(f"⚠️ 警告：坡度 {slope} 大於 10%，屬陡坡渠道，請確認 Manning 公式是否適用")


def manning_rect(b, h, n, slope, check=True):
    """
    矩形渠道 Manning 流量計算（公制）

    輸入：
        b     渠寬 (m)
        h     水深 (m)
        n     Manning 粗糙係數
        slope 渠底坡度 S
        check 是否檢查渠道條件（預設 True）
              如果已經先呼叫過 check_channel()，可以傳入 check=False 省略重複檢查
    輸出：
        Q     流量 (m³/s)
    """
    if check:
        check_channel(b, n, slope)

    # 水深每次都不同，所以每次都要檢查
    if h <= 0:
        raise ValueError(f"水深 h 必須大於 0，目前輸入 h = {h}")

    # ---------- 計算 ----------
    A = b * h
    P = b + 2 * h
    R = A / P
    V = (1 / n) * R ** (2 / 3) * slope ** 0.5
    Q = A * V

    return Q
