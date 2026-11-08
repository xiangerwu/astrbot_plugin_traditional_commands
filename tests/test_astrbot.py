"""Integration checks against externally supplied AstrBot 4.29.4 source.

AST loading removes imports/decorators only. Filter, waking, registry and
upstream handler bodies execute unchanged; no upstream code is redistributed.
Set ASTRBOT_REFERENCE to the source snapshot described in docs/development.md.
"""

import ast
import enum
import inspect
import logging
import os
import re
import types
import typing
import unittest
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace as NS

from core.runtime import Compatibility

REFERENCE = os.environ.get("ASTRBOT_REFERENCE")


def load_definitions(filename, namespace, names=None):
    path = Path(REFERENCE) / filename
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    selected = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and (
            names is None or node.name in names
        ):
            node.decorator_list = [
                d
                for d in node.decorator_list
                if isinstance(d, ast.Name) and d.id == "dataclass"
            ]
            selected.append(node)
    module = ast.Module(
        body=[
            ast.ImportFrom(
                module="__future__", names=[ast.alias(name="annotations")], level=0
            ),
            *selected,
        ],
        type_ignores=[],
    )
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)  # noqa: S102 - execute reviewed upstream test definitions only


class Event:
    def __init__(self, text, sender="admin"):
        self.message_str = text
        self.sender = sender
        self.role = "member"
        self.is_at_or_wake_command = False
        self.is_wake = False
        self.stopped = False
        self._extras = {}
        self.sent = []
        self.unified_msg_origin = "test:GroupMessage:room"

    def get_message_str(self):
        return self.message_str

    def get_extra(self, key=None, default=None):
        return self._extras if key is None else self._extras.get(key, default)

    def set_extra(self, key, value):
        self._extras[key] = value

    def get_messages(self):
        return [NS(text=self.message_str)]

    def get_platform_name(self):
        return "discord"

    def get_self_id(self):
        return "bot"

    def get_sender_id(self):
        return self.sender

    def get_group_id(self):
        return "room"

    def is_admin(self):
        return self.role == "admin"

    def is_private_chat(self):
        return False

    def is_button_interaction(self):
        return False

    def get_button_interaction(self):
        return None

    def stop_event(self):
        self.stopped = True

    def plain_result(self, text):
        return text

    async def send(self, result):
        self.sent.append(result)


class Message:
    def message(self, text):
        self.text = text
        return self

    def use_markdown(self, value):
        return self


@unittest.skipUnless(
    REFERENCE, "Set ASTRBOT_REFERENCE to run actual AstrBot integration tests"
)
class AstrBotTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ns = {
            "inspect": inspect,
            "re": re,
            "types": types,
            "typing": typing,
            "enum": enum,
            "Any": typing.Any,
            "Generic": typing.Generic,
            "TypeVar": typing.TypeVar,
            "overload": typing.overload,
            "T": typing.TypeVar("T"),
            "H": typing.TypeVar("H"),
            "dataclass": dataclass,
            "field": field,
            "HandlerFilter": object,
            "logger": logging.getLogger("tests"),
            "Stage": object,
            "AsyncGenerator": AsyncGenerator,
            "FILTERS": [],
            "USER_SESSIONS": {},
            "MessageChain": Message,
            "MessageEventResult": Message,
        }
        for name in ("At", "AtAll", "Reply", "ButtonInteraction", "ButtonActionFilter"):
            self.ns[name] = type(name, (), {})
        load_definitions("astrbot__core__star__filter__command.py", self.ns)
        load_definitions("astrbot__core__star__filter__command_group.py", self.ns)
        load_definitions("permission.py", self.ns)
        load_definitions(
            "star_handler.py",
            self.ns,
            {"StarHandlerRegistry", "EventType", "StarHandlerMetadata"},
        )
        self.registry = self.ns["StarHandlerRegistry"]()
        self.plugins = {}
        self.ns.update(star_handlers_registry=self.registry, star_map=self.plugins)

        class SessionManager:
            @staticmethod
            async def filter_handlers_by_session(event, handlers):
                return [] if event.get_extra("test_session_disabled") else handlers

        self.ns["SessionPluginManager"] = SessionManager
        load_definitions("astrbot__core__pipeline__waking_check__stage.py", self.ns)
        self.config = {
            "admins_id": ["admin"],
            "wake_prefix": ["/"],
            "plugin_set": ["*"],
        }
        self.stage = self.ns["WakingCheckStage"]()
        self.stage.ctx = NS(astrbot_config=self.config)
        self.stage.ignore_bot_self_message = False
        self.stage.ignore_at_all = True
        self.stage.friend_message_needs_wake_prefix = True
        self.stage.disable_builtin_commands = False
        self.stage.no_permission_reply = True
        self.stage._umo_auto_name_recorder = NS(schedule=lambda e: None)
        self.runtime = Compatibility(
            self.registry,
            self.plugins,
            self.ns["CommandFilter"],
            self.ns["CommandGroupFilter"],
            logging.getLogger("test"),
        )
        self.calls = []

    def tearDown(self):
        self.runtime.uninstall()

    def add(
        self,
        plugin,
        version,
        command,
        *,
        aliases=(),
        params=None,
        admin=False,
        func=None,
    ):
        async def record(event, **kwargs):
            self.calls.append((event.message_str, kwargs))
            return event.message_str

        module = "data.plugins." + plugin + ".main"
        self.plugins[module] = NS(
            name=plugin, version=version.split("|")[0], activated=True, reserved=False
        )
        handler = self.ns["StarHandlerMetadata"](
            self.ns["EventType"].AdapterMessageEvent,
            module + "_" + command,
            command,
            module,
            func or record,
            [],
        )
        parent, _, fragment = command.rpartition(" ")
        f = self.ns["CommandFilter"](
            fragment, set(aliases), parent_command_names=[parent]
        )
        f.handler_md = handler
        f.handler_params = params or {}
        handler.event_filters.append(f)
        if admin:
            handler.event_filters.insert(
                0, self.ns["PermissionTypeFilter"](self.ns["PermissionType"].ADMIN)
            )
        self.registry.append(handler)
        return handler, f

    async def dispatch(self, text, sender="admin", session_disabled=False):
        event = Event(text, sender)
        event.set_extra("test_session_disabled", session_disabled)
        await self.stage.process(event)
        for handler in event.get_extra("activated_handlers", []):
            result = handler.handler(
                event,
                **event.get_extra("handlers_parsed_params", {}).get(
                    handler.handler_full_name, {}
                ),
            )
            if inspect.isasyncgen(result):
                async for value in result:
                    self.calls.append(value)
            else:
                await result
        return event

    async def test_all_registered_commands_and_both_scripts(self):
        for row in self.runtime.rules:
            if row["kind"] == "registered_command":
                self.add(row["plugin"], row["version"], row["original"])
        self.runtime.install()
        for row in self.runtime.rules:
            if row["kind"] != "registered_command":
                continue
            for spelling in (row["original"], row["traditional"]):
                with self.subTest(command=spelling):
                    before = len(self.calls)
                    event = await self.dispatch("/" + spelling)
                    self.assertEqual(len(self.calls), before + 1)
                    self.assertEqual(self.calls[-1][0], row["original"])
                    self.assertEqual(event.message_str, spelling)

    async def test_meme_manager_supported_versions_and_upgrade(self):
        rows = [r for r in self.runtime.rules if r["plugin"] == "meme_manager"]
        self.assertEqual(len(rows), 13)
        for version in ("5.3.5", "5.3.6", "5.3.7"):
            # Simulate upstream handlers being replaced during a plugin reload.
            self.registry.clear()
            for row in rows:
                self.add("meme_manager", version, row["original"], admin=True)
            self.runtime.install()
            self.runtime.install()
            for row in rows:
                for spelling in (row["original"], row["traditional"]):
                    with self.subTest(version=version, command=spelling):
                        before = len(self.calls)
                        event = await self.dispatch("/" + spelling)
                        allowed = version != "5.3.7" or spelling == row["original"]
                        self.assertEqual(len(self.calls), before + int(allowed))
                        if allowed:
                            self.assertEqual(self.calls[-1][0], row["original"])
                        self.assertEqual(event.message_str, spelling)
                        before = len(self.calls)
                        await self.dispatch("/" + spelling, sender="member")
                        self.assertEqual(len(self.calls), before)

    async def test_manual_parameters_and_group_permissions(self):
        self.add(
            "favoradmin",
            "v1.2.0",
            "管理",
            params={"cmd": str, "target": "", "value": 0},
            admin=True,
        )
        self.add("meme_manager", "5.3.5", "表情管理 查看图库", admin=True)
        self.runtime.install()
        await self.dispatch("/管理 計數器 間隔 50")
        self.assertEqual(
            self.calls[-1][1], {"cmd": "计数器", "target": "间隔", "value": 50}
        )
        for text in (
            "/表情管理 查看圖庫",
            "/表情管理 查看图库",
            "/管理 計數器 間隔 50",
        ):
            before = len(self.calls)
            event = await self.dispatch(text, sender="member")
            self.assertEqual(len(self.calls), before)
            self.assertTrue(event.stopped)
            self.assertEqual(len(event.sent), 1)

    async def test_image_versions_preserve_commands_and_free_text(self):
        rows = [
            r
            for r in self.runtime.rules
            if r["plugin"] == "astrbot_plugin_image_generation"
        ]
        self.assertEqual(len(rows), 6)
        payload = " 雲端 保留繁體文字"
        for version in ("v1.8.4", "v1.8.5", "v1.8.6"):
            self.registry.clear()
            for row in rows:
                if row["kind"] == "registered_command":
                    self.add(row["plugin"], version, row["original"])
            self.runtime.install()
            for row in rows:
                for spelling in (row["original"], row["traditional"]):
                    with self.subTest(version=version, command=spelling):
                        before = len(self.calls)
                        event = await self.dispatch("/" + spelling + payload)
                        allowed = version != "v1.8.6" or spelling == row["original"]
                        self.assertEqual(len(self.calls), before + int(allowed))
                        if allowed:
                            self.assertEqual(
                                self.calls[-1][0], row["original"] + payload
                            )
                        self.assertEqual(event.message_str, spelling + payload)

    async def test_disabled_renamed_alias_collision_and_unload(self):
        h, f = self.add(
            "astrbot_plugin_help_page", "1.3.1", "帮助", aliases={"help", "菜单"}
        )
        self.runtime.install()
        for text in ("/帮助", "/幫助", "/help", "/菜单", "/菜單"):
            before = len(self.calls)
            await self.dispatch(text)
            self.assertEqual(len(self.calls), before + 1)
        # Duplicate load does not stack wrappers.
        wrapper = h.handler
        self.runtime.install()
        self.assertIs(h.handler, wrapper)
        h.enabled = False
        before = len(self.calls)
        await self.dispatch("/幫助")
        self.assertEqual(len(self.calls), before)
        h.enabled = True
        self.plugins[h.handler_module_path].activated = False
        await self.dispatch("/幫助")
        self.assertEqual(len(self.calls), before)
        self.plugins[h.handler_module_path].activated = True
        await self.dispatch("/幫助", session_disabled=True)
        self.assertEqual(len(self.calls), before)
        f.command_name, f.alias, f._cmpl_cmd_names = "新的名稱", {"custom"}, None
        await self.dispatch("/幫助")
        self.assertEqual(len(self.calls), before)
        await self.dispatch("/custom")
        self.assertEqual(len(self.calls), before + 1)
        f.command_name, f.alias, f._cmpl_cmd_names = "帮助", {"菜单", "help"}, None
        self.add("another_plugin", "1", "幫助")
        await self.dispatch("/幫助")
        self.assertEqual(self.calls[-1][0], "幫助")
        self.assertEqual(len(self.calls), before + 2)
        self.runtime.uninstall()
        self.assertEqual(f.alias, {"菜单", "help"})
        before = len(self.calls)
        await self.dispatch("/菜單")
        self.assertEqual(len(self.calls), before)
        await self.dispatch("/菜单")
        self.assertEqual(len(self.calls), before + 1)

    async def test_profile_and_ordinary_chat(self):
        self.add("astrbot_plugin_image_generation", "v1.8.4", "生图")
        self.runtime.install()
        for text in ("生圖 貓咪", "/生圖案", "/請生圖"):
            await self.dispatch(text)
        self.assertEqual(self.calls, [])
        self.config["plugin_set"] = ["astrbot_plugin_image_generation"]
        await self.dispatch("/生圖")
        self.assertEqual(self.calls, [])
        await self.dispatch("/生图")
        self.assertEqual(len(self.calls), 1)

    async def test_raw_text_and_greedy_parameters(self):
        self.add("astrbot_plugin_master_aware", "4.4.1", "认主")
        self.add(
            "astrbot_plugin_gengwiki",
            "0.9.0",
            "添加梗",
            params={"text": self.ns["GreedyStr"]},
        )
        self.runtime.install()
        await self.dispatch("/認主 記住 刪除  雲端\n第二行")
        self.assertEqual(self.calls[-1][0], "认主 记住 刪除  雲端\n第二行")
        await self.dispatch("/添加梗 人設 雲端 我說繁體中文")
        self.assertEqual(self.calls[-1][1]["text"], "人设 雲端 我說繁體中文")

    async def test_all_manual_paths_and_existing_alias_options(self):
        seen = set()
        for row in self.runtime.rules:
            if row["kind"] != "manual_keyword":
                continue
            root = row["original"].split()[0]
            if (row["plugin"], root) not in seen:
                self.add(row["plugin"], row["version"], root)
                seen.add((row["plugin"], root))
        self.runtime.install()
        for row in self.runtime.rules:
            if row["kind"] != "manual_keyword":
                continue
            for spelling in (row["original"], row["traditional"]):
                with self.subTest(path=spelling):
                    before = len(self.calls)
                    await self.dispatch("/" + spelling + " 雲端")
                    self.assertEqual(len(self.calls), before + 1)
                    self.assertEqual(self.calls[-1][0], row["original"] + " 雲端")
        bulk = next(h for h in self.registry if h.handler_name == "群发")
        f = bulk.event_filters[0]
        f.alias = {"bulksend", "群发助手"}
        f._cmpl_cmd_names = None
        for spelling in ("/bulksend 暫停", "/群發助手 暫停", "/群发助手 暫停"):
            await self.dispatch(spelling)
            self.assertEqual(self.calls[-1][0], "群发 暂停")

    async def test_real_master_and_image_handlers(self):
        def method(filename, name, namespace):
            path = Path(REFERENCE) / filename
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            node = next(
                n
                for n in ast.walk(tree)
                if isinstance(n, ast.AsyncFunctionDef) and n.name == name
            )
            node.decorator_list = []
            module = ast.Module(
                body=[
                    ast.ImportFrom(
                        module="__future__",
                        names=[ast.alias(name="annotations")],
                        level=0,
                    ),
                    node,
                ],
                type_ignores=[],
            )
            exec(  # noqa: S102 - execute reviewed upstream handler in an isolated test
                compile(ast.fix_missing_locations(module), str(path), "exec"), namespace
            )
            return namespace[name]

        master = method("master-aware-main.py", "master_cmd", {})
        self.add(
            "astrbot_plugin_master_aware",
            "4.4.1",
            "认主",
            admin=True,
            func=types.MethodType(master, NS()),
        )
        deleted = []
        image_ns = {
            "mask_sensitive": lambda x: x,
            "safe_log_text": lambda x: x,
            "logger": logging.getLogger("test"),
            "LOG": "test",
        }
        preset = method("image-main.py", "preset_command", image_ns)
        fake = NS(
            config_manager=NS(delete_preset=lambda name: deleted.append(name) or True)
        )
        self.add(
            "astrbot_plugin_image_generation",
            "v1.8.4",
            "预设",
            func=types.MethodType(preset, fake),
        )
        self.runtime.install()
        for spelling in ("/認主 綁定", "/认主 绑定"):
            await self.dispatch(spelling)
            self.assertEqual(self.calls[-1], "只能在私聊里绑定，群里不行。")
        for spelling in ("/預設 刪除 雲端", "/预设 删除 雲端"):
            await self.dispatch(spelling)
            self.assertEqual(self.calls[-1], "✅ 预设已删除: 雲端")
        self.assertEqual(deleted, ["雲端", "雲端"])

    async def test_reload_new_handler_and_unknown_version(self):
        h, _ = self.add("astrbot_plugin_master_aware", "4.4.1", "认主")
        self.runtime.install()
        self.registry.remove(h)
        self.add("astrbot_plugin_master_aware", "4.4.1", "认主")
        self.runtime.install()
        await self.dispatch("/認主 檔案")
        self.assertEqual(len(self.calls), 1)
        self.runtime.uninstall()
        for plugin in self.plugins.values():
            plugin.version = "999.0"
        self.runtime.install()
        await self.dispatch("/認主 檔案")
        self.assertEqual(len(self.calls), 1)
        await self.dispatch("/认主 档案")
        self.assertEqual(len(self.calls), 2)


if __name__ == "__main__":
    unittest.main()
