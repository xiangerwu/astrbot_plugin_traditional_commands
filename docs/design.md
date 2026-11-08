# 實作與官方依據

[返回首頁](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/README.md)

## 執行方式

本版包裝已支援插件的 `CommandFilter.filter` 與對應 `StarHandlerMetadata.handler`，不新增第二個指令處理器、不直接跨過路由呼叫上游，也不修改資料庫中的別名。

核心先處理 `/`、@ Bot、群聊／私聊與配置文件，再進行原篩選器、權限檢查及會話插件過濾。只有已喚醒且符合表列詞序的文字，才以簡體指令視圖交給原篩選器。原篩選器依舊解析參數；原處理器依舊負責操作與回覆。

成功匹配時記錄該處理器專用的文字視圖。呼叫原處理器時，`CommandEvent` 只覆蓋 `message_str` 與 `get_message_str()`；發送、停止事件、結果與額外資料均委派給真正事件。原事件與其他插件看到的文字不被全域改寫。原協程／非同步生成器直接返回，保留取消與關閉行為。

CSV 由精確的指令與固定選項組成，較長路徑優先。只接受整個詞元，支援簡繁混用；不將整句文字交給繁簡轉換器。空白和自由文字在相容層保持不變；AstrBot 的原 `GreedyStr` 仍有其自身合併空白的行為。

## 為何不直接保存別名

官方原生別名適合單純指令，但認主會硬比對原始文字前綴，其他插件還會自行解析固定選項。載入事件後核心也會同步保存的指令設定，單純在載入事件加記憶體別名可能被覆蓋。

本版不更動名稱或別名集合，而是在原篩選入口讀取當前有效名稱。使用者改名或移除入口後，不會從固定映射重建該入口；其他處理器已註冊的主名稱／別名優先。既有別名的繁體固定選項同樣回到原處理器。

核心的命令管理 API 因 Key 缺少所需 scope 回傳 403。這不影響本版執行：插件在同一程序直接讀取有效篩選器，不用 API Key。未宣稱已核驗正式環境的所有自訂別名。

## 生命週期與版本

初始化及 `on_plugin_loaded` 掃描目前註冊處理器，依物件身分避免重複包裝。停用時只撤回仍由本插件持有的包裝，不清掉別人後來加的包裝；已失效的舊包裝會直接沿用原行為。

目標插件版本必須與 CSV 一致（忽略前置 `v`）。未知版本不套用補丁、輸出警告，原簡體指令繼續使用。這讓上游更新不會覆蓋本插件原始碼，但不代表未知版本已自動相容。

## 範圍

指令相容只處理表列文字指令。Discord 原生斜線選單、第三方設定說明、回覆文字、互動精靈後續答案、任意其他插件皆不自動翻譯。0.2.0 另提供預設關閉的 [WebUI 核心語系覆蓋](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/webui.md)，只攔截已核對的靜態語系資產。內部篩選器 API 有版本耦合，因此核心先限制於 `>=4.29.4,<4.30`。與其他也包裝相同指令處理器的插件仍需實機驗收。

## 官方與上游來源

- [AstrBot CommandFilter](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.4/astrbot/core/star/filter/command.py)
- [喚醒與指令篩選流程](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.4/astrbot/core/pipeline/waking_check/stage.py)
- [權限篩選器](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.4/astrbot/core/star/filter/permission.py)
- [處理器派發](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.4/astrbot/core/pipeline/context_utils.py)
- [命令管理與設定同步](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.4/astrbot/core/star/command_management.py)
- [Discord 選單擷取](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.4/astrbot/core/platform/sources/discord/discord_platform_adapter.py)
- [通用生圖 1.8.4 固定提交](https://github.com/Railgun19457/astrbot_plugin_image_generation/tree/ec43a459690baf4c13565df9ec45b0c94de065ac)
- [群發助手 1.2.4 固定提交](https://github.com/AlanBacker/astrbot_plugin_bulk_send/tree/7dc0363f07a6bec8ca17bafd0f24c42cf5c69b16)
- [梗Wiki 0.9.0 固定提交](https://github.com/Niox1337/astrbot_plugin_gengwiki/tree/83c4a5b988c6af79d26e1cd5f6955b298591fca4)

其餘插件及版本見 [README 支援表](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/README.md#支援插件與上游倉庫)。公開專案不內嵌上游函式或私人修補碼；測試參考來源另行取得。
