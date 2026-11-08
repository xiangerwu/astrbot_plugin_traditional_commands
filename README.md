# 繁體指令相容

[繁體中文](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/README.md) | [English](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/README.en.md)

![繁體指令相容：熟悉的寫法，相同的功能](https://raw.githubusercontent.com/xiangerwu/astrbot_plugin_traditional_commands/main/assets/intro.png)

讓已支援的 AstrBot 插件同時接受繁體與原有簡體文字指令，例如 `/生圖` 和 `/生图` 都進入原插件。只轉換已確認的指令與固定選項，不翻譯生圖提示詞、預設名稱、記憶內容或聊天文字。

**0.2.1：17 項本機測試通過，已部署並以 API 核對插件狀態與繁體語系資產；Discord 指令實機互動及介面視覺驗收仍待完成，尚未提交插件市場。** 無額外模型費用；介面繁體化使用 OpenCC。指令相容不修改其他插件檔案或保存的指令設定。

## 支援插件與上游倉庫

| 插件 | 已核對版本 | 簡體 → 繁體範例 | 對照數 | 上游倉庫 |
|---|---|---|---:|---|
| 通用生圖 | v1.8.4 | 生图 → 生圖；预设 删除 → 預設 刪除 | 6 | [Railgun19457/astrbot_plugin_image_generation](https://github.com/Railgun19457/astrbot_plugin_image_generation) |
| 表情包管理器 | 5.3.5 | 表情管理 查看图库 → 表情管理 查看圖庫 | 13 | [anka-afk/astrbot_plugin_meme_manager](https://github.com/anka-afk/astrbot_plugin_meme_manager) |
| 認主 | 4.4.1 | 认主 档案 → 認主 檔案；记住 → 記住 | 13 | [QuanWander/astrbot_plugin_master_aware](https://github.com/QuanWander/astrbot_plugin_master_aware) |
| 好感度管理 | v1.2.0 | 管理 计数器 开启 → 管理 計數器 開啟 | 9 | [wuyan1003/likability-level](https://github.com/wuyan1003/likability-level) |
| 更好的幫助 | 1.3.1 | 帮助 → 幫助；菜单 → 菜單 | 2 | [yuexuan6699/astrbot_plugin_help_page](https://github.com/yuexuan6699/astrbot_plugin_help_page) |
| DeepSeek 餘額 | 1.0.1 | 余额 → 餘額；收款码 → 收款碼 | 2 | [Mao19927/astrbot_plugin_dsbalance](https://github.com/Mao19927/astrbot_plugin_dsbalance) |
| 梗Wiki | 0.9.0 | 热梗 → 熱梗；梗插话 关 → 梗插話 關 | 16 | [Niox1337/astrbot_plugin_gengwiki](https://github.com/Niox1337/astrbot_plugin_gengwiki) |
| 群發助手 | v1.2.4 | 群发 暂停 → 群發 暫停；群发助手 → 群發助手 | 12 | [AlanBacker/astrbot_plugin_bulk_send](https://github.com/AlanBacker/astrbot_plugin_bulk_send) |

共 **73 筆**對照：33 個註冊指令／子指令、2 個既有別名、38 個固定選項路徑。它們共用原處理器，不代表新增 73 個功能。完整列表見[指令對照](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/command-catalog.md)。

- 原簡體與現有英文別名繼續可用，也接受已列出的簡繁混合寫法。
- 繁體入口繼承原插件的權限、停用、會話範圍與參數解析；補丁本身不授予新權限。
- 已被 WebUI 移除或改名的原入口不會被重新啟用；若繁體名稱已被其他指令占用，保留原有路由。
- 僅啟用表列版本；目標插件升級到尚未核對的版本時，會記錄警告並保留其原始行為。更新獨立補丁後才恢復該版本的繁體支援。
- 群發助手只支援指令入口與表列子指令，不轉換互動精靈後續答案或篩選表達式。
- 舊 `astrbot_plugin_memewiki` 不在本版支援範圍；梗Wiki 指的是上表 Niox1337 的專案。

## 安裝與使用

需要 AstrBot **4.29.4**（版本限制 `>=4.29.4,<4.30`）、Python **3.12+**。先安裝需要的上游插件，再將本專案目錄放到 `data/plugins/astrbot_plugin_traditional_commands`，或在 WebUI 上傳正式打包的 ZIP，然後重載本插件。不需要 API Key。AstrBot 安裝時會處理 `requirements.txt`；手動安裝請在 AstrBot 的 Python 環境執行 `python -m pip install -r requirements.txt`。

若配置文件的插件範圍不是「全部」，請同時啟用目標插件與「繁體指令相容」。停用本插件會撤回它加上的執行期包裝，原始簡體入口保留。

| 你輸入 | 原插件收到 | 保留的內容 |
|---|---|---|
| `/生圖 雲端貓咪` | `生图 雲端貓咪` | 提示詞「雲端貓咪」 |
| `/認主 記住 我喜歡繁體中文` | `认主 记住 我喜歡繁體中文` | 記憶文字 |
| `/管理 計數器 間隔 50` | `管理 计数器 间隔 50` | 數值 50 |
| `/添加梗 詞 雲端 說明文字` | `添加梗 词 雲端 說明文字` | 梗名稱與說明 |

上表的 `/` 由 AstrBot 喚醒流程處理，仍可使用你原本的喚醒前綴或 @ Bot。管理與資料修改指令仍依上游規則判斷權限，請勿把範例當成測試刪除的建議。

## 可選：WebUI 核心介面繁體化

在插件設定開啟 **WebUI 核心介面繁體化**（`webui_traditional_enabled`，預設關閉），儲存並重載本插件後重新整理頁面。在語言選單選擇新增的「繁體中文」，旗幟留空；原「简体中文」仍可使用。關閉後重載、重新整理即可恢復。

針對已核對的 **4.29.4 WebUI 建置**新增繁體語系載入與選單項目，原 WebUI 檔案不變；簡體及其他語言不受影響。伺服器開關控制選項是否可用，語言選擇由各瀏覽器分別儲存。

不掃描或改寫 DOM、表單值、聊天紀錄、API 回應、模型名稱與使用者輸入。第三方插件頁面、後端傳回的設定說明及寫死在程式中的文字可能仍是簡體，並非全站逐字翻譯。不同 WebUI 建置不會強行套用。詳見[介面繁體化](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/webui.md)。

## 範圍與限制

**Discord 原生 `/` 下拉選單、第三方插件設定說明與插件回覆文字不會自動翻譯。** WebUI 核心語系另由上面的獨立開關處理。官方 4.29.4 Discord 選單不會自動列出別名。

本插件使用 AstrBot 指令篩選器的內部介面，故限制核心版本。未知上游版本、自訂解析方式與其他也修改相同篩選器的插件，需要另行核對。完整指令管理 API 曾回傳 403，因此沒有宣稱取得正式環境所有別名；相容處理直接使用執行中的有效名稱與別名判斷，不依賴遠端 API 快照。

## 文件

| 文件 | 內容 |
|---|---|
| [介面繁體化](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/webui.md) | 開關、支援建置、輸入隔離與恢復 |
| [完整對照](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/command-catalog.md)／[CSV](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/command-mappings.csv) | 支援的全部文字路徑；CSV 也是執行期映射來源 |
| [實作與依據](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/design.md) | 原路由、參數隔離、設定同步與撤回 |
| [開發與測試](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/development.md) | 重現測試、外部參考來源與已知測試邊界 |
| [驗證記錄](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/verification-plan.md) | 已執行項目與正式驗收待辦 |
| [開源與市場發布](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/publishing.md) | 敏感資料檢查、GitHub、打包與市場提交 |
| [美術來源](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/artwork.md) | 介紹圖、透明圖示及角色來源 |

## 授權

新撰寫的程式、文件與對照資料採 [MIT](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/LICENSE)。[OpenCC 純 Python 套件](https://github.com/yichen0831/opencc-python) 及其字典依各自授權提供，不隨本倉庫重新授權。不包含上游原始碼副本、私人整合修補、主機位址、設定或 API Key。上游各自保有原有授權；本專案不代表其作者或 AstrBot 官方背書。

兩張圖為非官方 AI 衍生美術；MIT 不重新授權 AstrBot 原角色與品牌。回報問題請附核心／插件版本、使用的指令與去識別化日誌，不要附秘密或聊天內容。
