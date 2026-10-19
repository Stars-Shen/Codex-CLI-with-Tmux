#!/usr/bin/env python3
"""Install a light Codex theme using only the Python standard library."""

import os
from pathlib import Path
import re
import shutil
import tempfile
from datetime import datetime


def update_config(text):
    lines = text.splitlines(keepends=True)
    header = re.compile(r"^\s*\[tui\]\s*(?:#.*)?$")
    start = next((i for i, line in enumerate(lines) if header.match(line)), None)
    theme_line = 'theme = "codex-light"\n'
    if start is None:
        if re.search(r"(?m)^\s*tui\s*(?:\.|=)", text):
            raise SystemExit("Inline/dotted tui configuration detected. Install the theme manually and select it with /theme; see README.md.")
        return text + ("\n" if text and not text.endswith("\n") else "") + "\n[tui]\n" + theme_line
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^\s*\[", lines[i])), len(lines))
    index = next((i for i in range(start + 1, end) if re.match(r"^\s*theme\s*=", lines[i])), None)
    if index is None:
        if not lines[start].endswith("\n"):
            lines[start] += "\n"
        lines.insert(start + 1, theme_line)
    elif lines[index].strip() != theme_line.strip():
        lines[index] = theme_line
    return "".join(lines)


def write_file(path, data):
    if path.exists() and path.read_bytes() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_name(path.name + ".backup-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
        shutil.copy2(path, backup)
        print("Backup:", backup)
    fd, temporary = tempfile.mkstemp(dir=str(path.parent), prefix=".codex-light-")
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print("Updated:", path)


if __name__ == "__main__":
    source = Path(__file__).resolve().parent
    target = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    config = target / "config.toml"
    text = config.read_text(encoding="utf-8") if config.exists() else ""
    updated = update_config(text)
    for filename in ("codex-light.tmTheme", "codex-light.LICENSE"):
        write_file(target / "themes" / filename, (source / filename).read_bytes())
    write_file(config, updated.encode("utf-8"))
    print("Installed. In Codex, run /theme and select codex-light (custom), or restart Codex.")
