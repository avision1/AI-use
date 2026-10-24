"""Overlay contract checks. Run inside the contained build/test VM only.

    python3 -B -m unittest discover -s tests -v

Browser execution is mocked. These checks do not establish Microsoft service,
KDE GUI, installation, or hardware compatibility.
"""
import ast
import configparser
import contextlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import runpy
import shlex
import sys
import unittest
from unittest.mock import Mock, patch
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

PROJECT = Path(__file__).resolve().parents[1]
IMAGE = PROJECT / "image"
WEBAPP = IMAGE / "usr/local/bin/windows12-webapp"
WELCOME = IMAGE / "usr/local/bin/windows12-welcome"


class LauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = runpy.run_path(str(WEBAPP), run_name="overlay_test_webapp")
        cls.command = staticmethod(cls.module["command"])
        cls.main = staticmethod(cls.module["main"])

    def test_allowlist_is_explicit_https_microsoft_services(self):
        apps = self.module["APPS"]
        self.assertEqual(set(apps), {"office", "word", "excel", "powerpoint", "outlook", "onedrive", "teams"})
        for key, (label, url) in apps.items():
            with self.subTest(app=key):
                parsed = urlparse(url)
                self.assertEqual(parsed.scheme, "https")
                self.assertIn(parsed.hostname, {
                    "www.microsoft365.com", "word.cloud.microsoft", "excel.cloud.microsoft",
                    "powerpoint.cloud.microsoft", "outlook.office.com", "onedrive.live.com", "teams.microsoft.com",
                })
                self.assertFalse(parsed.username)
                self.assertFalse(parsed.password)
                self.assertIn("web", label.lower())

    def test_chromium_preferred_to_firefox(self):
        finder = Mock(side_effect=lambda name: {"chromium": "/browser/chromium", "firefox": "/browser/firefox"}.get(name))
        argv = self.command("word", find=finder)
        self.assertEqual(argv[0], "/browser/chromium")
        self.assertIn("--app=https://word.cloud.microsoft/", argv)
        self.assertIn("--class=windows12-word", argv)
        self.assertNotIn("--no-sandbox", argv)
        self.assertNotIn("firefox", [call.args[0] for call in finder.call_args_list])

    def test_each_chromium_family_fallback(self):
        for browser in ("chromium-browser", "google-chrome", "microsoft-edge"):
            with self.subTest(browser=browser):
                argv = self.command("excel", find=lambda name: "/browser/" + name if name == browser else None)
                self.assertEqual(argv[0], "/browser/" + browser)
                self.assertIn("--app=https://excel.cloud.microsoft/", argv)

    def test_firefox_esr_preferred_and_plain_firefox_fallback(self):
        for browser in ("firefox-esr", "firefox"):
            with self.subTest(browser=browser):
                argv = self.command("outlook", find=lambda name: "/browser/" + name if name == browser else None)
                self.assertEqual(argv, ["/browser/" + browser, "--new-window", "https://outlook.office.com/mail/"])

    def test_missing_browser_reports_actionable_error(self):
        with self.assertRaisesRegex(RuntimeError, "No supported browser"):
            self.command("office", find=lambda name: None)
        stderr = io.StringIO()
        with patch.object(sys, "argv", [str(WEBAPP), "office"]), patch.dict(self.main.__globals__, {"command": Mock(side_effect=RuntimeError("No supported browser"))}), contextlib.redirect_stderr(stderr):
            self.assertEqual(self.main(), 1)
        self.assertIn("No supported browser", stderr.getvalue())

    def test_arbitrary_ids_rejected_before_browser_lookup(self):
        for value in ("https://example.invalid", "word;touch bad", "$(id)", "../word", "WORD"):
            with self.subTest(value=value):
                finder = Mock()
                with self.assertRaises(KeyError):
                    self.command(value, find=finder)
                finder.assert_not_called()
                resolver = Mock()
                with patch.object(sys, "argv", [str(WEBAPP), value]), patch.dict(self.main.__globals__, {"command": resolver}), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        self.main()
                self.assertEqual(error.exception.code, 2)
                resolver.assert_not_called()

    def test_root_refused_without_exec(self):
        with patch.object(sys, "argv", [str(WEBAPP), "word"]), patch.dict(self.main.__globals__, {"command": Mock(return_value=["/browser/chromium", "--app=https://word.cloud.microsoft/"])}), patch("os.geteuid", return_value=0), patch("os.execv") as execute, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.main(), 1)
            execute.assert_not_called()

    def test_nonroot_exec_preserves_argument_boundaries(self):
        # A path with spaces/shell punctuation must remain one executable path.
        argv = ["/browser/path with spaces;not-a-shell", "--app=https://word.cloud.microsoft/"]
        with patch.object(sys, "argv", [str(WEBAPP), "word"]), patch.dict(self.main.__globals__, {"command": Mock(return_value=argv)}), patch("os.geteuid", return_value=1000), patch("os.execv") as execute:
            self.main()
            execute.assert_called_once_with(argv[0], argv)

    def test_print_command_is_json_and_never_executes(self):
        argv = ["/browser/chromium", "--app=https://word.cloud.microsoft/"]
        stdout = io.StringIO()
        with patch.object(sys, "argv", [str(WEBAPP), "word", "--print-command"]), patch.dict(self.main.__globals__, {"command": Mock(return_value=argv)}), patch("os.execv") as execute, contextlib.redirect_stdout(stdout):
            self.assertEqual(self.main(), 0)
            execute.assert_not_called()
        self.assertEqual(json.loads(stdout.getvalue()), argv)

    def test_no_shell_execution_or_disabled_browser_sandbox(self):
        for script in (WEBAPP, WELCOME):
            source = script.read_text()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        self.assertNotIn(node.func.attr, {"system", "popen"}, script.name)
                    for keyword in node.keywords:
                        if keyword.arg == "shell":
                            self.assertIsInstance(keyword.value, ast.Constant)
                            self.assertFalse(keyword.value.value)
            self.assertNotIn("--no-sandbox", source)
            self.assertNotIn("--ignore-certificate-errors", source)


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        for key in ("href", "src"):
            if key in attributes:
                self.references.append(attributes[key])
        if tag == "script":
            self.scripts.append(attributes)


class DesktopAssetTests(unittest.TestCase):
    def test_desktop_launchers_match_curated_services_and_local_commands(self):
        module = runpy.run_path(str(WEBAPP), run_name="overlay_test_assets")
        services = set()
        entries = sorted((IMAGE / "usr/share/applications").glob("windows12-*.desktop"))
        self.assertEqual(len(entries), len(module["APPS"]) + 1)
        for path in entries:
            with self.subTest(entry=path.name):
                parser = configparser.ConfigParser(interpolation=None, strict=True)
                parser.optionxform = str
                parser.read(path)
                entry = parser["Desktop Entry"]
                self.assertEqual(entry["Type"], "Application")
                self.assertEqual(entry["Terminal"], "false")
                argv = shlex.split(entry["Exec"])
                self.assertTrue(argv[0].startswith("/usr/local/bin/"))
                executable = IMAGE / argv[0].lstrip("/")
                self.assertTrue(executable.is_file(), str(executable))
                self.assertEqual(entry["TryExec"], argv[0])
                if argv[0] == "/usr/local/bin/windows12-webapp":
                    self.assertEqual(len(argv), 2)
                    self.assertIn(argv[1], module["APPS"])
                    self.assertNotIn(argv[1], services)
                    services.add(argv[1])
                    self.assertIn("web", entry["Name"].lower())
                else:
                    self.assertEqual(argv, ["/usr/local/bin/windows12-welcome"])
        self.assertEqual(services, set(module["APPS"]))

    def test_double_click_explicitly_configured(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        parser.read(IMAGE / "etc/skel/.config/kdeglobals")
        self.assertEqual(parser["KDE"]["SingleClick"], "false")

    def test_welcome_local_assets_and_no_active_scripts(self):
        page = IMAGE / "usr/local/share/windows12/welcome.html"
        self.assertTrue(page.is_file())
        source = page.read_text()
        parser = AssetParser()
        parser.feed(source)
        self.assertFalse(parser.scripts)
        self.assertIn("Content-Security-Policy", source)
        for reference in parser.references:
            parsed = urlparse(reference)
            if parsed.scheme:
                self.assertEqual(parsed.scheme, "https")
            elif not reference.startswith("#"):
                asset = (IMAGE / reference.lstrip("/")) if reference.startswith("/") else (page.parent / reference)
                self.assertTrue(asset.resolve().is_relative_to(IMAGE.resolve()))
                self.assertTrue(asset.is_file(), str(asset))

    def test_wallpaper_metadata_svg_and_layout_reference(self):
        wallpaper = IMAGE / "usr/share/wallpapers/Windows12"
        metadata = json.loads((wallpaper / "metadata.json").read_text())
        self.assertEqual(metadata["KPlugin"]["Id"], "Windows12")
        svg = wallpaper / "contents/images/3840x2160.svg"
        root = ET.parse(svg).getroot()
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertTrue(root.get("viewBox") or (root.get("width") and root.get("height")))
        for element in root.iter():
            self.assertNotEqual(element.tag.rsplit("}", 1)[-1], "script")
            for key, value in element.attrib.items():
                if key.rsplit("}", 1)[-1] == "href":
                    self.assertTrue(value.startswith("#"), "Wallpaper must not load external resources")
        layout = IMAGE / "usr/share/plasma/shells/org.kde.plasma.desktop/contents/updates/windows12-layout.js"
        source = layout.read_text()
        for reference in re.findall(r'file://(/[^"\s]+)', source):
            self.assertTrue((IMAGE / reference.lstrip("/")).is_file(), reference)
        for app in re.findall(r'applications:(windows12-[^"\s]+)', source):
            self.assertTrue((IMAGE / "usr/share/applications" / app).is_file(), app)


class WelcomeLauncherTests(unittest.TestCase):
    def test_root_refused(self):
        module = runpy.run_path(str(WELCOME), run_name="overlay_test_welcome")
        main = module["main"]
        page = Mock()
        page.is_file.return_value = True
        with patch.dict(main.__globals__, {"Path": Mock(return_value=page)}), patch("shutil.which", return_value="/usr/bin/xdg-open"), patch("os.geteuid", return_value=0), patch("os.execv") as execute, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(), 1)
            execute.assert_not_called()

    def test_failed_opener_reports_failure_without_traceback(self):
        module = runpy.run_path(str(WELCOME), run_name="overlay_test_welcome_exec_error")
        main = module["main"]
        page = Mock()
        page.is_file.return_value = True
        page.as_uri.return_value = "file:///usr/local/share/windows12/welcome.html"
        stderr = io.StringIO()
        with patch.dict(main.__globals__, {"Path": Mock(return_value=page)}), patch("shutil.which", return_value="/usr/bin/xdg-open"), patch("os.geteuid", return_value=1000), patch("os.execv", side_effect=OSError("opener failed")), contextlib.redirect_stderr(stderr):
            self.assertEqual(main(), 1)
        self.assertIn("opener failed", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_missing_help_or_opener_reports_failure(self):
        for page_exists, opener in ((False, "/usr/bin/xdg-open"), (True, None)):
            with self.subTest(page_exists=page_exists, opener=opener):
                module = runpy.run_path(str(WELCOME), run_name="overlay_test_welcome_missing")
                main = module["main"]
                page = Mock()
                page.is_file.return_value = page_exists
                with patch.dict(main.__globals__, {"Path": Mock(return_value=page)}), patch("shutil.which", return_value=opener), patch("os.execv") as execute, contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(main(), 1)
                    execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
