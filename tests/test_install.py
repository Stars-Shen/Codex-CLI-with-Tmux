"""Installation checks using temporary Codex homes, never the user's config."""

import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-light-test-")
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.config = self.home / "config.toml"

    def install(self, check=True):
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(self.home)
        return subprocess.run(
            [sys.executable, str(ROOT / "install.py")],
            cwd=self.home,
            env=environment,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    def test_fresh_install_has_light_diff_colors(self):
        self.install()
        self.assertIn('[tui]\ntheme = "codex-light"', self.config.read_text())
        with (self.home / "themes/codex-light.tmTheme").open("rb") as source:
            theme = plistlib.load(source)
        scopes = {rule.get("scope"): rule["settings"] for rule in theme["settings"]}
        self.assertEqual(scopes["markup.inserted, diff.inserted"]["background"], "#dafbe1")
        self.assertEqual(scopes["markup.deleted, diff.deleted"]["background"], "#ffebe9")
        self.assertTrue((self.home / "themes/codex-light.LICENSE").is_file())

    def test_preserves_other_settings_and_nested_tables(self):
        original = (
            'model = "example"\n\n[tui]\nnotifications = false\n'
            'status_line = [\n  "model",\n  "current-dir",\n]\n\n'
            '[tui.model_availability_nux]\nexample = 1\n\n'
            '[projects."/work"]\ntrust_level = "trusted"\n'
        )
        self.config.write_text(original)
        self.install()
        expected = original.replace('[tui]\n', '[tui]\ntheme = "codex-light"\n')
        self.assertEqual(self.config.read_text(), expected)
        backups = list(self.home.glob("config.toml.backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), original)

    def test_replaces_theme_and_backup_restores_original(self):
        original = '[tui] # interface\ntheme = "catppuccin-mocha"\nnotifications = false\n'
        self.config.write_text(original)
        self.install()
        self.assertEqual(self.config.read_text(), original.replace("catppuccin-mocha", "codex-light"))
        backup = next(self.home.glob("config.toml.backup-*"))
        shutil.copy2(backup, self.config)
        self.assertEqual(self.config.read_text(), original)

    def test_adds_tui_after_existing_tables(self):
        original = '[projects."/work"]\ntrust_level = "trusted"\n'
        self.config.write_text(original)
        self.install()
        self.assertEqual(self.config.read_text(), original + '\n[tui]\ntheme = "codex-light"\n')

    def test_header_without_final_newline(self):
        self.config.write_text("[tui]")
        self.install()
        self.assertEqual(self.config.read_text(), '[tui]\ntheme = "codex-light"\n')

    def test_repeat_install_does_not_write_files_or_create_backups(self):
        self.install()
        before = {str(p.relative_to(self.home)): (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in self.home.rglob("*") if p.is_file()}
        self.install()
        after = {str(p.relative_to(self.home)): (p.read_bytes(), p.stat().st_mtime_ns)
                 for p in self.home.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_existing_theme_is_backed_up(self):
        target = self.home / "themes/codex-light.tmTheme"
        target.parent.mkdir()
        target.write_text("previous custom theme")
        self.install()
        backup = next(target.parent.glob("codex-light.tmTheme.backup-*"))
        self.assertEqual(backup.read_text(), "previous custom theme")

    def test_inline_and_dotted_tui_fail_without_changes(self):
        for original in ('tui.theme = "catppuccin-mocha"\n', 'tui = { theme = "catppuccin-mocha" }\n'):
            with self.subTest(original=original):
                self.config.write_text(original)
                result = self.install(check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.config.read_text(), original)
                self.assertEqual(list(self.home.iterdir()), [self.config])


if __name__ == "__main__":
    unittest.main()
