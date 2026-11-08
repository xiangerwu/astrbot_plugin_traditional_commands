import csv
import unittest
from pathlib import Path
from types import SimpleNamespace

from core.runtime import CommandEvent, replace_prefix


class PrefixTests(unittest.TestCase):
    def test_all_documented_mappings_and_originals(self):
        path = Path(__file__).parents[1] / "docs/command-mappings.csv"
        with path.open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            simple, trad = row["original"], row["traditional"]
            with self.subTest(command=trad):
                payload = "  保留繁體名稱：https://例子.test/雲端?字=圖\n第二行"
                self.assertEqual(
                    replace_prefix(trad + payload, simple, trad), simple + payload
                )
                self.assertEqual(
                    replace_prefix(simple + payload, simple, trad), simple + payload
                )
                self.assertEqual(
                    replace_prefix("請使用 " + trad, simple, trad), "請使用 " + trad
                )
                self.assertEqual(
                    replace_prefix(trad + "更多", simple, trad), trad + "更多"
                )

    def test_mixed_script_whitespace_and_free_text(self):
        self.assertEqual(
            replace_prefix(
                "認主\t记忆  全部刪除", "认主 记忆 全部删除", "認主 記憶 全部刪除"
            ),
            "认主\t记忆  全部删除",
        )
        self.assertEqual(
            replace_prefix("認主 記住 刪除 雲端", "认主 记住", "認主 記住"),
            "认主 记住 刪除 雲端",
        )

    def test_view_forwards_state_without_mutating_original_text(self):
        event = SimpleNamespace(message_str="認主 檔案", role="member")
        view = CommandEvent(event, "认主 档案")
        view.role = "admin"
        self.assertEqual(event.role, "admin")
        self.assertEqual(event.message_str, "認主 檔案")
        self.assertEqual(view.get_message_str(), "认主 档案")


if __name__ == "__main__":
    unittest.main()
