"""Adapt verified command tokens without changing saved aliases or plugin files."""

import csv
import re
from functools import wraps
from pathlib import Path

PLUGIN_NAME = "astrbot_plugin_traditional_commands"
EXTRA_KEY = "traditional_commands.normalized"


class CommandEvent:
    """A handler-local text view; all state changes still reach the real event."""

    def __init__(self, event, text):
        object.__setattr__(self, "_event", event)
        object.__setattr__(self, "message_str", text)

    def get_message_str(self):
        return self.message_str

    def __getattr__(self, name):
        return getattr(self._event, name)

    def __setattr__(self, name, value):
        if name == "message_str":
            object.__setattr__(self, name, value)
        else:
            setattr(self._event, name, value)


def replace_prefix(text, original, traditional):
    """Accept either script at each fixed token, preserving all other characters."""
    matches = list(re.finditer(r"\S+", text))
    source, target = original.split(), traditional.split()
    if len(matches) < len(source):
        return text
    for match, simple, trad in zip(matches, source, target):
        if match.group() not in (simple, trad):
            return text
    # Replace backwards so character offsets and whitespace remain intact.
    for match, simple in reversed(list(zip(matches, source))):
        text = text[: match.start()] + simple + text[match.end() :]
    return text


class Compatibility:
    def __init__(self, registry, plugins, command_type, group_type, logger):
        self.registry = registry
        self.plugins = plugins
        self.command_type = command_type
        self.group_type = group_type
        self.logger = logger
        with (Path(__file__).parents[1] / "docs/command-mappings.csv").open(
            encoding="utf-8-sig", newline=""
        ) as stream:
            self.rules = list(csv.DictReader(stream))
        self.rules.sort(key=lambda row: len(row["original"].split()), reverse=True)
        self.patches = []
        self.active = False
        self.warned = set()

    def install(self):
        self.active = True
        for handler in list(self.registry):
            plugin = self.plugins.get(handler.handler_module_path)
            if not plugin or not plugin.activated:
                continue
            rules = [r for r in self.rules if r["plugin"] == plugin.name]
            if not rules:
                continue
            # Manual parsers are version-specific; unknown releases fail closed.
            rules = [
                r
                for r in rules
                if r["version"].lstrip("v") == plugin.version.lstrip("v")
            ]
            if not rules:
                key = (plugin.name, plugin.version)
                if key not in self.warned:
                    self.logger.warning(
                        "[traditional_commands] 未核對版本，跳過 %s %s", *key
                    )
                    self.warned.add(key)
                continue
            for command in handler.event_filters:
                if not isinstance(command, self.command_type):
                    continue
                if any(obj is command for obj, *_ in self.patches):
                    continue
                self._patch_filter(command, handler, rules)
            if any(obj is handler for obj, *_ in self.patches):
                continue
            if any(isinstance(f, self.command_type) for f in handler.event_filters):
                self._patch_handler(handler)

    def _patch_filter(self, command, handler, rules):
        original = command.filter

        @wraps(original)
        def compatible(event, config):
            if not self.active or not event.is_at_or_wake_command:
                return original(event, config)
            allowed = config.get("plugin_set", ["*"])
            if allowed != ["*"] and PLUGIN_NAME not in allowed:
                return original(event, config)
            text = event.get_message_str()
            names = command.get_complete_command_names()
            for rule in rules:
                # Read effective names on every request: WebUI changes take effect
                # immediately; removed names/aliases are never resurrected.
                if not any(
                    rule["original"] == n or rule["original"].startswith(n + " ")
                    for n in names
                ):
                    continue
                normalized = replace_prefix(text, rule["original"], rule["traditional"])
                if normalized == text and rule["kind"] == "manual_keyword":
                    base = next(
                        (n for n in names if rule["original"].startswith(n + " ")), None
                    )
                    if base:
                        suffix = rule["original"][len(base) :]
                        trad_suffix = " " + " ".join(
                            rule["traditional"].split()[len(base.split()) :]
                        )
                        for alias in names:
                            converted_alias = next(
                                (
                                    r["traditional"]
                                    for r in rules
                                    if r["original"] == alias
                                ),
                                alias,
                            )
                            candidate = replace_prefix(
                                text, alias + suffix, converted_alias + trad_suffix
                            )
                            if candidate != text:
                                # Raw-text parsers may require their canonical root.
                                end = list(re.finditer(r"\S+", candidate))[
                                    len(alias.split()) - 1
                                ].end()
                                normalized = base + candidate[end:]
                                break
                if normalized == text:
                    continue
                if self._claimed_elsewhere(text, handler):
                    return original(event, config)
                passed = original(CommandEvent(event, normalized), config)
                if passed:
                    values = event.get_extra(EXTRA_KEY, {})
                    values[handler.handler_full_name] = (text, normalized)
                    event.set_extra(EXTRA_KEY, values)
                return passed
            return original(event, config)

        command.filter = compatible
        self.patches.append((command, "filter", original, compatible))

    def _claimed_elsewhere(self, text, owner):
        text = re.sub(r"\s+", " ", text.strip())
        for handler in self.registry:
            if handler is owner:
                continue
            for command in handler.event_filters:
                if not isinstance(command, (self.command_type, self.group_type)):
                    continue
                # A parent group is expected to match its own children.
                if isinstance(command, self.group_type):
                    continue
                for name in command.get_complete_command_names():
                    if text == name or text.startswith(name + " "):
                        return True
        return False

    def _patch_handler(self, handler):
        original = handler.handler

        @wraps(original)
        def compatible(event, *args, **kwargs):
            saved = event.get_extra(EXTRA_KEY, {}).get(handler.handler_full_name)
            if self.active and saved and saved[0] == event.get_message_str():
                event = CommandEvent(event, saved[1])
            # Return the original coroutine/generator unchanged, including close
            # and cancellation semantics. Never dispatch another handler here.
            return original(event, *args, **kwargs)

        handler.handler = compatible
        self.patches.append((handler, "handler", original, compatible))

    def uninstall(self):
        self.active = False
        for obj, attr, original, wrapper in reversed(self.patches):
            if getattr(obj, attr) is wrapper:
                setattr(obj, attr, original)
        self.patches.clear()
