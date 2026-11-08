# 開源與插件市場發布

[返回首頁](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/README.md)

本專案參照 [靜默連結閱讀](https://github.com/xiangerwu/astrbot_plugin_link_context) 的 MIT、雙語 README、文件分類、根目錄圖示與介紹圖安排。公開倉庫為 [astrbot_plugin_traditional_commands](https://github.com/xiangerwu/astrbot_plugin_traditional_commands)；尚未提交插件市場。

## 發布前

1. 完成[完整測試](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/development.md)，核對 `metadata.yaml` 版本與實際相容範圍。
2. 確認 `metadata.yaml` 的 `repo` 指向本公開倉庫。
3. 將 README、文件與圖片連結改成該倉庫的 GitHub／raw 永久網址，避免 AstrBot WebUI 將相對 `.md` 連結導向自己的頁面。
4. 檢查 Git 待提交檔案：只包含本專案程式、CSV、文件、MIT 與兩張圖片。不得提交 `.env`、`research/`、參考上游原始碼、執行資料、ZIP、虛擬環境或私人整合修補。
5. 確認授權後才 commit、push；若要依賴自動市場更新，先完成正式環境驗收。

## 打包

安裝必需：`main.py`、`metadata.yaml`、`core/`、`docs/command-mappings.csv`。發行包一併保留 README、中英文文件、`LICENSE`、`assets/intro.png` 與根目錄 `logo.png`。不得攤平目錄。

0.2.2 須包含 `requirements.txt`（OpenCC）與 `_conf_schema.json`（預設關閉的介面繁體化開關）。不要打包執行時產生的 WebUI 語系副本；這些副本保存在 AstrBot 的插件資料目錄。

推送已通過驗證的提交後，可在已建立的 Git 倉庫中使用：

```bash
mkdir -p dist
git archive --format=zip --output=dist/astrbot_plugin_traditional_commands-0.2.2.zip HEAD
```

只包含已追蹤且已提交檔案；打包前檢查 `git status --short`。本機 `dist/` 不提交。

## 市場

公開倉庫不等於市場上架。依 [AstrBot 官方發布說明](https://docs.astrbot.app/dev/star/plugin-publish.html)，到 [插件發布平台](https://cloud.astrbot.app/publish) 提交倉庫並核對名稱、圖示、版本、支援平台及標籤。是否收錄，以平台審核及市場實際結果為準。

目前 metadata 宣告 Discord 為預計支援平台；程式依賴共同文字指令流程，但本次未在正式 Discord 驗收，更未宣稱所有 adapter 都實測。
