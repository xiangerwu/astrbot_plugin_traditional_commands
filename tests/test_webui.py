import ast
import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from opencc import OpenCC

from core.webui import (
    LITERALS,
    LOCALE_ASSET,
    LOCALE_SHA256,
    MAIN_ASSET,
    MAIN_SHA256,
    PROTECTED,
    TRADITIONAL_ASSET,
    WebUILocale,
    add_language_option,
    translate_asset,
    translate_text,
)

REFERENCE = os.environ.get("ASTRBOT_REFERENCE")


class TextTests(unittest.TestCase):
    def test_only_static_text_not_tokens_links_or_code(self):
        text = '加载 {用户名称} ${count} https://例子.test/设置 `删除 设置` <span title="设置">配置</span> \\u8bbe'
        converted = translate_text(text, OpenCC("s2twp"))
        self.assertIn("載入", converted)
        self.assertEqual(PROTECTED.findall(text), PROTECTED.findall(converted))

    def test_unknown_asset_is_not_rewritten(self):
        with self.assertRaises(ValueError):
            translate_asset(b'export default {text:"unknown"}', OpenCC("s2twp"))
        with self.assertRaises(ValueError):
            add_language_option(b'const input="do not change"')


@unittest.skipUnless(
    REFERENCE and shutil.which("node"),
    "Needs ASTRBOT_REFERENCE and Node.js for real WebUI data tests",
)
class WebUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = (Path(REFERENCE) / "webui-zh-CN.js").read_bytes()
        tree = ast.parse(
            (
                Path(REFERENCE) / "astrbot__dashboard__services__static_file_service.py"
            ).read_text(encoding="utf-8-sig")
        )
        definition = next(
            n
            for n in tree.body
            if isinstance(n, ast.ClassDef) and n.name == "StaticFileService"
        )
        namespace = {"Path": Path}
        exec(  # noqa: S102 - reviewed upstream resolver, isolated test
            compile(
                ast.Module(body=[definition], type_ignores=[]),
                "official_static_service",
                "exec",
            ),
            namespace,
        )
        self.service_type = namespace["StaticFileService"]
        self.service = self.service_type()
        self.overlay = WebUILocale(
            self.service_type, self.root / "plugin-data", logging.getLogger("tests")
        )
        self.addCleanup(self.overlay.uninstall)
        self.original_file = self.root / "dist" / LOCALE_ASSET
        self.original_file.parent.mkdir(parents=True)
        self.original_file.write_bytes(self.source)
        self.main_source = (Path(REFERENCE) / "webui-main.js").read_bytes()
        self.main_file = self.root / "dist" / MAIN_ASSET
        self.main_file.write_bytes(self.main_source)

    def read_module(self, path):
        script = """const fs=require('node:fs');
        (async()=>{const s=fs.readFileSync(process.argv[1]);
        const m=await import('data:text/javascript;base64,'+s.toString('base64'));
        process.stdout.write(JSON.stringify(m.default));})().catch(e=>{console.error(e);process.exit(1)});"""
        return json.loads(
            subprocess.check_output(["node", "-e", script, str(path)], encoding="utf-8")
        )

    def test_complete_data_module_structure_and_interpolation(self):
        translated = translate_asset(self.source, OpenCC("s2twp"))
        original_text, translated_text = self.source.decode(), translated.decode()
        # Identical executable syntax outside literals; no imports/events/input hooks added.
        self.assertEqual(
            LITERALS.sub('"TEXT"', original_text),
            LITERALS.sub('"TEXT"', translated_text),
        )
        target = self.root / "converted.js"
        target.write_bytes(translated)
        original, converted = (
            self.read_module(self.original_file),
            self.read_module(target),
        )
        self.changed = 0

        def compare(a, b):
            self.assertIs(type(a), type(b))
            if isinstance(a, dict):
                self.assertEqual(list(a), list(b))
                for key in a:
                    compare(a[key], b[key])
            elif isinstance(a, list):
                self.assertEqual(len(a), len(b))
                for x, y in zip(a, b):
                    compare(x, y)
            elif isinstance(a, str):
                self.assertEqual(PROTECTED.findall(a), PROTECTED.findall(b))
                if a != b:
                    self.changed += 1
                if a.isascii():
                    self.assertEqual(a, b)
            else:
                self.assertEqual(a, b)

        compare(original, converted)
        self.assertGreater(self.changed, 1000)
        # Execute the actual upstream t() function, stripping only TS annotations.
        source = (Path(REFERENCE) / "dashboard__src__i18n__composables.ts").read_text(
            encoding="utf-8-sig"
        )
        function = source[source.index("  const t = ") : source.index("  // 切换语言")]
        function = (
            function.replace(
                "key: string, params?: Record<string, string | number>", "key, params"
            )
            .replace(") : string", ")")
            .replace("): string", ")")
            .replace("let value: any", "let value")
            .replace("match: string, paramKey: string", "match, paramKey")
        )
        template_path = next(
            path for path, value in flatten(converted) if "{name}" in value
        )
        payload = "设置 雲端 /生图 <input value='设置'> https://例子.test/删除"
        harness = (
            'const translations={value:JSON.parse(require("node:fs").readFileSync(0,"utf8"))};'
            + function
        )
        harness += "process.stdout.write(JSON.stringify(t(process.argv[1],{name:process.argv[2]})));"
        result = json.loads(
            subprocess.check_output(
                ["node", "-e", harness, template_path, payload],
                input=json.dumps(converted, ensure_ascii=False),
                encoding="utf-8",
            )
        )
        self.assertIn(payload, result)

    def test_toggle_repeated_load_and_original_files(self):
        baseline = self.service_type.resolve_static_file
        self.assertEqual(
            self.service.resolve_static_file(self.root / "dist", LOCALE_ASSET),
            self.original_file,
        )
        self.overlay.install()
        wrapper = self.service_type.resolve_static_file
        self.overlay.install()
        self.assertIs(self.service_type.resolve_static_file, wrapper)
        result = self.service.resolve_static_file(self.root / "dist", TRADITIONAL_ASSET)
        self.assertNotEqual(result, self.original_file)
        self.assertIn("載入", result.read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(self.original_file.read_bytes()).hexdigest(), LOCALE_SHA256
        )
        self.assertEqual(
            self.service.resolve_static_file(self.root / "dist", LOCALE_ASSET),
            self.original_file,
        )
        menu = self.service.resolve_static_file(self.root / "dist", MAIN_ASSET)
        self.assertIn('label:"繁體中文",flag:""', menu.read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(self.main_file.read_bytes()).hexdigest(), MAIN_SHA256
        )
        for name, content in [
            ("assets/main.js", 'const input="设置"'),
            ("chat.json", '{"content":"设置"}'),
        ]:
            path = self.root / "dist" / name
            path.parent.mkdir(exist_ok=True)
            path.write_text(content, encoding="utf-8")
            returned = self.service.resolve_static_file(self.root / "dist", name)
            self.assertEqual(returned, path)
            self.assertEqual(returned.read_text(encoding="utf-8"), content)
        self.assertIsNone(
            self.service.resolve_static_file(
                self.root / "dist", "../plugin-data/private.js"
            )
        )
        self.assertIsNone(
            self.service.resolve_static_file(self.root / "dist", "api/chat")
        )
        self.overlay.uninstall()
        self.assertIs(self.service_type.resolve_static_file, baseline)
        self.assertEqual(
            self.service.resolve_static_file(self.root / "dist", LOCALE_ASSET),
            self.original_file,
        )
        self.assertIsNone(
            self.service.resolve_static_file(self.root / "dist", TRADITIONAL_ASSET)
        )
        self.assertEqual(
            self.service.resolve_static_file(self.root / "dist", MAIN_ASSET),
            self.main_file,
        )

    def test_unknown_build_and_write_failure_keep_original(self):
        self.overlay.install()
        self.original_file.write_bytes(self.source + b"\n// other build")
        self.assertEqual(
            self.service.resolve_static_file(self.root / "dist", MAIN_ASSET),
            self.main_file,
        )
        self.original_file.write_bytes(self.source)
        self.overlay.data_dir.write_text("not a directory", encoding="utf-8")
        self.assertEqual(
            self.service.resolve_static_file(self.root / "dist", MAIN_ASSET),
            self.main_file,
        )

    def test_real_language_menu_selection_persistence_and_blank_flag(self):
        patched = add_language_option(self.main_source).decode("utf-8")
        module = self.root / "main.mjs"
        module.write_text(patched, encoding="utf-8")
        subprocess.run(
            ["node", "--check", str(module)], check=True, capture_output=True
        )
        start, end = patched.index('Qo={"zh-CN"'), patched.index("const Ly=")
        original = self.main_source.decode("utf-8")
        self.assertEqual(patched[:start], original[: original.index('Qo={"zh-CN"')])
        self.assertEqual(patched[end:], original[original.index("const Ly=") :])
        block = "const " + patched[start:end]
        # Run the deployed i18n code; replace only its external chunk URLs and Vue/browser primitives.
        for filename, content in {
            "index-Bs76R583.js": self.source.decode(),
            "traditional-commands-zh-TW.js": translate_asset(
                self.source, OpenCC("s2twp")
            ).decode(),
            "index-BuNqbOFW.js": 'export default {language:"en-US"}',
            "index-C_6nve1l.js": 'export default {language:"ru-RU"}',
            "index-B2wxV3Ox.js": 'export default {language:"ja-JP"}',
        }.items():
            path = self.root / filename
            path.write_text(content, encoding="utf-8")
            block = block.replace('"./' + filename + '"', json.dumps(path.as_uri()))
        harness = (
            r"""
const assert = require('node:assert/strict');
const J=value=>({value}), S=get=>({get value(){return get()}}), Te=f=>f();
const stored=new Map(), events=[];
const localStorage={getItem:k=>stored.get(k),setItem:(k,v)=>stored.set(k,v)};
const document={documentElement:{lang:''}};
const window={dispatchEvent:e=>events.push(e)};
class CustomEvent{constructor(type,options){this.type=type;this.detail=options.detail;}}
"""
            + block
            + r"""
(async()=>{
 await QT(); const menu=G$();
 assert.equal(menu.currentLanguage.value.value,'zh-CN');
 assert.deepEqual(menu.availableLocales,['zh-CN','zh-TW','en-US','ru-RU','ja-JP']);
 assert.equal(menu.languageOptions.value.filter(x=>x.value==='zh-TW').length,1);
 await menu.switchLanguage('zh-TW');
 assert.equal(menu.currentLanguage.value.label,'繁體中文');
 assert.equal(menu.currentLanguage.value.flag,'');
 assert.equal(document.documentElement.lang,'zh-TW');
 assert.equal(stored.get('astrbot-locale'),'zh-TW');
 assert.equal(events.at(-1).detail.locale,'zh-TW');
 const traditional=JSON.stringify(ga.value);
 Ar.value='zh-CN'; await QT(); assert.equal(Ar.value,'zh-TW');
 assert.equal(JSON.stringify(ga.value),traditional);
 await menu.switchLanguage('zh-CN');
 assert.equal(menu.currentLanguage.value.label,'简体中文');
 assert.notEqual(JSON.stringify(ga.value),traditional);
 for(const lang of ['en-US','ru-RU','ja-JP']){
   await menu.switchLanguage(lang);assert.equal(ga.value.language,lang);
 }
 assert.equal(stored.size,1); // No input, token or unrelated preference storage changed.
 process.stdout.write('language menu OK');
})().catch(e=>{console.error(e);process.exit(1)});
"""
        )
        script = self.root / "menu.cjs"
        script.write_text(harness, encoding="utf-8")
        self.assertEqual(
            subprocess.check_output(["node", str(script)], encoding="utf-8"),
            "language menu OK",
        )


def flatten(value, prefix=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from flatten(item, f"{prefix}.{key}".strip("."))
    elif isinstance(value, str):
        yield prefix, value


if __name__ == "__main__":
    unittest.main()
