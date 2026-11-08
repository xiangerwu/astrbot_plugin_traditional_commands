# Traditional Commands for AstrBot

[繁體中文](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/README.md) | [English](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/README.en.md)

![Traditional Commands](https://raw.githubusercontent.com/xiangerwu/astrbot_plugin_traditional_commands/main/assets/intro.png)

Accept verified Traditional Chinese command spellings alongside the original Simplified Chinese commands. Both routes use the original plugin handler, permissions and argument parser. Prompts, names, remembered text and ordinary chat are not translated.

Version 0.2.2 passed 18 local tests and has been deployed, with plugin status and translated locale assets verified through the API. Live Discord command interactions and visual UI acceptance remain untested. Marketplace submission is pending. No additional model calls or API keys are required. Optional WebUI conversion uses the OpenCC dependency in `requirements.txt`.

## Supported plugins

The table lists tested upstream versions, spelling examples, mapping counts and repository links.

| 插件 | 已核對版本 | 簡體 → 繁體範例 | 對照數 | 上游倉庫 |
|---|---|---|---:|---|
| 通用生圖 | v1.8.4 | 生图 → 生圖；预设 删除 → 預設 刪除 | 6 | [Railgun19457/astrbot_plugin_image_generation](https://github.com/Railgun19457/astrbot_plugin_image_generation) |
| 表情包管理器 | 5.3.5、5.3.6 | 表情管理 查看图库 → 表情管理 查看圖庫 | 13 | [anka-afk/astrbot_plugin_meme_manager](https://github.com/anka-afk/astrbot_plugin_meme_manager) |
| 認主 | 4.4.1 | 认主 档案 → 認主 檔案；记住 → 記住 | 13 | [QuanWander/astrbot_plugin_master_aware](https://github.com/QuanWander/astrbot_plugin_master_aware) |
| 好感度管理 | v1.2.0 | 管理 计数器 开启 → 管理 計數器 開啟 | 9 | [wuyan1003/likability-level](https://github.com/wuyan1003/likability-level) |
| 更好的幫助 | 1.3.1 | 帮助 → 幫助；菜单 → 菜單 | 2 | [yuexuan6699/astrbot_plugin_help_page](https://github.com/yuexuan6699/astrbot_plugin_help_page) |
| DeepSeek 餘額 | 1.0.1 | 余额 → 餘額；收款码 → 收款碼 | 2 | [Mao19927/astrbot_plugin_dsbalance](https://github.com/Mao19927/astrbot_plugin_dsbalance) |
| 梗Wiki | 0.9.0 | 热梗 → 熱梗；梗插话 关 → 梗插話 關 | 16 | [Niox1337/astrbot_plugin_gengwiki](https://github.com/Niox1337/astrbot_plugin_gengwiki) |
| 群發助手 | v1.2.4 | 群发 暂停 → 群發 暫停；群发助手 → 群發助手 | 12 | [AlanBacker/astrbot_plugin_bulk_send](https://github.com/AlanBacker/astrbot_plugin_bulk_send) |

There are 73 mappings: 33 registered commands/subcommands, two existing aliases and 38 fixed keyword paths. See the [complete catalog](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/command-catalog.md).

## Installation

Requires AstrBot 4.29.4 (`>=4.29.4,<4.30`) and Python 3.12+. Install the desired upstream plugins first. Place this directory at `data/plugins/astrbot_plugin_traditional_commands`, or upload the packaged ZIP in AstrBot, then reload this plugin. Enable both this plugin and the target plugin in restricted configuration profiles.

Install `requirements.txt` in the AstrBot Python environment if installing manually.

Original Simplified Chinese commands and existing English aliases remain available. For example, `/認主 記住 我喜歡繁體中文` becomes `认主 记住 我喜歡繁體中文` only for the original command parser and handler. The payload remains unchanged. AstrBot continues to enforce wake prefixes, permissions and target plugin/session activation.

## Optional WebUI conversion

Enable `webui_traditional_enabled` (off by default), save/reload this plugin, and refresh the page. Select the new “繁體中文” option (blank flag). The original Simplified Chinese option remains available. Disable, reload and refresh to restore the original text.

The reviewed 4.29.4 main asset gains a locale loader and menu entry, backed by a separate translated locale copy. Original files remain untouched. The server-wide switch makes the option available; each browser stores its own language choice. No DOM manipulation, input-field processing, chat rewriting or API response translation is performed. Unknown dashboard builds fall back to the original asset. Hard-coded labels and third-party plugin pages/descriptions may remain Simplified Chinese. See [WebUI details](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/webui.md).

## Compatibility boundaries

- Runtime wrappers do not modify upstream files or persisted aliases. Disabling this plugin removes its own wrappers.
- Removed or renamed original routes are not recreated. Existing command-name collisions keep their native routing.
- Unknown target versions are skipped with a warning; the original commands continue working. Upgrade this compatibility plugin after the new upstream release has been reviewed.
- Discord native slash-command menus, third-party configuration descriptions and response text are not translated; core WebUI locale conversion is a separate option.
- The bulk-send wizard's later answers and filter expressions are outside this patch.
- The older `astrbot_plugin_memewiki` is not supported. The GengWiki entry above refers to Niox1337's project.
- Full production alias data was unavailable through the API. Routing uses the live effective command names, not a stale inventory.

## Documentation and release

[Design](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/design.md) · [Development and tests](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/development.md) · [Verification](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/verification-plan.md) · [Publishing](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/publishing.md) · [Artwork](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/docs/artwork.md)

New code, documents and mappings use the [MIT license](https://github.com/xiangerwu/astrbot_plugin_traditional_commands/blob/main/LICENSE). Upstream implementations and private deployment snapshots are not distributed. The unofficial AI-generated artwork references AstrBot's character; MIT does not relicense the original character or brand.
