from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, StarTools
from astrbot.core.star.filter.command import CommandFilter
from astrbot.core.star.filter.command_group import CommandGroupFilter
from astrbot.core.star.star import star_map
from astrbot.core.star.star_handler import star_handlers_registry

from .core.runtime import Compatibility
from .core.webui import WebUILocale


class TraditionalCommandsPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.webui = None
        self.compatibility = Compatibility(
            star_handlers_registry, star_map, CommandFilter, CommandGroupFilter, logger
        )

    async def initialize(self):
        self.compatibility.install()
        if self.config.get("webui_traditional_enabled", False):
            from astrbot.dashboard.services.static_file_service import StaticFileService

            self.webui = WebUILocale(
                StaticFileService,
                StarTools.get_data_dir("astrbot_plugin_traditional_commands") / "webui",
                logger,
            )
            try:
                self.webui.install()
            except ImportError:
                logger.warning(
                    "[traditional_commands] 缺少 OpenCC，WebUI 保持原樣；請安裝 requirements.txt。指令相容繼續運作。"
                )

    @filter.on_plugin_loaded()
    async def plugin_loaded(self, metadata):
        self.compatibility.install()

    async def terminate(self):
        if self.webui:
            self.webui.uninstall()
        self.compatibility.uninstall()
