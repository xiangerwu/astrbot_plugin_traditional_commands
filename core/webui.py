"""Serve a translated copy of a reviewed locale asset, never edit the WebUI."""

import hashlib
import re
from functools import wraps
from pathlib import Path

# AstrBot 4.29.4 deployed dashboard asset, reviewed as a locale data module.
# Unknown builds must keep their original asset instead of guessing its role.
LOCALE_ASSET = "assets/index-Bs76R583.js"
LOCALE_SHA256 = "08972d27cc3f86f6c591728aae427491626e73e24e324abcd94a6fa2f2873c31"
MAIN_ASSET = "assets/index-G8Mkbqos.js"
MAIN_SHA256 = "046e8be9ca52b35001407c5755995d80b5d7abd6d892f7e6e2717315b9b9b190"
TRADITIONAL_ASSET = "assets/traditional-commands-zh-TW.js"
LITERALS = re.compile(
    r'"(?:\\[\s\S]|[^"\\])*"|\'(?:\\[\s\S]|[^\'\\])*\'|`(?:\\[\s\S]|[^`\\])*`'
)
PROTECTED = re.compile(
    r"https?://[^\s<>\"'`]+|(?:\\`|`)[\s\S]*?(?:\\`|`)"
    r"|\$?\{[^{}]*\}|<[^>]*>|\\(?:u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|[\s\S])"
)


def translate_text(value, converter):
    """Keep interpolation, links, inline code, HTML tags and escapes literal."""
    result = []
    end = 0
    for match in PROTECTED.finditer(value):
        result.extend((converter.convert(value[end : match.start()]), match.group()))
        end = match.end()
    result.append(converter.convert(value[end:]))
    return "".join(result)


def translate_asset(source, converter):
    if hashlib.sha256(source).hexdigest() != LOCALE_SHA256:
        raise ValueError("未核對的 WebUI 語系檔，維持原始內容")
    text = source.decode("utf-8")

    def replace(match):
        literal = match.group()
        if text[match.end() :].lstrip().startswith(":"):
            return literal  # Object keys identify behavior; never translate keys.
        value = translate_text(literal[1:-1], converter)
        return literal[0] + value + literal[-1]

    return LITERALS.sub(replace, text).encode("utf-8")


def add_language_option(source):
    """Extend only the reviewed loader, menu and saved-language allowlists."""
    if hashlib.sha256(source).hexdigest() != MAIN_SHA256:
        raise ValueError("未核對的 WebUI 主程式，維持原始介面")
    text = source.decode("utf-8")
    loader = '"zh-CN":()=>Te(()=>import("./index-Bs76R583.js"),[]).then(e=>e.default)'
    option = '{value:"zh-CN",label:"简体中文",flag:"🇨🇳"}'
    locales = '["zh-CN","en-US","ru-RU","ja-JP"]'
    changes = (
        (
            loader,
            loader
            + ',"zh-TW":()=>Te(()=>import("./traditional-commands-zh-TW.js"),[]).then(e=>e.default)',
            1,
        ),
        (option, option + ',{value:"zh-TW",label:"繁體中文",flag:""}', 1),
        (locales, '["zh-CN","zh-TW","en-US","ru-RU","ja-JP"]', 2),
    )
    for before, after, count in changes:
        if text.count(before) != count:
            raise ValueError("WebUI 語言入口不同，維持原始介面")
        text = text.replace(before, after)
    return text.encode("utf-8")


class WebUILocale:
    def __init__(self, service_type, data_dir, logger):
        self.service_type = service_type
        self.data_dir = Path(data_dir)
        self.logger = logger
        self.wrapper = None
        self.original = None
        self.active = False
        self.converter = None
        self.cached = None
        self.warned = False

    def install(self):
        if self.active:
            return
        from opencc import OpenCC

        self.converter = OpenCC("s2twp")
        self.original = self.service_type.resolve_static_file
        original = self.original
        self.active = True

        @wraps(original)
        def resolve(service, static_folder, requested_path):
            # The official resolver still performs path and file validation.
            path = original(service, static_folder, requested_path)
            if not self.active or requested_path not in (MAIN_ASSET, TRADITIONAL_ASSET):
                return path
            main = original(service, static_folder, MAIN_ASSET)
            locale = original(service, static_folder, LOCALE_ASSET)
            if main is None or locale is None:
                return path
            try:
                return self.translated_files(main, locale)[requested_path]
            except (OSError, UnicodeError, ValueError) as exc:
                if not self.warned:
                    self.logger.warning(
                        "[traditional_commands] WebUI 繁體化未套用：%s", exc
                    )
                    self.warned = True
                return path

        self.wrapper = resolve
        self.service_type.resolve_static_file = resolve
        self.logger.info(
            "[traditional_commands] WebUI 繁體選項已開啟；重新整理後選擇繁體中文"
        )

    def translated_files(self, main_path, locale_path):
        main = Path(main_path).read_bytes()
        source = Path(locale_path).read_bytes()
        if (
            hashlib.sha256(source).hexdigest() != LOCALE_SHA256
            or hashlib.sha256(main).hexdigest() != MAIN_SHA256
        ):
            raise ValueError("WebUI 建置不同，維持原始語系；需要重新核對")
        if self.cached is not None and all(p.is_file() for p in self.cached.values()):
            return self.cached
        assets = {
            MAIN_ASSET: add_language_option(main),
            TRADITIONAL_ASSET: translate_asset(source, self.converter),
        }
        self.data_dir.mkdir(parents=True, exist_ok=True)
        paths = {}
        # Prepare both assets before exposing the menu that imports the new locale.
        for name, content in assets.items():
            path = self.data_dir / (hashlib.sha256(content).hexdigest() + ".js")
            path.write_bytes(content)
            paths[name] = path
        self.cached = paths
        return self.cached

    def uninstall(self):
        self.active = False
        if (
            self.wrapper is not None
            and self.service_type.resolve_static_file is self.wrapper
        ):
            self.service_type.resolve_static_file = self.original
        self.wrapper = None
        self.cached = None
