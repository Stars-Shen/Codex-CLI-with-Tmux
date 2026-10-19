"""Exercise real tmux on a private socket with a fake, offline Codex command."""

import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
TMUX = shutil.which("tmux")


@unittest.skipUnless(TMUX and shutil.which("bash"), "tmux and Bash are required")
class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-workspace-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.socket = str(self.root / "tmux.sock")
        self.bindir = self.root / "bin"
        self.bindir.mkdir()
        self.workdir = self.root / "project with spaces"
        self.workdir.mkdir()
        self.launch_log = self.root / "codex.log"
        self.connect_log = self.root / "connect.log"
        self.environment = os.environ.copy()
        self.environment.pop("TMUX", None)
        self.environment.update(
            PATH=str(self.bindir) + os.pathsep + os.environ["PATH"],
            SHELL="/bin/sh",
            NO_COLOR="1",
            CODEX_LAUNCH_LOG=str(self.launch_log),
            CODEX_CONNECT_LOG=str(self.connect_log),
        )
        wrapper = (
            '#!/bin/sh\ncase "$1" in\n'
            'attach-session|switch-client) printf "%s\\n" "$*" > "$CODEX_CONNECT_LOG"; exit 0;;\n'
            'esac\nexec ' + shlex.quote(TMUX) + ' -S ' + shlex.quote(self.socket)
            + ' -f /dev/null "$@"\n'
        )
        fake_codex = (
            '#!/bin/sh\nprintf "%s\\t%s\\t%s\\t%s\\n" "$$" "$TMUX_PANE" "$PWD" '
            '"${NO_COLOR-<unset>}" >> "$CODEX_LAUNCH_LOG"\nexec sleep 300\n'
        )
        for name, text in (("tmux", wrapper), ("codex", fake_codex)):
            path = self.bindir / name
            path.write_text(text)
            path.chmod(0o755)
        self.addCleanup(lambda: self.tmux("kill-server", check=False))
        self.tmux("new-session", "-d", "-s", "untouched", "-n", "keep", "sleep", "300")
        self.tmux("set-option", "-g", "base-index", "9")

    def tmux(self, *args, check=True):
        return subprocess.run(
            [TMUX, "-S", self.socket, "-f", "/dev/null", *args],
            env=self.environment, check=check, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, universal_newlines=True,
        ).stdout.strip()

    def launch(self, name="swq", inside=False):
        environment = self.environment.copy()
        if inside:
            environment["TMUX"] = self.socket + ",0,0"
        result = subprocess.run(
            ["bash", str(ROOT / "start.sh"), name, str(self.workdir)],
            env=environment, cwd=self.root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def records(self):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if self.launch_log.exists():
                rows = [line.split("\t") for line in self.launch_log.read_text().splitlines()]
                if len(rows) >= 4:
                    return rows
            time.sleep(0.03)
        self.fail("Four independent fake Codex processes did not start")

    def windows(self, name="swq"):
        return self.tmux("list-windows", "-t", name, "-F", "#{window_id}:#{window_index}:#{window_name}")

    def test_creates_independent_processes_without_changing_other_sessions(self):
        untouched = self.windows("untouched")
        options = ("mouse", "status-position", "base-index", "renumber-windows")
        before = {key: self.tmux("show-options", "-gv", key) for key in options}
        self.launch()
        rows = self.records()
        self.assertEqual(len({row[0] for row in rows}), 4)
        self.assertEqual({row[2] for row in rows}, {str(self.workdir)})
        self.assertEqual({row[3] for row in rows}, {"<unset>"})
        self.assertEqual([row.split(":", 1)[1] for row in self.windows().splitlines()],
                         ["1:shell", "2:paper", "3:code", "4:debug", "5:experiment"])
        self.assertEqual(self.tmux("show-options", "-t", "swq", "-v", "mouse"), "on")
        self.assertEqual(self.tmux("show-options", "-t", "swq", "-v", "status-position"), "bottom")
        self.assertEqual(self.windows("untouched"), untouched)
        self.assertEqual({key: self.tmux("show-options", "-gv", key) for key in options}, before)
        self.assertEqual(self.connect_log.read_text(), "attach-session -t =swq\n")

    def test_reconnect_preserves_processes_and_custom_layout(self):
        self.launch()
        processes = self.records()
        self.tmux("rename-window", "-t", "swq:paper", "research")
        self.tmux("new-window", "-d", "-t", "swq:", "-n", "notes", "sleep", "300")
        before = self.windows()
        self.launch()
        self.assertEqual(self.records(), processes)
        self.assertEqual(self.windows(), before)

    def test_switches_inside_tmux_without_nested_attach(self):
        self.launch(name="inside", inside=True)
        self.records()
        self.assertEqual(self.connect_log.read_text(), "switch-client -t =inside\n")

    def test_codex_exit_returns_to_shell_without_removing_window(self):
        self.launch()
        rows = self.records()
        pane = self.tmux("display-message", "-p", "-t", "swq:paper", "#{pane_id}")
        pid = next(int(row[0]) for row in rows if row[1] == pane)
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            command = self.tmux("display-message", "-p", "-t", "swq:paper", "#{pane_current_command}")
            if command == "sh":
                break
            time.sleep(0.03)
        self.assertEqual(command, "sh")
        self.assertEqual(len(self.windows().splitlines()), 5)


if __name__ == "__main__":
    unittest.main()
