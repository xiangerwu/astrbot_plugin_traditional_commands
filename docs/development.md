# 開發與測試

[返回首頁](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/README.md)

## 目錄

- `main.py`：AstrBot 初始化、插件載入通知及撤回。
- `core/webui.py`：只回傳已核對語系資產的繁體副本，原檔與 API 不變。
- `core/runtime.py`：精確詞元轉換、原篩選器／處理器包裝。
- `docs/command-mappings.csv`：唯一執行期對照來源，不可在打包時省略。
- `tests/`：標準函式庫 unittest，無額外測試框架。
- `assets/intro.png`、`logo.png`：介紹橫幅與透明列表圖示。

## 基本檢查

在專案根目錄執行（先以 `python -m pip install -r requirements.txt` 安裝 OpenCC）：

```bash
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
```

未設定 `ASTRBOT_REFERENCE` 時只執行 5 項獨立測試，12 項原始碼整合測試會明確跳過；不能把這次結果稱為全部整合通過。

## 完整整合測試

測試會從受信任的上游來源以 AST 載入定義，移除匯入與框架註冊裝飾器，保留函式主體不變。請只提供已審閱的來源。測試不呼叫模型、Discord、雲端同步或真正刪除資料。平台事件、發送及資料寫入是測試邊界替身。

將以下來源保存到同一個不提交的參考目錄，檔名需符合左欄。AstrBot 來源一律使用 **v4.29.4**；插件版本需與右欄一致。

| 本機檔名 | 上游路徑 |
|---|---|
| `astrbot__core__star__filter__command.py` | AstrBot：`astrbot/core/star/filter/command.py` |
| `astrbot__core__star__filter__command_group.py` | AstrBot：`astrbot/core/star/filter/command_group.py` |
| `permission.py` | AstrBot：`astrbot/core/star/filter/permission.py` |
| `star_handler.py` | AstrBot：`astrbot/core/star/star_handler.py` |
| `astrbot__core__pipeline__waking_check__stage.py` | AstrBot：`astrbot/core/pipeline/waking_check/stage.py` |
| `master-aware-main.py` | `QuanWander/astrbot_plugin_master_aware` 4.4.1 的 `main.py` |
| `image-main.py` | `Railgun19457/astrbot_plugin_image_generation` 提交 `ec43a459690baf4c13565df9ec45b0c94de065ac` 的 `main.py` |

來源連結見[設計依據](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/design.md)。可用 GitHub CLI 下載個別檔案，例如：

```bash
gh api 'repos/AstrBotDevs/AstrBot/contents/astrbot/core/star/filter/command.py?ref=v4.29.4' --jq .content | python -c 'import base64,sys; from pathlib import Path; Path("research/astrbot__core__star__filter__command.py").write_bytes(base64.b64decode(sys.stdin.read()))'
```

先建立 `research/`，其已被 `.gitignore` 忽略；依表取得其餘檔案後，Linux 執行：

```bash
ASTRBOT_REFERENCE="$PWD/research" python -m unittest discover -s tests -v
```

PowerShell：

```powershell
$env:ASTRBOT_REFERENCE = (Resolve-Path research).Path
python -m unittest discover -s tests -v
```

本次完整執行結果為 **17 項通過、0 跳過**。Windows 沙箱若限制 `asyncio` 建立本機 socketpair，測試可能卡在事件迴圈初始化；請在正常本機終端執行，不要將環境問題改成略過測試。

## 新增映射

先核對相同版本的指令註冊、手動解析與權限流程，再修改 CSV，重跑完整測試並同步 README 與完整對照表。保留所有原寫法。版本升級需重新核對，不能單純移除版本限制。

## WebUI 整合測試補充

本機測試需要 Node.js（只用來載入語系資料、執行官方插值與語言切換函式，不是插件執行期依賴）。同一個參考目錄另需下列檔案：

| 本機檔名 | 來源 |
|---|---|
| `webui-main.js` | 已核對的 WebUI `assets/index-G8Mkbqos.js`，SHA-256 見 `core/webui.py` |
| `webui-zh-CN.js` | 已核對的 WebUI `assets/index-Bs76R583.js`，SHA-256 見 `core/webui.py` |
| `astrbot__dashboard__services__static_file_service.py` | AstrBot v4.29.4：`astrbot/dashboard/services/static_file_service.py` |
| `dashboard__src__i18n__composables.ts` | AstrBot v4.29.4：`dashboard/src/i18n/composables.ts` |

未提供參考檔或 Node.js 時，4 項 WebUI 整合測試會跳過。完整驗證比較全部語系物件鍵名、非字串值、插值參數與程式骨架，並執行官方 `t()` 的原邏輯，確認使用者提供的文字未改寫。測試只用 API 取得的靜態原始碼與本機程序，不操作瀏覽器；不等於全部頁面已完成視覺驗收。

請以二進位模式保存 HTTP 取得的參考資產，避免 Windows 自動把 LF 改成 CRLF，造成與正式資產的 SHA-256 不符。
