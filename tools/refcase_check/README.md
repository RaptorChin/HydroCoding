# ref case 參考成果檢核工具

這個資料夾裡的程式，用 Python **獨立重算** `ref case/` 裡的過往成果，找出隱藏的錯誤。
檢核結果的說明，見教案 `水利工程師多語言程式學習完整規劃v2026.11.md` 第十八節。

> 核心觀念：參考成果不是標準答案。程式跟參考成果對不上時，可能是程式錯、參考成果錯，
> 或兩邊定義不同；對得上，也不代表兩邊都對。

---

## 一、第一次使用前的準備

在 **HydroCoding 資料夾**開啟終端機，安裝讀取舊版 `.xls` 需要的套件：

```text
python -m pip install xlrd
```

如果也想擷取 `.xlsm` 裡的 VBA 巨集（`extract_macros.py`），再安裝：

```text
python -m pip install oletools
```

其他用到的套件（numpy、scipy、openpyxl）已經安裝過了。

---

## 二、怎麼執行

一律在 **HydroCoding 資料夾**執行（不是在這個資料夾裡）。

一次全部跑完，最後會列出總表：

```text
python tools\refcase_check\run_all.py
```

只跑其中一支：

```text
python tools\refcase_check\check_frequency.py
```

---

## 三、每支程式在檢核什麼

| 程式 | 檢核對象 | 教案週次 | 第十八節編號 |
|---|---|---|---|
| `check_reservoir_routing.py` | 牡丹水庫例 01 的 Fortran 演算成果（用二分法獨立重算） | W13 | E1、D3 |
| `check_frequency.py` | `降雨頻率分析_20231008.xlsx`（用 scipy 精確分布獨立重算） | W6–7 | E5、D1 |
| `check_thiessen_yuanshan.py` | `鳶山堰徐昇氏.xlsx`（權重、缺測處理、兩表矛盾、日期） | W4、W10 | E2、D2 |
| `check_detention.py` | `滯洪量體計算V2.xlsm`、`逕流係數0928.xlsx`（標題與參數、CN、面積） | W3、W9、W13 | E4、D4 |
| `check_sewer_idf.py` | 管涵溝渠檢核計算書（5 種降雨強度公式的參數） | W11 | E3 |
| `check_soil_conservation.py` | 水保相關 4 個檔（排水溝、坡度、土方、經費） | W1–2、W10、W11 | E7、D5、D6 |
| `check_duplicates.py` | 同名檔案的內容、曾文例 05 是否誤用牡丹資料 | W9、W14 | E6 |

以下兩支不是檢核，是輔助閱讀用的，結果存在 `output/` 資料夾：

| 程式 | 用途 |
|---|---|
| `survey_excel.py` | 掃描 ref case 所有 Excel 檔的工作表與前幾列，產生目錄 `output/excel_survey.txt` |
| `extract_macros.py` | 把 VBA 巨集與 Lotus 1-2-3 巨集存成文字檔，不用打開 Excel 就能讀 |

`common.py` 是共用函數（路徑、讀 Excel、回報格式），不用直接執行。

---

## 四、怎麼看結果

| 符號 | 意思 |
|---|---|
| ✅ | 獨立重算的結果與原檔一致 |
| ❌ | 確定有錯誤或不一致 |
| ⚠️ | 疑點，要查原始資料或問原作者才能確認 |
| ℹ️ | 資訊，不是對錯判斷 |

方括號裡的編號（例如 `[E2]`）對應教案第十八節的表格。`[-]` 表示沒有編號的一般檢查。

---

## 五、注意事項

- **`output/` 資料夾不會進 git**（已在本資料夾的 `.gitignore` 排除），因為裡面有從 ref case 擷取的工程資料。
- 程式裡的路徑都是從 HydroCoding 資料夾往下找 `ref case/`。如果 ref case 換了位置或改了資料夾名稱，要改 `common.py` 的 `REF`。
- 程式找資料夾時不寫死人名（例如用 `Conditions.org` 找 Fortran 的執行資料夾），避免把個人資訊放進程式碼。
- 這些檢核程式本身也可能有錯。上課時可以把它們當教材：讀懂邏輯、故意改壞參數，看它能不能抓到錯誤。
  實例：`check_thiessen_yuanshan.py` 第一版只把「空白」當缺測，漏掉了「填 0 當缺測」的寫法，
  所以漏抓了民國 99 年的錯誤，修正後才抓到。

---

## 六、新增檢核

每檢核一份新的參考成果（教案第十八節標 ⬜ 的檔案）：

1. 參考現有程式，新增一支 `check_xxx.py`，`import common` 使用共用函數。
2. 用 `report("ok" / "error" / "doubt" / "info", "編號", "說明")` 回報結果，最後呼叫 `summary("名稱")`。
3. 把新程式加進 `run_all.py` 的 `CHECKS` 清單。
4. 回教案第十八節更新檢核狀態。
