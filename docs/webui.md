# WebUI 核心介面繁體化

[返回首頁](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/README.md)

## 使用方式

1. 安裝本插件的 `requirements.txt`。AstrBot 一般安裝流程會處理依賴；手動安裝時請在 AstrBot 的 Python 環境執行 `python -m pip install -r requirements.txt`。
2. 在本插件設定開啟「WebUI 核心介面繁體化」，儲存並重載本插件。
3. WebUI 的語言保持「简体中文」，重新整理頁面。核心語系文案會顯示繁體；官方語言選單本身仍可能顯示「简体中文」。
4. 要恢復原樣，關閉開關、重載插件並重新整理。已開啟的頁面在重新整理前會繼續使用記憶體中的舊語系。

這是伺服器層級的開關，影響所有選用簡體語系的 WebUI 使用者。英文、日文及俄文語系檔不會改變。不需重啟整個 AstrBot。

## 已確認的可行性

AstrBot 4.29.4 的核心語系使用獨立非同步 JavaScript 資料模組；靜態檔案路由在回傳資產前會呼叫 `StaticFileService.resolve_static_file()`。本插件暫時包裝這個解析方法，只對已核對的語系資產回傳繁體副本的路徑。

這不是官方全站語系擴充 API，而是有限版本的執行期相容處理。原本的路徑驗證、檔案回應、壓縮與 `no-cache` 標頭仍由官方流程處理；不修改原 `data/dist`，也不插入腳本、不放寬 iframe 隔離、不掃描 DOM。

目前支援的靜態資產：

- 路徑：`assets/index-Bs76R583.js`
- SHA-256：`08972d27cc3f86f6c591728aae427491626e73e24e324abcd94a6fa2f2873c31`
- 已核對核心：AstrBot 4.29.4

相同核心版本也可能有不同 WebUI 建置。路徑或內容不符時保留原檔，不能只靠版本號推定相容；新增建置前需重新審閱語系資產與跑完整測試。

## 保留哪些內容

只轉換語系模組的顯示字串，使用 OpenCC `s2twp`。物件鍵名、程式結構、非字串值、插值占位符、網址、內嵌程式碼、HTML 標籤及跳脫序列保持不變。原翻譯函式之後才代入使用者名稱等動態值，因此動態內容不會送進 OpenCC。

下列內容不進入這個轉換流程：

- 表單值、輸入框、API Key、模型名稱、會話名稱。
- 聊天訊息、生成結果、記憶資料、API 回應。
- 其他 JavaScript、HTML、JSON 或圖片資產。
- 第三方插件自己的頁面、設定說明及回覆文字。

本版也不修改核心程式中寫死的標籤。因此可能同時看到繁體與簡體，不宣稱整個生態系全部繁體化。翻譯採自動字形／用詞轉換，不等於逐句人工校訂的官方繁體語系。

## 開關與檔案

轉換副本放在 AstrBot `plugin_data/astrbot_plugin_traditional_commands/webui/`，不放入公開倉庫。關閉或卸載時撤回本插件的解析包裝，原語系立即恢復供應；不刪除原始 WebUI 或使用者資料。

缺少 OpenCC、未知內容或副本寫入失敗時，維持原 WebUI。指令相容功能仍可運作。未改變插件保存的簡體指令及其他配置。

## 驗證與限制

使用實際語系模組比較完整物件結構與原官方插值函式，確認輸入的簡體、繁體、網址和 HTML 字樣原樣代入。另測開關、重複載入、撤回、路徑驗證、未知建置與磁碟寫入失敗。

已在正式環境安裝、開啟並重載，API 取得的繁體語系檔與本機預期位元組完全一致；原有 170 筆指令／事件元件資料未變，未列出載入失敗插件。全程未操作瀏覽器，所有頁面的視覺或互動驗收仍待完成。

## 原始碼依據

- [官方語系載入表](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.4/dashboard/src/i18n/translations.ts)
- [翻譯、插值與語言切換](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.4/dashboard/src/i18n/composables.ts)
- [靜態檔案解析](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.4/astrbot/dashboard/services/static_file_service.py)
- [靜態回應與快取](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.4/astrbot/dashboard/api/static_files.py)
- [官方插件頁面機制](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.4/docs/zh/dev/star/guides/plugin-pages.md)
- [OpenCC 純 Python 轉換器與授權](https://github.com/yichen0831/opencc-python)
